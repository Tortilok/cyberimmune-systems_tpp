import base64

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


# Шифратор
class AESCipher(object):
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = key.encode('utf-8')

    def encrypt(self, raw):
        raw = pad(raw.encode(), self.bs)
        iv = self.key[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[self.bs:])).decode('utf-8')

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]