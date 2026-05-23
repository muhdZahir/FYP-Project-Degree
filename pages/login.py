from core.imports import st

def check_login(username, password):
    if username == "staff" and password == "1234staff": #staff login
        role = "IT Staff"
        st.session_state['user_role'] = role
        return True
    if username == "admin" and password == "4321admin": #admin login
        role = "Manager"
        st.session_state['user_role'] = role
        return True
    return False

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("assets/URO_logo.png")

st.title("URO: University Resource Optimization")
st.info("Login to Your App")

with st.form(key="login_form"):
    username = st.text_input(label="Username", placeholder="Enter your username")
    password = st.text_input(label="Password", placeholder="Enter your password", type='password')

    submit_button = st.form_submit_button("Log in")

if submit_button:
    if check_login(username, password):
        st.rerun()
    else:
        st.error("Invalid username or password. Please try again.")