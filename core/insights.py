# Business logic + text generation
from core.imports import st
from core.processing import format_floor_name, compute_rooms_difference

# Determine correlation text
def interpret_cv(cv):
    if cv < 0.2:
        return "relatively uniform distribution"
    elif cv < 0.5:
        return "moderate variation in distribution"
    else:
        return "wide variation in distribution"

# Determine correlation findings
def classify_correlation(r2_score, baseline, slope):
    # -----------------------------
    # 1. Relationship strength text
    # -----------------------------
    if r2_score < 0.3:
        strength_text = "**weakly aligned** with student attendance"
    elif r2_score < 0.7:
        strength_text = "**moderately aligned** with student attendance"
    else:
        strength_text = "**strongly aligned** with student attendance"

    # -----------------------------
    # 2. Baseline interpretation
    # -----------------------------
    if baseline > 0.5:
        baseline_text = "we have a **massive 'Ghost Bill'**, meaning a large portion of electricity is burned blindly even when no students are around"
    elif baseline > 0.2:
        baseline_text = "we have a **noticeable 'Ghost Bill'** running in the background"
    else:
        baseline_text = "our electricity usage is efficiently driven by actual student attendance"

    # -----------------------------
    # 3. Special “autopilot” trigger
    # -----------------------------
    if r2_score < 0.3 and baseline > 0.5:
        headline = "### **Observation: Major 'Autopilot' Wastage Detected**"
        insight_extra = "⚠️ **Warning:** Systems like air conditioning and lights are likely running 24/7 on autopilot, regardless of whether classrooms are empty."
    elif r2_score < 0.3:
        headline = "### **Observation: Bills are NOT following student traffic**"
        insight_extra = "💡 **Tip:** Something else is eating your electricity budget. You have 'blind spending' going on."
    elif baseline > 0.5:
        headline = "### **Observation: Very high baseline cost detected**"
        insight_extra = "⚠️ **Warning:** A huge chunk of your bill is fixed. You are paying heavily even when the campus is completely empty."
    else:
        headline = "### **Observation: Bills are safely following student traffic**"
        insight_extra = "✅ **Good News:** Your energy consumption scales nicely when students enter and leave."

    # -----------------------------
    # 4. Slope interpretation
    # -----------------------------
    if slope < 0:
        slope_text = "The model estimates a negative relationship, which is not practically meaningful and indicates no reliable linear trend."
    else:
        slope_text = f"The estimated energy cost increases by RM {slope:,.2f} per additional student."

    return headline, strength_text, slope_text, baseline_text, insight_extra

# Display underutilized rooms findings (Bar Chart)
def underutilized_rooms_findings(worst, second, best, avg):    
    # Calculate Difference (Delta) from Campus Average
    worst_diff, second_diff, best_diff = compute_rooms_difference(
        worst["Percent_Utilize"], second["Percent_Utilize"], best["Percent_Utilize"], avg
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label=f"Most Critical: Room {worst['classroom_name']}",
            value=f"{worst['Percent_Utilize']:.2f}%",
            delta=f"{worst_diff:.2f}% vs Avg",
            delta_color="normal" 
        )
    with col2:
        st.metric(
            label=f"2nd Worst: Room {second['classroom_name']}",
            value=f"{second['Percent_Utilize']:.2f}%",
            delta=f"{second_diff:.2f}% vs Avg",
            delta_color="normal"
        )
    with col3:
        st.metric(
            label=f"Best Utilized: Room {best['classroom_name']}",
            value=f"{best['Percent_Utilize']:.2f}%",
            delta=f"{best_diff:.2f}% vs Avg",
            delta_color="normal"
        )
    
    # Extract Exact Value for the Worst Room
    worst_students = int(worst.get('actual_occupancy', 0))
    worst_capacity = int(worst.get('capacity', 0))
    worst_util = worst['Percent_Utilize']
    worst_unused = 100 - worst_util

    # Extract Exact Value for the Best Room
    best_students = int(best.get('actual_occupancy', 0))
    best_capacity = int(best.get('capacity', 0))
    best_util = best['Percent_Utilize']
    best_unused = 100 - best_util

    st.markdown(f"""
    ### **Observation: Classroom Space Summary**

    On average, our campus is running at **{avg:.2f}%** capacity.

    **Biggest Space Waster**
    - **Room {worst['classroom_name']}** has **{worst_capacity} seats**, but on average only **{worst_students} students** show up.
    - This means the room is only **{worst_util:.1f}%** full, leaving **{worst_unused:.1f}%** of the seats completely empty.

    **Most Efficient Room**
    - **Room {best['classroom_name']}** has **{best_capacity} seats**, with an average of **{best_students} students** showing up.
    - This room is **{best_util:.1f}%** full, with only **{best_unused:.1f}%** of seats empty.

    **What this means**
    - There is a **{best_util - worst_util:.1f}%** gap in how efficiently we pack our classes.
    - We could easily move the classes from the mostly-empty rooms into smaller ones, and completely shut off the power to the large halls.
    """)

# Display floor x time findings
def heatmap_findings(peak, lowest):
    peak_utilize = peak["Percent_Utilize"]
    lowest_utilize = lowest["Percent_Utilize"]

    peak_floor = format_floor_name(peak["floor"])
    low_floor = format_floor_name(lowest["floor"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔥 Busiest Time & Floor")
        st.metric("Time Slot", peak["time_slot"])
        st.metric("Floor Level", f"{peak_floor}")
        st.write(f"**Utilization:** {peak_utilize:.2f}%")

    with col2:
        st.markdown("### ❄️ Quietest Time & Floor")
        st.metric("Time Slot", lowest["time_slot"])
        st.metric("Floor Level", f"{low_floor}")
        st.write(f"**Utilization:** {lowest_utilize:.2f}%")
    
    # Calculate variation (simple and factual)
    util_gap = peak_utilize - lowest_utilize

    st.markdown(f"""
    ### **Observation: Busiest vs Quietest Times**

    **The Busiest Time:**
    - **{peak_floor}** during **{peak['time_slot']}**, running at **{peak_utilize:.2f}%** capacity.

    **The Quietest Time ('Dead Zone'):**
    - **{low_floor}** during **{lowest['time_slot']}**, dropping down to just **{lowest_utilize:.2f}%** capacity.

    **What this means**
    - The gap between our busiest and quietest times is **{util_gap:.2f}%**.
    - This shows empty gaps in our timetable. Moving a few scattered classes closer together could let us completely shut down power to entire floors during quiet hours.
    """)

# Display monthly energy cost findings
def monthly_energy_cost_findings(monthly_sorted,df):
    # Identify highest, 2nd highest and lowest month
    high_month = monthly_sorted.iloc[0]
    second_high_month = monthly_sorted.iloc[1]
    low_month = monthly_sorted.iloc[-1]

    if len(monthly_sorted) >= 2:
        second_high_month = monthly_sorted.iloc[1]
    else:
        second_high_month = high_month

    # Floors in highest month
    high_month_floors = df[df["month"] == high_month["month"]]
    high_floor_high_month = high_month_floors.loc[high_month_floors["energy_cost"].idxmax()]
    high_floor_name_high = format_floor_name(high_floor_high_month["floor"])
    low_floor_high_month = high_month_floors.loc[high_month_floors["energy_cost"].idxmin()]
    low_floor_name_high = format_floor_name(low_floor_high_month["floor"])

    # Floors in 2nd highest month
    second_month_floors = df[df["month"] == second_high_month["month"]]
    high_floor_second_month = second_month_floors.loc[second_month_floors["energy_cost"].idxmax()]
    high_floor_name_second = format_floor_name(high_floor_second_month["floor"])
    low_floor_second_month = second_month_floors.loc[second_month_floors["energy_cost"].idxmin()]
    low_floor_name_second = format_floor_name(low_floor_second_month["floor"])

    # Floors in lowest month
    low_month_floors = df[df["month"] == low_month["month"]]
    high_floor_low_month = low_month_floors.loc[low_month_floors["energy_cost"].idxmax()]
    high_floor_name_low = format_floor_name(high_floor_low_month["floor"])
    low_floor_low_month = low_month_floors.loc[low_month_floors["energy_cost"].idxmin()]
    low_floor_name_low = format_floor_name(low_floor_low_month["floor"])

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Highest Energy Cost Month",
            high_month["month"],
            f"RM {high_month['energy_cost']:,.2f}"
        )

    with col2:
        st.metric(
            "2nd Highest Energy Cost Month",
            second_high_month["month"],
            f"RM {second_high_month['energy_cost']:,.2f}"
        )

    with col3:
        st.metric(
            "Lowest Energy Cost Month",
            low_month["month"],
            f"RM {low_month['energy_cost']:,.2f}"
        )

    difference = high_month["energy_cost"] - second_high_month["energy_cost"]

    st.metric("Difference of Costs Between 1st and 2nd Highest Energy Cost Month", f"RM {difference:,.2f}")

    # Text Findings based on monthly energy cost
    # The text findings will explain the energy cost patterns and the contributing floors during those months.
    st.markdown(f"""
    ### **Observation: Monthly Bill Summary**

    - The **most expensive month** was **{high_month['month']}**, costing **RM {high_month['energy_cost']:,.2f}**.
    - The **second most expensive** was **{second_high_month['month']}**, costing **RM {second_high_month['energy_cost']:,.2f}**.
    - The **cheapest month** was **{low_month['month']}**, costing just **RM {low_month['energy_cost']:,.2f}**.

    **The Spike**
    - The difference between our worst and second-worst month is **RM {difference:,.2f}**.

    #### **Who Spent the Most?**

    **{high_month['month']} (Most Expensive Month)**
    - Top Spender: **{high_floor_name_high}** (RM {high_floor_high_month['energy_cost']:,.2f})
    - Lowest Spender: **{low_floor_name_high}** (RM {low_floor_high_month['energy_cost']:,.2f})

    **{second_high_month['month']}**
    - Top Spender: **{high_floor_name_second}** (RM {high_floor_second_month['energy_cost']:,.2f})
    - Lowest Spender: **{low_floor_name_second}** (RM {low_floor_second_month['energy_cost']:,.2f})

    **{low_month['month']} (Cheapest Month)**
    - Top Spender: **{high_floor_name_low}** (RM {high_floor_low_month['energy_cost']:,.2f})
    - Lowest Spender: **{low_floor_name_low}** (RM {low_floor_low_month['energy_cost']:,.2f})

    **What this means**
    - This shows that certain months and floors are eating way more of the budget than others. We need to check what appliances
    (like heavy lab equipment) or behaviors (like leaving ACs on overnight) are driving up the bills on those specific floors.
    """)

# Display energy cost contribution findings
def pie_findings(floor_energy_cost):
    avg_cost = floor_energy_cost["energy_cost"].mean()

    # Identify dominant floor
    dominant_floor = floor_energy_cost.loc[floor_energy_cost["Contribution (%)"].idxmax()]
    least_floor = floor_energy_cost.loc[floor_energy_cost["Contribution (%)"].idxmin()]

    # Variance Analysis
    std_dev = floor_energy_cost["energy_cost"].std()

    max_cost = floor_energy_cost["energy_cost"].max()
    min_cost = floor_energy_cost["energy_cost"].min()
    range_diff = max_cost - min_cost

    # Prevent division by zero when minimum cost is 0
    if min_cost == 0:
        percent_diff = 0.0
    else:
        percent_diff = ((max_cost - min_cost) / min_cost) * 100

    col1, col2 = st.columns(2)

    dom_floor = format_floor_name(dominant_floor["floor"])
    lst_floor = format_floor_name(least_floor["floor"])

    with col1:
        st.metric(
            "Highest Energy Cost Contributor",
            dom_floor,
            f"{dominant_floor['Contribution (%)']:.2f}%"
        )

    with col2:
        st.metric(
            "Lowest Energy Cost Contributor",
            lst_floor,
            f"{least_floor['Contribution (%)']:.2f}%"
        )

    cv = (std_dev / avg_cost) if avg_cost != 0 else 0
    share_gap = dominant_floor["Contribution (%)"] - least_floor["Contribution (%)"]
    
    st.markdown(f"""
    ### **Observation: Who is Eating the Budget?**

    - The most expensive floor is **{dom_floor}**, eating up **{dominant_floor['Contribution (%)']:.2f}%** of the entire electricity budget.
    - The cheapest floor is **{lst_floor}**, using only **{least_floor['Contribution (%)']:.2f}%**.

    **The Numbers**
    - Average bill per floor: **RM {avg_cost:,.2f}**
    - The gap between the most expensive and cheapest floor is **{share_gap:.2f}%** (or **RM {range_diff:,.2f}**).

    **What this means**
    - The billing shows **{interpret_cv(cv)}** across floors.
    - This proves some floors are energy drainers compared to the rest of the campus. 
    - If the most expensive floor doesn't have the most students, we have a major electricity leak.
    """)

# Display correlation findings
def correlation_findings(corr_coef, slope, r2_score, y_intercept, corr_df):
    # Metric Columns
    # Changed 4 columns to a 2-column layout to create a spacious 2x2 grid
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Correlation Coefficient (r)",
            value=f"{corr_coef:.2f}",
            help="1.0 is perfect correlation. Near 0 means no relationship."
        )
        # Stacked the 3rd metric inside the 1st column
        st.metric(
            label="Est. Cost per Occupant",
            value=f"RM {slope:,.2f}",
            help="Estimated increase in energy bill for each additional student."
        )
    with col2:
        st.metric(
            label="R-Squared Score",
            value=f"{r2_score * 100:.1f}%",
            help="Percentage of energy cost explained by student occupancy."
        )
        # Stacked the 4th metric inside the 2nd column
        st.metric(
            label="Base Cost (0 Students)",
            value=f"RM {y_intercept:,.2f}",
            help="The 'Autopilot Cost'. The estimated electricity bill even if the building is completely empty."
        )

    avg_cost = corr_df["energy_cost"].mean()
    baseline_ratio = y_intercept / avg_cost if avg_cost != 0 else 0
    unexplained = 100 - (r2_score * 100)

    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(r2_score, baseline_ratio, slope)

    # Final dynamic text findings
    st.markdown(f"""
    {headline}

    This analysis shows that our electric bill is {strength_text}. Only **{r2_score * 100:.1f}%** of our electric bill is driven by actual students attending class. 
    
    The other **{unexplained:.1f}%** is "blind spending" caused by things running in the background (e.g., central air conditioning left on, hallway lights, or heavy lab equipment operating 24/7).

    - {slope_text}
    - Even if the campus is completely empty (0 students), our base 'Ghost Bill' is still **RM {y_intercept:,.2f}**, which means {baseline_text}.

    {insight_extra}
    """)