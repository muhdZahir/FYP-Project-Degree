# pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run dashboard.py'. to close, press 'ctrl + c' at terminal
import streamlit as st

st.title("URO: University Resource Optimization")

#Introduction of the system
st.write(
    f"University Resource Optimization is a system designed to analyze classroom usage and energy cost and provide optimization recommendation.\n"
    f"\nOptimization is the process of finding the best possible solution (maximum profit, minimum cost, highest efficiency)\n"
    f"from a set of available options, by using mathematical models and algorithms to improve a system, process, or design, while satisfying\n"
    f"specific limitations or constraints. It's about making something as perfect or effective as possible, whether it's a business operation,\n"
    f"a software program, or an engineering structure.\n"
)

st.write(
    f"\nThis system allows IT staff to upload classroom usage and energy cost data files, analyze the data, and generate reports and visualizations to help\n"
    f"identify areas for improvement. The system also provides optimization recommendations based on the analysis results, such as adjusting classroom schedules\n"
    f"or implementing energy-saving measures for Managers. Overall, the University Resource Optimization system aims to help educational institutions optimize their\n"
    f"resources and reduce costs while maintaining a high level of service quality.\n"
)
