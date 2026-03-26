import os
from config import SUBJECTS_DIR, FREESURFER_AVERAGE_DIR, run_cmd_logged

def run_step7_parcellation(subject_id):
    """
    BƯỚC 7: PARCELLATION (mris_ca_label)
    Input: surf/?h.sphere.reg
    Output: label/?h.aparc.annot
    """
    print(f"\n[7/8] [PROCESSING] PARCELLATION (mris_ca_label) for {subject_id}...")
    
    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    surf_dir = os.path.join(subj_dir, "surf")
    label_dir = os.path.join(subj_dir, "label")
    os.makedirs(label_dir, exist_ok=True)

    results = []
    for hemi in ["lh", "rh"]:
        sphere_reg = os.path.join(surf_dir, f"{hemi}.sphere.reg")
        if not os.path.exists(sphere_reg):
            print(f"[WARNING] Registered sphere not found for {hemi} at {sphere_reg}. Skipping.")
            continue
            
        out_annot = os.path.join(label_dir, f"{hemi}.aparc.annot")
        
        # Classifier file for Desikan-Killiany atlas
        classifier = os.path.join(FREESURFER_AVERAGE_DIR, f"{hemi}.curvature.buckner40.filled.desikan_killiany.2010-03-25.gcs")
        
        if not os.path.exists(classifier):
            print(f"[ERROR] Classifier not found: {classifier}")
            continue

        print(f" >>> Running mris_ca_label for {hemi}...")
        # mris_ca_label [options] <subject> <hemi> <surf> <classifier> <output_annot>
        # Note: <subject> is just a string, but FreeSurfer usually looks for it in SUBJECTS_DIR 
        # However, we can use the subject name and let it find the files since we set SUBJECTS_DIR env in main.py
        
        cmd = [
            "mris_ca_label",
            subject_id,
            hemi,
            sphere_reg,
            classifier,
            out_annot
        ]
        
        try:
            run_cmd_logged(cmd)
            print(f" [SUCCESS] Created: {out_annot}")
            results.append(out_annot)
        except Exception as e:
            print(f"[ERROR] Parcellation failed for {hemi}: {e}")
            
    return results if results else None
