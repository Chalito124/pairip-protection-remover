#!/usr/bin/env python3
"""
PairIP Protection Remover - Termux Optimized v1.2
Versión completa con soporte mejorado para librerías nativas
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

# ==============================================
# CONFIGURACIÓN INICIAL Y DEPENDENCIAS
# ==============================================

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
                    urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")
                    subprocess.run([sys.executable, "get-pip.py", "--user"], 
                                  check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    os.remove("get-pip.py")
                except Exception as e:
                    print(f"Failed to install pip: {e}")
                    sys.exit(1)
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                print(f"Installing {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", "--user", package], 
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Dependencies installed. Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

try:
    from colorama import init, Fore, Back, Style
    from tqdm import tqdm
except ImportError:
    install_dependencies()

init(autoreset=True)

# ==============================================
# CLASE LOGGER (SIN CAMBIOS)
# ==============================================

class Logger:
    def __init__(self):
        self.progress_bars = {}
    
    def info(self, message):
        print(f"{Fore.BLUE}[i]{Style.RESET_ALL} {message}")
    
    def success(self, message):
        print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} {message}")
    
    def error(self, message):
        print(f"{Fore.RED}[✗]{Style.RESET_ALL} {message}")
    
    def warning(self, message):
        print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {message}")
    
    def header(self, message):
        print(f"\n{Style.BRIGHT}{Fore.CYAN}▶ {message}{Style.RESET_ALL}")
    
    def subheader(self, message):
        print(f"{Fore.CYAN}  ➤ {message}{Style.RESET_ALL}")
    
    def create_progress_bar(self, name, total, desc="Processing"):
        self.progress_bars[name] = tqdm(total=total, desc=f"{Fore.CYAN}{desc}{Style.RESET_ALL}", 
                                       bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}")
        return self.progress_bars[name]
    
    def update_progress(self, name, amount=1):
        if name in self.progress_bars:
            self.progress_bars[name].update(amount)
    
    def close_progress(self, name):
        if name in self.progress_bars:
            self.progress_bars[name].close()
            del self.progress_bars[name]

log = Logger()

# ==============================================
# FUNCIONES AUXILIARES (CON MEJORAS)
# ==============================================

def show_spinner(stop_event):
    birds = itertools.cycle(["𓅰", "𓅬", "𓅭", "𓅮", "𓅯"])
    colors = itertools.cycle([Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.BLUE, Fore.WHITE])
    
    while not stop_event.is_set():
        bird = next(birds)
        color = next(colors)
        sys.stdout.write(f'\r{color}Cargando... {Fore.CYAN}{bird}{Style.RESET_ALL}')
        sys.stdout.flush()
        time.sleep(0.3)

    for i in range(4):
        sys.stdout.write(f'\r{Fore.GREEN}✔ Completado' + '.' * i + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write('\n')

def run_command(command, verbose=False, exit_on_error=True):
    if verbose:
        log.info(f"Running: {command}")
    
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_event,))
    spinner_thread.start()
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        stop_event.set()
        spinner_thread.join()
        if result.returncode != 0:
            log.error(f"Command failed with error code {result.returncode}")
            if verbose:
                log.error(f"STDERR: {result.stderr}")
            if exit_on_error:
                sys.exit(1)
        return result.stdout.strip()
    except Exception as e:
        stop_event.set()
        spinner_thread.join()
        log.error(f"Exception while executing command: {e}")
        if exit_on_error:
            sys.exit(1)
        return ""

def extract_file(zipfile, target=None):
    try:
        if platform.system() == "Windows":
            if shutil.which("7z"):
                run_command(f'7z e "{zipfile}" {target or ""} -y -o.', verbose=False)
            else:
                import zipfile as zf
                with zf.ZipFile(zipfile, 'r') as zip_ref:
                    if target:
                        zip_ref.extract(target)
                    else:
                        zip_ref.extractall()
        else:
            if shutil.which("unzip"):
                result = run_command(f'unzip -o "{zipfile}" {target or ""}', verbose=False, exit_on_error=False)
                if not os.path.exists(target or ''):
                    log.error(f"Extracted file not found after unzip")
            else:
                import zipfile as zf
                with zf.ZipFile(zipfile, 'r') as zip_ref:
                    if target:
                        zip_ref.extract(target)
                    else:
                        zip_ref.extractall()
        return True
    except Exception as e:
        log.error(f"Failed to extract {target or 'files'} from {zipfile}: {e}")
        return False

def delete_dir_crossplatform(path):
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

def setup_termux_workdir():
    """Crea y prepara el directorio de trabajo rápido en Termux"""
    termux_dir = os.path.expanduser("~/apk_work")
    if not os.path.exists(termux_dir):
        os.makedirs(termux_dir)
    
    # Limpiar trabajos anteriores (excepto librerías necesarias)
    keep_files = {'libpairipcorex.so', 'libFirebaseCppApp.so'}
    for item in os.listdir(termux_dir):
        if item not in keep_files:
            item_path = os.path.join(termux_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
            except Exception:
                pass
    return termux_dir

def copy_to_termux(src_path, dest_dir):
    """Copia archivos al directorio rápido de Termux"""
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
    """Mueve el resultado final al directorio original del usuario"""
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

# ==============================================
# FUNCIÓN DE PARCHES MEJORADA
# ==============================================

def patch_files(base_dir):
    """Apply patches to the decompiled files"""
    base_lib_dir = os.path.join(base_dir, 'root/lib')
    resources_dir = os.path.join(base_dir, 'resources')
    cwd = os.getcwd()
    
    log.header("Applying patches to decompiled files")

    # --- Replacement for VMRunner.clinit()
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

    # --- Patch Smali Files ---
    log.subheader("Patching protection code...")
    vmrunner_patched = False
    sigcheck_patched = False
    
    for root, dirs, files in os.walk(base_dir):
        # --- Patch VMRunner.smali ---
        if os.path.basename(root) == 'pairip' and 'VMRunner.smali' in files:
            vmrunner_path = os.path.join(root, 'VMRunner.smali')
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
                log.success('Patched VMRunner.smali')
                vmrunner_patched = True

        # --- Patch SignatureCheck.smali ---
        if os.path.basename(root) == 'pairip' and 'SignatureCheck.smali' in files:
            sig_path = os.path.join(root, 'SignatureCheck.smali')
            with open(sig_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = []
            inside_verify = False
            annotation_ended = False
            method_found = False

            for i, line in enumerate(lines):
                stripped = line.strip()

                if not inside_verify and stripped.startswith('.method') and 'verifyIntegrity(Landroid/content/Context;)V' in stripped:
                    inside_verify = True
                    method_found = True

                if inside_verify and not annotation_ended and stripped == '.end annotation':
                    annotation_ended = True
                    new_lines.append(line)
                    if not any('return-void' in l for l in lines[i+1:i+5]):
                        new_lines.append('    return-void\n')
                    continue

                new_lines.append(line)

            if method_found:
                with open(sig_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                log.success('Patched SignatureCheck.smali')
                sigcheck_patched = True

    if not vmrunner_patched:
        log.warning('VMRunner.smali not found or not patched')
    if not sigcheck_patched:
        log.warning('SignatureCheck.smali not found or not patched')

    # --- Copy .so Files ---
    log.subheader("Copying native libraries...")
    so_files_to_copy = [
        'libpairipcorex.so',
        'libFirebaseCppApp.so'
    ]

    for so_file in so_files_to_copy:
        src_path = os.path.join(cwd, so_file)
        if not os.path.exists(src_path):
            log.error(f"Missing library file: {so_file}")
            sys.exit(1)
        
        lib_dirs_found = 0
        arch_types = []
        for root, dirs, files in os.walk(base_lib_dir):
            if 'libpairipcore.so' in files:
                arch_type = os.path.basename(root)
                arch_types.append(arch_type)
                lib_dirs_found += 1
                dst_path = os.path.join(root, so_file)
                shutil.copy2(src_path, dst_path)
                log.success(f'Copied {so_file} to {arch_type} architecture')
        
        if lib_dirs_found == 0:
            log.warning(f"No library directories found for {so_file}")
        else:
            log.success(f"Copied {so_file} to {lib_dirs_found} architecture(s): {', '.join(arch_types)}")

    # --- Patch file_paths.xml ---
    import xml.etree.ElementTree as ET

    log.subheader("Patching file paths configuration...")
    file_paths_patched = 0

    for root, dirs, files in os.walk(resources_dir):
        if 'file_paths.xml' in files and 'res/xml' in root:
            xml_path = os.path.join(root, 'file_paths.xml')
            try:
                tree = ET.parse(xml_path)
                root_xml = tree.getroot()
                changed = False

                for elem in list(root_xml):
                    if (
                        elem.tag == "external-path"
                        and elem.attrib.get("path", "").startswith("Android/data/")
                        and elem.attrib.get("path", "").endswith("/files/Pictures")
                    ):
                        root_xml.remove(elem)
                        changed = True

                exists = any(
                    e.tag == "external-files-path" and
                    e.attrib.get("name") == "my_images" and
                    e.attrib.get("path") == "Pictures/"
                    for e in root_xml
                )
                if not exists:
                    ET.SubElement(root_xml, "external-files-path", name="my_images", path="Pictures/")
                    changed = True

                if changed:
                    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
                    file_paths_patched += 1
                    log.success(f"Patched {xml_path}")
            except Exception as e:
                log.error(f"Failed to patch XML {xml_path}: {e}")

    if file_paths_patched > 0:
        log.success(f"Patched {file_paths_patched} file_paths.xml file(s)")
    else:
        log.warning("No matching <external-path> entries found or already patched")

    return vmrunner_patched or sigcheck_patched

# ==============================================
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# ==============================================

def process_apk(apks_file):
    """Procesa un archivo APKS con la nueva optimización para Termux"""
    # Configurar directorios
    original_dir = os.path.dirname(os.path.abspath(apks_file))
    termux_dir = setup_termux_workdir()
    
    # Verificar archivos requeridos
    required_jars = ["APKEditor-1.4.3.jar", "uber-apk-signer.jar"]
    missing_jars = [jar for jar in required_jars if not os.path.exists(os.path.join(original_dir, jar))]
    if missing_jars:
        log.error(f"Archivos requeridos no encontrados: {', '.join(missing_jars)}")
        sys.exit(1)
    
    # Copiar archivos necesarios a Termux
    log.header("Preparando entorno en Termux...")
    try:
        termux_files = {
            "apks": copy_to_termux(apks_file, termux_dir),
            "apkeditor": copy_to_termux(os.path.join(original_dir, "APKEditor-1.4.3.jar"), termux_dir),
            "signer": copy_to_termux(os.path.join(original_dir, "uber-apk-signer.jar"), termux_dir)
        }
        
        # Copiar librerías nativas si existen en el directorio original
        required_libs = ["libpairipcorex.so", "libFirebaseCppApp.so"]
        for lib in required_libs:
            lib_path = os.path.join(original_dir, lib)
            if os.path.exists(lib_path):
                copy_to_termux(lib_path, termux_dir)
            elif not os.path.exists(os.path.join(termux_dir, lib)):
                log.warning(f"Library not found (will try to generate if needed): {lib}")
    except Exception as e:
        log.error(f"Error al preparar archivos en Termux: {e}")
        sys.exit(1)
    
    # Cambiar al directorio de Termux
    os.chdir(termux_dir)
    
    # Configurar memoria Java
    if "_JAVA_OPTIONS" not in os.environ:
        os.environ["_JAVA_OPTIONS"] = os.environ.get("_JAVA_OPTIONS", "") + " -Xmx2g"
    
    # Proceso de descompilación/compilación
    total_steps = 10
    progress = log.create_progress_bar("main", total_steps, "Patching process")
    
    # Paso 1: Extraer base.apk
    log.header("Step 1/10: Extracting base.apk")
    extract_file(termux_files["apks"], "base.apk")
    progress.update(1)
    
    # Paso 2: Crear libFirebaseCppApp.so si no existe
    log.header("Step 2/10: Handling libFirebaseCppApp.so")
    if not os.path.exists("libFirebaseCppApp.so"):
        if os.path.exists("base.apk"):
            shutil.copy("base.apk", "libFirebaseCppApp.so")
            log.success("Created libFirebaseCppApp.so from base.apk")
        else:
            log.error("base.apk not found to create libFirebaseCppApp.so")
            sys.exit(1)
    else:
        log.success("libFirebaseCppApp.so already exists")
    progress.update(1)
    
    # Paso 3: Limpieza previa
    log.header("Step 3/10: Cleaning previous files")
    cleaned = 0
    if os.path.exists("merged_app.apk"):
        os.remove("merged_app.apk")
        cleaned += 1
    decompile_dir = os.path.join(termux_dir, "merged_app_decompile_xml")
    if os.path.exists(decompile_dir):
        delete_dir_crossplatform(decompile_dir)
        cleaned += 1
    log.success(f"Removed {cleaned} old files/directories")
    progress.update(1)
    
    # Paso 4: Fusionar APKS a APK
    log.header("Step 4/10: Merging APKS to APK")
    run_command(f'java -jar APKEditor-1.4.3.jar m -i "{termux_files["apks"]}" -o merged_app.apk -extractNativeLibs true', verbose=False)
    if os.path.exists("merged_app.apk"):
        merged_size = os.path.getsize("merged_app.apk") / (1024 * 1024)
        log.success(f"Successfully merged to APK (Size: {merged_size:.2f} MB)")
    else:
        log.error("Failed to merge APKS to APK")
        sys.exit(1)
    progress.update(1)
    
    # Paso 5: Preparar descompilación
    log.header("Step 5/10: Preparing decompilation")
    if os.path.exists(decompile_dir):
        log.info("Removing existing decompiled directory")
        shutil.rmtree(decompile_dir, ignore_errors=True)
    progress.update(1)
    
    # Paso 6: Descompilar APK fusionado
    log.header("Step 6/10: Decompiling merged APK")
    log.info("This may take several minutes depending on APK size...")
    start_time = time.time()
    run_command("java -jar APKEditor-1.4.3.jar d -i merged_app.apk", verbose=False)
    elapsed_time = time.time() - start_time
    
    if os.path.exists(decompile_dir):
        log.success(f"Decompilation completed in {elapsed_time:.1f} seconds")
    else:
        log.error("Decompilation failed")
        sys.exit(1)
    progress.update(1)
    
    # Paso 7: Modificar AndroidManifest.xml
    log.header("Step 7/10: Modifying AndroidManifest.xml")
    manifest_path = os.path.join(decompile_dir, "AndroidManifest.xml")
    
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern1 = r'<activity[^>]+com\.pairip\.licensecheck\.LicenseActivity[^<]+/>'
        pattern2 = r'<provider[^>]+com\.pairip\.licensecheck\.LicenseContentProvider[^<]+/>'
        
        entries_removed = 0
        for pattern in [pattern1, pattern2]:
            matches = re.findall(pattern, content, flags=re.DOTALL)
            entries_removed += len(matches)
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        if entries_removed > 0:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)
            log.success(f"Removed {entries_removed} license check entries")
        else:
            log.warning("No license check entries found in manifest")
    else:
        log.warning("AndroidManifest.xml not found")
    progress.update(1)
    
    # Paso 8: Parchear archivos
    log.header("Step 8/10: Patching decompiled files")
    patch_result = patch_files(decompile_dir)
    progress.update(1)
    
    # Paso 9: Construir APK modificado
    log.header("Step 9/10: Building modified APK")
    if os.path.exists("out.apk"):
        os.remove("out.apk")
    
    log.info("Building APK from modified files...")
    start_time = time.time()
    run_command(f'java -jar APKEditor-1.4.3.jar b -i "{decompile_dir}" -o out.apk', verbose=False)
    elapsed_time = time.time() - start_time
    
    if os.path.exists("out.apk"):
        out_size = os.path.getsize("out.apk") / (1024 * 1024)
        log.success(f"Build completed in {elapsed_time:.1f} seconds (Size: {out_size:.2f} MB)")
    else:
        log.error("Failed to build modified APK")
        sys.exit(1)
    progress.update(1)
    
    # Paso 10: Firmar el APK
    log.header("Step 10/10: Signing the APK")
    run_command("java -jar uber-apk-signer.jar -a out.apk --overwrite", verbose=False)
    
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
    
    base_name = os.path.basename(termux_files["apks"]).rsplit('.', 1)[0]
    output_name = f"{base_name}-patched.apk"
    
    if signed_apk:
        os.rename(signed_apk, output_name)
        sign_size = os.path.getsize(output_name) / (1024 * 1024)
        log.success(f"APK signed successfully (Size: {sign_size:.2f} MB)")
    else:
        if os.path.exists("out.apk"):
            os.rename("out.apk", output_name)
            log.warning(f"Signing failed. Using unsigned APK as: {output_name}")
        else:
            log.error("Error: No output APK found")
            sys.exit(1)
    progress.update(1)
    
    # Mover el resultado al directorio original
    try:
        final_output = move_result_back(os.path.join(termux_dir, output_name), original_dir)
        log.success(f"Final APK moved to: {final_output}")
    except Exception as e:
        log.error(f"Failed to move final APK: {e}")
        sys.exit(1)
    
    # Limpieza en Termux
    log.subheader("Cleaning up temporary files...")
    cleanup_files = 0
    for item in os.listdir(termux_dir):
        item_path = os.path.join(termux_dir, item)
        try:
            if item != output_name:  # No borrar el APK final por si acaso
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    cleanup_files += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                    cleanup_files += 1
        except Exception:
            pass
    
    log.success(f"Removed {cleanup_files} temporary files/directories")
    log.close_progress("main")
    
    return final_output

# ==============================================
# FUNCIÓN MAIN (INTERFAZ)
# ==============================================

def center_text(text, width):
    return text.center(width)
    
def main():
    width = shutil.get_terminal_size().columns
    border = "▓" * width

    line1 = center_text("PairIP Protection Remover v1.2 (Termux Optimized)", width)
    line2 = center_text("Cross-platform Edition", width)
    footer = center_text("© void.eth | Modified for Termux by Zalgo ", width)

    print(f"\n{Style.BRIGHT}{Fore.CYAN}{border}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{line1}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{line2}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{border}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{footer}{Style.RESET_ALL}\n")
    
    # Detección de APKS
    apks_file = None
    if len(sys.argv) == 2:
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
    
    # Validar APKS
    try:
        with zipfile.ZipFile(apks_file, 'r') as zip_ref:
            zip_ref.testzip()
        log.success(f"Input file '{apks_file}' is a valid ZIP archive")
    except zipfile.BadZipFile:
        log.error(f"Input file '{apks_file}' is not a valid .apks file")
        sys.exit(1)
    
    if not apks_file.endswith('.apks'):
        log.warning(f"Input file doesn't have .apks extension")
    
    # Verificar Java
    log.info("Checking Java installation...")
    try:
        java_version = run_command("java -version", verbose=False, exit_on_error=False)
        if not java_version:
            java_version = run_command("java -version 2>&1", verbose=False, exit_on_error=False)
        log.success("Java detected")
    except Exception:
        log.error("Java not found. Please install Java Runtime Environment")
        sys.exit(1)
    
    # Procesar APK
    log.info(f"Processing file: {os.path.basename(apks_file)}")
    start_time = time.time()
    out_name = process_apk(apks_file)
    total_time = time.time() - start_time
    
    # Resultado final
    log.header("Finalizing...")
    if out_name:
        output_path = os.path.abspath(out_name)
        output_size = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"\n{Style.BRIGHT}{Fore.GREEN}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Style.BRIGHT}{Fore.GREEN}║              PROCESS COMPLETE                ║{Style.RESET_ALL}")
        print(f"{Style.BRIGHT}{Fore.GREEN}╚══════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}✓ Final APK: {Style.BRIGHT}{out_name}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Size: {output_size:.2f} MB{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Location: {output_path}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Total processing time: {total_time:.1f} seconds{Style.RESET_ALL}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Process cancelled by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
        sys.exit(1)