import pygame
import Board as Board
import Drawable
import Colors
import Fonts.Fonts as Fonts
import Utilities.Animations as Animations
import Utilities.Bezier as Bezier

pygame.init()

screen = pygame.display.set_mode((640, 640))
clock = pygame.time.Clock()

# print("time,progress")

objects:list[Drawable.Drawable] = [
    Board.Board(6, colors=3)
]

running = True
ticks = 0
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
        tick_objects = object.tick(events, (0, 0))
        if tick_objects is not None: new_objects.extend(tick_objects)
        screen.blit(object.display(ticks), (0, 0))
        if object.should_destroy:
            new_objects.extend(object.destroy())
            destroy_objects.append(index)
    for index in reversed(destroy_objects): # reversed so it doesn't do weird stuff with indexes
        del objects[index]
    objects.extend(new_objects)


    # hello_world_surface = Fonts.molle.render("Hello, world", True, Colors.font)
    # screen.blit(hello_world_surface, (100 + 2 * Animations.animate(Animations.wiggle, 0.5, lambda _1, _2, x: x, (ticks/60)%1, True), 100))
    pygame.display.flip()
    clock.tick(60)
    ticks += 1
    # print(clock.get_fps())

pygame.quit()
