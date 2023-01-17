from typing import List
from seedener.models import Key
from seedener.models.key import InvalidKeyException

class KeyStorage:
    def __init__(self) -> None:
        self.keys: List[Key] = []
        self.pending_key: Key = None
    
    def set_pending_key(self, key: Key):
        self.pending_key = key

    def get_pending_key(self) -> Key:
        return self.pending_key

    def finalize_pending_key(self) -> int:
        # Finally store the pending key and return its index
        if self.pending_key in self.keys:
            index = self.keys.index(self.pending_key)
        else:
            self.keys.append(self.pending_key)
            index = len(self.keys) - 1
        self.pending_key = None
        return index

    def clear_pending_key(self):
        self.pending_key = None

    def num_keys(self):
        return len(self.keys)