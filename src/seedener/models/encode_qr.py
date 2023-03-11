import math
from dataclasses import dataclass
from seedener.helpers.qr import QR 
from seedener.models import Key, QRType  
from seedener.models.settings import SettingsConstants 

@dataclass
class EncodeQR:
    """
       Encode Secret Component key for displaying as qr image
    """
    # TODO: Refactor so that this is a base class with implementation classes for each
    # QR type. No reason exterior code can't directly instantiate the encoder it needs.

    # Dataclass input vars on __init__()
    key_phrase: str = None
    passphrase: str = None
    derivation: str = None
    qr_type: str = None
    qr_density: str = SettingsConstants.DENSITY__HIGH
    chunk_size: int = 0

    def __post_init__(self):
        self.qr = QR()

        if not self.qr_type:
            raise Exception('qr_type is required')

        if self.qr_density == None:
            self.qr_density = SettingsConstants.DENSITY__HIGH

        self.encoder: BaseQrEncoder = None

        # QR formats
        if  self.qr_type == QRType.KEY__KEYQR:
            self.encoder = KeyQrEncoder(key_phrase=self.key_phrase)
        elif self.qr_type == QRType.BUNDLE__QR:
            self.encoder = KeyQrEncoder(key_phrase=self.key_phrase,chunk_size=self.chunk_size)
        else:
            raise Exception('QR Type not supported')

    def total_parts(self) -> int:
        return self.encoder.seq_len()

    def next_part(self):
        return self.encoder.next_part()

    def part_to_image(self, part, width=240, height=240, border=3):
        return self.qr.qrimage_io(part, width, height, border)

    def next_part_image(self, width=240, height=240, border=3, background_color="bdbdbd"):
        part = self.next_part()
        if self.qr_type == QRType.KEY__KEYQR:
            return self.qr.qrimage(part, width, height, border)
        elif self.qr_type == QRType.BUNDLE__QR:
            return self.qr.qrimage_io(part, width, height, border, background_color=background_color, qrversion=10)
        else:
            raise Exception('QR Type not supported')

    # TODO: Make these properties?
    def get_is_complete(self):
        return self.encoder.get_is_complete()

    def get_qr_density(self):
        return self.qr_density

    def get_qr_type(self):
        return self.qr_type

class BaseQrEncoder:
    def seq_len(self):
        raise Exception("Not implemented in child class")

    def next_part(self) -> str:
        raise Exception("Not implemented in child class")

    def _create_parts(self):
        raise Exception("Not implemented in child class")

    def get_is_complete(self):
        raise Exception("Not implemented in child class")

class KeyQrEncoder(BaseQrEncoder):
    def __init__(self, key_phrase: str, chunk_size: int=0 ):
        super().__init__()
        self.key_phrase = key_phrase
        self.chunk_size = chunk_size
        self.is_complete = None
        self.saved_key_phrase = key_phrase


    def seq_len(self):
        return 1

    def next_part(self):
        # To Make sure string is unicode UTF8 encode and decode
        next_key_part: str=''
        length=len(self.key_phrase)
        if self.chunk_size==0:
            next_key_part=self.key_phrase
            self.key_phrase=self.saved_key_phrase
            self.is_complete=True
        else:
            if length >=self.chunk_size:
                next_key_part= self.key_phrase[:self.chunk_size]
                self.key_phrase= self.key_phrase[self.chunk_size:]
                self.is_complete=False
            else:
                next_key_part=self.key_phrase
                self.key_phrase=self.saved_key_phrase
                self.is_complete=True

        return next_key_part.encode().decode('UTF-8')

    def get_is_complete(self):
        return self.is_complete
    