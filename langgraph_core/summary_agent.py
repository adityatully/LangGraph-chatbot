import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .state import Graph_state  # your state type
from langchain_core.messages import AIMessage
from backend.full_db_utils import get_full_pdf_text
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

SUMMARIZER_PROMPT = """ You are a help AI assistant who help in providing summary or
 short notes about the text that is provided to you
 You will be given some text and a user's query , understand the user query and perfrom the function it requires 
 You can be given the following functions for example - 
 - Providing summary of the text 
 - Generating short notes for a student using the text 
 - Providing important bullet pointers 
 - Providing revision notes from the text
 You are also provided with the conversation history for refrence , the User query might context to the chat history 
 NOTE ONLY USE THE TEXT PROVIDED TO YOU FOR GIVING RESPONSE TO THE USER QUERY 

 User query: {current_user_query}
 Provided_text : {full_text}
"""



def Summary_agent(state: Graph_state) -> Graph_state:
    user_question = state["current_user_query"]
    #pprint.pprint(state)
    pdf_files = []
    for f in state["files"]:
        if isinstance(f, dict) and f.get("file_type", "").strip().lower() == "application/pdf":
            pdf_files.append(f)

    pdf_files = [
        f for f in state["files"]
        if f["file_type"].strip().lower() == "application/pdf"
    ]

    print(f"PDF files found: {len(pdf_files)}")
    if not pdf_files:
        state["final_response"] = "No PDF file found."
        return state

    try:
        file_id = pdf_files[0]["id"]
        full_text = get_full_pdf_text(file_id)
        if not full_text:
            state["final_response"] = "Could not retrieve text from the PDF."
            return state

        full_prompt = SUMMARIZER_PROMPT.format(
            current_user_query=user_question,
            full_text=full_text
        )

        messages = [SystemMessage(content=full_prompt)]

        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                messages.append(HumanMessage(content=msg.content))
            elif isinstance(msg, AIMessage):
                messages.append(AIMessage(content=msg.content))

        response = llm.invoke(messages)
        state["messages"].append(AIMessage(content=response.content))
        state["final_response"] = response.content

    except Exception as e:
        state["final_response"] = f"An error occurred during summarisation: {str(e)}"

    return state