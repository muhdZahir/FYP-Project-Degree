from core.imports import st, pd, np, LinearRegression
from core.processing import map_week_to_month, normalize_month, compute_utilization, center_button, require_role
from core.visualization import plot_next_classroom_demand, plot_next_energy_cost

require_role(["Manager"])

if "batch" not in st.session_state:
    st.session_state["batch"] = st.session_state["batch_name"]

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
            
            model_df = class_df[["week", "capacity", "actual_occupancy"]].copy()
        except Exception as e:
            st.warning(f"Classroom Data Error: {e}")

    # Pre-process energy data
    if not energy_df.empty and not class_df.empty:
        try:
            # Energy
            energy_df["Month_Num"] = energy_df["month"].apply(normalize_month)

            monthly_cost = (energy_df.groupby("Month_Num")["energy_cost"].sum().reset_index())

            # Occupancy
            class_df["Month_Num"] = class_df["week"].apply(map_week_to_month)
            monthly_occ = (class_df.groupby("Month_Num")["actual_occupancy"].sum().reset_index())

            # Merge
            energy_model_df = pd.merge(
                monthly_cost,
                monthly_occ,
                on="Month_Num",
                how="inner"
            )

            energy_model_df["Month_Num"] = pd.to_numeric(
                energy_model_df["Month_Num"],
                errors="coerce"
            )

            energy_model_df = (energy_model_df.sort_values("Month_Num").reset_index(drop=True))
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
            > 📂 **Data Source:** Classroom Data *(Columns: Week, Capacity, Actual_Occupancy)*  
            > ⚙️ **AI Engine:** Linear Regression Model  
            > 💡 **Why This Engine:** It is the industry standard for tracking straightforward trends over time, making it highly reliable for predicting
            steady student growth or decline without overfitting the data.  
            > 🧮 **AI Audit Rule:** Analyzes past attendance patterns using linear regression to predict how full the campus will be next cycle. *(Formula:
            Linear Regression Projection on Avg Fullness %)*
            
            **2. Next Month Est. Cost**
            > 📂 **Data Source:** Energy Data *(Columns: Month, Occupancy, Energy_Cost)* 
            > ⚙️ **AI Engine:** Linear Regression Model  
            > 💡 **Why This Engine:** It prevents wild financial guessing by strictly anchoring future cost predictions to your actual historical billing
            patterns. It calculates the realistic financial baseline.  
            > 🧮 **AI Audit Rule:** Uses linear regression on past electric bills to estimate what you will have to pay next month if nothing changes.
            *(Formula: Linear Regression Trend × Expected Operating Days)*
            """)

        col1, col2 = st.columns(2)
        
        # Prediction 1: 14-Week Demand
        future_weeks_df = pd.DataFrame()
        pred_demand_avg = 0
        if not class_df.empty and len(class_df["week"].unique()) >= 2:
            try:
                avg_capacity = class_df["capacity"].mean()

                X_d = model_df[["week", "capacity"]]
                y_d = model_df["actual_occupancy"]

                model_d = LinearRegression().fit(X_d, y_d)
                
                max_w = int(class_df["week"].max())
                future_df = pd.DataFrame({
                    "week": [max_w + i for i in range(1, 15)],
                    "capacity": [avg_capacity] * 14
                })

                future_occ = model_d.predict(future_df)
                future_util = (
                    future_occ / avg_capacity
                ) * 100
                
                future_weeks_df = pd.DataFrame({"week": future_df["week"], "actual_occupancy": future_occ, "capacity": avg_capacity, "Percent_Utilize": future_util, "Type": "Prediction"})
                pred_demand_avg = future_util.mean()
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
        if not energy_df.empty and len(energy_model_df) >= 2:
            try:
                X_e = energy_model_df[["Month_Num", "actual_occupancy"]]
                y_e = energy_model_df["energy_cost"]

                model_e = LinearRegression().fit(X_e, y_e)
                
                next_m = int(energy_model_df["Month_Num"].max()) + 1

                avg_occ = (energy_model_df["actual_occupancy"].mean())

                future_energy = pd.DataFrame({
                    "Month_Num": [next_m],
                    "actual_occupancy": [avg_occ]
                })

                pred_e = max(0, model_e.predict(future_energy)[0])
                avg_monthly_cost = energy_model_df["energy_cost"].mean()
                with col2:
                    st.metric("Next Month Est. Cost", f"RM {pred_e:,.2f}", help="Your expected electric bill next month.")
            except Exception as e:
                col2.metric("Next Month Est. Cost", "Error")
                st.warning(f"Unable to estimate next month cost: {e}")
        else:
            with col2:
                st.metric(label="Next Month Est. Cost", value="N/A", help="No energy data available.")

        # ---------------------------------------------------------
        # VISUALIZING THE TRENDS
        # ---------------------------------------------------------
        st.write("")
        chart_col1, chart_col2 = st.columns(2)
        
        if not class_df.empty and not future_weeks_df.empty:
            try:
                historical = class_df.groupby("week")["Percent_Utilize"].mean().reset_index()
                historical["Type"] = "Historical"
                combined_class = pd.concat([historical, future_weeks_df], ignore_index=True)
                
                fig1 = plot_next_classroom_demand(combined_class)
                chart_col1.plotly_chart(fig1, width='stretch')
                chart_col1.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")
            except Exception as e:
                chart_col1.error(f"Chart Error: {e}")
        else:
            chart_col1.info("No classroom data available to visualize demand.")
                
        if not energy_df.empty and 'next_m' in locals() and len(energy_model_df) >= 2:
            try:
                monthly_plot = energy_model_df[["Month_Num", "energy_cost"]].copy()
                monthly_plot["Type"] = "Historical"
                pred_row = pd.DataFrame({"Month_Num": [next_m], "energy_cost": [pred_e], "Type": ["Prediction"]})
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
        st.subheader("🔴 Check Electricity Bill Matching")
        st.markdown(
            "> 📂 **Data Source:** Classroom + Energy Data  \n"
            "> 🧮 **Audit Rule:** Compares electric bills against student attendance. If a floor eats a massive budget but has very few students, the " \
            "system triggers an alert. *(Formula: % of Total Bill vs % of Total Students)*"
        )
        if not class_df.empty and not energy_df.empty:
            try:
                floor_energy = energy_df.groupby('floor')['energy_cost'].sum().reset_index()
                floor_energy['Cost_Pct'] = (floor_energy['energy_cost'] / floor_energy['energy_cost'].sum()) * 100
                floor_occupancy = class_df.groupby('floor')['actual_occupancy'].sum().reset_index()
                floor_occupancy['Occ_Pct'] = (floor_occupancy['actual_occupancy'] / floor_occupancy['actual_occupancy'].sum()) * 100
                
                merged_data = pd.merge(floor_energy, floor_occupancy, on='floor')
                merged_data['Gap'] = merged_data['Cost_Pct'] - merged_data['Occ_Pct']
                
                overall_util = class_df["Percent_Utilize"].mean()
                
                # Why 15%? 5-10% gap is normal due to heavy equipment like labs. A gap of >15% proves 
                # serious wastage (e.g. airconds left running on empty floors).
                if merged_data['Gap'].max() > 15.0:
                    w_leak = merged_data.sort_values(by='Gap', ascending=False).iloc[0]
                    actual_cost = w_leak['energy_cost']
                    floor_students = int(w_leak['actual_occupancy'])
                    
                    st.error(f"**BUDGET IMBALANCE:** Floor {int(w_leak['floor'])} costs **RM {actual_cost:,.2f}**, **{w_leak['Cost_Pct']:.1f}%** of budget, \
                             but only accounts for only **{floor_students:,} students**, which are **{w_leak['Occ_Pct']:.1f}%** of total student attended.\n\n"
                             f"**Action:** Consider sending maintenance to Floor {int(w_leak['floor'])}. The electricity is running at maximum capacity for \
                             a nearly empty floor. If this floor has labs or special equipment, check if they are being left on 24/7. If it's just classrooms, \
                             this is a clear sign of energy wastage."
                             f"\n\n**Pro Tip:** Do proactive checks to ensure air conditioning and lights are turned off when not in use.")
                elif overall_util < 30.0:
                    total_campus_bill = floor_energy['energy_cost'].sum()
                    st.error(f"**ENERGY WASTAGE:** The campus is practically empty with only {overall_util:.1f}% utilized, yet electricity is running as if the building is \
                             fully packed, costing RM {total_campus_bill:,.2f}.\n\n"
                             f"**Action:** Consider overriding the centralized Building Management System (BMS). It should have an override mode for low-occupancy periods. \
                             Use it to set a more energy-efficient schedule that matches actual student presence."
                             f"\n\n**Pro Tip:** If you don't have a BMS, this is a strong signal to invest in one, as it can automatically adjust energy usage\
                             based on real-time occupancy. Also, do proactive checks to ensure air conditioning and lights are turned off when not in use.")
                else:
                    st.success(f"**BALANCED:** Energy consumption aligns naturally with student attendance."
                               f"\n\n**Pro Tip:** A good practice is to do proactive checks to ensure air conditioning and lights are turned off when not in use.")
            except Exception as e:
                st.warning(f"Electrical audit could not be completed: {e}")
        else:
            st.info("Please upload Classroom and Energy data for optimization audit.")

        # --- STEP 2: CLASSROOM OPTIMIZATION ---
        st.subheader("🟢 Check Room Utilization")
        st.markdown(
            "> 📂 **Data Source:** Classroom Data only  \n"
            "> 🧮 **Audit Rule:** Checks if classrooms are consistently used for small group of students and below 60% utilization rate. *(Formula: Average " \
            "Students Present ÷ Maximum Physical Seats)*"
        )
        if not class_df.empty:
            try:
                r_avg = class_df.groupby('classroom_id').agg(
                    Percent_Utilize=('Percent_Utilize', 'mean'),
                    Avg_Students=('actual_occupancy', 'mean'),
                    Room_Size=('capacity', 'first') 
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
                                    low_util_rooms['classroom_id'].astype(str)
                                )
                    st.error(f"**SPACE WASTAGE:** {len(low_util_rooms)} rooms are consistently empty.\n\n"
                             f"**Underutilized Rooms:** {room_list}\n\n"
                             f"**Reality:** For example, room {w_room['classroom_id']} and room {b_room['classroom_id']} has **{int(w_room['Room_Size'])} \
                             seats** and **{int(b_room['Room_Size'])} seats**, but is usually occupied by only **{int(w_room['Avg_Students'])} students** \
                             (**{w_room['Percent_Utilize']:.1f}%** full) and **{int(b_room['Avg_Students'])} students** (**{b_room['Percent_Utilize']:.1f}%** full), respectively.\n\n"
                             f"**Action:** Consider moving the lectures in these rooms to smaller rooms or combining them to reduce electricity and lighting load.")
                elif len(low_util_rooms) > 0:
                    st.warning(f"**INEFFICIENT SPACE:** Room {w_room['classroom_id']} has **{int(w_room['Room_Size'])} seats**, but is usually occupied \
                               by only **{int(w_room['Avg_Students'])} students** (**{w_room['Percent_Utilize']:.1f}%** full).\n\n"
                               f"**Action:** Consider scheduling this room for a lecture with an appropriate number of students next semester.")
                else:
                    st.success("**EFFICIENT:** All lectures are placed in appropriately sized rooms. No space wastage.")
            except Exception as e:
                st.warning(f"Room sizing check could not be completed: {e}")