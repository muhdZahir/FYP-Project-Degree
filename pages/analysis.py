from core.imports import st, pd, LinearRegression
from core.processing import compute_utilization, compute_contribution, get_room_stats, get_heatmap_data, get_heatmap_pivot, get_monthly_energy, get_total_energy_cost, center_button, require_role
from core.visualization import plot_underutilized_rooms, plot_heatmap, plot_monthly_cost, plot_pie, plot_correlation
from core.insights import underutilized_rooms_findings, heatmap_findings, monthly_energy_cost_findings, pie_findings, correlation_findings

require_role(["Manager"])

if "batch" not in st.session_state:
    st.session_state["batch"] = st.session_state["batch_name"]

def run_classroom_analysis(class_df):
    df = compute_utilization(class_df)

    # Display Average Utilization
    avg_util = df["Utilization"].mean() * 100
    st.metric("Average Classroom Utilization", f"{avg_util:.2f}%")

    # ------------------------------------------
    # Bar Chart: Worst Utilized Rooms
    # ------------------------------------------
    st.subheader("Worst Utilized Rooms")
    with st.expander("🔍 How this analysis works"):
            st.markdown("""
            **📉 The 'Ghost Rooms' (Highest Wasted Space)** 
                        
            💡 **What this means:** These are the used classrooms with too many empty seats than the actual number of students. If we move these small classes to smaller rooms, we can turn off the lights and AC in these large halls entirely.  
            
            > 📂 **Where the data comes from:** Classroom Data *(Columns: Classroom Name, Capacity, Actual Occupancy)*  
            > 📊 **Chart used:** Bar Chart  
            > 💡 **Why this Chart:** It makes it easy to compare rooms side-by-side. Because it tracks utilization, the **lowest** bar shows you the biggest space-waster instantly.  
            > 🧮 **How it is calculated:** We check all rooms and flag the ones that are mostly empty. *(Calculation: [Average Students Present ÷ Total Seats] × 100)*
            """)
    # added an interactive slider to let users choose how many underutilized rooms they want to view
    max_rooms = df["Classroom_Name"].nunique()
    max_slider = min(50, max_rooms)

    if max_slider <= 3:
        n_rooms = max_slider
        st.info(f"Only {max_slider} underutilized rooms available.")
    else:
        n_rooms = st.slider("How many underutilized rooms do you want to view?", min_value=3, max_value=max_slider, value=min(5, max_slider), step=1)

    # Group by Room to get average utilization
    room_stats = get_room_stats(df)
    
    top_underutilized = room_stats.sort_values("Percent_Utilize", ascending=True).head(n_rooms)

    # Visualize top underutilized rooms bar chart
    bar_fig = plot_underutilized_rooms(top_underutilized, n_rooms)
    st.plotly_chart(bar_fig, width="stretch")
    st.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")

    # ==========================================
    # Findings: Worst Utilized Rooms
    # ==========================================
    st.write("#### Findings: Worst Utilized Rooms")
    with st.expander("Show details"):
        # Compute percentile for each room
        room_stats["percentile"] = room_stats["Percent_Utilize"].rank(pct=True)

        # Data Extraction & Baseline Calculation
        rooms_utilize = room_stats.sort_values("Percent_Utilize", ascending=True)
        campus_avg = df["Percent_Utilize"].mean()
        worst_room = rooms_utilize.iloc[0]
        second_worst = rooms_utilize.iloc[1]
        best_room = rooms_utilize.iloc[-1]

        # Display underutilized rooms findings
        underutilized_rooms_findings(worst_room, second_worst, best_room, campus_avg)

    # ------------------------------------------
    # Heatmap: Floor vs Time Slot
    # ------------------------------------------
    st.subheader("Utilization Heatmap (Floor vs Time)")
    with st.expander("🔍 How this analysis works"):
            st.markdown("""
            **🔥 Busiest Zones vs ❄️ Wasted Zones**         
                
            💡 **What this means:** Darker areas show packed schedules. Lighter areas mean the floor is mostly empty, but we might still be running electricity there.  
            
            > 📂 **Where the data comes from:** Classroom Data *(Columns: Floor, Time Slot, Utilization Rate)*  
            > 📊 **Chart used:** Color-Coded Heatmap  
            > 💡 **Why this Chart:** It acts like a thermal camera for the building. It lets you easily spot "dead zones" where electricity is running for an empty floor.  
            > 🧮 **How it is calculated:** We group student attendance by floor and time to find periods where the floor is used but nobody is around.
            """)
    # Pivot data for heatmap
    heatmap_data = get_heatmap_data(df)
    heatmap_pivot = get_heatmap_pivot(heatmap_data)
    
    # Visualize floor x time slot heatmap chart
    heat_fig = plot_heatmap(heatmap_pivot)
    st.plotly_chart(heat_fig, width="stretch")
    st.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")

    # ==========================================
    # Findings: Utilization Heatmap
    # ==========================================
    st.write("#### Findings: Floor vs Time Utilization")
    with st.expander("Show details"):
        # Data Extraction
        peak_usage = heatmap_data.loc[heatmap_data["Percent_Utilize"].idxmax()]
        lowest_usage = heatmap_data.loc[heatmap_data["Percent_Utilize"].idxmin()]

        # Display floor x time findings
        heatmap_findings(peak_usage, lowest_usage) 

def run_energy_analysis(energy_df):
    df = energy_df.copy()
    # Total energy per month
    monthly_energy = get_monthly_energy(df)

    # Average monthly cost
    avg_monthly_cost = monthly_energy["Energy_Cost"].mean()
    # Display average monthly energy cost with commas as thousand separators and 2 decimal places
    st.metric("Average Monthly Energy Cost: ", f"RM {avg_monthly_cost:,.2f}")
    
    # ------------------------------------------
    # Line chart: Monthly Energy Cost Per Floor
    # ------------------------------------------
    st.subheader("Monthly Energy Cost per Floor")
    with st.expander("🔍 How this analysis works"):
            st.markdown("""
            **⚡ Monthly Energy Cost per Floor**
                        
            💡 **What this means:** This chart tracks electricity spending over time. A flat line means normal usage, but a sudden jump means a floor started to use much more power.  
            
            > 📂 **Where the data comes from:** Energy Data *(Columns: Month, Floor, Energy Cost)*  
            > 📊 **Chart used:** Line Chart  
            > 💡 **Why this Chart:** It shows your spending over time. It helps you quickly see if your bills are staying flat, spiking during certain months, or slowly creeping up.  
            > 🧮 **How it is calculated:** We track the total electric bill for each floor across different months to spot unusual spending.
            """)
    month_order = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    df["Month"] = pd.Categorical(
        df["Month"],
        categories=month_order,
        ordered=True
    )
    df = df.sort_values("Month")

    # Visualize monthly energy cost line chart
    line_fig = plot_monthly_cost(df)
    st.plotly_chart(line_fig, width="stretch")
    st.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")

    # ==========================================
    # Findings: Monthly Energy Cost per Floor
    # ==========================================
    st.write("#### Findings: Monthly Energy Cost per Floor")
    with st.expander("Show details"):
        # Sort by energy cost (descending)
        monthly_sorted = monthly_energy.sort_values(by="Energy_Cost", ascending=False)
        monthly_energy_cost_findings(monthly_sorted, df)

    # ------------------------------------------
    # Pie chart: Percentage Contribution
    # ------------------------------------------
    st.subheader("Energy Cost Contribution by Floor")
    with st.expander("🔍 How this analysis works"):
            st.markdown("""
            **🍰 Energy Cost Contribution by Floor** 
                        
            💡 **What this means:** This shows which floor is using the biggest slice of your budget. If a floor with very few students takes up a huge chunk, energy is being wasted.  
            
            > 📂 **Where the data comes from:** Energy Data *(Columns: Floor, Energy Cost)*   
            > 📊 **Chart used:** Pie Chart  
            > 💡 **Why this Chart:** It visually splits the budget. If one floor takes up half the pie but only has a few classes, you will know where the electricity is being wasted.  
            > 🧮 **How it is calculated:** We calculate the total energy cost and split it by floor to show each floor's percentage of the total bill.
            """)

    # Calculate total energy cost of the whole floor
    floor_energy_cost = get_total_energy_cost(df)

    total_energy_cost = df["Energy_Cost"].sum()
    # Display total energy cost with commas as thousand separators and 2 decimal places
    st.metric("Total Energy Cost:", f"RM {total_energy_cost:,.2f}")

    # Visualize energy cost contribution pie chart
    pie_fig = plot_pie(floor_energy_cost)
    st.plotly_chart(pie_fig, width="stretch")
    st.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")
    # ==========================================
    # Findings: Energy Cost Contribution
    # ==========================================
    st.write("#### Findings: Energy Cost Contribution by Floor")
    with st.expander("Show details"):
        # Calculate percentage contribution
        floor_energy_cost = compute_contribution(floor_energy_cost, total_energy_cost)

        # Sort by energy cost (descending)
        cost_sorted = floor_energy_cost.sort_values(by="Energy_Cost", ascending=False, ignore_index=True)
        cost_sorted = cost_sorted.rename(columns=lambda x: x.replace("_", " ").title())

        st.markdown("Top Energy Cost Contributor by Floor:")
        st.dataframe(cost_sorted.head(5).style.format({"Energy Cost": "RM {:,.2f}", "Contribution (%)": "{:.2f}%"}))

        pie_findings(floor_energy_cost)

def run_correlation_analysis(class_df):
    correlation_df = class_df[["Classroom_Name", "Actual_Occupancy", "Energy_Cost"]].copy()
    
    # Linear Regression for Trendline
    # We will fit a simple linear regression model to the data to get the trendline.
    # This will help us understand the overall relationship between occupancy and energy cost.
    # ==============================================================================
    # PENJELASAN (Untuk Supervisor):
    # Isu Data Science: "Kenapa tajuk Correlation tapi guna graf Linear Regression?"
    # JAWAPAN: Kedua-dua metrik digunakan serentak.
    # - Correlation (r): Mengira 'Kekuatan Hubungan' antara bilangan pelajar & kos elektrik.
    # - Linear Regression: Digunakan untuk visualisasi (trendline) dan mencari nilai 
    #   'Base Autopilot Cost' (Y-Intercept) serta pertambahan kos untuk 1 orang pelajar (Slope).
    # ==============================================================================
    X = correlation_df["Actual_Occupancy"].values.reshape(-1, 1)
    y = correlation_df["Energy_Cost"].values

    model = LinearRegression()
    model.fit(X, y)
    correlation_df["Predicted_Cost"] = model.predict(X)

    # Visualize correlation scatter plot
    corr_fig = plot_correlation(correlation_df)
    st.plotly_chart(corr_fig, width="stretch")
    st.caption("💡 **Pro Tip:** Hover your mouse over the graphs for more information.")

    # ==========================================
    # Findings: Correlation Analysis
    # ==========================================
    st.write("#### Findings: Occupancy vs Energy Cost Correlation")
    with st.expander("Show details"):
        # Statistical Calculations
        r2_score = model.score(X, y)
        corr_coef = correlation_df['Actual_Occupancy'].corr(correlation_df['Energy_Cost'])
        slope = model.coef_[0]
        # Added y-intercept to calculate the Base Autopilot Cost at 0 students
        y_intercept = model.intercept_

        correlation_findings(corr_coef, slope, r2_score, y_intercept, correlation_df)

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("ANALYSIS")
    st.write("This page acts as an X-ray for your campus. It breaks down your actual student attendance and "
             "electricity bills to expose hidden patterns, 'ghost rooms', and expensive peak hours.\n"
    )
    st.write(f"Choose the semester data Batch stored in the system for analysis.")
            
    class_df = st.session_state.get('class_df', pd.DataFrame())
    energy_df = st.session_state.get('energy_df', pd.DataFrame())
    batch_name = st.session_state.get('batch_name', None)

    if not class_df.empty or not energy_df.empty:
        st.divider()
        col2 = center_button()
        with col2:
            if st.button(label="Start Analyzing", width="stretch", icon=":material/analytics:", key="blue"):
                st.session_state['show'] = True
    else:
        st.divider()
        st.warning("⚠️ **Wait! You haven't loaded any data yet.**\n\nPlease look at the left sidebar, select a **Data Batch**, and click **Load Data** to start your analysis.")

    if st.session_state.get('show', False):
        st.title(f"Data Analysis & Insights: {batch_name}")
        # ==========================================
        # CLASSROOM ANALYSIS
        # ==========================================
        if not class_df.empty:
            st.header("Classroom Utilization Analysis")

            with st.spinner("Analyzing data...", show_time=True):
                run_classroom_analysis(class_df)
                st.divider()
        elif class_df.empty:
            st.info(f"No classroom data available for batch {batch_name} to analyze classroom.")

        # ==========================================
        # ENERGY ANALYSIS
        # ==========================================
        if not energy_df.empty:
            st.header("Energy Cost Analysis")

            with st.spinner("Analyzing data...", show_time=True):
                run_energy_analysis(energy_df)
                st.divider()          
        elif energy_df.empty:
            st.info(f"No energy data available for batch {batch_name} to analyze energy.")

        # ==========================================
        # CORRELATION ANALYSIS
        # ==========================================
        if not class_df.empty:
            st.subheader("Correlation Analysis")
            with st.expander("🔍 How this analysis works"):
                st.markdown("""
                **📈 Alignment Test: Electric Bill vs. Student Attendance** 
                                
                💡 **What this means:** We want the dots to go up in a straight line as more students attend. If the dots are scattered everywhere, it means electricity is running blindly even when rooms are empty.  
                
                > 📂 **Where the data comes from:** Combined Classroom & Energy Data *(Columns: Actual Occupancy, Energy Cost)*  
                > 📊 **Chart used:** Scatter Plot with a Trendline  
                > 💡 **Why this Chart:** It checks if your electric bill makes sense based on student numbers. A straight line means your building is efficient; scattered dots mean money is being wasted.  
                > 🧮 **How it is calculated:** We measure if the electric bills go up and down based on actual human traffic, or if they stay high even when the campus is empty.
                """)

            with st.spinner("Analyzing data...", show_time=True):
                run_correlation_analysis(class_df)
        elif class_df.empty:
            st.info(f"No classroom data available for batch {batch_name} to correlate.")
