"""GNN Orchestrator - Main Intelligence Layer
Coordinates all modules and handles workflow execution
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from gnn_core.knowledge_base.logistics.route_optimizer import RouteOptimizer, Location
from gnn_core.knowledge_base.logistics.inventory_manager import InventoryManager, Product
from gnn_core.knowledge_base.logistics.predictive_maintenance import PredictiveMaintenance, Equipment, EquipmentType
from gnn_core.knowledge_base.ocr_nlp.document_processor import DocumentProcessor, DocumentType
from gnn_core.automation.routing.workflow_mapper import WorkflowMapper
from gnn_core.automation.crm.customer_onboarding import CustomerOnboarding, LeadSource
from gnn_core.automation.exception_handler.exception_handler import IntelligentExceptionHandler, ExceptionCategory, ExceptionSeverity
from gnn_core.operational.data_literacy.data_processor import DataProcessor
from gnn_core.operational.hitl.human_in_the_loop import HumanInTheLoop, ReviewCategory
from gnn_core.operational.security.compliance import ComplianceManager, ComplianceFramework, DataCategory


@dataclass
class GNNTask:
    task_id: str
    task_type: str
    description: str
    status: str
    input_data: Dict
    output_data: Optional[Dict]
    created_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]


@dataclass
class GNNSession:
    session_id: str
    user_id: str
    started_at: datetime
    tasks: List[str]
    context: Dict


class GNNOrchestrator:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.route_optimizer = RouteOptimizer()
        self.inventory_manager = InventoryManager()
        self.predictive_maintenance = PredictiveMaintenance()
        self.document_processor = DocumentProcessor()
        self.workflow_mapper = WorkflowMapper()
        self.customer_onboarding = CustomerOnboarding()
        self.exception_handler = IntelligentExceptionHandler()
        self.data_processor = DataProcessor()
        self.hitl = HumanInTheLoop()
        self.compliance_manager = ComplianceManager()
        self.tasks: Dict[str, GNNTask] = {}
        self.sessions: Dict[str, GNNSession] = {}
        self._setup_callbacks()

    def _setup_callbacks(self):
        def exception_notification(exception, message):
            print(f"[Exception Handler] {message}")
        def hitl_notification(checkpoint, event):
            print(f"[HITL] Event: {event} - Checkpoint: {checkpoint.checkpoint_id}")
        self.exception_handler.register_notification_callback(exception_notification)
        self.hitl.register_notification_callback(hitl_notification)

    def create_session(self, user_id: str) -> GNNSession:
        session_id = f"SESSION-{uuid.uuid4().hex[:8].upper()}"
        session = GNNSession(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            tasks=[],
            context={},
        )
        self.sessions[session_id] = session
        return session

    def create_task(self, task_type: str, description: str, input_data: Dict) -> GNNTask:
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
        task = GNNTask(
            task_id=task_id,
            task_type=task_type,
            description=description,
            status="pending",
            input_data=input_data,
            output_data=None,
            created_at=datetime.now(),
            completed_at=None,
            error=None,
        )
        self.tasks[task_id] = task
        return task

    def execute_route_optimization(self, origin: Dict, destination: Dict, cargo_type: str = "standard") -> Dict:
        task = self.create_task("route_optimization", "Finding optimal routes", {"origin": origin, "destination": destination})
        try:
            origin_loc = Location(origin.get("lat", 0), origin.get("lng", 0), origin.get("address", ""))
            dest_loc = Location(destination.get("lat", 0), destination.get("lng", 0), destination.get("address", ""))
            routes = self.route_optimizer.optimize_route(origin_loc, dest_loc, cargo_type)
            result = {
                "optimal_route": None,
                "alternatives": [],
                "count": len(routes),
            }
            if routes:
                result["optimal_route"] = {
                    "route_id": routes[0].route_id,
                    "total_cost": routes[0].total_cost,
                    "total_time_hours": routes[0].total_time_hours,
                    "total_distance_km": routes[0].total_distance_km,
                    "carrier": routes[0].carrier.name,
                    "score": routes[0].score,
                }
                result["alternatives"] = [
                    {"route_id": r.route_id, "cost": r.total_cost, "time": r.total_time_hours, "carrier": r.carrier.name}
                    for r in routes[1:]
                ]
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_rate_quote(self, origin: Dict, destination: Dict, cargo_type: str, weight_kg: float, volume_m3: float) -> Dict:
        task = self.create_task("rate_quote", "Generating rate quotes", {"origin": origin, "destination": destination})
        try:
            origin_loc = Location(origin.get("lat", 0), origin.get("lng", 0), origin.get("address", ""))
            dest_loc = Location(destination.get("lat", 0), destination.get("lng", 0), destination.get("address", ""))
            quotes = self.route_optimizer.get_rate_quote(origin_loc, dest_loc, cargo_type, weight_kg, volume_m3)
            result = {
                "quotes": [
                    {
                        "quote_id": q.quote_id,
                        "carrier": q.carrier.name,
                        "rate_per_kg": q.rate_per_kg,
                        "total_cost": q.total_cost,
                        "estimated_delivery": q.estimated_delivery.isoformat(),
                        "validity_hours": q.validity_hours,
                    }
                    for q in quotes
                ]
            }
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_inventory_check(self, sku: str) -> Dict:
        task = self.create_task("inventory_check", f"Checking inventory for {sku}", {"sku": sku})
        try:
            forecast = self.inventory_manager.forecast_demand(sku)
            stockout_risk = self.inventory_manager.analyze_stockout_risk(sku)
            reorder_level = self.inventory_manager.assess_reorder_level(sku)
            result = {
                "sku": sku,
                "forecast": {
                    "predicted_demand": forecast.predicted_demand,
                    "confidence": forecast.confidence,
                    "trend": forecast.trend,
                },
                "stockout_risk": {
                    "risk_level": stockout_risk.risk_level,
                    "days_until_stockout": stockout_risk.days_until_stockout,
                    "recommended_action": stockout_risk.recommended_action,
                },
                "reorder_level": reorder_level.value,
            }
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_document_processing(self, text: str, document_type: Optional[str] = None) -> Dict:
        task = self.create_task("document_processing", "Processing document", {"document_type": document_type})
        try:
            processed = self.document_processor.process_document(text)
            result = {
                "document_id": processed.document_id,
                "document_type": processed.metadata.document_type.value,
                "confidence_score": processed.confidence_score,
                "validation_status": processed.validation_status.value,
                "extracted_fields": [{"name": f.field_name, "value": f.value, "confidence": f.confidence} for f in processed.extracted_fields],
                "requires_human_review": processed.requires_human_review,
            }
            if processed.requires_human_review:
                checkpoint = self.hitl.create_checkpoint(
                    category=ReviewCategory.CUSTOM,
                    title=f"Document Review: {processed.metadata.document_type.value}",
                    description=f"Document confidence: {processed.confidence_score:.2f}",
                    context_data=result,
                    requested_by="system",
                )
                result["review_checkpoint_id"] = checkpoint.checkpoint_id
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_lead_capture(self, company: str, contact: str, email: str, phone: str, source: str, requirements: List[str]) -> Dict:
        task = self.create_task("lead_capture", f"Capturing lead for {company}", {"company": company})
        try:
            lead_source = LeadSource[source.upper()] if source.upper() in LeadSource.__members__ else LeadSource.UNKNOWN
            lead = self.customer_onboarding.capture_lead(company, contact, email, phone, lead_source, requirements)
            result = {
                "lead_id": lead.lead_id,
                "company": lead.company_name,
                "score": lead.score,
                "priority": lead.priority.value,
                "assigned_to": lead.assigned_to,
                "status": lead.status.value,
            }
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_exception_detection(self, data: Dict, source_system: str, source_id: str) -> Dict:
        task = self.create_task("exception_detection", "Detecting exceptions", {"source_system": source_system})
        try:
            exceptions = self.exception_handler.process_exception_data(data, source_system, source_id)
            result = {
                "exceptions_detected": len(exceptions),
                "exceptions": [
                    {
                        "exception_id": e.exception_id,
                        "category": e.category.value,
                        "severity": e.severity.value,
                        "title": e.title,
                        "status": e.status.value,
                    }
                    for e in exceptions
                ],
            }
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_workflow_analysis(self, workflow_id: Optional[str] = None, workflow_type: Optional[str] = None) -> Dict:
        task = self.create_task("workflow_analysis", "Analyzing workflow", {"workflow_id": workflow_id, "type": workflow_type})
        try:
            if workflow_type and not workflow_id:
                workflow = self.workflow_mapper.create_sample_workflow(workflow_type)
            elif workflow_id:
                summary = self.workflow_mapper.get_workflow_summary(workflow_id)
                task.output_data = summary
                task.status = "completed"
                task.completed_at = datetime.now()
                return summary
            else:
                candidates = self.workflow_mapper.get_high_volume_automation_candidates()
                task.output_data = {"candidates": candidates}
                task.status = "completed"
                task.completed_at = datetime.now()
                return {"candidates": candidates}
            if workflow:
                summary = self.workflow_mapper.get_workflow_summary(workflow.workflow_id)
                task.output_data = summary
                task.status = "completed"
                task.completed_at = datetime.now()
                return summary
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_compliance_check(self, framework: str, processing_description: str, data_categories: List[str], users_affected: int) -> Dict:
        task = self.create_task("compliance_check", "Running compliance assessment", {"framework": framework})
        try:
            fw = ComplianceFramework[framework.upper()] if framework.upper() in ComplianceFramework.__members__ else ComplianceFramework.GDPR
            data_cats = [DataCategory[dc.upper()] for dc in data_categories if dc.upper() in DataCategory.__members__]
            pia = self.compliance_manager.get_privacy_impact_assessment(processing_description, data_cats, users_affected)
            report = self.compliance_manager.generate_compliance_report(fw)
            result = {
                "privacy_impact_assessment": pia,
                "compliance_report": report,
            }
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def execute_equipment_health_check(self, equipment_id: str) -> Dict:
        task = self.create_task("equipment_health", f"Checking equipment {equipment_id}", {"equipment_id": equipment_id})
        try:
            prediction = self.predictive_maintenance.predict_health(equipment_id)
            alerts = self.predictive_maintenance.get_active_alerts(equipment_id)
            result = {
                "equipment_id": equipment_id,
                "health_score": prediction.health_score,
                "status": prediction.status.value,
                "predicted_failure_date": prediction.predicted_failure_date.isoformat() if prediction.predicted_failure_date else None,
                "remaining_useful_life_hours": prediction.remaining_useful_life_hours,
                "failure_probability_30d": prediction.failure_probability_30d,
                "recommended_actions": prediction.recommended_actions,
                "active_alerts": len(alerts),
            }
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.now()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}

    def get_system_status(self) -> Dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "route_optimizer": "active",
                "inventory_manager": "active",
                "predictive_maintenance": "active",
                "document_processor": "active",
                "workflow_mapper": "active",
                "customer_onboarding": "active",
                "exception_handler": "active",
                "data_processor": "active",
                "hitl": "active",
                "compliance_manager": "active",
            },
            "stats": {
                "total_tasks": len(self.tasks),
                "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
                "failed_tasks": len([t for t in self.tasks.values() if t.status == "failed"]),
                "active_sessions": len(self.sessions),
            },
            "inventory": self.inventory_manager.get_inventory_status(),
            "pipeline": self.customer_onboarding.get_sales_pipeline()["summary"],
            "exceptions": self.exception_handler.get_exception_summary(),
            "hitl": self.hitl.get_hitl_summary(),
        }

    def get_recommendations(self) -> List[Dict]:
        recommendations = []
        inventory = self.inventory_manager.get_inventory_status()
        if inventory.get("products_critical", 0) > 0:
            recommendations.append({
                "type": "inventory",
                "priority": "high",
                "message": f"{inventory['products_critical']} products at critical stock level",
                "action": "Execute emergency replenishment",
            })
        overdue_exceptions = self.exception_handler.get_overdue_exceptions()
        if overdue_exceptions:
            recommendations.append({
                "type": "exceptions",
                "priority": "high",
                "message": f"{len(overdue_exceptions)} exceptions overdue",
                "action": "Review and assign immediately",
            })
        overdue_reviews = self.hitl.get_overdue_checkpoints()
        if overdue_reviews:
            recommendations.append({
                "type": "reviews",
                "priority": "medium",
                "message": f"{len(overdue_reviews)} reviews overdue",
                "action": "Assign to available reviewers",
            })
        candidates = self.workflow_mapper.get_high_volume_automation_candidates()
        if candidates:
            top_candidate = candidates[0]
            recommendations.append({
                "type": "automation",
                "priority": "medium",
                "message": f"Workflow '{top_candidate['workflow_name']}' could save {top_candidate['estimated_hours_saved_per_month']} hours/month",
                "action": "Review automation opportunities",
            })
        overdue_leads = self.customer_onboarding.get_overdue_leads()
        if overdue_leads:
            recommendations.append({
                "type": "leads",
                "priority": "low",
                "message": f"{len(overdue_leads)} leads need follow-up",
                "action": "Contact assigned representatives",
            })
        return recommendations
