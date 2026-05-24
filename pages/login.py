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

# ==============================================================================
# PENJELASAN (Untuk Supervisor):
# Isu Sekuriti: "Hardcoded Credentials" (Kata laluan diletak terus dalam kod).
# Dalam industri, ini adalah satu kesalahan besar. Namun, untuk projek FYP ini,
# sistem dibangunkan pada peringkat "Minimum Viable Product (MVP)" / Prototaip.
# Untuk "Production Deployment" yang sebenar, jadual 'Users' akan ditambah dalam 
# pangkalan data dan kata laluan akan di-hash (Bcrypt/SHA-256) demi keselamatan.
# ==============================================================================

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
        st.toast(f"Login successful!", icon="✅", duration="long")
        st.rerun()
    else:
        st.error("Invalid username or password. Please try again.")