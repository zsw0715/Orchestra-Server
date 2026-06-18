"""
Phase 1: Research — per-agent multi-turn research conversations
"""
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent.state import AgenticWorkflowState, ResearchPhaseState, ChatMessage
from config.model import init_model
from prompts.phase import PHASE_SYSTEM_PROMPT


# ============================================================
# Internal helpers
# ============================================================
def _strip_fence(text: str) -> str:
    return text.removeprefix("```").removesuffix("```").strip()


def _looks_like_json(text: str) -> bool:
    return text.startswith("{")


def _invoke_json(model, conversation: list) -> str:
    response = model.invoke(conversation)
    return _strip_fence(response.content.strip())


# ============================================================
# Building blocks
# ============================================================
def _init_model(cfg):
    return init_model(
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        streaming=False,
    )


def _init_research(state: AgenticWorkflowState):
    print("=" * 50)
    print(f"  Phase 1: Research — {len(state.sub_agents)} sub-agents")
    print("=" * 50)


def _run_agent_conversation(model, agent, user_query: str, context_messages: list) -> str:
    """Single-agent while-loop conversation. Returns findings text on [READY] + ok."""
    prompt = PHASE_SYSTEM_PROMPT["research"].format(
        label=agent.label,
        description=agent.description,
    )
    conversation = [SystemMessage(content=prompt)]

    # Inject alignment context so sub-agent knows what was already discussed
    if context_messages:
        conversation.append(HumanMessage(content="Previous conversation between user and Orchestrator (already resolved):"))
        conversation.extend(context_messages)

    conversation.append(HumanMessage(content=f"Now research your specific domain and produce findings. Do NOT ask questions already answered above."))

    print(f"\n--- {agent.label} ---")

    while True:
        response = model.invoke(conversation)
        content = response.content.strip()
        conversation.append(AIMessage(content=content))
        print(f"\n[{agent.label}]\n{content}\n")

        if _looks_like_json(content):
            return _strip_fence(content)

        if "[READY]" in content:
            human = input("You (ok=confirm / type to continue): ").strip()
            if human.lower() in ("ok", "yes", "y", "go", "confirm"):
                conversation.append(HumanMessage(
                    content="OK, please output your findings as a JSON object now."))
                return _invoke_json(model, conversation)
            conversation.append(HumanMessage(content=human))
            continue

        human = input("You: ").strip()
        conversation.append(HumanMessage(content=human))


def _summarize_findings(model, findings_map: dict, user_query: str) -> str:
    """Orchestrator reads all findings and writes a global summary."""
    parts = "\n\n".join(f"### {label}\n{text}" for label, text in findings_map.items())
    prompt = (
        f"User request: {user_query}\n\n"
        f"All sub-agent research findings:\n\n{parts}\n\n"
        "Write a concise global summary (under 300 words). Identify cross-domain conflicts if any."
    )
    response = model.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def _compose_return(findings_map: dict, summary: str) -> dict:
    print(f"\n[research] Done: {len(findings_map)} agents, summary {len(summary)} chars")
    print("=" * 50)
    return {
        "research": ResearchPhaseState(research_summary=summary),
        "current_phase": "plan",
    }


# ============================================================
# Node
# ============================================================
def make_research_node():
    """Create research node — serial foreach over sub-agents."""

    def research_node(state: AgenticWorkflowState) -> dict:
        if not state.sub_agents:
            return _compose_return({}, "No sub-agents, research skipped.")

        _init_research(state)

        orch_model = _init_model(state.orchestrator)
        context_msgs = state.messages  # Phase 0 alignment conversation

        findings_map = {}
        for agent in state.sub_agents:
            agent_model = _init_model(agent)
            findings_map[agent.label] = _run_agent_conversation(agent_model, agent, state.user_query, context_msgs)
            agent.findings.append(findings_map[agent.label])
            agent.status = "done"
            print(f"\n✓ {agent.label} done ({len(findings_map[agent.label])} chars)")

        summary = _summarize_findings(orch_model, findings_map, state.user_query)
        return _compose_return(findings_map, summary)

    return research_node
