import time
import math

from dataclasses import dataclass
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFilter

from .screen import RET_CODE__BACK_BUTTON, BaseScreen, BaseTopNavScreen, ButtonListScreen, KeyboardScreen, WarningEdgesMixin
from seedener.gui.components import GUIConstants, SeedenerCustomIconConstants
from seedener.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from ..components import (Button, FontAwesomeIconConstants, Fonts, FormattedAddress, IconButton,
    IconTextLine, SeedenerCustomIconConstants, TextArea, GUIConstants,
    calc_text_centering)
from seedener.gui.keyboard import Keyboard, TextEntryDisplay

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

@dataclass
class KeyExportScreen(WarningEdgesMixin, ButtonListScreen):
    words: List[str] = None
    page_index: int = 0
    num_pages: int = 3
    is_bottom_list: bool = True
    status_color: str = GUIConstants.DIRE_WARNING_COLOR


    def __post_init__(self):
        super().__post_init__()

        words_per_page = len(self.words)

        self.body_x = 0
        self.body_y = self.top_nav.height - int(GUIConstants.COMPONENT_PADDING / 2)
        self.body_height = self.buttons[0].screen_y - self.body_y

        # Have to supersample the whole body since it's all at the small font size
        supersampling_factor = 1
        font = Fonts.get_font(GUIConstants.BODY_FONT_NAME, (GUIConstants.TOP_NAV_TITLE_FONT_SIZE + 2) * supersampling_factor)

        # Calc horizontal center based on longest word
        max_word_width = 0
        for word in self.words:
            (left, top, right, bottom) = font.getbbox(word, anchor="ls")
            if right > max_word_width:
                max_word_width = right

        # Measure the max digit height for the numbering boxes, from baseline
        number_font = Fonts.get_font(GUIConstants.BODY_FONT_NAME, GUIConstants.BUTTON_FONT_SIZE * supersampling_factor)
        (left, top, right, bottom) = number_font.getbbox("24", anchor="ls")
        number_height = -1 * top
        number_width = right
        number_box_width = number_width + int(GUIConstants.COMPONENT_PADDING/2 * supersampling_factor)
        number_box_height = number_box_width

        number_box_x = int((self.canvas_width * supersampling_factor - number_box_width - GUIConstants.COMPONENT_PADDING*supersampling_factor - max_word_width))/2
        number_box_y = GUIConstants.COMPONENT_PADDING * supersampling_factor

        # Set up our temp supersampled rendering surface
        self.body_img = Image.new(
            "RGB",
            (self.canvas_width * supersampling_factor, self.body_height * supersampling_factor),
            GUIConstants.BACKGROUND_COLOR
        )
        draw = ImageDraw.Draw(self.body_img)

        for index, word in enumerate(self.words):
            draw.rounded_rectangle(
                (number_box_x, number_box_y, number_box_x + number_box_width, number_box_y + number_box_height),
                fill="#202020",
                radius=5 * supersampling_factor
            )
            baseline_y = number_box_y + number_box_height - int((number_box_height - number_height)/2)
            draw.text(
                (number_box_x + int(number_box_width/2), baseline_y),
                font=number_font,
                text=str(self.page_index * words_per_page + index + 1),
                fill="#0084ff",
                anchor="ms"  # Middle (centered), baSeline
            )

            # Now draw the word
            draw.text(
                (number_box_x + number_box_width + (GUIConstants.COMPONENT_PADDING * supersampling_factor), baseline_y),
                font=font,
                text=word,
                fill=GUIConstants.BODY_FONT_COLOR,
                anchor="ls",  # Left, baSeline
            )

            number_box_y += number_box_height + (int(1.5*GUIConstants.COMPONENT_PADDING) * supersampling_factor)

        # Resize to target and sharpen final image
        self.body_img = self.body_img.resize((self.canvas_width, self.body_height), Image.LANCZOS)
        self.body_img = self.body_img.filter(ImageFilter.SHARPEN)
        self.paste_images.append((self.body_img, (self.body_x, self.body_y)))

@dataclass
class KeyFinalizeScreen(ButtonListScreen):
    fingerprint: str = None
    title: str = "Finalize Key"
    is_bottom_list: bool = True
    button_data: list = None

    def __post_init__(self):
        self.show_back_button = False

        super().__post_init__()

        self.fingerprint_icontl = IconTextLine(
            icon_name=SeedenerCustomIconConstants.FINGERPRINT,
            icon_color="blue",
            icon_size=GUIConstants.ICON_FONT_SIZE + 12,
            label_text="fingerprint",
            value_text=self.fingerprint,
            font_size=GUIConstants.BODY_FONT_SIZE + 2,
            is_text_centered=True,
            screen_y=self.top_nav.height + int((self.buttons[0].screen_y - self.top_nav.height) / 2) - 30
        )
        self.components.append(self.fingerprint_icontl)

@dataclass
class KeyAddPassphraseScreen(BaseTopNavScreen):
    title: str = "Add Passphrase"
    passphrase: str = ""

    KEYBOARD__LOWERCASE_BUTTON_TEXT = "abc"
    KEYBOARD__UPPERCASE_BUTTON_TEXT = "ABC"
    KEYBOARD__DIGITS_BUTTON_TEXT = "123"
    KEYBOARD__SYMBOLS_1_BUTTON_TEXT = "!@#"
    KEYBOARD__SYMBOLS_2_BUTTON_TEXT = "*[]"


    def __post_init__(self):
        super().__post_init__()

        keys_lower = "abcdefghijklmnopqrstuvwxyz"
        keys_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        keys_number = "0123456789"

        # Present the most common/puncutation-related symbols & the most human-friendly
        #   symbols first (limited to 18 chars).
        keys_symbol_1 = """!@#$%&();:,.-+='"?"""

        # Isolate the more math-oriented or just uncommon symbols
        keys_symbol_2 = """^*[]{}_\\|<>/`~"""


        # Set up the keyboard params
        self.right_panel_buttons_width = 56

        max_cols = 9
        text_entry_display_y = self.top_nav.height
        text_entry_display_height = 30

        keyboard_start_y = text_entry_display_y + text_entry_display_height + GUIConstants.COMPONENT_PADDING
        self.keyboard_abc = Keyboard(
            draw=self.renderer.draw,
            charset=keys_lower,
            rows=4,
            cols=max_cols,
            rect=(
                GUIConstants.COMPONENT_PADDING,
                keyboard_start_y,
                self.canvas_width - GUIConstants.COMPONENT_PADDING - self.right_panel_buttons_width,
                self.canvas_height - GUIConstants.EDGE_PADDING
            ),
            additional_keys=[
                Keyboard.KEY_SPACE_5,
                Keyboard.KEY_CURSOR_LEFT,
                Keyboard.KEY_CURSOR_RIGHT,
                Keyboard.KEY_BACKSPACE
            ],
            auto_wrap=[Keyboard.WRAP_LEFT, Keyboard.WRAP_RIGHT]
        )

        self.keyboard_ABC = Keyboard(
            draw=self.renderer.draw,
            charset=keys_upper,
            rows=4,
            cols=max_cols,
            rect=(
                GUIConstants.COMPONENT_PADDING,
                keyboard_start_y,
                self.canvas_width - GUIConstants.COMPONENT_PADDING - self.right_panel_buttons_width,
                self.canvas_height - GUIConstants.EDGE_PADDING
            ),
            additional_keys=[
                Keyboard.KEY_SPACE_5,
                Keyboard.KEY_CURSOR_LEFT,
                Keyboard.KEY_CURSOR_RIGHT,
                Keyboard.KEY_BACKSPACE
            ],
            auto_wrap=[Keyboard.WRAP_LEFT, Keyboard.WRAP_RIGHT],
            render_now=False
        )

        self.keyboard_digits = Keyboard(
            draw=self.renderer.draw,
            charset=keys_number,
            rows=3,
            cols=5,
            rect=(
                GUIConstants.COMPONENT_PADDING,
                keyboard_start_y,
                self.canvas_width - GUIConstants.COMPONENT_PADDING - self.right_panel_buttons_width,
                self.canvas_height - GUIConstants.EDGE_PADDING
            ),
            additional_keys=[
                Keyboard.KEY_CURSOR_LEFT,
                Keyboard.KEY_CURSOR_RIGHT,
                Keyboard.KEY_BACKSPACE
            ],
            auto_wrap=[Keyboard.WRAP_LEFT, Keyboard.WRAP_RIGHT],
            render_now=False
        )

        self.keyboard_symbols_1 = Keyboard(
            draw=self.renderer.draw,
            charset=keys_symbol_1,
            rows=4,
            cols=6,
            rect=(
                GUIConstants.COMPONENT_PADDING,
                keyboard_start_y,
                self.canvas_width - GUIConstants.COMPONENT_PADDING - self.right_panel_buttons_width,
                self.canvas_height - GUIConstants.EDGE_PADDING
            ),
            additional_keys=[
                Keyboard.KEY_SPACE_2,
                Keyboard.KEY_CURSOR_LEFT,
                Keyboard.KEY_CURSOR_RIGHT,
                Keyboard.KEY_BACKSPACE
            ],
            auto_wrap=[Keyboard.WRAP_LEFT, Keyboard.WRAP_RIGHT],
            render_now=False
        )

        self.keyboard_symbols_2 = Keyboard(
            draw=self.renderer.draw,
            charset=keys_symbol_2,
            rows=4,
            cols=6,
            rect=(
                GUIConstants.COMPONENT_PADDING,
                keyboard_start_y,
                self.canvas_width - GUIConstants.COMPONENT_PADDING - self.right_panel_buttons_width,
                self.canvas_height - GUIConstants.EDGE_PADDING
            ),
            additional_keys=[
                Keyboard.KEY_SPACE_2,
                Keyboard.KEY_CURSOR_LEFT,
                Keyboard.KEY_CURSOR_RIGHT,
                Keyboard.KEY_BACKSPACE
            ],
            auto_wrap=[Keyboard.WRAP_LEFT, Keyboard.WRAP_RIGHT],
            render_now=False
        )

        self.text_entry_display = TextEntryDisplay(
            canvas=self.renderer.canvas,
            rect=(
                GUIConstants.EDGE_PADDING,
                text_entry_display_y,
                self.canvas_width - self.right_panel_buttons_width,
                text_entry_display_y + text_entry_display_height
            ),
            cursor_mode=TextEntryDisplay.CURSOR_MODE__BAR,
            is_centered=False,
            cur_text=''.join(self.passphrase)
        )

        # Nudge the buttons off the right edge w/padding
        hw_button_x = self.canvas_width - self.right_panel_buttons_width + GUIConstants.COMPONENT_PADDING

        # Calc center button position first
        hw_button_y = int((self.canvas_height - GUIConstants.BUTTON_HEIGHT)/2)

        self.hw_button1 = Button(
            text=self.KEYBOARD__UPPERCASE_BUTTON_TEXT,
            is_text_centered=False,
            font_name=GUIConstants.FIXED_WIDTH_EMPHASIS_FONT_NAME,
            font_size=GUIConstants.BUTTON_FONT_SIZE + 4,
            width=self.right_panel_buttons_width,
            screen_x=hw_button_x,
            screen_y=hw_button_y - 3*GUIConstants.COMPONENT_PADDING - GUIConstants.BUTTON_HEIGHT,
        )

        self.hw_button2 = Button(
            text=self.KEYBOARD__DIGITS_BUTTON_TEXT,
            is_text_centered=False,
            font_name=GUIConstants.FIXED_WIDTH_EMPHASIS_FONT_NAME,
            font_size=GUIConstants.BUTTON_FONT_SIZE + 4,
            width=self.right_panel_buttons_width,
            screen_x=hw_button_x,
            screen_y=hw_button_y,
        )

        self.hw_button3 = IconButton(
            icon_name=FontAwesomeIconConstants.SOLID_CIRCLE_CHECK,
            icon_color=GUIConstants.SUCCESS_COLOR,
            width=self.right_panel_buttons_width,
            screen_x=hw_button_x,
            screen_y=hw_button_y + 3*GUIConstants.COMPONENT_PADDING + GUIConstants.BUTTON_HEIGHT,
        )

@dataclass
class KeyReviewPassphraseScreen(ButtonListScreen):
    fingerprint_without: str = None
    fingerprint_with: str = None
    passphrase: str = None

    def __post_init__(self):
        # Customize defaults
        self.title = "Verify Passphrase"
        self.is_bottom_list = True

        super().__post_init__()

        self.components.append(IconTextLine(
            icon_name=SeedenerCustomIconConstants.FINGERPRINT,
            icon_color="blue",
            label_text="changes fingerprint",
            value_text=f"{self.fingerprint_without} >> {self.fingerprint_with}",
            is_text_centered=True,
            screen_y = self.buttons[0].screen_y - GUIConstants.COMPONENT_PADDING - int(GUIConstants.BODY_FONT_SIZE*2.5)
        ))

        available_height = self.components[-1].screen_y - self.top_nav.height + GUIConstants.COMPONENT_PADDING
        max_font_size = GUIConstants.TOP_NAV_TITLE_FONT_SIZE + 8
        min_font_size = GUIConstants.TOP_NAV_TITLE_FONT_SIZE - 4
        font_size = max_font_size
        max_lines = 3
        passphrase = [self.passphrase]
        found_solution = False
        for font_size in range(max_font_size, min_font_size, -2):
            if found_solution:
                break
            font = Fonts.get_font(font_name=GUIConstants.FIXED_WIDTH_FONT_NAME, size=font_size)
            char_width, char_height = font.getsize("X")
            for num_lines in range(1, max_lines+1):
                # Break the passphrase into n lines
                chars_per_line = math.ceil(len(self.passphrase) / num_lines)
                passphrase = []
                for i in range(0, len(self.passphrase), chars_per_line):
                    passphrase.append(self.passphrase[i:i+chars_per_line])
                
                # See if it fits in this configuration
                if char_width * len(passphrase[0]) <= self.canvas_width - 2*GUIConstants.EDGE_PADDING:
                    # Width is good...
                    if num_lines * char_height <= available_height:
                        # And the height is good!
                        found_solution = True
                        break

        # Set up each line of text
        screen_y = self.top_nav.height + int((available_height - char_height*num_lines)/2) - GUIConstants.COMPONENT_PADDING
        for line in passphrase:
            self.components.append(TextArea(
                text=line,
                font_name=GUIConstants.FIXED_WIDTH_FONT_NAME,
                font_size=font_size,
                is_text_centered=True,
                screen_y=screen_y,
                allow_text_overflow=True
            ))
            screen_y += char_height + 2

@dataclass
class KeyBackupTestPromptScreen(ButtonListScreen):
    def __post_init__(self):
        self.title = "Verify Backup?"
        self.show_back_button = False
        self.is_bottom_list = True
        super().__post_init__()

        self.components.append(TextArea(
            text="Optionally verify that your mnemonic backup is correct.",
            screen_y=self.top_nav.height,
            is_text_centered=True,
        ))