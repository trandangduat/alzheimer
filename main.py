import sys
import os
from config import ensure_dirs, INPUT_FILE_PATH, SUBJECTS_DIR
from step1_input import run_step1_input
from step2_3_preprocess import run_step2_3_preprocess
from step4_segmentation import run_step4_segmentation
from step5_cortical_flow import run_step5_cortical_flow
from step6_mesh import run_step6_mesh_generation
from step7_stats import run_step7_full_stats

def main():
    print("🚀 KHỞI ĐỘNG PIPELINE ALZHEIMER (Refactored - Subject Centric)")
    ensure_dirs()
    
    input_path = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE_PATH
    print(f"📂 Input: {input_path}")

    # Detect Subject ID
    fname = os.path.basename(input_path)
    if fname.endswith(".nii.gz"):
        sid = fname[:-7]
    elif fname.endswith(".nii"):
        sid = fname[:-4]
    else:
         # remove extension
        sid = os.path.splitext(fname)[0]
    
    # Set SUBJECTS_DIR env var
    os.environ["SUBJECTS_DIR"] = SUBJECTS_DIR
    print(f"export SUBJECTS_DIR={SUBJECTS_DIR}")
    print(f"👤 Subject ID: {sid}")
    
    try:
        # Step 1: Input Processing -> mri/orig.mgz
        mri_file = run_step1_input(input_path, sid, SUBJECTS_DIR)
        if not mri_file: return
        
        # Step 4: Segmentation (SynthSeg) -> mri/aseg.mgz
        seg_file = run_step4_segmentation(mri_file, sid)
        if not seg_file: return
        
        # Step 5: Cortical Surface Reconstruction (CorticalFlow) -> surf/*h.white, *h.pial
        cf_output_dir = run_step5_cortical_flow(mri_file, sid) 
        if not cf_output_dir: print("⚠️ CorticalFlow failed, continuing pipeline...")

        print("\n🏁 PIPELINE HOÀN TẤT!")
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")

if __name__ == "__main__":
    main()
