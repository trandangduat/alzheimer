import os

# Base paths
BASE_DIR = r"/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer"
INPUT_FILE_PATH = r"/home/trandangduat/freesurfer-test/disc1/OAS1_0001_MR1/PROCESSED/MPRAGE/SUBJ_111/OAS1_0001_MR1_mpr_n4_anon_sbj_111.img"

# Output configuration
OUTPUT_ROOT = os.path.join(BASE_DIR, "final_r")

# Tool paths
TOOLS = {
    "fastsurfer_root": os.path.join(BASE_DIR, "tools", "FastSurfer"),
    "vox2cortex_root": os.path.join(BASE_DIR, "tools", "Vox2Cortex"),
    "cortical_flow_root": os.path.join(BASE_DIR, "tools", "CorticalFlow")
}

# Subdirectories for each step
DIRS = {
    "step1": os.path.join(OUTPUT_ROOT, "step1_input"),
    "step2_3": os.path.join(OUTPUT_ROOT, "step2_3_preprocessed"),
    "step4": os.path.join(OUTPUT_ROOT, "step4_segmentation"),
    "step7": os.path.join(OUTPUT_ROOT, "step7_stats"),
    "step8": os.path.join(OUTPUT_ROOT, "step8_registration")
}

def ensure_dirs():
    """Create necessary directories if they don't exist."""
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    for d in DIRS.values():
        os.makedirs(d, exist_ok=True)
