import pytest
from core.insights import classify_correlation

def test_classify_correlation_weak_high_baseline():
    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(0.2, 0.6, 50.0)
    assert "weakly aligned" in strength_text
    assert "Autopilot" in headline
    assert "massive 'Ghost Bill'" in baseline_text

def test_classify_correlation_strong_low_baseline():
    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(0.8, 0.1, 20.0)
    assert "strongly aligned" in strength_text
    assert "safely following student traffic" in headline
    assert "efficiently driven by actual student attendance" in baseline_text

def test_classify_correlation_negative_slope():
    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(0.5, 0.3, -10.0)
    assert "moderately aligned" in strength_text
    assert "negative relationship" in slope_text
    assert "noticeable 'Ghost Bill'" in baseline_text
