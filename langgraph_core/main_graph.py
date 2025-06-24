from .router_agent import Router
from .state import Graph_state
from .general_agent import general_talking_agent
from .excel_agent import excel_qna_agent
from .human_in_the_loop import human_in_loop_agent
from .summary_agent import Summary_agent
from .RAG_agent import PDF_RAG_agent
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import add_messages , StateGraph , END
load_dotenv()


main_graph = StateGraph(Graph_state)    
main_graph.add_node("router", Router)
main_graph.add_node("general_agent", general_talking_agent)
main_graph.add_node("excel_qna_agent", excel_qna_agent)
main_graph.add_node("human_in_loop", human_in_loop_agent)
main_graph.add_node("pdf_summarizer_agent", Summary_agent)
main_graph.add_node("pdf_rag_agent", PDF_RAG_agent)
main_graph.set_entry_point("router")


def route_condition(state: Graph_state) -> str:
    return state["active_agent"]  # activ agent


main_graph.add_conditional_edges(
    "router",  
    route_condition,  
    {
        "general_agent": "general_agent",
        "excel_qna_agent": "excel_qna_agent",
        "human_in_loop": "human_in_loop",
        "pdf_summarizer_agent": "pdf_summarizer_agent",
        "pdf_rag_agent": "pdf_rag_agent"
    }
)

main_graph.add_edge("general_agent", END)
main_graph.add_edge("excel_qna_agent", END)
main_graph.add_edge("human_in_loop", END)
main_graph.add_edge("pdf_summarizer_agent", END)
main_graph.add_edge("pdf_rag_agent", END)



the_final_agent = main_graph.compile()
