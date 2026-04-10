"""
RLS GNN System - Flask Web Server with Dashboard
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime

from gnn_orchestrator.orchestrator import GNNOrchestrator
from gnn_core.knowledge_base.logistics.route_optimizer import Location
from gnn_core.knowledge_base.logistics.inventory_manager import Product
from gnn_core.knowledge_base.logistics.predictive_maintenance import Equipment, EquipmentType

app = Flask(__name__, template_folder='api/templates', static_folder='api/static')
CORS(app)
gnn = GNNOrchestrator()


@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/drivers')
def drivers_portal():
    return render_template('drivers.html')

@app.route('/handlers')
def handlers_portal():
    return render_template('handlers.html')


@app.route('/api/status')
def api_status():
    return jsonify(gnn.get_system_status())


@app.route('/api/recommendations')
def api_recommendations():
    return jsonify(gnn.get_recommendations())


@app.route('/api/route/optimize', methods=['POST'])
def api_route_optimize():
    data = request.json
    origin = data.get('origin', {'lat': -26.2041, 'lng': 28.0473, 'address': 'Johannesburg'})
    destination = data.get('destination', {'lat': -33.9249, 'lng': 18.4241, 'address': 'Cape Town'})
    cargo_type = data.get('cargo_type', 'standard')
    result = gnn.execute_route_optimization(origin, destination, cargo_type)
    return jsonify(result)


@app.route('/api/rate/quote', methods=['POST'])
def api_rate_quote():
    data = request.json
    origin = Location(data.get('origin_lat', -26.2041), data.get('origin_lng', 28.0473))
    destination = Location(data.get('dest_lat', -33.9249), data.get('dest_lng', 18.4241))
    cargo_type = data.get('cargo_type', 'standard')
    weight = data.get('weight_kg', 1000)
    volume = data.get('volume_m3', 10)
    result = gnn.execute_rate_quote(
        {'lat': origin.lat, 'lng': origin.lng},
        {'lat': destination.lat, 'lng': destination.lng},
        cargo_type, weight, volume
    )
    return jsonify(result)


@app.route('/api/inventory/check', methods=['POST'])
def api_inventory_check():
    data = request.json
    sku = data.get('sku', 'SKU001')
    if sku not in gnn.inventory_manager.products:
        product = Product(
            sku=sku, name=f"Product {sku}", category="general",
            unit_cost=10.0, unit_price=25.0, reorder_point=100,
            reorder_quantity=500, lead_time_days=7, safety_stock=50,
            current_stock=200, max_stock=2000
        )
        gnn.inventory_manager.add_product(product)
        gnn.inventory_manager.simulate_demand_history(sku, 90)
    result = gnn.execute_inventory_check(sku)
    return jsonify(result)


@app.route('/api/document/process', methods=['POST'])
def api_document_process():
    data = request.json
    text = data.get('text', '')
    result = gnn.execute_document_processing(text)
    return jsonify(result)


@app.route('/api/lead/capture', methods=['POST'])
def api_lead_capture():
    data = request.json
    result = gnn.execute_lead_capture(
        data.get('company', 'Test Company'),
        data.get('contact', 'John Doe'),
        data.get('email', 'john@test.com'),
        data.get('phone', '+1-555-0100'),
        data.get('source', 'website'),
        data.get('requirements', ['freight'])
    )
    return jsonify(result)


@app.route('/api/exception/detect', methods=['POST'])
def api_exception_detect():
    data = request.json
    result = gnn.execute_exception_detection(
        data.get('data', {}),
        data.get('source_system', 'api'),
        data.get('source_id', 'API-001')
    )
    return jsonify(result)


@app.route('/api/compliance/check', methods=['POST'])
def api_compliance_check():
    data = request.json
    result = gnn.execute_compliance_check(
        data.get('framework', 'gdpr'),
        data.get('processing_description', 'Data processing'),
        data.get('data_categories', ['pii']),
        data.get('users_affected', 1000)
    )
    return jsonify(result)


@app.route('/api/pipeline')
def api_pipeline():
    return jsonify(gnn.customer_onboarding.get_sales_pipeline())


@app.route('/api/exceptions')
def api_exceptions():
    return jsonify(gnn.exception_handler.get_exception_summary())


@app.route('/api/hitl')
def api_hitl():
    return jsonify(gnn.hitl.get_hitl_summary())


if __name__ == '__main__':
    print("=" * 60)
    print("RLS GNN System - Web Dashboard")
    print("=" * 60)
    print("Starting server at http://127.0.0.1:5000")
    print("Open your browser to view the dashboard")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
