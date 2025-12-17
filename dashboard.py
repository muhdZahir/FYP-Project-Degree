import streamlit as st # pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run dashboard.py'. to close, press 'ctrl + c' at terminal

with st.sidebar:
    st.page_link("dashboard.py", label="Dashboard", icon=":material/dashboard:")
    st.page_link("pages/upload.py", label="Upload Files", icon=":material/upload:")
    st.page_link("pages/analysis.py", label="Analysis", icon=":material/analytics:")

st.set_page_config(page_title="Dashboard", page_icon=":material/dashboard:")

st.title("URO: University Resource Optimization")

#Introduction of the system
st.write(
    f"University Resource Optimization is a system designed to analyze classroom usage and energy cost and provide optimization recommendation.\n"
    f"\nOptimization .\n"
)

