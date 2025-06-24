import sqlite3
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

DB_NAME = "full_pdf_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_pdf_full_texts():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pdf_full_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER UNIQUE,
            full_text TEXT,
            FOREIGN KEY(file_id) REFERENCES document_storage(id) ON DELETE CASCADE
        )
    ''')
    conn.close()

def load_full_pdf_text(file_path: str) -> str:
    """
    Loads the entire PDF content as a single string.
    Useful for summarization and DB storage.
    """
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    full_text = "\n\n".join([page.page_content for page in pages])
    return full_text

def insert_full_pdf_text( file_path: str , file_id: int) -> bool:
    """
    Loads full text from PDF and inserts into DB.
    Args:
        file_id (int): The associated document_storage ID
        file_path (str): Path to the temp PDF file
    """
    try:
        full_text = load_full_pdf_text(file_path)

        conn = get_db_connection()
        conn.execute(
            'INSERT OR REPLACE INTO pdf_full_texts (file_id, full_text) VALUES (?, ?)',
            (file_id, full_text)
        )

        conn.commit()
        return True
        conn.close()
        
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

    

def get_full_pdf_text(file_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT full_text FROM pdf_full_texts WHERE file_id = ?', (file_id,))
    row = cursor.fetchone()
    conn.close()
    return row['full_text'] if row else None

def delete_full_pdf_text(file_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM pdf_full_texts WHERE file_id = ?', (file_id,))
    conn.commit()
    conn.close()

# Initialize the table on import
create_pdf_full_texts()
