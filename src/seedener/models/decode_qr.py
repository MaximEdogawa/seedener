import base64
import json
import logging
import re

from binascii import a2b_base64, b2a_base64
from enum import IntEnum
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from . import QRType, Key
from .settings import SettingsConstants


logger = logging.getLogger(__name__)
class DecodeQRStatus(IntEnum):
    """
        Used in DecodeQR to communicate status of adding qr frame/segment
    """
    PART_COMPLETE = 1
    PART_EXISTING = 2
    COMPLETE = 3
    FALSE = 4
    INVALID = 5

class DecodeQR:
    """
        Used to process images or string data from animated qr codes.
    """
    def __init__(self):
        self.complete = False
        self.qr_type = None
        self.decoder = None
 
    def add_image(self, image):
        data = DecodeQR.extract_qr_data(image)
        if data == None:
            return DecodeQRStatus.FALSE

        return self.add_data(data)

    def add_data(self, data):
        if data == None:
            return DecodeQRStatus.FALSE

        qr_type = DecodeQR.detect_segment_type(data)

        if self.qr_type == None:
            self.qr_type = qr_type
            if self.qr_type in [QRType.SPEND_BUNDLE, QRType.SECRECT__COMPONENT]:
                self.decoder = KeyQrDecoder()          

        elif self.qr_type != qr_type:
            raise Exception('QR Fragment Unexpected Type Change')
            
        if not self.decoder:
            # Did not find any recognizable format
            return DecodeQRStatus.INVALID

        # Convert to string data
        if type(data) == bytes:
            # Should always be bytes, but the test suite has some manual datasets that
            # are strings.
            # TODO: Convert the test suite rather than handle here?
            qr_str = data.decode('utf-8')
        else:
            # it's already str data
            qr_str = data

         # All other formats use the same method signature
        rt = self.decoder.add(qr_str, self.qr_type)
        if rt == DecodeQRStatus.COMPLETE:
            self.complete = True
        return rt

    @staticmethod
    def detect_segment_type(s):
        # print("-------------- DecodeQR.detect_segment_type --------------")
        # print(type(s))
        # print(len(s))
        try:
            # Convert to str data
            if type(s) == bytes:
                # Should always be bytes, but the test suite has some manual datasets that
                # are strings.
                # TODO: Convert the test suite rather than handle here?
                s = s.decode('utf-8')

            # Spend Bundle
            if re.search(QRType.SPEND_BUNDLE, s, re.IGNORECASE):
                return QRType.SPEND_BUNDLE
            # Secret Component
            elif re.search(QRType.SECRECT__COMPONENT, s, re.IGNORECASE):
                return QRType.SECRECT__COMPONENT

            # config data
            if "type=settings" in s:
                return QRType.SETTINGS
            # Is it byte data?
        except UnicodeDecodeError:
            # Probably this isn't meant to be string data; check if it's valid byte data
            # below.
            pass

        return QRType.INVALID

    def get_key_phrase(self):
        if self.is_key:
            return self.decoder.get_key_phrase()

    def get_percent_complete(self) -> int:
        if not self.decoder:
            return 0

        elif self.decoder.total_segments == 1:
            # The single frame QR formats are all or nothing
            if self.decoder.complete:
                return 100
            else:
                return 0
        else:
            return 0

    @property
    def is_complete(self) -> bool:
        return self.complete

    @property
    def is_invalid(self) -> bool:
        return self.qr_type == QRType.INVALID

    @property
    def is_key(self):
        return self.qr_type in [
            QRType.SECRECT__COMPONENT,
        ]    

    @property
    def is_spendBundle(self):
        return self.qr_type in [
            QRType.SPEND_BUNDLE,
        ] 

    @property
    def is_settings(self):
        return self.qr_type == QRType.SETTINGS

    @staticmethod
    def extract_qr_data(image) -> str:
        if image is None:
            return None

        barcodes = pyzbar.decode(image, symbols=[ZBarSymbol.QRCODE])

        for barcode in barcodes:
            # Only pull and return the first barcode
            return barcode.data

class BaseQrDecoder:
    def __init__(self):
        self.total_segments = None
        self.collected_segments = 0
        self.complete = False

    @property
    def is_complete(self) -> bool:
        return self.complete

    def add(self, segment, qr_type):
        raise Exception("Not implemented in child class")

class BaseSingleFrameQrDecoder(BaseQrDecoder):
    def __init__(self):
        super().__init__()
        self.total_segments = 1

class KeyQrDecoder(BaseSingleFrameQrDecoder):
    def __init__(self):
        super().__init__()
        self.key_phrase = []

    def add(self, key_phrase, qr_type=QRType.KEY__KEYQR):
        # `key_phrase` data will either be bytes or str, depending on the qr_typ

        if qr_type == QRType.SECRECT__COMPONENT:
            try:
                self.key_phrase = key_phrase
                if len(self.key_phrase) > 0:
                    if self.is_62_char_phrase() == False:
                        return DecodeQRStatus.INVALID
                    self.complete = True
                    self.collected_segments = 1
                    return DecodeQRStatus.COMPLETE
                else:
                    return DecodeQRStatus.INVALID
            except Exception as e:
                return DecodeQRStatus.INVALID

        elif qr_type == QRType.SPEND_BUNDLE:
            try:
                self.key_phrase = key_phrase
                if len(self.key_phrase) > 0:
                    if self.is241_char_phrase() == False:
                        return DecodeQRStatus.INVALID
                    self.complete = True
                    self.collected_segments = 1
                    return DecodeQRStatus.COMPLETE
                else:
                    return DecodeQRStatus.INVALID
            except Exception as e:
                return DecodeQRStatus.INVALID
        else:
            return DecodeQRStatus.INVALID

    def get_key_phrase(self):
        if self.complete:
            return self.key_phrase[:]
        return []

    # Secret Component 62 
    def is_62_char_phrase(self):
        if len(self.key_phrase) == 62:
            return True
        return False
    # Spend Bundle 241
    # TODO: Find a way to check for Spend Bundle the right way
    def is_92_char_phrase(self):
        if len(self.key_phrase) == 241:
            return True
        return False

