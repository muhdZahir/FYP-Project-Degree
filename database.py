import sqlite3  # For database operations, using SQLite for simplicity 
import pandas as pd  # sqlite checking; python -c "import sqlite3; print(sqlite3.sqlite_version)"
import time
import streamlit as st

# name of the database
DB_NAME = "uro_system.db"

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
            Batch_Name TEXT,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
            Batch_Name TEXT,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Batch table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Batch (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Batch_Name TEXT UNIQUE,
            Upload_Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
        save_df["Batch_Name"] = batch_name
        
        # Write to SQL (append mode)
        save_df.to_sql(table_name, conn, if_exists='append', index=False)
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
        conn.execute("INSERT INTO Batch (Batch_Name) VALUES (?)", (batch_name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.toast("Batch name already exists.", icon="⚠️")
        time.sleep(1)  # brief pause to ensure toast is seen
        return False
    finally:
        conn.close()

def load_from_db(table_name, batch_name):
    """Loads data from the database. Optionally filters by batch."""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT * FROM {table_name}"
    
    # If a specific batch is selected (and it's not "All History"), filter by it
    if batch_name != "All History":
        query += f" WHERE Batch_Name = '{batch_name}'"
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def class_batch_unique(batch_name):
    """Checks whether an Batch_Name already exists in Classroom table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """SELECT 1 FROM Classroom WHERE LOWER(Batch_Name) = LOWER(?)"""

        result = conn.execute(query, (batch_name,)).fetchone()
        return result is None  # True if unique
    finally:
        conn.close()

def energy_batch_unique(batch_name):
    """Checks whether an Batch_Name already exists in Energy table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = """SELECT 1 FROM Energy WHERE LOWER(Batch_Name) = LOWER(?)"""
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

def clear_classroom_data(batch_name):
    """Clears all records from Classroom table for a specific batch."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM Classroom WHERE Batch_Name = ?", (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_energy_data(batch_name):
    """Clears all records from Energy table for a specific batch."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM Energy WHERE Batch_Name = ?", (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()

def clear_batch(batch_name):
    """Clears batch record from Batch table."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM Batch WHERE Batch_Name = ?", (batch_name,))
        conn.commit()
        return True
    finally:
        conn.close()