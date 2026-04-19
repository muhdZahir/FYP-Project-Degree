from core.imports import st, pd, np, os, px, calendar, LinearRegression

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

def inject_custom_css(css_file_path):
        #Injects custom CSS from a local file into the Streamlit app.
        try:
            with open(css_file_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except FileNotFoundError:
            st.error(f"Error: CSS file not found at {css_file_path}")

with st.spinner("Loading page...", show_time=True):
    # Define the relative path to your CSS file
    css_path = os.path.join("assets", "style.css")

    # Inject the CSS
    inject_custom_css(css_path)

    st.title("ANALYSIS")
    st.write(f"Analyze the data and generate insights to identify areas for improvement. The system provides insights into "
            f"classroom usage and energy/electrical cost patterns, helping you make informed decisions about resource allocation and cost management.\n"
    )
    st.write(f"Choose the semester data batch stored in the system for analysis.")
            
    class_df = st.session_state.get('class_df', pd.DataFrame())
    energy_df = st.session_state.get('energy_df', pd.DataFrame())
    batch_name = st.session_state.get('batch_name', None)

    if not class_df.empty or not energy_df.empty:
        st.divider()
        if st.button(label="Start Analyzing", width="stretch", icon=":material/analytics:", key="blue"):
            st.session_state['show'] = True

    if st.session_state.get('show', False):
        st.title(f"Data Analysis & Insights: {batch_name}")
        # ==========================================
        # CLASSROOM ANALYSIS
        # ==========================================
        if not class_df.empty:
            st.header("Classroom Utilization Analysis")

            with st.spinner("Analyzing data...", show_time=True):
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

                # Display Average Utilization
                avg_util = class_df["Utilization"].mean() * 100
                st.metric("Average Classroom Utilization", f"{avg_util:.2f}%")

                # Bar Chart: Top 5 Underutilized Rooms
                st.subheader("Top 5 Underutilized Rooms")
                # Group by Room to get average utilization
                room_stats = class_df.groupby("Classroom_ID")["Percent_Utilize"].mean().reset_index()
                # Sort lowest first
                top_underutilized = room_stats.sort_values("Percent_Utilize", ascending=True).head(5)
                
                bar_fig = px.bar(
                    top_underutilized,
                    x="Classroom_ID",
                    y="Percent_Utilize",
                    color="Percent_Utilize",
                    color_continuous_scale="Reds_r", # Red = Low utilization
                    title="Rooms with Lowest Utilization Rate (%)",
                    text_auto='.1f',
                    labels={"Classroom_ID": "Classroom ID","Percent_Utilize": "Utilization (%)"}
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
                
                st.plotly_chart(bar_fig, width="stretch")
                # ------------------------------------------
                # Findings: Top 5 Underutilized Rooms (UPGRADED VARIANCE ANALYSIS)
                # ------------------------------------------
                st.markdown("Findings: Top 5 Underutilized Rooms")

                with st.expander("Show details"):
                    # Data Extraction & Baseline Calculation
                    campus_avg = class_df["Percent_Utilize"].mean()
                    worst_room = top_underutilized.iloc[0]
                    second_worst = top_underutilized.iloc[1]
                    fifth_worst = top_underutilized.iloc[-1]
                    
                    # Calculate Difference (Delta) from Campus Average
                    worst_diff = worst_room['Percent_Utilize'] - campus_avg
                    second_diff = second_worst['Percent_Utilize'] - campus_avg
                    fifth_diff = fifth_worst['Percent_Utilize'] - campus_avg

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            label=f"Most Critical: Room {worst_room['Classroom_ID']}",
                            value=f"{worst_room['Percent_Utilize']:.2f}%",
                            delta=f"{worst_diff:.2f}% vs Avg",
                            delta_color="normal" # Up = Green, Down = Red (Danger)
                        )
                    with col2:
                        st.metric(
                            label=f"2nd Worst: Room {second_worst['Classroom_ID']}",
                            value=f"{second_worst['Percent_Utilize']:.2f}%",
                            delta=f"{second_diff:.2f}% vs Avg",
                            delta_color="normal"
                        )
                    with col3:
                        st.metric(
                            label=f"5th Worst: Room {fifth_worst['Classroom_ID']}",
                            value=f"{fifth_worst['Percent_Utilize']:.2f}%",
                            delta=f"{fifth_diff:.2f}% vs Avg",
                            delta_color="normal"
                        )

                    # Calculate Total Wasted Space for the Worst Room (100% - Utilized%)
                    worst_wasted_space = 100 - worst_room['Percent_Utilize']

                    # --- [EDITED: Simplified the wording to plain English, removed consultant jargon] ---
                    st.markdown(f"""
                    **Observation: Rooms are too big for the classes**

                    The campus average utilization is **{campus_avg:.2f}%**. But the worst performing rooms are wasting a lot of space:
                    
                    - **Room {worst_room['Classroom_ID']}** is only **{worst_room['Percent_Utilize']:.2f}%** full. 
                    - This means the room is **{worst_wasted_space:.2f}% empty air**, but we are still paying the full price to air-condition it.
                    - Even the 5th worst room (**Room {fifth_worst['Classroom_ID']}**) is operating **{abs(fifth_diff):.2f}% below** the normal campus average.

                    **What to do:** The university is bleeding money on these specific rooms. We need to stop putting small classes into **Room {worst_room['Classroom_ID']}** immediately. Move these students to a smaller room to stop wasting electricity on empty space.
                    """)

                # Heatmap: Floor vs Time Slot
                st.subheader("Utilization Heatmap (Floor vs Time)")
                # Pivot data for heatmap
                heatmap_data = class_df.groupby(["Floor", "Time_Slot"])["Percent_Utilize"].mean().reset_index()
                heatmap_pivot = heatmap_data.pivot(index="Floor", columns="Time_Slot", values="Percent_Utilize")
                
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

                st.plotly_chart(heat_fig, width="stretch")

                # ------------------------------------------
                # Findings: Utilization Heatmap
                # ------------------------------------------
                st.markdown("Findings: Floor vs Time Utilization")

                with st.expander("Show details"):
                    # Data Extraction
                    peak_usage = heatmap_data.loc[heatmap_data["Percent_Utilize"].idxmax()]
                    lowest_usage = heatmap_data.loc[heatmap_data["Percent_Utilize"].idxmin()]

                    col1, col2 = st.columns(2)

                    with col1:
                        # --- [EDITED: Simplified the header titles] ---
                        st.markdown("### 🔥 Busiest Time & Floor")
                        st.metric("Time Slot", peak_usage["Time_Slot"])
                        st.metric("Floor Level", f"Floor {peak_usage['Floor']}")
                        st.write(f"**Utilization:** {peak_usage['Percent_Utilize']:.2f}%")

                    with col2:
                        # --- [EDITED: Simplified the header titles] ---
                        st.markdown("### ❄️ Quietest Time & Floor")
                        st.metric("Time Slot", lowest_usage["Time_Slot"])
                        st.metric("Floor Level", f"Floor {lowest_usage['Floor']}")
                        st.write(f"**Utilization:** {lowest_usage['Percent_Utilize']:.2f}%")

                    # --- [EDITED: Simplified the explanation, removed spatial fragmentation jargon] ---
                    st.markdown(f"""
                    **Observation: Wasted AC on empty floors**

                    The current timetable is scattered. We have busy areas like **Floor {peak_usage['Floor']}** at **{peak_usage['Time_Slot']}** (**{peak_usage['Percent_Utilize']:.2f}%** full), but we also have "Ghost Zones":
                    
                    - During **{lowest_usage['Time_Slot']}**, **Floor {lowest_usage['Floor']}** drops to a terrible **{lowest_usage['Percent_Utilize']:.2f}%** utilization.
                    - Because the classes are scattered, the building management has to turn on the central AC for the entire floor just for one or two isolated classes.

                    **What to do:** Look at the isolated classes on **Floor {lowest_usage['Floor']}** at **{lowest_usage['Time_Slot']}**. Move these few classes to a busier floor. Once they are moved, we can completely shut down the electricity and AC for Floor {lowest_usage['Floor']} during that time.
                    """)
            st.divider()
        elif class_df.empty:
            st.info(f"No classroom data available for batch {batch_name} to analyze.")
            st.divider()

        # ==========================================
        # ENERGY ANALYSIS
        # ==========================================
        if not energy_df.empty:
            st.header("Energy Cost Analysis")

            # Total energy per month
            monthly_energy = energy_df.groupby("Month")["Energy_Cost"].sum().reset_index()

            # Average monthly cost
            avg_monthly_cost = monthly_energy["Energy_Cost"].mean()

            st.metric("Average Monthly Energy Cost: ", f"RM {avg_monthly_cost:.2f}")

            with st.spinner("Analyzing data...", show_time=True):
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

                st.plotly_chart(line_fig, width="stretch")

                # ==========================================
                # Findings: Monthly Energy Cost per Floor
                # ==========================================
                st.markdown("Findings: Monthly Energy Cost per Floor")

                with st.expander("Show details"):
                    # Sort by energy cost (descending)
                    monthly_sorted = monthly_energy.sort_values(by="Energy_Cost", ascending=False)

                    # Identify highest, 2nd highest and lowest month
                    high_month = monthly_sorted.iloc[0]
                    second_high_month = monthly_sorted.iloc[1]
                    low_month = monthly_sorted.iloc[-1]

                    # Floors in highest month
                    high_month_floors = energy_df[energy_df["Month"] == high_month["Month"]]
                    high_floor_high_month = high_month_floors.loc[high_month_floors["Energy_Cost"].idxmax()]
                    low_floor_high_month = high_month_floors.loc[high_month_floors["Energy_Cost"].idxmin()]

                    # Floors in 2nd highest month
                    second_month_floors = energy_df[energy_df["Month"] == second_high_month["Month"]]
                    high_floor_second_month = second_month_floors.loc[second_month_floors["Energy_Cost"].idxmax()]
                    low_floor_second_month = second_month_floors.loc[second_month_floors["Energy_Cost"].idxmin()]

                    # Floors in lowest month
                    low_month_floors = energy_df[energy_df["Month"] == low_month["Month"]]
                    high_floor_low_month = low_month_floors.loc[low_month_floors["Energy_Cost"].idxmax()]
                    low_floor_low_month = low_month_floors.loc[low_month_floors["Energy_Cost"].idxmin()]

                    # Display metrics
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Highest Energy Cost Month",
                            high_month["Month"],
                            f"RM {high_month['Energy_Cost']:.2f}"
                        )

                    with col2:
                        st.metric(
                            "2nd Highest Energy Cost Month",
                            second_high_month["Month"],
                            f"RM {second_high_month['Energy_Cost']:.2f}"
                        )

                    with col3:
                        st.metric(
                            "Lowest Energy Cost Month",
                            low_month["Month"],
                            f"RM {low_month['Energy_Cost']:.2f}"
                        )

                    difference = high_month["Energy_Cost"] - second_high_month["Energy_Cost"]

                    st.metric("Difference of Costs Between 1st and 2nd Highest Energy Cost Month", f"RM {difference:.2f}")

                    # text findings
                    st.markdown(f"""
                    **Observations:**

                    **{high_month['Month']} recorded the highest total energy cost** of **RM {high_month['Energy_Cost']:.2f}**.

                    - The **highest contributing floor** during this month was **{high_floor_high_month['Floor']}**, with**RM {high_floor_high_month['Energy_Cost']:.2f}**.
                    - The **lowest contributing floor** was **{low_floor_high_month['Floor']}**, with **RM {low_floor_high_month['Energy_Cost']:.2f}**.

                    **{second_high_month['Month']} recorded the second highest energy cost** of **RM {second_high_month['Energy_Cost']:.2f}**.

                    - The **highest contributing floor** during this month was **{high_floor_second_month['Floor']}**, with **RM {high_floor_second_month['Energy_Cost']:.2f}**.
                    - The **lowest contributing floor** was **{low_floor_second_month['Floor']}**, with **RM {low_floor_second_month['Energy_Cost']:.2f}**.

                    **{low_month['Month']} recorded the lowest total energy cost** of **RM {low_month['Energy_Cost']:.2f}**.

                    - The **highest contributing floor** during this month was **{high_floor_low_month['Floor']}**, with **RM {high_floor_low_month['Energy_Cost']:.2f}**.
                    - The **lowest contributing floor** was **{low_floor_low_month['Floor']}**, with **RM {low_floor_low_month['Energy_Cost']:.2f}**.
                    """)

                # Pie chart: percentage contribution
                st.subheader("Floor Contribution to Total Energy Cost")

                # Calculate total energy cost of the whole floor
                floor_energy_cost = energy_df.groupby("Floor")["Energy_Cost"].sum().reset_index()

                total_energy_cost = energy_df["Energy_Cost"].sum()
                st.metric("Total Energy Cost:", f"RM {total_energy_cost:.2f}")

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

                st.plotly_chart(pie_fig, width="stretch")
                
                # ==========================================
                # Findings: Energy Cost Contribution
                # ==========================================
                st.markdown("Findings: Floor Contribution to Total Energy Cost")

                with st.expander("Show details"):
                    # Calculate percentage contribution
                    floor_energy_cost["Contribution (%)"] = (
                        floor_energy_cost["Energy_Cost"] / total_energy_cost * 100
                    )

                    # Sort by energy cost (descending)
                    cost_sorted = floor_energy_cost.sort_values(by="Energy_Cost", ascending=False, ignore_index=True)

                    st.markdown("Top Energy Cost Contribution by Floor:")
                    st.dataframe(cost_sorted.head(5).style.format({"Energy_Cost": "RM {:.2f}", "Contribution (%)": "{:.2f}%"}))

                    avg_cost = floor_energy_cost["Energy_Cost"].mean()

                    # Identify dominant floor
                    dominant_floor = floor_energy_cost.loc[floor_energy_cost["Contribution (%)"].idxmax()]
                    least_floor = floor_energy_cost.loc[floor_energy_cost["Contribution (%)"].idxmin()]

                    # ==============================
                    # Variance Analysis
                    # ==============================
                    variance = floor_energy_cost["Energy_Cost"].var()
                    std_dev = floor_energy_cost["Energy_Cost"].std()

                    max_cost = floor_energy_cost["Energy_Cost"].max()
                    min_cost = floor_energy_cost["Energy_Cost"].min()
                    range_diff = max_cost - min_cost

                    percent_diff = ((max_cost - min_cost) / min_cost) * 100

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Highest Energy Cost Contributor",
                            dominant_floor["Floor"],
                            f"{dominant_floor['Contribution (%)']:.2f}%"
                        )

                    with col2:
                        st.metric(
                            "Lowest Energy Cost Contributor",
                            least_floor["Floor"],
                            f"{least_floor['Contribution (%)']:.2f}%"
                        )

                    cv = std_dev / avg_cost
                    
                    # --- [EDITED: Translated the variation analysis to plain, actionable English] ---
                    if cv > 0.3:
                        variation_level = "High"
                        variation_text = """
                        This means there is a **huge difference in electricity bills** between the floors. 
                        Some floors are burning way more electricity than others. This usually means someone is leaving the AC running too long, or there are classes scattered across large spaces.

                        **What to do:** Check the highest-consuming floor immediately. Group their classes together or adjust the AC timers.
                        """
                    elif cv >= 0.2 and cv <= 0.3:
                        variation_level = "Moderate"
                        variation_text = """
                        This means there is a **moderate difference in electricity bills** between the floors. 
                        The energy usage is mostly okay, but some floors are slightly higher than normal.

                        **What to do:** Keep an eye on the top-consuming floor and see if you can move a few classes to save energy.
                        """
                    else:
                        variation_level = "Low"
                        variation_text = """
                        This means there is a **low difference in electricity bills**, meaning the power usage is very balanced across all floors.

                        **What to do:** The electricity is well-managed right now. No major changes needed.
                        """

                    st.markdown(f"""
                    **Observation:**
                                
                    **Floor {dominant_floor['Floor']}** is our biggest spender, 
                    burning **{dominant_floor['Contribution (%)']:.2f}%** of the total electricity bill. 

                    On the other hand, **Floor {least_floor['Floor']}** is the cheapest, only using **{least_floor['Contribution (%)']:.2f}%**. 

                    The difference between the highest and lowest floors is **RM {range_diff:.2f}** (which is **{percent_diff:.2f}%** higher).
                    """)

                    st.markdown(f"""{variation_text}""")   
            st.divider()          
        elif energy_df.empty:
            st.info(f"No energy data available for batch {batch_name} to analyze.")
            st.divider()

    
        # ==========================================
        # CORRELATION ANALYSIS
        # ==========================================
        if not class_df.empty and not energy_df.empty:
            st.header("Correlation Analysis")
            st.write("Analyzing the relationship between Total Occupancy (from Classrooms) and Total Energy Cost.")

            with st.spinner("Analyzing data...", show_time=True):
                # 1. Prepare Data: Map Weeks to Months to align datasets
                # Logic: Weeks 1-4 = Month 1, 5-8 = Month 2, 9-12 = Month 3, 13-16 = Month 4
                def map_week_to_month(week):
                    try:
                        week = int(week)
                    except Exception:
                        return None
                    if week <= 4: return "1"
                    elif week <= 8: return "2"
                    elif week <= 12: return "3"
                    elif week <= 16: return "4"
                    return None

                # Helper: normalize various month representations to a canonical numeric-string (1-12)
                month_name_map = {m.lower(): str(i) for i, m in enumerate(calendar.month_name) if m}
                month_abbr_map = {m.lower(): str(i) for i, m in enumerate(calendar.month_abbr) if m}

                def normalize_month(val):
                    if pd.isna(val):
                        return None
                    # ints
                    if isinstance(val, (int, np.integer)):
                        return str(int(val))
                    # numeric strings
                    s = str(val).strip()
                    if s.isdigit():
                        return str(int(s))
                    s_lower = s.lower()
                    # full month name
                    if s_lower in month_name_map:
                        return month_name_map[s_lower]
                    # abbreviated month name
                    if s_lower in month_abbr_map:
                        return month_abbr_map[s_lower]
                    return s  # fallback: keep as-is

                # Create working copies
                corr_class = class_df.copy()
                corr_energy = energy_df.copy()

                # Ensure Month column exists in class data: map from Week if possible
                if "Month" not in corr_class.columns and "Week" in corr_class.columns:
                    corr_class["Month"] = corr_class["Week"].apply(map_week_to_month)

                # Normalize Month values in both dataframes if present
                if "Month" in corr_class.columns:
                    corr_class["Month"] = corr_class["Month"].apply(normalize_month)

                if "Month" not in corr_energy.columns and "Week" in corr_energy.columns:
                    corr_energy["Month"] = corr_energy["Week"].apply(map_week_to_month)

                if "Month" in corr_energy.columns:
                    corr_energy["Month"] = corr_energy["Month"].apply(normalize_month)

                # At this point we attempt to aggregate and merge. Preferred: by Floor+Month
                grouped_occupancy = corr_class.groupby([col for col in ["Floor", "Month"] if col in corr_class.columns])["Actual_Occupancy"].sum().reset_index()
                grouped_energy = corr_energy.groupby([col for col in ["Floor", "Month"] if col in corr_energy.columns])["Energy_Cost"].sum().reset_index()

                # Try merge by Floor+Month if both have Month and Floor
                if set(["Floor", "Month"]).issubset(grouped_occupancy.columns) and set(["Floor", "Month"]).issubset(grouped_energy.columns):
                    correlation_df = pd.merge(grouped_occupancy, grouped_energy, on=["Floor", "Month"], how="inner")
                else:
                    correlation_df = pd.DataFrame()

                # Fallback: if no Floor+Month overlap, try aggregating by Month only (sum across floors)
                if correlation_df.empty:
                    if "Month" in grouped_occupancy.columns and "Month" in grouped_energy.columns:
                        occ_total = grouped_occupancy.groupby("Month")["Actual_Occupancy"].sum().reset_index()
                        energy_total = grouped_energy.groupby("Month")["Energy_Cost"].sum().reset_index()
                        correlation_df = pd.merge(occ_total, energy_total, on="Month", how="inner")
                    else:
                        correlation_df = pd.DataFrame()

                # If still empty, show helpful diagnostics
                if correlation_df.empty:
                    occ_months = sorted(list(set(corr_class["Month"].dropna().astype(str).unique()))) if "Month" in corr_class.columns else []
                    eng_months = sorted(list(set(corr_energy["Month"].dropna().astype(str).unique()))) if "Month" in corr_energy.columns else []
                    st.warning("Insufficient overlapping data (Months) to plot correlation.")
                    st.info(f"Classroom months found: {occ_months}")
                    st.info(f"Energy months found: {eng_months}")
                    st.write("Suggestion: Ensure both files contain a compatible `Month` column (numeric 1-12, month name, or derived from `Week`) covering at least one common month.")
                else:
                    # 2. Linear Regression for Trendline
                    X = correlation_df["Actual_Occupancy"].values.reshape(-1, 1)
                    y = correlation_df["Energy_Cost"].values

                    model = LinearRegression()
                    model.fit(X, y)
                    correlation_df["Predicted_Cost"] = model.predict(X)

                    # 3. Plot Scatter with Trendline
                    if "Floor" in correlation_df.columns:
                        color_arg = "Floor"
                        title_text = "Correlation: Occupancy vs Energy Cost (Monthly per Floor)"
                    else:
                        color_arg = None
                        title_text = "Correlation: Occupancy vs Energy Cost (Monthly)"

                    corr_fig = px.scatter(
                        correlation_df,
                        x="Actual_Occupancy",
                        y="Energy_Cost",
                        color=color_arg,
                        size="Energy_Cost",
                        title=title_text,
                        labels={"Actual_Occupancy": "Total Occupancy", "Energy_Cost": "Total Cost (RM)"},
                        hover_data=[c for c in ["Month", "Floor"] if c in correlation_df.columns]
                    )

                    # update title font size
                    corr_fig.update_layout(title=dict(text=title_text,
                            font=dict(size=20),
                            x=0.1
                        ),
                        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)),
                        legend=dict(title=dict(text="Floor", font=dict(size=18)), font=dict(size=16))
                    )

                    # Add trendline trace
                    line_data = correlation_df.sort_values("Actual_Occupancy")
                    corr_fig.add_traces(px.line(line_data, x="Actual_Occupancy", y="Predicted_Cost").data[0])
                    corr_fig.data[-1].update(line=dict(color='black', width=3, dash='dash'), name='Trendline')

                    st.plotly_chart(corr_fig, width="stretch")

                    # ==========================================
                    # 4. Findings: Correlation Analysis
                    # ==========================================
                    st.markdown("Findings: Occupancy vs Energy Cost Correlation")

                    with st.expander("Show details"):
                        # Statistical Calculations
                        r2_score = model.score(X, y)
                        corr_coef = correlation_df['Actual_Occupancy'].corr(correlation_df['Energy_Cost'])
                        slope = model.coef_[0]
                        # --- [NEW: Added y-intercept to calculate the Base Autopilot Cost at 0 students] ---
                        y_intercept = model.intercept_
                        unexplained_variance = 100 - (r2_score * 100)

                        # Metric Columns
                        # --- [EDITED: Changed 4 columns to a 2-column layout to create a spacious 2x2 grid] ---
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric(
                                label="Correlation Coefficient (r)",
                                value=f"{corr_coef:.2f}",
                                help="1.0 is perfect correlation. Near 0 means no relationship."
                            )
                            # --- [EDITED: Stacked the 3rd metric inside the 1st column] ---
                            st.metric(
                                label="Est. Cost per Occupant",
                                value=f"RM {slope:.2f}",
                                help="Estimated increase in energy bill for each additional student."
                            )
                        with col2:
                            st.metric(
                                label="R-Squared Score",
                                value=f"{r2_score * 100:.1f}%",
                                help="Percentage of energy cost explained by student occupancy."
                            )
                            # --- [EDITED: Stacked the 4th metric inside the 2nd column] ---
                            st.metric(
                                label="Base Cost (0 Students)",
                                value=f"RM {y_intercept:.2f}",
                                help="The 'Autopilot Cost'. The estimated electricity bill even if the building is completely empty."
                            )  

                        # --- [EDITED: Simplified the wording to plain English, removed 'Decoupled' jargon] ---
                        st.markdown(f"""
                        **Observation: The AC is running on autopilot**

                        This statistical model proves a major financial problem. Only **{r2_score * 100:.1f}%** of the electricity bill is actually because of students sitting in class.
                    
                        - The other **{unexplained_variance:.1f}% is wasted money**—we are paying to cool and light up empty spaces because the AC is left on or the rooms are too big.
                        - For every single student we add to the schedule, the university pays an extra **RM {slope:.2f}** in electricity because the scheduling is inefficient.
                    
                        **What to do:** The current timetable only cares about finding empty time slots. Management needs to start using URO to group classes together. Only turn on the AC when there are actually people inside, and stop the autopilot wastage.
                            """)

        elif class_df.empty or energy_df.empty:
            if class_df.empty:
                st.info(f"No classroom data available for batch {batch_name} to correlate.")
            elif energy_df.empty:
                st.info(f"No energy data available for batch {batch_name} to correlate.")