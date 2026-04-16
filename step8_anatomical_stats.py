import os
import shutil
from config import SUBJECTS_DIR, run_cmd_logged


def run_step8_anatomical_stats(subject_id):
    """
    BƯỚC 8: ANATOMICAL STATS (mris_anatomical_stats)
    Input: label/?h.aparc.schaefer2018_200_7.annot
    Output: stats/?h.aparc.schaefer2018_200_7.stats
    """
    print(
        f"\n[8/8] [PROCESSING] ANATOMICAL STATS (mris_anatomical_stats) for {subject_id}..."
    )

    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    mri_dir = os.path.join(subj_dir, "mri")
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

        thickness_cmd = [
            "mris_thickness",
            subject_id,
            hemi,
            os.path.join(surf_dir, f"{hemi}.thickness"),
        ]

        cmd = [
            "mris_anatomical_stats",
            "-noglobal",
            "-a",
            annot,
            "-f",
            out_stats,
            subject_id,
            hemi,
            "pial",
        ]

        try:
            # Sửa lỗi Env: Đảm bảo biến SUBJECTS_DIR được set tường minh cho OS
            os.environ["SUBJECTS_DIR"] = SUBJECTS_DIR
            env = os.environ.copy()
            env["SUBJECTS_DIR"] = SUBJECTS_DIR

            cortex_label = os.path.join(label_dir, f"{hemi}.cortex.label")
            if not os.path.exists(cortex_label):
                print(
                    f" >>> Generating missing {hemi}.cortex.label using FreeSurfer tools..."
                )

                aseg_aparc = os.path.join(mri_dir, "aseg+aparc.mgz")
                aseg_presurf = os.path.join(mri_dir, "aseg.presurf.mgz")
                if os.path.exists(aseg_aparc):
                    shutil.copy2(aseg_aparc, aseg_presurf)
                else:
                    print(f"[WARNING] Missing source file: {aseg_aparc}")

                white = os.path.join(surf_dir, f"{hemi}.white")
                white_preaparc = os.path.join(surf_dir, f"{hemi}.white.preaparc")
                if os.path.exists(white):
                    shutil.copy2(white, white_preaparc)
                else:
                    print(f"[WARNING] Missing source file: {white}")

                run_cmd_logged(
                    [
                        "mri_entowm_seg",
                        "--s",
                        subject_id,
                        "--conform",
                        "--threads",
                        "1",
                    ],
                    env=env,
                )
                run_cmd_logged(
                    [
                        "/usr/local/freesurfer/8.1.0/bin/label-cortex",
                        "--s",
                        subject_id,
                        "--lh",
                        "--fix-ga",
                    ],
                    env=env,
                )

            print(f" >>> Running mris_thickness for {hemi}...")
            run_cmd_logged(thickness_cmd, env=env)

            print(f" >>> Running mris_anatomical_stats for {hemi}...")
            run_cmd_logged(cmd, env=env)
            print(f" [SUCCESS] Created: {out_stats}")

            out_thickness = os.path.join(
                subj_dir, f"{hemi}.schaefer2018_200_7.thickness.mine.txt"
            )
            aparcstats2table_cmd = [
                "aparcstats2table",
                "--hemi",
                hemi,
                "--subjects",
                subject_id,
                "--parc",
                "aparc.schaefer2018_200_7",
                "--meas",
                "thickness",
                "--tablefile",
                out_thickness,
            ]

            print(f" >>> Running aparcstats2table for {hemi}...")
            run_cmd_logged(aparcstats2table_cmd, env=env)
            print(f" [SUCCESS] Thickness extracted to: {out_thickness}")

            results.append(out_stats)
        except Exception as e:
            print(f"[ERROR] Anatomical stats failed for {hemi}: {e}")

    return results if results else None
