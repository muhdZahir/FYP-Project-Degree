import pytest
import sqlite3
import pandas as pd
from unittest.mock import patch
import core.database as db

@pytest.fixture(autouse=True)
def mock_db_name(tmp_path):
    # Overwrite the DB_NAME to a temporary test database
    test_db = tmp_path / "test_uro_system.db"
    with patch("core.database.DB_NAME", str(test_db)):
        db.init_db()
        yield str(test_db)

def test_init_db(mock_db_name):
    # Verify tables are created
    conn = sqlite3.connect(mock_db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    assert "Classroom" in tables
    assert "Energy" in tables
    assert "Batch" in tables

def test_save_batch_to_db():
    assert db.save_batch_to_db("Batch 1") == True
    assert db.save_batch_to_db("Batch 2") == True
    
    batches = db.get_unique_batches()
    assert "Batch 1" in batches
    assert "Batch 2" in batches

def test_batch_unique():
    db.save_batch_to_db("UniqueBatch")
    assert db.batch_unique("UniqueBatch") == False
    assert db.batch_unique("NewBatch") == True

def test_save_to_db_invalid_table():
    df = pd.DataFrame({"Capacity": [10]})
    with pytest.raises(ValueError, match="Invalid table name: InvalidTable"):
        db.save_to_db(df, "InvalidTable", "Batch 1")

def test_clear_batch():
    db.save_batch_to_db("ClearMe")
    assert "ClearMe" in db.get_unique_batches()
    db.clear_batch("ClearMe")
    assert "ClearMe" not in db.get_unique_batches()
