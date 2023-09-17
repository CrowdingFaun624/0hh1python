import cProfile
import os
import random

try:
    import LevelCreator.LevelGenerator as LevelGenerator
    import LevelCreator.LevelUtilities as LU
    import LevelCreator.LevelSolver as LevelSolver
    import LevelCreator.LevelValidator as LevelValidator
except ImportError:
    import LevelGenerator
    import LevelUtilities as LU
    import LevelSolver
    import LevelValidator

def generate(size:int|tuple[int,int], seed:int=None, colors:int=2, usable_rules:list[bool]|None=None, gen_info:LU.GenerationInfo|None=None) -> tuple[list[int],list[int],dict[str,any]]|None:
    '''Returns the solution, the incomplete puzzle, and other data. Will return None if the first item of `break_holder` is True.'''

    if seed is None: seed = LU.get_seed()
    after_seed = LU.get_seed() # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    if isinstance(size, int): size = (size, size)
    if size[0] % colors != 0: raise ValueError("Invalid width for %s colors!" % colors)
    elif size[1] % colors != 0: raise ValueError("Invalid height for %s colors!" % colors)
    if size[0] > size[1]: solution_generator_size = (size[1], size[0]); is_rotated = True
    else: solution_generator_size = size; is_rotated = False
    full_grid = LevelGenerator.generate_solution(solution_generator_size, seed, colors, gen_info=gen_info)
    if full_grid is None: return None
    if is_rotated: full_grid = LU.rotate_board(full_grid, solution_generator_size)

    empty_grid = breakdown(full_grid, size, seed, colors, usable_rules, gen_info=gen_info)
    if empty_grid is None: return None
    quality = round(LU.count_empty_tiles(empty_grid) / (size[0] * size[1]) * 100) # how many empty tiles there are
    other_data = {"seed": seed, "quality": quality}
    random.seed(after_seed)
    return full_grid, empty_grid, other_data


def breakdown(tiles:list[int], size:tuple[int,int], seed:int, colors:int=2, usable_rules:list[bool]|None=None, gen_info:LU.GenerationInfo|None=None) -> list[int]:
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
    # `index2` causes it to break early if it does not find any tiles
    # within 6 iterations. It is not necessary to breakdown, but it probably
    # speeds it up greatly. The existence of this variable is why some tiles
    # clearly not necessary to the completion of the board exist on larger sizes.
    # If this is removed, the quality stuff may be removed, too. If larger board
    # sizes are created, the value should be raised above 6.
    dependencies:list[list[int]] = [[] for i in range(size[0] * size[1])] # this is a thing I'm making
     # for optimization. It tracks the tiles a tile is dependent on to be solved.
    tiles_cache:list[int] = [list(range(1, colors + 1))] * (size[0] * size[1])
    DEFAULT = list(range(1, colors + 1))
    # debug_string = ""
    for index, tile_index in enumerate(random_range):
        # print(tile_index)
        tile_value = tiles[tile_index]
        tiles[tile_index] = DEFAULT[:]
        LU.strip_dependencies(dependencies, tile_index, tiles_cache, colors)

        current_state = LU.copy_tiles(tiles)
        LU.restore_cache(tiles, tiles_cache, colors) # TODO: if the board is full except for one after this function; assume it's completable (and measure performance)
        # was_successful = LevelSolverOld.solve(size, tiles, tile_index, dependencies, colors)
        was_successful = LevelSolver.solve(size, colors, tiles, tile_index, dependencies, usable_rules=usable_rules)
        tiles_cache = tiles
        tiles = current_state
        # debug_string += str(int(was_successful))

        if was_successful: tiles[tile_index] = DEFAULT[:]; since_last_success = 0
        else: tiles[tile_index] = tile_value; since_last_success += 1 # resets the tile's value in case it cannot be extrapolated from current board
        if gen_info is not None:
            if gen_info.breaker: return None
            gen_info.generation_progress = 0.9 + (index / (len(random_range))) * 0.1
        # LevelPrinter.print_board(tiles, size)
    # print(debug_string)
    random.seed(after_seed)
    tiles = LU.collapse_board(tiles, colors, True)
    if all([color not in tiles for color in range(1, colors + 1)]): # if there are no non-empty tiles
        raise RuntimeError("The board is empty!")
    return tiles

if __name__ == "__main__":
    os.chdir(os.path.split(os.path.split(__file__)[0])[0])
    size = 6
    seed = 34
    colors = 2
    usable_rules = [True, True, True, True, True]
    size_tuple = (size, size) if isinstance(size, int) else size
    # full, empty, other_data = cProfile.run("generate(size_tuple, seed, colors, usable_rules)")
    full, empty, other_data = generate(size_tuple, seed, colors, usable_rules)
    solved = LU.expand_board(colors, empty)

    print("FULL:")
    LU.print_board(full, size_tuple)
    print("EMPTY:")
    LU.print_board(empty, size_tuple)
    solved = LU.expand_board(colors, empty)
    LevelSolver.solve(size, colors, solved, None, None, True, usable_rules=usable_rules)
    if not LU.boards_match(full, solved, colors):
        print("SOLVED:")
        LU.print_board(solved, size)
        different_tiles = LU.get_not_matching_tiles(full, solved, colors)
        different_positions = [str(LU.get_pos(different_tile, size)) for different_tile in different_tiles]
        raise RuntimeError("The full and solved boards are different at positions [%s]." % (", ".join(different_positions)))

# TODO: re-design the generation script:
# 1. Generate a random tile.
# 2. Solve the board as far as possible.
# 3. If the generated board creates a mistake, switch the color of the previous tile. If
#    both colors generate an error, switch another tile placed previously to another color.
# 4. Return to step 1 if the board is not complete.
# 5. Check for errors.
