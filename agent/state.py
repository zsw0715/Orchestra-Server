"""
Overall Agentic Workflow 状态对象
"""
from typing import Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
import uuid


# AG2 Chatting Room State
class ChattingRoomState(BaseModel):
    """
    AG2 Chatting Room 状态对象
    Attributes:
        xxx
    """
    pass


# Agent State
class OrchestratorConfig(BaseModel):
    """
    Orchestrator Agent 配置对象
    Attributes:
        xxx
    """
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str = "Orchestrator"
    phase: str = "alignment"
    status: str = "idle"
    system_prompt: str
    model: str
    model_icon: str
    temperature: float = 0.3
    max_tokens: int = 4096
    reasoning: bool = True
    max_rounds: int = 3
    subagents: list = Field(default_factory=list)
    tools: list = Field(default_factory=list)
    skills: list = Field(default_factory=list)
    messages: list = Field(default_factory=list)


# Phase State
class AlignmentPhaseState(BaseModel):
    """
    Alignment Phase 状态对象
    Attributes:
        xxx
    """
    pass


class ResearchPhaseState(BaseModel):
    """
    Research Phase 状态对象
    Attributes:
        xxx
    """
    pass


class PlanningPhaseState(BaseModel):
    """
    Planning Phase 状态对象
    Attributes:
        xxx
    """
    pass


class WritingPhaseState(BaseModel):
    """
    Writing Phase 状态对象
    Attributes:
        xxx
    """
    pass


# 主 State (Workflow State)
class AgenticWorkflowState(BaseModel):
    """
    Agentic Workflow 状态对象
    贯穿 LangGraph 所有 Phase 的全局状态。
    Attributes:
        workflow_id: Agentic Workflow ID，用于唯一标识会话
        messages: 当前 Agentic Workflow 的所有消息列表
        human_checkpoint: 当前 Agentic Workflow 是否需要人工审核卡点
    """
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    human_checkpoint: bool = False