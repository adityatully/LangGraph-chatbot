from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import Graph_state

# Initialize your LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
)

GENERAL_AGENT_PROMPT = """You are a general conversing agent for an AI agent system that has many functions 

You are powered by google's gemini 
when the user asks what can you do , you should reply with -
The system can perform the following functions
- summarising the PDF provided or giving short notes 
- perform RAG on the PDF uploaded 
- perform QNA tasks on the Excel sheets that are uploaded 
- provide general knowledge using the Gemini model 

The system is built on Streamlit, LangGraph, FastAPI, SQLite database, LangChain, and Chroma vector database.

Your task is as the anchor of the entire system. You are the conversing agent that converses with the user,
when someone asks about the system or general things to talk about or some information which you can find.

You will be provided the user query. You need to give an appropriate response 
according to the given instructions.  
You are also provided with the conversation history for reference; the user query might have context related to chat history.

User query: {current_user_query}
"""

def general_talking_agent(state: Graph_state) -> Graph_state:
    user_question = state["current_user_query"]
    
    full_prompt = GENERAL_AGENT_PROMPT.format(
        current_user_query=user_question,
    )
    
    messages = [SystemMessage(content=full_prompt)]
    
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(AIMessage(content=msg.content))
    
    # Get response from LLM
    response = llm.invoke(messages)
    assistant_reply = response.content.strip()

    # Update the state with assistant reply
    state["messages"].append(AIMessage(content=assistant_reply))  # Add LLM's response
    state["final_response"] = assistant_reply
    state["active_agent"] = "general_talking_agent"

    return state
