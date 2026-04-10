"""Human-in-the-Loop (HITL) Module
Checkpoints for human review on complex cases
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class ReviewStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class ReviewPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ReviewCategory(Enum):
    PRICING_APPROVAL = "pricing_approval"
    CREDIT_CHECK = "credit_check"
    COMPLIANCE_REVIEW = "compliance_review"
    CUSTOMER_DISPUTE = "customer_dispute"
    EXCEPTION_APPROVAL = "exception_approval"
    NEW_VENDOR = "new_vendor"
    CONTRACT_REVIEW = "contract_review"
    CUSTOM = "custom"


@dataclass
class ReviewCheckpoint:
    checkpoint_id: str
    category: ReviewCategory
    title: str
    description: str
    context_data: Dict
    priority: ReviewPriority
    status: ReviewStatus
    requested_by: str
    assigned_to: Optional[str]
    created_at: datetime
    deadline: datetime
    completed_at: Optional[datetime]
    reviewer_notes: List[str]
    decision: Optional[str]
    attachments: List[str] = field(default_factory=list)


@dataclass
class ReviewTemplate:
    template_id: str
    name: str
    category: ReviewCategory
    description: str
    priority: ReviewPriority
    default_deadline_hours: int
    required_fields: List[str]
    escalation_rules: Dict


@dataclass
class HITLRule:
    rule_id: str
    name: str
    description: str
    trigger_conditions: Dict
    category: ReviewCategory
    priority: ReviewPriority
    deadline_hours: int
    auto_escalate: bool
    enabled: bool = True


class HumanInTheLoop:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.checkpoints: Dict[str, ReviewCheckpoint] = {}
        self.templates: Dict[str, ReviewTemplate] = {}
        self.rules: Dict[str, HITLRule] = {}
        self.reviewers: Dict[str, Dict] = {}
        self.notification_callbacks: List[Callable] = []
        self._load_default_templates()
        self._load_default_rules()
        self._load_default_reviewers()

    def _default_config(self) -> Dict:
        return {
            "default_deadline_hours": 24,
            "urgent_deadline_hours": 4,
            "high_priority_deadline_hours": 8,
            "auto_expire_after_hours": 168,
            "reminder_interval_hours": 8,
            "escalation_threshold_hours": 4,
        }

    def _load_default_templates(self):
        templates = [
            ReviewTemplate("TMPL001", "Standard Pricing Approval", ReviewCategory.PRICING_APPROVAL, "Approve non-standard pricing or discounts", ReviewPriority.NORMAL, 24, ["customer_id", "requested_price", "standard_price"], {}),
            ReviewTemplate("TMPL002", "Credit Check Review", ReviewCategory.CREDIT_CHECK, "Review credit limits for new or risky customers", ReviewPriority.HIGH, 8, ["customer_id", "credit_request", "payment_history"], {}),
            ReviewTemplate("TMPL003", "Compliance Exception", ReviewCategory.COMPLIANCE_REVIEW, "Review compliance exceptions or violations", ReviewPriority.HIGH, 8, ["violation_type", "severity", "remediation_plan"], {}),
            ReviewTemplate("TMPL004", "Customer Dispute", ReviewCategory.CUSTOMER_DISPUTE, "Review customer complaints and disputes", ReviewPriority.NORMAL, 24, ["customer_id", "dispute_amount", "issue_description"], {}),
            ReviewTemplate("TMPL005", "Exception Approval", ReviewCategory.EXCEPTION_APPROVAL, "Approve operational exceptions", ReviewPriority.HIGH, 12, ["exception_type", "exception_data"], {}),
            ReviewTemplate("TMPL006", "New Vendor Onboarding", ReviewCategory.NEW_VENDOR, "Approve new vendor relationships", ReviewPriority.NORMAL, 48, ["vendor_name", "vendor_details", "risk_assessment"], {}),
        ]
        for tmpl in templates:
            self.templates[tmpl.template_id] = tmpl

    def _load_default_rules(self):
        rules = [
            HITLRule("HITL001", "High Value Transaction", "Route transactions over $50,000 for review", {"amount_greater_than": 50000}, ReviewCategory.PRICING_APPROVAL, ReviewPriority.HIGH, 4, True),
            HITLRule("HITL002", "New Customer Large Order", "Review orders from new customers over $10,000", {"is_new_customer": True, "order_amount_greater_than": 10000}, ReviewCategory.CREDIT_CHECK, ReviewPriority.HIGH, 8, True),
            HITLRule("HITL003", "Compliance Violation", "Any compliance violation requires review", {"violation_detected": True}, ReviewCategory.COMPLIANCE_REVIEW, ReviewPriority.URGENT, 4, True),
            HITLRule("HITL004", "Pricing Exception", "Non-standard pricing requires approval", {"has_pricing_exception": True, "discount_over_percent": 15}, ReviewCategory.PRICING_APPROVAL, ReviewPriority.NORMAL, 24, False),
            HITLRule("HITL005", "Customer Complaint", "Route customer complaints to support manager", {"complaint_severity": "high"}, ReviewCategory.CUSTOMER_DISPUTE, ReviewPriority.HIGH, 12, False),
        ]
        for rule in rules:
            self.rules[rule.rule_id] = rule

    def _load_default_reviewers(self):
        self.reviewers = {
            "R001": {"name": "Alice Manager", "role": "Operations Manager", "specializations": [ReviewCategory.EXCEPTION_APPROVAL, ReviewCategory.COMPLIANCE_REVIEW], "workload": 0, "max_workload": 20},
            "R002": {"name": "Bob Finance", "role": "Finance Director", "specializations": [ReviewCategory.PRICING_APPROVAL, ReviewCategory.CREDIT_CHECK], "workload": 0, "max_workload": 15},
            "R003": {"name": "Carol Legal", "role": "Legal Counsel", "specializations": [ReviewCategory.COMPLIANCE_REVIEW, ReviewCategory.CONTRACT_REVIEW], "workload": 0, "max_workload": 10},
            "R004": {"name": "Dave Support", "role": "Support Manager", "specializations": [ReviewCategory.CUSTOMER_DISPUTE], "workload": 0, "max_workload": 25},
        }

    def register_notification_callback(self, callback: Callable):
        self.notification_callbacks.append(callback)

    def _notify(self, checkpoint: ReviewCheckpoint, event: str):
        for callback in self.notification_callbacks:
            try:
                callback(checkpoint, event)
            except Exception:
                pass

    def check_triggers(self, data: Dict) -> List[HITLRule]:
        triggered = []
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            conditions_met = True
            for key, expected in rule.trigger_conditions.items():
                actual = data.get(key)
                if actual is None:
                    conditions_met = False
                    break
                if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                    if key == "amount_greater_than" and actual <= expected:
                        conditions_met = False
                    elif key == "order_amount_greater_than" and actual <= expected:
                        conditions_met = False
                    elif key == "discount_over_percent" and actual <= expected:
                        conditions_met = False
                elif isinstance(expected, bool) and actual != expected:
                    conditions_met = False
                elif isinstance(expected, str) and actual != expected:
                    conditions_met = False
            if conditions_met:
                triggered.append(rule)
        return triggered

    def _assign_reviewer(self, category: ReviewCategory, priority: ReviewPriority) -> Optional[str]:
        available = {k: v for k, v in self.reviewers.items() if v["workload"] < v["max_workload"]}
        specialized = {k: v for k, v in available.items() if category in v["specializations"]}
        candidates = specialized if specialized else available
        if not candidates:
            return None
        return min(candidates.items(), key=lambda x: x[1]["workload"])[0]

    def create_checkpoint(self, category: ReviewCategory, title: str, description: str, context_data: Dict, requested_by: str, priority: Optional[ReviewPriority] = None, template_id: Optional[str] = None) -> ReviewCheckpoint:
        checkpoint_id = f"CHK-{uuid.uuid4().hex[:8].upper()}"
        deadline_hours = self.config["default_deadline_hours"]
        assigned_priority = priority or ReviewPriority.NORMAL
        if template_id and template_id in self.templates:
            tmpl = self.templates[template_id]
            assigned_priority = tmpl.priority
            deadline_hours = tmpl.default_deadline_hours
        elif assigned_priority == ReviewPriority.URGENT:
            deadline_hours = self.config["urgent_deadline_hours"]
        elif assigned_priority == ReviewPriority.HIGH:
            deadline_hours = self.config["high_priority_deadline_hours"]
        assigned_to = self._assign_reviewer(category, assigned_priority)
        if assigned_to and assigned_to in self.reviewers:
            self.reviewers[assigned_to]["workload"] += 1
        checkpoint = ReviewCheckpoint(
            checkpoint_id=checkpoint_id,
            category=category,
            title=title,
            description=description,
            context_data=context_data,
            priority=assigned_priority,
            status=ReviewStatus.PENDING,
            requested_by=requested_by,
            assigned_to=assigned_to,
            created_at=datetime.now(),
            deadline=datetime.now() + timedelta(hours=deadline_hours),
            completed_at=None,
            reviewer_notes=[],
            decision=None,
        )
        self.checkpoints[checkpoint_id] = checkpoint
        self._notify(checkpoint, "checkpoint_created")
        return checkpoint

    def evaluate_and_create_checkpoint(self, data: Dict, requested_by: str) -> List[ReviewCheckpoint]:
        created = []
        triggered_rules = self.check_triggers(data)
        for rule in triggered_rules:
            checkpoint = self.create_checkpoint(
                category=rule.category,
                title=f"Review Required: {rule.name}",
                description=rule.description,
                context_data=data,
                requested_by=requested_by,
                priority=rule.priority,
            )
            created.append(checkpoint)
        return created

    def submit_review(self, checkpoint_id: str, decision: str, reviewer_notes: Optional[str] = None, reviewer_id: Optional[str] = None) -> bool:
        if checkpoint_id not in self.checkpoints:
            return False
        checkpoint = self.checkpoints[checkpoint_id]
        if checkpoint.status == ReviewStatus.APPROVED or checkpoint.status == ReviewStatus.REJECTED:
            return False
        checkpoint.status = ReviewStatus.APPROVED if decision.lower() == "approve" else ReviewStatus.REJECTED
        checkpoint.decision = decision
        checkpoint.completed_at = datetime.now()
        if reviewer_notes:
            checkpoint.reviewer_notes.append(reviewer_notes)
        if checkpoint.assigned_to and checkpoint.assigned_to in self.reviewers:
            self.reviewers[checkpoint.assigned_to]["workload"] = max(0, self.reviewers[checkpoint.assigned_to]["workload"] - 1)
        self._notify(checkpoint, f"review_{checkpoint.status.value}")
        return True

    def escalate_checkpoint(self, checkpoint_id: str, escalation_reason: str, target_reviewer_id: Optional[str] = None) -> bool:
        if checkpoint_id not in self.checkpoints:
            return False
        checkpoint = self.checkpoints[checkpoint_id]
        checkpoint.status = ReviewStatus.ESCALATED
        checkpoint.reviewer_notes.append(f"Escalated: {escalation_reason}")
        if checkpoint.assigned_to and checkpoint.assigned_to in self.reviewers:
            self.reviewers[checkpoint.assigned_to]["workload"] = max(0, self.reviewers[checkpoint.assigned_to]["workload"] - 1)
        if target_reviewer_id and target_reviewer_id in self.reviewers:
            checkpoint.assigned_to = target_reviewer_id
            self.reviewers[target_reviewer_id]["workload"] += 1
        else:
            new_reviewer = self._assign_reviewer(checkpoint.category, checkpoint.priority)
            if new_reviewer:
                checkpoint.assigned_to = new_reviewer
                self.reviewers[new_reviewer]["workload"] += 1
        self._notify(checkpoint, "checkpoint_escalated")
        return True

    def get_pending_checkpoints(self, reviewer_id: Optional[str] = None, category: Optional[ReviewCategory] = None) -> List[ReviewCheckpoint]:
        pending = [c for c in self.checkpoints.values() if c.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]]
        if reviewer_id:
            pending = [c for c in pending if c.assigned_to == reviewer_id]
        if category:
            pending = [c for c in pending if c.category == category]
        return sorted(pending, key=lambda x: (x.priority == ReviewPriority.LOW, x.deadline))

    def get_overdue_checkpoints(self) -> List[Dict]:
        overdue = []
        now = datetime.now()
        for checkpoint in self.checkpoints.values():
            if checkpoint.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW] and checkpoint.deadline < now:
                overdue.append({
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "title": checkpoint.title,
                    "category": checkpoint.category.value,
                    "priority": checkpoint.priority.value,
                    "assigned_to": self.reviewers.get(checkpoint.assigned_to, {}).get("name", "Unassigned") if checkpoint.assigned_to else "Unassigned",
                    "overdue_hours": int((now - checkpoint.deadline).total_seconds() / 3600),
                    "status": checkpoint.status.value,
                })
        return sorted(overdue, key=lambda x: x["overdue_hours"], reverse=True)

    def get_reviewer_workload(self) -> List[Dict]:
        return [
            {
                "reviewer_id": rid,
                "name": r["name"],
                "role": r["role"],
                "current_workload": r["workload"],
                "max_workload": r["max_workload"],
                "utilization_pct": round(r["workload"] / r["max_workload"] * 100, 1) if r["max_workload"] > 0 else 0,
                "pending_reviews": len([c for c in self.checkpoints.values() if c.assigned_to == rid and c.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]]),
            }
            for rid, r in self.reviewers.items()
        ]

    def get_hitl_summary(self) -> Dict:
        total = len(self.checkpoints)
        pending = len([c for c in self.checkpoints.values() if c.status == ReviewStatus.PENDING])
        in_review = len([c for c in self.checkpoints.values() if c.status == ReviewStatus.IN_REVIEW])
        approved = len([c for c in self.checkpoints.values() if c.status == ReviewStatus.APPROVED])
        rejected = len([c for c in self.checkpoints.values() if c.status == ReviewStatus.REJECTED])
        overdue = self.get_overdue_checkpoints()
        return {
            "total_checkpoints": total,
            "pending": pending,
            "in_review": in_review,
            "approved": approved,
            "rejected": rejected,
            "overdue_count": len(overdue),
            "approval_rate": f"{(approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 0:.1f}%",
            "avg_resolution_hours": self._calculate_avg_resolution_time(),
            "reviewer_workload": self.get_reviewer_workload(),
        }

    def _calculate_avg_resolution_time(self) -> Optional[float]:
        completed = [c for c in self.checkpoints.values() if c.completed_at]
        if not completed:
            return None
        total_seconds = sum((c.completed_at - c.created_at).total_seconds() for c in completed)
        return round(total_seconds / len(completed) / 3600, 1)
