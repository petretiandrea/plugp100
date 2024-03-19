from plugp100.encryption import helpers


class LoginDeviceParams(object):
    password: str
    username: str

    def __init__(self, username: str, password: str):
        digest_username = helpers.sha1_from_str(username)
        self.username = helpers.base64encode(digest_username)
        self.password = helpers.base64encode(password)


class LoginDeviceParamsV2(object):
    password2: str
    username: str

    def __init__(self, username: str, password: str):
        self.username = helpers.base64encode(helpers.sha1_from_str(username))
        self.password2 = helpers.base64encode(helpers.sha1_from_str(password))
