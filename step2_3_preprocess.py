import os
import shutil
import subprocess
import SimpleITK as sitk
from config import SUBJECTS_DIR

def run_step2_3_preprocess(subject_id):
    """
    BƯỚC 2 & 3: Skull Stripping (HD-BET), N4 Bias Correction, Normalization, Masking.
    Input: mri/orig.mgz
    Outputs: 
        - mri/skullstrip.mgz
        - mri/nu.mgz
        - mri/T1.mgz
        - mri/brainmask.mgz
    """
    print(f"\n[2-3/5] 🛠️ PRE-PROCESSING (Skull Strip, N4, Normalize) for {subject_id}...")
    
    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    mri_dir = os.path.join(subj_dir, "mri")
    orig_mgz = os.path.join(mri_dir, "orig.mgz")
    
    if not os.path.exists(orig_mgz):
        print(f"❌ Input not found: {orig_mgz}")
        return None

    # Outputs
    skullstrip_mgz = os.path.join(mri_dir, "skullstrip.mgz")
    nu_mgz = os.path.join(mri_dir, "nu.mgz")
    t1_mgz = os.path.join(mri_dir, "T1.mgz")
    brainmask_mgz = os.path.join(mri_dir, "brainmask.mgz")

    # Temp files (NIfTI for HD-BET/N4)
    temp_orig_nii = os.path.join(mri_dir, "temp_orig.nii.gz")
    temp_bet_nii = os.path.join(mri_dir, "temp_bet.nii.gz")
    temp_nu_nii = os.path.join(mri_dir, "temp_nu.nii.gz")

    try:
        # Helper to run commands
        def run_cmd(cmd):
            print(f"    CMD: {cmd}")
            subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')

        # Convert orig.mgz to NIfTI for processing
        if not os.path.exists(temp_orig_nii):
            run_cmd(f"mri_convert {orig_mgz} {temp_orig_nii}")

        # --- A. SKULL STRIPPING (HD-BET) ---
        if not os.path.exists(skullstrip_mgz):
            print(" >>> Running HD-BET (Skull Stripping)...")
            # HD-BET
            # Note: HD-BET output filename logic might append _bet if not specified exactly?
            # We specify -o.
            run_cmd(f"hd-bet -i {temp_orig_nii} -o {temp_bet_nii} -device cpu --disable_tta")
            
            # Convert back to mgz
            run_cmd(f"mri_convert {temp_bet_nii} {skullstrip_mgz}")
            print(f" ✅ Created: {skullstrip_mgz}")
        else:
            print(f" -> Found existing skullstrip: {skullstrip_mgz}")

        # --- B. N4 BIAS CORRECTION ---
        if not os.path.exists(nu_mgz):
            print(" >>> Running N4 Bias Correction...")
            # Use SimpleITK on the temp_orig_nii (Whole Head)
            img = sitk.ReadImage(temp_orig_nii, sitk.sitkFloat32)
            corrector = sitk.N4BiasFieldCorrectionImageFilter()
            corrector.SetMaximumNumberOfIterations([20, 20, 20]) # Simplified params
            img_corrected = corrector.Execute(img)
            sitk.WriteImage(img_corrected, temp_nu_nii)
            
            # Convert to mgz
            run_cmd(f"mri_convert {temp_nu_nii} {nu_mgz}")
            print(f" ✅ Created: {nu_mgz}")
        else:
            print(f" -> Found existing nu: {nu_mgz}")

        # --- C. NORMALIZATION ---
        if not os.path.exists(t1_mgz):
            print(" >>> Running mri_normalize...")
            # mri_normalize -g 1 -seed 1234 -mprage nu.mgz T1.mgz
            run_cmd(f"mri_normalize -g 1 -seed 1234 -mprage {nu_mgz} {t1_mgz}")
            print(f" ✅ Created: {t1_mgz}")
        else:
            print(f" -> Found existing T1: {t1_mgz}")

        # --- D. BRAIN MASKING ---
        if not os.path.exists(brainmask_mgz):
            print(" >>> Running mri_mask (Create brainmask.mgz)...")
            # mri_mask mri/T1.mgz mri/skullstrip.mgz mri/brainmask.mgz
            run_cmd(f"mri_mask {t1_mgz} {skullstrip_mgz} {brainmask_mgz}")
            print(f" ✅ Created: {brainmask_mgz}")
        else:
             print(f" -> Found existing brainmask: {brainmask_mgz}")

        # Cleanup temp files (optional, keeping for debug or removing?)
        # os.remove(temp_orig_nii)
        # os.remove(temp_bet_nii)
        # os.remove(temp_nu_nii)

        return brainmask_mgz

    except Exception as e:
        print(f"❌ Error in Step 2-3: {e}")
        return None
