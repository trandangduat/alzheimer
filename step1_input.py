import os
import subprocess
from config import DIRS

def run_step1_input(input_path):
    """
    BƯỚC 1: XỬ LÝ ĐẦU VÀO (Dùng FreeSurfer mri_convert --conform)
    Resamples image to 1mm isotropic, 256^3, and standard LIA orientation.
    """
    print("\n[1/5] 📥 ĐANG XỬ LÝ ĐẦU VÀO (mri_convert --conform)...")
    output_dir = DIRS["step1"]
    filename = os.path.basename(input_path)
    base_name = filename.replace(".img", "").replace(".nii.gz", "").replace(".nii", "")
    final_path = os.path.join(output_dir, base_name + "_conform.img") # mri_convert often defaults to mgz if not specified, but let's stick to nii.gz or img if user wants. FS usually likes mgz. Let's use .nii.gz for compatibility with other tools if needed, but 'orig.mgz' suggests mgz. 
    # User's request said "ensure output looks like mri/orig.mgz". 
    # Let's output .nii.gz for now as the pipeline expects it, but formatted correctly.
    final_path = os.path.join(output_dir, base_name + "_conform.nii.gz")

    try:
        print(f" -> Đang chạy mri_convert cho: {filename}")
        
        # Command: mri_convert --conform input output
        cmd = ["mri_convert", "--conform", input_path, final_path]
        
        print(f"    CMD: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(result.stdout)
        
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
