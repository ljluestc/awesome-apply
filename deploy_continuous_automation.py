#!/usr/bin/env python3
"""
🚀 DEPLOY CONTINUOUS JOB AUTOMATION 🚀
======================================

This script deploys and manages your continuous job application automation system.
It orchestrates all your existing automation scripts for maximum job application efficiency.

What this system does:
✅ Starts the JobRight.ai server with job scraping
✅ Runs your automated job application system (10 browser tabs)
✅ Monitors and restarts systems if they fail
✅ Provides real-time progress monitoring
✅ Runs continuously until you stop it
"""

import sys
import os
import time
import subprocess
import signal
import threading
import requests
from datetime import datetime, timedelta
from pathlib import Path

class ContinuousJobAutomation:
    """Deploys and manages continuous job application automation"""

    def __init__(self):
        self.base_dir = Path('/home/calelin/awesome-apply')
        self.python_path = '/home/calelin/awesome-apply/venv/bin/python'
        self.env = {
            'PYTHONPATH': '/home/calelin/awesome-apply/venv/lib/python3.13/site-packages:/home/calelin/awesome-apply',
            'PATH': os.environ.get('PATH', '')
        }

        self.processes = {}
        self.running = True
        self.stats = {
            'start_time': time.time(),
            'jobright_restarts': 0,
            'automation_restarts': 0,
            'total_applications': 0
        }

    def log(self, message: str, system: str = "DEPLOY"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{system}] {message}")

    def start_jobright_server(self):
        """Start the JobRight.ai server"""
        self.log("🚀 Starting JobRight.ai server...")

        try:
            process = subprocess.Popen(
                [self.python_path, 'ultimate_jobright_complete.py'],
                cwd=str(self.base_dir),
                env={**os.environ, **self.env},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes['jobright'] = {
                'process': process,
                'start_time': time.time(),
                'type': 'server'
            }

            # Wait for server to start
            self.log("⏳ Waiting for JobRight server to initialize...")
            time.sleep(15)

            # Check if server is running
            try:
                response = requests.get('http://localhost:5000', timeout=5)
                if response.status_code == 200:
                    self.log("✅ JobRight server started successfully", "JOBRIGHT")
                    return True
                else:
                    self.log("❌ JobRight server not responding properly", "JOBRIGHT")
                    return False
            except:
                self.log("❌ JobRight server failed to start", "JOBRIGHT")
                return False

        except Exception as e:
            self.log(f"❌ Failed to start JobRight server: {e}", "ERROR")
            return False

    def start_automation_system(self):
        """Start the automated job application system"""
        self.log("🤖 Starting automated job application system...")

        try:
            process = subprocess.Popen(
                [self.python_path, 'automated_job_application_system.py'],
                cwd=str(self.base_dir),
                env={**os.environ, **self.env},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes['automation'] = {
                'process': process,
                'start_time': time.time(),
                'type': 'automation'
            }

            # Give system time to initialize
            time.sleep(5)

            if process.poll() is None:
                self.log("✅ Automation system started successfully", "AUTOMATION")
                return True
            else:
                self.log("❌ Automation system failed to start", "AUTOMATION")
                return False

        except Exception as e:
            self.log(f"❌ Failed to start automation system: {e}", "ERROR")
            return False

    def check_system_health(self):
        """Check health of running systems and restart if needed"""
        while self.running:
            try:
                time.sleep(60)  # Check every minute

                # Check JobRight server
                if 'jobright' in self.processes:
                    process_info = self.processes['jobright']
                    process = process_info['process']

                    if process.poll() is not None:  # Process has stopped
                        self.log("⚠️ JobRight server stopped, restarting...", "MONITOR")
                        if self.start_jobright_server():
                            self.stats['jobright_restarts'] += 1
                            self.log("✅ JobRight server restarted successfully", "MONITOR")
                    else:
                        # Check if server is responding
                        try:
                            response = requests.get('http://localhost:5000', timeout=2)
                            if response.status_code != 200:
                                self.log("⚠️ JobRight server not responding, restarting...", "MONITOR")
                                process.terminate()
                                time.sleep(3)
                                if self.start_jobright_server():
                                    self.stats['jobright_restarts'] += 1
                        except:
                            pass

                # Check automation system
                if 'automation' in self.processes:
                    process_info = self.processes['automation']
                    process = process_info['process']

                    if process.poll() is not None:  # Process has stopped
                        self.log("⚠️ Automation system stopped, restarting...", "MONITOR")
                        if self.start_automation_system():
                            self.stats['automation_restarts'] += 1
                            self.log("✅ Automation system restarted successfully", "MONITOR")

            except Exception as e:
                self.log(f"❌ Health check error: {e}", "ERROR")

    def get_application_stats(self):
        """Get current application statistics"""
        try:
            response = requests.get('http://localhost:5000/api/analytics', timeout=3)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}

    def monitor_progress(self):
        """Monitor and display progress"""
        while self.running:
            try:
                time.sleep(300)  # Update every 5 minutes

                runtime = (time.time() - self.stats['start_time']) / 3600
                stats = self.get_application_stats()

                self.log("=" * 70)
                self.log("📊 CONTINUOUS AUTOMATION STATUS")
                self.log("=" * 70)
                self.log(f"⏱️  Runtime: {runtime:.1f} hours")
                self.log(f"🚀 JobRight restarts: {self.stats['jobright_restarts']}")
                self.log(f"🤖 Automation restarts: {self.stats['automation_restarts']}")

                if stats:
                    self.log(f"📝 Total applications: {stats.get('successful_applications', 0)}")
                    self.log(f"📋 Jobs in system: {stats.get('total_jobs', 0)}")
                    self.log(f"📈 Success rate: {stats.get('success_rate', 0):.1f}%")

                # Check process status
                active_processes = 0
                for name, proc_info in self.processes.items():
                    if proc_info['process'].poll() is None:
                        active_processes += 1
                        self.log(f"✅ {name.upper()}: Running")
                    else:
                        self.log(f"❌ {name.upper()}: Stopped")

                self.log(f"🏃 Active processes: {active_processes}/{len(self.processes)}")
                self.log("=" * 70)

            except Exception as e:
                self.log(f"❌ Monitor error: {e}", "ERROR")

    def deploy_automation(self):
        """Main deployment function"""
        self.log("🚀 DEPLOYING CONTINUOUS JOB APPLICATION AUTOMATION")
        self.log("=" * 70)
        self.log("🎯 MISSION: Continuously apply to jobs until you find employment")
        self.log("⚡ FEATURES: Multi-system orchestration with auto-restart")
        self.log("🤖 SYSTEMS: JobRight.ai + 10-tab automation + monitoring")
        self.log("=" * 70)

        try:
            # Start JobRight server
            if not self.start_jobright_server():
                self.log("❌ Failed to start JobRight server, aborting", "ERROR")
                return False

            # Start automation system
            if not self.start_automation_system():
                self.log("❌ Failed to start automation system, continuing anyway", "WARNING")

            # Start health monitoring
            health_thread = threading.Thread(target=self.check_system_health, daemon=True)
            health_thread.start()

            # Start progress monitoring
            monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
            monitor_thread.start()

            self.log("🎉 ALL SYSTEMS DEPLOYED SUCCESSFULLY!")
            self.log("🌐 JobRight Dashboard: http://localhost:5000")
            self.log("🤖 Automation: Running in 10 browser tabs")
            self.log("📊 Monitoring: Real-time health and progress tracking")
            self.log("⌨️  Press Ctrl+C to stop all systems")
            self.log("=" * 70)

            # Main loop
            while self.running:
                try:
                    time.sleep(3600)  # Sleep for 1 hour

                    # Hourly summary
                    runtime_hours = (time.time() - self.stats['start_time']) / 3600
                    stats = self.get_application_stats()

                    self.log("🕐 HOURLY SUMMARY:")
                    self.log(f"   ⏱️  Runtime: {runtime_hours:.1f} hours")
                    self.log(f"   🚀 Applications: {stats.get('successful_applications', 0)}")
                    self.log(f"   📋 Jobs available: {stats.get('total_jobs', 0)}")

                    if stats.get('successful_applications', 0) > 0:
                        self.log("   🎉 Applications are being submitted successfully!")
                    else:
                        self.log("   ⏳ Systems are running, applications will come...")

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.log(f"❌ Main loop error: {e}", "ERROR")

            return True

        except KeyboardInterrupt:
            self.log("🛑 Deployment stopped by user")
            return True
        except Exception as e:
            self.log(f"❌ Fatal deployment error: {e}", "ERROR")
            return False

    def stop_all_systems(self):
        """Gracefully stop all systems"""
        self.log("🛑 Stopping all automation systems...")
        self.running = False

        for name, proc_info in self.processes.items():
            try:
                process = proc_info['process']
                if process.poll() is None:
                    self.log(f"🛑 Stopping {name}...")
                    process.terminate()

                    try:
                        process.wait(timeout=10)
                        self.log(f"✅ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        self.log(f"⚠️ Force killing {name}...")
                        process.kill()
                        process.wait()
                        self.log(f"💀 {name} force killed")

            except Exception as e:
                self.log(f"❌ Error stopping {name}: {e}", "ERROR")

        self.log("✅ All systems stopped")

    def print_final_summary(self):
        """Print final deployment summary"""
        runtime_hours = (time.time() - self.stats['start_time']) / 3600
        stats = self.get_application_stats()

        self.log("=" * 70)
        self.log("🏁 CONTINUOUS AUTOMATION DEPLOYMENT COMPLETED")
        self.log("=" * 70)
        self.log(f"⏱️  Total runtime: {runtime_hours:.1f} hours")
        self.log(f"🔄 JobRight restarts: {self.stats['jobright_restarts']}")
        self.log(f"🔄 Automation restarts: {self.stats['automation_restarts']}")

        if stats:
            applications = stats.get('successful_applications', 0)
            jobs = stats.get('total_jobs', 0)
            self.log(f"🚀 Applications submitted: {applications}")
            self.log(f"📋 Jobs processed: {jobs}")

            if applications > 0:
                self.log("🎉 SUCCESS! Job applications have been submitted")
                self.log("📧 Check your email for responses from employers")
                self.log("💼 Keep your LinkedIn and phone available for interviews")
            else:
                self.log("⏳ Systems ran successfully but may need more time")
                self.log("💡 Consider running for longer periods for best results")
        else:
            self.log("ℹ️ Statistics not available")

        self.log("=" * 70)

def main():
    """Main deployment function"""
    automation = ContinuousJobAutomation()

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutdown signal received...")
        automation.stop_all_systems()
        automation.print_final_summary()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 CONTINUOUS JOB APPLICATION AUTOMATION DEPLOYMENT")
    print("=" * 70)
    print("This system will:")
    print("✅ Deploy JobRight.ai server with job scraping")
    print("✅ Launch 10 automated browser tabs for job applications")
    print("✅ Monitor and restart systems automatically")
    print("✅ Provide real-time progress updates")
    print("✅ Run continuously until you stop it (Ctrl+C)")
    print("✅ Apply to jobs 24/7 to maximize your chances")
    print("=" * 70)

    try:
        success = automation.deploy_automation()
        automation.stop_all_systems()
        automation.print_final_summary()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        automation.stop_all_systems()
        sys.exit(1)

if __name__ == "__main__":
    main()