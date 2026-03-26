import os
import numpy as np
import nibabel as nib
from config import SUBJECTS_DIR

# FreeSurfer cortical label range (ctx-lh: 1000-1999, ctx-rh: 2000-2999)
CTX_LH_MIN, CTX_LH_MAX = 1000, 1999
CTX_RH_MIN, CTX_RH_MAX = 2000, 2999


def load_lut(lut_path: str) -> dict:
    """
    Parse FreeSurferColorLUT.txt → {label_id: label_name}.
    Falls back to empty dict if file not found.
    """
    lut = {}
    if not os.path.exists(lut_path):
        return lut
    with open(lut_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    lut[int(parts[0])] = parts[1]
                except ValueError:
                    pass
    return lut


def vertices_to_voxels(coords: np.ndarray, inv_vox2ras_tkr: np.ndarray) -> np.ndarray:
    """
    Convert surface vertex coordinates (tkr-RAS) to voxel indices.
    coords: (N, 3)  →  returns (N, 3) integer voxel indices
    """
    ones = np.ones((coords.shape[0], 1))
    coords_h = np.hstack([coords, ones])          # (N, 4)
    vox_h = (inv_vox2ras_tkr @ coords_h.T).T      # (N, 4)
    return np.round(vox_h[:, :3]).astype(int)


def compute_hemisphere_thickness(
    white_path: str,
    pial_path: str,
    seg_data: np.ndarray,
    inv_vox2ras_tkr: np.ndarray,
    seg_shape: tuple,
    hemi_label_min: int,
    hemi_label_max: int,
) -> dict:
    """
    For one hemisphere:
      1. Compute per-vertex thickness = Euclidean distance White→Pial.
      2. Map each vertex to a voxel in aseg+aparc.mgz.
      3. Group by label → ThickAvg (mm).

    Returns {label_id: mean_thickness_mm}
    """
    white_coords, _ = nib.freesurfer.read_geometry(white_path)
    pial_coords, _  = nib.freesurfer.read_geometry(pial_path)

    # Per-vertex thickness (Euclidean distance)
    thickness = np.linalg.norm(pial_coords - white_coords, axis=1)  # (N,)

    # Map vertices → voxel indices
    vox_idx = vertices_to_voxels(white_coords, inv_vox2ras_tkr)  # (N, 3)

    # Clip to volume bounds
    shape = np.array(seg_shape)
    valid = np.all((vox_idx >= 0) & (vox_idx < shape), axis=1)
    vox_idx = vox_idx[valid]
    thickness = thickness[valid]

    # Lookup label at each vertex
    labels = seg_data[vox_idx[:, 0], vox_idx[:, 1], vox_idx[:, 2]]

    # Keep only cortical labels for this hemisphere
    cortical_mask = (labels >= hemi_label_min) & (labels <= hemi_label_max)
    labels    = labels[cortical_mask]
    thickness = thickness[cortical_mask]

    # Aggregate: label → mean thickness
    result = {}
    for lbl in np.unique(labels):
        result[int(lbl)] = float(np.mean(thickness[labels == lbl]))

    return result


def run_step6_thickness_estimate(subject_id: str) -> dict | None:
    """
    BƯỚC 6: THICKNESS ESTIMATE
    Tính độ dày trung bình ThickAvg (mm) của từng vùng vỏ não bằng nibabel.

    Inputs (từ các bước trước):
        surf/lh.white, surf/lh.pial
        surf/rh.white, surf/rh.pial
        mri/aseg+aparc.mgz

    Output:
        stats/thickness_estimate.csv  (và dict trả về)
        dict key   = label id  (ví dụ: 1024 = ctx-lh-precentral)
        dict value = ThickAvg (mm)
    """
    print(f"\n[6/7] [STARTED] THICKNESS ESTIMATE (nibabel) CHO {subject_id}...")

    subj_dir  = os.path.join(SUBJECTS_DIR, subject_id)
    surf_dir  = os.path.join(subj_dir, "surf")
    mri_dir   = os.path.join(subj_dir, "mri")
    stats_dir = os.path.join(subj_dir, "stats")
    os.makedirs(stats_dir, exist_ok=True)

    # --- Paths ---
    seg_path = os.path.join(mri_dir, "aseg+aparc.mgz")
    lh_white = os.path.join(surf_dir, "lh.white")
    lh_pial  = os.path.join(surf_dir, "lh.pial")
    rh_white = os.path.join(surf_dir, "rh.white")
    rh_pial  = os.path.join(surf_dir, "rh.pial")
    out_csv  = os.path.join(stats_dir, "thickness_estimate.csv")

    for p in [seg_path, lh_white, lh_pial, rh_white, rh_pial]:
        if not os.path.exists(p):
            print(f"[ERROR] File không tồn tại: {p}")
            return None

    try:
        # Load aseg+aparc volume
        print(" >>> Loading aseg+aparc.mgz...")
        seg_img  = nib.load(seg_path)
        seg_data = np.asarray(seg_img.dataobj, dtype=np.int32)

        # FreeSurfer MGH: vox2ras_tkr transforms voxel → tkr-RAS
        # We need the inverse: tkr-RAS → voxel
        vox2ras_tkr     = seg_img.header.get_vox2ras_tkr()
        inv_vox2ras_tkr = np.linalg.inv(vox2ras_tkr)

        print(" >>> Computing LH thickness...")
        lh_thickness = compute_hemisphere_thickness(
            lh_white, lh_pial,
            seg_data, inv_vox2ras_tkr, seg_data.shape,
            CTX_LH_MIN, CTX_LH_MAX
        )

        print(" >>> Computing RH thickness...")
        rh_thickness = compute_hemisphere_thickness(
            rh_white, rh_pial,
            seg_data, inv_vox2ras_tkr, seg_data.shape,
            CTX_RH_MIN, CTX_RH_MAX
        )

        # Merge both hemispheres
        all_thickness = {**lh_thickness, **rh_thickness}
        print(f" >>> Found {len(all_thickness)} cortical regions.")

        # Load label names from FreeSurferColorLUT.txt
        fs_home = os.environ.get("FREESURFER_HOME", "/usr/local/freesurfer/8.1.0")
        lut_path = os.path.join(fs_home, "FreeSurferColorLUT.txt")
        lut = load_lut(lut_path)

        # Save to CSV
        import csv
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Label_ID", "Region_Name", "ThickAvg_mm"])
            for label_id, thick in sorted(all_thickness.items()):
                region_name = lut.get(label_id, f"label_{label_id}")
                writer.writerow([label_id, region_name, round(thick, 4)])

        print(f" [SUCCESS] Thickness estimate saved: {out_csv}")
        return all_thickness

    except Exception as e:
        print(f"[ERROR] Lỗi Thickness Estimate: {e}")
        import traceback
        traceback.print_exc()
        return None
