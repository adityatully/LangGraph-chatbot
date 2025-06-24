import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pprint
from langchain_core.messages import AIMessage
from .excel_qna_graph import run_excel_qna_graph
from backend.excel_db_utils import get_excel_table_name  # fetches table name from file_id
from .state import Graph_state  # your state type

def excel_qna_agent(state: Graph_state) -> Graph_state:
    
    user_question = state["current_user_query"]

    excel_files = [
        f for f in state["files"]
        if f["file_type"].strip().lower() == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]
    print(f"Excel files found: {len(excel_files)}")
    if not excel_files:
        state["final_response"] = "No Excel file found."
        return state

    file = excel_files[0]
    file_id = file["id"]

    try:
        table_name = get_excel_table_name(file_id)

        
        final_answer = run_excel_qna_graph(user_question, table_name)

        # Update state
        state["excel_agent_result"] = {
            "file_id": file_id,
            "filename": file["filename"],
            "table": table_name,
            "user_query": user_question,
            "answer": final_answer,
        }
        state["final_response"] = final_answer
        state["messages"].append(AIMessage(content=final_answer))

    except Exception as e:
        state["final_response"] = f"Error processing Excel file: {str(e)}"

    return state
