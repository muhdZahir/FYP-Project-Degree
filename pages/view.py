from core.imports import st, pd
from core.processing import center_button, require_role

require_role(["Manager"])

if "batch" not in st.session_state:
    st.session_state["batch"] = st.session_state["batch_name"]

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("VIEW DATA RECORDS")
    st.write(f"View your data records stored in the system. You can only view the data for its information.\n")
    st.write(f"Choose the semester data Batch stored in the system for display.\n")

    class_df = st.session_state.get('class_df', pd.DataFrame())
    energy_df = st.session_state.get('energy_df', pd.DataFrame())
    batch_name = st.session_state.get('batch_name', None)

    if not class_df.empty or not energy_df.empty:
        st.divider()
        col2 = center_button()
        with col2:
            if st.button(label="View Data", width="stretch", icon=":material/view_list:", key="blue"):
                st.session_state['show'] = True
    else:
        st.divider()
        st.warning("⚠️ **Wait! You haven't loaded any data yet.**\n\nPlease look at the left sidebar, select a **Data Batch**, and click **Load Data** to start your analysis.")

    if st.session_state.get('show', False):
        st.subheader(f"Data Records for Batch: {batch_name}")

        if 'class_df' in locals() and not class_df.empty:
            st.subheader(f"Classroom Data Records")
            # Display the classroom data with formatted column names for better readability and only essential columns
            class_df_renamed = class_df.rename(columns=lambda x: x.replace("_", " ").title())
            st.dataframe(class_df_renamed[["Classroom Id", "Floor", "Capacity", "Scheduled Hours", "Actual Occupancy", "Day", "Time Slot", "Week"]])

        if 'energy_df' in locals() and not energy_df.empty:
            st.subheader(f"Energy Data Records")
            # Display the energy data with formatted column names for better readability and only essential columns
            energy_df_renamed = energy_df.rename(columns=lambda x: x.replace("_", " ").title())
            st.dataframe(energy_df_renamed[["Floor", "Month", "Energy Kwh", "Energy Cost"]])
