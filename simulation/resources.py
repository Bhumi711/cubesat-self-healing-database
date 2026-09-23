from dataclasses import dataclass


@dataclass
class ResourceState:

    battery: float = 100.0
    storage: float = 0.0
    cpu: float = 20.0
    bandwidth: float = 100.0


class ResourceManager:

    def __init__(self):
        self.resources = ResourceState()

    def get_state(self):
        return {
            "battery": self.resources.battery,
            "storage": self.resources.storage,
            "cpu": self.resources.cpu,
            "bandwidth": self.resources.bandwidth
        }

    def set_battery(self, value):
        self.resources.battery = self._clamp(value)

    def set_storage(self, value):
        self.resources.storage = self._clamp(value)

    def set_cpu(self, value):
        self.resources.cpu = self._clamp(value)

    def set_bandwidth(self, value):
        self.resources.bandwidth = self._clamp(value)

    def consume_battery(self, amount):
        self.resources.battery = self._clamp(
            self.resources.battery - amount
        )

    def consume_storage(self, amount):
        self.resources.storage = self._clamp(
            self.resources.storage + amount
        )

    def release_storage(self, amount):
        self.resources.storage = self._clamp(
            self.resources.storage - amount
        )

    def consume_cpu(self, amount):
        self.resources.cpu = self._clamp(
            self.resources.cpu + amount
        )

    def set_bandwidth(self, value):
        self.resources.bandwidth = self._clamp(value)

    def is_low_battery(self):
        return self.resources.battery < 20

    def is_critical_battery(self):
        return self.resources.battery < 10

    def is_high_storage(self):
        return self.resources.storage >= 80

    def is_critical_storage(self):
        return self.resources.storage >= 90

    def is_low_bandwidth(self):
        return self.resources.bandwidth < 30

    def is_communication_available(self):
        return self.resources.bandwidth > 0

    @staticmethod
    def _clamp(value):

        return max(0.0, min(100.0, float(value)))


if __name__ == "__main__":

    manager = ResourceManager()

    manager.set_battery(8)
    manager.set_storage(95)
    manager.set_cpu(85)
    manager.set_bandwidth(0)

    print("=== CRITICAL RESOURCE SCENARIO ===")

    print(manager.get_state())

    print(
        "Critical battery:",
        manager.is_critical_battery()
    )

    print(
        "Critical storage:",
        manager.is_critical_storage()
    )

    print(
        "Communication available:",
        manager.is_communication_available()
    )