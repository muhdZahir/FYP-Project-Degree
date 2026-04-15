from core.imports import st, pd,os, time, db
# to read excel, install 'pip install openpyxl'

db.init_db()

# Initialize upload-specific session keys
if 'class_file' not in st.session_state:
    st.session_state.class_file = None
if 'energy_file' not in st.session_state:
    st.session_state.energy_file = None

def inject_custom_css(css_file_path):
        #Injects custom CSS from a local file into the Streamlit app.
        try:
            with open(css_file_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except FileNotFoundError:
            st.error(f"Error: CSS file not found at {css_file_path}")

def check_columns(df, required_cols): #function to check column
    return [col for col in required_cols if col not in df.columns]

def clear_files():
    # Increment the key to force a fresh widget instance
    st.session_state["uploader_key"] += 1

class_df = pd.DataFrame()
energy_df = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    # Define the relative path to your CSS file
    css_path = os.path.join("assets", "style.css")

    # Inject the CSS
    inject_custom_css(css_path)

    st.title("UPLOAD FILES")

    #Introduction of the system
    st.write(
        f"2 files are needed to analyze; 1 contains the necessary columns for classroom and 1 for energy.\n"
        f"\nSystem will identify only 1 dataset for each classroom and energy. Other files will be ignored.\n"
        f"\nIf you need to clear the uploaded files, click the 'Clear Files' button below.\n"
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

    st.write(f"Upload raw Excel/CSV files to analyze and save them to the database.")

    with st.expander("Data Preprocessing Notes", icon="⚠️"):
        st.warning(f"Dataset may differ from the original uploaded files after preprocessing. Please review the data and ensure it is correct before saving to the database.")
        st.write(f"Preprocessing steps taken:\n"
                 f"- Dropped rows with any missing values.\n"
                 f"- Dropped rows with non-numeric values in 'Capacity', 'Scheduled_Hours', and 'Actual_Occupancy' in classroom data.\n"
                 f"- Dropped rows with non-numeric values in 'Energy_kWh' and 'Energy_Cost' in energy data."
        )

    # Initialize uploader key in session state
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    # File uploader widget that accepts multiple files
    uploaded_files = st.file_uploader(
        "Upload your files here",
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['uploader_key']}"
    )

    if uploaded_files:
        st.write("Uploaded Files:")

        #reqiured columns for class and energy
        class_col = ["Classroom_ID","Floor","Capacity","Scheduled_Hours","Actual_Occupancy","Day","Time_Slot","Week"]
        energy_col = ["Floor","Month","Energy_kWh","Energy_Cost"]
        
        for file in uploaded_files:
            st.write(f"- {file.name}")

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

            # Determine dataset type based on missing columns
            # Both match in a single file
            if len(missing_class) == 0 and len(missing_energy) == 0:
                st.error("This file matches BOTH classroom and energy schemas. Please split the dataset.")
            # For matching classroom dataset
            elif len(missing_class) == 0:
                if class_df.empty:
                    class_df = df.copy()
                    st.success("Identified as Classroom Dataset")
                    st.session_state.class_file = file.name
                else:
                    st.warning(f"Classroom dataset already loaded from '{st.session_state.class_file}'. Additional classroom files are ignored.")
            # For matching energy dataset
            elif len(missing_energy) == 0:
                if energy_df.empty:
                    energy_df = df.copy()
                    st.success("Identified as Energy Dataset")
                    st.session_state.energy_file = file.name
                else:
                    st.warning(f"Energy dataset already loaded from '{st.session_state.energy_file}'. Additional energy files are ignored.")
            # Neither matches
            else:
                st.error(
                    f"Could not identify this file.\n"
                    f"- Missing classroom columns: {missing_class}\n"
                    f"- Missing energy columns: {missing_energy}\n"
                    f"\nPlease upload the correct dataset."
                )

        # clear the uploaded files for a fresh start
        if st.button("Clear Files"):
            clear_files()
            st.toast("Files cleared successfully!", icon="✅")
            time.sleep(1)  # brief pause to ensure toast is seen
            st.rerun()

        st.divider()
        
    # Preprocessing classroom data
    if 'class_df' in locals() and not class_df.empty:
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

        with st.expander("Classroom Usage Data"):
            st.dataframe(class_df)

    # Preprocessing energy data
    if 'energy_df' in locals() and not energy_df.empty:
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

        with st.expander("Energy Cost Data"):
            st.dataframe(energy_df)

    if 'class_df' in locals() and not class_df.empty or 'energy_df' in locals() and not energy_df.empty:
        st.divider()
        st.write("💾 Save to System Memory")
        col1, col2 = st.columns([3, 1])
        with col1:
            batch_name = st.text_input("Batch Name (e.g., Sem 1 2024)", placeholder="Enter a name to tag this data...")
        with col2:
            st.write("") # Spacer
            st.write("")
            save_btn = st.button("Save Data", key="green")
        
        if save_btn and batch_name:
            saved_c = False
            saved_e = False
            
            if not class_df.empty:
                if not db.class_batch_unique(batch_name):
                    st.error("❌ This batch name already exists in Classroom Data. Please use a unique batch name.")
                else:
                    if db.save_to_db(class_df, "Classroom", batch_name):
                        saved_c = True

            if not energy_df.empty:
                if not db.energy_batch_unique(batch_name):
                    st.error("❌ This batch name already exists in Energy Data. Please use a unique batch name.")
                else:
                    if db.save_to_db(energy_df, "Energy", batch_name):
                        saved_e = True

            if saved_c:
                st.success(f"Successfully saved batch '{batch_name}' classroom data to database!")

            if saved_e:
                st.success(f"Successfully saved batch '{batch_name}' energy data to database!")

        elif save_btn and not batch_name:
            st.error("Please enter a Batch Name before saving.")