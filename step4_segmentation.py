import os
import sys
import subprocess
from config import DIRS, TOOLS

def run_step4_segmentation(input_nifti):
    """
    BƯỚC 4: SEGMENTATION (ĐÃ KHÔI PHỤC LOGIC STREAMING LOG CŨ)
    Runs FastSurfer analysis.
    """
    print("\n[3/5] 🧠 ĐANG CHẠY FASTSURFER AI (Mode: CPU)...")
    output_dir = DIRS["step4"]
    fastsurfer_root = TOOLS['fastsurfer_root']
    script_path = os.path.join(fastsurfer_root, "FastSurferCNN", "run_prediction.py")
    
    sid = os.path.basename(input_nifti).replace(".nii.gz", "").replace("_final_preproc", "")
    mri_dir = os.path.join(output_dir, sid, "mri")
    expected_output = os.path.join(mri_dir, "aparc.DKTatlas+aseg.deep.mgz")
    
    if os.path.exists(expected_output):
        print(f"✅ Đã có kết quả Segmentation: {expected_output}")
        return expected_output

    # Environment setup
    cmd = [
        sys.executable, script_path,
        "--t1", input_nifti,
        "--sd", output_dir,
        "--sid", sid,
        "--device", "cpu",
        "--viewagg_device", "cpu",
        "--batch_size", "1"
    ]
    
    my_env = os.environ.copy()
    my_env["PYTHONPATH"] = fastsurfer_root + os.pathsep + my_env.get("PYTHONPATH", "")

    try:
        print(f" >>> Đang xử lý Subject: {sid}...")
        
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
             print("❌ Lỗi FastSurfer (Process returned non-zero code)")
             return None

        if os.path.exists(mri_dir):
            if os.path.exists(expected_output):
                print(f" ✅ Segmentation thành công: {expected_output}")
                return expected_output
            
            # Fallback tìm file mgz khác
            found = [f for f in os.listdir(mri_dir) if f.endswith(".mgz")]
            if found: 
                print(f" ✅ Tìm thấy file output: {found[0]}")
                return os.path.join(mri_dir, found[0])
        
        print(f"❌ Không tìm thấy output tại: {mri_dir}")
        return None

    except Exception as e:
        print(f"❌ Lỗi gọi subprocess segment: {e}")
        return None
