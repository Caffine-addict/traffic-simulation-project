import random
import math
from vehicle import Vehicle

class TrafficSimulation:
    def __init__(self):
        self.vehicles = []
        self.emergency_vehicles = []
        self.time = 0.0
        self.crashes = []
        self.completed_trips = 0
        self.scenario = 'normal'
        self.nodes = {}

        # 10x10 grid sized to match UI visuals
        self.origin_x, self.origin_y = 50, 50
        self.spacing_x, self.spacing_y = 80, 60
        self.grid_w, self.grid_h = 10, 10

        self.locations = {
            'hospital': (self.origin_x, self.origin_y),
            'business_district': (self.origin_x + 5 * self.spacing_x, self.origin_y + 4 * self.spacing_y)
        }

    # ---------------- Grid ----------------

    def build_nodes(self):
        self.nodes.clear()
        for gx in range(self.grid_w):
            for gy in range(self.grid_h):
                nid = f"N{gx}_{gy}"
                self.nodes[nid] = (
                    self.origin_x + gx * self.spacing_x,
                    self.origin_y + gy * self.spacing_y
                )

    def reset(self):
        self.vehicles.clear()
        self.emergency_vehicles.clear()
        self.crashes.clear()
        self.time = 0.0
        self.completed_trips = 0
        self.build_nodes()

        def add_link(a, b, lane, speed, vehicle_type='car'):
            path = [self.nodes[a], self.nodes[b]]  # adjacent, axis-aligned
            v = Vehicle(path=path, lane=lane, velocity=speed, vehicle_type=vehicle_type)
            self.vehicles.append(v)

        # Seed conservative traffic along adjacent links (always on-road)
        for gx in range(self.grid_w):
            for gy in range(self.grid_h):
                a = f"N{gx}_{gy}"
                if gx < self.grid_w - 1:
                    b = f"N{gx + 1}_{gy}"
                    for k in range(2):
                        lane = k % 2
                        speed = random.uniform(5.0, 9.0)
                        vt = random.choice(['car', 'car', 'truck', 'bus'])
                        add_link(a, b, lane, speed, vt)
                if gy < self.grid_h - 1:
                    b = f"N{gx}_{gy + 1}"
                    for k in range(2):
                        lane = k % 2
                        speed = random.uniform(4.0, 8.0)
                        vt = random.choice(['car', 'car', 'truck'])
                        add_link(a, b, lane, speed, vt)

    # ------------- Routing (Manhattan) -------------

    def manhattan_path(self, sx, sy, dx, dy):
        """
        Build an axis-aligned waypoint list along the grid from (sx,sy) to (dx,dy).
        """
        if not self.nodes:
            self.build_nodes()

        path = []
        x, y = sx, sy
        path.append(self.nodes[f"N{x}_{y}"])
        while x != dx:
            x += 1 if dx > x else -1
            path.append(self.nodes[f"N{x}_{y}"])
        while y != dy:
            y += 1 if dy > y else -1
            path.append(self.nodes[f"N{x}_{y}"])
        return path

    # ------------- Signals (same timing as /signals/status) -------------

    def intersection_state(self, gx, gy, t_seconds):
        """
        Returns 'ns_green' | 'ew_green' | 'amber' for intersection timing with offsets.
        """
        cycle = 120.0
        offset_cycle = (int(t_seconds) + gx * 25 + gy * 17) % int(cycle)
        if offset_cycle < 40:
            return 'ns_green'
        if offset_cycle < 45:
            return 'amber'
        if offset_cycle < 85:
            return 'ew_green'
        return 'amber'

    # Helper: direction tag for current segment
    @staticmethod
    def seg_dir(sx, sy, ex, ey):
        # y increases downward in pixels; treat vertical as 'ns', horizontal as 'ew'
        return 'ns' if abs(ey - sy) > abs(ex - sx) else 'ew'

    # ------------- Spawning -------------

    def spawn_regular_traffic(self):
        if not self.nodes:
            self.build_nodes()
        if len(self.vehicles) > 250:
            return

        if random.random() < (0.35 if self.scenario == 'rush_hour' else 0.2):
            sx = random.randrange(self.grid_w)
            sy = random.randrange(self.grid_h)
            dx = random.randrange(self.grid_w)
            dy = random.randrange(self.grid_h)
            while dx == sx and dy == sy:
                dx = random.randrange(self.grid_w)
                dy = random.randrange(self.grid_h)

            path = self.manhattan_path(sx, sy, dx, dy)

            vtype = random.choice(['car', 'car', 'truck', 'bus'])
            speed = random.uniform(5.0, 9.0)
            v = Vehicle(path=path, lane=random.randint(0, 1), velocity=speed, vehicle_type=vtype)
            self.vehicles.append(v)

    def _random_edge_node(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            return (random.randrange(self.grid_w), 0)
        if edge == 'bottom':
            return (random.randrange(self.grid_w), self.grid_h - 1)
        if edge == 'left':
            return (0, random.randrange(self.grid_h))
        return (self.grid_w - 1, random.randrange(self.grid_h))

    def _random_center_node(self):
        gx = random.randrange(max(2, self.grid_w // 3), min(self.grid_w - 2, 2 * self.grid_w // 3))
        gy = random.randrange(max(2, self.grid_h // 3), min(self.grid_h - 2, 2 * self.grid_h // 3))
        return (gx, gy)

    def spawn_emergency_vehicle(self, vehicle_type='ambulance'):
        if not self.nodes:
            self.build_nodes()

        sx, sy = self._random_edge_node()
        dx, dy = self._random_center_node()
        while (dx, dy) == (sx, sy):
            dx, dy = self._random_center_node()

        path = self.manhattan_path(sx, sy, dx, dy)

        v = Vehicle(path=path, lane=0, velocity=8.0, vehicle_type=vehicle_type)
        v.is_emergency = True
        self.vehicles.append(v)
        try:
            self.emergency_vehicles.append(v)
        except Exception:
            self.emergency_vehicles = [v]
        return v

    # ------------- Flow control -------------

    def optimize_traffic_flow(self):
        buckets = {}
        for v in self.vehicles:
            x, y = v.get_position()
            bx = int((x - self.origin_x) // (self.spacing_x * 2))
            by = int((y - self.origin_y) // (self.spacing_y * 2))
            buckets[(bx, by)] = buckets.get((bx, by), 0) + 1

        for v in self.vehicles:
            x, y = v.get_position()
            bx = int((x - self.origin_x) // (self.spacing_x * 2))
            by = int((y - self.origin_y) // (self.spacing_y * 2))
            density = buckets.get((bx, by), 0)
            if density > 12:
                v.max_speed = max(v.max_speed * 0.95, 5.0)
                v.acceleration = min(v.acceleration, 0.8)
            elif density < 4:
                v.max_speed = min(v.max_speed * 1.02, 12.0)

    # ------------- Simulation step -------------

    def step(self, dt):
        if not self.nodes:
            self.build_nodes()

        self.spawn_regular_traffic()

        brake_cap = 2.8  # comfortable max decel
        hold_margin = 4.0  # meters/pixels to stop before the intersection center

        vehicles_to_remove = []
        for v in self.vehicles:
            # Signal-aware braking ahead of the next intersection
            if v.current_segment < len(v.path) - 1:
                sx, sy = v.path[v.current_segment]
                ex, ey = v.path[v.current_segment + 1]
                direction = self.seg_dir(sx, sy, ex, ey)

                # distance remaining to the intersection node
                x, y = v.get_position()
                seg_len = max(1.0, math.hypot(ex - sx, ey - sy))
                # project progress along the segment endpoint
                # compute remaining distance along the centerline (ignore lane offset for stop logic)
                # approximate remaining = direct distance to end
                remaining = max(0.0, math.hypot(ex - x, ey - y) - hold_margin)

                state = self.intersection_state(
                    int(round((ex - self.origin_x) / self.spacing_x)),
                    int(round((ey - self.origin_y) / self.spacing_y)),
                    self.time
                )

                must_stop = False
                if state == 'amber':
                    # If close enough, proceed; otherwise plan a stop
                    go_threshold = max(6.0, v.velocity * 0.8)
                    must_stop = remaining > go_threshold
                elif state == 'ns_green' and direction == 'ew':
                    must_stop = True
                elif state == 'ew_green' and direction == 'ns':
                    must_stop = True

                if must_stop:
                    # Physics stopping: a = v^2 / (2 d)
                    if remaining > 1e-3:
                        req_brake = min(brake_cap, (v.velocity * v.velocity) / (2.0 * remaining))
                    else:
                        req_brake = brake_cap
                    v.acceleration = -req_brake
                    # Prevent overshooting the stop line
                    # Clamp progress so we never cross into the node while red
                    # (Vehicle.update uses progress; emulate by zeroing velocity near line)
                    if remaining < 0.5 and v.velocity < 0.6:
                        v.velocity = 0.0

            v.update(dt)

            # Despawn when final waypoint reached (clean disappearance)
            if v.current_segment >= len(v.path) - 1:
                x2, y2 = v.get_position()
                ex2, ey2 = v.path[-1]
                if math.hypot(x2 - ex2, y2 - ey2) < 8.0:
                    vehicles_to_remove.append(v)
                    self.completed_trips += 1

        for v in vehicles_to_remove:
            if v in self.vehicles:
                self.vehicles.remove(v)
            if v in getattr(self, 'emergency_vehicles', []):
                try:
                    self.emergency_vehicles.remove(v)
                except ValueError:
                    pass

        self.optimize_traffic_flow()
        self.time += dt

    # ------------- Output -------------

    def get_enhanced_vehicle_states(self):
        states = []
        for v in self.vehicles:
            x, y = v.get_position()
            heading = 0.0
            if v.current_segment < len(v.path) - 1:
                tx, ty = v.path[v.current_segment + 1]
                dx, dy = tx - x, ty - y
                if abs(dx) + abs(dy) > 1e-3:
                    heading = math.degrees(math.atan2(dy, dx))
            states.append({
                'id': v.id,
                'x': x,
                'y': y,
                'speed': v.velocity,
                'heading': heading,
                'type': getattr(v, 'vehicle_type', 'car'),
                'is_emergency': getattr(v, 'is_emergency', False),
                'crashed': v.crashed
            })
        return states
