import sqlite3  # For database operations, using SQLite for simplicity 
import pandas as pd  # sqlite checking; python -c "import sqlite3; print(sqlite3.sqlite_version)"
import streamlit as st

# name of the database, can change as needed
DB_NAME = "uro_system.db"

def init_db():
    """Initializes the local database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # classroom_data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS classroom_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Classroom_ID TEXT,
            Floor INTEGER,
            Capacity INTEGER,
            Scheduled_Hours REAL,
            Actual_Occupancy INTEGER,
            Day TEXT,
            Time_Slot TEXT,
            Week INTEGER,
            Upload_Batch TEXT,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # energy_data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS energy_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Floor INTEGER,
            Month TEXT,
            Energy_kWh REAL,
            Energy_Cost REAL,
            Upload_Batch TEXT,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_to_db(df, table_name, batch_name):
    """Saves a dataframe to the database with a specific batch tag."""
    conn = sqlite3.connect(DB_NAME)
    try:
        # Create a copy to avoid modifying the original view
        save_df = df.copy()
        save_df["Upload_Batch"] = batch_name
        
        # Write to SQL (append mode)
        save_df.to_sql(table_name, conn, if_exists='append', index=False)
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False
    finally:
        conn.close()

def load_from_db(table_name, batch_name):
    """Loads data from the database. Optionally filters by batch."""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT * FROM {table_name}"
    
    # If a specific batch is selected (and it's not "All History"), filter by it
    if batch_name != "All History":
        query += f" WHERE Upload_Batch = '{batch_name}'"
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def class_batch_unique(batch_name):
    """Checks whether an Upload_Batch already exists in classroom_data table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """SELECT 1 FROM classroom_data WHERE LOWER(Upload_Batch) = LOWER(?)"""

        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def energy_batch_unique(batch_name):
    """Checks whether an Upload_Batch already exists in energy_data table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """SELECT 1 FROM energy_data WHERE LOWER(Upload_Batch) = LOWER(?)"""
        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def get_unique_batches():
    """Fetches list of unique upload batches for the dropdown."""
    conn = sqlite3.connect(DB_NAME)
    try:
        # Check if table exists first by trying to query it
        batches = pd.read_sql("SELECT DISTINCT Upload_Batch FROM classroom_data UNION SELECT DISTINCT Upload_Batch FROM energy_data", conn)
        return batches["Upload_Batch"].tolist()
    except:
        return []
    finally:
        conn.close()

def clear_classroom_data(batch_name):
    """Clears all records from classroom_data table for a specific batch."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM classroom_data WHERE Upload_Batch = ?", (batch_name,))
        conn.commit()
    finally:
        conn.close()

def clear_energy_data(batch_name):
    """Clears all records from energy_data table for a specific batch."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM energy_data WHERE Upload_Batch = ?", (batch_name,))
        conn.commit()
    finally:
        conn.close()