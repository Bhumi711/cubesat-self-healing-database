import sys
from pathlib import Path
from statistics import median

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from database.db import get_connection

from mission.mission_state_manager import (
    MissionStateManager,
    MissionState
)

from mission.priority import PriorityEngine

from simulation.resources import ResourceManager

from simulation.fault_injection import FaultInjector

from compression.compressor import CompressionEngine

from sync.dtn import DTNSynchronizer

from anomaly.detector import is_anomaly

from recovery.recovery import (
    recover_telemetry,
    get_recovery_history
)


class CubeSatController:

    def __init__(self):

        self.mission = MissionStateManager()

        self.priority = PriorityEngine()

        self.resources = ResourceManager()

        self.fault_injector = FaultInjector()

        self.compression = CompressionEngine()

        self.dtn = DTNSynchronizer()

    # ========================================================
    # MISSION STATE
    # ========================================================

    def get_mission_state(self):
        return self.mission.get_state().value

    def set_mission_state(self, state):

        if isinstance(state, str):

            try:
                state = MissionState[state.upper()]

            except KeyError:
                raise ValueError(
                    f"Invalid mission state: {state}"
                )

        return self.mission.set_state(state)

    def enter_anomaly_investigation(self):
        return self.mission.enter_anomaly_investigation()

    def enter_recovery(self):
        return self.mission.enter_recovery()

    def enter_safe_mode(self):
        return self.mission.enter_safe_mode()

    def return_to_nominal(self):
        return self.mission.return_to_nominal()

    # ========================================================
    # RESOURCES
    # ========================================================

    def get_resources(self):
        return self.resources.get_state()

    def set_battery(self, value):
        self.resources.set_battery(value)

    def set_storage(self, value):
        self.resources.set_storage(value)

    def set_cpu(self, value):
        self.resources.set_cpu(value)

    def set_bandwidth(self, value):
        self.resources.set_bandwidth(value)

    def consume_battery(self, amount):
        self.resources.consume_battery(amount)

    def consume_storage(self, amount):
        self.resources.consume_storage(amount)

    def release_storage(self, amount):
        self.resources.release_storage(amount)

    def consume_cpu(self, amount):
        self.resources.consume_cpu(amount)

    def get_resource_status(self):

        resources = self.resources.get_state()

        return {
            "resources": resources,
            "low_battery":
                self.resources.is_low_battery(),
            "critical_battery":
                self.resources.is_critical_battery(),
            "high_storage":
                self.resources.is_high_storage(),
            "critical_storage":
                self.resources.is_critical_storage(),
            "low_bandwidth":
                self.resources.is_low_bandwidth(),
            "communication_available":
                self.resources.is_communication_available()
        }

    # ========================================================
    # TELEMETRY
    # ========================================================

    def get_telemetry(self):

        connection = get_connection()

        connection.row_factory = (
            lambda cursor, row: {
                column[0]: row[index]
                for index, column
                in enumerate(cursor.description)
            }
        )

        records = connection.execute(
            """
            SELECT
                id,
                timestamp,
                sensor,
                parameter,
                value,
                unit,
                mission_phase,
                priority,
                checksum,
                version,
                status,
                created_at,
                updated_at
            FROM telemetry
            ORDER BY id
            """
        ).fetchall()

        connection.close()

        return records

    def get_telemetry_record(self, telemetry_id):

        connection = get_connection()

        connection.row_factory = (
            lambda cursor, row: {
                column[0]: row[index]
                for index, column
                in enumerate(cursor.description)
            }
        )

        record = connection.execute(
            """
            SELECT
                id,
                timestamp,
                sensor,
                parameter,
                value,
                unit,
                mission_phase,
                priority,
                checksum,
                version,
                status,
                created_at,
                updated_at
            FROM telemetry
            WHERE id = ?
            """,
            (telemetry_id,)
        ).fetchone()

        connection.close()

        return record

    # ========================================================
    # FAULT INJECTION
    # ========================================================

    def inject_fault(
        self,
        telemetry_id,
        fault_type="EXTREME_VALUE"
    ):

        fault_type = fault_type.upper()

        if fault_type == "EXTREME_VALUE":

            return self.fault_injector.inject_extreme_value(
                telemetry_id=telemetry_id,
                multiplier=10.0
            )

        if fault_type == "NEGATIVE_VALUE":

            return self.fault_injector.inject_negative_fault(
                telemetry_id=telemetry_id
            )

        if fault_type == "VALUE_OFFSET":

            return self.fault_injector.inject_offset(
                telemetry_id=telemetry_id,
                offset=100.0
            )

        raise ValueError(
            f"Unknown fault type: {fault_type}"
        )

    # ========================================================
    # NORMAL VALUES
    # ========================================================

    def get_normal_values(
        self,
        sensor,
        parameter,
        exclude_id=None
    ):

        connection = get_connection()

        if exclude_id is None:

            rows = connection.execute(
                """
                SELECT value
                FROM telemetry
                WHERE sensor = ?
                AND parameter = ?
                AND value IS NOT NULL
                AND status = 'VALID'
                ORDER BY timestamp
                """,
                (
                    sensor,
                    parameter
                )
            ).fetchall()

        else:

            rows = connection.execute(
                """
                SELECT value
                FROM telemetry
                WHERE sensor = ?
                AND parameter = ?
                AND value IS NOT NULL
                AND status = 'VALID'
                AND id != ?
                ORDER BY timestamp
                """,
                (
                    sensor,
                    parameter,
                    exclude_id
                )
            ).fetchall()

        connection.close()

        return [
            float(row[0])
            for row in rows
        ]

    # ========================================================
    # ROBUST ANOMALY DETECTION
    # ========================================================

    @staticmethod
    def robust_anomaly(
        value,
        normal_values
    ):

        if len(normal_values) < 3:
            return False

        value = float(value)

        centre = median(normal_values)

        deviations = [
            abs(x - centre)
            for x in normal_values
        ]

        mad = median(deviations)

        # ----------------------------------------------------
        # Case 1: normal data has almost no variation
        # ----------------------------------------------------

        if mad < 1e-9:

            return abs(value - centre) > 1e-9

        # ----------------------------------------------------
        # Modified Z-score using MAD
        # ----------------------------------------------------

        modified_z_score = (
            0.6745
            * abs(value - centre)
            / mad
        )

        # ----------------------------------------------------
        # Very strong deviation from mission baseline
        # ----------------------------------------------------

        if modified_z_score >= 6.0:
            return True

        # ----------------------------------------------------
        # Relative-value protection
        #
        # Useful for faults such as:
        #
        # normal = 24.5
        # corrupted = 245
        # corrupted = -2350
        # ----------------------------------------------------

        scale = max(
            abs(centre),
            1.0
        )

        relative_difference = (
            abs(value - centre)
            / scale
        )

        if relative_difference >= 5.0:
            return True

        return False

    # ========================================================
    # ANOMALY DETECTION
    # ========================================================

    def detect_telemetry_anomaly(
        self,
        telemetry_id
    ):

        record = self.get_telemetry_record(
            telemetry_id
        )

        if record is None:

            raise ValueError(
                f"Telemetry record {telemetry_id} "
                "not found"
            )

        normal_values = self.get_normal_values(
            sensor=record["sensor"],
            parameter=record["parameter"],
            exclude_id=telemetry_id
        )

        if len(normal_values) < 3:

            return {
                "telemetry_id":
                    telemetry_id,

                "value":
                    record["value"],

                "anomaly":
                    False,

                "reason":
                    "Not enough historical values "
                    "for anomaly detection.",

                "normal_samples":
                    len(normal_values)
            }

        # ----------------------------------------------------
        # Machine-learning detector
        # ----------------------------------------------------

        try:

            isolation_result = bool(
                is_anomaly(
                    record["value"],
                    normal_values
                )
            )

        except Exception:

            isolation_result = False

        # ----------------------------------------------------
        # Robust statistical detector
        # ----------------------------------------------------

        robust_result = self.robust_anomaly(
            record["value"],
            normal_values
        )

        # ----------------------------------------------------
        # Either detector can trigger the anomaly state
        # ----------------------------------------------------

        anomaly = (
            isolation_result
            or robust_result
        )

        if anomaly:

            self._mark_anomaly(
                telemetry_id
            )

        return {
            "telemetry_id":
                telemetry_id,

            "value":
                record["value"],

            "sensor":
                record["sensor"],

            "parameter":
                record["parameter"],

            "anomaly":
                anomaly,

            "isolation_forest":
                isolation_result,

            "robust_statistical_check":
                robust_result,

            "normal_samples":
                len(normal_values)
        }

    # ========================================================
    # ANOMALY STATUS
    # ========================================================

    def _mark_anomaly(self, telemetry_id):

        connection = get_connection()

        connection.execute(
            """
            UPDATE telemetry
            SET
                status = 'ANOMALY',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (telemetry_id,)
        )

        connection.commit()

        connection.close()

    def mark_valid(self, telemetry_id):

        connection = get_connection()

        connection.execute(
            """
            UPDATE telemetry
            SET
                status = 'VALID',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (telemetry_id,)
        )

        connection.commit()

        connection.close()

    # ========================================================
    # PRIORITY
    # ========================================================

    def process_telemetry(
        self,
        telemetry_id,
        anomaly=False
    ):

        record = self.get_telemetry_record(
            telemetry_id
        )

        if record is None:

            raise ValueError(
                f"Telemetry record {telemetry_id} "
                "not found"
            )

        if anomaly:

            self._mark_anomaly(
                telemetry_id
            )

            self.enter_anomaly_investigation()

            record = self.get_telemetry_record(
                telemetry_id
            )

        result = (
            self.priority.update_database_priority(
                telemetry_id=telemetry_id,
                anomaly=anomaly,
                resources=self.resources.get_state()
            )
        )

        return {
            "telemetry_id":
                telemetry_id,

            "sensor":
                record["sensor"],

            "parameter":
                record["parameter"],

            "value":
                record["value"],

            "status":
                record["status"],

            "mission_state":
                self.get_mission_state(),

            "priority":
                result["priority"],

            "score":
                result["score"],

            "base_score":
                result["base_score"],

            "resource_adjustment":
                result["resource_adjustment"]
        }

    # ========================================================
    # RECOVERY
    # ========================================================

    def recover_telemetry(
        self,
        telemetry_id
    ):

        record = self.get_telemetry_record(
            telemetry_id
        )

        if record is None:

            raise ValueError(
                f"Telemetry record {telemetry_id} "
                "not found"
            )

        self.enter_recovery()

        recovery_result = recover_telemetry(
            telemetry_id
        )

        self.return_to_nominal()

        self.priority.update_database_priority(
            telemetry_id=telemetry_id,
            anomaly=False,
            resources=self.resources.get_state()
        )

        return {
            "recovery":
                recovery_result,

            "mission_state":
                self.get_mission_state()
        }

    def get_recovery_history(
        self,
        telemetry_id=None
    ):

        return get_recovery_history(
            telemetry_id
        )

    # ========================================================
    # COMPLETE SELF-HEALING
    # ========================================================

    def run_self_healing_cycle(
        self,
        telemetry_id
    ):

        detection = (
            self.detect_telemetry_anomaly(
                telemetry_id
            )
        )

        if not detection["anomaly"]:

            priority_result = (
                self.priority.update_database_priority(
                    telemetry_id=telemetry_id,
                    anomaly=False,
                    resources=self.resources.get_state()
                )
            )

            return {
                "telemetry_id":
                    telemetry_id,

                "anomaly_detected":
                    False,

                "recovery_performed":
                    False,

                "mission_state":
                    self.get_mission_state(),

                "priority":
                    priority_result["priority"],

                "score":
                    priority_result["score"],

                "message":
                    "Telemetry is within normal range."
            }

        self.enter_anomaly_investigation()

        priority_result = (
            self.priority.update_database_priority(
                telemetry_id=telemetry_id,
                anomaly=True,
                resources=self.resources.get_state()
            )
        )

        recovery_result = self.recover_telemetry(
            telemetry_id
        )

        return {
            "telemetry_id":
                telemetry_id,

            "anomaly_detected":
                True,

            "recovery_performed":
                True,

            "detection":
                detection,

            "priority":
                priority_result,

            "recovery":
                recovery_result,

            "final_mission_state":
                self.get_mission_state(),

            "message":
                "Anomaly detected and telemetry recovered."
        }

    # ========================================================
    # DEMO
    # ========================================================

    def run_fault_recovery_demo(
        self,
        telemetry_id,
        fault_type="EXTREME_VALUE"
    ):

        before = self.get_telemetry_record(
            telemetry_id
        )

        if before is None:

            raise ValueError(
                f"Telemetry record {telemetry_id} "
                "not found"
            )

        # ----------------------------------------------------
        # If this record is already anomalous/recovered,
        # don't keep multiplying the corrupted value.
        # ----------------------------------------------------

        if before["status"] in (
            "ANOMALY",
            "RECOVERED"
        ):

            raise ValueError(
                "This telemetry record has already "
                "participated in a fault event. "
                "Select a fresh telemetry record."
            )

        fault = self.inject_fault(
            telemetry_id=telemetry_id,
            fault_type=fault_type
        )

        after_fault = self.get_telemetry_record(
            telemetry_id
        )

        detection = (
            self.detect_telemetry_anomaly(
                telemetry_id
            )
        )

        if not detection["anomaly"]:

            return {
                "success":
                    False,

                "fault":
                    fault,

                "detection":
                    detection,

                "message":
                    "Fault was injected, but the "
                    "anomaly detector did not classify "
                    "the value as anomalous."
            }

        self.enter_anomaly_investigation()

        priority = (
            self.priority.update_database_priority(
                telemetry_id=telemetry_id,
                anomaly=True,
                resources=self.resources.get_state()
            )
        )

        recovery = self.recover_telemetry(
            telemetry_id
        )

        final_record = (
            self.get_telemetry_record(
                telemetry_id
            )
        )

        return {
            "success":
                True,

            "telemetry_id":
                telemetry_id,

            "before":
                dict(before),

            "fault":
                fault,

            "after_fault":
                dict(after_fault),

            "detection":
                detection,

            "priority":
                priority,

            "recovery":
                recovery,

            "final_record":
                dict(final_record),

            "mission_state":
                self.get_mission_state(),

            "message":
                "Fault detected, prioritized, recovered, "
                "versioned, and returned to nominal."
        }

    # ========================================================
    # PRIORITY REFRESH
    # ========================================================

    def refresh_priorities(self):

        records = self.get_telemetry()

        results = []

        for record in records:

            result = (
                self.priority.update_database_priority(
                    telemetry_id=record["id"],
                    anomaly=(
                        record["status"]
                        == "ANOMALY"
                    ),
                    resources=self.resources.get_state()
                )
            )

            results.append(
                {
                    "telemetry_id":
                        record["id"],

                    "priority":
                        result["priority"],

                    "score":
                        result["score"]
                }
            )

        return results

    # ========================================================
    # COMPRESSION
    # ========================================================

    def get_sensor_values(
        self,
        sensor,
        parameter=None
    ):

        connection = get_connection()

        if parameter is None:

            rows = connection.execute(
                """
                SELECT value
                FROM telemetry
                WHERE sensor = ?
                AND value IS NOT NULL
                ORDER BY timestamp
                """,
                (sensor,)
            ).fetchall()

        else:

            rows = connection.execute(
                """
                SELECT value
                FROM telemetry
                WHERE sensor = ?
                AND parameter = ?
                AND value IS NOT NULL
                ORDER BY timestamp
                """,
                (
                    sensor,
                    parameter
                )
            ).fetchall()

        connection.close()

        return [
            row[0]
            for row in rows
        ]

    def compress_sensor_data(
        self,
        sensor,
        parameter=None,
        priority="MEDIUM",
        anomaly=False
    ):

        values = self.get_sensor_values(
            sensor=sensor,
            parameter=parameter
        )

        if not values:

            raise ValueError(
                "No telemetry values found "
                "for this sensor."
            )

        result = self.compression.compress(
            values=values,
            priority=priority,
            anomaly=anomaly,
            resources=self.resources.get_state()
        )

        return {
            "sensor":
                sensor,

            "parameter":
                parameter,

            "number_of_values":
                len(values),

            "mode":
                result["mode"],

            "original_size":
                result["original_size"],

            "compressed_size":
                result["compressed_size"],

            "compression_ratio":
                result["compression_ratio"]
        }

    # ========================================================
    # DTN
    # ========================================================

    def communication_status(self):
        return self.dtn.get_status()

    def simulate_blackout(self):

        self.dtn.disconnect()

        return {
            "connected":
                self.dtn.is_connected(),

            "status":
                "COMMUNICATION_OFFLINE"
        }

    def restore_connection(self):

        self.dtn.reconnect()

        return {
            "connected":
                self.dtn.is_connected(),

            "status":
                "COMMUNICATION_ONLINE"
        }

    def synchronize(self):

        self.dtn.synchronize()

        return self.dtn.get_status()

    def queue_pending_records(self):

        self.dtn.queue_pending_records()

        return self.dtn.get_pending_records()

    # ========================================================
    # SYSTEM STATUS
    # ========================================================

    def get_system_status(self):

        connection = get_connection()

        telemetry_stats = connection.execute(
        """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'ANOMALY' THEN 1 ELSE 0 END) AS anomalies,
                SUM(CASE WHEN status = 'RECOVERED' THEN 1 ELSE 0 END) AS recovered,
                SUM(CASE WHEN priority = 'CRITICAL' THEN 1 ELSE 0 END) AS critical,
                SUM(CASE WHEN priority = 'HIGH' THEN 1 ELSE 0 END) AS high
            FROM telemetry
            """
        ).fetchone()

        connection.close()

        total, anomaly_count, recovered_count, critical_count, high_count = (
            telemetry_stats
        )

        resources = self.get_resource_status()

        communication = self.communication_status()

        return {
            "mission_state": self.get_mission_state(),

            "telemetry": {
                "total": total or 0,
                "anomalies": anomaly_count or 0,
                "recovered": recovered_count or 0,
                "critical": critical_count or 0,
                "high": high_count or 0,
            },

            "resources": resources,

            "communication": communication,
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    controller = CubeSatController()

    print()
    print("============================================")
    print("       CUBESAT SELF-HEALING CONTROLLER")
    print("============================================")

    print()
    print("Mission state:")
    print(controller.get_mission_state())

    print()
    print("Resources:")
    print(controller.get_resources())

    telemetry = controller.get_telemetry()

    print()
    print(
        "Telemetry records:",
        len(telemetry)
    )

    if telemetry:

        test_record = telemetry[0]

        print()
        print(
            "Testing telemetry ID:",
            test_record["id"]
        )

        print()
        print("Anomaly detection:")

        print(
            controller.detect_telemetry_anomaly(
                test_record["id"]
            )
        )

    print()
    print("============================================")
    print("             TEST COMPLETE")
    print("============================================")