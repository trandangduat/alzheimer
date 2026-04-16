#!/usr/bin/env python3
"""
debug_adni_surface_alignment.py

Comprehensive diagnostic tool để phân tích vấn đề tái tạo bề mặt ADNI
So sánh OASIS (baseline) vs ADNI (problem)

Usage:
    python debug_adni_surface_alignment.py
"""

import os
import sys
import numpy as np
import nibabel as nib
from pathlib import Path

# Configuration
BASE_DIR = "/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer"
SUBJECTS_DIR = os.path.join(BASE_DIR, "pipeline-subjects")
OASIS_SID = "0006"
ADNI_SID = "I776974"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{bcolors.BOLD}{bcolors.HEADER}{'='*60}{bcolors.ENDC}")
    print(f"{bcolors.BOLD}{bcolors.HEADER}{text:^60}{bcolors.ENDC}")
    print(f"{bcolors.BOLD}{bcolors.HEADER}{'='*60}{bcolors.ENDC}\n")

def print_section(text):
    print(f"\n{bcolors.OKBLUE}▶ {text}{bcolors.ENDC}")

def print_success(text):
    print(f"{bcolors.OKGREEN}✓ {text}{bcolors.ENDC}")

def print_warning(text):
    print(f"{bcolors.WARNING}⚠ {text}{bcolors.ENDC}")

def print_error(text):
    print(f"{bcolors.FAIL}✗ {text}{bcolors.ENDC}")

def check_mri_conformity(sid):
    """Check if mri/orig.mgz has correct dimensions after conform"""
    orig_path = os.path.join(SUBJECTS_DIR, sid, "mri", "orig.mgz")
    
    if not os.path.exists(orig_path):
        print_error(f"File not found: {orig_path}")
        return None
    
    try:
        img = nib.load(orig_path)
        shape = img.shape
        affine = img.affine
        voxel_size = np.diag(affine)[:3]
        
        print(f"  Shape: {shape}")
        print(f"  Voxel size: {voxel_size} mm")
        print(f"  Affine matrix (first 3x4):\n{str(affine)}")
        
        # Check conformity
        expected_shape = (256, 256, 256)
        expected_voxel_size = np.array([1.0, 1.0, 1.0])
        
        is_correct = (shape == expected_shape and 
                     np.allclose(np.abs(voxel_size), expected_voxel_size, atol=0.01))
        
        if is_correct:
            print_success(f"{sid}: Conform output is CORRECT (256³, 1mm iso)")
        else:
            print_warning(f"{sid}: Conform output may be INCORRECT")
            if shape != expected_shape:
                print_error(f"  Expected shape {expected_shape}, got {shape}")
            if not np.allclose(np.abs(voxel_size), expected_voxel_size, atol=0.01):
                print_error(f"  Expected voxel size {expected_voxel_size}, got {voxel_size}")
        
        return {"shape": shape, "voxel_size": voxel_size, "affine": affine}
        
    except Exception as e:
        print_error(f"Error reading {orig_path}: {e}")
        return None

def check_affine_registration(sid):
    """Check affine registration matrix quality"""
    affine_path = os.path.join(SUBJECTS_DIR, sid, "mri", "transforms", "reg_affine.txt")
    
    if not os.path.exists(affine_path):
        print_warning(f"Affine file not found: {affine_path}")
        return None
    
    try:
        affine_matrix = np.loadtxt(affine_path)
        
        print(f"  Matrix shape: {affine_matrix.shape}")
        print(f"  Affine matrix:\n{affine_matrix}")
        
        # Decompose affine into rotation, scale, translation
        if affine_matrix.shape == (4, 4):
            rotation_scale = affine_matrix[:3, :3]
            translation = affine_matrix[:3, 3]
            
            # Calculate scale factor (determinant)
            scale = np.linalg.det(rotation_scale) ** (1/3)
            
            # Calculate condition number (should be low)
            cond_num = np.linalg.cond(rotation_scale)
            
            # Calculate inverse for back-transformation
            try:
                inverse_matrix = np.linalg.inv(affine_matrix)
                det_inverse = np.linalg.det(inverse_matrix[:3, :3]) ** (1/3)
            except:
                inverse_matrix = None
                det_inverse = None
            
            print(f"\n  Scale factor: {scale:.6f} (should be ~1.0)")
            print(f"  Condition number: {cond_num:.6f} (lower is better, should be <100)")
            print(f"  Translation: {translation} mm")
            if det_inverse:
                print(f"  Inverse scale: {det_inverse:.6f} (for back-transform)")
            
            return {
                "matrix": affine_matrix,
                "scale": scale,
                "cond_num": cond_num,
                "translation": translation,
                "inverse": inverse_matrix
            }
        else:
            print_warning(f"Unexpected affine matrix shape: {affine_matrix.shape}")
            return {"matrix": affine_matrix}
            
    except Exception as e:
        print_error(f"Error reading {affine_path}: {e}")
        return None

def check_surface_files(sid):
    """Check if surface files exist and have reasonable vertices"""
    surf_dir = os.path.join(SUBJECTS_DIR, sid, "surf")
    
    surfaces = {}
    for hemisphere in ["lh", "rh"]:
        for surf_type in ["white", "pial"]:
            surf_file = os.path.join(surf_dir, f"{hemisphere}.{surf_type}")
            
            if os.path.exists(surf_file):
                try:
                    # Try to read as STL or FreeSurfer format
                    if surf_file.endswith('.stl'):
                        import trimesh
                        mesh = trimesh.load(surf_file)
                        vertices = mesh.vertices
                    else:
                        # Assume FreeSurfer format
                        verts, faces = nib.freesurfer.read_geometry(surf_file)
                        vertices = verts
                    
                    surfaces[f"{hemisphere}.{surf_type}"] = {
                        "exists": True,
                        "path": surf_file,
                        "n_verts": len(vertices),
                        "bounds": {
                            "min": vertices.min(axis=0),
                            "max": vertices.max(axis=0),
                            "mean": vertices.mean(axis=0)
                        }
                    }
                    print_success(f"{hemisphere}.{surf_type}: {len(vertices)} vertices")
                    print(f"    Bounds (mm): x=[{vertices[:, 0].min():.1f}, {vertices[:, 0].max():.1f}], "
                          f"y=[{vertices[:, 1].min():.1f}, {vertices[:, 1].max():.1f}], "
                          f"z=[{vertices[:, 2].min():.1f}, {vertices[:, 2].max():.1f}]")
                except Exception as e:
                    print_error(f"{hemisphere}.{surf_type}: {e}")
                    surfaces[f"{hemisphere}.{surf_type}"] = {"exists": False, "error": str(e)}
            else:
                print_warning(f"{hemisphere}.{surf_type}: Not found")
                surfaces[f"{hemisphere}.{surf_type}"] = {"exists": False}
    
    return surfaces

def compare_subjects():
    """Main diagnostic comparison"""
    
    print_header("MRI Conformity Check (1mm Isotropic, 256³)")
    
    print_section(f"OASIS Subject {OASIS_SID}")
    oasis_mri = check_mri_conformity(OASIS_SID)
    
    print_section(f"ADNI Subject {ADNI_SID}")
    adni_mri = check_mri_conformity(ADNI_SID)
    
    # Compare conformity
    if oasis_mri and adni_mri:
        if oasis_mri["shape"] == adni_mri["shape"]:
            print_success("Both have same shape after conform ✓")
        else:
            print_error(f"Shape mismatch: OASIS={oasis_mri['shape']}, ADNI={adni_mri['shape']}")
    
    # ============================================================
    
    print_header("Affine Registration Analysis")
    
    print_section(f"OASIS Subject {OASIS_SID}")
    oasis_affine = check_affine_registration(OASIS_SID)
    
    print_section(f"ADNI Subject {ADNI_SID}")
    adni_affine = check_affine_registration(ADNI_SID)
    
    # Compare affine matrices
    if oasis_affine and adni_affine:
        if "scale" in oasis_affine and "scale" in adni_affine:
            print_section("Affine Comparison")
            print(f"  OASIS scale: {oasis_affine['scale']:.6f}")
            print(f"  ADNI scale:  {adni_affine['scale']:.6f}")
            
            scale_diff = abs(oasis_affine['scale'] - adni_affine['scale'])
            if scale_diff > 0.1:
                print_warning(f"Scale difference: {scale_diff:.6f} (may indicate poor registration)")
            else:
                print_success(f"Scale difference: {scale_diff:.6f} (acceptable)")
    
    # ============================================================
    
    print_header("Surface Files Check")
    
    print_section(f"OASIS Subject {OASIS_SID} - Surfaces")
    oasis_surfaces = check_surface_files(OASIS_SID)
    
    print_section(f"ADNI Subject {ADNI_SID} - Surfaces")
    adni_surfaces = check_surface_files(ADNI_SID)
    
    # Compare surface vertices bounds
    if all(oasis_surfaces.get(k, {}).get("exists") for k in ["lh.white", "lh.pial"]):
        print_success("OASIS has all surfaces")
    else:
        print_error("OASIS missing surfaces")
    
    if all(adni_surfaces.get(k, {}).get("exists") for k in ["lh.white", "lh.pial"]):
        print_success("ADNI has all surfaces")
    else:
        print_error("ADNI missing surfaces")
    
    # ============================================================
    
    print_header("Recommendations")
    
    issues = []
    
    if oasis_mri and adni_mri and oasis_mri["shape"] != adni_mri["shape"]:
        issues.append("1. MRI conformity issue - shapes differ after mri_convert --conform")
    
    if oasis_affine and adni_affine and "scale" in oasis_affine and "scale" in adni_affine:
        if abs(oasis_affine['scale'] - adni_affine['scale']) > 0.1:
            issues.append("2. Affine registration problem - scale factors differ significantly")
    
    if not adni_surfaces.get("lh.white", {}).get("exists"):
        issues.append("3. Surface files missing for ADNI - rerun CorticalFlow")
    
    if issues:
        print("Potential issues identified:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("No obvious issues detected. Issue may be subtle in coordinate transforms.")
    
    print("\nDebug Next Steps:")
    print("  1. Visualize orig.mgz: freeview pipeline-subjects/{OASIS,ADNI}/mri/orig.mgz &")
    print("  2. Compare resampled images after affine registration")
    print("  3. Check visual alignment in FreeView")
    print("  4. Verify hemisphere cropping in CorticalFlow/src/data.py")

if __name__ == "__main__":
    try:
        compare_subjects()
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
