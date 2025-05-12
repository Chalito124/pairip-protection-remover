# PairIP Protection Remover

A specialized tool for removing PairIP protection from Flutter applications packaged as `.apks` files. This script automates patching operations to bypass Google's PairIP protection mechanism.

## Required Files

Your working directory **must** contain these exact files:
- `patch.py` - The main Python script
- `APKEditor-1.4.3.jar` - For APK manipulation
- `uber-apk-signer.jar` - For signing the patched APK
- `libpairipcorex.so` - Essential library file for patching

The script will fail if any of these files are missing. The `libpairipcorex.so` file included in this repository is critical and cannot be substituted.

## Installation Instructions

### Windows

1. **Install Python 3**:
   - Download from [python.org](https://www.python.org/downloads/windows/)
   - **Important**: Check "Add Python to PATH" during installation
   - Verify in Command Prompt: `python --version`

2. **Install Java JRE**:
   - Download from [Oracle](https://www.java.com/en/download/) or [AdoptOpenJDK](https://adoptopenjdk.net/)
   - Add to PATH:
     ```
     setx JAVA_HOME "C:\Program Files\Java\jre-xx.x.x"
     setx PATH "%PATH%;%JAVA_HOME%\bin"
     ```
   - Verify: `java -version`

3. **Install unzip utility**:
   - Download and install [7-Zip](https://www.7-zip.org/download.html)
   - Add to PATH or use full path when executing the script

4. **Download required files**:
   - Download all four required files to the same directory
   - Ensure the files have the exact names listed above

### Ubuntu/Debian

```bash
# Install required packages
sudo apt update
sudo apt install -y python3 python3-pip default-jre unzip

# Create a working directory
mkdir pairip-remover
cd pairip-remover

# Download required tools
wget https://github.com/REAndroid/APKEditor/releases/download/1.4.3/APKEditor-1.4.3.jar
wget https://github.com/patrickfav/uber-apk-signer/releases/download/v1.2.1/uber-apk-signer-1.2.1.jar

# Download the patch script and libpairipcorex.so from this repository
wget https://raw.githubusercontent.com/void-eth/pairip-protection-remover/main/patch.py
wget https://raw.githubusercontent.com/void-eth/pairip-protection-remover/main/libpairipcorex.so

# Make the script executable
chmod +x patch.py
```

### Fedora/RHEL/CentOS

```bash
# Install required packages
sudo dnf install -y python3 python3-pip java-latest-openjdk unzip

# Follow the same steps as Ubuntu/Debian for downloading the required files
```

### macOS

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python openjdk unzip

# Add Java to PATH
echo 'export JAVA_HOME=$(/usr/libexec/java_home)' >> ~/.zshrc
echo 'export PATH=$PATH:$JAVA_HOME/bin' >> ~/.zshrc
source ~/.zshrc

# Download required files (same as Ubuntu/Debian)
```

### Android (via Termux)

```bash
# Install required packages
pkg update
pkg install -y python openjdk-17 unzip wget

# Allow storage access
termux-setup-storage

# Create working directory
mkdir pairip-remover
cd pairip-remover

# Download required tools and files
wget https://github.com/REAndroid/APKEditor/releases/download/1.4.3/APKEditor-1.4.3.jar
wget https://github.com/patrickfav/uber-apk-signer/releases/download/v1.2.1/uber-apk-signer-1.2.1.jar
wget https://raw.githubusercontent.com/void-eth/pairip-protection-remover/main/patch.py
wget https://raw.githubusercontent.com/void-eth/pairip-protection-remover/main/libpairipcorex.so

# Make script executable
chmod +x patch.py
```

## Usage

The script requires a `.apks` file as input:

```bash
# On Windows
python patch.py your_app.apks

# On Linux/macOS/Termux
python3 patch.py your_app.apks
```

## How It Works

The script performs these operations:

1. **Extraction**: Unpacks `base.apk` from the `.apks` file
2. **Library Setup**: Creates `libFirebaseCppApp.so` from `base.apk`
3. **APK Merging**: Creates a merged APK with native libraries enabled
4. **Decompilation**: Decompiles the APK for patching
5. **Manifest Modification**: Removes license check components using regex patterns
6. **Smali Patching**:
   - Replaces the `<clinit>` method in `VMRunner.smali` to modify library loading
   - Modifies `SignatureCheck.smali` to add an early return, bypassing integrity checks
7. **Library Injection**: Copies `libpairipcorex.so` and `libFirebaseCppApp.so` to architecture directories
8. **File Path Patching**: Updates external path entries in XML files
9. **Rebuilding**: Reassembles the modified files into a new APK
10. **Signing**: Signs the APK for installation

## Modifications Made by the Script

### VMRunner Patching

Replaces the `<clinit>` method to load our custom libraries:

```smali
.method static constructor <clinit>()V
    .registers 1

    .line 30
    const-string v0, "pairipcorex"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    const-string v0, "pairipcore"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    return-void
.end method
```

### SignatureCheck Bypassing

Adds an early return to the integrity verification method:

```smali
.method public static verifyIntegrity(Landroid/content/Context;)V
    # Method annotations
    .end annotation
    return-void  # Early return added here to skip the entire verification
```

### AndroidManifest Cleaning

Removes these components using regex:
- `<activity android:name="com.pairip.licensecheck.LicenseActivity" ... />`
- `<provider android:name="com.pairip.licensecheck.LicenseContentProvider" ... />`

### File Path Modifications

Changes external path entries:
```xml
<!-- From -->
<external-path name="..." path="Android/data/package.name/files/Pictures" />

<!-- To -->
<external-files-path name="my_images" path="Pictures/" />
```

## Troubleshooting

### Common Issues

1. **"Missing files in current directory"**
   - Ensure `libpairipcorex.so` and all required JAR files are in the same directory as the script
   - The filenames must be exactly as expected: `APKEditor-1.4.3.jar`, `uber-apk-signer.jar`, and `libpairipcorex.so`

2. **Java-related errors**
   - Verify Java is installed: `java -version`
   - Make sure Java is in your PATH
   - For large APKs, increase Java memory: 
     ```
     # Windows
     set _JAVA_OPTIONS=-Xmx2g
     
     # Linux/macOS/Termux
     export _JAVA_OPTIONS="-Xmx2g"
     ```

3. **"unzip: command not found"**
   - Install unzip utility for your platform
   - For Windows, install 7-Zip and ensure it's in your PATH

4. **"Could not find any signed APK"**
   - The script will try to use fallback options
   - If signing fails completely, try running the signing step manually:
     ```
     java -jar uber-apk-signer.jar -a out.apk
     ```

5. **Permission Denied**
   - Make the script executable: `chmod +x patch.py`
   - On Windows, run Command Prompt as Administrator

### Platform-Specific Issues

#### Windows
- If PowerShell blocks execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- Use double quotes in paths that contain spaces

#### Termux
- If you get "Bad system call", try: `termux-change-repo` to switch repositories
- Ensure you've run `termux-setup-storage` if accessing files from shared storage

## Memory Considerations

This process can be memory-intensive, especially for large APKs. If you encounter memory errors:

1. Close other applications to free up memory
2. Increase Java's memory allocation as mentioned above
3. On Termux, try restarting Termux before running the script

## Final Notes

- The patched APK will be named `[original_name]-patched.apk`
- The script preserves `libpairipcorex.so` and `libFirebaseCppApp.so` for future runs
- Always keep a backup of your original `.apks` file

## Disclaimer

This tool is provided for educational and research purposes only. Use it responsibly and only on applications you own or have permission to modify.
