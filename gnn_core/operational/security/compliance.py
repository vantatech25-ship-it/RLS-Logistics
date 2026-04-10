"""Security and Compliance Module
Data privacy and regulatory compliance management
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class ComplianceFramework(Enum):
    GDPR = "gdpr"
    POPIA = "popia"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"


class DataCategory(Enum):
    PII = "pii"
    SENSITIVE_PII = "sensitive_pii"
    FINANCIAL = "financial"
    HEALTH = "health"
    BUSINESS = "business"
    PUBLIC = "public"


class DataSubjectRights(Enum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICTION = "restriction"
    PORTABILITY = "portability"
    OBJECTION = "objection"


class ViolationSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class AuditStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DataMapping:
    field_name: str
    data_category: DataCategory
    is_personal_data: bool
    retention_period_days: int
    legal_basis: str
    third_party_sharing: List[str] = field(default_factory=list)


@dataclass
class PrivacyPolicy:
    policy_id: str
    name: str
    framework: ComplianceFramework
    effective_date: datetime
    review_date: datetime
    requirements: List[str]
    controls: List[str]


@dataclass
class ComplianceViolation:
    violation_id: str
    framework: ComplianceFramework
    severity: ViolationSeverity
    description: str
    detected_at: datetime
    remediated_at: Optional[datetime]
    status: str
    affected_records: int
    remediation_steps: List[str]


@dataclass
class DataSubjectRequest:
    request_id: str
    requester_id: str
    request_type: DataSubjectRights
    status: str
    submitted_at: datetime
    completed_at: Optional[datetime]
    data_retrieved: Optional[Dict]
    verification_status: str


@dataclass
class AuditLog:
    log_id: str
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str
    ip_address: Optional[str]
    metadata: Dict


@dataclass
class ConsentRecord:
    consent_id: str
    user_id: str
    consent_type: str
    granted: bool
    granted_at: datetime
    withdrawn_at: Optional[datetime]
    version: str


class ComplianceManager:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.data_mappings: Dict[str, List[DataMapping]] = {}
        self.policies: Dict[str, PrivacyPolicy] = {}
        self.violations: Dict[str, ComplianceViolation] = {}
        self.data_subject_requests: Dict[str, DataSubjectRequest] = {}
        self.audit_logs: List[AuditLog] = []
        self.consent_records: Dict[str, List[ConsentRecord]] = {}
        self.retention_policies: Dict[str, int] = {}
        self._load_default_policies()
        self.notification_callbacks: List[Callable] = []

    def _default_config(self) -> Dict:
        return {
            "retention_default_days": 2555,
            "pii_retention_days": 365,
            "financial_retention_days": 2555,
            "consent_refresh_days": 365,
            "audit_log_retention_days": 730,
            "require_consent_for_pii": True,
            "auto_anonymize_after_days": 3650,
        }

    def _load_default_policies(self):
        policies = [
            PrivacyPolicy("POL-GDPR-001", "GDPR Data Protection Policy", ComplianceFramework.GDPR, datetime(2024, 1, 1), datetime(2025, 1, 1), ["Lawful basis required", "Data minimization", "Right to erasure", "Breach notification 72h"], ["Encryption at rest", "Access controls", "Pseudonymization"]),
            PrivacyPolicy("POL-POPIA-001", "POPIA Compliance Policy", ComplianceFramework.POPIA, datetime(2024, 1, 1), datetime(2025, 1, 1), ["Responsible party designation", "Purpose specification", "Information quality", "Openness principle"], ["Security safeguards", "Documentation", "Consent management"]),
            PrivacyPolicy("POL-SOC2-001", "SOC 2 Trust Services Policy", ComplianceFramework.SOC2, datetime(2024, 1, 1), datetime(2025, 1, 1), ["Security controls", "Availability monitoring", "Processing integrity", "Confidentiality", "Privacy"], ["Access management", "Monitoring", "Incident response"]),
        ]
        for policy in policies:
            self.policies[policy.policy_id] = policy

    def register_notification_callback(self, callback: Callable):
        self.notification_callbacks.append(callback)

    def _notify(self, event_type: str, data: Dict):
        for callback in self.notification_callbacks:
            try:
                callback(event_type, data)
            except Exception:
                pass

    def register_data_mapping(self, system_id: str, mappings: List[DataMapping]) -> bool:
        self.data_mappings[system_id] = mappings
        for mapping in mappings:
            if mapping.data_category in [DataCategory.PII, DataCategory.SENSITIVE_PII]:
                self.retention_policies[mapping.field_name] = self.config["pii_retention_days"]
            elif mapping.data_category == DataCategory.FINANCIAL:
                self.retention_policies[mapping.field_name] = self.config["financial_retention_days"]
        return True

    def anonymize_data(self, data: Dict, fields_to_anonymize: List[str]) -> Dict:
        anonymized = data.copy()
        for field in fields_to_anonymize:
            if field in anonymized:
                if isinstance(anonymized[field], str):
                    anonymized[field] = hashlib.sha256(anonymized[field].encode()).hexdigest()[:16] + "***"
                elif isinstance(anonymized[field], (int, float)):
                    anonymized[field] = None
                else:
                    anonymized[field] = "[REDACTED]"
        return anonymized

    def pseudonymize_data(self, data: Dict, fields_to_pseudonymize: List[str], salt: str = "") -> Dict:
        pseudonymized = data.copy()
        for field in fields_to_pseudonymize:
            if field in pseudonymized and pseudonymized[field]:
                value = str(pseudonymized[field])
                hash_input = f"{value}{salt}{field}"
                pseudonymized[field] = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return pseudonymized

    def check_consent(self, user_id: str, consent_type: str) -> bool:
        if user_id not in self.consent_records:
            return not self.config["require_consent_for_pii"]
        records = self.consent_records[user_id]
        valid_records = [r for r in records if r.consent_type == consent_type and r.granted and (r.withdrawn_at is None or r.withdrawn_at > datetime.now())]
        return len(valid_records) > 0

    def record_consent(self, user_id: str, consent_type: str, granted: bool, version: str = "1.0") -> ConsentRecord:
        if user_id not in self.consent_records:
            self.consent_records[user_id] = []
        record = ConsentRecord(
            consent_id=f"CONS-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=datetime.now(),
            withdrawn_at=None if granted else datetime.now(),
            version=version,
        )
        self.consent_records[user_id].append(record)
        return record

    def withdraw_consent(self, user_id: str, consent_type: str) -> bool:
        if user_id not in self.consent_records:
            return False
        for record in self.consent_records[user_id]:
            if record.consent_type == consent_type and record.granted and record.withdrawn_at is None:
                record.withdrawn_at = datetime.now()
                return True
        return False

    def create_data_subject_request(self, requester_id: str, request_type: DataSubjectRights) -> DataSubjectRequest:
        request = DataSubjectRequest(
            request_id=f"DSR-{uuid.uuid4().hex[:8].upper()}",
            requester_id=requester_id,
            request_type=request_type,
            status="pending_verification",
            submitted_at=datetime.now(),
            completed_at=None,
            data_retrieved=None,
            verification_status="pending",
        )
        self.data_subject_requests[request.request_id] = request
        self._log_audit(request.requester_id, "dsr_submitted", "data_subject_request", request.request_id, "success", None, {"request_type": request_type.value})
        return request

    def process_dsr(self, request_id: str, verification_status: str, retrieved_data: Optional[Dict] = None) -> bool:
        if request_id not in self.data_subject_requests:
            return False
        request = self.data_subject_requests[request_id]
        request.verification_status = verification_status
        if verification_status == "verified":
            request.status = "processing"
        self.data_subject_requests[request_id] = request
        return True

    def complete_dsr(self, request_id: str, retrieved_data: Dict) -> bool:
        if request_id not in self.data_subject_requests:
            return False
        request = self.data_subject_requests[request_id]
        request.status = "completed"
        request.completed_at = datetime.now()
        request.data_retrieved = retrieved_data
        self._log_audit(request.requester_id, "dsr_completed", "data_subject_request", request_id, "success", None, {"request_type": request.request_type.value})
        return True

    def check_data_breach(self, affected_users: int, data_types: List[DataCategory], framework: ComplianceFramework) -> Dict:
        breach_check = {
            "requires_notification": False,
            "notification_deadline": None,
            "severity": ViolationSeverity.MINOR,
            "regulatory_notification_required": False,
        }
        has_sensitive = DataCategory.SENSITIVE_PII in data_types or DataCategory.HEALTH in data_types
        if affected_users > 100 or has_sensitive:
            breach_check["requires_notification"] = True
            breach_check["notification_deadline"] = datetime.now() + timedelta(hours=72)
            breach_check["severity"] = ViolationSeverity.CRITICAL if affected_users > 1000 or has_sensitive else ViolationSeverity.MAJOR
            breach_check["regulatory_notification_required"] = True
        elif affected_users > 10:
            breach_check["requires_notification"] = True
            breach_check["notification_deadline"] = datetime.now() + timedelta(days=3)
            breach_check["severity"] = ViolationSeverity.MODERATE
        return breach_check

    def report_violation(self, framework: ComplianceFramework, severity: ViolationSeverity, description: str, affected_records: int) -> ComplianceViolation:
        violation = ComplianceViolation(
            violation_id=f"VIOL-{uuid.uuid4().hex[:8].upper()}",
            framework=framework,
            severity=severity,
            description=description,
            detected_at=datetime.now(),
            remediated_at=None,
            status="open",
            affected_records=affected_records,
            remediation_steps=[],
        )
        self.violations[violation.violation_id] = violation
        self._log_audit("system", "violation_detected", "compliance_violation", violation.violation_id, "alert", None, {"framework": framework.value, "severity": severity.value})
        return violation

    def remediate_violation(self, violation_id: str, remediation_steps: List[str]) -> bool:
        if violation_id not in self.violations:
            return False
        violation = self.violations[violation_id]
        violation.status = "remediated"
        violation.remediated_at = datetime.now()
        violation.remediation_steps = remediation_steps
        self._log_audit("system", "violation_remediated", "compliance_violation", violation_id, "success", None, {"steps": remediation_steps})
        return True

    def _log_audit(self, user_id: str, action: str, resource_type: str, resource_id: str, outcome: str, ip_address: Optional[str], metadata: Optional[Dict] = None):
        log = AuditLog(
            log_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            ip_address=ip_address,
            metadata=metadata or {},
        )
        self.audit_logs.append(log)
        if len(self.audit_logs) > 100000:
            self.audit_logs = self.audit_logs[-50000:]

    def query_audit_logs(self, filters: Optional[Dict] = None, limit: int = 100) -> List[AuditLog]:
        results = self.audit_logs
        if filters:
            if "user_id" in filters:
                results = [r for r in results if r.user_id == filters["user_id"]]
            if "action" in filters:
                results = [r for r in results if r.action == filters["action"]]
            if "resource_type" in filters:
                results = [r for r in results if r.resource_type == filters["resource_type"]]
            if "start_date" in filters:
                results = [r for r in results if r.timestamp >= filters["start_date"]]
            if "end_date" in filters:
                results = [r for r in results if r.timestamp <= filters["end_date"]]
        return sorted(results, key=lambda x: x.timestamp, reverse=True)[:limit]

    def generate_compliance_report(self, framework: ComplianceFramework) -> Dict:
        framework_violations = [v for v in self.violations.values() if v.framework == framework]
        framework_policies = [p for p in self.policies.values() if p.framework == framework]
        open_violations = [v for v in framework_violations if v.status == "open"]
        remediated = [v for v in framework_violations if v.status == "remediated"]
        total_requests = len(self.data_subject_requests)
        completed_requests = len([r for r in self.data_subject_requests.values() if r.status == "completed"])
        pending_requests = len([r for r in self.data_subject_requests.values() if r.status in ["pending_verification", "processing"]])
        return {
            "framework": framework.value.upper(),
            "policy_name": framework_policies[0].name if framework_policies else "N/A",
            "report_date": datetime.now().isoformat(),
            "violations": {
                "total": len(framework_violations),
                "open": len(open_violations),
                "remediated": len(remediated),
                "critical_open": len([v for v in open_violations if v.severity == ViolationSeverity.CRITICAL]),
            },
            "data_subject_requests": {
                "total": total_requests,
                "completed": completed_requests,
                "pending": pending_requests,
                "completion_rate": f"{(completed_requests / total_requests * 100) if total_requests > 0 else 0:.1f}%",
            },
            "audit_logs_count": len(self.audit_logs),
            "consent_records": {
                "total_users": len(self.consent_records),
                "total_consents": sum(len(r) for r in self.consent_records.values()),
            },
            "controls_status": self._assess_controls(framework),
        }

    def _assess_controls(self, framework: ComplianceFramework) -> Dict:
        return {
            "access_controls": "implemented",
            "encryption": "implemented",
            "monitoring": "implemented",
            "incident_response": "implemented",
            "training": "in_progress",
            "documentation": "implemented",
        }

    def check_retention_compliance(self, data_age_days: int, data_category: DataCategory) -> Dict:
        retention_days = self.retention_policies.get(data_category.value, self.config["retention_default_days"])
        days_until_expiry = retention_days - data_age_days
        return {
            "compliant": days_until_expiry >= 0,
            "current_retention_days": data_age_days,
            "max_retention_days": retention_days,
            "days_until_expiry": days_until_expiry if days_until_expiry >= 0 else 0,
            "action_required": "delete" if days_until_expiry < 0 else ("review" if days_until_expiry < 30 else "none"),
        }

    def get_privacy_impact_assessment(self, processing_description: str, data_categories: List[DataCategory], users_affected: int) -> Dict:
        risk_score = 0
        risk_factors = []
        if DataCategory.SENSITIVE_PII in data_categories or DataCategory.HEALTH in data_categories:
            risk_score += 30
            risk_factors.append("Processing sensitive personal data")
        if users_affected > 1000:
            risk_score += 20
            risk_factors.append("Large scale processing")
        if DataCategory.PII in data_categories:
            risk_score += 10
            risk_factors.append("Processing personal data")
        risk_level = "high" if risk_score >= 40 else "medium" if risk_score >= 20 else "low"
        return {
            "processing_description": processing_description,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "requires_dpia": risk_level in ["high", "medium"] or users_affected > 5000,
            "recommendations": ["Conduct DPIA if processing is high risk", "Implement privacy by design", "Establish data minimization controls"] if risk_level in ["high", "medium"] else ["Continue monitoring"],
        }
