from core.imports import st, pd, np, LinearRegression
from core.processing import map_week_to_month, normalize_month, compute_utilization, center_button
from core.visualization import plot_next_classroom_demand, plot_next_energy_cost

# Initialize data containers
class_df = pd.DataFrame()
energy_df = pd.DataFrame()
weekly = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("OPTIMIZATION RECOMMENDATIONS")
    st.write("Generate optimization recommendations based on the analysis results. The system provides insights into classroom usage and " \
    "energy/electrical cost patterns. Use these insights to make informed decisions about resource allocation and cost management, helping you " \
    "optimize your resources and reduce costs while maintaining a high level of service quality."
    )
    st.write(f"Choose the semester data batch stored in the system for analysis.")
    
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
            st.warning(f"Classroom Preprocessing Error: {e}")

    # Pre-process energy data
    if not energy_df.empty:
        try:
            energy_df["Month_Num"] = energy_df["Month"].apply(normalize_month)
            monthly_cost = energy_df.groupby("Month_Num")["Energy_Cost"].sum().reset_index()
            # Ensure Month_Num is sorted correctly (1, 2, 3, 4) for plotting and modeling
            monthly_cost["Month_Num"] = pd.to_numeric(monthly_cost["Month_Num"], errors='coerce')
            monthly_cost = monthly_cost.sort_values("Month_Num").reset_index(drop=True)
        except Exception as e:
            st.warning(f"Energy Preprocessing Error: {e}")

    if not class_df.empty or not energy_df.empty:
        st.divider()
        col2 = center_button()
        with col2:
            if st.button(label="Generate Optimization Audit", width="stretch", icon=":material/auto_fix_high:", key="blue"):
                st.session_state['show'] = True

    if st.session_state.get('show', False):
        st.title(f"Predictive Forecasting & Trend Analysis: {batch_name}")
        
        # ---------------------------------------------------------
        # THE 3-PILLAR PREDICTIONS
        # ---------------------------------------------------------
        st.header("Executive Forecasts")
        # Using weighted columns. Column 2 and 3 now get 50% more space than Column 1
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
                    st.metric("Next Semester Demand", f"{pred_demand_avg:.1f}%", help="Predicted average classroom utilization for the upcoming cycle.")
            except:
                col1.metric("Next Semester Demand", "Error")
        else:
            with col1:
                st.metric(label="Next Semester Demand", value="N/A", help="No classroom data available for demand forecasting.")
        
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
                col2.metric("Next Month Est. Cost", f"RM {pred_e:,.2f}", help="Forecasted utility bill based on current trajectory.")
            except:
                col2.metric("Next Month Est. Cost", "Error")
        else:
            with col2:
                st.metric(label="Next Month Est. Cost", value="N/A", help="No energy data available for cost forecasting.")

        # Prediction 3: Cost of Inaction (Bridged Logic)
        if not class_df.empty and not energy_df.empty:
            try:
                c_copy = class_df.copy()
                c_copy["Month_Map"] = c_copy["Week"].apply(map_week_to_month)
                e_copy = energy_df.copy()
                e_copy["Month_Map"] = e_copy["Month"].apply(normalize_month)
                
                occ_m = c_copy.groupby("Month_Map")["Actual_Occupancy"].sum().reset_index()
                eng_m = e_copy.groupby("Month_Map")["Energy_Cost"].sum().reset_index()
                merged = pd.merge(occ_m, eng_m, on="Month_Map")
                
                # Calculate R² to estimate how well occupancy explains energy cost variability
                # If R² is high, we assume less wastage (more efficient usage); if low, we assume more wastage.
                # We can use the R² value to estimate a "waste factor" that scales the average energy cost to project potential wastage.
                # For example, if R² is 0.8, we might assume only 20% of the energy cost is wasted. If R² is 0.2, we might assume 80% is wasted.
                if len(merged) > 1:
                    r2 = LinearRegression().fit(merged[["Actual_Occupancy"]], merged["Energy_Cost"]).score(merged[["Actual_Occupancy"]], merged["Energy_Cost"])
                    waste_factor = max(0.1, 1.0 - r2)
                else:
                    waste_factor = 0.5  # Default to 50% waste if we don't have enough data to calculate R²
                    # This is a very rough heuristic and can be adjusted based on domain knowledge or further analysis.
                    
                waste = (energy_df["Energy_Cost"].mean() * waste_factor) * 4 # Projected 4-month wastage
                col3.metric("Projected 4-Month Wastage",
                            f"RM {waste:,.2f}",
                            delta="-High Risk",
                            delta_color="inverse",
                            help="Estimated cost of inaction over the next 4 months based on current inefficiencies."
                        )
            except:
                col3.metric("Projected 4-Month Wastage", "Error")

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
                
                # Visualize next sem classroom demand
                fig1 = plot_next_classroom_demand(combined_class)
                chart_col1.plotly_chart(fig1, width='stretch')
            except Exception as e:
                chart_col1.error(f"Chart Error: {e}")
        else:
            chart_col1.info("No classroom data available to visualize demand trends.")
                
        if not energy_df.empty and 'next_m' in locals() and len(monthly_cost) >= 2:
            try:
                monthly_plot = monthly_cost.copy()
                monthly_plot["Type"] = "Historical"
                pred_row = pd.DataFrame({"Month_Num": [next_m], "Energy_Cost": [pred_e], "Type": ["Prediction"]})
                combined_energy = pd.concat([monthly_plot, pred_row], ignore_index=True)

                # Visualize next month energy cost
                fig2 = plot_next_energy_cost(combined_energy)
                chart_col2.plotly_chart(fig2, width='stretch')
            except Exception as e:
                chart_col2.error(f"Chart Error: {e}")
        else:
            chart_col2.info("No energy data available to visualize cost trends.")

        # ---------------------------------------------------------
        # OPTIMIZATION STEPS (Executive Action Plan - Integrated Transparency)
        # ---------------------------------------------------------
        st.divider()
        st.header("Executive Action Plan")
        st.write("Follow these priorities to stop wastage without sacrificing schedule comfort.")

        # --- STEP 1: FINANCIAL AUDIT ---
        st.subheader("🔴 Priority 1: Stop Financial Leaks")
        st.markdown(
            "> 📂 **Data Source:** Classroom Data + Energy Data  \n"
            "> 🧮 **AI Audit Rule:** Compares floor electricity bills against student density. If the bill is >15% higher than the human traffic there, the system triggers an alert. *(Formula: Floor's % of Total Electric Bill - Floor's % of Total Students)*"
        )
        if not class_df.empty and not energy_df.empty:
            try:
                f_eng = energy_df.groupby('Floor')['Energy_Cost'].sum().reset_index()
                f_eng['Cost_Pct'] = (f_eng['Energy_Cost'] / f_eng['Energy_Cost'].sum()) * 100
                f_occ = class_df.groupby('Floor')['Actual_Occupancy'].sum().reset_index()
                f_occ['Occ_Pct'] = (f_occ['Actual_Occupancy'] / f_occ['Actual_Occupancy'].sum()) * 100
                
                t3 = pd.merge(f_eng, f_occ, on='Floor')
                t3['Gap'] = t3['Cost_Pct'] - t3['Occ_Pct']
                
                overall_util = class_df["Percent_Utilize"].mean()
                
                if t3['Gap'].max() > 15.0:
                    w_leak = t3.sort_values(by='Gap', ascending=False).iloc[0]
                    actual_cost = w_leak['Energy_Cost']
                    floor_students = int(w_leak['Actual_Occupancy'])
                    
                    st.error(f"🚨 **BUDGET IMBALANCE:** Floor {int(w_leak['Floor'])} costs **RM {actual_cost:,.2f}** (**{w_leak['Cost_Pct']:.1f}%** of budget) for only **{floor_students} students** (**{w_leak['Occ_Pct']:.1f}%** of total campus).\n\n"
                             f"🎯 **Action:** Send maintenance to Floor {int(w_leak['Floor'])}. The AC is running at maximum capacity for a nearly empty floor.")
                elif overall_util < 30.0:
                    total_campus_bill = f_eng['Energy_Cost'].sum()
                    st.error(f"🚨 **SYSTEM DISCONNECT:** The campus is practically empty ({overall_util:.1f}% full), yet the centralized AC is running as if the building is fully packed, costing RM {total_campus_bill:,.2f}.\n\n"
                             f"🎯 **Action:** Override the centralized Building Management System immediately.")
                else:
                    st.success("✅ **BALANCED:** Energy consumption aligns naturally with student density.")
            except Exception as e: 
                pass
        else:
            st.info("Please upload Classroom and Energy data for a financial audit.")

        # --- STEP 2: CLASS GROUPING ---
        st.subheader("🟡 Priority 2: Consolidate Floors (Zone Consolidation)")
        st.markdown(
            "> 📂 **Data Source:** Classroom Data only  \n"
            "> 🧮 **AI Audit Rule:** Detects if an entire floor's AC is turned on for an extremely low number of concurrent classes. *(Formula: Count of Active Classes per Floor per Time Slot ≤ 2)*"
        )
        if not class_df.empty:
            try:
                t_floor = class_df.groupby(['Floor', 'Time_Slot']).size().reset_index(name='Count')
                ghost_slots = t_floor[t_floor['Count'] <= 2]
                
                if len(ghost_slots) >= 3:
                    st.error(f"🚨 **AC WASTAGE:** We have too many isolated classes scattered across empty floors. We are cooling entire building wings for almost nobody.\n\n"
                             f"🎯 **Action:** Group schedules on the lower floors and completely shut down the upper floors.")
                elif len(ghost_slots) > 0:
                    w_slot = ghost_slots.iloc[0]
                    st.warning(f"⚠️ **ISOLATED CLASS:** Floor {w_slot['Floor']} is running full AC for only **{w_slot['Count']} class(es)** during {w_slot['Time_Slot']}.\n\n"
                               f"🎯 **Action:** Relocate this class to an already active floor.")
                else:
                    st.success("✅ **EFFICIENT:** Timetables are tightly packed. No empty floors are wasting AC.")
            except: pass

        # --- STEP 3: ROOM SIZING ---
        st.subheader("🟢 Priority 3: Fix Room Sizing (Space Optimization)")
        st.markdown(
            "> 📂 **Data Source:** Classroom Data only  \n"
            "> 🧮 **AI Audit Rule:** Checks if the physical chair capacity in a room is consistently left empty by more than 40%. *(Formula: [Average Students Present ÷ Maximum Physical Seats] × 100 < 60%)*"
        )
        if not class_df.empty:
            try:
                # Group by room and get both percentage AND hard numbers
                r_avg = class_df.groupby('Classroom_ID').agg(
                    Percent_Utilize=('Percent_Utilize', 'mean'),
                    Avg_Students=('Actual_Occupancy', 'mean'),
                    Room_Size=('Capacity', 'max') 
                ).reset_index()
                
                c_mean = r_avg['Percent_Utilize'].mean()
                c_std = r_avg['Percent_Utilize'].std() if len(r_avg) > 1 else 0
                
                ghosts = r_avg[(r_avg['Percent_Utilize'] < (c_mean - (c_std * 0.5))) & (r_avg['Percent_Utilize'] < 60.0)]
                
                if len(ghosts) >= 3:
                    w_room = ghosts.sort_values(by='Percent_Utilize').iloc[0]
                    st.error(f"🚨 **SPACE WASTAGE:** {len(ghosts)} rooms are consistently empty.\n\n"
                             f"📉 **The Reality:** Room {w_room['Classroom_ID']} has **{int(w_room['Room_Size'])} seats**, but is usually occupied by only **{int(w_room['Avg_Students'])} students** (**{w_room['Percent_Utilize']:.1f}%** full).\n\n"
                             f"🎯 **Action:** Move this class to a smaller room to reduce AC and lighting load.")
                elif len(ghosts) > 0:
                    w_room = ghosts.sort_values(by='Percent_Utilize').iloc[0]
                    st.warning(f"⚠️ **INEFFICIENT SPACE:** Room {w_room['Classroom_ID']} has **{int(w_room['Room_Size'])} seats**, but is usually occupied by only **{int(w_room['Avg_Students'])} students** (**{w_room['Percent_Utilize']:.1f}%** full).\n\n"
                               f"🎯 **Action:** Consider swapping this room next semester.")
                else:
                    st.success("✅ **EFFICIENT:** All classes are placed in correctly sized rooms. No space wastage.")
            except: pass