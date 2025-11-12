import streamlit as st
import pandas as pd

st.title("File Upload Example")

uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt", "png", "jpg"])

if uploaded_file is not None:
    # You can process the uploaded file based on its type
    file_details = {"filename": uploaded_file.name, "filetype": uploaded_file.type, "filesize": uploaded_file.size}
    st.write(file_details)

    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
    elif uploaded_file.type.startswith("image/"):
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    else:
        # For other file types, you can read the content as bytes
        bytes_data = uploaded_file.getvalue()
        st.write("File content (first 100 bytes):")
        st.code(bytes_data[:100].decode("utf-8", errors="ignore"))