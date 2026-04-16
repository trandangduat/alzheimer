#!/bin/bash
# debug_surface_alignment.sh
# Diagnostic script để kiểm tra vấn đề tái tạo bề mặt vỏ não
# So sánh OASIS vs ADNI

set -e

BASE_DIR="/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer"
SUBJECTS_DIR="${BASE_DIR}/pipeline-subjects"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}DIAGNOSTIC: Surface Alignment Issues${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to check file and print info
check_mri_info() {
    local subject=$1
    local file_path="${SUBJECTS_DIR}/${subject}/mri/orig.mgz"
    
    if [ ! -f "$file_path" ]; then
        echo -e "${RED}[ERROR] File not found: ${file_path}${NC}"
        return 1
    fi
    
    echo -e "\n${YELLOW}Subject: ${subject}${NC}"
    echo "File: ${file_path}"
    mri_info "$file_path" | grep -E "dimensions|voxel_size|RAS|done"
}

# Function to check affine registration result
check_affine_registration() {
    local subject=$1
    local affine_file="${SUBJECTS_DIR}/${subject}/mri/transforms/reg_affine.txt"
    
    if [ ! -f "$affine_file" ]; then
        echo -e "${RED}[WARNING] Affine file not found: ${affine_file}${NC}"
        return 1
    fi
    
    echo -e "\n${YELLOW}Affine Registration Matrix for ${subject}:${NC}"
    cat "$affine_file"
}

# Function to check surface files
check_surfaces() {
    local subject=$1
    local surf_dir="${SUBJECTS_DIR}/${subject}/surf"
    
    echo -e "\n${YELLOW}Surface files for ${subject}:${NC}"
    if [ ! -d "$surf_dir" ]; then
        echo -e "${RED}  Directory not found: ${surf_dir}${NC}"
        return 1
    fi
    
    ls -lh "$surf_dir"/*.pial "$surf_dir"/*.white 2>/dev/null || echo -e "${RED}  No surfaces found!${NC}"
}

# Function to check intermediate files
check_intermediate() {
    local subject=$1
    local tmp_dir="${SUBJECTS_DIR}/${subject}/tmp/niftyreg"
    
    echo -e "\n${YELLOW}Intermediate files for ${subject}:${NC}"
    if [ -d "$tmp_dir" ]; then
        ls -lh "$tmp_dir"/ 2>/dev/null | head -20
    else
        echo -e "${RED}  Temp directory not found${NC}"
    fi
}

# MAIN EXECUTION
echo -e "\n${GREEN}[1/5] Kiểm tra Info MRI${NC}"
check_mri_info "0006"    # OASIS
check_mri_info "I776974" # ADNI

echo -e "\n${GREEN}[2/5] Kiểm tra Affine Registration${NC}"
check_affine_registration "0006"
check_affine_registration "I776974"

echo -e "\n${GREEN}[3/5] Kiểm tra Surface Files${NC}"
check_surfaces "0006"
check_surfaces "I776974"

echo -e "\n${GREEN}[4/5] Kiểm tra Intermediate Files${NC}"
check_intermediate "0006"
check_intermediate "I776974"

# Additional check: Calculate affine matrix determinant (scale factor)
echo -e "\n${GREEN}[5/5] Phân Tích Affine Matrices${NC}"

calculate_affine_stats() {
    local subject=$1
    local affine_file="${SUBJECTS_DIR}/${subject}/mri/transforms/reg_affine.txt"
    
    if [ ! -f "$affine_file" ]; then
        return
    fi
    
    echo -e "\n${YELLOW}Affine Statistics for ${subject}:${NC}"
    
    # Use Python to calculate matrix properties
    python3 << EOF
import numpy as np

affine = np.loadtxt('${affine_file}')
print(f"Matrix shape: {affine.shape}")
print(f"Determinant: {np.linalg.det(affine[:3,:3]):.6f}")  # Zoom factor (should be close to 1)
print(f"Condition number: {np.linalg.cond(affine[:3,:3]):.6f}")  # Should be low
print(f"Inverse determinant: {1/np.linalg.det(affine[:3,:3]):.6f}")  # For back-transform
print(f"Translation: {affine[:3, 3]}")  # Should be reasonable values
EOF
}

calculate_affine_stats "0006"
calculate_affine_stats "I776974"

echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. If MRI dimensions differ from 256x256x256 → Fix mri_convert --conform"
echo -e "2. If affine matrices differ greatly → Check NiftyReg parameters"
echo -e "3. If surfaces missing → Re-run CorticalFlow step"
echo -e "4. Compare visual alignment in FreeView"
echo -e "${BLUE}================================================${NC}\n"
