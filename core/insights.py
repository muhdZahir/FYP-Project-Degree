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
        headline = "### **Observation: Energy usage is likely operating independently of occupancy (Autopilot behavior detected)**"
        insight_extra = "This strongly suggests that systems such as air conditioning may be running continuously regardless of actual classroom usage."
    elif r2_score < 0.3:
        headline = "### **Observation: Weak alignment between occupancy and energy usage**"
        insight_extra = "This indicates that factors other than occupancy play a significant role in driving energy consumption."
    elif baseline > 0.5:
        headline = "### **Observation: High baseline energy consumption detected**"
        insight_extra = "A large portion of energy cost appears to be fixed, regardless of how many students are present."
    else:
        headline = "### **Observation: Energy usage generally follows occupancy patterns**"
        insight_extra = "Energy consumption appears to scale reasonably with classroom usage."

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
            label=f"Most Critical: Room {worst['Classroom_ID']}",
            value=f"{worst['Percent_Utilize']:.2f}%",
            delta=f"{worst_diff:.2f}% vs Avg",
            delta_color="normal" 
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
            label=f"Best Utilized: Room {best['Classroom_ID']}",
            value=f"{best['Percent_Utilize']:.2f}%",
            delta=f"{best_diff:.2f}% vs Avg",
            delta_color="normal"
        )
    
    # Extract Exact Value for the Worst Room
    worst_students = int(worst.get('Actual_Occupancy', 0))
    worst_capacity = int(worst.get('Capacity', 0))
    worst_util = worst['Percent_Utilize']
    worst_unused = 100 - worst_util

    # Extract Exact Value for the Best Room
    best_students = int(best.get('Actual_Occupancy', 0))
    best_capacity = int(best.get('Capacity', 0))
    best_util = best['Percent_Utilize']
    best_unused = 100 - best_util

    st.markdown(f"""
    ### **Observation: Classroom Utilization Overview**

    The campus average utilization is **{avg:.2f}%**.

    **Lowest Utilized Room**
    - **Room {worst['Classroom_ID']}** has a seating capacity of **{worst_capacity}**, with an average occupancy of **{worst_students} students**.
    - This corresponds to a utilization rate of **{worst_util:.1f}%**, leaving **{worst_unused:.1f}%** of capacity unused.

    **Highest Utilized Room**
    - **Room {best['Classroom_ID']}** has a seating capacity of **{best_capacity}**, with an average occupancy of **{best_students} students**.
    - This corresponds to a utilization rate of **{best_util:.1f}%**, with **{best_unused:.1f}%** of capacity unoccupied.

    **Context**
    - The difference between the lowest and highest utilized rooms is **{best_util - worst_util:.1f} percentage points**.
    - This indicates variation in how classroom capacity is being used across the campus.
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
    
    # Calculate variation (simple and factual)
    util_gap = peak_utilize - lowest_utilize

    st.markdown(f"""
    ### **Observation: Utilization Across Time and Floors**

    The highest observed utilization occurs at:
    - **{peak_floor}** during **{peak['Time_Slot']}**, with **{peak_utilize:.2f}%** utilization.

    The lowest observed utilization occurs at:
    - **{low_floor}** during **{lowest['Time_Slot']}**, with **{lowest_utilize:.2f}%** utilization.

    **Comparison**
    - The difference between peak and lowest utilization is **{util_gap:.2f} percentage points**.

    **Interpretation**
    - Utilization levels vary across different floors and time slots.
    - Some floor-time combinations operate at higher occupancy levels, while others show lower usage.

    **Note**
    - This analysis reflects occupancy patterns only and does not directly account for operational factors such as energy usage or scheduling constraints.
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
    ### **Observation: Monthly Energy Cost Distribution**

    - The **highest total energy cost** was recorded in **{high_month['Month']}**, at **RM {high_month['Energy_Cost']:,.2f}**.
    - The **second highest** was **{second_high_month['Month']}**, at **RM {second_high_month['Energy_Cost']:,.2f}**.
    - The **lowest** was **{low_month['Month']}**, at **RM {low_month['Energy_Cost']:,.2f}**.

    **Comparison**
    - The difference between the highest and second highest month is **RM {difference:,.2f}**.

    #### **Floor-Level Breakdown**

    **{high_month['Month']} (Highest Month)**
    - Highest floor-level cost: **{high_floor_name_high}** (RM {high_floor_high_month['Energy_Cost']:,.2f})
    - Lowest floor-level cost: **{low_floor_name_high}** (RM {low_floor_high_month['Energy_Cost']:,.2f})

    **{second_high_month['Month']} (Second Highest)**
    - Highest floor-level cost: **{high_floor_name_second}** (RM {high_floor_second_month['Energy_Cost']:,.2f})
    - Lowest floor-level cost: **{low_floor_name_second}** (RM {low_floor_second_month['Energy_Cost']:,.2f})

    **{low_month['Month']} (Lowest Month)**
    - Highest floor-level cost: **{high_floor_name_low}** (RM {high_floor_low_month['Energy_Cost']:,.2f})
    - Lowest floor-level cost: **{low_floor_name_low}** (RM {low_floor_low_month['Energy_Cost']:,.2f})

    **Interpretation**
    - Energy costs vary across months and across floors within each month.
    - Certain floors consistently account for higher portions of total cost within a given month.

    **Note**
    - These observations reflect recorded energy costs and do not directly indicate the underlying causes (e.g., occupancy levels, equipment usage, or operational settings).
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

    # Prevent division by zero when minimum cost is 0
    if min_cost == 0:
        percent_diff = 0.0
    else:
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

    cv = (std_dev / avg_cost) if avg_cost != 0 else 0
    share_gap = dominant_floor["Contribution (%)"] - least_floor["Contribution (%)"]
    
    st.markdown(f"""
    ### **Observation: Energy Cost Distribution by Floor**

    - The highest contributing floor is **{dom_floor}**, accounting for **{dominant_floor['Contribution (%)']:.2f}%** of total energy cost.
    - The lowest contributing floor is **{lst_floor}**, accounting for **{least_floor['Contribution (%)']:.2f}%**.

    **Distribution Metrics**
    - Average floor-level cost: **RM {avg_cost:,.2f}**
    - Difference in contribution: **{share_gap:.2f}%**
    - Difference in cost between top and lowest floor: **RM {range_diff:,.2f}** (**{percent_diff:.2f}% difference**)

    **Interpretation**
    - The distribution shows **{interpret_cv(cv)}** across floors.
    - Energy cost distribution varies across floors.
    - The difference between the highest and lowest contributing floors indicates how costs are spread within the building.

    **Note**
    - These values describe cost distribution only and do not directly indicate underlying causes such as occupancy levels or equipment usage.
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