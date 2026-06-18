"""Phase 1: Research — 子 Agent 并行调研"""
from agent.state import AgenticWorkflowState, ResearchPhaseState


def make_research_node():
    """创建 research 节点。"""

    def research_node(state: AgenticWorkflowState) -> dict:
        print("[research] Phase 1 完成 → plan")
        return {
            "research": ResearchPhaseState(research_summary="demo: 三个领域调研完成"),
            "current_phase": "plan",
        }

    return research_node
