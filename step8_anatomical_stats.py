import os
from config import SUBJECTS_DIR, run_cmd_logged

def run_step8_anatomical_stats(subject_id):
    """
    BƯỚC 8: ANATOMICAL STATS (mris_anatomical_stats)
    Input: label/?h.aparc.schaefer2018_200_7.annot
    Output: stats/?h.aparc.schaefer2018_200_7.stats
    """
    print(f"\n[8/8] [PROCESSING] ANATOMICAL STATS (mris_anatomical_stats) for {subject_id}...")
    
    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    surf_dir = os.path.join(subj_dir, "surf")
    label_dir = os.path.join(subj_dir, "label")
    stats_dir = os.path.join(subj_dir, "stats")
    os.makedirs(stats_dir, exist_ok=True)

    results = []
    for hemi in ["lh"]:
        annot = os.path.join(label_dir, f"{hemi}.aparc.schaefer2018_200_7.annot")
        if not os.path.exists(annot):
            print(f"[WARNING] Annotation not found for {hemi} at {annot}. Skipping.")
            continue
            
        out_stats = os.path.join(stats_dir, f"{hemi}.aparc.schaefer2018_200_7.stats")
        
        print(f" >>> Running mris_anatomical_stats for {hemi}...")
        # mris_anatomical_stats -a <annot> -f <output> <subject> <hemi> <surf>
        # Usually runs on 'pial' or 'white' surface. Using 'pial' as it's common for thickness.
        
        # Bổ sung ước lượng thickness. mris_thickness sẽ tạo file lh.thickness
        thickness_cmd = [
            "mris_thickness",
            subject_id,
            hemi,
            os.path.join(surf_dir, f"{hemi}.thickness")
        ]
        
        # Lệnh mris_anatomical_stats với -noglobal
        cmd = [
            "mris_anatomical_stats",
            "-noglobal",
            "-a", annot,
            "-f", out_stats,
            subject_id,
            hemi,
            "pial"
        ]
        
        try:
            env = os.environ.copy()
            env["SUBJECTS_DIR"] = SUBJECTS_DIR
            
            print(f" >>> Running mris_thickness for {hemi}...")
            run_cmd_logged(thickness_cmd, env=env)
            
            print(f" >>> Running mris_anatomical_stats for {hemi}...")
            run_cmd_logged(cmd, env=env)
            print(f" [SUCCESS] Created: {out_stats}")
            
            # Additional step: Extract thickness into a single txt file using aparcstats2table
            # aparcstats2table --hemi lh --subjects 0013 --parc aparc.schaefer2018_200_7 --meas thickness --tablefile <output>
            out_thickness = os.path.join(subj_dir, f"{hemi}.schaefer2018_200_7.thickness.mine.txt")
            aparcstats2table_cmd = [
                "aparcstats2table",
                "--hemi", hemi,
                "--subjects", subject_id,
                "--parc", "aparc.schaefer2018_200_7",
                "--meas", "thickness",
                "--tablefile", out_thickness
            ]
            
            print(f" >>> Running aparcstats2table for {hemi}...")
            run_cmd_logged(aparcstats2table_cmd, env=env)
            print(f" [SUCCESS] Thickness extracted to: {out_thickness}")
            
            results.append(out_stats)
        except Exception as e:
            print(f"[ERROR] Anatomical stats failed for {hemi}: {e}")
            
    return results if results else None
