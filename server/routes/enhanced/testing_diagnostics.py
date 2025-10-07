"""
Comprehensive Testing Framework and Diagnostics System
Includes automated testing, system diagnostics, performance monitoring, and health checks
"""

import os
import sys
import json
import time
import psutil
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from flask import Blueprint, request, jsonify, current_app
import requests
import sqlite3

bp = Blueprint('testing_diagnostics', __name__)

class SystemDiagnostics:
    """Comprehensive system diagnostics and monitoring"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitoring_thread = None
        self.performance_history = []
        self.max_history_size = 1000
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # CPU Information
            cpu_info = {
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'cpu_usage': psutil.cpu_percent(interval=1),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            # Memory Information
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free,
                'buffers': getattr(memory, 'buffers', 0),
                'cached': getattr(memory, 'cached', 0)
            }
            
            # Disk Information
            disk_info = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    })
                except PermissionError:
                    continue
            
            # Network Information
            network_info = {}
            try:
                net_io = psutil.net_io_counters()
                network_info = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                }
            except Exception:
                pass
            
            # Process Information
            current_process = psutil.Process()
            process_info = {
                'pid': current_process.pid,
                'memory_info': current_process.memory_info()._asdict(),
                'cpu_percent': current_process.cpu_percent(),
                'num_threads': current_process.num_threads(),
                'create_time': current_process.create_time(),
                'status': current_process.status()
            }
            
            # Python Information
            python_info = {
                'version': sys.version,
                'executable': sys.executable,
                'platform': sys.platform,
                'path': sys.path[:5]  # First 5 paths only
            }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'process': process_info,
                'python': python_info
            }
        
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check all system dependencies and their status"""
        dependencies = {
            'python_packages': [
                'flask', 'requests', 'psutil', 'feedparser', 'sqlite3'
            ],
            'system_commands': [
                'ffmpeg', 'curl', 'wget', 'unzip', 'zip'
            ],
            'optional_packages': [
                'opencv-python', 'pillow', 'numpy', 'pandas'
            ]
        }
        
        results = {
            'python_packages': {},
            'system_commands': {},
            'optional_packages': {},
            'overall_status': 'healthy'
        }
        
        # Check Python packages
        for package in dependencies['python_packages']:
            try:
                __import__(package)
                results['python_packages'][package] = {
                    'status': 'installed',
                    'version': self._get_package_version(package)
                }
            except ImportError:
                results['python_packages'][package] = {
                    'status': 'missing',
                    'version': None
                }
                results['overall_status'] = 'warning'
        
        # Check system commands
        for command in dependencies['system_commands']:
            try:
                result = subprocess.run(
                    [command, '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                results['system_commands'][command] = {
                    'status': 'available',
                    'version': result.stdout.split('\n')[0] if result.stdout else 'unknown'
                }
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                results['system_commands'][command] = {
                    'status': 'missing',
                    'version': None
                }
                results['overall_status'] = 'warning'
        
        # Check optional packages
        for package in dependencies['optional_packages']:
            try:
                __import__(package)
                results['optional_packages'][package] = {
                    'status': 'installed',
                    'version': self._get_package_version(package)
                }
            except ImportError:
                results['optional_packages'][package] = {
                    'status': 'missing',
                    'version': None
                }
        
        return results
    
    def _get_package_version(self, package_name: str) -> Optional[str]:
        """Get version of a Python package"""
        try:
            import importlib.metadata
            return importlib.metadata.version(package_name)
        except Exception:
            try:
                module = __import__(package_name)
                return getattr(module, '__version__', 'unknown')
            except Exception:
                return 'unknown'
    
    def run_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance tests"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # CPU Performance Test
        start_time = time.time()
        # Simple CPU intensive task
        total = 0
        for i in range(1000000):
            total += i * i
        cpu_time = time.time() - start_time
        
        results['tests']['cpu_performance'] = {
            'duration': cpu_time,
            'operations_per_second': 1000000 / cpu_time,
            'status': 'pass' if cpu_time < 1.0 else 'slow'
        }
        
        # Memory Performance Test
        start_time = time.time()
        test_data = [i for i in range(100000)]
        memory_time = time.time() - start_time
        del test_data
        
        results['tests']['memory_performance'] = {
            'duration': memory_time,
            'status': 'pass' if memory_time < 0.5 else 'slow'
        }
        
        # Disk I/O Test
        test_file = Path('/tmp/mediahub_disk_test.tmp')
        try:
            start_time = time.time()
            with open(test_file, 'w') as f:
                f.write('x' * 1024 * 1024)  # Write 1MB
            write_time = time.time() - start_time
            
            start_time = time.time()
            with open(test_file, 'r') as f:
                data = f.read()
            read_time = time.time() - start_time
            
            test_file.unlink()  # Delete test file
            
            results['tests']['disk_io'] = {
                'write_time': write_time,
                'read_time': read_time,
                'write_speed_mb_s': 1.0 / write_time if write_time > 0 else 0,
                'read_speed_mb_s': 1.0 / read_time if read_time > 0 else 0,
                'status': 'pass' if (write_time < 1.0 and read_time < 0.5) else 'slow'
            }
        except Exception as e:
            results['tests']['disk_io'] = {
                'error': str(e),
                'status': 'fail'
            }
        
        # Network Test (if possible)
        try:
            start_time = time.time()
            response = requests.get('https://httpbin.org/get', timeout=5)
            network_time = time.time() - start_time
            
            results['tests']['network_connectivity'] = {
                'duration': network_time,
                'status_code': response.status_code,
                'status': 'pass' if response.status_code == 200 and network_time < 3.0 else 'fail'
            }
        except Exception as e:
            results['tests']['network_connectivity'] = {
                'error': str(e),
                'status': 'fail'
            }
        
        return results
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous system monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            args=(interval,)
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def _monitoring_loop(self, interval: int):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect performance data
                data_point = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': [
                        {
                            'mountpoint': partition.mountpoint,
                            'percent': psutil.disk_usage(partition.mountpoint).percent
                        }
                        for partition in psutil.disk_partitions()
                        if partition.mountpoint in ['/', '/home', '/tmp']
                    ]
                }
                
                # Add to history
                self.performance_history.append(data_point)
                
                # Limit history size
                if len(self.performance_history) > self.max_history_size:
                    self.performance_history = self.performance_history[-self.max_history_size:]
                
                time.sleep(interval)
            
            except Exception as e:
                current_app.logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)
    
    def get_performance_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_history = []
        for data_point in self.performance_history:
            try:
                timestamp = datetime.fromisoformat(data_point['timestamp'])
                if timestamp >= cutoff_time:
                    filtered_history.append(data_point)
            except Exception:
                continue
        
        return filtered_history

class APITester:
    """Automated API testing framework"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url
        self.test_results = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests"""
        test_suites = [
            self._test_basic_endpoints,
            self._test_real_debrid_endpoints,
            self._test_downloader_endpoints,
            self._test_text_editor_endpoints,
            self._test_smart_collections_endpoints,
            self._test_rss_endpoints,
            self._test_metadata_endpoints
        ]
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_suites': {},
            'overall_status': 'pass'
        }
        
        for test_suite in test_suites:
            try:
                suite_name = test_suite.__name__.replace('_test_', '').replace('_endpoints', '')
                suite_results = test_suite()
                
                results['test_suites'][suite_name] = suite_results
                results['total_tests'] += suite_results['total']
                results['passed_tests'] += suite_results['passed']
                results['failed_tests'] += suite_results['failed']
                
                if suite_results['failed'] > 0:
                    results['overall_status'] = 'fail'
            
            except Exception as e:
                results['test_suites'][test_suite.__name__] = {
                    'error': str(e),
                    'total': 0,
                    'passed': 0,
                    'failed': 1
                }
                results['failed_tests'] += 1
                results['overall_status'] = 'fail'
        
        return results
    
    def _test_basic_endpoints(self) -> Dict[str, Any]:
        """Test basic application endpoints"""
        tests = [
            ('GET', '/api/health', 200),
            ('GET', '/api/system/info', 200),
            ('GET', '/api/profiles/list', 200)
        ]
        
        return self._run_test_suite('basic_endpoints', tests)
    
    def _test_real_debrid_endpoints(self) -> Dict[str, Any]:
        """Test Real-Debrid endpoints"""
        tests = [
            ('GET', '/api/rd/user/info', [200, 401, 500]),  # May fail if no API key
            ('GET', '/api/rd/torrents/list', [200, 401, 500]),
            ('POST', '/api/rd/deduplication/analyze', [200, 400, 500])
        ]
        
        return self._run_test_suite('real_debrid', tests)
    
    def _test_downloader_endpoints(self) -> Dict[str, Any]:
        """Test downloader endpoints"""
        tests = [
            ('GET', '/api/downloader/status', 200),
            ('GET', '/api/downloader/queue', 200),
            ('POST', '/api/downloader/linkgrabber/analyze', [200, 400])
        ]
        
        return self._run_test_suite('downloader', tests)
    
    def _test_text_editor_endpoints(self) -> Dict[str, Any]:
        """Test text editor endpoints"""
        tests = [
            ('GET', '/api/editor/files/list', 200),
            ('POST', '/api/editor/text/analyze', [200, 400])
        ]
        
        return self._run_test_suite('text_editor', tests)
    
    def _test_smart_collections_endpoints(self) -> Dict[str, Any]:
        """Test smart collections endpoints"""
        tests = [
            ('GET', '/api/collections/universes/list', 200),
            ('GET', '/api/collections/list', 200),
            ('POST', '/api/smart-rules/analyze', [200, 400])
        ]
        
        return self._run_test_suite('smart_collections', tests)
    
    def _test_rss_endpoints(self) -> Dict[str, Any]:
        """Test RSS endpoints"""
        tests = [
            ('POST', '/api/rss/metadata/search', [200, 400]),
            ('POST', '/api/rss/missing-episodes/check', [200, 400])
        ]
        
        return self._run_test_suite('rss', tests)
    
    def _test_metadata_endpoints(self) -> Dict[str, Any]:
        """Test metadata endpoints"""
        tests = [
            ('POST', '/api/metadata/search', [200, 400, 500])
        ]
        
        return self._run_test_suite('metadata', tests)
    
    def _run_test_suite(self, suite_name: str, tests: List[Tuple]) -> Dict[str, Any]:
        """Run a test suite"""
        results = {
            'suite_name': suite_name,
            'total': len(tests),
            'passed': 0,
            'failed': 0,
            'tests': []
        }
        
        for test in tests:
            method, endpoint, expected_status = test
            expected_statuses = expected_status if isinstance(expected_status, list) else [expected_status]
            
            test_result = self._run_single_test(method, endpoint, expected_statuses)
            results['tests'].append(test_result)
            
            if test_result['status'] == 'pass':
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def _run_single_test(self, method: str, endpoint: str, expected_statuses: List[int]) -> Dict[str, Any]:
        """Run a single API test"""
        test_result = {
            'method': method,
            'endpoint': endpoint,
            'expected_statuses': expected_statuses,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                # Send minimal valid data for POST requests
                test_data = self._get_test_data_for_endpoint(endpoint)
                response = requests.post(url, json=test_data, timeout=10)
            else:
                test_result.update({
                    'status': 'fail',
                    'error': f'Unsupported method: {method}'
                })
                return test_result
            
            test_result.update({
                'actual_status': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'response_size': len(response.content)
            })
            
            if response.status_code in expected_statuses:
                test_result['status'] = 'pass'
            else:
                test_result['status'] = 'fail'
                test_result['error'] = f'Unexpected status code: {response.status_code}'
        
        except requests.exceptions.RequestException as e:
            test_result.update({
                'status': 'fail',
                'error': str(e)
            })
        except Exception as e:
            test_result.update({
                'status': 'fail',
                'error': f'Test execution error: {str(e)}'
            })
        
        return test_result
    
    def _get_test_data_for_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Get appropriate test data for POST endpoints"""
        test_data_map = {
            '/api/rd/deduplication/analyze': {'profile': 'default'},
            '/api/downloader/linkgrabber/analyze': {'urls': ['https://example.com/test.zip']},
            '/api/editor/text/analyze': {'text': 'test content'},
            '/api/smart-rules/analyze': {'item': {'title': 'Test Movie', 'filename': 'test.mp4'}},
            '/api/rss/metadata/search': {'query': 'test', 'content_type': 'movie'},
            '/api/rss/missing-episodes/check': {'series_name': 'Test Series', 'available_episodes': []},
            '/api/metadata/search': {'query': 'test movie', 'content_type': 'movie'}
        }
        
        return test_data_map.get(endpoint, {})

class DatabaseTester:
    """Database integrity and performance testing"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def run_database_tests(self) -> Dict[str, Any]:
        """Run comprehensive database tests"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'pass'
        }
        
        # Test database connection
        connection_test = self._test_connection()
        results['tests']['connection'] = connection_test
        if connection_test['status'] != 'pass':
            results['overall_status'] = 'fail'
        
        # Test table integrity
        integrity_test = self._test_table_integrity()
        results['tests']['table_integrity'] = integrity_test
        if integrity_test['status'] != 'pass':
            results['overall_status'] = 'fail'
        
        # Test performance
        performance_test = self._test_performance()
        results['tests']['performance'] = performance_test
        if performance_test['status'] != 'pass':
            results['overall_status'] = 'warning'
        
        return results
    
    def _test_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            return {
                'status': 'pass' if result and result[0] == 1 else 'fail',
                'message': 'Database connection successful'
            }
        
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }
    
    def _test_table_integrity(self) -> Dict[str, Any]:
        """Test database table integrity"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            
            # Check if required tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'media_items', 'collections', 'rss_feeds', 'profiles',
                'download_queue', 'real_debrid_cache'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            # Run PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()
            
            conn.close()
            
            status = 'pass'
            issues = []
            
            if missing_tables:
                status = 'fail'
                issues.append(f"Missing tables: {', '.join(missing_tables)}")
            
            if integrity_result and integrity_result[0] != 'ok':
                status = 'fail'
                issues.append(f"Integrity check failed: {integrity_result[0]}")
            
            return {
                'status': status,
                'tables_found': len(tables),
                'missing_tables': missing_tables,
                'integrity_check': integrity_result[0] if integrity_result else 'unknown',
                'issues': issues
            }
        
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }
    
    def _test_performance(self) -> Dict[str, Any]:
        """Test database performance"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            
            # Test simple query performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            simple_query_time = time.time() - start_time
            
            # Test more complex query if media_items table exists
            complex_query_time = None
            try:
                start_time = time.time()
                cursor.execute("SELECT * FROM media_items LIMIT 100")
                complex_query_time = time.time() - start_time
            except sqlite3.OperationalError:
                pass  # Table might not exist
            
            conn.close()
            
            status = 'pass'
            if simple_query_time > 1.0:
                status = 'slow'
            if complex_query_time and complex_query_time > 2.0:
                status = 'slow'
            
            return {
                'status': status,
                'simple_query_time': simple_query_time,
                'complex_query_time': complex_query_time,
                'performance_rating': 'good' if status == 'pass' else 'needs_optimization'
            }
        
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }

# Global instances
system_diagnostics = SystemDiagnostics()
api_tester = None
database_tester = None

def init_testing_diagnostics(db_path: str):
    """Initialize testing and diagnostics"""
    global api_tester, database_tester
    api_tester = APITester()
    database_tester = DatabaseTester(db_path)

@bp.route('/system/info')
def get_system_info():
    """Get comprehensive system information"""
    try:
        system_info = system_diagnostics.get_system_info()
        return jsonify({
            'success': True,
            'system_info': system_info
        })
    
    except Exception as e:
        current_app.logger.error(f"Get system info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/system/dependencies')
def check_dependencies():
    """Check system dependencies"""
    try:
        dependencies = system_diagnostics.check_dependencies()
        return jsonify({
            'success': True,
            'dependencies': dependencies
        })
    
    except Exception as e:
        current_app.logger.error(f"Check dependencies error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/system/performance-test', methods=['POST'])
def run_performance_test():
    """Run system performance test"""
    try:
        performance_results = system_diagnostics.run_performance_test()
        return jsonify({
            'success': True,
            'performance_results': performance_results
        })
    
    except Exception as e:
        current_app.logger.error(f"Performance test error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start system monitoring"""
    try:
        data = request.json or {}
        interval = data.get('interval', 60)
        
        system_diagnostics.start_monitoring(interval)
        
        return jsonify({
            'success': True,
            'message': 'System monitoring started',
            'interval': interval
        })
    
    except Exception as e:
        current_app.logger.error(f"Start monitoring error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop system monitoring"""
    try:
        system_diagnostics.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'System monitoring stopped'
        })
    
    except Exception as e:
        current_app.logger.error(f"Stop monitoring error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/monitoring/history')
def get_monitoring_history():
    """Get system monitoring history"""
    try:
        hours = request.args.get('hours', 24, type=int)
        history = system_diagnostics.get_performance_history(hours)
        
        return jsonify({
            'success': True,
            'history': history,
            'data_points': len(history)
        })
    
    except Exception as e:
        current_app.logger.error(f"Get monitoring history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api-tests/run', methods=['POST'])
def run_api_tests():
    """Run comprehensive API tests"""
    try:
        if not api_tester:
            return jsonify({'success': False, 'error': 'API tester not initialized'})
        
        test_results = api_tester.run_all_tests()
        
        return jsonify({
            'success': True,
            'test_results': test_results
        })
    
    except Exception as e:
        current_app.logger.error(f"API tests error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/database-tests/run', methods=['POST'])
def run_database_tests():
    """Run database integrity tests"""
    try:
        if not database_tester:
            return jsonify({'success': False, 'error': 'Database tester not initialized'})
        
        test_results = database_tester.run_database_tests()
        
        return jsonify({
            'success': True,
            'test_results': test_results
        })
    
    except Exception as e:
        current_app.logger.error(f"Database tests error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/health')
def health_check():
    """Simple health check endpoint"""
    try:
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500
