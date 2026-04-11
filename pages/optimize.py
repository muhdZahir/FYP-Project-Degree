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

    st.title("OPTIMIZATION")

    st.write(f"Choose the semester data batch stored in the system for prediction and optimization.")

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
                st.session_state['class_df_optimize'] = pd.DataFrame()
                st.session_state['energy_df_optimize'] = pd.DataFrame()
                st.session_state['show_insights'] = False # reset insights view when loading new data

            else:
                with st.spinner("Fetching data from SQL Engine..."):
                    # store loaded dataframes in session_state so they persist across interactions
                    st.session_state['class_df_optimize'] = db.load_from_db("Classroom", st.session_state['selected_batch'])
                    st.session_state['energy_df_optimize'] = db.load_from_db("Energy", st.session_state['selected_batch'])
                    st.session_state['show_insights'] = False # reset insights view when loading new data
            
                    st.toast(f"Loaded {len(st.session_state.get('class_df_optimize', pd.DataFrame()))} classroom records and {len(st.session_state.get('energy_df_optimize', pd.DataFrame()))} energy records.", icon="✅")
            
    class_df = st.session_state.get('class_df_optimize', pd.DataFrame())
    # Normalize classroom data
    if not class_df.empty:
        # Calculate utilization rate per room
        if (class_df["Actual_Occupancy"] == 0).any():
            class_df["Utilization"] = 0
        else:
            class_df["Utilization"] = class_df["Actual_Occupancy"] / class_df["Capacity"]
        class_df["Percent_Utilize"] = class_df["Utilization"] * 100

        # Aggregate by week if week column exists
        if "Week" in class_df.columns:
            weekly = class_df.groupby("Week")["Percent_Utilize"].mean().reset_index()
        else:
            # fallback: use row index as timeline
            weekly = class_df.groupby(class_df.index)["Percent_Utilize"].mean().reset_index()
            weekly.rename(columns={"index": "Week"}, inplace=True)

        scaler_class = MinMaxScaler()

        weekly["util_norm"] = scaler_class.fit_transform(
            weekly[["Percent_Utilize"]]
        )

        with st.expander("View Processed Weekly Classroom Utilization Data"):
            st.dataframe(weekly)

    energy_df = st.session_state.get('energy_df_optimize', pd.DataFrame())
    # Normalize energy data
    if not energy_df.empty:
        # Convert Month to number if needed
        try:
            energy_df["Month"] = pd.to_datetime(energy_df["Month"], format="%b").dt.month
        except:
            try:
                energy_df["Month"] = pd.to_datetime(energy_df["Month"], format="%B").dt.month
            except:
                pass  # already numeric
        
        monthly_cost = energy_df.groupby("Month")["Energy_Cost"].sum().reset_index()

        scaler_energy = MinMaxScaler()

        monthly_cost["cost_norm"] = scaler_energy.fit_transform(
            monthly_cost[["Energy_Cost"]]
        )
        with st.expander("View Processed Monthly Energy Cost Data"):
            st.dataframe(monthly_cost)

    if not class_df.empty or not energy_df.empty:
        if st.button(label="Generate Insights", width="stretch", icon=":material/auto_fix_high:", key="blue"):
            st.session_state['show_insights'] = True

    if st.session_state['show_insights']:
        st.subheader("Next Semester Classroom Demand Prediction")
        
        if not class_df.empty:
            X_demand = weekly["Week"].values.reshape(-1, 1)
            y_demand = weekly["util_norm"].values

            model_demand = LinearRegression()
            model_demand.fit(X_demand, y_demand)

            next_week = weekly["Week"].max() + 1
            pred_demand_norm = model_demand.predict([[next_week]])
            pred_demand = scaler_class.inverse_transform(
                np.array(pred_demand_norm).reshape(-1, 1)
            )[0][0]

            st.metric("Predicted Utilization of The Whole Next Semester", f"{pred_demand:.2f}%")

            # Plot demand trend
            weekly_plot = weekly.copy()
            weekly_plot.loc[next_week] = [next_week, np.nan, pred_demand_norm[0]]

            fig1 = px.line(
                weekly_plot,
                x="Week",
                y="util_norm",
                title="Predicted Classroom Demand Trend",
                markers=True,
                labels={"util_norm": "Normalized Utilization"}
            )
            fig1.add_scatter(
                x=[next_week],
                y=[pred_demand_norm[0]],
                mode="markers+text",
                text=["Next Semester"],
                textposition="top center"
            )

            st.plotly_chart(fig1, width='stretch')
        else:
            st.write("No classroom data available for prediction.")
        
        st.subheader("Next Month Energy Cost Prediction")
        
        if not energy_df.empty:
            X_energy = monthly_cost["Month"].values.reshape(-1, 1)
            y_energy = monthly_cost["cost_norm"].values

            model_energy = LinearRegression()
            model_energy.fit(X_energy, y_energy)

            next_month = monthly_cost["Month"].max() + 1
            pred_energy_norm = model_energy.predict([[next_month]])
            pred_energy = scaler_energy.inverse_transform(
                np.array(pred_energy_norm).reshape(-1, 1)
            )[0][0]

            st.metric("Predicted Energy Cost Next Month (RM)", f"RM {pred_energy:.2f}")

            # Plot energy trend
            monthly_plot = monthly_cost.copy()
            monthly_plot.loc[len(monthly_cost)] = [next_month, np.nan, pred_energy_norm[0]]

            fig2 = px.line(
                monthly_plot,
                x="Month",
                y="cost_norm",
                title="Predicted Energy Cost Trend",
                markers=True,
                labels={"cost_norm": "Normalized Energy Cost"}
            )
            fig2.add_scatter(
                x=[next_month],
                y=[pred_energy_norm[0]],
                mode="markers+text",
                text=["Next Month"],
                textposition="top center"
            )

            st.plotly_chart(fig2, width='stretch')
        else:
            st.write("No energy data available for prediction.")
        
        st.subheader("Optimization Recommendations")
        
        if not class_df.empty:
            avg_util = class_df['Utilization'].mean()
            if avg_util < 0.7:
                st.write("**Classroom Recommendation:** Utilization is below 70%. Consider optimizing class scheduling to increase occupancy rates, such as combining smaller classes or adjusting time slots.")
            else:
                st.write("**Classroom Recommendation:** Utilization is adequate. Maintain current scheduling practices.")
            
            # For occupancy prediction
            X_class = class_df[['Scheduled_Hours']].values
            y_class = class_df['Actual_Occupancy'].values
            if len(X_class) > 0:
                model_class = LinearRegression()
                model_class.fit(X_class, y_class)
                next_sched = class_df['Scheduled_Hours'].mean()
                pred_occ = model_class.predict([[next_sched]])[0]
                total_capacity = class_df['Capacity'].sum()
                if pred_occ < total_capacity * 0.8:
                    st.write("Predicted occupancy suggests underutilization. Recommend reviewing course enrollments and room assignments.")
        
        if not energy_df.empty:
            current_avg_cost = energy_df['Energy_Cost'].mean()
            if 'pred_energy' in locals() and pred_energy > current_avg_cost * 1.1:
                st.write("**Energy Recommendation:** Predicted cost is higher than average. Implement energy-saving measures such as LED lighting upgrades, HVAC optimization, or smart metering.")
            else:
                st.write("**Energy Recommendation:** Energy costs are stable. Continue monitoring and maintenance.")