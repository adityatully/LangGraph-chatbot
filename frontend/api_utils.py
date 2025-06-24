import requests
import streamlit as st

def get_api_response(question, session_id):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {"question": question}
    if session_id:
        data["session_id"] = session_id
    try:
        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None


def upload_document(file  ,session_id):
    try:
        files = {"file": (file.name, file, file.type)}
        data = {
            "filename": file.name,
            "file_type": file.type,
            "session_id": session_id or "default-session-id"
        }
        if file.type == "application/pdf":
            response = requests.post("http://localhost:8000/upload-doc", files=files , data = data)
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            response = requests.post("http://localhost:8000/upload-excel", files=files , data = data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload file. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
        return None

def list_documents():
    try:
        response = requests.get("http://localhost:8000/list-docs")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
        return []

def delete_document(file_id):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {"file_id": file_id}

    try:
        response = requests.post("http://localhost:8000/delete-doc", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None
