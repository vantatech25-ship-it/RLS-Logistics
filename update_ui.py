import os

def apply_base_edits(content):
    c1 = content.replace(
        '<button class="refresh-btn" onclick="loadDashboard()">Refresh</button>',
        '<button class="refresh-btn" onclick="loadDashboard()">Refresh</button>\n            <button class="refresh-btn" style="border-color:#f44336; color:#f44336;" onclick="document.getElementById(\'loginOverlay\').style.display=\'flex\'; setTimeout(()=>document.getElementById(\'loginOverlay\').style.opacity=\'1\', 10);">Log Out</button>'
    )
    c2 = c1.replace(
        'map.fitBounds(polyline.getBounds(), {padding: [50, 50]});',
        'map.fitBounds(polyline.getBounds(), {padding: [50, 50]});\n            const truckIcon = L.icon({iconUrl: \'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png\', shadowUrl: \'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png\', iconSize: [25, 41], iconAnchor: [12, 41]});\n            const driver = L.marker([-29.0852, 26.1596], {icon: truckIcon}).addTo(map).bindPopup("<b>Truck ZA-042</b><br>Sipho Khumalo<br>Status: IN TRANSIT").openPopup();'
    )
    return c2

# Dashboard
with open('api/templates/dashboard.html', 'r', encoding='utf-8') as f: dash = f.read()
with open('api/templates/dashboard.html', 'w', encoding='utf-8') as f: f.write(apply_base_edits(dash))

# Drivers
with open('api/templates/drivers.html', 'r', encoding='utf-8') as f: drivers = f.read()
drivers = apply_base_edits(drivers).replace(
    '<div class="stats-grid" id="statsGrid">',
    '''<div class="section" style="border-color:#ff9800; background:rgba(255,152,0,0.05); margin-bottom:20px;">
            <div class="section-header">
                <h2 class="section-title" style="color:#ff9800; margin:0;">Incoming Dispatch Job #RT-993</h2>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                     <p style="color:#fff; font-size:16px; margin-bottom:5px;"><strong>Route:</strong> Johannesburg (ZA) &rarr; Cape Town (ZA)</p>
                     <p style="color:#71767b; font-size:14px;"><strong>Cargo:</strong> Standard Freight | <strong>Distance:</strong> 1398 km | <strong>Est. Payout:</strong> ZAR 12,500</p>
                </div>
                <div style="display:flex; gap:15px;">
                     <button class="btn" style="background:#00d4aa; color:#000;" onclick="this.textContent=\'JOB ACCEPTED\'; this.style.background=\'#2f3842\'; this.style.color=\'#71767b\'; alert(\'Dispatch notified. Route initialized on map.\');">ACCEPT JOB</button>
                     <button class="btn" style="background:transparent; border:1px solid #f44336; color:#f44336;" onclick="this.parentElement.parentElement.parentElement.style.display=\'none\';">DECLINE</button>
                </div>
            </div>
        </div>
        <div class="stats-grid" id="statsGrid">'''
)
with open('api/templates/drivers.html', 'w', encoding='utf-8') as f: f.write(drivers)

# Handlers
with open('api/templates/handlers.html', 'r', encoding='utf-8') as f: handlers = f.read()
handlers = apply_base_edits(handlers).replace(
    '<div class="stats-grid" id="statsGrid">',
    '''<div class="two-col" style="margin-bottom:20px;">
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title" style="margin:0;">Driver Comms (Live)</h2>
                </div>
                <div>
                   <div style="background:#0f1419; padding:15px; border-radius:8px; height:200px; overflow-y:auto; border:1px solid #2f3842; margin-bottom:15px;">
                      <div style="margin-bottom:10px;"><span style="color:#00d4aa; font-weight:bold;">Sipho Khumalo (ZA-042):</span> <span style="color:#e7e9ea">Arrived at Bloemfontein checkpoint. Traffic is heavy.</span></div>
                      <div style="margin-bottom:10px; text-align:right;"><span style="color:#71767b; font-weight:bold;">You:</span> <span style="color:#e7e9ea">Copy that. Checking alternative routes.</span></div>
                   </div>
                   <div style="display:flex; gap:10px;">
                       <input type="text" class="form-input" placeholder="Message driver ZA-042..." style="flex:1;">
                       <button class="btn" onclick="alert(\'Message Sent\')">Send</button>
                   </div>
                </div>
            </div>
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title" style="margin:0;">Active Route Override</h2>
                </div>
                <div>
                    <div class="form-group">
                        <label class="form-label">Active Driver</label>
                        <select class="form-input"><option>Sipho Khumalo (ZA-042)</option><option>Thabo Ndlovu (ZA-118)</option></select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">New Waypoint (Lat, Lng)</label>
                        <input type="text" class="form-input" value="-30.7167, 25.0833 (Colesberg)">
                    </div>
                    <button class="btn" style="background:#ff9800; width:100%; border:none; color:#000;" onclick="alert(\'Reroute instruction dispatched securely to driver unit.\')">DISPATCH NEW ROUTE</button>
                </div>
            </div>
        </div>
        <div class="stats-grid" id="statsGrid">'''
)
with open('api/templates/handlers.html', 'w', encoding='utf-8') as f: f.write(handlers)
