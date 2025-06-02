#!/usr/bin/env python3
"""
PairIP Protection Remover v1.3 (Termux Optimized)
Cross-platform tool for patching Flutter applications
Repository: https://github.com/void-eth/pairip-protection-remover
Enhanced with Termux support, improved visuals, and robust file handling
"""
import os
import sys
import shutil
import re
import subprocess
import glob
import platform
from pathlib import Path
import time
import zipfile
import urllib.request
import threading
import itertools
from multiprocessing import Pool

# Auto-install required packages
def install_dependencies():
    """Install required dependencies if not present"""
    try:
        required_packages = ['colorama', 'tqdm']
        try:
            import pip
        except ImportError:
            print("Installing pip...")
            if platform.system() == "Windows":
                subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], 
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                try:
                    print("Downloading get-pip.py...")
                    urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")
                    subprocess.run([sys.executable, "get-pip.py", "--user"], 
                                  check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    os.remove("get-pip.py")
                except Exception as e:
                    print(f"Failed to install pip: {e}")
                    print("Please install pip manually and try again.")
                    sys.exit(1)
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                print(f"Installing {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", "--user", package], 
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Dependencies installed successfully. Restarting script...")
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

try:
    from colorama import init, Fore, Style
    from tqdm import tqdm
except ImportError:
    install_dependencies()

# Initialize colorama
init(autoreset=True)

class Logger:
    """Beautiful logger for terminal output"""
    def __init__(self):
        self.progress_bars = {}
    
    def info(self, message):
        """Print info message"""
        print(f"{Fore.BLUE}[i]{Style.RESET_ALL} {message}")
    
    def success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} {message}")
    
    def error(self, message):
        """Print error message"""
        print(f"{Fore.RED}[✗]{Style.RESET_ALL} {message}")
    
    def warning(self, message):
        """Print warning message"""
        print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {message}")
    
    def header(self, message):
        """Print header message"""
        print(f"\n{Style.BRIGHT}{Fore.CYAN}▶ {message}{Style.RESET_ALL}")
    
    def subheader(self, message):
        """Print subheader message"""
        print(f"{Fore.CYAN}  ➤ {message}{Style.RESET_ALL}")
    
    def create_progress_bar(self, name, total, desc="Processing"):
        """Create a new progress bar with enhanced visuals"""
        self.progress_bars[name] = tqdm(total=total, 
                                        desc=f"{Fore.CYAN}{desc}{Style.RESET_ALL}",
                                        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                                        colour='cyan',
                                        dynamic_ncols=True)
        return self.progress_bars[name]
    
    def update_progress(self, name, amount=1):
        """Update progress bar by name"""
        if name in self.progress_bars:
            self.progress_bars[name].update(amount)
    
    def close_progress(self, name):
        """Close progress bar by name"""
        if name in self.progress_bars:
            self.progress_bars[name].close()
            del self.progress_bars[name]

log = Logger()

def show_spinner(stop_event, message="LOADING"):
    """Show a colorful spinner animation with bird characters"""
    birds = itertools.cycle(["𓅰", "𓅬", "𓅭", "𓅮"])
    colors = itertools.cycle([Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.BLUE, Fore.WHITE])
    term_width = shutil.get_terminal_size().columns
    
    while not stop_event.is_set():
        bird = next(birds)
        color = next(colors)
        sys.stdout.write(f'\r{" " * term_width}\r{message}... {color}{bird}{Style.RESET_ALL}')
        sys.stdout.flush()
        time.sleep(0.2)
    
    sys.stdout.write(f'\r{" " * term_width}\r{Fore.GREEN}✔ Completed{Style.RESET_ALL}\n')
    sys.stdout.flush()

def run_with_spinner(cmd, verbose=True, exit_on_error=True, spinner_message="Processing"):
    """Run a command with a context-specific spinner"""
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_event, spinner_message))
    spinner_thread.start()
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        stop_event.set()
        spinner_thread.join()
        
        if result.returncode != 0 and exit_on_error:
            if verbose:
                log.error(f"Error executing command: {cmd}\n{result.stderr}")
            sys.exit(1)
        return result.stdout.strip()
    except Exception as e:
        stop_event.set()
        spinner_thread.join()
        if verbose:
            log.error(f"Error executing command: {cmd}\n{str(e)}")
        if exit_on_error:
            sys.exit(1)
        raise

def run_command(command, verbose=False, exit_on_error=True):
    """Run a shell command and return output with spinner"""
    return run_with_spinner(command, verbose, exit_on_error, spinner_message="Processing")

def extract_file(zipfile, target=None):
    """Extract file from zip archive using platform-appropriate method"""
    try:
        if platform.system() == "Windows":
            if shutil.which("7z"):
                run_command(f'7z e "{zipfile}" {target or ""} -y -o.', verbose=False)
            else:
                with zipfile.ZipFile(zipfile, 'r') as zip_ref:
                    if target:
                        zip_ref.extract(target)
                    else:
                        zip_ref.extractall()
        else:
            if shutil.which("unzip"):
                result = run_command(f'unzip -o "{zipfile}" {target or ""}', verbose=False, exit_on_error=False)
                log.info(f"Unzip result: {result}")
                if not os.path.exists(target or ''):
                    log.error(f"Extracted file not found after unzip")
            else:
                with zipfile.ZipFile(zipfile, 'r') as zip_ref:
                    if target:
                        zip_ref.extract(target)
                    else:
                        zip_ref.extractall()
        return True
    except Exception as e:
        log.error(f"Failed to extract {target or 'files'} from {zipfile}: {e}")
        return False

def delete_dir_crossplatform(path):
    """Delete directory or file cross-platform"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
        elif os.path.isdir(path):
            if platform.system() == "Windows":
                os.system(f'rmdir /s /q "{path}" > nul 2>&1')
            else:
                os.system(f'rm -rf "{path}" > /dev/null 2>&1')
            return True
        return False
    except Exception as e:
        log.warning(f"Failed to delete {path}: {e}")
        return False

def is_termux():
    """Check if running in a Termux environment"""
    return os.path.exists("/data/data/com.termux") or "TERMUX" in os.environ

def setup_termux_workdir():
    """Create and prepare a Termux working directory"""
    termux_dir = os.path.expanduser("~/apk_work")
    if not os.path.exists(termux_dir):
        os.makedirs(termux_dir)
    
    # Clean all files and directories in ~/apk_work to start fresh
    cleanup_count = 0
    for item in os.listdir(termux_dir):
        item_path = os.path.join(termux_dir, item)
        try:
            if os.path.isfile(item_path):
                os.unlink(item_path)
                cleanup_count += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path, ignore_errors=True)
                cleanup_count += 1
            log.info(f"Deleted during setup: {item}")
        except Exception as e:
            log.warning(f"Failed to delete {item_path} during setup: {e}")
    
    if cleanup_count > 0:
        log.info(f"Cleaned {cleanup_count} items from Termux working directory")
    return termux_dir

def copy_to_termux(src_path, dest_dir):
    """Copy files to Termux working directory"""
    try:
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Source file not found: {src_path}")
            
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        if os.path.exists(dest_path):
            os.remove(dest_path)
        
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path)
        else:
            shutil.copy2(src_path, dest_path)
        return dest_path
    except Exception as e:
        raise RuntimeError(f"Error copying to Termux workdir: {str(e)}")

def move_result_back(termux_path, original_dir):
    """Move the final result back to the original directory"""
    try:
        if not os.path.exists(termux_path):
            raise FileNotFoundError(f"Termux output not found: {termux_path}")
            
        final_name = os.path.basename(termux_path)
        final_path = os.path.join(original_dir, final_name)
        
        if os.path.exists(final_path):
            os.remove(final_path)
            
        shutil.move(termux_path, original_dir)
        return final_path
    except Exception as e:
        raise RuntimeError(f"Error moving result back: {str(e)}")

def process_xml_file(xml_path):
    """Process an XML file (validate or transform)"""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '<' not in content or '>' not in content:
            return False
        return True
    except Exception as e:
        log.warning(f"Error processing {xml_path}: {e}")
        return False

def patch_files():
    """Apply patches to the decompiled files"""
    base_dir = os.path.expanduser('merged_app_decompile_xml')
    smali_base_dir = os.path.join(base_dir, 'smali')
    base_lib_dir = os.path.join(base_dir, 'root/lib')
    resources_dir = os.path.join(base_dir, 'resources')
    cwd = os.getcwdb().decode('utf-8')
    
    log.header("Applying patches to decompiled files")

    # Verify architectures in the APK
    log.subheader("Verifying native library architectures...")
    architectures = []
    try:
        with zipfile.ZipFile("merged_app.apk", 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.startswith("lib/") and file.endswith("libpairipcore.so"):
                    arch = file.split("/")[1]
                    architectures.append(arch)
        if architectures:
            log.success(f"Found architectures: {', '.join(architectures)}")
        else:
            log.warning("No native libraries found in APK")
    except Exception as e:
        log.warning(f"Could not verify architectures: {e}")

    # Smali patching definitions
    new_clinit_block = [
        ".method static constructor <clinit>()V",
        "    .registers 1",
        "",
        "    .line 30",
        "    const-string v0, \"pairipcorex\"",
        "    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V",
        "",
        "    const-string v0, \"pairipcore\"",
        "    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V",
        "",
        "    return-void",
        ".end method"
    ]

    new_verify_signature_block = [
        ".method static verifySignatureMatches(Ljava/lang/String;)Z",
        "    .registers 1",
        "",
        "    const/4 p0, 0x1",
        "    return p0",
        ".end method"
    ]

    new_initialize_license_block = [
        ".method public initializeLicenseCheck()V",
        "    .registers 1",
        "    return-void",
        ".end method"
    ]

    new_connect_license_block = [
        ".method private connectToLicensingService()V",
        "    .registers 1",
        "    return-void",
        ".end method"
    ]

    # Apply Smali patches
    log.subheader("Patching protection code...")
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_event, "Patching Smali"))
    spinner_thread.start()

    vmrunner_patched = False
    sigcheck_patched = False
    verify_signature_patched = False
    initialize_license_patched = False
    connect_license_patched = False
    
    smali_dirs = [d for d in os.listdir(smali_base_dir) if d.startswith('classes') and os.path.isdir(os.path.join(smali_base_dir, d))]
    
    if not smali_dirs:
        stop_event.set()
        spinner_thread.join()
        log.warning("No smali/classes* directories found, skipping Smali patching")
    else:
        for smali_dir in smali_dirs:
            pairip_dir = os.path.join(smali_base_dir, smali_dir, 'com/pairip')
            if not os.path.exists(pairip_dir):
                continue

            for root, dirs, files in os.walk(pairip_dir):
                if 'VMRunner.smali' in files:
                    vmrunner_path = os.path.join(root, 'VMRunner.smali')
                    try:
                        with open(vmrunner_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()

                        new_lines = []
                        inside_clinit = False
                        method_start_found = False

                        for line in lines:
                            if not inside_clinit and line.strip().startswith('.method') and '<clinit>()V' in line:
                                inside_clinit = True
                                method_start_found = True
                                new_lines.extend(line + '\n' for line in new_clinit_block)
                                continue

                            if inside_clinit:
                                if line.strip() == '.end method':
                                    inside_clinit = False
                                continue

                            new_lines.append(line)

                        if method_start_found:
                            with open(vmrunner_path, 'w', encoding='utf-8') as f:
                                f.writelines(new_lines)
                            vmrunner_patched = True
                    except Exception as e:
                        log.error(f"Failed to patch VMRunner.smali: {e}")

                if 'SignatureCheck.smali' in files or 'LicenseClient.smali' in files:
                    smali_file = 'LicenseClient.smali' if 'LicenseClient.smali' in files else 'SignatureCheck.smali'
                    sig_path = os.path.join(root, smali_file)
                    try:
                        with open(sig_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()

                        new_lines = []
                        inside_verify = False
                        inside_verify_signature = False
                        inside_initialize_license = False
                        inside_connect_license = False
                        verify_method_found = False
                        verify_signature_method_found = False
                        initialize_license_method_found = False
                        connect_license_method_found = False

                        i = 0
                        while i < len(lines):
                            stripped = lines[i].strip()

                            if not inside_verify and stripped.startswith('.method') and 'verifyIntegrity(Landroid/content/Context;)V' in stripped:
                                inside_verify = True
                                verify_method_found = True
                                new_lines.append(lines[i])
                                i += 1
                                new_lines.append('    .registers 1\n')
                                new_lines.append('    return-void\n')
                                new_lines.append('.end method\n')
                                while i < len(lines) and not lines[i].strip().startswith('.end method'):
                                    i += 1
                                i += 1
                                continue

                            if not inside_verify_signature and stripped.startswith('.method') and 'verifySignatureMatches(Ljava/lang/String;)Z' in stripped:
                                inside_verify_signature = True
                                verify_signature_method_found = True
                                new_lines.extend(line + '\n' for line in new_verify_signature_block)
                                while i < len(lines) and not lines[i].strip().startswith('.end method'):
                                    i += 1
                                i += 1
                                continue

                            if not inside_initialize_license and stripped.startswith('.method') and 'initializeLicenseCheck()V' in stripped:
                                inside_initialize_license = True
                                initialize_license_method_found = True
                                new_lines.extend(line + '\n' for line in new_initialize_license_block)
                                while i < len(lines) and not lines[i].strip().startswith('.end method'):
                                    i += 1
                                i += 1
                                continue

                            if not inside_connect_license and stripped.startswith('.method') and 'connectToLicensingService()V' in stripped:
                                inside_connect_license = True
                                connect_license_method_found = True
                                new_lines.extend(line + '\n' for line in new_connect_license_block)
                                while i < len(lines) and not lines[i].strip().startswith('.end method'):
                                    i += 1
                                i += 1
                                continue

                            new_lines.append(lines[i])
                            i += 1

                        if verify_method_found or verify_signature_method_found or initialize_license_method_found or connect_license_method_found:
                            with open(sig_path, 'w', encoding='utf-8') as f:
                                f.writelines(new_lines)
                            if verify_method_found:
                                sigcheck_patched = True
                            if verify_signature_method_found:
                                verify_signature_patched = True
                            if initialize_license_method_found:
                                initialize_license_patched = True
                            if connect_license_method_found:
                                connect_license_patched = True
                    except Exception as e:
                        log.error(f"Failed to patch {smali_file}: {e}")

        stop_event.set()
        spinner_thread.join()

        if vmrunner_patched:
            log.success("Patched VMRunner.smali")
        if sigcheck_patched:
            log.success("Patched verifyIntegrity")
        if verify_signature_patched:
            log.success("Patched verifySignatureMatches")
        if initialize_license_patched:
            log.success("Patched initializeLicenseCheck")
        if connect_license_patched:
            log.success("Patched connectToLicensingService")
        if not (vmrunner_patched or sigcheck_patched or verify_signature_patched or initialize_license_patched or connect_license_patched):
            log.warning("No Smali files patched")

# Copy .so Files
    log.subheader("Copying native libraries...")
    so_files_to_copy = [
        'libpairipcorex.so',
        'libFirebaseCppApp.so'
    ]

    # Use the current working directory (~/apk_work in Termux)
    current_dir = os.getcwd()
    log.info(f"Checking for .so files in working directory: {current_dir}")
    
    missing = [f for f in so_files_to_copy if not os.path.exists(os.path.join(current_dir, f))]
    if missing:
        log.error(f"Missing .so files in working directory ({current_dir}): {', '.join(missing)}")
        sys.exit(1)
    
    supported_archs = ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64']
    lib_dirs_found = 0
    arch_types = []
    for root, dirs, files in os.walk(base_lib_dir):
        if 'libpairipcore.so' in files:
            arch_type = os.path.basename(root)
            if arch_type in architectures and arch_type in supported_archs:
                arch_types.append(arch_type)
                lib_dirs_found += 1
                for so_file in so_files_to_copy:
                    src_path = os.path.join(current_dir, so_file)
                    dst_path = os.path.join(root, so_file)
                    try:
                        shutil.copy2(src_path, dst_path)
                        log.success(f'Copied {so_file} to {arch_type} architecture')
                    except Exception as e:
                        log.error(f"Failed to copy {so_file} to {arch_type}: {e}")
                        sys.exit(1)
            else:
                log.warning(f"Skipping incompatible architecture: {arch_type}")
    
    if lib_dirs_found == 0:
        log.warning("No library directories found containing libpairipcore.so")
    else:
        log.success(f"Libraries copied to {lib_dirs_found} architecture(s): {', '.join(arch_types)}")
        
    # Patch file_paths.xml
    log.subheader("Patching file paths configuration...")
    file_paths_patched = False
    pattern = re.compile(
        r'<external-path\s+name="[^"]*"\s+path="Android/data/[^"]*/files/Pictures"\s*/>',
        re.IGNORECASE
    )
    replacement = '<external-files-path name="my_images" path="Pictures/" />'

    for root, dirs, files in os.walk(resources_dir):
        if 'file_paths.xml' in files and 'res/xml' in root:
            xml_path = os.path.join(root, 'file_paths.xml')
            try:
                with open(xml_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if pattern.search(content):
                    content_new = pattern.sub(replacement, content)
                    with open(xml_path, 'w', encoding='utf-8') as f:
                        f.write(content_new)
                    file_paths_patched = True
                    log.success("Patched file_paths.xml")
            except Exception as e:
                log.error(f"Failed to patch {xml_path}: {e}")

    if not file_paths_patched:
        log.warning("No matching <external-path> entries found")

    return vmrunner_patched or sigcheck_patched or verify_signature_patched or initialize_license_patched or connect_license_patched or file_paths_patched

def process_apk(apks_file, so_path=None):
    """Process an APKS file with Termux optimization"""
    original_dir = os.path.dirname(os.path.abspath(apks_file))
    work_dir = original_dir
    termux_files = {}

    required_jars = ["APKEditor-1.4.3.jar", "uber-apk-signer.jar"]
    for jar in required_jars:
        if not os.path.exists(os.path.join(original_dir, jar)):
            log.error(f"Required JAR file '{jar}' not found")
            sys.exit(1)

    if is_termux():
        log.header("Preparing Termux environment...")
        work_dir = setup_termux_workdir()
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=show_spinner, args=(stop_event, "Setting up Termux"))
        spinner_thread.start()

        try:
            termux_files = {
                "apks": copy_to_termux(apks_file, work_dir),
                "apkeditor": copy_to_termux(os.path.join(original_dir, "APKEditor-1.4.3.jar"), work_dir),
                "signer": copy_to_termux(os.path.join(original_dir, "uber-apk-signer.jar"), work_dir)
            }

            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            # Only check for libpairipcorex.so, as libFirebaseCppApp.so is generated later
            required_libs = ["libpairipcorex.so"]
            for lib in required_libs:
                lib_path = None
                if so_path and os.path.exists(os.path.join(so_path, lib)):
                    lib_path = os.path.join(so_path, lib)
                elif os.path.exists(os.path.join(original_dir, lib)):
                    lib_path = os.path.join(original_dir, lib)
                elif os.path.exists(os.path.join(script_dir, lib)):
                    lib_path = os.path.join(script_dir, lib)

                if lib_path:
                    copy_to_termux(lib_path, work_dir)
                    log.success(f"Copied {lib} to Termux working directory")
                else:
                    log.error(f"Library not found: {lib}")
                    stop_event.set()
                    spinner_thread.join()
                    sys.exit(1)
        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            log.error(f"Error preparing Termux environment: {e}")
            sys.exit(1)
        stop_event.set()
        spinner_thread.join()

    os.chdir(work_dir)
    
    base_name = os.path.basename(apks_file).rsplit('.', 1)[0]
    decompile_dir = os.path.expanduser("merged_app_decompile_xml")
    
    if "_JAVA_OPTIONS" not in os.environ:
        os.environ["_JAVA_OPTIONS"] = os.environ.get("_JAVA_OPTIONS", "") + " -Xmx2g"
    
    total_steps = 11
    progress = log.create_progress_bar("main", total_steps, "Patching process")
    
    # Step 1: Extract base.apk
    start_time = time.time()
    log.header("Step 1/11: Extracting base.apk")
    success = extract_file(termux_files.get("apks", apks_file), "base.apk")
    if not success:
        log.error("Failed to extract base.apk")
        sys.exit(1)
    log.success(f"Extracted base.apk in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 2: Create libFirebaseCppApp.so
    start_time = time.time()
    log.header("Step 2/11: Creating libFirebaseCppApp.so")
    if not os.path.exists("libFirebaseCppApp.so"):
        if os.path.exists("base.apk"):
            shutil.copy("base.apk", "libFirebaseCppApp.so")
            log.success("Created libFirebaseCppApp.so from base.apk")
        else:
            log.error("base.apk not found to create libFirebaseCppApp.so")
            sys.exit(1)
    else:
        log.success("libFirebaseCppApp.so already exists")
    log.success(f"Completed in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 3: Remove old files
    start_time = time.time()
    log.header("Step 3/11: Cleaning previous files")
    cleaned = 0
    if os.path.exists("merged_app.apk"):
        os.remove("merged_app.apk")
        cleaned += 1
    if os.path.exists(decompile_dir):
        delete_dir_crossplatform(decompile_dir)
        cleaned += 1
    log.success(f"Removed {cleaned} old files/directories in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 2: Create libFirebaseCppApp.so
    start_time = time.time()
    log.header("Step 2/11: Creating libFirebaseCppApp.so")
    if not os.path.exists("libFirebaseCppApp.so"):
        if os.path.exists("base.apk"):
            shutil.copy("base.apk", "libFirebaseCppApp.so")
            log.success("Created libFirebaseCppApp.so from base.apk")
        else:
            log.error("base.apk not found to create libFirebaseCppApp.so")
            sys.exit(1)
    else:
        log.success("libFirebaseCppApp.so already exists")
    log.success(f"Completed in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 3: Remove old files
    start_time = time.time()
    log.header("Step 3/11: Cleaning previous files")
    cleaned = 0
    if os.path.exists("merged_app.apk"):
        os.remove("merged_app.apk")
        cleaned += 1
    if os.path.exists(decompile_dir):
        delete_dir_crossplatform(decompile_dir)
        cleaned += 1
    log.success(f"Removed {cleaned} old files/directories in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 4: Merge APKS to APK
    start_time = time.time()
    log.header("Step 4/11: Merging APKS to APK")
    run_with_spinner(
        f'java -jar APKEditor-1.4.3.jar m -i "{termux_files.get("apks", apks_file)}" -o merged_app.apk -extractNativeLibs true',
        verbose=False,
        spinner_message="Merging APKS"
    )
    if os.path.exists("merged_app.apk"):
        merged_size = os.path.getsize("merged_app.apk") / (1024 * 1024)
        log.success(f"Successfully merged to APK (Size: {merged_size:.2f} MB) in {time.time() - start_time:.1f} seconds")
    else:
        log.error("Failed to merge APKS to APK")
        sys.exit(1)
    progress.update(1)
    
    # Step 5: Prepare decompilation
    start_time = time.time()
    log.header("Step 5/11: Preparing decompilation")
    if os.path.exists(decompile_dir):
        log.info("Removing existing decompiled directory")
        shutil.rmtree(decompile_dir, ignore_errors=True)
    log.success(f"Completed in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 6: Decompile the merged APK
    start_time = time.time()
    log.header("Step 6/11: Decompiling merged APK")
    run_with_spinner(
        "java -jar APKEditor-1.4.3.jar d -i merged_app.apk",
        verbose=False,
        spinner_message="Decompiling APK"
    )
    if os.path.exists(decompile_dir):
        log.success(f"Decompilation completed in {time.time() - start_time:.1f} seconds")
    else:
        log.error("Decompilation failed")
        sys.exit(1)
    progress.update(1)
    
    # Step 7: Modify AndroidManifest.xml
    start_time = time.time()
    log.header("Step 7/11: Modifying AndroidManifest.xml")
    manifest_path = os.path.join(decompile_dir, "AndroidManifest.xml")
    entries_removed = 0
    permissions_removed = 0
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove license check entries
        pattern1 = r'<activity[^>]+com\.pairip\.licensecheck\.LicenseActivity[^<]+/>'
        pattern2 = r'<provider[^>]+com\.pairip\.licensecheck\.LicenseContentProvider[^<]+/>'
        for pattern in [pattern1, pattern2]:
            matches = re.findall(pattern, content, flags=re.DOTALL)
            entries_removed += len(matches)
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Remove CHECK_LICENSE permission
        permission_pattern = r'<uses-permission[^>]+android:name="com\.android\.vending\.CHECK_LICENSE"[^<]*/>'
        matches = re.findall(permission_pattern, content, flags=re.DOTALL)
        permissions_removed = len(matches)
        content = re.sub(permission_pattern, '', content, flags=re.DOTALL)
        
        if entries_removed > 0 or permissions_removed > 0:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if entries_removed > 0:
                log.success(f"Removed {entries_removed} license check entries")
            if permissions_removed > 0:
                log.success(f"Removed CHECK_LICENSE permission")
        else:
            log.warning("No license check entries or CHECK_LICENSE permission found")
    else:
        log.warning("AndroidManifest.xml not found")
    log.success(f"Completed in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 8: Patch files
    start_time = time.time()
    log.header("Step 8/11: Patching decompiled files")
    patch_result = patch_files()
    if not patch_result:
        log.warning("No files were patched")
    log.success(f"Completed in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 9: Preprocess XML files in parallel
    start_time = time.time()
    log.header("Step 9/11: Preprocessing XML files in parallel")
    xml_files = []
    for root, _, files in os.walk(os.path.join(decompile_dir, 'resources')):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    
    if xml_files:
        with Pool() as pool:
            results = pool.map(process_xml_file, xml_files)
        if all(results):
            log.success("All XML files preprocessed successfully")
        else:
            log.warning("Some XML files failed to preprocess")
    else:
        log.info("No XML files found for preprocessing")
    log.success(f"Completed in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Step 10: Build APK
    start_time = time.time()
    log.header("Step 10/11: Building modified APK")
    if os.path.exists("out.apk"):
        os.remove("out.apk")
    
    run_with_spinner(
        f'java -jar APKEditor-1.4.3.jar b -i "{decompile_dir}" -o out.apk',
        verbose=False,
        spinner_message="Building APK"
    )
    if os.path.exists("out.apk"):
        out_size = os.path.getsize("out.apk") / (1024 * 1024)
        log.success(f"Build completed in {time.time() - start_time:.1f} seconds (Size: {out_size:.2f} MB)")
    else:
        log.error("Failed to build modified APK")
        sys.exit(1)
    progress.update(1)
    
    # Step 11: Sign the APK
    start_time = time.time()
    log.header("Step 11/11: Signing the APK")
    run_with_spinner(
        "java -jar uber-apk-signer.jar -a out.apk --overwrite",
        verbose=False,
        spinner_message="Signing APK"
    )
    
    signed_apk_patterns = [
        "out-aligned-signed.apk",
        "out-signed.apk",
        "out-debugSigned.apk",
        "out-aligned-debugSigned.apk"
    ]
    
    signed_apk = None
    for pattern in signed_apk_patterns:
        if os.path.exists(pattern):
            signed_apk = pattern
            break
    
    output_name = f"{base_name}-patched.apk"
    
    if signed_apk:
        shutil.move(signed_apk, output_name)
        sign_size = os.path.getsize(output_name) / (1024 * 1024)
        log.success(f"APK signed successfully (Size: {sign_size:.2f} MB)")
    else:
        if os.path.exists("out.apk"):
            shutil.move("out.apk", output_name)
            log.warning(f"Signing failed. Using unsigned APK: {output_name}")
        else:
            log.error("Error: No output APK found")
            sys.exit(1)
    log.success(f"Completed in {time.time() - start_time:.1f} seconds")
    progress.update(1)
    
    # Move result back if Termux
    if is_termux():
        try:
            final_output = move_result_back(os.path.join(work_dir, output_name), original_dir)
            log.success(f"Final APK moved to: {final_output}")
            output_name = final_output
        except Exception as e:
            log.error(f"Failed to move final APK: {e}")
            sys.exit(1)
    
    # Clean up temporary files
    start_time = time.time()
    log.subheader("Cleaning up temporary files...")
    cleanup_files = 0
    for tmp_file in glob.glob("*.tmp*"):
        try:
            os.remove(tmp_file)
            cleanup_files += 1
        except Exception:
            pass
    
    for tmp_dir in glob.glob("tmp-*"):
        if os.path.isdir(tmp_dir):
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                cleanup_files += 1
            except Exception:
                pass
    
    log.success(f"Removed {cleanup_files} temporary files/directories in {time.time() - start_time:.1f} seconds")
    
    log.close_progress("main")
    return output_name

def center_text(text, width):
    """Center text for display"""
    return text.center(width)

def main():
    """Main function"""
    width = shutil.get_terminal_size().columns
    border = "▓" * width

    line1 = center_text("PairIP Protection Remover v1.3 (Termux Optimized)", width)
    line2 = center_text("Cross-platform Edition", width)
    footer = center_text("© void.eth | Modified for Termux by Zalgo", width)

    print(f"\n{Style.BRIGHT}{Fore.CYAN}{border}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{line1}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{line2}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{border}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{footer}{Style.RESET_ALL}\n")
    
    apks_file = None
    so_path = None
    if len(sys.argv) == 3:
        apks_file = sys.argv[1]
        so_path = sys.argv[2]
    elif len(sys.argv) == 2:
        apks_file = sys.argv[1]
    else:
        apks_files = glob.glob("*.apks")
        if not apks_files:
            log.error("No .apks files found in the current directory")
            sys.exit(1)
        elif len(apks_files) > 1:
            log.warning(f"Multiple .apks files found: {', '.join(apks_files)}")
            log.info(f"Selecting the first one: {apks_files[0]}")
        apks_file = apks_files[0]

    if not os.path.exists(apks_file):
        log.error(f"Input file '{apks_file}' not found")
        sys.exit(1)
    
    try:
        with zipfile.ZipFile(apks_file, 'r') as zip_ref:
            zip_ref.testzip()
        log.success(f"Input file '{apks_file}' is a valid ZIP archive")
    except zipfile.BadZipFile:
        log.error(f"Input file '{apks_file}' is not a valid .apks file")
        sys.exit(1)
    
    if not apks_file.endswith('.apks'):
        log.warning(f"Input file doesn't have .apks extension")
    
    log.info("Checking Java installation...")
    try:
        java_version = run_command("java -version", verbose=False, exit_on_error=False)
        if not java_version:
            java_version = run_command("java -version 2>&1", verbose=False, exit_on_error=False)
        log.success("Java detected")
    except Exception:
        log.error("Java not found. Please install Java Runtime Environment")
        sys.exit(1)
    
    work_dir = os.path.dirname(os.path.abspath(apks_file))
    os.chdir(work_dir)
    
    log.info(f"Processing file: {os.path.basename(apks_file)}")
    start_time = time.time()
    out_name = process_apk(apks_file, so_path)
    total_time = time.time() - start_time
    
    log.header("Finalizing...")
    leftovers = [
        "base.apk", "merged_app.apk", "out.apk", 
        "out-aligned-debugSigned.apk", "out-aligned-signed.apk", 
        "out-debugSigned.apk", "out-signed.apk", "merged_app_decompile_xml"
    ]
    
    cleanup_count = 0
    for file in leftovers:
        if os.path.exists(file):
            try:
                delete_dir_crossplatform(file)
                cleanup_count += 1
                if file == "merged_app_decompile_xml":
                    log.success(f"Deleted temporary directory: {file}")
                else:
                    log.info(f"Deleted temporary file: {file}")
            except Exception as e:
                log.warning(f"Failed to delete {file}: {e}")
    
    # Clean up additional temporary files and directories
    for tmp_file in glob.glob("*.tmp*"):
        try:
            os.remove(tmp_file)
            cleanup_count += 1
            log.info(f"Deleted temporary file: {tmp_file}")
        except Exception as e:
            log.warning(f"Failed to remove {tmp_file}: {e}")
    
    for tmp_dir in glob.glob("tmp-*"):
        if os.path.isdir(tmp_dir):
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                cleanup_count += 1
                log.info(f"Deleted temporary directory: {tmp_dir}")
            except Exception as e:
                log.warning(f"Failed to remove {tmp_dir}: {e}")
    
    # Clean up Termux working directory (~/apk_work)
    termux_dir = os.path.expanduser("~/apk_work")
    termux_cleanup_count = 0
    if is_termux():
        log.info(f"Starting cleanup of Termux working directory: {termux_dir}")
        if os.path.exists(termux_dir):
            # First attempt: delete individual items
            for item in os.listdir(termux_dir):
                item_path = os.path.join(termux_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                        termux_cleanup_count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                        termux_cleanup_count += 1
                    log.success(f"Deleted from Termux working directory: {item}")
                except Exception as e:
                    log.warning(f"Failed to delete {item_path} from Termux working directory: {e}")
            if termux_cleanup_count > 0:
                log.success(f"Cleared {termux_cleanup_count} items from Termux working directory")
            # Second attempt: forcefully remove the directory
            try:
                shutil.rmtree(termux_dir, ignore_errors=True)
                if not os.path.exists(termux_dir):
                    log.success("Deleted Termux working directory: ~/apk_work")
                else:
                    log.warning("Termux working directory still exists after cleanup attempt")
            except Exception as e:
                log.warning(f"Failed to delete Termux working directory {termux_dir}: {e}")
        else:
            log.info("Termux working directory does not exist, no cleanup needed")
    else:
        log.info("Not running in Termux, skipping ~/apk_work cleanup")
    
    if cleanup_count > 0 or termux_cleanup_count > 0:
        log.success(f"Removed {cleanup_count + termux_cleanup_count} temporary files/directories")
    else:
        log.info("No temporary files or directories to remove")
    
    if out_name:
        output_path = os.path.abspath(out_name)
        output_size = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"\n{Style.BRIGHT}{Fore.GREEN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Style.BRIGHT}{Fore.GREEN}║              PROCESS COMPLETE                ║{Style.RESET_ALL}")
        print(f"{Style.BRIGHT}{Fore.GREEN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}✓ Final APK: {Style.BRIGHT}{out_name}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Size: {output_size:.2f} MB{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Location: {output_path}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Total processing time: {total_time:.1f} seconds{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Temporary directories and files, including merged_app_decompile_xml and ~/apk_work, have been cleared{Style.RESET_ALL}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Process cancelled by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
        sys.exit(1)