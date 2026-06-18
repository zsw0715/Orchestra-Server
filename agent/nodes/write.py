"""Phase 3: Write — 子 Agent 撰写 + 纠错审查"""
from agent.state import AgenticWorkflowState, WritingPhaseState, OutputGatheringState


def make_write_node():
    """创建 write 节点。"""

    def write_node(state: AgenticWorkflowState) -> dict:
        print("[write] Phase 3 完成 → done")
        return {
            "writing": WritingPhaseState(summary="demo: 纠错审查通过"),
            "output": OutputGatheringState(final_output="demo final output"),
            "current_phase": "done",
        }

    return write_node
