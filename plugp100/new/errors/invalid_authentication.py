class InvalidAuthentication(Exception):
    def __init__(self, host: str, device_type: str):
        super().__init__(f"Invalid authentication error for ${host}, ${device_type}")
