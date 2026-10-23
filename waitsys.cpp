#include <cstdlib>
#include <fcntl.h>
#include <unistd.h>

#include <binder/IServiceManager.h>
#include <binder/IBinder.h>
#include <utils/String8.h>
#include <binder/ProcessState.h>
#include <utils/StrongPointer.h>
#include <map>
#include <condition_variable>
#include <thread>

#include "logging.h"
#include "utils/Errors.h"
#include <mutex>

using namespace android;

std::string to_string(const String16 &s) {
    return String8{s}.c_str();
}

template<typename F>
struct Recipient : public IBinder::DeathRecipient {
    F f;
    Recipient(F&& f) : f(std::move(f)) {}

    void binderDied(const wp<android::IBinder> &who) override {
        f(who);
    }
};

int main() {
#ifndef NDEBUG
    logging::setPrintEnabled(true);
#endif
    ProcessState::self()->startThreadPool();

    int controller_fd = -1;
    if (auto e = getenv("KSU_WAITSYS_FD"); e) {
        controller_fd = strtol(e, nullptr, 0);
        LOGD("controller fd %d", controller_fd);
    }

    auto sm = android::defaultServiceManager();

    status_t status;
    pid_t am_pid;
    std::map<sp<IBinder>, String16> ss_services{};
    bool am_died = false;

    std::mutex ss_services_mtx{};
    std::condition_variable cv{};
    
    auto fn = [&](const wp<android::IBinder> &who) {
        {
            std::unique_lock lk{ss_services_mtx};
            am_died = true;
        }
        cv.notify_one();
    };
    auto recipient = sp<Recipient<decltype(fn)>>::make(std::move(fn));

    auto am = sm->checkService(String16{"activity"});
    if (!am) {
        LOGE("no activity service found!");
        return 1;
    }

    status = am->getDebugPid(&am_pid);
    if (status != OK) {
        LOGE("could not get am pid: %d", status);
        return 1;
    }

    LOGD("am_pid=%d", am_pid);
    am->linkToDeath(recipient);

    auto services = sm->listServices();
    auto N = services.size();
    pid_t pid;
    for (size_t i = 0; i < N; i++) {
        auto b = sm->checkService(services[i]);
        if (!b) continue;
        status = b->getDebugPid(&pid);
        if (status != OK) {
            LOGE("could not get pid of service %s: %d", to_string(services[i]).c_str(), status);
        } else if (pid == am_pid) {
            ss_services.emplace(b, services[i]);
        }
    }

    if (controller_fd >= 0) {
        char buf = 1;
        if (TEMP_FAILURE_RETRY(write(controller_fd, &buf, sizeof(buf))) != 1) {
            PLOGE("write 1");
        }
    }

    LOGD("collected %zu services, waiting ...", ss_services.size());

    {
        std::unique_lock lk{ss_services_mtx};
        cv.wait(lk, [&]{ return am_died; });

        LOGI("am died");

        int try_count = 0;
        for (;;) {
            try_count++;
            bool has_live = false;
            for (auto &[_, name]: ss_services) {
                if (sm->checkService(name)) {
                    LOGE("still exist in servicemanager: %s", to_string(name).c_str());
                    has_live = true;
                    break;
                }
            }

            if (has_live) {
                using namespace std::chrono_literals;
                std::this_thread::sleep_for(200ms);
            } else {
                break;
            }
        }

        LOGI("all services are removed from ServiceManager (tried %d)", try_count);
    }

    if (controller_fd >= 0) {
        char buf = 2;
        if (TEMP_FAILURE_RETRY(write(controller_fd, &buf, sizeof(buf))) != 1) {
            PLOGE("write 2");
        }
    }

    return 0;
}
