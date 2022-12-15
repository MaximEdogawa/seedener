import logging
import traceback
import os

from embit.descriptor import Descriptor
from PIL.Image import Image
from typing import List

from seedener.gui.renderer import Renderer
from seedener.hardware.buttons import HardwareButtons
from seedener.hardware.microsd import MicroSD
from seedener.views.screensaver import ScreensaverScreen
from seedener.views.view import Destination, NotYetImplementedView, UnhandledExceptionView

from .models import Seed, SeedStorage, Settings, Singleton

logger = logging.getLogger(__name__)

class BackStack(List[Destination]):
    def __repr__(self):
        if len(self) == 0:
            return "[]"
        out = "[\n"
        for index, destination in reversed(list(enumerate(self))):
            out += f"    {index:2d}: {destination}\n"
        out += "]"
        return out
            


class Controller(Singleton):
    VERSION = "0.0.1"
    buttons: HardwareButtons = None
    tmpStorage: SeedStorage = None
    settings: Settings = None
    renderer: Renderer = None
    unverified_address = None

    multisig_wallet_descriptor: Descriptor = None

    image_entropy_preview_frames: List[Image] = None
    image_entropy_final_image: Image = None

    address_explorer_data: dict = None

    FLOW__VERIFY_MULTISIG_ADDR = "multisig_addr"
    FLOW__VERIFY_SINGLESIG_ADDR = "singlesig_addr"
    FLOW__ADDRESS_EXPLORER = "address_explorer"
    resume_main_flow: str = None

    back_stack: BackStack = None
    screensaver: ScreensaverScreen = None


    @classmethod
    def get_instance(cls):
        if cls._instance:
            return cls._instance
        else:
            return cls.configure_instance()

    @classmethod
    def configure_instance(cls, disable_hardware=False):
        # Must be called before the first get_instance() call
        if cls._instance:
            raise Exception("Instance already configured")

        # Instantiate the one and only Controller instance
        controller = cls.__new__(cls)
        cls._instance = controller

        # Input Buttons
        if disable_hardware:
            controller.buttons = None
        else:
            controller.buttons = HardwareButtons.get_instance()

        # models
        controller.tmpStorage = SeedStorage()
        controller.settings = Settings.get_instance()
        
        controller.microsd = MicroSD.get_instance()
        controller.microsd.start_detection()

        # Configure the Renderer
        Renderer.configure_instance()
        controller.screensaver = ScreensaverScreen(controller.buttons)
        controller.back_stack = BackStack()

        # Other behavior constants
        controller.screensaver_activation_ms = 120 * 1000
    
        return cls._instance


    @property
    def camera(self):
        from .hardware.camera import Camera
        return Camera.get_instance()


    def get_seed(self, seed_num: int) -> Seed:
        if seed_num < len(self.tmpStorage.seeds):
            return self.tmpStorage.seeds[seed_num]
        else:
            raise Exception(f"There is no seed_num {seed_num}; only {len(self.tmpStorage.seeds)} in memory.")


    def discard_seed(self, seed_num: int):
        if seed_num < len(self.tmpStorage.seeds):
            del self.tmpStorage.seeds[seed_num]
        else:
            raise Exception(f"There is no seed_num {seed_num}; only {len(self.tmpStorage.seeds)} in memory.")


    def pop_prev_from_back_stack(self):
        from .views import Destination
        if len(self.back_stack) > 0:
            # Pop the top View (which is the current View_cls)
            self.back_stack.pop()

            if len(self.back_stack) > 0:
                # One more pop back gives us the actual "back" View_cls
                return self.back_stack.pop()
        return Destination(None)
    

    def clear_back_stack(self):
        self.back_stack = BackStack()


    def start(self) -> None:
        from .views import MainMenuView, BackStackView
        from .views.screensaver import OpeningSplashScreen

        opening_splash = OpeningSplashScreen()
        opening_splash.start()
        try:
            next_destination = Destination(MainMenuView)
            while True:
                # Destination(None) is a special case; render the Home screen
                if next_destination.View_cls is None:
                    next_destination = Destination(MainMenuView)

                if next_destination.View_cls == MainMenuView:
                    # Home always wipes the back_stack
                    self.clear_back_stack()
                    # Clear other temp vars
                    self.resume_main_flow = None
                    self.multisig_wallet_descriptor = None
                    self.unverified_address = None
                    self.address_explorer_data = None

                
                print(f"back_stack: {self.back_stack}")

                try:
                    print(f"Executing {next_destination}")
                    next_destination = next_destination.run()
                except Exception as e:
                    # Display user-friendly error screen w/debugging info
                    next_destination = self.handle_exception(e)

                if not next_destination:
                    # Should only happen during dev when you hit an unimplemented option
                    next_destination = Destination(NotYetImplementedView)

                if next_destination.skip_current_view:
                    # Remove the current View from history; it's forwarding us straight
                    # to the next View so it should be as if this View never happened.
                    current_view = self.back_stack.pop()
                    print(f"Skipping current view: {current_view}")

                # Hang on to this reference...
                clear_history = next_destination.clear_history

                if next_destination.View_cls == BackStackView:
                    # "Back" arrow was clicked; load the previous view
                    next_destination = self.pop_prev_from_back_stack()

                if clear_history:
                    self.clear_back_stack()

                if len(self.back_stack) == 0 or self.back_stack[-1] != next_destination:
                    print(f"Appending next destination: {next_destination}")
                    self.back_stack.append(next_destination)
                else:
                    print(f"NOT appending {next_destination}")
                
                print("-" * 30)

        finally:
            if self.screensaver.is_running:
                self.screensaver.stop()

            print("Clearing screen, exiting")
            Renderer.get_instance().display_blank_screen()


    def start_screensaver(self):
        self.screensaver.start()

    def handle_exception(self, e) -> Destination:
        logger.exception(e)
        last_line = traceback.format_exc().splitlines()[-1]
        exception_type = last_line.split(":")[0].split(".")[-1]
        exception_msg = last_line.split(":")[1]

        # Scan for the last debugging line that includes a line number reference
        line_info = None
        for i in range(len(traceback.format_exc().splitlines()) - 1, 0, -1):
            traceback_line = traceback.format_exc().splitlines()[i]
            if ", line " in traceback_line:
                line_info = traceback_line.split("/")[-1].replace("\"", "").replace("line ", "")
                break
        
        error = [
            exception_type,
            line_info,
            exception_msg,
        ]
        return Destination(UnhandledExceptionView, view_args={"error": error}, clear_history=True)
