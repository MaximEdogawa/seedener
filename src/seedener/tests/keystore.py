import hashlib

from seedener.models.key import Key

class KeyStoreTest():
    def __init__(self, passphrase: str = ""):
        self.key = Key(passphrase)
    
    def teststart(self, passphrase: str = ""):
        print(self.key.get_pub())
        print(self.key.get_private(passphrase)) 
