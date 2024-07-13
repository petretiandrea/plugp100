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


class LoginDeviceParamsH200(object):
    encrypt_type: str
    username: str
    cnonce: str
    password: str
    hashed: bool
    digest_passwd: str

    def __init__(self, cnonce, password, hashed, digest_passwd):
        self.username = "admin"
        if password is None:
            self.encrypt_type = "3"
        if cnonce is not None:
            self.cnonce = cnonce
        if password is not None:
            self.password = password
        if hashed is not None:
            self.hashed = hashed
        if digest_passwd is not None:
            self.digest_passwd = digest_passwd
