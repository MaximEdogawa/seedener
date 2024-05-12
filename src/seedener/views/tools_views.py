import time
from textwrap import wrap

from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from .bundle_views import BundleMenuView
from .key_views import CreateKeyEntryView
from .view import View, Destination, BackStackView
from .scan_views import ScanView

class ToolsMenuView(View):
    def run(self):
        SCAN = ("Scan key",FontAwesomeIconConstants.QRCODE)
        CREATE = ("Create key", FontAwesomeIconConstants.PLUS)
        SIGN = ("Sign bundle", FontAwesomeIconConstants.PEN)
        REKEY = ("Rekey", FontAwesomeIconConstants.KEY)
        button_data = [SCAN,CREATE, SIGN, REKEY]
        screen = ButtonListScreen(
            title="Tools",
            is_button_text_centered=False,
            button_data=button_data
        )
        selected_menu_num = screen.display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        elif button_data[selected_menu_num] == SCAN:
            return Destination(ScanView)

        elif button_data[selected_menu_num] == CREATE:
            return Destination(CreateKeyEntryView, view_args=dict(total_keys=1))

        elif button_data[selected_menu_num] == SIGN:
            return Destination(BundleMenuView)

        elif button_data[selected_menu_num] == REKEY:
            return Destination(ToolsCreateReKeyView)

"""****************************************************************************
    Create Key Views
****************************************************************************"""
class ToolsCreateReKeyView(View):
    def run(self):
        ONE = "Generate a new Key"
        
        button_data = [ONE]
        selected_menu_num = ButtonListScreen(
            title="Keys for Rekey",
            is_bottom_list=True,
            is_button_text_centered=True,
            button_data=button_data,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == ONE:
            return Destination(CreateKeyEntryView, view_args=dict(total_keys=1))


