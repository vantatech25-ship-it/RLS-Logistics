"""Customer Onboarding and Lead Management Module
Automated lead capture, routing, and onboarding sequences
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class LeadSource(Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    TRADE_SHOW = "trade_show"
    COLD_OUTREACH = "cold_outreach"
    PARTNER = "partner"
    SOCIAL_MEDIA = "social_media"
    UNKNOWN = "unknown"


class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class LeadPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OnboardingStage(Enum):
    INVITATION_SENT = "invitation_sent"
    REGISTRATION = "registration"
    VERIFICATION = "verification"
    DOCUMENTATION = "documentation"
    TRAINING = "training"
    ACTIVE = "active"


@dataclass
class Lead:
    lead_id: str
    company_name: str
    contact_name: str
    email: str
    phone: Optional[str]
    source: LeadSource
    status: LeadStatus
    priority: LeadPriority
    assigned_to: Optional[str]
    created_at: datetime
    last_contact: Optional[datetime]
    score: int
    requirements: List[str]
    metadata: Dict = field(default_factory=dict)


@dataclass
class OnboardingSequence:
    sequence_id: str
    customer_id: str
    stages: List[OnboardingStage]
    current_stage: OnboardingStage
    started_at: datetime
    estimated_completion: datetime
    completed_at: Optional[datetime]
    stage_history: List[Dict] = field(default_factory=list)


@dataclass
class CommunicationTemplate:
    template_id: str
    name: str
    subject: str
    body: str
    channel: str
    trigger: str
    delay_days: int = 0


@dataclass
class LeadAssignment:
    assignment_id: str
    lead_id: str
    assigned_to: str
    assigned_at: datetime
    reason: str
    priority_override: Optional[str] = None


class CustomerOnboarding:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.leads: Dict[str, Lead] = {}
        self.onboarding_sequences: Dict[str, OnboardingSequence] = {}
        self.assignments: Dict[str, LeadAssignment] = {}
        self.templates = self._load_templates()
        self.sales_reps = self._load_sales_reps()

    def _default_config(self) -> Dict:
        return {
            "auto_qualify_threshold": 70,
            "max_leads_per_rep": 50,
            "follow_up_interval_hours": 24,
            "onboarding_duration_days": 14,
            "critical_score_below": 30,
        }

    def _load_templates(self) -> List[CommunicationTemplate]:
        return [
            CommunicationTemplate("T1", "Welcome Email", "Welcome to RLS!", "Dear {name}, Welcome aboard...", "email", "onboarding_start", 0),
            CommunicationTemplate("T2", "Introduction Call", "Schedule Your Introduction", "Hi {name}, Let's schedule...", "email", "onboarding_day3", 3),
            CommunicationTemplate("T3", "Documentation Request", "Required Documents", "Dear {name}, Please provide...", "email", "onboarding_day5", 5),
            CommunicationTemplate("T4", "Training Invite", "Training Session Scheduled", "Hi {name}, Your training...", "email", "onboarding_day10", 10),
            CommunicationTemplate("T5", "Activation Complete", "Account Active!", "Congratulations {name}...", "email", "onboarding_complete", 14),
        ]

    def _load_sales_reps(self) -> Dict:
        return {
            "SR001": {"name": "John Smith", "territory": "North", "specialization": "enterprise", "current_load": 0, "max_load": 50},
            "SR002": {"name": "Sarah Johnson", "territory": "South", "specialization": "mid-market", "current_load": 0, "max_load": 40},
            "SR003": {"name": "Mike Chen", "territory": "West", "specialization": "startup", "current_load": 0, "max_load": 60},
            "SR004": {"name": "Emily Davis", "territory": "East", "specialization": "enterprise", "current_load": 0, "max_load": 50},
        }

    def capture_lead(self, company_name: str, contact_name: str, email: str, phone: Optional[str], source: LeadSource, requirements: List[str], metadata: Optional[Dict] = None) -> Lead:
        lead_id = f"LEAD-{uuid.uuid4().hex[:8].upper()}"
        score = self._calculate_lead_score(company_name, contact_name, source, requirements)
        priority = self._determine_priority(score, source)
        lead = Lead(
            lead_id=lead_id,
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            source=source,
            status=LeadStatus.NEW,
            priority=priority,
            assigned_to=None,
            created_at=datetime.now(),
            last_contact=None,
            score=score,
            requirements=requirements,
            metadata=metadata or {},
        )
        self.leads[lead_id] = lead
        self._auto_assign_lead(lead)
        return lead

    def _calculate_lead_score(self, company_name: str, contact_name: str, source: LeadSource, requirements: List[str]) -> int:
        score = 50
        if source == LeadSource.REFERRAL:
            score += 25
        elif source == LeadSource.WEBSITE:
            score += 15
        elif source == LeadSource.TRADE_SHOW:
            score += 20
        elif source == LeadSource.COLD_OUTREACH:
            score -= 10
        if len(requirements) >= 3:
            score += 15
        elif len(requirements) == 0:
            score -= 10
        if len(company_name) > 5:
            score += 10
        return max(0, min(100, score))

    def _determine_priority(self, score: int, source: LeadSource) -> LeadPriority:
        if score >= 80 or source == LeadSource.REFERRAL:
            return LeadPriority.CRITICAL
        elif score >= 60:
            return LeadPriority.HIGH
        elif score >= 40:
            return LeadPriority.MEDIUM
        return LeadPriority.LOW

    def _auto_assign_lead(self, lead: Lead) -> Optional[str]:
        available_reps = {k: v for k, v in self.sales_reps.items() if v["current_load"] < v["max_load"]}
        if not available_reps:
            return None
        if lead.priority == LeadPriority.CRITICAL:
            best_rep = min(available_reps.items(), key=lambda x: x[1]["current_load"])
        else:
            best_rep = min(available_reps.items(), key=lambda x: x[1]["current_load"])
        rep_id = best_rep[0]
        self.sales_reps[rep_id]["current_load"] += 1
        lead.assigned_to = rep_id
        assignment = LeadAssignment(
            assignment_id=f"ASN-{uuid.uuid4().hex[:8].upper()}",
            lead_id=lead.lead_id,
            assigned_to=rep_id,
            assigned_at=datetime.now(),
            reason=f"Auto-assigned based on priority and workload",
            priority_override=lead.priority.value,
        )
        self.assignments[lead.lead_id] = assignment
        return rep_id

    def route_lead(self, lead_id: str, target_rep_id: Optional[str] = None) -> bool:
        if lead_id not in self.leads:
            return False
        lead = self.leads[lead_id]
        if target_rep_id and target_rep_id in self.sales_reps:
            if self.sales_reps[target_rep_id]["current_load"] >= self.sales_reps[target_rep_id]["max_load"]:
                return False
            if lead.assigned_to and lead.assigned_to in self.sales_reps:
                self.sales_reps[lead.assigned_to]["current_load"] -= 1
            self.sales_reps[target_rep_id]["current_load"] += 1
            lead.assigned_to = target_rep_id
        return True

    def update_lead_status(self, lead_id: str, new_status: LeadStatus) -> bool:
        if lead_id not in self.leads:
            return False
        self.leads[lead_id].status = new_status
        self.leads[lead_id].last_contact = datetime.now()
        return True

    def start_onboarding(self, lead_id: str) -> OnboardingSequence:
        if lead_id not in self.leads:
            raise ValueError("Lead not found")
        lead = self.leads[lead_id]
        sequence_id = f"OB-{uuid.uuid4().hex[:8].upper()}"
        stages = list(OnboardingStage)
        sequence = OnboardingSequence(
            sequence_id=sequence_id,
            customer_id=lead_id,
            stages=stages,
            current_stage=OnboardingStage.INVITATION_SENT,
            started_at=datetime.now(),
            estimated_completion=datetime.now() + timedelta(days=self.config["onboarding_duration_days"]),
            completed_at=None,
            stage_history=[{"stage": OnboardingStage.INVITATION_SENT.value, "timestamp": datetime.now().isoformat()}],
        )
        self.onboarding_sequences[sequence_id] = sequence
        self.update_lead_status(lead_id, LeadStatus.WON)
        return sequence

    def advance_onboarding_stage(self, sequence_id: str) -> bool:
        if sequence_id not in self.onboarding_sequences:
            return False
        sequence = self.onboarding_sequences[sequence_id]
        current_idx = sequence.stages.index(sequence.current_stage)
        if current_idx < len(sequence.stages) - 1:
            sequence.current_stage = sequence.stages[current_idx + 1]
            sequence.stage_history.append({"stage": sequence.current_stage.value, "timestamp": datetime.now().isoformat()})
            if sequence.current_stage == OnboardingStage.ACTIVE:
                sequence.completed_at = datetime.now()
            return True
        return False

    def get_next_communication(self, sequence_id: str) -> Optional[CommunicationTemplate]:
        if sequence_id not in self.onboarding_sequences:
            return None
        sequence = self.onboarding_sequences[sequence_id]
        for template in self.templates:
            if template.trigger == f"onboarding_{sequence.current_stage.value}":
                return template
        return None

    def get_lead_summary(self, lead_id: str) -> Dict:
        if lead_id not in self.leads:
            return {"error": "Lead not found"}
        lead = self.leads[lead_id]
        rep_info = self.sales_reps.get(lead.assigned_to, {}) if lead.assigned_to else None
        return {
            "lead_id": lead.lead_id,
            "company": lead.company_name,
            "contact": lead.contact_name,
            "score": lead.score,
            "priority": lead.priority.value,
            "status": lead.status.value,
            "source": lead.source.value,
            "assigned_to": rep_info["name"] if rep_info else "Unassigned",
            "age_days": (datetime.now() - lead.created_at).days,
            "days_since_contact": (datetime.now() - lead.last_contact).days if lead.last_contact else "Never",
            "qualification_status": "Qualified" if lead.score >= self.config["auto_qualify_threshold"] else "Needs Nurturing",
        }

    def get_sales_pipeline(self) -> Dict:
        pipeline = {status.value: [] for status in LeadStatus}
        for lead in self.leads.values():
            pipeline[lead.status.value].append({
                "lead_id": lead.lead_id,
                "company": lead.company_name,
                "score": lead.score,
                "priority": lead.priority.value,
                "age_days": (datetime.now() - lead.created_at).days,
            })
        summary = {
            "total_leads": len(self.leads),
            "by_status": {status: len(leads) for status, leads in pipeline.items()},
            "avg_score": sum(l.score for l in self.leads.values()) / len(self.leads) if self.leads else 0,
            "high_priority_count": len([l for l in self.leads.values() if l.priority in [LeadPriority.CRITICAL, LeadPriority.HIGH]]),
            "conversion_probability": self._calculate_conversion_probability(),
        }
        return {"pipeline": pipeline, "summary": summary}

    def _calculate_conversion_probability(self) -> float:
        if not self.leads:
            return 0.0
        qualified = len([l for l in self.leads.values() if l.status in [LeadStatus.QUALIFIED, LeadStatus.PROPOSAL, LeadStatus.NEGOTIATION]])
        won = len([l for l in self.leads.values() if l.status == LeadStatus.WON])
        total = len(self.leads)
        return ((qualified + won) / total * 100) if total > 0 else 0.0

    def get_overdue_leads(self) -> List[Dict]:
        overdue = []
        for lead in self.leads.values():
            if lead.status not in [LeadStatus.WON, LeadStatus.LOST]:
                hours_since_creation = (datetime.now() - lead.created_at).total_seconds() / 3600
                follow_up_deadline = hours_since_creation - self.config["follow_up_interval_hours"]
                if lead.last_contact:
                    hours_since_contact = (datetime.now() - lead.last_contact).total_seconds() / 3600
                    if hours_since_contact > self.config["follow_up_interval_hours"]:
                        overdue.append({
                            "lead_id": lead.lead_id,
                            "company": lead.company_name,
                            "status": lead.status.value,
                            "hours_since_contact": round(hours_since_contact, 1),
                            "priority": lead.priority.value,
                            "assigned_to": self.sales_reps.get(lead.assigned_to, {}).get("name", "Unassigned") if lead.assigned_to else "Unassigned",
                        })
                elif follow_up_deadline > 0:
                    overdue.append({
                        "lead_id": lead.lead_id,
                        "company": lead.company_name,
                        "status": lead.status.value,
                        "hours_since_creation": round(hours_since_creation, 1),
                        "priority": lead.priority.value,
                        "assigned_to": self.sales_reps.get(lead.assigned_to, {}).get("name", "Unassigned") if lead.assigned_to else "Unassigned",
                    })
        return sorted(overdue, key=lambda x: x.get("hours_since_contact", x.get("hours_since_creation", 0)), reverse=True)
