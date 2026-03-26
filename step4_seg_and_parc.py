import os
import sys
import subprocess
from config import SUBJECTS_DIR, run_cmd_logged

def run_step4_seg_and_parc(input_file, subject_id):
    """
    BƯỚC 4: SEG AND PARC (Subcortical Segmentation & Cortical Parcellation)
    Runs SynthSeg with --parc flag to generate both subcortical segmentation
    and cortical parcellation (aseg+aparc.mgz).
    """
    print(f"\n[4/5] [STARTED] SEG AND PARC (Subcortical Segmentation & Cortical Parcellation) CHO {subject_id}...")

    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    synthseg_script = os.path.join(base_dir, "mri_synthseg.py")
    model_path = os.path.join(base_dir, "models", "synthseg_2.0.h5")

    # Define output directory: <SUBJECTS_DIR>/<subject_id>/mri
    mri_dir = os.path.join(SUBJECTS_DIR, subject_id, "mri")
    os.makedirs(mri_dir, exist_ok=True)

    # Output file: aseg+aparc.mgz
    final_output_name = "aseg+aparc.mgz"
    expected_output = os.path.join(mri_dir, final_output_name)

    if os.path.exists(expected_output):
        print(f"[SUCCESS] Đã có kết quả Seg and Parc: {expected_output}")
        return expected_output

    # Environment setup
    my_env = os.environ.copy()
    if "FREESURFER_HOME" not in my_env:
        my_env["FREESURFER_HOME"] = base_dir

    # Ensure python path includes base dir
    my_env["PYTHONPATH"] = base_dir + os.pathsep + my_env.get("PYTHONPATH", "")

    cmd = [
        sys.executable, synthseg_script,
        "--i", input_file,
        "--o", expected_output,
        "--model", model_path,
        # "--threads", "1",
        "--cpu",
        "--parc",
        "--noaddctab",
        "--crop", "192"
    ]

    try:
        print(f" >>> Input: {input_file}")
        print(f" >>> Output: {expected_output}")

        try:
            run_cmd_logged(cmd, env=my_env)
        except subprocess.CalledProcessError:
            print("[ERROR] Lỗi SynthSeg (Process returned non-zero code)")
            return None

        if os.path.exists(expected_output):
            print(f" [SUCCESS] Seg and Parc thành công: {expected_output}")
            return expected_output

        print(f"[ERROR] Không tìm thấy output tại: {expected_output}")
        return None

    except Exception as e:
        print(f"[ERROR] Lỗi gọi subprocess Seg and Parc: {e}")
        return None
