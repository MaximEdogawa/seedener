import time
from textwrap import wrap

from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from seedener.gui.screens.screen import LoadingScreenThread, WarningScreen
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedener.gui.screens.tools_screens import ToolsImageEntropyLivePreviewScreen, ToolsImageEntropyFinalImageScreen
from seedener.models.settings import SettingsConstants, SettingsDefinition
from seedener.models.key import Key

from seedener.views.key_views import KeyWarningView
from .view import View, Destination, BackStackView


class ToolsMenuView(View):
    def run(self):
        CREATE = ("Create key", FontAwesomeIconConstants.PLUS)
        button_data = [CREATE]
        screen = ButtonListScreen(
            title="Tools",
            is_button_text_centered=False,
            button_data=button_data
        )
        selected_menu_num = screen.display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == CREATE:
            return Destination(ToolsCreateKeyView)

"""****************************************************************************
    Create Key Views
****************************************************************************"""
class ToolsCreateKeyView(View):
    def run(self):
        ONE = "Generate 1 Key"
        
        button_data = [ONE]
        selected_menu_num = ButtonListScreen(
            title="Keys to Generate",
            is_bottom_list=True,
            is_button_text_centered=True,
            button_data=button_data,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == ONE:
            return Destination(ToolsCreateKeyEntryView, view_args=dict(total_keys=1))

class ToolsCreateKeyEntryView(View):
    def __init__(self, total_keys: int):
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
        return Destination(KeyWarningView, view_args=dict(key_num= None, passphrase=""), clear_history=True)
