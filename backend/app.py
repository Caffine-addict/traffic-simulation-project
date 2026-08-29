from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from signal_logic import AdaptiveSignalController
from simulation import TrafficSimulation

app = Flask(__name__)
# Allow local frontend by default
CORS(app, resources={r"/*": {"origins": "*"}})

# Controllers and simulation state
signal_controller = AdaptiveSignalController()
traffic_sim = TrafficSimulation()

@app.route('/', methods=['GET'])
def index():
    """
    Landing endpoint so opening http://localhost:5000 shows a status page
    instead of 404. Lists available API routes for the frontend.
    """
    return jsonify({
        "status": "ok",
        "message": "Traffic simulation API running",
        "endpoints": [
            "POST /simulation/start",
            "POST /simulation/step",
            "GET  /signals/status",
            "GET  /traffic/analytics",
            "POST /emergency/spawn"
        ]
    }), 200

@app.route('/simulation/start', methods=['POST'])
def sim_start():
    """
    Reset and start a fresh simulation.
    """
    global traffic_sim
    traffic_sim = TrafficSimulation()
    traffic_sim.reset()
    return jsonify({'status': 'started'}), 200

@app.route('/simulation/step', methods=['POST'])
def sim_step():
    """
    Advance the simulation by dt seconds and return current vehicles and stats.
    Lazily initializes the grid if step is called before /simulation/start.
    Body: { "dt": 0.06 }
    """
    data = request.json or {}
    try:
        dt = float(data.get('dt', 0.06))
    except Exception:
        dt = 0.06

    # Lazy init to prevent crashes if step is called before start/reset
    if not getattr(traffic_sim, 'nodes', None) or not traffic_sim.nodes:
        traffic_sim.reset()

    traffic_sim.step(dt)

    vehicles = traffic_sim.get_enhanced_vehicle_states()
    return jsonify({
        'vehicles': vehicles,
        'statistics': {
            'completed_trips': traffic_sim.completed_trips,
            'time': traffic_sim.time
        }
    }), 200

@app.route('/emergency/spawn', methods=['POST'])
def emergency_spawn():
    """
    Spawn an emergency vehicle and temporarily override signals for its corridor.
    Request body: { "vehicle_type": "ambulance" | "fire_truck" | "police" }
    """
    data = request.json or {}
    vehicle_type = str(data.get('vehicle_type', 'ambulance')).strip().lower()
    if vehicle_type not in ('ambulance', 'fire_truck', 'police'):
        vehicle_type = 'ambulance'

    # Spawn via simulation
    if not hasattr(traffic_sim, 'spawn_emergency_vehicle'):
        return jsonify({"status": "error", "message": "Emergency spawn not supported"}), 500

    emergency_vehicle = traffic_sim.spawn_emergency_vehicle(vehicle_type)

    # Determine corridor axis from route endpoints
    try:
        sx, sy = emergency_vehicle.path[0]
        ex, ey = emergency_vehicle.path[-1]
        override_dir = 'ns' if abs(ey - sy) >= abs(ex - sx) else 'ew'
    except Exception:
        override_dir = 'ns'

    # Activate emergency mode with auto-expiry (45s)
    signal_controller.emergency_mode_active = True
    signal_controller.emergency_override_direction = override_dir
    setattr(signal_controller, 'emergency_end_ts', time.time() + 45.0)

    return jsonify({
        "status": "ok",
        "vehicle_id": emergency_vehicle.id,
        "vehicle_type": vehicle_type,
        "signal_override": override_dir,
        "override_seconds": 45
    }), 200

@app.route('/signals/status', methods=['GET'])
def signals_status():
    """
    Return every intersection's current state with coordination offsets,
    honoring emergency override with auto-expiry.
    States: 'ns_green' | 'ew_green' | 'amber'
    """
    status = {}
    now = int(time.time())

    # Auto-expire emergency override
    if getattr(signal_controller, 'emergency_mode_active', False):
        end_ts = getattr(signal_controller, 'emergency_end_ts', 0)
        if end_ts and time.time() > end_ts:
            signal_controller.emergency_mode_active = False
            signal_controller.emergency_override_direction = None
            setattr(signal_controller, 'emergency_end_ts', 0)

    for i in range(10):
        for j in range(10):
            key = f"intersection_{i}_{j}"
            if getattr(signal_controller, 'emergency_mode_active', False):
                status[key] = (
                    'ns_green'
                    if signal_controller.emergency_override_direction == 'ns'
                    else 'ew_green'
                )
                continue
            # Staggered offsets for green-wave style coordination
            offset_cycle = (now + i * 25 + j * 17) % 120
            if offset_cycle < 40:
                state = 'ns_green'
            elif offset_cycle < 45:
                state = 'amber'
            elif offset_cycle < 85:
                state = 'ew_green'
            else:
                state = 'amber'
            status[key] = state

    return jsonify(status), 200

@app.route('/traffic/analytics', methods=['GET'])
def analytics():
    """
    Simple analytics for UI: throughput (trips/min) and average travel time (min).
    """
    trips = traffic_sim.completed_trips
    sim_t = max(traffic_sim.time, 1e-3)
    throughput_tpm = (trips / sim_t) * 60.0
    avg_travel_min = (sim_t / max(trips, 1)) if trips > 0 else 0.0
    return jsonify({
        'completed_trips': trips,
        'throughput_trips_per_min': round(throughput_tpm, 2),
        'avg_travel_time_min': round(avg_travel_min, 2)
    }), 200

if __name__ == '__main__':
    # Run development server
    app.run(host='0.0.0.0', port=5000, debug=True)
