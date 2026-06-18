"""
Overall Agentic Workflow State Object
"""
from typing import Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
import uuid


# ============================================================
# Infrastructure
# ============================================================
class NodePosition(BaseModel):
    """
    React Flow Node Position.
    
    Attributes:
        x: horizontal coordinate
        y: Node vertical coordinate
    """
    x: float = 0
    y: float = 0


class ExternalKBState(BaseModel):
    """
    External Knowledge Base Node State.
    Only stores metadata, actual file content are vectorized and stored in ChromaDB.

    Attributes:
        label:            Frontend node display name.
        status:           Current status (idle | indexing | ready | error).
        source:           Knowledge base type description ("RAG / personal knowledge base").
        document_count:   Indexed document count.
        files:            Indexed file names.
        folder_name:      Selected folder name.
        collection_name:  ChromaDB collection name, Sub-Agent retrieves from.
        position:         Frontend node position.
        node_type:        React Flow node type identifier.
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
    Common Chat message for Research / Plan / Write phase.

    Attributes:
        role:      Speaker role ("accommodationAgent" | "foodAgent" | "orchestrator" | "human").
        content:   Message body.
        timestamp: ISO 8601 timestamp.
    """
    role: str
    content: str
    timestamp: str


# ============================================================
# Agent Configuration and Runtime State
# ============================================================
class OrchestratorConfig(BaseModel):
    """
    Orchestrator Agent 配置与运行时状态

    Attributes:
        agent_id:       Agent unique identifier.
        label:          Frontend node display name.
        phase:          Current phase in the workflow (alignment/research/plan/write/done).
        status:         Current status (idle/thinking/waiting_human/done/error).
        system_prompt:  Orchestrator system prompt.
        model:          Model ID (like deepseek-v4-flash).
        model_icon:     Frontend model icon identifier.
        temperature:    Model temperature parameter.
        max_tokens:     Maximum output token count.
        reasoning:      Whether to enable reasoning.
        subagents:      List of Sub-Agent dispatched.
        tools:          Available tools list.
        skills:         Available skills list.
        self_messages:  Orchestrator's own message history, manually managed.
        position:       Frontend node position.
        node_type:      React Flow node type identifier.
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
    Sub-Agent Agent Configuration and Runtime State

    Attributes:
        agent_id:        SubAgent unique identifier.
        label:           Frontend node display name.
        role:            Domain role (like accommodation/food/sightseeing).
        description:     Description text displayed in the frontend node.
        phase:           Current phase in the workflow.
        status:          Current status (idle/thinking/waiting_human/done/error).
        system_prompt:   Sub-Agent system prompt.
        model:           Model ID (like deepseek-v4-flash).
        model_icon:      Frontend model icon identifier.
        temperature:     Model temperature parameter.
        max_tokens:      Maximum output token count.
        reasoning:       Whether to enable reasoning.
        max_rounds:      Maximum coordination rounds.
        tools:           Available tools list.
        skills:          Available skills list.
        self_messages:   SubAgent's message history.
        findings:        List of findings in Phase 1 Research.
        section_content: Content written by SubAgent in Phase 3 Write.
        position:        Frontend node position.
        node_type:       React Flow node type identifier.
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
# Phase State — Independent Output for Each Phase
# ============================================================
class AlignmentPhaseState(BaseModel):
    """
    Phase 0: Alignment Phase Output.
    The user engages in multiple rounds of dialogues with Orchestrator, 
    aligning requirements, determining task types, and jointly formulating 
    the sub-Agent splitting plan.
    Dialogues are recorded in AgenticWorkflowState.messages, 
    and sub-Agent agents are dispatched in AgenticWorkflowState.sub_agents.

    Attributes:
        task_type:              Task type ("travel" | "industry_report" | "study_abroad" | ……).
        agent_split_reasoning:  Orchestrator's reasoning process for splitting the task into sub-Agent agents.
    """
    task_type: str = ""
    agent_split_reasoning: str = ""


class ResearchPhaseState(BaseModel):
    """
    Phase 1: Research Phase Output
    Each sub-agent conducts independent research in parallel, 
    aiming to maximize the breadth of information, and allowing contradictions to exist.
    Orchestrator collects all the findings and writes a global summary. 
    Cross-domain contradictions are left for the Phase 2 group chat to naturally expose.

    Attributes:
        agent_statuses:    Research status mapping (agent_name → thinking | done | error).
        research_summary:  Orchestrator collects all the findings and writes a global summary.
    """
    agent_statuses: dict[str, str] = Field(default_factory=dict)
    research_summary: str = ""


class PlanningPhaseState(BaseModel):
    """
    Phase 2: Planning Phase Output
    Orchestrator launches an AG2 group chat, where each sub-agent negotiates 
    to resolve cross-domain contradictions exposed in the Research Phase.
    Human participants can inject gradient signals 
    (e.g., "Focus on food and accommodation, change hotel to Guanyin Bridge") during the chat,
    which are then reinjected into the group chat, 
    iteratively until a conflict-free structured plan is produced.

    Attributes:
        agent_statuses:      Group chat status mapping (agent_name → talking | waiting | done).
        content_summary:     Group chat summary text (frontend node directly renders).
        chat_history:        Full group chat history.
        round_count:         Total rounds of group chat.
        human_interventions: List of human gradient signals [{round: int, feedback: str}]        
        position:            Frontend node position.
        node_type:           React Flow node type identifier.
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
    Phase 3: Writing Phase Output
    Each sub-agent writes their domain-specific content section in order.
    Once all agents have completed their sections, 
    Orchestrator launches an AG2 correction chat room, 
    where all agents review each other's work for cross-domain conflicts 
    (e.g., time conflicts, logical vulnerabilities).
    Each agent's draft is stored in SubAgentConfig.section_content.

    Attributes:
        agent_statuses: Writing status mapping (agent_name → writing | reviewing | done | error).
        draft_order:    Writing order (agent label list).
        chat_history:   Full correction chat room dialogues.
        summary:        Correction chat room summary.
    """
    agent_statuses: dict[str, str] = Field(default_factory=dict)
    draft_order: list[str] = Field(default_factory=list)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    summary: str = ""


class OutputGatheringState(BaseModel):
    """
    After the Writing Phase, Orchestrator gathers all the outputs from all sub-agents.

    Attributes:
        final_output: Final concatenated output text.
        position:     Frontend node position.
        node_type:    React Flow node type identifier.
    """
    final_output: str = ""
    position: NodePosition = Field(default_factory=NodePosition)
    node_type: str = "output"


# ============================================================
# Main Workflow State, For LangGraph StateGraph
# ============================================================
class AgenticWorkflowState(BaseModel):
    """
    The global state that runs through all phases of LangGraph.

    Merging behavior:
        - messages: The only field that uses the "add_messages" reducer. After the node returns, it automatically appends rather than replaces.
        - All other top-level fields: Complete replacement. Each node must return the complete corresponding object.
        For example, the "research_node" must return {"research": ResearchPhaseState(...)} }

    Attributes:
        workflow_id: The unique identifier of this workflow, which is consistent with the PostgresSaver thread_id.
        user_query: The original user requirement text, which is reused throughout the process (each Agent retrieves/researches based on this basis).
        messages: The global conversation history between the user and the Orchestrator, with the add_messages reducer automatically accumulating.
        current_phase: The current macro stage (alignment | research | plan | write | done).
        orchestrator: The configuration and runtime status of the Orchestrator.
        sub_agents: The configuration and runtime status list of all sub Agents, which is reused throughout the process after the Alignment stage is determined.
        alignment: The output of Phase 0 alignment stage.
        research: The output of Phase 1 research stage.
        planning: The output of Phase 2 planning stage.
        writing: The output of Phase 3 writing stage.
        output: The final aggregated output.
        external_kb: The status of external knowledge nodes (metadata identifier, actual content is in ChromaDB).
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
