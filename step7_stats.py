import os
import subprocess
from config import SUBJECTS_DIR, SCHAEFER_GCS_ROOT, FREESURFER_AVERAGE_DIR

def run_cmd(cmd):
    """Executes a shell command and checks for errors."""
    print(f"Executing: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {cmd}")
        print(f"Error details: {e}")
        raise

def run_step7_full_stats(sid):
    """
    BƯỚC 7: STATS GENERATION
    Generates Schaefer2018 atlas statistics for the subject.
    """
    print(f"\n[7/7] 📊 Generating Schaefer Atlas Stats for {sid}...")
    
    subj_dir = os.path.join(SUBJECTS_DIR, sid)
    
    if not os.path.exists(subj_dir):
        print(f"❌ Subject directory not found: {subj_dir}")
        return None

    # Define paths relative to subject directory
    label_dir = os.path.join(subj_dir, "label")
    surf_dir = os.path.join(subj_dir, "surf")
    mri_dir = os.path.join(subj_dir, "mri")
    stats_dir = os.path.join(subj_dir, "stats")
    
    os.makedirs(label_dir, exist_ok=True)
    os.makedirs(stats_dir, exist_ok=True)

    # Environment setup
    # Note: SUBJECTS_DIR is already set in main.py, but explicit paths are safer
    
    try:
        # 1. mri_label2label (cortex labels)
        run_cmd(f"mri_label2label --label-cortex {os.path.join(surf_dir, 'lh.white')} {os.path.join(mri_dir, 'aseg.mgz')} 1 {os.path.join(label_dir, 'lh.cortex.label')}")
        run_cmd(f"mri_label2label --label-cortex {os.path.join(surf_dir, 'rh.white')} {os.path.join(mri_dir, 'aseg.mgz')} 1 {os.path.join(label_dir, 'rh.cortex.label')}")

        # 2. mris_smooth (smoothwm)
        run_cmd(f"mris_smooth -n 3 -nw -seed 1234 {os.path.join(surf_dir, 'lh.white')} {os.path.join(surf_dir, 'lh.smoothwm')}")
        run_cmd(f"mris_smooth -n 3 -nw -seed 1234 {os.path.join(surf_dir, 'rh.white')} {os.path.join(surf_dir, 'rh.smoothwm')}")

        # 3. mris_inflate (inflated)
        run_cmd(f"mris_inflate {os.path.join(surf_dir, 'lh.smoothwm')} {os.path.join(surf_dir, 'lh.inflated')}")
        run_cmd(f"mris_inflate {os.path.join(surf_dir, 'rh.smoothwm')} {os.path.join(surf_dir, 'rh.inflated')}")

        # 4. mris_sphere (sphere)
        run_cmd(f"mris_sphere -threads 4 -seed 1234 {os.path.join(surf_dir, 'lh.inflated')} {os.path.join(surf_dir, 'lh.sphere')}")
        run_cmd(f"mris_sphere -threads 4 -seed 1234 {os.path.join(surf_dir, 'rh.inflated')} {os.path.join(surf_dir, 'rh.sphere')}")

        # 5. mris_register (sphere.reg)
        run_cmd(f"mris_register -curv -threads 4 {os.path.join(surf_dir, 'lh.sphere')} {os.path.join(FREESURFER_AVERAGE_DIR, 'lh.folding.atlas.acfb40.noaparc.i12.2016-08-02.tif')} {os.path.join(surf_dir, 'lh.sphere.reg')}")
        run_cmd(f"mris_register -curv -threads 4 {os.path.join(surf_dir, 'rh.sphere')} {os.path.join(FREESURFER_AVERAGE_DIR, 'rh.folding.atlas.acfb40.noaparc.i12.2016-08-02.tif')} {os.path.join(surf_dir, 'rh.sphere.reg')}")

        # 6. mris_ca_label (annot)
        run_cmd(f"mris_ca_label -l {os.path.join(label_dir, 'lh.cortex.label')} {sid} lh {os.path.join(surf_dir, 'lh.sphere.reg')} {os.path.join(SCHAEFER_GCS_ROOT, 'lh.Schaefer2018_200Parcels_7Networks.gcs')} {os.path.join(label_dir, 'lh.Schaefer2018_200Parcels_7Networks_order.annot')}")
        run_cmd(f"mris_ca_label -l {os.path.join(label_dir, 'rh.cortex.label')} {sid} rh {os.path.join(surf_dir, 'rh.sphere.reg')} {os.path.join(SCHAEFER_GCS_ROOT, 'rh.Schaefer2018_200Parcels_7Networks.gcs')} {os.path.join(label_dir, 'rh.Schaefer2018_200Parcels_7Networks_order.annot')}")

        # 7. mris_place_surface (curv, area, thickness)
        # LH
        run_cmd(f"mris_place_surface --curv-map {os.path.join(surf_dir, 'lh.white')} 2 10 {os.path.join(surf_dir, 'lh.curv')}")
        run_cmd(f"mris_place_surface --area-map {os.path.join(surf_dir, 'lh.white')} {os.path.join(surf_dir, 'lh.area')}")
        run_cmd(f"mris_place_surface --curv-map {os.path.join(surf_dir, 'lh.pial')} 2 10 {os.path.join(surf_dir, 'lh.curv.pial')}")
        run_cmd(f"mris_place_surface --area-map {os.path.join(surf_dir, 'lh.pial')} {os.path.join(surf_dir, 'lh.area.pial')}")
        run_cmd(f"mris_place_surface --thickness {os.path.join(surf_dir, 'lh.white')} {os.path.join(surf_dir, 'lh.pial')} 20 5 {os.path.join(surf_dir, 'lh.thickness')}")

        # RH
        run_cmd(f"mris_place_surface --curv-map {os.path.join(surf_dir, 'rh.white')} 2 10 {os.path.join(surf_dir, 'rh.curv')}")
        run_cmd(f"mris_place_surface --area-map {os.path.join(surf_dir, 'rh.white')} {os.path.join(surf_dir, 'rh.area')}")
        run_cmd(f"mris_place_surface --curv-map {os.path.join(surf_dir, 'rh.pial')} 2 10 {os.path.join(surf_dir, 'rh.curv.pial')}")
        run_cmd(f"mris_place_surface --area-map {os.path.join(surf_dir, 'rh.pial')} {os.path.join(surf_dir, 'rh.area.pial')}")
        run_cmd(f"mris_place_surface --thickness {os.path.join(surf_dir, 'rh.white')} {os.path.join(surf_dir, 'rh.pial')} 20 5 {os.path.join(surf_dir, 'rh.thickness')}")

        # 8. mris_anatomical_stats (stats)
        run_cmd(f"mris_anatomical_stats -f {os.path.join(stats_dir, 'lh.Schaefer2018_200Parcels_7Networks.stats')} -b -a {os.path.join(label_dir, 'lh.Schaefer2018_200Parcels_7Networks_order.annot')} {sid} lh")
        run_cmd(f"mris_anatomical_stats -f {os.path.join(stats_dir, 'rh.Schaefer2018_200Parcels_7Networks.stats')} -b -a {os.path.join(label_dir, 'rh.Schaefer2018_200Parcels_7Networks_order.annot')} {sid} rh")

        print("✅ Schaefer Atlas Stats generated successfully.")
        return stats_dir
        
    except Exception as e:
        # print error but don't re-raise, let pipeline continue or handle it? 
        # For now, print error.
        print(f"❌ Failed to generate Schaefer Atlas Stats: {e}")
        return None
