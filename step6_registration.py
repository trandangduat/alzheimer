import os
import subprocess
import nibabel as nib
import numpy as np
from config import SUBJECTS_DIR, TOOLS, run_cmd_logged

def fs_to_vtk(sphere_path, curv_path, sulc_path, out_vtk):
    """Convert FreeSurfer sphere and scalars to VTK for S3Reg."""
    coords, faces = nib.freesurfer.read_geometry(sphere_path)
    curv = nib.freesurfer.read_morph_data(curv_path)
    sulc = nib.freesurfer.read_morph_data(sulc_path)

    with open(out_vtk, "w") as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write("Surface exported from FreeSurfer\n")
        f.write("ASCII\n")
        f.write("DATASET POLYDATA\n")
        f.write(f"POINTS {len(coords)} float\n")
        for c in coords:
            f.write(f"{c[0]} {c[1]} {c[2]}\n")
        
        f.write(f"POLYGONS {len(faces)} {len(faces)*4}\n")
        for face in faces:
            f.write(f"3 {face[0]} {face[1]} {face[2]}\n")
        
        f.write(f"POINT_DATA {len(coords)}\n")
        
        f.write("SCALARS curv float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for v in curv:
            f.write(f"{v}\n")
            
        f.write("SCALARS sulc float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for v in sulc:
            f.write(f"{v}\n")

def vtk_to_fs(vtk_path, out_reg_path):
    """Extract registered vertices from VTK and save as FreeSurfer .reg file."""
    # S3Reg output VTK has the registered positions in POINTS
    # We can use nibabel to save it. 
    # But .reg files are just geometry files (usually spheres) in FreeSurfer.
    
    # Simple way: use mris_convert if we have a template
    # Or just write it using nibabel if we know the format.
    # Actually, S3Reg output is the registered SPHERE.
    
    import torch # Needed if s3pipe is used
    from s3pipe.utils.vtk import read_vtk
    
    surf = read_vtk(vtk_path)
    vertices = surf['vertices']
    
    # We need the original faces to save as FreeSurfer geometry
    # We'll reload them from the original sphere
    return vertices

def run_step6_registration(subject_id):
    """
    BƯỚC 6: CORTICAL SURFACE REGISTRATION (S3Reg)
    Input: surf/?h.sphere, surf/?h.curv, surf/?h.sulc
    Output: surf/?h.sphere.reg
    """
    print(f"\n[6/8] [PROCESSING] CORTICAL SURFACE REGISTRATION (S3Reg) for {subject_id}...")
    
    subj_dir = os.path.join(SUBJECTS_DIR, subject_id)
    surf_dir = os.path.join(subj_dir, "surf")
    s3reg_root = TOOLS["s3reg_root"]
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "bin", "python")
    
    if not os.path.exists(venv_python): # Fallback
        venv_python = "python"

    results = []
    for hemi in ["lh", "rh"]:
        white = os.path.join(surf_dir, f"{hemi}.white")
        sphere = os.path.join(surf_dir, f"{hemi}.sphere")
        curv = os.path.join(surf_dir, f"{hemi}.curv")
        sulc = os.path.join(surf_dir, f"{hemi}.sulc")
        
        if not os.path.exists(white):
            print(f"[ERROR] Missing {hemi}.white for registration. Skipping {hemi}.")
            continue

        # 0. Generate missing files if needed
        if not os.path.exists(sphere) or not os.path.exists(curv) or not os.path.exists(sulc):
            print(f" >>> Generating missing FreeSurfer files for {hemi}...")
            
            # 0a. Create smoothwm symlink (required by mris_sphere)
            smoothwm = os.path.join(surf_dir, f"{hemi}.smoothwm")
            if not os.path.exists(smoothwm):
                os.symlink(os.path.basename(white), smoothwm)

            # 0b. mris_inflate (Generates inflated and sulc)
            inflated = os.path.join(surf_dir, f"{hemi}.inflated")
            if not os.path.exists(inflated) or not os.path.exists(sulc):
                print(f"     -> Running mris_inflate (this may take a few minutes)...")
                run_cmd_logged(["mris_inflate", white, inflated])
                # mris_inflate generates ?h.sulc automatically from white
            
            # 0c. mris_sphere (Requires inflated)
            if not os.path.exists(sphere):
                print(f"     -> Running mris_sphere (this may take a few minutes)...")
                # Syntax for FS 8.1.0 discovered in sphere_subject-lh script:
                # mris_sphere -w 0 <inflated> <sphere>
                run_cmd_logged(["mris_sphere", "-w", "0", inflated, sphere])

            # 0d. mris_curvature (Generates curv)
            if not os.path.exists(curv):
                print(f"     -> Running mris_curvature...")
                # mris_curvature -w white generates white.H and white.K
                run_cmd_logged(["mris_curvature", "-w", white])
                temp_h = f"{white}.H"
                if os.path.exists(temp_h):
                    os.rename(temp_h, curv)
                elif os.path.exists(f"{white}.curv"): # Fallback for other versions
                    os.rename(f"{white}.curv", curv)

        if not all(os.path.exists(p) for p in [sphere, curv, sulc]):
            print(f"[ERROR] Could not generate missing inputs for {hemi} registration. Skipping.")
            continue
            
        out_vtk = os.path.join(surf_dir, f"{hemi}.sphere.vtk")
        reg_vtk = os.path.join(surf_dir, f"{hemi}.sphere.reg.vtk")
        out_reg = os.path.join(surf_dir, f"{hemi}.sphere.reg")
        
        # 1. Convert to VTK
        print(f" >>> Converting {hemi} to VTK...")
        fs_to_vtk(sphere, curv, sulc, out_vtk)
        
        # 2. Run S3Reg
        # We use a specific config for sucu (sulc+curv)
        config_path = os.path.join(s3reg_root, "config", "regConfig_3level_sucu.yaml")
        # S3Reg needs an atlas. We'll use the one in the repo if available.
        atlas_path = os.path.join(s3reg_root, "atlas", f"FS.{hemi}.SphereSurf.vtk")
        
        print(f" >>> Running S3Reg for {hemi}...")
        cmd = [
            venv_python, os.path.join(s3reg_root, "s3reg.py"),
            "-hemi", hemi,
            "-c", config_path,
            "-i", out_vtk,
            "-a", atlas_path,
            "-o", reg_vtk,
            "--device", "CPU"
        ]
        
        try:
            run_cmd_logged(cmd)
            
            # 3. Convert back to FS .reg
            print(f" >>> Converting {hemi} result back to FreeSurfer format...")
            # We need to read the registered vertices and original faces
            reg_vertices = vtk_to_fs(reg_vtk, out_reg)
            _, faces = nib.freesurfer.read_geometry(sphere)
            nib.freesurfer.write_geometry(out_reg, reg_vertices, faces)
            
            print(f" [SUCCESS] Created: {out_reg}")
            results.append(out_reg)
            
        except Exception as e:
            print(f"[ERROR] Registration failed for {hemi}: {e}")
            
    return results if results else None
