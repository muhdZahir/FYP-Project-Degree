import streamlit as st # to open streamlit, run 'python -m streamlit run try.py' | to close, ctrl + c
import pandas as pd
import numpy as np
import os
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler # pip install -U scikit-learn
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
    st.header("🔧 Data Preprocessing")

    # Utilization = Actual_Occupancy / Capacity
    class_df["utilization"] = (class_df["Actual_Occupancy"] / class_df["Capacity"])

    # Aggregate by week if week column exists
    if "Week" in class_df.columns:
        weekly = class_df.groupby("Week")["utilization"].mean().reset_index()
    else:
        # fallback: use row index as timeline
        weekly = class_df.groupby(class_df.index)["utilization"].mean().reset_index()
        weekly.rename(columns={"index": "Week"}, inplace=True)

    st.subheader("Processed Weekly Classroom Utilization")
    st.dataframe(weekly)

    # =========================================================
    # 3. PREPROCESS ENERGY DATA
    # =========================================================
    # Convert Month to number if needed
    try:
        energy_df["Month"] = pd.to_datetime(energy_df["Month"], format="%b").dt.month
    except:
        try:
            energy_df["Month"] = pd.to_datetime(energy_df["Month"], format="%B").dt.month
        except:
            pass  # already numeric

    monthly_cost = energy_df.groupby("Month")["Energy_Cost"].sum().reset_index()

    st.subheader("Processed Monthly Energy Cost")
    st.dataframe(monthly_cost)

    # =========================================================
    # 4. NORMALIZATION
    # =========================================================
    st.header("🔄 Normalization")

    scaler_class = MinMaxScaler()
    scaler_energy = MinMaxScaler()

    weekly["util_norm"] = scaler_class.fit_transform(
        weekly[["utilization"]]
    )

    monthly_cost["cost_norm"] = scaler_energy.fit_transform(
        monthly_cost[["Energy_Cost"]]
    )

    st.success("Normalization complete!")

    # =========================================================
    # 5. PREDICT NEXT SEMESTER DEMAND
    # =========================================================
    st.header("📘 Predicted Classroom Demand (Next Semester)")

    X_demand = weekly["Week"].values.reshape(-1, 1)
    y_demand = weekly["util_norm"].values

    model_demand = LinearRegression()
    model_demand.fit(X_demand, y_demand)

    next_week = weekly["Week"].max() + 1
    predicted_demand_norm = model_demand.predict([[next_week]])
    predicted_demand = scaler_class.inverse_transform(
        np.array(predicted_demand_norm).reshape(-1, 1)
    )[0][0]

    st.metric("Predicted Utilization Next Semester", f"{predicted_demand:.2f}")

    # Plot demand trend
    weekly_plot = weekly.copy()
    weekly_plot.loc[next_week] = [next_week, np.nan, predicted_demand_norm[0]]

    fig1 = px.line(
        weekly_plot,
        x="Week",
        y="util_norm",
        title="Predicted Classroom Demand Trend",
        markers=True,
    )
    fig1.add_scatter(
        x=[next_week],
        y=[predicted_demand_norm[0]],
        mode="markers+text",
        text=["Next Semester"],
        textposition="top center"
    )

    st.plotly_chart(fig1, width='stretch')

    # =========================================================
    # 6. PREDICT NEXT MONTH ENERGY COST
    # =========================================================
    st.header("💡 Predicted Energy Cost (Next Month)")

    X_energy = monthly_cost["Month"].values.reshape(-1, 1)
    y_energy = monthly_cost["cost_norm"].values

    model_energy = LinearRegression()
    model_energy.fit(X_energy, y_energy)

    next_month = monthly_cost["Month"].max() + 1
    predicted_energy_norm = model_energy.predict([[next_month]])
    predicted_energy = scaler_energy.inverse_transform(
        np.array(predicted_energy_norm).reshape(-1, 1)
    )[0][0]

    st.metric("Predicted Energy Cost Next Month (RM)", f"RM {predicted_energy:.2f}")

    # Plot energy trend
    monthly_plot = monthly_cost.copy()
    monthly_plot.loc[len(monthly_cost)] = [next_month, np.nan, predicted_energy_norm[0]]

    fig2 = px.line(
        monthly_plot,
        x="Month",
        y="cost_norm",
        title="Predicted Energy Cost Trend",
        markers=True,
    )
    fig2.add_scatter(
        x=[next_month],
        y=[predicted_energy_norm[0]],
        mode="markers+text",
        text=["Next Month"],
        textposition="top center"
    )

    st.plotly_chart(fig2, width='stretch')

    st.success("Prediction Completed!")