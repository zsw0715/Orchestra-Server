"""
Phase 2: Plan — autogen GroupChat for cross-agent coordination
"""
import time

from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

from agent.state import AgenticWorkflowState, PlanningPhaseState, ChatMessage
from config.model import build_autogen_llm_config
from prompts.phase import PHASE_SYSTEM_PROMPT


# ============================================================
# Internal helpers
# ============================================================
def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


# ============================================================
# Building blocks
# ============================================================
def _init_plan(state: AgenticWorkflowState):
    print("=" * 50)
    print(f"  Phase 2: Plan — Group Chat ({len(state.sub_agents)} agents, max_rounds={state.orchestrator.max_rounds})")
    print("=" * 50)
    print(f"\nResearch summary:\n  {state.research.research_summary[:200]}...\n")


def _create_orchestrator_agent(state: AgenticWorkflowState) -> AssistantAgent:
    cfg = state.orchestrator
    return AssistantAgent(
        name="Orchestrator",
        system_message=PHASE_SYSTEM_PROMPT["plan_orchestrator"],
        llm_config=build_autogen_llm_config(cfg.model, cfg.temperature),
        max_consecutive_auto_reply=2,
    )


def _create_sub_agents(state: AgenticWorkflowState, findings_map: dict) -> list[AssistantAgent]:
    agents = []
    for sub in state.sub_agents:
        findings_text = findings_map.get(sub.label, "no findings yet")
        system_msg = PHASE_SYSTEM_PROMPT["plan_agent"].format(
            label=sub.label,
            findings=findings_text[:2000],
        )
        agents.append(AssistantAgent(
            name=sub.label,
            system_message=system_msg,
            llm_config=build_autogen_llm_config(sub.model, sub.temperature),
            max_consecutive_auto_reply=2,
        ))
    return agents


def _run_single_chat(user_proxy, manager, initial_message: str) -> list[ChatMessage]:
    """Run one group-chat session, return parsed messages."""
    user_proxy.initiate_chat(manager, message=initial_message, clear_history=True)

    messages: list[ChatMessage] = []
    for msg in manager.groupchat.messages:
        name = msg.get("name", "unknown")
        content = msg.get("content", "")
        role = msg.get("role", "")
        if role == "assistant" or name == "user_proxy":
            messages.append(ChatMessage(role=name, content=str(content), phase="plan", timestamp=_now_iso()))

    return messages


def _compose_return(messages: list[ChatMessage], round_count: int, interventions: list[dict]) -> dict:
    summary = ""
    for m in messages:
        if m.role == "Orchestrator":
            summary = m.content[:500]
            break
    print(f"\n[plan] Done — {max(round_count, 1)} session(s), {len(messages)} messages")
    print("=" * 50)
    return {
        "planning": PlanningPhaseState(
            content_summary=summary or "group chat completed",
            chat_history=messages,
            round_count=round_count,
            human_interventions=interventions,
        ),
        "current_phase": "write",
    }


# ============================================================
# Node
# ============================================================
def make_plan_node():
    """Create plan node — autogen GroupChat with human gradient injection."""

    def plan_node(state: AgenticWorkflowState) -> dict:
        _init_plan(state)

        findings_map = {a.label: (a.findings[-1] if a.findings else "no findings") for a in state.sub_agents}

        orch_agent = _create_orchestrator_agent(state)
        sub_agents = _create_sub_agents(state, findings_map)

        all_agents = [orch_agent] + sub_agents
        # Ensure every agent gets at least one turn, plus back-and-forth
        max_rounds = max(state.orchestrator.max_rounds, len(all_agents) * 2)

        user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=0,
        )

        initial_message = (
            f"User request: {state.user_query}\n\n"
            f"Research summary: {state.research.research_summary}\n\n"
            "Discuss and produce a coordinated plan. Orchestrator, lead the discussion."
        )

        all_messages: list[ChatMessage] = []
        interventions: list[dict] = []
        session = 0

        while True:
            session += 1
            groupchat = GroupChat(
                agents=all_agents,
                messages=[],
                max_round=max_rounds,
                speaker_selection_method="round_robin",
            )
            manager = GroupChatManager(
                groupchat=groupchat,
                llm_config=build_autogen_llm_config(state.orchestrator.model, state.orchestrator.temperature),
            )

            print(f"\n--- Group Chat session {session} ---")
            msgs = _run_single_chat(user_proxy, manager, initial_message)
            all_messages.extend(msgs)

            for m in msgs:
                print(f"\n[{m.role}] {m.content[:300]}...")

            human = input("\nYou (ok / type feedback to re-run): ").strip()
            if human.lower() in ("ok", "yes", "y", "go", "confirm", ""):
                break

            interventions.append({"session": session, "feedback": human})
            initial_message = f"User feedback: {human}\n\nPlease re-discuss incorporating this feedback."

        return _compose_return(all_messages, session, interventions)

    return plan_node
