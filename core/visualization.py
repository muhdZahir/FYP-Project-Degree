# All charts visualization
from core.imports import px

# update chart
def style_chart(fig, title_x):
    fig.update_layout(
        title=dict(
            font=dict(size=20),   # ← change size here
            x=title_x             # ← position the title
        ),
        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
        coloraxis_colorbar=dict(title_font=dict(size=14), tickfont=dict(size=15)) # ← change legend (color lables) font size
    )
    return fig

# helper to sort floor names numerically
def get_category_orders(df):
    orders = {}
    if "floor" in df.columns:
        def extract_num(floor_str):
            try:
                return int(''.join(filter(str.isdigit, str(floor_str))))
            except ValueError:
                return 0
        orders["floor"] = sorted(df["floor"].unique().tolist(), key=extract_num)
    return orders

# plot underutilized rooms
def plot_underutilized_rooms(df, n):
    fig = px.bar(
        df,
        x="classroom_name",
        y="Percent_Utilize",
        color="Percent_Utilize",
        color_continuous_scale="Reds",
        labels={"Percent_Utilize": "Utilization (%)", "classroom_name": "Classroom"},
        range_color=[0, 100],
        title=f"Top {n} Rooms with Lowest Utilization Rate (%)",
        text_auto='.1f',
    )
    fig.update_traces(
        hovertemplate=
            "<b>%{x}</b><br>" +
            "Utilization: %{y:.2f}%<extra></extra>"
    )
    fig.update_layout(
        xaxis=dict(type='category'), # ← change x axis font (title and tick) size
    )
    return style_chart(fig, 0.25)

# plot floor x time slot
def plot_heatmap(df):
    # Sort floors numerically so "Floor 10" comes after "Floor 9" instead of "Floor 1"
    def extract_num(floor_str):
        try:
            # Extract digits from string, e.g., "Floor 10" -> 10
            return int(''.join(filter(str.isdigit, str(floor_str))))
        except ValueError:
            return 0
            
    sorted_floors = sorted(df.index.tolist(), key=extract_num)
    df_sorted = df.loc[sorted_floors]

    fig = px.imshow(
        df_sorted,
        color_continuous_scale="Reds",
        labels={"x": "Time Slot", "y": "Floor", "color": "Utilization (%)"},
        range_color=[0, 100],
        text_auto='.1f',
        title="Avg Utilization Rate (%) by Floor and Time",
        aspect="auto"
    )
    fig.update_traces(
        hovertemplate=
            "<b>%{y}</b><br>" +
            "Time Slot: %{x}<br>" +
            "Utilization: %{z:.2f}%<extra></extra>"
    )
    return style_chart(fig, 0.25)

# plot monthly energy cost per floor
def plot_monthly_cost(df):
    fig = px.line(
        df,
        x="month",
        y="energy_cost",
        color="floor",
        labels={"energy_cost": "Energy Cost (RM)", "month": "Month", "floor": "Floor"},
        title="Floor Energy Cost by Month",
        category_orders=get_category_orders(df),
        markers=True
    )
    fig.update_traces(
        hovertemplate=
            "<b>%{fullData.name}</b><br>" +
            "Month: %{x}<br>" +
            "Cost: RM %{y:.2f}<extra></extra>"
    )
    return style_chart(fig, 0.35)

# plot floor energy contribution
def plot_pie(df):
    fig = px.pie(
        df,
        names="floor",
        values="energy_cost",
        title="Energy Cost (RM) Contribution by Floor to Total Energy Cost",
        labels={"energy_cost": "Energy Cost (RM)", "floor": "Floor"},
        category_orders=get_category_orders(df)
    )
    fig.update_traces(
        hovertemplate=
            "<b>%{label}</b><br>" +
            "Energy Cost: RM %{value:,.2f}<br>" +
            "Contribution: %{percent}<extra></extra>"
    )
    fig.update_traces(sort=False)
    return style_chart(fig, 0.2)

# plot correlation
def plot_correlation(corr_df):
    fig = px.scatter(
        corr_df,
        x="actual_occupancy",
        y="energy_cost",
        labels={"actual_occupancy": "Occupancy", "energy_cost": "Energy Cost (RM)"},
        size="energy_cost",
        title="Correlation: Occupancy vs Energy Cost",
        render_mode="svg",
        category_orders=get_category_orders(corr_df)
    )
    fig = style_chart(fig, 0.3)

    # Add trendline trace
    line_data = corr_df.sort_values("actual_occupancy")
    fig.add_traces(px.line(line_data, x="actual_occupancy", y="predicted_cost").data[0])
    fig.data[-1].update(line=dict(color='black', width=3, dash='dash'), name='Trendline')
    
    fig.update_traces(
        hovertemplate=
            "Occupancy: %{x:.0f}<br>" +
            "Energy Cost: RM %{y:,.2f}<extra></extra>"
    )
    return fig

# plot classroom occupancy
def plot_classroom_occupancy(df):
    fig = px.line(
        df,
        x="week",
        y="actual_occupancy",
        color="Type",
        labels={"actual_occupancy": "Average Student Attendance"},
        title="Average Attendance by Week",
        markers=True
    )
    fig.update_traces(
        hovertemplate=
            "Week: %{x}<br>" +
            "Avg Attendance: %{y:.0f} students<extra></extra>"
    )
    return style_chart(fig, 0.2)

# plot monthly energy cost
def plot_monthly_energy_cost(df):
    fig = px.line(
        df,
        x="month_num",
        y="energy_cost",
        color="Type", 
        labels={"month_num": "Month", "energy_cost": "Energy Cost (RM)"},
        title="Monthly Energy Cost Trend",
        markers=True
    )
    fig.update_traces(
        hovertemplate=
            "Month: %{x}<br>" +
            "Cost: RM %{y:,.2f}<extra></extra>"
    )
    return style_chart(fig, 0.3)

# plot energy cost prediction
def plot_cost_prediction(df, occ, pred_energy):
    fig = px.line(
        df,
        x="actual_occupancy",
        y="predicted_energy_cost",
        title="Energy Cost Prediction Model",
        labels={
            "actual_occupancy": "Student Attendance",
            "predicted_energy_cost": "Predicted Energy Cost (RM)"
        }
    )
    fig.update_traces(
        hovertemplate=
            "Attendance: %{x:.0f}<br>"
            "Energy Cost: RM %{y:.2f}"
            "<extra></extra>",
    )

    fig.add_scatter(
        x=[occ], # from attendance model
        y=[pred_energy],
        mode="markers",
        name="Selected Prediction",
        marker=dict(
            color="red",
            size=8,
            symbol="diamond"
        ),
        hovertemplate=(
            "Attendance: %{x:.0f}<br>"
            "Energy Cost: RM %{y:.2f}"
            "<extra></extra>"
        )
    )
    return style_chart(fig, 0.25)