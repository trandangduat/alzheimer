import os
import subprocess
import nibabel as nib
import numpy as np
from config import SUBJECTS_DIR, TOOLS, run_cmd_logged

# SUGAR chỉ hỗ trợ lh (left hemisphere) hiện tại
SUGAR_HEMIS = ["lh"]

# Docker image của SUGAR
SUGAR_DOCKER_IMAGE = "ninganme/sugar:latest"

def run_step6_registration(subject_id):
    """
    BƯỚC 6: CORTICAL SURFACE REGISTRATION (SUGAR via Docker)
    Input:  subjects/{subject_id}/surf/lh.sphere
            subjects/{subject_id}/surf/lh.curv
            subjects/{subject_id}/surf/lh.sulc
    Output: subjects/{subject_id}/surf/lh.sphere.reg
    
    SUGAR được chạy trong Docker container (ninganme/sugar:latest).
    Kết quả đầu ra được mount vào thư mục tạm rồi copy về surf/.
    NOTE: SUGAR hiện chỉ hỗ trợ hemisphere "lh".
    """
    print(f"\n[6/8] [PROCESSING] CORTICAL SURFACE REGISTRATION (SUGAR) for {subject_id}...")

    subj_dir    = os.path.join(SUBJECTS_DIR, subject_id)
    surf_dir    = os.path.join(subj_dir, "surf")

    # Thư mục output tạm cho SUGAR (bên ngoài container, được mount vào /out)
    sugar_out_dir = os.path.join(subj_dir, "sugar_out")
    os.makedirs(sugar_out_dir, exist_ok=True)

    results = []

    for hemi in SUGAR_HEMIS:
        white  = os.path.join(surf_dir, f"{hemi}.white")
        sphere = os.path.join(surf_dir, f"{hemi}.sphere")
        curv   = os.path.join(surf_dir, f"{hemi}.curv")
        sulc   = os.path.join(surf_dir, f"{hemi}.sulc")

        if not os.path.exists(white):
            print(f"[ERROR] Missing {hemi}.white for registration. Skipping {hemi}.")
            continue

        # ── Tạo các file đầu vào còn thiếu ──────────────────────────────────
        if not os.path.exists(sphere) or not os.path.exists(curv) or not os.path.exists(sulc):
            print(f" >>> Generating missing FreeSurfer files for {hemi}...")

            # smoothwm symlink (mris_sphere yêu cầu)
            smoothwm = os.path.join(surf_dir, f"{hemi}.smoothwm")
            if not os.path.exists(smoothwm):
                os.symlink(os.path.basename(white), smoothwm)

            # mris_inflate → sinh ra inflated & sulc
            inflated = os.path.join(surf_dir, f"{hemi}.inflated")
            if not os.path.exists(inflated) or not os.path.exists(sulc):
                print(f"     -> Running mris_inflate (this may take a few minutes)...")
                run_cmd_logged(["mris_inflate", white, inflated])

            # mris_sphere → sinh ra sphere
            if not os.path.exists(sphere):
                print(f"     -> Running mris_sphere (this may take a few minutes)...")
                run_cmd_logged(["mris_sphere", "-w", "0", inflated, sphere])

            # mris_curvature → sinh ra curv
            if not os.path.exists(curv):
                print(f"     -> Running mris_curvature...")
                run_cmd_logged(["mris_curvature", "-w", white])
                temp_h = f"{white}.H"
                if os.path.exists(temp_h):
                    os.rename(temp_h, curv)
                elif os.path.exists(f"{white}.curv"):
                    os.rename(f"{white}.curv", curv)

        if not all(os.path.exists(p) for p in [sphere, curv, sulc]):
            print(f"[ERROR] Could not generate missing inputs for {hemi} registration. Skipping.")
            continue

        # ── Chạy SUGAR qua Docker ────────────────────────────────────────────
        # Mount:
        #   SUBJECTS_DIR  → /data   (SUGAR đọc subject qua --sd /data --sid <id>)
        #   sugar_out_dir → /out    (SUGAR ghi kết quả vào /out/<sid>/surf/)
        out_reg = os.path.join(surf_dir, f"{hemi}.sphere.reg")

        print(f" >>> Running SUGAR (Docker) for {hemi}...")

        docker_cmd = [
            "sudo", "docker", "run",
            "--rm",
            "--gpus", "all",
            "-v", f"{SUBJECTS_DIR}:/data",
            "-v", f"{sugar_out_dir}:/out",
            SUGAR_DOCKER_IMAGE,
            "--fsd", "/usr/local/freesurfer",
            "--sd",  "/data",
            "--out", "/out",
            "--sid", subject_id,
            "--hemi", hemi,
            "--device", "cuda",
        ]

        try:
            run_cmd_logged(docker_cmd)

            # SUGAR ghi: /out/<sid>/surf/lh.sphere.reg
            sugar_result = os.path.join(sugar_out_dir, subject_id, "surf", f"{hemi}.sphere.reg")

            if not os.path.exists(sugar_result):
                print(f"[ERROR] SUGAR did not produce {sugar_result}. Skipping {hemi}.")
                continue

            # Copy kết quả vào surf/ của subject
            import shutil
            shutil.copy2(sugar_result, out_reg)
            print(f" [SUCCESS] Created: {out_reg}")
            results.append(out_reg)

        except Exception as e:
            print(f"[ERROR] SUGAR registration failed for {hemi}: {e}")

    return results if results else None
