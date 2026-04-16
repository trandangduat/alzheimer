#!/bin/bash
# reprocess_adni_step5.sh
# Reprocess ADNI with fixes to surface reconstruction

set -e

BASE_DIR="/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer"
SUBJECTS_DIR="${BASE_DIR}/pipeline-subjects"
SUBJECT_ID="I776974"  # ADNI subject
CORTICAL_FLOW="${BASE_DIR}/tools/CorticalFlow"

echo "=========================================="
echo "REPROCESSING ADNI Step 5 WITH FIXES"
echo "=========================================="
echo ""
echo "Subject: ${SUBJECT_ID}"
echo "Changes made:"
echo "  1. apply_affine.py - Use INVERSE affine for template→native transform"
echo "  2. data.py - Removed hard-coded hemisphere cropping"
echo "  3. recon_all.sh - Added debug output"
echo ""

# Step 1: Backup old results
SUBJ_DIR="${SUBJECTS_DIR}/${SUBJECT_ID}"
if [ -d "${SUBJ_DIR}/surf" ]; then
    echo "Backing up old surfaces..."
    mv "${SUBJ_DIR}/surf" "${SUBJ_DIR}/surf_backup_$(date +%Y%m%d_%H%M%S)"
fi

if [ -d "${SUBJ_DIR}/tmp" ]; then
    echo "Clearing temporary files..."
    rm -rf "${SUBJ_DIR}/tmp"
fi

# Step 2: Prepare input
echo ""
echo "Checking input files..."
INPUT_FILE="${SUBJ_DIR}/mri/T1.mgz"
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input not found: ${INPUT_FILE}"
    exit 1
fi

echo "Input file: ${INPUT_FILE}"

# Step 3: Run recon_all.sh with fixes
echo ""
echo "Running recon_all.sh with fixes..."
echo "Command: ${CORTICAL_FLOW}/recon_all.sh ${SUBJECT_ID} ${INPUT_FILE} ${SUBJECTS_DIR}"
echo ""

cd "${CORTICAL_FLOW}"
bash recon_all.sh "${SUBJECT_ID}" "${INPUT_FILE}" "${SUBJECTS_DIR}" 2>&1 | tee "${SUBJ_DIR}/step5_reprocess.log"

echo ""
echo "=========================================="
echo "Step 5 Reprocessing Complete"
echo "=========================================="
echo ""
echo "Results:"
ls -lh "${SUBJ_DIR}/surf/"
echo ""
echo "Log saved to: ${SUBJ_DIR}/step5_reprocess.log"
echo ""
echo "Next: Run diagnostic to compare with OASIS"
echo "  python ${BASE_DIR}/debug_adni_surface_alignment.py"
