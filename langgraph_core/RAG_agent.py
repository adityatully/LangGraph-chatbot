import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.chroma_utils import vectorstore
from .state import Graph_state

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

RAG_SYSTEM_PROMPT = """
You are an intelligent assistant helping the user understand the contents of a PDF document.
You are given a user query and relevant excerpts (context) from the document.

You are also given the chat history fro refrence  and the user query might be related to the chat history

Your job is to:
- Understand the user's query
- Only use the provided context to answer
- Be concise and accurate
- If the answer is not present in the context, clearly say "The information is not available in the document."

Guidelines:
- Do not hallucinate or guess beyond the context
- Answer in a friendly, helpful tone

User Query: {user_query}

Relevant Context:
---------------------
{context}
---------------------

Now provide the best possible answer:
"""



def retrieve_chunks_from_chroma(multi_queries: list[str], file_id: str, top_k: int = 5) -> list[str]:
    all_results = []

    for query in multi_queries:
        results = vectorstore.similarity_search(
            query=query,
            k=top_k,
            filter={"file_id": file_id}
        )
        # `results` is a list of Documents
        chunks = [doc.page_content for doc in results]
        all_results.extend(chunks)

    # Deduplicate while preserving order
    seen = set()
    unique_chunks = []
    for chunk in all_results:
        if chunk not in seen:
            unique_chunks.append(chunk)
            seen.add(chunk)

    return unique_chunks


def PDF_RAG_agent(state: Graph_state) -> Graph_state:
    user_query = state["current_user_query"]
    pdf_files = []
    for f in state["files"]:
        if isinstance(f, dict) and f.get("file_type", "").strip().lower() == "application/pdf":
            pdf_files.append(f)

    pdf_files = [
        f for f in state["files"]
        if f["file_type"].strip().lower() == "application/pdf"
    ]

    if not pdf_files:
        state["final_response"] = "No PDF file found."
        return state

    file_id = pdf_files[0]["id"]

    # 1. Generate multiple queries
    multi_queries = get_multiple_queries(user_query)

    # 2. Retrieve relevant chunks
    chunks = retrieve_chunks_from_chroma(multi_queries, file_id)
    if not chunks:
        state["final_response"] = "No relevant information found in the document."
        return state

    context_text = "\n\n".join(chunks)
    state["pdf_rag_context"] = context_text
    # 3. Create message list with system prompt and chat history
    full_prompt = RAG_SYSTEM_PROMPT.format(user_query=user_query, context=context_text)
    messages = [SystemMessage(content=full_prompt)]

    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(AIMessage(content=msg.content))

    # 4. Get response from LLM
    response = llm.invoke(messages)
    # 5. Save final response
    state["final_response"] = response.content
    state["messages"].append(AIMessage(content=response.content))
    return state


def get_multiple_queries(user_query: str) -> list[str]:
    prompt = f"""
        You are an AI language model assistant. Your task is to generate 4 different versions of the given user question to 
        retrieve relevant documents from a vector database. By generating multiple perspectives on the user question, 
        your goal is to help the user overcome some of the limitations of distance-based similarity search.
        Add additional context from the chat history if provided to inform the query variations.
        Provide these alternative questions separated by newlines.

        User query: "{user_query}"

        Alternate queries:
        """
    response = llm.invoke([HumanMessage(content=prompt)])

    # Ensure the response is valid
    if not hasattr(response, "content") or not response.content:
        return [user_query]  # Fallback to the original query if no response

    # Clean and split the response into individual queries
    lines = [line.strip("-• \n") for line in response.content.strip().split("\n") if line.strip()]
    return lines or [user_query]
