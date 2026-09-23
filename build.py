import os
import subprocess as sp
import json
import sys
import shutil

from pathlib import Path
from argparse import ArgumentParser


def initialize():
    global ANDROID_HOME, ANDROID_NDK_HOME, PLATFORM, CMAKE_TOOLCHAIN_FILE, BUILD_DIR, OUTPUT_DIR
    ANDROID_HOME = os.getenv('ANDROID_HOME')
    if ANDROID_HOME is None:
        ANDROID_HOME = os.getenv('ANDROID_SDK_ROOT')
    if ANDROID_HOME is None:
        raise ValueError('Please add ANDROID_SDK_ROOT or ANDROID_HOME to your environment variable!')
    ANDROID_HOME = Path(ANDROID_HOME)

    with open('project-config.json', 'r', encoding='utf-8') as f:
        project_config = json.load(f)
        if 'ndkVer' not in project_config:
            raise ValueError('ndkVer not exist!')
        ndk_ver = project_config['ndkVer']
        if ndk_ver == '':
            raise ValueError('ndkVer should not be empty!')
        ANDROID_NDK_HOME = ANDROID_HOME / 'ndk' / ndk_ver
        if not os.path.isdir(ANDROID_NDK_HOME):
            raise ValueError(f'Ndk {ndk_ver} not exist: {ANDROID_NDK_HOME}')
        if 'platform' not in project_config:
            raise ValueError('platform not exist!')
        PLATFORM = project_config['platform']

    CMAKE_TOOLCHAIN_FILE = ANDROID_NDK_HOME / 'build/cmake/android.toolchain.cmake'
    BUILD_DIR = Path("./my_build").absolute()
    OUTPUT_DIR = Path("./output").absolute()


initialize()


def exec_out(cmd):
    p = sp.Popen(cmd, stdout=sp.PIPE)
    content = p.stdout.read().decode('utf-8').strip()
    p.wait()
    return content


def exec_cmd(cmd, *args, **kwargs):
    p = sp.Popen(cmd, *args, **kwargs)
    v = p.wait()
    if v != 0:
        raise RuntimeError(f'exec return non-zero: {v} {cmd}')


def exec_adb_cmd(c, device=None):
    cmd = ['adb']
    if device is not None:
        cmd += ['-s', device]
    cmd += c
    exec_cmd(cmd)


def exec_adb_shell(c, device=None, root=False):
    cmd = ['adb']
    if device is not None:
        cmd += ['-s', device]
    cmd += ['shell']
    if root:
        cmd += [f'exec su -c \'{c}\'']
    else:
        cmd += [c]
    exec_cmd(cmd)

def config(abi, plat, build_type="Debug"):
    build_dir = BUILD_DIR / build_type / abi
    output_dir = OUTPUT_DIR / build_type / abi
    exec_cmd(
        [
            'cmake',
            '-H.',
            f'-B{build_dir}',
            f'-DANDROID_ABI={abi}',
            f'-DANDROID_PLATFORM={plat}',
            f'-DANDROID_NDK={ANDROID_NDK_HOME}',
            f'-DCMAKE_TOOLCHAIN_FILE={CMAKE_TOOLCHAIN_FILE}',
            f'-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={output_dir}',
            f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={output_dir}',
            f"-DCMAKE_BUILD_TYPE={build_type}",
            '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
            '-G', 'Ninja'
        ]
    )


def build_target(target, abi='arm64-v8a', plat=PLATFORM, build_type="Debug", lib: bool=False):
    build_dir = BUILD_DIR / build_type / abi
    output_dir = OUTPUT_DIR / build_type / abi
    config(abi, plat, build_type=build_type)
    exec_cmd(['ninja', target], cwd=build_dir)
    if lib:
        target = f'lib{target}.so'
    output = output_dir / target
    print('Build output', output)
    return output


def get_device_abi(device):
    cmd = ['adb']
    if device is not None:
        cmd += ['-s', device]
    cmd += ['shell', 'getprop ro.product.cpu.abi']
    return exec_out(cmd)


SUPPORTED_ABIS = ['arm64-v8a', 'armeabi-v7a', 'x86_64', 'x86', 'riscv64']


def deploy(target, device, abi, dest, build_type, lib: bool):
    if abi is None:
        abi = get_device_abi(device)
    if abi not in SUPPORTED_ABIS:
        raise ValueError(f'device has unsupported abi: {abi}')
    print('** Deploying', abi)
    output = build_target(target, abi, PLATFORM, build_type=build_type, lib=lib)
    if lib:
        target = f'lib{target}.so'
    exec_adb_cmd(['push', output, dest], device=device)
    exec_adb_cmd(['shell', f'chmod +x {dest}/{target}'], device=device)
    print(f'Deploy {target} to {dest}/{target}')


ABI_NAME_ALIAS = {
    'arm64-v8a': ['arm64', 'a64', 'aarch64', 'arm64_v8a'],
    'armeabi-v7a': ['armeabi', 'arm', 'arm32', 'a32', 'armeabi_v7a'],
    'x86': ['i386', 'x32'],
    'x86_64': ['x64', 'x86-64'],
    'riscv64': ['riscv', 'r64'],
}
ABI_CHOICES = list(ABI_NAME_ALIAS.keys()) + sum(ABI_NAME_ALIAS.values(), [])
ABI_MAP = {None: None}
def initialize_abi_alias():
    for k in ABI_NAME_ALIAS:
        ABI_MAP[k] = k
        for v in ABI_NAME_ALIAS[k]:
            ABI_MAP[v] = k
initialize_abi_alias()
DEFAULT_ABI = "arm64-v8a"
ABI_TO_ARCH = {
    'arm64-v8a': 'aarch64',
    'armeabi-v7a': 'arm',
    'x86_64': 'x86_64',
    'x86': 'i386',
    'riscv64': 'riscv64'
}
BUILD_TYPE_CHOICES = ["debug", "release"]
BUILD_TYPE_CHOICES_MAP = {
    "debug": "Debug",
    "release": "RelWithDebInfo"
}


def build_cmd(args):
    build_target(args.target, abi=ABI_MAP[args.abi], plat=PLATFORM, build_type=BUILD_TYPE_CHOICES_MAP[args.build_type])


def config_cmd(args):
    config(ABI_MAP[args.abi], plat=PLATFORM, build_type=BUILD_TYPE_CHOICES_MAP[args.build_type])


def deploy_cmd(args):
    deploy(args.target, args.device, abi=ABI_MAP[args.abi], dest=args.dest, build_type=BUILD_TYPE_CHOICES_MAP[args.build_type], lib=args.lib)

def clean_cmd(args):
    abi = '*'
    if args.abi is not None:
        abi = args.abi
    build_type = '*'
    if args.abi is not None:
        build_type = BUILD_TYPE_CHOICES_MAP[args.build_type]
    for p in Path.glob(BUILD_DIR, f'{build_type}/{abi}'):
        print('Cleaning', p)
        shutil.rmtree(p)

def find_lldb(abi):
    arch = ABI_TO_ARCH[abi]
    return next(ANDROID_NDK_HOME.glob(f'toolchains/llvm/prebuilt/*/lib/clang/*/lib*/linux/{arch}/lldb-server'))


def lldb_cmd(args):
    abi = args.abi
    if abi is None:
        abi = get_device_abi(args.device)
    else:
        abi = ABI_MAP[abi]
    lldb_path = find_lldb(abi)
    if args.print:
        print(lldb_path)
        return
    # lldb-server require its working directory has a 'lldb-server' to launch gdbserver ...
    device_path = f'/data/local/tmp/lldb-server'
    exec_adb_cmd(['push', lldb_path, device_path], args.device)
    try:
        exec_adb_shell(f'chmod +x {device_path}', args.device)
        if not args.deploy:
            exec_adb_cmd(['forward', f'tcp:{args.port}', f'tcp:{args.port}'])
            exec_adb_shell(f'{device_path} p --server --listen 0.0.0.0:{args.port}', device=args.device, root=args.root)
    finally:
        '''
        try:
            exec_adb_cmd(['shell', f'rm {device_path}'])
        except:
            pass
        '''
        try:
            if not args.deploy:
                exec_adb_cmd(['forward', '--remove', f'tcp:{args.port}'])
        except:
            pass


def main():
    ap = ArgumentParser(
        prog="build",
        description=""
    )

    subps = ap.add_subparsers(required=True)

    build_args = subps.add_parser('build')
    build_args.add_argument('target')
    build_args.add_argument('-a', dest='abi', choices=ABI_CHOICES, default=DEFAULT_ABI)
    build_args.add_argument('-t', dest='build_type', choices=BUILD_TYPE_CHOICES, default=BUILD_TYPE_CHOICES[0])
    build_args.set_defaults(func=build_cmd)

    config_args = subps.add_parser('config')
    config_args.set_defaults(func=config_cmd)
    config_args.add_argument('-a', dest='abi', choices=ABI_CHOICES, default=DEFAULT_ABI)
    config_args.add_argument('-t', dest='build_type', choices=BUILD_TYPE_CHOICES, default=BUILD_TYPE_CHOICES[0])

    deploy_args = subps.add_parser('deploy')
    deploy_args.add_argument('target')
    deploy_args.set_defaults(func=deploy_cmd)
    deploy_args.add_argument('-s', dest='device', required=False)
    deploy_args.add_argument('-a', dest='abi', choices=ABI_CHOICES, default=None)
    deploy_args.add_argument('-d', dest='dest', default='/data/local/tmp')
    deploy_args.add_argument('-l', dest='lib', action='store_true')
    deploy_args.add_argument('-t', dest='build_type', choices=BUILD_TYPE_CHOICES, default=BUILD_TYPE_CHOICES[0])

    lldb_args = subps.add_parser('lldb')
    lldb_args.set_defaults(func=lldb_cmd)
    lldb_args.add_argument('-s', dest='device', required=False)
    lldb_args.add_argument('-p', dest='print', action='store_true', default=False)
    lldb_args.add_argument('-d', dest='deploy', action='store_true', default=False)
    lldb_args.add_argument('-a', dest='abi', choices=ABI_CHOICES, default=None)
    lldb_args.add_argument('-P', dest='port', default='12345')
    lldb_args.add_argument('--root', default=False)

    clean_args = subps.add_parser('clean')
    clean_args.add_argument('-a', '--abi', default=None)
    clean_args.set_defaults(func=clean_cmd)
    clean_args.add_argument('-t', dest='build_type', choices=BUILD_TYPE_CHOICES, default=BUILD_TYPE_CHOICES[0])

    args = ap.parse_args(sys.argv[1:])
    args.func(args)


main()
