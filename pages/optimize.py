from core.imports import st, pd, np, LinearRegression
from core.processing import map_week_to_month, normalize_month, compute_utilization, center_button
from core.visualization import plot_next_classroom_demand, plot_next_energy_cost

# Initialize data containers
class_df = pd.DataFrame()
energy_df = pd.DataFrame()
weekly = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("OPTIMIZATION RECOMMENDATIONS")
    st.write("This page gives you a direct action plan to cut costs and fix space issues. The system looks at your classroom schedules and electric " \
    "bills to find exactly where money is bleeding. Use recommendations to make fast, smart decisions without guessing.")
    st.write("Choose the semester data Batch stored in the system for optimization.")
    
    class_df = st.session_state.get('class_df', pd.DataFrame())
    energy_df = st.session_state.get('energy_df', pd.DataFrame())
    batch_name = st.session_state.get('batch_name', None)

    # Pre-process class data
    if not class_df.empty:
        try:
            class_df = compute_utilization(class_df)
            
            if "Week" in class_df.columns:
                weekly = class_df.groupby("Week")["Percent_Utilize"].mean().reset_index()
            else:
                weekly = class_df.groupby(class_df.index)["Percent_Utilize"].mean().reset_index()
                weekly.rename(columns={"index": "Week"}, inplace=True)
        except Exception as e:
            st.warning(f"Classroom Data Error: {e}")

    # Pre-process energy data
    if not energy_df.empty:
        try:
            energy_df["Month_Num"] = energy_df["Month"].apply(normalize_month)
            monthly_cost = energy_df.groupby("Month_Num")["Energy_Cost"].sum().reset_index()
            monthly_cost["Month_Num"] = pd.to_numeric(monthly_cost["Month_Num"], errors='coerce')
            monthly_cost = monthly_cost.sort_values("Month_Num").reset_index(drop=True)
        except Exception as e:
            st.warning(f"Energy Data Error: {e}")

    if not class_df.empty or not energy_df.empty:
        st.divider()
        col2 = center_button()
        with col2:
            if st.button(label="Generate Optimization Audit", width="stretch", icon=":material/auto_fix_high:", key="blue"):
                st.session_state['show'] = True
    else:
        st.divider()
        st.warning("⚠️ **Wait! You haven't loaded any data yet.**\n\nPlease look at the left sidebar, select a **Data Batch**, and click **Load Data** to start optimizing.")

    if st.session_state.get('show', False):
        st.title(f"Optimization Audit & Future Trends: {batch_name}")
        
        # ---------------------------------------------------------
        # THE 3-PILLAR PREDICTIONS
        # ---------------------------------------------------------
        st.header("Executive Forecasts")
        
        # --- Glass Box Transparency Header ---
        with st.expander("🔍 View AI Forecasting Logic (Data Sources, Models & Math)"):
            st.markdown("""
            **1. Next Semester Demand**
            > 📂 **Data Source:** Classroom Data *(Columns: Week, Percent_Utilize)*  
            > ⚙️ **AI Engine:** Linear Regression Model  
            > 💡 **Why This Engine:** It is the industry standard for tracking straightforward trends over time, making it highly reliable for predicting
            steady student growth or decline without overfitting the data.  
            > 🧮 **AI Audit Rule:** Analyzes past attendance patterns using linear regression to predict how full the campus will be next cycle. *(Formula:
            Linear Regression Projection on Avg Fullness %)*
            
            **2. Next Month Est. Cost**
            > 📂 **Data Source:** Energy Data *(Columns: Month, Energy_Cost)*  
            > ⚙️ **AI Engine:** Linear Regression Model  
            > 💡 **Why This Engine:** It prevents wild financial guessing by strictly anchoring future cost predictions to your actual historical billing
            patterns. It calculates the realistic financial baseline.  
            > 🧮 **AI Audit Rule:** Uses linear regression on past electric bills to estimate what you will have to pay next month if nothing changes.
            *(Formula: Linear Regression Trend × Expected Operating Days)*
            
            **3. Projected 4-Month Wastage**
            > 📂 **Data Source:** Combined Classroom & Energy Data *(Columns: Actual_Occupancy, Energy_Cost)*  
            > ⚙️ **AI Engine:** Linear Regression + Residual (Extra Cost) Tracking  
            > 💡 **Why This Engine:** It compares your actual monthly bill with the bill that is expected from student occupancy. Any extra amount above
            expected is treated as avoidable wastage.  
            > 🧮 **AI Audit Rule:** Build expected cost line from occupancy, then sum only positive gaps *(Actual Cost - Expected Cost, if positive)* and
            project for 4 months. *(Formula: Avg Monthly Extra Cost × 4 Months)*
            """)

        col1, col2, col3 = st.columns([1.2, 1.4, 1.4])
        
        # Prediction 1: 14-Week Demand
        future_weeks_df = pd.DataFrame()
        pred_demand_avg = 0
        if not class_df.empty and len(weekly) >= 2:
            try:
                X_d = weekly["Week"].values.reshape(-1, 1)
                y_d = weekly["Percent_Utilize"].values

                model_d = LinearRegression().fit(X_d, y_d)
                
                max_w = int(weekly["Week"].max())
                future_w = np.array([[max_w + i] for i in range(1, 15)])
                future_p = np.clip(model_d.predict(future_w), 0, 100)
                
                future_weeks_df = pd.DataFrame({"Week": future_w.flatten(), "Percent_Utilize": future_p, "Type": "Prediction"})
                pred_demand_avg = future_p.mean()
                with col1:
                    st.metric("Next Semester Demand", f"{pred_demand_avg:.1f}%", help="How full your classrooms are expected to be next cycle.")
            except Exception as e:
                col1.metric("Next Semester Demand", "Error")
                st.warning(f"Unable to estimate next semester demand: {e}")
        else:
            with col1:
                st.metric(label="Next Semester Demand", value="N/A", help="No classroom data available.")
        
        # Prediction 2: Energy
        pred_e = 0
        avg_monthly_cost = 0
        if not energy_df.empty and len(monthly_cost) >= 2:
            try:
                X_e = pd.to_numeric(monthly_cost["Month_Num"]).values.reshape(-1, 1)
                y_e = monthly_cost["Energy_Cost"].values

                model_e = LinearRegression().fit(X_e, y_e)
                
                next_m = int(monthly_cost["Month_Num"].astype(int).max()) + 1
                pred_e = max(0, model_e.predict([[next_m]])[0])
                avg_monthly_cost = energy_df["Energy_Cost"].mean()
                with col2:
                    st.metric("Next Month Est. Cost", f"RM {pred_e:,.2f}", help="Your expected electric bill next month.")
            except Exception as e:
                col2.metric("Next Month Est. Cost", "Error")
                st.warning(f"Unable to estimate next month cost: {e}")
        else:
            with col2:
                st.metric(label="Next Month Est. Cost", value="N/A", help="No energy data available.")

        # Prediction 3: Cost of Inaction
        if not class_df.empty and not energy_df.empty:
            try:
                c_copy = class_df.copy()
                c_copy["Month_Map"] = c_copy["Week"].apply(map_week_to_month)
                e_copy = energy_df.copy()
                e_copy["Month_Map"] = e_copy["Month"].apply(normalize_month)
                
                occ_m = c_copy.groupby("Month_Map")["Actual_Occupancy"].sum().reset_index()
                eng_m = e_copy.groupby("Month_Map")["Energy_Cost"].sum().reset_index()
                merged = pd.merge(occ_m, eng_m, on="Month_Map").dropna(subset=["Actual_Occupancy", "Energy_Cost"])

                if len(merged) >= 2:
                    waste_model = LinearRegression().fit(merged[["Actual_Occupancy"]], merged["Energy_Cost"])
                    merged["Expected_Cost"] = waste_model.predict(merged[["Actual_Occupancy"]])
                    merged["Extra_Cost"] = (merged["Energy_Cost"] - merged["Expected_Cost"]).clip(lower=0)
                    avg_monthly_extra_cost = merged["Extra_Cost"].mean()
                    waste = avg_monthly_extra_cost * 4
                else:
                    # Fallback if overlap is too little: use a conservative 10% of average monthly bill
                    avg_monthly_extra_cost = energy_df["Energy_Cost"].mean() * 0.10
                    waste = avg_monthly_extra_cost * 4

                col3.metric("Projected 4-Month Wastage",
                            f"RM {waste:,.2f}",
                            delta="-High Risk",
                            delta_color="inverse",
                            help="Estimated avoidable cost over 4 months, based on extra bill above expected usage."
                        )
                st.caption(f"Simple logic: average monthly extra cost is RM {avg_monthly_extra_cost:,.2f}; projected semester wastage = monthly extra × 4.")
            except Exception as e:
                col3.metric("Projected 4-Month Wastage", "Error")
                st.warning(f"Unable to estimate wastage: {e}")

        # ---------------------------------------------------------
        # VISUALIZING THE TRENDS
        # ---------------------------------------------------------
        st.write("")
        chart_col1, chart_col2 = st.columns(2)
        
        if not class_df.empty and not future_weeks_df.empty:
            try:
                historical = weekly.copy()
                historical["Type"] = "Historical"
                combined_class = pd.concat([historical, future_weeks_df], ignore_index=True)
                
                fig1 = plot_next_classroom_demand(combined_class)
                chart_col1.plotly_chart(fig1, width='stretch')
                chart_col1.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")
            except Exception as e:
                chart_col1.error(f"Chart Error: {e}")
        else:
            chart_col1.info("No classroom data available to visualize demand.")
                
        if not energy_df.empty and 'next_m' in locals() and len(monthly_cost) >= 2:
            try:
                monthly_plot = monthly_cost.copy()
                monthly_plot["Type"] = "Historical"
                pred_row = pd.DataFrame({"Month_Num": [next_m], "Energy_Cost": [pred_e], "Type": ["Prediction"]})
                combined_energy = pd.concat([monthly_plot, pred_row], ignore_index=True)

                fig2 = plot_next_energy_cost(combined_energy)
                chart_col2.plotly_chart(fig2, width='stretch')
                chart_col2.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")
            except Exception as e:
                chart_col2.error(f"Chart Error: {e}")
        else:
            chart_col2.info("No energy data available to visualize cost trends.")

        # ---------------------------------------------------------
        # OPTIMIZATION STEPS (Executive Action Plan)
        # ---------------------------------------------------------
        st.divider()
        st.header("Optimization Recommendations")
        st.write("Follow these priorities to stop wastage without hurting student comfort.")

        # --- STEP 1: ENERGY OPTIMIZATION ---
        st.subheader("🔴 Check Electricity Bill Matching (Electrical Audit)")
        st.markdown(
            "> 📂 **Data Source:** Classroom + Energy Data  \n"
            "> 🧮 **Audit Rule:** Compares electric bills against student traffic. If a floor eats a massive budget but has very few students, the " \
            "system triggers an alert. *(Formula: % of Total Bill vs % of Total Students)*"
        )
        if not class_df.empty and not energy_df.empty:
            try:
                floor_energy = energy_df.groupby('Floor')['Energy_Cost'].sum().reset_index()
                floor_energy['Cost_Pct'] = (floor_energy['Energy_Cost'] / floor_energy['Energy_Cost'].sum()) * 100
                floor_occupancy = class_df.groupby('Floor')['Actual_Occupancy'].sum().reset_index()
                floor_occupancy['Occ_Pct'] = (floor_occupancy['Actual_Occupancy'] / floor_occupancy['Actual_Occupancy'].sum()) * 100
                
                merged_data = pd.merge(floor_energy, floor_occupancy, on='Floor')
                merged_data['Gap'] = merged_data['Cost_Pct'] - merged_data['Occ_Pct']
                
                overall_util = class_df["Percent_Utilize"].mean()
                
                # Why 15%? 5-10% gap is normal due to heavy equipment like labs. A gap of >15% proves 
                # serious wastage (e.g. airconds left running on empty floors).
                if merged_data['Gap'].max() > 15.0:
                    w_leak = merged_data.sort_values(by='Gap', ascending=False).iloc[0]
                    actual_cost = w_leak['Energy_Cost']
                    floor_students = int(w_leak['Actual_Occupancy'])
                    
                    st.error(f"**BUDGET IMBALANCE:** Floor {int(w_leak['Floor'])} costs **RM {actual_cost:,.2f}** (**{w_leak['Cost_Pct']:.1f}%** of budget) \
                             for only an attendance of **{floor_students:,} students** (**{w_leak['Occ_Pct']:.1f}%** of total student attended).\n\n"
                             f"**Action:** Consider sending maintenance to Floor {int(w_leak['Floor'])}. The electricity is running at maximum capacity for a nearly empty floor."
                             f"\n\n**Pro Tip:** If this floor has labs or special equipment, check if they are being left on 24/7. If it's just classrooms, this is a clear \
                             sign of energy wastage. Also, do proactive checks to ensure air conditioning and lights are turned off when not in use.")
                elif overall_util < 30.0:
                    total_campus_bill = floor_energy['Energy_Cost'].sum()
                    st.error(f"**ENERGY WASTAGE:** The campus is practically empty ({overall_util:.1f}% full), yet electricity is running as if the building is \
                             fully packed, costing RM {total_campus_bill:,.2f}.\n\n"
                             f"**Action:** Consider overriding the centralized Building Management System."
                             f"\n\n**Pro Tip:** If your campus has a BMS, it should have an override mode for low-occupancy periods. Use it to set a more energy-efficient \
                             schedule that matches actual student presence. If you don't have a BMS, this is a strong signal to invest in one, as it can automatically adjust \
                             energy usage based on real-time occupancy. Also, do proactive checks to ensure air conditioning and lights are turned off when not in use.")
                else:
                    st.success(f"**BALANCED:** Energy consumption aligns naturally with student attendance."
                               f"\n\n**Pro Tip:** A good practice is to do proactive checks to ensure air conditioning and lights are turned off when not in use.")
            except Exception as e:
                st.warning(f"Electrical audit could not be completed: {e}")
        else:
            st.info("Please upload Classroom and Energy data for optimization audit.")

        # --- STEP 2: CLASSROOM OPTIMIZATION ---
        st.subheader("🟢 Check Room Sizing (Classroom Audit)")
        st.markdown(
            "> 📂 **Data Source:** Classroom Data only  \n"
            "> 🧮 **Audit Rule:** Checks if classrooms are consistently used and below 60% utilization rate. *(Formula: Average " \
            "Students Present ÷ Maximum Physical Seats)*"
        )
        if not class_df.empty:
            try:
                r_avg = class_df.groupby('Classroom_ID').agg(
                    Percent_Utilize=('Percent_Utilize', 'mean'),
                    Avg_Students=('Actual_Occupancy', 'mean'),
                    Room_Size=('Capacity', 'max') 
                ).reset_index()
                
                c_mean = r_avg['Percent_Utilize'].mean()
                c_std = r_avg['Percent_Utilize'].std() if len(r_avg) > 1 else 0
                
                # Why 60%? The industry sweet spot (TEFMA standard) is 60%-75%. 
                # 35% is too low (misses wasted space) and 75% is too strict (flags everything).
                low_util_rooms = r_avg[(r_avg['Percent_Utilize'] < (c_mean - (c_std * 0.5))) & (r_avg['Percent_Utilize'] < 60.0)]
                
                if not low_util_rooms.empty:
                    w_room = low_util_rooms.sort_values(by='Percent_Utilize').iloc[0]
                
                if len(low_util_rooms) >= 3:
                    b_room = low_util_rooms.sort_values(by='Percent_Utilize').iloc[-1]
                    room_list = ", ".join(
                                    low_util_rooms['Classroom_ID'].astype(str)
                                )
                    st.error(f"**SPACE WASTAGE:** {len(low_util_rooms)} rooms are consistently empty.\n\n"
                             f"**Underutilized Rooms:** {room_list}\n\n"
                             f"**Reality:** For example, room {w_room['Classroom_ID']} and room {b_room['Classroom_ID']} has **{int(w_room['Room_Size'])} \
                             seats** and **{int(b_room['Room_Size'])} seats**, but is usually occupied by only **{int(w_room['Avg_Students'])} students** \
                             (**{w_room['Percent_Utilize']:.1f}%** full) and **{int(b_room['Avg_Students'])} students** (**{b_room['Percent_Utilize']:.1f}%** full), respectively.\n\n"
                             f"**Action:** Consider moving the lectures in these rooms to smaller rooms or combining them to reduce electricity and lighting load.")
                elif len(low_util_rooms) > 0:
                    st.warning(f"**INEFFICIENT SPACE:** Room {w_room['Classroom_ID']} has **{int(w_room['Room_Size'])} seats**, but is usually occupied \
                               by only **{int(w_room['Avg_Students'])} students** (**{w_room['Percent_Utilize']:.1f}%** full).\n\n"
                               f"**Action:** Consider scheduling this room for a lecture with an appropriate number of students next semester.")
                else:
                    st.success("✅ **EFFICIENT:** All lectures are placed in appropriately sized rooms. No space wastage.")
            except Exception as e:
                st.warning(f"Room sizing check could not be completed: {e}")