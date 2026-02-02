# Manual Android APK Build Guide (No Gradle/Studio)

This guide documents how to build a fully functional Android application using only command-line tools (`aapt2`, `d8`, `apksigner`, `zip`) without relying on the Gradle build system or Android Studio. This method is lightweight and ideal for environments like Termux or CI/CD pipelines where full IDEs are unavailable.

## 1. Prerequisites

Ensure you have the Android SDK Command-line Tools installed.
*   **SDK Path:** `/data/data/com.termux/files/usr/share/android-sdk` (or your specific path)
*   **Required Binaries:** `aapt2`, `d8`, `zipalign`, `apksigner`, `javac`/`kotlinc`.

## 2. Project Structure

Set up a standard source structure manually:
```
ProjectRoot/
├── app/
│   ├── src/main/
│   │   ├── AndroidManifest.xml       # App Manifest
│   │   ├── java/                     # Source Code (Kotlin/Java)
│   │   │   └── com/example/app/
│   │   │       └── MainActivity.kt
│   │   ├── res/                      # Resources (Layouts, Strings, etc.)
│   │   │   ├── layout/
│   │   │   ├── values/
│   │   │   └── xml/
│   │   └── assets/                   # Raw Assets (Binaries, etc.)
└── build_manual.sh                   # The Build Script
```

## 3. The Build Steps

The build process involves 6 distinct stages. Create a script (e.g., `build.sh`) with the following commands.

### Variables
Define your paths first:
```bash
SDK_DIR="/path/to/android-sdk"
ANDROID_JAR="$SDK_DIR/platforms/android-34/android.jar"
BUILD_DIR="build_manual"
```

### Step 1: Compile Resources (`aapt2 compile`)
Converts readable XML resources (layouts, strings) into binary `.flat` files.
```bash
aapt2 compile -o $BUILD_DIR/compiled_res/ app/src/main/res/**/*.xml
```

### Step 2: Link Resources (`aapt2 link`)
Merges compiled resources into a single APK container and generates the `R.java` ID file.
```bash
aapt2 link -o $BUILD_DIR/apk/unaligned.apk \
    -I $ANDROID_JAR \
    --manifest app/src/main/AndroidManifest.xml \
    --java $BUILD_DIR/gen \
    --auto-add-overlay \
    $(find $BUILD_DIR/compiled_res -name "*.flat")
```

### Step 3: Compile Source Code (`kotlinc` / `javac`)
Compiles your Kotlin/Java code along with the generated `R.java` into Java class files.
*   **Important:** Include `kotlin-stdlib.jar` if using Kotlin.
```bash
kotlinc -cp "$ANDROID_JAR:/path/to/kotlin-stdlib.jar" \
    -d $BUILD_DIR/obj \
    $BUILD_DIR/gen/com/example/app/R.java \
    app/src/main/java/com/example/app/*.kt
```

### Step 4: Convert to DEX (`d8`)
Converts Java class files (`.class`) into Android Dalvik Executable (`classes.dex`).
*   Replaces the older `dx` tool.
```bash
d8 --min-api 26 \
   --output $BUILD_DIR/apk \
   $BUILD_DIR/obj/*.class \
   /path/to/kotlin-stdlib.jar
```

### Step 5: Packaging
Add the generated `classes.dex` and any native libraries (`.so` files) to the APK created in Step 2.
```bash
cd $BUILD_DIR/apk
zip -u unaligned.apk classes.dex
# Add native libs if needed
zip -u unaligned.apk lib/arm64-v8a/*.so
```

### Step 6: Align & Sign
1.  **Zipalign:** Optimizes the APK layout for RAM efficiency (Required for Android).
2.  **Sign:** Signs the APK with a keystore so Android accepts it.

```bash
# Align
zipalign -v -p 4 $BUILD_DIR/apk/unaligned.apk $BUILD_DIR/apk/aligned.apk

# Generate Key (One time)
keytool -genkey -v -keystore debug.keystore -alias androiddebugkey ...

# Sign
apksigner sign --ks debug.keystore --out final-app.apk $BUILD_DIR/apk/aligned.apk
```

## 4. Common Pitfalls

*   **Missing Libraries:** If your app crashes with `NoClassDefFoundError`, you likely forgot to pass a `.jar` (like `kotlin-stdlib`) to *both* the compiler (Step 3) and the Dexer (Step 4).
*   **Resource IDs:** If `R.layout.main` isn't found, ensure `aapt2 link` (Step 2) ran successfully and generated the `R.java` file in the correct package structure.
*   **Native Libs:** Android strictly requires `.so` filenames for native libraries. Renaming `lib.so.1` to `lib.so` is mandatory.

## 5. Benefits of Manual Building
*   **Speed:** Compiles in seconds, not minutes.
*   **Control:** You know exactly what goes into the APK.
*   **Size:** No Gradle bloat; produces minimal APKs.
