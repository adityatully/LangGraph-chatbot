import sys
import os
# Adjust the path to your project root accordingly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Optional, List, Dict
from langchain_core.messages import HumanMessage , AIMessage
from .state import Graph_state
from backend.db_utils import get_chat_history , get_documents_by_session


def initialize_state(user_query: str, session_id: Optional[str] = None)->Graph_state:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    raw_history = get_chat_history(session_id)

    formatted_history = []
    for msg in raw_history:
        if msg["role"] == "human":
            formatted_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            formatted_history.append(AIMessage(content=msg["content"]))

    
    formatted_history.append(HumanMessage(content=user_query))

    document_records = get_documents_by_session(session_id)

    files = [
        {
            "id": doc["id"],
            "filename": doc["filename"],
            "file_type": doc["file_type"],
            "upload_timestamp": doc["upload_timestamp"],
        }
        for doc in document_records
    ]

    return {
        "messages": formatted_history,
        "active_agent": "",  # Start with the router agent
        "current_user_query": user_query,
        "sql_gen_query": "",
        "excel_agent_result": None,
        "pdf_agent_result": None,
        "summarizer_agent_result": None,
        "final_response": None,
        "session_id": session_id,
        "files": files,
    }

