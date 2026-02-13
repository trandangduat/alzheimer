import os
import shutil
import subprocess
import SimpleITK as sitk
from config import DIRS

def run_step2_3_preprocess(input_nifti):
    """
    BƯỚC 2 & 3: HD-BET & N4 (Giữ nguyên logic lệnh String cho Windows/Linux)
    """
    print("\n[2/5] 🛠️ ĐANG CHẠY PRE-PROCESSING (HD-BET & N4)...")
    output_dir = DIRS["step2_3"]
    # Expect input_nifti is absolute path from Step 1
    filename = os.path.basename(input_nifti).replace(".nii.gz", "")
    
    bet_output = os.path.join(output_dir, f"{filename}_bet.nii.gz")
    
    if os.path.exists(bet_output):
         print(" -> Đã có file HD-BET.")
    else:
        print(" >>> Đang chạy HD-BET (Mode: CPU)...")
        # Ensure input path is quoted
        cmd = f'hd-bet -i "{input_nifti}" -o "{bet_output}" -device cpu --disable_tta'
        try:
            subprocess.run(cmd, check=True, shell=True)
            print(" ✅ HD-BET hoàn tất.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Lỗi HD-BET: {e}")
            # Fallback copy if HD-BET fails (as per original logic)
            shutil.copy(input_nifti, bet_output)

    n4_output = os.path.join(output_dir, f"{filename}_final_preproc.nii.gz")

    # Simple check if "n4" is already in the original input filename (passed down implicitly? 
    # Original code checked `self.input_path`. Here we check input_nifti or just run it.)
    # The original logic `if "n4" in self.input_path.lower():` depends on the *original* input.
    # We will assume if "n4" is in the filename we skip it, otherwise run it.
    
    if "n4" in filename.lower(): 
        print(" -> File name contains 'n4', skipping N4 correction.")
        shutil.copy(bet_output, n4_output)
    else:
        print(" >>> Đang chạy N4 Bias Correction...")
        try:
            img = sitk.ReadImage(bet_output, sitk.sitkFloat32)
            corrector = sitk.N4BiasFieldCorrectionImageFilter()
            corrector.SetMaximumNumberOfIterations([20, 20, 20])
            img_corrected = corrector.Execute(img)
            sitk.WriteImage(img_corrected, n4_output)
            print(" ✅ Xong N4.")
        except Exception as e:
            print(f"❌ Lỗi N4: {e}")
            shutil.copy(bet_output, n4_output)
    
    return n4_output
