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
from seedener.hardware.buttons import HardwareButtons, HardwareButtonsConstants
from seedener.helpers.qr import QR

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
class KeyPassphraseScreen(BaseTopNavScreen):
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


    def _render(self):
        super()._render()

        self.text_entry_display.render()
        self.hw_button1.render()
        self.hw_button2.render()
        self.hw_button3.render()
        self.keyboard_abc.render_keys()

        self.renderer.show_image()


    def _run(self):
        cursor_position = len(self.passphrase)

        cur_keyboard = self.keyboard_abc
        cur_button1_text = self.KEYBOARD__UPPERCASE_BUTTON_TEXT
        cur_button2_text = self.KEYBOARD__DIGITS_BUTTON_TEXT

        # Start the interactive update loop
        while True:
            input = self.hw_inputs.wait_for(
                HardwareButtonsConstants.ALL_KEYS,
                check_release=True,
                release_keys=[HardwareButtonsConstants.KEY_PRESS, HardwareButtonsConstants.KEY1, HardwareButtonsConstants.KEY2, HardwareButtonsConstants.KEY3]
            )

            keyboard_swap = False

            # Check our two possible exit conditions
            if input == HardwareButtonsConstants.KEY3:
                # Save!
                # First light up key3
                self.hw_button3.is_selected = True
                self.hw_button3.render()
                self.renderer.show_image()

                if len(self.passphrase) > 0:
                    return self.passphrase.strip()

            elif input == HardwareButtonsConstants.KEY_PRESS and self.top_nav.is_selected:
                # Back button clicked
                return self.top_nav.selected_button

            # Check for keyboard swaps
            if input == HardwareButtonsConstants.KEY1:
                # First light up key1
                self.hw_button1.is_selected = True
                self.hw_button1.render()

                # Return to the same button2 keyboard, if applicable
                if cur_keyboard == self.keyboard_digits:
                    cur_button2_text = self.KEYBOARD__DIGITS_BUTTON_TEXT
                elif cur_keyboard == self.keyboard_symbols_1:
                    cur_button2_text = self.KEYBOARD__SYMBOLS_1_BUTTON_TEXT
                elif cur_keyboard == self.keyboard_symbols_2:
                    cur_button2_text = self.KEYBOARD__SYMBOLS_2_BUTTON_TEXT

                if cur_button1_text == self.KEYBOARD__LOWERCASE_BUTTON_TEXT:
                    self.keyboard_abc.set_selected_key_indices(x=cur_keyboard.selected_key["x"], y=cur_keyboard.selected_key["y"])
                    cur_keyboard = self.keyboard_abc
                    cur_button1_text = self.KEYBOARD__UPPERCASE_BUTTON_TEXT
                else:
                    self.keyboard_ABC.set_selected_key_indices(x=cur_keyboard.selected_key["x"], y=cur_keyboard.selected_key["y"])
                    cur_keyboard = self.keyboard_ABC
                    cur_button1_text = self.KEYBOARD__LOWERCASE_BUTTON_TEXT
                cur_keyboard.render_keys()

                # Show the changes; this loop will have two renders
                self.renderer.show_image()

                keyboard_swap = True
                ret_val = None

            elif input == HardwareButtonsConstants.KEY2:
                # First light up key2
                self.hw_button2.is_selected = True
                self.hw_button2.render()
                self.renderer.show_image()

                # And reset for next redraw
                self.hw_button2.is_selected = False

                # Return to the same button1 keyboard, if applicable
                if cur_keyboard == self.keyboard_abc:
                    cur_button1_text = self.KEYBOARD__LOWERCASE_BUTTON_TEXT
                elif cur_keyboard == self.keyboard_ABC:
                    cur_button1_text = self.KEYBOARD__UPPERCASE_BUTTON_TEXT

                if cur_button2_text == self.KEYBOARD__DIGITS_BUTTON_TEXT:
                    self.keyboard_digits.set_selected_key_indices(x=cur_keyboard.selected_key["x"], y=cur_keyboard.selected_key["y"])
                    cur_keyboard = self.keyboard_digits
                    cur_keyboard.render_keys()
                    cur_button2_text = self.KEYBOARD__SYMBOLS_1_BUTTON_TEXT
                elif cur_button2_text == self.KEYBOARD__SYMBOLS_1_BUTTON_TEXT:
                    self.keyboard_symbols_1.set_selected_key_indices(x=cur_keyboard.selected_key["x"], y=cur_keyboard.selected_key["y"])
                    cur_keyboard = self.keyboard_symbols_1
                    cur_keyboard.render_keys()
                    cur_button2_text = self.KEYBOARD__SYMBOLS_2_BUTTON_TEXT
                elif cur_button2_text == self.KEYBOARD__SYMBOLS_2_BUTTON_TEXT:
                    self.keyboard_symbols_2.set_selected_key_indices(x=cur_keyboard.selected_key["x"], y=cur_keyboard.selected_key["y"])
                    cur_keyboard = self.keyboard_symbols_2
                    cur_keyboard.render_keys()
                    cur_button2_text = self.KEYBOARD__DIGITS_BUTTON_TEXT
                cur_keyboard.render_keys()

                # Show the changes; this loop will have two renders
                self.renderer.show_image()

                keyboard_swap = True
                ret_val = None

            else:
                # Process normal input
                if input in [HardwareButtonsConstants.KEY_UP, HardwareButtonsConstants.KEY_DOWN] and self.top_nav.is_selected:
                    # We're navigating off the previous button
                    self.top_nav.is_selected = False
                    self.top_nav.render_buttons()

                    # Override the actual input w/an ENTER signal for the Keyboard
                    if input == HardwareButtonsConstants.KEY_DOWN:
                        input = Keyboard.ENTER_TOP
                    else:
                        input = Keyboard.ENTER_BOTTOM
                elif input in [HardwareButtonsConstants.KEY_LEFT, HardwareButtonsConstants.KEY_RIGHT] and self.top_nav.is_selected:
                    # ignore
                    continue

                ret_val = cur_keyboard.update_from_input(input)

            # Now process the result from the keyboard
            if ret_val in Keyboard.EXIT_DIRECTIONS:
                self.top_nav.is_selected = True
                self.top_nav.render_buttons()

            elif ret_val in Keyboard.ADDITIONAL_KEYS and input == HardwareButtonsConstants.KEY_PRESS:
                if ret_val == Keyboard.KEY_BACKSPACE["code"]:
                    if cursor_position == 0:
                        pass
                    elif cursor_position == len(self.passphrase):
                        self.passphrase = self.passphrase[:-1]
                    else:
                        self.passphrase = self.passphrase[:cursor_position - 1] + self.passphrase[cursor_position:]

                    cursor_position -= 1

                elif ret_val == Keyboard.KEY_CURSOR_LEFT["code"]:
                    cursor_position -= 1
                    if cursor_position < 0:
                        cursor_position = 0

                elif ret_val == Keyboard.KEY_CURSOR_RIGHT["code"]:
                    cursor_position += 1
                    if cursor_position > len(self.passphrase):
                        cursor_position = len(self.passphrase)

                elif ret_val == Keyboard.KEY_SPACE["code"]:
                    if cursor_position == len(self.passphrase):
                        self.passphrase += " "
                    else:
                        self.passphrase = self.passphrase[:cursor_position] + " " + self.passphrase[cursor_position:]
                    cursor_position += 1

                # Update the text entry display and cursor
                self.text_entry_display.render(self.passphrase, cursor_position)

            elif input == HardwareButtonsConstants.KEY_PRESS and ret_val not in Keyboard.ADDITIONAL_KEYS:
                # User has locked in the current letter
                if cursor_position == len(self.passphrase):
                    self.passphrase += ret_val
                else:
                    self.passphrase = self.passphrase[:cursor_position] + ret_val + self.passphrase[cursor_position:]
                cursor_position += 1

                # Update the text entry display and cursor
                self.text_entry_display.render(self.passphrase, cursor_position)

            elif input in HardwareButtonsConstants.KEYS__LEFT_RIGHT_UP_DOWN or keyboard_swap:
                # Live joystick movement; haven't locked this new letter in yet.
                # Leave current spot blank for now. Only update the active keyboard keys
                # when a selection has been locked in (KEY_PRESS) or removed ("del").
                pass
        
            if keyboard_swap:
                # Show the hw buttons' updated text and not active state
                self.hw_button1.text = cur_button1_text
                self.hw_button2.text = cur_button2_text                
                self.hw_button1.is_selected = False
                self.hw_button2.is_selected = False
                self.hw_button1.render()
                self.hw_button2.render()

            self.renderer.show_image()

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

@dataclass
class KeyTranscribeKeyQRWholeQRScreen(WarningEdgesMixin, ButtonListScreen):
    qr_data: str = None
    num_modules: int = None

    def __post_init__(self):
        self.title = "Transcribe KeyQR"
        self.button_data = [f"Begin {self.num_modules}x{self.num_modules}"]
        self.is_bottom_list = True
        self.status_color = GUIConstants.DIRE_WARNING_COLOR
        super().__post_init__()

        qr_height = self.buttons[0].screen_y - self.top_nav.height - GUIConstants.COMPONENT_PADDING
        qr_width = qr_height

        qr = QR()
        qr_image = qr.qrimage(
            data=self.qr_data,
            width=qr_width,
            height=qr_height,
            border=1,
            style=QR.STYLE__ROUNDED
        ).convert("RGBA")

        self.paste_images.append((qr_image, (int((self.canvas_width - qr_width)/2), self.top_nav.height)))

@dataclass
class KeyTranscribeKeyQRZoomedInScreen(BaseScreen):
    qr_data: str = None
    num_modules: int = None

    def __post_init__(self):
        super().__post_init__()

        # Render an oversized QR code that we can view up close
        self.pixels_per_block = 24

        # Border must accommodate the 3 blocks outside the center 5x5 mask plus up to
        # 1 empty block inside the 5x5 mask (29x29 has a 4-block final col/row).
        self.qr_border = 4
        if self.num_modules == 21:
            # Optimize for 21x21
            self.qr_blocks_per_zoom = 7
        else:
            self.qr_blocks_per_zoom = 5

        self.qr_width = (self.qr_border + self.num_modules + self.qr_border) * self.pixels_per_block
        self.height = self.qr_width
        qr = QR()
        self.qr_image = qr.qrimage(
            self.qr_data,
            width=self.qr_width,
            height=self.height,
            border=self.qr_border,
            style=QR.STYLE__ROUNDED
        ).convert("RGBA")

        # Render gridlines but leave the 1-block border as-is
        draw = ImageDraw.Draw(self.qr_image)
        for i in range(self.qr_border, math.floor(self.qr_width/self.pixels_per_block) - self.qr_border):
            draw.line((i * self.pixels_per_block, self.qr_border * self.pixels_per_block, i * self.pixels_per_block, self.height - self.qr_border * self.pixels_per_block), fill="#bbb")
            draw.line((self.qr_border * self.pixels_per_block, i * self.pixels_per_block, self.qr_width - self.qr_border * self.pixels_per_block, i * self.pixels_per_block), fill="#bbb")

        # Prep the semi-transparent mask overlay
        # make a blank image for the overlay, initialized to transparent
        self.block_mask = Image.new("RGBA", (self.canvas_width, self.canvas_height), (255,255,255,0))
        draw = ImageDraw.Draw(self.block_mask)

        self.mask_width = int((self.canvas_width - self.qr_blocks_per_zoom * self.pixels_per_block)/2)
        self.mask_height = int((self.canvas_height - self.qr_blocks_per_zoom * self.pixels_per_block)/2)
        mask_rgba = (0, 0, 0, 226)
        draw.rectangle((0, 0, self.canvas_width, self.mask_height), fill=mask_rgba)
        draw.rectangle((0, self.canvas_height - self.mask_height - 1, self.canvas_width, self.canvas_height), fill=mask_rgba)
        draw.rectangle((0, self.mask_height, self.mask_width, self.canvas_height - self.mask_height), fill=mask_rgba)
        draw.rectangle((self.canvas_width - self.mask_width - 1, self.mask_height, self.canvas_width, self.canvas_height - self.mask_height), fill=mask_rgba)

        # Draw a box around the cutout portion of the mask for better visibility
        draw.line((self.mask_width, self.mask_height, self.mask_width, self.canvas_height - self.mask_height), fill=GUIConstants.ACCENT_COLOR)
        draw.line((self.canvas_width - self.mask_width, self.mask_height, self.canvas_width - self.mask_width, self.canvas_height - self.mask_height), fill=GUIConstants.ACCENT_COLOR)
        draw.line((self.mask_width, self.mask_height, self.canvas_width - self.mask_width, self.mask_height), fill=GUIConstants.ACCENT_COLOR)
        draw.line((self.mask_width, self.canvas_height - self.mask_height, self.canvas_width - self.mask_width, self.canvas_height - self.mask_height), fill=GUIConstants.ACCENT_COLOR)

        msg = "click to exit"
        font = Fonts.get_font(GUIConstants.BODY_FONT_NAME, GUIConstants.BODY_FONT_SIZE)
        (left, top, right, bottom) = font.getbbox(msg, anchor="ls")
        msg_height = -1 * top
        msg_width = right
        TextArea(
            canvas=self.block_mask,
            image_draw=draw,
            text=msg,
            background_color=GUIConstants.BACKGROUND_COLOR,
            is_text_centered=True,
            screen_y=self.canvas_height - GUIConstants.BODY_FONT_SIZE - GUIConstants.COMPONENT_PADDING,
            height=GUIConstants.BODY_FONT_SIZE + GUIConstants.COMPONENT_PADDING,
        ).render()


    def draw_block_labels(self, cur_block_x, cur_block_y):
        # Create overlay for block labels (e.g. "D-5")
        block_labels_x = ["1", "2", "3", "4", "5", "6"]
        block_labels_y = ["A", "B", "C", "D", "E", "F"]

        block_labels = Image.new("RGBA", (self.canvas_width, self.canvas_height), (255,255,255,0))
        draw = ImageDraw.Draw(block_labels)
        draw.rectangle((self.mask_width, 0, self.canvas_width - self.mask_width, self.pixels_per_block), fill=GUIConstants.ACCENT_COLOR)
        draw.rectangle((0, self.mask_height, self.pixels_per_block, self.canvas_height - self.mask_height), fill=GUIConstants.ACCENT_COLOR)

        label_font = Fonts.get_font(GUIConstants.FIXED_WIDTH_EMPHASIS_FONT_NAME, GUIConstants.TOP_NAV_TITLE_FONT_SIZE + 8)
        x_label = block_labels_x[cur_block_x]
        (left, top, right, bottom) = label_font.getbbox(x_label, anchor="ls")
        x_label_height = -1 * top

        draw.text(
            (int(self.canvas_width/2), self.pixels_per_block - int((self.pixels_per_block - x_label_height)/2)),
            text=x_label,
            fill=GUIConstants.BUTTON_SELECTED_FONT_COLOR,
            font=label_font,
            anchor="ms",  # Middle, baSeline
        )

        y_label = block_labels_y[cur_block_y]
        (left, top, right, bottom) = label_font.getbbox(y_label, anchor="ls")
        y_label_height = -1 * top
        draw.text(
            (int(self.pixels_per_block/2), int((self.canvas_height + y_label_height) / 2)),
            text=y_label,
            fill=GUIConstants.BUTTON_SELECTED_FONT_COLOR,
            font=label_font,
            anchor="ms",  # Middle, baSeline
        )

        return block_labels


    def _run(self):
        # Track our current coordinates for the upper left corner of our view
        cur_block_x = 0
        cur_block_y = 0
        cur_x = self.qr_border * self.pixels_per_block - self.mask_width
        cur_y = self.qr_border * self.pixels_per_block - self.mask_height
        next_x = cur_x
        next_y = cur_y

        block_labels = self.draw_block_labels(0, 0)

        self.renderer.show_image(
            self.qr_image.crop((cur_x, cur_y, cur_x + self.canvas_width, cur_y + self.canvas_height)),
            alpha_overlay=Image.alpha_composite(self.block_mask, block_labels)
        )

        while True:
            input = self.hw_inputs.wait_for(HardwareButtonsConstants.KEYS__LEFT_RIGHT_UP_DOWN + HardwareButtonsConstants.KEYS__ANYCLICK)
            if input == HardwareButtonsConstants.KEY_RIGHT:
                next_x = cur_x + self.qr_blocks_per_zoom * self.pixels_per_block
                cur_block_x += 1
                if next_x > self.qr_width - self.canvas_width:
                    next_x = cur_x
                    cur_block_x -= 1
            elif input == HardwareButtonsConstants.KEY_LEFT:
                next_x = cur_x - self.qr_blocks_per_zoom * self.pixels_per_block
                cur_block_x -= 1
                if next_x < 0:
                    next_x = cur_x
                    cur_block_x += 1
            elif input == HardwareButtonsConstants.KEY_DOWN:
                next_y = cur_y + self.qr_blocks_per_zoom * self.pixels_per_block
                cur_block_y += 1
                if next_y > self.height - self.canvas_height:
                    next_y = cur_y
                    cur_block_y -= 1
            elif input == HardwareButtonsConstants.KEY_UP:
                next_y = cur_y - self.qr_blocks_per_zoom * self.pixels_per_block
                cur_block_y -= 1
                if next_y < 0:
                    next_y = cur_y
                    cur_block_y += 1
            elif input in HardwareButtonsConstants.KEYS__ANYCLICK:
                return

            # Create overlay for block labels (e.g. "D-5")
            block_labels = self.draw_block_labels(cur_block_x, cur_block_y)

            if cur_x != next_x or cur_y != next_y:
                self.renderer.show_image_pan(
                    self.qr_image,
                    cur_x, cur_y, next_x, next_y,
                    rate=self.pixels_per_block,
                    alpha_overlay=Image.alpha_composite(self.block_mask, block_labels)
                )
                cur_x = next_x
                cur_y = next_y

@dataclass
class KeyTranscribeKeyQRConfirmQRPromptScreen(ButtonListScreen):
    def __post_init__(self):
        self.is_bottom_list = True
        super().__post_init__()

        self.components.append(TextArea(
            text="Optionally scan your transcribed KeyQR to confirm that it reads back correctly.",
            screen_y=self.top_nav.height,
            height=self.buttons[0].screen_y - self.top_nav.height,
        ))

@dataclass
class KeyTranscribeKeyQRFormatScreen(ButtonListScreen):
    def __post_init__(self):
        self.is_bottom_list = True
        super().__post_init__()

        self.components.append(IconTextLine(
            label_text="Standard",
            value_text="Key Substring indices",
            is_text_centered=False,
            auto_line_break=True,
            screen_x=GUIConstants.EDGE_PADDING,
            screen_y=self.top_nav.height + GUIConstants.COMPONENT_PADDING,
        ))
        self.components.append(IconTextLine(
            label_text="Compact",
            value_text="Raw entropy bits",
            is_text_centered=False,
            screen_x=GUIConstants.EDGE_PADDING,
            screen_y=self.components[-1].screen_y + self.components[-1].height + 2*GUIConstants.COMPONENT_PADDING,
        ))