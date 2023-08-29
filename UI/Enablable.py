class Enablable():
    def __init__(self, start_enabled:bool=True) -> None:
        self.enabled = start_enabled
    
    def disable(self) -> None:
        self.enabled = False

    def enable(self) -> None:
        self.enabled = True