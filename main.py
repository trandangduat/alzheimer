import sys
import os
import time
import datetime
from config import ensure_dirs, SUBJECT_LIST, SUBJECTS_INPUT_DIR, SUBJECTS_DIR
from step1_input_reorientation import run_step1_input_reorientation
from step2_image_standardization import run_step2_image_standardization
from step3_brain_extraction import run_step3_brain_extraction
from step4_seg_and_parc import run_step4_seg_and_parc
from step5_surface_reconstruction import run_step5_surface_reconstruction
from step6_registration import run_step6_registration
from step7_parcellation import run_step7_parcellation
from step8_anatomical_stats import run_step8_anatomical_stats
from monitor import StepMonitor, save_timeseries, save_step_stats


class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")
        self.is_new_line = True

    def write(self, message):
        if not message:
            return

        lines = message.splitlines(True)
        for line in lines:
            if self.is_new_line and line != '\n':
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                out_line = f"[{timestamp}] {line}"
            else:
                out_line = line

            self.terminal.write(out_line)
            self.log.write(out_line)
            self.is_new_line = line.endswith('\n')

        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()


def log_message(msg, log_file=None):
    print(msg)


def run_monitored(step_name, fn, sid, scripts_dir, stats_path, subject_stats_path, *args, **kwargs):
    """
    Run fn(*args, **kwargs) while monitoring the current process tree for
    CPU and RAM usage. Saves raw timeseries and step stats afterwards.
    Writes to both the global stats_path and the per-subject subject_stats_path.
    Returns fn's return value.
    """
    monitor = StepMonitor(interval=2)
    monitor.start(step_name, os.getpid())
    t0 = time.time()
    try:
        result = fn(*args, **kwargs)
    finally:
        rows = monitor.stop()
        elapsed_minutes = (time.time() - t0) / 60.0
        if rows:
            save_timeseries(sid, rows, scripts_dir)
            save_step_stats(sid, step_name, rows, elapsed_minutes, stats_path)          # global
            save_step_stats(sid, step_name, rows, elapsed_minutes, subject_stats_path)  # per-subject
            ram_mean = sum(r[3] for r in rows) / len(rows)
            log_message(
                f"[MONITOR] {step_name} — "
                f"elapsed: {elapsed_minutes:.2f} min, "
                f"RAM mean: {ram_mean:.3f} GB"
            )
        else:
            log_message(f"[MONITOR] {step_name} — no samples collected")
    return result


def process_subject(sid):
    input_path = os.path.join(
        SUBJECTS_INPUT_DIR,
        f"OAS1_{sid}_MR1",
        "PROCESSED",
        "MPRAGE",
        "SUBJ_111",
        f"OAS1_{sid}_MR1_mpr_n4_anon_sbj_111.img"
    )

    # Ensure subject specific dirs exist
    subj_dir = os.path.join(SUBJECTS_DIR, sid)
    scripts_dir = os.path.join(subj_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    log_file = os.path.join(scripts_dir, "pipeline.log")

    # Shared stats file (accumulates rows across all subjects)
    stats_path = os.path.join(SUBJECTS_DIR, "step_stats.csv")
    # Per-subject stats file
    subject_stats_path = os.path.join(scripts_dir, f"step_stats_{sid}.csv")

    # Save original stdout/stderr and redirect
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Logger(log_file)
    sys.stderr = sys.stdout

    log_message(f"--- STARTING PIPELINE FOR SUBJECT: {sid} ---")
    log_message(f"Input path: {input_path}")

    os.environ["SUBJECTS_DIR"] = SUBJECTS_DIR
    log_message(f"export SUBJECTS_DIR={SUBJECTS_DIR}")
    log_message(f"Subject ID: {sid}")

    try:
        # Step 1: Input Reorientation
        log_message("Step 1: Input Reorientation started")
        mri_file = run_monitored(
            "Step 1: Input Reorientation",
            run_step1_input_reorientation,
            sid, scripts_dir, stats_path, subject_stats_path,
            input_path, sid, SUBJECTS_DIR
        )
        log_message("Step 1: Input Reorientation finished")
        if not mri_file:
            return

        # Step 2: Image Standardization (nu, t1)
        log_message("Step 2: Image Standardization (nu, t1) started")
        t1_file = run_monitored(
            "Step 2: Image Standardization (nu, t1)",
            run_step2_image_standardization,
            sid, scripts_dir, stats_path, subject_stats_path,
            sid
        )
        log_message("Step 2: Image Standardization (nu, t1) finished")
        if not t1_file:
            log_message("[WARNING] Image Standardization failed, continuing pipeline...")

        # Step 3: Brain Extraction
        log_message("Step 3: Brain Extraction started")
        brainmask_file = run_monitored(
            "Step 3: Brain Extraction",
            run_step3_brain_extraction,
            sid, scripts_dir, stats_path, subject_stats_path,
            sid
        )
        log_message("Step 3: Brain Extraction finished")
        if not brainmask_file:
            log_message("[WARNING] Brain Extraction failed, continuing pipeline...")

        # Step 4: Seg and Parc (Subcortical Segmentation & Cortical Parcellation)
        log_message("Step 4: Seg and Parc (Subcortical Segmentation & Cortical Parcellation) started")
        seg_file = run_monitored(
            "Step 4: Seg and Parc",
            run_step4_seg_and_parc,
            sid, scripts_dir, stats_path, subject_stats_path,
            mri_file, sid
        )
        log_message("Step 4: Seg and Parc (Subcortical Segmentation & Cortical Parcellation) finished")
        if not seg_file:
            return

        # Step 5: Surface Reconstruction (CorticalFlow)
        log_message("Step 5: Surface Reconstruction started")
        cf_output_dir = run_monitored(
            "Step 5: Surface Reconstruction",
            run_step5_surface_reconstruction,
            sid, scripts_dir, stats_path, subject_stats_path,
            mri_file, sid
        )
        log_message("Step 5: Surface Reconstruction finished")
        if not cf_output_dir:
            log_message("[WARNING] Surface Reconstruction failed, continuing pipeline...")

        # Step 6: Cortical Surface Registration
        log_message("Step 6: Cortical Surface Registration started")
        registration_result = run_monitored(
            "Step 6: Registration",
            run_step6_registration,
            sid, scripts_dir, stats_path, subject_stats_path,
            sid
        )
        log_message("Step 6: Cortical Surface Registration finished")
        if not registration_result:
            log_message("[WARNING] Registration failed, continuing pipeline...")

        # Step 7: Parcellation
        log_message("Step 7: Parcellation started")
        parcellation_result = run_monitored(
            "Step 7: Parcellation",
            run_step7_parcellation,
            sid, scripts_dir, stats_path, subject_stats_path,
            sid
        )
        log_message("Step 7: Parcellation finished")
        if not parcellation_result:
            log_message("[WARNING] Parcellation failed, continuing pipeline...")

        # Step 8: Anatomical Stats
        log_message("Step 8: Anatomical Stats started")
        stats_result = run_monitored(
            "Step 8: Anatomical Stats",
            run_step8_anatomical_stats,
            sid, scripts_dir, stats_path, subject_stats_path,
            sid
        )
        log_message("Step 8: Anatomical Stats finished")
        if not stats_result:
            log_message("[WARNING] Anatomical Stats failed.")


        log_message("--- PIPELINE COMPLETED SUCCESSFULLY ---")

    except Exception as e:
        log_message(f"[ERROR] Pipeline failed: {e}")
    finally:
        # Restore stdout/stderr
        sys.stdout.log.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def main():
    print("STARTING ALZHEIMER PIPELINES (Sequential)")
    ensure_dirs()

    if len(sys.argv) > 1:
        process_subject(sys.argv[1])
    else:
        for sid in SUBJECT_LIST:
            process_subject(sid)


if __name__ == "__main__":
    main()
