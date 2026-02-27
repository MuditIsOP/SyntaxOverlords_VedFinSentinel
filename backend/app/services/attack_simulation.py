"""
Attack Simulation Laboratory

Provides realistic attack scenarios for demonstrating fraud detection capabilities:
- Card Testing Attack: Rapid small transactions to test stolen cards
- Account Takeover: Transactions from new devices/locations
- Velocity Attack: Burst of transactions in short time window
- Location Spoofing: Impossible travel patterns
- Merchant Fraud: Suspicious merchant category patterns
"""

import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import structlog

from app.schemas.predict import TransactionRequest
from app.services.fraud_scoring import process_fraud_prediction
from app.db.session import get_db_session

logger = structlog.get_logger()


class AttackSimulator:
    """
    Simulates various fraud attack patterns for testing and demo purposes.
    """
    
    @staticmethod
    def generate_card_testing_attack(
        base_user_id: UUID,
        num_transactions: int = 20,
        time_window_seconds: int = 60
    ) -> List[TransactionRequest]:
        """
        Generate card testing attack: small rapid transactions to test card validity.
        Pattern: Multiple small amounts (often $1 or round numbers) in quick succession.
        """
        now = datetime.now(timezone.utc)
        attacks = []
        
        # Common card testing amounts
        test_amounts = [1.0, 5.0, 10.0, 25.0, 50.0, 0.99, 9.99, 19.99]
        
        for i in range(num_transactions):
            # Rapid fire with slight jitter
            txn_time = now + timedelta(seconds=random.uniform(0, time_window_seconds))
            
            txn = TransactionRequest(
                user_id=base_user_id,
                amount=random.choice(test_amounts),
                txn_timestamp=txn_time,
                geo_lat=random.uniform(28.6, 28.7),  # Delhi area
                geo_lng=random.uniform(77.2, 77.3),
                device_id=f"test_device_{random.randint(1000, 9999)}",  # New device each time
                device_os="Android",
                ip_subnet=f"192.168.{random.randint(0,255)}.0/24",
                merchant_category=random.choice(["ELECTRONICS", "GIFT_CARDS", "DIGITAL_GOODS"]),
                merchant_id=f"merchant_{random.randint(1000, 9999)}",
                recipient_id=None
            )
            attacks.append(txn)
        
        return attacks
    
    @staticmethod
    def generate_account_takeover_attack(
        victim_user_id: UUID,
        num_transactions: int = 3
    ) -> List[TransactionRequest]:
        """
        Generate account takeover attack: transactions from new location/device.
        Pattern: Large transaction from completely different geography.
        """
        now = datetime.now(timezone.utc)
        attacks = []
        
        # Attack from different geography (e.g., Mumbai vs user's usual Delhi)
        attack_locations = [
            (19.0760, 72.8777),  # Mumbai
            (13.0827, 80.2707),  # Chennai
            (22.5726, 88.3639),  # Kolkata
        ]
        
        for i in range(num_transactions):
            lat, lng = random.choice(attack_locations)
            
            txn = TransactionRequest(
                user_id=victim_user_id,
                amount=random.uniform(5000, 25000),  # Large amount
                txn_timestamp=now + timedelta(minutes=i*5),
                geo_lat=lat,
                geo_lng=lng,
                device_id=f"hacked_device_{uuid4().hex[:8]}",  # New device
                device_os="iOS" if random.random() > 0.5 else "Android",
                ip_subnet=f"10.{random.randint(0,255)}.0.0/16",
                merchant_category=random.choice(["CRYPTO", "GAMBLING", "LUXURY_GOODS"]),
                merchant_id=f"suspicious_merchant_{i}",
                recipient_id=None
            )
            attacks.append(txn)
        
        return attacks
    
    @staticmethod
    def generate_velocity_burst_attack(
        user_id: UUID,
        num_transactions: int = 15,
        time_window_seconds: int = 30
    ) -> List[TransactionRequest]:
        """
        Generate velocity attack: burst of transactions in very short time.
        Pattern: Many transactions in seconds (bot/automated behavior).
        """
        now = datetime.now(timezone.utc)
        attacks = []
        
        for i in range(num_transactions):
            # Very rapid succession
            txn_time = now + timedelta(seconds=random.uniform(0, time_window_seconds))
            
            txn = TransactionRequest(
                user_id=user_id,
                amount=random.uniform(100, 2000),
                txn_timestamp=txn_time,
                geo_lat=28.6139,  # Fixed location (bot behavior)
                geo_lng=77.2090,
                device_id="automated_bot_device",
                device_os="Linux",  # Unusual for mobile banking
                ip_subnet="103.21.244.0/22",
                merchant_category=random.choice(["DIGITAL_GOODS", "GIFT_CARDS"]),
                merchant_id=f"auto_merchant_{i}",
                recipient_id=None
            )
            attacks.append(txn)
        
        return attacks
    
    @staticmethod
    def generate_impossible_travel_attack(
        user_id: UUID
    ) -> List[TransactionRequest]:
        """
        Generate impossible travel attack: transactions from distant locations too quickly.
        Pattern: Transaction in Delhi, then 1 hour later in London (impossible).
        """
        now = datetime.now(timezone.utc)
        
        # First transaction: Delhi
        txn1 = TransactionRequest(
            user_id=user_id,
            amount=1500.0,
            txn_timestamp=now,
            geo_lat=28.6139,
            geo_lng=77.2090,
            device_id="user_phone_001",
            device_os="Android",
            ip_subnet="182.76.0.0/16",
            merchant_category="RETAIL",
            merchant_id="local_store_delhi",
            recipient_id=None
        )
        
        # Second transaction: London (impossible to travel in 30 minutes)
        txn2 = TransactionRequest(
            user_id=user_id,
            amount=3000.0,
            txn_timestamp=now + timedelta(minutes=30),
            geo_lat=51.5074,
            geo_lng=-0.1278,
            device_id="user_phone_001",  # Same device
            device_os="Android",
            ip_subnet="185.60.0.0/16",  # UK IP
            merchant_category="LUXURY_GOODS",
            merchant_id="london_luxury_store",
            recipient_id=None
        )
        
        return [txn1, txn2]
    
    @staticmethod
    def generate_merchant_fraud_attack(
        user_id: UUID,
        num_transactions: int = 5
    ) -> List[TransactionRequest]:
        """
        Generate merchant fraud: suspicious category patterns.
        Pattern: User suddenly buying from high-risk merchants they never used.
        """
        now = datetime.now(timezone.utc)
        attacks = []
        
        high_risk_categories = ["CRYPTO", "GAMBLING", "PRECIOUS_METALS", "WIRE_TRANSFER"]
        
        for i in range(num_transactions):
            txn = TransactionRequest(
                user_id=user_id,
                amount=random.uniform(5000, 50000),
                txn_timestamp=now - timedelta(minutes=i*10),
                geo_lat=28.6139,
                geo_lng=77.2090,
                device_id="user_phone_001",
                device_os="Android",
                ip_subnet="182.76.0.0/16",
                merchant_category=random.choice(high_risk_categories),
                merchant_id=f"high_risk_merchant_{i}",
                recipient_id=None
            )
            attacks.append(txn)
        
        return attacks


class AttackSimulationRunner:
    """
    Runs attack simulations and reports results.
    """
    
    def __init__(self):
        self.simulator = AttackSimulator()
    
    async def run_simulation(
        self,
        attack_type: str,
        user_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a specific attack simulation and return results.
        
        Args:
            attack_type: Type of attack ('card_testing', 'account_takeover', 
                        'velocity_burst', 'impossible_travel', 'merchant_fraud')
            user_id: User ID for the attack simulation
            **kwargs: Additional parameters for the attack generator
        
        Returns:
            Dictionary with attack details and detection results
        """
        # Generate attack transactions
        if attack_type == "card_testing":
            transactions = self.simulator.generate_card_testing_attack(user_id, **kwargs)
        elif attack_type == "account_takeover":
            transactions = self.simulator.generate_account_takeover_attack(user_id, **kwargs)
        elif attack_type == "velocity_burst":
            transactions = self.simulator.generate_velocity_burst_attack(user_id, **kwargs)
        elif attack_type == "impossible_travel":
            transactions = self.simulator.generate_impossible_travel_attack(user_id)
        elif attack_type == "merchant_fraud":
            transactions = self.simulator.generate_merchant_fraud_attack(user_id, **kwargs)
        else:
            raise ValueError(f"Unknown attack type: {attack_type}")
        
        # Process each transaction
        results = []
        fraud_detected = 0
        blocked = 0
        
        async with get_db_session() as session:
            for txn in transactions:
                try:
                    # Process through fraud detection pipeline
                    result = await process_fraud_prediction(None, txn, session)
                    results.append({
                        "txn_id": str(result.txn_id),
                        "fraud_score": result.fraud_score,
                        "risk_band": result.risk_band,
                        "action": result.action_taken,
                        "latency_ms": result.latency_ms,
                        "reasons": result.reasons
                    })
                    
                    if result.risk_band in ["FRAUD", "SUSPICIOUS"]:
                        fraud_detected += 1
                    if result.action_taken == "BLOCKED":
                        blocked += 1
                        
                except Exception as e:
                    logger.error("attack_simulation_error", error=str(e))
                    results.append({"error": str(e)})
        
        return {
            "attack_type": attack_type,
            "total_transactions": len(transactions),
            "fraud_detected": fraud_detected,
            "blocked": blocked,
            "detection_rate": fraud_detected / len(transactions) if transactions else 0,
            "block_rate": blocked / len(transactions) if transactions else 0,
            "transactions": results
        }
    
    async def run_all_simulations(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Run all attack types and return summary."""
        simulations = []
        
        attack_types = [
            ("card_testing", {"num_transactions": 10}),
            ("account_takeover", {"num_transactions": 3}),
            ("velocity_burst", {"num_transactions": 10}),
            ("impossible_travel", {}),
            ("merchant_fraud", {"num_transactions": 5}),
        ]
        
        for attack_type, kwargs in attack_types:
            try:
                result = await self.run_simulation(attack_type, user_id, **kwargs)
                simulations.append(result)
                logger.info("attack_simulation_complete",
                           attack_type=attack_type,
                           detection_rate=result["detection_rate"])
            except Exception as e:
                logger.error("attack_simulation_failed",
                           attack_type=attack_type,
                           error=str(e))
        
        return simulations


# Singleton instance
attack_runner = AttackSimulationRunner()
