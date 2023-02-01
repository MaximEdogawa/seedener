import base64
from base64 import b32decode
import json
import logging
import re

from binascii import a2b_base64, b2a_base64
from enum import IntEnum
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from . import QRType
from .settings import SettingsConstants

from typing import List
import subprocess
import hashlib
from binascii import hexlify

PBKDF2_ROUNDS = 2048

class InvalidBundleException(Exception):
    pass

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

        if type(data) == str:
            # Should always be bytes, but the test suite has some manual datasets that
            # TODO: Convert the test suite rather than handle here?
            data=data.decode('utf-8')

        header, payload = DecodeQR.decode_data(data)
        qr_type = DecodeQR.detect_segment_type(data, header)

        if self.qr_type == None:
            self.qr_type = qr_type
            if self.qr_type in [QRType.SECRECT_COMPONENT]:
                self.decoder = KeyQrDecoder()
            elif self.qr_type in [QRType.QR_SEQUENCE_MODE]:
                self.decoder = BundleQrDecoder()        
            
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

        if self.qr_type in [QRType.QR_SEQUENCE_MODE]:
            rt = self.decoder.add(header, payload, self.qr_type)
        else:
            # All other formats use the same method signature
            rt = self.decoder.add(qr_str, self.qr_type)
        
        if rt == DecodeQRStatus.COMPLETE:
            self.complete = True
        return rt

    @staticmethod
    def detect_segment_type(data, header= {}):
        #print("-------------- DecodeQR.detect_segment_type --------------")
        #print(type(data))
        #print(len(data))
        try:
            if header[QRType.QR_SEQUENCE_MODE]:
                return QRType.QR_SEQUENCE_MODE

            else:
                # Secret Component
                if re.search(QRType.SECRECT_COMPONENT, data, re.IGNORECASE):
                   return QRType.SECRECT_COMPONENT 
        
            # config data
            #if "type=settings" in s:
            #    return QRType.SETTINGS
            # Is it byte data?
        except UnicodeDecodeError:
            # Probably this isn't meant to be string data; check if it's valid byte data
            # below.
            pass

        return QRType.INVALID

    @staticmethod
    def decode_data(data):
        content = b32decode(data.decode('ascii').replace('%', '=').encode('ascii'))
        cursor = 0
        header = {}
        header_size = { QRType.QR_SEQUENCE_MODE: 1 , QRType.BUNDLE_CHUNK: 7 , QRType.BUNDLE_TOTAL_CHUNKS: 7}
        for k,size in header_size.items():
            header[k] = int.from_bytes(content[cursor:cursor+size], 'big')
            cursor += size
        payload = content[cursor:]
        return header, payload

    def get_key_phrase(self):
        if self.is_key:
            return self.decoder.get_key_phrase()

    def get_spend_bundle(self):
        return self.decoder.get_spend_bundle()
    
    def get_spend_bundle_hash(self):
        return self.decoder.get_spend_bundle_hash()
    
    def _generate_hash(self,bundle_bytes: bytes=None ): 
        try:
            bundle_hash_bytes = hashlib.pbkdf2_hmac(
                "sha512",
                bundle_bytes.encode("utf-8"),
                '',
                PBKDF2_ROUNDS,
                64, 
            )
        except Exception as e:
            print(repr(e))
            raise InvalidBundleException(repr(e))
        
        return bundle_hash_bytes 

    def get_percent_complete(self) -> int:
        if not self.decoder:
            return 0

        elif self.decoder.total_segments != None:
            # The single frame QR formats are all or nothing
            if self.decoder.complete:
                return 100
            else:
                return (100 * float(self.decoder.collected_segments)/float(self.decoder.total_segments))
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
            QRType.SECRECT_COMPONENT,
        ]    

    @property
    def is_spendBundle(self):
        return self.qr_type in [
            QRType.QR_SEQUENCE_MODE,
        ] 

    @property
    def is_settings(self):
        return self.qr_type == QRType.SETTINGS

    @staticmethod
    def extract_qr_data(image) -> str:
        if image is None:
            return None

        barcodes = pyzbar.decode(image, symbols=[ZBarSymbol.CODE128, ZBarSymbol.QRCODE])

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

        if qr_type == QRType.SECRECT_COMPONENT:
            try:
                self.key_phrase = key_phrase
                if len(self.key_phrase) > 0:
                    if self.is_62_char_phrase() == False:
                        return DecodeQRStatus.INVALID
                    self.collected_segments = 1
                    self.complete = True
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

class BundleQrDecoder(BaseQrDecoder):
    def __init__(self):
        super().__init__()
        self.spend_bundle = []
        self.spend_bundle_hash : bytes = None
    
    def add(self, header, payload, qr_type=QRType.QR_SEQUENCE_MODE):
        if qr_type == QRType.QR_SEQUENCE_MODE:
            #TODO: Review decode logic for spend bundle to be faster
            try:
                if header[QRType.QR_SEQUENCE_MODE]==QRType.MODE_CHUNK:
                    if type(payload) == bytes:
                        payload = payload.decode('utf-8')

                    if(self.total_segments == None):
                        self.total_segments=int(header[QRType.BUNDLE_TOTAL_CHUNKS])
                        self.spend_bundle  = ["" for x in range(self.total_segments)]
                    #TODO: Review code 
                    chunk_index = header[QRType.BUNDLE_CHUNK]-1
                    if self.spend_bundle[chunk_index]=='' and payload != '':
                        self.spend_bundle[chunk_index] = payload
                        self.collected_segments=self.collected_segments+1 
                        print("Added "+ str(self.collected_segments) +" of "+ str(self.total_segments)+" Chunks")

                elif header[QRType.QR_SEQUENCE_MODE]==QRType.MODE_HASH:
                    if type(payload) == str:
                        payload = payload.encode('utf-8')
                    if self.spend_bundle_hash==None and payload != '':
                        self.spend_bundle_hash = payload
                        self.collected_segments=self.collected_segments+1 
                        print("Added Controll Hash of Chunks")

            except Exception as e:
                return DecodeQRStatus.INVALID

            if(self.collected_segments==self.total_segments):
                self.complete = True
                print("Chunks Complete!")
                return DecodeQRStatus.COMPLETE

    def get_spend_bundle(self):
        if self.complete:
            bundle_str: str=''
            bundle_len = len(self.spend_bundle[:])-1
            while(bundle_len >= 0):
                bundle_str+=self.spend_bundle[bundle_len]
                bundle_len -= 1
            return bundle_str
        return []
    
    def get_spend_bundle_hash(self):
        if self.complete:
            return self.spend_bundle_hash 
        return
    
    
