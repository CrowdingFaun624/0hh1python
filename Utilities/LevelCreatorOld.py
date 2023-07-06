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
        break # TEST
        # if quality > quality_requirement: break # the more empty tiles, the better. break if it's good enough.
    other_data = {"seed": seed, "quality": quality}
    random.seed(after_seed)
    return full_grid, empty_grid, other_data

def solve(size:int, tiles_pos:list[dict[str,int|tuple[int,int]]], current_tile:dict[str,int|tuple[int,int]]) -> bool:
    '''This function goes through all of the tiles, attempting to solve empty ones. If it does and it is the wanted
    tile, then hurray, return True. If it isn't, check that nothing went wrong and continue. It continues to grow
    the found tiles until it can finally solve the desired tile.'''
    same_column:list[dict[str,int|tuple[int,int]]] = []
    same_row:list[dict[str,int|tuple[int,int]]] = []
    other_tiles:list[dict[str,int|tuple[int,int]]] = []
    for tile in tiles_pos:
        if tile["pos"][0] == current_tile["pos"][0]:
            same_column.append(tile) # contains `size` items, including `current_tile`.
        elif tile["pos"][1] == current_tile["pos"][1]: # since this is elif, it doesn't catch `current_tile` again.
            same_row.append(tile) # contains `size - 1` items, excluding `current_tile`.
        else: other_tiles.append(tile) # contains all tiles not in the same row or column as `current_tile` (does not include `current_tile`). Contains `(size - 1) ** 2` items.
    tile = None
    solve_function_tiles = same_row + same_column + [current_tile] + other_tiles # length of `size ** 2 + 1`, duplicate tile is `current_tile`.
    # `solve_function_tiles` could theoretically be any ordering of tiles (as long as it contains all of them).
    # It does it in this order since tiles in the same row or column have a much greater impact on the desired
    # tile than other tiles.
    # TODO: make it do some thing where it avoids checking the current tile again if it hasn't found anything yet
    for total_tries in range((size ** 2) * 50): # it can loop around again and continue trying to solve if it fails the first time.
        # this range can theoretically be extended to infinity, since it will break if it can't find any tile at all.
        # It is not necessary to raise for bigger boards (probably), since it scales with the area.
        empty_tile = None # the tile that it attempts to solve for to see if the current tile is necessary
        for tile in solve_function_tiles: # the index of this resets every time it finds a tile's value, since it breaks.
            if tile["type"] == 0:
                if breakdown_tile(size, tile, tiles_pos): # setting of the tile's type occurs in here. Tile's type is set to 0 in `breakdown`
                    empty_tile = tile
                    break
        if empty_tile is not None and current_tile["pos"] == empty_tile["pos"]:
            # if the empty tile is the same as the current tile.
            return True
        elif empty_tile is None: break # occurs if it failed to find any tiles
    else: print("The board expired")
    # NOTE: before it returns, it also activates a function `v()`, which does nothing. It could potentially be reassigned somewhere
    return count_empty_tiles([tile["type"] for tile in tiles_pos]) == 0 # occurs if the tile is truly impossible to find.
    # If there are no empty tiles, then the board is completable, and completable without the current tile

def grid_is_valid(size:int, tiles:list[dict[str,int|tuple[int,int]]]) -> bool: # NOTE: this is no longer called.
    '''Returns False if the row/column is not valid, because of three-in-a-row, unbalanced, or duplicate'''
    # I'm getting serious deja-vu right now; I could've sworn I've already written this.
    three_in_a_row_regular_expression = re.compile(r"1{3}|2{3}")
    def is_invalid(row_or_column:str) -> bool:
        return bool(re.search(three_in_a_row_regular_expression, row_or_column)) or row_or_column.count("1") > max_per_row or row_or_column.count("2") > max_per_row
    max_per_column = size // 2
    max_per_row = size // 2
    already_columns:set[str] = set()
    already_rows:set[str] = set()
    for index in range(size):
        column = stringify_row_or_column(get_column(tiles, index, size))
        if is_invalid(column):
            return False
        elif column.count("0") == 0:
            if column in already_columns: return False
            else: already_columns.add(column)
        row = stringify_row_or_column(get_row(tiles, index, size))
        if is_invalid(row):
            return False
        elif row.count("0") == 0:
            if row in already_rows: return False
            else: already_rows.add(row)
    else: return True # deja-vu

def breakdown_tile(size:int, tile:dict[str,int|tuple[int,int]], tiles:list[dict[str,int|tuple[int,int]]]) -> bool:
    '''Sets a tile to its value; returns if it did that. This does not receive the `current_tile`, but instead a (probably)
    different, empty tile determined by the `solve` function.'''
    # NOTE: if you wish to make the produced puzzles harder, modify this function to include additional rules.
    collection, empty_row_pair_with, empty_column_pair_with = collect(size, tile, tiles)
    if collection is not None:
        tile["type"] = collection
        return True
    # this really should not give a KeyError due to unboundedness. if so, please scream
    elif empty_column_pair_with is not None and see_if_it_has_a_clone(tile, empty_column_pair_with, size, tiles):
        # thankfully most of the code that would be here is avoided since hints are not included in this
        return True
    elif empty_row_pair_with is not None and see_if_it_has_a_clone(tile, empty_row_pair_with, size, tiles):
        return True
    else:
        return False

def see_if_it_has_a_clone(tile:dict[str,int|tuple[int,int]], other_tile:dict[str,int|tuple[int,int]], size:int, tiles:list[dict[str,int|tuple[int,int]]]) -> bool:
    '''Parameters are the two tiles that make up the missing part of a line while attempting to find a clone.
    It sets the values to their possible values, and checks if it duplicates another line. If it does,
    then it sets the first given tile to its only possible value, and leaves the other one empty.'''
    def get_other_tile_value(tile_value:int) -> int: return 3 - tile_value # does {1: 2, 2: 1}[value]
    for value in (1, 2):
        tile["type"] = value
        other_tile["type"] = get_other_tile_value(value)
        if row_or_column_is_cloning(tile, other_tile, tiles, size):
            tile["type"] = get_other_tile_value(value)
            other_tile["type"] = value
            return True # in javascript it returns 1, not true
    else:
        tile["type"] = 0
        other_tile["type"] = 0
        return False

def row_or_column_is_cloning(tile:dict[str,int|tuple[int,int]], other_tile:dict[str,int|tuple[int,int]], tiles:dict[str,int|tuple[int,int]], size:int) -> bool:
    is_row = tile["pos"][0] != other_tile["pos"][0] # if their x-positions are the same, it is a column
    this_index = tile["pos"][int(is_row)]
    row_or_column = get_row(tiles, this_index, size) if is_row else get_column(tiles, this_index, size)
    this_row_or_column_string = stringify_row_or_column(row_or_column)
    for index in range(size):
        if index == this_index: continue
        row_or_column = get_row(tiles, index, size) if is_row else get_column(tiles, index, size)
        row_or_column_string = stringify_row_or_column(row_or_column)
        if this_row_or_column_string == row_or_column_string: return True
    else: return False

def collect(size:int, tile:dict[str,int|tuple[int,int]], tiles:list[dict[str,int|tuple[int,int]]]) -> tuple[int|None,None|dict[str,int|tuple[int,int]],None|dict[str,int|tuple[int,int]]]:
    '''The possible tiles based on rules for removing during breakdown, for reasons such as cap-at-two-in-a-row, between, or others.'''
    DIRECTIONS = [(-1, 0), (1, 0), (0, 1), (0, -1)]
    for tile_value1 in (1, 2):
        tile_value2 = 3 - tile_value1 # gets the other tile value
        for direction in DIRECTIONS: # caps at two in a row
            tile_in_direction1 = get_tile_in_direction(tiles, tile, direction, size)
            if tile_in_direction1 is None: continue
            tile_in_direction2 = get_tile_in_direction(tiles, tile_in_direction1, direction, size)
            if tile_in_direction2 is None: continue
            if tile_in_direction1["type"] == tile_value1 and tile_in_direction2["type"] == tile_value1:
                return tile_value2, None, None
        left_tile = get_tile_in_direction(tiles, tile, DIRECTIONS[0], size)
        if left_tile is not None:
            right_tile = get_tile_in_direction(tiles, tile, DIRECTIONS[1], size)
            if right_tile is not None and left_tile["type"] == tile_value1 and right_tile["type"] == tile_value1:
                return tile_value2, None, None
        up_tile = get_tile_in_direction(tiles, tile, DIRECTIONS[3], size)
        if up_tile is not None:
            down_tile = get_tile_in_direction(tiles, tile, DIRECTIONS[2], size)
            if down_tile is not None and up_tile["type"] == tile_value1 and down_tile["type"] == tile_value1:
                return tile_value2, None, None
    row = get_row(tiles, tile["pos"][1], size)
    row_string = stringify_row_or_column(row)
    max_per_row = size // 2
    max_per_column = size // 2
    empty_row_pair_with = None; empty_column_pair_with = None
    this_tile_x, this_tile_y = tile["pos"]
    if row_string.count("1") >= max_per_row:
        return 2, None, None
    elif row_string.count("2") >= max_per_row:
        return 1, None, None
    elif row_string.count("0") == 2: # this is used for if it fails to find one possible value for the tile.
        for index, row_tile in enumerate(row_string):
            if int(row_tile) == 0 and index != this_tile_x:
                empty_row_pair_with = row[index]
                break
    column = get_column(tiles, tile["pos"][0], size)
    column_string = stringify_row_or_column(column)
    if column_string.count("1") >= max_per_column:
        return 2, empty_row_pair_with, None
    elif column_string.count("2") >= max_per_column:
        return 1, empty_row_pair_with, None
    elif column_string.count("0") == 2:
        for index, column_tile in enumerate(column_string):
            if int(column_tile) == 0 and index != this_tile_y:
                empty_column_pair_with = column[index]
                break
    return None, empty_row_pair_with, empty_column_pair_with

def stringify_row_or_column(tiles:list[dict[str,int|tuple[int,int]]]) -> str:
    '''Stringifies a list of `size` tiles'''
    return "".join([str(tile["type"]) for tile in tiles])
def get_row(tiles:list[dict[str,int|tuple[int,int]]], y_position:int, size:int) -> list[dict[str,int|tuple[int,int]]]:
    return [tiles[index] for index in range(y_position * size, (y_position + 1) * size, 1)]
def get_column(tiles:list[dict[str,int|tuple[int,int]]], x_position:int, size:int) -> list[dict[str,int|tuple[int,int]]]:
    return [tiles[index] for index in range(x_position, len(tiles), size)]

def get_tile_in_direction(tiles:list[dict[str,int|tuple[int,int]]], tile:dict[str,int|tuple[int,int]], direction:tuple[int,int], size:int) -> dict[str,int|tuple[int,int]]|None:
    old_pos = tile["pos"]
    new_pos = (old_pos[0] + direction[0], old_pos[1] + direction[1])
    if new_pos[0] >= 0 and new_pos[0] < size and new_pos[1] >= 0 and new_pos[1] < size:
        new_index = new_pos[0] + (size * new_pos[1])
        return tiles[new_index]
    else: return None

def breakdown(tiles:list[int], size:int, seed) -> list[int]:
    '''Removes tiles from the board so it's an actual puzzle.'''
    # basically how this works is that it picks a random tile from the board,
    # and then picks an empty tile. That empty tile is picked in order of in
    # the row, in the column, and everything else. It attempts to *solve* for
    # the value of the empty tile using data available (hence why it
    # prioritizes tiles in rows and columns), and then sets the non-empty
    # tile to be empty if it was able to find it.
    def label_positions(tiles:list[int]) -> list[dict[str,int|tuple[int,int]]]:
        '''Turns the list of ints into a list of dicts of {"pos": (0, 0), "type": 2}'''
        return [{"pos": (index % size, index // size), "type": tile} for index, tile in enumerate(tiles)]
    def save_state() -> None:
        '''Saves the tiles_pos to the output.'''
        for tile in deepcopy(tiles_pos): # using deepcopy so that nothing wonky happens with anything at all
            x_pos, y_pos = tile["pos"]
            index = y_pos * size + x_pos
            output[index] = tile["type"]
    def restore_state() -> None:
        '''Restores the output to tiles_pos'''
        for index, value in enumerate(deepcopy(output)):
            tile = tiles_pos[index]
            tile["type"] = value


    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    tiles_pos = label_positions(tiles)
    output = tiles.copy()
    random_range = list(range(size ** 2))
    random.shuffle(random_range)
    index1 = 0
    since_last_success = 0
    # `index2` causes it to break early if it does not find any tiles
    # within 6 iterations. It is not necessary to breakdown, but it probably
    # speeds it up greatly. The existence of this variable is why some tiles
    # clearly not necessary to the completion of the board exist on larger sizes.
    # If this is removed, the quality stuff may be removed, too. If larger board
    # sizes are created, the value should be raised above 6.
    while index1 < len(tiles_pos) and since_last_success < 6:
        tile_index = random_range[index1]
        current_tile = tiles_pos[tile_index] # current_tile is tileToSolve in the code
        index1 += 1
        current_tile_type = current_tile["type"]
        current_tile["type"] = 0
        save_state() # TODO: it is probably possible to instead provide a deep copy of tiles_pos and current_tile, since all of the modifications made to them
        # can be forgotten anyways; only if it can be found needs to be known.
        should_reset_index2 = solve(size, tiles_pos, current_tile)
        restore_state() # this undoes all of the tile wonkiness (setting them back to their original value)
        # after this, only one tile, `current_tile`, should have changed.
        if should_reset_index2: since_last_success = 0
        else: current_tile["type"] = current_tile_type # resets the tile's value in case it cannot be extrapolated from current board
        # print_board(tiles_pos)
    # The reason that you can just solve for the current tile instead of the whole board
    # when checking if you need the tile is that 
    save_state()
    random.seed(after_seed)
    if 1 not in output and 2 not in output:
        raise RuntimeError("The board is empty!")
    return output

def print_board(tiles:list[int]|str|list[dict[str,int|tuple[int,int]]]) -> None:
    width:int = len(tiles) ** 0.5
    if width % 1 != 0: raise ValueError("Wonky width board!")
    width = int(width)
    if isinstance(tiles, str): tiles = [int(i) for i in tiles]
    elif isinstance(tiles[0], dict):
        new_tiles:dict[int,int] = dict([(i, None) for i in range(len(tiles))])
        for tile in tiles:
            x_pos:int = tile["pos"][0]
            y_pos:int = tile["pos"][1]
            index:int = y_pos * width + x_pos
            new_tiles[index] = tile["type"]
        tiles = list(new_tiles.values())

    width = int(width)
    emojis = {0: "⬛", 1: "🟥", 2: "🟦"}
    output = ""
    for index, tile in enumerate(tiles):
        output += emojis[tile]
        if index % width == width - 1: output += "\n"
    print(output)

if __name__ == "__main__":
    # full, empty, other_data = cProfile.run("generate(14, 99)")
    full, empty, other_data = generate(4, 2)

    print("FULL:")
    print_board(full)
    print("EMPTY:")
    print_board(empty)
