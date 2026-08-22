import time
import requests
import json
import statistics

API_URL = "http://127.0.0.1:8000/predict"

def run_performance_test(num_requests=100):
    print(f"Starting performance test with {num_requests} sequential requests...")
    
    payload = {
        "transaction_id": "TEST_PERF_1",
        "channel": "UPI",
        "step": 1,
        "type": "TRANSFER",
        "amount": 500.0,
        "oldbalanceOrg": 1000.0,
        "oldbalanceDest": 0.0
    }
    
    latencies = []
    errors = 0
    
    # Warmup
    try:
        requests.post(API_URL, json=payload)
    except Exception:
        print("API is not running. Please start the server on port 8000.")
        return

    start_time = time.time()
    
    for i in range(num_requests):
        payload["transaction_id"] = f"TEST_PERF_{i}"
        req_start = time.time()
        try:
            resp = requests.post(API_URL, json=payload)
            if resp.status_code == 200:
                latencies.append((time.time() - req_start) * 1000) # ms
            else:
                errors += 1
        except Exception:
            errors += 1
            
    total_time = time.time() - start_time
    
    print("\n--- Performance Test Results ---")
    print(f"Total Requests: {num_requests}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Throughput: {num_requests / total_time:.2f} req/sec")
    print(f"Errors: {errors}")
    
    if latencies:
        print(f"Average Latency: {statistics.mean(latencies):.2f} ms")
        print(f"Median Latency: {statistics.median(latencies):.2f} ms")
        print(f"P95 Latency: {statistics.quantiles(latencies, n=100)[94]:.2f} ms")
        print(f"Max Latency: {max(latencies):.2f} ms")
        
if __name__ == "__main__":
    run_performance_test(200)
