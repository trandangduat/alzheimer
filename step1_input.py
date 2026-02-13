import os
import SimpleITK as sitk
from config import DIRS

def run_step1_input(input_path):
    """
    BƯỚC 1: XỬ LÝ ĐẦU VÀO (Dùng SimpleITK để Bẻ thẳng não)
    Resamples image to 1mm isotropic and standard orientation.
    """
    print("\n[1/5] 📥 ĐANG XỬ LÝ ĐẦU VÀO (SimpleITK)...")
    output_dir = DIRS["step1"]
    filename = os.path.basename(input_path)
    base_name = filename.replace(".img", "").replace(".nii.gz", "").replace(".nii", "")
    final_path = os.path.join(output_dir, base_name + "_conform.nii.gz")

    try:
        print(f" -> Đang đọc file ảnh: {filename}")
        img = sitk.ReadImage(input_path, sitk.sitkFloat32)
        
        # Ép về 3D
        if img.GetDimension() == 4:
            print(" ⚠️ Ảnh 4D. Đang lấy volume đầu tiên...")
            size = img.GetSize()
            img = sitk.Extract(img, (size[0], size[1], size[2], 0), (0, 0, 0, 0))
        
        # Resample về chuẩn 1mm isotropic & Orientation chuẩn
        print(" 🔄 Đang Resample & Bẻ thẳng ảnh (Conform)...")
        new_size = [256, 256, 256]
        new_spacing = [1.0, 1.0, 1.0]
        # Identity Matrix for direction
        new_direction = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0] 
        
        ref_img = sitk.Image(new_size, sitk.sitkFloat32)
        ref_img.SetOrigin([0,0,0])
        ref_img.SetSpacing(new_spacing)
        ref_img.SetDirection(new_direction)
        
        tx = sitk.CenteredTransformInitializer(
            ref_img, 
            img, 
            sitk.Euler3DTransform(), 
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )
        
        resampler = sitk.ResampleImageFilter()
        resampler.SetReferenceImage(ref_img)
        resampler.SetTransform(tx)
        resampler.SetInterpolator(sitk.sitkLinear)
        resampler.SetDefaultPixelValue(0)
        
        img_conformed = resampler.Execute(img)
        sitk.WriteImage(img_conformed, final_path)
        print(f"✅ Đã xử lý xong: {final_path}")
        return final_path

    except Exception as e:
        print(f"❌ Lỗi xử lý Step 1: {e}")
        return None
