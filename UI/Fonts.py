import pygame.font

pygame.font.init()

JOSEFINE_FILE = "./_fonts/JosefinSans-Bold.ttf"
MOLLE_FILE = "./_fonts/Molle-Regular.ttf"

fonts:dict[str,str] = {"josefin": JOSEFINE_FILE, "molle": MOLLE_FILE}

josefin = pygame.font.Font(JOSEFINE_FILE, 95)
molle = pygame.font.Font(MOLLE_FILE, 95)

board_timer = pygame.font.Font(JOSEFINE_FILE, 20)
loading_screen = pygame.font.Font(MOLLE_FILE, 115)
loading_screen_progress = pygame.font.Font(JOSEFINE_FILE, 15)

other_fonts:dict[tuple[str,int],pygame.font.Font] = {} # for fonts that can change in size.

def get_font(font_name:str, size:float) -> pygame.font.Font:
    if not isinstance(size, int): size = int(size)
    if (font_name, size) in other_fonts: return other_fonts[(font_name, size)]
    if font_name not in fonts: raise IndexError("Font \"%s\" does not exist!" % font_name)
    font_file = fonts[font_name]
    font = pygame.font.Font(font_file, size)
    other_fonts[(font_name, size)] = font
    return font

def get_fitted_font_size(text:str, font_name:str, max_size:int, max_width:int, max_height:int) -> float:
    '''Returns the size of a font that will fit in the size provided.'''
    start_font = get_font(font_name, max_size)
    start_font_size = start_font.size(text)
    new_size = max_size
    if start_font_size[0] > max_width:
        ratio = max_width / start_font_size[0]
        new_size = min(max_size * ratio, new_size)
    if start_font_size[1] > max_height:
        ratio = max_height / start_font_size[1]
        new_size = min(max_size * ratio, new_size)
    return new_size

def get_fitted_font(text:str, font_name:str, max_size:int, max_width:int, max_height:int) -> pygame.font.Font:
    '''Returns a Font that will fit in the size provided.'''
    return get_font(font_name, get_fitted_font_size(text, font_name, max_size, max_width, max_height))

def get_fitted_font_multi(texts:list[str], font_name:str, max_size:int, max_width:int, max_height:int) -> pygame.font.Font:
    '''Gets the smallest font size that will fit in the size provided.'''
    return get_font(font_name, min(get_fitted_font_size(text, font_name, max_size, max_width, max_height) for text in texts))
