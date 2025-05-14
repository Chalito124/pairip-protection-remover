#!/bin/bash
# PairIP Protection Remover - Bash version
# Based on the Python script by void.eth
# Repository: https://github.com/void-eth/pairip-protection-remover

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BRIGHT_CYAN='\033[1;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Initialize terminal width
TERM_WIDTH=$(tput cols)

# Logger functions
log_info() {
  echo -e "${BLUE}[i]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
  echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[!]${NC} $1"
}

log_header() {
  echo -e "\n${BRIGHT_CYAN}▶ $1${NC}"
}

log_subheader() {
  echo -e "${CYAN}  ➤ $1${NC}"
}

# Function to display progress bar
show_progress() {
  local current=$1
  local total=$2
  local message="$3"
  local percent=$((current * 100 / total))
  local progress=$((current * 40 / total))
  
  # Create the progress bar
  local bar=""
  for ((i=0; i<progress; i++)); do
    bar="${bar}█"
  done
  
  for ((i=progress; i<40; i++)); do
    bar="${bar}░"
  done
  
  echo -ne "${CYAN}${message}${NC}: ${percent}%|${bar}| ${current}/${total}\r"
  if [ "$current" -eq "$total" ]; then
    echo ""
  fi
}

# Check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check and install dependencies
check_dependencies() {
  log_header "Checking dependencies"
  
  # Check Java installation
  if ! command_exists java; then
    log_error "Java is not installed. Please install Java Runtime Environment and try again."
    exit 1
  else
    log_success "Java detected"
  fi
  
  # Check for required commands
  local missing_deps=()
  for cmd in unzip zip basename dirname realpath; do
    if ! command_exists "$cmd"; then
      missing_deps+=("$cmd")
    fi
  done
  
  if [ ${#missing_deps[@]} -gt 0 ]; then
    log_error "Missing dependencies: ${missing_deps[*]}"
    log_info "Please install them using your package manager and try again."
    exit 1
  else
    log_success "All required bash commands are available"
  fi
  
  # Check for required JAR files
  for jar in "APKEditor-1.4.3.jar" "uber-apk-signer.jar"; do
    if [ ! -f "$jar" ]; then
      log_error "Required JAR file '$jar' not found in the current directory"
      exit 1
    fi
  done
  log_success "All required JAR files found"
}

# Function to extract file from zip archive
extract_file() {
  local zipfile="$1"
  local target="${2:-}"
  
  if command_exists unzip; then
    if [ -z "$target" ]; then
      unzip -o "$zipfile" >/dev/null 2>&1
    else
      unzip -o "$zipfile" "$target" >/dev/null 2>&1
    fi
    return $?
  else
    log_error "unzip command not found"
    return 1
  fi
}

# Function to delete directory or file
delete_dir_file() {
  local path="$1"
  
  if [ -f "$path" ]; then
    rm -f "$path" >/dev/null 2>&1
    return $?
  elif [ -d "$path" ]; then
    rm -rf "$path" >/dev/null 2>&1
    return $?
  fi
  return 1
}

# Function to patch VMRunner.smali
patch_vmrunner() {
  local file="$1"
  local new_clinit_block='
.method static constructor <clinit>()V
    .registers 1

    .line 30
    const-string v0, "pairipcorex"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    const-string v0, "pairipcore"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    return-void
.end method'

  # Create a temporary file
  local temp_file=$(mktemp)
  
  # Process the file line by line
  local inside_clinit=0
  local method_start_found=0
  
  while IFS= read -r line; do
    if [ $inside_clinit -eq 0 ] && [[ "$line" == *".method"* && "$line" == *"<clinit>()V"* ]]; then
      inside_clinit=1
      method_start_found=1
      echo -e "$new_clinit_block" >> "$temp_file"
      continue
    fi
    
    if [ $inside_clinit -eq 1 ]; then
      if [[ "$line" == *".end method"* ]]; then
        inside_clinit=0
      fi
      continue
    fi
    
    echo "$line" >> "$temp_file"
  done < "$file"
  
  # Replace the original file with the modified one
  mv "$temp_file" "$file"
  
  if [ $method_start_found -eq 1 ]; then
    return 0
  else
    return 1
  fi
}

# Function to patch SignatureCheck.smali
patch_sigcheck() {
  local file="$1"
  
  # Create a temporary file
  local temp_file=$(mktemp)
  
  # Process the file line by line
  local inside_verify=0
  local annotation_ended=0
  local method_found=0
  
  while IFS= read -r line; do
    if [ $inside_verify -eq 0 ] && [[ "$line" == *".method"* && "$line" == *"verifyIntegrity(Landroid/content/Context;)V"* ]]; then
      inside_verify=1
      method_found=1
    fi
    
    if [ $inside_verify -eq 1 ] && [ $annotation_ended -eq 0 ] && [[ "$line" == *".end annotation"* ]]; then
      annotation_ended=1
      echo "$line" >> "$temp_file"
      
      # Check next few lines for return-void
      local has_return=0
      local next_lines=$(head -n 5 <(tail -n +$(grep -n -A 5 -m 1 ".end annotation" "$file" | head -n 1 | cut -d '-' -f 1) "$file"))
      if [[ "$next_lines" == *"return-void"* ]]; then
        has_return=1
      fi
      
      if [ $has_return -eq 0 ]; then
        echo "    return-void" >> "$temp_file"
      fi
      continue
    fi
    
    echo "$line" >> "$temp_file"
  done < "$file"
  
  # Replace the original file with the modified one
  mv "$temp_file" "$file"
  
  if [ $method_found -eq 1 ]; then
    return 0
  else
    return 1
  fi
}

# Function to patch file_paths.xml
patch_file_paths() {
  local file="$1"
  local count=0
  
  # Create a temporary file
  local temp_file=$(mktemp)
  
  # Replace the external-path entry with our modified version
  sed -E 's|<external-path[[:space:]]+name="[^"]*"[[:space:]]+path="Android/data/[^"]*/files/Pictures"[[:space:]]*/?>|<external-files-path name="my_images" path="Pictures/" />|g' "$file" > "$temp_file"
  
  # Count replacements
  if diff "$file" "$temp_file" >/dev/null; then
    count=0
  else
    count=1
  fi
  
  # Replace the original file with the modified one
  mv "$temp_file" "$file"
  
  return $count
}

# Function to patch AndroidManifest.xml
patch_manifest() {
  local file="$1"
  local count=0
  
  # Create a temporary file
  local temp_file=$(mktemp)
  
  # Remove license check components
  sed -E '/<activity[^>]+com\.pairip\.licensecheck\.LicenseActivity[^<]+\/>/d; /<provider[^>]+com\.pairip\.licensecheck\.LicenseContentProvider[^<]+\/>/d' "$file" > "$temp_file"
  
  # Count replacements
  if diff "$file" "$temp_file" >/dev/null; then
    count=0
  else
    count=$(grep -E 'com\.pairip\.licensecheck\.(LicenseActivity|LicenseContentProvider)' "$file" | wc -l)
  fi
  
  # Replace the original file with the modified one
  mv "$temp_file" "$file"
  
  return $count
}

# Function to patch all files
patch_files() {
  local base_dir="merged_app_decompile_xml"
  local base_lib_dir="$base_dir/root/lib"
  local resources_dir="$base_dir/resources"
  local cwd=$(pwd)
  
  log_header "Applying patches to decompiled files"
  
  # --- Patch Smali Files ---
  log_subheader "Patching protection code..."
  local vmrunner_patched=0
  local sigcheck_patched=0
  
  # Find and patch VMRunner.smali
  find "$base_dir" -name "VMRunner.smali" -path "*/pairip/*" | while read -r file; do
    if patch_vmrunner "$file"; then
      log_success "Patched VMRunner.smali"
      vmrunner_patched=1
    fi
  done
  
  if [ $vmrunner_patched -eq 0 ]; then
    log_warning "VMRunner.smali not found or not patched"
  fi
  
  # Find and patch SignatureCheck.smali
  find "$base_dir" -name "SignatureCheck.smali" -path "*/pairip/*" | while read -r file; do
    if patch_sigcheck "$file"; then
      log_success "Patched SignatureCheck.smali"
      sigcheck_patched=1
    fi
  done
  
  if [ $sigcheck_patched -eq 0 ]; then
    log_warning "SignatureCheck.smali not found or not patched"
  fi
  
  # --- Copy .so Files ---
  log_subheader "Copying native libraries..."
  local so_files_to_copy=("libpairipcorex.so" "libFirebaseCppApp.so")
  
  # Check if all required .so files exist
  local missing_files=()
  for so_file in "${so_files_to_copy[@]}"; do
    if [ ! -f "$so_file" ]; then
      missing_files+=("$so_file")
    fi
  done
  
  if [ ${#missing_files[@]} -gt 0 ]; then
    log_error "Missing files in current directory: ${missing_files[*]}"
    exit 1
  else
    local lib_dirs_found=0
    local arch_types=()
    
    find "$base_lib_dir" -name "libpairipcore.so" | while read -r file; do
      local lib_dir=$(dirname "$file")
      local arch_type=$(basename "$lib_dir")
      arch_types+=("$arch_type")
      lib_dirs_found=$((lib_dirs_found + 1))
      
      for so_file in "${so_files_to_copy[@]}"; do
        cp "$cwd/$so_file" "$lib_dir/"
        log_success "Copied $so_file to $arch_type architecture"
      done
    done
    
    if [ $lib_dirs_found -eq 0 ]; then
      log_warning "No library directories found containing libpairipcore.so"
    else
      log_success "Libraries copied to $lib_dirs_found architecture(s): ${arch_types[*]}"
    fi
  fi
  
  # --- Patch file_paths.xml ---
  log_subheader "Patching file paths configuration..."
  local file_paths_patched=0
  
  find "$resources_dir" -path "*/res/xml/file_paths.xml" | while read -r file; do
    if patch_file_paths "$file"; then
      file_paths_patched=$((file_paths_patched + 1))
    fi
  done
  
  if [ $file_paths_patched -gt 0 ]; then
    log_success "Patched $file_paths_patched file_paths.xml file(s)"
  else
    log_warning "No matching <external-path> entries found"
  fi
  
  return $((vmrunner_patched + sigcheck_patched))
}

# Main function to process the APK
process_apk() {
  local apks_file="$1"
  local base_name=$(basename "$apks_file" .apks)
  local decompile_dir="merged_app_decompile_xml"
  local current_step=0
  local total_steps=10
  
  # Set Java memory options for large APKs
  export _JAVA_OPTIONS="-Xmx2g"
  
  # Step 1: Extract base.apk
  log_header "Step 1/10: Extracting base.apk"
  extract_file "$apks_file" "base.apk"
  if [ ! -f "base.apk" ]; then
    log_error "Failed to extract base.apk"
    exit 1
  fi
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 2: Create libFirebaseCppApp.so
  log_header "Step 2/10: Creating libFirebaseCppApp.so"
  cp "base.apk" "libFirebaseCppApp.so"
  log_success "Created libFirebaseCppApp.so from base.apk"
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 3: Remove old merged_app.apk if exists
  log_header "Step 3/10: Cleaning previous files"
  local cleaned=0
  if [ -f "merged_app.apk" ]; then
    rm -f "merged_app.apk"
    cleaned=$((cleaned + 1))
  fi
  if [ -d "merged_app_decompile_xml" ]; then
    rm -rf "merged_app_decompile_xml"
    cleaned=$((cleaned + 1))
  fi
  log_success "Removed $cleaned old files/directories"
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 4: Merge APKS to APK
  log_header "Step 4/10: Merging APKS to APK"
  java -jar APKEditor-1.4.3.jar m -i "$apks_file" -o merged_app.apk -extractNativeLibs true
  if [ -f "merged_app.apk" ]; then
    local merged_size=$(du -m "merged_app.apk" | cut -f1)
    log_success "Successfully merged to APK (Size: ${merged_size} MB)"
  else
    log_error "Failed to merge APKS to APK"
    exit 1
  fi
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 5: Remove old decompiled directory if exists
  log_header "Step 5/10: Preparing decompilation"
  if [ -d "$decompile_dir" ]; then
    log_info "Removing existing decompiled directory"
    rm -rf "$decompile_dir"
  fi
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 6: Decompile the merged APK
  log_header "Step 6/10: Decompiling merged APK"
  log_info "This may take several minutes depending on APK size..."
  local start_time=$(date +%s)
  java -jar APKEditor-1.4.3.jar d -i merged_app.apk
  local end_time=$(date +%s)
  local elapsed_time=$((end_time - start_time))
  
  if [ -d "$decompile_dir" ]; then
    log_success "Decompilation completed in ${elapsed_time} seconds"
  else
    log_error "Decompilation failed"
    exit 1
  fi
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 7: Modify AndroidManifest.xml
  log_header "Step 7/10: Modifying AndroidManifest.xml"
  local manifest_path="$decompile_dir/AndroidManifest.xml"
  
  if [ -f "$manifest_path" ]; then
    local entries_removed=$(patch_manifest "$manifest_path")
    
    if [ $entries_removed -gt 0 ]; then
      log_success "Removed $entries_removed license check entries"
    else
      log_warning "No license check entries found in manifest"
    fi
  else
    log_warning "AndroidManifest.xml not found"
  fi
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 8: Patch files
  log_header "Step 8/10: Patching decompiled files"
  patch_files
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 9: Build APK from decompiled files
  log_header "Step 9/10: Building modified APK"
  if [ -f "out.apk" ]; then
    rm -f "out.apk"
  fi
  
  log_info "Building APK from modified files..."
  local start_time=$(date +%s)
  java -jar APKEditor-1.4.3.jar b -i "$decompile_dir" -o out.apk
  local end_time=$(date +%s)
  local elapsed_time=$((end_time - start_time))
  
  if [ -f "out.apk" ]; then
    local out_size=$(du -m "out.apk" | cut -f1)
    log_success "Build completed in ${elapsed_time} seconds (Size: ${out_size} MB)"
  else
    log_error "Failed to build modified APK"
    exit 1
  fi
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Step 10: Sign the APK
  log_header "Step 10/10: Signing the APK"
  java -jar uber-apk-signer.jar -a out.apk --overwrite
  
  # Find the signed APK
  local signed_apk=""
  local signed_apk_patterns=("out-aligned-signed.apk" "out-signed.apk" "out-debugSigned.apk" "out-aligned-debugSigned.apk")
  
  for pattern in "${signed_apk_patterns[@]}"; do
    if [ -f "$pattern" ]; then
      signed_apk="$pattern"
      break
    fi
  done
  
  local output_name="${base_name}-patched.apk"
  
  if [ -n "$signed_apk" ]; then
    cp "$signed_apk" "$output_name"
    local sign_size=$(du -m "$output_name" | cut -f1)
    log_success "APK signed successfully (Size: ${sign_size} MB)"
  else
    # Fallback to unsigned APK if signing fails
    if [ -f "out.apk" ]; then
      cp "out.apk" "$output_name"
      log_warning "Signing failed. Using unsigned APK as: $output_name"
    else
      log_error "Error: No output APK found"
      exit 1
    fi
  fi
  current_step=$((current_step + 1))
  show_progress $current_step $total_steps "Patching process"
  
  # Clean up temporary files
  log_subheader "Cleaning up temporary files..."
  local cleanup_files=0
  
  # Find and clean up any temporary files
  for tmp_file in *.tmp*; do
    if [ -f "$tmp_file" ]; then
      rm -f "$tmp_file"
      cleanup_files=$((cleanup_files + 1))
    fi
  done
  
  # Find and clean up any temporary directories created by Java
  for tmp_dir in tmp-*; do
    if [ -d "$tmp_dir" ]; then
      rm -rf "$tmp_dir"
      cleanup_files=$((cleanup_files + 1))
    fi
  done
  
  log_success "Removed $cleanup_files temporary files/directories"
  
  echo "$output_name"
}

# Main function
main() {
  # Display header
  TERM_WIDTH=$(tput cols)
  local border=$(printf '%*s' "$TERM_WIDTH" '' | tr ' ' '=')
  
  echo -e "\n${BRIGHT_CYAN}${border}${NC}"
  printf "${BRIGHT_CYAN}%*s${NC}\n" $((TERM_WIDTH/2 + 20/2)) "PairIP Protection Remover"
  printf "${BRIGHT_CYAN}%*s${NC}\n" $((TERM_WIDTH/2 + 15/2)) "Bash Edition v1.0"
  echo -e "${BRIGHT_CYAN}${border}${NC}"
  printf "${BRIGHT_CYAN}%*s${NC}\n\n" $((TERM_WIDTH/2 + 10/2)) "© void.eth"
  
  # Check arguments
  if [ $# -ne 1 ]; then
    log_error "Usage: $0 app.apks"
    exit 1
  fi
  
  local apks_file="$1"
  if [ ! -f "$apks_file" ]; then
    log_error "Input file '$apks_file' not found"
    exit 1
  fi
  
  if [[ "$apks_file" != *.apks ]]; then
    log_warning "Input file doesn't have .apks extension"
  fi
  
  # Check dependencies
  check_dependencies
  
  # Create working directory if needed
  local work_dir=$(dirname "$(realpath "$apks_file")")
  cd "$work_dir"
  
  log_info "Processing file: $(basename "$apks_file")"
  local start_time=$(date +%s)
  local out_name=$(process_apk "$apks_file")
  local end_time=$(date +%s)
  local total_time=$((end_time - start_time))
  
  log_header "Finalizing..."
  local leftovers=("base.apk" "merged_app.apk" "out.apk" "out-aligned-debugSigned.apk" "out-aligned-signed.apk" "out-debugSigned.apk" "out-signed.apk" "merged_app_decompile_xml")
  
  local cleanup_count=0
  for file in "${leftovers[@]}"; do
    if [ -e "$file" ]; then
      delete_dir_file "$file"
      cleanup_count=$((cleanup_count + 1))
    fi
  done
  
  if [ $cleanup_count -gt 0 ]; then
    log_success "Removed $cleanup_count leftover files/directories"
  fi
  
  if [ -n "$out_name" ]; then
    local output_path=$(realpath "$out_name")
    local output_size=$(du -m "$output_path" | cut -f1)
    
    echo -e "\n${BOLD}${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║              PROCESS COMPLETE                ║${NC}"
    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo -e "\n${GREEN}✓ Final APK: ${BOLD}${out_name}${NC}"
    echo -e "${GREEN}✓ Size: ${output_size} MB${NC}"
    echo -e "${GREEN}✓ Location: ${output_path}${NC}"
    echo -e "${GREEN}✓ Total processing time: ${total_time} seconds${NC}\n"
  fi
}

# Handle interruptions
trap 'echo -e "\n${YELLOW}Process cancelled by user.${NC}"; exit 0' INT

# Run the main function
main "$@"