"""Scoring utilities for program analysis."""

from datetime import datetime
from typing import Tuple

from ywh_program_selector.config import DATE_FORMAT
from ywh_program_selector.display import format_number, green, orange, red


def get_date_from(timestamp: float) -> float:
    """Get age in days from a timestamp."""
    import time
    return (time.time() - timestamp) / (24 * 3600)


def score_and_colorize(
    value: float,
    threshold_1: float,
    threshold_2: float,
    points_high: int = 3,
    points_mid: int = 2,
    points_low: int = 1,
    reverse: bool = False
) -> Tuple[int, str]:
    """
    Score a value based on thresholds and return colorized string.
    
    Args:
        value: The value to score
        threshold_1: Lower threshold (green if value <= this when not reversed)
        threshold_2: Upper threshold (orange if value <= this when not reversed)
        points_high: Points for best score
        points_mid: Points for medium score  
        points_low: Points for worst score
        reverse: If True, higher values are better (red→green instead of green→red)
    
    Returns:
        Tuple of (points earned, colorized value string)
    """
    formatted = format_number(value) if isinstance(value, float) else str(value)
    
    if reverse:
        # Higher values are better
        if value >= threshold_2:
            return points_high, green(formatted)
        elif value >= threshold_1:
            return points_mid, orange(formatted)
        return points_low, red(formatted)
    else:
        # Lower values are better (default)
        if value <= threshold_1:
            return points_high, green(formatted)
        elif value <= threshold_2:
            return points_mid, orange(formatted)
        return points_low, red(formatted)


def score_date(
    date: datetime,
    threshold_1: float,
    threshold_2: float,
    points_high: int = 3,
    points_mid: int = 2,
    points_low: int = 1,
    fresh_is_good: bool = True
) -> Tuple[int, str, float]:
    """
    Score a date based on age thresholds.
    
    Args:
        date: The datetime to score
        threshold_1: Age in days for best score
        threshold_2: Age in days for medium score
        points_high/mid/low: Points for each tier
        fresh_is_good: If True, recent dates score higher
    
    Returns:
        Tuple of (points, colorized date string, age in days)
    """
    age = get_date_from(date.timestamp())
    formatted = date.strftime(DATE_FORMAT)
    
    if fresh_is_good:
        if age <= threshold_1:
            return points_high, green(formatted), age
        elif age <= threshold_2:
            return points_mid, orange(formatted), age
        return points_low, red(formatted), age
    else:
        # Old dates are good (e.g., last hacktivity)
        if age <= threshold_1:
            return points_low, red(formatted), age
        elif age <= threshold_2:
            return points_mid, orange(formatted), age
        return points_high, green(formatted), age
