# SeedSaver Recovery Information

Encryption of private key:
- Python hashlib
- PBKDF2_ROUNDS = 2048
- encrypt: hashlib.pbkdf2_hmac("sha512",self.priv_key.encode("utf-8"),passphrase.encode("utf-8"),PBKDF2_ROUNDS,64,)

