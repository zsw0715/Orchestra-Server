"""
Overall Agentic Workflow 状态对象
"""
from typing import Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
import uuid


# ============================================================
# 基础设施
# ============================================================
class NodePosition(BaseModel):
    """
    React Flow 节点画布坐标。
    
    Attributes:
        x: 节点横坐标
        y: 节点纵坐标
    """
    x: float = 0
    y: float = 0


class ExternalKBState(BaseModel):
    """
    外部知识库节点状态。
    仅存元数据标识，真正的文件内容向量化后存储在 ChromaDB 中。

    Attributes:
        label:            前端节点显示名称。
        status:           当前状态 (idle | indexing | ready | error)。
        source:           知识库类型描述 ("RAG / 个人数据库")。
        document_count:   已索引的文档数量。
        files:            已索引的文件名列表。
        folder_name:      用户选中的文件夹名称。
        collection_name:  ChromaDB 中对应的 collection 名称，SubAgent 检索时以此定位。
        position:         前端画布坐标。
        node_type:        React Flow 节点类型标识。
    """
    label: str = ""
    status: str = "idle"
    source: str = ""
    document_count: int = 0
    files: list[str] = Field(default_factory=list)
    folder_name: str = ""
    collection_name: str = ""
    position: NodePosition = Field(default_factory=NodePosition)
    node_type: str = "knowledge-base"


class ChatMessage(BaseModel):
    """
    通用聊天消息，Research / Plan / Write 阶段共用，etc。

    Attributes:
        role:      发言者角色 ("住宿Agent" | "美食Agent" | "orchestrator" | "human")。
        content:   消息正文。
        timestamp: ISO 8601 时间戳。
    """
    role: str
    content: str
    timestamp: str


# ============================================================
# Agent 配置与运行时状态
# ============================================================
class OrchestratorConfig(BaseModel):
    """
    Orchestrator Agent 配置与运行时状态

    Attributes:
        agent_id:       Agent 唯一标识。
        label:          前端节点显示名称。
        phase:          当前所处宏观阶段 (alignment/research/plan/write/done)。
        status:         当前运行状态 (idle/thinking/waiting_human/done/error)，驱动前端光晕。
        system_prompt:  Orchestrator 的系统提示词。
        model:          使用的模型 ID (如 deepseek-v4-flash)。
        model_icon:     前端模型图标标识。
        temperature:    模型温度参数。
        max_tokens:     最大输出 token 数。
        reasoning:      是否启用推理/思考链。
        max_rounds:     最大协调轮次。
        subagents:      已派出的子 Agent 列表 (SubAgentConfig)，前端节点内缩略渲染。
        tools:          可用工具列表。
        skills:         可用技能列表。
        self_messages:  Orchestrator 自己的发言记录，手动管理。
        position:       前端画布坐标。
        node_type:      React Flow 节点类型标识。
    """
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str = "Orchestrator"
    phase: str = "alignment"
    status: str = "idle"
    system_prompt: str = ""
    model: str = ""
    model_icon: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    reasoning: bool = True
    max_rounds: int = 3
    subagents: list = Field(default_factory=list)
    tools: list = Field(default_factory=list)
    skills: list = Field(default_factory=list)
    self_messages: list = Field(default_factory=list)
    position: NodePosition = Field(default_factory=NodePosition)
    node_type: str = "orchestrator"


class SubAgentConfig(BaseModel):
    """
    子 Agent 配置与运行时状态

    Attributes:
        agent_id:        SubAgent 唯一标识。
        label:           前端节点显示名称。
        role:            领域角色 (如 accommodation/food/sightseeing)。
        description:     前端节点内显示的描述文本。
        phase:           当前所处宏观阶段。
        status:          当前运行状态 (idle/thinking/waiting_human/done/error)。
        system_prompt:   子 Agent 的系统提示词。
        model:           使用的模型 ID。
        model_icon:      前端模型图标标识。
        temperature:     模型温度参数。
        max_tokens:      最大输出 token 数。
        reasoning:       是否启用推理/思考链。
        max_rounds:      最大协调轮次。
        tools:           可用工具列表。
        skills:          可用技能列表。
        self_messages:   该 SubAgent 的发言记录。
        findings:        该 SubAgent 在 Phase 1 Research 调研发现列表。
        section_content: 该 SubAgent 在 Phase 3 Write 撰写的章节内容。
        position:        前端画布坐标。
        node_type:       React Flow 节点类型标识。
    """
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str
    role: str
    description: str
    phase: str = "alignment"
    status: str = "idle"
    system_prompt: str = ""
    model: str = ""
    model_icon: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    reasoning: bool = True
    max_rounds: int = 10
    tools: list = Field(default_factory=list)
    skills: list = Field(default_factory=list)
    self_messages: list = Field(default_factory=list)
    findings: list = Field(default_factory=list)
    section_content: str = ""
    position: NodePosition = Field(default_factory=NodePosition)
    node_type: str = "subagent"


# ============================================================
# Phase State — 各阶段独立产出
# ============================================================
class AlignmentPhaseState(BaseModel):
    """
    Phase 0: Alignment 阶段产出。
    用户与 Orchestrator 多轮对话，对齐需求、确定任务类型，共同制定子 Agent 拆分方案。
    对话过程记录在 AgenticWorkflowState.messages 中，Agent 阵容写入 AgenticWorkflowState.sub_agents。

    Attributes:
        task_type:              任务类型 ("travel" | "industry_report" | "study_abroad" | ……)，
                                后续各 Phase 节点可根据此字段选择对应的 Few-Shot 模板调优 LLM 输出。
        agent_split_reasoning:  Orchestrator 将任务拆分为这些子 Agent 维度的推理过程。
    """
    task_type: str = ""
    agent_split_reasoning: str = ""


class ResearchPhaseState(BaseModel):
    """
    Phase 1: Research 阶段产出。
    各子 Agent 并行独立调研，追求信息广度最大化，允许矛盾存在。
    Orchestrator 收取所有 findings 后撰写一份全局摘要，跨领域矛盾留给 Phase 2 群聊自然暴露。

    Attributes:
        agent_statuses:    各 Agent 调研进度映射表 (agent_name → thinking | done | error)。
        research_summary:  Orchestrator 汇总所有 finding 后的全局调研摘要。
    """
    agent_statuses: dict[str, str] = Field(default_factory=dict)
    research_summary: str = ""


class PlanningPhaseState(BaseModel):
    """
    Phase 2: Plan 阶段产出。
    启动 AG2 群聊，各子 Agent 在 Orchestrator 主持下协商解决 Research 阶段暴露的跨领域矛盾。
    人类可在群聊过程中注入梯度信号（如“全部以美食为中心，住宿改观音桥”），
    系统将此信号重新注入群聊，循环直至产出无冲突的结构化计划。

    Attributes:
        agent_statuses:      各 Agent 在群聊中的状态映射表 (agent_name → talking | waiting | done)。
        content_summary:     群聊协调结果的摘要文本（前端 Plan 节点直接渲染）。
        chat_history:        完整的群聊记录（前端点击 Plan 节点展开查看）。
        round_count:         群聊运行的总轮次。
        human_interventions: 人类梯度信号记录列表 [{round: int, feedback: str}]。
        position:            前端画布坐标。
        node_type:           React Flow 节点类型标识。
    """
    agent_statuses: dict[str, str] = Field(default_factory=dict)
    content_summary: str = ""
    chat_history: list[ChatMessage] = Field(default_factory=list)
    round_count: int = 0
    human_interventions: list[dict] = Field(default_factory=list)
    position: NodePosition = Field(default_factory=NodePosition)
    node_type: str = "plan"


class WritingPhaseState(BaseModel):
    """
    Phase 3: Write 阶段产出。
    各子 Agent 按顺序撰写自己领域的内容章节，全部完成后启动 AG2 纠错聊天室，
    所有 Agent 对终稿进行交叉审查（时间矛盾、逻辑漏洞等）。
    各章节草稿储存在 SubAgentConfig.section_content 中。

    Attributes:
        agent_statuses: 各 Agent 撰写/审查进度映射表 (agent_name → writing | reviewing | done | error)。
        draft_order:    撰写顺序（agent label 列表），按序执行以保持上下文连贯。
        chat_history:   纠错聊天室的完整对话记录。
        summary:        纠错聊天室的结论摘要。
    """
    agent_statuses: dict[str, str] = Field(default_factory=dict)
    draft_order: list[str] = Field(default_factory=list)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    summary: str = ""


class OutputGatheringState(BaseModel):
    """
    Write 阶段结束后，Orchestrator 将所有 Agent 的 section_content 拼接为全文。

    Attributes:
        final_output: 拼接合并后的最终输出全文。
        position:     前端画布坐标。
        node_type:    React Flow 节点类型标识。
    """
    final_output: str = ""
    position: NodePosition = Field(default_factory=NodePosition)
    node_type: str = "output"


# ============================================================
# 主 State — LangGraph StateGraph 使用
# ============================================================
class AgenticWorkflowState(BaseModel):
    """
    贯穿 LangGraph 所有 Phase 的全局状态。

    合并行为：
      - messages:  唯一使用 add_messages reducer 的字段，节点返回后自动追加而非替换。
      - 其余所有顶层字段: 整体替换。每个节点必须返回完整的对应对象。
        例如 research_node 需返回 {"research": ResearchPhaseState(...)}。

    Attributes:
        workflow_id:     本次工作流的唯一标识，与 PostgresSaver thread_id 一致。
        user_query:      用户原始需求文本，全流程复用（各 Agent 检索/调研以此为基础）。
        messages:        用户 ↔ Orchestrator 的全局对话历史，add_messages reducer 自动累加。
        current_phase:   当前宏观阶段 (alignment | research | plan | write | done)。
        orchestrator:    Orchestrator 的配置与运行时状态。
        sub_agents:      所有子 Agent 的配置与运行时状态列表，Alignment 阶段确定后全流程复用。
        alignment:       Phase 0 对齐阶段产物。
        research:        Phase 1 研究阶段产物。
        planning:        Phase 2 规划阶段产物。
        writing:         Phase 3 撰写阶段产物。
        output:          最终汇总产物。
        external_kb:     外部知识库节点状态（元数据标识，实际内容在 ChromaDB）。
    """
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_query: str = ""
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    current_phase: str = "alignment"
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    sub_agents: list[SubAgentConfig] = Field(default_factory=list)
    alignment: AlignmentPhaseState = Field(default_factory=AlignmentPhaseState)
    research: ResearchPhaseState = Field(default_factory=ResearchPhaseState)
    planning: PlanningPhaseState = Field(default_factory=PlanningPhaseState)
    writing: WritingPhaseState = Field(default_factory=WritingPhaseState)
    output: OutputGatheringState = Field(default_factory=OutputGatheringState)
    external_kb: ExternalKBState = Field(default_factory=ExternalKBState)
