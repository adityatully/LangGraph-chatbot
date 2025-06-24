from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict
from .state import Graph_state

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

#HUMAN_IN_LOOP_PROMPT = """
#You are the human in the loop agent of a large agentic AI system that is used to query on the files uploaded 
#by the user 
#The user has uploaded both PDF and Excel files, and the query is ambiguous.
#
#Please ask the user to clarify which file type they want to query (PDF or Excel) or how to proceed.
#
#Reply only with a polite clarification question, for example:
#"Hi! I see you have both PDFs and Excel files. Could you please specify which files or file types you'd like me to use to answer your query?"
#You are provided with the chat history and the user query  refrence , the User query might context to the chat history 
#
#User query:
#{user_query}
#"""

def human_in_loop_agent(state: Graph_state) -> Graph_state:
    user_question = state.get("current_user_query", "")
    
    clarification_prompt = (
        f"The user has uploaded both PDF and Excel files, and their query is ambiguous.\n\n"
        f"User query: {user_question}\n\n"
        "Please ask the user to clarify which file type they want to query (PDF or Excel). "
        "Reply only with a polite clarification question, such as:\n"
        "\"Hi! I see you have both PDFs and Excel files. Could you please specify which files or file types you'd like me to use to answer your query?\""
    )

    messages = []
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            messages.append(msg)
        elif isinstance(msg, AIMessage):
            messages.append(msg)

    messages.append(SystemMessage(content="You are a helpful assistant in an agentic AI system."))
    messages.append(HumanMessage(content=clarification_prompt))

    response = llm.invoke(messages)
    clarification_message = response.content.strip()

    state["messages"].append(AIMessage(content=clarification_message))
    state["final_response"] = clarification_message
    state["active_agent"] = "human_in_loop"

    return state
