from enum import StrEnum

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


class InputState(BaseModel):
    user_input: str


class OutputState(BaseModel):
    response: str | None = None


class InternalState(InputState, OutputState):
    pass


class Node(StrEnum):
    START = START
    END = END
    BASIC = "basic"


def basic_node(state: InternalState) -> OutputState:
    return OutputState(response=f"Response to {state.user_input}")


builder = StateGraph(InternalState)

builder.add_node(Node.BASIC, basic_node)

builder.add_edge(Node.START, Node.BASIC)
builder.add_edge(Node.BASIC, Node.END)

graph = builder.compile()
