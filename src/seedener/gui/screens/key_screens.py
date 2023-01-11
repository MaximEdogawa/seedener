from dataclasses import dataclass
from seedener.gui.components import FontAwesomeIconConstants, GUIConstants, SeedenerCustomIconConstants
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedener.models.settings import Settings, SettingsConstants

@dataclass
class KeyOptionsScreen(ButtonListScreen):
    # Customize defaults
    fingerprint: str = None
    has_passphrase: bool = False

    def __post_init__(self):
        self.top_nav_icon_name = SeedenerCustomIconConstants.FINGERPRINT
        self.top_nav_icon_color = "blue"
        self.title = self.fingerprint
        self.is_button_text_centered = False
        self.is_bottom_list = True

        super().__post_init__()


