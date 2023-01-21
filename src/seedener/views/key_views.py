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
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen,
    WarningScreen, DireWarningScreen, key_screens)
from seedener.models.qr_type import QRType 
from seedener.models.encode_qr import EncodeQR 

SUBSTRING_LENGTH = 7
class KeysMenuView(View):
    def __init__(self):
        super().__init__()
        self.keys = []
        for key in self.controller.inMemoryStore.keys:
            self.keys.append({
                "fingerprint": key.get_fingerprint(),
                "has_passphrase": key.getPasswordProtect()
            })

    def run(self):
        if not self.keys:
            # Nothing to do here unless we have a key loaded
            return Destination(LoadKeyView, clear_history=True)

        button_data = []
        for key in self.keys:
            if(key["has_passphrase"]):
                button_data.append((key["fingerprint"][:15] + "...", SeedenerCustomIconConstants.FINGERPRINT, "blue"))
            else:
                button_data.append((key["fingerprint"][:15] + "...", SeedenerCustomIconConstants.FINGERPRINT, "gray"))

        button_data.append("Load a key")

        selected_menu_num = ButtonListScreen(
            title="In-Memory Keys",
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if len(self.keys) > 0 and selected_menu_num < len(self.keys):
            return Destination(KeyOptionsView, view_args=dict(key_num = selected_menu_num))

        elif selected_menu_num == len(self.keys):
            return Destination(LoadKeyView)

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

"""****************************************************************************
    Loading keys, passphrases, etc
****************************************************************************"""
class LoadKeyView(View):
    def run(self):
        KEY_QR = (" Scan a KeyQR", FontAwesomeIconConstants.QRCODE)
        CREATE = (" Create a key", FontAwesomeIconConstants.PLUS)
        button_data=[
            KEY_QR,
            CREATE,
        ]

        selected_menu_num = ButtonListScreen(
            title="Load A Key",
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        if button_data[selected_menu_num] == KEY_QR:
            from .scan_views import ScanView
            return Destination(ScanView)

        elif button_data[selected_menu_num] == CREATE:
            from .tools_views import ToolsCreateKeyView
            return Destination(ToolsCreateKeyView)

"""****************************************************************************
    View Key Substring flow
****************************************************************************"""
class KeyWarningView(View):
    def __init__(self, key_num: int, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.passphrase = passphrase

    def run(self):
        destination = Destination(
            KeyView,
            view_args=dict(
                key_num=self.key_num,
                page_index=0,
                passphrase=self.passphrase,
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

"""****************************************************************************
    Views for actions on individual keys:
****************************************************************************"""
class KeyOptionsView(View):
    def __init__(self, key_num: int): 
        super().__init__()
        self.key_num = key_num
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
            return Destination(KeyPasshpraseDecisionView, view_args=dict(key_num=self.key_num,))

        elif button_data[selected_menu_num] == DISCARD:
            return Destination(KeyDiscardView, view_args=dict(key_num=self.key_num,))

"""****************************************************************************
   Export Private Key flow
****************************************************************************"""
class KeyView(View):
    def __init__(self, key_num: int, page_index: int = 0, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.passphrase = passphrase
        if self.key_num is None:
            self.key = self.controller.inMemoryStore.get_pending_key()
        else:
            self.key = self.controller.get_key(self.key_num)
        
        self.page_index = page_index
        self.privKeyString = self.key.get_private(self.passphrase)
    
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
                        key_num=self.key_num,
                        passphrase=self.passphrase,
                    )
                )
            else:
                return Destination(
                    KeyView,
                    view_args=dict(
                        key_num=self.key_num, 
                        page_index=self.page_index + 1,
                        passphrase=self.passphrase,
                    )
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
    def __init__(self, key_num: int, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.passphrase = passphrase

    def run(self):
        STANDARD = "Standard: 29x29"
        COMPACT = "Compact: 25x25"
        num_modules_standard = 29
        num_modules_compact = 25

        if self.settings.get_value(SettingsConstants.SETTING__COMPACT_KEYQR) != SettingsConstants.OPTION__ENABLED:
            # Only configured for standard KeyQR
            return Destination(
                KeyTranscribeKeyQRWarningView,
                view_args={
                    "key_num": self.key_num,
                    "keyqr_format": QRType.KEY__KEYQR,
                    "num_modules": num_modules_standard,
                    "passphrase": self.passphrase,

                },
                skip_current_view=True,
            ) 

        button_data = [STANDARD, COMPACT]

        selected_menu_num = key_screens.KeyTranscribeKeyQRFormatScreen( 
            title="KeyQR Format",
            button_data=button_data,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        if button_data[selected_menu_num] == STANDARD: 
            keyqr_format = QRType.KEY__KEYQR
            num_modules = num_modules_standard
        else:
            keyqr_format = QRType.KEY__COMPACTKEYQR 
            num_modules = num_modules_compact
        
        return Destination(
            KeyTranscribeKeyQRWarningView,
                view_args={
                    "key_num": self.key_num,
                    "keyqr_format": keyqr_format,
                    "num_modules": num_modules,
                }
            )

class KeyTranscribeKeyQRWarningView(View):
    def __init__(self, key_num: int, keyqr_format: str = QRType.KEY__KEYQR, num_modules: int = 29, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.keyqr_format = keyqr_format
        self.num_modules = num_modules
        self.passphrase = passphrase

    def run(self):
        destination = Destination(
            KeyTranscribeKeyQRWholeQRView,
            view_args={
                "key_num": self.key_num,
                "keyqr_format": self.keyqr_format,
                "num_modules": self.num_modules,
                "passphrase": self.passphrase,

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
    def __init__(self, key_num: int, keyqr_format: str, num_modules: int, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.keyqr_format = keyqr_format
        self.num_modules = num_modules
        self.key = self.controller.get_key(key_num)
        self.passphrase = passphrase

    def run(self):
        e = EncodeQR(
            key_phrase=self.key.get_private(self.passphrase),
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
                    "passphrase": self.passphrase
                }
            )

class KeyTranscribeKeyQRZoomedInView(View):
    def __init__(self, key_num: int, keyqr_format: str, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num 
        self.keyqr_format = keyqr_format
        self.key = self.controller.get_key(key_num)
        self.passphrase = passphrase


    def run(self):
        e = EncodeQR(
            key_phrase=self.key.get_private(self.passphrase),
            qr_type=self.keyqr_format,
        )

        data = e.next_part()
        if self.keyqr_format == QRType.KEY__COMPACTKEYQR:
            num_modules = 21
        else:
            num_modules = 25

        key_screens.KeyTranscribeKeyQRZoomedInScreen( 
            qr_data=data,
            num_modules=num_modules,
        ).display()

        return Destination(KeyTranscribeKeyQRConfirmQRPromptView, view_args=dict(key_num=self.key_num, passphrase=self.passphrase))

class KeyTranscribeKeyQRConfirmQRPromptView(View):
    def __init__(self, key_num: int, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.key = self.controller.get_key(key_num)
        self.passphrase = passphrase

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
        #TODO: Implement Scan View first
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
            return Destination(KeyExportPubQRDisplayView, view_args=dict(key_num=self.key_num))

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

        qr_density = self.settings.get_value(SettingsConstants.SETTING__QR_DENSITY)
        qr_type = QRType.KEY__KEYQR
 
        self.qr_encoder = EncodeQR(
            key_phrase=self.key.get_pub(), 
            qr_type=qr_type,
            qr_density=qr_density,
        )

    def run(self):
        QRDisplayScreen(qr_encoder=self.qr_encoder).display()  
        return Destination(MainMenuView)

"""****************************************************************************
    Key Backup View
****************************************************************************"""
class KeyBackupView(View):
    def __init__(self, key_num, passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.key = self.controller.get_key(self.key_num)
        self.passphrase = passphrase

    def run(self):
        VIEW_SUBSTRINGS = "View Key"    
        EXPORT_KEYQR = "Export as KeyQR"
        button_data = [VIEW_SUBSTRINGS, EXPORT_KEYQR]

        selected_menu_num = ButtonListScreen(
            title="Backup Key",
            button_data=button_data,
            is_bottom_list=True,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == VIEW_SUBSTRINGS:
            return Destination(KeyWarningView, view_args=dict(key_num=self.key_num, passphrase=self.passphrase), clear_history=True)

        elif button_data[selected_menu_num] == EXPORT_KEYQR:
            return Destination(KeyTranscribeKeyQRFormatView, view_args=dict(key_num=self.key_num, passphrase=self.passphrase), clear_history=True)

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

        fingerprint = self.key.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK))
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
            if self.key_num is not None:
                self.controller.discard_key(self.key_num)
            else:
                self.controller.inMemoryStore.clear_pending_key()
            return Destination(MainMenuView, clear_history=True)

"""****************************************************************************
    Key SubString Backup Test
****************************************************************************"""
class KeyBackupTestPromptView(View):
    def __init__(self, key_num: int, passphrase: str = ""):
        self.key_num = key_num
        self.passhprase = passphrase

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
        
        self.substrings = wrap(self.key.get_private(), SUBSTRING_LENGTH)
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
            return Destination(MainMenuView, clear_history=True)

        elif button_data[selected_menu_num] == PASSPHRASE:
            return Destination(KeyAddPassphraseView)

class KeyAddPassphraseView(View):
    def __init__(self):
        super().__init__()
        self.key = self.controller.inMemoryStore.get_pending_key()

    def run(self):
        ret = key_screens.KeyPassphraseScreen().display()  

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        # The new passphrase will be the return value
        return Destination(KeyReviewPassphraseView, view_args=dict(passphrase=ret))

class KeyPasshpraseDecisionView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num
        if self.key_num is None:
            self.key = self.controller.inMemoryStore.get_pending_key()
        else:
            self.key = self.controller.get_key(self.key_num)

    def run(self):
        if(self.key.getPasswordProtect()):
            return  Destination(InputPassphraseView,view_args=dict(key_num=self.key_num))
        else:
            return Destination(KeyBackupView,view_args=dict(key_num=self.key_num, passphrase=""))


class InputPassphraseView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num
        self.passphrase: str = ""

    def run(self):
        ret = key_screens.KeyPassphraseScreen(title="Input Passphrase", passphrase=self.passphrase).display() 

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        # The passphrase will be the return value
        self.passphrase = ret
        return Destination(CheckKeyInputView,
                view_args=dict(
                key_num=self.key_num,
                passphrase=self.passphrase
            )
        )

class CheckKeyInputView(View):
    def __init__(self, key_num: int , passphrase: str = ""):
        super().__init__()
        self.key_num = key_num
        self.passphrase = passphrase
        if self.key_num is None:
            self.key = self.controller.inMemoryStore.get_pending_key()
        else:
            self.key = self.controller.get_key(self.key_num)
        
    def run(self):
        if(self.key.get_private(self.passphrase)!=""):
            return Destination(KeyBackupView, view_args=dict(key_num= self.key_num, passphrase=self.passphrase), clear_history=True)
        else:
            return Destination(KeyPassphraseRetryView, view_args=dict(key_num=self.key_num))


class KeyPassphraseRetryView(View):
    def __init__(self, key_num: int):
        self.key_num=key_num

    def run(self):
        BACK = "Back"
        RETRY = "Try Again"
        button_data = [BACK,RETRY]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Passphrase!",
            text=f"Please input the correct passphrase.",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == RETRY:
            return  Destination(InputPassphraseView,view_args=dict(key_num=self.key_num)) 
        elif button_data[selected_menu_num] == BACK:
            return Destination(KeyOptionsView, view_args=dict(key_num = self.key_num), clear_history=True)

class KeyReviewPassphraseView(View):
    def __init__(self, passphrase: str = ""):
        super().__init__()
        self.key = self.controller.inMemoryStore.get_pending_key()
        self.passhrase = passphrase

    def run(self):
        EDIT = "Edit passphrase"
        DONE = "Done"
        button_data = [EDIT, DONE]

        # Get the before/after fingerprints
        network = self.settings.get_value(SettingsConstants.SETTING__NETWORK)
        # Only 10 char for fingerprint for display purpose
        fingerprint_with = self.key.get_fingerprint()[:4] + "..."
        self.key.set_passphrase(self.passhrase)
        fingerprint_without = self.key.get_fingerprint()[:4] + "..."
        # Because we have ane explicit "Edit" button, we disable "BACK" to keep the
        # routing options sane.
        #TODO: Review if showing password to the user is good for usablity or bad for security
        #hiddenPassphrase = "*" * len(self.passhrase)
        selected_menu_num = key_screens.KeyReviewPassphraseScreen( 
            fingerprint_without=fingerprint_without,
            fingerprint_with=fingerprint_with,
            passphrase=self.passhrase, 
            button_data=button_data,
            show_back_button=False,
        ).display()

        if button_data[selected_menu_num] == EDIT:
            return Destination(KeyAddPassphraseView)
        
        elif button_data[selected_menu_num] == DONE:
            self.controller.inMemoryStore.finalize_pending_key()
            return Destination(KeysMenuView, clear_history=True)
            