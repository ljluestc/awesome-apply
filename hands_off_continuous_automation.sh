#!/bin/bash
# Ultimate Hands-Off Continuous 100+ Job Application System
# This script will run indefinitely and maintain 100+ job applications

set -e

# Configuration
SCRIPT_DIR="/home/calelin/awesome-apply"
PYTHON_ENV="$SCRIPT_DIR/venv/bin/python"
AUTOMATION_SCRIPT="$SCRIPT_DIR/ultimate_100_job_applicator.py"
DATABASE_FILE="$SCRIPT_DIR/ultimate_100_jobs.db"
LOG_FILE="/tmp/continuous_job_automation.log"
MIN_APPLICATIONS=100
CHECK_INTERVAL=1800  # 30 minutes
MAX_CYCLES=1000      # Maximum cycles before restart

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

# Function to get current application statistics
get_application_stats() {
    if [ -f "$DATABASE_FILE" ]; then
        local stats=$(sqlite3 "$DATABASE_FILE" "SELECT
            COUNT(*) as total,
            SUM(CASE WHEN application_status = 'applied' THEN 1 ELSE 0 END) as applied,
            SUM(CASE WHEN application_status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN application_status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM job_applications;" 2>/dev/null || echo "0|0|0|0")
        echo "$stats"
    else
        echo "0|0|0|0"
    fi
}

# Function to check if we need more applications
check_application_needs() {
    local stats=$(get_application_stats)
    local applied=$(echo "$stats" | cut -d'|' -f2)

    if [ "$applied" -lt "$MIN_APPLICATIONS" ]; then
        return 0  # Need more applications
    else
        return 1  # Have enough applications
    fi
}

# Function to run application cycle
run_application_cycle() {
    local cycle_number=$1

    print_info "🚀 Starting Application Cycle #$cycle_number"

    # Set environment variables
    export PYTHONPATH="$SCRIPT_DIR/venv/lib/python3.13/site-packages:$SCRIPT_DIR"

    # Run the automation script with timeout
    if timeout 3600s "$PYTHON_ENV" "$AUTOMATION_SCRIPT" >> "$LOG_FILE" 2>&1; then
        print_success "Application cycle #$cycle_number completed successfully"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            print_warning "Application cycle #$cycle_number timed out after 1 hour"
        else
            print_error "Application cycle #$cycle_number failed with exit code $exit_code"
        fi
        return $exit_code
    fi
}

# Function to display comprehensive status
display_status() {
    local cycle=$1
    local stats=$(get_application_stats)
    local total=$(echo "$stats" | cut -d'|' -f1)
    local applied=$(echo "$stats" | cut -d'|' -f2)
    local failed=$(echo "$stats" | cut -d'|' -f3)
    local pending=$(echo "$stats" | cut -d'|' -f4)

    local success_rate=0
    if [ $((applied + failed)) -gt 0 ]; then
        success_rate=$((applied * 100 / (applied + failed)))
    fi

    local status_icon="🎯"
    local status_text="TARGET ACHIEVED"
    if [ "$applied" -lt "$MIN_APPLICATIONS" ]; then
        status_icon="🔄"
        status_text="WORKING TO TARGET"
    fi

    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}                    ${PURPLE}🤖 HANDS-OFF CONTINUOUS AUTOMATION STATUS${NC}                   ${CYAN}║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}🎯 Target:${NC} $MIN_APPLICATIONS applications    ${CYAN}│${NC} ${GREEN}✅ Applied:${NC} $applied                     ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}📊 Total Jobs:${NC} $total              ${CYAN}│${NC} ${GREEN}🔄 Pending:${NC} $pending                   ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}❌ Failed:${NC} $failed                  ${CYAN}│${NC} ${GREEN}📈 Success Rate:${NC} $success_rate%            ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}🔄 Cycle:${NC} #$cycle                  ${CYAN}│${NC} ${GREEN}🏆 Status:${NC} $status_icon $status_text        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${YELLOW}💡 System running continuously • Next check in $(($CHECK_INTERVAL/60)) minutes${NC}            ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}\n"
}

# Function to cleanup old data
cleanup_database() {
    if [ -f "$DATABASE_FILE" ]; then
        print_info "🧹 Running database cleanup..."

        # Remove failed applications older than 3 days
        local three_days_ago=$(date -d '3 days ago' '+%Y-%m-%d %H:%M:%S')
        sqlite3 "$DATABASE_FILE" "DELETE FROM job_applications WHERE application_status IN ('failed', 'error') AND created_at < '$three_days_ago';" 2>/dev/null || true

        # Reset stuck pending applications
        local two_hours_ago=$(date -d '2 hours ago' '+%Y-%m-%d %H:%M:%S')
        sqlite3 "$DATABASE_FILE" "UPDATE job_applications SET application_status = 'pending', attempt_count = 0 WHERE application_status = 'pending' AND last_attempt < '$two_hours_ago' AND attempt_count > 0;" 2>/dev/null || true

        print_success "Database cleanup completed"
    fi
}

# Function to handle shutdown gracefully
shutdown_handler() {
    print_warning "🛑 Received shutdown signal, cleaning up..."

    # Kill any running Python processes
    pkill -f "ultimate_100_job_applicator.py" 2>/dev/null || true
    pkill -f "enhanced_100_job_automation.py" 2>/dev/null || true

    print_success "👋 Hands-off continuous automation stopped"
    exit 0
}

# Main execution function
main() {
    # Set up signal handlers
    trap shutdown_handler SIGINT SIGTERM

    # Initialize
    local cycle=0
    local start_time=$(date +%s)

    # Print startup banner
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}              ${GREEN}🤖 HANDS-OFF CONTINUOUS JOB AUTOMATION SYSTEM${NC}                   ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}                                                                              ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  ${GREEN}🎯 Maintains exactly $MIN_APPLICATIONS+ job applications continuously${NC}                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  ${GREEN}⚡ Runs indefinitely with automatic maintenance every $(($CHECK_INTERVAL/60)) minutes${NC}           ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  ${GREEN}🔧 Completely hands-off operation${NC}                                        ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  ${GREEN}📊 Automatic cleanup and optimization${NC}                                   ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  ${GREEN}🛡️  Robust error handling and recovery${NC}                                  ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}                                                                              ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}                      ${YELLOW}🚀 SYSTEM STARTING...${NC}                                  ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

    print_status "🚀 Hands-Off Continuous Job Automation System Started"
    print_info "📂 Working Directory: $SCRIPT_DIR"
    print_info "🐍 Python Environment: $PYTHON_ENV"
    print_info "📊 Database: $DATABASE_FILE"
    print_info "📝 Log File: $LOG_FILE"
    print_info "🎯 Target Applications: $MIN_APPLICATIONS"
    print_info "⏰ Check Interval: $(($CHECK_INTERVAL/60)) minutes"

    # Initial status check
    display_status 0

    # Main continuous loop
    while true; do
        cycle=$((cycle + 1))

        print_info "🔍 Cycle #$cycle: Checking application status..."

        if check_application_needs; then
            local current_stats=$(get_application_stats)
            local current_applied=$(echo "$current_stats" | cut -d'|' -f2)
            local needed=$((MIN_APPLICATIONS - current_applied))

            print_warning "🎯 Need $needed more applications to reach target of $MIN_APPLICATIONS"

            # Run application cycle
            if run_application_cycle $cycle; then
                print_success "✅ Application cycle #$cycle completed successfully"
            else
                print_error "❌ Application cycle #$cycle failed, will retry next cycle"
            fi

            # Show updated status
            display_status $cycle
        else
            local current_stats=$(get_application_stats)
            local current_applied=$(echo "$current_stats" | cut -d'|' -f2)
            print_success "🎉 Target maintained! Currently have $current_applied applications (Target: $MIN_APPLICATIONS)"
            display_status $cycle
        fi

        # Periodic cleanup (every 12 hours)
        if [ $((cycle % 24)) -eq 0 ]; then
            cleanup_database
        fi

        # Calculate uptime
        local current_time=$(date +%s)
        local uptime_hours=$(((current_time - start_time) / 3600))
        print_info "⏱️  System uptime: $uptime_hours hours, completed $cycle cycles"

        # Break if max cycles reached (safety mechanism)
        if [ $cycle -ge $MAX_CYCLES ]; then
            print_warning "🔄 Maximum cycles reached ($MAX_CYCLES), restarting system..."
            break
        fi

        # Wait before next check
        print_info "💤 Waiting $(($CHECK_INTERVAL/60)) minutes before next check..."
        sleep $CHECK_INTERVAL
    done

    # Restart the system if we exit the loop
    print_info "🔄 Restarting continuous automation system..."
    exec "$0"
}

# Check prerequisites
check_prerequisites() {
    if [ ! -f "$PYTHON_ENV" ]; then
        print_error "Python environment not found: $PYTHON_ENV"
        exit 1
    fi

    if [ ! -f "$AUTOMATION_SCRIPT" ]; then
        print_error "Automation script not found: $AUTOMATION_SCRIPT"
        exit 1
    fi

    # Check if required commands exist
    for cmd in sqlite3 timeout; do
        if ! command -v $cmd &> /dev/null; then
            print_error "Required command not found: $cmd"
            exit 1
        fi
    done

    # Create log file if it doesn't exist
    touch "$LOG_FILE"

    print_success "✅ Prerequisites check passed"
}

# Create systemd service
create_systemd_service() {
    local service_file="continuous-job-automation.service"
    local current_user=$(whoami)

    cat > "$service_file" << EOF
[Unit]
Description=Continuous 100+ Job Application Automation
After=network.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=60
User=$current_user
Group=$current_user
WorkingDirectory=$SCRIPT_DIR
Environment=HOME=$HOME
Environment=DISPLAY=:0
ExecStart=$SCRIPT_DIR/hands_off_continuous_automation.sh
StandardOutput=journal
StandardError=journal
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF

    print_success "📝 Created systemd service file: $service_file"
    print_info "🔧 To install as system service:"
    print_info "   sudo cp $service_file /etc/systemd/system/"
    print_info "   sudo systemctl daemon-reload"
    print_info "   sudo systemctl enable continuous-job-automation.service"
    print_info "   sudo systemctl start continuous-job-automation.service"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --service     Create systemd service file"
    echo "  --status      Show current application status"
    echo "  --cleanup     Run database cleanup"
    echo "  --help        Show this help message"
    echo ""
    echo "Run without options to start continuous automation"
}

# Handle command line arguments
case "${1:-}" in
    --service)
        create_systemd_service
        exit 0
        ;;
    --status)
        if [ -f "$DATABASE_FILE" ]; then
            stats=$(get_application_stats)
            echo "Current Application Status:"
            echo "  Total Jobs: $(echo "$stats" | cut -d'|' -f1)"
            echo "  Applied: $(echo "$stats" | cut -d'|' -f2)"
            echo "  Failed: $(echo "$stats" | cut -d'|' -f3)"
            echo "  Pending: $(echo "$stats" | cut -d'|' -f4)"
        else
            echo "No database found. Run automation first."
        fi
        exit 0
        ;;
    --cleanup)
        cleanup_database
        exit 0
        ;;
    --help)
        show_usage
        exit 0
        ;;
    --*)
        echo "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac

# Main execution
check_prerequisites
main