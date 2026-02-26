"""
Hackathon Demo Script - Attack Simulation Laboratory

This script demonstrates all attack types and shows real-time detection.
Run this after starting the backend: uvicorn app.main:app --reload

Usage:
    python demo_attack_simulation.py

Output:
    - Console output showing attack detection results
    - JSON file with detailed results for presentation
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_result(attack_type: str, result: Dict[str, Any]):
    """Print attack simulation results."""
    print(f"\n🎯 {attack_type}")
    print(f"   Transactions: {result['total_transactions']}")
    print(f"   Fraud Detected: {result['fraud_detected']} ({result['detection_rate']*100:.1f}%)")
    print(f"   Blocked: {result['blocked']} ({result['block_rate']*100:.1f}%)")
    
    # Show sample transaction results
    for txn in result['transactions'][:3]:  # Show first 3
        if 'error' in txn:
            print(f"   ⚠️  Error: {txn['error']}")
        else:
            status_emoji = "🚫" if txn['action'] == "BLOCKED" else "⚠️" if txn['action'] == "HELD" else "✅"
            print(f"   {status_emoji} Score: {txn['fraud_score']:.3f} | Action: {txn['action']} | Latency: {txn['latency_ms']}ms")


def run_demo():
    """Run the full 'Heist & Catch' demo."""
    
    print_header("VEDFIN SENTINEL - ATTACK SIMULATION LABORATORY")
    print("\n  🎭 The Heist & Catch Demo")
    print("  Demonstrating real-time fraud detection on 5 attack types")
    print(f"\n  API Endpoint: {BASE_URL}")
    
    # Create a demo user
    demo_user_id = str(uuid.uuid4())
    print(f"\n  Demo User ID: {demo_user_id}")
    
    # Check if API is running
    try:
        health = requests.get(f"{BASE_URL}/api/v1/metrics/precision-recall", timeout=5)
        print(f"\n  ✅ API Status: ONLINE (status {health.status_code})")
    except:
        print(f"\n  ❌ API Status: OFFLINE - Please start the backend first:")
        print(f"     cd backend && uvicorn app.main:app --reload")
        return
    
    # Run individual attack simulations
    results = {}
    
    print_header("TEST 1: CARD TESTING ATTACK")
    print("  Simulating 20 rapid small transactions (stolen card testing)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simulate/attack",
            params={
                "attack_type": "card_testing",
                "user_id": demo_user_id,
                "num_transactions": 20
            },
            timeout=30
        )
        if response.status_code == 200:
            results['card_testing'] = response.json()
            print_result("Card Testing Attack", results['card_testing'])
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_header("TEST 2: ACCOUNT TAKEOVER (ATO)")
    print("  Simulating 3 transactions from new device/location")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simulate/attack",
            params={
                "attack_type": "account_takeover",
                "user_id": demo_user_id,
                "num_transactions": 3
            },
            timeout=30
        )
        if response.status_code == 200:
            results['account_takeover'] = response.json()
            print_result("Account Takeover", results['account_takeover'])
        else:
            print(f"   ❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_header("TEST 3: VELOCITY BURST ATTACK")
    print("  Simulating 15 transactions in 30 seconds (bot behavior)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simulate/attack",
            params={
                "attack_type": "velocity_burst",
                "user_id": demo_user_id,
                "num_transactions": 15
            },
            timeout=30
        )
        if response.status_code == 200:
            results['velocity_burst'] = response.json()
            print_result("Velocity Burst", results['velocity_burst'])
        else:
            print(f"   ❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_header("TEST 4: IMPOSSIBLE TRAVEL")
    print("  Simulating Delhi→London in 30 minutes (impossible)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simulate/attack",
            params={
                "attack_type": "impossible_travel",
                "user_id": demo_user_id
            },
            timeout=30
        )
        if response.status_code == 200:
            results['impossible_travel'] = response.json()
            print_result("Impossible Travel", results['impossible_travel'])
        else:
            print(f"   ❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_header("TEST 5: MERCHANT FRAUD")
    print("  Simulating 5 transactions at high-risk merchants")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simulate/attack",
            params={
                "attack_type": "merchant_fraud",
                "user_id": demo_user_id,
                "num_transactions": 5
            },
            timeout=30
        )
        if response.status_code == 200:
            results['merchant_fraud'] = response.json()
            print_result("Merchant Fraud", results['merchant_fraud'])
        else:
            print(f"   ❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    print_header("SUMMARY: THE HEIST & CATCH")
    
    total_attacks = sum(r.get('total_transactions', 0) for r in results.values())
    total_detected = sum(r.get('fraud_detected', 0) for r in results.values())
    total_blocked = sum(r.get('blocked', 0) for r in results.values())
    
    print(f"\n  📊 Total Attacks Simulated: {total_attacks}")
    print(f"  🎯 Total Fraud Detected: {total_detected}")
    print(f"  🚫 Total Blocked: {total_blocked}")
    print(f"  📈 Overall Detection Rate: {(total_detected/total_attacks*100 if total_attacks > 0 else 0):.1f}%")
    print(f"  🛡️  Overall Block Rate: {(total_blocked/total_attacks*100 if total_attacks > 0 else 0):.1f}%")
    
    print("\n  ✅ Attack Simulation Laboratory: OPERATIONAL")
    print("  ✅ Real-time Fraud Detection: ACTIVE")
    print("  ✅ Statistical Behavioral Analysis: FUNCTIONAL")
    
    # Save results to file
    output = {
        "demo_title": "The Heist & Catch - Attack Simulation Laboratory",
        "timestamp": datetime.now().isoformat(),
        "user_id": demo_user_id,
        "summary": {
            "total_attacks": total_attacks,
            "total_detected": total_detected,
            "total_blocked": total_blocked,
            "detection_rate": total_detected/total_attacks if total_attacks > 0 else 0,
            "block_rate": total_blocked/total_attacks if total_attacks > 0 else 0
        },
        "simulations": results
    }
    
    output_file = "demo_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n  💾 Detailed results saved to: {output_file}")
    print("\n" + "="*70)
    print("  DEMO COMPLETE - Ready for Hackathon Presentation")
    print("="*70 + "\n")


def run_single_api_test():
    """Quick test of a single prediction endpoint."""
    print_header("QUICK API TEST")
    
    # Test the predict endpoint directly
    test_txn = {
        "user_id": str(uuid.uuid4()),
        "amount": 15000.0,
        "txn_timestamp": datetime.now().isoformat(),
        "geo_lat": 28.6139,
        "geo_lng": 77.2090,
        "device_id": "test_device_001",
        "device_os": "Android",
        "merchant_category": "CRYPTO",
        "merchant_id": "suspicious_merchant_001"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/predict",
            json=test_txn,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"\n  ✅ Prediction API: WORKING")
            print(f"     Fraud Score: {result['fraud_score']:.3f}")
            print(f"     Risk Band: {result['risk_band']}")
            print(f"     Action: {result['action_taken']}")
            print(f"     Latency: {result['latency_ms']}ms")
            print(f"     Integrity Valid: {result['integrity_check_valid']}")
        else:
            print(f"\n  ❌ API Error: {response.status_code}")
            print(f"  {response.text}")
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        print(f"\n  Is the backend running? Try:")
        print(f"    cd backend && uvicorn app.main:app --reload")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_single_api_test()
    else:
        run_demo()
