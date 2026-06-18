"""
LangGraph Graph Construction
"""
import os

os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "false")

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgenticWorkflowState
from agent.nodes.alignment import make_alignment_node
from agent.nodes.research import make_research_node
from agent.nodes.plan import make_plan_node
from agent.nodes.write import make_write_node


def create_graph():
    """
    construct and compile LangGraph state graph with four phases
    """
    builder = StateGraph(AgenticWorkflowState)

    builder.add_node("alignment", make_alignment_node())
    builder.add_node("research", make_research_node())
    builder.add_node("plan", make_plan_node())
    builder.add_node("write", make_write_node())

    builder.add_edge(START, "alignment")
    builder.add_edge("alignment", "research")
    builder.add_edge("research", "plan")
    builder.add_edge("plan", "write")
    builder.add_edge("write", END)

    return builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["research", "plan", "write"],
    )
