"""Intelligent Exception Handling Module
AI-powered anomaly detection and automated escalation
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class ExceptionSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    BLOCKING = "blocking"


class ExceptionCategory(Enum):
    PRICING_ERROR = "pricing_error"
    SHIPPING_DELAY = "shipping_delay"
    INVENTORY_ISSUE = "inventory_issue"
    DOCUMENT_ERROR = "document_error"
    SYSTEM_ERROR = "system_error"
    COMPLIANCE_VIOLATION = "compliance_violation"
    CUSTOMER_COMPLAINT = "customer_complaint"
    DATA_QUALITY = "data_quality"


class EscalationLevel(Enum):
    AUTOMATED = "automated"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    MANAGEMENT = "management"
    EXECUTIVE = "executive"


class ResolutionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


@dataclass
class ExceptionRule:
    rule_id: str
    name: str
    category: ExceptionCategory
    conditions: Dict
    severity: ExceptionSeverity
    escalation_level: EscalationLevel
    auto_resolve: bool
    notify_customer: bool
    enabled: bool = True


@dataclass
class Exception:
    exception_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    title: str
    description: str
    source_system: str
    source_id: str
    detected_at: datetime
    status: ResolutionStatus
    assigned_to: Optional[str]
    escalated_to: Optional[EscalationLevel]
    resolution_notes: List[str]
    customer_notification_sent: bool
    metadata: Dict = field(default_factory=dict)


@dataclass
class AnomalyDetection:
    detection_id: str
    exception_id: str
    anomaly_type: str
    baseline_value: float
    actual_value: float
    deviation_percentage: float
    confidence: float
    detected_at: datetime


@dataclass
class EscalationPath:
    escalation_id: str
    exception_id: str
    current_level: EscalationLevel
    escalation_history: List[Dict]
    sla_deadline: datetime
    sla_breached: bool = False


class IntelligentExceptionHandler:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.exceptions: Dict[str, Exception] = {}
        self.rules: Dict[str, ExceptionRule] = {}
        self.anomalies: Dict[str, AnomalyDetection] = {}
        self.escalation_paths: Dict[str, EscalationPath] = {}
        self.notification_callbacks: List[Callable] = []
        self.baselines: Dict[str, Dict] = {}
        self._load_default_rules()

    def _default_config(self) -> Dict:
        return {
            "auto_escalate_after_minutes": 30,
            "max_auto_resolution_attempts": 3,
            "anomaly_threshold_std_devs": 3.0,
            "sla_response_minutes": {
                ExceptionSeverity.CRITICAL: 15,
                ExceptionSeverity.HIGH: 60,
                ExceptionSeverity.MEDIUM: 240,
                ExceptionSeverity.LOW: 1440,
            },
            "customer_notification_required": [ExceptionSeverity.CRITICAL, ExceptionSeverity.HIGH],
        }

    def _load_default_rules(self):
        default_rules = [
            ExceptionRule("R001", "Pricing Anomaly", ExceptionCategory.PRICING_ERROR, {"deviation_percent": 20}, ExceptionSeverity.HIGH, EscalationLevel.AGENT, False, True),
            ExceptionRule("R002", "Shipping Delay > 48h", ExceptionCategory.SHIPPING_DELAY, {"delay_hours": 48}, ExceptionSeverity.MEDIUM, EscalationLevel.AGENT, False, True),
            ExceptionRule("R003", "Critical Shipping Delay", ExceptionCategory.SHIPPING_DELAY, {"delay_hours": 72}, ExceptionSeverity.CRITICAL, EscalationLevel.SUPERVISOR, False, True),
            ExceptionRule("R004", "Stockout Risk", ExceptionCategory.INVENTORY_ISSUE, {"stock_level_percent": 10}, ExceptionSeverity.HIGH, EscalationLevel.AGENT, False, True),
            ExceptionRule("R005", "Document Validation Failure", ExceptionCategory.DOCUMENT_ERROR, {"confidence_below": 0.6}, ExceptionSeverity.MEDIUM, EscalationLevel.AGENT, True, False),
            ExceptionRule("R006", "Compliance Violation", ExceptionCategory.COMPLIANCE_VIOLATION, {"rule_violated": True}, ExceptionSeverity.CRITICAL, EscalationLevel.MANAGEMENT, False, True),
            ExceptionRule("R007", "System Timeout", ExceptionCategory.SYSTEM_ERROR, {"timeout_seconds": 30}, ExceptionSeverity.LOW, EscalationLevel.AUTOMATED, True, False),
            ExceptionRule("R008", "Data Quality Alert", ExceptionCategory.DATA_QUALITY, {"missing_fields": 3}, ExceptionSeverity.MEDIUM, EscalationLevel.AUTOMATED, True, False),
        ]
        for rule in default_rules:
            self.rules[rule.rule_id] = rule

    def register_notification_callback(self, callback: Callable):
        self.notification_callbacks.append(callback)

    def _notify(self, exception: Exception, message: str):
        for callback in self.notification_callbacks:
            try:
                callback(exception, message)
            except Exception:
                pass

    def detect_anomaly(self, metric_name: str, value: float, context: Optional[Dict] = None) -> Optional[AnomalyDetection]:
        if metric_name not in self.baselines:
            self.baselines[metric_name] = {"values": [], "mean": 0, "std": 0}
        baseline = self.baselines[metric_name]
        baseline["values"].append(value)
        if len(baseline["values"]) > 100:
            baseline["values"] = baseline["values"][-100:]
        import statistics
        if len(baseline["values"]) >= 10:
            baseline["mean"] = statistics.mean(baseline["values"])
            baseline["std"] = statistics.stdev(baseline["values"])
        if baseline["std"] > 0:
            z_score = abs(value - baseline["mean"]) / baseline["std"]
            threshold = self.config["anomaly_threshold_std_devs"]
            if z_score > threshold:
                detection_id = f"ANOM-{uuid.uuid4().hex[:8].upper()}"
                deviation = ((value - baseline["mean"]) / baseline["mean"] * 100) if baseline["mean"] != 0 else 0
                detection = AnomalyDetection(
                    detection_id=detection_id,
                    exception_id="",
                    anomaly_type=f"{metric_name}_anomaly",
                    baseline_value=baseline["mean"],
                    actual_value=value,
                    deviation_percentage=deviation,
                    confidence=min(0.99, z_score / 5),
                    detected_at=datetime.now(),
                )
                self.anomalies[detection_id] = detection
                return detection
        return None

    def check_rules(self, data: Dict) -> List[ExceptionRule]:
        triggered = []
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            conditions_met = True
            for key, expected in rule.conditions.items():
                if key not in data:
                    conditions_met = False
                    break
                actual = data[key]
                if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                    if key == "deviation_percent" and "reference_value" in data:
                        deviation = abs(actual - data["reference_value"]) / data["reference_value"] * 100
                        if deviation < expected:
                            conditions_met = False
                    elif actual < expected:
                        conditions_met = False
                elif actual != expected:
                    conditions_met = False
            if conditions_met:
                triggered.append(rule)
        return triggered

    def create_exception(self, category: ExceptionCategory, severity: ExceptionSeverity, title: str, description: str, source_system: str, source_id: str, metadata: Optional[Dict] = None) -> Exception:
        exception_id = f"EXC-{uuid.uuid4().hex[:8].upper()}"
        exception = Exception(
            exception_id=exception_id,
            category=category,
            severity=severity,
            title=title,
            description=description,
            source_system=source_system,
            source_id=source_id,
            detected_at=datetime.now(),
            status=ResolutionStatus.PENDING,
            assigned_to=None,
            escalated_to=None,
            resolution_notes=[],
            customer_notification_sent=False,
            metadata=metadata or {},
        )
        self.exceptions[exception_id] = exception
        self._create_escalation_path(exception_id)
        self._notify(exception, f"New exception created: {title}")
        return exception

    def process_exception_data(self, data: Dict, source_system: str, source_id: str) -> List[Exception]:
        created_exceptions = []
        triggered_rules = self.check_rules(data)
        for rule in triggered_rules:
            exception = self.create_exception(
                category=rule.category,
                severity=rule.severity,
                title=f"Exception: {rule.name}",
                description=f"Rule {rule.name} triggered with conditions: {rule.conditions}",
                source_system=source_system,
                source_id=source_id,
                metadata={"rule_id": rule.rule_id},
            )
            if rule.auto_resolve:
                exception.status = ResolutionStatus.RESOLVED
                exception.resolution_notes.append(f"Auto-resolved by rule: {rule.name}")
            if rule.notify_customer:
                self._mark_customer_notification(exception)
            created_exceptions.append(exception)
        anomaly = self.detect_anomaly(data.get("metric_name", "unknown"), data.get("value", 0), data)
        if anomaly:
            exception = self.create_exception(
                category=ExceptionCategory.DATA_QUALITY,
                severity=ExceptionSeverity.MEDIUM,
                title=f"Anomaly Detected: {anomaly.anomaly_type}",
                description=f"Value {anomaly.actual_value:.2f} deviates {anomaly.deviation_percentage:.1f}% from baseline",
                source_system=source_system,
                source_id=source_id,
                metadata={"detection_id": anomaly.detection_id},
            )
            anomaly.exception_id = exception.exception_id
            created_exceptions.append(exception)
        return created_exceptions

    def _create_escalation_path(self, exception_id: str) -> EscalationPath:
        if exception_id not in self.exceptions:
            return None
        exception = self.exceptions[exception_id]
        sla_minutes = self.config["sla_response_minutes"].get(exception.severity, 1440)
        path = EscalationPath(
            escalation_id=f"ESC-{uuid.uuid4().hex[:8].upper()}",
            exception_id=exception_id,
            current_level=exception.escalated_to or EscalationLevel.AUTOMATED,
            escalation_history=[{"level": EscalationLevel.AUTOMATED.value, "timestamp": datetime.now().isoformat()}],
            sla_deadline=datetime.now() + timedelta(minutes=sla_minutes),
        )
        self.escalation_paths[exception_id] = path
        return path

    def escalate_exception(self, exception_id: str, target_level: EscalationLevel, reason: str) -> bool:
        if exception_id not in self.exceptions:
            return False
        exception = self.exceptions[exception_id]
        exception.status = ResolutionStatus.ESCALATED
        exception.escalated_to = target_level
        exception.resolution_notes.append(f"Escalated to {target_level.value}: {reason}")
        if exception_id in self.escalation_paths:
            path = self.escalation_paths[exception_id]
            path.current_level = target_level
            path.escalation_history.append({"level": target_level.value, "timestamp": datetime.now().isoformat(), "reason": reason})
        self._notify(exception, f"Exception escalated to {target_level.value}")
        return True

    def _mark_customer_notification(self, exception: Exception):
        exception.customer_notification_sent = True
        exception.resolution_notes.append("Customer notification sent")

    def assign_exception(self, exception_id: str, assignee: str) -> bool:
        if exception_id not in self.exceptions:
            return False
        self.exceptions[exception_id].assigned_to = assignee
        self.exceptions[exception_id].status = ResolutionStatus.IN_PROGRESS
        return True

    def resolve_exception(self, exception_id: str, resolution: str) -> bool:
        if exception_id not in self.exceptions:
            return False
        exception = self.exceptions[exception_id]
        exception.status = ResolutionStatus.RESOLVED
        exception.resolution_notes.append(f"Resolved: {resolution}")
        self._notify(exception, f"Exception resolved: {resolution}")
        return True

    def get_exceptions_by_severity(self, severity: ExceptionSeverity) -> List[Exception]:
        return [e for e in self.exceptions.values() if e.severity == severity and e.status not in [ResolutionStatus.CLOSED, ResolutionStatus.RESOLVED]]

    def get_exceptions_by_status(self, status: ResolutionStatus) -> List[Exception]:
        return [e for e in self.exceptions.values() if e.status == status]

    def get_overdue_exceptions(self) -> List[Dict]:
        overdue = []
        now = datetime.now()
        for exc_id, path in self.escalation_paths.items():
            if path.sla_deadline < now and self.exceptions[exc_id].status not in [ResolutionStatus.RESOLVED, ResolutionStatus.CLOSED]:
                exc = self.exceptions[exc_id]
                overdue.append({
                    "exception_id": exc_id,
                    "title": exc.title,
                    "severity": exc.severity.value,
                    "status": exc.status.value,
                    "overdue_minutes": int((now - path.sla_deadline).total_seconds() / 60),
                    "assigned_to": exc.assigned_to or "Unassigned",
                    "category": exc.category.value,
                })
        return sorted(overdue, key=lambda x: x["overdue_minutes"], reverse=True)

    def get_exception_summary(self) -> Dict:
        total = len(self.exceptions)
        by_status = {s.value: 0 for s in ResolutionStatus}
        by_severity = {s.value: 0 for s in ExceptionSeverity}
        by_category = {c.value: 0 for c in ExceptionCategory}
        open_count = 0
        for exc in self.exceptions.values():
            by_status[exc.status.value] += 1
            by_severity[exc.severity.value] += 1
            by_category[exc.category.value] += 1
            if exc.status in [ResolutionStatus.PENDING, ResolutionStatus.IN_PROGRESS, ResolutionStatus.ESCALATED]:
                open_count += 1
        resolution_rate = ((by_status.get(ResolutionStatus.RESOLVED.value, 0) + by_status.get(ResolutionStatus.CLOSED.value, 0)) / total * 100) if total > 0 else 0
        return {
            "total_exceptions": total,
            "open_exceptions": open_count,
            "resolution_rate_percent": round(resolution_rate, 1),
            "by_status": by_status,
            "by_severity": by_severity,
            "by_category": by_category,
            "overdue_count": len(self.get_overdue_exceptions()),
        }
