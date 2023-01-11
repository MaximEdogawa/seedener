from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from .view import View, Destination, BackStackView, MainMenuView

from seedener.controller import Controller
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen, settings_screens)
from seedener.models.settings import SettingsConstants, SettingsDefinition

from seedener.models.key import InvalidKeyException, Key
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen,
    WarningScreen, DireWarningScreen, key_screens)

class KeysMenuView(View):
    def __init__(self):
        super().__init__()
        self.keys = []
        for key in self.controller.inMemoryStore.keys:
            self.keys.append({
                "fingerprint": key.get_fingerprint(),
                "has_passphrase": key.passphrase is not None
            })

    def run(self):
        if not self.keys:
            # Nothing to do here unless we have a key loaded
            return Destination(LoadKeyView, clear_history=True)

        button_data = []
        for key in self.keys:
            button_data.append((key["fingerprint"], SeedenerCustomIconConstants.FINGERPRINT, "blue"))
        button_data.append("Load a key")

        selected_menu_num = ButtonListScreen(
            title="In-Memory Keys",
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if len(self.keys) > 0 and selected_menu_num < len(self.keys):
            return Destination(KeyOptionsView, view_args={"key_num": selected_menu_num})

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
            from .tools_views import ToolsMenuView
            return Destination(ToolsMenuView)

"""****************************************************************************
    View Key Words flow
****************************************************************************"""
class KeyWarningView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num

    def run(self):
        destination = Destination(
            view_args=dict(
                key_num=self.key_num,
                page_index=0,
            ),
            skip_current_view=True,  # Prevent going BACK to WarningViews
        )
        if self.settings.get_value(SettingsConstants.SETTING__DIRE_WARNINGS) == SettingsConstants.OPTION__DISABLED:
            # Forward straight to showing the words
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
            fingerprint=self.key.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK)),
            has_passphrase=self.key.passphrase is not None,
        ).display() 

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            # Force BACK to always return to the Main Menu
            return Destination(MainMenuView)
       
        elif button_data[selected_menu_num] == EXPORT_XPUB:
            return Destination(KeyExportPubTypeView, view_args=dict(key_num=self._num))

        elif button_data[selected_menu_num] == BACKUP:
            return Destination(KeyBackupView, view_args=dict(key_num=self.key_num))

        elif button_data[selected_menu_num] == DISCARD:
            return Destination(KeyDiscardView, view_args=dict(key_num=self.key_num))

"""****************************************************************************
    Export Pub flow
****************************************************************************"""
class KeyExportPubTypeView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num

"""****************************************************************************
    Export as SeedQR
****************************************************************************"""
class KeyTranscribeKeyQRFormatView(View):
    def __init__(self, key_num: int):
        super().__init__()
        self.key_num = key_num

"""****************************************************************************
    Key backup View
****************************************************************************"""
class KeyBackupView(View):
    def __init__(self, key_num):
        super().__init__()
        self.key_num = key_num
        self.key = self.controller.get_key(self.key_num)
    

    def run(self):
        VIEW_WORDS = "View Key Words"
        EXPORT_KEYQR = "Export as KeyQR"
        button_data = [VIEW_WORDS, EXPORT_KEYQR]

        selected_menu_num = ButtonListScreen(
            title="Backup Key",
            button_data=button_data,
            is_bottom_list=True,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == VIEW_WORDS:
            return Destination(KeyWarningView, view_args={"key_num": self.key_num})

        elif button_data[selected_menu_num] == EXPORT_KEYQR:
            return Destination(KeyTranscribeKeyQRFormatView, view_args={"key_num": self.key_num})

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
            self.seed = self.controller.inMemoryStore.pending_key