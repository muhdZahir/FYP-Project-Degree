from core.imports import st, pd, time, db, datetime, re
from main import require_role

require_role(["IT Staff"])

if "batch" not in st.session_state:
    st.session_state["batch"] = st.session_state["batch_name"]

# Initialize session state for persistence across reruns
if 'edit_success' not in st.session_state:
    st.session_state['edit_success'] = False
if 'edit' not in st.session_state:
    st.session_state['edit'] = False
if 'edit_pending' not in st.session_state:
    st.session_state['edit_pending'] = None
if 'delete_pending' not in st.session_state:
    st.session_state['delete_pending'] = None

def save_batch_name(old_name, new_name):
    """Perform the actual batch name update operation."""
    with st.spinner("Updating batch name..."):
        if db.update_batch_name(old_name, new_name):
            st.session_state['batch_name'] = new_name
            st.session_state['batch'] = new_name
            st.session_state["class_df"] = db.load_from_db("Classroom", st.session_state['batch'])
            st.session_state['energy_df'] = db.load_from_db("Energy", st.session_state['batch'])
            st.session_state['edit_pending'] = None  # Reset the flag after saving
            st.session_state['edit_success'] = True
            st.session_state['edit'] = False

            st.toast(f"Batch name updated to '{new_name}'.", icon="✅")
            time.sleep(1)  # brief pause to ensure toast is seen
        else:
            st.toast("Failed to update batch name. Please try again.")
            time.sleep(1)  # brief pause to ensure toast is seen

def confirm_edit_batch_name(old_name, new_name):
    """Displays the confirmation UI for batch name change."""
    st.warning(f"Are you sure you want to change the batch name from '**{old_name}**' to '**{new_name}**'?")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("Yes, Change Name", on_click=save_batch_name, args=(old_name, new_name), key="green")
    with col2:
        st.button("No, Keep Original", on_click=cancel_edit_batch_name, key="cancel_edit_batch_name_btn")

def cancel_edit():
    """Cancels edit action and resets the input field."""
    st.session_state['edit'] = False

def cancel_edit_batch_name():
    """Cancels the batch name edit action and resets the input field."""
    st.session_state['edit_pending'] = None

def delete_data(data_type, batch_name):
    """Perform the actual delete operation."""
    with st.spinner("Clearing " + data_type + " data..."):
        if data_type == "Classroom" and db.clear_classroom_data(batch_name):
            st.cache_data.clear()  # Clear cached data to ensure UI updates with the cleared data
            st.toast(f"Classroom data for batch '{batch_name}' has been cleared.", icon="✅")
            time.sleep(1)  # brief pause to ensure toast is seen

            # If classroom data is already cleared, clear the batch record as well to keep the database clean
            if db.energy_batch_unique(batch_name):
                db.clear_batch(batch_name)
                st.session_state['batch'] = None
                st.session_state['batch_name'] = None
                st.session_state['show'] = False

            st.session_state.class_df = pd.DataFrame()
            st.session_state['edit_pending'] = None
            st.session_state['edit'] = False
            st.session_state['delete_pending'] = None # Reset the flag after deletion

        elif data_type == "Energy" and db.clear_energy_data(batch_name):
            st.cache_data.clear()  # Clear cached data to ensure UI updates with the cleared data
            st.toast(f"Energy data for batch '{batch_name}' has been cleared.", icon="✅")
            time.sleep(1)  # brief pause to ensure toast is seen
            
            # If energy data is already cleared, clear the batch record as well to keep the database clean
            if db.class_batch_unique(batch_name):
                db.clear_batch(batch_name)
                st.session_state['batch'] = None
                st.session_state['batch_name'] = None
                st.session_state['show'] = False
            
            st.session_state.energy_df = pd.DataFrame()
            st.session_state['edit_pending'] = None
            st.session_state['edit'] = False
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

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("MANAGE DATA RECORDS")
    st.write(f"Manage your data records stored in the system. You can view the data, edit the batch name, clear old data, and maintain an organized database for analysis.\n")
    st.write(f"Choose the semester data Batch stored in the system for management.\n")
    st.caption("Batch name is a label that groups related data together. It identifies a specific dataset period — usually a semester and year.")
    st.write("")

    available_batches = db.get_unique_batches()

    if available_batches:
        if (
            st.session_state["batch"] is None or
            st.session_state["batch"] not in available_batches
        ):
            st.session_state["batch"] = st.session_state["batch_name"]

    if not available_batches:
        st.warning("No data found in database. Please upload and save files first.")
    else:
        if "batch" not in st.session_state:
            st.session_state.batch = None

        batch = st.selectbox(
            "Select Data Batch:",
            available_batches,
            index=0,
            key="batch",
            width=500
        )

        if st.button("Load Data", key="load_db_btn"):
            if st.session_state["batch"] is None:
                st.info("Choose a data batch and click 'Load Data'.")
                st.session_state["class_df"] = pd.DataFrame()
                st.session_state["energy_df"] = pd.DataFrame()
                st.session_state["batch_name"] = None
                st.session_state['edit_pending'] = None
                st.session_state['delete_pending'] = None
                st.session_state['show'] = False
            else:
                with st.spinner("Fetching data from SQL Engine..."):
                    # store loaded dataframes in session_state so they persist across interactions
                    st.session_state["class_df"] = db.load_from_db("Classroom", st.session_state['batch'])
                    st.session_state["energy_df"] = db.load_from_db("Energy", st.session_state['batch'])
                    st.session_state["batch_name"] = st.session_state['batch']
                    st.session_state['edit_pending'] = None
                    st.session_state['delete_pending'] = None
                    st.session_state['show'] = True
                    st.toast("Data loaded successfully.", icon="✅")

        st.divider()

        class_df = st.session_state.get('class_df', pd.DataFrame())
        energy_df = st.session_state.get('energy_df', pd.DataFrame())
        batch_name = st.session_state.get('batch_name', None)
        edit_batch_name = batch_name

        if st.session_state['show']:
            st.header(f"Data Records for Batch: {batch_name}")
            st.write(f"Review the data records for the selected batch. You can choose to edit the batch name or clear the Classroom or Energy data, but "
                    f"please note that the delete action is irreversible and will permanently remove the data from the database.\n"
                    f"Make sure to double-check the data before confirming deletion.\n")
            
            if st.session_state['edit'] == True:
                st.text(f"Edit Batch Name:")
                # update batch name and save to db if user edits the batch name
                match = re.match(r"Sem (\d) (\d{4})", batch_name)

                if match:
                    current_sem = int(match.group(1))
                    current_year = int(match.group(2))
                else:
                    # fallback defaults
                    current_sem = 1
                    current_year = datetime.now().year

                col1, col2, col3 = st.columns([0.2, 1, 1])
                with col1:
                    st.header("Sem")

                with col2:
                    sem = st.selectbox(
                        "Semester", 
                        [1, 2, 3],
                        index=[1, 2, 3].index(current_sem),
                        key="edit_semester"
                    )
                    
                with col3:
                    current_calendar_year = datetime.now().year
                    year_range = list(range(current_calendar_year - 10, current_calendar_year + 1))

                    year = st.selectbox(
                        "Year",
                        year_range,
                        index=year_range.index(current_year),
                        key="edit_year"
                    )
                new_batch_name = f"Sem {sem} {year}"
            else:
                st.markdown(f"#### Batch Name: {batch_name}")
                if st.button("Edit", key="edit_btn"):
                    st.session_state['edit'] = True
                    st.rerun()  # Rerun immediately to show the edit UI
            
            if st.session_state["edit"] == True:
                if st.session_state['edit_pending'] == "Batch Name":
                    confirm_edit_batch_name(batch_name, new_batch_name)
                else:
                    col4, col5 = st.columns([1, 1])
                    with col4:
                        if st.button("Save Batch Name", key="green"):
                            if st.session_state['edit_success']:
                                st.session_state['edit_success'] = False
                                st.rerun()
                            
                            if new_batch_name == batch_name:
                                st.info("Batch name is unchanged. No update occurred.", width=500)
                            else:
                                if new_batch_name != batch_name:
                                    if not db.batch_unique(new_batch_name):
                                        st.error(f"A Batch with the name '{new_batch_name}' already exists. Please choose a different name.")
                                    else:
                                        st.session_state['edit_pending'] = "Batch Name"
                                        # Rerunning immediately after setting the flag updates the UI to show the confirmation
                                        st.rerun()
                    with col5:
                        if st.button("Cancel Edit",  on_click=cancel_edit, key="cancel_edit_btn"):
                            cancel_edit()
                            st.rerun()  # Rerun immediately to reset the UI

            if 'class_df' in locals() and not class_df.empty:
                st.subheader(f"Classroom Data Records")
                # Display the classroom data with formatted column names for better readability and only essential columns
                class_df_renamed = class_df.rename(columns=lambda x: x.replace("_", " ").title())
                st.dataframe(class_df_renamed[["Classroom Id", "Floor", "Capacity", "Scheduled Hours", "Actual Occupancy", "Day", "Time Slot", "Week"]])

                if st.session_state['delete_pending'] == "Classroom":
                    confirm_delete("Classroom", batch_name)
                else:
                    if st.button("Clear Classroom Data", type="primary", key="clear_class_btn"):
                        st.session_state['delete_pending'] = "Classroom"
                        # Rerunning immediately after setting the flag updates the UI to show the confirmation
                        st.rerun()

            if 'energy_df' in locals() and not energy_df.empty:
                st.subheader(f"Energy Data Records")
                # Display the energy data with formatted column names for better readability and only essential columns
                energy_df_renamed = energy_df.rename(columns=lambda x: x.replace("_", " ").title())
                st.dataframe(energy_df_renamed[["Floor", "Month", "Energy Kwh", "Energy Cost"]])

                if st.session_state['delete_pending'] == "Energy":
                    confirm_delete("Energy", batch_name)
                else:
                    if st.button("Clear Energy Data", type="primary", key="clear_energy_btn"):
                        st.session_state['delete_pending'] = "Energy"
                        # Rerunning immediately after setting the flag updates the UI to show the confirmation
                        st.rerun()
