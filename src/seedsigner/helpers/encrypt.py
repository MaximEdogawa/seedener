import os
import struct
import hashlib
import base64
from Crypto.Cipher import AES
from seedsigner.models.qr_type import QRType 

# Render bytes for AES encrytpion
RENDER_BYTES=16
class Encrypt:
    #TODO: Review code for safety
    @staticmethod
    def encrypt_string(plaintext, password, key_length=32):
        bs = AES.block_size
        salt = os.urandom(bs - len('Salted__'))
        key, iv = derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES.new(key, AES.MODE_CBC, iv)

        if type(plaintext)==str:
            plaintext = plaintext.encode('utf-8')

        padding_length = bs - len(plaintext) % bs 
        plaintext += padding_length * struct.pack('b', padding_length)
        encrypted = cipher.encrypt(plaintext)

        return 'Salted__' + base64.b64encode(salt + encrypted).decode('utf-8')

    @staticmethod
    def decrypt_string(ciphertext, password, key_length=32):
        bs = AES.block_size
        ciphertext = base64.b64decode(ciphertext[len('Salted__'):].encode('utf-8'))
        salt = ciphertext[:bs - len('Salted__')]
        ciphertext = ciphertext[bs - len('Salted__'):]
        key, iv = derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        padding_length = struct.unpack('b', decrypted[-1:])[0]
        decrypted = decrypted[:-padding_length]
        #TODO Rereview if there is a better way to recognize correct decryption
        substring : str = QRType.SECRECT_COMPONENT
        if decrypted.find(substring.encode()) != -1:
            return decrypted.decode('utf-8')
        else:
            return ""

def derive_key_and_iv(password, salt, key_length, iv_length):
    d = d_i = b''
    if type(password)==str:
        password=password.encode('utf-8')
    while len(d) < key_length + iv_length:
        d_i = hashlib.sha256(d_i + password + salt).digest()
        d += d_i
    return d[:key_length], d[key_length:key_length+iv_length]