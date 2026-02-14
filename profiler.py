import time
import os
import resource
import platform

try:
    import psutil
except ImportError:
    psutil = None

class StepProfiler:
    def __init__(self):
        self.stats = []
        self.current_step_start = 0
        self.current_step_name = ""
        self.start_global = time.time()

    def start_step(self, step_name):
        """Starts timing a step."""
        self.current_step_name = step_name
        self.current_step_start = time.time()
        print(f"\n--- ⏱️ START: {step_name} ---")

    def stop_step(self):
        """Stops timing the current step and records stats."""
        if not self.current_step_name:
            return

        end_time = time.time()
        duration = end_time - self.current_step_start
        
        # Memory usage (Max RSS)
        # Linux: ru_maxrss is in KB
        # macOS: ru_maxrss is in bytes
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_rss = usage.ru_maxrss
        
        if platform.system() == "Linux":
            max_rss_mb = max_rss / 1024
        else:
            max_rss_mb = max_rss / (1024 * 1024)

        # CPU percent (requires psutil for current process)
        cpu_percent = 0.0
        if psutil:
            try:
                p = psutil.Process(os.getpid())
                # This is instantaneous CPU usage, might not be representative of the whole step
                # but better than nothing. For a better metric, we'd need a background monitor.
                # Average CPU over the step is hard without background monitoring.
                # We will record the CPU usage at the END of the step.
                cpu_percent = p.cpu_percent(interval=None)
            except:
                pass

        self.stats.append({
            "step": self.current_step_name,
            "duration": duration,
            "ram_mb": max_rss_mb,
            "cpu_percent": cpu_percent
        })
        
        print(f"--- 🏁 END: {self.current_step_name} (⏱️ {duration:.2f}s, 💾 {max_rss_mb:.2f} MB) ---")
        self.current_step_name = ""

    def generate_report(self, subject_dir=None):
        """Generates a text report of the profiling stats."""
        total_time = time.time() - self.start_global
        
        lines = []
        lines.append("\n" + "="*60)
        lines.append(f"📊 PIPELINE RESOURCE REPORT")
        lines.append("="*60)
        lines.append(f"{'STEP':<40} | {'TIME (s)':<10} | {'MAX RAM (MB)':<12}")
        lines.append("-" * 60)
        
        for stat in self.stats:
            lines.append(f"{stat['step']:<40} | {stat['duration']:<10.2f} | {stat['ram_mb']:<12.2f}")
            
        lines.append("-" * 60)
        lines.append(f"{'TOTAL PIPELINE':<40} | {total_time:<10.2f} | -")
        lines.append("="*60 + "\n")
        
        report = "\n".join(lines)
        print(report)
        
        if subject_dir:
            report_path = os.path.join(subject_dir, "pipeline_stats.txt")
            try:
                with open(report_path, "w") as f:
                    f.write(report)
                print(f"📄 Report saved to: {report_path}")
            except Exception as e:
                print(f"⚠️ Could not save report: {e}")
                
        return report
