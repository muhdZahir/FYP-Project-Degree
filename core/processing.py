# ==============================================================================
# LOGIK PERNIAGAAN (Business Logic / Controller)
# PENJELASAN (Untuk Supervisor):
# Fail ini mematuhi prinsip MVC (Model-View-Controller) dengan memisahkan 
# pengiraan data dari fail paparan antaramuka (View). Ini mengelakkan kod
# bercampur aduk (Spaghetti Code) dan menjadikan sistem lebih mudah diselenggara.
# ==============================================================================
# Data cleaning & aggregation
from core.imports import st, pd, np, calendar, re

def require_role(allowed_roles):
    role = st.session_state.get("user_role")

    # Not logged in
    if role is None:
        st.toast("Please log in first.", icon="⚠️", duration="long")
        st.session_state.clear() # clear all session state then rerun
        st.cache_data.clear()  # Clear cached data to ensure a fresh start on next login
        st.switch_page("pages/login.py")
        st.stop()

    # Wrong role
    if role not in allowed_roles:
        st.toast("Access denied.", icon="⚠️", duration="long")
        st.session_state.clear() # clear all session state then rerun
        st.cache_data.clear()  # Clear cached data to ensure a fresh start on next login
        st.switch_page("pages/login.py")
        st.stop()

# If floor name doesn't include "Floor", we can add a prefix to make it more readable
# Also, change the floor name in the format of float to int if possible (e.g. 1.0 to 1) to make it cleaner
def format_floor_name(floor):
    try:
        floor_num = int(float(floor))
        return f"Floor {floor_num}"
    except Exception:
        if isinstance(floor, str) and not floor.lower().startswith("floor"):
            return f"Floor {floor}"
        return floor

def map_week_to_month(week):
    try:
        week = int(week)
    except Exception:
        return None
    if week <= 4: return "1"
    elif week <= 8: return "2"
    elif week <= 12: return "3"
    elif week <= 16: return "4"
    return None

def normalize_month(val):
    # Helper: normalize various month representations to a canonical numeric-string (1-12)
    month_name_map = {m.lower(): str(i) for i, m in enumerate(calendar.month_name) if m}
    month_abbr_map = {m.lower(): str(i) for i, m in enumerate(calendar.month_abbr) if m}

    if pd.isna(val):
        return None
    # ints
    if isinstance(val, (int, np.integer)):
        return str(int(val))
    # numeric strings
    s = str(val).strip()
    if s.isdigit():
        return str(int(s))
    s_lower = s.lower()
    # full month name
    if s_lower in month_name_map:
        return month_name_map[s_lower]
    # abbreviated month name
    if s_lower in month_abbr_map:
        return month_abbr_map[s_lower]
    return s  # fallback: keep as-is


def batch_sort_key(batch_name):
    match = re.match(r"Sem\s+(\d+)\s+(\d+)", batch_name)
    if match:
        semester = int(match.group(1))
        year = int(match.group(2))
        return (year, semester)
    return (9999, 9999)  # invalid names go to end

def center_button():
    col1, col2, col3 = st.columns([0.25, 1, 0.3])
    return col2

# Calculate utilization per Room
def compute_utilization(df):
    df = df.copy()
    try:
        # Prevent division by zero when capacity is 0
        df["Utilization"] = np.where(df["Capacity"] == 0, 0, df["Actual_Occupancy"] / df["Capacity"])
        df.loc[df["Actual_Occupancy"] == 0, "Utilization"] = 0
        df["Percent_Utilize"] = df["Utilization"] * 100
        
        if "Week" in df.columns:
            weekly = df.groupby("Week")["Percent_Utilize"].mean().reset_index()
        else:
            weekly = df.groupby(df.index)["Percent_Utilize"].mean().reset_index()
            weekly.rename(columns={"index": "Week"}, inplace=True)
    except Exception as e:
        st.warning(f"Classroom Preprocessing Error: {e}")
    return df

# Calculate Difference (Delta) from Campus Average
def compute_rooms_difference(worst, second, best, avg):
    worst_diff = worst - avg
    second_diff = second - avg
    best_diff = best - avg

    return worst_diff, second_diff, best_diff

# Calculate percentage contribution
def compute_contribution(df, total):
    if total == 0:
        df["Contribution (%)"] = 0
    else:
        df["Contribution (%)"] = (df["Energy_Cost"] / total * 100)
    df.loc[df["Energy_Cost"] == 0, "Contribution (%)"] = 0
    return df

# Group by Room to get average utilization
def get_room_stats(df):
    return (
        df.groupby("Classroom_Name").agg({
            "Actual_Occupancy": "mean",
            "Capacity": "first",  # or 'mean' or 'max'
            "Percent_Utilize": "mean"
        }).reset_index()
    )

# Pivot data for heatmap
def get_heatmap_pivot(df):
    return df.pivot(index="Floor", columns="Time_Slot", values="Percent_Utilize")

# Get heatmap data
def get_heatmap_data(df):
    grouped = (
        df.groupby(["Floor", "Time_Slot"])["Percent_Utilize"]
        .mean()
        .reset_index()
    )
    return grouped

# Get total energy per month
def get_monthly_energy(df):
    return (
        df.groupby("Month")["Energy_Cost"]
        .sum()
        .reset_index()
    )

# Get total energy cost of the whole floor
def get_total_energy_cost(df):
    return (
        df.groupby("Floor")["Energy_Cost"]
        .sum()
        .reset_index()
    )

# Ensure Month column exists
def ensure_months(class_df, energy_df):
    corr_class = class_df.copy()
    corr_energy = energy_df.copy()

    # Ensure Month column exists in class data: map from Week if possible
    if "Month" not in corr_class.columns and "Week" in corr_class.columns:
        corr_class["Month"] = corr_class["Week"].apply(map_week_to_month)

    # Normalize Month values in both dataframes if present
    if "Month" in corr_class.columns:
        corr_class["Month"] = corr_class["Month"].apply(normalize_month)

    if "Month" not in corr_energy.columns and "Week" in corr_energy.columns:
        corr_energy["Month"] = corr_energy["Week"].apply(map_week_to_month)

    if "Month" in corr_energy.columns:
        corr_energy["Month"] = corr_energy["Month"].apply(normalize_month)

    return corr_class, corr_energy