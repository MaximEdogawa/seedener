import random
import time
import string
from typing import List

from textwrap import wrap
from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from .view import View, Destination, BackStackView, MainMenuView

from seedener.controller import Controller
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen, settings_screens)
from seedener.models.settings import SettingsConstants, SettingsDefinition
from seedener.gui.screens.screen import LargeIconStatusScreen, QRDisplayScreen 
from seedener.models.key import InvalidKeyException, Key
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen, WarningScreen, DireWarningScreen ,key_screens)
from seedener.models.qr_type import QRType 
from seedener.models.encode_qr import EncodeQR 
from seedener.gui.screens.screen import LoadingScreenThread
from seedener.models.key import Key

SUBSTRING_LENGTH = 7
class KeysMenuView(View):
    def __init__(self, isRekey: bool=False):
        super().__init__()
        self.keys = []
        for key in self.controller.inMemoryStore.keys:
            self.keys.append({
                "fingerprint": key.get_fingerprint(),
                "has_passphrase": key.getPasswordProtect(),
                "new": key.get_is_new(),
            })

    def run(self):
        if not self.keys:
            # Nothing to do here unless we have a key loaded
            return Destination(LoadKeyView, clear_history=True)

        button_data = []
        for key in self.keys:
            
            if key["new"]:
                if(key["has_passphrase"]):
                    button_data.append(("NEW - "+key["fingerprint"][:10] + "...", FontAwesomeIconConstants.LOCK, "yellow"))
                else:
                    button_data.append(("NEW - "+key["fingerprint"][:10] + "...", SeedenerCustomIconConstants.CIRCLE_EXCLAMATION, "yellow"))
            else:
                if(key["has_passphrase"]):
                    button_data.append((key["fingerprint"][:15] + "...", FontAwesomeIconConstants.LOCK, "blue"))
                else:
                    button_data.append((key["fingerprint"][:15] + "...", SeedenerCustomIconConstants.FINGERPRINT, "blue"))
                

        button_data.append(" Create a key")

        selected_menu_num = ButtonListScreen(
            title="In-Memory Keys",
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if len(self.keys) > 0 and selected_menu_num < len(self.keys):
            return Destination(KeyOptionsView, view_args=dict(key_num = selected_menu_num))

        elif selected_menu_num == len(self.keys):
            return Destination(CreateKeyEntryView, view_args=dict(total_keys=1))

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(MainMenuView)

"""****************************************************************************
    Loading keys, passphrases, etc
****************************************************************************"""
class LoadKeyView(View):
    def run(self):
        CREATE = (" Create a key", FontAwesomeIconConstants.PLUS)
        button_data=[
            CREATE,
        ]

        selected_menu_num = ButtonListScreen(
            title="Load A Key",
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == CREATE:
            return Destination(CreateKeyEntryView, view_args=dict(total_keys=1))

"""****************************************************************************
    Create Key Views
****************************************************************************"""
class CreateKeyEntryView(View):
    def __init__(self, total_keys: int=1):
        super().__init__()
        self.total_keys = total_keys
        self.loading_screen = None

    def run(self):
        ret = WarningScreen(
            title="Caution",
            status_headline="You will create a new Key Pair!",
            text="Be at a save place!",
            button_data=["I Understand"],
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        self.loading_screen = LoadingScreenThread(text="Creating Key Pair...")
        self.loading_screen.start()

        try:
            key = Key()
            self.controller.inMemoryStore.set_pending_key(key)
            self.loading_screen.stop()
        except Exception as e:
            self.loading_screen.stop()
            raise e

        # Cannot return BACK to this View
        return Destination(KeyWarningView, view_args=dict(key_num= None), clear_history=True)

"""****************************************************************************
    View Key Substring flow
****************************************************************************"""
class KeyWarningView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num
        if self.key_num is None:
            self.key = self.controller.inMemoryStore.get_pending_key()
        else:
            self.key = self.controller.get_key(self.key_num)
            
    def run(self):
        if(self.key.getPasswordProtect()):
            ret = key_screens.KeyPassphraseScreen(title="Input Passphrase").display() 
            if ret == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)
            
            if(self.key.compareKey_passphrase(ret)==False):
                return Destination(KeyPassphraseBackupKeyRetryView, view_args=dict(key_num=self.key_num))

        destination = Destination(
            KeyView,
            view_args=dict(
                key_num=self.key_num,
                page_index=0,
            ),
            skip_current_view=True,  # Prevent going BACK to WarningViews
        )
        if self.settings.get_value(SettingsConstants.SETTING__DIRE_WARNINGS) == SettingsConstants.OPTION__DISABLED:
            # Forward straight to showing the Substring
            return destination

        selected_menu_num = DireWarningScreen(
            text="""You must keep your Keys private & away from all online devices.""",
        ).display()

        if selected_menu_num == 0:
            # User clicked "I Understand"
            return destination

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
class KeyPassphraseBackupKeyRetryView(View):
    def __init__(self, key_num: int):
        self.key_num=key_num

    def run(self):
        BACK = "Back"
        RETRY = "Try Again"
        button_data = [RETRY, BACK]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Passphrase!",
            text=f"Please input the correct passphrase.",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == RETRY:
            return  Destination(KeyWarningView,view_args=dict(key_num=self.key_num)) 
        elif button_data[selected_menu_num] == BACK:
            return Destination(KeyOptionsView, view_args=dict(key_num = self.key_num), clear_history=True)

"""****************************************************************************
    Views for actions on individual keys:
****************************************************************************"""
class KeyOptionsView(View):
    def __init__(self, key_num: int): 
        super().__init__()
        self.key_num = key_num
        if self.key_num is None:
            self.key = self.controller.inMemoryStore.get_pending_key()
        else:
            self.key = self.controller.get_key(self.key_num)
            
    def run(self):
        EXPORT_XPUB = "Export Pub"
        BACKUP = ("Backup key", None, None, None, SeedenerCustomIconConstants.SMALL_CHEVRON_RIGHT)
        DISCARD = ("Discard key", None, None, "red")

        button_data = []
           
        if self.settings.get_value(SettingsConstants.SETTING__XPUB_EXPORT) == SettingsConstants.OPTION__ENABLED:
            button_data.append(EXPORT_XPUB)

        button_data.append(BACKUP)

        button_data.append(DISCARD)

        selected_menu_num = key_screens.KeyOptionsScreen(
            button_data=button_data,
            fingerprint=self.key.get_fingerprint()[:15] + "...",
            has_passphrase=self.key.getPasswordProtect(),
        ).display() 

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            # Force BACK to always return to the Main Menu
            return Destination(MainMenuView)
       
        elif button_data[selected_menu_num] == EXPORT_XPUB:
            return Destination(KeyExportPubTypeView, view_args=dict(key_num=self.key_num,))

        elif button_data[selected_menu_num] == BACKUP:
            return Destination(KeyBackupView, view_args=dict(key_num=self.key_num,))

        elif button_data[selected_menu_num] == DISCARD:
            return Destination(KeyDiscardView, view_args=dict(key_num=self.key_num,))

"""****************************************************************************
   Export Private Key flow
****************************************************************************"""
class KeyView(View):
    def __init__(self, key_num: int, page_index: int = 0):
        super().__init__()
        self.key_num = key_num
        if self.key_num is None:
            self.key = self.controller.inMemoryStore.get_pending_key()
        else:
            self.key = self.controller.get_key(self.key_num)
        
        self.page_index = page_index
        self.privKeyString = self.key.get_privateKey_backUp_flow()
    
    def run(self):
        NEXT = "Next"
        DONE = "Done"
        title = "Private Key"
        button_data = []
        substring_per_page = 4
        key_length = len(self.privKeyString)
        num_pages = int((key_length/SUBSTRING_LENGTH)/substring_per_page) + 1 #Increase Number by one for rest values

        substrings = wrap(self.privKeyString, SUBSTRING_LENGTH)
        substrings_per_page = substrings[self.page_index*substring_per_page:(self.page_index + 1)*substring_per_page]
        
        if self.page_index < num_pages - 1 or self.key_num is None:
            button_data.append(NEXT)
        else:
            button_data.append(DONE)

        
        button_data = []
        if self.page_index < num_pages - 1 or self.key_num is None:
            button_data.append(NEXT)
        else:
            button_data.append(DONE)

        selected_menu_num = key_screens.KeyExportScreen( 
            title=f"{title}: {self.page_index+1}/{num_pages}",
            words=substrings_per_page,
            page_index=self.page_index,
            num_pages=num_pages,
            button_data=button_data,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        if button_data[selected_menu_num] == NEXT:
            if self.key_num is None and self.page_index == num_pages - 1:
                return Destination(
                    KeyBackupTestPromptView,
                    view_args=dict(
                        key_num=self.key_num
                    )
                )
            else:
                return Destination(
                    KeyView,
                    view_args=dict(
                        key_num=self.key_num, 
                        page_index=self.page_index + 1                    )
                )

        elif button_data[selected_menu_num] == DONE:
                # Must clear history to avoid BACK button returning to private info
                return Destination(
                    KeyBackupTestPromptView,
                    view_args=dict(key_num=self.key_num,)
                )  

"""****************************************************************************
    Export Key as QR
****************************************************************************"""
class KeyTranscribeKeyQRFormatView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num

    def run(self):
        STANDARD = "Standard: 29x29"
        num_modules_standard = 29

        button_data = [STANDARD]

        selected_menu_num = key_screens.KeyTranscribeKeyQRFormatScreen( 
            title="KeyQR Format",
            button_data=button_data,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        if button_data[selected_menu_num] == STANDARD: 
            keyqr_format = QRType.KEY__KEYQR
            num_modules = num_modules_standard
        
        return Destination(
                KeyTranscribeKeyQRWarningView,
                view_args={
                    "key_num": self.key_num,
                    "keyqr_format": keyqr_format, 
                    "num_modules": num_modules,

                },
                skip_current_view=True,
            ) 

class KeyTranscribeKeyQRWarningView(View):
    def __init__(self, key_num: int, keyqr_format: str = QRType.KEY__KEYQR, num_modules: int = 29):
        super().__init__()
        self.key_num = key_num
        self.keyqr_format = keyqr_format
        self.num_modules = num_modules

    def run(self):
        destination = Destination(
            KeyTranscribeKeyQRWholeQRView,
            view_args={
                "key_num": self.key_num,
                "keyqr_format": self.keyqr_format,
                "num_modules": self.num_modules,
            },
            skip_current_view=True,  # Prevent going BACK to WarningViews
        )

        if self.settings.get_value(SettingsConstants.SETTING__DIRE_WARNINGS) == SettingsConstants.OPTION__DISABLED:
            # Forward straight to transcribing the KeyQR
            return destination

        selected_menu_num = DireWarningScreen(
            status_headline="KeyQR is your private key!",
            text="""Never photograph it or scan it into an online device.""",
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        else:
            # User clicked "I Understand"
            return destination  

class KeyTranscribeKeyQRWholeQRView(View):
    def __init__(self, key_num: int, keyqr_format: str, num_modules: int):
        super().__init__()
        self.key_num = key_num
        self.keyqr_format = keyqr_format
        self.num_modules = num_modules
        self.key = self.controller.get_key(key_num)

    def run(self):
        if(self.key.getPasswordProtect()):
            ret = key_screens.KeyPassphraseScreen(title="Input Passphrase").display() 
            if ret == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)
            
            if(self.key.compareKey_passphrase(ret)==False):
                return Destination(KeyPassphraseTranscribeKeyRetryView, view_args=dict(key_num=self.key_num))

        e = EncodeQR(
            key_phrase=self.key.get_privateKey_backUp_flow(),
            qr_type=self.keyqr_format,
        )
        data = e.next_part()

        ret = key_screens.KeyTranscribeKeyQRWholeQRScreen( 
            qr_data=data,
            num_modules=self.num_modules,
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        else:
            return Destination(
                KeyTranscribeKeyQRZoomedInView,
                view_args={
                    "key_num": self.key_num,
                    "keyqr_format": self.keyqr_format,
                }
            )
            
class KeyPassphraseTranscribeKeyRetryView(View):
    def __init__(self, key_num: int):
        self.key_num=key_num

    def run(self):
        BACK = "Back"
        RETRY = "Try Again"
        button_data = [RETRY, BACK]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Passphrase!",
            text=f"Please input the correct passphrase.",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == RETRY:
            return  Destination(KeyTranscribeKeyQRWholeQRView,view_args=dict(key_num=self.key_num)) 
        elif button_data[selected_menu_num] == BACK:
            return Destination(KeyOptionsView, view_args=dict(key_num = self.key_num), clear_history=True)


class KeyTranscribeKeyQRZoomedInView(View):
    def __init__(self, key_num: int, keyqr_format: str):
        super().__init__()
        self.key_num = key_num 
        self.keyqr_format = keyqr_format
        self.key = self.controller.get_key(key_num)

    def run(self):
        e = EncodeQR(
            key_phrase=self.key.get_privateKey_backUp_flow(),
            qr_type=self.keyqr_format,
        )

        data = e.next_part()
        num_modules = 25

        key_screens.KeyTranscribeKeyQRZoomedInScreen( 
            qr_data=data,
            num_modules=num_modules,
        ).display()

        return Destination(KeyTranscribeKeyQRConfirmQRPromptView, view_args=dict(key_num=self.key_num))

class KeyTranscribeKeyQRConfirmQRPromptView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num
        self.key = self.controller.get_key(key_num)

    def run(self):
        SCAN = ("Confirm KeyQR", FontAwesomeIconConstants.QRCODE)
        DONE = "Done"
        button_data = [SCAN, DONE]

        selected_menu_option = key_screens.KeyTranscribeKeyQRConfirmQRPromptScreen( 
            title="Confirm KeyQR?",
            button_data=button_data,
        ).display()

        if selected_menu_option == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_option] == SCAN:
            return Destination(KeyTranscribeKeyQRConfirmScanView, view_args={"key_num": self.key_num})

        elif button_data[selected_menu_option] == DONE:
            return Destination(KeyOptionsView, view_args={"key_num": self.key_num}, clear_history=True)

class KeyTranscribeKeyQRConfirmScanView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num
        self.key = self.controller.get_key(key_num)

    def run(self):
        from seedener.gui.screens.scan_screen import ScanScreen
        from seedener.models import DecodeQR
        self.decoder = DecodeQR()
        ScanScreen(decoder=self.decoder, instructions_text="Scan your KeyQR").display()

        if self.decoder.is_complete:
            if self.decoder.is_key:
                key_phrase = self.decoder.get_key_phrase()
                if not key_phrase:
                    # key is not valid, Exit if not valid with message
                    raise Exception("Key is not valid!")
                else:
                    if key_phrase != self.key.get_privateKey_forSigning():
                        DireWarningScreen(
                            title="Confirm KeyQR",
                            status_headline="Error!",
                            text="Your transcribed KeyQR does not match your original key!",
                            show_back_button=False,
                            button_data=["Review KeyQR"],
                        ).display()

                        return Destination(BackStackView, skip_current_view=True)

                    else:
                        LargeIconStatusScreen(
                            title="Confirm KeyQR",
                            status_headline="Success!",
                            text="Your transcribed KeyQR successfully scanned and yielded the same key.",
                            show_back_button=False,
                            button_data=["OK"],
                        ).display() 

                        return Destination(KeyOptionsView, view_args={"key_num": self.key_num})
            else:
                # Will this case ever happen? Will trigger if a different kind of QR code is scanned
                DireWarningScreen(
                    title="Confirm KeyQR",
                    status_headline="Error!",
                    text="Your transcribed KeyQR could not be read!",
                    show_back_button=False,
                    button_data=["Review KeyQR"],
                ).display()

                return Destination(BackStackView, skip_current_view=True)

"""****************************************************************************
    Export Public Key flow
****************************************************************************"""
class KeyExportPubTypeView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num
        self.key = self.controller.get_key(key_num)

    def run(self):
        fingerprint = self.key.get_fingerprint()[:10]+"..."
        ret = WarningScreen(
            title="Caution",
            status_headline="You will display the public key of:",
            text= fingerprint,
            button_data=["I Understand"],
        ).display()
        
        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        else:
            return Destination(KeyExportPubQRDisplayView, view_args=dict(key_num=self.key_num), clear_history=True)

class KeyTranscribePubKeyQRWholeQRView(View):
    def __init__(self, key_num: int, keyqr_format: str, num_modules: int):
        super().__init__()
        self.key_num = key_num
        self.keyqr_format = keyqr_format
        self.num_modules = num_modules
        self.key = self.controller.get_key(key_num)
        self.qr_encoder = EncodeQR(
            key_phrase=self.key.get_pub(), 
            qr_type=self.keyqr_format,
        )

    def run(self):
       
        data = self.qr_encoder.next_part() 

        ret = key_screens.KeyTranscibePubKeyQRWholeQRScreen(  
            qr_data=data,
            num_modules=self.num_modules,
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        else:
            return Destination(KeysMenuView)

class KeyExportPubQRDisplayView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key = self.controller.get_key(key_num)
        self.key_num = key_num

        qr_density = self.settings.get_value(SettingsConstants.SETTING__QR_DENSITY)
        qr_type = QRType.KEY__KEYQR
 
        self.qr_encoder = EncodeQR(
            key_phrase=self.key.get_pub(), 
            qr_type=qr_type,
            qr_density=qr_density,
        )

    def run(self):
        ret = QRDisplayScreen(qr_encoder=self.qr_encoder).display()  
        return Destination(KeysMenuView, clear_history=True)

"""****************************************************************************
    Key Backup View
****************************************************************************"""
class KeyBackupView(View):
    def __init__(self, key_num):
        super().__init__()
        self.key_num = key_num
        self.key = self.controller.get_key(key_num)


    def run(self):
        VIEW_SUBSTRINGS = "View Key"
        EXPORT_KEYQR = "Export KeyQR"
        EXPORT_ENCRYPT_KEYQR = "Export Encrypted KeyQR"

        button_data = [VIEW_SUBSTRINGS, EXPORT_KEYQR]

        if(self.key.getPasswordProtect()):
            button_data.append(EXPORT_ENCRYPT_KEYQR)

        selected_menu_num = ButtonListScreen(
            title="Backup Key",
            button_data=button_data,
            is_bottom_list=True,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(KeysMenuView)

        elif button_data[selected_menu_num] == VIEW_SUBSTRINGS:
            return Destination(KeyWarningView, view_args=dict(key_num=self.key_num), clear_history=True)

        elif button_data[selected_menu_num] == EXPORT_KEYQR:
            return Destination(KeyTranscribeKeyQRFormatView, view_args=dict(key_num=self.key_num), clear_history=True)

        elif button_data[selected_menu_num] == EXPORT_ENCRYPT_KEYQR:
            return Destination(EncryptKeyQRFormatView, view_args=dict(key_num=self.key_num), clear_history=True)

"""****************************************************************************
    Export Encrypted Key as QR
****************************************************************************"""
class EncryptKeyQRFormatView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num
            
    def run(self):
        ret = WarningScreen(
                title="Caution",
                status_headline="You will display your encrypted KeyQR.",
                text= "This KeyQR will be encrypted with your Passphrase!",
                button_data=["I Understand"],
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        else:
            return Destination(KeyExportEncryptQRDisplayView, view_args=dict(key_num=self.key_num))

class KeyExportEncryptQRDisplayView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key = self.controller.get_key(key_num)
        self.key_num = key_num

    def run(self):
        if(self.key.getPasswordProtect()):
            ret = key_screens.KeyPassphraseScreen(title="Input Passphrase").display() 
            if ret == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)
            
            if(self.key.compareKey_passphrase(ret)==False):
                return Destination(KeyPassphraseEncryptKeyRetryView, view_args=dict(key_num=self.key_num))
        else:
            return Destination(KeyOptionsView, view_args=dict(key_num=self.key_num))
  
        qr_density = self.settings.get_value(SettingsConstants.SETTING__QR_DENSITY)
        qr_type = QRType.KEY__KEYQR
        self.key.set_encrypted_priv_key(ret)
        encrypted_key = self.key.get_encrypted_priv_key()
        if type(encrypted_key)==bytes:
            encrypted_key = encrypted_key.decode('utf-8')

        self.qr_encoder = EncodeQR(
            key_phrase=encrypted_key, 
            qr_type=qr_type,
            qr_density=qr_density,
        )
        ret2 = QRDisplayScreen(qr_encoder=self.qr_encoder).display()  
        return Destination(KeyOptionsView, view_args=dict(key_num=self.key_num))
    
class KeyPassphraseEncryptKeyRetryView(View):
    def __init__(self, key_num: int):
        self.key_num=key_num

    def run(self):
        BACK = "Back"
        RETRY = "Try Again"
        button_data = [RETRY,BACK]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Passphrase!",
            text=f"Please input the correct passphrase.",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == RETRY:
            return  Destination(KeyExportEncryptQRDisplayView,view_args=dict(key_num=self.key_num)) 
        elif button_data[selected_menu_num] == BACK:
            return Destination(KeyOptionsView, view_args=dict(key_num = self.key_num), clear_history=True)


"""****************************************************************************
    Key Discard View
****************************************************************************"""
class KeyDiscardView(View):
    def __init__(self, key_num: int = None):
        super().__init__()
        self.key_num = key_num
        if self.key_num is not None:
            self.key = self.controller.get_key(self.key_num)
        else:
            self.key = self.controller.inMemoryStore.pending_key

    def run(self):
        KEEP = "Keep key"
        DISCARD = ("Discard", None, None, "red")
        button_data = [KEEP, DISCARD]

        fingerprint = self.key.get_fingerprint()[:15] + "..."
        selected_menu_num = WarningScreen(
            title="Discard in Memory Key?!",
            status_headline=None,
            text=f"Wipe key {fingerprint} from the device?",
            show_back_button=False,
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == KEEP:
            # Use skip_current_view=True to prevent BACK from landing on this warning screen
            if self.key_num is not None:
                return Destination(KeyOptionsView, view_args=dict(key_num=self.key_num,), skip_current_view=True)
            else:
                return Destination(KeyFinalizeView, skip_current_view=True,)

        elif button_data[selected_menu_num] == DISCARD:
            if(self.key.getPasswordProtect()):
                ret = key_screens.KeyPassphraseScreen(title="Input Passphrase").display() 
                if ret == RET_CODE__BACK_BUTTON:
                    return Destination(BackStackView)
            
                if(self.key.compareKey_passphrase(ret)==False):
                    return Destination(KeyPassphraseDeleteRetryView, view_args=dict(key_num=self.key_num))

            if self.key_num is not None:
                self.controller.discard_key(self.key_num)
            else:
                self.controller.inMemoryStore.clear_pending_key()
            return Destination(MainMenuView, clear_history=True)
        
class KeyPassphraseDeleteRetryView(View):
    def __init__(self, key_num: int):
        self.key_num=key_num

    def run(self):
        BACK = "Back"
        RETRY = "Try Again"
        button_data = [RETRY, BACK]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Passphrase!",
            text=f"Please input the correct passphrase.",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == RETRY:
            return  Destination(KeyDiscardView,view_args=dict(key_num=self.key_num)) 
        elif button_data[selected_menu_num] == BACK:
            return Destination(KeyOptionsView, view_args=dict(key_num = self.key_num), clear_history=True)


"""****************************************************************************
    Key SubString Backup Test
****************************************************************************"""
class KeyBackupTestPromptView(View):
    def __init__(self, key_num: int):
        self.key_num = key_num

    def run(self):
        VERIFY = "Verify"
        SKIP = "Skip"
        button_data = [VERIFY, SKIP]
        selected_menu_num = key_screens.KeyBackupTestPromptScreen( 
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == VERIFY:
            return Destination(
                KeyBackupTestView,
                view_args=dict(key_num=self.key_num)
            )

        elif button_data[selected_menu_num] == SKIP:
            if self.key_num is not None:
                return Destination(KeyOptionsView, view_args=dict(key_num=self.key_num))
            else:
                return Destination(KeyFinalizeView)

class KeyBackupTestView(View):
    def __init__(self, key_num: int, confirmed_list: List[bool] = None, cur_index: int = None):
        super().__init__()
        self.key_num = key_num
        if self.key_num is None:
            self.key = self.controller.inMemoryStore.get_pending_key()
        else:
            self.key = self.controller.get_key(self.key_num)
        
        self.confirmed_list = confirmed_list
        if not self.confirmed_list:
            self.confirmed_list = []
         
        self.substrings = wrap(self.key.get_privateKey_backUp_flow(), SUBSTRING_LENGTH)
        self.cur_index = cur_index

    def run(self):
        if self.cur_index is None:
            self.cur_index = int(random.random() * len(self.substrings))
            while self.cur_index in self.confirmed_list:
                self.cur_index = int(random.random() * len(self.substrings))

        # initializing size of string
        real_string = self.substrings[self.cur_index]
        fake_string1 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=SUBSTRING_LENGTH))
        fake_string2 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=SUBSTRING_LENGTH))
        fake_string3 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=SUBSTRING_LENGTH))

        button_data = [real_string, fake_string1, fake_string2, fake_string3]
        random.shuffle(button_data)

        selected_menu_num = ButtonListScreen(
            title=f"Verify Substring #{self.cur_index + 1}",
            show_back_button=False,
            button_data=button_data,
            is_bottom_list=True,
            is_button_text_centered=True,
        ).display()

        if button_data[selected_menu_num] == real_string:
            self.confirmed_list.append(self.cur_index)
            if len(self.confirmed_list) == len(self.substrings):
                # Successfully confirmed the full key!
                return Destination(
                    KeyBackupTestSuccessView,
                    view_args=dict(key_num=self.key_num,)
                )
            else:
                # Continue testing the remaining substrings
                return Destination(
                    KeyBackupTestView,
                    view_args=dict(key_num=self.key_num, confirmed_list=self.confirmed_list,)
                )
        else:
            # Picked the WRONG Substring!
            return Destination(
                KeyBackupTestMistakeView,
                view_args=dict(
                    key_num=self.key_num,
                    cur_index=self.cur_index,
                    wrong_string=button_data[selected_menu_num],
                    confirmed_list=self.confirmed_list,
                )
            )

class KeyBackupTestMistakeView(View):
    def __init__(self, key_num: int, cur_index: int = None, wrong_string: str = None, confirmed_list: List[bool] = None):
        super().__init__()
        self.key_num = key_num
        self.cur_index = cur_index
        self.wrong_string = wrong_string
        self.confirmed_list = confirmed_list

    def run(self):
        REVIEW = "Review Key Substrings"
        RETRY = "Try Again"
        button_data = [REVIEW, RETRY]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Substring!",
            text=f"Substring #{self.cur_index + 1} is not \"{self.wrong_string}\"!",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == REVIEW:
            return Destination(
                KeyView,
                view_args=dict(key_num=self.key_num)
            )

        elif button_data[selected_menu_num] == RETRY:
            return Destination(
                KeyBackupTestView,
                view_args=dict(
                    key_num=self.key_num,
                    confirmed_list=self.confirmed_list,
                    cur_index=self.cur_index
                )
            )

class KeyBackupTestSuccessView(View):
    def __init__(self, key_num: int):
        self.key_num = key_num

    def run(self):
        LargeIconStatusScreen(
            title="Backup Verified",
            show_back_button=False,
            status_headline="Success!",
            text="Private Key is backed up and successfully verified!",
            button_data=["OK"]
        ).display()

        if self.key_num is not None:
            return Destination(KeyOptionsView, view_args=dict(key_num=self.key_num), clear_history=True)
        else:
            return Destination(KeyFinalizeView)

"""****************************************************************************
   Finalize Key View
****************************************************************************"""
class KeyFinalizeView(View):
    def __init__(self):
        super().__init__()
        self.key = self.controller.inMemoryStore.get_pending_key()
        self.fingerprint = self.key.get_fingerprint()

    def run(self):
        FINALIZE = "Done"
        PASSPHRASE = ("Add Passphrase", FontAwesomeIconConstants.LOCK)
        button_data = []

        button_data.append(FINALIZE)

        if self.settings.get_value(SettingsConstants.SETTING__PASSPHRASE) != SettingsConstants.OPTION__DISABLED:
            button_data.append(PASSPHRASE)

        selected_menu_num = key_screens.KeyFinalizeScreen( 
            fingerprint=self.fingerprint,
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == FINALIZE:
            self.controller.inMemoryStore.finalize_pending_key()
            return Destination(KeysMenuView, clear_history=True)

        elif button_data[selected_menu_num] == PASSPHRASE:
            return Destination(KeyReviewPassphraseView)

class KeyPassphraseRetryView(View):
    def __init__(self, key_num: int):
        self.key_num=key_num

    def run(self):
        BACK = "Back"
        RETRY = "Try Again"
        button_data = [RETRY, BACK]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Passphrase!",
            text=f"Please input the correct passphrase.",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == RETRY:
            return  Destination(KeyReviewPassphraseView,view_args=dict(key_num=self.key_num)) 
        elif button_data[selected_menu_num] == BACK:
            return Destination(KeyOptionsView, view_args=dict(key_num = self.key_num), clear_history=True)

class KeyReviewPassphraseView(View):
    def __init__(self):
        super().__init__()
        self.key = self.controller.inMemoryStore.get_pending_key()

    def run(self):
        # The new passphrase will be the return value
        ret = key_screens.KeyPassphraseScreen().display() 
        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
         
        EDIT = "Edit passphrase"
        DONE = "Done"
        button_data = [EDIT, DONE]
        fingerprint_with = self.key.get_fingerprint()[:4] + "..."
        fingerprint_without = self.key.get_fingerprint()[:4] + "..."
        # Because we have ane explicit "Edit" button, we disable "BACK" to keep the
        # routing options sane.
        #TODO: Review if showing password to the user is good for usablity or bad for security
        selected_menu_num = key_screens.KeyReviewPassphraseScreen( 
            fingerprint_without=fingerprint_without,
            fingerprint_with=fingerprint_with,
            passphrase=ret, 
            button_data=button_data,
            show_back_button=False,
        ).display()

        if button_data[selected_menu_num] == EDIT:
            return Destination(KeyReviewPassphraseView)
        
        elif button_data[selected_menu_num] == DONE:
            self.key.set_passphrase(ret)
            self.controller.inMemoryStore.finalize_pending_key()
            return Destination(KeysMenuView, clear_history=True)
            