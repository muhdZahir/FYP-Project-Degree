import streamlit as st ## Gemini dah satukan semua code dalam dashboard lama 
import pandas as pd  # python -m streamlit run dashboard_gemini.py
import plotly.express as px # ni dia siap buat sidebar boleh tengok cane nak guna
import os 
import database as db  # Importing your database.py
from sklearn.linear_model import LinearRegression

# ==========================================
# 0. SETUP & CONFIGURATION
# ==========================================
# Initialize DB on startup
db.init_db()

def inject_custom_css(css_file_path):
    """Injects custom CSS from a local file into the Streamlit app."""
    try:
        with open(css_file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Note: CSS file not found at {css_file_path}. Using default style.")

# Define path and inject CSS
css_path = os.path.join("assets", "style.css")
inject_custom_css(css_path)

st.title("URO: University Resource Optimization")

# ==========================================
# 1. SIDEBAR: DATA CONTROLLER
# ==========================================
st.sidebar.header("Data Controller")
data_source = st.sidebar.radio("Choose Data Source:", ["Upload New Files", "Load from Database"])

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

# ==========================================
# 2. FLOW A: UPLOAD NEW FILES
# ==========================================
if data_source == "Upload New Files":
    # --- Introduction & Examples (Only show this when uploading) ---
    st.write(
        f"University Resource Optimization is a system designed to analyze classroom usage and energy cost.\n"
        f"Upload your Classroom (Schedule) and Energy (Bill) files below."
    )
    
    with st.expander("View Example Data Formats"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Classroom Data Example**")
            st.dataframe(pd.DataFrame({
                "Classroom_ID": ["1901", "802"], "Floor": [19, 8], "Capacity": [30, 40],
                "Actual_Occupancy": [17, 34], "Day": ["Mon", "Thu"], "Time_Slot": ["10-12", "14-16"], "Week": [4, 7]
            }))
        with col_b:
            st.write("**Energy Data Example**")
            st.dataframe(pd.DataFrame({
                "Floor": [1, 4], "Month": ["Feb", "Mar"], "Energy_kWh": [1023, 894], "Energy_Cost": [657, 454]
            }))

    st.info("Upload raw Excel/CSV files to analyze and optionally save them to the database.")
    
    uploaded_files = st.file_uploader("Upload Files Here", accept_multiple_files=True)
    
    if uploaded_files:
        class_col = ["Classroom_ID","Floor","Capacity","Scheduled_Hours","Actual_Occupancy","Day","Time_Slot","Week"]
        energy_col = ["Floor","Month","Energy_kWh","Energy_Cost"]

        def check_columns(df, required_cols):
            return [col for col in required_cols if col not in df.columns]

        for file in uploaded_files:
            # File Type Handling
            file_extension = os.path.splitext(file.name)[1].lower()
            try:
                if "csv" in file_extension:
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
            except Exception as e:
                st.error(f"Could not read file {file.name}: {e}")
                continue

            # Identify Dataset Type
            missing_class = check_columns(df, class_col)
            missing_energy = check_columns(df, energy_col)

            if len(missing_class) == 0:
                class_df = df.copy()
                st.success(f"✅ {file.name}: Identified as Classroom Data")
            elif len(missing_energy) == 0:
                energy_df = df.copy()
                st.success(f"✅ {file.name}: Identified as Energy Data")
            else:
                st.warning(f"⚠️ {file.name}: Unknown format. Missing columns.")

        # --- SAVE TO DB SECTION ---
        if not class_df.empty or not energy_df.empty:
            st.markdown("---")
            st.write("### 💾 Save to System Memory")
            col1, col2 = st.columns([3, 1])
            with col1:
                batch_name = st.text_input("Batch Name (e.g., Sem 1 2024)", placeholder="Enter a name to tag this data...")
            with col2:
                st.write("") # Spacer
                st.write("")
                save_btn = st.button("Save Data", type="primary")
            
            if save_btn and batch_name:
                saved_c = False
                saved_e = False
                
                if not class_df.empty:
                    # Calculate utilization before saving
                    class_df["Utilization"] = (pd.to_numeric(class_df["Actual_Occupancy"], errors='coerce') / 
                                             pd.to_numeric(class_df["Capacity"], errors='coerce'))
                    if db.save_to_db(class_df, "classroom_data", batch_name):
                        saved_c = True
                
                if not energy_df.empty:
                    if db.save_to_db(energy_df, "energy_data", batch_name):
                        saved_e = True
                
                if saved_c or saved_e:
                    st.success(f"Successfully saved batch '{batch_name}' to database!")
                    st.balloons()
            elif save_btn and not batch_name:
                st.error("Please enter a Batch Name before saving.")

# ==========================================
# 3. FLOW B: LOAD FROM DATABASE
# ==========================================
elif data_source == "Load from Database":
    st.info("Load historical data stored in the system for longitudinal analysis.")
    
    available_batches = db.get_unique_batches()
    if not available_batches:
        st.warning("No data found in database. Please upload and save files first.")
    else:
        selected_batch = st.selectbox("Select Data Batch:", ["All History"] + available_batches)
        
        if st.button("Load Data", key="load_db_btn"):
            with st.spinner("Fetching data from SQL Engine..."):
                class_df = db.load_from_db("classroom_data", selected_batch)
                energy_df = db.load_from_db("energy_data", selected_batch)
                
                st.success(f"Loaded {len(class_df)} classroom records and {len(energy_df)} energy records.")

# ==========================================
# 4. ANALYTICS ENGINE (Visualizations)
# ==========================================
if not class_df.empty or not energy_df.empty:
    st.markdown("---")
    
    # Pre-processing (Cleaning for Display)
    if not class_df.empty:
        cols_to_numeric = ['Capacity', 'Scheduled_Hours', 'Actual_Occupancy']
        for col in cols_to_numeric:
            if col in class_df.columns:
                class_df[col] = pd.to_numeric(class_df[col], errors='coerce')
        class_df.dropna(subset=cols_to_numeric, inplace=True)
        class_df["Utilization"] = (class_df["Actual_Occupancy"] / class_df["Capacity"])

    if not energy_df.empty:
        cols_to_numeric = ['Energy_kWh', 'Energy_Cost']
        for col in cols_to_numeric:
            if col in energy_df.columns:
                energy_df[col] = pd.to_numeric(energy_df[col], errors='coerce')
        energy_df.dropna(subset=cols_to_numeric, inplace=True)

    # Master Button to Trigger Analysis
    if st.button(label="Start Analyzing", use_container_width=True, icon=":material/analytics:", key="green"):
        
        # --- 4.1 CLASSROOM ANALYSIS ---
        if not class_df.empty:
            st.header("1. Classroom Utilization Analysis")
            avg_util = class_df["Utilization"].mean() * 100
            st.metric("Average Classroom Utilization", f"{avg_util:.2f}%")

            st.subheader("Top 5 Underutilized Rooms")
            room_stats = class_df.groupby("Classroom_ID")["Utilization"].mean().reset_index()
            top_underutilized = room_stats.sort_values("Utilization", ascending=True).head(5)
            
            bar_fig = px.bar(
                top_underutilized, x="Classroom_ID", y="Utilization",
                color="Utilization", color_continuous_scale="Reds_r",
                title="Rooms with Lowest Utilization Rate (%)", text_auto='.1f'
            )
            # Apply your specific custom styling
            bar_fig.update_layout(
                title=dict(font=dict(size=20), x=0.2),
                xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15))
            )
            st.plotly_chart(bar_fig, use_container_width=True)

            st.subheader("Utilization Heatmap (Floor vs Time)")
            heatmap_data = class_df.groupby(["Floor", "Time_Slot"])["Utilization"].mean().reset_index()
            if not heatmap_data.empty:
                heatmap_pivot = heatmap_data.pivot(index="Floor", columns="Time_Slot", values="Utilization")
                heat_fig = px.imshow(
                    heatmap_pivot, color_continuous_scale="RdYlGn", 
                    title="Avg Utilization Rate (%) by Floor and Time"
                )
                heat_fig.update_layout(
                    title=dict(font=dict(size=20), x=0.2),
                    xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                    yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15))
                )
                st.plotly_chart(heat_fig, use_container_width=True)

        # --- 4.2 ENERGY ANALYSIS ---
        if not energy_df.empty:
            st.header("2. Energy Cost Analysis")
            
            st.subheader("Monthly Energy Cost per Floor")
            line_fig = px.line(
                energy_df, x="Month", y="Energy_Cost", color="Floor",
                markers=True, title="Floor Energy Cost by Month"
            )
            line_fig.update_layout(
                title=dict(font=dict(size=20), x=0.2),
                xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16))
            )
            st.plotly_chart(line_fig, use_container_width=True)

            st.subheader("Floor Contribution to Total Energy Cost")
            floor_energy_cost = energy_df.groupby("Floor")["Energy_Cost"].sum().reset_index()
            pie_fig = px.pie(
                floor_energy_cost, names="Floor", values="Energy_Cost",
                title="Total Cost Distribution by Floor"
            )
            pie_fig.update_layout(
                 title=dict(font=dict(size=20), x=0.1),
                 legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16))
            )
            st.plotly_chart(pie_fig, use_container_width=True)

        # --- 4.3 CORRELATION ANALYSIS ---
        if not class_df.empty and not energy_df.empty:
            st.header("3. Correlation Analysis")
            st.write("Analyzing the relationship between Total Occupancy (from Classrooms) and Total Energy Cost.")
            
            def map_week_to_month(week):
                try:
                    week = int(week)
                    if week <= 4: return "January"
                    elif week <= 8: return "February"
                    elif week <= 12: return "March"
                    elif week <= 16: return "April"
                    return "Other"
                except: return "Unknown"

            corr_class = class_df.copy()
            corr_energy = energy_df.copy()

            if "Week" in corr_class.columns:
                corr_class["Month"] = corr_class["Week"].apply(map_week_to_month)
                
                grouped_occupancy = corr_class.groupby(["Floor", "Month"])["Actual_Occupancy"].sum().reset_index()
                grouped_energy = corr_energy.groupby(["Floor", "Month"])["Energy_Cost"].sum().reset_index()
                correlation_df = pd.merge(grouped_occupancy, grouped_energy, on=["Floor", "Month"])

                if not correlation_df.empty:
                    X = correlation_df["Actual_Occupancy"].values.reshape(-1, 1)
                    y = correlation_df["Energy_Cost"].values
                    model = LinearRegression()
                    model.fit(X, y)
                    correlation_df["Predicted_Cost"] = model.predict(X)

                    corr_fig = px.scatter(
                        correlation_df, x="Actual_Occupancy", y="Energy_Cost",
                        color="Floor", size="Energy_Cost",
                        title="Correlation: Occupancy vs Energy Cost",
                        hover_data=["Month"]
                    )
                    
                    # Update Layout for Correlation
                    corr_fig.update_layout(
                        title=dict(font=dict(size=20), x=0.1),
                        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                        legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16))
                    )

                    line_data = correlation_df.sort_values("Actual_Occupancy")
                    corr_fig.add_traces(px.line(line_data, x="Actual_Occupancy", y="Predicted_Cost").data[0])
                    corr_fig.data[-1].update(line=dict(color='red', width=3, dash='dash'), name='Trendline')
                    st.plotly_chart(corr_fig, use_container_width=True)
                else:
                    st.warning("Insufficient data overlap (Months/Floors) to run correlation.")
            else:
                st.error("Classroom data is missing 'Week' column required for mapping.")