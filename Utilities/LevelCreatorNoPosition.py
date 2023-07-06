import cProfile
import random
import re
from copy import deepcopy


def generate_solution(size:int, seed:int=None) -> list[int]:
    # wave collapse algorithm I think
    def get_tile(x:int, y:int) -> int:
        return tiles[size * y + x]
    def set_tile_to(x:int, y:int, value:int) -> None:
        tiles[size * y + x] = value
    
    def row_or_column_is_valid() -> bool:
        already_rows:set[str] = set() # in the javascript, the structure of these is the string column/row and their index. I am not doing that.
        already_columns:set[str] = set()
        for index in range(size):
            column = get_column(index)
            if is_invalid_base_1(column): return False
            elif is_full(column) and column in already_columns: return False
            else: already_columns.add(column)
            row = get_row(index)
            if is_invalid_base_1(row): return False
            elif is_full(row) and row in already_rows: return False
            else: already_rows.add(row)
        else: return True
    
    def clear_row_from_tiles(y:int, situation) -> None:
        for x_position in range(size):
            set_tile_to(x_position, y, 0)
        output_rows[y] = None
        if y in wave_collapse_storage and wave_collapse_storage[y] is not None:
            valid_rows.append(wave_collapse_storage[y])
            wave_collapse_storage[y] = None
    def get_row(y_position:int) -> str:
        return "".join(str(i) for i in tiles[y_position * size:(y_position + 1) * size])
    def get_column(x_position:int) -> str: # TODO: please stop using these godforesaken string operations; they're so slow
        return "".join(str(i) for i in tiles[x_position::size])
    def is_full(row_or_column:str) -> bool:
        '''Returns if a "0" is not in a base-1 row or column'''
        return "0" not in row_or_column
    def is_invalid_base_0(row_or_column:str) -> bool:
        '''Detects the invalidity of a row or column if red is 0 and blue is 1'''
        return bool(re.search(three_in_a_row_regular_expression_base_0, row_or_column)) or row_or_column.count("0") > max_per_row or row_or_column.count("1") > max_per_row
    def is_invalid_base_1(row_or_column:str) -> bool:
        '''Detects the invalidity of a row or column if empty is 0, red is 1, and blue is 2'''
        return bool(re.search(three_in_a_row_regular_expression_base_1, row_or_column)) or row_or_column.count("1") > max_per_row or row_or_column.count("2") > max_per_row

    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    if not isinstance(size, int): raise TypeError("generate() requires size to be an int!")
    elif size <= 0 or size % 2 != 0: raise ValueError("generate() requires size to be a positive, even number!")
    max_per_row = size // 2
    max_per_col = size // 2
    valid_rows:list[str] = []

    three_in_a_row_regular_expression_base_0 = re.compile(r"0{3}|1{3}")
    three_in_a_row_regular_expression_base_1 = re.compile(r"1{3}|2{3}")
    for index in range(2**size):
        index_string = bin(index)[2:].zfill(size)
        if not is_invalid_base_0(index_string):
            valid_rows.append(index_string)
    random.shuffle(valid_rows)

    y_position = 0
    tiles:list[int] = [0 for i in range(size ** 2)] # output
    wave_collapse_storage:dict[int,str] = {} # javascript arrays define an index as undefined and don't change length of list when deleting an index
    output_rows:dict[int,str] = dict([(i, None) for i in range(7)]) # for debug
    row_tries:list[int] = [0 for i in range(size)] # how many times this row has failed to find itself. If it goes beyond the number of valid rows, it goes back and tries again
    while y_position < size:
        row_tries[y_position] += 1
        current_row = valid_rows.pop(0)
        for x_position in range(size):
            set_tile_to(x_position, y_position, int(current_row[x_position]) + 1)
        output_rows[y_position] = current_row
        if row_or_column_is_valid():
            wave_collapse_storage[y_position] = current_row
            y_position += 1
        else:
            valid_rows.append(current_row)
            clear_row_from_tiles(y_position, "base")
            if row_tries[y_position] >= len(valid_rows):
                row_tries[y_position] = 0
                for remove_index in range(1, y_position):
                    clear_row_from_tiles(remove_index,"iter")
                    row_tries[remove_index] = 0
                y_position = 1
    random.seed(after_seed) # NOTE: random seed is reset here!
    return tiles


def count_empty_tiles(tiles:list[int]) -> int:
    return tiles.count(0)

def generate(size:int, seed:int=None) -> tuple[list[int],list[int],dict[str,any]]:
    '''Returns the solution, the incomplete puzzle, and other data.'''

    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    full_grid = generate_solution(size, seed)
    QUALITY_REQUIREMENTS = {4: 60, 6: 60, 8: 60, 10: 60, 12: 60}
    quality_requirement = QUALITY_REQUIREMENTS[size] if size in QUALITY_REQUIREMENTS else 60
    TOTAL_TRIES = 42
    for i in range(TOTAL_TRIES):
        empty_grid = breakdown(full_grid, size, seed)
        quality = round(count_empty_tiles(empty_grid) / (size ** 2) * 100) # how many empty tiles there are
        break
        # if quality > quality_requirement: break # the more empty tiles, the better. break if it's good enough.
    other_data = {"seed": seed, "quality": quality}
    random.seed(after_seed)
    return full_grid, empty_grid, other_data

def solve(size:int, tiles_values:list[int], current_tile_value:int, current_tile_index:int) -> bool:
    '''This function goes through all of the tiles, attempting to solve empty ones. If it does and it is the wanted
    tile, then hurray, return True. If it isn't, check that nothing went wrong and continue. It continues to grow
    the found tiles until it can finally solve the desired tile.'''
    same_column:list[int] = []
    same_row:list[int] = []
    other_tiles:list[int] = []
    current_tile_pos = get_pos(current_tile_index, size)
    for tile_index in range(len(tiles_values)):
        tile_pos = get_pos(tile_index, size)
        if tile_pos[0] == current_tile_pos[0]:
            same_column.append(tile_index) # contains `size` items, including `current_tile`.
        elif tile_pos[1] == current_tile_pos[1]: # since this is elif, it doesn't catch `current_tile` again.
            same_row.append(tile_index) # contains `size - 1` items, excluding `current_tile`.
        else: other_tiles.append(tile_index) # contains all tiles not in the same row or column as `current_tile` (does not include `current_tile`). Contains `(size - 1) ** 2` items.
    tile_pos = None
    solve_function_tiles_indexes = same_row + same_column + [current_tile_index] + other_tiles # length of `size ** 2 + 1`, duplicate tile is `current_tile`.
    # `solve_function_tiles` could theoretically be any ordering of tiles (as long as it contains all of them).
    # It does it in this order since tiles in the same row or column have a much greater impact on the desired
    # tile than other tiles.
    # TODO: make it do some thing where it avoids checking the current tile again if it hasn't found anything yet
    for total_tries in range((size ** 2) * 50): # it can loop around again and continue trying to solve if it fails the first time.
        # this range can theoretically be extended to infinity, since it will break if it can't find any tile at all.
        # It is not necessary to raise for bigger boards (probably), since it scales with the area.
        empty_tile_index = None # the tile that it attempts to solve for to see if the current tile is necessary
        for tile_index in solve_function_tiles_indexes: # the index of this resets every time it finds a tile's value, since it breaks.
            tile_value = tiles_values[tile_index]
            if tile_value == 0:
                if breakdown_tile(size, tiles_values, tile_value, tile_index): # setting of the tile's type occurs in here. Tile's type is set to 0 in `breakdown`
                    empty_tile_index = tile_index
                    break
        if empty_tile_index is not None and current_tile_index == empty_tile_index:
            # if the empty tile is the same as the current tile.
            return True
        elif empty_tile_index is None: break # occurs if it failed to find any tiles
    else: print("The board expired")
    # NOTE: before it returns, it also activates a function `v()`, which does nothing. It could potentially be reassigned somewhere
    return count_empty_tiles(tiles_values) == 0
    # occurs if the tile is truly impossible to find.
    # If there are no empty tiles, then the board is completable, and completable without the current tile

def grid_is_valid(size:int, tiles_values:list[int]) -> bool: # NOTE: this is no longer called.
    '''Returns False if the row/column is not valid, because of three-in-a-row, unbalanced, or duplicate'''
    # I'm getting serious deja-vu right now; I could've sworn I've already written this.
    three_in_a_row_regular_expression = re.compile(r"1{3}|2{3}")
    def is_invalid(row_or_column:list[int], row_or_column_string:str) -> bool:
        return bool(re.search(three_in_a_row_regular_expression, row_or_column_string)) or row_or_column.count(1) > max_per_row or row_or_column.count(2) > max_per_row
    max_per_column = size // 2
    max_per_row = size // 2
    already_columns:set[str] = set()
    already_rows:set[str] = set()
    for index in range(size):
        column = get_values(tiles_values, get_column(index, size))
        column_string = "".join(column)
        if is_invalid(column, column_string):
            return False
        elif column.count(0) == 0:
            if column_string in already_columns: return False
            else: already_columns.add(column_string)
        row = get_values(tiles_values, get_row(index, size))
        row_string = "".join(row)
        if is_invalid(row, row_string):
            return False
        elif row.count(0) == 0:
            if row_string in already_rows: return False
            else: already_rows.add(row_string)
    else: return True # deja-vu

def breakdown_tile(size:int, tiles_values:list[int], tile_value:int, tile_index:int) -> bool:
    '''Sets a tile to its value; returns if it did that. This does not receive the `current_tile`, but instead a (probably)
    different, empty tile determined by the `solve` function.'''
    # NOTE: if you wish to make the produced puzzles harder, modify this function to include additional rules.
    collection_value, empty_row_pair_with_index, empty_column_pair_with_index = collect(size, tiles_values, tile_value, tile_index)
    if collection_value is not None:
        tiles_values[tile_index] = collection_value
        return True
    # this really should not give a KeyError due to unboundedness. if so, please scream
    elif empty_column_pair_with_index is not None and see_if_it_has_a_clone(tiles_values, tile_index, empty_column_pair_with_index, size):
        # thankfully most of the code that would be here is avoided since hints are not included in this
        return True
    elif empty_row_pair_with_index is not None and see_if_it_has_a_clone(tiles_values, tile_index, empty_row_pair_with_index, size):
        return True
    else:
        return False

def see_if_it_has_a_clone(tiles_values:list[int], tile_index:int, other_tile_index:int, size:int) -> bool:
    '''Parameters are the two tiles that make up the missing part of a line while attempting to find a clone.
    It sets the values to their possible values, and checks if it duplicates another line. If it does,
    then it sets the first given tile to its only possible value, and leaves the other one empty.'''
    for value, other_value in ((1, 2), (2, 1)):
        tiles_values[tile_index] = value
        tiles_values[other_tile_index] = other_value
        if row_or_column_is_cloning(tiles_values, tile_index, other_tile_index, size):
            tiles_values[tile_index] = other_value
            tiles_values[other_tile_index] = value
            return True # in javascript it returns 1, not true
    else:
        tiles_values[tile_index] = 0
        tiles_values[other_tile_index] = 0
        return False

def row_or_column_is_cloning(tiles_values:list[int], tile_index:int, other_tile_index:int, size:int) -> bool:
    tile_pos = get_pos(tile_index, size); other_tile_pos = get_pos(other_tile_index, size)
    is_row = tile_pos[0] != other_tile_pos[0] # if their x-positions are the same, it is a column
    this_index = tile_pos[int(is_row)]
    row_or_column_indexes = get_row(this_index, size) if is_row else get_column(this_index, size)
    this_row_or_column_values = get_values(tiles_values, row_or_column_indexes)
    for index in range(size): # FIXME: this might have bug of checking even rows that aren't full.
        if index == this_index: continue
        row_or_column_indexes = get_row(index, size) if is_row else get_column(index, size)
        row_or_column_values = get_values(tiles_values, row_or_column_indexes)
        if this_row_or_column_values == row_or_column_values: return True
    else: return False

def collect(size:int, tiles_values:list[int], tile_value:int, tile_index:int) -> tuple[int|None,int|None,int|None]:
    '''The possible tile value based on rules for removing during breakdown, for reasons such as cap-at-two-in-a-row, between, or others. Also returns the
    empty_row_pair_with and empty_column_pair_with's indexes'''
    DIRECTIONS = [(-1, 0), (1, 0), (0, 1), (0, -1)]
    for test_value1 in (1, 2):
        test_value2 = 3 - test_value1 # gets the other tile value
        for direction in DIRECTIONS: # caps at two in a row
            tile_in_direction1 = get_tile_in_direction(tile_index, direction, size)
            if tile_in_direction1 is None: continue
            tile_in_direction2 = get_tile_in_direction(tile_in_direction1, direction, size)
            if tile_in_direction2 is None: continue
            if tiles_values[tile_in_direction1] == test_value1 and tiles_values[tile_in_direction2] == test_value1:
                return test_value2, None, None
        left_tile = get_tile_in_direction(tile_index, DIRECTIONS[0], size)
        if left_tile is not None:
            right_tile = get_tile_in_direction(tile_index, DIRECTIONS[1], size)
            if right_tile is not None and tiles_values[left_tile] == test_value1 and tiles_values[right_tile] == test_value1:
                return test_value2, None, None
        up_tile = get_tile_in_direction(tile_index, DIRECTIONS[3], size)
        if up_tile is not None:
            down_tile = get_tile_in_direction(tile_index, DIRECTIONS[2], size)
            if down_tile is not None and tiles_values[up_tile] == test_value1 and tiles_values[down_tile] == test_value1:
                return test_value2, None, None
   
    tile_pos = get_pos(tile_index, size)
    max_per_row = size // 2; max_per_column = size // 2
    empty_row_pair_with = None; empty_column_pair_with = None

    row_indexes = get_row(tile_pos[1], size)
    row_values = get_values(tiles_values, row_indexes)
    if row_values.count(1) >= max_per_row:
        return 2, None, None
    elif row_values.count(2) >= max_per_row:
        return 1, None, None
    elif row_values.count(0) == 2: # this is used for if it fails to find one possible value for the tile.
        for index, row_tile_index in enumerate(row_indexes):
            if row_values[index] == 0 and index != tile_pos[0]:
                empty_row_pair_with = row_tile_index
                break

    column_indexes = get_column(tile_pos[0], size)
    column_values:list[int] = get_values(tiles_values, column_indexes) # vscode is very silly
    if column_values.count(1) >= max_per_column:
        return 2, empty_row_pair_with, None
    elif column_values.count(2) >= max_per_column:
        return 1, empty_row_pair_with, None
    elif column_values.count(0) == 2:
        for index, column_tile_index in enumerate(column_indexes):
            if column_values[index] == 0 and index != tile_pos[1]:
                empty_column_pair_with = column_tile_index
                break
   
    return None, empty_row_pair_with, empty_column_pair_with

def get_values(tiles_values:list[int], indexes:list[int]) -> list[int]:
    '''Gets the values of a list of indexes'''
    return [tiles_values[index] for index in indexes]
def get_row(y_position:int, size:int) -> list[int]:
    '''Returns a list of indexes in the row'''
    return list(range(y_position * size, (y_position + 1) * size, 1))
def get_column(x_position:int, size:int) -> list[int]:
    '''Returns a list of indexes in the column'''
    return list(range(x_position, size ** 2, size))

def get_tile_in_direction(tile_index:int, direction:tuple[int,int], size:int) -> int|None:
    tile_pos = get_pos(tile_index, size)
    new_pos = (tile_pos[0] + direction[0], tile_pos[1] + direction[1])
    if new_pos[0] >= 0 and new_pos[0] < size and new_pos[1] >= 0 and new_pos[1] < size: return get_index(new_pos, size)
    else: return None

def get_pos(index:int, size:int) -> tuple[int,int]:
    return (index % size, index // size)
def get_index(pos:tuple[int,int], size:int) -> int:
    return (pos[0] + pos[1] * size)

def breakdown(tiles:list[int], size:int, seed) -> list[int]:
    '''Removes tiles from the board so it's an actual puzzle.'''
    # basically how this works is that it picks a random tile from the board,
    # and then picks an empty tile. That empty tile is picked in order of in
    # the row, in the column, and everything else. It attempts to *solve* for
    # the value of the empty tile using data available (hence why it
    # prioritizes tiles in rows and columns), and then sets the non-empty
    # tile to be empty if it was able to find it.
    tiles = tiles.copy()

    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    # tiles_pos = label_positions(tiles)
    # output = tiles.copy()
    random_range = list(range(size ** 2))
    random.shuffle(random_range)
    tile_index = 0
    since_last_success = 0
    # `index2` causes it to break early if it does not find any tiles
    # within 6 iterations. It is not necessary to breakdown, but it probably
    # speeds it up greatly. The existence of this variable is why some tiles
    # clearly not necessary to the completion of the board exist on larger sizes.
    # If this is removed, the quality stuff may be removed, too. If larger board
    # sizes are created, the value should be raised above 6.
    for tile_index in random_range:
        if since_last_success >= 6: break
        tile_value = tiles[tile_index] # current_tile is tileToSolve in the code
        tiles[tile_index] = 0

        current_state = tiles.copy()
        was_successful = solve(size, tiles, tile_value, tile_index)
        tiles = current_state

        if was_successful: since_last_success = 0
        else: tiles[tile_index] = tile_value # resets the tile's value in case it cannot be extrapolated from current board
        print_board(tiles)
    # The reason that you can just solve for the current tile instead of the whole board
    # when checking if you need the tile is that
    random.seed(after_seed)
    if 1 not in tiles and 2 not in tiles:
        raise RuntimeError("The board is empty!")
    return tiles

def print_board(tiles:list[int]|str) -> None:
    width:int = len(tiles) ** 0.5
    if width % 1 != 0: raise ValueError("Wonky width board!")
    width = int(width)
    emojis = {0: "⬛", 1: "🟥", 2: "🟦"}
    output = ""
    for index, tile in enumerate(tiles):
        output += emojis[int(tile)]
        if index % width == width - 1: output += "\n"
    print(output)

if __name__ == "__main__":
    # full, empty, other_data = cProfile.run("generate(14, 99)")
    full, empty, other_data = generate(4, 2)


    print("FULL:")
    print_board(full)
    print("EMPTY:")
    print_board(empty)
# TODO: Experiment with removing tiles_pos and just having list of values in all circumstances.
