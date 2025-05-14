# PairIP Protection Remover

[![GitHub stars](https://img.shields.io/github/stars/void-eth/pairip-protection-remover.svg?style=social&label=Star&maxAge=2592000)](https://github.com/void-eth/pairip-protection-remover/stargazers/)
[![License](https://img.shields.io/github/license/void-eth/pairip-protection-remover.svg)](https://github.com/void-eth/pairip-protection-remover/blob/main/LICENSE)
[![Release](https://img.shields.io/github/release/void-eth/pairip-protection-remover.svg)](https://github.com/void-eth/pairip-protection-remover/archive/refs/heads/main.zip)

A simple, cross-platform tool for bypassing Google's PairIP protection in Flutter applications. Available in both Python and Bash versions.

## What is PairIP Protection?

PairIP is Google's app protection system that implements multiple layers of security checks:
- Signature verification
- License verification
- Integrity checks
- Runtime protection measures

When an app with PairIP protection is modified, it typically crashes immediately or exhibits black screens. This occurs because the protection detects changes to the app and prevents execution.

## Features

- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Easy to Use**: Simple command-line interface
- **Automatic Processing**: Handles all the steps required to remove PairIP protection
- **Multiple Patches**: Modifies various components including:
  - `VMRunner.smali` to bypass runtime VM checks
  - `SignatureCheck.smali` to bypass integrity verification
  - `AndroidManifest.xml` to remove license checks
  - `file_paths.xml` to fix external storage access issues
- **Automatic Cleanup**: Removes temporary files after processing

## Requirements

### For Python Version:
- Python 3.6 or higher
- Java Runtime Environment (JRE) 8 or higher

### For Bash Version:
- Bash shell (available by default on Linux/macOS, requires installation on Windows)
- Java Runtime Environment (JRE) 8 or higher
- Common UNIX tools: `unzip`, `zip`, `basename`, `dirname`, `realpath`

### Common Requirements (both versions):
- `APKEditor-1.4.3.jar` (included in release)
- `uber-apk-signer.jar` (included in release)

## Installation

### Python Version Installation

#### Windows:
1. Download the latest release from the [releases page](https://github.com/void-eth/pairip-protection-remover/archive/refs/heads/main.zip)
2. Extract the ZIP file to a directory of your choice
3. Ensure you have Python installed:
   ```
   # Check Python version
   python --version
   ```
   If Python is not installed, download and install it from [python.org](https://www.python.org/downloads/)
4. Ensure you have Java installed:
   ```
   # Check Java version
   java -version
   ```
   If Java is not installed, download and install it from [Oracle Java](https://www.oracle.com/java/technologies/javase-jre8-downloads.html) or [OpenJDK](https://adoptopenjdk.net/)

#### Linux/macOS:
1. Download the latest release from the [releases page](https://github.com/void-eth/pairip-protection-remover/archive/refs/heads/main.zip)
2. Extract the archive:
   ```bash
   unzip pairip-protection-remover-*.zip
   # OR
   tar -xzvf pairip-protection-remover-*.tar.gz
   ```
3. Ensure you have Python installed:
   ```bash
   # Check Python version
   python3 --version
   ```
   If Python is not installed, install it using your package manager:
   ```bash
   # For Debian/Ubuntu
   sudo apt-get install python3 python3-pip
   
   # For macOS with Homebrew
   brew install python3
   ```
4. Ensure you have Java installed:
   ```bash
   # Check Java version
   java -version
   ```
   If Java is not installed, install it using your package manager:
   ```bash
   # For Debian/Ubuntu
   sudo apt-get install default-jre
   
   # For macOS with Homebrew
   brew install --cask adoptopenjdk
   ```

### Bash Version Installation

#### Linux/macOS:
1. Download the latest release from the [releases page](https://github.com/void-eth/pairip-protection-remover/archive/refs/heads/main.zip)
2. Extract the archive:
   ```bash
   unzip pairip-protection-remover-*.zip
   # OR
   tar -xzvf pairip-protection-remover-*.tar.gz
   ```
3. Make the script executable:
   ```bash
   chmod +x patch.sh
   ```
4. Ensure you have Java installed:
   ```bash
   # Check Java version
   java -version
   ```
   If Java is not installed, install it using your package manager:
   ```bash
   # For Debian/Ubuntu
   sudo apt-get install default-jre
   
   # For macOS with Homebrew
   brew install --cask adoptopenjdk
   ```
5. Ensure required tools are installed:
   ```bash
   # For Debian/Ubuntu
   sudo apt-get install unzip zip
   
   # For macOS with Homebrew
   brew install coreutils
   ```

#### Windows (using WSL):
1. Install Windows Subsystem for Linux (WSL) by following the [official guide](https://docs.microsoft.com/en-us/windows/wsl/install)
2. Open WSL terminal and follow the Linux installation steps above

## Usage

### Python Version

```bash
# On Windows
python patch_new.py your_app.apks

# On Linux/macOS
python3 patch_new.py your_app.apks
```

### Bash Version

```bash
# On Linux/macOS
./patch.sh your_app.apks

# On Windows with WSL
bash patch.sh your_app.apks
```

## How It Works

The PairIP Protection Remover works by performing the following steps:

1. **Extract base.apk**: Extracts the base APK from the APKS bundle
2. **Create libFirebaseCppApp.so**: Creates a modified native library
3. **Merge APKS to APK**: Merges the split APK files into a single APK
4. **Decompile the APK**: Decompiles the merged APK to access its code
5. **Modify AndroidManifest.xml**: Removes license check components
6. **Patch VMRunner.smali**: Replaces the `clinit()` method to bypass VM checks
7. **Patch SignatureCheck.smali**: Modifies integrity verification checks
8. **Copy Modified Native Libraries**: Replaces the original libraries with patched versions
9. **Patch file_paths.xml**: Updates external storage access configuration
10. **Rebuild and Sign**: Recompiles and signs the modified APK

## Common Issues and Troubleshooting

### Java Issues
- **Error**: `java: command not found` or `Java not found`
  - **Solution**: Install Java Runtime Environment (JRE) 8 or higher

### Python Issues
- **Error**: `ModuleNotFoundError: No module named 'colorama'`
  - **Solution**: The script should auto-install dependencies, but you can manually install them with:
    ```bash
    pip install colorama tqdm
    ```

### JAR File Issues
- **Error**: `Required JAR file 'APKEditor-1.4.3.jar' not found`
  - **Solution**: Ensure the JAR files are in the same directory as the script

### APK Processing Issues
- **Error**: `Failed to merge APKS to APK`
  - **Solution**: Check if the input file is a valid APKS file and if Java has enough memory

## Advanced Usage

### Creating Custom Patched Native Libraries

For advanced users who want to create custom patched versions of the native libraries:

1. Extract the original `libpairipcore.so` from your app
2. Use a tool like Ghidra or IDA Pro to analyze and modify the library
3. Replace the default library with your custom version in the script directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is provided for educational purposes only. Use it at your own risk. The authors are not responsible for any misuse of this tool or any violations of terms of service of any app marketplaces.

## Acknowledgements

- Thanks to all contributors who have helped to improve this tool
- Special thanks to the Flutter and Android developer communities
