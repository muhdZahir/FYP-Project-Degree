from core.imports import st, pd, os, time, db, calendar, datetime
# to read excel, install 'pip install openpyxl'
from core.processing import require_role

require_role(["IT Staff"])

if "batch" not in st.session_state:
    st.session_state["batch"] = st.session_state["batch_name"]

# Initialize upload-specific session keys
if 'class_file' not in st.session_state:
    st.session_state.class_file = None
if 'energy_file' not in st.session_state:
    st.session_state.energy_file = None
if 'save_btn' not in st.session_state:
    st.session_state["save_btn"] = False

def check_columns(df, required_cols): #function to check column
    return [col for col in required_cols if col not in df.columns]

def clear_files():
    # Increment the key to force a fresh widget instance
    st.session_state["uploader_key"] += 1

def normalize_month(x):
    if pd.isna(x):
        return None
    
    # Case 1: numeric (1, 1.0, etc.)
    if isinstance(x, (int, float)):
        try:
            return calendar.month_abbr[int(x)]
        except Exception: # We catch normal errors to avoid hiding system stops
            return None
    
    # Case 2: string (Jan, January, etc.)
    if isinstance(x, str):
        x = x.strip().capitalize()
        abbr = x[:3]
        if abbr in calendar.month_abbr:
            return abbr
    
    return None  # invalid values

class_df = pd.DataFrame()
energy_df = pd.DataFrame()

with st.spinner("Loading page...", show_time=True):
    st.title("UPLOAD FILES")

    st.markdown(f"""
                Upload raw Excel/CSV files and save them to the database.

                Instructions on how to upload:
                
                1. Two files are needed to upload, one for **classroom** and one for **energy**.
                2. Click the "Browse files" button and select the files you want to upload.
                3. System will identify only **one** dataset for each classroom and energy. Other files will be **ignored**.
                4. Choose the semester and year for the **Batch Name** (e.g., Sem 1 2024) and click the "Save Data" button to save.
                5. Click the 'Clear Files' button to clear all uploaded data.

                It is important that both classroom and energy files are uploaded with the necessary columns.\n
                Below are examples of classroom and energy data; each with their respective columns.
            """)

    class_example = {
        "Classroom_Name": ["1901", "802"],
        "Floor": [19, 8],
        "Capacity": [30, 40],
        "Number_of_Students": [25, 35],
        "Actual_Occupancy": [17, 34],
        "Energy_Cost": [20.5, 35.0],
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

    st.write(f"After uploading, system will **preprocessed** the data to ensure coherence. Read the notes below for more details.")

    # ==============================================================================
    # PENGGUNAAN IKON AMARAN (WARNING ⚠️)
    # Ini berfungsi sebagai "Error Prevention" dalam HCI. Kita letak ikon amaran
    # supaya pengguna berhati-hati sebelum save data, mengelakkan kesilapan maut 
    # (data rosak masuk ke dalam database).
    # ==============================================================================
    with st.expander("Data Preprocessing Notes", icon="⚠️"):
        st.warning(f"Dataset may differ from the original uploaded files after preprocessing. Please review the data and ensure it is correct before saving to the database.")
        st.write(f"Preprocessing steps taken:\n"
                f"- Dropped rows with any missing values.\n\n"
                f"**CLASSROOM DATA:**\n"
                f"- Dropped rows with non-numeric values in **'Capacity'**, **'Number_of_Students'**, **'Actual_Occupancy'**, and **'Energy_Cost'**.\n"
                f"- Dropped rows where **'Capacity'** is negative or 0.\n"
                f"- Dropped rows where **'Number_of_Students'** is negative or greater than **'Capacity'**.\n"
                f"- Dropped rows where **'Actual_Occupancy'** is negative or greater than **'Capacity'**.\n"
                f"- Standardized **'Day'** to 3-letter format and dropped invalid days.\n"
                f"- Dropped rows with invalid time slot format (e.g., not like '10:00-12:00').\n"
                f"- Dropped rows with invalid week numbers (not between 1-16).\n"
                f"- Dropped duplicate rows of data that happen during the same time period (e.g., multiple entries for the same data in the same "
                f"classroom (**'1901'**) at the same time, day, & week (**'10:00-12:00'**, **'Mon'**, **4**)).\n\n"
                f"**ENERGY DATA:**\n"
                f"- Dropped rows with non-numeric values in **'Energy_kWh'** and **'Energy_Cost'**.\n"
                f"- Dropped rows where **'Energy_kWh'** or **'Energy_Cost'** is negative.\n"
                f"- Standardized **'Month'** to 3-letter format (e.g., 'Jan', 'Feb'), including months in numeric format (e.g., '1', '2' and '1.2') and dropped invalid months.\n"
                f"- Dropped duplicate rows of data of the same floor during the same month (e.g., multiple entries for the same floor (e.g., **'1'**) in the same month (**'Feb'**)).\n"
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
        class_col = ["Classroom_Name","Floor","Capacity","Number_of_Students","Actual_Occupancy","Energy_Cost","Day","Time_Slot","Week"]
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

        # Convert string data in Week, Capacity, Number_of_Students, Actual_Occupancy & Energy_Cost to numeric, coercing errors to NaN
        class_df['Capacity_clean'] = pd.to_numeric(class_df['Capacity'], errors='coerce')
        class_df['Number_of_Students_clean'] = pd.to_numeric(class_df['Number_of_Students'], errors='coerce')
        class_df['ActOccu_clean'] = pd.to_numeric(class_df['Actual_Occupancy'], errors='coerce')
        class_df['Energy_Cost_clean'] = pd.to_numeric(class_df['Energy_Cost'], errors='coerce')
        class_df['Week_clean'] = pd.to_numeric(class_df['Week'], errors='coerce')

        # Day of week standardization (Mon, Monday, mon -> Monday)
        class_df['Day'] = class_df['Day'].str.strip().str.capitalize().str[:3] # Standardize to 3-letter format
        valid_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        class_df = class_df[class_df['Day'].isin(valid_days)] # Keep only valid days

        # Week number validation for 1 semester (1-16)
        class_df['Week_invalid'] = (class_df['Week_clean'] < 1) | (class_df['Week_clean'] > 16)

        # Time slot format validation (e.g., "10:00-12:00") if file is excel
        if st.session_state.class_file and st.session_state.class_file.lower().endswith(('.xls', '.xlsx')):
            class_df['Time_Slot'] = class_df['Time_Slot'].astype(str).str.strip() # Remove leading/trailing whitespace
            
            # PENJELASAN (Untuk Supervisor):
            # Kadang-kadang Excel automatik tukar tanda '-' (hyphen) kepada '–' (en dash).
            # Baris ini ("Data Cleaning") wajib ada untuk pastikan format masa konsisten 
            # supaya sistem tidak "crash" bila buat pengiraan masa kelak.
            class_df['Time_Slot'] = class_df['Time_Slot'].str.replace('–', '-') # Replace en dash with hyphen if present
            
            class_df['Time_Slot_invalid'] = ~class_df['Time_Slot'].str.contains(r'^\d{1,2}:\d{2}-\d{1,2}:\d{2}$') # Simple regex to check format like "10:00-12:00 OR "9:00–11:00"
            class_df = class_df[~class_df['Time_Slot_invalid']] # Drop invalid time slots
            class_df = class_df.drop(columns=['Time_Slot_invalid'])

        # Flag rows where Capacity is invalid (negative or 0)
        class_df['Capacity_invalid'] = (class_df['Capacity_clean'] < 0) | (class_df["Capacity_clean"] == 0)  
        # Flag rows where Number of Students is invalid (negative or greater than capacity)
        class_df['Number_of_Students_invalid'] = (class_df['Number_of_Students_clean'] < 0) | (class_df["Number_of_Students_clean"] > class_df["Capacity_clean"])
        # Flag rows where Actual Occupancy is invalid (negative or greater than capacity)
        class_df['ActOccu_invalid'] = (class_df['ActOccu_clean'] < 0) | (class_df['ActOccu_clean'] > class_df['Capacity_clean'])

        # Flag rows duplicate of same data during the same time period
        class_df['Duplicate_class'] = class_df.duplicated(subset=["Classroom_Name", "Week", "Day", "Time_Slot"], keep="first")

        # Drop rows where data is NaN (meaning original value was not numeric)
        class_df = class_df.dropna(subset=['Capacity_clean', 'Number_of_Students_clean', 'ActOccu_clean', 'Energy_Cost_clean', 'Week_clean'])
        class_df = class_df[# Drop invalid Capacity (negative or 0) or invalid Actual Occupancy (negative or greater than capacity) or invalid Number of Students (negative or greater than capacity)
            ~class_df['Capacity_invalid'] & ~class_df['ActOccu_invalid'] & ~class_df['Number_of_Students_invalid'] &
            ~class_df['Week_invalid'] & # Drop invalid week numbers
            ~class_df['Duplicate_class'] # Drop duplicate lessons in the same time period
        ]

        # Remove the temporary cleaned column
        class_df = class_df.drop(
            columns=['Capacity_clean', 'Number_of_Students_clean', 'ActOccu_clean', 'Energy_Cost_clean', 'Week_clean',
                     'Capacity_invalid', 'ActOccu_invalid', 'Number_of_Students_invalid', 'Week_invalid',
                     'Duplicate_class']
        )

        with st.expander("Classroom Usage Data"):
            st.dataframe(class_df)

    # Preprocessing energy data
    if 'energy_df' in locals() and not energy_df.empty:
        energy_df = energy_df.dropna() # drop missing values in a row

        # Convert string data in Energy_kWh & Energy_Cost to numeric, coercing errors to NaN
        energy_df['Energy_clean'] = pd.to_numeric(energy_df['Energy_kWh'], errors='coerce')
        energy_df['Cost_clean'] = pd.to_numeric(energy_df['Energy_Cost'], errors='coerce')

        # Month in numeric to month name conversion (1, Jan, January -> Jan)
        energy_df['Month'] = energy_df['Month'].apply(normalize_month)

        # Flag rows where Energy_kWh and Energy_Cost are invalid (negative)
        energy_df['Energy_invalid'] = energy_df['Energy_clean'] < 0
        energy_df['Cost_invalid'] = energy_df['Cost_clean'] < 0
        
        # Flag rows duplicate of same data of a floor during the same month
        energy_df['Duplicate_energy'] = energy_df.duplicated(subset=["Floor", "Month"], keep="first")

        # Drop rows where data is NaN (meaning original value was not numeric)
        energy_df = energy_df.dropna(subset=['Energy_clean', 'Cost_clean', 'Month'])
        
        # PENJELASAN (Untuk Supervisor):
        # Proses "Data Sanitization". Data yang tidak logik (seperti bil elektrik negatif
        # atau bil bulan yang sama direkodkan dua kali) mesti dibuang awal-awal. 
        # Kalau tak, ia akan rosakkan purata/total (Aggregate functions) di halaman Analysis.
        energy_df = energy_df[
            ~energy_df['Energy_invalid'] & ~energy_df['Cost_invalid'] & # Drop rows where Energy_kWh or Energy_Cost is invalid (negative)
            ~energy_df['Duplicate_energy'] # Drop duplicate rows of the same floor during the same month
        ]

        # Remove the temporary cleaned column
        energy_df = energy_df.drop(columns=['Energy_clean', 'Cost_clean', 'Energy_invalid', 'Cost_invalid', 'Duplicate_energy'])

        with st.expander("Energy Cost Data"):
            st.dataframe(energy_df)

    if 'class_df' in locals() and not class_df.empty or 'energy_df' in locals() and not energy_df.empty:
        st.divider()
        st.write("💾 Save to System Memory")
        st.caption("Batch name is a label that groups related data together. It identifies a specific dataset period — usually a semester and year.")
        st.text("Batch Name (e.g., Sem 1 2024)")
        col1, col2, col3 = st.columns([0.2, 1, 1])
        with col1:
            st.header("Sem")

        with col2:
            sem = st.selectbox("Semester", [1, 2, 3])
            
        with col3:
            current_year = datetime.now().year
            year = st.selectbox("Year", range(current_year - 10, current_year + 1))

        st.session_state["save_btn"] = st.button("Save Data", key="green")
        batch_name = f"Sem {sem} {year}"

        if st.session_state["save_btn"]:
            if year > current_year:
                st.warning("Year cannot be in the future.")

            else:
                saved_c = False
                saved_e = False
                
                if not class_df.empty:
                    if not db.class_batch_unique(batch_name):
                        st.error("❌ This Batch name already exists in Classroom Data. Please use a unique Batch name.")
                    else:
                        if db.save_to_db(class_df, "Classroom", batch_name):
                            saved_c = True

                if not energy_df.empty:
                    if not db.energy_batch_unique(batch_name):
                        st.error("❌ This Batch name already exists in Energy Data. Please use a unique Batch name.")
                    else:
                        if db.save_to_db(energy_df, "Energy", batch_name):
                            saved_e = True

                if saved_c:
                    st.success(f"Successfully saved Batch '{batch_name}' classroom data to database!")

                if saved_e:
                    st.success(f"Successfully saved Batch '{batch_name}' energy data to database!")