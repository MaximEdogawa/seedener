from .view import View, Destination, BackStackView, MainMenuView
from seedener.gui.components import FontAwesomeIconConstants
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen,)
from seedener.views.scan_views import ScanView
from seedener.views.key_views import LoadKeyView
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen, bundle_screens, WarningScreen)
from seedener.models.settings import SettingsConstants
from seedener.models.qr_type import QRType 
from seedener.models.encode_qr import EncodeQR 
from seedener.gui.screens.screen import QRDisplayScreen 
from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants
from seedener.gui.screens.screen import LoadingScreenThread, WarningScreen
from seedener.gui.screens.bundle_screens import BundleExportQrDisplayLoopScreen

class BundleMenuView(View):
        def __init__(self):
            super().__init__()
            self.bundles = []
            for bundle in self.controller.bundleStore.bundles:
                if(bundle.isSigned()):
                    fingerprint= bundle.get_signed_bundle()
                else:
                    fingerprint= bundle.get_unsigned_bundle()

                self.bundles.append({
                    "fingerprint": fingerprint,
                    "signed": bundle.isSigned()
                })

        def run(self):
            button_data = []
            if self.bundles: 
                for bundle in self.bundles:
                    if(bundle["signed"]):
                        button_data.append((bundle["fingerprint"][:15] + "...", FontAwesomeIconConstants.PEN, "blue"))
                    else:
                        button_data.append((bundle["fingerprint"][:15] + "...", FontAwesomeIconConstants.PEN, "gray"))

            button_data.append(" Scan a Spend Bundle")

            selected_menu_num = ButtonListScreen(
                title="Unsigned Spend Bundle",
                is_button_text_centered=False,
                button_data=button_data
            ).display()

            if len(self.bundles) > 0 and selected_menu_num < len(self.bundles):
                return Destination(BundleOptionsView, view_args=dict(bundle_num = selected_menu_num))

            elif selected_menu_num == len(self.bundles):
                return Destination(ScanView)

            elif selected_menu_num == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)

class BundleOptionsView(View):
        def __init__(self, bundle_num: int):
            super().__init__()
            self.bundle_num = bundle_num
            self.bundle = self.controller.get_bundle(self.bundle_num)

        def run(self):
            EXPORT_BUNDLE = "Export Spend Bundle"
            SIGN_BUNDLE = ("Sign Spend Bundle", None, None, None, FontAwesomeIconConstants.PEN)
            
            button_data = []
            button_data.append(EXPORT_BUNDLE)

            if self.bundle.isSigned():
                selected_menu_num = bundle_screens.BundleOptionsScreen(
                    button_data=button_data, 
                    fingerprint=self.bundle.get_signed_bundle()[:15] + "...",
                ).display() 
            else:
                button_data.append(SIGN_BUNDLE)
                selected_menu_num = bundle_screens.BundleOptionsScreen(
                    button_data=button_data, 
                    fingerprint=self.bundle.get_unsigned_bundle()[:15] + "...",
                ).display()
    
            if selected_menu_num == RET_CODE__BACK_BUTTON:
            # Force BACK to always return to the Main Menu
                return Destination(MainMenuView)
       
            elif button_data[selected_menu_num] == EXPORT_BUNDLE:
                return Destination(BundleExportView, view_args=dict(bundle_num=self.bundle_num,))

            elif button_data[selected_menu_num] == SIGN_BUNDLE:
                return Destination(BundleSignSelectKeysView, view_args=dict(bundle_num=self.bundle_num,))

class BundleExportView(View):
        def __init__(self, bundle_num: int):
            super().__init__()
            self.bundle_num = bundle_num
            self.bundle = self.controller.get_bundle(bundle_num)

        def run(self):
            if(self.bundle.isSigned()):
                fingerprint = self.bundle.get_signed_bundle()[:10]+ "..."
            else:
                fingerprint = self.bundle.get_unsigned_bundle()[:10]+ "..."
            
            ret = WarningScreen(
                title="Caution",
                status_headline="You will display the spend bundle of:",
                text= fingerprint,
                button_data=["I Understand"],
            ).display()
            
            if ret == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)
            else:
                return Destination(BundleExportQRDisplayView, view_args=dict(bundle_num=self.bundle_num))

class BundleExportQRDisplayView(View):
    def __init__(self, bundle_num: int):
        super().__init__()
        self.bundle = self.controller.get_bundle(bundle_num)
        self.header_size = { 'mode':1, 'chunk': 7, 'chunks': 7}
        self.bundle_phrase: str= ''
        self.qr_density = self.settings.get_value(SettingsConstants.SETTING__QR_DENSITY)
        self.qr_type = QRType.BUNDLE__QR
        self.bundle_num =bundle_num

        if(self.bundle.isSigned()):
            self.bundle_phrase = self.bundle.get_signed_bundle()
        else:
            self.bundle_phrase = self.bundle.get_unsigned_bundle()
 
    def run(self):
        BundleExportQrDisplayLoopScreen(  
            bundle_phrase=self.bundle_phrase,
            qr_density=self.qr_density,
            qr_type=self.qr_type
        )

        return Destination(BundleOptionsView, view_args=dict(bundle_num = self.bundle_num))


    
class BundleSignSelectKeysView(View):
    def __init__(self, bundle_num: int):
        super().__init__()
        self.bundle_num = bundle_num
        self.bundle = self.controller.get_bundle(bundle_num)
        self.keys = []
        for key in self.controller.inMemoryStore.keys:
            self.keys.append({
                "fingerprint": key.get_fingerprint(),
                "has_passphrase": key.getPasswordProtect(),
                "isSelected": key.getSelected()
            })
    
    def run(self):
        if not self.keys:
            # Nothing to do here unless we have a key loaded
            return Destination(LoadKeyView, clear_history=True)

        button_data = []
        for key in self.keys:
            if(key["isSelected"]):
                button_data.append((key["fingerprint"][:15] + "...", SeedenerCustomIconConstants.CIRCLE_CHECK, "blue"))
            else:
                button_data.append((key["fingerprint"][:15] + "...", SeedenerCustomIconConstants.CIRCLE_X, "blue"))

        selected_menu_num = ButtonListScreen(
            title="Sign spend Bundle",
            is_button_text_centered=False,
            button_data=button_data
        ).display()        

        button_data.append("Sign with selected Keys")

        if len(self.keys) > 0 and selected_menu_num < len(self.keys): 
            if(key["isSelected"]):
                return Destination(ToggleKeyForSigningView, view_args=dict(bundle_num=self.bundle_num, key_num=selected_menu_num, selected=False))
            else:
                return Destination(ToggleKeyForSigningView, view_args=dict(bundle_num=self.bundle_num, key_num=selected_menu_num, selected=True))

        elif selected_menu_num == len(self.keys):
            return Destination(SigneBundleView)

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView) 

class ToggleKeyForSigningView(View):
    def __init__(self, bundle_num: int, key_num: int, selected: bool=False):
        self.controller.get_key(key_num).setSelected(selected) 
        self.bundle_num=bundle_num
    def run(self):
        return Destination(BundleSignSelectKeysView, view_args=dict(bundle_num=self.bundle_num))


class SigneBundleView (View):
    def __init__(self, bundle_num: int):
        self.bundle_num = bundle_num
        self.bundle = self.controller.get_bundle(bundle_num)
    def run(self):
        self.loading_screen = LoadingScreenThread(text="Signing Bundle with Key:")
        self.loading_screen.start()
        for key in self.controller.inMemoryStore.keys:
            if(key["isSelected"]):
                self.bundle._signBundle(key.get_privateKey_forSigning)

        self.bundle._mergeSignedBundles()
        self.loading_screen.stop()
        fingerprint= self.bundle.get_signed_bundle()[:15]+ "..."
        ret = WarningScreen(
            title="Signing of Spend Bundle finished!",
            status_headline="You will display the signed Spend Bundle:",
            text= fingerprint,
            button_data=["I Understand"],
        ).display()
        
        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        else:
            return Destination(BundleExportQRDisplayView, view_args=dict(bundle_num=self.bundle_num))

