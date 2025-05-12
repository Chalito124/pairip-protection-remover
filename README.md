# PairIP Protection Remover

A specialized tool for removing PairIP protection from Flutter applications packaged as `.apks` files. This script automates a series of operations to bypass Google's PairIP protection mechanism through targeted patching.

## Purpose

This tool is designed to bypass PairIP protection in Flutter applications by:
- Modifying native libraries
- Patching signature verification mechanisms
- Removing license check components from the manifest
- Reconfiguring file paths

## Usage

The tool is straightforward to use with a single command:

```bash
python3 patch.py app.apks
```

After processing, you'll get a patched APK file that has PairIP protection removed.

## Prerequisites

The following tools must be installed and available in your working directory:

1. **Python 3**
2. **Java Runtime Environment (JRE)**
3. **APKEditor-1.4.3.jar** - For APK manipulation
4. **uber-apk-signer.jar** - For signing the patched APK

## Installation

### On Linux/Termux:

```bash
# 1. Download required JAR files (if not already available)
wget https://github.com/REAndroid/APKEditor/releases/download/1.4.3/APKEditor-1.4.3.jar
wget https://github.com/patrickfav/uber-apk-signer/releases/download/v1.2.1/uber-apk-signer-1.2.1.jar -O uber-apk-signer.jar

# 2. Make the script executable
chmod +x patch.py
```

## How It Works

The script performs the following operations:

1. Extracts and processes the APKS file
2. Modifies key components to bypass PairIP protection
3. Patches native libraries and signature verification
4. Rebuilds and signs the modified APK

After completion, the script will create a patched APK with the same name as the input APKS file but with "-patched" added to the filename.

## Detailed Process Explanation

The script performs these operations in sequence:

1. **Extraction**: Unpacks `base.apk` from the `.apks` file
2. **Library Setup**: Copies `base.apk` to `libFirebaseCppApp.so`
3. **APK Merging**: Creates a merged APK with native libraries
4. **Decompilation**: Decompiles the APK for patching
5. **Manifest Modification**: Removes license check components
6. **Smali Patching**:
   - Updates `VMRunner.smali` to modify library loading
   - Modifies `SignatureCheck.smali` to bypass integrity checks
7. **Library Injection**: Copies required `.so` files
8. **Path Configuration**: Updates file path XML entries
9. **Rebuilding**: Reassembles the modified files into a new APK
10. **Signing**: Signs the APK for installation

## Troubleshooting

### Common Issues:

#### JAR files not found
```
Error: Required JAR file 'APKEditor-1.4.3.jar' not found in the current directory
```
**Solution**: Make sure to download all required JAR files to the same directory as the script.

#### Missing libraries
```
Error: Missing files in current directory: libpairipcorex.so, libFirebaseCppApp.so
```
**Solution**: Run the script once to generate these files, then run it again.

#### No signed APK found
```
Warning: No signed APK found in the output directory
```
**Solution**: Check if the uber-apk-signer.jar is properly working. The script will attempt to use the unsigned APK as a fallback.

#### Permission denied on Linux/macOS
```
Permission denied: 'patch.py'
```
**Solution**: Run `chmod +x patch.py` to make the script executable.

## Technical Details

### Target Modifications

- **Library Loading**: Modifies how native libraries are loaded
- **Signature Verification**: Bypasses app signature integrity checks
- **License Activity**: Removes license check activities from manifest
- **Content Provider**: Removes license content provider from manifest
- **File Paths**: Updates file path configuration for external storage access

### File Structure

```
/
├── patch.py                  # Main script
├── APKEditor-1.4.3.jar       # Required tool
├── uber-apk-signer.jar       # Required tool
├── your_app.apks             # Input file
├── libFirebaseCppApp.so      # Generated library
├── libpairipcorex.so         # Generated library
└── your_app-patched.apk      # Output file
```

## Security Considerations

This tool is intended for educational and research purposes only. Use it responsibly and only on applications you own or have permission to modify. Unauthorized modification of proprietary applications may violate terms of service and laws.

## License

This project is provided for educational purposes only. All modifications should respect the original application's licensing terms.

## Disclaimer

The developers of this tool are not responsible for any misuse, damage, or legal issues arising from the use of this software. Use at your own risk and only on applications you have the right to modify.
