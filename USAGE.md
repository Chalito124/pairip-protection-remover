# Usage Guide

This tool is designed to be simple and direct. It requires minimal setup and interaction.

## Basic Usage

```bash
python3 patch.py your_app.apks
```

That's it. The tool does everything automatically.

## What the Tool Does

1. Extracts the base APK from the APKS file
2. Creates necessary library files
3. Disables PairIP protection mechanisms:
   - Patches native library loading
   - Bypasses signature verification
   - Removes license check activities
   - Modifies file paths for access
4. Rebuilds and signs the APK

## Example Output

```
$ python3 patch.py app.apks

[1/10] Extracting base.apk from APKS file...
Executing: unzip -o "app.apks" base.apk

[2/10] Renaming base.apk to libFirebaseCppApp.so...

[3/10] Removing existing merged_app.apk...

[4/10] Merging APKS to APK...
Executing: java -jar APKEditor-1.4.3.jar m -i "app.apks" -o merged_app.apk -extractNativeLibs true

[5/10] Removing existing decompiled directory...

[6/10] Decompiling merged APK...
Executing: java -jar APKEditor-1.4.3.jar d -i merged_app.apk

[7/10] Modifying AndroidManifest.xml...
Modified AndroidManifest.xml: /data/data/com.termux/files/home/merged_app_decompile_xml/AndroidManifest.xml

[8/10] Removing existing out.apk...

Running patch operations...
Patched <clinit>: /data/data/com.termux/files/home/merged_app_decompile_xml/smali/classes/com/pairip/VMRunner.smali
Patched verifyIntegrity: /data/data/com.termux/files/home/merged_app_decompile_xml/smali/classes/com/pairip/SignatureCheck.smali
Copied libpairipcoree.so to: /data/data/com.termux/files/home/merged_app_decompile_xml/root/lib/arm64-v8a
Copied libFirebaseCppApp.so to: /data/data/com.termux/files/home/merged_app_decompile_xml/root/lib/arm64-v8a
Patched file_paths.xml: /data/data/com.termux/files/home/merged_app_decompile_xml/resources/package_1/res/xml/file_paths.xml
[✓] Patched 1 file_paths.xml file(s).

[9/10] Building APK from modified files...
Executing: java -jar APKEditor-1.4.3.jar b -i /data/data/com.termux/files/home/merged_app_decompile_xml -o out.apk

[10/10] Signing the APK...
Executing: java -jar uber-apk-signer.jar -a out.apk

Process complete! Final patched APK saved as: app-patched.apk

Cleaning up temporary files...
Kept files: app-patched.apk and app.apks
All temporary files have been removed.
```

## Common Issues

### Missing JAR Files

Make sure APKEditor-1.4.3.jar and uber-apk-signer.jar are in the same directory as the script.

### Permission Issues

In Linux/Termux, make sure the script is executable:
```bash
chmod +x patch.py
```

### Java Memory Issues

For large APKs, you may need to increase Java's memory:
```bash
export _JAVA_OPTIONS="-Xmx2g"
```

## Getting the Patched APK

After successful patching, you'll find a file named `[original-name]-patched.apk` in the same directory. This is your patched APK with PairIP protection removed.
