#!/usr/bin/env bash
# Offline APK packaging with the Android SDK; Gradle is optional.
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"
sdk_root="${ANDROID_SDK_ROOT:-/opt/android-sdk}"
build_tools="$sdk_root/build-tools/${BUILD_TOOLS:-36.0.0}"
android_jar="$sdk_root/platforms/android-35/android.jar"
package_dir="$PWD/build/package"
jni_dir="$PWD/app/src/main/jniLibs/arm64-v8a"
java_dir="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk}/bin"
ndk_dir="${NDK:-$sdk_root/ndk/28.2.13676358}"
for lib in libmain.so libSDL3.so libc++_shared.so; do
    [[ -f "$jni_dir/$lib" ]] || { echo "Missing $lib: run build-native.sh first" >&2; exit 1; }
done
mkdir -p "$package_dir" "$package_dir/classes" "$package_dir/dex" "$package_dir/generated"
"$build_tools/aapt2" compile --dir app/src/main/res -o "$package_dir/resources.zip"
python3 - "$package_dir/AndroidManifest.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET
ET.register_namespace('android', 'http://schemas.android.com/apk/res/android')
tree = ET.parse('app/src/main/AndroidManifest.xml')
tree.getroot().set('package', 'com.crownpark.hotd3')
tree.write(sys.argv[1], encoding='utf-8', xml_declaration=True)
PY
"$build_tools/aapt2" link -I "$android_jar" --manifest "$package_dir/AndroidManifest.xml" \
    --min-sdk-version 33 --target-sdk-version 35 --version-code 2 --version-name 0.2.0-preview \
    --java "$package_dir/generated" -o "$package_dir/base.apk" "$package_dir/resources.zip"
mapfile -t sources < <(find app/src/main/java "$package_dir/generated" -name '*.java' -print)
"$java_dir/javac" -encoding UTF-8 --release 8 -classpath "$android_jar:$PWD/libs/*" \
    -d "$package_dir/classes" "${sources[@]}"
"$java_dir/jar" cf "$package_dir/classes.jar" -C "$package_dir/classes" .
"$build_tools/d8" --min-api 33 --lib "$android_jar" --output "$package_dir/dex" "$package_dir/classes.jar" "$PWD"/libs/*.jar
mkdir -p "$package_dir/payload/lib/arm64-v8a"
cp "$package_dir/dex/classes.dex" "$package_dir/payload/"
for lib in "$jni_dir"/*.so; do
    "$ndk_dir/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" \
        --strip-unneeded -o "$package_dir/payload/lib/arm64-v8a/$(basename "$lib")" "$lib"
done
cp "$package_dir/base.apk" "$package_dir/unsigned.apk"
(
    cd "$package_dir/payload"
    zip -q -0 "$package_dir/unsigned.apk" classes.dex lib/arm64-v8a/*.so
)
"$build_tools/zipalign" -P 16 -f 4 "$package_dir/unsigned.apk" "$package_dir/aligned.apk"
mkdir -p "$PWD/../.local/keys"
keystore="${KEYSTORE:-$PWD/../.local/keys/android-release.keystore}"
if [[ ! -f "$keystore" ]]; then
    "$java_dir/keytool" -genkeypair -keystore "$keystore" -storepass android -keypass android \
        -alias crownparkrelease -keyalg RSA -keysize 2048 -validity 10000 -dname 'CN=CrownPark Chihiro Ports,O=CrownPark,C=GB'
fi
apk="$PWD/build/HOTD3-Android-arm64.apk"
"$build_tools/apksigner" sign --ks "$keystore" --ks-pass pass:android --key-pass pass:android \
    --ks-key-alias crownparkrelease --out "$apk" "$package_dir/aligned.apk"
"$build_tools/apksigner" verify "$apk"
"$build_tools/zipalign" -c -P 16 4 "$apk"
echo "$apk"
