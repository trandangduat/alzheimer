import os
from config import SUBJECTS_DIR, run_cmd_logged

def run_step8_anatomical_stats(subject_id):
    """
    BƯỚC 8: ANATOMICAL STATS (mris_anatomical_stats)
    Input: label/?h.aparc.annot
    Output: stats/?h.aparc.stats
    """
    print(f"\n[8/8] [PROCESSING] ANATOMICAL STATS (mris_anatomical_stats) for {subject_id}...")
    
    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    label_dir = os.path.join(subj_dir, "label")
    stats_dir = os.path.join(subj_dir, "stats")
    os.makedirs(stats_dir, exist_ok=True)

    results = []
    for hemi in ["lh", "rh"]:
        annot = os.path.join(label_dir, f"{hemi}.aparc.annot")
        if not os.path.exists(annot):
            print(f"[WARNING] Annotation not found for {hemi} at {annot}. Skipping.")
            continue
            
        out_stats = os.path.join(stats_dir, f"{hemi}.aparc.stats")
        
        print(f" >>> Running mris_anatomical_stats for {hemi}...")
        # mris_anatomical_stats -a <annot> -f <output> <subject> <hemi> <surf>
        # Usually runs on 'pial' or 'white' surface. Using 'pial' as it's common for thickness.
        
        cmd = [
            "mris_anatomical_stats",
            "-a", annot,
            "-f", out_stats,
            subject_id,
            hemi,
            "pial"
        ]
        
        try:
            run_cmd_logged(cmd)
            print(f" [SUCCESS] Created: {out_stats}")
            results.append(out_stats)
        except Exception as e:
            print(f"[ERROR] Anatomical stats failed for {hemi}: {e}")
            
    return results if results else None
