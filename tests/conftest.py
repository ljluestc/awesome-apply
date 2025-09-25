"""
Pytest configuration and fixtures for comprehensive testing
"""
import pytest
import asyncio
import docker
import kubernetes
import clickhouse_connect
import redis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from unittest.mock import Mock, patch
import tempfile
import os
import yaml
from typing import Generator, Dict, Any
import requests
from datetime import datetime

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def docker_client():
    """Docker client for container testing."""
    client = docker.from_env()
    yield client
    client.close()

@pytest.fixture(scope="session")
def kubernetes_client():
    """Kubernetes client for cluster testing."""
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.ConfigException:
        try:
            kubernetes.config.load_kube_config()
        except kubernetes.config.ConfigException:
            pytest.skip("No Kubernetes config available")

    v1 = kubernetes.client.CoreV1Api()
    apps_v1 = kubernetes.client.AppsV1Api()
    return {"core": v1, "apps": apps_v1}

@pytest.fixture
def clickhouse_client():
    """ClickHouse client for database testing."""
    try:
        client = clickhouse_connect.get_client(
            host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
            port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
            username=os.getenv('CLICKHOUSE_USER', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', ''),
            database=os.getenv('CLICKHOUSE_DB', 'default')
        )
        yield client
        client.close()
    except Exception:
        pytest.skip("ClickHouse not available")

@pytest.fixture
def redis_client():
    """Redis client for cache testing."""
    try:
        client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        client.ping()
        yield client
        client.flushdb()
    except Exception:
        pytest.skip("Redis not available")

@pytest.fixture
def chrome_driver():
    """Selenium Chrome WebDriver for UI testing."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

@pytest.fixture
def mock_job_data():
    """Mock job data for testing."""
    return {
        "id": "test-job-123",
        "title": "Senior Software Engineer",
        "company": "Test Company",
        "location": "San Francisco, CA",
        "salary_min": 120000,
        "salary_max": 180000,
        "job_type": "full-time",
        "employment_type": "permanent",
        "description": "Test job description",
        "requirements": "Test requirements",
        "url": "https://example.com/job/123",
        "source": "test-source",
        "posted_date": datetime.now(),
        "remote_friendly": True,
        "skills": ["Python", "Kubernetes", "Docker"]
    }

@pytest.fixture
def api_client():
    """HTTP client for API testing."""
    base_url = os.getenv('API_BASE_URL', 'http://localhost:8080')
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})

    class APIClient:
        def __init__(self, session, base_url):
            self.session = session
            self.base_url = base_url

        def get(self, endpoint, **kwargs):
            return self.session.get(f"{self.base_url}{endpoint}", **kwargs)

        def post(self, endpoint, **kwargs):
            return self.session.post(f"{self.base_url}{endpoint}", **kwargs)

        def put(self, endpoint, **kwargs):
            return self.session.put(f"{self.base_url}{endpoint}", **kwargs)

        def delete(self, endpoint, **kwargs):
            return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)

    yield APIClient(session, base_url)
    session.close()

@pytest.fixture
def test_namespace(kubernetes_client):
    """Create a test namespace for Kubernetes testing."""
    namespace_name = f"test-jobautomation-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Create namespace
    namespace = kubernetes.client.V1Namespace(
        metadata=kubernetes.client.V1ObjectMeta(name=namespace_name)
    )
    kubernetes_client["core"].create_namespace(namespace)

    yield namespace_name

    # Cleanup namespace
    try:
        kubernetes_client["core"].delete_namespace(namespace_name)
    except kubernetes.client.exceptions.ApiException:
        pass

@pytest.fixture
def temp_config_file():
    """Temporary configuration file for testing."""
    config = {
        'database': {
            'clickhouse_host': 'localhost',
            'clickhouse_port': 8123,
            'clickhouse_db': 'test_db'
        },
        'redis': {
            'redis_host': 'localhost',
            'redis_port': 6379
        },
        'scraping': {
            'max_concurrent_scrapers': 2,
            'scrape_interval': 60
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        temp_file = f.name

    yield temp_file

    os.unlink(temp_file)

@pytest.fixture
def mock_selenium_driver():
    """Mock Selenium WebDriver for unit testing."""
    mock_driver = Mock()
    mock_element = Mock()

    mock_driver.get.return_value = None
    mock_driver.find_element.return_value = mock_element
    mock_driver.find_elements.return_value = [mock_element]
    mock_driver.page_source = "<html><body>Test Page</body></html>"
    mock_driver.current_url = "https://example.com"

    mock_element.text = "Test Text"
    mock_element.get_attribute.return_value = "test-attribute"
    mock_element.click.return_value = None
    mock_element.send_keys.return_value = None
    mock_element.is_displayed.return_value = True

    return mock_driver

@pytest.fixture
def sample_resume_file():
    """Sample resume file for testing."""
    resume_content = """
    John Doe
    Senior Software Engineer

    Experience:
    - 5+ years in Python development
    - Kubernetes and Docker expertise
    - Microservices architecture

    Skills:
    - Python, Go, JavaScript
    - Kubernetes, Docker, CI/CD
    - AWS, GCP, Azure
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(resume_content)
        temp_file = f.name

    yield temp_file

    os.unlink(temp_file)

@pytest.fixture
def performance_metrics():
    """Performance metrics collection for testing."""
    metrics = {
        'start_time': None,
        'end_time': None,
        'duration': None,
        'memory_usage': [],
        'cpu_usage': [],
        'requests_count': 0,
        'errors_count': 0
    }

    def start_measuring():
        metrics['start_time'] = datetime.now()

    def stop_measuring():
        metrics['end_time'] = datetime.now()
        if metrics['start_time']:
            metrics['duration'] = (metrics['end_time'] - metrics['start_time']).total_seconds()

    def add_request():
        metrics['requests_count'] += 1

    def add_error():
        metrics['errors_count'] += 1

    metrics['start'] = start_measuring
    metrics['stop'] = stop_measuring
    metrics['add_request'] = add_request
    metrics['add_error'] = add_error

    return metrics

@pytest.fixture(autouse=True)
def cleanup_test_data(clickhouse_client, redis_client):
    """Cleanup test data after each test."""
    yield

    # Cleanup ClickHouse test data
    if clickhouse_client:
        try:
            clickhouse_client.command("DROP TABLE IF EXISTS test_jobs")
            clickhouse_client.command("DROP TABLE IF EXISTS test_applications")
        except Exception:
            pass

    # Cleanup Redis test data
    if redis_client:
        try:
            for key in redis_client.keys("test:*"):
                redis_client.delete(key)
        except Exception:
            pass

# Performance testing utilities
@pytest.fixture
def load_test_config():
    """Load testing configuration."""
    return {
        'concurrent_users': 10,
        'duration_seconds': 60,
        'ramp_up_seconds': 10,
        'target_rps': 100,
        'max_response_time_ms': 1000
    }

# Security testing utilities
@pytest.fixture
def security_test_payloads():
    """Security test payloads for vulnerability testing."""
    return {
        'sql_injection': [
            "'; DROP TABLE jobs; --",
            "1' OR '1'='1",
            "admin'--",
            "admin'/*"
        ],
        'xss': [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ],
        'path_traversal': [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
    }

# Test data generators
@pytest.fixture
def job_data_generator():
    """Generate test job data."""
    def generate_jobs(count=10):
        jobs = []
        for i in range(count):
            job = {
                "id": f"test-job-{i}",
                "title": f"Test Position {i}",
                "company": f"Test Company {i}",
                "location": f"Test City {i}",
                "salary_min": 50000 + (i * 10000),
                "salary_max": 80000 + (i * 10000),
                "job_type": "full-time",
                "source": "test-source",
                "posted_date": datetime.now(),
                "skills": [f"skill-{i}", f"skill-{i+1}"]
            }
            jobs.append(job)
        return jobs

    return generate_jobs

# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    test_env = {
        'TESTING': 'true',
        'LOG_LEVEL': 'DEBUG',
        'CLICKHOUSE_DB': 'test_job_automation',
        'REDIS_DB': '15'  # Use Redis database 15 for testing
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value