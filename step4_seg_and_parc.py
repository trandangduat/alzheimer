import os
import sys
import subprocess
import shutil
from config import SUBJECTS_DIR, run_cmd_logged


TEMP_SYNTHSEG_ROOT = "/mnt/c/Users/ADMIN/Desktop/MRI/frsf_output_9patients"


def _find_temp_synthseg_rca(subject_id):
    """Return a temporary synthseg.rca.mgz path if one exists for the subject."""
    candidates = [
        os.path.join(TEMP_SYNTHSEG_ROOT, subject_id, "mri", "synthseg.rca.mgz"),
        os.path.join(TEMP_SYNTHSEG_ROOT, subject_id, "synthseg.rca.mgz"),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    if os.path.isdir(TEMP_SYNTHSEG_ROOT):
        for root, _, files in os.walk(TEMP_SYNTHSEG_ROOT):
            if "synthseg.rca.mgz" in files and subject_id in root:
                return os.path.join(root, "synthseg.rca.mgz")

    return None


def run_step4_seg_and_parc(input_file, subject_id):
    """
    BƯỚC 4: SEG AND PARC (Subcortical Segmentation & Cortical Parcellation)
    Runs SynthSeg with --parc flag to generate both subcortical segmentation
    and cortical parcellation (aseg+aparc.mgz).
    """
    print(
        f"\n[4/5] [STARTED] SEG AND PARC (Subcortical Segmentation & Cortical Parcellation) CHO {subject_id}..."
    )

    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    synthseg_script = os.path.join(base_dir, "mri_synthseg.py")
    model_path = os.path.join(base_dir, "models", "synthseg_2.0.h5")

    # Define output directory: <SUBJECTS_DIR>/<subject_id>/mri
    mri_dir = os.path.join(SUBJECTS_DIR, subject_id, "mri")
    stats_dir = os.path.join(SUBJECTS_DIR, subject_id, "stats")
    os.makedirs(mri_dir, exist_ok=True)
    os.makedirs(stats_dir, exist_ok=True)

    # Output file: aseg+aparc.mgz
    final_output_name = "aseg+aparc.mgz"
    expected_output = os.path.join(mri_dir, final_output_name)
    segstat_path = os.path.join(stats_dir, "synthseg.vol.csv")

    if os.path.exists(expected_output):
        print(f"[SUCCESS] Đã có kết quả Seg and Parc: {expected_output}")
        return expected_output

    temp_rca = _find_temp_synthseg_rca(subject_id)
    if temp_rca:
        try:
            shutil.copy2(temp_rca, expected_output)
            print(
                f"[SUCCESS] Dùng tạm synthseg.rca.mgz cho {subject_id}: {expected_output}"
            )
            return expected_output
        except Exception as e:
            print(
                f"[WARNING] Không thể copy synthseg.rca.mgz sang {expected_output}: {e}"
            )

    # Environment setup
    my_env = os.environ.copy()
    if "FREESURFER_HOME" not in my_env:
        my_env["FREESURFER_HOME"] = base_dir

    # Ensure python path includes base dir
    my_env["PYTHONPATH"] = base_dir + os.pathsep + my_env.get("PYTHONPATH", "")

    cmd = [
        sys.executable,
        synthseg_script,
        "--i",
        input_file,
        "--o",
        expected_output,
        "--model",
        model_path,
        "--threads",
        "4",
        "--vol",
        segstat_path,
        "--addctab",
        "--keepgeom",
        "--cpu",
        # "--parc",
        # "--crop", "192"
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
