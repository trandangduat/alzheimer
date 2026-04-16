# Chẩn Đoán: Issues Tái Tạo Bề Mặt Vỏ Não ADNI

## 📌 Tóm Tắt Vấn Đề

**OASIS**: ✅ Surfaces khớp tốt với 2D slices  
**ADNI**: ❌ Surfaces bị lệch với 2D slices

Pipeline qua 5 bước, nhưng lỗi xuất hiện ở **Step 5: Surface Reconstruction (CorticalFlow)**

---

## 🔍 Phân Tích Chi Tiết

### 1. **Quy Trình Pipeline**

```
Input → Step 1: mri_convert --conform → Step 2: Bias Correction
              ↓
         Step 3: Brain Extraction
              ↓
         Step 4: Segmentation & Parcellation
              ↓
         Step 5: CorticalFlow Surface Reconstruction
         ├─ Affine registration (NiftyReg): native → MNI152 template
         ├─ CorticalFlow prediction: surfaces in template space
         └─ apply_affine: transform surfaces back to native space ← LỖI NẰM ĐÂY
```

### 2. **Các Nguyên Nhân Tiềm Năng**

#### **A. Affine Registration Không Chính Xác (recon_all.sh)**

```bash
# Dòng 50-52 trong recon_all.sh
reg_aladin -ref MNI152_T1_1mm.nii.gz -flo input.nii.gz -aff reg_affine.txt
reg_resample -ref template -flo input -trans affine.txt -res resampled.nii.gz
```

**Vấn đề:**
- OASIS và ADNI có **phân bố cường độ khác nhau**
- NiftyReg có thể không align ADNI tốt như OASIS
- Kết quả: Affine matrix không chính xác → Quay lại native space sai

**Chẩn đoán:** Hãy inspect file `reg_affine.txt` cho OASIS vs ADNI

---

#### **B. Vấn Đề Tại apply_affine.py**

```python
# Dòng 28-32 trong apply_affine.py
affine_matrix = np.loadtxt(affine_path)  # Đọc từ reg_aladin
vertices = np.column_stack([vertices, np.ones((vertices.shape[0], 1))])
vertices = np.matmul(affine_matrix, vertices.T).T[:, :-1]  # Áp dụng affine
```

**Vấn đề:**
- Nếu `affine_matrix` từ reg_aladin sai → surfaces sai
- **CÓ THỂ** theo dõi ma trận affine tại đây không đúng cách
- Coordinate frame mismatch

---

#### **C. Vấn Đề Input Format**

**OASIS:**
```
OAS1_0006_MR1_mpr_n4_anon_sbj_111.img/.hdr → mri_convert --conform → orig.mgz
```

**ADNI:**
```
*.nii.gz → mri_convert --conform → orig.mgz
```

**Vấn đề:**
- NIfTI vs Analyze format khác nhau về affine matrix
- `mri_convert --conform` có thể xử lý khác nhau
- Kết quả: Affine nội tại không nhất quán

---

#### **D. Crop Hemisphere Sai (CorticalFlow/src/data.py:100)**

```python
if hemisphere: 
    nib_mri = {
        'lh': nib_mri.slicer[75:171,12:204,10:170], 
        'rh': nib_mri.slicer[9:105,12:204,10:170]
    }[hemisphere]
```

**Vấn đề:**
- Các chỉ số này giả định kích thước 256×256×256 cụ thể
- Nếu `mri_convert --conform` không tạo ra chính xác 256³ → crop sai
- ADNI có thể có kích thước sau conform khác OASIS

---

### 3. **Các Bước Chẩn Đoán Cần Thực Hiện**

#### **Bước 1: Kiểm tra Output của conform**

```bash
# Xem kích thước sau mri_convert --conform
mri_info pipeline-subjects/0006/mri/orig.mgz
mri_info pipeline-subjects/I776974/mri/orig.mgz

# Nên kết quả:
# 256 x 256 x 256 voxels
# 1.0 x 1.0 x 1.0 mm/voxel
```

Nếu **I776974 khác 256³ hoặc voxel spacing khác 1mm** → **Đây là lỗi!**

---

#### **Bước 2: Kiểm tra Affine Registration**

```bash
# Trong CorticalFlow folder
freeview resampled.nii.gz MNI152_T1_1mm.nii.gz &
```

Chạy với cả OASIS (0006) và ADNI (I776974), so sánh visual alignment.

---

#### **Bước 3: Kiểm tra Affine Matrix**

```bash
# So sánh các affine matrix
echo "=== OASIS 0006 ===" 
cat pipeline-subjects/0006/tmp/niftyreg/reg_affine.txt

echo "=== ADNI I776974 ===" 
cat pipeline-subjects/I776974/tmp/niftyreg/reg_affine.txt
```

Affine matrix ADNI có **giá trị rất khác nhau** không? Nếu vậy → registration problem.

---

#### **Bước 4: Kiểm tra Voxel-to-World Coordinate**

```python
# Thêm vào predict.py sau khi load MRI (dòng ~100)

print(f"[DEBUG] MRI shapes and affine for subject {subject_ids}")
for i, (shape, aff) in enumerate(zip(mri_vox.shape, mri_affine)):
    print(f"  Subject {i}: shape={shape}, affine=\n{aff}")
    
# So sánh giữa OASIS và ADNI
```

---

### 4. **Các Giải Pháp Tiềm Năng**

#### **Giải Pháp 1: Cải Thiện Affine Registration**

Nếu vấn đề là ở NiftyReg, có thể:

```bash
# Thử với skull-stripped image thay vì full head
reg_aladin -ref template -flo skullstrip.nii.gz -aff affine.txt

# Hoặc dùng rigid registration trước
reg_rigid -ref template -flo input -aff rigid.txt
reg_aladin -ref template -flo input -aff rigid.txt -inaff rigid.txt
```

---

#### **Giải Pháp 2: Preserve Original Affine**

Trong `recon_all.sh`, cần lưu affine dari subject space:

```bash
# Lấy affine từ file input gốc TRƯỚC khi convert/conform
# Sau đó combine với affine từ reg_aladin

# Hoặc: Quy lại surfaces dùng INVERSE của (MNI → native)
# Thay vì direct: apply_affine(predicted_surfaces)
```

---

#### **Giải Pháp 3: Kiểm tra Enforce RAS Orientation**

```bash
# Trong Step 1 reorientation
# Thêm flag để đảm bảo RAS orientation consistent

mri_convert --conform --force_ras_good input.nii output.mgz
```

---

#### **Giải Pháp 4: Validate Hemisphere Cropping**

Sửa hard-coded crop indices:

```python
# File: CorticalFlow/src/data.py, hàm mri_reader()

# Thay vì hard-code: sử dụng dynamic cropping
def mri_reader(path, hemisphere=None):
    nib_mri = nibabel.load(path)
    mri_vox = nib_mri.get_fdata().astype(np.float32)
    
    if hemisphere:
        # Crop middle 96 voxels in x-direction
        mid_x = mri_vox.shape[0] // 2
        if hemisphere == 'lh':
            nib_mri = nib_mri.slicer[mid_x:mid_x+96, :, :]
        elif hemisphere == 'rh':
            nib_mri = nib_mri.slicer[mid_x-96:mid_x, :, :]
    ...
```

---

## 🛠️ Tóm Tắt Hành Động Ngay Lập Tức

### **Priority 1 - Diagnostic** (30 phút)
1. ✅ Kiểm tra size confom (Bước 1 diagnostics)
2. ✅ So sánh 2 affine matrices (Bước 3)
3. ✅ Visual inspect registration (Bước 2)

### **Priority 2 - Fix** (1 giờ)
- Nếu affine registration sai → cải thiện NiftyReg parameters
- Nếu hemisphere crop sai → fix indices
- Nếu voxel space sai → fix conform

### **Priority 3 - Validation** (30 phút)
- Chạy lại OASIS để compare
- Verify surfaces in FreeView
- Check stats in step 7

---

## 📝 Ký Hiệu Debug

Thêm vào `recon_all.sh` để save intermediate files:

```bash
# Sau mỗi bước major, save debug files
mri_convert resampled_template_space.nii.gz resampled_debug.mgz
cp reg_affine.txt reg_affine_${INPUT_MRI_ID}_debug.txt

# Cho phép inspect sau
echo "DEBUG: Affine matrix saved to reg_affine_${INPUT_MRI_ID}_debug.txt"
```

---

**Tiếp theo:** Hãy chạy các diagnostic steps trên và báo cáo kết quả!
