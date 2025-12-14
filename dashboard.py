import streamlit as st # pip install streamlit | streamlit is use to create the dashboard. to open streamlit, run 'python -m streamlit run dashboard.py'. to close, press 'ctrl + c' at terminal
import pandas as pd # pip install pandas | pandas is use to analyze data from csv/xlsx
import numpy as np # pip install numpy |
import os
import plotly.express as px # pip install plotly | plotly is use to create interactive visualization/chart
# pip install -U scikit-learn
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

# to read excel, install 'pip install openpyxl'

def inject_custom_css(css_file_path):
    """Injects custom CSS from a local file into the Streamlit app."""
    try:
        with open(css_file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: CSS file not found at {css_file_path}")

# Define the relative path to your CSS file
css_path = os.path.join("assets", "style.css")

# Inject the CSS
inject_custom_css(css_path)

st.title("URO: University Resource Optimization")

#Introduction of the system
st.write(
    f"University Resource Optimization is a system designed to analyze classroom usage and energy cost and provide optimization recommendation.\n"
    f"\n2 files are needed to analyze; 1 contains the nessecary columns for classroom and 1 for energy.\n"
    f"\nBelow are examples of classroom and energy data; each with their respective columns.\n"
)

class_example = {
    "Classroom_ID": ["1901", "802"],
    "Floor": [19, 8],
    "Capacity": [30, 40],
    "Actual_Occupancy": [17, 34],
    "Day": ["Mon", "Thursday"],
    "Time_Slot": ["10.00-12.00", "14.00-16.00"],
    "Week": [4, 7]
}
_class = pd.DataFrame(class_example)
st.write("Example of classroom data table")
st.dataframe(_class)

energy_example = {
    "Floor": [1, 4],
    "Month": ["Feb", "March"],
    "Energy_kWh": [1023, 894],
    "Energy_Cost": [657, 454]
}
_energy = pd.DataFrame(energy_example)
st.write("Example of energy data table")
st.dataframe(_energy)

# File uploader widget that accepts multiple files
uploaded_files = st.file_uploader(
    "Upload your files here",
    accept_multiple_files=True
)

if uploaded_files:
    st.write("Uploaded Files:")

    #reqiured columns for class and energy
    class_col = ["Classroom_ID","Floor","Capacity","Scheduled_Hours","Actual_Occupancy","Day","Time_Slot","Week"]
    energy_col = ["Floor","Month","Energy_kWh","Energy_Cost"]

    def check_columns(df, required_cols): #function to check column
        return [col for col in required_cols if col not in df.columns]
    
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
        
        #check missing columns for class and energy
        missing_class = check_columns(df, class_col)
        missing_energy = check_columns(df, energy_col)

        # For matching classroom dataset
        if len(missing_class) == 0:
            class_df = df.copy()
            st.success(f"Identified as Classroom Dataset")
            st.subheader("Classroom Usage Data:")
            st.dataframe(class_df)
        # For matching energy dataset
        elif len(missing_energy) == 0:
            energy_df = df.copy()
            st.success(f"Identified as Energy Dataset")
            st.subheader("Energy Cost Data:")
            st.dataframe(energy_df)
        # Neither matches
        else:
            st.error(
                f"Could not identify this file.\n"
                f"- Missing classroom columns: {missing_class}\n"
                f"- Missing energy columns: {missing_energy}\n"
                f"\nPlease upload the correct dataset."
            )

# Preprocessing classroom data
if "class_df" in locals():
    class_df = class_df.dropna() # drop missing values in a row

    # Convert string data in Capacity, Scheduled_Hours, & Actual_Occupancy to numeric, coercing errors to NaN
    class_df['Capacity_clean'] = pd.to_numeric(class_df['Capacity'], errors='coerce')
    class_df['Scheduled_clean'] = pd.to_numeric(class_df['Scheduled_Hours'], errors='coerce')
    class_df['ActOccu_clean'] = pd.to_numeric(class_df['Actual_Occupancy'], errors='coerce')

    # Drop rows where data is NaN (meaning original value was not numeric)
    class_df = class_df.dropna(subset=['Capacity_clean'])
    class_df = class_df.dropna(subset=['Scheduled_clean'])
    class_df = class_df.dropna(subset=['ActOccu_clean'])

    # Remove the temporary cleaned column
    class_df = class_df.drop(columns=['Capacity_clean'])
    class_df = class_df.drop(columns=['Scheduled_clean'])
    class_df = class_df.drop(columns=['ActOccu_clean'])

    # Calculate utilization rate per room
    class_df["Utilization"] = (class_df["Actual_Occupancy"] / class_df["Capacity"])

    #scaler = MinMaxScaler()
    #class_cols = ["Scheduled_Hours","Utilization"]
    #class_df[class_cols] = scaler.fit_transform(class_df[class_cols])

    #st.subheader("Preprocessed Classroom Usage Data")
    #st.dataframe(class_df)

# Preprocessing energy data
if "energy_df" in locals():
    energy_df = energy_df.dropna() # drop missing values in a row

    # Convert string data in Energy_kWh & Energy_Cost to numeric, coercing errors to NaN
    energy_df['Energy_clean'] = pd.to_numeric(energy_df['Energy_kWh'], errors='coerce')
    energy_df['Cost_clean'] = pd.to_numeric(energy_df['Energy_Cost'], errors='coerce')

    # Drop rows where data is NaN (meaning original value was not numeric)
    energy_df = energy_df.dropna(subset=['Energy_clean'])
    energy_df = energy_df.dropna(subset=['Cost_clean'])

    # Remove the temporary cleaned column
    energy_df = energy_df.drop(columns=['Energy_clean'])
    energy_df = energy_df.drop(columns=['Cost_clean'])

    #scaler = MinMaxScaler()
    #energy_cols = ["Energy_kWh","Energy_Cost"]
    #energy_df[energy_cols] = scaler.fit_transform(energy_df[energy_cols])

    # Calculate total energy cost of the whole floor
    floor_energy_cost = energy_df.groupby("Floor")["Energy_Cost"].sum().reset_index()

    #st.subheader("Preprocessed Energy Cost Data")
    #st.dataframe(energy_df)

if "class_df" in locals() or "energy_df" in locals():
    if st.button(label="Start Analyzing", width="stretch", icon=":material/analytics:", key="green"):
        # ==========================================
        # CLASSROOM ANALYSIS
        # ==========================================
        if "class_df" in locals():
            st.header("1. Classroom Utilization Analysis")

            st.spinner("Loading...")

            # Display Average Utilization
            avg_util = class_df["Utilization"].mean() * 100
            st.metric("Average Classroom Utilization", f"{avg_util:.2f}%")

            # Bar Chart: Top 5 Underutilized Rooms
            st.subheader("Top 5 Underutilized Rooms")
            # Group by Room to get average utilization
            room_stats = class_df.groupby("Classroom_ID")["Utilization"].mean().reset_index()
            # Sort lowest first
            top_underutilized = room_stats.sort_values("Utilization", ascending=True).head(5)
            
            bar_fig = px.bar(
                top_underutilized,
                x="Classroom_ID",
                y="Utilization",
                color="Utilization",
                color_continuous_scale="Reds_r", # Red = Low utilization
                title="Rooms with Lowest Utilization Rate (%)",
                text_auto='.1f',
                labels={"Utilization": "Utilization (%)"}
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
            
            st.plotly_chart(bar_fig, width='stretch')

            # Heatmap: Floor vs Time Slot
            st.subheader("Utilization Heatmap (Floor vs Time)")
            # Pivot data for heatmap
            heatmap_data = class_df.groupby(["Floor", "Time_Slot"])["Utilization"].mean().reset_index()
            heatmap_pivot = heatmap_data.pivot(index="Floor", columns="Time_Slot", values="Utilization")
            
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

            st.plotly_chart(heat_fig, width='stretch')
        elif "class_df" not in locals():
            st.info("Upload class file to view the classroom analysis.")

        # ==========================================
        # ENERGY ANALYSIS
        # ==========================================
        if "energy_df" in locals():
            st.header("2. Energy Cost Analysis")

            st.spinner("Loading...")

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

            st.plotly_chart(line_fig, width='stretch')

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

            st.plotly_chart(pie_fig, width='stretch')
        elif "energy_df" not in locals():
            st.info("Upload energy file to view the energy analysis.")

        # ==========================================
        # CORRELATION ANALYSIS
        # ==========================================
        if "class_df" in locals() and "energy_df" in locals():
            st.header("3. Correlation Analysis")
            st.write("Analyzing the relationship between Total Occupancy (from Classrooms) and Total Energy Cost.")

            st.spinner("Loading...")

            # 1. Prepare Data: Map Weeks to Months to align datasets
            # Logic: Weeks 1-4 = Jan, 5-8 = Feb, 9-12 = Mar, 13-16 = Apr
            def map_week_to_month(week):
                if week <= 4: return "January"
                elif week <= 8: return "February"
                elif week <= 12: return "March"
                elif week <= 16: return "April"
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
                    corr_fig.data[-1].update(line=dict(color='red', width=3, dash='dash'), name='Trendline')

                    st.plotly_chart(corr_fig, width="stretch")
                else:
                    st.warning("Insufficient overlapping data (Months) to plot correlation.")
            else:
                st.warning("Classroom file missing 'Week' column required for correlation mapping.")
        elif "class_df" not in locals() or "energy_df" not in locals():
            st.info("Upload both classroom and energy file to view the correlation analysis.")
