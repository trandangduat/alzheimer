import os
from config import SUBJECTS_DIR, run_cmd_logged

def run_step3_brain_extraction(subject_id):
    """
    BƯỚC 3: BRAIN EXTRACTION (HD-BET Skull Stripping)
    Input: mri/orig.mgz
    Outputs:
        - mri/skullstrip.mgz  (Brain extracted image)
        - mri/brainmask.mgz   (Brain mask applied to T1)
    """
    print(f"\n[3/5] [PROCESSING] BRAIN EXTRACTION (HD-BET Skull Stripping) for {subject_id}...")

    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    mri_dir = os.path.join(subj_dir, "mri")
    orig_mgz = os.path.join(mri_dir, "orig.mgz")
    t1_mgz = os.path.join(mri_dir, "T1.mgz")

    if not os.path.exists(orig_mgz):
        print(f"[ERROR] Input not found: {orig_mgz}")
        return None

    # Outputs
    skullstrip_mgz = os.path.join(mri_dir, "skullstrip.mgz")
    brainmask_mgz = os.path.join(mri_dir, "brainmask.mgz")

    # Temp files (NIfTI for HD-BET)
    temp_orig_nii = os.path.join(mri_dir, "temp_orig.nii.gz")
    temp_bet_nii = os.path.join(mri_dir, "temp_bet.nii.gz")

    try:
        # Helper to run commands
        def run_cmd(cmd):
            run_cmd_logged(cmd, shell=True, executable='/bin/bash')

        # Convert orig.mgz to NIfTI if not already done
        if not os.path.exists(temp_orig_nii):
            run_cmd(f"mri_convert {orig_mgz} {temp_orig_nii}")

        # --- A. SKULL STRIPPING ---
        if not os.path.exists(skullstrip_mgz):
            from config import USE_SYNTHSTRIP
            if USE_SYNTHSTRIP:
                print(" >>> Running SynthStrip (Skull Stripping)...")
                # mri_synthstrip -i input -o output -m mask
                run_cmd(f"mri_synthstrip -i {temp_orig_nii} -o {temp_bet_nii} -m {mri_dir}/brainmask_synth.nii.gz")
            else:
                print(" >>> Running HD-BET (Skull Stripping)...")
                run_cmd(f"hd-bet -i {temp_orig_nii} -o {temp_bet_nii} -device cpu --disable_tta")

            if not os.path.exists(temp_bet_nii):
                print(f"[ERROR] Brain extraction failed to create {temp_bet_nii}")
                return None

            # Convert back to mgz
            run_cmd(f"mri_convert {temp_bet_nii} {skullstrip_mgz}")
            print(f" [SUCCESS] Created: {skullstrip_mgz}")
        else:
            print(f" -> Found existing skullstrip: {skullstrip_mgz}")

        # --- B. BRAIN MASKING ---
        if not os.path.exists(brainmask_mgz):
            print(" >>> Running mri_mask (Create brainmask.mgz)...")
            # Requires T1.mgz from Step 2
            if not os.path.exists(t1_mgz):
                print(f"[ERROR] T1.mgz not found at {t1_mgz}. Run Step 2 first.")
                return None
            run_cmd(f"mri_mask {t1_mgz} {skullstrip_mgz} {brainmask_mgz}")
            print(f" [SUCCESS] Created: {brainmask_mgz}")
        else:
            print(f" -> Found existing brainmask: {brainmask_mgz}")

        # Cleanup temp files (optional)
        # os.remove(temp_orig_nii)
        # os.remove(temp_bet_nii)

        return brainmask_mgz

    except Exception as e:
        print(f"[ERROR] Error in Step 3 - Brain Extraction: {e}")
        return None
