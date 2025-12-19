# pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run main.py'. to close, press 'ctrl + c' at terminal
import streamlit as st

if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

def choose_role():
    st.info("Please select your user role to log in")
    
    role = st.radio(
        "Select User Role",
        options=["IT Staff", "Manager"],
    )

    if st.button("Log in"):
        st.session_state['user_role'] = role
        st.rerun()

def logout():
    if st.button("Log out"):
        # actually clear the session state then rerun
        st.session_state.clear()
        st.rerun()

login_page = st.Page(choose_role, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

dashboard_page = st.Page("pages/dashboard.py", title="Dashboard", icon=":material/home:")
upload_page = st.Page("pages/upload.py", title="Upload Files", icon=":material/upload:")
manage_page = st.Page("pages/manage.py", title="Manage Data", icon=":material/storage:")
analysis_page = st.Page("pages/analysis.py", title="Analysis", icon=":material/analytics:")

if st.session_state['user_role'] == "IT Staff":
    pg = st.navigation(
        [
            dashboard_page,
            upload_page,
            manage_page,
            logout_page,
        ],
    )
elif st.session_state['user_role'] == "Manager":
    pg = st.navigation(
        [
            dashboard_page,
            analysis_page,
            logout_page,
        ],
    )
else:
    pg = st.navigation([login_page])

pg.run()