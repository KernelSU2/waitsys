#pragma once
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused-private-field"

namespace android {
class String16 {
public:
    String16();

    String16(const String16 &o);

    String16(String16 &&o) noexcept;

    explicit String16(const char *o);

    ~String16();

void                setTo(const String16& other);
inline  String16&           operator=(const String16& other);
        String16&           operator=(String16&& other) noexcept;

private:
    const char16_t *mString;
};

inline String16& String16::operator=(const String16& other)
{
    setTo(other);
    return *this;
}


}  // namespace android

#pragma clang diagnostic pop
