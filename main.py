import sys
import os
from config import ensure_dirs, INPUT_FILE_PATH, SUBJECTS_DIR
from step1_input import run_step1_input
from step2_3_preprocess import run_step2_3_preprocess
from step4_segmentation import run_step4_segmentation
from step5_cortical_flow import run_step5_cortical_flow
from step7_stats import run_step7_full_stats

from profiler import StepProfiler

def main():
    print("🚀 KHỞI ĐỘNG PIPELINE ALZHEIMER (Refactored - Subject Centric)")
    ensure_dirs()
    
    profiler = StepProfiler()
    
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
        # Step 1: Input Processing
        profiler.start_step("Step 1: Input Processing")
        mri_file = run_step1_input(input_path, sid, SUBJECTS_DIR)
        profiler.stop_step()
        if not mri_file: return
        
        # Step 2-3: Preprocessing
        profiler.start_step("Step 2-3: Preprocessing (Skull Strip, N4, Norm, Mask)")
        brainmask_file = run_step2_3_preprocess(sid)
        profiler.stop_step()
        if not brainmask_file: 
             print("⚠️ Preprocessing failed, continuing pipeline...")
        
        # Step 4: Segmentation (SynthSeg)
        profiler.start_step("Step 4: Segmentation (SynthSeg)")
        seg_file = run_step4_segmentation(mri_file, sid)
        profiler.stop_step()
        if not seg_file: return
        
        # Step 5: Cortical Surface Reconstruction (CorticalFlow)
        profiler.start_step("Step 5: Cortical Surface Reconstruction")
        cf_output_dir = run_step5_cortical_flow(mri_file, sid) 
        profiler.stop_step()
        if not cf_output_dir: print("⚠️ CorticalFlow failed, continuing pipeline...")

        # Step 7: Schaefer Atlas Stats
        profiler.start_step("Step 7: Schaefer Atlas Stats")
        run_step7_full_stats(sid)
        profiler.stop_step()

        print("\n🏁 PIPELINE HOÀN TẤT!")
        
        # Determine subject output dir for report
        subj_dir = os.path.join(SUBJECTS_DIR, sid)
        profiler.generate_report(subj_dir)
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        # Try to save report even on error
        try:
             subj_dir = os.path.join(SUBJECTS_DIR, sid)
             profiler.generate_report(subj_dir)
        except:
            pass

if __name__ == "__main__":
    main()
