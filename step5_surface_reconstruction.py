import os
import sys
import subprocess
from config import TOOLS, SUBJECTS_DIR, run_cmd_logged

def run_step5_surface_reconstruction(input_file, subject_id):
    """
    BƯỚC 5: SURFACE RECONSTRUCTION (CorticalFlow)
    Wrapper cho script recon_all.sh
    """
    print("\n[5/5] [STARTED] SURFACE RECONSTRUCTION (CorticalFlow)...")

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
        print(f"[SUCCESS] Đã có kết quả Surface Reconstruction cho {subject_id}")
        return os.path.join(SUBJECTS_DIR, subject_id)

    print(f" >>> Input: {input_file}")
    print(f" >>> Subject ID: {subject_id}")
    print(f" >>> Subjects Dir: {SUBJECTS_DIR}")
    print(f" >>> CWD: {cortical_flow_root}")

    # Prepare environment with venv python for the shell script to use
    env = os.environ.copy()
    
    # Lọc bỏ các biến của Conda để tránh xung đột thư viện C++ (libstdc++) khiến `import torch` bị treo
    keys_to_remove = [k for k in env if k.startswith("CONDA_")] + ["LD_LIBRARY_PATH", "PYTHONPATH"]
    for k in keys_to_remove:
        env.pop(k, None)
        
    if os.path.exists(venv_python):
        env["VENV_PYTHON"] = venv_python
        print(f" >>> Using python at: {venv_python}")
    else:
        print(f"[WARNING] Warning: Venv python not found at {venv_python}. Relying on system default.")

    # Command: ./recon_all.sh <subject_id> <input_file> <subjects_dir>
    cmd = [
        recon_script,
        subject_id,
        input_file,
        SUBJECTS_DIR
    ]

    try:
        try:
            run_cmd_logged(cmd, cwd=cortical_flow_root, env=env)
        except subprocess.CalledProcessError:
            print("[ERROR] Lỗi Surface Reconstruction (Exit Code != 0)")
            return None

        # Kiểm tra thực tế file output có tồn tại không
        expected_lh_pial  = os.path.join(SUBJECTS_DIR, subject_id, "surf", "lh.pial")
        expected_lh_white = os.path.join(SUBJECTS_DIR, subject_id, "surf", "lh.white")
        if not os.path.exists(expected_lh_pial) or not os.path.exists(expected_lh_white):
            print(f"[ERROR] Surface Reconstruction hoàn thành nhưng KHÔNG tạo ra file surf/lh.pial hoặc lh.white!")
            print(f"        Kiểm tra lại predict.py / recon_all.sh. Có thể thiếu dependency (omegaconf, pytorch3d...).")
            return None

        print(f" [SUCCESS] Surface Reconstruction thành công. Output tại: {os.path.join(SUBJECTS_DIR, subject_id)}")
        return os.path.join(SUBJECTS_DIR, subject_id)

    except Exception as e:
        print(f"[ERROR] Lỗi gọi subprocess Surface Reconstruction: {e}")
        return None

