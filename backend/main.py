import sys
import os
# Add the PROJECT folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pprint
from langchain_core.messages import AIMessage
from fastapi import FastAPI, File, UploadFile, HTTPException , Form
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest 
#from langchain_utils import get_rag_chain
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
from excel_db_utils import save_excel_sheets_to_db
import os
from dotenv import load_dotenv
import uuid
import logging  
import shutil
from langgraph_core.main_graph import the_final_agent
from langgraph_core.start_state import initialize_state
from full_db_utils import  insert_full_pdf_text  , delete_full_pdf_text
load_dotenv()

#Opens a file in binary write mode ("wb").
#shutil.copyfileobj(...) copies the uploaded file's contents into the temporary file on disk.

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DEFAULT_MODEL_NAME = "gemini-2.0-flash"

# Initialize FastAPI app
app = FastAPI()


@app.post("/chat", response_model=QueryResponse) # how to response model 
def chat(query_input: QueryInput):
    if not query_input.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {DEFAULT_MODEL_NAME}")

    
    chat_history = get_chat_history(session_id)
    state = initialize_state(user_query=query_input.question, session_id=query_input.session_id)
    #pprint.pprint(state)
    
    
    #rag_chain = get_rag_chain(query_input.model.value)
    #answer = rag_chain.invoke({
    #    "input": query_input.question,
    #    "chat_history": chat_history
    #})['answer']  

    final_state = the_final_agent.invoke(state)
   # pprint.pprint(final_state)
    answer = final_state.get("final_response", "No response generated.")
    final_state["messages"].append(AIMessage(content=answer))
    #insert_application_logs(
    #    session_id, query_input.question, final_state["final_response"]
    #)
    #return QueryResponse(answer=final_state["final_response"], session_id=session_id, model=query_input.model)

    insert_application_logs(session_id, query_input.question, answer, DEFAULT_MODEL_NAME)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id)


@app.post("/upload-doc")
def upload_and_index_document(
    file: UploadFile = File(...),
    filename: str = Form(...),
    file_type: str = Form(...),
    session_id: str = Form(...)
):
    session_id = session_id 
    allowed_extensions = ['.pdf']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    temp_file_path = f"temp_{file.filename}" # made a temp file o the local storega to upload the uploade file

    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_id = insert_document_record(file.filename , file_type ,  session_id )
        success = index_document_to_chroma(temp_file_path, file_id)
        sucesss2 = insert_full_pdf_text(temp_file_path, file_id)
        print(file_id)
        print(success)
        print(sucesss2)

        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/upload-excel")
def upload_excel(
    file: UploadFile = File(...),
    filename: str = Form(...),
    file_type: str = Form(...),
    session_id: str = Form(...)
):
    session_id = session_id or str(uuid.uuid4())
    allowed_extensions = ['.xlsx']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed for this endpoint.")

    temp_file_path = f"temp_{file.filename}"

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Insert metadata, get file_id
        file_id = insert_document_record(file.filename , file_type , session_id)

        # Save excel sheets to excel_data.db
        sucess = save_excel_sheets_to_db(temp_file_path, file_id)
        print(file_id)
        print(sucess)


        return {"message": f"Excel file '{file.filename}' uploaded and processed.", "file_id": file_id}
    except Exception as e:
        # Rollback metadata insertion if needed
        delete_document_record(file_id)
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()


@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    chroma_delete_success = delete_doc_from_chroma(request.file_id)
    full_del_success = delete_full_pdf_text(request.file_id)
    if chroma_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}
