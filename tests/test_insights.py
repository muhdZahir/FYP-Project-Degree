import pytest
from core.insights import classify_correlation

def test_classify_correlation_weak_high_baseline():
    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(0.2, 0.6, 50.0)
    assert "weak relationship" in strength_text
    assert "Autopilot behavior detected" in headline
    assert "high level of fixed energy usage" in baseline_text

def test_classify_correlation_strong_low_baseline():
    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(0.8, 0.1, 20.0)
    assert "strong relationship" in strength_text
    assert "follows occupancy patterns" in headline
    assert "largely driven by actual occupancy" in baseline_text

def test_classify_correlation_negative_slope():
    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(0.5, 0.3, -10.0)
    assert "moderate relationship" in strength_text
    assert "negative relationship" in slope_text
    assert "noticeable baseline" in baseline_text
