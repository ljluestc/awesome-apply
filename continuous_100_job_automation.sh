#!/bin/bash

# CONTINUOUS 100 JOB APPLICATION AUTOMATION
# This script will run continuously until 100 job applications are completed with proof

LOG_FILE="/home/calelin/awesome-apply/continuous_automation.log"
PYTHON_PATH="/home/calelin/awesome-apply/venv/bin/python"
SCRIPT_PATH="/home/calelin/awesome-apply/ultimate_100_job_applicator_with_real_proof.py"

echo "🚀 STARTING CONTINUOUS 100 JOB APPLICATION AUTOMATION" | tee -a "$LOG_FILE"
echo "📅 Started at: $(date)" | tee -a "$LOG_FILE"
echo "🎯 Target: 100 job applications with proof" | tee -a "$LOG_FILE"
echo "=" | tee -a "$LOG_FILE"

# Function to check if target is reached
check_target_reached() {
    SUCCESS_COUNT=$(sqlite3 /home/calelin/awesome-apply/ULTIMATE_100_REAL_JOBS.db "SELECT COUNT(*) FROM applications WHERE status = 'successfully_applied';" 2>/dev/null || echo "0")
    return $SUCCESS_COUNT
}

# Function to run the automation
run_automation() {
    echo "🔄 Starting automation run at $(date)" | tee -a "$LOG_FILE"

    cd /home/calelin/awesome-apply

    timeout 3600s env PYTHONPATH=/home/calelin/awesome-apply/venv/lib/python3.13/site-packages:/home/calelin/awesome-apply "$PYTHON_PATH" "$SCRIPT_PATH" 2>&1 | tee -a "$LOG_FILE"

    local exit_code=$?
    echo "🏁 Automation run completed with exit code: $exit_code at $(date)" | tee -a "$LOG_FILE"

    return $exit_code
}

# Main continuous loop
ATTEMPT=1
MAX_ATTEMPTS=50

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "🔄 ATTEMPT #$ATTEMPT of $MAX_ATTEMPTS" | tee -a "$LOG_FILE"

    # Check if target already reached
    check_target_reached
    SUCCESS_COUNT=$?

    if [ $SUCCESS_COUNT -ge 100 ]; then
        echo "🎉 TARGET REACHED! $SUCCESS_COUNT applications completed!" | tee -a "$LOG_FILE"
        echo "🏆 MISSION ACCOMPLISHED at $(date)" | tee -a "$LOG_FILE"
        break
    fi

    echo "📊 Current progress: $SUCCESS_COUNT/100 applications" | tee -a "$LOG_FILE"

    # Run automation
    run_automation

    # Check progress after run
    check_target_reached
    NEW_SUCCESS_COUNT=$?

    echo "📈 Progress after attempt #$ATTEMPT: $NEW_SUCCESS_COUNT/100 applications" | tee -a "$LOG_FILE"

    if [ $NEW_SUCCESS_COUNT -ge 100 ]; then
        echo "🎉 TARGET REACHED! $NEW_SUCCESS_COUNT applications completed!" | tee -a "$LOG_FILE"
        echo "🏆 MISSION ACCOMPLISHED at $(date)" | tee -a "$LOG_FILE"
        break
    fi

    # Wait before next attempt (5 minutes)
    echo "⏸️ Waiting 5 minutes before next attempt..." | tee -a "$LOG_FILE"
    sleep 300

    ATTEMPT=$((ATTEMPT + 1))
done

# Final report
echo "=" | tee -a "$LOG_FILE"
echo "📊 FINAL AUTOMATION REPORT" | tee -a "$LOG_FILE"
echo "🏁 Completed at: $(date)" | tee -a "$LOG_FILE"

if command -v sqlite3 >/dev/null 2>&1; then
    FINAL_SUCCESS=$(sqlite3 /home/calelin/awesome-apply/ULTIMATE_100_REAL_JOBS.db "SELECT COUNT(*) FROM applications WHERE status = 'successfully_applied';" 2>/dev/null || echo "0")
    TOTAL_ATTEMPTS=$(sqlite3 /home/calelin/awesome-apply/ULTIMATE_100_REAL_JOBS.db "SELECT COUNT(*) FROM applications;" 2>/dev/null || echo "0")
    PROOF_COUNT=$(find /home/calelin/awesome-apply/ULTIMATE_100_REAL_PROOFS -name "*.png" 2>/dev/null | wc -l)

    echo "✅ Successful Applications: $FINAL_SUCCESS" | tee -a "$LOG_FILE"
    echo "🎲 Total Attempts: $TOTAL_ATTEMPTS" | tee -a "$LOG_FILE"
    echo "📸 Proof Screenshots: $PROOF_COUNT" | tee -a "$LOG_FILE"

    if [ $FINAL_SUCCESS -ge 100 ]; then
        echo "🏆 MISSION SUCCESSFUL!" | tee -a "$LOG_FILE"
        exit 0
    else
        echo "⚠️ Target not reached, but system completed $ATTEMPT attempts" | tee -a "$LOG_FILE"
        exit 1
    fi
else
    echo "📊 sqlite3 not available for final count" | tee -a "$LOG_FILE"
    exit 1
fi