#!/bin/bash
# LinkedIn Job Automation Runner
# Searches for software jobs within 25 miles of San Jose and applies automatically

echo "🔗 LINKEDIN JOB AUTOMATION"
echo "Searching for software jobs in San Jose area (25 mile radius)"
echo "=========================================="

# Activate virtual environment and run the automation
source venv/bin/activate
python linkedin_job_automation.py

echo "Automation completed. Check the generated log files for results."