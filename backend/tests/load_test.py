"""
Load Test Script — Validates latency claims against the prediction endpoint.

Fires concurrent requests and reports p50/p95/p99 latency.
Usage: python tests/load_test.py [--url http://localhost:8000] [--requests 100] [--concurrency 10]
"""
import asyncio
import time
import argparse
import uuid
import json
import sys
from datetime import datetime, timezone

try:
    import httpx
except ImportError:
    print("httpx required: pip install httpx")
    sys.exit(1)


def generate_payload() -> dict:
    return {
        "user_id": str(uuid.uuid4()),
        "amount": 5000.0,
        "txn_timestamp": datetime.now(timezone.utc).isoformat(),
        "geo_lat": 28.6139,
        "geo_lng": 77.2090,
        "device_id": f"device_{uuid.uuid4().hex[:8]}",
        "device_os": "Android 14",
        "merchant_category": "E-commerce",
        "merchant_id": "merchant_001",
    }


async def send_request(client: httpx.AsyncClient, url: str) -> float:
    """Send a single prediction request, return latency in ms."""
    payload = generate_payload()
    start = time.perf_counter()
    try:
        response = await client.post(url, json=payload, timeout=10.0)
        latency = (time.perf_counter() - start) * 1000
        return latency
    except Exception as e:
        return -1  # Error marker


async def run_load_test(base_url: str, total_requests: int, concurrency: int):
    url = f"{base_url}/api/v1/predict"
    
    print(f"\n{'='*60}")
    print(f"VedFin Sentinel — Load Test")
    print(f"{'='*60}")
    print(f"Target:       {url}")
    print(f"Requests:     {total_requests}")
    print(f"Concurrency:  {concurrency}")
    print(f"{'='*60}\n")
    
    latencies = []
    errors = 0
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async with httpx.AsyncClient() as client:
        async def bounded_request():
            nonlocal errors
            async with semaphore:
                lat = await send_request(client, url)
                if lat < 0:
                    errors += 1
                else:
                    latencies.append(lat)
        
        start = time.perf_counter()
        tasks = [bounded_request() for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start
    
    if not latencies:
        print("❌ All requests failed!")
        return
    
    latencies.sort()
    n = len(latencies)
    
    p50 = latencies[int(n * 0.50)]
    p90 = latencies[int(n * 0.90)]
    p95 = latencies[int(n * 0.95)]
    p99 = latencies[min(int(n * 0.99), n - 1)]
    avg = sum(latencies) / n
    
    print(f"Results:")
    print(f"  Total Time:    {total_time:.2f}s")
    print(f"  Throughput:    {n / total_time:.1f} req/s")
    print(f"  Successes:     {n}")
    print(f"  Errors:        {errors}")
    print(f"\nLatency Distribution:")
    print(f"  Average:       {avg:.1f}ms")
    print(f"  p50:           {p50:.1f}ms")
    print(f"  p90:           {p90:.1f}ms")
    print(f"  p95:           {p95:.1f}ms  {'✅' if p95 < 340 else '❌'} (PRD target: <340ms)")
    print(f"  p99:           {p99:.1f}ms")
    print(f"  Min:           {latencies[0]:.1f}ms")
    print(f"  Max:           {latencies[-1]:.1f}ms")
    
    if p95 < 340:
        print(f"\n✅ PASS — p95 latency ({p95:.1f}ms) is below the 340ms PRD target")
    else:
        print(f"\n⚠️  WARNING — p95 latency ({p95:.1f}ms) exceeds the 340ms PRD target")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VedFin Sentinel Load Test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--requests", type=int, default=100, help="Total requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    args = parser.parse_args()
    
    asyncio.run(run_load_test(args.url, args.requests, args.concurrency))
