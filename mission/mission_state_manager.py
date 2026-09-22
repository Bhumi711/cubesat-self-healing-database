from enum import Enum
from database.db import get_connection


class MissionState(Enum):
    NOMINAL = "NOMINAL"
    ANOMALY_INVESTIGATION = "ANOMALY_INVESTIGATION"
    RECOVERY = "RECOVERY"
    SAFE_MODE = "SAFE_MODE"


class MissionStateManager:

    def __init__(self):
        self.current_state = MissionState.NOMINAL

    def get_state(self):
        return self.current_state

    def set_state(self, new_state):

        if not isinstance(new_state, MissionState):
            raise ValueError("Invalid mission state")

        old_state = self.current_state
        self.current_state = new_state

        self._update_database()

        return old_state, new_state

    def _update_database(self):

        connection = get_connection()

        connection.execute(
            """
            UPDATE telemetry
            SET mission_phase = ?,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.current_state.value,)
        )

        connection.commit()
        connection.close()

    def enter_anomaly_investigation(self):
        return self.set_state(
            MissionState.ANOMALY_INVESTIGATION
        )

    def enter_recovery(self):
        return self.set_state(
            MissionState.RECOVERY
        )

    def enter_safe_mode(self):
        return self.set_state(
            MissionState.SAFE_MODE
        )

    def return_to_nominal(self):
        return self.set_state(
            MissionState.NOMINAL
        )


if __name__ == "__main__":

    manager = MissionStateManager()

    print("Current state:", manager.get_state().value)

    old_state, new_state = manager.enter_anomaly_investigation()
    print(
        f"State change: "
        f"{old_state.value} → {new_state.value}"
    )

    old_state, new_state = manager.enter_recovery()
    print(
        f"State change: "
        f"{old_state.value} → {new_state.value}"
    )

    old_state, new_state = manager.return_to_nominal()
    print(
        f"State change: "
        f"{old_state.value} → {new_state.value}"
    )