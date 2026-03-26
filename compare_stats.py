import os
import sys
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

def parse_freesurfer_stats(file_path):
    """
    Parses a FreeSurfer license/stats file.
    Returns a DataFrame with the data.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return None

    # Read all lines
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Filter out comment lines but keep the header (last comment line usually)
    # The header line usually starts with "# ColHeaders"
    header_line = None
    data_lines = []

    for line in lines:
        if line.startswith("# ColHeaders"):
            header_line = line.strip().replace("# ColHeaders", "").strip().split()
        elif not line.startswith("#"):
            data_lines.append(line.strip().split())

    if not header_line:
        print(f"[ERROR] Could not find header in {file_path}")
        return None

    # Create DataFrame
    try:
        df = pd.DataFrame(data_lines, columns=header_line)
        # Convert numeric columns
        for col in df.columns:
            # Try to convert to numeric, ignore errors (keep as string if fails)
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
        return df
    except Exception as e:
        print(f"[ERROR] Error parsing DataFrame: {e}")
        return None

def compare_subject(sid, subjects_ref_dir, subjects_target_dir):
    print(f"\n[INFO] Comparing Subject: {sid}")
    print(f"   Reference: {subjects_ref_dir}")
    print(f"   Target   : {subjects_target_dir}")

    # Files to compare (LH and RH Schaefer)
    files = [
        "stats/lh.Schaefer2018_200Parcels_7Networks.stats",
        "stats/rh.Schaefer2018_200Parcels_7Networks.stats"
    ]

    # Metrics to compare
    metrics = {
        "SurfArea": "Area",
        "GrayVol": "Volume",
        "ThickAvg": "Thickness"
    }
    
    overall_stats = []

    for rel_path in files:
        ref_path = os.path.join(subjects_ref_dir, sid, rel_path)
        tgt_path = os.path.join(subjects_target_dir, sid, rel_path)
        
        print(f"\nFile: {rel_path}")
        if not os.path.exists(ref_path) or not os.path.exists(tgt_path):
            print(" Missing file in one of the directories. Skipping.")
            continue
            
        df_ref = parse_freesurfer_stats(ref_path)
        df_tgt = parse_freesurfer_stats(tgt_path)

        if df_ref is None or df_tgt is None:
            continue
        
        # Merge on StructName to ensure we compare same ROIs
        # StructName is usually unique
        merged = pd.merge(df_ref, df_tgt, on="StructName", suffixes=('_ref', '_tgt'))
        
        print(f"   Matched ROIs: {len(merged)}")
        
        for metric_col, metric_name in metrics.items():
            col_ref = f"{metric_col}_ref"
            col_tgt = f"{metric_col}_tgt"
            
            if col_ref not in merged.columns or col_tgt not in merged.columns:
                print(f"   [WARNING] Metric column {metric_col} not found.")
                continue
                
            # Calculations
            refs = merged[col_ref]
            tgts = merged[col_tgt]
            
            # Correlation
            if len(refs) > 1:
                corr, _ = pearsonr(refs, tgts)
            else:
                corr = 0
            
            # Absolute Percentage Error per ROI
            # Avoid division by zero
            valid_mask = refs != 0
            diff_pct = np.abs((tgts[valid_mask] - refs[valid_mask]) / refs[valid_mask]) * 100
            mean_error_pct = diff_pct.mean()
            accuracy = max(0, 100 - mean_error_pct)
            
            print(f"   -> {metric_name:<10}: Correlation = {corr:.4f} | Accuracy = {accuracy:.2f}% (Mean Err: {mean_error_pct:.2f}%)")
            
            overall_stats.append({
                "File": rel_path,
                "Metric": metric_name,
                "Correlation": corr,
                "Accuracy": accuracy,
                "MeanError": mean_error_pct
            })

    # Summary
    if overall_stats:
        print("\n" + "="*60)
        print(" SUMMARY")
        print("="*60)
        df_summary = pd.DataFrame(overall_stats)
        # Group by Metric
        grouped = df_summary.groupby("Metric")[["Correlation", "Accuracy", "MeanError"]].mean()
        print(grouped)
        print("="*60)
    else:
        print("\n[ERROR] No valid stats compared.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_stats.py <subject_id>")
        sys.exit(1)
        
    sid = sys.argv[1]
    
    # Paths (Hardcoded based on user context, or configurable)
    base_dir = "/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer"
    subjects_ref = os.path.join(base_dir, "freesurfer_result")   # FreeSurfer Standard
    subjects_tgt = os.path.join(base_dir, "subjects2")  # Pipeline Output
    
    compare_subject(sid, subjects_ref, subjects_tgt)
