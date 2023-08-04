import pygame.font

pygame.font.init()

JOSEFINE_FILE = "./_fonts/JosefinSans-Bold.ttf"
MOLLE_FILE = "./_fonts/Molle-Regular.ttf"

fonts:dict[str,str] = {"josefin": JOSEFINE_FILE, "molle": MOLLE_FILE}

josefin = pygame.font.Font(JOSEFINE_FILE, 95)
molle = pygame.font.Font(MOLLE_FILE, 95)

loading_screen = pygame.font.Font(MOLLE_FILE, 115)

other_fonts:dict[tuple[str,int],pygame.font.Font] = {} # for fonts that can change in size.

def get_font(font_name:str, size:int) -> pygame.font.Font:
    if not isinstance(size, int): size = int(size)
    if (font_name, size) in other_fonts: return other_fonts[(font_name, size)]
    if font_name not in fonts: raise IndexError("Font \"%s\" does not exist!" % font_name)
    font_file = fonts[font_name]
    font = pygame.font.Font(font_file, size)
    other_fonts[(font_name, size)] = font
    return font
