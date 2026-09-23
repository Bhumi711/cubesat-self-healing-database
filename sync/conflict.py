from enum import Enum


class ConflictResolution(Enum):
    ONBOARD_WINS = "ONBOARD_WINS"
    GROUND_WINS = "GROUND_WINS"
    HIGHER_VERSION = "HIGHER_VERSION"
    HIGHER_PRIORITY = "HIGHER_PRIORITY"
    HIGHER_CONFIDENCE = "HIGHER_CONFIDENCE"
    UNRESOLVED = "UNRESOLVED"


class ConflictResolver:

    PRIORITY_LEVELS = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4
    }

    def resolve(self, onboard, ground):

        # -------------------------------------------------
        # No ground record
        # -------------------------------------------------

        if ground is None:
            return {
                "decision": ConflictResolution.ONBOARD_WINS.value,
                "record": onboard,
                "reason": "Record does not exist on ground."
            }

        # -------------------------------------------------
        # Higher version wins
        # -------------------------------------------------

        onboard_version = onboard.get(
            "version",
            1
        )

        ground_version = ground.get(
            "version",
            1
        )

        if onboard_version > ground_version:

            return {
                "decision": ConflictResolution.HIGHER_VERSION.value,
                "record": onboard,
                "reason": (
                    f"Onboard version {onboard_version} "
                    f"is newer than ground version "
                    f"{ground_version}."
                )
            }

        if ground_version > onboard_version:

            return {
                "decision": ConflictResolution.HIGHER_VERSION.value,
                "record": ground,
                "reason": (
                    f"Ground version {ground_version} "
                    f"is newer than onboard version "
                    f"{onboard_version}."
                )
            }

        # -------------------------------------------------
        # Same version → compare priority
        # -------------------------------------------------

        onboard_priority = self.PRIORITY_LEVELS.get(
            onboard.get("priority", "LOW").upper(),
            1
        )

        ground_priority = self.PRIORITY_LEVELS.get(
            ground.get("priority", "LOW").upper(),
            1
        )

        if onboard_priority > ground_priority:

            return {
                "decision": ConflictResolution.HIGHER_PRIORITY.value,
                "record": onboard,
                "reason": "Onboard record has higher priority."
            }

        if ground_priority > onboard_priority:

            return {
                "decision": ConflictResolution.HIGHER_PRIORITY.value,
                "record": ground,
                "reason": "Ground record has higher priority."
            }

        # -------------------------------------------------
        # Same version + same priority
        # → compare confidence
        # -------------------------------------------------

        onboard_confidence = onboard.get(
            "confidence",
            0.0
        )

        ground_confidence = ground.get(
            "confidence",
            0.0
        )

        if onboard_confidence > ground_confidence:

            return {
                "decision": ConflictResolution.HIGHER_CONFIDENCE.value,
                "record": onboard,
                "reason": "Onboard record has higher confidence."
            }

        if ground_confidence > onboard_confidence:

            return {
                "decision": ConflictResolution.HIGHER_CONFIDENCE.value,
                "record": ground,
                "reason": "Ground record has higher confidence."
            }

        # -------------------------------------------------
        # Nothing clearly wins
        # -------------------------------------------------

        return {
            "decision": ConflictResolution.UNRESOLVED.value,
            "record": None,
            "reason": (
                "Both records have equal version, "
                "priority, and confidence."
            )
        }


if __name__ == "__main__":

    resolver = ConflictResolver()

    print("======================================")
    print("      CONFLICT RESOLUTION TEST")
    print("======================================")

    onboard = {
        "id": 1042,
        "value": 27.4,
        "version": 3,
        "priority": "CRITICAL",
        "confidence": 0.97
    }

    ground = {
        "id": 1042,
        "value": 28.1,
        "version": 2,
        "priority": "HIGH",
        "confidence": 0.72
    }

    result = resolver.resolve(
        onboard,
        ground
    )

    print("\nVersion conflict:")
    print(result)

    onboard = {
        "id": 1050,
        "value": 30.1,
        "version": 3,
        "priority": "CRITICAL",
        "confidence": 0.95
    }

    ground = {
        "id": 1050,
        "value": 29.8,
        "version": 3,
        "priority": "HIGH",
        "confidence": 0.80
    }

    result = resolver.resolve(
        onboard,
        ground
    )

    print("\nPriority conflict:")
    print(result)

    onboard = {
        "id": 1060,
        "value": 27.5,
        "version": 3,
        "priority": "HIGH",
        "confidence": 0.95
    }

    ground = {
        "id": 1060,
        "value": 27.6,
        "version": 3,
        "priority": "HIGH",
        "confidence": 0.70
    }

    result = resolver.resolve(
        onboard,
        ground
    )

    print("\nConfidence conflict:")
    print(result)

    print("\n======================================")
    print("          TEST COMPLETE")
    print("======================================") 