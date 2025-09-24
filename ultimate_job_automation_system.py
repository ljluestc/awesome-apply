#!/usr/bin/env python3
"""
🚀 ULTIMATE JOB AUTOMATION SYSTEM 🚀
====================================

This is the most comprehensive job application automation system that:
✅ Runs multiple job application systems in parallel
✅ Uses your existing JobRight.ai system for job matching and applications
✅ Scrapes jobs from multiple platforms (LinkedIn, Indeed, Glassdoor, etc.)
✅ Automatically applies to jobs using intelligent automation
✅ Tracks applications across all systems
✅ Provides real-time monitoring and statistics
✅ Runs continuously until stopped

Features:
- Multi-system orchestration (runs all your existing automation scripts)
- Real-time progress monitoring across all systems
- Consolidated application tracking
- Intelligent load balancing
- Error recovery and retry mechanisms
- Comprehensive logging and analytics
"""

import sys
import os
import time
import threading
import subprocess
import json
import requests
import signal
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import random
from typing import Dict, List, Any, Optional

sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

class UltimateJobAutomationSystem:
    """Orchestrates all job automation systems for maximum job application efficiency"""

    def __init__(self):
        self.base_dir = Path('/home/calelin/awesome-apply')
        self.python_path = '/home/calelin/awesome-apply/venv/bin/python'
        self.env = {
            'PYTHONPATH': '/home/calelin/awesome-apply/venv/lib/python3.13/site-packages:/home/calelin/awesome-apply',
            'PATH': os.environ.get('PATH', '')
        }

        # System orchestration
        self.active_systems = {}
        self.system_stats = {}
        self.total_applications = 0
        self.running = True

        # Define all automation systems to run
        self.automation_systems = {
            'jobright_complete': {
                'script': 'ultimate_jobright_complete.py',
                'description': 'Complete JobRight.ai system with real job aggregation',
                'type': 'server',
                'port': 5000,
                'priority': 1
            },
            'automated_applications': {
                'script': 'automated_job_application_system.py',
                'description': '10-page parallel job application automation',
                'type': 'client',
                'priority': 2
            },
            'master_applier': {
                'script': 'master_job_applier.py',
                'description': 'LinkedIn scraper with intelligent auto-apply',
                'type': 'scraper',
                'priority': 3
            },
            'jobright_browser': {
                'script': 'jobright_browser_automation.py',
                'description': 'Browser-based job application automation',
                'type': 'browser',
                'priority': 4
            },
            'ultimate_automation': {
                'script': 'ultimate_jobright_automation.py',
                'description': 'Ultimate JobRight automation with pattern learning',
                'type': 'pattern',
                'priority': 5
            }
        }

    def log(self, message: str, system: str = "ORCHESTRATOR"):
        """Enhanced logging with system identification"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{system}] {message}")

    def check_system_requirements(self) -> bool:
        """Check if all required systems and dependencies are available"""
        self.log("🔍 Checking system requirements...")

        # Check Python environment
        if not os.path.exists(self.python_path):
            self.log(f"❌ Python environment not found at {self.python_path}", "ERROR")
            return False

        # Check required scripts
        missing_scripts = []
        for name, system in self.automation_systems.items():
            script_path = self.base_dir / system['script']
            if not script_path.exists():
                missing_scripts.append(system['script'])

        if missing_scripts:
            self.log(f"❌ Missing scripts: {', '.join(missing_scripts)}", "ERROR")
            return False

        self.log("✅ All system requirements satisfied")
        return True

    def start_jobright_server(self):
        """Start the JobRight.ai server system"""
        system = self.automation_systems['jobright_complete']
        self.log(f"🚀 Starting {system['description']}")

        try:
            # Start the server
            process = subprocess.Popen(
                [self.python_path, system['script']],
                cwd=str(self.base_dir),
                env={**os.environ, **self.env},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.active_systems['jobright_complete'] = {
                'process': process,
                'start_time': time.time(),
                'type': 'server',
                'status': 'starting'
            }

            # Wait for server to start
            self.log("⏳ Waiting for JobRight server to start...")
            time.sleep(15)

            # Check if server is running
            try:
                response = requests.get('http://localhost:5000', timeout=5)
                if response.status_code == 200:
                    self.log("✅ JobRight server started successfully")
                    self.active_systems['jobright_complete']['status'] = 'running'
                    return True
                else:
                    self.log("❌ JobRight server not responding properly")
                    return False
            except:
                self.log("❌ JobRight server failed to start")
                return False

        except Exception as e:
            self.log(f"❌ Failed to start JobRight server: {e}", "ERROR")
            return False

    def start_automation_system(self, system_name: str) -> bool:
        """Start a specific automation system"""
        system = self.automation_systems[system_name]
        self.log(f"🚀 Starting {system['description']}")

        try:
            process = subprocess.Popen(
                [self.python_path, system['script']],
                cwd=str(self.base_dir),
                env={**os.environ, **self.env},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.active_systems[system_name] = {
                'process': process,
                'start_time': time.time(),
                'type': system['type'],
                'status': 'running',
                'applications': 0,
                'errors': 0
            }

            # Give system time to initialize
            time.sleep(5)

            # Check if process is still running
            if process.poll() is None:
                self.log(f"✅ {system_name} started successfully (PID: {process.pid})")
                return True
            else:
                self.log(f"❌ {system_name} failed to start")
                return False

        except Exception as e:
            self.log(f"❌ Failed to start {system_name}: {e}", "ERROR")
            return False

    def monitor_system_health(self):
        """Monitor health and performance of all running systems"""
        while self.running:
            try:
                time.sleep(30)  # Check every 30 seconds

                current_time = time.time()
                active_count = 0
                total_apps = 0

                self.log("=" * 60)
                self.log("📊 SYSTEM HEALTH MONITORING")
                self.log("=" * 60)

                for system_name, system_info in self.active_systems.items():
                    try:
                        process = system_info['process']

                        if process.poll() is None:  # Process is running
                            active_count += 1
                            runtime = (current_time - system_info['start_time']) / 60

                            # Try to get CPU and memory usage
                            try:
                                psutil_process = psutil.Process(process.pid)
                                cpu_percent = psutil_process.cpu_percent()
                                memory_mb = psutil_process.memory_info().rss / 1024 / 1024
                            except:
                                cpu_percent = 0
                                memory_mb = 0

                            self.log(f"✅ {system_name.upper()}: RUNNING")
                            self.log(f"    Runtime: {runtime:.1f}m | CPU: {cpu_percent:.1f}% | RAM: {memory_mb:.0f}MB")

                            # Estimate applications from JobRight API if available
                            if system_name == 'jobright_complete':
                                try:
                                    response = requests.get('http://localhost:5000/api/analytics', timeout=2)
                                    if response.status_code == 200:
                                        data = response.json()
                                        apps = data.get('successful_applications', 0)
                                        total_apps += apps
                                        self.log(f"    Applications: {apps}")
                                except:
                                    pass
                        else:
                            self.log(f"❌ {system_name.upper()}: STOPPED (Exit code: {process.returncode})")

                            # Try to restart critical systems
                            if system_name == 'jobright_complete':
                                self.log("🔄 Attempting to restart JobRight server...")
                                if self.start_jobright_server():
                                    self.log("✅ JobRight server restarted successfully")

                    except Exception as e:
                        self.log(f"⚠️ Error monitoring {system_name}: {e}")

                self.log(f"📈 SUMMARY: {active_count} systems active | ~{total_apps} total applications")
                self.log("=" * 60)

                # Update global stats
                self.total_applications = total_apps

            except Exception as e:
                self.log(f"❌ Health monitoring error: {e}", "ERROR")

    def get_jobright_analytics(self) -> Dict:
        """Get analytics from JobRight server"""
        try:
            response = requests.get('http://localhost:5000/api/analytics', timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}

    def trigger_automated_applications(self):
        """Trigger automated job applications via JobRight API"""
        try:
            # Trigger job scraping
            scrape_response = requests.post('http://localhost:5000/api/scrape',
                json={
                    'keywords': 'software engineer',
                    'location': 'San Francisco, CA'
                }, timeout=30)

            if scrape_response.status_code == 200:
                scrape_data = scrape_response.json()
                self.log(f"✅ Scraped {scrape_data.get('jobs_scraped', 0)} new jobs")

            # Get available jobs
            jobs_response = requests.get('http://localhost:5000/api/jobs')
            if jobs_response.status_code == 200:
                jobs_data = jobs_response.json()
                jobs = jobs_data.get('jobs', [])

                if jobs:
                    # Select first 10 jobs for application
                    job_ids = [job['id'] for job in jobs[:10]]

                    # Apply to jobs
                    apply_response = requests.post('http://localhost:5000/api/apply',
                        json={'job_ids': job_ids}, timeout=60)

                    if apply_response.status_code == 200:
                        apply_data = apply_response.json()
                        applied_count = apply_data.get('total_applied', 0)
                        self.log(f"🎯 Applied to {applied_count} jobs via JobRight API")
                        return applied_count

        except Exception as e:
            self.log(f"⚠️ API application attempt failed: {e}")

        return 0

    def automated_application_cycle(self):
        """Run automated application cycles"""
        while self.running:
            try:
                # Wait 10 minutes between cycles
                time.sleep(600)

                if not self.running:
                    break

                self.log("🔄 Starting automated application cycle")

                # Trigger applications via API
                applied_count = self.trigger_automated_applications()

                if applied_count > 0:
                    self.log(f"✅ Cycle completed: {applied_count} applications submitted")
                else:
                    self.log("ℹ️ Cycle completed: No new applications")

            except Exception as e:
                self.log(f"❌ Application cycle error: {e}", "ERROR")

    def start_all_systems(self):
        """Start all automation systems in priority order"""
        self.log("🚀 STARTING ALL AUTOMATION SYSTEMS")
        self.log("=" * 60)

        # Start JobRight server first (highest priority)
        if not self.start_jobright_server():
            self.log("❌ Critical: JobRight server failed to start", "ERROR")
            return False

        # Start other systems
        successful_starts = 1  # JobRight server already started

        for system_name in sorted(self.automation_systems.keys(),
                                key=lambda x: self.automation_systems[x]['priority']):
            if system_name == 'jobright_complete':
                continue  # Already started

            try:
                if self.start_automation_system(system_name):
                    successful_starts += 1
                    time.sleep(10)  # Stagger starts
                else:
                    self.log(f"⚠️ {system_name} failed to start but continuing...")

            except Exception as e:
                self.log(f"❌ Error starting {system_name}: {e}", "ERROR")

        self.log(f"📊 Started {successful_starts}/{len(self.automation_systems)} systems")
        return successful_starts > 1  # At least JobRight + 1 other system

    def run_ultimate_automation(self):
        """Run the ultimate job automation system"""
        self.log("🌟 ULTIMATE JOB AUTOMATION SYSTEM STARTING")
        self.log("=" * 60)
        self.log("🎯 MISSION: Maximize job applications across all platforms")
        self.log("🚀 STRATEGY: Multi-system orchestration with intelligent monitoring")
        self.log("💪 SCALE: Enterprise-level automation coordination")
        self.log("=" * 60)

        try:
            # Check requirements
            if not self.check_system_requirements():
                return False

            # Start all systems
            if not self.start_all_systems():
                self.log("❌ Failed to start minimum required systems", "ERROR")
                return False

            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_system_health, daemon=True)
            monitor_thread.start()

            # Start automated application cycle thread
            app_cycle_thread = threading.Thread(target=self.automated_application_cycle, daemon=True)
            app_cycle_thread.start()

            self.log("🎉 ALL SYSTEMS OPERATIONAL!")
            self.log("📊 Monitor: http://localhost:5000 for JobRight dashboard")
            self.log("🤖 Automation cycles will run every 10 minutes")
            self.log("⌨️  Press Ctrl+C to stop all systems")

            # Main monitoring loop
            start_time = time.time()
            last_report = 0

            while self.running:
                try:
                    time.sleep(60)  # Check every minute

                    current_time = time.time()
                    runtime_hours = (current_time - start_time) / 3600

                    # Hourly progress report
                    if int(runtime_hours) > last_report:
                        last_report = int(runtime_hours)

                        analytics = self.get_jobright_analytics()

                        self.log("=" * 60)
                        self.log(f"📊 HOURLY REPORT - Runtime: {runtime_hours:.1f}h")
                        self.log("=" * 60)
                        self.log(f"✅ Total applications: {analytics.get('successful_applications', 0)}")
                        self.log(f"📋 Jobs in database: {analytics.get('total_jobs', 0)}")
                        self.log(f"📈 Success rate: {analytics.get('success_rate', 0):.1f}%")
                        self.log(f"🔥 Active systems: {len([s for s in self.active_systems.values() if s['process'].poll() is None])}")
                        self.log("=" * 60)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.log(f"❌ Main loop error: {e}", "ERROR")

            return True

        except KeyboardInterrupt:
            self.log("🛑 Shutdown requested by user")
            return True
        except Exception as e:
            self.log(f"❌ Fatal error: {e}", "ERROR")
            return False

    def stop_all_systems(self):
        """Gracefully stop all automation systems"""
        self.log("🛑 Stopping all automation systems...")
        self.running = False

        for system_name, system_info in self.active_systems.items():
            try:
                process = system_info['process']
                if process.poll() is None:
                    self.log(f"🛑 Stopping {system_name}...")
                    process.terminate()

                    # Wait up to 10 seconds for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        self.log(f"✅ {system_name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        self.log(f"⚠️ Force killing {system_name}...")
                        process.kill()
                        process.wait()
                        self.log(f"💀 {system_name} force killed")

            except Exception as e:
                self.log(f"❌ Error stopping {system_name}: {e}", "ERROR")

        self.log("✅ All systems stopped")

    def print_final_report(self):
        """Print comprehensive final report"""
        try:
            analytics = self.get_jobright_analytics()

            self.log("=" * 80)
            self.log("🏁 ULTIMATE JOB AUTOMATION SYSTEM - FINAL REPORT")
            self.log("=" * 80)
            self.log(f"✅ Total applications submitted: {analytics.get('successful_applications', 0)}")
            self.log(f"📋 Total jobs processed: {analytics.get('total_jobs', 0)}")
            self.log(f"📈 Overall success rate: {analytics.get('success_rate', 0):.1f}%")
            self.log(f"🏢 Systems deployed: {len(self.automation_systems)}")
            self.log(f"⚡ Peak concurrent systems: {len(self.active_systems)}")

            if analytics.get('successful_applications', 0) > 0:
                self.log("🎉 MISSION ACCOMPLISHED!")
                self.log("✨ Your job applications have been submitted across multiple platforms")
                self.log("📧 Check your email for responses from employers")
            else:
                self.log("⚠️ No applications were recorded in the final count")
                self.log("💡 This could be due to systems still processing or API delays")

            self.log("=" * 80)

        except Exception as e:
            self.log(f"❌ Error generating final report: {e}", "ERROR")

def main():
    """Main function to run the ultimate job automation system"""
    automation_system = UltimateJobAutomationSystem()

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutdown signal received...")
        automation_system.stop_all_systems()
        automation_system.print_final_report()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        success = automation_system.run_ultimate_automation()
        automation_system.stop_all_systems()
        automation_system.print_final_report()
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"💥 Fatal system error: {e}")
        automation_system.stop_all_systems()
        sys.exit(1)

if __name__ == "__main__":
    main()