from enum import Enum
from typing import Literal, TypedDict

from langgraph.types import Interrupt
from langgraph.types import interrupt as interrupt_graph

INTERRUPT_KEY = "__interrupt__"


class InterruptType(Enum):
    """Interrupt types."""

    MESSAGE = "message"


class MessageInterrupt(TypedDict):
    """Message interrupt."""

    type: Literal[InterruptType.MESSAGE]
    message: str


class MessageInterruptResponse(TypedDict):
    """Message interrupt response."""

    type: Literal[InterruptType.MESSAGE]
    response: str


DispatchedInterrupt = MessageInterrupt
InterruptResponse = MessageInterruptResponse


def dispatch_message_interrupt(message: str) -> MessageInterruptResponse:
    """Dispatch a message interrupt."""
    return interrupt_graph(MessageInterrupt(type=InterruptType.MESSAGE, message=message))  # type: ignore[no-any-return]


def handle_interrupts(interrupts: list[Interrupt]) -> dict[str, InterruptResponse]:
    """Handle interrupts and return commands to be executed."""
    commands: dict[str, InterruptResponse] = {}
    for interrupt in interrupts:
        interrupt_id = interrupt.id
        interrupt_value: DispatchedInterrupt = interrupt.value

        if not interrupt_id or not isinstance(interrupt_id, str):
            raise ValueError("Interrupt ID is required and must be a string")
        interrupt_type = interrupt_value.get("type")
        if not interrupt_type:
            raise ValueError("Interrupt type is required")
        if not isinstance(interrupt_type, InterruptType):
            raise ValueError("Interrupt type must be an InterruptType")

        if interrupt_type == InterruptType.MESSAGE:
            commands[interrupt_id] = handle_message_interrupt(interrupt_value)
        else:
            raise ValueError(f"Unknown interrupt type: {interrupt_type}")
    return commands


def handle_message_interrupt(interrupt: MessageInterrupt) -> MessageInterruptResponse:
    """Handle a message interrupt."""
    print(interrupt["message"], end="\n\n")
    response = input("User: ").strip()  # TODO: How do I sanitize the user input.
    return MessageInterruptResponse(type=InterruptType.MESSAGE, response=response)
