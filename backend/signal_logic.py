import time

class AdaptiveSignalController:
    def __init__(self):
        self.MIN_GREEN_TIME = 10
        self.MAX_GREEN_TIME = 60
        self.AMBER_TIME = 3
        self.ALL_RED_TIME = 2
        self.emergency_mode_active = False
        self.emergency_override_direction = None

    def calculate_timings(self, counts, cycle_base=60, high_demand_scale=1.5):
        ns_traffic = counts.get('north', 0) + counts.get('south', 0)
        ew_traffic = counts.get('east', 0) + counts.get('west', 0)
        total = ns_traffic + ew_traffic

        cycle = int(min(self.MAX_GREEN_TIME * 2,
                        max(self.MIN_GREEN_TIME * 2,
                            cycle_base * (high_demand_scale if total > 100 else 1.0))))

        if total == 0:
            ns_green = self.MIN_GREEN_TIME
            ew_green = self.MIN_GREEN_TIME
        else:
            ns_green = int(max(self.MIN_GREEN_TIME, min((ns_traffic / total) * cycle, self.MAX_GREEN_TIME)))
            ew_green = int(max(self.MIN_GREEN_TIME, min((ew_traffic / total) * cycle, self.MAX_GREEN_TIME)))

        return {
            "ns_green": ns_green,
            "ns_amber": self.AMBER_TIME,
            "ew_green": ew_green,
            "ew_amber": self.AMBER_TIME,
            "all_red": self.ALL_RED_TIME
        }

    def activate_emergency_override(self, direction):
        print(f"--- 🚨 EMERGENCY OVERRIDE ACTIVATED FOR DIRECTION: {direction.upper()} 🚨 ---")
        self.emergency_mode_active = True
        if direction.lower() in ['north', 'south']:
            self.emergency_override_direction = 'ns'
        elif direction.lower() in ['east', 'west']:
            self.emergency_override_direction = 'ew'
        else:
            self.emergency_mode_active = False

    def deactivate_emergency_override(self):
        print("--- 🚨 EMERGENCY OVERRIDE DEACTIVATED ---")
        self.emergency_mode_active = False
        self.emergency_override_direction = None
