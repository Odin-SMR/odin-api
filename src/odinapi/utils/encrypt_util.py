import os
import json
import base64
from Crypto.Cipher import AES


SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
)


def encrypt(msg):
    msg = msg + ' '*(16 - (len(msg) % 16 or 16))
    cipher = AES.new(SECRET_KEY.encode(), AES.MODE_ECB)
    return base64.urlsafe_b64encode(
        cipher.encrypt(msg.encode())
    ).decode()


def decrypt(msg):
    cipher = AES.new(SECRET_KEY.encode(), AES.MODE_ECB)
    return cipher.decrypt(
        base64.urlsafe_b64decode(msg.encode())
    ).decode().strip()


def encode_level2_target_parameter(scanid, freqmode, project):
    """Return encrypted string from scanid and freqmode to be used as
    parameter in a level2 post url
    """
    data = {'ScanID': scanid, 'FreqMode': freqmode, 'Project': project}
    return encrypt(json.dumps(data))


def decode_level2_target_parameter(param):
    """Decrypt and return scan id and freq mode from a level2 post url
    parameter.
    """
    data = json.loads(decrypt(param))
    return data['ScanID'], data['FreqMode'], data['Project']
