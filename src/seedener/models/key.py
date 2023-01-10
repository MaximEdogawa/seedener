import unicodedata
import subprocess
import hashlib

# Hsms Command-line Commands:
HSMGEN = "hsmgen" #Keys generate
HSMPK = "hsmpk" #Derive public key

# Hashing Const
PBKDF2_ROUNDS = 2048
 
class InvalidKeyException(Exception):
    pass

class Key:
    def __init__(self, secretComponent: str = None, passphrase: str = "") -> None:
        if not secretComponent:
             raise Exception("Must initialize a Key with a secretComponent.")

        self._passphrase: str = ""
        self.set_passphrase(passphrase, regenerate_key=False)

        self.key_bytes: bytes = None
        self.pub_key: str = ""

        self._generate_key()
        
        
    def _generate_key(self) -> bool:
        try:
            output = subprocess.Popen(HSMGEN, shell = True, stdout=subprocess.PIPE).stdout.read()
            commadPubGen = HSMPK + " " + output.decode()
            self.key_bytes = hashlib.pbkdf2_hmac(
                "sha512",
                output.decode().encode("utf-8"),
                self._passphrase.encode("utf-8"),
                PBKDF2_ROUNDS,
                64,
            )
            self.pub_key = subprocess.Popen(commadPubGen, shell = True, stdout=subprocess.PIPE).stdout.read().decode()        
        except Exception as e:
            print(repr(e))
            raise InvalidKeyException(repr(e))


    @property
    def passphrase(self):
        return self._passphrase

    @property
    def passphrase_display(self):
        return unicodedata.normalize("NFC", self._passphrase)
    
    def set_passphrase(self, passphrase: str, regenerate_key: bool = True):
        if passphrase:
            self._passphrase = unicodedata.normalize("NFKD", passphrase)
        else:
            # Passphrase must always have a string value, even if it's just the empty
            # string.
            self._passphrase = ""

        if regenerate_key:
            # Regenerate the internal key since passphrase changes the result
            self._generate_key()
    
    def encodeKey(self, password: str = ""):
        return 

    def get_fingerprint(self) -> str:
        return self.key_bytes

    def get_pub(self):
        return self.pub_key

    ### override operators    
    def __eq__(self, other):
        if isinstance(other, Key):
            return self.key_bytes == other.key_bytes
        return False