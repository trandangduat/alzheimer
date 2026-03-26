import os
import subprocess
from config import run_cmd_logged

def run_step1_input_reorientation(input_path, subject_id, subjects_dir):
    """
    BƯỚC 1: INPUT REORIENTATION (Dùng FreeSurfer mri_convert --conform)
    Resamples image to 1mm isotropic, 256^3, and standard LIA orientation.
    Saves as mri/orig.mgz in the subject's directory.
    """
    print(f"\n[1/5] [STARTED] INPUT REORIENTATION CHO {subject_id} (mri_convert --conform)...")
    
    # Define subject mri directory
    # Structure: <subjects_dir>/<subject_id>/mri
    subject_dir = os.path.join(subjects_dir, subject_id)
    mri_dir = os.path.join(subject_dir, "mri")
    os.makedirs(mri_dir, exist_ok=True)
    
    # Output file: mri/orig.mgz (Standard FreeSurfer naming)
    final_path = os.path.join(mri_dir, "orig.mgz")

    try:
        print(f" -> Đang chạy mri_convert cho: {os.path.basename(input_path)}")
        
        # Command: mri_convert --conform input output
        cmd = ["mri_convert", "--conform", input_path, final_path]
        
        run_cmd_logged(cmd)
        
        if os.path.exists(final_path):
            print(f"[SUCCESS] Đã xử lý xong: {final_path}")

            # Tạo talairach.xfm
            transforms_dir = os.path.join(mri_dir, "transforms")
            os.makedirs(transforms_dir, exist_ok=True)
            talairach_xfm = os.path.join(transforms_dir, "talairach.xfm")

            print(f" -> Đang chạy talairach_avi...")
            cmd_tal = ["talairach_avi", "--i", final_path, "--xfm", talairach_xfm]
            run_cmd_logged(cmd_tal)
            print(f"[SUCCESS] Đã tạo talairach transform: {talairach_xfm}")

            return final_path
        else:
            print("[ERROR] File output không tồn tại sau khi chạy mri_convert.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Lỗi khi chạy mri_convert: {e.stderr}")
        return None
    except Exception as e:
        print(f"[ERROR] Lỗi xử lý Step 1 - Input Reorientation: {e}")
        return None
