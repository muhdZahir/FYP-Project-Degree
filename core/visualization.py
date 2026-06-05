# All charts visualization
from core.imports import px

# update chart
def style_chart(fig, title_x):
    fig.update_layout(
        title=dict(
            font=dict(size=20),   # ← change size here
            x=title_x                 # ← position the title
        ),
        xaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change x axis font (title and tick) size
        yaxis=dict(title_font=dict(size=20), tickfont=dict(size=15)), # ← change y axis font (title and tick) size
        coloraxis_colorbar=dict(title_font=dict(size=14), tickfont=dict(size=15)) # ← change legend (color lables) font size
    )
    return fig

# plot underutilized rooms
def plot_underutilized_rooms(df, n):
    fig = px.bar(
        df,
        x="Classroom_Name",
        y="Percent_Utilize",
        color="Percent_Utilize",
        color_continuous_scale="Reds",
        range_color=[0, 100],
        title=f"Top {n} Rooms with Lowest Utilization Rate (%)",
        text_auto='.1f',
        labels={"Classroom_Name": "Classroom Name","Percent_Utilize": "Utilization (%)"}
    )
    fig.update_layout(
        xaxis=dict(type='category'), # ← change x axis font (title and tick) size
    )
    return style_chart(fig, 0.25)

# plot floor x time slot
def plot_heatmap(df):
    fig = px.imshow(
        df,
        labels=dict(x="Time Slot", y="Floor", color="Utilization (%)"),
        color_continuous_scale="Reds",
        range_color=[0, 100],
        title="Avg Utilization Rate (%) by Floor and Time"
    )
    return style_chart(fig, 0.25)

# plot monthly energy cost per floor
def plot_monthly_cost(df):
    fig = px.line(
        df,
        x="Month",
        y="Energy_Cost",
        color="Floor",
        labels={"Energy_Cost": "Energy Cost (RM)"},
        title="Floor Energy Cost by Month",
        markers=True
    )
    return style_chart(fig, 0.35)

# plot floor energy contribution
def plot_pie(df):
    fig = px.pie(
        df,
        names="Floor",
        values="Energy_Cost",
        title="Energy Cost (RM) Contribution by Floor to Total Energy Cost",
        labels={"Energy_Cost": "Energy Cost (RM)"}
    )
    return style_chart(fig, 0.2)

# plot correlation
def plot_correlation(corr_df, color, text):
    fig = px.scatter(
        corr_df,
        x="Actual_Occupancy",
        y="Energy_Cost",
        color=color,
        size="Energy_Cost",
        title=text,
        labels={"Actual_Occupancy": "Total Occupancy", "Energy_Cost": "Total Cost (RM)"},
        hover_data=[c for c in ["Month", "Floor"] if c in corr_df.columns]
    )
    fig = style_chart(fig, 0.2)

    # Add trendline trace
    line_data = corr_df.sort_values("Actual_Occupancy")
    fig.add_traces(px.line(line_data, x="Actual_Occupancy", y="Predicted_Cost").data[0])
    fig.data[-1].update(line=dict(color='black', width=3, dash='dash'), name='Trendline')
    return fig

# plot next semester classroom demand
def plot_next_classroom_demand(combined):
    fig = px.line(
        combined,
        x="Week",
        y="Percent_Utilize",
        color="Type", 
        labels={"Percent_Utilize": "Avg Utilization (%)"},
        title="Classroom Demand Trend",
        markers=True
    )
    return style_chart(fig, 0.1)

# plot next month energy cost
def plot_next_energy_cost(combined):
    fig = px.line(
        combined,
        x="Month_Num",
        y="Energy_Cost",
        color="Type", 
        labels={"Month_Num": "Month", "Energy_Cost": "Total Energy Cost (RM)"},
        title="Energy Cost Trend",
        markers=True
    )
    return style_chart(fig, 0.2)
