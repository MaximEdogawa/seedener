from typing import List
import subprocess
import hashlib
from binascii import hexlify

HSMS = " | hsms -y -- nochunks" #Sign unsigned bundles
HSMMERGE = "hsmmerge" #Merge signed bundles
# Hashing Const
PBKDF2_ROUNDS = 2048

class InvalidBundleException(Exception):
    pass

class Bundle:
    def __init__(self, unsigned_bundle: str = "") -> None:
        self.unsigned_bundle: str = unsigned_bundle
        self.unsigned_bundle_hash: bytes = None
        self.signed_bundle: str = ""
        self.signed_bundle_list: List[str] = []
        self.finilized_signed_bundle: str = ""
        self.finilized: bool = False
        self._generate_hash()        

    def _signBundle(self, priv_key: str = ""):
        commandSign=self.unsigned_bundle + HSMS + priv_key
        try:
            self.signed_bundle = subprocess.Popen(commandSign, shell = True, stdout=subprocess.PIPE).stdout.read().decode()
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))
 
        self.signed_bundle_list.append(self.signed_bundle)

    def _mergeSignedBundles(self):
        commandMerge=HSMMERGE
        for i in len(self.signed_bundle_list):
            commandMerge+=" "+self.signed_bundle_list[i]
        try:
            self.finilized_signed_bundle = subprocess.Popen(commandMerge, shell = True, stdout=subprocess.PIPE).stdout.read().decode()
            self.finilized=True
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))
    
    def get_signed_bundle(self):
        return self.finilized_signed_bundle

    def get_unsigned_bundle(self):
        return self.unsigned_bundle 
    
    def get_unsigned_bundle_hash(self):
        return self.unsigned_bundle_hash

    def isSigned(self):
        return self.finilized
    
    def _generate_hash(self): 
        try:
            self.unsigned_bundle_hash = hashlib.pbkdf2_hmac(
                "sha512",
                bytes(self.unsigned_bundle,'utf-8'),
                bytes('','utf-8'),
                PBKDF2_ROUNDS,
                64,
            )
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))