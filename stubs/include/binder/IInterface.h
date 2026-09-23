#pragma once

#include "binder/IBinder.h"
#include "utils/RefBase.h"

namespace android {
    class IInterface : public virtual RefBase {
protected:
    virtual                     ~IInterface();
    virtual IBinder*            onAsBinder() = 0;
    };
}
