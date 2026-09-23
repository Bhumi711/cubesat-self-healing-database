from enum import Enum

from database.db import get_connection
from simulation.resources import ResourceManager


class Priority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriorityEngine:

    CRITICAL_SENSORS = {
        "battery",
        "power",
        "voltage",
        "current",
    }

    HIGH_SENSORS = {
        "temperature",
        "pressure",
        "attitude",
        "gyroscope",
        "accelerometer",
    }

    def calculate_score(
        self,
        sensor,
        parameter,
        mission_phase="NOMINAL",
        status="VALID",
        anomaly=False
    ):
        score = 0

        sensor_name = sensor.lower()
        parameter_name = parameter.lower()
        phase = mission_phase.upper()
        record_status = status.upper()

        # Sensor importance
        if (
            sensor_name in self.CRITICAL_SENSORS
            or parameter_name in self.CRITICAL_SENSORS
        ):
            score += 70

        elif (
            sensor_name in self.HIGH_SENSORS
            or parameter_name in self.HIGH_SENSORS
        ):
            score += 40

        # Anomaly detected
        if anomaly:
            score += 40

        # Current telemetry status
        if record_status == "ANOMALY":
            score += 40

        elif record_status == "RECOVERED":
            score += 30

        elif record_status == "UNCERTAIN":
            score += 25

        # Mission phase
        if phase == "ANOMALY_INVESTIGATION":
            score += 20

        elif phase == "RECOVERY":
            score += 20

        elif phase == "SAFE_MODE":
            score += 20

        return score

    def get_priority(self, score):

        if score >= 70:
            return Priority.CRITICAL

        elif score >= 40:
            return Priority.HIGH

        elif score >= 20:
            return Priority.MEDIUM

        return Priority.LOW

    def calculate_resource_adjustment(
        self,
        priority,
        resources
    ):
        adjustment = 0

        battery = resources.get("battery", 100)
        storage = resources.get("storage", 0)
        bandwidth = resources.get("bandwidth", 100)

        # Low battery:
        # prioritize important telemetry.
        if battery < 20:

            if priority == Priority.CRITICAL.value:
                adjustment += 20

            elif priority == Priority.HIGH.value:
                adjustment += 10

        # High storage usage:
        # low-priority data becomes less urgent.
        if storage >= 90:

            if priority == Priority.LOW.value:
                adjustment -= 10

            elif priority == Priority.MEDIUM.value:
                adjustment -= 5

        # Low bandwidth:
        # prioritize important records for transmission.
        if bandwidth < 30:

            if priority == Priority.CRITICAL.value:
                adjustment += 20

            elif priority == Priority.HIGH.value:
                adjustment += 10

        return adjustment

    def evaluate(
        self,
        sensor,
        parameter,
        mission_phase="NOMINAL",
        status="VALID",
        anomaly=False,
        resources=None
    ):

        base_score = self.calculate_score(
            sensor=sensor,
            parameter=parameter,
            mission_phase=mission_phase,
            status=status,
            anomaly=anomaly
        )

        base_priority = self.get_priority(base_score)

        resource_adjustment = 0

        if resources is not None:

            resource_adjustment = (
                self.calculate_resource_adjustment(
                    priority=base_priority.value,
                    resources=resources
                )
            )

        final_score = max(
            0,
            base_score + resource_adjustment
        )

        final_priority = self.get_priority(final_score)

        return {
            "base_score": base_score,
            "resource_adjustment": resource_adjustment,
            "score": final_score,
            "priority": final_priority.value
        }

    def update_database_priority(
        self,
        telemetry_id,
        anomaly=False,
        resources=None
    ):

        connection = get_connection()

        row = connection.execute(
            """
            SELECT sensor,
                   parameter,
                   mission_phase,
                   status
            FROM telemetry
            WHERE id = ?
            """,
            (telemetry_id,)
        ).fetchone()

        if row is None:

            connection.close()

            raise ValueError(
                f"Telemetry record {telemetry_id} not found"
            )

        sensor, parameter, mission_phase, status = row

        result = self.evaluate(
            sensor=sensor,
            parameter=parameter,
            mission_phase=mission_phase,
            status=status,
            anomaly=anomaly,
            resources=resources
        )

        connection.execute(
            """
            UPDATE telemetry
            SET priority = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                result["priority"],
                telemetry_id
            )
        )

        connection.commit()
        connection.close()

        return result


if __name__ == "__main__":

    engine = PriorityEngine()

    resources = ResourceManager()

    print("======================================")
    print("       PRIORITY ENGINE TEST")
    print("======================================")

    print("\n--- NORMAL CONDITIONS ---")

    result = engine.evaluate(
        sensor="temperature",
        parameter="temperature",
        mission_phase="NOMINAL",
        status="VALID",
        anomaly=False,
        resources=resources.get_state()
    )

    print(result)

    print("\n--- BATTERY TELEMETRY ---")

    result = engine.evaluate(
        sensor="battery",
        parameter="voltage",
        mission_phase="NOMINAL",
        status="VALID",
        anomaly=False,
        resources=resources.get_state()
    )

    print(result)

    print("\n--- ANOMALY INVESTIGATION ---")

    result = engine.evaluate(
        sensor="temperature",
        parameter="temperature",
        mission_phase="ANOMALY_INVESTIGATION",
        status="ANOMALY",
        anomaly=True,
        resources=resources.get_state()
    )

    print(result)

    print("\n--- CRITICAL RESOURCE CONDITIONS ---")

    resources.set_battery(8)
    resources.set_storage(95)
    resources.set_bandwidth(10)

    print("Resources:")
    print(resources.get_state())

    result = engine.evaluate(
        sensor="temperature",
        parameter="temperature",
        mission_phase="ANOMALY_INVESTIGATION",
        status="ANOMALY",
        anomaly=True,
        resources=resources.get_state()
    )

    print("\nTemperature anomaly:")
    print(result)

    print("\n--- LOW PRIORITY PAYLOAD ---")

    result = engine.evaluate(
        sensor="payload",
        parameter="image",
        mission_phase="NOMINAL",
        status="VALID",
        anomaly=False,
        resources=resources.get_state()
    )

    print(result)

    print("\n======================================")
    print("          TEST COMPLETE")
    print("======================================")