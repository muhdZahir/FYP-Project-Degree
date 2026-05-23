from core.imports import os, st, pd, db #to open streamlit, run 'python -m streamlit run main.py'. to close, press 'ctrl + c' at terminal

db.init_db()

if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if "batch" not in st.session_state:
    st.session_state["batch"] = None
if 'class_df' not in st.session_state:
    st.session_state["class_df"] = pd.DataFrame()
if 'energy_df' not in st.session_state:
    st.session_state["energy_df"] = pd.DataFrame()
if 'batch_name' not in st.session_state:
    st.session_state["batch_name"] = None
if 'show' not in st.session_state:
    st.session_state['show'] = False
    
def inject_custom_css(css_file_path):
    #Injects custom CSS from a local file into the Streamlit app.
    try:
        with open(css_file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: CSS file not found at {css_file_path}")

# Define the relative path to your CSS file
css_path = os.path.join("assets", "style.css")

# Inject the CSS
inject_custom_css(css_path)

available_batches = db.get_unique_batches()            

# Define all the pages
login_page = st.Page("pages/login.py", title="Log in", icon=":material/login:")
logout_page = st.Page("pages/logout.py", title="Log out", icon=":material/logout:")
dashboard_page = st.Page("pages/dashboard.py", title="Dashboard", icon=":material/home:")
upload_page = st.Page("pages/upload.py", title="Upload Files", icon=":material/upload:")
manage_page = st.Page("pages/manage.py", title="Manage Data", icon=":material/storage:")
view_page = st.Page("pages/view.py", title="View Data", icon=":material/storage:")
analysis_page = st.Page("pages/analysis.py", title="Analysis", icon=":material/analytics:")
optimize_page = st.Page("pages/optimize.py", title="Optimization", icon=":material/auto_fix_high:")

st.html("""
  <style>
    [alt=Logo] {
      height: 4rem;
    }
  </style>
        """)

# Sidebar navigation
st.logo("assets/URO_small.png", icon_image="assets/URO_small.png")
if st.session_state['user_role'] == "IT Staff":
    st.sidebar.markdown(f"Welcome, **IT Staff**!")
    pg = st.navigation(
        [
            dashboard_page,
            upload_page,
            manage_page,
            logout_page,
        ],
    )
elif st.session_state['user_role'] == "Manager":
    st.sidebar.markdown(f"Welcome, **Manager**!")
    pg = st.navigation(
        [
            dashboard_page,
            view_page,
            analysis_page,
            optimize_page,
            logout_page,
        ],
    )
    if available_batches:
        if st.session_state["batch"] is None or st.session_state["batch"] not in available_batches:
            st.session_state["batch"] = st.session_state["batch_name"]

    # Data loading for view, analysis, optimize pages
    if pg in [view_page, analysis_page, optimize_page]:
        if not available_batches:
            st.sidebar.warning("No data found in database. Please upload and save files first.")
        else:
            st.sidebar.write("Load data batch.")

            st.sidebar.selectbox(
                "Select Data Batch",
                available_batches,
                key="batch"
            )

            if st.sidebar.button("Load Data", key="load_db_btn"):
                if st.session_state["batch"] is None:
                    st.toast("Choose a data batch and click 'Load Data'.")
                    st.session_state['class_df'] = pd.DataFrame()
                    st.session_state['energy_df'] = pd.DataFrame()
                    st.session_state['batch_name'] = None
                    st.session_state['show'] = False 
                else:
                    with st.spinner("Fetching data from SQL Engine..."):
                        st.session_state['class_df'] = db.load_from_db("Classroom", st.session_state['batch'])
                        st.session_state['energy_df'] = db.load_from_db("Energy", st.session_state['batch'])
                        st.session_state['batch_name'] = st.session_state['batch']
                        st.session_state['show'] = False 
                        st.toast(f"Batch '{st.session_state['batch']}' Loaded Successfully.", icon="✅")
else:
    pg = st.navigation(
        [
            dashboard_page,
            login_page
        ]
    )

pg.run()