from enum import StrEnum

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.core.context import AgentContext

from .nodes import assemble_resume_data, generate_experience, generate_skills, generate_summary, router_node
from .state import GenerateNode, InputState, InternalState, OutputState


class Node(StrEnum):
    """Node names for the resume generation agent."""

    START = START
    END = END
    GENERATE_SUMMARY = "generate_summary"
    GENERATE_EXPERIENCE = "generate_experience"
    GENERATE_SKILLS = "generate_skills"
    ASSEMBLE_RESUME_DATA = "assemble_resume_data"
    ROUTER = "router_node"


# === GRAPH ===
builder = StateGraph(
    InternalState,
    input_schema=InputState,
    output_schema=OutputState,
    context_schema=AgentContext,
)

# === NODES ===
builder.add_node(Node.ROUTER, router_node)
builder.add_node(Node.GENERATE_SUMMARY, generate_summary)
builder.add_node(Node.GENERATE_EXPERIENCE, generate_experience)
builder.add_node(Node.GENERATE_SKILLS, generate_skills)
builder.add_node(Node.ASSEMBLE_RESUME_DATA, assemble_resume_data)


# === EDGES ===
def map_router_targets_edge(state: InternalState) -> list[Send]:
    """
    Fan-out edge based on router targets.

    Reads:
    - router_targets

    Returns:
    - List[Send] to the selected generation nodes
    """
    # Default to all generate nodes if router returned nothing
    targets = state.router_targets or [
        GenerateNode.skills,
        GenerateNode.experience,
        GenerateNode.professional_summary,
    ]

    sends: list[Send] = []
    for target in targets:
        if target == GenerateNode.skills:
            sends.append(Send(Node.GENERATE_SKILLS, InternalState.model_validate(state)))
        elif target == GenerateNode.experience:
            sends.append(Send(Node.GENERATE_EXPERIENCE, InternalState.model_validate(state)))
        elif target == GenerateNode.professional_summary:
            sends.append(Send(Node.GENERATE_SUMMARY, InternalState.model_validate(state)))
    return sends


# Map router selections to generation nodes
builder.add_conditional_edges(
    Node.ROUTER,
    map_router_targets_edge,  # type: ignore[arg-type]
    [Node.GENERATE_SUMMARY, Node.GENERATE_EXPERIENCE, Node.GENERATE_SKILLS],
)

# All generation nodes feed into assemble_resume_data
builder.add_edge(Node.START, Node.ROUTER)
builder.add_edge(Node.GENERATE_SUMMARY, Node.ASSEMBLE_RESUME_DATA)
builder.add_edge(Node.GENERATE_EXPERIENCE, Node.ASSEMBLE_RESUME_DATA)
builder.add_edge(Node.GENERATE_SKILLS, Node.ASSEMBLE_RESUME_DATA)
builder.add_edge(Node.ASSEMBLE_RESUME_DATA, Node.END)

# === GRAPH ===
graph = builder.compile()
