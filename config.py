import os
import sys
import subprocess

# Base paths
BASE_DIR = r"/home/anhdomixi/alzheimer"
SUBJECTS_INPUT_DIR = r"/home/anhdomixi/disc1"
SUBJECT_LIST = [
    "0012"
]

SUBJECTS_DIR = os.path.join(BASE_DIR, "subjects2")
OUTPUT_ROOT = SUBJECTS_DIR # Alias for backward compatibility if needed

# Tool configuration
USE_SYNTHSTRIP = True # Set to True to use SynthStrip, False for HD-BET

# Tool paths
TOOLS = {
    "fastsurfer_root": os.path.join(BASE_DIR, "tools", "FastSurfer"),
    "cortical_flow_root": os.path.join(BASE_DIR, "tools", "CorticalFlow"),
    "s3reg_root": os.path.join(BASE_DIR, "tools", "S3Reg")
}

# Atlas paths
SCHAEFER_GCS_ROOT = r"/home/anhdomixi/gcs_Schaefer2018_update20190916/gcs"
FREESURFER_AVERAGE_DIR = r"/usr/local/freesurfer/8.1.0/average"
S3REG_ATLAS_DIR = os.path.join(TOOLS["s3reg_root"], "atlas")

# Subdirectories for each step - DEPRECATED in favor of Subject-Centric structure
# We keep this empty or minimal if other scripts rely on importing DIRS, 
# but logic should move to using SUBJECTS_DIR/<sid>/...
DIRS = {} 

def ensure_dirs():
    """Create necessary directories if they don't exist."""
    os.makedirs(SUBJECTS_DIR, exist_ok=True)

import time

def run_cmd_logged(cmd, pid_callback=None, **kwargs):
    """Run a command, optionally notifying a callback with the child PID right after spawn."""
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd

    start_time = time.time()
    print(f"    [STARTED] CMD: {cmd_str}")

    # Hide output by default
    if "stdout" not in kwargs:
        kwargs["stdout"] = subprocess.DEVNULL
    if "stderr" not in kwargs:
        kwargs["stderr"] = subprocess.DEVNULL

    # check=True equivalent: raise on non-zero returncode
    check = kwargs.pop("check", True)

    try:
        proc = subprocess.Popen(cmd, **kwargs)

        # Notify caller about the PID immediately after spawn
        if pid_callback is not None:
            try:
                pid_callback(proc.pid)
            except Exception:
                pass

        returncode = proc.wait()
        end_time = time.time()
        elapsed = end_time - start_time

        if check and returncode != 0:
            print(f"    [FAILED] CMD (Elapsed: {elapsed:.2f}s, Exit Code: {returncode}): {cmd_str}")
            raise subprocess.CalledProcessError(returncode, cmd)

        print(f"    [FINISHED] CMD (Elapsed: {elapsed:.2f}s): {cmd_str}")
        return returncode

    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"    [FAILED] CMD (Elapsed: {elapsed:.2f}s): {cmd_str} — {e}")
        raise


