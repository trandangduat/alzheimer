import os
import subprocess

def run_step1_input(input_path, subject_id, subjects_dir):
    """
    BƯỚC 1: XỬ LÝ ĐẦU VÀO (Dùng FreeSurfer mri_convert --conform)
    Resamples image to 1mm isotropic, 256^3, and standard LIA orientation.
    Saves as mri/orig.mgz in the subject's directory.
    """
    print(f"\n[1/5] 📥 ĐANG XỬ LÝ ĐẦU VÀO CHO {subject_id} (mri_convert --conform)...")
    
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
        
        print(f"    CMD: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # print(result.stdout) # Optional: print only if strict need
        
        if os.path.exists(final_path):
            print(f"✅ Đã xử lý xong: {final_path}")
            return final_path
        else:
            print("❌ Lỗi: File output không tồn tại sau khi chạy mri_convert.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi chạy mri_convert: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ Lỗi xử lý Step 1: {e}")
        return None
