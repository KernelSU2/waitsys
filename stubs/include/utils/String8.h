#pragma once

#include <stdint.h>

namespace android {
class String16;

class String8
{
public:
                                String8();
                                String8(const String8& o);
    explicit                    String8(const char* o);
    explicit                    String8(const char* o, size_t numChars);

    explicit                    String8(const String16& o);
                                ~String8();
    inline  const char*         c_str() const;
private:
    const char* mString;
};

inline const char* String8::c_str() const
{
    return mString;
}

}
