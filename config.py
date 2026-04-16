import os
import sys
import subprocess

# Base paths
BASE_DIR = r"/mnt/c/Users/ADMIN/Desktop/MRI/alzheimer"

# #FOR OASIS
# SUBJECTS_INPUT_DIR = r"/home/trandangduat/freesurfer-test/disc1"
# SUBJECT_LIST = [
#     "0006",
#     "0012",
#     "0022",
#     "0023"
# ]

# FOR ADNI
SUBJECTS_INPUT_DIR = r"/mnt/c/Users/ADMIN/Desktop/MRI/ADNI/OneDrive_1_4-10-2026/009_S_4741/MPRAGE_GRAPPA2/2016-08-24_15_47_32.0"
SUBJECT_LIST = [ "I776974" ]


SUBJECTS_DIR = os.path.join(BASE_DIR, "pipeline-subjects")
OUTPUT_ROOT = SUBJECTS_DIR  # Alias for backward compatibility if needed

# Tool configuration
USE_SYNTHSTRIP = True  # Set to True to use SynthStrip, False for HD-BET

# Tool paths
TOOLS = {
    "fastsurfer_root": os.path.join(BASE_DIR, "tools", "FastSurfer"),
    "cortical_flow_root": os.path.join(BASE_DIR, "tools", "CorticalFlow"),
    "sugar_docker_image": "ninganme/sugar:latest",  # SUGAR registration tool
}

# Atlas paths
SCHAEFER_GCS_ROOT = (
    r"/mnt/c/Users/ADMIN/Desktop/MRI/gcs_Schaefer2018_update20190916/gcs"
)
FREESURFER_AVERAGE_DIR = r"/usr/local/freesurfer/8.1.0/average"
# S3REG_ATLAS_DIR removed — registration now uses SUGAR

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
    cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd

    start_time = time.time()
    print(f"    [STARTED] CMD: {cmd_str}")

    # Capture output by default so failures can be diagnosed from logs.
    capture_stdout = "stdout" not in kwargs
    capture_stderr = "stderr" not in kwargs
    if capture_stdout:
        kwargs["stdout"] = subprocess.PIPE
    if capture_stderr:
        kwargs["stderr"] = subprocess.PIPE

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

        stdout_data, stderr_data = proc.communicate()
        returncode = proc.returncode
        end_time = time.time()
        elapsed = end_time - start_time

        if check and returncode != 0:
            print(
                f"    [FAILED] CMD (Elapsed: {elapsed:.2f}s, Exit Code: {returncode}): {cmd_str}"
            )
            if capture_stdout and stdout_data:
                print("    [STDOUT]")
                print(
                    stdout_data.decode(errors="replace")
                    if isinstance(stdout_data, bytes)
                    else stdout_data
                )
            if capture_stderr and stderr_data:
                print("    [STDERR]")
                print(
                    stderr_data.decode(errors="replace")
                    if isinstance(stderr_data, bytes)
                    else stderr_data
                )
            raise subprocess.CalledProcessError(
                returncode, cmd, output=stdout_data, stderr=stderr_data
            )

        print(f"    [FINISHED] CMD (Elapsed: {elapsed:.2f}s): {cmd_str}")
        return returncode

    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"    [FAILED] CMD (Elapsed: {elapsed:.2f}s): {cmd_str} — {e}")
        raise
