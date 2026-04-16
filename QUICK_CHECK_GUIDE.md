# 🎯 Quick Reference: Các Điểm Kiểm Tra Quan Trọng

## File Quan Trọng Trong Pipeline

```
pipeline-subjects/
├── 0006/ (OASIS - Working ✓)
│   └── mri/
│       ├── orig.mgz                          [Input sau conform]
│       ├── T1.mgz                            [Standardized]
│       ├── skullstrip.mgz                    [Brain extracted]
│       └── transforms/
│           ├── reg_affine.txt               [KEY: Affine matrix]
│           └── talairach.xfm
│
└── I776974/ (ADNI - Broken ❌)
    └── mri/
        ├── orig.mgz                          [Check size: 256³?]
        ├── T1.mgz
        ├── skullstrip.mgz
        ├── transforms/
        │   ├── reg_affine.txt               [Check values vs OASIS]
        │   └── talairach.xfm
        └── tmp/
            ├── niftyreg/
            │   ├── orig.nii.gz              [Pre-conform]
            │   ├── orig_affine.nii.gz       [After affine xform]
            │   └── reg_affine.txt
            └── CFPP/
                ├── I776974/
                │   ├── I776974_lh_white_Df2.pial
                │   ├── I776974_lh_white_Df2.white
                │   └── *_native.{pial,white} [These should be in surf/]
```

---

## 1️⃣ **Kiểm Tra MRI Conform (Step 1)**

### Command
```bash
# Check kích thước
mri_info /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/mri/orig.mgz
mri_info /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/mri/orig.mgz
```

### Expected Output (OASIS)
```
----------
 Voxel sizes:             1.000 1.000 1.000 mm
 Voxel dimensions:      256 256 256
 RAS space?             Yes
 ----------
```

### Expected Output (ADNI) - Should Match OASIS!
```
 Voxel sizes:             1.000 1.000 1.000 mm
 Voxel dimensions:      256 256 256
 RAS space?             Yes
```

### ⚠️ Problem Indicators
- **ADNI dimensions ≠ 256x256x256** → Problem in Step 1
- **ADNI voxel size ≠ 1mm** → Problem in Step 1
- **RAS space = No** → Problem in Step 1

---

## 2️⃣ **Kiểm Tra Affine Registration (Step 5 - NiftyReg)**

### File Location
```
pipeline-subjects/0006/mri/transforms/reg_affine.txt
pipeline-subjects/I776974/mri/transforms/reg_affine.txt
```

### Expected Format
```
4x4 matrix (3x3 rotation+scale, 3x1 translation, 0001 padding)

Example OASIS:
 1.002453  -0.009283  -0.019403   -85.654175
 0.029123   0.998234   0.006234    45.123456
-0.005431  -0.001234   1.001234   -125.324123
 0.000000   0.000000   0.000000     1.000000
```

### How to Check Scale Factor (Determinant)
```bash
python3 << 'EOF'
import numpy as np

# OASIS
oasis_affine = np.loadtxt('/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/mri/transforms/reg_affine.txt')
oasis_scale = np.linalg.det(oasis_affine[:3, :3]) ** (1/3)

# ADNI
adni_affine = np.loadtxt('/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/mri/transforms/reg_affine.txt')
adni_scale = np.linalg.det(adni_affine[:3, :3]) ** (1/3)

print(f"OASIS scale: {oasis_scale:.6f}")
print(f"ADNI scale:  {adni_scale:.6f}")
print(f"Difference:  {abs(oasis_scale - adni_scale):.6f}")

if abs(oasis_scale - adni_scale) > 0.1:
    print("⚠️  Scales differ significantly! Registration problem!")
else:
    print("✓ Scales are similar")
EOF
```

### ⚠️ Problem Indicators
- **ADNI scale ≠ OASIS scale by > 0.1** → NiftyReg problem
- **Condition number > 1000** → Ill-conditioned matrix
- **File doesn't exist** → Surface reconstruction failed

---

## 3️⃣ **Kiểm Tra Surface Files**

### Check Existence
```bash
# OASIS surfaces
ls -lh /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/surf/

# Expected output:
# -rw-r--r--  lh.white, lh.pial, rh.white, rh.pial
# ~5MB each

# ADNI surfaces  
ls -lh /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/surf/

# Should match OASIS
```

### Check Surface Bounds
```bash
python3 << 'EOF'
import nibabel as nib

# OASIS
oasis_path = '/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/surf/lh.white'
oasis_v, _ = nib.freesurfer.read_geometry(oasis_path)

# ADNI (if exists)
try:
    adni_path = '/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/surf/lh.white'
    adni_v, _ = nib.freesurfer.read_geometry(adni_path)
    
    print("OASIS bounds (mm):")
    print(f"  X: [{oasis_v[:, 0].min():.1f}, {oasis_v[:, 0].max():.1f}]")
    print(f"  Y: [{oasis_v[:, 1].min():.1f}, {oasis_v[:, 1].max():.1f}]")
    print(f"  Z: [{oasis_v[:, 2].min():.1f}, {oasis_v[:, 2].max():.1f}]")
    
    print("\nADNI bounds (mm):")
    print(f"  X: [{adni_v[:, 0].min():.1f}, {adni_v[:, 0].max():.1f}]")
    print(f"  Y: [{adni_v[:, 1].min():.1f}, {adni_v[:, 1].max():.1f}]")
    print(f"  Z: [{adni_v[:, 2].min():.1f}, {adni_v[:, 2].max():.1f}]")
    
    # Check if bounds are reasonable
    if abs(oasis_v[:, 0].mean() - adni_v[:, 0].mean()) > 10:
        print("\n⚠️  X position differs! May indicate coordinate transform issue")
        
except Exception as e:
    print(f"Error: {e}")
    print("ADNI surfaces may not exist yet")
EOF
```

### ⚠️ Problem Indicators
- **ADNI surfaces don't exist** → Step 5 failed entirely
- **ADNI bounds very different from OASIS** → Affine back-transform wrong
- **ADNI surfaces way off center** → Coordinate frame issue

---

## 4️⃣ **Visual Inspection in FreeView**

### Open Both Datasets Side-by-Side

**Terminal 1 (OASIS):**
```bash
freeview /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/mri/orig.mgz \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/surf/lh.white:edgecolor=red &
```

**Terminal 2 (ADNI):**
```bash
freeview /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/mri/orig.mgz \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/surf/lh.white:edgecolor=red &
```

### What to Look For

✅ **OASIS (expected):**
- Surface overlays on brain image
- Red outline follows cortical surface
- Alignment looks anatomically correct

❌ **ADNI (problem indicators):**
- Surface doesn't align with brain
- Surface is floating away
- Surface is upside down or rotated
- Surface is too big/small

---

## 5️⃣ **Debug Info During Processing**

### Enable Debug Output

Add to `tools/CorticalFlow/recon_all.sh` after line 50:

```bash
# DEBUG: Print affine matrix
echo "[DEBUG] Affine registration completed"
echo "[DEBUG] Affine matrix:"
cat "${AFFINE_TXT}"
```

Add to `tools/CorticalFlow/scripts/apply_affine.py` around line 30:

```python
# DEBUG output
print(f"[DEBUG] Applying affine to {surf_path}")
print(f"[DEBUG] Affine matrix det: {np.linalg.det(affine_matrix[:3,:3]):.6f}")
print(f"[DEBUG] Vertices sample: {vertices[0]}")
```

---

## 🔧 Sửa Nhanh Dành Cho Từng Loại Lỗi

### **Nếu Lỗi 1: MRI Conform (Size ≠ 256³)**

Edit `step1_input_reorientation.py` line 30:

```python
# Thay:
cmd = ["mri_convert", "--conform", input_path, final_path]

# Từ:
cmd = ["mri_convert", "--conform", "--force_ras_good", input_path, final_path]
```

### **Nếu Lỗi 2: Affine Registration (Scale ≠ 1)**

Edit `tools/CorticalFlow/recon_all.sh` line 50:

```bash
# Thêm rigid pre-registration
RIGID_TXT="${SUBJ_DIR}/mri/transforms/reg_rigid.txt"
reg_aladin -ref "${TEMPLATE_PATH}" -flo "${INPUT_NII}" -aff "${RIGID_TXT}" \
    -maxit 5 -ln 3
reg_aladin -ref "${TEMPLATE_PATH}" -flo "${INPUT_NII}" -aff "${AFFINE_TXT}" \
    -inaff "${RIGID_TXT}" -maxit 15 -ln 4 -lp 3
```

### **Nếu Lỗi 3: Hemisphere Cropping**

Edit `tools/CorticalFlow/src/data.py` line 100-110 (xem `PROPOSED_FIXES.md` Fix 4)

### **Nếu Lỗi 4: Affine Transform**

Verify `tools/CorticalFlow/scripts/apply_affine.py` is using correct matrix (xem `PROPOSED_FIXES.md` Fix 5)

---

## ✅ Acceptance Criteria

### When Problem is FIXED:

- [ ] ADNI orig.mgz: 256×256×256, 1mm voxel
- [ ] ADNI affine matrix scale ≈ OASIS scale
- [ ] ADNI surfaces exist (lh/rh white, pial)
- [ ] ADNI surface bounds similar to OASIS
- [ ] FreeView visual alignment looks good
- [ ] Stats files generated correctly

### Command to Verify End Result

```bash
# Run all checks
python /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/debug_adni_surface_alignment.py

# Visual check
freeview /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/mri/orig.mgz \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/surf/lh.white &
```

If everything passes, problem is solved! ✓

---

**Last Updated:** 2026-04-16
