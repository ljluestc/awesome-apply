-- Create database and tables for job automation system
CREATE DATABASE IF NOT EXISTS job_automation;

USE job_automation;

-- Jobs table with comprehensive metadata
CREATE TABLE IF NOT EXISTS jobs (
    id String,
    title String,
    company String,
    location String,
    salary_min Nullable(Int32),
    salary_max Nullable(Int32),
    job_type String,
    employment_type String,
    description String,
    requirements String,
    url String,
    source String,
    posted_date DateTime,
    scraped_at DateTime DEFAULT now(),
    location_type String DEFAULT 'onsite',
    remote_friendly Boolean DEFAULT false,
    experience_level String DEFAULT 'mid',
    department String DEFAULT '',
    skills Array(String) DEFAULT [],
    benefits Array(String) DEFAULT [],
    company_size String DEFAULT '',
    industry String DEFAULT '',
    is_active Boolean DEFAULT true,
    application_deadline Nullable(DateTime),
    job_function String DEFAULT '',
    seniority_level String DEFAULT '',
    company_url String DEFAULT '',
    logo_url String DEFAULT '',
    application_count Nullable(Int32),
    view_count Nullable(Int32),
    geo_latitude Nullable(Float64),
    geo_longitude Nullable(Float64),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (source, posted_date, id)
PARTITION BY toYYYYMM(posted_date)
TTL posted_date + INTERVAL 6 MONTH;

-- Applications tracking table
CREATE TABLE IF NOT EXISTS applications (
    id String,
    job_id String,
    user_id String DEFAULT 'default_user',
    status String DEFAULT 'pending',
    applied_at DateTime DEFAULT now(),
    response_received Boolean DEFAULT false,
    response_date Nullable(DateTime),
    interview_scheduled Boolean DEFAULT false,
    interview_date Nullable(DateTime),
    resume_version String DEFAULT '',
    cover_letter_used Boolean DEFAULT false,
    automation_pattern String DEFAULT '',
    success_probability Float32 DEFAULT 0.0,
    notes String DEFAULT '',
    source_automation String DEFAULT 'manual',
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (user_id, applied_at, id)
PARTITION BY toYYYYMM(applied_at)
TTL applied_at + INTERVAL 1 YEAR;

-- Automation patterns for reusable form filling
CREATE TABLE IF NOT EXISTS automation_patterns (
    id String,
    site_domain String,
    pattern_name String,
    form_selector String,
    field_mappings String, -- JSON string
    success_rate Float32 DEFAULT 0.0,
    last_used DateTime DEFAULT now(),
    usage_count Int32 DEFAULT 0,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (site_domain, pattern_name, id);

-- Companies information
CREATE TABLE IF NOT EXISTS companies (
    id String,
    name String,
    domain String DEFAULT '',
    industry String DEFAULT '',
    size String DEFAULT '',
    headquarters String DEFAULT '',
    founded_year Nullable(Int32),
    description String DEFAULT '',
    logo_url String DEFAULT '',
    careers_page String DEFAULT '',
    glassdoor_rating Nullable(Float32),
    indeed_rating Nullable(Float32),
    linkedin_followers Nullable(Int32),
    job_count Nullable(Int32),
    recent_hiring Boolean DEFAULT false,
    tech_stack Array(String) DEFAULT [],
    benefits Array(String) DEFAULT [],
    culture_keywords Array(String) DEFAULT [],
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (name, id);

-- Performance metrics
CREATE TABLE IF NOT EXISTS metrics (
    timestamp DateTime DEFAULT now(),
    metric_name String,
    metric_value Float64,
    tags Map(String, String) DEFAULT map(),
    source String DEFAULT 'automation_system'
) ENGINE = MergeTree()
ORDER BY (metric_name, timestamp)
PARTITION BY toYYYYMM(timestamp)
TTL timestamp + INTERVAL 3 MONTH;

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS jobs_by_day AS
SELECT
    toDate(posted_date) as date,
    source,
    count() as job_count,
    countIf(remote_friendly = true) as remote_jobs,
    avg(salary_min) as avg_salary_min,
    avg(salary_max) as avg_salary_max
FROM jobs
GROUP BY date, source
ORDER BY date DESC;

-- Application success rate view
CREATE MATERIALIZED VIEW IF NOT EXISTS application_success_rate AS
SELECT
    toYYYYMM(applied_at) as month,
    status,
    count() as application_count,
    countIf(response_received = true) as responses,
    countIf(interview_scheduled = true) as interviews,
    avg(success_probability) as avg_success_prob
FROM applications
GROUP BY month, status
ORDER BY month DESC;