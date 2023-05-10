import base64
import hashlib
import os
from typing import Tuple


def b64decode(inp: bytes) -> bytes:
    return base64.b64decode(inp)


def b64encode(inp: bytes) -> bytes:
    return base64.b64encode(inp)


def split_salt_pw(salted_pw: bytes) -> Tuple[bytes, bytes]:
    return salted_pw[:salted_pw.rfind(b'#') + 1], salted_pw[salted_pw.rfind(b'#') + 1:]


def gen_salt(rounds: int = 12, prefix: bytes = b'1a') -> bytes:
    if prefix not in (b'1a'):
        raise ValueError('Prefix not found')
    if rounds < 4 or rounds > 9:
        raise ValueError('Invalid rounds')
    salt = os.urandom(16)
    b64salt = b64encode(salt)[:-2]
    return b'#' + prefix + b'#' + ('%2.2u' % rounds).encode('ascii') + b64salt + b'#'


def hashpass(password: bytes, salt: bytes):
    rounds = int(salt[4:6])
    hashed_pw = hashlib.scrypt(password, salt=salt, n=2 ** rounds, r=4, p=1)
    return hashed_pw


def get_hashed_password(plain_text_password: bytes) -> bytes:
    salt = gen_salt(9)
    hashed_pw = hashpass(password=plain_text_password, salt=salt)
    return salt + b64encode(hashed_pw)


def check_password(plain_text_password: bytes, hashed_password: bytes) -> bool:
    pass


def check_pass(salted_hashed_pw: bytes, plain_text_passw: bytes) -> bool:
    salt, hashed_pw = split_salt_pw(salted_hashed_pw)
    return b64encode(hashpass(password=plain_text_passw, salt=salt)) == hashed_pw


if __name__ == '__main__':
    print(get_hashed_password(b"pass"))
