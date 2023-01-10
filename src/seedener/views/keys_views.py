from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from .view import View, Destination, BackStackView, MainMenuView

from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen, settings_screens)
from seedener.models.settings import SettingsConstants, SettingsDefinition

class KeysMenuView(View):
    def __init(self):
        super().__init__()
        self.keys = []
        for key in self.controller.storage.keys:
            self.keys.append({
                "fingerprint": key.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK)),
                "has_passphrase": key.passphrase is not None
            })

    def run(self):
        if not self.keys:
            # Nothing to do here unless we have a key loaded
            return Destination(LoadKeysView, clear_history=True)

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