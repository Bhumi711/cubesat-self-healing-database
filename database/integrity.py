import hashlib


def calculate_checksum(value):
    value_string = str(value)
    return hashlib.sha256(value_string.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    checksum = calculate_checksum(24.5)
    print("Checksum:", checksum)