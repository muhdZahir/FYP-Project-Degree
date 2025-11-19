import streamlit as st # to run, python -m streamlit run uni.py
import pandas as pd

st.title("University Resource Optimization")

# Create a file uploader widget that accepts multiple files
uploaded_files = st.file_uploader(
    "Upload your files here",
    type=["csv", "txt", "xlsx"], # Optional: specify accepted file types
    accept_multiple_files=True
)

if uploaded_files:
    st.write("Uploaded Files:")
    for file in uploaded_files:
        st.write(f"- {file.name}")

        # Example of processing a CSV file
        if file.type == "text/csv":
            df = pd.read_csv(file)
            st.subheader(f"Table {file.name}:")
            st.dataframe(df)
        
        # Example of processing a text file
        elif file.type == "text/plain":
            content = file.read().decode("utf-8")
            st.subheader(f"Content of {file.name}:")
            st.text(content[:200]) # Display first 200 characters
        
        # Example of processing an Excel file
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(file)
            st.subheader(f"Content of {file.name}:")
            st.dataframe(df.head())