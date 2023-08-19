import time


class SnowflakeId:
    EPOCH = 1420041600000  # Custom epoch (in milliseconds)
    WORKER_ID_BITS = 5
    DATA_CENTER_ID_BITS = 5
    SEQUENCE_BITS = 12

    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1
    MAX_DATA_CENTER_ID = (1 << DATA_CENTER_ID_BITS) - 1

    SEQUENCE_MASK = (1 << SEQUENCE_BITS) - 1

    def __init__(self, worker_id, data_center_id):
        if worker_id > SnowflakeId.MAX_WORKER_ID or worker_id < 0:
            raise ValueError(
                f"Worker ID can't be greater than {SnowflakeId.MAX_WORKER_ID} or less than 0"
            )
        if data_center_id > SnowflakeId.MAX_DATA_CENTER_ID or data_center_id < 0:
            raise ValueError(
                f"Data center ID can't be greater than {SnowflakeId.MAX_DATA_CENTER_ID} or less than 0"
            )

        self.worker_id = worker_id
        self.data_center_id = data_center_id
        self.sequence = 0
        self.last_timestamp = -1

    def generate_id(self):
        timestamp = self._current_millis()

        if timestamp < self.last_timestamp:
            raise ValueError("Clock moved backwards. Refusing to generate ID.")

        if timestamp == self.last_timestamp:
            # Within the same millisecond, increment the sequence number
            self.sequence = (self.sequence + 1) & SnowflakeId.SEQUENCE_MASK
            if self.sequence == 0:
                # Sequence exceeds its bit range, wait until the next millisecond
                timestamp = self._wait_next_millis(self.last_timestamp)
        else:
            # New millisecond, reset the sequence number
            self.sequence = 0

        # Update the last timestamp
        self.last_timestamp = timestamp

        # Generate and return the final ID
        return (
            (
                (timestamp - SnowflakeId.EPOCH)
                << (
                    SnowflakeId.WORKER_ID_BITS
                    + SnowflakeId.SEQUENCE_BITS
                    + SnowflakeId.DATA_CENTER_ID_BITS
                )
            )
            | (
                self.data_center_id
                << (SnowflakeId.SEQUENCE_BITS + SnowflakeId.WORKER_ID_BITS)
            )
            | (self.worker_id << SnowflakeId.SEQUENCE_BITS)
            | self.sequence
        )

    def _current_millis(self):
        return round(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp):
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp
