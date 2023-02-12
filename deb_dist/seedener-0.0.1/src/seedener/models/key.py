import unicodedata
import subprocess
import hashlib
from binascii import hexlify
from seedener.helpers.encrypt import Encrypt
# Hsms Command-line Commands:
HSMGEN = "hsmgen" #Keys generate
HSMPK = "hsmpk" #Derive public key

# Hashing Const
PBKDF2_ROUNDS = 2048
 
class InvalidKeyException(Exception):
    pass

class Key:
    def __init__(self, priv_key: str = "", passphrase: str = "") -> None:
        self.paswordProtect: bool = False
        self.key_hash_bytes: bytes = None
        self.priv_key: str = priv_key
        self.pub_key: str = ""
        self.selected: bool = False
        self.is_new:bool=False
        self.encrypted_priv_key = ""
        if(self.priv_key==""):
            self._generate_key(passphrase)

        self._generate_pubKey()
        self._generate_hash(passphrase)
        
    def _generate_key(self, passphrase: str = ""):
        try:
            self.priv_key = subprocess.Popen(HSMGEN, shell = True, stdout=subprocess.PIPE).stdout.read().decode()
            self.is_new=True
        except Exception as e:
            print(repr(e))
            raise InvalidKeyException(repr(e))

    def _generate_pubKey(self):
        try:
            commadPubGen = HSMPK + " " + self.priv_key
            self.pub_key = subprocess.Popen(commadPubGen, shell = True, stdout=subprocess.PIPE).stdout.read().decode()
     
        except Exception as e:
            print(repr(e))
            raise InvalidKeyException(repr(e))


    def _generate_hash(self, passphrase: str = ""):
        try:
            self.key_hash_bytes = hashlib.pbkdf2_hmac(
                "sha512",
                self.priv_key.encode("utf-8"),
                passphrase.encode("utf-8"),
                PBKDF2_ROUNDS,
                64,
            )
        except Exception as e:
            print(repr(e))
            raise InvalidKeyException(repr(e))

    #TODO: review get private key code for security
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
    
    def get_privateKey_forSigning(self):
        return self.priv_key

    def get_pub(self):
        return self.pub_key

    def get_fingerprint(self):
        return hexlify(self.key_hash_bytes).decode('utf-8')

    def getPasswordProtect(self):
        return self.paswordProtect

    def set_passphrase(self, passphrase: str, paswordProtect: bool = True):   
        if passphrase:
            passphrase = unicodedata.normalize("NFKD", passphrase)
        else:
            # Passphrase must always have a string value, even if it's just the empty
            # string.
            passphrase=""

        if paswordProtect:
            self.paswordProtect=True
            # Regenerate the internal key since passphrase changes the result
            self._generate_hash(passphrase)
        else:
            self.paswordProtect=False

    ### override operators    
    def __eq__(self, other):
        if isinstance(other, Key):
            return self.priv_key == other.priv_key
        return False

    def getSelected(self):
        return self.selected
    
    def setSelected(self, selected: bool = False):
        self.selected= selected
    
    def get_is_new(self):
        return self.is_new
    
    def set_encrypted_priv_key(self, passphrase):
        self.encrypted_priv_key = Encrypt.encrypt_string(self.get_private(passphrase), passphrase)

    def get_encrypted_priv_key(self):
        return self.encrypted_priv_key

