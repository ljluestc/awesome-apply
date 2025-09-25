"""
Load and performance testing for the job automation system
"""
import pytest
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import threading
from typing import List, Dict, Any
import json

class PerformanceTestResult:
    """Container for performance test results."""

    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.status_codes: Dict[int, int] = {}
        self.throughput: float = 0.0
        self.cpu_usage: List[float] = []
        self.memory_usage: List[float] = []
        self.start_time: float = 0
        self.end_time: float = 0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        total_requests = len(self.response_times) + len(self.errors)
        if total_requests == 0:
            return 0.0
        return len(self.response_times) / total_requests * 100

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0

    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]

    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]


class SystemMonitor:
    """Monitor system resources during performance tests."""

    def __init__(self):
        self.monitoring = False
        self.cpu_usage: List[float] = []
        self.memory_usage: List[float] = []
        self.monitor_thread = None

    def start_monitoring(self):
        """Start system monitoring in a separate thread."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_resources(self):
        """Monitor CPU and memory usage."""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                self.cpu_usage.append(cpu_percent)
                self.memory_usage.append(memory_percent)
            except Exception:
                pass
            time.sleep(1)


@pytest.mark.performance
class TestLoadPerformance:
    """Load performance tests for the job automation system."""

    @pytest.fixture(autouse=True)
    def setup_performance_test(self, api_client):
        """Setup for performance testing."""
        self.api_client = api_client
        self.base_url = api_client.base_url

    async def make_request(self, session: aiohttp.ClientSession, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make an async HTTP request and measure response time."""
        start_time = time.time()
        try:
            async with session.request(method, url, **kwargs) as response:
                await response.read()  # Ensure full response is received
                end_time = time.time()
                return {
                    'success': True,
                    'status_code': response.status,
                    'response_time': end_time - start_time,
                    'error': None
                }
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'status_code': 0,
                'response_time': end_time - start_time,
                'error': str(e)
            }

    async def run_load_test(
        self,
        endpoint: str,
        concurrent_users: int,
        duration_seconds: int,
        method: str = 'GET',
        **request_kwargs
    ) -> PerformanceTestResult:
        """Run load test against an endpoint."""
        result = PerformanceTestResult()
        system_monitor = SystemMonitor()

        url = f"{self.base_url}{endpoint}"

        # Start system monitoring
        system_monitor.start_monitoring()
        result.start_time = time.time()

        async with aiohttp.ClientSession() as session:
            end_time = result.start_time + duration_seconds
            tasks = []

            # Create concurrent requests
            while time.time() < end_time:
                if len(tasks) < concurrent_users:
                    task = asyncio.create_task(
                        self.make_request(session, url, method, **request_kwargs)
                    )
                    tasks.append(task)

                # Process completed tasks
                done_tasks = [task for task in tasks if task.done()]
                for task in done_tasks:
                    try:
                        response_data = await task
                        if response_data['success']:
                            result.response_times.append(response_data['response_time'])
                            status_code = response_data['status_code']
                            result.status_codes[status_code] = result.status_codes.get(status_code, 0) + 1
                        else:
                            result.errors.append(response_data['error'])
                    except Exception as e:
                        result.errors.append(str(e))
                    tasks.remove(task)

                await asyncio.sleep(0.01)  # Small delay to prevent overwhelming

            # Wait for remaining tasks
            if tasks:
                remaining_results = await asyncio.gather(*tasks, return_exceptions=True)
                for response_data in remaining_results:
                    if isinstance(response_data, dict):
                        if response_data['success']:
                            result.response_times.append(response_data['response_time'])
                            status_code = response_data['status_code']
                            result.status_codes[status_code] = result.status_codes.get(status_code, 0) + 1
                        else:
                            result.errors.append(response_data['error'])
                    else:
                        result.errors.append(str(response_data))

        result.end_time = time.time()
        system_monitor.stop_monitoring()

        # Calculate metrics
        result.throughput = len(result.response_times) / result.duration
        result.cpu_usage = system_monitor.cpu_usage
        result.memory_usage = system_monitor.memory_usage

        return result

    @pytest.mark.asyncio
    async def test_api_health_load(self, load_test_config):
        """Load test the health endpoint."""
        result = await self.run_load_test(
            endpoint='/health',
            concurrent_users=load_test_config['concurrent_users'],
            duration_seconds=30  # Shorter duration for health check
        )

        # Assertions
        assert result.success_rate >= 99.0, f"Success rate too low: {result.success_rate}%"
        assert result.avg_response_time < 0.1, f"Average response time too high: {result.avg_response_time}s"
        assert result.p95_response_time < 0.2, f"P95 response time too high: {result.p95_response_time}s"
        assert result.throughput > 50, f"Throughput too low: {result.throughput} req/s"

        print(f"Health endpoint performance:")
        print(f"  Success rate: {result.success_rate:.2f}%")
        print(f"  Average response time: {result.avg_response_time:.3f}s")
        print(f"  P95 response time: {result.p95_response_time:.3f}s")
        print(f"  Throughput: {result.throughput:.2f} req/s")

    @pytest.mark.asyncio
    async def test_jobs_api_load(self, load_test_config, mock_job_data):
        """Load test the jobs API."""
        result = await self.run_load_test(
            endpoint='/api/jobs',
            concurrent_users=load_test_config['concurrent_users'],
            duration_seconds=load_test_config['duration_seconds']
        )

        # Assertions for jobs API
        assert result.success_rate >= 95.0, f"Success rate too low: {result.success_rate}%"
        assert result.avg_response_time < 1.0, f"Average response time too high: {result.avg_response_time}s"
        assert result.p95_response_time < 2.0, f"P95 response time too high: {result.p95_response_time}s"
        assert result.throughput > 10, f"Throughput too low: {result.throughput} req/s"

        print(f"Jobs API performance:")
        print(f"  Success rate: {result.success_rate:.2f}%")
        print(f"  Average response time: {result.avg_response_time:.3f}s")
        print(f"  P95 response time: {result.p95_response_time:.3f}s")
        print(f"  Throughput: {result.throughput:.2f} req/s")

    @pytest.mark.asyncio
    async def test_application_submission_load(self, load_test_config, mock_job_data):
        """Load test job application submission."""
        application_data = {
            'job_id': mock_job_data['id'],
            'resume_path': '/tmp/test_resume.pdf',
            'cover_letter': 'Test cover letter'
        }

        result = await self.run_load_test(
            endpoint='/api/applications',
            method='POST',
            concurrent_users=5,  # Lower concurrency for write operations
            duration_seconds=30,
            json=application_data
        )

        # More lenient assertions for write operations
        assert result.success_rate >= 90.0, f"Success rate too low: {result.success_rate}%"
        assert result.avg_response_time < 3.0, f"Average response time too high: {result.avg_response_time}s"
        assert result.p95_response_time < 5.0, f"P95 response time too high: {result.p95_response_time}s"

        print(f"Application submission performance:")
        print(f"  Success rate: {result.success_rate:.2f}%")
        print(f"  Average response time: {result.avg_response_time:.3f}s")
        print(f"  P95 response time: {result.p95_response_time:.3f}s")
        print(f"  Throughput: {result.throughput:.2f} req/s")

    @pytest.mark.asyncio
    async def test_mixed_workload(self, load_test_config):
        """Test mixed workload with different endpoint access patterns."""
        endpoints = [
            ('/health', 'GET', 0.4),  # 40% health checks
            ('/api/jobs', 'GET', 0.3),  # 30% job listings
            ('/api/stats', 'GET', 0.2),  # 20% statistics
            ('/metrics', 'GET', 0.1)   # 10% metrics
        ]

        results = []
        tasks = []

        for endpoint, method, weight in endpoints:
            concurrent_users = max(1, int(load_test_config['concurrent_users'] * weight))
            task = asyncio.create_task(
                self.run_load_test(
                    endpoint=endpoint,
                    method=method,
                    concurrent_users=concurrent_users,
                    duration_seconds=load_test_config['duration_seconds']
                )
            )
            tasks.append((endpoint, task))

        # Wait for all tasks to complete
        for endpoint, task in tasks:
            result = await task
            results.append((endpoint, result))
            print(f"{endpoint} - Success: {result.success_rate:.2f}%, "
                  f"Avg RT: {result.avg_response_time:.3f}s, "
                  f"Throughput: {result.throughput:.2f} req/s")

        # Overall assertions
        overall_success_rate = sum(r.success_rate for _, r in results) / len(results)
        assert overall_success_rate >= 95.0, f"Overall success rate too low: {overall_success_rate}%"

    def test_database_connection_pool_performance(self, clickhouse_client):
        """Test database connection pool under load."""
        def execute_query():
            try:
                start_time = time.time()
                result = clickhouse_client.query("SELECT 1 as test")
                end_time = time.time()
                return end_time - start_time, None
            except Exception as e:
                return 0, str(e)

        # Execute concurrent database queries
        response_times = []
        errors = []

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(execute_query) for _ in range(100)]

            for future in as_completed(futures):
                response_time, error = future.result()
                if error:
                    errors.append(error)
                else:
                    response_times.append(response_time)

        # Assertions
        success_rate = len(response_times) / (len(response_times) + len(errors)) * 100
        assert success_rate >= 95.0, f"Database success rate too low: {success_rate}%"

        if response_times:
            avg_time = statistics.mean(response_times)
            assert avg_time < 0.1, f"Average database response time too high: {avg_time}s"

        print(f"Database performance:")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Average response time: {avg_time:.3f}s" if response_times else "  No successful queries")

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation."""
        initial_memory = psutil.virtual_memory().percent
        system_monitor = SystemMonitor()
        system_monitor.start_monitoring()

        # Run extended test
        result = await self.run_load_test(
            endpoint='/health',
            concurrent_users=5,
            duration_seconds=120  # 2 minutes
        )

        system_monitor.stop_monitoring()
        final_memory = psutil.virtual_memory().percent

        # Check for memory leaks
        memory_increase = final_memory - initial_memory
        avg_memory_during_test = statistics.mean(system_monitor.memory_usage) if system_monitor.memory_usage else 0

        assert memory_increase < 10, f"Potential memory leak detected: {memory_increase}% increase"
        assert avg_memory_during_test < 90, f"Memory usage too high: {avg_memory_during_test}%"

        print(f"Memory analysis:")
        print(f"  Initial memory: {initial_memory:.1f}%")
        print(f"  Final memory: {final_memory:.1f}%")
        print(f"  Memory increase: {memory_increase:.1f}%")
        print(f"  Average during test: {avg_memory_during_test:.1f}%")

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_stress_test(self):
        """Stress test with high load."""
        result = await self.run_load_test(
            endpoint='/api/jobs',
            concurrent_users=50,  # High concurrency
            duration_seconds=300  # 5 minutes
        )

        # More lenient thresholds for stress test
        assert result.success_rate >= 85.0, f"Stress test success rate too low: {result.success_rate}%"
        assert result.avg_response_time < 5.0, f"Stress test response time too high: {result.avg_response_time}s"

        print(f"Stress test results:")
        print(f"  Success rate: {result.success_rate:.2f}%")
        print(f"  Average response time: {result.avg_response_time:.3f}s")
        print(f"  P95 response time: {result.p95_response_time:.3f}s")
        print(f"  P99 response time: {result.p99_response_time:.3f}s")
        print(f"  Throughput: {result.throughput:.2f} req/s")
        print(f"  Total requests: {len(result.response_times)}")
        print(f"  Total errors: {len(result.errors)}")