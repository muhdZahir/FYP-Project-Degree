import pytest
import pandas as pd
import numpy as np
from core.processing import compute_utilization, compute_contribution, map_week_to_month, normalize_month

def test_compute_utilization_normal():
    data = {"Capacity": [100, 50], "Actual_Occupancy": [50, 25]}
    df = pd.DataFrame(data)
    result = compute_utilization(df)
    assert result["Utilization"].iloc[0] == 0.5
    assert result["Utilization"].iloc[1] == 0.5
    assert result["Percent_Utilize"].iloc[0] == 50.0

def test_compute_utilization_zero_capacity():
    data = {"Capacity": [0, 50], "Actual_Occupancy": [0, 25]}
    df = pd.DataFrame(data)
    result = compute_utilization(df)
    # Utilization should safely be 0 where capacity is 0
    assert result["Utilization"].iloc[0] == 0
    assert result["Percent_Utilize"].iloc[0] == 0

def test_compute_utilization_zero_occupancy():
    data = {"Capacity": [100, 50], "Actual_Occupancy": [0, 25]}
    df = pd.DataFrame(data)
    result = compute_utilization(df)
    assert result["Utilization"].iloc[0] == 0

def test_compute_contribution_normal():
    data = {"Energy_Cost": [100, 300]}
    df = pd.DataFrame(data)
    total = 400
    result = compute_contribution(df, total)
    assert result["Contribution (%)"].iloc[0] == 25.0
    assert result["Contribution (%)"].iloc[1] == 75.0

def test_compute_contribution_zero_total():
    data = {"Energy_Cost": [0, 0]}
    df = pd.DataFrame(data)
    total = 0
    result = compute_contribution(df, total)
    assert result["Contribution (%)"].iloc[0] == 0.0

def test_map_week_to_month():
    assert map_week_to_month(1) == "1"
    assert map_week_to_month(4) == "1"
    assert map_week_to_month(5) == "2"
    assert map_week_to_month(16) == "4"
    assert map_week_to_month("invalid") is None

def test_normalize_month():
    assert normalize_month(1) == "1"
    assert normalize_month("1") == "1"
    assert normalize_month("January") == "1"
    assert normalize_month("jan") == "1"
    assert normalize_month(pd.NA) is None
