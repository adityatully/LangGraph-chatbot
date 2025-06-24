import streamlit as st
from sidebar import display_sidebar
from chat_interface import display_chat_interface
import uuid
st.title("Langchain RAG Chatbot")

# Initialize session state variables
if "messages" not in st.session_state:   # agar usse pele koi session nhi hua and
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# Display the sidebar
display_sidebar()

# Display the chat interface
display_chat_interface()
