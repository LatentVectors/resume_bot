from enum import StrEnum

from langgraph.graph import END, START, StateGraph

from src.core.context import AgentContext

from .nodes import create_resume, generate_experience, generate_skills, generate_summary
from .state import InputState, InternalState, OutputState


class Node(StrEnum):
    """Node names for the resume generation agent."""

    START = START
    END = END
    GENERATE_SUMMARY = "generate_summary"
    GENERATE_EXPERIENCE = "generate_experience"
    GENERATE_SKILLS = "generate_skills"
    CREATE_RESUME = "create_resume"


# === GRAPH ===
builder = StateGraph(
    InternalState,
    input_schema=InputState,
    output_schema=OutputState,
    context_schema=AgentContext,
)

# === NODES ===
builder.add_node(Node.GENERATE_SUMMARY, generate_summary)
builder.add_node(Node.GENERATE_EXPERIENCE, generate_experience)
builder.add_node(Node.GENERATE_SKILLS, generate_skills)
builder.add_node(Node.CREATE_RESUME, create_resume)

# === EDGES ===
# Start branches to all three generation nodes in parallel
builder.add_edge(Node.START, Node.GENERATE_SUMMARY)
builder.add_edge(Node.START, Node.GENERATE_EXPERIENCE)
builder.add_edge(Node.START, Node.GENERATE_SKILLS)

# All generation nodes feed into create_resume
builder.add_edge(Node.GENERATE_SUMMARY, Node.CREATE_RESUME)
builder.add_edge(Node.GENERATE_EXPERIENCE, Node.CREATE_RESUME)
builder.add_edge(Node.GENERATE_SKILLS, Node.CREATE_RESUME)

# create_resume ends the graph
builder.add_edge(Node.CREATE_RESUME, Node.END)

# === GRAPH ===
graph = builder.compile()
