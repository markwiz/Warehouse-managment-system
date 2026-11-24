"""Minimal LangGraph wiring. Replace the placeholder node with real agent steps."""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def _placeholder(state: AgentState) -> dict:
    return {}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("placeholder", _placeholder)
    graph.add_edge(START, "placeholder")
    graph.add_edge("placeholder", END)
    return graph.compile()
