# 🔧 FIXES APPLIED - ADNI Surface Misalignment

## ✅ Fixes Implemented

Based on diagnostic results, I've identified and fixed **3 critical issues** in the CorticalFlow surface reconstruction pipeline:

---

## **Fix #1: Apply INVERSE Affine Transform** ⭐ KEY FIX

**File:** `tools/CorticalFlow/scripts/apply_affine.py`

**Problem:**
```
The affine matrix from NiftyReg (reg_aladin) transforms: native space → template space

But CorticalFlow predicts surfaces in TEMPLATE space!

To transform back: template → native, we MUST use the INVERSE of the registration affine.

Original code was applying the FORWARD affine instead of INVERSE.
```

**What Changed:**
```python
# BEFORE (WRONG):
affine_matrix = np.loadtxt(affine_path)
vertices = np.matmul(affine_matrix, vertices.T).T

# AFTER (CORRECT):
affine_matrix = np.loadtxt(affine_path)  # native → template
affine_inv = np.linalg.inv(affine_matrix)  # NOW get inverse: template → native
vertices = np.matmul(affine_inv, vertices.T).T  # Apply INVERSE
```

**Why This Fixes ADNI:**
- OASIS and ADNI have different affine matrices from NiftyReg
- ADNI's affine matrix had a larger transformation (especially in Y/Z)
- Using the wrong (forward instead of inverse) transformation magnified this error
- Surfaces ended up shifted in native space
- Using INVERSE transform corrects this

**Impact:** Surfaces should now align correctly when transformed back to native space.

---

## **Fix #2: Remove Hard-Coded Hemisphere Cropping**

**File:** `tools/CorticalFlow/src/data.py` (mri_reader function)

**Problem:**
```python
# BEFORE (WRONG):
if hemisphere: nib_mri = {'lh': nib_mri.slicer[75:171,12:204,10:170], 
                           'rh': nib_mri.slicer[9:105,12:204,10:170]}[hemisphere]
```

- Hard-coded crop indices `[75:171,12:204,10:170]` assume fixed image sizes/orientations
- These indices don't work universally across OASIS and ADNI
- Cropping disrupts the relationship between voxel coordinates and world coordinates (affine matrix)
- When surfaces are back-transformed, the crop offset is not accounted for

**What Changed:**
```python
# AFTER (CORRECT):
# Don't crop in voxel space - let template mesh handle hemisphere constraint
# Load full image and preserve affine matrix integrity

nib_mri = nibabel.load(path)
mri_vox = nib_mri.get_fdata().astype(np.float32)
mri_affine = nib_mri.affine.astype(np.float32)

# Hemisphere constraint is enforced by template mesh, not voxel cropping
```

**Why This Fixes ADNI:**
- Hard-coded indices were not appropriate for ADNI's coordinate system
- Removing crop preserves the integrity of affine matrix relationships
- Surface back-transformation now works consistently

**Impact:** Affine matrix stays consistent throughout the pipeline.

---

## **Fix #3: Add Debug Output for Validation**

**File:** `tools/CorticalFlow/recon_all.sh`

**What Added:**
```bash
# After affine registration, print the matrix
echo "[DEBUG] Affine matrix from NiftyReg (native → template):"
cat "${AFFINE_TXT}"

# Save backup for debugging
cp "${AFFINE_TXT}" "${SUBJ_DIR}/mri/transforms/reg_affine_backup.txt"
```

Also added to `apply_affine.py`:
```python
print(f"[DEBUG {i}] Processing surface: {os.path.basename(surf_path)}")
print(f"  Original affine determinant: {np.linalg.det(affine_matrix[:3,:3]):.6f}")
print(f"  Inverse affine determinant: {np.linalg.det(affine_inv[:3,:3]):.6f}")
print(f"  Vertices before transform (sample): {vertices_orig[0]}")
print(f"  Vertices after transform (sample): {vertices[0]}")
```

**Impact:** Can now trace exactly how affine transformation is applied.

---

## 📊 Summary of Changes

| File | Line(s) | Change | Reason |
|------|---------|--------|--------|
| `apply_affine.py` | 20-45 | Use INVERSE affine (template→native) | Surfaces in template space need inverse transform |
| `data.py` | 96-125 | Remove hard-coded cropping | Preserve affine matrix integrity |
| `recon_all.sh` | 52-57 | Add debug output | Validate affine matrix |

---

## 🚀 How to Test the Fixes

### Step 1: Verify Code Changes
```bash
# Check that fixes were applied
grep -A 5 "INVERSE affine" /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/tools/CorticalFlow/scripts/apply_affine.py
# Should show: affine_inv = np.linalg.inv(affine_matrix)

grep "constraint is enforced by template mesh" /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/tools/CorticalFlow/src/data.py
# Should show: hemisphere constraint message
```

### Step 2: Reprocess ADNI with Fixes
```bash
bash /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/reprocess_adni_step5.sh
```

This will:
1. Backup old results → `surf_backup_TIMESTAMP/`
2. Clear temporary files
3. Run recon_all.sh with the fixes
4. Save log to `step5_reprocess.log`

**Expected duration:** ~5-10 minutes

### Step 3: Verify Results
```bash
python /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/debug_adni_surface_alignment.py
```

**Expected improvements:**
- ✓ ADNI and OASIS surface bounds should be much more similar
- ✓ ADNI surface Y/Z ranges should be closer to OASIS
- ✓ No more 45mm shift in Y-axis

### Step 4: Visual Verification
```bash
# Compare before vs after
freeview /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/mri/orig.mgz \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/surf/lh.white &

freeview /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/mri/orig.mgz \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/surf/lh.white &
```

Look for:
- Surfaces align with brain outline
- No obvious shifts or rotations
- Pial surface is outer, white surface is inner

---

## 📋 Expected Results After Fixes

### Before Fixes:
```
ADNI lh.white Y bounds: [-86.1, 100.8] (range 186.9)
OASIS lh.white Y bounds: [-85.4, 56.4] (range 141.8)
Difference: +45.1 mm ❌
```

### After Fixes:
```
ADNI lh.white Y bounds: ~[-85, 56] (similar to OASIS)
OASIS lh.white Y bounds: [-85.4, 56.4]
Difference: <5 mm ✓
```

---

## 🔍 Why These Fixes Work

### Root Cause Analysis:

**The Problem:**
1. Surfaces are predicted in **template space** by CorticalFlow
2. To return to **native space**, need to apply **inverse** of registration affine
3. ADNI's affine matrix from NiftyReg was slightly different than OASIS
4. When wrong (forward) affine was applied, the difference got **amplified**
5. Result: Surfaces shifted dramatically in Y/Z for ADNI

**The Solution:**
1. Apply **INVERSE** affine to transform template→native correctly
2. Remove cropping that was disrupting coordinate frames
3. Add validation to track transformations

### Mathematical Explanation:
```
Registration affine: M = native_coords → template_coords

CorticalFlow prediction:
  Input: resampled MRI in template space
  Output: surfaces in template space (S_template)

Back-transformation (convert to native):
  S_native = M^(-1) @ S_template  ← Need INVERSE!
  
Original (wrong) code:
  S_native = M @ S_template  ← This is WRONG! Magnifies error
```

---

## ⚠️ Important Notes

1. **These fixes apply to both OASIS and ADNI**, but:
   - OASIS might look slightly different after inverse affine fix
   - This is expected - we're correcting a systematic error
   - OASIS should still align well with brain

2. **If OASIS gets worse after fixes:**
   - It means OASIS was accidentally working well despite the wrong code
   - The correct code might show OASIS coordinates differently
   - Re-run OASIS diagnostic to verify

3. **Check debug logs:** 
   - Log file: `pipeline-subjects/I776974/step5_reprocess.log`
   - Look for `[DEBUG]` messages showing affine matrix and vertex transforms

---

## 📂 Modified Files

```
.
├── tools/CorticalFlow/
│   ├── src/data.py                 [MODIFIED] Remove hemisphere cropping
│   ├── scripts/apply_affine.py     [MODIFIED] Use INVERSE affine
│   └── recon_all.sh                [MODIFIED] Add debug output
│
└── reprocess_adni_step5.sh         [NEW] Script to reprocess with fixes
```

---

## 🎯 Next Steps

1. **Review these changes** - Understand what was fixed
2. **Run reprocessing** - `bash reprocess_adni_step5.sh`
3. **Validate results** - `python debug_adni_surface_alignment.py`
4. **Visual check** - Compare in FreeView
5. **Run full pipeline** - Steps 6-8 (registration, parcellation, stats)

**Expected time to test:** ~30 minutes

---

**Summary:** The main issue was using the wrong affine matrix direction (forward instead of inverse) to transform surfaces from template space back to native space. Combined with removing disruptive hard-coded hemisphere cropping, this should fix the ADNI misalignment issue.
