# 📊 Sơ Đồ Pipeline - Vị Trí Lỗi

```
INPUT IMAGE (OASIS ✓ vs ADNI ❌)
    ↓
┌─────────────────────────────────────────────────┐
│ Step 1: INPUT REORIENTATION                     │
│ mri_convert --conform                           │
│ Result: 256³ voxels, 1mm isotropic, LIA format  │
│                                                 │
│ OASIS ✓ Output: OK 256³, 1mm                   │
│ ADNI  ? Output: Check size!                    │
└─────────────────────────────────────────────────┘
        ↓
        ⚠️ ISSUE #1 POSSIBLE: If ADNI ≠ 256³ or voxel_size ≠ 1mm
        
    ↓ (If Step 1 OK)
┌─────────────────────────────────────────────────┐
│ Steps 2-4: IMAGE PREPROCESSING                  │
│ • Stage 2: Bias correction + normalize          │
│ • Stage 3: Brain extraction (skull strip)       │
│ • Stage 4: Segmentation & parcellation          │
│ Usually OK for both datasets                    │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Step 5: SURFACE RECONSTRUCTION (CorticalFlow)  │
│                                                 │
│ [5.1] Affine Registration                       │
│ ├─ Tool: NiftyReg (reg_aladin)                  │
│ ├─ Input: normalized MRI (native space)         │
│ ├─ Template: MNI152_T1_1mm.nii.gz              │
│ ├─ Output: reg_affine.txt (4x4 matrix)         │
│ │                                              │
│ │ OASIS ✓ Scale ≈ 1.0 (good registration)     │
│ │ ADNI  ? Scale ?    (check via determinant)  │
│ │                                              │
│ └─ ⚠️ ISSUE #2 POSSIBLE: If scale differs > 0.1
│                                                 │
│ [5.2] CorticalFlow Prediction                   │
│ ├─ Input: registered MRI (template space)      │
│ ├─ Model: white_model, pial_model              │
│ └─ Output: surfaces in template space          │
│    (in tmp/CFPP/{SUBJECT_ID}/)                │
│                                                 │
│ [5.3] Back-Transform to Native Space           │
│ ├─ Tool: apply_affine.py                       │
│ ├─ Input: affine matrix + surfaces             │
│ ├─ Operation: vertices_new = mat @ vertices    │
│ ├─ Output: *_native.pial, *_native.white in    │
│ │           tmp/CFPP/{SUBJECT_ID}/            │
│ │                                              │
│ │ OASIS ✓ Surfaces align ✓                     │
│ │ ADNI  ? Surfaces align? ← CHECK!             │
│ │                                              │
│ └─ ⚠️ ISSUE #3,#4 PROBABLE: If misaligned
│                                                 │
│ [5.4] Move to Final Location                    │
│ └─ Output: surf/lh.white, lh.pial, etc.       │
│                                                 │
└─────────────────────────────────────────────────┘
    ↓
Step 6-8: REGISTRATION, PARCELLATION, STATS
```

---

## 🔴 4 Vấn Đề Chính (4 Main Issues)

### **ISSUE #1: MRI Conform Sai (30% khả năng)**
```
Vị trí:     step1_input_reorientation.py, line 30
Biểu hiện:  ADNI orig.mgz ≠ 256³ hoặc khác 1mm
Nguyên nhân: mri_convert --conform không hoạt động tối ưu với ADNI
Fix:        Thêm --force_ras_good flag, Debug output
Chi tiết:   PROPOSED_FIXES.md - Fix 1, 2
```

### **ISSUE #2: Affine Registration Sai (40% khả năng)**
```
Vị trí:     tools/CorticalFlow/recon_all.sh, line 50
            NiftyReg reg_aladin command
Biểu hiện:  ADNI affine matrix scale ≠ OASIS
            Determinant khác 1 từng phần trăm
Nguyên nhân: NiftyReg không converge tốt với ADNI intensities
Fix:        Thêm rigid pre-registration, improve parameters
Chi tiết:   PROPOSED_FIXES.md - Fix 3
```

### **ISSUE #3: Hemisphere Cropping Sai (20% khả năng)**
```
Vị trí:     tools/CorticalFlow/src/data.py, line 100-110
            mri_reader() function
Biểu hiện:  Hard-coded crop [75:171,12:204,10:170] không phù hợp
Nguyên nhân: Giả định fixed image size, nhưng ADNI khác
Fix:        Dynamic cropping dựa trên image center
Chi tiết:   PROPOSED_FIXES.md - Fix 4
```

### **ISSUE #4: Affine Transform Sai (10% khả năng)**
```
Vị trí:     tools/CorticalFlow/scripts/apply_affine.py, line 28-33
Biểu hiện:  Surfaces không map về đúng vị trí native space
Nguyên nhân: Affine matrix không được apply đúng cách,
            hoặc matrix không được invert đúng
Fix:        Debug + validate affine operations
Chi tiết:   PROPOSED_FIXES.md - Fix 5
```

---

## 🔍 Diagnostic Workflow

```
START
  ↓
[1] Chạy diagnostic scripts
    ├─ bash debug_surface_alignment.sh
    └─ python debug_adni_surface_alignment.py
  ↓
[2] Kiểm tra output
    ├─ Is ADNI size 256³? → NO → ISSUE #1 ← Fix 1
    ├─ Is ADNI scale ≈ OASIS? → NO → ISSUE #2 ← Fix 3
    ├─ Do ADNI surfaces exist? → NO → May need all fixes
    └─ Do ADNI surface bounds OK? → NO → ISSUE #3/4 ← Fix 4/5
  ↓
[3] Áp dụng fix phù hợp
    ├─ Edit file (xem PROPOSED_FIXES.md)
    ├─ Reset data: rm -rf pipeline-subjects/I776974/{surf,tmp}/*
    └─ Re-run Step 5
  ↓
[4] Verify fix
    ├─ Run diagnostics lại
    ├─ Visual check in FreeView
    └─ Compare OASIS vs ADNI
  ↓
[5] Success? → YES ✓ DONE
     ↓ NO
     └─ Try next fix, loop [3]
```

---

## 📋 Quick Checklist

### Pre-Diagnostic (5 min)
- [ ] FreeView installed AND working
- [ ] Python3 with nibabel installed
- [ ] Both subjects processed through Steps 1-4

### Main Diagnostic (20 min)
- [ ] Run `bash debug_surface_alignment.sh` → Check output
- [ ] Run `python debug_adni_surface_alignment.py` → Parse results
- [ ] Note which ISSUE numbers are triggered

### Make Fixes (1-2 hours)
- [ ] For ISSUE #1: Edit step1_input_reorientation.py
- [ ] For ISSUE #2: Edit tools/CorticalFlow/recon_all.sh
- [ ] For ISSUE #3: Edit tools/CorticalFlow/src/data.py
- [ ] For ISSUE #4: Edit tools/CorticalFlow/scripts/apply_affine.py

### Validate (30 min)
- [ ] Delete ADNI output: `rm -rf pipeline-subjects/I776974/{surf,tmp}/*`
- [ ] Reprocess: Run main.py for ADNI
- [ ] Visual check: FreeView comparison
- [ ] Re-run diagnostics: Should show ✓ everywhere

---

## 💾 File Locations Reference

```
Workspace Root: /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer

Key Files to Edit:
  1️⃣ step1_input_reorientation.py        → Line 30
  2️⃣ tools/CorticalFlow/recon_all.sh    → Line 50
  3️⃣ tools/CorticalFlow/src/data.py     → Line 100-110
  4️⃣ tools/CorticalFlow/scripts/apply_affine.py → Line 28-33

Diagnostic Tools (already created):
  📊 debug_surface_alignment.sh
  📊 debug_adni_surface_alignment.py
  📄 DIAGNOSTIC_ADNI_SURFACE_MISALIGNMENT.md
  📄 PROPOSED_FIXES.md
  📄 QUICK_CHECK_GUIDE.md
  📄 README_ADNI_ISSUE.md
```

---

## ✅ Success Criteria

Fix is successful when:

```bash
# 1. Sizes match
mri_info pipeline-subjects/I776974/mri/orig.mgz | grep -E "dimension|voxel"
# Should show: 256 x 256 x 256, 1.000 1.000 1.000 mm

# 2. Affine matrices similar
python -c "
import numpy as np
oasis = np.linalg.det(np.loadtxt('pipeline-subjects/0006/mri/transforms/reg_affine.txt')[:3,:3]) ** (1/3)
adni = np.linalg.det(np.loadtxt('pipeline-subjects/I776974/mri/transforms/reg_affine.txt')[:3,:3]) ** (1/3)
print(f'Scale diff: {abs(oasis-adni):.6f}')  # Should be < 0.1
"

# 3. Surfaces exist
ls pipeline-subjects/I776974/surf/ | wc -l  # Should be 4 (lh.white, lh.pial, rh.white, rh.pial)

# 4. Visual alignment good
freeview pipeline-subjects/I776974/mri/orig.mgz \
         pipeline-subjects/I776974/surf/lh.white &
# Should look like OASIS example
```

---

**Tiếp theo:** Lấy diagnostic output và báo cáo!
