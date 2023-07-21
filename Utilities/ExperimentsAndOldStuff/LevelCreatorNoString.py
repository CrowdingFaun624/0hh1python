# NOTE: THIS IS SLOWER THAN THE DEFAULT GENERATOR

import cProfile
from math import ceil
import os
import random
import re

def generate_solution(size:tuple[int,int], seed:int=None, colors:int=2) -> list[int]:
    # wave collapse algorithm I think
    def get_tile(x:int, y:int) -> int:
        return tiles[size[0] * y + x]
    def set_tile_to(x:int, y:int, value:int) -> None:
        tiles[size[0] * y + x] = value
    
    def row_or_column_is_valid() -> bool:
        already_rows:set[str] = set()
        already_columns:set[str] = set()
        for index in range(size[0]): # TODO: try doing rows first
            column = get_column(index)
            if is_invalid_base_1_column(column): return False
            elif (column_string := "".join([str(char) for char in column])) in already_columns and is_full(column): return False
            else: already_columns.add(column_string)
        for index in range(size[1]):
            row = get_row(index)
            if is_invalid_base_1_row(row): return False
            elif (row_string := "".join([str(char) for char in row])) in already_rows and is_full(row): return False
            else: already_rows.add(row_string)
        else: return True
    
    def clear_row_from_tiles(y:int) -> None:
        for x_position in range(size[0]):
            set_tile_to(x_position, y, 0)
        output_rows[y] = None
        if y in wave_collapse_storage and wave_collapse_storage[y] is not None:
            valid_rows.append(wave_collapse_storage[y])
            wave_collapse_storage[y] = None
    def get_row(y_position:int) -> list[int]:
        return tiles[y_position * size[0]:(y_position + 1) * size[0]]
    def get_column(x_position:int) -> list[int]: # TODO: please stop using these godforesaken string operations; they're so slow
        return tiles[x_position::size[0]]
    def is_full(row_or_column:list[int]) -> bool:
        '''Returns if a "0" is not in a base-1 row or column'''
        return 0 not in row_or_column
    def is_invalid_base_0_row(row:str) -> bool:
        '''Detects the invalidity of a row or column if red is 0 and blue is 1'''
        for color in range(colors):
            if row.count(str(color)) > max_per_row: return True
        if bool(three_in_a_row_regular_expression_base_0.search(row)): return True
        return False
    def is_invalid_base_1_row(row:list[int]) -> bool:
        '''Detects the invalidity of a row or column if empty is 0, red is 1, and blue is 2'''
        for color in range(1, colors + 1): # TODO: experiment with order again
            if row.count(color) > max_per_row: return True
        prev_tile1 = None; prev_tile2 = None
        for tile in row:
            if prev_tile1 != 0 and prev_tile2 != 0 and tile == prev_tile1 and tile == prev_tile2: return True
            prev_tile2 = prev_tile1
            prev_tile1 = tile
        return False
    def is_invalid_base_1_column(column:list[int]) -> bool:
        '''Detects the invalidity of a row or column if empty is 0, red is 1, and blue is 2'''
        for color in range(1, colors + 1):
            if column.count(color) > max_per_column: return True
        prev_tile1 = None; prev_tile2 = None
        for tile in column:
            if prev_tile1 != 0 and prev_tile2 != 0 and tile == prev_tile1 and tile == prev_tile2: return True
            prev_tile2 = prev_tile1
            prev_tile1 = tile
        return False

    def get_valid_rows() -> list[list[int]]: # TODO: experiment with this thing being no strings too
        if colors ** size[0] >= 4096:
            cached_data = fetch_cache()
            if cached_data is not None: return cached_data
        valid_rows:list[list[int]] = []
        for index in range(colors ** size[0]):
            index_string = int_to_string(index, colors).zfill(size[0])
            if not is_invalid_base_0_row(index_string):
                valid_rows.append([int(char) for char in index_string])
        if size[0] * colors >= 24: create_cache(valid_rows)
        return valid_rows

    def create_cache(valid_rows:list[list[int]]) -> None: # TODO: experiment with this thing being no strings too
        path_name = "./_cache/solution_%s_%s.bin" % (size[0], colors)
        if os.path.exists(path_name): return
        byte_length = ceil((size[0] + 7) / (16 / colors)) # how long each valid row is
        data_bytes = b"".join([int(str(valid_row), colors).to_bytes(byte_length, "big") for valid_row in valid_rows])
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
        valid_rows = [[int(char) for char in valid_row] for valid_row in valid_rows]
        return valid_rows
    def get_this_state() -> str: return "".join(["".join([str(char) for char in valid_row]) for valid_row in valid_rows[:6]]) + ",".join([str(i) for i in row_tries])
    if seed is None: seed = random.randint(-2147483648, 2147483647)
    after_seed = random.randint(-2147483648, 2147483647) # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    max_per_row = size[0] // colors
    max_per_column = size[1] // colors
    
    three_in_a_row_regular_expression_base_0 = re.compile("|".join([str(i) + "{3}" for i in range(colors)]))
    three_in_a_row_regular_expression_base_1 = re.compile("|".join([str(i) + "{3}" for i in range(1, colors + 1)]))
    valid_rows = get_valid_rows()
    random.shuffle(valid_rows)

    y_position = 0
    tiles:list[int] = [0 for i in range(size[0] * size[1])] # output
    volume = size[0] * size[1] * colors
    wave_collapse_storage:dict[int,list[int]] = {} # javascript arrays define an index as undefined and don't change length of list when deleting an index
    output_rows:dict[int,list[int]] = dict([(i, None) for i in range(7)]) # for debug
    row_tries:list[int] = [0 for i in range(size[1])]
    if volume <= 392: previous_states:set[str] = set()
    while y_position < size[1]:
        if volume <= 392:
            this_state = get_this_state()
            if this_state in previous_states: random.shuffle(valid_rows) # protection against stalling
            previous_states.add(this_state)
        # print(seed, size, this_state, wave_collapse_storage, output_rows, row_tries, y_position, len(valid_rows))

        row_tries[y_position] += 1
        current_row = valid_rows.pop(0)
        # print(seed, size, wave_collapse_storage, output_rows, row_tries, y_position)
        for x_position in range(size[0]):
            set_tile_to(x_position, y_position, current_row[x_position] + 1)
        output_rows[y_position] = current_row
        if row_or_column_is_valid():
            wave_collapse_storage[y_position] = current_row
            y_position += 1
        else:
            valid_rows.append(current_row)
            clear_row_from_tiles(y_position)
            if row_tries[y_position] >= len(valid_rows):
                row_tries[y_position] = 0
                for remove_index in range(1, y_position):
                    clear_row_from_tiles(remove_index)
                    row_tries[remove_index] = 0
                y_position = 1
    random.seed(after_seed) # NOTE: random seed is reset here!
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

def get_tile_order(current_tile_index:int, size:tuple[int,int], colors:int) -> list[int]:
    current_tile_pos = get_pos(current_tile_index, size)
    same_row = [tile_index for tile_index in get_row(current_tile_pos[1], size) if tile_index != current_tile_index]
    same_column = [tile_index for tile_index in get_column(current_tile_pos[0], size) if tile_index != current_tile_index]
    other_tiles = [tile_index for tile_index in range(size[0] * size[1]) if tile_index != current_tile_index and tile_index not in same_row and tile_index not in same_column]
    if size[0] * size[1] * colors < 392:
        output = [current_tile_index] + same_row + same_column + other_tiles
    else: output = same_row + same_column + [current_tile_index] + other_tiles
    return output

def restore_cache(tiles_values:list[list[int]], tiles_cache:list[list[int]], colors:int) -> None:
    DEFAULT = list(range(1, colors + 1))
    for index, tile in enumerate(tiles_cache):
        if tile != DEFAULT: tiles_values[index] = tile[:]

def solve(size:tuple[int,int], tiles_values:list[list[int]], current_tile_index:int, dependencies:list[list[int]], tiles_cache:list[list[int]], colors:int) -> bool:
    '''This function goes through all of the tiles, attempting to solve empty ones. If it does and it is the wanted
    tile, then hurray, return True. If it isn't, continue. It continues to grow the found tiles until it can finally
    solve the desired tile.'''
    tile_order = get_tile_order(current_tile_index, size, colors) # the order it solves tiles in. Tiles at beginning are looked at first and more often.
    restore_cache(tiles_values, tiles_cache, colors)
    previous_tile = None
    for total_tries in range(size[0] * size[1] * 50): # it can loop around again and continue trying to solve if it fails the first time.
        # this range can theoretically be extended to infinity, since it will break if it can't find any tile at all.
        # It is not necessary to raise for bigger boards (probably), since it scales with the area.
        was_successful = False
        for tile_index in tile_order: # the index of this resets every time it finds a tile's value, since it breaks.
            if len(tiles_values[tile_index]) != 1 and previous_tile != tile_index:
                if breakdown_tile(size, tiles_values, tile_index, dependencies, tiles_cache, colors): # setting of the tile's type occurs in here. Tile's type is set to default in `breakdown`
                    was_successful = True
                    previous_tile = tile_index
                    break
        if not was_successful: break # occurs if it failed to find any tiles
        elif len(tiles_values[current_tile_index]) == 1: return True # if the desired tile has been solved
    else: raise RuntimeError("The board expired!")
    # NOTE: before it returns, it also activates a function `v()`, which does nothing. It could potentially be reassigned somewhere
    return [len(tile) == 1 for tile in tiles_values].count(False) == 0
    # occurs if the tile is truly impossible to find.
    # If there are no empty tiles, then the board is completable, and completable without the current tile

def grid_is_valid(size:tuple[int,int], tiles_values:list[list[int]], colors:int=2) -> bool: # NOTE: this is no longer called.
    '''Returns False if the row/column is not valid, because of three-in-a-row, unbalanced, or duplicate'''
    three_in_a_row_regular_expression = re.compile("|".join([str(i) + "{3}" for i in range(1, colors + 1)]))
    def is_invalid_row(row:str) -> bool:
        '''Detects the invalidity of a row or column if empty is 0, red is 1, and blue is 2'''
        if bool(three_in_a_row_regular_expression.search(row)): return True
        for color in range(1, colors + 1):
            if row.count(str(color)) > max_per_row: return True
        return False
    def is_invalid_column(column:str) -> bool:
        '''Detects the invalidity of a row or column if empty is 0, red is 1, and blue is 2'''
        if bool(three_in_a_row_regular_expression.search(column)): return True
        for color in range(1, colors + 1):
            if column.count(str(color)) > max_per_column: return True
        return False
    tiles_values = collapse_board(tiles_values, colors, False)
    max_per_row = size[0] // 2
    max_per_column = size[1] // 2
    already_columns:set[str] = set()
    already_rows:set[str] = set()
    for index in range(size[1]):
        column = get_values(tiles_values, get_column(index, size))
        column_string = "".join(column)
        if is_invalid_column(column, column_string):
            return False
        elif column.count(0) == 0:
            if column_string in already_columns: return False
            else: already_columns.add(column_string)
    for index in range(size[0]):
        row = get_values(tiles_values, get_row(index, size))
        row_string = "".join(row)
        if is_invalid_row(row, row_string):
            return False
        elif row.count(0) == 0:
            if row_string in already_rows: return False
            else: already_rows.add(row_string)
    else: return True

def breakdown_tile(size:tuple[int,int], tiles_values:list[list[int]], tile_index:int, dependencies:list[list[int]], tiles_cache:list[list[int]], colors:int=2) -> bool:
    '''Sets a tile to its value; returns if it did that. This does not receive the `current_tile`, but instead a (probably)
    different, empty tile determined by the `solve` function.'''
    # NOTE: if you wish to make the produced puzzles harder, modify this function to include additional rules.
    was_successful = False
    collection_success, empty_row_pair_with_index, empty_column_pair_with_index = collect(size, tiles_values, tile_index, dependencies, tiles_cache, colors)
    if collection_success: was_successful = True
    if empty_column_pair_with_index is not None and len(tiles_values[tile_index]) != 1 and see_if_it_has_a_clone(tiles_values, tile_index, empty_column_pair_with_index, size, dependencies, tiles_cache, colors):
        was_successful = True
    if empty_row_pair_with_index is not None and len(tiles_values[tile_index]) != 1 and see_if_it_has_a_clone(tiles_values, tile_index, empty_row_pair_with_index, size, dependencies, tiles_cache, colors):
        was_successful = True
    return was_successful

def see_if_it_has_a_clone(tiles_values:list[list[int]], tile_index:int, other_tile_index:int, size:tuple[int,int], dependencies:list[list[int]], tiles_cache:list[list[int]], colors:int) -> bool:
    '''Parameters are the two tiles that make up the missing part of a line while attempting to find a clone.
    It sets the values to their possible values, and checks if it duplicates another line. If it does,
    then it sets the first given tile to its only possible value, and leaves the other one empty.'''
    DEFAULT = list(range(1, colors + 1))
    pre_tile = tiles_values[tile_index][:] # used for resetting
    pre_other_tile = tiles_values[other_tile_index][:]
    tile_pos, other_tile_pos = get_pos(tile_index, size), get_pos(other_tile_index, size)
    is_row = tile_pos[0] != other_tile_pos[0] # if their x-positions are the same, it is a column
    this_index = tile_pos[int(is_row)]
    this_row_or_column_indexes = get_row(this_index, size) if is_row else get_column(this_index, size)
    this_row_or_column_values = get_values(tiles_values, this_row_or_column_indexes)
    max_per_row_or_column = size[int(is_row)] // colors
    for value in DEFAULT:
        if value not in tiles_values[tile_index]: continue
        if this_row_or_column_values.count([value]) >= max_per_row_or_column: continue
        for other_value in DEFAULT:
            if value == other_value: continue
            if other_value not in tiles_values[other_tile_index]: continue
            if this_row_or_column_values.count([value]) >= max_per_row_or_column: continue
            # print(value, other_value, tiles_values[tile_index], tiles_values[other_tile_index], tile_index, other_tile_index)
            temp_tile = tiles_values[tile_index][:]; temp_other_tile = tiles_values[other_tile_index][:]
            tiles_values[tile_index] = [value]; tiles_values[other_tile_index] = [other_value]
            index_carrier:list[int] = [] # will contain the indexes of the cloned row/column after row_or_column_is_cloning
            is_cloning = row_or_column_is_cloning(tiles_values, tile_index, other_tile_index, size, colors, index_carrier)
            tiles_values[tile_index] = temp_tile; tiles_values[other_tile_index] = temp_other_tile
            if is_cloning:
                dependencies_copy = index_carrier
                dependencies[tile_index] = dependencies_copy
                dependencies[other_tile_index] = dependencies_copy[:]
                rule_out_value(tiles_cache[tile_index], value)
                rule_out_value(tiles_cache[other_tile_index], other_value)
                rule_out_value(tiles_values[tile_index], value)
                rule_out_value(tiles_values[other_tile_index], other_value)
                return True
    else:
        tiles_values[tile_index] = pre_tile # reset
        tiles_values[other_tile_index] = pre_other_tile
        return False

def row_or_column_is_cloning(tiles_values:list[list[int]], tile_index:int, other_tile_index:int, size:tuple[int,int], colors:int, index_carrier:list[int]|None=None) -> bool:
    tile_pos = get_pos(tile_index, size); other_tile_pos = get_pos(other_tile_index, size)
    is_row = tile_pos[0] != other_tile_pos[0] # if their x-positions are the same, it is a column
    this_index = tile_pos[int(is_row)]
    this_row_or_column_indexes = get_row(this_index, size) if is_row else get_column(this_index, size)
    this_row_or_column_values = get_values(tiles_values, this_row_or_column_indexes)
    for index in range(size[int(is_row)]): # FIXME: this might have bug of checking even rows that aren't full.
        if index == this_index: continue
        row_or_column_indexes = get_row(index, size) if is_row else get_column(index, size)
        row_or_column_values = get_values(tiles_values, row_or_column_indexes)
        if this_row_or_column_values == row_or_column_values:
            if index_carrier is not None:
                index_carrier.extend(row_or_column_indexes)
                index_carrier.extend(this_row_or_column_indexes)
            return True
    else: return False

def rule_out_value(tile:list[int], value:int) -> None:
    # if value in tile: tile.remove(value)
    tile.remove(value)

def collect(size:tuple[int,int], tiles_values:list[list[int]], tile_index:int, dependencies:list[list[int]], tiles_cache:list[list[int]], colors:int) -> tuple[bool, int|None,int|None]:
    '''The possible tile value based on rules for removing during breakdown, for reasons such as cap-at-two-in-a-row, between, or others. Also returns the
    empty_row_pair_with and empty_column_pair_with's indexes'''
    DIRECTIONS = [(-1, 0), (1, 0), (0, 1), (0, -1)]
    DEFAULT = list(range(1, colors + 1))
    did_something = False
    directional_tiles:list[int] = [] # stores the indexes for left_tile, right_tile, up_tile etc. using the below thing
    for direction in DIRECTIONS:
        tile_in_direction1 = get_tile_in_direction(tile_index, direction, size)
        directional_tiles.append(tile_in_direction1)
        if did_something and colors == 2: continue # skip if the value is already known
        if tile_in_direction1 is None: continue
        tile_in_direction2 = get_tile_in_direction(tile_in_direction1, direction, size)
        if tile_in_direction2 is None: continue
        for testing_value in tiles_values[tile_index][:]:
            if tiles_values[tile_in_direction1] == [testing_value] and tiles_values[tile_in_direction2] == [testing_value]:
                dependencies[tile_index].extend([tile_in_direction1, tile_in_direction2])
                rule_out_value(tiles_cache[tile_index], testing_value)
                rule_out_value(tiles_values[tile_index], testing_value)
                did_something = True
    left_tile, right_tile, down_tile, up_tile = directional_tiles
    for testing_value in tiles_values[tile_index][:]:
        if left_tile is not None and right_tile is not None and tiles_values[left_tile] == [testing_value] and tiles_values[right_tile] == [testing_value]:
            dependencies[tile_index].extend([left_tile, right_tile])
            rule_out_value(tiles_cache[tile_index], testing_value)
            rule_out_value(tiles_values[tile_index], testing_value)
            did_something = True
            if colors == 2: break
            continue
        if down_tile is not None and up_tile is not None and tiles_values[down_tile] == [testing_value] and tiles_values[up_tile] == [testing_value]:
            dependencies[tile_index].extend([up_tile, down_tile])
            rule_out_value(tiles_cache[tile_index], testing_value)
            rule_out_value(tiles_values[tile_index], testing_value)
            did_something = True
            if colors == 2: break
            continue
   
    tile_pos = get_pos(tile_index, size)
    max_per_row = size[0] // colors; max_per_column = size[1] // colors
    empty_row_pair_with = None; empty_column_pair_with = None

    def add_dependencies(index_list:list[int], value:int) -> list[int]:
        '''Returns all items that are the given value within the given index list. Is used for dependencies of in-a-row-or-column.'''
        dependency:list[int] = []
        for index in index_list:
            if tiles_values[index] == [value]: dependency.append(index)
        return dependency
    def apply_dependencies(index_list:list[int], dependency:list[int], value:int) -> bool:
        '''Applies dependencies, caching, and possibilities to all possible tiles in the row/column. Returns if it actually did anything or not.'''
        was_successful = False
        for index in index_list:
            if value not in tiles_values[index] or len(tiles_values[index]) == 1: continue # NOTE: I am having a brain fart with this and this line may be wrong. Original is if it's not empty
            dependencies[index].extend(dependency)
            # print(index, value, tiles_cache[index], tiles_values[index])
            rule_out_value(tiles_cache[index], value)
            rule_out_value(tiles_values[index], value)
            was_successful = True
        return was_successful

    row_indexes = get_row(tile_pos[1], size)
    row_values = get_values(tiles_values, row_indexes)
    row_values_counts = [row_values.count([color]) for color in DEFAULT]
    if row_values_counts.count(max_per_row) != colors: # if the row is not full
        for color in DEFAULT:
            if row_values_counts[color - 1] >= max_per_row: # minus one because `row_values_counts` doesn't start at index 1
                dependency = add_dependencies(row_indexes, color)
                was_successful = apply_dependencies(row_indexes, dependency, color)
                if was_successful: did_something = True
    # print(count_unknown_tiles(row_values), row_values)
    if count_unknown_tiles(row_values) == 2: # this is used for cloning
        for index, row_tile_index in enumerate(row_indexes):
            if len(row_values[index]) != 1 and index != tile_pos[0]:
                empty_row_pair_with = row_tile_index
                break
        else: raise RuntimeError()

    column_indexes = get_column(tile_pos[0], size)
    column_values = get_values(tiles_values, column_indexes)
    column_values_counts = [column_values.count([color]) for color in DEFAULT]
    if column_values_counts.count(max_per_column) != colors: # if the column is not full
        for color in DEFAULT:
            if column_values_counts[color - 1] >= max_per_column:  # minus one because `column_values_counts` doesn't start at index 1
                dependency = add_dependencies(column_indexes, color)
                was_successful = apply_dependencies(column_indexes, dependency, color)
                if was_successful: did_something = True
    # print(count_empty_tiles(column_values), column_values)
    if count_unknown_tiles(column_values) == 2:
        for index, column_tile_index in enumerate(column_indexes):
            if len(column_values[index]) != 1 and index != tile_pos[1]:
                empty_column_pair_with = column_tile_index
                break
        else: raise RuntimeError()
    return did_something, empty_row_pair_with, empty_column_pair_with

def get_values(tiles_values:list[list[int]], indexes:list[int]) -> list[list[int]]:
    '''Gets the values of a list of indexes'''
    return [tiles_values[index] for index in indexes]
def get_row(y_position:int, size:tuple[int,int]) -> list[int]:
    '''Returns a list of indexes in the row'''
    return list(range(y_position * size[0], (y_position + 1) * size[0], 1))
def get_column(x_position:int, size:tuple[int,int]) -> list[int]:
    '''Returns a list of indexes in the column'''
    return list(range(x_position, size[0] * size[1], size[0]))

def get_tile_in_direction(tile_index:int, direction:tuple[int,int], size:tuple[int,int]) -> int|None:
    tile_pos = get_pos(tile_index, size)
    new_pos = (tile_pos[0] + direction[0], tile_pos[1] + direction[1])
    if new_pos[0] >= 0 and new_pos[0] < size[0] and new_pos[1] >= 0 and new_pos[1] < size[1]: return get_index(new_pos, size)
    else: return None

def get_pos(index:int, size:tuple[int,int]) -> tuple[int,int]:
    return (index % size[0], index // size[0])
def get_index(pos:tuple[int,int], size:tuple[int,int]) -> int:
    return (pos[0] + pos[1] * size[0])

def strip_dependencies(dependencies:list[list[int]], tiles:list[int], tile_index:int, tiles_cache:list[list[int]], colors:int) -> None:
    '''Removes tiles related to the given tile and resets their dependencies'''
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
        was_successful = solve(size, tiles, tile_index, dependencies, tiles_cache, colors)
        tiles = current_state

        if was_successful: tiles[tile_index] = DEFAULT[:]; since_last_success = 0
        else: tiles[tile_index] = tile_value; since_last_success += 1 # resets the tile's value in case it cannot be extrapolated from current board
        # print_board(tiles, size)
    # The reason that you can just solve for the current tile instead of the whole board
    # when checking if you need the tile is that
    random.seed(after_seed)
    tiles = collapse_board(tiles, colors, True)
    if all([color not in tiles for color in range(1, colors + 1)]): # if there are no non-empty tiles
        raise RuntimeError("The board is empty!")
    return tiles

def collapse_board(tiles:list[list[int]], colors:int=None, strict:bool=False) -> list[int]:
    output:list[int] = []
    for tile in tiles:
        if len(tile) == 0: raise ValueError("0-length tile!")
        if len(tile) == 1: output.append(tile[0])
        elif strict and len(tile) < colors: raise ValueError("%s-length tile!" % len(tile))
        else: output.append(0)
    return output

def print_board(tiles:list[int]|list[list[int]]|str, size:tuple[int,int]|int) -> None:
    if isinstance(size, int): width = size
    else: width, height = size
    if isinstance(tiles[0], list): tiles = collapse_board(tiles, strict=False)
    emojis = {0: "⬛", 1: "🟥", 2: "🟦", 3: "🟨", 4: "🟩", 5: "🟪", 6: "🟧", 7: "🟫", 8: "⬜"}
    output = ""
    for index, tile in enumerate(tiles):
        output += emojis[int(tile)]
        if index % width == width - 1: output += "\n"
    print(output)

if __name__ == "__main__":
    os.chdir(os.path.split(os.path.split(__file__)[0])[0])
    size = 4
    # full, empty, other_data = cProfile.run("generate(size, 1234, 3)")
    full, empty, other_data = generate(size, 284, colors=2)

    print("FULL:")
    print_board(full, size)
    print("EMPTY:")
    print_board(empty, size)
