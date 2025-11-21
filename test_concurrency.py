"""
Test MCP Server Concurrency
Tests the ability to handle multiple concurrent requests
"""

import asyncio
import time
import httpx
import statistics
import argparse
from typing import List, Dict, Any


class ConcurrencyTester:
    def __init__(self, host: str = "localhost", port: int = 8001):
        self.base_url = f"http://{host}:{port}"
        self.request_id = 0
    
    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id
    
    async def add_memory(self, user_id: str, message: str) -> Dict[str, Any]:
        """Add a memory via MCP server"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            start = time.time()
            response = await client.post(
                f"{self.base_url}/mcp/messages",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "tools/call",
                    "params": {
                        "name": "add_memory",
                        "arguments": {
                            "messages": [
                                {"role": "user", "content": message}
                            ],
                            "user_id": user_id
                        }
                    }
                }
            )
            elapsed = time.time() - start
            return {
                "status": response.status_code,
                "elapsed": elapsed,
                "success": response.status_code == 200
            }
    
    async def search_memory(self, user_id: str, query: str) -> Dict[str, Any]:
        """Search memories via MCP server"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            start = time.time()
            response = await client.post(
                f"{self.base_url}/mcp/messages",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "tools/call",
                    "params": {
                        "name": "search_memory",
                        "arguments": {
                            "query": query,
                            "user_id": user_id,
                            "limit": 5
                        }
                    }
                }
            )
            elapsed = time.time() - start
            return {
                "status": response.status_code,
                "elapsed": elapsed,
                "success": response.status_code == 200
            }
    
    async def get_health(self) -> Dict[str, Any]:
        """Get server health including concurrency metrics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            return response.json()


async def test_concurrent_writes(num_requests: int = 10, host: str = "localhost", port: int = 8001):
    """Test concurrent write operations"""
    print(f"\n{'='*60}")
    print(f"Test: {num_requests} Concurrent Write Operations")
    print(f"{'='*60}\n")
    
    tester = ConcurrencyTester(host, port)
    
    # Create concurrent tasks
    tasks = [
        tester.add_memory(
            user_id=f"test_user_{i % 5}",  # 5 different users
            message=f"测试消息 #{i}: 这是一个并发测试消息，用于验证服务器的并发处理能力。"
        )
        for i in range(num_requests)
    ]
    
    # Run all tasks concurrently
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time
    
    # Analyze results
    successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    failures = num_requests - successes
    
    response_times = [r["elapsed"] for r in results if isinstance(r, dict)]
    
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests per Second: {num_requests/total_time:.2f}")
    print(f"Success: {successes}/{num_requests} ({successes/num_requests*100:.1f}%)")
    print(f"Failed: {failures}")
    
    if response_times:
        print(f"\nResponse Times:")
        print(f"  Min: {min(response_times)*1000:.0f}ms")
        print(f"  Max: {max(response_times)*1000:.0f}ms")
        print(f"  Avg: {statistics.mean(response_times)*1000:.0f}ms")
        print(f"  Median: {statistics.median(response_times)*1000:.0f}ms")
    
    # Get server metrics
    health = await tester.get_health()
    print(f"\nServer Metrics:")
    print(f"  Total Requests: {health['metrics']['total_requests']}")
    print(f"  Success Rate: {health['metrics']['success_rate']}%")
    print(f"  Avg Response Time: {health['metrics']['avg_response_time_ms']:.0f}ms")
    
    return results


async def test_concurrent_reads(num_requests: int = 20, host: str = "localhost", port: int = 8001):
    """Test concurrent read operations"""
    print(f"\n{'='*60}")
    print(f"Test: {num_requests} Concurrent Read Operations")
    print(f"{'='*60}\n")
    
    tester = ConcurrencyTester(host, port)
    
    # Create concurrent tasks
    tasks = [
        tester.search_memory(
            user_id=f"test_user_{i % 5}",
            query=f"测试 并发"
        )
        for i in range(num_requests)
    ]
    
    # Run all tasks concurrently
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time
    
    # Analyze results
    successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    failures = num_requests - successes
    
    response_times = [r["elapsed"] for r in results if isinstance(r, dict)]
    
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests per Second: {num_requests/total_time:.2f}")
    print(f"Success: {successes}/{num_requests} ({successes/num_requests*100:.1f}%)")
    print(f"Failed: {failures}")
    
    if response_times:
        print(f"\nResponse Times:")
        print(f"  Min: {min(response_times)*1000:.0f}ms")
        print(f"  Max: {max(response_times)*1000:.0f}ms")
        print(f"  Avg: {statistics.mean(response_times)*1000:.0f}ms")
        print(f"  Median: {statistics.median(response_times)*1000:.0f}ms")
    
    # Get server metrics
    health = await tester.get_health()
    print(f"\nServer Metrics:")
    print(f"  Total Requests: {health['metrics']['total_requests']}")
    print(f"  Success Rate: {health['metrics']['success_rate']}%")
    print(f"  Avg Response Time: {health['metrics']['avg_response_time_ms']:.0f}ms")
    
    return results


async def test_mixed_workload(num_writes: int = 10, num_reads: int = 30, host: str = "localhost", port: int = 8001):
    """Test mixed read/write workload"""
    print(f"\n{'='*60}")
    print(f"Test: Mixed Workload ({num_writes} writes + {num_reads} reads)")
    print(f"{'='*60}\n")
    
    tester = ConcurrencyTester(host, port)
    
    # Create mixed tasks
    write_tasks = [
        tester.add_memory(
            user_id=f"test_user_{i % 5}",
            message=f"混合测试消息 #{i}"
        )
        for i in range(num_writes)
    ]
    
    read_tasks = [
        tester.search_memory(
            user_id=f"test_user_{i % 5}",
            query="测试"
        )
        for i in range(num_reads)
    ]
    
    # Mix and run all tasks concurrently
    all_tasks = write_tasks + read_tasks
    
    start_time = time.time()
    results = await asyncio.gather(*all_tasks, return_exceptions=True)
    total_time = time.time() - start_time
    
    total_requests = num_writes + num_reads
    successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests per Second: {total_requests/total_time:.2f}")
    print(f"Success Rate: {successes/total_requests*100:.1f}%")
    
    # Get final server metrics
    health = await tester.get_health()
    print(f"\nFinal Server State:")
    print(f"  Active Requests: {health['concurrency']['active_requests']}")
    print(f"  Total Processed: {health['metrics']['total_requests']}")
    print(f"  Overall Success Rate: {health['metrics']['success_rate']}%")
    
    return results


async def stress_test(duration_seconds: int = 10, host: str = "localhost", port: int = 8001):
    """Run continuous stress test for specified duration"""
    print(f"\n{'='*60}")
    print(f"Stress Test: Continuous Load for {duration_seconds}s")
    print(f"{'='*60}\n")
    
    tester = ConcurrencyTester(host, port)
    
    request_count = 0
    errors = 0
    start_time = time.time()
    end_time = start_time + duration_seconds
    
    async def make_request():
        nonlocal request_count, errors
        try:
            if request_count % 3 == 0:  # 1/3 writes, 2/3 reads
                result = await tester.add_memory(
                    user_id=f"stress_user_{request_count % 10}",
                    message=f"压力测试 #{request_count}"
                )
            else:
                result = await tester.search_memory(
                    user_id=f"stress_user_{request_count % 10}",
                    query="压力测试"
                )
            
            if not result.get("success"):
                errors += 1
            request_count += 1
        except Exception as e:
            errors += 1
    
    # Continuously send requests
    tasks = []
    while time.time() < end_time:
        # Maintain some concurrency
        if len(tasks) < 10:
            tasks.append(asyncio.create_task(make_request()))
        
        # Remove completed tasks
        tasks = [t for t in tasks if not t.done()]
        await asyncio.sleep(0.01)
    
    # Wait for remaining tasks
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    print(f"Duration: {total_time:.2f}s")
    print(f"Total Requests: {request_count}")
    print(f"Requests/Second: {request_count/total_time:.2f}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {(request_count-errors)/request_count*100:.1f}%")
    
    # Get server metrics
    health = await tester.get_health()
    print(f"\nServer Metrics:")
    print(f"  Total Requests: {health['metrics']['total_requests']}")
    print(f"  Success Rate: {health['metrics']['success_rate']}%")
    print(f"  Avg Response Time: {health['metrics']['avg_response_time_ms']:.0f}ms")


async def main(host: str = "localhost", port: int = 8001):
    """Run all concurrency tests"""
    print("\n" + "="*60)
    print("MCP Server Concurrency Tests")
    print(f"Target: http://{host}:{port}")
    print("="*60)
    
    # Test 1: Concurrent writes
    await test_concurrent_writes(num_requests=10, host=host, port=port)
    await asyncio.sleep(1)
    
    # Test 2: Concurrent reads
    await test_concurrent_reads(num_requests=20, host=host, port=port)
    await asyncio.sleep(1)
    
    # Test 3: Mixed workload
    await test_mixed_workload(num_writes=10, num_reads=30, host=host, port=port)
    await asyncio.sleep(1)
    
    # Test 4: Stress test
    await stress_test(duration_seconds=10, host=host, port=port)
    
    print("\n" + "="*60)
    print("All Tests Completed!")
    print("="*60)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test MCP server concurrency")
    parser.add_argument("--host", default="localhost", help="MCP server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8001, help="MCP server port (default: 8001)")
    
    args = parser.parse_args()
    
    asyncio.run(main(args.host, args.port))
