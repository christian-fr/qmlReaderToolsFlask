import argparse
import os
import base64
import math
import hashlib
import getpass


def hash_salt_password(password, n: int = 16384, r: int = 16, p: int = 16) -> str:
    version = "s0"
    salt = base64.b64encode(os.urandom(16))
    try:
        n_param = math.log2(n)
        assert n_param.is_integer()
    except AssertionError:
        raise AssertionError(f'Argument "n" must have a base of 2.')
    passwd_hash_str = base64.b64encode(
        hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32, maxmem=2 ** 30))
    n_param_int = int(n_param)
    params_str = "{0:x}".format(((n_param_int & 65535) << 16) + ((r & 255) << 8) + (p & 255))
    return '$' + '$'.join((version, params_str, base64.b64encode(salt).decode(), passwd_hash_str.decode()))


def verify_password(password: str, password_check: str) -> bool:
    parts = password_check.split("$")
    allowed_versions = ['s0']
    try:
        assert parts[1] in allowed_versions
    except AssertionError:
        raise AssertionError(f'wrong version! found: {parts[1]}; but should be one of: {allowed_versions}')
    params = int(parts[2], 16)
    n = int(math.pow(2.0, float((params >> 16 & 65535))))
    r = int(params >> 8 & 255)
    p = int(params & 255)
    salt = base64.b64decode(parts[3])
    decoded_hash = base64.b64decode(parts[4])
    result = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32, maxmem=2 ** 30)
    return decoded_hash == result


if __name__ == '__main__':
    #parser = argparse.ArgumentParser(
    #    description="Helper program to generate hashed and salted password (bcrypt).")
    #parser.add_argument('password', help='The password string')

    # password_clear = "pass123"
    #args = parser.parse_args()
    print(hash_salt_password(getpass.getpass()))
    # print(verify_password(password_clear, pass_hash_salted))
