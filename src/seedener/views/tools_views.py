import time
from textwrap import wrap

from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from seedener.gui.screens.screen import LoadingScreenThread
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedener.gui.screens.tools_screens import ToolsDiceEntropyEntryScreen, ToolsImageEntropyLivePreviewScreen, ToolsImageEntropyFinalImageScreen
from seedener.models.settings import SettingsConstants, SettingsDefinition
from seedener.models.key import Key

from seedener.views.key_views import KeyWarningView
from .view import View, Destination, BackStackView


class ToolsMenuView(View):
    def run(self):
        CREATE = ("Create seed", FontAwesomeIconConstants.PLUS)
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
        TWO = "Generate 2 Keys"
        FIVE = "Generate 5 Keys"
        
        button_data = [ONE, TWO, FIVE]
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

        elif button_data[selected_menu_num] == TWO:
            return Destination(ToolsCreateKeyEntryView, view_args=dict(total_keys=2))

        elif button_data[selected_menu_num] == FIVE:
            return Destination(ToolsCreateKeyEntryView, view_args=dict(total_keys=5))

class ToolsCreateKeyEntryView(View):
    def __init__(self, total_keys: int):
        super().__init__()
        self.total_keys = total_keys
    

    def run(self):
        ret = ToolsDiceEntropyEntryScreen(
            return_after_n_chars=self.total_keys,
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        key = Key()
        substrings = wrap(key.get_private(), 7) 
        print(key.get_private())
        print(substrings)   
        self.controller.inMemoryStore.set_pending_key(key)
        
        # Cannot return BACK to this View
        return Destination(KeyWarningView, view_args={"key_num": None}, clear_history=True)
