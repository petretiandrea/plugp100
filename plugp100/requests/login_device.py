from plugp100.encryption import helpers


class LoginDeviceParams(object):
    password: str
    username: str

    def __init__(self, username: str, password: str):
        digest_username = helpers.sha1(username)
        self.username = helpers.base64encode(digest_username)
        self.password = helpers.base64encode(password)
