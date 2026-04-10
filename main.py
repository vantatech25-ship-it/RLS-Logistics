"""
RLS GNN System - Main Entry Point
Usage: python main.py [command] [options]
"""

import sys
import json
from datetime import datetime

from gnn_orchestrator.orchestrator import GNNOrchestrator


def main():
    gnn = GNNOrchestrator()
    print("=" * 60)
    print("RLS GNN (Global Neural Network) System v1.0.0")
    print("=" * 60)
    print("\nSystem Initialized Successfully")
    print("\nAvailable Commands:")
    print("  python main.py demo              - Run demo scenarios")
    print("  python main.py status           - Show system status")
    print("  python main.py recommendations  - Get AI recommendations")
    print("  python main.py help             - Show help")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            status = gnn.get_system_status()
            print(json.dumps(status, indent=2, default=str))
            
        elif command == "recommendations":
            recs = gnn.get_recommendations()
            print("\nAI Recommendations:")
            print("-" * 40)
            for i, rec in enumerate(recs, 1):
                print(f"\n{i}. [{rec['priority'].upper()}] {rec['type'].upper()}")
                print(f"   Message: {rec['message']}")
                print(f"   Action: {rec['action']}")
                
        elif command == "demo":
            run_demos(gnn)
            
        elif command == "help":
            show_help()
            
        else:
            print(f"Unknown command: {command}")
            show_help()
    else:
        status = gnn.get_system_status()
        print("\nQuick Status:")
        print(f"  Modules Active: {len([m for m in status['modules'].values() if m == 'active'])}")
        print(f"  Total Tasks: {status['stats']['total_tasks']}")
        print(f"  Completed Tasks: {status['stats']['completed_tasks']}")
        print(f"  Active Sessions: {status['stats']['active_sessions']}")


def run_demos(gnn):
    print("\n" + "=" * 60)
    print("RUNNING DEMO SCENARIOS")
    print("=" * 60)
    
    print("\n1. Route Optimization Demo...")
    result = gnn.execute_route_optimization(
        origin={"lat": 40.7128, "lng": -74.0060, "address": "New York, NY"},
        destination={"lat": 34.0522, "lng": -118.2437, "address": "Los Angeles, CA"},
        cargo_type="standard"
    )
    print(f"   Optimal Route Found: ${result['optimal_route']['total_cost']:.2f}")
    print(f"   Transit Time: {result['optimal_route']['total_time_hours']:.1f} hours")
    print(f"   Carrier: {result['optimal_route']['carrier']}")
    
    print("\n2. Lead Capture Demo...")
    result = gnn.execute_lead_capture(
        company="Acme Corporation",
        contact="John Doe",
        email="john@acme.com",
        phone="+1-555-0123",
        source="website",
        requirements=["freight_services", "warehousing", "customs_brokerage"]
    )
    print(f"   Lead Created: {result['lead_id']}")
    print(f"   Lead Score: {result['score']}")
    print(f"   Priority: {result['priority']}")
    print(f"   Assigned To: {result['assigned_to']}")
    
    print("\n3. Document Processing Demo...")
    sample_text = """
    INVOICE #INV-2024-001234
    FROM: ABC Suppliers Inc.
    TO: XYZ Corporation
    Date: 01/15/2024
    TOTAL AMOUNT DUE: $15,750.00
    Payment Terms: Net 30
    """
    result = gnn.execute_document_processing(sample_text)
    print(f"   Document Type: {result['document_type']}")
    print(f"   Confidence: {result['confidence_score']:.2%}")
    print(f"   Validation: {result['validation_status']}")
    print(f"   Fields Extracted: {len(result['extracted_fields'])}")
    
    print("\n4. Exception Detection Demo...")
    result = gnn.execute_exception_detection(
        data={
            "amount": 75000,
            "is_new_customer": True,
            "order_amount_greater_than": 10000
        },
        source_system="order_management",
        source_id="ORD-12345"
    )
    print(f"   Exceptions Detected: {result['exceptions_detected']}")
    for exc in result['exceptions']:
        print(f"   - [{exc['severity']}] {exc['title']}")
    
    print("\n5. Compliance Check Demo...")
    result = gnn.execute_compliance_check(
        framework="gdpr",
        processing_description="Customer data analytics for marketing",
        data_categories=["pii", "financial"],
        users_affected=50000
    )
    pia = result['privacy_impact_assessment']
    print(f"   Risk Level: {pia['risk_level'].upper()}")
    print(f"   DPIA Required: {pia['requires_dpia']}")
    
    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 60)


def show_help():
    print("""
RLS GNN System Help
===================

The RLS Global Neural Network (GNN) System provides comprehensive
AI-powered automation for logistics and business operations.

MODULES:
--------
1. Core Knowledge Base - Logistics AI
   - Route & Rate Optimization
   - Predictive Inventory Management
   - Predictive Maintenance
   - Document Processing (OCR/NLP)

2. Universal Business Automation
   - Workflow Mapping & Analysis
   - Lead & Customer Onboarding
   - Intelligent Exception Handling

3. Technical & Operational Layer
   - Data Literacy & Processing
   - Human-in-the-Loop (HITL)
   - Security & Compliance

API ENDPOINTS:
-------------
POST /api/route/optimize     - Optimize routes
POST /api/inventory/check    - Check inventory
POST /api/document/process   - Process documents
POST /api/lead/capture      - Capture leads
POST /api/exception/detect  - Detect exceptions
GET  /api/status            - System status
GET  /api/recommendations   - Get AI recommendations
""")


if __name__ == "__main__":
    main()
