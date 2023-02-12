from typing import List
import subprocess
import hashlib
from binascii import hexlify
import tempfile

HSMS = "hsms -y --nochunks " #Sign unsigned bundles
HSMMERGE = "hsmmerge " #Merge signed bundles
CAT = "cat "
PIPE = " | "
# Hashing Const
PBKDF2_ROUNDS = 2048

class InvalidBundleException(Exception):
    pass

class Bundle:
    def __init__(self, unsigned_bundle: str = "") -> None:
        self.unsigned_bundle: str = unsigned_bundle
        self.unsigned_bundle_hash: bytes = None
        self.signed_bundle_list: List[str] = []
        self.is_signed_part=False
        self.signed_bundle=False
        self.finilized_signed_bundle: str = ""
        self.finilized: bool = False
        self._generate_hash()        

    def _signBundle(self, priv_key: str = ""):
        temp_priv_key = tempfile.NamedTemporaryFile('w+t',suffix='.se')
        temp_unsigned_bundle = tempfile.NamedTemporaryFile('w+t',suffix='.unsigned')
        try:
            temp_unsigned_bundle.write(self.unsigned_bundle)
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))
        temp_unsigned_bundle.seek(0)

        try:
            temp_priv_key.write(priv_key)
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))
        
        temp_priv_key.seek(0)

        if type(self.unsigned_bundle)==bytes:
            self.unsigned_bundle=self.unsigned_bundle.decode('utf-8')
            
        commandSign= CAT + temp_unsigned_bundle.name + PIPE + HSMS + temp_priv_key.name

        try:
            proc = subprocess.Popen(commandSign, shell = True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            proc.wait()
            proc.stdin.close()
            signed_bundle = proc.stdout.read()
            print('\n')
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))

        if(signed_bundle!=b''):
            self.is_signed_part=True
            self.signed_bundle=True
            self.signed_bundle_list.append(signed_bundle.decode('utf-8'))
        else:
            self.is_signed_part=False
           
        temp_priv_key.close()
        return self.is_signed_part

    def get_is_signed_bundle(self):
        return self.signed_bundle

    def _mergeSignedBundles(self):
        temp_unsigned_bundle = tempfile.NamedTemporaryFile('w+t',suffix='.unsigned')
        try:
            temp_unsigned_bundle.write(self.unsigned_bundle)
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))
            
        #TODO: Review code if there are some leftover data of temp files
        commandMerge=HSMMERGE + temp_unsigned_bundle.name
        temp_unsigned_bundle.seek(0)
        # Create temp file list
        files = []
        for i in range(len(self.signed_bundle_list)):
            f = tempfile.NamedTemporaryFile('w+t',suffix='_'+str(i+1)+'.sig')
            f.write(self.signed_bundle_list[i])
            f.seek(0)
            files.append(f)
            commandMerge+=" "+ f.name
        try:
            self.finilized_signed_bundle = subprocess.Popen(commandMerge, shell = True, stdout=subprocess.PIPE).stdout.read().decode()
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))

        if self.finilized_signed_bundle!="":
            self.finilized=True
        else:
            self.finilized=False

        #Close all temp files
        list(map(lambda f: f.close(), files))
        temp_unsigned_bundle.close()
    
    def get_finilized_signed_bundle(self):
        return self.finilized_signed_bundle

    def get_unsigned_bundle(self):
        return self.unsigned_bundle 
    
    def get_unsigned_bundle_hash(self):
        return self.unsigned_bundle_hash

    def isFinilized(self):
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
    
    def clear_signed_bundle_list(self):
        self.signed_bundle_list.clear()