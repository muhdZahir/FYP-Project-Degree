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

                    # Pie chart: percentage contribution
                    st.subheader("Floor Contribution to Total Energy Cost")

                    total_energy_cost = energy_df["Energy_Cost"].sum()
                    st.metric("Total Energy Cost: RM", f"{total_energy_cost:.2f}")

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
                    # Logic: Weeks 1-4 = First Month, 5-8 = Second Month, 9-12 = Third Month, 13-16 = Fourth Month
                    def map_week_to_month(week):
                        if week <= 4: return "1"
                        elif week <= 8: return "2"
                        elif week <= 12: return "3"
                        elif week <= 16: return "4"
                        return "Other"

                    # Create working copies
                    corr_class = class_df.copy()
                    corr_energy = energy_df.copy()

                    if "Week" in corr_class.columns:
                        corr_class["Month"] = corr_class["Week"].apply(map_week_to_month)
                
                        # Aggregate Occupancy by Floor and Month
                        grouped_occupancy = corr_class.groupby(["Floor", "Month"])["Actual_Occupancy"].sum().reset_index()
                
                        # Aggregate Energy by Floor and Month (handling potential duplicates)
                        grouped_energy = corr_energy.groupby(["Floor", "Month"])["Energy_Cost"].sum().reset_index()

                        # Merge datasets
                        correlation_df = pd.merge(grouped_occupancy, grouped_energy, on=["Floor", "Month"])

                        if not correlation_df.empty:
                            # 2. Linear Regression for Trendline
                            # We use sklearn because it's imported at the top
                            X = correlation_df["Actual_Occupancy"].values.reshape(-1, 1)
                            y = correlation_df["Energy_Cost"].values
                    
                            model = LinearRegression()
                            model.fit(X, y)
                            correlation_df["Predicted_Cost"] = model.predict(X)

                            # 3. Plot Scatter with Trendline
                            corr_fig = px.scatter(
                                correlation_df,
                                x="Actual_Occupancy",
                                y="Energy_Cost",
                                color="Floor",
                                size="Energy_Cost",
                                title="Correlation: Occupancy vs Energy Cost (Monthly per Floor)",
                                labels={"Actual_Occupancy": "Total Occupancy", "Energy_Cost": "Total Cost (RM)"},
                                hover_data=["Month"]
                            )

                            # update title font size
                            corr_fig.update_layout(title=dict(text="Correlation: Occupancy vs Energy Cost (Monthly per Floor)",
                                    font=dict(size=20),   # ← change size here
                                    x=0.1                 # ← position the title
                                ),
                                xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
                                yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
                                legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16)) # ← change legend (color lables) font (title and tick) size
                            )
                    
                            # Add trendline trace
                            # Sort by X to make line plotting correct
                            line_data = correlation_df.sort_values("Actual_Occupancy")
                            
                            # Update line color to be distinct
                            corr_fig.add_traces(px.line(line_data, x="Actual_Occupancy", y="Predicted_Cost").data[0])
                            corr_fig.data[-1].update(line=dict(color='black', width=3, dash='dash'), name='Trendline')

                            st.plotly_chart(corr_fig, width="stretch")
                        else:
                            st.warning("Insufficient overlapping data (Months) to plot correlation.")
                    else:
                        st.warning("Classroom file missing 'Week' column required for correlation mapping.")
            elif class_df.empty or energy_df.empty:
                st.info(f"No data available for batch {selected_batch}.")