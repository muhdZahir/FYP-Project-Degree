import streamlit as st # pip install streamlit | streamlit is use to create the UI. to open streamlit, run 'python -m streamlit run dashboard.py'. to close, press 'ctrl + c' at terminal
import pandas as pd # pip install pandas | pandas is use to analyze data from csv/xlsx
import os # to handle file path
import hashlib # to create file hash to avoid duplicate upload
import time # to handle time delay
import plotly.express as px # pip install plotly | plotly is use to create interactive visualization/chart
import database as db  # Importing your database.py

# to read excel, install 'pip install openpyxl'

db.init_db()

with st.sidebar:
    st.page_link("dashboard.py", label="Dashboard", icon=":material/dashboard:")
    st.page_link("pages/upload.py", label="Upload Files", icon=":material/upload:")
    st.page_link("pages/analysis.py", label="Analysis", icon=":material/analytics:")

st.set_page_config(page_title="Upload files", page_icon=":material/upload:")

st.title("URO: University Resource Optimization")

#Introduction of the system
st.write(
    f"2 files are needed to analyze; 1 contains the nessecary columns for classroom and 1 for energy.\n"
    f"\nBelow are examples of classroom and energy data; each with their respective columns.\n"
)

class_example = {
    "Classroom_ID": ["1901", "802"],
    "Floor": [19, 8],
    "Capacity": [30, 40],
    "Actual_Occupancy": [17, 34],
    "Day": ["Mon", "Thursday"],
    "Time_Slot": ["10.00-12.00", "14.00-16.00"],
    "Week": [4, 7]
}
_class = pd.DataFrame(class_example)
st.write("Example of classroom data table")
st.dataframe(_class)

energy_example = {
    "Floor": [1, 4],
    "Month": ["Feb", "March"],
    "Energy_kWh": [1023, 894],
    "Energy_Cost": [657, 454]
}
_energy = pd.DataFrame(energy_example)
st.write("Example of energy data table")
st.dataframe(_energy)

st.info("Upload raw Excel/CSV files to analyze and optionally save them to the database.")

# Initialize data containers (Empty at start)
class_df = pd.DataFrame()
energy_df = pd.DataFrame()

# Initialize session state for storing hashes and filenames
if 'file_hashes' not in st.session_state:
    st.session_state['file_hashes'] = {} # {hash: filename}

def get_file_hash(uploaded_file):
    #Calculates the MD5 hash of an uploaded file's content.
    # Ensure the file pointer is at the beginning
    uploaded_file.seek(0)
    file_hash = hashlib.md5(uploaded_file.read()).hexdigest()
    # Seek back to the start if you need to read it again later
    uploaded_file.seek(0)
    return file_hash

# File uploader widget that accepts multiple files
uploaded_files = st.file_uploader(
    "Upload your files here",
    accept_multiple_files=True,
)

if uploaded_files:
    st.write("Uploaded Files:")

    #reqiured columns for class and energy
    class_col = ["Classroom_ID","Floor","Capacity","Scheduled_Hours","Actual_Occupancy","Day","Time_Slot","Week"]
    energy_col = ["Floor","Month","Energy_kWh","Energy_Cost"]

    def check_columns(df, required_cols): #function to check column
        return [col for col in required_cols if col not in df.columns]
    
    for file in uploaded_files:
        st.write(f"- {file.name}")

        file_hash = get_file_hash(file)
        filename = file.name

        if file_hash in st.session_state['file_hashes']:
            # Duplicate found
            st.warning(f"Duplicate file detected: **{filename}** was already uploaded as **{st.session_state['file_hashes'][file_hash]}**.")
            continue
        else:
            # New file, process and store hash
            st.session_state['file_hashes'][file_hash] = filename

        # Get the file extension
        file_extension = os.path.splitext(file.name)[1].lower()
        
        df = None
        if file.type == "text/csv": # Processing for CSV file
            df = pd.read_csv(file)
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": # Processing for Excel file
            df = pd.read_excel(file)
        else:
            # Fallback based on filename extension when MIME type isn't present
            fname = file.name.lower()
            if fname.endswith(".csv"):
                df = pd.read_csv(file)
            elif fname.endswith(".xls") or fname.endswith(".xlsx"):
                df = pd.read_excel(file)

        if df is None:
            st.error(f"Error: Unsupported file type. Please upload a .csv or .xlsx file. You uploaded a {file_extension} file.")
            continue
        
        #check missing columns for class and energy
        missing_class = check_columns(df, class_col)
        missing_energy = check_columns(df, energy_col)

        # For matching classroom dataset
        if len(missing_class) == 0:
            class_df = df.copy()
            st.success(f"Identified as Classroom Dataset")
            st.subheader("Classroom Usage Data:")
            st.dataframe(class_df)
        # For matching energy dataset
        elif len(missing_energy) == 0:
            energy_df = df.copy()
            st.success(f"Identified as Energy Dataset")
            st.subheader("Energy Cost Data:")
            st.dataframe(energy_df)
        # Neither matches
        else:
            st.error(
                f"Could not identify this file.\n"
                f"- Missing classroom columns: {missing_class}\n"
                f"- Missing energy columns: {missing_energy}\n"
                f"\nPlease upload the correct dataset."
            )

# Preprocessing classroom data
if not class_df.empty:
    class_df = class_df.dropna() # drop missing values in a row

    # Convert string data in Capacity, Scheduled_Hours, & Actual_Occupancy to numeric, coercing errors to NaN
    class_df['Capacity_clean'] = pd.to_numeric(class_df['Capacity'], errors='coerce')
    class_df['Scheduled_clean'] = pd.to_numeric(class_df['Scheduled_Hours'], errors='coerce')
    class_df['ActOccu_clean'] = pd.to_numeric(class_df['Actual_Occupancy'], errors='coerce')

    # Drop rows where data is NaN (meaning original value was not numeric)
    class_df = class_df.dropna(subset=['Capacity_clean'])
    class_df = class_df.dropna(subset=['Scheduled_clean'])
    class_df = class_df.dropna(subset=['ActOccu_clean'])

    # Remove the temporary cleaned column
    class_df = class_df.drop(columns=['Capacity_clean'])
    class_df = class_df.drop(columns=['Scheduled_clean'])
    class_df = class_df.drop(columns=['ActOccu_clean'])

# Preprocessing energy data
if not energy_df.empty:
    energy_df = energy_df.dropna() # drop missing values in a row

    # Convert string data in Energy_kWh & Energy_Cost to numeric, coercing errors to NaN
    energy_df['Energy_clean'] = pd.to_numeric(energy_df['Energy_kWh'], errors='coerce')
    energy_df['Cost_clean'] = pd.to_numeric(energy_df['Energy_Cost'], errors='coerce')

    # Drop rows where data is NaN (meaning original value was not numeric)
    energy_df = energy_df.dropna(subset=['Energy_clean'])
    energy_df = energy_df.dropna(subset=['Cost_clean'])

    # Remove the temporary cleaned column
    energy_df = energy_df.drop(columns=['Energy_clean'])
    energy_df = energy_df.drop(columns=['Cost_clean'])

if not class_df.empty or not energy_df.empty:
    st.markdown("---")
    st.write("💾 Save to System Memory")
    col1, col2 = st.columns([3, 1])
    with col1:
        batch_name = st.text_input("Batch Name (e.g., Sem 1 2024)", placeholder="Enter a name to tag this data...")
    with col2:
        st.write("") # Spacer
        st.write("")
        save_btn = st.button("Save Data", type="primary")
    
    if save_btn and batch_name:
        saved_c = False
        saved_e = False
        
        if not class_df.empty:
            if db.save_to_db(class_df, "classroom_data", batch_name):
                saved_c = True
        
        if not energy_df.empty:
            if db.save_to_db(energy_df, "energy_data", batch_name):
                saved_e = True
        
        if saved_c:
            st.success(f"Successfully saved batch '{batch_name}' classroom data to database!")

        if saved_e:
            st.success(f"Successfully saved batch '{batch_name}' energy data to database!")

    elif save_btn and not batch_name:
        st.error("Please enter a Batch Name before saving.")

# clear the uploader and session state for a fresh start
if st.button("Clear Uploaded Files List"):
    st.session_state['file_hashes'] = {}
    st.toast("Files cleared successfully!", icon="✅")
    time.sleep(0.5)
    st.rerun()