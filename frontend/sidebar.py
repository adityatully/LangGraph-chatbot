import streamlit as st
from api_utils import upload_document, list_documents, delete_document
from datetime import datetime, timedelta
SESSION_TIMEOUT = timedelta(minutes=60)

def display_sidebar():
    # Document upload
    session_id = st.session_state["session_id"]
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "xlsx"])
    if uploaded_file and st.sidebar.button("Upload"):
        with st.spinner("Uploading..."):
            #file_type = uploaded_file.type
            upload_response = upload_document(uploaded_file , session_id)
            if upload_response:
                st.sidebar.success(f"File uploaded successfully with ID {upload_response['file_id']}.")
                st.session_state.documents = list_documents()

    # List and delete documents
    st.sidebar.header("Uploaded Documents")
    if st.sidebar.button("Refresh Document List"):
        st.session_state.documents = list_documents()

    # Display document list and delete functionality
    if "documents" in st.session_state and st.session_state.documents:
        for doc in st.session_state.documents:
            st.sidebar.text(f"{doc['filename']} (ID: {doc['id']})")

        selected_file_id = st.sidebar.selectbox("Select a document to delete", 
                                                options=[doc['id'] for doc in st.session_state.documents])
        if st.sidebar.button("Delete Selected Document"):
            delete_response = delete_document(selected_file_id)
            if delete_response:
                st.sidebar.success(f"Document deleted successfully.")
                st.session_state.documents = list_documents()
