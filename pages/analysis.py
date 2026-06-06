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
    with st.expander("🔍 View Analysis Logic (Data Sources, Charts & Math)"):
            st.markdown("""
            **📉 The 'Ghost Rooms' (Highest Wasted Space)** 
                        
            💡 **What this means:** These are rooms that are ranked lowest in terms of utilization. If we move these classes, we can turn off the electric power
            in those large rooms entirely.  
            
            > 📂 **Data Source:** Classroom Data *(Columns: Classroom_Name, Capacity, Actual_Occupancy)*  
            > 📊 **Chart Selection:** Bar Chart  
            > 💡 **Why this Chart:** It makes it incredibly easy to compare rooms side-by-side. The tallest bar instantly shows you the biggest space-waster
            without needing to read a single number.  
            > 🧮 **Audit Rule:** Scans all rooms and flags the ones that are consistently almost empty. *(Formula: [Average Students Present ÷ Physical Seats]
            × 100)*
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
    with st.expander("🔍 View Analysis Logic (Data Sources, Charts & Math)"):
            st.markdown("""
            **🔥 Busiest Zones vs ❄️ Wasted Zones**         
                
            💡 **What this means:** Red areas show packed schedules. White areas mean we are burning electricity for empty floors.  
            
            > 📂 **Data Source:** Classroom Data *(Columns: Floor, Time_Slot, Percent_Utilize)*  
            > 📊 **Chart Selection:** Color-Coded Heatmap  
            > 💡 **Why this Chart:** It acts like a thermal camera for the building. Red means busy, white means quiet. It lets you spot completely empty
            floors that are still running electricity at a single glance.  
            > 🧮 **Audit Rule:** Groups student attendance by floor and time to find "dead zones" where the building is open but nobody is there.
            *(Formula: Total Students grouped by Floor and Time Slot)*
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
    with st.expander("🔍 View Analysis Logic (Data Sources, Charts & Math)"):
            st.markdown("""
            **⚡ Monthly Energy Cost per Floor**
                        
            💡 **What this means:** This chart tracks your electricity spending over time. A flat line means stable usage, but a sudden jump means a floor suddenly
            started to consume more power.  
            
            > 📂 **Data Source:** Energy Data *(Columns: Month, Floor, Energy_Cost)*  
            > 📊 **Chart Selection:** Line Chart  
            > 💡 **Why this Chart:** It shows the timeline of your spending. It helps you quickly see if your bills are staying flat, spiking during certain
            months, or slowly creeping up over time.  
            > 🧮 **Audit Rule:** Tracks the total electric bill for each floor across different months to catch unusual spending spikes. *(Formula: Sum of
            Energy Cost per Floor per Month)*
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
    with st.expander("🔍 View Analysis Logic (Data Sources, Charts & Math)"):
            st.markdown("""
            **🍰 Energy Cost Contribution by Floor** 
                        
            💡 **What this means:** This shows exactly who is eating the biggest slice of your budget. If a floor with very few students takes up a huge
            chunk, you have a major leak.  
            
            > 📂 **Data Source:** Energy Data *(Columns: Floor, Energy_Cost)*   
            > 📊 **Chart Selection:** Pie Chart  
            > 💡 **Why this Chart:** It visually divides the budget. If one floor takes up half the pie but only has a few classes, you know exactly where to
            send maintenance.  
            > 🧮 **Audit Rule:** Calculates the total energy cost and splits it by floor to show each floor's percentage of the total bill. *(Formula: Floor
            Energy Cost ÷ Total Campus Energy Cost)*
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
    st.write(f"Analyze the data and generate insights to identify areas for improvement. The system provides insights into "
            f"classroom usage and energy/electrical cost patterns, helping you make informed decisions about resource allocation and cost management.\n"
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
            with st.expander("🔍 View Analysis Logic (Data Sources, Charts & Math)"):
                st.markdown("""
                **📈 Alignment Test: Bill (Energy Cost) vs. Students (Occupancy)** 
                                
                💡 **What this means:** We want these dots to go up in a straight line. If the data is scattered everywhere, it means the electricity
                is running blindly in empty rooms.  
                
                > 📂 **Data Source:** Combined Classroom & Energy Data *(Columns: Actual_Occupancy, Energy_Cost)*  
                > 📊 **Chart Selection:** Scatter Plot with a Trendline  
                > 💡 **Why this Chart:** It proves if your electric bill is actually following your students. Dots lined up straight mean your building is smart;
                scattered dots mean your building is wasting money.  
                > 🧮 **Audit Rule:** Measures if electric bills go up and down based on actual human traffic, or if they stay high even when the campus is empty.
                *(Formula: Correlation between Energy Cost and Actual Student Count)*
                """)

            with st.spinner("Analyzing data...", show_time=True):
                run_correlation_analysis(class_df)
        elif class_df.empty:
            st.info(f"No classroom data available for batch {batch_name} to correlate.")
