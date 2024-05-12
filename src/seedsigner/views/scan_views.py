import json
import re

from seedsigner.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from .view import View, Destination, BackStackView, MainMenuView, NotYetImplementedView

from seedsigner.gui.screens import (RET_CODE__BACK_BUTTON, DireWarningScreen, key_screens)
from seedsigner.models.settings import SettingsConstants, SettingsDefinition
from seedsigner.models import DecodeQR, Key, Bundle, Encrypt

class ScanView(View):
    def run(self):
        from seedsigner.gui.screens.scan_screen import ScanScreen 
        self.decoder = DecodeQR()
        # Start the live preview and background QR reading
        ScanScreen(decoder=self.decoder).display()

        # Handle the results
        if self.decoder.is_complete:
            if self.decoder.is_key:
                key_phrase = self.decoder.get_key_phrase()
                if not key_phrase:
                    # key is not valid, Exit if not valid with message
                    raise Exception("Key is not valid!")
                else:
                    # Found a valid Secret Component! All new keys should be considered
                    self.controller.inMemoryStore.set_pending_key(
                        Key(priv_key=key_phrase)
                    )
                    if self.settings.get_value(SettingsConstants. SETTING__PRIVACY_WARNINGS) == SettingsConstants.OPTION__REQUIRED:
                        from seedsigner.views.key_views import KeyWarningView
                        return Destination(KeyWarningView)
                    else:
                        from seedsigner.views.key_views import  KeyFinalizeView
                        return Destination(KeyFinalizeView)

            elif self.decoder.is_spendBundle:
                spendBundle = self.decoder.get_spend_bundle()
                
                if not spendBundle:
                     raise Exception("Spend bundle is not valid!") 
                else:
                    self.controller.bundleStore.set_pending_bundle(
                            Bundle(unsigned_bundle=spendBundle)
                    )
                    # Disabled hash check! TODO: Write a better implementation for hash check on seedener side and seedsaver_wallet.
                    self.controller.bundleStore.finalize_pending_bundle()
                    #TODO: Implement Signing Screen for Spend Bundles
                    from seedsigner.views.bundle_views import BundleMenuView
                    return Destination(BundleMenuView)
                    
            elif self.decoder.is_encrypted_key:
                encrypted_key = self.decoder.get_encrypted_key_phrase()
                if not encrypted_key:
                    # key is not valid, Exit if not valid with message
                    raise Exception("Encrypted Key is not valid!")
                else:  
                    decoded=""
                    QUIT = "Quit to Menu"
                    RETRY = "Try Again"
                    button_data = [RETRY, QUIT]
                    while decoded == "":
                        ret = key_screens.KeyPassphraseScreen(title="Input Passphrase").display() 
                        decoded_key_phrase=Encrypt.decrypt_string(encrypted_key,ret)
                        if not decoded_key_phrase:
                            selected_menu_num = DireWarningScreen(
                                title="Confirm Passphrase",
                                status_headline="Error!",
                                text="Your Passphrase is not correct!",
                                show_back_button=False,
                                button_data=button_data,
                            ).display() 
                            if button_data[selected_menu_num] == QUIT:
                                return Destination(MainMenuView)
                        else:
                            # Found a valid Secret Component! All new keys should be considered
                            self.controller.inMemoryStore.set_pending_key(
                                Key(priv_key=decoded_key_phrase)
                            )
                            key = self.controller.inMemoryStore.get_pending_key()
                            key.set_passphrase(ret)
                            self.controller.inMemoryStore.finalize_pending_key()
                            from seedsigner.views.key_views import KeysMenuView
                            return Destination(KeysMenuView)
            else:
                return Destination(NotYetImplementedView)

        return Destination(MainMenuView)


class SettingsUpdatedView(View):
    def __init__(self, config_name: str):
        super().__init__()
        self.config_name = config_name

    def run(self):
        from seedsigner.gui.screens.scan_screen import SettingsUpdatedScreen
        screen = SettingsUpdatedScreen(config_name=self.config_name)
        selected_menu_num = screen.display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        # Only one exit point
        return Destination(MainMenuView)
