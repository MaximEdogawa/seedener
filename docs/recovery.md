# SeedSaver Recovery Information

Encryption of private key:
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

Decryption of private key:
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

Derive Key and IV function:
def derive_key_and_iv(password, salt, key_length, iv_length):
    d = d_i = b''
    if type(password)==str:
        password=password.encode('utf-8')
    while len(d) < key_length + iv_length:
        d_i = hashlib.sha256(d_i + password + salt).digest()
        d += d_i
    return d[:key_length], d[key_length:key_length+iv_length]
