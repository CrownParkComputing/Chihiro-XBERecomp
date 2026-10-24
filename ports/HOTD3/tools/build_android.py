#!/usr/bin/env python3
"""Build a standalone ARM64 APK. Game files are imported locally and never packaged."""
import argparse,hashlib,json,os,shutil,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--deps-source',type=Path,help='Optional cached dependency sources')
    parser.add_argument('--deps-build',type=Path,help='Optional compatible Android dependency _deps directory')
    parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.jobs<1:parser.error('--jobs must be positive')
    sdk=Path(os.environ.get('ANDROID_SDK_ROOT','/opt/android-sdk'))
    ndk=Path(os.environ.get('NDK',str(sdk/'ndk/28.2.13676358')))
    android=ROOT/'android';profile=json.loads((ROOT/'config/media.json').read_text())
    if not (ROOT/'generated/game/x86_func_mapping.cpp').exists():
        parser.error('Import the supported .7z and run tools/build_native.py --generate-only first')
    actual=hashlib.sha256((ROOT/'assets'/profile['executable']).read_bytes()).hexdigest()
    if actual!=profile['sha256']:parser.error('Unsupported game executable')
    common=['-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),'-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-33','-DANDROID_STL=c++_shared','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_POLICY_VERSION_MINIMUM=3.5']
    deps_project=android/'dependencies/build';deps=args.deps_build.resolve() if args.deps_build else deps_project/'_deps'
    sources=args.deps_source.resolve() if args.deps_source else deps
    if not args.package_only:
        if not args.deps_build:
            subprocess.run(['cmake','-G','Ninja','-S',str(android/'dependencies'),'-B',str(deps_project),*common],check=True)
            subprocess.run(['cmake','--build',str(deps_project),'--target','SDL3-shared','glslang','SPIRV','glslang-default-resource-limits','-j',str(args.jobs)],check=True)
        build=android/'build-native'
        subprocess.run(['cmake','-G','Ninja','-S',str(android),'-B',str(build),'-DXBE_DEPS_SOURCE='+str(sources),'-DXBE_DEPS_BUILD='+str(deps),*common],check=True)
        subprocess.run(['cmake','--build',str(build),'--target','main','-j',str(args.jobs)],check=True)
        libs=android/'app/src/main/jniLibs/arm64-v8a';libs.mkdir(parents=True,exist_ok=True)
        for lib in [build/'libmain.so',deps/'sdl3-build/libSDL3.so',ndk/'toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/libc++_shared.so']:shutil.copy2(lib,libs)
    jars=json.loads((android/'dependencies/java.json').read_text())
    for jar in jars:
        path=android/'libs'/jar['name'];path.parent.mkdir(exist_ok=True)
        if not path.exists():
            with urllib.request.urlopen(jar['url']) as response:path.write_bytes(response.read())
        if hashlib.sha256(path.read_bytes()).hexdigest()!=jar['sha256']:raise ValueError('Java dependency checksum differs: '+jar['name'])
    subprocess.run(['bash',str(android/'package.sh')],check=True)
if __name__=='__main__':main()
