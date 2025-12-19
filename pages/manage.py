import streamlit as st # pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run main.py'. to close, press 'ctrl + c' at terminal
import pandas as pd # pip install pandas | pandas is use to analyze data from csv/xlsx
import time # to handle time delay
import plotly.express as px # pip install plotly | plotly is use to create interactive visualization/chart
import database as db  # Importing your database.py

db.init_db()

# Initialize session state for persistence across reruns
if 'class_df_manage' not in st.session_state:
    st.session_state["class_df_manage"] = pd.DataFrame()
if 'energy_df_manage' not in st.session_state:
    st.session_state["energy_df_manage"] = pd.DataFrame()
if 'selected_batch_manage' not in st.session_state:
    st.session_state.selected_batch_manage = None

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
            st.session_state.selected_batch_manage = "All History"

        selected_batch = st.selectbox(
            "Select Data Batch:",
            ["All History"] + available_batches,
            key="selected_batch_manage"
        )

        if st.button("Load Data", key="load_db_btn"):
            if st.session_state["selected_batch_manage"] is None:
                st.info("Click 'Load Data' button to fetch data from database.")
                st.session_state["class_df_manage"] = pd.DataFrame()
                st.session_state["energy_df_manage"] = pd.DataFrame()

            else:
                with st.spinner("Fetching data from SQL Engine..."):
                    # store loaded dataframes in session_state so they persist across interactions
                    st.session_state["class_df_manage"] = db.load_from_db("classroom_data", st.session_state['selected_batch_manage'])
                    st.session_state["energy_df_manage"] = db.load_from_db("energy_data", st.session_state['selected_batch_manage'])
                    st.toast("Data loaded successfully.", icon="✅")

    class_df = st.session_state.get('class_df_manage', pd.DataFrame())
    energy_df = st.session_state.get('energy_df_manage', pd.DataFrame())

    if not class_df.empty:
        st.subheader(f"Classroom Data Records for {st.session_state['selected_batch_manage']}")
        st.dataframe(class_df)

        if st.button("Clear Classroom Data for This Batch", type="primary", key="clear_class_btn"):
            with st.spinner("Clearing classroom data..."):
                db.clear_classroom_data(st.session_state['selected_batch_manage'])
                st.toast(f"Classroom data for batch '{st.session_state['selected_batch_manage']}' has been cleared.", icon="✅")
                time.sleep(1)  # brief pause to ensure toast is seen
                # Refresh the displayed data
                st.session_state['class_df_manage'] = db.load_from_db("classroom_data", st.session_state['selected_batch_manage'])
                class_df = st.session_state['class_df_manage']
                st.rerun()

    if not energy_df.empty:
        st.subheader(f"Energy Data Records for {st.session_state['selected_batch_manage']}")
        st.dataframe(energy_df)

        if st.button("Clear Energy Data for This Batch", type="primary", key="clear_energy_btn"):
            with st.spinner("Clearing energy data..."):
                db.clear_energy_data(st.session_state['selected_batch_manage'])
                st.toast(f"Energy data for batch '{st.session_state['selected_batch_manage']}' has been cleared.", icon="✅")
                time.sleep(1)  # brief pause to ensure toast is seen
                # Refresh the displayed data
                st.session_state['energy_df_manage'] = db.load_from_db("energy_data", st.session_state['selected_batch_manage'])
                energy_df = st.session_state['energy_df_manage']
                st.rerun()
