
from dataclasses import dataclass
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedener.gui.components import GUIConstants, FontAwesomeIconConstants

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