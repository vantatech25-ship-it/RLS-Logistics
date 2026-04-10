"""
RLS GNN (Global Neural Network) System
A comprehensive AI system for logistics and business automation
"""

__version__ = "1.0.0"
__author__ = "RLS Systems"

from gnn_orchestrator.orchestrator import GNNOrchestrator
from gnn_core.knowledge_base.logistics.route_optimizer import RouteOptimizer
from gnn_core.knowledge_base.logistics.inventory_manager import InventoryManager
from gnn_core.knowledge_base.logistics.predictive_maintenance import PredictiveMaintenance
from gnn_core.knowledge_base.ocr_nlp.document_processor import DocumentProcessor
from gnn_core.automation.routing.workflow_mapper import WorkflowMapper
from gnn_core.automation.crm.customer_onboarding import CustomerOnboarding
from gnn_core.automation.exception_handler.exception_handler import IntelligentExceptionHandler
from gnn_core.operational.data_literacy.data_processor import DataProcessor
from gnn_core.operational.hitl.human_in_the_loop import HumanInTheLoop
from gnn_core.operational.security.compliance import ComplianceManager

__all__ = [
    "GNNOrchestrator",
    "RouteOptimizer",
    "InventoryManager",
    "PredictiveMaintenance",
    "DocumentProcessor",
    "WorkflowMapper",
    "CustomerOnboarding",
    "IntelligentExceptionHandler",
    "DataProcessor",
    "HumanInTheLoop",
    "ComplianceManager",
]
