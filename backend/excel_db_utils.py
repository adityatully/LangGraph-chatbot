import sqlite3
from datetime import datetime
import pandas as pd
import logging
DB_NAME = "excel_data.db"  # Database name for storing Excel data


logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_excel_sheet_registry():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS excel_sheet_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            sheet_name TEXT,
            table_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_excel_table_name(file_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT table_name FROM excel_sheet_registry WHERE file_id = ? ORDER BY created_at DESC LIMIT 1',
        (file_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if result is None:
        raise ValueError(f"No registered Excel table found for file_id {file_id}")

    return result['table_name']




def save_excel_sheets_to_db(excel_path: str, file_id: int) -> bool:
    try:
        conn = get_db_connection()
        print(conn)
        xls = pd.ExcelFile(excel_path)
        sheet_name = xls.sheet_names[0]  # Only one sheet
        print(sheet_name)
        df = pd.read_excel(xls, sheet_name=sheet_name)

        safe_sheet_name = sheet_name.replace(' ', '_').replace('-', '_')
        print(safe_sheet_name)
        table_name = f"file{file_id}_{safe_sheet_name}"
        print(table_name)

        # Save sheet data to a table
        df.to_sql(table_name, conn, if_exists='replace', index=False)

        # Register in metadata
        conn.execute(
            'INSERT INTO excel_sheet_registry (file_id, sheet_name, table_name) VALUES (?, ?, ?)',
            (file_id, sheet_name, table_name)
        )

        conn.commit()
        logging.info(f"Saved sheet '{sheet_name}' to table '{table_name}'")
        return True

    except Exception as e:
        print(f"Error in save_excel_sheets_to_db: {e}")
        logging.error(f"Failed to save Excel sheet to DB: {e}")
        return False

    finally:
        conn.close()


create_excel_sheet_registry()