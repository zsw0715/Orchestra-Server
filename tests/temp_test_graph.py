"""本地测试入口：交互式终端演示完整 4 Phase 流程"""
from langgraph.types import Command

from agent.graph import create_graph
from agent.state import AgenticWorkflowState


def main():
    graph = create_graph()
    config = {"configurable": {"thread_id": "demo-run-005"}}
    initial_state = AgenticWorkflowState(user_query="五一去重庆玩")

    print("=" * 50)
    print(f"初始 phase: {initial_state.current_phase}")
    print("=" * 50)

    # alignment — 节点内部有多轮对话 input()
    state = graph.invoke(initial_state, config)
    print(f"\n✅ alignment → research (sub_agents: {len(state['sub_agents'])} 个)")

    # research
    human = input("\n👤 人类: 批准进入 Research？(yes/no): ").strip().lower()
    if human != "yes":
        print("❌ 中断")
        exit(0)
    state = graph.invoke(Command(resume=human), config)
    print(f"✅ research → {state['current_phase']}")

    # plan
    human = input("\n👤 人类: 批准进入 Plan？(yes/no): ").strip().lower()
    if human != "yes":
        print("❌ 中断")
        exit(0)
    state = graph.invoke(Command(resume=human), config)
    print(f"✅ plan → {state['current_phase']}")

    # write
    human = input("\n👤 人类: 批准进入 Write？(yes/no): ").strip().lower()
    if human != "yes":
        print("❌ 中断")
        exit(0)
    state = graph.invoke(Command(resume=human), config)
    print(f"✅ write → {state['current_phase']}")

    print("\n" + "=" * 50)
    print("🎉 跑通！")
    print(f"   task_type: {state['alignment'].task_type}")
    print(f"   summary:   {state['research'].research_summary}")
    print(f"   plan:      {state['planning'].content_summary}")
    print(f"   output:    {state['output'].final_output}")
    print("=" * 50)


if __name__ == "__main__":
    main()
