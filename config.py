import os

# Base paths
BASE_DIR = r"/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer"
INPUT_FILE_PATH = r"/home/trandangduat/freesurfer-test/disc1/OAS1_0001_MR1/PROCESSED/MPRAGE/SUBJ_111/OAS1_0001_MR1_mpr_n4_anon_sbj_111.img"

# Output configuration
SUBJECTS_DIR = os.path.join(BASE_DIR, "subjects2")
OUTPUT_ROOT = SUBJECTS_DIR # Alias for backward compatibility if needed

# Tool paths
TOOLS = {
    "fastsurfer_root": os.path.join(BASE_DIR, "tools", "FastSurfer"),
    "cortical_flow_root": os.path.join(BASE_DIR, "tools", "CorticalFlow")
}

# Atlas paths
SCHAEFER_GCS_ROOT = r"/mnt/c/Users/ADMIN/Desktop/MRI/gcs_Schaefer2018_update20190916/gcs"
FREESURFER_AVERAGE_DIR = r"/usr/local/freesurfer/8.1.0/average"

# Subdirectories for each step - DEPRECATED in favor of Subject-Centric structure
# We keep this empty or minimal if other scripts rely on importing DIRS, 
# but logic should move to using SUBJECTS_DIR/<sid>/...
DIRS = {} 

def ensure_dirs():
    """Create necessary directories if they don't exist."""
    os.makedirs(SUBJECTS_DIR, exist_ok=True)

