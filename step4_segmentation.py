import os
import sys
import subprocess
from config import SUBJECTS_DIR

def run_step4_segmentation(input_file, subject_id):
    """
    BƯỚC 4: SEGMENTATION (SYNTHSEG)
    Runs SynthSeg to generate segmentation (aseg.mgz).
    """
    print(f"\n[3/5] 🧠 ĐANG CHẠY SYNTHSEG 2.0 CHO {subject_id}...")
    
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    synthseg_script = os.path.join(base_dir, "mri_synthseg.py")
    model_path = os.path.join(base_dir, "models", "synthseg_2.0.h5")
    
    # Define output directory: <SUBJECTS_DIR>/<subject_id>/mri
    mri_dir = os.path.join(SUBJECTS_DIR, subject_id, "mri")
    os.makedirs(mri_dir, exist_ok=True)
    
    # Output file: aseg.mgz (Standard FreeSurfer naming)
    final_output_name = "aseg.mgz"
    expected_output = os.path.join(mri_dir, final_output_name)
    
    if os.path.exists(expected_output):
        print(f"✅ Đã có kết quả Segmentation: {expected_output}")
        return expected_output

    # Environment setup
    my_env = os.environ.copy()
    if "FREESURFER_HOME" not in my_env:
        my_env["FREESURFER_HOME"] = base_dir
        
    # Ensure python path includes base dir
    my_env["PYTHONPATH"] = base_dir + os.pathsep + my_env.get("PYTHONPATH", "")

    # Command: python mri_synthseg.py --i <input> --o <output> --threads 4 --noaddctab
    # We might want --parc if we need parcellation later
    cmd = [
        sys.executable, synthseg_script,
        "--i", input_file,
        "--o", expected_output,
        "--model", model_path,
        "--threads", "4",
        "--cpu",
        "--noaddctab",
        "--crop", "192"
    ]

    try:
        print(f" >>> Input: {input_file}")
        print(f" >>> Output: {expected_output}")
        print(f"     CMD: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd, 
            env=my_env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True
        )
        for line in process.stdout:
            print(line.strip())            
        process.wait()
        
        if process.returncode != 0:
            print("❌ Lỗi SynthSeg (Process returned non-zero code)")
            return None

        if os.path.exists(expected_output):
            print(f" ✅ Segmentation thành công: {expected_output}")
            return expected_output
        
        print(f"❌ Không tìm thấy output tại: {expected_output}")
        return None

    except Exception as e:
        print(f"❌ Lỗi gọi subprocess segment: {e}")
        return None
