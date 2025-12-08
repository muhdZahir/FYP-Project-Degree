import streamlit as st # to open streamlit, run python -m streamlit run dashboard.py | to close, ctrl + c at terminal
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler # pip install -U scikit-learn
from sklearn.linear_model import LinearRegression

st.title("University Resource Optimization")

# Create a file uploader widget that accepts multiple files
uploaded_files = st.file_uploader(
    "Upload your files here",
    type=["csv", "xlsx"], # Specify accepted file types, csv/xlsx
    accept_multiple_files=True
)

if uploaded_files:
    st.write("Uploaded Files:")
    for file in uploaded_files:
        st.write(f"- {file.name}")

        if file.type == "text/csv": # Processing for CSV file
            df = pd.read_csv(file)
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": # Processing for Excel file
            df = pd.read_excel(file)

        class_col = ["Classroom_ID","Floor","Capacity","Actual_Occupancy","Day","Time_Slot","Week"]
        energy_col = ["Floor","Month","Energy_kWh","Energy_Cost"]

        def check_columns(df, required_cols):
            return [col for col in required_cols if col not in df.columns]
        
        if "classroom" in file.name.lower(): #for table classroom
            missing_class = check_columns(df, class_col)
            if missing_class:
                st.error(f"Classroom file is missing column: {missing_class}. Please ensure the file contains all of the required column.")
            else:
                class_df = df
                st.subheader(f"Table of classroom usage:")
                st.dataframe(class_df)
        elif "energy" in file.name.lower(): # for table energy
            missing_energy = check_columns(df, energy_col)
            if missing_energy:
                st.error(f"Energy file is missing column: {missing_energy}. Please ensure the file contains all of the required column.")
            else:
                energy_df = df
                st.subheader(f"Table of energy cost:")
                st.dataframe(energy_df)
        else:
            st.error("File is missing 'classroom' or 'energy' text. Please ensure the file name is correct.")

# Only run preprocessing if both classroom and energy exist
if "class_df" in locals() and "energy_df" in locals():

    class_df["Utilization"] = class_df["Actual_Occupancy"] / class_df["Capacity"]
    total_energy_cost = df.groupby("Floor")["Energy_Cost"].sum().reset_index()

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

if "energy_df" in locals():
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
        total_energy_cost,
        names="Floor",
        values="Energy_Cost"
    )

    st.plotly_chart(pie_fig, width='stretch')
elif "energy_df" not in locals():
    st.info("Upload a CSV file to see the data and generate a line chart.")