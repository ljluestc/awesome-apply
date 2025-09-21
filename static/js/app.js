// JobRight.ai Clone - Frontend JavaScript
class JobRightApp {
    constructor() {
        this.jobs = [];
        this.filteredJobs = [];
        this.currentPage = 1;
        this.jobsPerPage = 12;
        this.searchCriteria = null;
        this.selectedJob = null;

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSavedJobs();
        this.loadAnalytics();
    }

    bindEvents() {
        // Search form submission
        document.getElementById('job-search-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSearch();
        });

        // Modal events
        document.getElementById('job-modal').addEventListener('click', (e) => {
            if (e.target.id === 'job-modal') {
                this.closeModal();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    async handleSearch() {
        const formData = new FormData(document.getElementById('job-search-form'));

        const criteria = {
            keywords: formData.get('keywords').split(',').map(k => k.trim()),
            location: formData.get('location'),
            experience_level: formData.get('experience_level'),
            job_type: formData.get('job_type'),
            date_posted: formData.get('date_posted'),
            remote_ok: formData.get('remote_ok') === 'on'
        };

        this.searchCriteria = criteria;
        this.showLoading('Searching for jobs...');

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(criteria)
            });

            const result = await response.json();

            if (result.success) {
                this.jobs = result.jobs;
                this.filteredJobs = [...this.jobs];
                this.displayJobs();
                this.showNotification('success', `Found ${result.count} jobs!`);

                // Show results section
                document.getElementById('results-section').style.display = 'block';
                document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
            } else {
                this.showNotification('error', result.error || 'Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showNotification('error', 'Search failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async loadSavedJobs() {
        try {
            const response = await fetch('/api/jobs');
            const result = await response.json();

            if (result.success) {
                this.jobs = result.jobs;
                this.filteredJobs = [...this.jobs];

                if (this.jobs.length > 0) {
                    this.displayJobs();
                    document.getElementById('results-section').style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Error loading saved jobs:', error);
        }
    }

    displayJobs() {
        const jobsGrid = document.getElementById('jobs-grid');
        const startIndex = (this.currentPage - 1) * this.jobsPerPage;
        const endIndex = startIndex + this.jobsPerPage;
        const jobsToShow = this.filteredJobs.slice(startIndex, endIndex);

        // Update results count
        document.getElementById('results-count').textContent = `${this.filteredJobs.length} jobs found`;

        // Update applied/pending counts
        const appliedCount = this.filteredJobs.filter(job => job.application_status === 'applied').length;
        const pendingCount = this.filteredJobs.filter(job => job.application_status === 'pending').length;

        document.getElementById('applied-count').textContent = appliedCount;
        document.getElementById('pending-count').textContent = pendingCount;

        // Enable/disable bulk apply button
        const bulkApplyBtn = document.getElementById('bulk-apply-btn');
        const notAppliedJobs = this.filteredJobs.filter(job => job.application_status === 'not_applied');
        bulkApplyBtn.disabled = notAppliedJobs.length === 0;

        // Clear and populate jobs grid
        jobsGrid.innerHTML = '';

        jobsToShow.forEach(job => {
            const jobCard = this.createJobCard(job);
            jobsGrid.appendChild(jobCard);
        });

        // Update load more button
        const loadMoreBtn = document.getElementById('load-more-btn');
        loadMoreBtn.style.display = endIndex >= this.filteredJobs.length ? 'none' : 'block';
    }

    createJobCard(job) {
        const card = document.createElement('div');
        card.className = 'job-card';
        card.onclick = () => this.showJobDetail(job);

        const statusClass = `status-${job.application_status.replace('_', '-')}`;
        const statusText = job.application_status.replace('_', ' ').toUpperCase();

        card.innerHTML = `
            <div class="job-card-header">
                <div class="job-info">
                    <h3 class="job-title">${this.escapeHtml(job.title)}</h3>
                    <div class="job-company">${this.escapeHtml(job.company)}</div>
                </div>
                <span class="job-status ${statusClass}">${statusText}</span>
            </div>

            <div class="job-details">
                ${job.location ? `
                    <div class="job-location">
                        <i class="fas fa-map-marker-alt"></i>
                        ${this.escapeHtml(job.location)}
                    </div>
                ` : ''}
                ${job.salary ? `
                    <div class="job-salary">
                        <i class="fas fa-dollar-sign"></i>
                        ${this.escapeHtml(job.salary)}
                    </div>
                ` : ''}
            </div>

            <div class="job-description">
                ${this.escapeHtml(job.description.substring(0, 150))}${job.description.length > 150 ? '...' : ''}
            </div>

            ${job.tags && job.tags.length > 0 ? `
                <div class="job-tags">
                    ${job.tags.slice(0, 3).map(tag => `<span class="job-tag">${this.escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}

            <div class="job-actions">
                <span class="job-posted">${this.formatDate(job.posted_date)}</span>
                <button class="btn btn-primary job-apply-btn" onclick="event.stopPropagation(); applyToJobFromCard('${job.id}')">
                    <i class="fas fa-paper-plane"></i>
                    ${job.application_status === 'applied' ? 'Applied' : 'Auto Apply'}
                </button>
            </div>
        `;

        return card;
    }

    showJobDetail(job) {
        this.selectedJob = job;

        document.getElementById('modal-job-title').textContent = job.title;
        document.getElementById('modal-company').textContent = job.company;
        document.getElementById('modal-location').textContent = job.location || 'Location not specified';
        document.getElementById('modal-salary').textContent = job.salary || 'Salary not disclosed';
        document.getElementById('modal-description').textContent = job.description || 'No description available';

        // Update apply button
        const applyBtn = document.getElementById('apply-btn');
        if (job.application_status === 'applied') {
            applyBtn.innerHTML = '<i class="fas fa-check"></i> Applied';
            applyBtn.className = 'btn btn-success';
            applyBtn.disabled = true;
        } else {
            applyBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Auto Apply';
            applyBtn.className = 'btn btn-primary';
            applyBtn.disabled = false;
        }

        document.getElementById('job-modal').style.display = 'flex';
    }

    closeModal() {
        document.getElementById('job-modal').style.display = 'none';
        this.selectedJob = null;
    }

    async applyToJob(jobId = null) {
        const job = jobId ? this.jobs.find(j => j.id === jobId) : this.selectedJob;
        if (!job) return;

        this.showLoading('Applying to job...');

        try {
            const response = await fetch('/api/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ job_id: job.id })
            });

            const result = await response.json();

            if (result.success) {
                // Update job status
                job.application_status = 'applied';
                this.displayJobs();
                this.showNotification('success', `Successfully applied to ${job.title}!`);

                if (this.selectedJob && this.selectedJob.id === job.id) {
                    this.closeModal();
                }
            } else {
                this.showNotification('error', result.error || 'Application failed');
            }
        } catch (error) {
            console.error('Apply error:', error);
            this.showNotification('error', 'Application failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async bulkApply() {
        const notAppliedJobs = this.filteredJobs.filter(job => job.application_status === 'not_applied');

        if (notAppliedJobs.length === 0) {
            this.showNotification('warning', 'No jobs available for bulk apply');
            return;
        }

        if (!confirm(`Apply to ${notAppliedJobs.length} jobs automatically?`)) {
            return;
        }

        this.showLoading(`Applying to ${notAppliedJobs.length} jobs...`);

        try {
            const jobIds = notAppliedJobs.map(job => job.id);

            const response = await fetch('/api/bulk-apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ job_ids: jobIds })
            });

            const result = await response.json();

            if (result.success) {
                // Update job statuses based on results
                result.results.forEach(({ job_id, result: applyResult }) => {
                    const job = this.jobs.find(j => j.id === job_id);
                    if (job && applyResult.success) {
                        job.application_status = 'applied';
                    }
                });

                this.displayJobs();

                const successCount = result.results.filter(r => r.result.success).length;
                this.showNotification('success', `Successfully applied to ${successCount} out of ${result.total_processed} jobs!`);
            } else {
                this.showNotification('error', result.error || 'Bulk apply failed');
            }
        } catch (error) {
            console.error('Bulk apply error:', error);
            this.showNotification('error', 'Bulk apply failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    sortJobs() {
        const sortBy = document.getElementById('sort-by').value;

        this.filteredJobs.sort((a, b) => {
            switch (sortBy) {
                case 'date':
                    return new Date(b.posted_date) - new Date(a.posted_date);
                case 'company':
                    return a.company.localeCompare(b.company);
                case 'relevance':
                    return b.automation_score - a.automation_score;
                default:
                    return 0;
            }
        });

        this.currentPage = 1;
        this.displayJobs();
    }

    filterJobs() {
        const companyFilter = document.getElementById('company-filter').value.toLowerCase();

        this.filteredJobs = this.jobs.filter(job => {
            return job.company.toLowerCase().includes(companyFilter);
        });

        this.currentPage = 1;
        this.displayJobs();
    }

    loadMoreJobs() {
        this.currentPage++;
        this.displayJobs();
    }

    exportResults() {
        const dataStr = JSON.stringify(this.filteredJobs, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});

        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `job_results_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }

    viewOriginal() {
        if (this.selectedJob && this.selectedJob.url) {
            window.open(this.selectedJob.url, '_blank');
        }
    }

    async loadAnalytics() {
        try {
            const response = await fetch('/api/analytics');
            const result = await response.json();

            if (result.success) {
                const analytics = result.analytics;

                document.getElementById('total-applications').textContent = analytics.total_applications;
                document.getElementById('success-rate').textContent = `${analytics.success_rate.toFixed(1)}%`;
                document.getElementById('avg-time').textContent = `${analytics.avg_completion_time.toFixed(1)}s`;
                document.getElementById('form-patterns').textContent = analytics.form_patterns.length;
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    showAnalytics() {
        document.getElementById('analytics-section').style.display = 'block';
        document.getElementById('analytics-section').scrollIntoView({ behavior: 'smooth' });
        this.loadAnalytics();
    }

    showLoading(text = 'Loading...') {
        document.getElementById('loading-text').textContent = text;
        document.getElementById('loading-overlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    showNotification(type, message) {
        const container = document.getElementById('notification-container');

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; cursor: pointer; font-size: 16px; color: #6b7280;">&times;</button>
            </div>
        `;

        container.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diff = now - date;
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));

            if (days === 0) return 'Today';
            if (days === 1) return 'Yesterday';
            if (days < 7) return `${days} days ago`;
            if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
            return `${Math.floor(days / 30)} months ago`;
        } catch {
            return dateString;
        }
    }
}

// Global functions for HTML onclick handlers
let app;

window.addEventListener('DOMContentLoaded', () => {
    app = new JobRightApp();
});

function startSearch() {
    document.getElementById('job-search-form').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('keywords').focus();
}

function loadSavedJobs() {
    app.loadSavedJobs();
}

function sortJobs() {
    app.sortJobs();
}

function filterJobs() {
    app.filterJobs();
}

function loadMoreJobs() {
    app.loadMoreJobs();
}

function exportResults() {
    app.exportResults();
}

function bulkApply() {
    app.bulkApply();
}

function applyToJob() {
    app.applyToJob();
}

function applyToJobFromCard(jobId) {
    app.applyToJob(jobId);
}

function viewOriginal() {
    app.viewOriginal();
}

function closeModal() {
    app.closeModal();
}

function showSettings() {
    app.showNotification('info', 'Settings panel coming soon!');
}

function showAnalytics() {
    app.showAnalytics();
}