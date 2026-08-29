import uuid, math, random

class Vehicle:
    def __init__(self, path, lane=0, velocity=6.0, acceleration=0.0, length=4.5, max_speed=11.0, vehicle_type='car'):
        self.id = str(uuid.uuid4())[:8]
        self.path = path
        self.lane = lane
        self.velocity = velocity
        self.acceleration = acceleration if acceleration != 0.0 else random.uniform(0.2, 0.8)
        self.length = length
        self.max_speed = max_speed
        self.vehicle_type = vehicle_type
        self.is_emergency = False
        self.crashed = False
        self.current_segment = 0
        self.progress = 0.0

        if vehicle_type == 'truck':
            self.max_speed = min(9.0, self.max_speed)
            self.acceleration = 0.6
            self.length = 8.0
        elif vehicle_type == 'bus':
            self.max_speed = min(10.0, self.max_speed)
            self.acceleration = 0.8
            self.length = 12.0
        elif vehicle_type == 'motorcycle':
            self.max_speed = min(12.0, self.max_speed)
            self.acceleration = 1.5
        elif vehicle_type in ('ambulance','fire_truck','police'):
            self.max_speed = min(13.0, self.max_speed)
            self.acceleration = 1.8
        else:
            self.max_speed = min(11.0, self.max_speed)
            self.acceleration = 1.2

        self.following_distance = random.uniform(14, 24)
        self.aggressiveness = random.uniform(0.3, 0.9)

    def get_position(self):
        if self.current_segment >= len(self.path) - 1:
            return self.path[-1]
        sx, sy = self.path[self.current_segment]
        ex, ey = self.path[self.current_segment + 1]
        x = sx + (ex - sx) * self.progress
        y = sy + (ey - sy) * self.progress

        dx, dy = ex - sx, ey - sy
        seg_len = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / seg_len, dx / seg_len
        lane_px = (self.lane - 0.5) * 4.0
        x += nx * lane_px
        y += ny * lane_px

        return (x, y)

    def update(self, dt):
        if self.crashed or self.current_segment >= len(self.path) - 1:
            return

        friction = 0.35
        brake_cap = 2.5
        jerk_cap = 1.0

        self.acceleration = max(self.acceleration - jerk_cap*dt, min(self.acceleration + jerk_cap*dt, self.acceleration))
        self.acceleration -= friction * dt

        target_max = self.max_speed * (1.1 if self.is_emergency else 1.0)
        self.velocity = max(0.0, min(self.velocity + self.acceleration * dt, target_max))

        sx, sy = self.path[self.current_segment]
        ex, ey = self.path[self.current_segment + 1]
        seg_len = max(1.0, math.hypot(ex - sx, ey - sy))
        advance = (self.velocity * dt) / (seg_len / 12.0)
        self.progress += max(0.0, advance)

        if self.progress >= 1.0:
            self.current_segment += 1
            self.progress = 0.0
