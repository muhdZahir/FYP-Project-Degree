import streamlit as st # pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run main.py'. to close, press 'ctrl + c' at terminal
import pandas as pd # pip install pandas | pandas is use to analyze data from csv/xlsx
import numpy as np # pip install numpy |
import os
import plotly.express as px # pip install plotly | plotly is use to create interactive visualization/chart
import database as db  # Importing your database.py
# pip install -U scikit-learn
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import calendar

# for the system to read excel, install 'pip install openpyxl'

db.init_db()

# Initialize session state for persistence across reruns
if 'class_df_analysis' not in st.session_state:
    st.session_state['class_df_analysis'] = pd.DataFrame()
if 'energy_df_analysis' not in st.session_state:
    st.session_state['energy_df_analysis'] = pd.DataFrame()
if 'selected_batch' not in st.session_state:
    st.session_state['selected_batch'] = None

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

def inject_custom_css(css_file_path):
        #Injects custom CSS from a local file into the Streamlit app.
        try:
            with open(css_file_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except FileNotFoundError:
            st.error(f"Error: CSS file not found at {css_file_path}")

with st.spinner("Loading page...", show_time=True):
    # Define the relative path to your CSS file
    css_path = os.path.join("assets", "style.css")

    # Inject the CSS
    inject_custom_css(css_path)

    st.title("ANALYSIS")

    st.write(f"Choose the semester data batch stored in the system for analysis.")

    available_batches = db.get_unique_batches()

    if not available_batches:
        st.warning("No data found in database. Please upload and save files first.")
    else:
        if "selected_batch" not in st.session_state:
            st.session_state.selected_batch = None

        selected_batch = st.selectbox(
            "Select Data Batch:",
            available_batches,
            index=0,
            key="selected_batch"
        )

        if st.button("Load Data", key="load_db_btn"):
            if st.session_state["selected_batch"] is None:
                st.info("Choose a data batch and click 'Load Data' to fetch data from database.")
                st.session_state['class_df_analysis'] = pd.DataFrame()
                st.session_state['energy_df_analysis'] = pd.DataFrame()

            else:
                with st.spinner("Fetching data from SQL Engine..."):
                    # store loaded dataframes in session_state so they persist across interactions
                    st.session_state['class_df_analysis'] = db.load_from_db("Classroom", st.session_state['selected_batch'])
                    st.session_state['energy_df_analysis'] = db.load_from_db("Energy", st.session_state['selected_batch'])
            
                    st.toast(f"Loaded {len(st.session_state.get('class_df_analysis', pd.DataFrame()))} classroom records and {len(st.session_state.get('energy_df_analysis', pd.DataFrame()))} energy records.", icon="✅")
            
    class_df = st.session_state.get('class_df_analysis', pd.DataFrame())
    # Preprocessing classroom data for normalization
    if not class_df.empty:
        # Calculate utilization rate per room
        if (class_df["Actual_Occupancy"] == 0).any():
            class_df["Utilization"] = 0
        else:
            class_df["Utilization"] = class_df["Actual_Occupancy"] / class_df["Capacity"]
        class_df["Percent_Utilize"] = class_df["Utilization"] * 100

        scaler = MinMaxScaler()
        class_df['norm_Scheduled_Hours'] = class_df['Scheduled_Hours']
        class_df['norm_Utilization'] = class_df['Utilization']
        class_cols = ["norm_Scheduled_Hours","norm_Utilization"]
        class_df[class_cols] = scaler.fit_transform(class_df[class_cols])

        #st.subheader("Preprocessed Classroom Usage Data")
        #st.dataframe(class_df)

    energy_df = st.session_state.get('energy_df_analysis', pd.DataFrame())
    # Preprocessing energy data for normalization
    if not energy_df.empty:

        scaler = MinMaxScaler()
        energy_df["norm_Energy_kWh"] = energy_df["Energy_kWh"]
        energy_df["norm_Energy_Cost"] = energy_df["Energy_Cost"]
        energy_cols = ["norm_Energy_kWh","norm_Energy_Cost"]
        energy_df[energy_cols] = scaler.fit_transform(energy_df[energy_cols])

        #st.subheader("Preprocessed Energy Cost Data")
        #st.dataframe(energy_df)

    if not class_df.empty or not energy_df.empty:
        if st.button(label="Start Analyzing", width="stretch", icon=":material/analytics:", key="blue"):
            # ==========================================
            # CLASSROOM ANALYSIS
            # ==========================================
            if not class_df.empty:
                st.header("Classroom Utilization Analysis")

                with st.spinner("Analyzing data...", show_time=True):
                    # Display Average Utilization
                    avg_util = class_df["Utilization"].mean() * 100
                    st.metric("Average Classroom Utilization", f"{avg_util:.2f}%")

                    # Bar Chart: Top 5 Underutilized Rooms
                    st.subheader("Top 5 Underutilized Rooms")
                    # Group by Room to get average utilization
                    room_stats = class_df.groupby("Classroom_ID")["Percent_Utilize"].mean().reset_index()
                    # Sort lowest first
                    top_underutilized = room_stats.sort_values("Percent_Utilize", ascending=True).head(5)
                    
                    bar_fig = px.bar(
                        top_underutilized,
                        x="Classroom_ID",
                        y="Percent_Utilize",
                        color="Percent_Utilize",
                        color_continuous_scale="Reds_r", # Red = Low utilization
                        title="Rooms with Lowest Utilization Rate (%)",
                        text_auto='.1f',
                        labels={"Classroom_ID": "Classroom ID","Percent_Utilize": "Utilization (%)"}
                    )

                    # update chart
                    bar_fig.update_layout(title=dict(text="Rooms with Lowest Utilization Rate (%)",
                            font=dict(size=20),   # ← change size here
                            x=0.2                 # ← position the title
                        ),
                        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
                        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
                        coloraxis_colorbar=dict(title_font=dict(size=14), tickfont=dict(size=15)) # ← change legend (color lables) font size
                    )
                    
                    st.plotly_chart(bar_fig, width="stretch")
                    # ------------------------------------------
                    # Findings: Top 5 Underutilized Rooms (UPGRADED VARIANCE ANALYSIS)
                    # ------------------------------------------
                    st.markdown("Findings: Top 5 Underutilized Rooms")

                    with st.expander("Show details"):
                        # Data Extraction & Baseline Calculation
                        campus_avg = class_df["Percent_Utilize"].mean()
                        worst_room = top_underutilized.iloc[0]
                        second_worst = top_underutilized.iloc[1]
                        fifth_worst = top_underutilized.iloc[-1]
                        
                        # Calculate Difference (Delta) from Campus Average
                        worst_diff = worst_room['Percent_Utilize'] - campus_avg
                        second_diff = second_worst['Percent_Utilize'] - campus_avg
                        fifth_diff = fifth_worst['Percent_Utilize'] - campus_avg

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                label=f"Most Critical: Room {worst_room['Classroom_ID']}",
                                value=f"{worst_room['Percent_Utilize']:.2f}%",
                                delta=f"{worst_diff:.2f}% vs Avg",
                                delta_color="normal" # Up = Green, Down = Red (Danger)
                            )
                        with col2:
                            st.metric(
                                label=f"2nd Worst: Room {second_worst['Classroom_ID']}",
                                value=f"{second_worst['Percent_Utilize']:.2f}%",
                                delta=f"{second_diff:.2f}% vs Avg",
                                delta_color="normal"
                            )
                        with col3:
                            st.metric(
                                label=f"5th Worst: Room {fifth_worst['Classroom_ID']}",
                                value=f"{fifth_worst['Percent_Utilize']:.2f}%",
                                delta=f"{fifth_diff:.2f}% vs Avg",
                                delta_color="normal"
                            )

                        # Calculate Total Wasted Space for the Worst Room (100% - Utilized%)
                        worst_wasted_space = 100 - worst_room['Percent_Utilize']

                        st.markdown(f"""
                        **Variance Observations:**

                        The campus average utilization currently sits at **{campus_avg:.2f}%**. However, the bottom-performing rooms deviate significantly from this baseline:
                        
                        - **Room {worst_room['Classroom_ID']}** is severely underperforming, operating at **{abs(worst_diff):.2f}% below** the campus average. 
                        - This means **{worst_wasted_space:.2f}% of Room {worst_room['Classroom_ID']}'s capacity is entirely wasted** during its scheduled hours.
                        - The variance remains critical even at the 5th worst room (**Room {fifth_worst['Classroom_ID']}**), which is still **{abs(fifth_diff):.2f}% below** acceptable average levels.

                        **Actionable Insight:** The university is not just scheduling inefficiently; it is actively bleeding resources on these specific outlier rooms. Management must quarantine **Room {worst_room['Classroom_ID']}** from the UniTime/FET scheduling pool immediately and re-route its assigned classes to standard-sized rooms to instantly eliminate this **{worst_wasted_space:.2f}%** capacity wastage.
                        """)

                    # Heatmap: Floor vs Time Slot
                    st.subheader("Utilization Heatmap (Floor vs Time)")
                    # Pivot data for heatmap
                    heatmap_data = class_df.groupby(["Floor", "Time_Slot"])["Percent_Utilize"].mean().reset_index()
                    heatmap_pivot = heatmap_data.pivot(index="Floor", columns="Time_Slot", values="Percent_Utilize")
                    
                    heat_fig = px.imshow(
                        heatmap_pivot,
                        labels=dict(x="Time Slot", y="Floor", color="Utilization (%)"),
                        color_continuous_scale="RdYlGn", 
                        title="Avg Utilization Rate (%) by Floor and Time"
                    )

                    # update chart
                    heat_fig.update_layout(title=dict(text="Avg Utilization Rate (%) by Floor and Time",
                            font=dict(size=20),   # ← change size here
                            x=0.2                 # ← position the title
                        ),
                        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
                        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
                        coloraxis_colorbar=dict(title_font=dict(size=14), tickfont=dict(size=15)) # ← change legend (color lables) font (title and tick) size
                    )

                    st.plotly_chart(heat_fig, width="stretch")

                    # ------------------------------------------
                    # Findings: Utilization Heatmap
                    # ------------------------------------------
                    st.markdown("Findings: Floor vs Time Utilization")

                    with st.expander("Show details"):
                        # Data Extraction
                        peak_usage = heatmap_data.loc[heatmap_data["Percent_Utilize"].idxmax()]
                        lowest_usage = heatmap_data.loc[heatmap_data["Percent_Utilize"].idxmin()]

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("### 🔥 Peak Usage Zone")
                            st.metric("Time Slot", peak_usage["Time_Slot"])
                            st.metric("Floor Level", f"Floor {peak_usage['Floor']}")
                            st.write(f"**Utilization:** {peak_usage['Percent_Utilize']:.2f}%")

                        with col2:
                            st.markdown("### ❄️ Dead Zone (Lowest Usage)")
                            st.metric("Time Slot", lowest_usage["Time_Slot"])
                            st.metric("Floor Level", f"Floor {lowest_usage['Floor']}")
                            st.write(f"**Utilization:** {lowest_usage['Percent_Utilize']:.2f}%")

                        st.markdown(f"""
                        **Observations:**

                        The campus experiences its highest density on **{peak_usage['Floor']}** during the **{peak_usage['Time_Slot']}** slot, reaching **{peak_usage['Percent_Utilize']:.2f}%** capacity. 
                        
                        Conversely, the most inefficient scheduling occurs on **{lowest_usage['Floor']}** during **{lowest_usage['Time_Slot']}**, dropping to a 'Dead Zone' level of just **{lowest_usage['Percent_Utilize']:.2f}%**.""")

                        ##**Actionable Insight:** This indicates **Temporal Energy Leakage**. Management should investigate the classes operating during the {lowest_usage['Time_Slot']} on Floor {lowest_usage['Floor']}. Moving these isolated classes to a different floor would allow the centralized air-conditioning for Floor {lowest_usage['Floor']} to be deactivated entirely during that time.
                        ##""")

            elif class_df.empty:
                st.info(f"No classroom data available for batch {selected_batch}.")

            # ==========================================
            # ENERGY ANALYSIS
            # ==========================================
            if not energy_df.empty:
                st.header("Energy Cost Analysis")

                # Calculate total energy cost of the whole floor
                floor_energy_cost = energy_df.groupby("Floor")["Energy_Cost"].sum().reset_index()

                with st.spinner("Analyzing data...", show_time=True):
                    # Line chart: monthly energy cost per floor
                    st.subheader("Monthly Energy Cost per Floor")

                    line_fig = px.line(
                        energy_df,
                        x="Month",
                        y="Energy_Cost",
                        color="Floor",
                        labels={"Energy_Cost": "Energy Cost (RM)"},
                        title="Floor Energy Cost by Month",
                        markers=True
                    )

                    # update chart
                    line_fig.update_layout(title=dict(text="Floor Energy Cost by Month",
                            font=dict(size=20),   # ← change font size here
                            x=0.2                 # ← position the title
                        ),
                        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
                        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
                        legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16)) # ← change legend (color lables) font (title and tick) size
                    )

                    st.plotly_chart(line_fig, width="stretch")

                    # ==========================================
                    # Findings: Monthly Energy Cost per Floor
                    # ==========================================
                    st.markdown("Findings: Monthly Energy Cost per Floor")

                    with st.expander("Show details"):
                        # Total energy per month
                        monthly_energy = energy_df.groupby("Month")["Energy_Cost"].sum().reset_index()

                        # Identify highest and lowest month
                        high_month = monthly_energy.loc[monthly_energy["Energy_Cost"].idxmax()]
                        low_month = monthly_energy.loc[monthly_energy["Energy_Cost"].idxmin()]

                        # Floors in highest month
                        high_month_floors = energy_df[energy_df["Month"] == high_month["Month"]]
                        high_floor_high_month = high_month_floors.loc[high_month_floors["Energy_Cost"].idxmax()]
                        low_floor_high_month = high_month_floors.loc[high_month_floors["Energy_Cost"].idxmin()]

                        # Floors in lowest month
                        low_month_floors = energy_df[energy_df["Month"] == low_month["Month"]]
                        high_floor_low_month = low_month_floors.loc[low_month_floors["Energy_Cost"].idxmax()]
                        low_floor_low_month = low_month_floors.loc[low_month_floors["Energy_Cost"].idxmin()]

                        # Average monthly cost
                        avg_monthly_cost = monthly_energy["Energy_Cost"].mean()

                        # Display metrics
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Highest Energy Cost Month",
                                high_month["Month"],
                                f"RM {high_month['Energy_Cost']:.2f}"
                            )

                        with col2:
                            st.metric(
                                "Lowest Energy Cost Month",
                                low_month["Month"],
                                f"RM {low_month['Energy_Cost']:.2f}"
                            )

                        with col3:
                            st.metric(
                                "Average Monthly Energy Cost",
                                f"RM {avg_monthly_cost:.2f}"
                            )

                        # text findings
                        st.markdown(f"""
                        **Observations:**

                        **{high_month['Month']} recorded the highest total energy cost** of **RM {high_month['Energy_Cost']:.2f}**.

                        - The **highest contributing floor** during this month was **{high_floor_high_month['Floor']}**, with **RM {high_floor_high_month['Energy_Cost']:.2f}**.
                        - The **lowest contributing floor** was **{low_floor_high_month['Floor']}**, with **RM {low_floor_high_month['Energy_Cost']:.2f}**.

                        **{low_month['Month']} recorded the lowest total energy cost** of **RM {low_month['Energy_Cost']:.2f}**.

                        - The **highest contributing floor** during this month was **{high_floor_low_month['Floor']}**, with **RM {high_floor_low_month['Energy_Cost']:.2f}**.
                        - The **lowest contributing floor** was **{low_floor_low_month['Floor']}**, with **RM {low_floor_low_month['Energy_Cost']:.2f}**.

                        These variations indicate that energy consumption patterns differ across floors and months, suggesting opportunities
                        for improved energy management and operational optimization.
                        """)

                    # Pie chart: percentage contribution
                    st.subheader("Floor Contribution to Total Energy Cost")

                    total_energy_cost = energy_df["Energy_Cost"].sum()
                    st.metric("Total Energy Cost:", f"RM {total_energy_cost:.2f}")

                    pie_fig = px.pie(
                        floor_energy_cost,
                        names="Floor",
                        values="Energy_Cost",
                        title="Energy Cost (RM) per floor contributes to Total Energy Cost (RM)"
                    )

                    # update title font size
                    pie_fig.update_layout(title=dict(text="Energy Cost (RM) per floor contributes to Total Energy Cost (RM)",
                            font=dict(size=20),   # ← change size here
                            x=0.1                 # ← position the title
                        ),
                        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
                        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
                        legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16)) # ← change legend (color lables) font (title and tick) size
                    )

                    st.plotly_chart(pie_fig, width="stretch")
                    
                    # ==========================================
                    # Findings: Energy Cost Contribution
                    # ==========================================
                    st.markdown("Findings: Floor Contribution to Total Energy Cost")

                    with st.expander("Show details"):
                        # Calculate percentage contribution
                        floor_energy_cost["Contribution (%)"] = (
                            floor_energy_cost["Energy_Cost"] / total_energy_cost * 100
                        )

                        st.dataframe(floor_energy_cost)

                        avg_cost = floor_energy_cost["Energy_Cost"].mean()

                        # Identify dominant floor
                        dominant_floor = floor_energy_cost.loc[
                            floor_energy_cost["Contribution (%)"].idxmax()
                        ]

                        least_floor = floor_energy_cost.loc[
                            floor_energy_cost["Contribution (%)"].idxmin()
                        ]

                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric(
                                "Highest Energy Cost Contributor",
                                dominant_floor["Floor"],
                                f"{dominant_floor['Contribution (%)']:.2f}%"
                            )

                        with col2:
                            st.metric(
                                "Lowest Energy Cost Contributor",
                                least_floor["Floor"],
                                f"{least_floor['Contribution (%)']:.2f}%"
                            )

                        st.markdown(f"""
                        **Observation:**  
                        **{dominant_floor['Floor']}** contributes the highest share of energy cost, 
                        accounting for **{dominant_floor['Contribution (%)']:.2f}%** of the total energy expenditure. 
                        In contrast, **{least_floor['Floor']}** contributes the least at **{least_floor['Contribution (%)']:.2f}%**. 
                        This suggests that **{dominant_floor['Floor']}** may have higher operational demand or energy usage and 
                        **{least_floor['Floor']}** have lower operational demand or energy usage.
                        """)

            elif energy_df.empty:
                st.info(f"No energy data available for batch {selected_batch}.")

            # ==========================================
            # CORRELATION ANALYSIS
            # ==========================================
            if not class_df.empty and not energy_df.empty:
                st.header("Correlation Analysis")
                st.write("Analyzing the relationship between Total Occupancy (from Classrooms) and Total Energy Cost.")

                with st.spinner("Analyzing data...", show_time=True):
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
                    else:
                        # 2. Linear Regression for Trendline
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
                        corr_fig.update_layout(title=dict(text=title_text,
                                font=dict(size=20),
                                x=0.1
                            ),
                            xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                            yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                            legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16))
                        )

                        # Add trendline trace
                        line_data = correlation_df.sort_values("Actual_Occupancy")
                        corr_fig.add_traces(px.line(line_data, x="Actual_Occupancy", y="Predicted_Cost").data[0])
                        corr_fig.data[-1].update(line=dict(color='black', width=3, dash='dash'), name='Trendline')

                        st.plotly_chart(corr_fig, width="stretch")

                        # ==========================================
                        # 4. Findings: Correlation Analysis
                        # ==========================================
                        st.markdown("Findings: Occupancy vs Energy Cost Correlation")

                        with st.expander("Show details"):
                            # Statistical Calculations
                            r2_score = model.score(X, y)
                            corr_coef = correlation_df['Actual_Occupancy'].corr(correlation_df['Energy_Cost'])
                            slope = model.coef_[0]
                            unexplained_variance = 100 - (r2_score * 100)

                            # Metric Columns
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric(
                                    label="Correlation Coefficient (r)",
                                    value=f"{corr_coef:.2f}",
                                    help="1.0 is perfect correlation. Near 0 means no relationship."
                                )
                            with col2:
                                st.metric(
                                    label="R-Squared Score",
                                    value=f"{r2_score * 100:.1f}%",
                                    help="Percentage of energy cost explained by student occupancy."
                                )
                            with col3:
                                st.metric(
                                    label="Est. Cost per Occupant",
                                    value=f"RM {slope:.2f}",
                                    help="Estimated increase in energy bill for each additional student."
                                )

                            # Dynamic Text Findings
                            st.markdown(f"""
                            **Observations:**

                            The correlation coefficient ($r$) is **{corr_coef:.2f}**, indicating the mathematical relationship between the number of students in a building and its resulting electricity bill.
                            
                            - The $R^2$ score reveals that only **{r2_score * 100:.1f}%** of the energy cost variance is actually driven by student occupancy.
                            - Alarmingly, the remaining **{unexplained_variance:.1f}%** of the energy bill is completely unlinked to human presence—representing fixed baseline costs or massive wastage (e.g., cooling empty hallways, running HVAC in underutilized 500-seater halls).
                            - The Linear Regression trendline estimates that every additional scheduled student adds approximately **RM {slope:.2f}** to the operational energy cost.""")
                            
                            ##**Actionable Insight:** A low $R^2$ score mathematically proves the critical flaw in traditional, logistics-only schedulers like **UniTime**. The university is paying exorbitant energy bills regardless of whether the rooms are full or empty. Management must implement strict **Zone Shutdown Policies** (e.g., packing all afternoon classes onto a single floor) to force the energy cost to align closely with actual human occupancy, rather than cooling an entire empty building.
                            ##""")

            elif class_df.empty or energy_df.empty:
                if class_df.empty:
                    st.info(f"No classroom data available for batch {selected_batch}.")
                elif energy_df.empty:
                    st.info(f"No energy data available for batch {selected_batch}.")
                else:
                    st.info(f"No data available for batch {selected_batch}.")