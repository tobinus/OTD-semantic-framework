import os
import binascii

class Config(object):
    SECRET_KEY = os.urandom(24).hex()
