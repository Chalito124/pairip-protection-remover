#!/usr/bin/env python3
import os
import sys
import shutil
import re
import subprocess
import glob
from pathlib import Path

def run_command(command, verbose=True, exit_on_error=True):
    """Run a shell command and return output"""
    if verbose:
        print(f"Executing: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command failed with error code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            if exit_on_error:
                sys.exit(1)
        return result.stdout.strip()
    except Exception as e:
        print(f"Exception while executing command: {e}")
        if exit_on_error:
            sys.exit(1)
        return ""

def patch_files():
    """Apply patches to the decompiled files as in the legacy script"""
    base_dir = os.path.expanduser('~/merged_app_decompile_xml')
    base_lib_dir = os.path.join(base_dir, 'root/lib')
    resources_dir = os.path.join(base_dir, 'resources')
    cwd = os.getcwd()

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
    for root, dirs, files in os.walk(base_dir):
        # --- Patch VMRunner.smali ---
        if root.endswith('/com/pairip') and 'VMRunner.smali' in files:
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
                print(f'Patched <clinit>: {vmrunner_path}')
            else:
                print(f'No match for <clinit> in: {vmrunner_path}')

        # --- Patch SignatureCheck.smali ---
        if root.endswith('/com/pairip') and 'SignatureCheck.smali' in files:
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
                print(f'Patched verifyIntegrity: {sig_path}')
            else:
                print(f'No match for verifyIntegrity in: {sig_path}')

    # --- Copy .so Files ---
    so_files_to_copy = [
        'libpairipcorex.so',
        'libFirebaseCppApp.so'
    ]

    missing = [f for f in so_files_to_copy if not os.path.exists(os.path.join(cwd, f))]
    if missing:
        print(f'Error: Missing files in current directory: {", ".join(missing)}')
        sys.exit(1)
    else:
        for root, dirs, files in os.walk(base_lib_dir):
            if 'libpairipcore.so' in files:
                for so_file in so_files_to_copy:
                    src_path = os.path.join(cwd, so_file)
                    dst_path = os.path.join(root, so_file)
                    shutil.copy2(src_path, dst_path)
                    print(f'Copied {so_file} to: {root}')

    # --- Patch file_paths.xml in resources/*/res/xml/
    file_paths_patched = 0
    pattern = re.compile(
        r'<external-path\s+name="[^"]*"\s+path="Android/data/[^"]*/files/Pictures"\s*/>',
        re.IGNORECASE
    )
    replacement = '<external-files-path name="my_images" path="Pictures/" />'

    for root, dirs, files in os.walk(resources_dir):
        if 'file_paths.xml' in files and 'res/xml' in root:
            xml_path = os.path.join(root, 'file_paths.xml')
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if pattern.search(content):
                content_new = pattern.sub(replacement, content)
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(content_new)
                print(f'Patched file_paths.xml: {xml_path}')
                file_paths_patched += 1

    if file_paths_patched == 0:
        print("[!] No matching <external-path> entries found.")
    else:
        print(f"[✓] Patched {file_paths_patched} file_paths.xml file(s).")

def process_apk(apks_file):
    """Process an APKS file according to the specified steps"""
    # Check if required JAR files exist
    required_jars = ["APKEditor-1.4.3.jar", "uber-apk-signer.jar"]
    for jar in required_jars:
        if not os.path.exists(jar):
            print(f"Error: Required JAR file '{jar}' not found in the current directory")
            sys.exit(1)

    # Get the base name of the APKS file without extension
    base_name = os.path.basename(apks_file).rsplit('.', 1)[0]
    
    # Step 1: Unzip apks to extract base.apk
    print("\n[1/10] Extracting base.apk from APKS file...")
    run_command(f"unzip -o \"{apks_file}\" base.apk")
    
    # Step 2: Rename base.apk to libFirebaseCppApp.so
    print("\n[2/10] Renaming base.apk to libFirebaseCppApp.so...")
    shutil.copy("base.apk", "libFirebaseCppApp.so")
    
    # Step 3: Remove merged_app.apk if exists
    if os.path.exists("merged_app.apk"):
        print("\n[3/10] Removing existing merged_app.apk...")
        os.remove("merged_app.apk")
    
    # Step 4: Merge APKS to APK
    print("\n[4/10] Merging APKS to APK...")
    run_command(f"java -jar APKEditor-1.4.3.jar m -i \"{apks_file}\" -o merged_app.apk -extractNativeLibs true")
    
    # Step 5: Remove decompiled directory if exists
    decompile_dir = os.path.expanduser("~/merged_app_decompile_xml")
    if os.path.exists(decompile_dir):
        print("\n[5/10] Removing existing decompiled directory...")
        shutil.rmtree(decompile_dir)
    
    # Step 6: Decompile the merged APK
    print("\n[6/10] Decompiling merged APK...")
    run_command("java -jar APKEditor-1.4.3.jar d -i merged_app.apk")
    
    # Step 7: Modify AndroidManifest.xml using awk-like operation
    print("\n[7/10] Modifying AndroidManifest.xml...")
    manifest_path = os.path.join(decompile_dir, "AndroidManifest.xml")
    
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use regex to remove the LicenseActivity and LicenseContentProvider entries
        # This is more reliable than line-by-line processing
        pattern1 = r'<activity\s+android:name="com\.pairip\.licensecheck\.LicenseActivity"[^>]*?>.*?(?=/>)/>'
        pattern2 = r'<provider\s+android:name="com\.pairip\.licensecheck\.LicenseContentProvider"[^>]*?>.*?(?=/>)/>'
        
        # Apply the substitutions with regex that handles multiline
        for pattern in [pattern1, pattern2]:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Modified AndroidManifest.xml: {manifest_path}")
    else:
        print(f"Warning: AndroidManifest.xml not found at {manifest_path}")
    
    # Step 8: Remove out.apk if exists
    if os.path.exists("out.apk"):
        print("\n[8/10] Removing existing out.apk...")
        os.remove("out.apk")
    
    # Run the patching function (from the legacy script)
    print("\nRunning patch operations...")
    patch_files()
    
    # Step 9: Build APK from decompiled files
    print("\n[9/10] Building APK from modified files...")
    run_command(f"java -jar APKEditor-1.4.3.jar b -i {decompile_dir} -o out.apk")
    
    # Step 10: Sign the APK
    print("\n[10/10] Signing the APK...")
    sign_output = run_command("java -jar uber-apk-signer.jar -a out.apk")
    print(sign_output)
    
    # Clean up: keep only the signed APK and the original APKS
    # Check for multiple possible signed APK naming patterns
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
    
    if signed_apk:
        output_name = f"{base_name}-patched.apk"
        shutil.copy(signed_apk, output_name)
        print(f"\nProcess complete! Final patched APK saved as: {output_name}")
    else:
        # If we can't find the expected output files, see if we can find any APK files
        any_apks = glob.glob("*.apk")
        recent_apks = [apk for apk in any_apks if os.path.getmtime(apk) > os.path.getmtime(apks_file)]
        
        if recent_apks and "out.apk" in recent_apks:
            output_name = f"{base_name}-patched.apk"
            shutil.copy("out.apk", output_name)
            print(f"\nFallback: Copying unsigned APK as: {output_name}")
            print("Note: The APK might not be properly signed!")
        else:
            print("\nError: Could not find any signed APK in the output directory")
            print("Please check if the signing process completed successfully")
        
    # Clean up temporary files
    print("\nCleaning up temporary files...")
    cleanup_files = [
        "base.apk", "merged_app.apk", "out.apk", 
        "out-aligned-debugSigned.apk", "out-aligned-signed.apk", 
        "out-debugSigned.apk", "out-signed.apk"
    ]
    
    for file in cleanup_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except Exception as e:
                print(f"Warning: Could not remove {file}: {e}")
    
    # Don't remove the libFirebaseCppApp.so and libpairipcorex.so as they may be needed for future runs
    
    print(f"Kept files: {base_name}-patched.apk and {apks_file}")
    print("All temporary files have been removed.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python myscript.py app.apks")
        sys.exit(1)
    
    apks_file = sys.argv[1]
    if not os.path.exists(apks_file):
        print(f"Error: Input file '{apks_file}' not found")
        sys.exit(1)
    
    if not apks_file.endswith('.apks'):
        print(f"Warning: Input file '{apks_file}' does not have .apks extension. Continuing anyway...")
    
    # Create libpairipcorex.so if it doesn't exist (copy it from base.apk)
    if not os.path.exists("libpairipcorex.so"):
        print("Note: Creating libpairipcorex.so (copy of base.apk)")
        if not os.path.exists("base.apk"):
            # First extract base.apk from the APKS file
            run_command(f"unzip -o \"{apks_file}\" base.apk", verbose=False)
        if os.path.exists("base.apk"):
            shutil.copy("base.apk", "libpairipcorex.so")
        else:
            print("Warning: Could not create libpairipcorex.so because base.apk extraction failed")
    
    process_apk(apks_file)

if __name__ == "__main__":
    main()