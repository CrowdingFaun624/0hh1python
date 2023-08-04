import pygame

import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.LevelSelector as LevelSelector
import Utilities.Animations as Animations
import Utilities.Bezier as Bezier


def extend_objects(objects_input:list[Drawable.Drawable], extension:list[tuple[Drawable.Drawable,int]]) -> None:
    '''Prepends items from extension with second item == -1 to objects, and appends items with 1.'''
    for new_object, position in extension:
        match position:
            case -1: objects_input.insert(0, new_object)
            case 1: objects_input.append(new_object)
            case _: raise ValueError("Invalid thing %s as ap- or pre-pending direction!" % str(position))

pygame.init()
DISPLAY_SIZE = (900, 900)
screen = pygame.display.set_mode(DISPLAY_SIZE)
clock = pygame.time.Clock()

# print("time,progress")

objects:list[Drawable.Drawable] = [
    LevelSelector.LevelSelector(DISPLAY_SIZE)
    # Board.Board(6, colors=3)
]

running = True
while running:
    events:list[pygame.event.Event] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # print(event)
        events.append(event)
    
    screen.fill(Colors.background)
    new_objects:list[Drawable.Drawable] = []
    destroy_objects:list[int] = []
    for index, object in enumerate(objects):
        tick_objects = object.tick(events, object.position)
        if tick_objects is not None: new_objects.extend(tick_objects)
        screen.blit(object.display(), object.position)
        if object.should_destroy:
            new_objects.extend(object.destroy())
            destroy_objects.append(index)
    for index in reversed(destroy_objects): # reversed so it doesn't do weird stuff with indexes
        del objects[index]
    extend_objects(objects, new_objects)


    # hello_world_surface = Fonts.molle.render("Hello, world", True, Colors.font)
    # screen.blit(hello_world_surface, (100 + 2 * Animations.animate(Animations.wiggle, 0.5, lambda _1, _2, x: x, (ticks/60)%1, True), 100))
    pygame.display.flip()
    clock.tick(60)
    # print(clock.get_fps())

pygame.quit()
