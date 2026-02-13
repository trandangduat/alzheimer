import os
import sys
import subprocess
from config import TOOLS, SUBJECTS_DIR

def run_step5_cortical_flow(input_file, subject_id):
    """
    BƯỚC 5: CORTICAL SURFACE RECONSTRUCTION (CorticalFlow)
    Wrapper cho script recon_all.sh
    """
    print("\n[4/5] 🧠 ĐANG CHẠY CORTICALFLOW RECONSTRUCTION (Shell Script)...")
    
    # Define paths
    cortical_flow_root = TOOLS["cortical_flow_root"] 
    recon_script = "./recon_all.sh"
    
    # Environment Setup
    venv_path = os.path.join(cortical_flow_root, "cortical-flow")
    if sys.platform == "win32":
        venv_python = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_path, "bin", "python")
        
    # Output check
    expected_output_lh = os.path.join(SUBJECTS_DIR, subject_id, "surf", "lh.pial")
    
    if os.path.exists(expected_output_lh):
         print(f"✅ Đã có kết quả CorticalFlow cho {subject_id}")
         return os.path.join(SUBJECTS_DIR, subject_id)

    print(f" >>> Input: {input_file}")
    print(f" >>> Subject ID: {subject_id}")
    print(f" >>> Subjects Dir: {SUBJECTS_DIR}")
    print(f" >>> CWD: {cortical_flow_root}")

    # Prepare environment with venv python for the shell script to use
    env = os.environ.copy()
    if os.path.exists(venv_python):
        env["VENV_PYTHON"] = venv_python
        print(f" >>> Using python at: {venv_python}")
    else:
        print(f"⚠️ Warning: Venv python not found at {venv_python}. Relying on system default.")

    # Command: ./recon_all.sh <subject_id> <input_file> <subjects_dir>
    # Note: We run this from the CorticalFlow root directory so relative paths in script work
    cmd = [
        recon_script,
        subject_id,
        input_file,
        SUBJECTS_DIR
    ]

    try:
        print(f" >>> Executing: {' '.join(cmd)}")
        
        # Run subprocess
        process = subprocess.Popen(
            cmd,
            cwd=cortical_flow_root, # Run inside CorticalFlow folder
            env=env,
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
            
        print(f" ✅ CorticalFlow thành công. Output tại: {os.path.join(SUBJECTS_DIR, subject_id)}")
        return os.path.join(SUBJECTS_DIR, subject_id)

    except Exception as e:
        print(f"❌ Lỗi gọi subprocess CorticalFlow: {e}")
        return None
