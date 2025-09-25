#!/usr/bin/env python3
"""
Enhanced Web Interface for Comprehensive Job Automation System
Provides a polished UI for job scraping, automation pattern management, and batch applications
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from comprehensive_job_automation_system import ComprehensiveAutomationSystem
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Global system instance
automation_system = None
background_tasks = {}

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('comprehensive_jobs.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    """Enhanced dashboard with comprehensive metrics"""
    try:
        conn = get_db_connection()

        # Job statistics
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs_comprehensive").fetchone()[0]
        pending_jobs = conn.execute("SELECT COUNT(*) FROM jobs_comprehensive WHERE application_status = 'pending'").fetchone()[0]
        applied_jobs = conn.execute("SELECT COUNT(*) FROM jobs_comprehensive WHERE application_status = 'applied'").fetchone()[0]
        failed_jobs = conn.execute("SELECT COUNT(*) FROM jobs_comprehensive WHERE application_status = 'failed'").fetchone()[0]

        # Source distribution
        sources = conn.execute("""
            SELECT source, COUNT(*) as count
            FROM jobs_comprehensive
            GROUP BY source
            ORDER BY count DESC
        """).fetchall()

        # Recent jobs
        recent_jobs = conn.execute("""
            SELECT * FROM jobs_comprehensive
            ORDER BY created_at DESC
            LIMIT 10
        """).fetchall()

        # Automation patterns
        pattern_count = conn.execute("SELECT COUNT(*) FROM automation_patterns").fetchone()[0]
        top_patterns = conn.execute("""
            SELECT domain, site_name, usage_count, success_rate
            FROM automation_patterns
            ORDER BY usage_count DESC
            LIMIT 5
        """).fetchall()

        # Application success rate over time
        success_rate_data = conn.execute("""
            SELECT
                DATE(created_at) as date,
                SUM(CASE WHEN application_status = 'applied' THEN 1 ELSE 0 END) as successful,
                COUNT(*) as total
            FROM jobs_comprehensive
            WHERE application_status IN ('applied', 'failed')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        """).fetchall()

        conn.close()

        stats = {
            'total_jobs': total_jobs,
            'pending_jobs': pending_jobs,
            'applied_jobs': applied_jobs,
            'failed_jobs': failed_jobs,
            'pattern_count': pattern_count
        }

        return render_template('enhanced_dashboard.html',
                             stats=stats,
                             sources=sources,
                             recent_jobs=recent_jobs,
                             top_patterns=top_patterns,
                             success_rate_data=success_rate_data)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', error=str(e))

@app.route('/jobs')
def job_list():
    """Enhanced job listing with filters"""
    try:
        conn = get_db_connection()

        # Get filter parameters
        company = request.args.get('company', '')
        location = request.args.get('location', '')
        source = request.args.get('source', '')
        status = request.args.get('status', '')
        min_confidence = request.args.get('min_confidence', 0, type=float)
        page = request.args.get('page', 1, type=int)
        per_page = 20

        # Build query with filters
        where_conditions = []
        params = []

        if company:
            where_conditions.append("company LIKE ?")
            params.append(f"%{company}%")

        if location:
            where_conditions.append("location LIKE ?")
            params.append(f"%{location}%")

        if source:
            where_conditions.append("source = ?")
            params.append(source)

        if status:
            where_conditions.append("application_status = ?")
            params.append(status)

        if min_confidence > 0:
            where_conditions.append("automation_confidence >= ?")
            params.append(min_confidence)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Count total results
        count_query = f"SELECT COUNT(*) FROM jobs_comprehensive {where_clause}"
        total_jobs = conn.execute(count_query, params).fetchone()[0]

        # Get paginated results
        offset = (page - 1) * per_page
        query = f"""
            SELECT * FROM jobs_comprehensive
            {where_clause}
            ORDER BY automation_confidence DESC, match_score DESC
            LIMIT ? OFFSET ?
        """

        jobs = conn.execute(query, params + [per_page, offset]).fetchall()

        # Get filter options
        companies = conn.execute("SELECT DISTINCT company FROM jobs_comprehensive ORDER BY company").fetchall()
        sources_list = conn.execute("SELECT DISTINCT source FROM jobs_comprehensive ORDER BY source").fetchall()

        conn.close()

        # Pagination info
        total_pages = (total_jobs + per_page - 1) // per_page

        return render_template('enhanced_jobs.html',
                             jobs=jobs,
                             companies=companies,
                             sources=sources_list,
                             current_page=page,
                             total_pages=total_pages,
                             total_jobs=total_jobs,
                             filters={
                                 'company': company,
                                 'location': location,
                                 'source': source,
                                 'status': status,
                                 'min_confidence': min_confidence
                             })

    except Exception as e:
        logger.error(f"Job list error: {e}")
        return render_template('error.html', error=str(e))

@app.route('/scrape-jobs', methods=['POST'])
def scrape_jobs():
    """Start job scraping process"""
    try:
        target_jobs = request.form.get('target_jobs', 1000, type=int)

        # Start background scraping task
        task_id = f"scrape_{datetime.now().timestamp()}"
        thread = threading.Thread(target=run_scraping_task, args=(task_id, target_jobs))
        thread.daemon = True
        thread.start()

        background_tasks[task_id] = {
            'status': 'running',
            'started_at': datetime.now(),
            'target_jobs': target_jobs,
            'progress': 0
        }

        flash(f'Job scraping started! Target: {target_jobs} jobs', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        logger.error(f"Scraping start error: {e}")
        flash(f'Failed to start scraping: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/batch-apply', methods=['POST'])
def batch_apply():
    """Start batch application process"""
    try:
        target_applications = request.form.get('target_applications', 50, type=int)
        time_limit = request.form.get('time_limit', 1, type=int)
        min_confidence = request.form.get('min_confidence', 0.7, type=float)

        # Start background application task
        task_id = f"apply_{datetime.now().timestamp()}"
        thread = threading.Thread(target=run_application_task,
                                args=(task_id, target_applications, time_limit, min_confidence))
        thread.daemon = True
        thread.start()

        background_tasks[task_id] = {
            'status': 'running',
            'started_at': datetime.now(),
            'target_applications': target_applications,
            'progress': 0
        }

        flash(f'Batch applications started! Target: {target_applications} applications', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        logger.error(f"Batch apply start error: {e}")
        flash(f'Failed to start batch applications: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/task-status/<task_id>')
def task_status(task_id):
    """Get status of background task"""
    if task_id in background_tasks:
        return jsonify(background_tasks[task_id])
    else:
        return jsonify({'status': 'not_found'}), 404

@app.route('/automation-patterns')
def automation_patterns():
    """View and manage automation patterns"""
    try:
        conn = get_db_connection()

        patterns = conn.execute("""
            SELECT * FROM automation_patterns
            ORDER BY confidence_score DESC, usage_count DESC
        """).fetchall()

        # Pattern statistics
        pattern_stats = {
            'total_patterns': len(patterns),
            'avg_confidence': sum(p['confidence_score'] for p in patterns) / len(patterns) if patterns else 0,
            'avg_success_rate': sum(p['success_rate'] for p in patterns) / len(patterns) if patterns else 0,
            'total_usage': sum(p['usage_count'] for p in patterns)
        }

        conn.close()

        return render_template('automation_patterns.html',
                             patterns=patterns,
                             pattern_stats=pattern_stats)

    except Exception as e:
        logger.error(f"Automation patterns error: {e}")
        return render_template('error.html', error=str(e))

@app.route('/settings')
def settings():
    """Application settings and configuration"""
    try:
        # Load current settings (this would normally come from a config file)
        current_settings = {
            'user_profile': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@email.com',
                'phone': '555-0123',
                'linkedin_url': 'https://linkedin.com/in/johndoe',
                'github_url': 'https://github.com/johndoe',
                'website_url': 'https://johndoe.dev'
            },
            'automation_settings': {
                'min_confidence_threshold': 0.7,
                'max_applications_per_hour': 100,
                'delay_between_applications': 3,
                'enable_sso': True,
                'preferred_sso_providers': ['google', 'linkedin']
            },
            'scraping_settings': {
                'max_jobs_per_source': 500,
                'update_frequency_hours': 6,
                'enabled_sources': ['remoteok', 'github', 'ycombinator']
            }
        }

        return render_template('settings.html', settings=current_settings)

    except Exception as e:
        logger.error(f"Settings error: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        conn = get_db_connection()

        stats = {}

        # Job counts by status
        status_counts = conn.execute("""
            SELECT application_status, COUNT(*) as count
            FROM jobs_comprehensive
            GROUP BY application_status
        """).fetchall()

        stats['status_distribution'] = {row['application_status']: row['count'] for row in status_counts}

        # Jobs by source
        source_counts = conn.execute("""
            SELECT source, COUNT(*) as count
            FROM jobs_comprehensive
            GROUP BY source
        """).fetchall()

        stats['source_distribution'] = {row['source']: row['count'] for row in source_counts}

        # Automation confidence distribution
        confidence_ranges = conn.execute("""
            SELECT
                CASE
                    WHEN automation_confidence >= 0.9 THEN 'Very High (0.9+)'
                    WHEN automation_confidence >= 0.7 THEN 'High (0.7-0.9)'
                    WHEN automation_confidence >= 0.5 THEN 'Medium (0.5-0.7)'
                    ELSE 'Low (<0.5)'
                END as confidence_range,
                COUNT(*) as count
            FROM jobs_comprehensive
            GROUP BY confidence_range
        """).fetchall()

        stats['confidence_distribution'] = {row['confidence_range']: row['count'] for row in confidence_ranges}

        conn.close()

        return jsonify(stats)

    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({'error': str(e)}), 500

def run_scraping_task(task_id, target_jobs):
    """Background task for job scraping"""
    try:
        global automation_system
        if not automation_system:
            automation_system = ComprehensiveAutomationSystem()

        # Update task status
        background_tasks[task_id]['status'] = 'scraping'

        # Run scraping (synchronous call in thread)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        results = loop.run_until_complete(
            automation_system.scraper.scrape_all_jobs(limit=target_jobs)
        )

        # Save results
        saved_count = automation_system.storage.save_jobs(results)

        # Update task status
        background_tasks[task_id].update({
            'status': 'completed',
            'completed_at': datetime.now(),
            'jobs_found': len(results),
            'jobs_saved': saved_count,
            'progress': 100
        })

        loop.close()

    except Exception as e:
        logger.error(f"Scraping task {task_id} failed: {e}")
        background_tasks[task_id].update({
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now()
        })

def run_application_task(task_id, target_applications, time_limit, min_confidence):
    """Background task for batch applications"""
    try:
        global automation_system
        if not automation_system:
            automation_system = ComprehensiveAutomationSystem()

        # Update task status
        background_tasks[task_id]['status'] = 'applying'

        # Run applications (synchronous call in thread)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        results = loop.run_until_complete(
            automation_system.batch_system.run_batch_applications(
                target_applications=target_applications,
                time_limit_hours=time_limit
            )
        )

        # Update task status
        background_tasks[task_id].update({
            'status': 'completed',
            'completed_at': datetime.now(),
            'results': results,
            'progress': 100
        })

        loop.close()

    except Exception as e:
        logger.error(f"Application task {task_id} failed: {e}")
        background_tasks[task_id].update({
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now()
        })

# Enhanced HTML Templates (inline for simplicity)
def create_templates():
    """Create enhanced HTML templates"""
    import os

    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)

    # Enhanced Dashboard Template
    with open('templates/enhanced_dashboard.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Automation Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50">
    <nav class="bg-blue-600 text-white p-4">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">Job Automation System</h1>
            <div class="flex space-x-4">
                <a href="/" class="hover:bg-blue-700 px-3 py-2 rounded">Dashboard</a>
                <a href="/jobs" class="hover:bg-blue-700 px-3 py-2 rounded">Jobs</a>
                <a href="/automation-patterns" class="hover:bg-blue-700 px-3 py-2 rounded">Patterns</a>
                <a href="/settings" class="hover:bg-blue-700 px-3 py-2 rounded">Settings</a>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto p-6">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-100 text-red-700{% else %}bg-green-100 text-green-700{% endif %}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- Key Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <div class="flex items-center">
                    <div class="p-3 bg-blue-100 rounded-full">
                        <i class="fas fa-briefcase text-blue-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-sm font-medium text-gray-500">Total Jobs</h3>
                        <p class="text-2xl font-semibold text-gray-900">{{ stats.total_jobs }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <div class="flex items-center">
                    <div class="p-3 bg-yellow-100 rounded-full">
                        <i class="fas fa-clock text-yellow-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-sm font-medium text-gray-500">Pending</h3>
                        <p class="text-2xl font-semibold text-gray-900">{{ stats.pending_jobs }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <div class="flex items-center">
                    <div class="p-3 bg-green-100 rounded-full">
                        <i class="fas fa-check-circle text-green-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-sm font-medium text-gray-500">Applied</h3>
                        <p class="text-2xl font-semibold text-gray-900">{{ stats.applied_jobs }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <div class="flex items-center">
                    <div class="p-3 bg-purple-100 rounded-full">
                        <i class="fas fa-robot text-purple-600 text-xl"></i>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-sm font-medium text-gray-500">Patterns</h3>
                        <p class="text-2xl font-semibold text-gray-900">{{ stats.pattern_count }}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <h3 class="text-lg font-semibold mb-4">Scrape New Jobs</h3>
                <form method="POST" action="/scrape-jobs" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Target Jobs</label>
                        <input type="number" name="target_jobs" value="1000" min="10" max="5000"
                               class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                    </div>
                    <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-200">
                        <i class="fas fa-download mr-2"></i>Start Scraping
                    </button>
                </form>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <h3 class="text-lg font-semibold mb-4">Batch Apply</h3>
                <form method="POST" action="/batch-apply" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Target Applications</label>
                        <input type="number" name="target_applications" value="50" min="1" max="200"
                               class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Time Limit (hours)</label>
                        <input type="number" name="time_limit" value="1" min="0.1" max="24" step="0.1"
                               class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Min Confidence</label>
                        <input type="number" name="min_confidence" value="0.7" min="0" max="1" step="0.1"
                               class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                    </div>
                    <button type="submit" class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-200">
                        <i class="fas fa-rocket mr-2"></i>Start Applications
                    </button>
                </form>
            </div>
        </div>

        <!-- Charts and Data -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <h3 class="text-lg font-semibold mb-4">Job Sources</h3>
                <canvas id="sourceChart" width="400" height="200"></canvas>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm border">
                <h3 class="text-lg font-semibold mb-4">Recent Jobs</h3>
                <div class="space-y-3 max-h-64 overflow-y-auto">
                    {% for job in recent_jobs %}
                    <div class="flex justify-between items-start p-3 bg-gray-50 rounded-lg">
                        <div>
                            <h4 class="font-medium text-gray-900">{{ job.title }}</h4>
                            <p class="text-sm text-gray-600">{{ job.company }} • {{ job.location }}</p>
                            <p class="text-xs text-gray-500">{{ job.source }} • Confidence: {{ "%.1f"|format(job.automation_confidence or 0) }}</p>
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full
                            {% if job.application_status == 'pending' %}bg-yellow-100 text-yellow-800{% endif %}
                            {% if job.application_status == 'applied' %}bg-green-100 text-green-800{% endif %}
                            {% if job.application_status == 'failed' %}bg-red-100 text-red-800{% endif %}">
                            {{ job.application_status }}
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <script>
        // Source distribution chart
        const sourceCtx = document.getElementById('sourceChart').getContext('2d');
        const sourceChart = new Chart(sourceCtx, {
            type: 'doughnut',
            data: {
                labels: [{% for source in sources %}'{{ source.source }}'{% if not loop.last %},{% endif %}{% endfor %}],
                datasets: [{
                    data: [{% for source in sources %}{{ source.count }}{% if not loop.last %},{% endif %}{% endfor %}],
                    backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    </script>
</body>
</html>
        """)

if __name__ == "__main__":
    # Create templates
    create_templates()

    # Initialize the system
    logger.info("🚀 Starting enhanced web interface...")

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)