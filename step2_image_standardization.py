import os
import SimpleITK as sitk
from config import SUBJECTS_DIR, run_cmd_logged

def run_step2_image_standardization(subject_id):
    """
    BƯỚC 2: IMAGE STANDARDIZATION (nu, t1)
    N4 Bias Correction và Normalization.
    Input: mri/orig.mgz
    Outputs:
        - mri/nu.mgz   (N4 Bias Corrected)
        - mri/T1.mgz   (Normalized)
    """
    print(f"\n[2/5] [PROCESSING] IMAGE STANDARDIZATION (N4 Bias Correction, Normalize) for {subject_id}...")

    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    mri_dir = os.path.join(subj_dir, "mri")
    orig_mgz = os.path.join(mri_dir, "orig.mgz")

    if not os.path.exists(orig_mgz):
        print(f"[ERROR] Input not found: {orig_mgz}")
        return None

    # Outputs
    nu_mgz = os.path.join(mri_dir, "nu.mgz")
    t1_mgz = os.path.join(mri_dir, "T1.mgz")

    # Temp files (NIfTI for N4)
    temp_orig_nii = os.path.join(mri_dir, "temp_orig.nii.gz")
    temp_nu_nii = os.path.join(mri_dir, "temp_nu.nii.gz")

    try:
        # Helper to run commands
        def run_cmd(cmd):
            run_cmd_logged(cmd, shell=True, executable='/bin/bash')

        # Convert orig.mgz to NIfTI for processing
        if not os.path.exists(temp_orig_nii):
            run_cmd(f"mri_convert {orig_mgz} {temp_orig_nii}")

        # --- A. N4 BIAS CORRECTION ---
        if not os.path.exists(nu_mgz):
            print(" >>> Running N4 Bias Correction...")
            img = sitk.ReadImage(temp_orig_nii, sitk.sitkFloat32)
            corrector = sitk.N4BiasFieldCorrectionImageFilter()
            corrector.SetMaximumNumberOfIterations([20, 20, 20])
            img_corrected = corrector.Execute(img)
            sitk.WriteImage(img_corrected, temp_nu_nii)

            # Convert to mgz
            run_cmd(f"mri_convert {temp_nu_nii} {nu_mgz}")
            print(f" [SUCCESS] Created: {nu_mgz}")
        else:
            print(f" -> Found existing nu: {nu_mgz}")

        # --- B. NORMALIZATION ---
        if not os.path.exists(t1_mgz):
            print(" >>> Running mri_normalize...")
            run_cmd(f"mri_normalize -g 1 -seed 1234 -mprage {nu_mgz} {t1_mgz}")
            print(f" [SUCCESS] Created: {t1_mgz}")
        else:
            print(f" -> Found existing T1: {t1_mgz}")

        return t1_mgz

    except Exception as e:
        print(f"[ERROR] Error in Step 2 - Image Standardization: {e}")
        return None
