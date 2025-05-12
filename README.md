# PairIP Protection Remover

A specialized tool for removing PairIP protection from Flutter applications packaged as `.apks` files. This script automates a series of operations to bypass Google's PairIP protection mechanism through targeted patching.

## Purpose

This tool is designed to bypass PairIP protection in Flutter applications by:
- Modifying native libraries
- Patching signature verification mechanisms
- Removing license check components from the manifest
- Reconfiguring file paths

## Prerequisites

The following tools must be installed and available in your working directory:

1. **Python 3**
2. **Java Runtime Environment (JRE)**
3. **APKEditor-1.4.3.jar** - For APK manipulation
4. **uber-apk-signer.jar** - For signing the patched APK

## Java Installation

### On Linux:

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install default-jre

# Fedora/RHEL
sudo dnf install java-latest-openjdk

# Verify installation
java -version
```

### On Termux (Android):

```bash
# Install OpenJDK
pkg update
pkg install openjdk-17

# Verify installation
java -version
```

### Making Java Globally Accessible

1. Add Java to your PATH by adding these lines to your `~/.bashrc` or `~/.zshrc` file:

```bash
# For typical Linux installations
export JAVA_HOME=/usr/lib/jvm/default-java
export PATH=$PATH:$JAVA_HOME/bin

# For Termux
export JAVA_HOME=/data/data/com.termux/files/usr/opt/openjdk
export PATH=$PATH:$JAVA_HOME/bin
```

2. Apply the changes:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

3. Verify Java is in your PATH:

```bash
which java
java -version
```

## Installation

### On Linux/Termux:

```bash
# 1. Download required JAR files (if not already available)
wget https://github.com/REAndroid/APKEditor/releases/download/1.4.3/APKEditor-1.4.3.jar
wget https://github.com/patrickfav/uber-apk-signer/releases/download/v1.2.1/uber-apk-signer-1.2.1.jar -O uber-apk-signer.jar

# 2. Make the script executable
chmod +x patch.py
```

## Usage

The tool is straightforward to use with a single command:

```bash
python3 patch.py app.apks
```

After processing, you'll get a patched APK file that has PairIP protection removed.

## How It Works

The script performs the following operations:

1. Extracts and processes the APKS file
2. Modifies key components to bypass PairIP protection
3. Patches native libraries and signature verification
4. Rebuilds and signs the modified APK

After completion, the script will create a patched APK with the same name as the input APKS file but with "-patched" added to the filename.

## Technical Summary

The script targets specific PairIP protection mechanisms:

1. **Library Modifications**: Replaces key native libraries
2. **VM Runner Patching**: Changes how libraries are loaded
3. **Signature Check Bypass**: Disables integrity verification
4. **Manifest Cleaning**: Removes license verification components
5. **Path Modifications**: Updates file access configurations

## Troubleshooting

### Java Not Found
If you get an error like "java: command not found", ensure Java is properly installed and in your PATH:

```bash
# Check if Java is installed
java -version

# If not found, install Java and add to PATH as described above
```

### Insufficient Java Memory
For large APKs, increase Java's memory allocation:

```bash
export _JAVA_OPTIONS="-Xmx2g"
```

### File Permission Issues
Make sure the script is executable:

```bash
chmod +x patch.py
```

## Requirements

Place these files in the same directory:
- patch.py
- APKEditor-1.4.3.jar
- uber-apk-signer.jar
- libpairipcorex.so

## Disclaimer

This tool is provided for educational and research purposes only. Use it responsibly and only on applications you own or have permission to modify.
