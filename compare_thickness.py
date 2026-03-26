"""
compare_thickness.py
Compares ThickAvg (mm) between:
  - Our pipeline:  subjects2/0006/stats/thickness_estimate.csv
  - FreeSurfer ref: ~/frsf_output/OAS1_0006_MR1/stats/{lh,rh}.aparc.stats

Output: subjects2/0006/stats/thickness_comparison.csv
"""

import os
import csv

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
OUR_CSV        = os.path.join(BASE_DIR, "subjects2", "0006", "stats", "thickness_estimate.csv")
FS_LH_STATS    = os.path.expanduser("~/frsf_output/OAS1_0006_MR1/stats/lh.aparc.stats")
FS_RH_STATS    = os.path.expanduser("~/frsf_output/OAS1_0006_MR1/stats/rh.aparc.stats")
OUT_CSV        = os.path.join(BASE_DIR, "subjects2", "0006", "stats", "thickness_comparison.csv")


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_aparc_stats(path: str, hemi: str) -> dict:
    """
    Parse a FreeSurfer *h.aparc.stats file.
    Returns {full_region_name: ThickAvg_mm}
    e.g. {'ctx-lh-bankssts': 2.796, ...}
    Column layout (0-indexed, space-separated, non-comment lines):
        0: StructName  1: NumVert  2: SurfArea  3: GrayVol
        4: ThickAvg    5: ThickStd  ...
    """
    result = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            struct = parts[0]
            try:
                thick = float(parts[4])
            except ValueError:
                continue
            full_name = f"ctx-{hemi}-{struct}"
            result[full_name] = thick
    return result


def parse_our_csv(path: str) -> dict:
    """
    Parse thickness_estimate.csv.
    Returns {region_name: ThickAvg_mm}
    """
    result = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name  = row["Region_Name"].strip()
            thick = float(row["ThickAvg_mm"])
            result[name] = thick
    return result


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading our thickness_estimate.csv ...")
    our_data = parse_our_csv(OUR_CSV)

    print("Loading FreeSurfer aparc.stats ...")
    fs_data  = parse_aparc_stats(FS_LH_STATS, "lh")
    fs_data |= parse_aparc_stats(FS_RH_STATS, "rh")

    # Union of all region names
    all_regions = sorted(set(our_data) | set(fs_data))

    rows = []
    for region in all_regions:
        our_val = our_data.get(region)
        fs_val  = fs_data.get(region)

        if our_val is not None and fs_val is not None:
            diff    = our_val - fs_val
            pct_err = (diff / fs_val) * 100.0 if fs_val != 0 else None
        else:
            diff    = None
            pct_err = None

        rows.append({
            "Region":              region,
            "Ours_ThickAvg_mm":   round(our_val, 4) if our_val is not None else "N/A",
            "FS_ThickAvg_mm":     round(fs_val,  4) if fs_val  is not None else "N/A",
            "Diff_mm":            round(diff,    4) if diff    is not None else "N/A",
            "Pct_Error":          round(pct_err, 2) if pct_err is not None else "N/A",
        })

    # Write output CSV
    fieldnames = ["Region", "Ours_ThickAvg_mm", "FS_ThickAvg_mm", "Diff_mm", "Pct_Error"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved: {OUT_CSV}")
    print(f"Total regions compared: {sum(1 for r in rows if r['Diff_mm'] != 'N/A')} / {len(rows)}")

    # ── Summary stats ──────────────────────────────────────────────────────────
    matched = [r for r in rows if isinstance(r["Diff_mm"], float)]
    if matched:
        diffs    = [abs(r["Diff_mm"])  for r in matched]
        pcts     = [abs(r["Pct_Error"]) for r in matched]
        print(f"\n{'─'*52}")
        print(f"  MAE  (mean |Diff| mm)      : {sum(diffs)/len(diffs):.4f} mm")
        print(f"  Max  |Diff|                : {max(diffs):.4f} mm")
        print(f"  MAPE (mean |Pct_Error|%)   : {sum(pcts)/len(pcts):.2f} %")
        print(f"{'─'*52}")

        print("\nTop 5 largest absolute differences:")
        top5 = sorted(matched, key=lambda r: abs(r["Diff_mm"]), reverse=True)[:5]
        for r in top5:
            print(f"  {r['Region']:<45} Ours={r['Ours_ThickAvg_mm']:.4f}  FS={r['FS_ThickAvg_mm']:.4f}  Δ={r['Diff_mm']:+.4f} mm ({r['Pct_Error']:+.1f}%)")


if __name__ == "__main__":
    main()
