"""Phase 2: Plan — 群聊协调"""
from agent.state import AgenticWorkflowState, PlanningPhaseState


def make_plan_node():
    """创建 plan 节点。"""

    def plan_node(state: AgenticWorkflowState) -> dict:
        print("[plan] Phase 2 完成 → write")
        return {
            "planning": PlanningPhaseState(content_summary="demo: 群聊协调完成"),
            "current_phase": "write",
        }

    return plan_node
