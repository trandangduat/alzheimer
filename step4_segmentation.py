import os
import sys
import subprocess
from config import DIRS, TOOLS

def run_step4_segmentation(input_nifti):
    """
    BƯỚC 4: SEGMENTATION (ĐÃ KHÔI PHỤC LOGIC STREAMING LOG CŨ)
    Runs FastSurfer analysis.
    """
    print("\n[3/5] 🧠 ĐANG CHẠY SYNTHSEG 2.0 (Mode: CPU)...")
    output_dir = DIRS["step4"]
    # Assuming mri_synthseg.py is in the base directory based on previous list_dir
    # And models are in 'models' subdirectory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    synthseg_script = os.path.join(base_dir, "mri_synthseg.py")
    
    sid = os.path.basename(input_nifti).replace(".nii.gz", "").replace("_conform", "") # Step 1 output suffix is _conform
    mri_dir = os.path.join(output_dir, sid, "mri")
    os.makedirs(mri_dir, exist_ok=True)
    
    # SynthSeg typical output: aseg.mgz or we can name it explicitly.
    # To mimic FreeSurfer/FastSurfer structure used downstream, we'll name it aparc.DKTatlas+aseg.deep.mgz (or similar) or just aseg.mgz
    # Step 7 stats usually looks for 'aparc.DKTatlas+aseg.deep.mgz' (from FastSurfer) or 'aseg.mgz' (FreeSurfer).
    # Let's align with what FastSurfer produced: aparc.DKTatlas+aseg.deep.mgz 
    final_output_name = "aseg.mgz"
    expected_output = os.path.join(mri_dir, final_output_name)
    
    if os.path.exists(expected_output):
        print(f"✅ Đã có kết quả Segmentation: {expected_output}")
        return expected_output

    # Environment setup
    # SynthSeg requires FREESURFER_HOME to find models folder (which is expected to be in FREESURFER_HOME/models)
    # Here we set FREESURFER_HOME to base_dir since 'models' is there.
    my_env = os.environ.copy()
    my_env["FREESURFER_HOME"] = base_dir
    # Ensure python path includes base dir
    my_env["PYTHONPATH"] = base_dir + os.pathsep + my_env.get("PYTHONPATH", "")

    # Command: python mri_synthseg.py --i <input> --o <output> --cpu --threads 4 --noaddctab
    cmd = [
        sys.executable, synthseg_script,
        "--i", input_nifti,
        "--o", expected_output,
        # "--cpu",
        "--threads", "4",
        "--noaddctab"
    ]

    try:
        print(f" >>> Đang xử lý Subject: {sid}...")
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
