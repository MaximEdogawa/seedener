from typing import List
from seedener.models import Bundle
from seedener.models.bundle import InvalidBundleException

class BundleStorage:
    def __init__(self) -> None:
        self.bundles: List[Bundle] = []
        self.pending_bundle: Bundle = None
    
    def set_pending_bundle(self, bundle: Bundle):
        self.pending_bundle = bundle

    def get_pending_bundle(self) -> Bundle:
        return self.pending_bundle

    def finalize_pending_bundle(self) -> int:
        # Finally store the pending key and return its index
        if self.pending_bundle in self.bundles:
            index = self.bundles.index(self.pending_bundle)
        else:
            self.bundles.append(self.pending_bundle)
            index = len(self.bundles) - 1
        self.pending_bundle = None
        return index

    def clear_pending_bundle(self):
        self.pending_bundle = None

    def num_keys(self):
        return len(self.bundles)