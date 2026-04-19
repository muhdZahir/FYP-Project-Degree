from core.imports import st, pd, np, os, px, calendar, MinMaxScaler, LinearRegression
# --- ADDED THESE TWO IMPORTS FOR ALGORITHM UPGRADE ---
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

# Initialize data containers
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

def inject_custom_css(css_file_path):
    try:
        with open(css_file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass # Silent pass to avoid clutter

def map_week_to_month(week):
    try:
        w = int(week)
        if w <= 4: return "1"
        elif w <= 8: return "2"
        elif w <= 12: return "3"
        elif w <= 16: return "4"
    except:
        return None
    return None

def normalize_month(val):
    if pd.isna(val): return None
    if isinstance(val, (int, np.integer)): return str(int(val))
    s = str(val).strip()
    if s.isdigit(): return str(int(s))
    # Map month names if necessary
    month_map = {m.lower(): str(i) for i, m in enumerate(calendar.month_name) if m}
    month_abbr = {m.lower(): str(i) for i, m in enumerate(calendar.month_abbr) if m}
    s_low = s.lower()
    if s_low in month_map: return month_map[s_low]
    if s_low in month_abbr: return month_abbr[s_low]
    return s

with st.spinner("Loading page...", show_time=True):
    css_path = os.path.join("assets", "style.css")
    inject_custom_css(css_path)

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
            class_df["Utilization"] = class_df["Actual_Occupancy"] / class_df["Capacity"]
            class_df.loc[class_df["Actual_Occupancy"] == 0, "Utilization"] = 0
            class_df["Percent_Utilize"] = class_df["Utilization"] * 100
            
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
        except Exception as e:
            st.warning(f"Energy Preprocessing Error: {e}")

    if not class_df.empty or not energy_df.empty:
        st.divider()
        if st.button(label="Generate Optimization Audit", width="stretch", icon=":material/auto_fix_high:", key="blue"):
            st.session_state['show'] = True

    if st.session_state.get('show', False):
        st.title(f"Predictive Forecasting & Trend Analysis: {batch_name}")
        
        # ---------------------------------------------------------
        # THE 3-PILLAR PREDICTIONS
        # ---------------------------------------------------------
        st.header("Executive Forecasts")
        col1, col2, col3 = st.columns(3)
        
        # Prediction 1: 14-Week Demand
        future_weeks_df = pd.DataFrame()
        pred_demand_avg = 0
        if not class_df.empty and len(weekly) >= 2:
            try:
                X_d = weekly["Week"].values.reshape(-1, 1)
                y_d = weekly["Percent_Utilize"].values
                # --- ALGORITHM UPGRADED TO POLYNOMIAL REGRESSION ---
                model_d = make_pipeline(PolynomialFeatures(degree=2), LinearRegression()).fit(X_d, y_d)
                
                max_w = int(weekly["Week"].max())
                future_w = np.array([[max_w + i] for i in range(1, 15)])
                future_p = np.clip(model_d.predict(future_w), 0, 100)
                
                future_weeks_df = pd.DataFrame({"Week": future_w.flatten(), "Percent_Utilize": future_p, "Type": "Prediction"})
                pred_demand_avg = future_p.mean()
                with col1:
                    st.metric("Next Semester Demand (Avg)", f"{pred_demand_avg:.1f}%", help="Predicted average classroom utilization for the upcoming cycle.")
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
                # --- ALGORITHM UPGRADED TO POLYNOMIAL REGRESSION ---
                model_e = make_pipeline(PolynomialFeatures(degree=2), LinearRegression()).fit(X_e, y_e)
                
                next_m = int(monthly_cost["Month_Num"].astype(int).max()) + 1
                pred_e = max(0, model_e.predict([[next_m]])[0])
                avg_monthly_cost = energy_df["Energy_Cost"].mean()
                col2.metric("Next Month Est. Cost", f"RM {pred_e:.2f}", help="Forecasted utility bill based on current trajectory.")
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
                
                if len(merged) > 1:
                    r2 = LinearRegression().fit(merged[["Actual_Occupancy"]], merged["Energy_Cost"]).score(merged[["Actual_Occupancy"]], merged["Energy_Cost"])
                    waste_factor = max(0.1, 1.0 - r2)
                else:
                    waste_factor = 0.40 
                    
                waste = (energy_df["Energy_Cost"].mean() * waste_factor) * 4 # Projected 4-month wastage
                col3.metric("Projected 4-Month Wastage", f"RM {waste:.2f}", delta="-High Risk", delta_color="inverse")
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
                combined = pd.concat([historical, future_weeks_df], ignore_index=True)
                fig1 = px.line(
                    combined, x="Week", y="Percent_Utilize", color="Type", 
                    labels={"Percent_Utilize": "Avg Utilization (%)"},
                    title="Classroom Demand Trend", markers=True
                )
                fig1.update_layout(
                    title=dict(text="Classroom Demand Trend", font=dict(size=20), x=0.1),
                    xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                    yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                    legend=dict(title=dict(text="Type", font=dict(size=18)), font=dict(size=16))
                )
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
                fig2 = px.line(
                    combined_energy, x="Month_Num", y="Energy_Cost", color="Type", 
                    labels={"Month_Num": "Month", "Energy_Cost": "Total Energy Cost (RM)"},
                    title="Energy Cost Trend", markers=True
                )
                fig2.update_layout(
                    title=dict(text="Energy Cost Trend", font=dict(size=20), x=0.2),
                    xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                    yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                    legend=dict(title=dict(text="Type", font=dict(size=18)), font=dict(size=16))
                )
                chart_col2.plotly_chart(fig2, width='stretch')
            except Exception as e:
                chart_col2.error(f"Chart Error: {e}")
        else:
            chart_col2.info("No energy data available to visualize cost trends.")

        # ---------------------------------------------------------
        # OPTIMIZATION STEPS
        # ---------------------------------------------------------
        st.divider()
        st.header("Optimization Recommendations")

        st.subheader("Step 1: Check Room Sizing (Space Leak Detection)")
        if not class_df.empty:
            try:
                r_avg = class_df.groupby('Classroom_ID')['Percent_Utilize'].mean().reset_index()
                c_mean = r_avg['Percent_Utilize'].mean()
                c_std = r_avg['Percent_Utilize'].std() if len(r_avg) > 1 else 0
                ghosts = r_avg[r_avg['Percent_Utilize'] < (c_mean - (c_std * 0.5))]
                
                if not ghosts.empty:
                    w_room = ghosts.sort_values(by='Percent_Utilize').iloc[0]
                    st.error(f"🚨 **SPACE LEAK:** Room {w_room['Classroom_ID']} is only {w_room['Percent_Utilize']:.1f}% full. This room is way too big for the number of students. Move them to a smaller room to save AC.")
                else:
                    st.success("✅ All classes are in the right-sized rooms. No space leaks detected.")
            except: pass
        else:
            st.info("Upload classroom data to check if your rooms are too big for your classes.")

        st.subheader("Step 2: Check Class Grouping (Same Time & Floor), Optimize Scheduling (Zone Consolidation)")
        if not class_df.empty:
            try:
                t_floor = class_df.groupby(['Floor', 'Time_Slot']).size().reset_index(name='Count')
                ghost_slots = t_floor[t_floor['Count'] <= 2]
                if not ghost_slots.empty:
                    w_slot = ghost_slots.iloc[0]
                    st.warning(f"⚠️ **WASTED AC:** Floor {w_slot['Floor']} only has {w_slot['Count']} class(es) at {w_slot['Time_Slot']}. Move these classes to an active floor so you can shut down the empty floor.")
                else:
                    st.success("✅ Classes are grouped perfectly. No empty floors wasting electricity.")
            except: pass
        else:
            st.info("Upload classroom data to see if you can group classes together and shut down unused empty floors.")

        st.subheader("Step 3: Check Electricity Bill Matching (Financial Audit)")
        if not class_df.empty and not energy_df.empty:
            try:
                f_eng = energy_df.groupby('Floor')['Energy_Cost'].sum().reset_index()
                f_eng['Cost_Pct'] = (f_eng['Energy_Cost'] / f_eng['Energy_Cost'].sum()) * 100
                f_occ = class_df.groupby('Floor')['Actual_Occupancy'].sum().reset_index()
                f_occ['Occ_Pct'] = (f_occ['Actual_Occupancy'] / f_occ['Actual_Occupancy'].sum()) * 100
                
                t3 = pd.merge(f_eng, f_occ, on='Floor')
                leaks = t3[(t3['Cost_Pct'] - t3['Occ_Pct']) > 15.0]
                if not leaks.empty:
                    w_leak = leaks.sort_values(by='Cost_Pct', ascending=False).iloc[0]
                    st.error(f"🚨 **MONEY LEAK:** Floor {int(w_leak['Floor'])} is burning {w_leak['Cost_Pct']:.1f}% of your electricity bill, but only has {w_leak['Occ_Pct']:.1f}% of your students. Someone is leaving the AC or lights on.")
                else:
                    st.success("✅ Your electricity bills match your student numbers.")
            except: pass
        else:
            st.info("Upload both classroom and energy data to see if any empty floors are secretly wasting resources.")