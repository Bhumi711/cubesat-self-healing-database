import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.integrity import calculate_checksum


def test_checksum_is_consistent():
    value = -2857.239501953125

    checksum_1 = calculate_checksum(value)
    checksum_2 = calculate_checksum(value)

    assert checksum_1 == checksum_2


def test_different_values_have_different_checksums():
    value_1 = -2857.239501953125
    value_2 = -2857.23779296875

    checksum_1 = calculate_checksum(value_1)
    checksum_2 = calculate_checksum(value_2)

    assert checksum_1 != checksum_2