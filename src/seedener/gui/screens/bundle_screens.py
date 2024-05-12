from dataclasses import dataclass
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedener.gui.components import GUIConstants, FontAwesomeIconConstants
from seedener.gui.screens.screen import QRDisplayScreen, BaseScreen
from seedener.models.encode_qr import EncodeQR 
from seedener.models.qr_type import QRType 

from binascii import hexlify
from base64 import b32encode
from textwrap import wrap

import hashlib
import qrcode
from seedener.models import QRType  

from seedener.models.settings import SettingsConstants 
# Hashing Const TODO: global const hashing rounds
PBKDF2_ROUNDS = 2048

@dataclass
class BundleOptionsScreen(ButtonListScreen):
    # Customize defaults
    fingerprint: str = None
    has_passphrase: bool = False

    def __post_init__(self):
        self.top_nav_icon_name = FontAwesomeIconConstants.PEN
        self.top_nav_icon_color = "blue"
        self.title = self.fingerprint
        self.is_button_text_centered = False
        self.is_bottom_list = True

        super().__post_init__()

@dataclass
class BundleExportQrDisplayLoopScreen(BaseScreen):
    bundle_phrase:str =''
    qr_density: str= ''
    qr_type:str = ''
     
    def __post_init__(self):
        super().__post_init__()
        qrversion: int = 10
        content :str=''
        # Size of in bytes for each header section
        header_size = { QRType.QR_SEQUENCE_MODE: 1 , QRType.BUNDLE_CHUNK: QRType.HEADER_SIZE , QRType.BUNDLE_TOTAL_CHUNKS: QRType.HEADER_SIZE}
        
        total_size = len(self.bundle_phrase)
        chunk_size = qrversion * 34 - 17 - (4 * qrcode.constants.ERROR_CORRECT_L)
        for v in header_size.values():
            chunk_size -= v
        if chunk_size <= 0:
            raise ValueError("The chosen QR-code parameters can't accomodate the header size.")
        
        chunks_list = wrap(self.bundle_phrase, chunk_size)
        total_chunks = (total_size-1)//chunk_size + 1 
        header :bytes = { 'mode':QRType.MODE_CHUNK , 'chunk': 1 , 'chunks':total_chunks }
        chunk = len(chunks_list)
        payload : bytes= chunks_list[0].encode('utf-8')
        header['chunk'] = chunk
        data : bytes = b''.join([ header[k].to_bytes(header_size[k], 'big') for k in header ]) + payload
        chunk_total_size = len(b32encode(data).decode('ascii').replace('=', '%'))
        
        if(chunk==total_chunks):
            #TODO: Write hashing function that can be hashed with the same algorithm on the companion app
            # Generate hash of spend bundle data and append it on content end
            #chunk_hash: bytes = None
            #try:
            #    chunk_hash = hashlib.pbkdf2_hmac('sha512', bytes(self.bundle_phrase,'utf-8'), bytes('','utf-8'), PBKDF2_ROUNDS, 64)
            #except Exception as e:
            #    print(repr(e))  
            #header['mode'] = 1; 
            #header['chunk'] = 1;
            #header['chunks'] = 1;
            #data : bytes = b''.join([ header[k].to_bytes(header_size[k], 'big') for k in header ]) + chunk_hash
            #hashContent = b32encode(data).decode('ascii').replace('=', '%')
            #qr_encoder = EncodeQR(
            #    key_phrase=hashContent,  
            #    qr_type= self.qr_type, 
            #    qr_density=self.qr_density,
            #    chunk_size=chunk_total_size
            #)
            #QRDisplayScreen(qr_encoder=qr_encoder).display()

            #TODO: Review code for safety of qr loop data transfer
            i=0
            header[QRType.QR_SEQUENCE_MODE] = QRType.MODE_CHUNK; 
            header[QRType.BUNDLE_CHUNK] = 1;
            header[QRType.BUNDLE_TOTAL_CHUNKS] = total_chunks;
            while i < total_chunks :
                payload : bytes= chunks_list[i].encode('utf-8')
                chunk = i+1
                header[QRType.BUNDLE_CHUNK] = chunk
                data : bytes = b''.join([ header[k].to_bytes(header_size[k], 'big') for k in header ]) + payload
                content += b32encode(data).decode('ascii').replace('=', '%')
                i+= 1
               
            qr_encoder = EncodeQR(
                key_phrase=content,  
                qr_type=self.qr_type, 
                qr_density=self.qr_density,
                chunk_size=chunk_total_size
            )
            QRDisplayScreen(qr_encoder=qr_encoder).display()

        return  
        