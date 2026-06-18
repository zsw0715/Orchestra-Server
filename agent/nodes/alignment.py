"""
Phase 0: Alignment — multi-turn conversation between user and Orchestrator

Version 0.1.0 For minimum demo
"""
import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent.state import AgenticWorkflowState, AlignmentPhaseState, SubAgentConfig
from config.model import init_model
from prompts.phase import PHASE_SYSTEM_PROMPT


# ============================================================
# Internal helpers
# ============================================================
def _strip_fence(text: str) -> str:
    """
    Remove JSON fence markers from the text.
    """
    return text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def _looks_like_json(text: str) -> bool:
    """
    Check if the text looks like JSON.
    """
    return text.startswith("{")


def _invoke_json(model, conversation: list) -> str:
    """
    Invoke the model with the conversation and strip the JSON fence markers.
    """
    response = model.invoke(conversation)
    return _strip_fence(response.content.strip())


# ============================================================
# Building blocks
# ============================================================
def _init_model(cfg):
    """
    Initialize the model with the given configuration.
    """
    return init_model(
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        streaming=False,
    )


def _init_orchestrator_human_conversation(state: AgenticWorkflowState) -> list:
    """
    Initialize the conversation between the Orchestrator and the user.
    """
    print("=" * 50)
    print("  Phase 0: Alignment — Start")
    print("=" * 50)
    conversation = [SystemMessage(content=PHASE_SYSTEM_PROMPT["alignment"])]
    conversation.append(HumanMessage(content=f"User request: {state.user_query}\nStart discussing with the user."))
    return conversation


def _run_conversation_loop(model, conversation: list) -> str:
    """
    Run the conversation loop between the Orchestrator and the user.
    """
    while True:
        response = model.invoke(conversation)
        content = response.content.strip()
        conversation.append(AIMessage(content=content))
        print(f"\n[Orchestrator]\n{content}\n")

        if _looks_like_json(content):
            return _strip_fence(content)

        if "[READY]" in content:
            human = input("You (ok=confirm / type to continue): ").strip()
            if human.lower() in ("ok", "yes", "y", "go", "confirm"):
                conversation.append(HumanMessage(content="OK, please output the final JSON now."))
                return _invoke_json(model, conversation)
            conversation.append(HumanMessage(content=human))
            continue

        human = input("You: ").strip()
        conversation.append(HumanMessage(content=human))


def _parse_json_with_retry(model, conversation: list, final_text: str) -> dict:
    """
    Parse the final text as JSON with retry mechanism.
    """
    while True:
        print(f"\n[alignment] JSON:\n{final_text}\n")
        try:
            return json.loads(final_text)
        except json.JSONDecodeError as e:
            print(f"[alignment] Invalid JSON: {e}")
            input("You: Invalid JSON! Press enter to retry. ")
            conversation.append(HumanMessage(
                content=f"Your last JSON was invalid ({e}). Please output valid JSON only, no extra text."))
            final_text = _invoke_json(model, conversation)


def _compose_return(data: dict, cfg) -> dict:
    """
    Compose the return data for the alignment phase.
    """
    task_type = data.get("task_type", "general")
    reasoning = data.get("agent_split_reasoning", "")

    sub_agents = []
    for sa in data.get("sub_agents", []):
        sub_agents.append(SubAgentConfig(
            label=sa.get("label", "Agent"),
            role=sa.get("role", "unknown"),
            description=sa.get("description", ""),
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        ))

    print(f"[alignment] Done: task_type={task_type}, sub_agents={[s.label for s in sub_agents]}")
    print("=" * 50)

    return {
        "alignment": AlignmentPhaseState(
            task_type=task_type,
            agent_split_reasoning=reasoning,
        ),
        "sub_agents": sub_agents,
        "current_phase": "research",
    }


# ============================================================
# Node implementation
# ============================================================
def make_alignment_node():
    """
    Create alignment node
    """

    def alignment_node(state: AgenticWorkflowState) -> dict:
        """
        Define the alignment node behavior.
        """
        cfg = state.orchestrator

        model = _init_model(cfg)
        conversation = _init_orchestrator_human_conversation(state)
        final_text = _run_conversation_loop(model, conversation)
        data = _parse_json_with_retry(model, conversation, final_text)
        return _compose_return(data, cfg)

    return alignment_node
