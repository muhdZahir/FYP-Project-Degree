from core.imports import st, pd, os, psycopg2, create_engine

engine = create_engine(os.environ["DATABASE_URL"])

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require"
    )

# allowed tables for read/write to avoid accidental SQL injection via table names
ALLOWED_TABLES = {"Classroom", "Energy"} 

def init_db():
    """Initializes the local database and creates tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    # Batch table
    c.execute('''
        CREATE TABLE IF NOT EXISTS batch (
            batch_id SERIAL PRIMARY KEY,
            batch_Name TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Classroom table
    c.execute('''
        CREATE TABLE IF NOT EXISTS classroom (
            id SERIAL PRIMARY KEY,
            classroom_ID TEXT,
            floor INTEGER,
            capacity INTEGER,
            scheduled_Hours REAL,
            actual_occupancy INTEGER,
            day TEXT,
            time_Slot TEXT,
            week INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            batch_id INTEGER REFERENCES batch(batch_id)
        )
    ''')
    
    # Energy table
    c.execute('''
        CREATE TABLE IF NOT EXISTS energy (
            id SERIAL PRIMARY KEY,
            floor INTEGER,
            month TEXT,
            energy_kWh REAL,
            energy_Cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            batch_id INTEGER REFERENCES batch(batch_id)
        )
    ''')

    conn.commit()
    conn.close()

def save_to_db(df, table_name, batch_name):
    """Saves a dataframe to the database with a specific batch tag."""

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

    conn = get_connection()

    try:
        # Ensure batch exists
        save_batch_to_db(batch_name)

        # Get batch_id
        query = """SELECT batch_id FROM batch WHERE LOWER(batch_Name) = LOWER(%s)"""
        result = conn.execute(query, (batch_name,)).fetchone()
        batch_id = result[0]

        # ==============================
        # 🔍 CHECK BEFORE INSERT
        # ==============================
        class_exists_before, energy_exists_before = get_batch_status(batch_id)

        # Save data
        save_df = df.copy()
        save_df["batch_id"] = batch_id
        save_df.to_sql(table_name, engine, if_exists='append', index=False)

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
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO batch (batch_Name) VALUES (%s)", (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_batch_status(batch_id):
    """Returns (class_exists, energy_exists)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM classroom WHERE batch_id = %s", (batch_id,))
    class_exists = cursor.fetchone()[0] > 0

    cursor.execute("SELECT COUNT(*) FROM energy WHERE batch_id = %s", (batch_id,))
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

    conn = get_connection()
    try:
        # use parameterized query to safely substitute batch_name
        if table_name == 'Classroom':
            df = pd.read_sql_query(
                "SELECT classroom.classroom_id, classroom.floor, classroom.capacity, classroom.scheduled_hours, classroom.actual_occupancy, classroom.day, classroom.time_slot, classroom.week, batch.batch_name "
                "FROM classroom INNER JOIN batch ON classroom.batch_id = batch.batch_id WHERE batch.batch_name = %s",
                conn,
                params=(batch_name,)
                )
        elif table_name == 'Energy':
            df = pd.read_sql_query(
                "SELECT energy.floor, energy.month, energy.energy_kwh, energy.energy_cost, batch.batch_name "
                "FROM energy INNER JOIN batch ON energy.batch_id = batch.batch_id WHERE batch.batch_name = %s",
                conn,
                params=(batch_name,)
                )

        return df
    finally:
        conn.close()

def batch_unique(batch_name):
    """Checks whether a Batch_Name already exists in the Batch table."""
    conn = get_connection()
    try:
        query = "SELECT 1 FROM batch WHERE LOWER(batch_Name) = LOWER(%s)"
        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def class_batch_unique(batch_name):
    """Checks whether a Batch_Name already exists in Classroom table."""
    conn = get_connection()
    try:
        query = """SELECT 1 FROM classroom INNER JOIN batch ON classroom.batch_id = batch.batch_id WHERE LOWER(batch.batch_Name) = LOWER(%s)"""

        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def energy_batch_unique(batch_name):
    """Checks whether a Batch_Name already exists in Energy table."""
    conn = get_connection()
    try:
        query = """SELECT 1 FROM energy INNER JOIN batch ON energy.batch_id = batch.batch_id WHERE LOWER(batch.batch_Name) = LOWER(%s)"""
        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def get_unique_batches():
    """Fetches list of unique upload batches for the dropdown."""
    conn = get_connection()
    try:
        # Check if table exists first by trying to query it
        batches = pd.read_sql("SELECT batch_Name FROM batch", conn)
        return batches["batch_Name"].tolist()
    except Exception as e: # We only catch normal errors here, so system stops are not ignored
        return []
    finally:
        conn.close()

def update_batch_name(old_name, new_name):
    """Updates the batch name in the Batch table."""
    conn = get_connection()
    try:
        conn.execute("UPDATE batch SET batch_Name = %s WHERE LOWER(batch_Name) = LOWER(%s)", (new_name, old_name))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_classroom_data(batch_name):
    """Clears all records from Classroom table for a specific batch."""
    conn = get_connection()
    try:
        conn.execute("""
            DELETE FROM classroom
            WHERE batch_id IN (
                SELECT batch_id
                FROM batch
                WHERE LOWER(batch_Name) = LOWER(%s)
            )
        """, (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_energy_data(batch_name):
    """Clears all records from Energy table for a specific batch."""
    conn = get_connection()
    try:
        conn.execute("""
            DELETE FROM energy
            WHERE batch_id IN (
                SELECT batch_id
                FROM batch
                WHERE LOWER(batch_Name) = LOWER(%s)
            )
        """, (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_batch(batch_name):
    """Clears batch record from Batch table."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM batch WHERE LOWER(batch_Name) = LOWER(%s)", (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()