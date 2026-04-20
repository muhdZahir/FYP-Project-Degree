import streamlit as st # to open streamlit, run 'python -m streamlit run try.py' | to close, ctrl + c
import pandas as pd
import numpy as np
import os
import calendar
import plotly.express as px
from sklearn.linear_model import LinearRegression

st.title("University Resource Optimization")

uploaded_files = st.file_uploader(
    "Upload your files here",
    accept_multiple_files=True
)

if uploaded_files:
    st.write("Uploaded Files:")

    # Required columns for each dataset
    class_col = ["Classroom_ID", "Floor", "Capacity", "Actual_Occupancy", "Day", "Time_Slot", "Week"]
    energy_col = ["Floor", "Month", "Energy_kWh", "Energy_Cost"]

    def check_columns(df, required_cols):
        return [c for c in required_cols if c not in df.columns]

    for file in uploaded_files:
        st.write(f"- {file.name}")

        # Get the file extension
        file_extension = os.path.splitext(file.name)[1]
        
        df = None
        if file.type == "text/csv": # Processing for CSV file
            df = pd.read_csv(file)
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": # Processing for Excel file
            df = pd.read_excel(file)
        else:
            # Fallback based on filename extension when MIME type isn't present
            fname = file.name.lower()
            if fname.endswith(".csv"):
                df = pd.read_csv(file)
            elif fname.endswith(".xls") or fname.endswith(".xlsx"):
                df = pd.read_excel(file)

        if df is None:
            st.error(f"Error: Unsupported file type. Please upload a .csv or .xlsx file. You uploaded a {file_extension} file.")
            continue

        # ---- Detect file type using column pattern ----
        missing_class = check_columns(df, class_col)
        missing_energy = check_columns(df, energy_col)

        if "classroom" in file.name.lower(): #for table classroom
            missing_class = check_columns(df, class_col)
            if missing_class:
                st.error(f"Classroom file is missing column: {missing_class}. Please ensure the file contains all of the required column.")
            else:
                class_df = df
        elif "energy" in file.name.lower(): # for table energy
            missing_energy = check_columns(df, energy_col)
            if missing_energy:
                st.error(f"Energy file is missing column: {missing_energy}. Please ensure the file contains all of the required column.")
            else:
                energy_df = df
        else:
            st.error("File is missing 'classroom' or 'energy' text. Please ensure the file name is correct.")

    # 1. Prepare Data: Map Weeks to Months to align datasets
    # Logic: Weeks 1-4 = Month 1, 5-8 = Month 2, 9-12 = Month 3, 13-16 = Month 4
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

    # Helper: normalize various month representations to a canonical numeric-string (1-12)
    month_name_map = {m.lower(): str(i) for i, m in enumerate(calendar.month_name) if m}
    month_abbr_map = {m.lower(): str(i) for i, m in enumerate(calendar.month_abbr) if m}

    def normalize_month(val):
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

    # Create working copies
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

    # Classroom side
    class_grouped = corr_class.groupby(["Floor", "Month"]).agg({
        "Actual_Occupancy": "sum",
        "Scheduled_Hours": "sum",
        "Capacity": "sum"
    }).reset_index()

    class_grouped["Usage"] = (
        class_grouped["Actual_Occupancy"] * class_grouped["Scheduled_Hours"] / (class_grouped["Capacity"] * class_grouped["Scheduled_Hours"].replace(0, np.nan))
    )

    # Energy side
    energy_grouped = corr_energy.groupby(["Floor", "Month"]).agg({
        "Energy_Cost": "sum"
    }).reset_index()

    # Merge
    corr_df = pd.merge(class_grouped, energy_grouped, on=["Floor", "Month"])

    corr = corr_df["Usage"].corr(corr_df["Energy_Cost"])
    st.write(f"Correlation: {corr:.2f}")

    X = corr_df["Usage"].values.reshape(-1, 1)
    y = corr_df["Energy_Cost"].values

    model = LinearRegression()
    model.fit(X, y)
    corr_df["Predicted"] = model.predict(X)

    fig2 = px.scatter(
        corr_df,
        x="Usage",
        y="Energy_Cost",
        color="Floor",
        title="Utilization × Scheduled Hours vs Energy Consumption",
    )

    # Add trendline trace
    line = corr_df.sort_values("Usage")
    fig2.add_traces(px.line(line, x="Usage", y="Predicted").data[0])
    fig2.data[-1].update(line=dict(color='black', width=3, dash='dash'), name='Trendline')

    st.plotly_chart(fig2, width="stretch")

    st.divider()
    # At this point we attempt to aggregate and merge. Preferred: by Floor+Month
    grouped_occupancy = corr_class.groupby([col for col in ["Floor", "Month"] if col in corr_class.columns])["Actual_Occupancy"].sum().reset_index()
    grouped_energy = corr_energy.groupby([col for col in ["Floor", "Month"] if col in corr_energy.columns])["Energy_Cost"].sum().reset_index()

    # Try merge by Floor+Month if both have Month and Floor
    if set(["Floor", "Month"]).issubset(grouped_occupancy.columns) and set(["Floor", "Month"]).issubset(grouped_energy.columns):
        correlation_df = pd.merge(grouped_occupancy, grouped_energy, on=["Floor", "Month"], how="inner")
    else:
        correlation_df = pd.DataFrame()

    # Fallback: if no Floor+Month overlap, try aggregating by Month only (sum across floors)
    if correlation_df.empty:
        if "Month" in grouped_occupancy.columns and "Month" in grouped_energy.columns:
            occ_total = grouped_occupancy.groupby("Month")["Actual_Occupancy"].sum().reset_index()
            energy_total = grouped_energy.groupby("Month")["Energy_Cost"].sum().reset_index()
            correlation_df = pd.merge(occ_total, energy_total, on="Month", how="inner")
        else:
            correlation_df = pd.DataFrame()

    # If still empty, show helpful diagnostics
    if correlation_df.empty:
        occ_months = sorted(list(set(corr_class["Month"].dropna().astype(str).unique()))) if "Month" in corr_class.columns else []
        eng_months = sorted(list(set(corr_energy["Month"].dropna().astype(str).unique()))) if "Month" in corr_energy.columns else []
        st.warning("Insufficient overlapping data (Months) to plot correlation.")
        st.info(f"Classroom months found: {occ_months}")
        st.info(f"Energy months found: {eng_months}")
        st.write("Suggestion: Ensure both files contain a compatible `Month` column (numeric 1-12, month name, or derived from `Week`) covering at least one common month.")
    elif len(correlation_df) < 2:
        st.warning("Not enough data points to plot correlation (need at least 2).")
        st.write(f"Data points found: {len(correlation_df)}. Please ensure both datasets have overlapping months with valid occupancy and energy cost values.")
    else:
        # 2. Linear Regression for Trendline
        # We will fit a simple linear regression model to the data to get the trendline.
        # This will help us understand the overall relationship between occupancy and energy cost.
        X = correlation_df["Actual_Occupancy"].values.reshape(-1, 1)
        y = correlation_df["Energy_Cost"].values

        model = LinearRegression()
        model.fit(X, y)
        correlation_df["Predicted_Cost"] = model.predict(X)

        # 3. Plot Scatter with Trendline
        if "Floor" in correlation_df.columns:
            color_arg = "Floor"
            title_text = "Correlation: Occupancy vs Energy Cost (Monthly per Floor)"
        else:
            color_arg = None
            title_text = "Correlation: Occupancy vs Energy Cost (Monthly)"

        corr_fig = px.scatter(
            correlation_df,
            x="Actual_Occupancy",
            y="Energy_Cost",
            color=color_arg,
            size="Energy_Cost",
            title=title_text,
            labels={"Actual_Occupancy": "Total Occupancy", "Energy_Cost": "Total Cost (RM)"},
            hover_data=[c for c in ["Month", "Floor"] if c in correlation_df.columns]
        )

        # update title font size
        corr_fig.update_layout(title=dict(
                font=dict(size=20),   # ← change size here
                x=0.2                # ← position the title
            ),
            xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
            yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
            legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16)) # ← change legend (color lables) font (title and tick) size
        )

        # Add trendline trace
        line_data = correlation_df.sort_values("Actual_Occupancy")
        corr_fig.add_traces(px.line(line_data, x="Actual_Occupancy", y="Predicted_Cost").data[0])
        corr_fig.data[-1].update(line=dict(color='black', width=3, dash='dash'), name='Trendline')

        st.plotly_chart(corr_fig, width="stretch")

        st.markdown("Findings: Occupancy vs Energy Cost Correlation")
        with st.expander("Show details"):
            # Statistical Calculations
            r2_score = model.score(X, y)
            corr_coef = correlation_df['Actual_Occupancy'].corr(correlation_df['Energy_Cost'])
            slope = model.coef_[0]
            # Added y-intercept to calculate the Base Autopilot Cost at 0 students
            y_intercept = model.intercept_
            unexplained_variance = 100 - (r2_score * 100)

            # Metric Columns
            # Changed 4 columns to a 2-column layout to create a spacious 2x2 grid
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Correlation Coefficient (r)",
                    value=f"{corr_coef:.2f}",
                    help="1.0 is perfect correlation. Near 0 means no relationship."
                )
                # Stacked the 3rd metric inside the 1st column
                st.metric(
                    label="Est. Cost per Occupant",
                    value=f"RM {slope:,.2f}",
                    help="Estimated increase in energy bill for each additional student."
                )
            with col2:
                st.metric(
                    label="R-Squared Score",
                    value=f"{r2_score * 100:.1f}%",
                    help="Percentage of energy cost explained by student occupancy."
                )
                # Stacked the 4th metric inside the 2nd column
                st.metric(
                    label="Base Cost (0 Students)",
                    value=f"RM {y_intercept:,.2f}",
                    help="The 'Autopilot Cost'. The estimated electricity bill even if the building is completely empty."
                )