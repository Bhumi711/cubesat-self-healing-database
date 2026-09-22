import sys
from pathlib import Path

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

import streamlit as st
import pandas as pd

from simulation.controller import CubeSatController


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CubeSat Mission Control",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONTROLLER
# ============================================================

@st.cache_resource
def get_controller():
    return CubeSatController()


controller = get_controller()


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #0b0f14;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1550px;
}

h1, h2, h3 {
    color: #f8fafc;
}

.mission-banner {
    background-color: #111820;
    border: 1px solid #26313d;
    border-radius: 16px;
    padding: 25px;
    margin-bottom: 25px;
}

.metric-card {
    background-color: #111820;
    border: 1px solid #26313d;
    border-radius: 14px;
    padding: 20px;
}

.demo-box {
    background-color: #111820;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px;
}

.small-text {
    color: #94a3b8;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.title("🛰️ CubeSat Self-Healing Mission Control")

st.caption(
    "Autonomous telemetry monitoring • anomaly detection • "
    "priority management • recovery • adaptive compression • "
    "DTN synchronization"
)


# ============================================================
# SYSTEM STATUS
# ============================================================

status = controller.get_system_status()

mission_state = status["mission_state"]

telemetry_status = status["telemetry"]

resource_status = status["resources"]

communication_status = status["communication"]

resources = resource_status["resources"]


# ============================================================
# TOP STATUS
# ============================================================

st.subheader("Mission Status")

status_col1, status_col2, status_col3, status_col4 = (
    st.columns(4)
)


with status_col1:

    st.metric(
        "Mission State",
        mission_state
    )


with status_col2:

    st.metric(
        "Active Anomalies",
        telemetry_status["anomalies"]
    )


with status_col3:

    st.metric(
        "Critical Telemetry",
        telemetry_status["critical"]
    )


with status_col4:

    st.metric(
        "Communication",
        "ONLINE"
        if communication_status["connected"]
        else "OFFLINE"
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Mission Controls")

    st.divider()

    # ========================================================
    # MISSION STATE
    # ========================================================

    st.subheader("Mission State")

    selected_state = st.selectbox(
        "Set mission state",
        [
            "NOMINAL",
            "ANOMALY_INVESTIGATION",
            "RECOVERY",
            "SAFE_MODE"
        ]
    )

    if st.button(
        "Apply Mission State",
        use_container_width=True
    ):

        try:

            controller.set_mission_state(
                selected_state
            )

            st.success(
                f"State changed to {selected_state}"
            )

            st.rerun()

        except Exception as error:

            st.error(str(error))


    st.divider()

    # ========================================================
    # COMMUNICATION
    # ========================================================

    st.subheader("Communication")

    if communication_status["connected"]:

        if st.button(
            "Simulate Communication Blackout",
            use_container_width=True
        ):

            controller.simulate_blackout()

            st.warning(
                "Communication link is offline."
            )

            st.rerun()

    else:

        if st.button(
            "Restore Communication",
            use_container_width=True
        ):

            controller.restore_connection()

            st.success(
                "Communication restored."
            )

            st.rerun()


    st.divider()

    # ========================================================
    # RESOURCE SIMULATION
    # ========================================================

    st.subheader("Resource Simulation")

    battery = st.slider(
        "Battery %",
        0.0,
        100.0,
        float(resources["battery"])
    )

    storage = st.slider(
        "Storage %",
        0.0,
        100.0,
        float(resources["storage"])
    )

    cpu = st.slider(
        "CPU %",
        0.0,
        100.0,
        float(resources["cpu"])
    )

    bandwidth = st.slider(
        "Bandwidth %",
        0.0,
        100.0,
        float(resources["bandwidth"])
    )

    if st.button(
        "Apply Resources",
        use_container_width=True
    ):

        controller.set_battery(battery)
        controller.set_storage(storage)
        controller.set_cpu(cpu)
        controller.set_bandwidth(bandwidth)

        st.success(
            "Resources updated."
        )

        st.rerun()


    st.divider()

    if st.button(
        "Refresh Dashboard",
        use_container_width=True
    ):

        st.rerun()


# ============================================================
# AUTONOMOUS SELF-HEALING
# ============================================================

st.divider()

st.header("🚨 Autonomous Self-Healing Demonstration")

st.write(
    "Deliberately corrupt a telemetry value and let the "
    "mission controller detect, prioritize, recover, "
    "version, and log the fault."
)


# ============================================================
# TELEMETRY
# ============================================================

telemetry = controller.get_telemetry()


if telemetry:

    demo_col1, demo_col2 = st.columns(2)


    with demo_col1:

        telemetry_options = {
            (
                f"ID {record['id']} — "
                f"{record['sensor']} / "
                f"{record['parameter']} — "
                f"{record['value']}"
            ):
                record["id"]

            for record in telemetry
        }

        selected_demo_label = st.selectbox(
            "Telemetry record for fault simulation",
            list(telemetry_options.keys()),
            key="demo_record"
        )

        selected_demo_id = telemetry_options[
            selected_demo_label
        ]


    with demo_col2:

        fault_type = st.selectbox(
            "Fault type",
            [
                "EXTREME_VALUE",
                "NEGATIVE_VALUE",
                "VALUE_OFFSET"
            ],
            key="demo_fault_type"
        )


    if st.button(
        "🚨 SIMULATE SATELLITE FAULT",
        use_container_width=True,
        type="primary"
    ):

        try:

            with st.spinner(
                "Running autonomous self-healing cycle..."
            ):

                result = controller.run_fault_recovery_demo(
                    telemetry_id=selected_demo_id,
                    fault_type=fault_type
                )

            st.session_state["last_demo_result"] = result

            if result["success"]:

                st.success(
                    "Self-healing cycle completed successfully."
                )

            else:

                st.warning(
                    result["message"]
                )

        except Exception as error:

            st.error(
                f"Self-healing cycle failed: {error}"
            )


# ============================================================
# SELF-HEALING RESULT
# ============================================================

if "last_demo_result" in st.session_state:

    result = st.session_state["last_demo_result"]

    st.divider()

    st.header("Self-Healing Event")

    if result.get("success"):

        detection = result["detection"]

        fault = result["fault"]

        recovery = result["recovery"]["recovery"]


        step1, step2, step3, step4, step5 = (
            st.columns(5)
        )


        with step1:

            st.metric(
                "⚠️ Fault",
                f"{fault['corrupted_value']:.3f}"
            )

            st.caption(
                "Corrupted value"
            )


        with step2:

            st.metric(
                "🔍 Detection",
                "ANOMALY"
                if detection["anomaly"]
                else "NORMAL"
            )

            st.caption(
                "Anomaly detector"
            )


        with step3:

            st.metric(
                "🚨 Priority",
                result["priority"]["priority"]
            )

            st.caption(
                f"Score: "
                f"{result['priority']['score']}"
            )


        with step4:

            st.metric(
                "🔧 Recovery",
                f"{recovery['recovered_value']:.3f}"
            )

            st.caption(
                recovery["recovery_method"]
            )


        with step5:

            st.metric(
                "✅ Version",
                recovery["new_version"]
            )

            st.caption(
                "Recovered telemetry"
            )


        st.success(
            f"Recovery method: "
            f"{recovery['recovery_method']} | "
            f"Confidence: "
            f"{recovery['confidence']:.0%}"
        )


        with st.expander(
            "View complete self-healing event"
        ):

            st.json(result)

    else:

        st.warning(
            result.get(
                "message",
                "Self-healing demonstration did not complete."
            )
        )


# ============================================================
# SYSTEM RESOURCES
# ============================================================

st.divider()

st.header("System Resources")

resource_col1, resource_col2, resource_col3, resource_col4 = (
    st.columns(4)
)


with resource_col1:

    st.metric(
        "Battery",
        f"{resources['battery']:.1f}%"
    )

    st.progress(
        resources["battery"] / 100
    )


with resource_col2:

    st.metric(
        "Storage",
        f"{resources['storage']:.1f}%"
    )

    st.progress(
        resources["storage"] / 100
    )


with resource_col3:

    st.metric(
        "CPU",
        f"{resources['cpu']:.1f}%"
    )

    st.progress(
        resources["cpu"] / 100
    )


with resource_col4:

    st.metric(
        "Bandwidth",
        f"{resources['bandwidth']:.1f}%"
    )

    st.progress(
        resources["bandwidth"] / 100
    )


# ============================================================
# RESOURCE ALERTS
# ============================================================

alerts = []


if resource_status["critical_battery"]:

    alerts.append(
        "CRITICAL — Battery below 10%"
    )

elif resource_status["low_battery"]:

    alerts.append(
        "WARNING — Battery below 20%"
    )


if resource_status["critical_storage"]:

    alerts.append(
        "CRITICAL — Storage above 90%"
    )

elif resource_status["high_storage"]:

    alerts.append(
        "WARNING — Storage above 80%"
    )


if resource_status["low_bandwidth"]:

    alerts.append(
        "WARNING — Communication bandwidth is low"
    )


if alerts:

    st.subheader("⚠️ Resource Alerts")

    for alert in alerts:

        st.warning(alert)


# ============================================================
# LIVE TELEMETRY
# ============================================================

st.divider()

st.header("Live Telemetry")


if telemetry:

    dataframe = pd.DataFrame(
        telemetry
    )

    display_columns = [
        "id",
        "timestamp",
        "sensor",
        "parameter",
        "value",
        "unit",
        "mission_phase",
        "priority",
        "version",
        "status"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in dataframe.columns
    ]

    dataframe = dataframe[
        available_columns
    ]

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No telemetry records available."
    )


# ============================================================
# TELEMETRY ANALYSIS
# ============================================================

st.divider()

st.header("Telemetry Analysis")


if telemetry:

    telemetry_ids = [
        record["id"]
        for record in telemetry
    ]

    selected_id = st.selectbox(
        "Select telemetry record",
        telemetry_ids,
        key="analysis_record"
    )


    process_col1, process_col2, process_col3 = (
        st.columns(3)
    )


    with process_col1:

        if st.button(
            "Process as Normal",
            use_container_width=True
        ):

            try:

                result = controller.process_telemetry(
                    telemetry_id=selected_id,
                    anomaly=False
                )

                st.success(
                    "Telemetry processed."
                )

                st.json(result)

            except Exception as error:

                st.error(str(error))


    with process_col2:

        if st.button(
            "Mark as Anomaly",
            use_container_width=True
        ):

            try:

                result = controller.process_telemetry(
                    telemetry_id=selected_id,
                    anomaly=True
                )

                st.error(
                    "Telemetry marked as anomalous."
                )

                st.json(result)

            except Exception as error:

                st.error(str(error))


    with process_col3:

        if st.button(
            "Recover Telemetry",
            use_container_width=True
        ):

            try:

                result = controller.recover_telemetry(
                    selected_id
                )

                st.success(
                    "Telemetry recovery completed."
                )

                st.json(result)

            except Exception as error:

                st.error(str(error))


# ============================================================
# RECOVERY HISTORY
# ============================================================

st.divider()

st.header("Recovery History")


try:

    recovery_history = (
        controller.get_recovery_history()
    )

    if recovery_history:

        recovery_dataframe = pd.DataFrame(
            recovery_history
        )

        st.dataframe(
            recovery_dataframe,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No recovery events recorded yet."
        )

except Exception as error:

    st.warning(
        f"Recovery history unavailable: {error}"
    )


# ============================================================
# ADAPTIVE COMPRESSION
# ============================================================

st.divider()

st.header("Adaptive Compression")


if telemetry:

    sensors = sorted(
        set(
            record["sensor"]
            for record in telemetry
        )
    )

    selected_sensor = st.selectbox(
        "Select sensor",
        sensors,
        key="compression_sensor"
    )


    if st.button(
        "Run Adaptive Compression",
        use_container_width=True
    ):

        try:

            result = controller.compress_sensor_data(
                sensor=selected_sensor
            )

            compression_col1, compression_col2, compression_col3 = (
                st.columns(3)
            )


            with compression_col1:

                st.metric(
                    "Compression Mode",
                    result["mode"]
                )


            with compression_col2:

                st.metric(
                    "Original Size",
                    f"{result['original_size']} B"
                )


            with compression_col3:

                st.metric(
                    "Compressed Size",
                    f"{result['compressed_size']} B"
                )


            st.info(
                f"Compression ratio: "
                f"{result['compression_ratio']:.3f}"
            )


        except Exception as error:

            st.error(str(error))


# ============================================================
# DTN SYNCHRONIZATION
# ============================================================

st.divider()

st.header("DTN Synchronization")


dtn_col1, dtn_col2, dtn_col3 = (
    st.columns(3)
)


with dtn_col1:

    st.metric(
        "Communication Link",
        "ONLINE"
        if communication_status["connected"]
        else "OFFLINE"
    )


with dtn_col2:

    st.metric(
        "Pending Records",
        communication_status["pending_records"]
    )


with dtn_col3:

    if st.button(
        "Synchronize",
        use_container_width=True
    ):

        try:

            controller.synchronize()

            st.success(
                "Synchronization complete."
            )

            st.rerun()

        except Exception as error:

            st.error(str(error))


# ============================================================
# MISSION SUMMARY
# ============================================================

st.divider()

st.header("Mission Summary")


summary_col1, summary_col2, summary_col3, summary_col4 = (
    st.columns(4)
)


with summary_col1:

    st.metric(
        "Total Telemetry",
        telemetry_status["total"]
    )


with summary_col2:

    st.metric(
        "Anomalies",
        telemetry_status["anomalies"]
    )


with summary_col3:

    st.metric(
        "Recovered",
        telemetry_status["recovered"]
    )


with summary_col4:

    st.metric(
        "High Priority",
        telemetry_status["high"]
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CubeSat Self-Healing Database • Autonomous Mission Control"
)