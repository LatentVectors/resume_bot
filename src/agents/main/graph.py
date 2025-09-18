from enum import StrEnum

from langgraph.graph import END, START, StateGraph

from src.core.context import AgentContext

from .nodes import assemble_resume_data, generate_experience, generate_skills, generate_summary
from .state import InputState, InternalState, OutputState


class Node(StrEnum):
    """Node names for the resume generation agent."""

    START = START
    END = END
    GENERATE_SUMMARY = "generate_summary"
    GENERATE_EXPERIENCE = "generate_experience"
    GENERATE_SKILLS = "generate_skills"
    ASSEMBLE_RESUME_DATA = "assemble_resume_data"


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
builder.add_node(Node.ASSEMBLE_RESUME_DATA, assemble_resume_data)

# === EDGES ===
# Start branches to all three generation nodes in parallel
builder.add_edge(Node.START, Node.GENERATE_SUMMARY)
builder.add_edge(Node.START, Node.GENERATE_EXPERIENCE)
builder.add_edge(Node.START, Node.GENERATE_SKILLS)

# All generation nodes feed into assemble_resume_data
builder.add_edge(Node.GENERATE_SUMMARY, Node.ASSEMBLE_RESUME_DATA)
builder.add_edge(Node.GENERATE_EXPERIENCE, Node.ASSEMBLE_RESUME_DATA)
builder.add_edge(Node.GENERATE_SKILLS, Node.ASSEMBLE_RESUME_DATA)

# assemble_resume_data ends the graph
builder.add_edge(Node.ASSEMBLE_RESUME_DATA, Node.END)

# === GRAPH ===
graph = builder.compile()
