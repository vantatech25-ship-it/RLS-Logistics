"""
RLS GNN System - Multi-Portal Server
Main, Drivers, and Handler Portals
"""

import sys
import os

# Add project root to path for module lookups
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from functools import wraps
import json
from datetime import datetime

from gnn_orchestrator.orchestrator import GNNOrchestrator
from gnn_core.operational.security.compliance import ComplianceFramework
from gnn_core.knowledge_base.logistics.route_optimizer import Location
from gnn_core.knowledge_base.logistics.inventory_manager import Product
from gnn_core.knowledge_base.logistics.predictive_maintenance import Equipment, EquipmentType, SensorReading
from gnn_core.automation.exception_handler.exception_handler import ExceptionCategory, ExceptionSeverity

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'portals', 'templates'), 
            static_folder=os.path.join(BASE_DIR, 'portals', 'static'))
app.secret_key = 'rls_super_secure_secret_key_gnn'
CORS(app)
gnn = GNNOrchestrator()

# Production Configuration
def load_config():
    config_path = os.path.join(BASE_DIR, 'portals', 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {"production_mode": False}

CONFIG = load_config()
PRODUCTION_MODE = CONFIG.get('production_mode', False)
print(f"SYSTEM INITIALIZATION: PRODUCTION_MODE={PRODUCTION_MODE}")

# User Management
def load_users():
    users_path = os.path.join(BASE_DIR, 'portals', 'users.json')
    with open(users_path, 'r') as f:
        return json.load(f)['users']

# Auth Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session or session['role'] not in roles:
                # Owners have God Mode access to all portals
                if session.get('role') == 'owner':
                    return f(*args, **kwargs)
                return "Unauthorized Access", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Data Loading Helpers
def load_json_data(filename, key):
    path = os.path.join(BASE_DIR, 'portals', filename)
    if not os.path.exists(path): return []
    with open(path, 'r') as f:
        return json.load(f).get(key, [])

# Initialize Production/Demo data
def init_system_data():
    # Load Products
    products = load_json_data('inventory.json', 'inventory')
    for p in products:
        sku = p['sku']
        if sku not in gnn.inventory_manager.products:
            product = Product(
                sku=sku, name=p['name'], category=p['category'],
                unit_cost=10.0, unit_price=25.0, reorder_point=p['reorder_point'],
                reorder_quantity=p['reorder_qty'], lead_time_days=7, safety_stock=50,
                current_stock=p['current'], max_stock=2000
            )
            gnn.inventory_manager.add_product(product)
            gnn.inventory_manager.simulate_demand_history(sku, 90)
    
    # Load Equipment
    equipment_data = load_json_data('equipment.json', 'equipment')
    for eq in equipment_data:
        eq_id = eq['id']
        if eq_id not in gnn.predictive_maintenance.equipment:
            equipment = Equipment(
                equipment_id=eq_id, name=eq['name'], 
                equipment_type=getattr(EquipmentType, eq['type'], EquipmentType.TRUCK),
                manufacturer="Client Supplied", model="Standard",
                installation_date=datetime(2023, 1, 1), last_maintenance=datetime(2024, 12, 1),
                operating_hours=5000, location="Main Facility",
                sensors=["temp", "vibration", "pressure", "rpm"]
            )
            gnn.predictive_maintenance.register_equipment(equipment)
            for _ in range(5): gnn.predictive_maintenance.simulate_sensor_reading(eq_id)
    
    # Create Real-world Exceptions if none exist
    if not gnn.exception_handler.exceptions:
        gnn.exception_handler.create_exception(
            ExceptionCategory.INVENTORY_ISSUE, ExceptionSeverity.MEDIUM,
            "Production Initialization", "System started with external data silos",
            "CoreSystem", "INIT"
        )

init_system_data()

# Fleet state (Loaded from JSON)
fleet_state = load_json_data('fleet.json', 'fleet')

# ==================== PORTAL ROUTES ====================

@app.route('/')
def landing():
    if 'user' in session:
        role = session['role']
        if role == 'owner': return redirect(url_for('main_portal'))
        if role == 'handler': return redirect(url_for('handlers_portal'))
        if role == 'driver': return redirect(url_for('drivers_portal'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form if request.form else request.json
        username = data.get('username')
        password = data.get('password')
        
        users = load_users()
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        
        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            
            # Direct to specific portal
            if user['role'] == 'owner': return redirect(url_for('main_portal'))
            if user['role'] == 'handler': return redirect(url_for('handlers_portal'))
            if user['role'] == 'driver': return redirect(url_for('drivers_portal'))
        
        return render_template('login.html', error="Invalid credentials. Please try again.", production_mode=PRODUCTION_MODE)
    
    return render_template('login.html', production_mode=PRODUCTION_MODE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@role_required(['owner'])
def main_portal():
    return render_template('main_dashboard.html', user=session.get('name'))

@app.route('/drivers')
@login_required
@role_required(['driver'])
def drivers_portal():
    return render_template('drivers_portal.html', user=session.get('name'))

@app.route('/handlers')
@login_required
@role_required(['handler'])
def handlers_portal():
    return render_template('handlers_portal.html', user=session.get('name'))

# ==================== MAIN PORTAL APIS ====================

@app.route('/api/main/status')
def main_status():
    return jsonify(gnn.get_system_status())

@app.route('/api/main/recommendations')
def main_recommendations():
    return jsonify(gnn.get_recommendations())

@app.route('/api/main/inventory/full')
def main_inventory():
    return jsonify(gnn.inventory_manager.get_inventory_status())

@app.route('/api/main/fleet/health')
def main_fleet_health():
    return jsonify(gnn.predictive_maintenance.get_fleet_health_summary())

@app.route('/api/main/pipeline')
def main_pipeline():
    return jsonify(gnn.customer_onboarding.get_sales_pipeline())

@app.route('/api/main/exceptions/full')
def main_exceptions():
    summary = gnn.exception_handler.get_exception_summary()
    summary['overdue'] = gnn.exception_handler.get_overdue_exceptions()
    return jsonify(summary)

@app.route('/api/main/hitl/full')
def main_hitl():
    summary = gnn.hitl.get_hitl_summary()
    summary['overdue'] = gnn.hitl.get_overdue_checkpoints()
    return jsonify(summary)

@app.route('/api/main/compliance')
def main_compliance():
    return jsonify(gnn.compliance_manager.generate_compliance_report(ComplianceFramework.GDPR))

@app.route('/api/main/workflows')
def main_workflows():
    # Create demo workflows
    wf_types = ['order_intake', 'freight_quoting']
    for wf_type in wf_types:
        gnn.workflow_mapper.create_sample_workflow(wf_type)
    candidates = gnn.workflow_mapper.get_high_volume_automation_candidates()
    return jsonify({"candidates": candidates})

@app.route('/api/main/fleet/full')
def main_fleet_full():
    return jsonify(fleet_state)

@app.route('/api/main/operations/report')
def main_operations_report():
    return jsonify({
        "operations": [
            {"id": "DEL-001", "client": "Shoprite CT", "driver": "v.d. Berg, S.", "payload": "14 Pallets (Cold)", "status": "In-Transit", "revenue": 12500},
            {"id": "DEL-002", "client": "Pick n Pay DBN", "driver": "Zwane, M.", "payload": "8 Pallets (Dry)", "status": "Loading", "revenue": 8200},
            {"id": "DEL-003", "client": "Checkers GP", "driver": "Mokoena, T.", "payload": "22 Pallets (Mixed)", "status": "Delayed", "revenue": 19400},
            {"id": "DEL-004", "client": "Woolworths PTA", "driver": "Nel, A.", "payload": "10 Pallets (Cold)", "status": "Idle", "revenue": 11000},
        ]
    })

# ==================== GOD MODE OVERRIDES ====================

@app.route('/api/main/override/reassign', methods=['POST'])
def override_reassign():
    data = request.json
    vehicle_id = data.get('vehicle_id')
    new_driver = data.get('new_driver')
    for v in fleet_state:
        if v['id'] == vehicle_id:
            v['driver'] = new_driver
            gnn.exception_handler.create_exception(
                ExceptionCategory.SYSTEM_ERROR, ExceptionSeverity.LOW,
                f"Manual Reassignment: {vehicle_id}", f"Vehicle reassigned to {new_driver} via God Mode",
                "GodMode", vehicle_id
            )
            return jsonify({"status": "success", "message": f"Vehicle {vehicle_id} reassigned to {new_driver}"})
    return jsonify({"status": "error", "message": "Vehicle not found"}), 404

@app.route('/api/main/override/reroute', methods=['POST'])
def override_reroute():
    data = request.json
    vehicle_id = data.get('vehicle_id')
    new_dest = data.get('destination')
    for v in fleet_state:
        if v['id'] == vehicle_id:
            v['destination'] = new_dest
            return jsonify({"status": "success", "message": f"Vehicle {vehicle_id} rerouted to {new_dest}"})
    return jsonify({"status": "error", "message": "Vehicle not found"}), 404

# ==================== DRIVERS PORTAL APIS ====================

@app.route('/api/drivers/routes')
def drivers_routes():
    return jsonify({
        "active_routes": [
            {"route_id": "R001", "origin": "New York, NY", "destination": "Los Angeles, CA", "status": "in_progress", "eta_hours": 24, "distance_km": 4500},
            {"route_id": "R002", "origin": "Chicago, IL", "destination": "Miami, FL", "status": "pending", "eta_hours": 36, "distance_km": 2100},
            {"route_id": "R003", "origin": "Seattle, WA", "destination": "Denver, CO", "status": "completed", "eta_hours": 0, "distance_km": 2100},
        ]
    })

@app.route('/api/drivers/vehicle/<vehicle_id>')
def drivers_vehicle(vehicle_id):
    health = gnn.predictive_maintenance.predict_health(vehicle_id)
    return jsonify({
        "vehicle_id": vehicle_id,
        "health_score": health.health_score,
        "status": health.status.value,
        "alerts": gnn.predictive_maintenance.get_active_alerts(vehicle_id),
        "recommended_actions": health.recommended_actions
    })

@app.route('/api/drivers/deliveries')
def drivers_deliveries():
    return jsonify({
        "deliveries": [
            {"id": "DEL001", "customer": "ABC Corp", "address": "123 Main St, LA", "status": "pending", "priority": "high", "time_window": "2-4 PM"},
            {"id": "DEL002", "customer": "XYZ Inc", "address": "456 Oak Ave, LA", "status": "in_transit", "priority": "normal", "time_window": "4-6 PM"},
            {"id": "DEL003", "customer": "Global Trade", "address": "789 Pine Rd, LA", "status": "delivered", "priority": "low", "time_window": "6-8 PM"},
        ]
    })

@app.route('/api/drivers/log-hours', methods=['POST'])
def drivers_log_hours():
    data = request.json
    return jsonify({"status": "success", "log_id": f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}"})

@app.route('/api/drivers/checklist', methods=['GET', 'POST'])
def drivers_checklist():
    checklist = {
        "pre_trip": ["Oil level check", "Tire pressure", "Lights working", "Brakes tested", "Mirrors adjusted"],
        "loading": ["Cargo secured", "Weight balanced", "Documentation complete", "Seals intact"],
        "delivery": ["Customer signature", "Photos taken", " POD uploaded", "Condition noted"]
    }
    if request.method == 'POST':
        data = request.json
        return jsonify({"status": "saved", "checklist_id": f"CHK-{datetime.now().strftime('%Y%m%d%H%M%S')}"})
    return jsonify(checklist)

# ==================== HANDLERS PORTAL APIS ====================

@app.route('/api/handlers/inventory')
def handlers_inventory():
    inventory = gnn.inventory_manager.get_inventory_status()
    products = []
    for sku, product in gnn.inventory_manager.products.items():
        forecast = gnn.inventory_manager.forecast_demand(sku)
        stockout = gnn.inventory_manager.analyze_stockout_risk(sku)
        reorder_level = gnn.inventory_manager.assess_reorder_level(sku)
        products.append({
            "sku": sku,
            "name": product.name,
            "current_stock": product.current_stock,
            "reorder_point": product.reorder_point,
            "reorder_qty": product.reorder_quantity,
            "demand_forecast": forecast.predicted_demand,
            "stockout_risk": stockout.risk_level,
            "reorder_level": reorder_level.value
        })
    return jsonify({"inventory": inventory, "products": products})

@app.route('/api/handlers/orders/inbound')
def handlers_inbound():
    return jsonify({
        "inbound_orders": [
            {"id": "PO001", "supplier": "Global Parts Co", "items": 150, "eta": "Today 3PM", "status": "expected"},
            {"id": "PO002", "supplier": "Industrial Supply", "items": 85, "eta": "Tomorrow 9AM", "status": "scheduled"},
            {"id": "PO003", "supplier": "FastShip Inc", "items": 200, "eta": "Today 5PM", "status": "in_transit"},
        ]
    })

@app.route('/api/handlers/orders/outbound')
def handlers_outbound():
    return jsonify({
        "outbound_orders": [
            {"id": "SO001", "customer": "ABC Corp", "items": 45, "priority": "high", "deadline": "Today 4PM", "status": "picking"},
            {"id": "SO002", "customer": "XYZ Inc", "items": 30, "priority": "normal", "deadline": "Tomorrow", "status": "packing"},
            {"id": "SO003", "customer": "MegaStore", "items": 120, "priority": "low", "deadline": "Next Week", "status": "queued"},
        ]
    })

@app.route('/api/handlers/equipment')
def handlers_equipment():
    fleet = gnn.predictive_maintenance.get_fleet_health_summary()
    equipment = []
    for eq_id in gnn.predictive_maintenance.equipment:
        health = gnn.predictive_maintenance.predict_health(eq_id)
        equipment.append({
            "equipment_id": eq_id,
            "name": gnn.predictive_maintenance.equipment[eq_id].name,
            "type": gnn.predictive_maintenance.equipment[eq_id].equipment_type.value,
            "health_score": health.health_score,
            "status": health.status.value,
            "alerts": len(gnn.predictive_maintenance.get_active_alerts(eq_id))
        })
    return jsonify({"fleet_summary": fleet, "equipment": equipment})

@app.route('/api/handlers/tasks')
def handlers_tasks():
    return jsonify({
        "tasks": [
            {"id": "TSK001", "description": "Restock SKU001 from warehouse B", "assigned_to": "Mike", "priority": "high", "due": "1 hour"},
            {"id": "TSK002", "description": "Move pallet to loading dock 3", "assigned_to": "Sarah", "priority": "normal", "due": "2 hours"},
            {"id": "TSK003", "description": "Cycle count aisle 5", "assigned_to": "John", "priority": "low", "due": "4 hours"},
            {"id": "TSK004", "description": "Clean forklift #2", "assigned_to": "Dave", "priority": "normal", "due": "End of shift"},
        ]
    })

@app.route('/api/handlers/scan', methods=['POST'])
def handlers_scan():
    data = request.json
    barcode = data.get('barcode', '')
    return jsonify({
        "status": "success",
        "barcode": barcode,
        "item": {"sku": "SKU001", "name": "Industrial Bearings", "location": "A-12-3", "quantity": 50}
    })

@app.route('/api/drivers/job/update', methods=['POST'])
def drivers_job_update():
    data = request.json
    job_id = data.get('job_id')
    status = data.get('status')
    vehicle_id = data.get('vehicle_id', 'TRUCK-001') # Default for demo
    
    # Update fleet state
    for v in fleet_state:
        if v['id'] == vehicle_id:
            v['status'] = 'active' if status == 'accepted' else 'idle' if status == 'completed' else v['status']
            break
            
    # Add to orchestrator tasks for record
    gnn.create_task("job_update", f"Job {job_id} status changed to {status}", data)
    
    return jsonify({"status": "success", "job_id": job_id, "new_status": status})

@app.route('/api/main/push-demo', methods=['POST'])
def push_demo():
    # In a real app, this would use a library like pywebpush
    # For demo, we just return a success message
    data = request.json
    print(f"🔔 MOCK PUSH TRIGGERED: {data.get('title')}: {data.get('body')}")
    return jsonify({
        "status": "success", 
        "message": "Push notification triggered in background (simulated)",
        "details": data
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 70)
    print("  RLS GNN SYSTEM - Multi-Portal Dashboard")
    print("=" * 70)
    print(f"  Live at: http://0.0.0.0:{port}")
    print("=" * 70)
    print("\nServer starting...")
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
