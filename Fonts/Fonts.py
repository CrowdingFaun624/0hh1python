import pygame.font

pygame.font.init()

JOSEFINE_FILE = "./Fonts/JosefinSans-Bold.ttf"
MOLLE_FILE = "./Fonts/Molle-Regular.ttf"

josefine = pygame.font.Font(JOSEFINE_FILE, 95)
molle = pygame.font.Font(MOLLE_FILE, 95)

loading_screen = pygame.font.Font(MOLLE_FILE, 115)