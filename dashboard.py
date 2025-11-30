import streamlit as st # to open streamlit, run python -m streamlit run dashboard.py. | to close, ctrl + c at terminal
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler # pip install -U scikit-learn
from sklearn.linear_model import LinearRegression

st.title("University Resource Optimization")

# Create a file uploader widget that accepts multiple files
uploaded_files = st.file_uploader(
    "Upload your files here",
    type=["csv", "xlsx"], # Optional: specify accepted file types
    accept_multiple_files=True
)

if uploaded_files:
    st.write("Uploaded Files:")
    for file in uploaded_files:
        st.write(f"- {file.name}")

        # Example of processing a CSV file
        if file.type == "text/csv":
            df = pd.read_csv(file)
            if file.name == "classroom_usage.csv": #for table classroom
                class_df = df
                st.subheader(f"Table of classroom usage:")
                st.dataframe(class_df)
            else: # for table energy
                energy_df = df
                st.subheader(f"Table of energy cost:")
                st.dataframe(energy_df)
        
        # Example of processing an Excel file
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(file)
            st.subheader(f"Table {file.name}:")
            st.dataframe(df)

# Only run preprocessing if both classroom and energy exist
if "class_df" in locals() and "energy_df" in locals():

    class_df["Utilization"] = class_df["Actual_Occupancy"] / class_df["Capacity"]
    total_cost = df.groupby("Floor")["Energy_Cost"].sum().reset_index()

'''
# classroom usage
    class_df = class_df.dropna()
    #class_df["Day"] = class_df["Day"].astype("category").cat.codes
    #class_df["Classroom_ID"] = class_df["Classroom_ID"].astype("category").cat.codes
    #class_df["Floor"] = class_df["Floor"].astype("category").cat.codes
    #class_df["Start_Time"] = class_df["Time_Slot"].str.split("–").str[0]
    #class_df["Start_Time"] = pd.to_datetime(class_df["Start_Time"])
    #class_df["Start_Hour"] = class_df["Start_Time"].dt.hour

    scaler = MinMaxScaler()
    class_cols = ["Capacity","Scheduled_Hours","Actual_Occupancy","Utilization"]
    class_df[class_cols] = scaler.fit_transform(class_df[class_cols])

    st.subheader("Preprocessed Classroom Usage Data")
    st.dataframe(class_df)

    # energy cost
    energy_df["Month"] = pd.to_datetime(energy_df["Month"], format="%B").dt.month
    energy_df["Floor"] = energy_df["Floor"].astype("category").cat.codes

    energy_cols = ["Energy_kWh","Energy_Cost","Month"]
    energy_df[energy_cols] = scaler.fit_transform(energy_df[energy_cols])

    st.subheader("Preprocessed Energy Cost Data")
    st.dataframe(energy_df)
'''

if "energy_df" in locals():
    # Convert month to correct order
    # values are 'January', 'February', etc, use %B:
    try:
        df["Month"] = pd.to_datetime(df["Month"], format="%B").dt.month
    except:
        pass  # If already numeric

    # Line chart: monthly energy cost per floor
    st.subheader("Monthly Energy Cost per Floor")

    line_fig = px.line(
        df,
        x="Month",
        y="Energy_Cost",
        color="Floor",
        markers=True
    )

    st.plotly_chart(line_fig, width='stretch')

    # Pie chart: percentage contribution
    st.subheader("Percentage Contribution to Total Energy Cost")

    pie_fig = px.pie(
        total_cost,
        names="Floor",
        values="Energy_Cost"
    )

    st.plotly_chart(pie_fig, width='stretch')
else:
    st.info("Upload a CSV file to see the data and generate a line chart.")