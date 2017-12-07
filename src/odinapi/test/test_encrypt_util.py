import unittest

from odinapi.utils import encrypt_util


class TestEncryptUtil(unittest.TestCase):

    def test_encrypt_decrypt(self):
        """Test encrypt/decrypt of string"""
        for i in (15, 16, 17):
            self.assertEqual(
                encrypt_util.decrypt(encrypt_util.encrypt('X'*i)), 'X'*i)

    def test_encode_decode_level2_param(self):
        """Test encode/decode of level2 post url parameter"""
        args = (7014791071, 1, 'myproject')
        s = encrypt_util.encode_level2_target_parameter(*args)
        self.assertEqual(encrypt_util.decode_level2_target_parameter(s), args)
