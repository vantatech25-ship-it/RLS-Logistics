"""Workflow Mapping and Process Analysis Module
Visualizes and documents workflows to identify automation opportunities
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    CONDITION = "condition"
    AUTOMATED_TASK = "automated_task"
    MANUAL_TASK = "manual_task"
    WEBHOOK = "webhook"
    API_CALL = "api_call"
    NOTIFICATION = "notification"
    APPROVAL = "approval"


class AutomationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProcessStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    OPTIMIZED = "optimized"
    DEPRECATED = "deprecated"


@dataclass
class WorkflowNode:
    node_id: str
    name: str
    node_type: NodeType
    description: str
    estimated_duration_minutes: int
    automation_potential: float
    requires_approval: bool = False
    assigned_role: Optional[str] = None
    tools_required: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class WorkflowConnection:
    connection_id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None
    probability: float = 1.0


@dataclass
class Workflow:
    workflow_id: str
    name: str
    description: str
    category: str
    status: ProcessStatus
    nodes: List[WorkflowNode]
    connections: List[WorkflowConnection]
    created_at: datetime
    updated_at: datetime
    estimated_cycle_time_minutes: int
    automation_score: float
    bottleneck_nodes: List[str] = field(default_factory=list)
    volume_per_month: int = 0
    avg_processing_time_minutes: int = 0


@dataclass
class ProcessMetrics:
    workflow_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_completion_time: float
    min_completion_time: float
    max_completion_time: float
    automation_coverage: float
    throughput_per_day: float


class WorkflowMapper:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.workflows: Dict[str, Workflow] = {}
        self.process_history: List[Dict] = []

    def create_workflow(self, name: str, description: str, category: str) -> Workflow:
        workflow_id = f"WF-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            category=category,
            status=ProcessStatus.DRAFT,
            nodes=[],
            connections=[],
            created_at=now,
            updated_at=now,
            estimated_cycle_time_minutes=0,
            automation_score=0.0,
        )
        self.workflows[workflow_id] = workflow
        return workflow

    def add_node(self, workflow_id: str, node: WorkflowNode) -> bool:
        if workflow_id not in self.workflows:
            return False
        workflow = self.workflows[workflow_id]
        workflow.nodes.append(node)
        workflow.updated_at = datetime.now()
        self._recalculate_automation_score(workflow_id)
        return True

    def add_connection(self, workflow_id: str, source_id: str, target_id: str, condition: Optional[str] = None) -> bool:
        if workflow_id not in self.workflows:
            return False
        connection = WorkflowConnection(
            connection_id=f"CONN-{uuid.uuid4().hex[:8].upper()}",
            source_node_id=source_id,
            target_node_id=target_id,
            condition=condition,
        )
        self.workflows[workflow_id].connections.append(connection)
        self.workflows[workflow_id].updated_at = datetime.now()
        return True

    def _calculate_automation_potential(self, node: WorkflowNode) -> float:
        if node.node_type in [NodeType.AUTOMATED_TASK, NodeType.API_CALL, NodeType.WEBHOOK]:
            return 0.95
        elif node.node_type == NodeType.MANUAL_TASK:
            return 0.20
        elif node.node_type == NodeType.DECISION or node.node_type == NodeType.CONDITION:
            return 0.75
        elif node.node_type == NodeType.APPROVAL:
            return 0.30
        elif node.node_type == NodeType.NOTIFICATION:
            return 0.90
        elif node.node_type in [NodeType.START, NodeType.END]:
            return 0.50
        return 0.40

    def _recalculate_automation_score(self, workflow_id: str) -> float:
        if workflow_id not in self.workflows:
            return 0.0
        workflow = self.workflows[workflow_id]
        if not workflow.nodes:
            return 0.0
        total_time = sum(n.estimated_duration_minutes for n in workflow.nodes)
        automated_time = sum(
            n.estimated_duration_minutes * self._calculate_automation_potential(n)
            for n in workflow.nodes
        )
        workflow.estimated_cycle_time_minutes = total_time
        workflow.automation_score = (automated_time / total_time * 100) if total_time > 0 else 0
        return workflow.automation_score

    def identify_bottlenecks(self, workflow_id: str) -> List[str]:
        if workflow_id not in self.workflows:
            return []
        workflow = self.workflows[workflow_id]
        bottlenecks = []
        for node in workflow.nodes:
            if node.estimated_duration_minutes > 60 or node.node_type == NodeType.MANUAL_TASK:
                bottlenecks.append(node.node_id)
        workflow.bottleneck_nodes = bottlenecks
        return bottlenecks

    def suggest_automation(self, workflow_id: str) -> List[Dict]:
        if workflow_id not in self.workflows:
            return []
        workflow = self.workflows[workflow_id]
        suggestions = []
        for node in workflow.nodes:
            if node.node_type == NodeType.MANUAL_TASK:
                suggestions.append({
                    "node_id": node.node_id,
                    "node_name": node.name,
                    "current_type": "manual",
                    "suggested_type": "automated_task",
                    "estimated_time_saved_minutes": node.estimated_duration_minutes,
                    "priority": self._determine_priority(node),
                    "implementation_effort": "medium",
                    "tools_needed": self._suggest_tools(node),
                })
            elif node.node_type == NodeType.DECISION:
                suggestions.append({
                    "node_id": node.node_id,
                    "node_name": node.name,
                    "current_type": "human_decision",
                    "suggested_type": "ai-assisted_decision",
                    "estimated_time_saved_minutes": int(node.estimated_duration_minutes * 0.7),
                    "priority": AutomationPriority.MEDIUM.value,
                    "implementation_effort": "high",
                    "tools_needed": ["ML model", "Rule engine"],
                })
        return sorted(suggestions, key=lambda x: x["estimated_time_saved_minutes"], reverse=True)

    def _determine_priority(self, node: WorkflowNode) -> str:
        if node.estimated_duration_minutes > 120:
            return AutomationPriority.CRITICAL.value
        elif node.estimated_duration_minutes > 60:
            return AutomationPriority.HIGH.value
        elif node.estimated_duration_minutes > 30:
            return AutomationPriority.MEDIUM.value
        return AutomationPriority.LOW.value

    def _suggest_tools(self, node: WorkflowNode) -> List[str]:
        if "data entry" in node.name.lower():
            return ["OCR", "Form automation", "RPA"]
        elif "email" in node.name.lower():
            return ["Email automation", "NLP parsing"]
        elif "report" in node.name.lower():
            return ["Report generator", "BI tool"]
        elif "approval" in node.name.lower():
            return ["Workflow engine", "Notification system"]
        return ["RPA", "API integration"]

    def create_sample_workflow(self, workflow_type: str) -> Workflow:
        if workflow_type == "order_intake":
            workflow = self.create_workflow("Order Intake Process", "Automated order processing workflow", "sales")
            steps = [
                ("Receive Order", NodeType.START, 5, 0.50),
                ("Validate Customer", NodeType.AUTOMATED_TASK, 10, 0.95),
                ("Check Inventory", NodeType.API_CALL, 15, 0.90),
                ("Credit Check", NodeType.DECISION, 20, 0.75),
                ("Approve Order", NodeType.APPROVAL, 30, 0.30),
                ("Generate Invoice", NodeType.AUTOMATED_TASK, 10, 0.95),
                ("Confirm Shipment", NodeType.AUTOMATED_TASK, 15, 0.90),
                ("Complete Order", NodeType.END, 5, 0.50),
            ]
        elif workflow_type == "freight_quoting":
            workflow = self.create_workflow("Freight Quoting Process", "Automated freight rate calculation", "logistics")
            steps = [
                ("Receive Quote Request", NodeType.START, 5, 0.50),
                ("Extract Details", NodeType.AUTOMATED_TASK, 10, 0.90),
                ("Calculate Rates", NodeType.API_CALL, 20, 0.95),
                ("Check Carrier Availability", NodeType.API_CALL, 15, 0.85),
                ("Generate Quote", NodeType.AUTOMATED_TASK, 10, 0.95),
                ("Send to Customer", NodeType.NOTIFICATION, 5, 0.90),
                ("Complete", NodeType.END, 5, 0.50),
            ]
        else:
            workflow = self.create_workflow("Sample Process", "Sample workflow", "general")
            steps = [("Start", NodeType.START, 5, 0.50), ("Process", NodeType.TASK, 30, 0.40), ("End", NodeType.END, 5, 0.50)]
        node_ids = []
        for i, (name, ntype, duration, potential) in enumerate(steps):
            node = WorkflowNode(
                node_id=f"NODE-{i+1}",
                name=name,
                node_type=ntype,
                description=f"Process step: {name}",
                estimated_duration_minutes=duration,
                automation_potential=potential,
            )
            self.add_node(workflow.workflow_id, node)
            node_ids.append(node.node_id)
        for i in range(len(node_ids) - 1):
            self.add_connection(workflow.workflow_id, node_ids[i], node_ids[i + 1])
        self._recalculate_automation_score(workflow.workflow_id)
        self.identify_bottlenecks(workflow.workflow_id)
        return workflow

    def get_workflow_summary(self, workflow_id: str) -> Dict:
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        workflow = self.workflows[workflow_id]
        node_summary = {nt.value: 0 for nt in NodeType}
        for node in workflow.nodes:
            node_summary[node.node_type.value] = node_summary.get(node.node_type.value, 0) + 1
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "total_nodes": len(workflow.nodes),
            "node_types": node_summary,
            "total_cycle_time_minutes": workflow.estimated_cycle_time_minutes,
            "automation_score_percent": round(workflow.automation_score, 2),
            "bottleneck_count": len(workflow.bottleneck_nodes),
            "automation_suggestions": self.suggest_automation(workflow_id),
        }

    def get_high_volume_automation_candidates(self) -> List[Dict]:
        candidates = []
        for wf in self.workflows.values():
            if wf.volume_per_month > 100 and wf.automation_score < 60:
                time_waste = wf.volume_per_month * wf.avg_processing_time_minutes * (1 - wf.automation_score / 100)
                candidates.append({
                    "workflow_id": wf.workflow_id,
                    "workflow_name": wf.name,
                    "volume_per_month": wf.volume_per_month,
                    "current_automation": f"{wf.automation_score:.1f}%",
                    "estimated_hours_saved_per_month": round(time_waste / 60, 1),
                    "priority": AutomationPriority.CRITICAL.value if time_waste > 1000 else AutomationPriority.HIGH.value,
                })
        return sorted(candidates, key=lambda x: x["estimated_hours_saved_per_month"], reverse=True)
