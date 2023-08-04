import cProfile
from math import ceil
import os
import random
import re

try:
    import LevelCreator.LevelPrinter as LevelPrinter
    import LevelCreator.LevelSolver as LevelSolver
    import LevelCreator.LevelValidator as LevelValidator
except ImportError:
    import LevelPrinter
    import LevelSolver
    import LevelValidator

def generate_solution(size:tuple[int,int], seed:int=None, colors:int=2) -> list[int]:
    # wave collapse algorithm
    random_range = list(range(size[0] * size[1]))
    random.shuffle(random_range)
    DEFAULT = list(range(1, colors + 1))
    tiles = [DEFAULT[:] for i in random_range]
    tiles_tries = [DEFAULT[:] for i in random_range] # pops from here each time a tile is collapsed
    for tiles_try in tiles_tries: random.shuffle(tiles_try)
    tiles_tries_originals = [tile_try[:] for tile_try in tiles_tries] # for restoration upon backtracking
    dependencies = [[] for i in random_range] # TODO: instead of dependencies, store a copy of the tiles at each tile.
    collapsed_tiles:list[tuple[int,int]] = [] # stack containing tile indexes that were collapsed and their position in random_range
    index = 0
    while index < len(random_range):
        tile_index = random_range[index]
        # tile_index = index # TODO: measure performance impact of this instead of line above.
        if len(tiles[tile_index]) == 1: index += 1; continue
        collapsed_tiles.append((tile_index, index))
        success = False
        while not success:
            if len(tiles_tries[index]) == 0: break
            for pick_value in tiles_tries[index]:
                if pick_value in tiles[tile_index]: break
            else: assert False
            tiles_tries[index].remove(pick_value)
            tiles[tile_index] = [pick_value]
            # print("Before %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            LevelSolver.solve(size, colors, tiles, None, dependencies) # TODO: make the starting rows_to_solve and columns_to_solve be only the ones with the set tile.
            # print("After: %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            if LevelValidator.is_valid(tiles, size, colors):
                index += 1
                # print("+%i" % index)
                success = True
                break
            else:
                strip_dependencies(dependencies, tile_index, tiles, colors)
                continue
        if not success:
            # print("Before strip: %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            # print(collapsed_tiles)
            collapsed_tiles.pop() # current tile; can be discarded
            backtrack_amount = 1 # int(len(collapsed_tiles) * 0.5)
            for i in range(backtrack_amount):
                tiles_tries[index] = tiles_tries_originals[index][:]
                tile_index, index = collapsed_tiles.pop()
                strip_dependencies(dependencies, tile_index, tiles, colors) # TODO: consider different amounts of backtracking, such as halfway, two, four, etc.
            # print("After strip: %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            # print(collapsed_tiles)
    if not LevelValidator.is_valid(tiles, size, colors):
        LevelPrinter.print_board(tiles, size)
        raise RuntimeError("An invalid board was generated!")
    tiles = collapse_board(tiles, colors, True)
    if 0 in tiles:
        LevelPrinter.print_board(tiles, size)
        raise RuntimeError("The board has empty tiles!")
    return tiles
    

def count_empty_tiles(tiles:list[int]) -> int:
    return tiles.count(0)
def count_unknown_tiles(tiles:list[list[int]]) -> int:
    '''Returns the number of tiles whose values are not completely known.'''
    return [len(tile) == 1 for tile in tiles].count(False)

def rotate_board(board:list[int], current_size:tuple[int,int]) -> list[int]:
    '''swaps the board's x and y positions.'''
    output:list[int] = [0] * len(board)
    new_size = (current_size[1], current_size[0])
    for old_index, tile in enumerate(board):
        old_pos = get_pos(old_index, current_size)
        new_pos = (old_pos[1], old_pos[0])
        new_index = get_index(new_pos, new_size)
        output[new_index] = tile
    return output

def get_pos(index:int, size:tuple[int,int]) -> tuple[int,int]:
    return (index % size[0], index // size[0])
def get_index(pos:tuple[int,int], size:tuple[int,int]) -> int:
    return (pos[0] + pos[1] * size[0])

def generate(size:int|tuple[int,int], seed:int=None, colors:int=2) -> tuple[list[int],list[int],dict[str,any]]:
    '''Returns the solution, the incomplete puzzle, and other data.'''

    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    if isinstance(size, int): size = (size, size)
    if size[0] % colors != 0: raise ValueError("Invalid width for %s colors!" % colors)
    elif size[1] % colors != 0: raise ValueError("Invalid height for %s colors!" % colors)
    if size[0] > size[1]: solution_generator_size = (size[1], size[0]); is_rotated = True
    else: solution_generator_size = size; is_rotated = False
    full_grid = generate_solution(solution_generator_size, seed, colors)
    if is_rotated: full_grid = rotate_board(full_grid, solution_generator_size)

    empty_grid = breakdown(full_grid, size, seed, colors)
    quality = round(count_empty_tiles(empty_grid) / (size[0] * size[1]) * 100) # how many empty tiles there are
    other_data = {"seed": seed, "quality": quality}
    random.seed(after_seed)
    return full_grid, empty_grid, other_data

def restore_cache(tiles_values:list[list[int]], tiles_cache:list[list[int]], colors:int) -> None:
    DEFAULT = list(range(1, colors + 1))
    for index, tile in enumerate(tiles_cache):
        if tile != DEFAULT: tiles_values[index] = tile[:]

def strip_dependencies(dependencies:list[list[int]], tile_index:int, tiles_cache:list[list[int]], colors:int) -> None:
    '''Removes tiles related to the given tile and resets their dependencies''' # TODO: remove the parameter `tiles`
    DEFAULT = list(range(1, colors + 1))
    affected_tiles = set([tile_index])
    while True:
        before_length = len(affected_tiles)
        new_tiles:set[int] = set()
        for affected_tile in affected_tiles:
            for tile, tile_dependencies in enumerate(dependencies):
                if affected_tile in tile_dependencies: new_tiles.add(tile)
        affected_tiles = affected_tiles | new_tiles
        if len(affected_tiles) == before_length: break
    for affected_tile in affected_tiles:
        dependencies[affected_tile] = []
        tiles_cache[affected_tile] = DEFAULT[:]

def collapse_board(tiles:list[list[int]], colors:int=None, strict:bool=False) -> list[int]:
    output:list[int] = []
    for tile_index, tile in enumerate(tiles):
        if len(tile) == 0: raise ValueError("0-length tile at %s!" % tile_index)
        if len(tile) == 1: output.append(tile[0])
        elif strict and len(tile) < colors: raise ValueError("%s-length tile at %s!" % (len(tile), tile_index))
        else: output.append(0)
    return output

def copy_tiles(tiles:list[list[int]]) -> list[list[int]]:
    return [copy_tile[:] for copy_tile in tiles]

def breakdown(tiles:list[int], size:tuple[int,int], seed:int, colors:int=2, quality_requirement:int|None=None) -> list[int]:
    '''Removes tiles from the board so it's an actual puzzle.
    basically how this works is that it picks a random tile from the board,
    and then picks an empty tile. That empty tile is picked in order of in
    the row, in the column, and everything else. It attempts to *solve* for
    the value of the empty tile using data available (hence why it
    prioritizes tiles in rows and columns), and then sets the non-empty
    tile to be empty if it was able to find it.'''
    tiles = [[tile] for tile in tiles]

    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    random_range = list(range(size[0] * size[1]))
    random.shuffle(random_range)
    tile_index = 0
    since_last_success = 0
    '''# `index2` causes it to break early if it does not find any tiles
    # within 6 iterations. It is not necessary to breakdown, but it probably
    # speeds it up greatly. The existence of this variable is why some tiles
    # clearly not necessary to the completion of the board exist on larger sizes.
    # If this is removed, the quality stuff may be removed, too. If larger board
    # sizes are created, the value should be raised above 6.'''
    dependencies:list[list[int]] = [[] for i in range(size[0] * size[1])] # this is a thing I'm making
     # for optimization. It tracks the tiles a tile is dependent on to be solved.
    tiles_cache:list[int] = [list(range(1, colors + 1))] * (size[0] * size[1])
    DEFAULT = list(range(1, colors + 1))
    for tile_index in random_range:
        tile_value = tiles[tile_index]
        tiles[tile_index] = DEFAULT[:]
        strip_dependencies(dependencies, tile_index, tiles_cache, colors)

        current_state = copy_tiles(tiles)
        restore_cache(tiles, tiles_cache, colors) # TODO: if the board is full except for one after this function; assume it's completable (and measure performance)
        # was_successful = LevelSolverOld.solve(size, tiles, tile_index, dependencies, colors)
        was_successful = LevelSolver.solve(size, colors, tiles, tile_index, dependencies)
        tiles_cache = tiles
        tiles = current_state

        if was_successful: tiles[tile_index] = DEFAULT[:]; since_last_success = 0
        else: tiles[tile_index] = tile_value; since_last_success += 1 # resets the tile's value in case it cannot be extrapolated from current board
        # LevelPrinter.print_board(tiles, size)
    # The reason that you can just solve for the current tile instead of the whole board
    # when checking if you need the tile is that
    random.seed(after_seed)
    tiles = collapse_board(tiles, colors, True)
    if all([color not in tiles for color in range(1, colors + 1)]): # if there are no non-empty tiles
        raise RuntimeError("The board is empty!")
    return tiles

if __name__ == "__main__":
    os.chdir(os.path.split(os.path.split(__file__)[0])[0])
    size = 12
    # full, empty, other_data = cProfile.run("generate(size, 1234, 2)")
    full, empty, other_data = generate(size, 28, colors=2)

    print("FULL:")
    LevelPrinter.print_board(full, size)
    print("EMPTY:")
    LevelPrinter.print_board(empty, size)

# TODO: re-design the generation script:
# 1. Generate a random tile.
# 2. Solve the board as far as possible.
# 3. If the generated board creates a mistake, switch the color of the previous tile. If
#    both colors generate an error, switch another tile placed previously to another color.
# 4. Return to step 1 if the board is not complete.
# 5. Check for errors.
