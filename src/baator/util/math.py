def clamp(value: int, low: int, high: int) -> int:
    """Clamp a numeric value between low and high inclusive."""
    return max(low, min(value, high))
