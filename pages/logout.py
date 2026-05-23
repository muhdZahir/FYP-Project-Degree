from core.imports import st

role = st.session_state.get("user_role")

if role is None:
    st.switch_page("pages/login.py")

st.write("Logging out...")
if st.button("Log out"):
    st.toast(f"Log out successful!", icon="✅", duration="long")
    # clear all session state then rerun
    st.session_state.clear()
    st.cache_data.clear()  # Clear cached data to ensure a fresh start on next login
    st.rerun()
