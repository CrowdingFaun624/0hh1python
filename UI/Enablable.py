import UI.Drawable as Drawable

class Enablable(Drawable.Drawable):
    def __init__(self, *args, **kwargs) -> None:
        self.enabled = kwargs["start_enabled"] if "start_enabled" in kwargs else True
        super().__init__(*args, **kwargs)
    
    def disable(self) -> None:
        self.enabled = False
        for child in self.children:
            if isinstance(child, Enablable): child.disable()

    def enable(self) -> None:
        self.enabled = True
        for child in self.children:
            if isinstance(child, Enablable): child.enable()