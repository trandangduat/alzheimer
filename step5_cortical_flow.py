import os
import sys
import subprocess
from config import DIRS, TOOLS, OUTPUT_ROOT

def run_step5_cortical_flow(input_nifti):
    """
    BƯỚC 5: CORTICAL SURFACE RECONSTRUCTION (CorticalFlow)
    Wrapper cho script recon_all.sh trong folder CorticalFlow
    """
    print("\n[4/5] 🧠 ĐANG CHẠY CORTICALFLOW RECONSTRUCTION...")
    
    # Define paths
    output_dir = DIRS.get("step5", os.path.join(OUTPUT_ROOT, "step5_cortical_flow"))
    cortical_flow_root = TOOLS["cortical_flow_root"] # e.g. .../tools/CorticalFlow
    recon_script = "./recon_all.sh"
    
    # Environment Setup
    # The 'cortical-flow' folder IS the venv
    venv_path = os.path.join(cortical_flow_root, "cortical-flow")
    venv_bin = os.path.join(venv_path, "bin") # Linux/MacOS
    
    # Path handling
    input_dir = os.path.dirname(input_nifti)
    fname = os.path.basename(input_nifti)
    
    # Handle filename extensions to get ID
    # Usually: subject_01.nii.gz
    if fname.endswith(".nii.gz"):
        sid = fname[:-7]
    elif fname.endswith(".nii"):
        sid = fname[:-4]
    else:
        sid = os.path.splitext(fname)[0]
        
    # Remove preprocessing suffixes if present (adjust logic as needed)
    sid = sid.replace("_final_preproc", "").replace("_conform", "")

    # Output check
    expected_output_lh = os.path.join(output_dir, sid, "CFPP", sid, f"{sid}_lh_white_native.pial")
    if os.path.exists(expected_output_lh):
         print(f"✅ Đã có kết quả CorticalFlow cho {sid}")
         return os.path.join(output_dir, sid)

    print(f" >>> Input: {input_nifti}")
    print(f" >>> Subject ID: {sid}")
    print(f" >>> Input Dir: {input_dir}")
    print(f" >>> CWD: {cortical_flow_root}")

    # Prepare environment with venv at the front of PATH
    env = os.environ.copy()
    if os.path.exists(venv_bin):
        env["PATH"] = venv_bin + os.pathsep + env["PATH"]
        print(f" >>> Using venv at: {venv_path}")
    else:
        print(f"⚠️ Warning: Venv bin not found at {venv_bin}. Relying on system PATH.")

    # Command: ./recon_all.sh <subject_id> <input_file> <output_dir>
    # NOTE: Modified logic to pass full file path, as recon_all.sh was updated to support this.
    cmd = [recon_script, sid, input_nifti, output_dir]

    try:
        print(f" >>> Executing: {' '.join(cmd)}")
        
        # Run subprocess
        process = subprocess.Popen(
            cmd,
            cwd=cortical_flow_root, # Run inside CorticalFlow folder
            env=env,                # With venv in PATH
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Stream output
        for line in process.stdout:
            print(line.strip())
            
        process.wait()
        
        if process.returncode != 0:
            print("❌ Lỗi CorticalFlow Reconstruction (Exit Code != 0)")
            return None
            
        print(f" ✅ CorticalFlow thành công. Output tại: {os.path.join(output_dir, sid)}")
        return os.path.join(output_dir, sid)

    except Exception as e:
        print(f"❌ Lỗi gọi subprocess CorticalFlow: {e}")
        return None
