/*
 * Copyright (C) 2005 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#pragma once

#include <binder/Common.h>
#include <binder/Parcel.h>
#include <utils/Errors.h>
#include <utils/Vector.h>

// ---------------------------------------------------------------------------
namespace android {

/**
 * Kernel binder thread state. All operations here refer to kernel binder. This
 * object is allocated per-thread.
 */
    class IPCThreadState {
    public:

        LIBBINDER_EXPORTED static IPCThreadState* self();
        LIBBINDER_EXPORTED static IPCThreadState* selfOrNull(); // self(), but won't instantiate

        [[nodiscard]] LIBBINDER_EXPORTED pid_t getCallingPid() const;

        /**
         * Returns the SELinux security identifier of the process which has
         * made the current binder call. If not in a binder call this will
         * return nullptr. If this isn't requested with
         * Binder::setRequestingSid, it will also return nullptr.
         *
         * This can't be restored once it's cleared, and it does not return the
         * context of the current process when not in a binder call.
         */
        [[nodiscard]] LIBBINDER_EXPORTED const char* getCallingSid() const;

        /**
         * Returns the UID of the process which has made the current binder
         * call. If not in a binder call, this will return 0.
         */
        [[nodiscard]] LIBBINDER_EXPORTED uid_t getCallingUid() const;

        LIBBINDER_EXPORTED int64_t clearCallingIdentity();
        // Restores PID/UID (not SID)
        LIBBINDER_EXPORTED void restoreCallingIdentity(int64_t token);
        LIBBINDER_EXPORTED status_t flushCommands();
        LIBBINDER_EXPORTED void joinThreadPool(bool isMain = true);
    };

    constexpr uint32_t encodeExplicitIdentity(bool hasExplicitIdentity, pid_t callingPid) {
        uint32_t as_unsigned = static_cast<uint32_t>(callingPid);
        if (hasExplicitIdentity) {
            return as_unsigned | (1 << 30);
        } else {
            return as_unsigned & ~(1 << 30);
        }
    }

    constexpr int64_t packCallingIdentity(bool hasExplicitIdentity, uid_t callingUid,
                                          pid_t callingPid) {
        // Calling PID is a 32-bit signed integer, but doesn't consume the entire 32 bit space.
        // To future-proof this and because we have extra capacity, we decided to also support -1,
        // since this constant is used to represent invalid UID in other places of the system.
        // Thus, we pack hasExplicitIdentity into the 2nd bit from the left.  This allows us to
        // preserve the (left-most) bit for the sign while also encoding the value of
        // hasExplicitIdentity.
        //               32b     |        1b         |         1b            |        30b
        // token = [ calling uid | calling pid(sign) | has explicit identity | calling pid(rest) ]
        uint64_t token = (static_cast<uint64_t>(callingUid) << 32) |
                         encodeExplicitIdentity(hasExplicitIdentity, callingPid);
        return static_cast<int64_t>(token);
    }

    constexpr bool unpackHasExplicitIdentity(int64_t token) {
        return static_cast<int32_t>(token) & (1 << 30);
    }

    constexpr uid_t unpackCallingUid(int64_t token) {
        return static_cast<uid_t>(token >> 32);
    }

    constexpr pid_t unpackCallingPid(int64_t token) {
        int32_t encodedPid = static_cast<int32_t>(token);
        if (encodedPid & (1 << 31)) {
            return encodedPid | (1 << 30);
        } else {
            return encodedPid & ~(1 << 30);
        }
    }


} // namespace android

// ---------------------------------------------------------------------------