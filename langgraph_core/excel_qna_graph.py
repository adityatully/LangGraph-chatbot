from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import sqlite3


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)


db = SQLDatabase.from_uri("sqlite:////Users/adityatully/Desktop/Langraph/PROJECT/backend/excel_data.db")


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain, always limit your query to
at most {top_k} results. You can order the results by a relevant column to
return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}
"""

user_prompt = "Question: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)


class QueryOutput(TypedDict):
    query: Annotated[str, "Generated SQL query."]


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}



def execute_query(state: State) -> dict:
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}


def generate_answer(state: State) -> dict:
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}


graph_builder = StateGraph(State).add_sequence([
    write_query,
    execute_query,
    generate_answer
])
graph_builder.add_edge(START, "write_query")
graph = graph_builder.compile()


def run_excel_qna_graph(question: str, table_name: str) -> str:
    question_with_table = f"{question} (Use table: {table_name})"
    result = graph.invoke({"question": question_with_table})
    return result["answer"]


