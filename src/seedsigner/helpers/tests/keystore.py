import hashlib

from seedsigner.models.key import Key

key = Key()
print(key.get_pub())
print(key.get_private())
print(len(key.get_pub())) 
print(len(key.get_private()))
