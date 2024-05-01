from multiprocessing.synchronize import Event
from multiprocessing.sharedctypes import Value


class TerminatedData:
    def __init__(self, event: Event, err_msg: Value) -> None:
        self.event = event
        self.err_msg = err_msg
    
    def set_event(self):
        self.event.set()

    def set_err_msg(self, value: str):
        self.err_msg.value = value