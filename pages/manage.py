from core.imports import st, pd, time, db

db.init_db()

def delete_data(data_type, batch_name):
    """Perform the actual delete operation."""
    with st.spinner("Clearing " + data_type + " data..."):
        if data_type == "Classroom" and db.clear_classroom_data(batch_name):
            st.toast(f"Classroom data for batch '{batch_name}' has been cleared.", icon="✅")
            time.sleep(1)  # brief pause to ensure toast is seen

            if db.energy_batch_unique(batch_name):
                db.clear_batch(batch_name)
                st.session_state['selected_batch'] = None
                st.session_state['batch_name'] = None

            st.session_state.class_df = pd.DataFrame()
            st.session_state['delete_pending'] = None # Reset the flag after deletion

        elif data_type == "Energy" and db.clear_energy_data(batch_name):
            st.toast(f"Energy data for batch '{batch_name}' has been cleared.", icon="✅")
            time.sleep(1)  # brief pause to ensure toast is seen
            
            if db.class_batch_unique(batch_name):
                db.clear_batch(batch_name)
                st.session_state['selected_batch'] = None
                st.session_state['batch_name'] = None
            
            st.session_state.energy_df = pd.DataFrame()
            st.session_state['delete_pending'] = None # Reset the flag after deletion

def confirm_delete(data_type, batch_name):
    """Displays the confirmation UI."""
    st.error("Are you sure you want to delete all data? This action cannot be undone.")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("Delete", type="primary", on_click=delete_data, args=(data_type, batch_name), key=f"confirm_delete_btn_{data_type}_{batch_name}")
    with col2:
        st.button("Cancel", on_click=cancel_delete, key=f"cancel_delete_btn_{data_type}")

def cancel_delete():
    """Cancels the delete action and hides the confirmation UI."""
    st.session_state['delete_pending'] = None

# Initialize session state for persistence across reruns
if 'class_df' not in st.session_state:
    st.session_state["class_df"] = pd.DataFrame()
if 'energy_df' not in st.session_state:
    st.session_state["energy_df"] = pd.DataFrame()
if 'selected_batch' not in st.session_state:
    st.session_state.selected_batch = None
if 'batch_name' not in st.session_state:
    st.session_state["batch_name"] = None
if 'show' not in st.session_state:
    st.session_state['show'] = False
if 'delete_pending' not in st.session_state:
    st.session_state['delete_pending'] = None

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("MANAGE DATA RECORDS")
    st.write(f"Manage your data records stored in the system. You can view the data, clear old data, and maintain an organized database for analysis.\n")
    st.write(f"Choose the semester data batch stored in the system for management.\n")

    available_batches = db.get_unique_batches()

    if available_batches:
        if (
            st.session_state["selected_batch"] is None or
            st.session_state["selected_batch"] not in available_batches
        ):
            st.session_state["selected_batch"] = st.session_state["batch_name"]

    if not available_batches:
        st.warning("No data found in database. Please upload and save files first.")
    else:
        if "selected_batch" not in st.session_state:
            st.session_state.selected_batch = None

        selected_batch = st.selectbox(
            "Select Data Batch:",
            available_batches,
            index=0,
            key="selected_batch"
        )

        if st.button("Load Data", key="load_db_btn"):
            if st.session_state["selected_batch"] is None:
                st.info("Choose a data batch and click 'Load Data'.")
                st.session_state["class_df"] = pd.DataFrame()
                st.session_state["energy_df"] = pd.DataFrame()
                st.session_state["batch_name"] = None
                st.session_state['show'] = False
            else:
                with st.spinner("Fetching data from SQL Engine..."):
                    # store loaded dataframes in session_state so they persist across interactions
                    st.session_state["class_df"] = db.load_from_db("Classroom", st.session_state['selected_batch'])
                    st.session_state["energy_df"] = db.load_from_db("Energy", st.session_state['selected_batch'])
                    st.session_state["batch_name"] = st.session_state['selected_batch']
                    st.session_state['show'] = True
                    st.toast("Data loaded successfully.", icon="✅")

        st.divider()

        class_df = st.session_state.get('class_df', pd.DataFrame())
        energy_df = st.session_state.get('energy_df', pd.DataFrame())
        batch_name = st.session_state.get('batch_name', None)

        if st.session_state['show']:
            if 'class_df' in locals() and not class_df.empty:
                st.subheader(f"Classroom Data Records for {batch_name}")
                st.dataframe(class_df)

                if st.session_state['delete_pending'] == "Classroom":
                    confirm_delete("Classroom", batch_name)
                else:
                    if st.button("Clear Classroom Data", type="primary", key="clear_class_btn"):
                        st.session_state['delete_pending'] = "Classroom"
                        # Rerunning immediately after setting the flag updates the UI to show the confirmation
                        st.rerun()

            if 'energy_df' in locals() and not energy_df.empty:
                st.subheader(f"Energy Data Records for {batch_name}")
                st.dataframe(energy_df)

                if st.session_state['delete_pending'] == "Energy":
                    confirm_delete("Energy", batch_name)
                else:
                    if st.button("Clear Energy Data", type="primary", key="clear_energy_btn"):
                        st.session_state['delete_pending'] = "Energy"
                        # Rerunning immediately after setting the flag updates the UI to show the confirmation
                        st.rerun()
