import sys
from config import ensure_dirs, INPUT_FILE_PATH
from step1_input import run_step1_input
from step2_3_preprocess import run_step2_3_preprocess
from step4_segmentation import run_step4_segmentation
from step5_cortical_flow import run_step5_cortical_flow
from step6_mesh import run_step6_mesh_generation
from step7_stats import run_step7_full_stats

def main():
    print("🚀 KHỞI ĐỘNG PIPELINE ALZHEIMER (Refactored)")
    ensure_dirs()
    
    input_path = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE_PATH
    print(f"📂 Input: {input_path}")
    
    # Run pipeline steps sequentially with early exit on failure
    try:
        # Step 1: Input Processing
        nifti_file = run_step1_input(input_path)
        if not nifti_file: return

        # # Step 2 & 3: Preprocessing
        # preproc_file = run_step2_3_preprocess(nifti_file)
        # if not preproc_file: return

        # # Step 4: Segmentation
        # seg_file = run_step4_segmentation(preproc_file)
        # if not seg_file: return
        
        # Step 5: Cortical Surface Reconstruction (CorticalFlow)
        cf_output_dir = run_step5_cortical_flow(nifti_file)
        if not cf_output_dir: print("⚠️ CorticalFlow failed, continuing pipeline...")

        print("\n🏁 PIPELINE HOÀN TẤT!")
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")

if __name__ == "__main__":
    main()
