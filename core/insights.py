# Business logic + text generation
from core.imports import st
from core.processing import format_floor_name, compute_rooms_difference
from core.config import THRESHOLDS

# Severity Assessment based on how far below average the worst room is
# This is a simple heuristic: if it's more than 50% below average, we consider it critical.
def classify_utilization_severity(worst_diff, fifth_diff):
    # If even the 5th worst room is also underperforming, then it's a critical issue that needs immediate attention.
    if worst_diff < THRESHOLDS["utilization"]["critical_gap"] and fifth_diff < THRESHOLDS["utilization"]["critical_gap"]:
        severity = "Critical"
    # If the worst room is underutilized but the 5th worst room is close to average, then it's a moderate issue that should be
    # monitored and addressed soon.
    elif worst_diff < THRESHOLDS["utilization"]["critical_gap"] and fifth_diff >= THRESHOLDS["utilization"]["critical_gap"]:
        severity = "Moderate"
    # If the worst room is underutilized but it's not drastically below average and the 5th worst room is also close to average,
    # then it's a low issue that can be monitored and addressed if it gets worse.
    elif worst_diff >= THRESHOLDS["utilization"]["critical_gap"] and fifth_diff >= THRESHOLDS["utilization"]["critical_gap"]:
        severity = "Low"
    else:
        severity = "Unknown"
    
    return severity

# Determine Utilization Pattern
# We can categorize the utilization pattern based on the difference between peak and lowest utilization.
def classify_utilization_pattern(peak, lowest):
    # If the peak utilization is above 80% and the lowest utilization is below 20%, we can say it's a "High Variance" pattern,
    # indicating a lot of wasted electricity on empty floors.
    if peak > THRESHOLDS["heatmap"]["high_peak"] and lowest < THRESHOLDS["heatmap"]["low_empty"]:
        pattern = "High Variance"
    # if the peak is high but the lowest is not extremely low, we can say it's a "Moderate Variance" pattern, indicating some
    # wasted electricity on empty floors.
    elif peak > THRESHOLDS["heatmap"]["high_peak"] and lowest >= THRESHOLDS["heatmap"]["high_peak"]:
        pattern = "Moderate Variance"
    # if the peak is not very high and the lowest is also not very low, we can say it's a "Low Variance" pattern, indicating a fairly
    # balanced timetable with less wasted electricity on empty floors.
    elif peak <= THRESHOLDS["heatmap"]["high_peak"] and lowest >= THRESHOLDS["heatmap"]["high_peak"]:
        pattern = "Low Variance"
    else:
        pattern = "Unknown"
    
    return pattern

# Determine variation level based on CV thresholds
def classify_cv(cv):
    # A CV above 0.3 is often considered high variability, indicating a large disparity in energy costs between floors.
    if cv > THRESHOLDS["energy"]["cv_high"]:
        level = "High"
        text = f"""
        The coefficient of variation (CV) between the floors is **{cv:.2f}**, which indicates a **high variance** in energy cost between the floors.
        This means there is a **huge difference in electricity bills** between the floors. 
        Some floors are burning way more electricity than others. This usually means someone is leaving the AC running too long, or there are classes scattered across large spaces.

        **What to do:** Check the highest-consuming floor immediately. Group their classes together or adjust the AC timers.
        """
    # A CV between 0.2 and 0.3 is considered moderate variability, indicating some disparity in energy costs between floors.
    elif cv >= THRESHOLDS["energy"]["cv_moderate"] and cv <= THRESHOLDS["energy"]["cv_high"]:
        level = "Moderate"
        text = f"""
        The coefficient of variation (CV) between the floors is **{cv:.2f}**, which indicates a **moderate variance** in energy cost between the floors.
        This means there is a **moderate difference in electricity bills** between the floors. 
        The energy usage is mostly okay, but some floors are slightly higher than normal.

        **What to do:** Keep an eye on the top-consuming floor and see if you can move a few classes to save energy.
        """
    # A CV below 0.2 is considered low variability, indicating a fairly balanced energy cost between floors.
    else:
        level = "Low"
        text = f"""
        The coefficient of variation (CV) between the floors is **{cv:.2f}**, which indicates a **low variance** in energy cost between the floors.
        This means there is a **low difference in electricity bills**, meaning the power usage is very balanced across all floors.

        **What to do:** The electricity is well-managed right now. No major changes needed.
        """
    return level, text

# Determine cost range difference
def classify_range(range, percent):
    if range > 1000:
        range_text = f"Additionally, the difference between the highest and lowest floors is quite large at RM {range:,.2f}, which indicates a \
        significant disparity in energy usage. (approximately **{percent:.2f}%** higher between the highest and lowest floors)"
    elif range >= 500 and range <= 1000:
        range_text = f"Additionally, the difference between the highest and lowest floors is moderate at RM {range:,.2f}, which indicates \
        some disparity in energy usage. (approximately **{percent:.2f}%** higher between the highest and lowest floors)"
    else:
        range_text = f"Additionally, the difference between the highest and lowest floors is small at RM {range:,.2f}, which indicates a \
        fairly balanced energy usage. (approximately **{percent:.2f}%** higher between the highest and lowest floors)"

    return range_text

# Determine correlation findings
def classify_correlation(r2_score, baseline, slope):
    # -----------------------------
    # 1. Relationship strength text
    # -----------------------------
    if r2_score < 0.3:
        strength_text = "a **weak relationship** between occupancy and energy cost"
    elif r2_score < 0.7:
        strength_text = "a **moderate relationship** between occupancy and energy cost"
    else:
        strength_text = "a **strong relationship** between occupancy and energy cost"

    # -----------------------------
    # 2. Baseline interpretation
    # -----------------------------
    if baseline > 0.5:
        baseline_text = "a **high level of fixed energy usage**, meaning a large portion of energy is consumed regardless of occupancy"
    elif baseline > 0.2:
        baseline_text = "a **noticeable baseline energy usage** even at lower occupancy levels"
    else:
        baseline_text = "energy usage that is largely driven by actual occupancy levels"

    # -----------------------------
    # 3. Special “autopilot” trigger
    # -----------------------------
    if r2_score < 0.3 and baseline > 0.5:
        headline = "**Observation: Energy usage is likely operating independently of occupancy (Autopilot behavior detected)**"
        insight_extra = "This strongly suggests that systems such as air conditioning may be running continuously regardless of actual classroom usage."
    elif r2_score < 0.3:
        headline = "**Observation: Weak alignment between occupancy and energy usage**"
        insight_extra = "This indicates that factors other than occupancy play a significant role in driving energy consumption."
    elif baseline > 0.5:
        headline = "**Observation: High baseline energy consumption detected**"
        insight_extra = "A large portion of energy cost appears to be fixed, regardless of how many students are present."
    else:
        headline = "**Observation: Energy usage generally follows occupancy patterns**"
        insight_extra = "Energy consumption appears to scale reasonably with classroom usage."

    # -----------------------------
    # 4. Slope interpretation
    # -----------------------------
    if slope < 0:
        slope_text = "The model estimates a negative relationship, which is not practically meaningful and indicates no reliable linear trend."
    else:
        slope_text = f"The estimated energy cost increases by RM {slope:,.2f} per additional student."

    return headline, strength_text, slope_text, baseline_text, insight_extra

# Display underutilized rooms findings
def underutilized_rooms_findings(worst, second, fifth, avg):    
    # Calculate Difference (Delta) from Campus Average
    worst_diff, second_diff, fifth_diff = compute_rooms_difference(
        worst["Percent_Utilize"], second["Percent_Utilize"], fifth["Percent_Utilize"], avg
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label=f"Most Critical: Room {worst['Classroom_ID']}",
            value=f"{worst['Percent_Utilize']:.2f}%",
            delta=f"{worst_diff:.2f}% vs Avg",
            delta_color="normal" # Up = Green, Down = Red (Danger)
        )
    with col2:
        st.metric(
            label=f"2nd Worst: Room {second['Classroom_ID']}",
            value=f"{second['Percent_Utilize']:.2f}%",
            delta=f"{second_diff:.2f}% vs Avg",
            delta_color="normal"
        )
    with col3:
        st.metric(
            label=f"5th Worst: Room {fifth['Classroom_ID']}",
            value=f"{fifth['Percent_Utilize']:.2f}%",
            delta=f"{fifth_diff:.2f}% vs Avg",
            delta_color="normal"
        )
    
    # Calculate Total Wasted Space for the Worst Room (100% - Utilized%)
    worst_wasted_space = 100 - worst['Percent_Utilize']
    severity = classify_utilization_severity(worst_diff,fifth_diff)
    
    # Text Findings based on severity
    # The text findings will explain the situation and provide actionable recommendations based on the severity level of
    # the worst-performing room.
    # If the worst room is critically underutilized and even the 5th worst room is also underperforming, then it's a critical issue that
    # needs immediate attention.
    if severity == "Critical":
        st.markdown(f"""
        **Observation: Rooms are too big for the classes**

        The campus average utilization is **{avg:.2f}%**. But the worst performing rooms are wasting a lot of space:
        
        - **Room {worst['Classroom_ID']}** is only **{worst['Percent_Utilize']:.2f}%** full. 
        - This means the room is **{worst_wasted_space:.2f}% empty air**, but we are still paying the full price to air-condition it.
        - Even the 5th worst room (**Room {fifth['Classroom_ID']}**) is operating **{abs(fifth_diff):.2f}% below** the normal campus
        average.

        **What to do:** The university is bleeding money on these specific rooms. We need to stop putting small classes into **Room
        {worst['Classroom_ID']}** immediately. Move these students to a smaller room to stop wasting electricity on empty space.
        """)
    # If the worst room is underutilized but the 5th worst room is close to average, then it's a moderate issue that should be
    # monitored and addressed soon.
    elif severity == "Moderate":
        st.markdown(f"""
        **Observation: Some rooms are underutilized**

        The campus average utilization is **{avg:.2f}%**. However, the worst performing room(s) is a major problem:
        
        - **Room {worst['Classroom_ID']}**) is only **{worst['Percent_Utilize']:.2f}%** full. 
        - This means the room is **{worst_wasted_space:.2f}% empty air**, but we are still paying the full price to air-condition it.
        - However, the 5th worst room (**Room {fifth['Classroom_ID']}**) is operating close to the campus average, only
        **{abs(fifth_diff):.2f}% below** the normal campus average.

        **What to do:** Room {worst['Classroom_ID']} is a major problem. We need to stop putting small classes into this room
        immediately. Move these students to a smaller room to stop wasting electricity on empty space.
        """)
    # If the worst room is underutilized but it's not drastically below average and the 5th worst room is also close to average,
    # then it's a low issue that can be monitored and addressed if it gets worse.
    elif severity == "Low":
        st.markdown(f"""
        **Observation: Underutilization is present but not critical**

        The campus average utilization is **{avg:.2f}%**. Most rooms are performing decently, but there are a few underperformers:
                                
        - **Room {worst['Classroom_ID']}** is only **{worst['Percent_Utilize']:.2f}%** full.
        - This means the room is **{worst_wasted_space:.2f}% empty air**. However, it's not a critical issue yet since it's not
        drastically below average.
        - Even the 5th worst room (**Room {fifth['Classroom_ID']}**) is operating close to the campus average, only
        **{abs(fifth_diff):.2f}% below** the normal campus average.

        **What to do:** Room {worst['Classroom_ID']} is underperforming, but it's not a critical issue yet. We can monitor this room and see if we can move a few classes to improve its utilization.
        """)
    else:
        st.markdown(f"""
        **Observation: Utilization pattern is unclear**

        The campus average utilization is **{avg:.2f}%**. The worst performing room is **Room {worst['Classroom_ID']}**, which is
        only **{worst['Percent_Utilize']:.2f}%** full. This means the room is **{worst_wasted_space:.2f}% empty air**. However, the
        severity of this issue is currently unclear because the 5th worst room (**Room {fifth['Classroom_ID']}**) is operating close to
        the campus average, only **{abs(fifth_diff):.2f}% below** the normal campus average.

        **What to do:** The utilization pattern is unclear, so we recommend doing a deeper analysis of the timetable and classroom usage to
        identify any potential issues or areas for improvement.
        """)

# Display floor x time findings
def heatmap_findings(peak, lowest):
    peak_utilize = peak["Percent_Utilize"]
    lowest_utilize = lowest["Percent_Utilize"]

    peak_floor = format_floor_name(peak["Floor"])
    low_floor = format_floor_name(lowest["Floor"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔥 Busiest Time & Floor")
        st.metric("Time Slot", peak["Time_Slot"])
        st.metric("Floor Level", f"{peak_floor}")
        st.write(f"**Utilization:** {peak_utilize:.2f}%")

    with col2:
        st.markdown("### ❄️ Quietest Time & Floor")
        st.metric("Time Slot", lowest["Time_Slot"])
        st.metric("Floor Level", f"{low_floor}")
        st.write(f"**Utilization:** {lowest_utilize:.2f}%")
    
    utilization_pattern = classify_utilization_pattern(peak_utilize, lowest_utilize)

    # Text Findings based on Utilization Pattern
    # The text findings will explain the utilization pattern and provide actionable recommendations based on whether it's a high variance,
    # moderate variance, or low variance pattern.
    if utilization_pattern == "High Variance":
        st.markdown(f"""
        **Observation: Wasted Electricity on empty floors**

        The current timetable is scattered. We have busy areas like **{peak_floor}** at **{peak['Time_Slot']}**
        (**{peak_utilize:.2f}%** full), but we also have "Ghost Zones":
        
        - During **{lowest['Time_Slot']}**, **{low_floor}** drops to a terrible **{lowest_utilize:.2f}%**
        utilization.
        - Because the classes are scattered, the building management has to turn on the central AC for the entire floor just for one or two
        isolated classes.

        **What to do:** Look at the isolated classes on **{low_floor}** at **{lowest['Time_Slot']}**. Move these few
        classes to a busier floor. Once they are moved, we can completely shut down the electricity and AC for {low_floor}
        during that time.
        """)
    elif utilization_pattern == "Moderate Variance":
        st.markdown(f"""
        **Observation: Wasted Electricity on some floors**

        The current timetable is somewhat scattered. We have busy areas like **{peak_floor}** at **{peak['Time_Slot']}**
        (**{peak_utilize:.2f}%** full), but we also have some quiet zones:
        
        - During **{lowest['Time_Slot']}**, **{low_floor}** drops to a low **{lowest_utilize:.2f}%**
        utilization.
        - Because the classes are scattered, the building management has to turn on the central AC for the entire floor just for one or two
        isolated classes.

        **What to do:** Look at the isolated classes on **{low_floor}** at **{lowest['Time_Slot']}**. If possible, move these few
        classes to a busier floor. This will help us save some electricity and reduce wasted AC on empty floors.
        """)
    elif utilization_pattern == "Low Variance":
        st.markdown(f"""
        **Observation: Electricity usage is fairly balanced**
        
        The current timetable is fairly well-organized. We have busy areas like **{peak_floor}** at **{peak['Time_Slot']}**
        (**{peak_utilize:.2f}%** full), but even the quietest zones like **{low_floor}** at 
        **{lowest['Time_Slot']}** are reasonably utilized.

        - During **{lowest['Time_Slot']}**, **{low_floor}** still maintains a decent **{lowest_utilize:.2f}%**
        utilization.
        - Because the classes are relatively well-distributed, the building management can optimize AC usage without worrying about isolated
        classes on empty floors.

        **What to do:** The timetable is fairly balanced, so there are no critical issues. We can monitor the utilization patterns and look
        for any emerging "Ghost Zones" in the future.
        """)
    else:
        st.markdown(f"""
        **Observation: Utilization pattern is unclear**

        The utilization pattern is currently unclear. We have a peak utilization of **{peak_utilize:.2f}%** on 
        {peak_floor} at {peak['Time_Slot']}, but the lowest utilization is only **{lowest_utilize:.2f}%** on
        {low_floor} at {lowest['Time_Slot']}. 

        **What to do:** The utilization pattern is unclear, so we recommend doing a deeper analysis of the timetable and classroom usage to
        identify any potential issues or areas for improvement.
        """)

# Display monthly energy cost findings
def monthly_energy_cost_findings(monthly_sorted,df):
    # Identify highest, 2nd highest and lowest month
    high_month = monthly_sorted.iloc[0]
    second_high_month = monthly_sorted.iloc[1]
    low_month = monthly_sorted.iloc[-1]

    # Floors in highest month
    high_month_floors = df[df["Month"] == high_month["Month"]]
    high_floor_high_month = high_month_floors.loc[high_month_floors["Energy_Cost"].idxmax()]
    high_floor_name_high = format_floor_name(high_floor_high_month["Floor"])
    low_floor_high_month = high_month_floors.loc[high_month_floors["Energy_Cost"].idxmin()]
    low_floor_name_high = format_floor_name(low_floor_high_month["Floor"])

    # Floors in 2nd highest month
    second_month_floors = df[df["Month"] == second_high_month["Month"]]
    high_floor_second_month = second_month_floors.loc[second_month_floors["Energy_Cost"].idxmax()]
    high_floor_name_second = format_floor_name(high_floor_second_month["Floor"])
    low_floor_second_month = second_month_floors.loc[second_month_floors["Energy_Cost"].idxmin()]
    low_floor_name_second = format_floor_name(low_floor_second_month["Floor"])

    # Floors in lowest month
    low_month_floors = df[df["Month"] == low_month["Month"]]
    high_floor_low_month = low_month_floors.loc[low_month_floors["Energy_Cost"].idxmax()]
    high_floor_name_low = format_floor_name(high_floor_low_month["Floor"])
    low_floor_low_month = low_month_floors.loc[low_month_floors["Energy_Cost"].idxmin()]
    low_floor_name_low = format_floor_name(low_floor_low_month["Floor"])

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Highest Energy Cost Month",
            high_month["Month"],
            f"RM {high_month['Energy_Cost']:,.2f}"
        )

    with col2:
        st.metric(
            "2nd Highest Energy Cost Month",
            second_high_month["Month"],
            f"RM {second_high_month['Energy_Cost']:,.2f}"
        )

    with col3:
        st.metric(
            "Lowest Energy Cost Month",
            low_month["Month"],
            f"RM {low_month['Energy_Cost']:,.2f}"
        )

    difference = high_month["Energy_Cost"] - second_high_month["Energy_Cost"]

    st.metric("Difference of Costs Between 1st and 2nd Highest Energy Cost Month", f"RM {difference:,.2f}")

    # Text Findings based on monthly energy cost
    # The text findings will explain the energy cost patterns and the contributing floors during those months.
    st.markdown(f"""
    **Observations: Electrical Cost Patterns**

    **{high_month['Month']} recorded the highest total energy cost** of **RM {high_month['Energy_Cost']:,.2f}**.

    - The **highest contributing floor** during this month was **{high_floor_name_high}**, with **RM {high_floor_high_month['Energy_Cost']:,.2f}**.
    - The **lowest contributing floor** was **{low_floor_name_high}**, with **RM {low_floor_high_month['Energy_Cost']:,.2f}**.

    **{second_high_month['Month']} recorded the second highest energy cost** of **RM {second_high_month['Energy_Cost']:,.2f}**.

    - The **highest contributing floor** during this month was **{high_floor_name_second}**, with **RM {high_floor_second_month['Energy_Cost']:,.2f}**.
    - The **lowest contributing floor** was **{low_floor_name_second}**, with **RM {low_floor_second_month['Energy_Cost']:,.2f}**.

    **{low_month['Month']} recorded the lowest total energy cost** of **RM {low_month['Energy_Cost']:,.2f}**.

    - The **highest contributing floor** during this month was **{high_floor_name_low}**, with **RM {high_floor_low_month['Energy_Cost']:,.2f}**.
    - The **lowest contributing floor** was **{low_floor_name_low}**, with **RM {low_floor_low_month['Energy_Cost']:,.2f}**.
    """)

# Display energy cost contribution findings
def pie_findings(floor_energy_cost):
    avg_cost = floor_energy_cost["Energy_Cost"].mean()

    # Identify dominant floor
    dominant_floor = floor_energy_cost.loc[floor_energy_cost["Contribution (%)"].idxmax()]
    least_floor = floor_energy_cost.loc[floor_energy_cost["Contribution (%)"].idxmin()]

    # Variance Analysis
    std_dev = floor_energy_cost["Energy_Cost"].std()

    max_cost = floor_energy_cost["Energy_Cost"].max()
    min_cost = floor_energy_cost["Energy_Cost"].min()
    range_diff = max_cost - min_cost

    percent_diff = ((max_cost - min_cost) / min_cost) * 100

    col1, col2 = st.columns(2)

    dom_floor = format_floor_name(dominant_floor["Floor"])
    lst_floor = format_floor_name(least_floor["Floor"])

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

    cv = std_dev / avg_cost
    
    variation_lvl, variation_text = classify_cv(cv)
    
    if variation_lvl == "High":
        st.markdown(f"""
        **Observation: High Disparity in Energy Cost Between Floors**

        The energy cost distribution across floors is highly unbalanced. The dominant floor, {dom_floor}, contributes a significant
        **{dominant_floor['Contribution (%)']:.2f}%** of the total energy cost, while the least contributing floor, {lst_floor},
        only contributes **{least_floor['Contribution (%)']:.2f}%**.
        """)
    elif variation_lvl == "Moderate":
        st.markdown(f"""
        **Observation: Moderate Disparity in Energy Cost Between Floors**

        The energy cost distribution across floors is somewhat unbalanced. The dominant floor, {dom_floor}, contributes a significant
        **{dominant_floor['Contribution (%)']:.2f}%** of the total energy cost, while the least contributing floor, {lst_floor},
        only contributes **{least_floor['Contribution (%)']:.2f}%**.
        """)
    else:
        st.markdown(f"""
        **Observation: Low Disparity in Energy Cost Between Floors**

        The energy cost distribution across floors is fairly balanced. The dominant floor, {dom_floor}, contributes a reasonable
        **{dominant_floor['Contribution (%)']:.2f}%** of the total energy cost, while the least contributing floor, {lst_floor},
        contributes **{least_floor['Contribution (%)']:.2f}%**.
        """)
    range_text = classify_range(range_diff, percent_diff)
    st.markdown(range_text)
    st.markdown(variation_text)

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

    avg_cost = corr_df["Energy_Cost"].mean()
    baseline_ratio = y_intercept / avg_cost if avg_cost != 0 else 0
    unexplained = 100 - (r2_score * 100)

    headline, strength_text, slope_text, baseline_text, insight_extra = classify_correlation(r2_score, baseline_ratio, slope)

    # Final dynamic text findings
    st.markdown(f"""
    {headline}

    This analysis shows {strength_text}. Occupancy explains **{r2_score * 100:.1f}% of the variation** in energy cost, 
    while the remaining **{unexplained:.1f}%** is influenced by other factors such as environmental conditions, building operations, or system inefficiencies.

    - {slope_text}
    - The model also estimates a baseline cost of **RM {y_intercept:,.2f}**, suggesting {baseline_text}.

    {insight_extra}

    **What this means for URO:**
    - If energy is not strongly tied to occupancy, optimizing schedules alone is not enough—**operational controls (e.g., AC scheduling, zoning)** must be improved.
    - If baseline costs are high, **reducing always-on systems** becomes a key opportunity for cost savings.
    - If the relationship is strong, **better class clustering and room utilization** can directly reduce energy consumption.
    """)