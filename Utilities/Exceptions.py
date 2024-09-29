from typing import Optional

class AttributeNoneError(Exception):
    """An attribute of this class is None and should not be."""
    
    def __init__(self, name:str, source:object, message:Optional[str]=None) -> None:
        super().__init__(name, source, message)
        self.name = name
        self.source = source
        self.message = message
    
    def __str__(self) -> str:
        output = "Attribute \"%s\" of %r is None" % (self.name, self.source)
        output += "!" if self.message is None else " %s!" % (self.message,)
        return output