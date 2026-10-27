# Traffic Signal Simulation API

A Flask backend that simulates traffic on a 10×10 city grid: vehicles routed across intersections,
coordinated signals, density-based speed control, and emergency vehicles that get a green
corridor.

## What it simulates

- **Grid and vehicles** (`simulation.py`, `vehicle.py`): a 10×10 intersection grid with regular
  traffic spawned at the edges and routed along Manhattan-style paths. A rush-hour scenario raises
  the spawn rate.
- **Signal coordination** (`app.py`): each intersection cycles north–south green, amber, east–west
  green, with offsets staggered by grid position to form green waves.
- **Adaptive timing** (`signal_logic.py`): a controller that splits green time between the two
  directions in proportion to traffic, bounded by minimum and maximum green times. It is not yet
  wired into the running simulation, which uses the fixed coordinated cycle above.
- **Flow control** (`simulation.py`): vehicles slow down in dense areas and speed up in empty ones.
- **Emergency vehicles**: spawning an ambulance, fire truck or police car turns every signal green
  along its axis for 45 seconds, then the override expires on its own.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/simulation/start` | Reset and start a fresh simulation |
| `POST` | `/simulation/step` | Advance by `dt` seconds (body `{"dt": 0.06}`); returns vehicles and stats |
| `GET` | `/signals/status` | Current state of every intersection |
| `GET` | `/traffic/analytics` | Traffic statistics |
| `POST` | `/emergency/spawn` | Spawn an emergency vehicle (body `{"vehicle_type": "ambulance"}`) |

## Run it

```bash
cd backend
pip install flask flask-cors
python app.py          # http://localhost:5000
```

The `frontend/` folder holds only the React project configuration; the frontend source is not in
this repository yet.

## Stack

Python · Flask · React (frontend, not included)
