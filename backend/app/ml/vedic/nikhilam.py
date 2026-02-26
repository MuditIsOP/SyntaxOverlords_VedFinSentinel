"""
Nikhilam Threshold Calibrator — Vedic Near-Base Arithmetic

Implements the "Nikhilam Navatashcaramam Dashatah" (All from 9, Last from 10)
sutra for fast multiplication of numbers near powers of 10.

HONEST NOTE (Issue #3): In Python, this is a PEDAGOGICAL DEMONSTRATION of an
elegant algorithm from Indian mathematical heritage. For small integers,
native Python multiplication (a * b) is faster because the Vedic method
involves math.log10, round, and multiple operations. The value here is in
ALGORITHMIC DIVERSITY and CULTURAL SIGNIFICANCE — demonstrating an alternative
computational approach, not a speed improvement.

In the fraud detection pipeline, this is used to compute threshold = baseline × risk_factor
where transaction amounts cluster near round numbers (₹100, ₹500, ₹1000, ₹10000).
The mathematical result is identical to standard multiplication.
"""
import math
import time


def find_nearest_base(n: int) -> int:
    """Find the nearest power of 10 to the given number."""
    if n <= 0:
        return 10
    power = round(math.log10(max(n, 1)))
    return int(10 ** max(power, 1))


def nikhilam_multiply(a: int, b: int) -> int:
    """
    Multiply two numbers using the Nikhilam sutra.
    
    For numbers near a base (power of 10), the algorithm works as:
    1. Find the nearest base B
    2. Compute deviations: d_a = a - B, d_b = b - B
    3. Cross-add: (a + d_b) or equivalently (b + d_a) → gives left part
    4. Multiply deviations: d_a * d_b → gives right part
    5. Result = left_part * B + right_part
    
    Example: 97 × 96 (base=100)
      d_a = -3, d_b = -4
      left = 97 + (-4) = 93
      right = (-3) * (-4) = 12
      result = 93 * 100 + 12 = 9312  ✓ (97 × 96 = 9312)
    """
    base = find_nearest_base(max(abs(a), abs(b)))

    d_a = a - base
    d_b = b - base

    # Cross-addition (either works due to symmetry)
    left_part = a + d_b  # same as b + d_a

    # Deviation product
    right_part = d_a * d_b

    # Combine
    result = left_part * base + right_part
    return result


def nikhilam_threshold(score: float, risk_factor: float) -> float:
    """
    Compute a dynamic fraud threshold using the Nikhilam sutra.
    
    The threshold represents how sensitive the system should be for this user.
    Higher risk users get lower thresholds (more sensitive detection).
    
    Using Nikhilam: threshold = nikhilam(score_int, risk_int) / normalizer
    """
    if score <= 0:
        return min(1.0, risk_factor * 0.85)

    # Scale to near-base integers for Nikhilam advantage
    # e.g., score=0.72, risk=1.5 → score_int=72, risk_int=150 → near base 100
    score_int = max(1, int(score * 100))
    risk_int = max(1, int(risk_factor * 100))

    # Compute product using Nikhilam
    product = nikhilam_multiply(score_int, risk_int)

    # Normalize back to 0-1 threshold scale
    # Higher product → higher threshold (less sensitive) for low-risk users
    # Lower product → lower threshold (more sensitive) for high-risk users
    raw_threshold = product / 10000.0  # Undo the ×100 ×100 scaling

    # Invert: high risk_factor should LOWER the threshold
    threshold = max(0.001, min(0.999, 0.85 / max(raw_threshold, 0.01)))
    return threshold


def standard_multiply(a: int, b: int) -> int:
    """Standard Python multiplication for benchmark comparison."""
    return a * b


def benchmark_nikhilam_vs_standard(score: float, risk_factor: float) -> dict:
    """
    Fair benchmark: runs both Nikhilam and standard multiplication N times
    and reports average timings.
    
    Uses a large iteration count to get measurable differences above
    timer noise floor.
    """
    ITERATIONS = 500
    score_int = max(1, int(score * 100))
    risk_int = max(1, int(risk_factor * 100))

    # Warm up both paths
    _ = nikhilam_multiply(score_int, risk_int)
    _ = standard_multiply(score_int, risk_int)

    # Benchmark standard multiplication
    start_std = time.perf_counter_ns()
    for _ in range(ITERATIONS):
        std_result = standard_multiply(score_int, risk_int)
    end_std = time.perf_counter_ns()

    # Benchmark Nikhilam multiplication
    start_nik = time.perf_counter_ns()
    for _ in range(ITERATIONS):
        nik_result = nikhilam_multiply(score_int, risk_int)
    end_nik = time.perf_counter_ns()

    time_std = (end_std - start_std) / ITERATIONS
    time_nik = (end_nik - start_nik) / ITERATIONS

    # Nikhilam threshold computation
    nik_thresh = nikhilam_threshold(score, risk_factor)

    try:
        speedup = float(time_std) / float(time_nik) if time_nik > 0 else 1.0
    except ZeroDivisionError:
        speedup = 1.0

    return {
        "nikhilam_time_ns": time_nik,
        "standard_time_ns": time_std,
        "speedup_multiplier": round(speedup, 3),
        "nikhilam_result": nik_thresh,
        "iterations": ITERATIONS,
        "nikhilam_product": nik_result,
        "standard_product": std_result,
        "products_match": nik_result == std_result
    }
