import streamlit as st # to open streamlit, run 'python -m streamlit run dashboard.py' | to close, ctrl + c at terminal
import pandas as pd
import numpy as np
import os
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler # pip install -U scikit-learn
from sklearn.linear_model import LinearRegression

st.title("University Resource Optimization")

#Introduction of the system
st.write(
    f"University Resource Optimization is a system designed to analyze classroom usage and energy cost and provide optimization recommendation.\n"
    f"\n2 files are needed to continue; 1 contains the nessecary columns for classroom and 1 for energy.\n"
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
st.dataframe(_class)

energy_example = {
    "Floor": [1, 4],
    "Month": ["Feb", "March"],
    "Energy_kWh": [1023, 894],
    "Energy_Cost": [657, 454]
}
_energy = pd.DataFrame(energy_example)
st.dataframe(_energy)

# File uploader widget that accepts multiple files
uploaded_files = st.file_uploader(
    "Upload your files here",
    accept_multiple_files=True
)

if uploaded_files:
    st.write("Uploaded Files:")

    #reqiured columns for class and energy
    class_col = ["Classroom_ID","Floor","Capacity","Actual_Occupancy","Day","Time_Slot","Week"]
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
            class_df = df
            st.success(f"Identified as Classroom Dataset")
            st.subheader("Classroom Usage Data:")
            st.dataframe(class_df)
        # For matching energy dataset
        elif len(missing_energy) == 0:
            energy_df = df
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

# Only run preprocessing if both classroom and energy exist
if "class_df" in locals() and "energy_df" in locals():

    class_df["Utilization"] = (class_df["Actual_Occupancy"] / class_df["Capacity"]) * 100
    total_energy_cost = energy_df.groupby("Floor")["Energy_Cost"].sum().reset_index()

# classroom usage
    #class_df = class_df.dropna()
    #class_df["Day"] = class_df["Day"].astype("category").cat.codes
    #class_df["Classroom_ID"] = class_df["Classroom_ID"].astype("category").cat.codes
    #class_df["Floor"] = class_df["Floor"].astype("category").cat.codes
    #class_df["Start_Time"] = class_df["Time_Slot"].str.split("–").str[0]
    #class_df["Start_Time"] = pd.to_datetime(class_df["Start_Time"])
    #class_df["Start_Hour"] = class_df["Start_Time"].dt.hour

    #scaler = MinMaxScaler()
    #class_cols = ["Capacity","Scheduled_Hours","Actual_Occupancy","Utilization"]
    #class_df[class_cols] = scaler.fit_transform(class_df[class_cols])

    #st.subheader("Preprocessed Classroom Usage Data")
    #st.dataframe(class_df)

    # energy cost
    #energy_df = energy_df.dropna()
    #energy_df["Month"] = pd.to_datetime(energy_df["Month"], format="%B").dt.month
    #energy_df["Floor"] = energy_df["Floor"].astype("category").cat.codes

    #energy_cols = ["Energy_kWh","Energy_Cost","Month"]
    #energy_df[energy_cols] = scaler.fit_transform(energy_df[energy_cols])

    #st.subheader("Preprocessed Energy Cost Data")
    #st.dataframe(energy_df)
        

if "class_df" in locals() or "energy_df" in locals():
    if st.button(label="Start Analyzing", width="stretch", icon=":material/analytics:"):
        # ==========================================
        # CLASSROOM ANALYSIS
        # ==========================================
        if "class_df" in locals():
            st.header("1. Classroom Utilization Analysis")

            st.spinner("Loading...")

            # Display Average Utilization
            avg_util = class_df["Utilization"].mean()
            st.metric("Average Classroom Utilization", f"{avg_util:.2f}%")

            # Bar Chart: Top 5 Underutilized Rooms
            st.subheader("Top 5 Underutilized Rooms")
            # Group by Room to get average utilization
            room_stats = class_df.groupby("Classroom_ID")["Utilization"].mean().reset_index()
            # Sort lowest first
            top_underutilized = room_stats.sort_values("Utilization", ascending=True).head(5)
            
            fig_bar = px.bar(
                top_underutilized,
                x="Classroom_ID",
                y="Utilization",
                color="Utilization",
                color_continuous_scale="Reds_r", # Red = Low utilization
                title="Rooms with Lowest Utilization Rate (%)",
                text_auto='.1f',
                labels={"Utilization": "Utilization (%)"}
            )
            
            st.plotly_chart(fig_bar, width='stretch')

            # Heatmap: Floor vs Time Slot
            st.subheader("Utilization Heatmap (Floor vs Time)")
            # Pivot data for heatmap
            heatmap_data = class_df.groupby(["Floor", "Time_Slot"])["Utilization"].mean().reset_index()
            heatmap_pivot = heatmap_data.pivot(index="Floor", columns="Time_Slot", values="Utilization")
            
            fig_heat = px.imshow(
                heatmap_pivot,
                labels=dict(x="Time Slot", y="Floor", color="Utilization (%)"),
                color_continuous_scale="RdYlGn", 
                title="Avg Utilization Rate (%) by Floor and Time"
            )

            st.plotly_chart(fig_heat, width='stretch')
        elif "class_df" not in locals():
            st.info("Upload class file to see the charts.")

        # ==========================================
        # ADDED SECTION: CORRELATION ANALYSIS
        # ==========================================
        if "class_df" in locals() and "energy_df" in locals():
            st.header("2. Correlation Analysis")
            st.write("Analyzing the relationship between Total Occupancy (from Classrooms) and Total Energy Cost.")

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
                    fig_corr = px.scatter(
                        correlation_df,
                        x="Actual_Occupancy",
                        y="Energy_Cost",
                        color="Floor",
                        size="Energy_Cost",
                        title="Correlation: Occupancy vs Energy Cost (Monthly per Floor)",
                        labels={"Actual_Occupancy": "Total Occupancy", "Energy_Cost": "Total Cost (RM)"},
                        hover_data=["Month"]
                    )
            
                    # Add trendline trace
                    
                    # Sort by X to make line plotting correct
                    line_data = correlation_df.sort_values("Actual_Occupancy")
                    fig_corr.add_traces(px.line(line_data, x="Actual_Occupancy", y="Predicted_Cost").data[0])
                    
                    # Update line color to be distinct (e.g., black dashed)
                    fig_corr.data[-1].update(line=dict(color='black', dash='dash'), name='Trendline')

                    st.plotly_chart(fig_corr, use_container_width=True)
                else:
                    st.warning("Insufficient overlapping data (Months) to plot correlation.")
            else:
                st.warning("Classroom file missing 'Week' column required for correlation mapping.")    


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
                markers=True
            )

            st.plotly_chart(line_fig, width='stretch')

            # Pie chart: percentage contribution
            st.subheader("Floor Contribution to Total Energy Cost")

            pie_fig = px.pie(
                total_energy_cost,
                names="Floor",
                values="Energy_Cost"
            )

            st.plotly_chart(pie_fig, width='stretch')
        elif "energy_df" not in locals():
            st.info("Upload energy file to see the charts.")

