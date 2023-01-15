import unicodedata
import subprocess
import hashlib
from binascii import hexlify

# Hsms Command-line Commands:
HSMGEN = "hsmgen" #Keys generate
HSMPK = "hsmpk" #Derive public key

# Hashing Const
PBKDF2_ROUNDS = 2048
 
class InvalidKeyException(Exception):
    pass

class Key:
    def __init__(self, passphrase: str = "") -> None:
        self._passphrase: str = ""
        self.isPassphraseSet: bool = False
        self.key_hash_bytes: bytes = None
        self.priv_key: str = ""
        self.pub_key: str = ""
        self.set_passphrase(passphrase, paswordProtect=False)
        self._generate_key()
        
    def _generate_key(self) -> bool:
        try:
            self.priv_key = subprocess.Popen(HSMGEN, shell = True, stdout=subprocess.PIPE).stdout.read().decode()
            commadPubGen = HSMPK + " " + self.priv_key
            self.pub_key = subprocess.Popen(commadPubGen, shell = True, stdout=subprocess.PIPE).stdout.read().decode()
            self.key_hash_bytes = hashlib.pbkdf2_hmac(
                "sha512",
                self.priv_key.encode("utf-8"),
                self.passphrase.encode("utf-8"),
                PBKDF2_ROUNDS,
                64,
            )     
        except Exception as e:
            print(repr(e))
            raise InvalidKeyException(repr(e))
    
    def get_private(self, passphrase: str = ""):
        check_hash = hashlib.pbkdf2_hmac(
                "sha512",
                self.priv_key.encode("utf-8"),
                passphrase.encode("utf-8"),
                PBKDF2_ROUNDS,
                64,
            )
        if(check_hash==self.key_hash_bytes):
            return self.priv_key
        else:
            return ""

    def get_pub(self):
        return self.pub_key

    def get_fingerprint(self):
        return hexlify(self.key_hash_bytes).decode('utf-8')

    def getIsPassphraseSet(self):
        return self.isPassphraseSet

    @property
    def passphrase(self):
        return self._passphrase

    @property
    def passphrase_display(self):
        return unicodedata.normalize("NFC", self._passphrase)

    def set_passphrase(self, passphrase: str, paswordProtect: bool = True):
        
        if passphrase:
            self.isPassphraseSet=True
            self._passphrase = unicodedata.normalize("NFKD", passphrase)
        else:
            # Passphrase must always have a string value, even if it's just the empty
            # string.
            self.isPassphraseSet=False
            self._passphrase = ""

        if paswordProtect:
            # Regenerate the internal key since passphrase changes the result
            self._generate_hash()

    def _generate_hash(self) -> bool:
        try:
            self.key_hash_bytes = hashlib.pbkdf2_hmac(
                "sha512",
                self.priv_key.encode("utf-8"),
                self.passphrase.encode("utf-8"),
                PBKDF2_ROUNDS,
                64,
            )
        except Exception as e:
            print(repr(e))
            raise InvalidKeyException(repr(e))

    ### override operators    
    def __eq__(self, other):
        if isinstance(other, Key):
            return self.priv_key == other.priv_key
        return False