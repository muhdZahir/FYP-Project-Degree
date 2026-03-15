import streamlit as st # pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run main.py'. to close, press 'ctrl + c' at terminal
import pandas as pd # pip install pandas | pandas is use to analyze data from csv/xlsx
import time # to handle time delay
import plotly.express as px # pip install plotly | plotly is use to create interactive visualization/chart
import database as db  # Importing your database.py

db.init_db()

def delete_data():
    """Function to perform the actual delete operation."""
    st.write("Data has been deleted!")
    # Add your actual deletion logic here (e.g., clear database, remove items from a list)
    st.session_state['delete_pending'] = False # Reset the flag after deletion
    # You might want to rerun the script to update the UI
    st.rerun()

def confirm_delete_ui():
    """Displays the confirmation UI."""
    st.error("Are you sure you want to delete all data? This action cannot be undone.")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("Yes, Delete Forever", on_click=delete_data, key="confirm_delete_btn")
    with col2:
        st.button("Cancel", on_click=cancel_delete, key="cancel_delete_btn")

def cancel_delete():
    """Cancels the delete action and hides the confirmation UI."""
    st.session_state['delete_pending'] = False

# Initialize session state for persistence across reruns
if 'class_df_manage' not in st.session_state:
    st.session_state["class_df_manage"] = pd.DataFrame()
if 'energy_df_manage' not in st.session_state:
    st.session_state["energy_df_manage"] = pd.DataFrame()
if 'selected_batch_manage' not in st.session_state:
    st.session_state.selected_batch_manage = None
if 'delete_pending' not in st.session_state:
    st.session_state['delete_pending'] = False

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("MANAGE DATA RECORDS")

    st.write(f"Choose the semester data batch stored in the system for management.\n")

    available_batches = db.get_unique_batches()

    if not available_batches:
        st.warning("No data found in database. Please upload and save files first.")
    else:
        if "selected_batch_manage" not in st.session_state:
            st.session_state.selected_batch_manage = None

        selected_batch = st.selectbox(
            "Select Data Batch:",
            available_batches,
            index=0,
            key="selected_batch_manage"
        )

        if st.button("Load Data", key="load_db_btn"):
            if st.session_state["selected_batch_manage"] is None:
                st.info("Choose a data batch and click 'Load Data' to fetch data from database.")
                st.session_state["class_df_manage"] = pd.DataFrame()
                st.session_state["energy_df_manage"] = pd.DataFrame()

            else:
                with st.spinner("Fetching data from SQL Engine..."):
                    # store loaded dataframes in session_state so they persist across interactions
                    st.session_state["class_df_manage"] = db.load_from_db("Classroom", st.session_state['selected_batch_manage'])
                    st.session_state["energy_df_manage"] = db.load_from_db("Energy", st.session_state['selected_batch_manage'])
                    st.toast("Data loaded successfully.", icon="✅")

        class_df = st.session_state.get('class_df_manage', pd.DataFrame())
        energy_df = st.session_state.get('energy_df_manage', pd.DataFrame())
        batch_name = st.session_state.get('selected_batch_manage', None)

        if not class_df.empty:
            st.subheader(f"Classroom Data Records for {batch_name}")
            st.dataframe(class_df)

            if st.button("Clear Classroom Data", type="primary", key="clear_class_btn"):
                if st.session_state['delete_pending']:
                    confirm_delete_ui()
                else:
                    st.write("Your data is safe (for now).")
                    if st.button("Initiate Delete Action"):
                        st.session_state['delete_pending'] = True
                        # Rerunning immediately after setting the flag updates the UI to show the confirmation
                        st.rerun()

                with st.spinner("Clearing classroom data..."):
                    if db.clear_classroom_data(batch_name):
                        st.toast(f"Classroom data for batch '{batch_name}' has been cleared.", icon="✅")
                        time.sleep(1)  # brief pause to ensure toast is seen
                        st.session_state.class_df_manage = pd.DataFrame()
                        class_df = pd.DataFrame()

                        if db.energy_batch_unique(batch_name):
                            db.clear_batch(batch_name)

                        st.rerun()

        if not energy_df.empty:
            st.subheader(f"Energy Data Records for {batch_name}")
            st.dataframe(energy_df)

            if st.button("Clear Energy Data", type="primary", key="clear_energy_btn"):
                with st.spinner("Clearing energy data..."):
                    if db.clear_energy_data(batch_name):
                        st.toast(f"Energy data for batch '{batch_name}' has been cleared.", icon="✅")
                        time.sleep(1)  # brief pause to ensure toast is seen
                        st.session_state.energy_df_manage = pd.DataFrame()
                        energy_df = pd.DataFrame()
                        
                        if db.class_batch_unique(batch_name):
                            db.clear_batch(batch_name)

                        st.rerun()
