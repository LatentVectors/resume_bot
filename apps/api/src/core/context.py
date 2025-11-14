from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """Runtime context passed through the LangGraph execution.

    Contains identifiers that allow nodes to perform on-demand look-ups while
    keeping the graph state itself small.
    """

    user_id: int = Field(..., description="Unique identifier of the user running the agent")
    job_posting_id: int = Field(
        ..., description="Job posting identifier that the agent is working with"
    )
