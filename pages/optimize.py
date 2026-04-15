import streamlit as st # pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run main.py'. to close, press 'ctrl + c' at terminal
import pandas as pd # pip install pandas | pandas is use to analyze data from csv/xlsx
import numpy as np # pip install numpy |
import os
import plotly.express as px # pip install plotly | plotly is use to create interactive visualization/chart
import database as db  # Importing your database.py
# pip install -U scikit-learn
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

# for the system to read excel, install 'pip install openpyxl'

db.init_db()

# Initialize session state for persistence across reruns
if 'class_df_optimize' not in st.session_state:
    st.session_state['class_df_optimize'] = pd.DataFrame()
if 'energy_df_optimize' not in st.session_state:
    st.session_state['energy_df_optimize'] = pd.DataFrame()
if 'selected_batch' not in st.session_state:
    st.session_state['selected_batch'] = None
if 'show_insights' not in st.session_state:
    st.session_state['show_insights'] = False

# Initialize data containers
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

def inject_custom_css(css_file_path):
    try:
        with open(css_file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: CSS file not found at {css_file_path}")

with st.spinner("Loading page...", show_time=True):
    css_path = os.path.join("assets", "style.css")
    inject_custom_css(css_path)

    st.title("OPTIMIZATION & RECOMMENDATIONS")
    st.write("Choose the semester data batch stored in the system for predictive forecasting and heuristic audits.")

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
                st.info("Choose a data batch and click 'Load Data'.")
                st.session_state['class_df_optimize'] = pd.DataFrame()
                st.session_state['energy_df_optimize'] = pd.DataFrame()
                st.session_state['show_insights'] = False 
            else:
                with st.spinner("Fetching data from SQL Engine..."):
                    st.session_state['class_df_optimize'] = db.load_from_db("Classroom", st.session_state['selected_batch'])
                    st.session_state['energy_df_optimize'] = db.load_from_db("Energy", st.session_state['selected_batch'])
                    st.session_state['show_insights'] = False 
                    st.toast("Data Loaded Successfully.", icon="✅")
            
    class_df = st.session_state.get('class_df_optimize', pd.DataFrame())
    energy_df = st.session_state.get('energy_df_optimize', pd.DataFrame())

    # Pre-process class data
    if not class_df.empty:
        if (class_df["Actual_Occupancy"] == 0).any():
            class_df["Utilization"] = 0
        else:
            class_df["Utilization"] = class_df["Actual_Occupancy"] / class_df["Capacity"]
        class_df["Percent_Utilize"] = class_df["Utilization"] * 100

        if "Week" in class_df.columns:
            weekly = class_df.groupby("Week")["Percent_Utilize"].mean().reset_index()
        else:
            weekly = class_df.groupby(class_df.index)["Percent_Utilize"].mean().reset_index()
            weekly.rename(columns={"index": "Week"}, inplace=True)

    # Pre-process energy data
    if not energy_df.empty:
        try:
            energy_df["Month_Num"] = pd.to_datetime(energy_df["Month"], format="%b").dt.month
        except:
            try:
                energy_df["Month_Num"] = pd.to_datetime(energy_df["Month"], format="%B").dt.month
            except:
                energy_df["Month_Num"] = energy_df["Month"]
        
        monthly_cost = energy_df.groupby("Month_Num")["Energy_Cost"].sum().reset_index()

    if not class_df.empty or not energy_df.empty:
        st.divider()
        if st.button(label="Generate Optimization Audit", width="stretch", icon=":material/auto_fix_high:", key="blue"):
            st.session_state['show_insights'] = True

    # ==========================================
    # FORECASTING & HEURISTIC ENGINE
    # ==========================================
    if st.session_state['show_insights']:
        
        # ---------------------------------------------------------
        # THE 3-PILLAR PREDICTIONS
        # ---------------------------------------------------------
        st.header("Executive Forecasts")
        st.write("Predictive modeling for upcoming operational cycles.")
        
        col1, col2, col3 = st.columns(3)
        
        # Prediction 1: Demand
        pred_demand = 0
        if not class_df.empty:
            X_demand = weekly["Week"].values.reshape(-1, 1)
            y_demand = weekly["Percent_Utilize"].values
            model_demand = LinearRegression().fit(X_demand, y_demand)
            next_week = weekly["Week"].max() + 1
            pred_demand = model_demand.predict([[next_week]])[0]
            
            with col1:
                st.metric(label="Next Semester Est. Demand", value=f"{pred_demand:.1f}%", help="Predicted average classroom utilization for the upcoming cycle.")
        
        # Prediction 2: Energy
        pred_energy = 0
        avg_monthly_cost = 0
        if not energy_df.empty:
            X_energy = monthly_cost["Month_Num"].values.reshape(-1, 1)
            y_energy = monthly_cost["Energy_Cost"].values
            model_energy = LinearRegression().fit(X_energy, y_energy)
            next_month = monthly_cost["Month_Num"].max() + 1
            pred_energy = model_energy.predict([[next_month]])[0]
            avg_monthly_cost = energy_df["Energy_Cost"].mean()
            
            with col2:
                st.metric(label="Next Month Est. Energy Cost", value=f"RM {pred_energy:.2f}", help="Forecasted utility bill based on current trajectory.")
                
        # Prediction 3: The Cost of Inaction (Wastage)
        if not class_df.empty and not energy_df.empty:
            # Safely estimate R-Squared variance. Using a safe fallback if merging fails.
            try:
                occ_agg = class_df.groupby("Month")["Actual_Occupancy"].sum().reset_index()
                eng_agg = energy_df.groupby("Month")["Energy_Cost"].sum().reset_index()
                merged = pd.merge(occ_agg, eng_agg, on="Month", how="inner")
                if len(merged) > 1:
                    r2 = LinearRegression().fit(merged[["Actual_Occupancy"]], merged["Energy_Cost"]).score(merged[["Actual_Occupancy"]], merged["Energy_Cost"])
                    wastage_factor = 1.0 - r2
                else:
                    wastage_factor = 0.40 # Fallback 40% if insufficient overlapping data
            except:
                wastage_factor = 0.40
            
            # Ensure wastage isn't negative
            wastage_factor = max(0.1, wastage_factor)
            projected_6mo_waste = (avg_monthly_cost * wastage_factor) * 6
            
            with col3:
                st.metric(label="Projected 6-Month Wastage", value=f"RM {projected_6mo_waste:.2f}", delta="-High Risk", delta_color="inverse", help="Estimated financial loss over 6 months if spatial inefficiencies are not resolved.")

        # Visualizing the Trends
        st.write("")
        chart_col1, chart_col2 = st.columns(2)
        
        if not class_df.empty:
            with chart_col1:
                weekly_plot = weekly.copy()
                weekly_plot.loc[len(weekly_plot)] = [next_week, pred_demand]
                fig1 = px.line(weekly_plot, x="Week", y="Percent_Utilize", title="Classroom Demand Trend", markers=True)
                fig1.add_scatter(x=[next_week], y=[pred_demand], mode="markers+text", text=["Prediction"], textposition="top center", name="Forecast")
                st.plotly_chart(fig1, use_container_width=True)
                
        if not energy_df.empty:
            with chart_col2:
                monthly_plot = monthly_cost.copy()
                monthly_plot.loc[len(monthly_plot)] = [next_month, pred_energy]
                fig2 = px.line(monthly_plot, x="Month_Num", y="Energy_Cost", title="Energy Cost Trend", markers=True)
                fig2.add_scatter(x=[next_month], y=[pred_energy], mode="markers+text", text=["Prediction"], textposition="top center", name="Forecast")
                st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # ---------------------------------------------------------
        # TIERED HEURISTIC OPTIMIZATION ENGINE
        # ---------------------------------------------------------
        # Tier 1: Spatial Optimization (Room Sizing) focuses on identifying underutilized rooms and recommending class relocations to improve space efficiency.
        # Tier 2: Temporal Optimization (Zone Consolidation) identifies time slots and floors with low activity, suggesting schedule adjustments to consolidate usage and reduce energy waste.
        # Tier 3: Financial Alignment Audit cross-references energy costs with occupancy to detect floors

        st.header("Strategic Optimization Directives")
        st.write("The URO heuristic engine has audited the schedule and identified the following operational leaks requiring immediate action:")

        # TIER 1: SPATIAL OPTIMIZATION
        if not class_df.empty:
            st.subheader("Tier 1: Spatial Optimization (Room Sizing)")
            room_avg = class_df.groupby('Classroom_ID')['Percent_Utilize'].mean().reset_index()
            campus_mean = room_avg['Percent_Utilize'].mean()
            campus_std = room_avg['Percent_Utilize'].std()
            critical_threshold = campus_mean - (campus_std * 0.5)
            ghost_rooms = room_avg[room_avg['Percent_Utilize'] < critical_threshold]
            
            if not ghost_rooms.empty:
                worst_room = ghost_rooms.sort_values(by='Percent_Utilize').iloc[0]
                st.error(f"""
                🚨 **THE BOTTOM LINE:** You are using massive rooms for tiny classes. **Room {worst_room['Classroom_ID']}** is operating at only **{worst_room['Percent_Utilize']:.1f}% capacity**, drastically below the campus standard. We are paying full electricity to cool empty air.
                * **The Fix:** Move the classes currently assigned to Room {worst_room['Classroom_ID']} into a smaller, appropriately sized venue.
                """)
                with st.expander("View Tier 1 Technical Details"):
                    st.write(f"**Engine Parameters:** Campus Mean = {campus_mean:.1f}%. Safe Threshold = {critical_threshold:.1f}%.")
                    st.dataframe(ghost_rooms.sort_values(by='Percent_Utilize').style.format({'Percent_Utilize': '{:.2f}%'}))
            else:
                st.success("✅ **Spatial Efficiency:** No critical room sizing violations detected. Classes are appropriately matched to room capacities.")

        # TIER 2: TEMPORAL OPTIMIZATION
        if not class_df.empty:
            st.subheader("Tier 2: Temporal Optimization (Zone Consolidation)")
            time_floor = class_df.groupby(['Floor', 'Time_Slot']).size().reset_index(name='Active_Classes')
            ghost_slots = time_floor[time_floor['Active_Classes'] <= 2]
            
            if not ghost_slots.empty:
                worst_slot = ghost_slots.sort_values(by='Active_Classes').iloc[0]
                st.warning(f"""
                ⚠️ **THE BOTTOM LINE:** The timetable is scattered. During **{worst_slot['Time_Slot']}**, **Floor {worst_slot['Floor']}** only has **{worst_slot['Active_Classes']} active class(es)** running. Central air-conditioning is running for the entire floor for a handful of students.
                * **The Fix:** Reschedule these isolated classes to a busier floor. Instruct Facility Management to shut down HVAC for Floor {worst_slot['Floor']} during the {worst_slot['Time_Slot']} block.
                """)
                with st.expander("View Tier 2 Technical Details"):
                    st.write("**Detected Ghost Floors (Consolidation Required):**")
                    st.dataframe(ghost_slots.sort_values(by=['Active_Classes', 'Time_Slot']))
            else:
                st.success("✅ **Temporal Efficiency:** No isolated classes detected. Schedule is well-consolidated.")

        # TIER 3: FINANCIAL ALIGNMENT
        if not class_df.empty and not energy_df.empty:
            st.subheader("Tier 3: Energy-Cost Alignment Audit")
            floor_energy = energy_df.groupby('Floor')['Energy_Cost'].sum().reset_index()
            floor_energy['Cost_Pct'] = (floor_energy['Energy_Cost'] / floor_energy['Energy_Cost'].sum()) * 100
            
            floor_occ = class_df.groupby('Floor')['Actual_Occupancy'].sum().reset_index()
            floor_occ['Occ_Pct'] = (floor_occ['Actual_Occupancy'] / floor_occ['Actual_Occupancy'].sum()) * 100
            
            tier3_df = pd.merge(floor_energy, floor_occ, on='Floor', how='inner')
            tier3_df['Disconnect'] = tier3_df['Cost_Pct'] - tier3_df['Occ_Pct']
            leaking_floors = tier3_df[tier3_df['Disconnect'] > 15.0]
            
            if not leaking_floors.empty:
                worst_leak = leaking_floors.sort_values(by='Disconnect', ascending=False).iloc[0]
                st.error(f"""
                🚨 **THE BOTTOM LINE (CRITICAL LEAK):** Massive financial disconnect on **Floor {int(worst_leak['Floor'])}**. It burns **{worst_leak['Cost_Pct']:.1f}% of your total electricity budget**, but holds only **{worst_leak['Occ_Pct']:.1f}% of the students**. 
                * **The Fix:** Immediate physical audit required. This indicates broken AC thermostats, lights left on, or unauthorized power usage.
                """)
                with st.expander("View Tier 3 Technical Details"):
                    st.dataframe(tier3_df[['Floor', 'Cost_Pct', 'Occ_Pct', 'Disconnect']].sort_values(by='Disconnect', ascending=False).style.format({
                        'Cost_Pct': '{:.1f}%', 'Occ_Pct': '{:.1f}%', 'Disconnect': '+{:.1f}%'
                    }))
            else:
                st.success("✅ **Financial Alignment:** Energy expenditure is proportional to student occupancy across all floors.")