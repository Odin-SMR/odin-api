import json
import base64
from Crypto.Cipher import AES

# TODO: Get secret from environ
SECRET_KEY = '***REMOVED***'


def encrypt(msg):
    msg = msg + ' '*(16 - (len(msg) % 16 or 16))
    print len(msg)
    cipher = AES.new(SECRET_KEY, AES.MODE_ECB)
    return base64.urlsafe_b64encode(cipher.encrypt(msg))


def decrypt(msg):
    cipher = AES.new(SECRET_KEY, AES.MODE_ECB)
    return cipher.decrypt(base64.urlsafe_b64decode(msg)).strip()


def encode_level2_target_parameter(scanid, freqmode):
    """Return encrypted string from scanid and freqmode to be used as
    parameter in a level2 post url
    """
    data = {'ScanID': scanid, 'FreqMode': freqmode}
    return encrypt(json.dumps(data))


def decode_level2_target_parameter(param):
    """Decrypt and return scan id and freq mode from a level2 post url
    parameter.
    """
    data = json.loads(decrypt(param))
    return data['ScanID'], data['FreqMode']
