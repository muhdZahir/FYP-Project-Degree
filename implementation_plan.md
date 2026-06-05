# Thorough Software Testing & Robustness Plan

As a professional software tester, I have analyzed your project's codebase (`core/`, `pages/`, `main.py`). The project is well-structured using the MVC pattern and Streamlit. However, to ensure **mathematical correctness, robust functionality, and crash prevention**, we need to set up a testing suite and implement several critical bug fixes.

## User Review Required

> [!IMPORTANT]  
> I plan to introduce `pytest` as the automated testing framework for this project. This will involve creating a `tests/` directory to automatically verify math calculations and logic. Please let me know if you are okay with adding `pytest` to `requirements.txt`.

## Open Questions

> [!WARNING]  
> **Question 1:** In `pages/analysis.py` (Energy Cost Analysis), the system tries to find the "Highest", "2nd Highest", and "Lowest" months. If a user uploads data containing **only 1 or 2 months**, the app will crash with an `IndexError`. How would you like to handle this? (e.g., skip the 2nd highest calculation if data is less than 3 months?)
> 
> **Question 2:** If the uploaded data contains `Capacity = 0` or `Total Energy Cost = 0`, the system will attempt to divide by zero (e.g., in `compute_utilization` or `compute_contribution`), causing `inf` or `NaN` values and potential graph failures. I plan to add safeguards to output `0` instead. Is this acceptable?

## Proposed Changes

### Tests Setup

We will create automated test scripts to ensure your logic remains mathematically sound over time.

#### [NEW] [test_processing.py](file:///d:/Unikl/SEM 6/FYP-Project-Degree/tests/test_processing.py)
- **Math Verification:** Test `compute_utilization` and `compute_contribution` with normal data, edge cases (0 capacity, 0 total cost), and null values.
- **Helper Verification:** Test `map_week_to_month` and `normalize_month` for various formats.

#### [NEW] [test_insights.py](file:///d:/Unikl/SEM 6/FYP-Project-Degree/tests/test_insights.py)
- **Logic Verification:** Ensure that the text-generation functions (e.g., `classify_correlation`) return the expected severity texts based on `r2_score` and baseline thresholds.

#### [NEW] [test_database.py](file:///d:/Unikl/SEM 6/FYP-Project-Degree/tests/test_database.py)
- **Data Integrity:** Verify that duplicate batch insertions are caught and that `get_batch_status` accurately reflects the database state.

### Core Logic Fixes (Robustness)

#### [MODIFY] [processing.py](file:///d:/Unikl/SEM 6/FYP-Project-Degree/core/processing.py)
- Prevent **Division by Zero** in `compute_utilization`:
  ```python
  df["Utilization"] = np.where(df["Capacity"] == 0, 0, df["Actual_Occupancy"] / df["Capacity"])
  ```
- Prevent **Division by Zero** in `compute_contribution` if total energy cost is `0`.

#### [MODIFY] [insights.py](file:///d:/Unikl/SEM 6/FYP-Project-Degree/core/insights.py)
- Fix potential `IndexError` in `monthly_energy_cost_findings` when the data contains fewer than 3 months of energy data. We will add fallbacks if the 2nd highest or lowest month is the same as the highest month.

#### [MODIFY] [optimize.py](file:///d:/Unikl/SEM 6/FYP-Project-Degree/pages/optimize.py)
- Add safeguards for division by zero when calculating `Cost_Pct` and `Occ_Pct`:
  ```python
  total_energy = floor_energy['Energy_Cost'].sum()
  floor_energy['Cost_Pct'] = (floor_energy['Energy_Cost'] / total_energy * 100) if total_energy > 0 else 0
  ```

## Verification Plan

### Automated Tests
- Run `pytest` to execute the new test suite:
  ```bash
  python -m pytest tests/
  ```
- Ensure 100% pass rate for all core processing functions.

### Manual Verification
- Start the Streamlit app (`python -m streamlit run main.py`).
- Upload synthetic data files containing edge cases (e.g., 0 capacities, 1-month-only data) to verify the UI does not crash and the graphs plot gracefully.
