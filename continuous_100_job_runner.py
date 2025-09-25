#!/usr/bin/env python3
"""
Continuous 100-Job Runner
Runs the job application system continuously until exactly 100 jobs are applied to
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

import asyncio
import sqlite3
import json
import time
from datetime import datetime, timedelta
import logging
from ultimate_100_job_applicator import Ultimate100JobApplicator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Continuous100Runner:
    """Continuous runner to ensure 100 job applications are completed"""

    def __init__(self):
        self.target_applications = 100
        self.max_runtime_hours = 2  # Maximum 2 hours
        self.check_interval = 60  # Check progress every 60 seconds
        self.db_path = 'ultimate_100_jobs.db'

    def get_current_stats(self) -> dict:
        """Get current application statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN application_status = 'applied' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN application_status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN application_status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN application_status = 'error' THEN 1 ELSE 0 END) as errors
                FROM job_applications
            """)

            result = cursor.fetchone()
            conn.close()

            return {
                'total_jobs': result[0] or 0,
                'successful': result[1] or 0,
                'failed': result[2] or 0,
                'pending': result[3] or 0,
                'errors': result[4] or 0
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'total_jobs': 0, 'successful': 0, 'failed': 0, 'pending': 0, 'errors': 0}

    async def run_until_100_complete(self):
        """Run the application system until 100 jobs are applied"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=self.max_runtime_hours)

        logger.info("🚀 Starting Continuous 100-Job Application Runner")
        logger.info(f"⏰ Maximum runtime: {self.max_runtime_hours} hours")
        logger.info(f"🎯 Target: {self.target_applications} successful applications")

        cycle_count = 0
        total_successful = 0

        while datetime.now() < end_time and total_successful < self.target_applications:
            cycle_count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 CYCLE #{cycle_count} - Starting new application run")
            logger.info(f"{'='*60}")

            try:
                # Run the application system
                applicator = Ultimate100JobApplicator()
                results = await applicator.run_100_job_application_cycle()

                # Get updated stats
                current_stats = self.get_current_stats()
                total_successful = current_stats['successful']

                # Log progress
                logger.info(f"📊 CYCLE #{cycle_count} COMPLETE")
                logger.info(f"✅ Total successful applications: {total_successful}/{self.target_applications}")
                logger.info(f"📈 Progress: {(total_successful/self.target_applications*100):.1f}%")

                if total_successful >= self.target_applications:
                    logger.info(f"🎉 TARGET ACHIEVED! Successfully applied to {total_successful} jobs!")
                    break

                # If we haven't reached the target, prepare for next cycle
                remaining = self.target_applications - total_successful
                logger.info(f"🔄 {remaining} more applications needed. Starting next cycle...")

                # Brief pause between cycles
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"❌ Cycle #{cycle_count} failed: {e}")
                await asyncio.sleep(10)  # Wait before retry
                continue

        # Final summary
        end_time_actual = datetime.now()
        total_duration = (end_time_actual - start_time).total_seconds()
        final_stats = self.get_current_stats()

        summary = {
            'mission_complete': final_stats['successful'] >= self.target_applications,
            'total_cycles': cycle_count,
            'duration_hours': total_duration / 3600,
            'final_statistics': final_stats,
            'applications_per_hour': final_stats['successful'] * 3600 / total_duration if total_duration > 0 else 0,
            'success_rate': final_stats['successful'] / max(1, final_stats['total_jobs'] - final_stats['pending']) * 100
        }

        self.print_final_report(summary)
        return summary

    def print_final_report(self, summary: dict):
        """Print comprehensive final report"""
        stats = summary['final_statistics']

        print(f"\n{'='*80}")
        print("🏆 FINAL MISSION REPORT - 100 JOB APPLICATION CHALLENGE")
        print(f"{'='*80}")

        print(f"🎯 MISSION STATUS: {'✅ COMPLETE' if summary['mission_complete'] else '⚠️ INCOMPLETE'}")
        print(f"⏱️  Total Duration: {summary['duration_hours']:.2f} hours")
        print(f"🔄 Application Cycles: {summary['total_cycles']}")

        print(f"\n📊 FINAL STATISTICS:")
        print(f"• Total Jobs in Database: {stats['total_jobs']}")
        print(f"• ✅ Successful Applications: {stats['successful']}")
        print(f"• ❌ Failed Applications: {stats['failed']}")
        print(f"• ⚠️  Error Applications: {stats['errors']}")
        print(f"• 🔄 Pending Applications: {stats['pending']}")

        print(f"\n🏆 PERFORMANCE METRICS:")
        print(f"• Success Rate: {summary['success_rate']:.1f}%")
        print(f"• Applications/Hour: {summary['applications_per_hour']:.1f}")
        print(f"• Target Achievement: {(stats['successful']/100*100):.1f}%")

        if summary['mission_complete']:
            print(f"\n🎉 CONGRATULATIONS!")
            print(f"🏆 Mission accomplished! You have successfully applied to {stats['successful']} jobs!")
            print(f"💪 This is a remarkable achievement in job application automation!")
        else:
            print(f"\n📈 PROGRESS UPDATE:")
            print(f"🔄 Applied to {stats['successful']} jobs so far")
            print(f"🎯 {100 - stats['successful']} more applications needed to reach target")
            print(f"💡 System can continue running to complete the mission")

        print(f"{'='*80}\n")

async def main():
    """Main execution function"""
    runner = Continuous100Runner()

    try:
        summary = await runner.run_until_100_complete()

        if summary['mission_complete']:
            print("🏆 SUCCESS: 100+ job applications completed!")
            return 0
        else:
            print("⚠️ Target not fully reached, but significant progress made")
            return 1

    except Exception as e:
        logger.error(f"Fatal error in continuous runner: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)