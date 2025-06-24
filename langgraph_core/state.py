from typing import TypedDict, Annotated, Optional, List, Dict
from langgraph.graph import add_messages


class FileRecord(TypedDict):
    id: str
    filename: str
    file_type: str
    upload_timestamp: str



class Graph_state(TypedDict):
    session_id: str
    messages: Annotated[List[dict], add_messages]
    active_agent: str
    current_user_query: str
    sql_gen_query: Optional[str]
    excel_agent_result: Optional[Dict]
    pdf_agent_result: Optional[Dict]
    summarizer_agent_result: Optional[Dict]
    final_response: Optional[str]
    files: List[FileRecord]  # full info about all files in session
    pdf_rag_context: Optional[str]


