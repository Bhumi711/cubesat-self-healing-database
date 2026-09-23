import json
import zlib
from typing import Any


class CompressionEngine:

    def __init__(self):
        self.compression_level = 6

    # ---------------------------------------------------------
    # Basic lossless compression
    # ---------------------------------------------------------

    def compress_raw(self, data: Any):

        serialized = json.dumps(
            data,
            separators=(",", ":")
        ).encode("utf-8")

        compressed = zlib.compress(
            serialized,
            self.compression_level
        )

        return compressed

    def decompress_raw(self, compressed_data):

        decompressed = zlib.decompress(
            compressed_data
        )

        return json.loads(
            decompressed.decode("utf-8")
        )

    # ---------------------------------------------------------
    # Delta encoding
    # ---------------------------------------------------------

    def delta_encode(self, values):

        if not values:
            return []

        deltas = [values[0]]

        for i in range(1, len(values)):
            deltas.append(
                values[i] - values[i - 1]
            )

        return deltas

    def delta_decode(self, deltas):

        if not deltas:
            return []

        values = [deltas[0]]

        for delta in deltas[1:]:
            values.append(
                values[-1] + delta
            )

        return values

    # ---------------------------------------------------------
    # RLE encoding
    # ---------------------------------------------------------

    def rle_encode(self, values):

        if not values:
            return []

        encoded = []

        current = values[0]
        count = 1

        for value in values[1:]:

            if value == current:
                count += 1

            else:
                encoded.append(
                    [current, count]
                )

                current = value
                count = 1

        encoded.append(
            [current, count]
        )

        return encoded

    def rle_decode(self, encoded):

        values = []

        for value, count in encoded:

            values.extend(
                [value] * count
            )

        return values

    # ---------------------------------------------------------
    # Delta + zlib
    # ---------------------------------------------------------

    def compress_delta(self, values):

        deltas = self.delta_encode(values)

        serialized = json.dumps(
            deltas,
            separators=(",", ":")
        ).encode("utf-8")

        return zlib.compress(
            serialized,
            self.compression_level
        )

    def decompress_delta(self, compressed_data):

        decompressed = zlib.decompress(
            compressed_data
        )

        deltas = json.loads(
            decompressed.decode("utf-8")
        )

        return self.delta_decode(deltas)

    # ---------------------------------------------------------
    # RLE + zlib
    # ---------------------------------------------------------

    def compress_rle(self, values):

        encoded = self.rle_encode(values)

        serialized = json.dumps(
            encoded,
            separators=(",", ":")
        ).encode("utf-8")

        return zlib.compress(
            serialized,
            self.compression_level
        )

    def decompress_rle(self, compressed_data):

        decompressed = zlib.decompress(
            compressed_data
        )

        encoded = json.loads(
            decompressed.decode("utf-8")
        )

        return self.rle_decode(encoded)

    # ---------------------------------------------------------
    # Adaptive compression policy
    # ---------------------------------------------------------

    def select_mode(
        self,
        priority="MEDIUM",
        anomaly=False,
        resources=None
    ):

        priority = priority.upper()

        # Never risk special handling of anomalous
        # telemetry. Preserve it using standard
        # lossless compression.
        if anomaly:
            return "LOSSLESS"

        # Critical data should always be preserved
        # without aggressive transformation.
        if priority == "CRITICAL":
            return "LOSSLESS"

        storage = 0

        bandwidth = 100

        if resources is not None:
            storage = resources.get(
                "storage",
                0
            )

            bandwidth = resources.get(
                "bandwidth",
                100
            )

        # High resource pressure:
        # use stronger reversible compression.
        if storage >= 90 or bandwidth < 30:

            if priority == "LOW":
                return "RLE"

            return "DELTA"

        if priority == "HIGH":
            return "DELTA"

        if priority == "MEDIUM":
            return "DELTA"

        if priority == "LOW":
            return "RLE"

        return "LOSSLESS"

    # ---------------------------------------------------------
    # Main adaptive compression function
    # ---------------------------------------------------------

    def compress(
        self,
        values,
        priority="MEDIUM",
        anomaly=False,
        resources=None
    ):

        mode = self.select_mode(
            priority=priority,
            anomaly=anomaly,
            resources=resources
        )

        original_size = len(
            json.dumps(values).encode("utf-8")
        )

        if mode == "LOSSLESS":

            compressed_data = self.compress_raw(
                values
            )

        elif mode == "DELTA":

            compressed_data = self.compress_delta(
                values
            )

        elif mode == "RLE":

            compressed_data = self.compress_rle(
                values
            )

        else:
            raise ValueError(
                f"Unknown compression mode: {mode}"
            )

        compressed_size = len(compressed_data)

        if original_size > 0:

            compression_ratio = (
                compressed_size / original_size
            )

        else:

            compression_ratio = 1.0

        return {
            "data": compressed_data,
            "mode": mode,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio
        }

    # ---------------------------------------------------------
    # Main decompression function
    # ---------------------------------------------------------

    def decompress(
        self,
        compressed_data,
        mode
    ):

        mode = mode.upper()

        if mode == "LOSSLESS":

            return self.decompress_raw(
                compressed_data
            )

        if mode == "DELTA":

            return self.decompress_delta(
                compressed_data
            )

        if mode == "RLE":

            return self.decompress_rle(
                compressed_data
            )

        raise ValueError(
            f"Unknown compression mode: {mode}"
        )

    # ---------------------------------------------------------
    # Verification
    # ---------------------------------------------------------

    def verify(
        self,
        original,
        compressed_data,
        mode
    ):

        recovered = self.decompress(
            compressed_data,
            mode
        )

        return recovered == original


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    engine = CompressionEngine()

    print("======================================")
    print("      ADAPTIVE COMPRESSION TEST")
    print("======================================")

    telemetry = [
        27.1,
        27.2,
        27.3,
        27.4,
        27.5,
        27.6,
        27.7,
        27.8
    ]

    print("\n--- NORMAL TELEMETRY ---")

    result = engine.compress(
        telemetry,
        priority="HIGH",
        anomaly=False,
        resources={
            "battery": 80,
            "storage": 40,
            "bandwidth": 80
        }
    )

    print("Mode:", result["mode"])
    print("Original size:", result["original_size"])
    print("Compressed size:", result["compressed_size"])
    print("Compression ratio:", result["compression_ratio"])

    print(
        "Lossless verification:",
        engine.verify(
            telemetry,
            result["data"],
            result["mode"]
        )
    )

    print("\n--- CRITICAL TELEMETRY ---")

    result = engine.compress(
        telemetry,
        priority="CRITICAL",
        anomaly=False,
        resources={
            "battery": 80,
            "storage": 40,
            "bandwidth": 80
        }
    )

    print("Mode:", result["mode"])
    print("Original size:", result["original_size"])
    print("Compressed size:", result["compressed_size"])

    print(
        "Lossless verification:",
        engine.verify(
            telemetry,
            result["data"],
            result["mode"]
        )
    )

    print("\n--- ANOMALOUS TELEMETRY ---")

    anomalous_data = [
        27.1,
        27.2,
        91.8,
        27.4,
        27.5
    ]

    result = engine.compress(
        anomalous_data,
        priority="CRITICAL",
        anomaly=True,
        resources={
            "battery": 80,
            "storage": 40,
            "bandwidth": 80
        }
    )

    print("Mode:", result["mode"])

    print(
        "Lossless verification:",
        engine.verify(
            anomalous_data,
            result["data"],
            result["mode"]
        )
    )

    print("\n--- RESOURCE CONSTRAINED ---")

    result = engine.compress(
        telemetry,
        priority="LOW",
        anomaly=False,
        resources={
            "battery": 15,
            "storage": 95,
            "bandwidth": 10
        }
    )

    print("Mode:", result["mode"])
    print("Original size:", result["original_size"])
    print("Compressed size:", result["compressed_size"])
    print("Compression ratio:", result["compression_ratio"])

    print(
        "Lossless verification:",
        engine.verify(
            telemetry,
            result["data"],
            result["mode"]
        )
    )

    print("\n======================================")
    print("          TEST COMPLETE")
    print("======================================")