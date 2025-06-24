from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import Graph_state
from dotenv import load_dotenv
load_dotenv()

# Initialize your LLM client
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

ROUTER_SYSTEM_PROMPT = """
You are a routing agent in a multi-agent system.

Your job is to examine the user query and the files uploaded in the current session. Based on that,
decide which specialized agent should handle the task. 

You have the following agents available:

1. pdf_rag_agent — for answering questions from PDFs using retrieval-based Q&A.
2. pdf_summarizer_agent — for summarizing PDF content.
3. excel_qna_agent — for answering questions using Excel spreadsheets.
4. general_agent — for small talk or general questions not related to uploaded documents.
5. human_in_loop — if the user has uploaded both Excel and PDF files or the query is ambiguous.


You are also provided with the conversation history for refrence , the User query might context to the chat history 

Here is how to decide:

- If the query is about a PDF , the file summary contains only pdf files 
and relates to understanding, summarizing, or extracting info → choose pdf_rag_agent or pdf_summarizer_agent based on context.
- If the query is about tabular data, the file summary consists of only excel files calculations, or Excel-specific terms → choose excel_qna_agent.
- If both Excel and PDF files are present and the query is unclear or could apply to either → choose the agent for the most recent file uploaded 
- If there are no files or the query is general (e.g., “Hi”, “What can you do?”) → choose general_agent.

Only respond with the name of the agent: one of `pdf_rag_agent`, `pdf_summarizer_agent`, `excel_qna_agent`, `general_agent`.
 

Current files uploaded: {file_summaries}
User query: {current_user_query}
"""


def Router(state: Graph_state) -> Graph_state:
    """
    Router to determine which agent should handle the query.
    Includes chat history to provide context for routing decisions.
    """
    query = state["current_user_query"]
    files: List[Dict] = state.get("files", [])

    if not files:
        file_summaries = "No files uploaded"
    else:
        file_summaries = ", ".join([f"{file['filename']} ({file['file_type']})" for file in files])

    prompt_text = ROUTER_SYSTEM_PROMPT.format(
        file_summaries=file_summaries,
        current_user_query=query
    )

    
    messages = [SystemMessage(content=prompt_text)]

    
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(AIMessage(content=msg.content))

    # Add current user query as the last HumanMessage
    #messages.append(HumanMessage(content=query))   
    # already done in initialisation step 

    # Call LLM to get the chosen agent
    response = llm.invoke(messages)
    agent_name = response.content.strip().lower()

    # Validate agent name, fallback to human_in_loop
    valid_agents = {
        "pdf_rag_agent",
        "pdf_summarizer_agent",
        "excel_qna_agent",
        "general_agent",
        "human_in_loop"
    }

    if agent_name not in valid_agents:
        agent_name = "human_in_loop"  # fallback for safety

    # Update active_agent in state
    state["active_agent"] = agent_name

    return state


