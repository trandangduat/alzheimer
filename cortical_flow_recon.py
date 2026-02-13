import os
import subprocess
import logging
import numpy as np
import trimesh
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorticalFlowRecon:
    def __init__(self, tools_dir, output_base_dir):
        """
        Initialize the CorticalFlowRecon class.
        
        Args:
            tools_dir (str): Path to the tools directory containing CorticalFlow.
            output_base_dir (str): Path to the directory where outputs will be saved.
        """
        self.tools_dir = os.path.abspath(tools_dir)
        self.cortical_flow_dir = os.path.join(self.tools_dir, "CorticalFlow")
        self.output_base_dir = os.path.abspath(output_base_dir)
        
        # Resource paths
        self.template_path = os.path.join(self.cortical_flow_dir, 'resources/MNI152_T1_1mm.nii.gz')
        self.cfpp_predict_lh = os.path.join(self.cortical_flow_dir, 'resources/trained_models/CFPP_predict_lh.yaml')
        self.cfpp_predict_rh = os.path.join(self.cortical_flow_dir, 'resources/trained_models/CFPP_predict_rh.yaml')
        
        # Verify resources exist
        self._check_paths()

    def _check_paths(self):
        if not os.path.exists(self.cortical_flow_dir):
            raise FileNotFoundError(f"CorticalFlow directory not found at {self.cortical_flow_dir}")
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found at {self.template_path}")
        if not os.path.exists(self.cfpp_predict_lh):
            raise FileNotFoundError(f"LH config not found at {self.cfpp_predict_lh}")
        if not os.path.exists(self.cfpp_predict_rh):
            raise FileNotFoundError(f"RH config not found at {self.cfpp_predict_rh}")

    def setup_dirs(self, mri_id):
        """Creates necessary subdirectories for a specific MRI ID."""
        subject_dir = os.path.join(self.output_base_dir, mri_id)
        dirs = [
            os.path.join(subject_dir, "niftyreg"),
            os.path.join(subject_dir, "CFPP")
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        return subject_dir

    def run_command(self, command):
        """Helper to run shell commands."""
        logger.info(f"Running command: {' '.join(command)}")
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr}")
            raise

    def run_registration(self, mri_id, mri_path):
        """Runs affine registration using NiftyReg."""
        subject_dir = os.path.join(self.output_base_dir, mri_id)
        niftyreg_dir = os.path.join(subject_dir, "niftyreg")
        
        affine_txt = os.path.join(niftyreg_dir, "reg_affine.txt")
        resampled_nii = os.path.join(niftyreg_dir, "orig_affine.nii.gz")
        
        # reg_aladin
        cmd_aladin = [
            "reg_aladin",
            "-ref", self.template_path,
            "-flo", mri_path,
            "-aff", affine_txt
        ]
        self.run_command(cmd_aladin)
        
        # reg_resample
        cmd_resample = [
            "reg_resample",
            "-ref", self.template_path,
            "-flo", mri_path,
            "-trans", affine_txt,
            "-res", resampled_nii,
            "-inter", "3"
        ]
        self.run_command(cmd_resample)
        
        return affine_txt, resampled_nii

    def run_prediction(self, mri_id, resampled_nii):
        """Runs CorticalFlow prediction for both hemispheres."""
        predict_script = os.path.join(self.cortical_flow_dir, "predict.py")
        subject_dir = os.path.join(self.output_base_dir, mri_id)
        cfpp_dir = os.path.join(subject_dir, "CFPP")
        
        common_args = [
            sys.executable, predict_script,
            f"outputs.output_dir={cfpp_dir}",
            "inputs.data_type='list'",
            f"inputs.path={resampled_nii}",
            f"inputs.split_name={mri_id}",
            "outputs.out_deform='[2]'"
        ]
        
        # Left Hemisphere
        cmd_lh = common_args + [f"user_config={self.cfpp_predict_lh}"]
        self.run_command(cmd_lh)
        
        # Right Hemisphere
        cmd_rh = common_args + [f"user_config={self.cfpp_predict_rh}"]
        self.run_command(cmd_rh)

    def apply_inverse_affine(self, mri_id, affine_txt_path):
        """
        Maps generated surfaces back to the original space using the inverse affine matrix.
        Replicates logic from CorticalFlow/scripts/apply_affine.py
        """
        import nibabel as nib

        subject_dir = os.path.join(self.output_base_dir, mri_id)
        cfpp_subject_dir = os.path.join(subject_dir, "CFPP", mri_id)
        
        # Find all generated surfaces (pial and white)
        surfaces = []
        if os.path.exists(cfpp_subject_dir):
            for f in os.listdir(cfpp_subject_dir):
                if f.endswith(".pial") or f.endswith(".white"):
                    surfaces.append(os.path.join(cfpp_subject_dir, f))
        
        if not surfaces:
            logger.warning(f"No surfaces found in {cfpp_subject_dir} to transform.")
            return

        # Load affine matrix and invert it
        try:
            affine_matrix = np.loadtxt(affine_txt_path)
            inv_affine_matrix = np.linalg.inv(affine_matrix)
        except Exception as e:
            logger.error(f"Failed to load or invert affine matrix: {e}")
            raise

        for surf_path in surfaces:
            try:
                # Load mesh using nibabel
                vertices, faces = nib.freesurfer.io.read_geometry(surf_path)
                vertices = np.array(vertices).astype(np.float64)
                
                # Apply inverse affine
                # Homogeneous coordinates
                ones = np.ones((vertices.shape[0], 1))
                vertices_homo = np.hstack([vertices, ones])
                
                # Transform
                vertices_transformed = np.dot(inv_affine_matrix, vertices_homo.T).T[:, :3]
                
                # Save
                dirname = os.path.dirname(surf_path)
                filename = os.path.basename(surf_path)
                name, ext = os.path.splitext(filename)
                
                output_filename = os.path.join(subject_dir, f"{name}_native{ext}")
                
                # Save using nibabel
                nib.freesurfer.io.write_geometry(output_filename, vertices_transformed, faces)
                logger.info(f"Saved native surface to {output_filename}")
                
            except Exception as e:
                logger.error(f"Failed to process surface {surf_path}: {e}")

    def process_single_mri(self, mri_id, mri_path):
        """Full pipeline for a single MRI."""
        logger.info(f"Processing MRI: {mri_id}")
        
        # 1. Setup
        self.setup_dirs(mri_id)
        
        # 2. Registration
        affine_txt, resampled_nii = self.run_registration(mri_id, mri_path)
        
        # 3. Prediction
        self.run_prediction(mri_id, resampled_nii)
        
        # 4. Map back to native space
        self.apply_inverse_affine(mri_id, affine_txt)
        
        logger.info(f"Completed processing for {mri_id}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run CorticalFlow Reconstruction")
    parser.add_argument("--input", required=True, help="Input MRI file path (nifti)")
    parser.add_argument("--sid", required=True, help="Subject ID")
    parser.add_argument("--tools_dir", required=True, help="Tools directory path")
    parser.add_argument("--output_dir", required=True, help="Base output directory")
    
    args = parser.parse_args()
    
    try:
        recon = CorticalFlowRecon(args.tools_dir, args.output_dir)
        recon.process_single_mri(args.sid, args.input)
        print("CorticalFlow reconstruction completed successfully.")
    except Exception as e:
        print(f"Error during CorticalFlow reconstruction: {e}")
        sys.exit(1)
