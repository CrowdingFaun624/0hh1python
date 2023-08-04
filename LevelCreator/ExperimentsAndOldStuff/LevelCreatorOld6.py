import cProfile
from math import ceil
import os
import random
import re

try:
    import LevelCreator.LevelPrinter as LevelPrinter
    import LevelCreator.LevelSolver as LevelSolver
except ImportError:
    import LevelPrinter
    import LevelSolver

def generate_solution(size:tuple[int,int], seed:int=None, colors:int=2) -> list[int]:
    # wave collapse algorithm I think
    def get_tile(x:int, y:int) -> int:
        return tiles[size[0] * y + x]
    def set_tile_to(x:int, y:int, value:int) -> None:
        tiles[size[0] * y + x] = value
    
    def grid_is_valid(is_final:bool) -> bool:
        already_columns:list[str] = []
        for index in range(size[0]):
            column = get_column(index)
            if is_invalid_base_1(column): return False
            elif is_final and column in already_columns: return False
            else: already_columns.append(column)
        return True
    
    def clear_row_from_tiles(y:int) -> None:
        for x_position in range(size[0]):
            set_tile_to(x_position, y, 0)
        # output_rows[y] = None
        if wave_collapse_storage[y] is not None: # if the line already exists, remove it and put it back in valid rows.
            valid_rows.append(wave_collapse_storage[y])
            wave_collapse_storage[y] = None
    def get_column(x_position:int) -> str:
        return "".join([str(i) for i in tiles[x_position::size[0]]])
    def is_invalid_base_0(row:str) -> bool:
        '''Detects the invalidity of a row or column if red is 0 and blue is 1'''
        for color in range(colors):
            if row.count(str(color)) > max_per_row: return True
        if bool(three_in_a_row_regular_expression_base_0.search(row)): return True
        return False
    def is_invalid_base_1(column:str) -> bool:
        '''Detects the invalidity of a row or column if empty is 0, red is 1, and blue is 2'''
        for color in range(1, colors + 1):
            if column.count(str(color)) > max_per_column: return True
        if bool(three_in_a_row_regular_expression_base_1.search(column)): return True
        return False

    def get_valid_rows() -> list[str]:
        if colors ** size[0] >= 4096:
            cached_data = fetch_cache()
            if cached_data is not None: return cached_data
        valid_rows:list[str] = []
        for index in range(colors ** size[0]):
            index_string = int_to_string(index, colors).zfill(size[0])
            if not is_invalid_base_0(index_string):
                valid_rows.append(index_string)
        if size[0] * colors >= 24: create_cache(valid_rows)
        return valid_rows

    def create_cache(valid_rows:list[str]) -> None:
        path_name = "./_cache/solution_%s_%s.bin" % (size[0], colors)
        if os.path.exists(path_name): return
        byte_length = ceil((size[0] + 7) / (16 / colors)) # how long each valid row is
        data_bytes = b"".join([int(valid_row, colors).to_bytes(byte_length, "big") for valid_row in valid_rows])
        with open(path_name, "wb") as f:
            f.write(data_bytes)

    def int_to_string(number:int, base:int) -> str: # https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base
        BASE_STRING = "0123456789"
        result = ""
        while number:
            result += BASE_STRING[number % base]
            number //= base
        return result[::-1] or "0"

    def fetch_cache() -> list[str]|None:
        path_name = "./_cache/solution_%s_%s.bin" % (size[0], colors)
        if not os.path.exists(path_name): return None
        with open(path_name, "rb") as f:
            data_bytes = f.read()
        byte_length = ceil((size[0] + 7) / (16 / colors)) # how long each valid row is
        data = [data_bytes[i:i + byte_length] for i in range(0, len(data_bytes), byte_length)]
        valid_rows = [int_to_string(int.from_bytes(valid_row, "big"), colors).zfill(size[0]) for valid_row in data]
        return valid_rows

    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    max_per_row = size[0] // colors
    max_per_column = size[1] // colors
    
    three_in_a_row_regular_expression_base_0 = re.compile("|".join([str(i) + "{3}" for i in range(colors)]))
    three_in_a_row_regular_expression_base_1 = re.compile("|".join([str(i) + "{3}" for i in range(1, colors + 1)]))
    valid_rows = get_valid_rows()
    # print(len(valid_rows)); assert False
    random.shuffle(valid_rows)

    y_position = 0
    tiles:list[int] = [0 for i in range(size[0] * size[1])] # output
    wave_collapse_storage:list[str] = [None] * size[1]
    # output_rows:dict[int,str] = dict([(i, None) for i in range(7)]) # for debug
    row_tries:list[int] = [0] * size[1]
    previous_states:set[str] = set()
    while y_position < size[1]:
        row_tries[y_position] += 1
        current_row = valid_rows.pop(0)
        # print(seed, size, wave_collapse_storage, output_rows, row_tries, y_position)
        for x_position in range(size[0]):
            set_tile_to(x_position, y_position, int(current_row[x_position]) + 1) # TODO: write some slicing weirdness or whatever to make this faster; maybe list comprehension.
        # output_rows[y_position] = current_row
        if grid_is_valid(y_position == size[1] - 1):
            wave_collapse_storage[y_position] = current_row
            y_position += 1
        else:
            valid_rows.append(current_row)
            clear_row_from_tiles(y_position)
            if row_tries[y_position] >= len(valid_rows):
            # if row_tries[y_position] >= len(valid_rows):
                this_state = tuple(valid_rows)
                if this_state in previous_states: random.shuffle(valid_rows)
                previous_states.add(this_state)
                row_tries[y_position] = 0
                for remove_index in range(1, y_position):
                    clear_row_from_tiles(remove_index)
                    row_tries[remove_index] = 0
                y_position = 1
    random.seed(after_seed)
    return tiles # TODO: make valid_rows a list of lists of ints *after* being generated and remove wave_collapse_storage

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
    largest_size = max(size)
    QUALITY_REQUIREMENTS = {4: 60, 6: 60, 8: 60, 10: 60, 12: 60}
    quality_requirement = QUALITY_REQUIREMENTS[largest_size] if largest_size in QUALITY_REQUIREMENTS else 60
    TOTAL_TRIES = 42
    for i in range(TOTAL_TRIES):
        empty_grid = breakdown(full_grid, size, seed, colors, quality_requirement)
        quality = round(count_empty_tiles(empty_grid) / (size[0] * size[1]) * 100) # how many empty tiles there are
        #if quality > quality_requirement: break # the more empty tiles, the better. break if it's good enough.
        break
    else: raise RuntimeError("The board expired!")
    other_data = {"seed": seed, "quality": quality}
    random.seed(after_seed)
    return full_grid, empty_grid, other_data

def restore_cache(tiles_values:list[list[int]], tiles_cache:list[list[int]], colors:int) -> None:
    DEFAULT = list(range(1, colors + 1))
    for index, tile in enumerate(tiles_cache):
        if tile != DEFAULT: tiles_values[index] = tile[:]

def strip_dependencies(dependencies:list[list[int]], tiles:list[int], tile_index:int, tiles_cache:list[list[int]], colors:int) -> None:
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
        # tiles[affected_tile] = 0

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
        if since_last_success >= 6:
            if quality_requirement is None: break
            elif round(count_unknown_tiles(tiles) / (size[0] * size[1]) * 100) > quality_requirement: break
        tile_value = tiles[tile_index]
        tiles[tile_index] = DEFAULT[:]
        strip_dependencies(dependencies, tiles, tile_index, tiles_cache, colors)

        current_state = copy_tiles(tiles)
        restore_cache(tiles, tiles_cache, colors) # TODO: if the board is full except for one after this function; assume it's completable (and measure performance)
        # was_successful = solve(size, tiles, tile_index, dependencies, colors)
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
    size = 4
    # full, empty, other_data = cProfile.run("generate(size, 1234, 2)")
    full, empty, other_data = generate(size, 889, colors=2)

    print("FULL:")
    LevelPrinter.print_board(full, size)
    print("EMPTY:")
    LevelPrinter.print_board(empty, size)

# TODO: generate solution: it may be possible to not generate the entire valid_rows list, but instead a small portion of it. The list may be expanded when it normally reshuffles the list.
