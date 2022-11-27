from ..iscreen import *

###############################################################
class OnionSkin(IScreen):
    def __init__(self, display):
        self.__display = display

    def display(self):
        return self.__display
        
    def refresh(self):
        self.__display.refresh()

    def begin_update_sequence(self):
        self.__display.begin_update_sequence()

    def in_update_sequence(self):
        return self.__display.in_update_sequence()

    def end_update_sequence(self):
        self.__display.end_update_sequence()

    def needs_update(self):
        return self.__display.needs_update()
    
    def notify_updated(self):
        return self.__display.notify_updated()

    def log_message(self, fgc, message):
        self.__display.log_message(fgc, message)

    def start_input_text(self, prompt):
        self.__display.start_input_text(prompt)
