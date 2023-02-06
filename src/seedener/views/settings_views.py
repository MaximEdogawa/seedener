from seedener.gui.components import FontAwesomeIconConstants, SeedenerCustomIconConstants

from .view import View, Destination, BackStackView, MainMenuView

from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen, settings_screens)
from seedener.models.settings import SettingsConstants, SettingsDefinition



class SettingsMenuView(View):
    def __init__(self, visibility: str = SettingsConstants.VISIBILITY__GENERAL, selected_attr: str = None):
        super().__init__()
        self.visibility = visibility
        self.selected_attr = selected_attr


    def run(self):
        IO_TEST = "I/O test"
        DONATE = "Donate"

        settings_entries = SettingsDefinition.get_settings_entries(
            visibiilty=self.visibility
        )
        button_data=[e.display_name for e in settings_entries]

        selected_button = 0
        if self.selected_attr:
            for i, entry in enumerate(settings_entries):
                if entry.attr_name == self.selected_attr:
                    selected_button = i
                    break

        if self.visibility == SettingsConstants.VISIBILITY__GENERAL:
            title = "Settings"

            # Set up the next nested level of menuing
            button_data.append(("Advanced", None, None, None, SeedenerCustomIconConstants.SMALL_CHEVRON_RIGHT))
            next = Destination(SettingsMenuView, view_args={"visibility": SettingsConstants.VISIBILITY__ADVANCED})

            button_data.append(IO_TEST)
            button_data.append(DONATE)

        elif self.visibility == SettingsConstants.VISIBILITY__ADVANCED:
            title = "Advanced"

            # So far there are no real Developer options; disabling for now
            # button_data.append(("Developer Options", None, None, None, SeedenerCustomIconConstants.SMALL_CHEVRON_RIGHT))
            # next = Destination(SettingsMenuView, view_args={"visibility": SettingsConstants.VISIBILITY__DEVELOPER})
            next = None
        
        elif self.visibility == SettingsConstants.VISIBILITY__DEVELOPER:
            title = "Dev Options"
            next = None

        selected_menu_num = ButtonListScreen(
            title=title,
            is_button_text_centered=False,
            button_data=button_data,
            selected_button=selected_button,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            if self.visibility == SettingsConstants.VISIBILITY__GENERAL:
                return Destination(MainMenuView)
            elif self.visibility == SettingsConstants.VISIBILITY__ADVANCED:
                return Destination(SettingsMenuView)
            else:
                return Destination(SettingsMenuView, view_args={"visibility": SettingsConstants.VISIBILITY__ADVANCED})
        
        elif selected_menu_num == len(settings_entries):
            return next

        elif len(button_data) > selected_menu_num and button_data[selected_menu_num] == IO_TEST:
            return Destination(IOTestView)

        elif len(button_data) > selected_menu_num and button_data[selected_menu_num] == DONATE:
            return Destination(DonateView)

"""****************************************************************************
    Misc
****************************************************************************"""
class IOTestView(View):
    def run(self):
        settings_screens.IOTestScreen().display()

        return Destination(SettingsMenuView)

class DonateView(View):
    def run(self):
        settings_screens.DonateScreen().display()

        return Destination(SettingsMenuView)
