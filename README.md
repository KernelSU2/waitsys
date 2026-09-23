# waitsys

用于 ksud 在软重启时 stop 后等待 system_server 在 servicemanager 中注册的服务清理完成，解决 LSPosed 等模块错误地获取到死亡服务的问题。

由于 AOSP 的系统库 libbinder 和 libutils 的 ABI 稳定性未知，且使用 C++ 编写，因此这部分逻辑与 rust 编写的 ksud 隔离开来，以避免让 ksud 直接链接到 libbinder 和 libutils 。

waitsys 由 ksud 执行，并通过 pipe 进行通信。通信逻辑较为简单：获取所有 binder 服务后向 pipe 写入字节 1 ，确认所有 binder 服务从 servicemanager 中移除后向 pipe 写入字节 2 。

构建：

```
python build.py build waitsys -t release -a arm64-v8a
python build.py build waitsys -t release -a x86_64
python build.py build waitsys -t release -a riscv64
```
