from core.imports import st, pd, sqlite3

# name of the database
DB_NAME = "database/uro_system.db"
# allowed tables for read/write to avoid accidental SQL injection via table names
ALLOWED_TABLES = {"Classroom", "Energy"} 

def init_db():
    """Initializes the local database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Classroom table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Classroom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Classroom_ID TEXT,
            Floor INTEGER,
            Capacity INTEGER,
            Scheduled_Hours REAL,
            Actual_Occupancy INTEGER,
            Day TEXT,
            Time_Slot TEXT,
            Week INTEGER,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            Batch_id INTEGER,
            FOREIGN KEY (Batch_id) REFERENCES Batch(Batch_id)
        )
    ''')
    
    # Energy table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Energy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Floor INTEGER,
            Month TEXT,
            Energy_kWh REAL,
            Energy_Cost REAL,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            Batch_id INTEGER,
            FOREIGN KEY (Batch_id) REFERENCES Batch(Batch_id)
        )
    ''')

    # Batch table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Batch (
            Batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Batch_Name TEXT UNIQUE,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def save_to_db(df, table_name, batch_name):
    """Saves a dataframe to the database with a specific batch tag."""

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

    conn = sqlite3.connect(DB_NAME)

    try:
        # Ensure batch exists
        save_batch_to_db(batch_name)

        # Get Batch_id
        query = """SELECT Batch_id FROM Batch WHERE LOWER(Batch_Name) = LOWER(?)"""
        result = conn.execute(query, (batch_name,)).fetchone()
        batch_id = result[0]

        # ==============================
        # 🔍 CHECK BEFORE INSERT
        # ==============================
        class_exists_before, energy_exists_before = get_batch_status(batch_id)

        # Save data
        save_df = df.copy()
        save_df["Batch_id"] = batch_id
        save_df.to_sql(table_name, conn, if_exists='append', index=False)

        # ==============================
        # 🚨 CONDITION (ONLY BEFORE)
        # ==============================
        if class_exists_before and energy_exists_before:
            st.toast(
                f"Batch '{batch_name}' already exists in both Classroom and Energy data.",
                icon="⚠️"
            )
        else:
            st.toast(
                f"{table_name} data saved successfully for batch '{batch_name}'.",
                icon="✅"
            )

        return True

    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

    finally:
        conn.close()

def save_batch_to_db(batch_name):
    """Saves a new batch name to the Batch table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("INSERT OR IGNORE INTO Batch (Batch_Name) VALUES (?)", (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_batch_status(batch_id):
    """Returns (class_exists, energy_exists)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Classroom WHERE Batch_id = ?", (batch_id,))
    class_exists = cursor.fetchone()[0] > 0

    cursor.execute("SELECT COUNT(*) FROM Energy WHERE Batch_id = ?", (batch_id,))
    energy_exists = cursor.fetchone()[0] > 0

    conn.close()
    return class_exists, energy_exists

@st.cache_data(ttl=3600)
def load_from_db(table_name, batch_name):
    """Loads data from the database for a specific batch. Returns empty DataFrame if batch_name is not provided."""
    if table_name not in ALLOWED_TABLES and table_name != 'Batch':
        raise ValueError(f"Invalid table name: {table_name}")

    if not batch_name:
        return pd.DataFrame()

    conn = sqlite3.connect(DB_NAME)
    try:
        # use parameterized query to safely substitute batch_name
        if table_name == 'Classroom':
            df = pd.read_sql_query(
                "SELECT Classroom.Classroom_ID, Classroom.Floor, Classroom.Capacity, Classroom.Scheduled_Hours, Classroom.Actual_Occupancy, Classroom.Day, Classroom.Time_Slot, Classroom.Week, Batch.Batch_Name "
                "FROM Classroom INNER JOIN Batch ON Classroom.Batch_id = Batch.Batch_id WHERE Batch.Batch_Name = ?",
                conn,
                params=(batch_name,)
                )
        elif table_name == 'Energy':
            df = pd.read_sql_query(
                "SELECT Energy.Floor, Energy.Month, Energy.Energy_kWh, Energy.Energy_Cost, Batch.Batch_Name "
                "FROM Energy INNER JOIN Batch ON Energy.Batch_id = Batch.Batch_id WHERE Batch.Batch_Name = ?",
                conn,
                params=(batch_name,)
                )

        return df
    finally:
        conn.close()

def batch_unique(batch_name):
    """Checks whether a Batch_Name already exists in the Batch table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = "SELECT 1 FROM Batch WHERE LOWER(Batch_Name) = LOWER(?)"
        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def class_batch_unique(batch_name):
    """Checks whether a Batch_Name already exists in Classroom table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """SELECT 1 FROM Classroom INNER JOIN Batch ON Classroom.Batch_id = Batch.Batch_id WHERE LOWER(Batch.Batch_Name) = LOWER(?)"""

        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def energy_batch_unique(batch_name):
    """Checks whether a Batch_Name already exists in Energy table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """SELECT 1 FROM Energy INNER JOIN Batch ON Energy.Batch_id = Batch.Batch_id WHERE LOWER(Batch.Batch_Name) = LOWER(?)"""
        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def get_unique_batches():
    """Fetches list of unique upload batches for the dropdown."""
    conn = sqlite3.connect(DB_NAME)
    try:
        # Check if table exists first by trying to query it
        batches = pd.read_sql("SELECT Batch_Name FROM Batch", conn)
        return batches["Batch_Name"].tolist()
    except:
        return []
    finally:
        conn.close()

def update_batch_name(old_name, new_name):
    """Updates the batch name in the Batch table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("UPDATE Batch SET Batch_Name = ? WHERE LOWER(Batch_Name) = LOWER(?)", (new_name, old_name))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_classroom_data(batch_name):
    """Clears all records from Classroom table for a specific batch."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("""
            DELETE FROM Classroom
            WHERE Batch_id IN (
                SELECT Batch_id
                FROM Batch
                WHERE LOWER(Batch_Name) = LOWER(?)
            )
        """, (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_energy_data(batch_name):
    """Clears all records from Energy table for a specific batch."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("""
            DELETE FROM Energy
            WHERE Batch_id IN (
                SELECT Batch_id
                FROM Batch
                WHERE LOWER(Batch_Name) = LOWER(?)
            )
        """, (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_batch(batch_name):
    """Clears batch record from Batch table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM Batch WHERE LOWER(Batch_Name) = LOWER(?)", (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()