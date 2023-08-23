import time

import pygame

import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Textures as Textures
import UI.UIManager as UIManager


def extend_objects(objects_input:list[Drawable.Drawable], extension:list[tuple[Drawable.Drawable,int]]) -> None:
    '''Prepends items from extension with second item == -1 to objects, and appends items with 1.'''
    for new_object, position in extension:
        match position:
            case -1: objects_input.insert(0, new_object)
            case 1: objects_input.append(new_object)
            case _: raise ValueError("Invalid thing %s as ap- or pre-pending direction!" % str(position))

def get_children(object:Drawable.Drawable) -> list[Drawable.Drawable]:
    '''Recursively gets the children of the Drawable. Returns a list of the back-children, the parent object, and the front-children, in that order.'''
    objects:list[Drawable.Drawable] = []
    for child in object.children:
        objects.append(child)
        objects.extend(get_children(child))
    return objects

pygame.init()
DISPLAY_SIZE = (900, 900)
screen = pygame.display.set_mode(DISPLAY_SIZE)
pygame.display.set_icon(Textures.get("logo_32"))
pygame.display.set_caption("0h h1")
clock = pygame.time.Clock()
UIManager.reload_carrier = [False]

objects:list[Drawable.Drawable] = [
    UIManager.get_main_object()
]

running = True
while running:
    events:list[pygame.event.Event] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # print(event)
        events.append(event)
    
    screen.fill(Colors.get("background"))
    new_objects:list[Drawable.Drawable] = []
    destroy_objects:list[int] = []
    for index, object in enumerate(objects):
        object_children = [object] + get_children(object)
        tick_objects:list[tuple[Drawable.Drawable,int]] = []
        for child in object_children:
            child_return = child.tick(events, child.position)
            if child_return is not None: tick_objects.extend(child_return)
        new_objects.extend(tick_objects)
        screen.blits([(child_surface, child.position) for child in object_children if (child_surface := child.display()) is not None])
        if object.should_destroy:
            new_objects.extend(object.destroy())
            destroy_objects.append(index)
    for index in reversed(destroy_objects): # reversed so it doesn't do weird stuff with indexes
        del objects[index]
    extend_objects(objects, new_objects)
    if UIManager.reload_carrier[0]:
        UIManager.reload_carrier[0] = False
        for object in objects:
            object.reload(time.time())

    pygame.display.flip()
    clock.tick(60)
    # print(clock.get_fps())

for object in objects:
    object.delete()

pygame.quit()

# TODO: make button panel nicer.
# TODO: timer
# TODO: row/column counters
# TODO: row/column checkboxes
# TODO: local leaderboard and score
# TODO: medium mode
# TODO: accessibility
# TODO: tutorial
# TODO: release?
# TODO: global leaderboard
# TODO: resource packs
