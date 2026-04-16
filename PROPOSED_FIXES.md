# Các Giải Pháp Cố Định Tiềm Năng

## 🔧 Fix 1: Cải Thiện MRI Conform (step1_input_reorientation.py)

**Vấn đề:** `mri_convert --conform` có thể không xử lý ADNI đúng cách

**Giải pháp:** Thêm flags để đảm bảo RAS consistency

```python
# Dòng 30 trong step1_input_reorientation.py
# Thay:
cmd = ["mri_convert", "--conform", input_path, final_path]

# Từ:
cmd = ["mri_convert", "--conform", "--force_ras_good", input_path, final_path]
```

---

## 🔧 Fix 2: Cách Tiếp Cập Tốt Hơn - Preserve Voxel-to-World Info

**Vấn đề:** Convert từ .nii → .mgz → resampling có thể mất thông tin affine

**Giải pháp:** Lưu affine gốc và kiểm tra consistency

Thêm vào `step1_input_reorientation.py`:

```python
import nibabel as nib

def run_step1_input_reorientation(input_path, subject_id, subjects_dir):
    # ... existing code ...
    
    # THÊM: Lưu affine gốc từ input
    print(f"\n[DEBUG] Original input affine matrix:")
    try:
        input_img = nib.load(input_path)
        orig_affine = input_img.affine
        np.savetxt(os.path.join(mri_dir, "orig_input_affine.txt"), orig_affine)
        print(f"  Input shape: {input_img.shape}")
        print(f"  Input affine:\n{orig_affine}")
    except:
        print("  Could not read input affine (expected for .img files)")
    
    # Chạy mri_convert (existing code)
    cmd = ["mri_convert", "--conform", "--force_ras_good", input_path, final_path]
    run_cmd_logged(cmd)
    
    # THÊM: Verify output
    print(f"\n[DEBUG] Output after conform:")
    output_img = nib.load(final_path)
    np.savetxt(os.path.join(mri_dir, "orig_conform_affine.txt"), output_img.affine)
    print(f"  Output shape: {output_img.shape}")
    print(f"  Output affine:\n{output_img.affine}")
    
    # Check consistency
    if output_img.shape != (256, 256, 256):
        print(f"[WARNING] Output shape {output_img.shape} != expected (256, 256, 256)")
```

---

## 🔧 Fix 3: Enhanced Affine Registration

**Vấn đề:** NiftyReg `reg_aladin` có thể không converge tốt với ADNI

**Giải pháp:** Thêm rigid pre-registration

Sửa `tools/CorticalFlow/recon_all.sh` (dòng 50-52):

```bash
# HIỆN TẠI:
reg_aladin -ref "${TEMPLATE_PATH}" -flo "${INPUT_NII}" -aff "${AFFINE_TXT}"

# CẢI THIỆN:
# Bước 1: Rigid registration (faster, more robust)
RIGID_TXT="${SUBJ_DIR}/mri/transforms/reg_rigid.txt"
reg_aladin -ref "${TEMPLATE_PATH}" -flo "${INPUT_NII}" -aff "${RIGID_TXT}" -specspl 3 -maxit 5

# Bước 2: Affine using rigid as initialization
reg_aladin -ref "${TEMPLATE_PATH}" -flo "${INPUT_NII}" -aff "${AFFINE_TXT}" \
    -inaff "${RIGID_TXT}" -specspl 3 -maxit 15 -ln 4 -lp 3

echo "[DEBUG] Affine matrix saved:"
cat "${AFFINE_TXT}"
```

---

## 🔧 Fix 4: Fix Hemisphere Cropping (CorticalFlow/src/data.py)

**Vấn đề:** Hard-coded crop indices không hoạt động cho mọi datasets

**Giải pháp:** Dynamic hemisphere cropping dựa trên image center

```python
# File: tools/CorticalFlow/src/data.py
# Thay hàm mri_reader() từ dòng 95

def mri_reader(path, hemisphere=None):
    nib_mri = nibabel.load(path)
    mri_header, mri_vox, mri_affine = nib_mri.header, nib_mri.get_fdata().astype(np.float32), nib_mri.affine.astype(np.float32)
    
    if hemisphere:
        # Dynamic cropping thay vì hard-coded
        shape = mri_vox.shape
        mid_x = shape[0] // 2
        width = 96  # Half-width for one hemisphere
        
        if hemisphere == 'lh':
            # Left hemisphere: từ mid đến end + padding
            start_x = max(mid_x, width)
            end_x = min(start_x + width, shape[0])
            mri_vox = mri_vox[end_x-width:end_x, :, :]
        elif hemisphere == 'rh':
            # Right hemisphere: từ start đến mid - padding
            end_x = min(mid_x, shape[0] - width)
            start_x = max(end_x - width, 0)
            mri_vox = mri_vox[start_x:start_x+width, :, :]
        
        # Cập nhật affine cho cropped image
        # Affine cần reflection của crop offset
        crop_offset = start_x if hemisphere == 'rh' else (end_x - width)
        mri_affine = mri_affine @ np.array([
            [1, 0, 0, crop_offset],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]).astype(np.float32)
    
    return mri_header, mri_vox, mri_affine
```

---

## 🔧 Fix 5: Validate Affine Back-Transform (apply_affine.py)

**Vấn đề:** Có thể affine matrix không được apply đúng

**Giải pháp:** Thêm validation và debug output

```python
# File: tools/CorticalFlow/scripts/apply_affine.py
# Thay phần xử lý affine (dòng 27-33)

for i, line in enumerate(file):            
    # read data            
    affine_path, surf_path = line.strip().split('\t')
    vertices, faces = import_mesh(surf_path.strip())
    affine_matrix = np.loadtxt(affine_path.strip())
    
    # DEBUG: Print affine matrix properties
    print(f"[DEBUG {i}] Applying affine from: {affine_path}")
    print(f"  Affine matrix:\n{affine_matrix}")
    print(f"  Surface path: {surf_path}")
    print(f"  Vertices before transform (sample): {vertices[:3, :]}")
    
    # apply affine to vertices
    affine_matrix = np.asanyarray(affine_matrix, dtype=np.float64)
    
    # Validate inverse affine
    try:
        affine_inv = np.linalg.inv(affine_matrix)
        det = np.linalg.det(affine_matrix[:3, :3])
        print(f"  Determinant: {det:.6f}")
    except:
        print(f"[WARNING] Affine matrix may be singular!")
    
    # Apply transformation
    vertices = np.column_stack([np.asanyarray(vertices, dtype=np.float64), 
                                np.ones((vertices.shape[0], 1))]) 
    vertices = np.matmul(affine_matrix, vertices.T).T[:, :-1]
    vertices = np.ascontiguousarray(vertices)
    
    print(f"  Vertices after transform (sample): {vertices[:3, :]}")

    # save the resulting surface
    dirname = os.path.dirname(surf_path)
    surf_name, surf_ext = os.path.basename(surf_path).split('.')
    filename_no_ext = os.path.join(dirname, surf_name.strip()+'_native')
    export_mesh(vertices, faces, filename_no_ext, 'freesurfer', white_or_pial=surf_ext.strip())            

    if (i+1) % 100 == 0:                 
        print('{}/{} transformed in {:.4f} secs'.format(i, 13536, timer.toc()))
```

---

## 🚀 Tóm Tắt Những Bước Cần Thực Hiện

### Ưu Tiên 1: Chẩn Đoán Nhanh (15 phút)

```bash
# 1. Chạy debug script
python /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/debug_adni_surface_alignment.py

# 2. Chạy bash diagnostic
bash /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/debug_surface_alignment.sh
```

**Cách diễn giải kết quả:**
- Nếu ADNI shape ≠ 256³ → Fix 1 (conform issue)
- Nếu ADNI scale ≠ OASIS scale → Fix 3 (registration issue)  
- Nếu ADNI vertices bounds khác → Fix 4 (cropping issue)

---

### Ưu Tiên 2: Áp Dụng Fix (30-60 phút)

**Sau khi chẩn đoán:**

1. Nếu conform issue:
   ```bash
   # Edit step1_input_reorientation.py
   # Thêm --force_ras_good flag
   # Thêm debug output (xem Fix 2)
   ```

2. Nếu registration issue:
   ```bash
   # Edit tools/CorticalFlow/recon_all.sh
   # Cải thiện NiftyReg parameters (xem Fix 3)
   ```

3. Nếu cropping issue:
   ```bash
   # Edit tools/CorticalFlow/src/data.py
   # Thay hard-coded indices (xem Fix 4)
   ```

4. Luôn thêm debug output:
   ```bash
   # Edit tools/CorticalFlow/scripts/apply_affine.py
   # Xem Fix 5
   ```

---

### Ưu Tiên 3: Validation (30 phút)

```bash
# 1. Xóa output ADNI cũ để reset
rm -rf pipeline-subjects/I776974/surf/*
rm -rf pipeline-subjects/I776974/tmp/*

# 2. Chạy lại step 5 ADNI
python main.py  # (chỉnh config để chạy ADNI)

# 3. Compare với OASIS visual trong FreeView
freeview pipeline-subjects/0006/mri/orig.mgz \
         pipeline-subjects/0006/surf/lh.white &

freeview pipeline-subjects/I776974/mri/orig.mgz \
         pipeline-subjects/I776974/surf/lh.white &
```

---

**Bước tiếp theo:** Chạy diagnostic scripts và báo cáo kết quả!
