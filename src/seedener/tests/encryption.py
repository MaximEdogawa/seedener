import os
import struct
import hashlib
import base64
from Crypto.Cipher import AES

def derive_key_and_iv(password, salt, key_length, iv_length):
    d = d_i = b''
    if type(password)==str:
        password=password.encode('utf-8')
    while len(d) < key_length + iv_length:
        d_i = hashlib.sha256(d_i + password + salt).digest()
        d += d_i
    return d[:key_length], d[key_length:key_length+iv_length]

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

    return decrypted.decode('utf-8')

plaintext = "This is the plaintext message."
ciphertext = encrypt_string(plaintext, "password")
decrypted_text = decrypt_string(ciphertext, "password")

print(f"Plaintext: {plaintext}")
print(f"Ciphertext: {ciphertext}")
print(f"Decrypted Text: {decrypted_text}")