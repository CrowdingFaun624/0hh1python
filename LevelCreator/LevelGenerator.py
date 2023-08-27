import collections
import math
import os
import random
import re
from math import ceil

from numpy import base_repr, binary_repr

try:
    import LevelCreator.LevelUtilities as LU
except ImportError:
    import LevelUtilities as LU

def grid_is_valid(size:tuple[int,int], colors:int, y_position:int, max_per_column:int, tiles:list[int], is_final:bool) -> bool:
    already_columns:list[list[int]] = []
    for index in range(size[0]):
        column = get_column(size, tiles, index) # TODO: remove functions `get_column` and `is_invalid_list` and just put them into this function.
        if is_invalid_list(colors, y_position, max_per_column, column): return False
        elif is_final:
            if column in already_columns: return False # TODO: this line is probably very expensive.
            else: already_columns.append(column)
    return True

def clear_row_from_tiles(size:tuple[int,int], tiles:list[int], valid_rows:collections.deque[list[int]], y:int) -> None:
    valid_rows.append(tiles[y * size[0]:(y + 1) * size[0]])
    tiles[y * size[0]:(y + 1) * size[0]] = [-1] * size[0]

def get_column(size:tuple[int,int], tiles:list[int], x_position:int) -> list[int]:
    return [i for i in tiles[x_position::size[0]]]

def is_invalid_string(colors:int, max_per_row:int, regular_expression:re.Pattern[str], row:str) -> bool:
    '''Detects the invalidity of a row or column if red is 0 and blue is 1'''
    for color in range(colors):
        if row.count(str(color)) > max_per_row: return True
    if bool(regular_expression.search(row)): return True
    return False

def is_invalid_list(colors:int, y_position:int, max_per_column:int, column:list[int]) -> bool:
    '''Detects the invalidity of a row or column if empty is 0, red is 1, and blue is 2'''
    if y_position >= 2 and (column[y_position] != -1 and column[y_position] == column[y_position-1] and column[y_position] == column[y_position-2]): return True
    for color in range(colors): # TODO: when a row is added/removed from 
        if column.count(color) > max_per_column: return True
    return False

def get_valid_rows(size:tuple[int,int], colors:int, max_per_row:int, regular_expression:re.Pattern[str]) -> list[list[int]]:
    if colors ** size[0] >= 4096:
        cached_data = fetch_cache(size, colors)
        if cached_data is not None: return cached_data
    valid_rows:list[list[int]] = []
    for index in range(colors ** size[0]):
        index_string = int_to_string(index, colors).zfill(size[0])
        if not is_invalid_string(colors, max_per_row, regular_expression, index_string):
            index_list = [int(i) for i in index_string]
            valid_rows.append(index_list)
    if colors ** size[0] >= 4096: create_cache(size, colors, valid_rows)
    return valid_rows

def create_cache(size:tuple[int,int], colors:int, valid_rows:list[list[int]]) -> None:
    path_name = "./_cache/solution_%s_%s.bin" % (size[0], colors)
    if os.path.exists(path_name): return
    byte_length = ceil((size[0] + 7) / (16 / colors)) # how long each valid row is
    data_bytes = b"".join([int("".join(int_to_string(tile, colors) for tile in valid_row), colors).to_bytes(byte_length, "big") for valid_row in valid_rows])
    with open(path_name, "wb") as f:
        f.write(data_bytes)

def fetch_cache(size:tuple[int,int], colors:int) -> list[list[int]]|None:
    path_name = "./_cache/solution_%s_%s.bin" % (size[0], colors)
    if not os.path.exists(path_name): return None
    byte_length = ceil((size[0] + 7) / (16 / colors)) # how long each valid row is
    valid_rows:list[list[int]] = []
    with open(path_name, "rb") as f:
        f.seek(0, os.SEEK_END); file_size = f.tell(); f.seek(0, os.SEEK_SET) # get size
        for i in range(file_size // byte_length):
            data = f.read(byte_length)
            valid_rows.append([int(tile, colors) for tile in list(int_to_string(int.from_bytes(data, "big"), colors).zfill(size[0]))])
    return valid_rows

def int_to_string(number:int, base:int) -> str: # https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base
    return binary_repr(number) if base == 2 else base_repr(number, base)

def generate_solution(size:tuple[int,int], seed:int=None, colors:int=2, gen_info:LU.GenerationInfo|None=None) -> list[int]:
    # wave collapse algorithm I think
    if seed is None: seed = LU.get_seed()
    if isinstance(size, int): size = (size, size)
    after_seed = LU.get_seed() # seed to start using after this is done to restore the randomness.
    random.seed(seed)
    max_per_row = size[0] // colors
    max_per_column = size[1] // colors
    
    regular_expression = re.compile("|".join([str(i) + "{3}" for i in range(colors)]))
    valid_rows = get_valid_rows(size, colors, max_per_row, regular_expression)
    random.shuffle(valid_rows)
    valid_rows = collections.deque(valid_rows)

    y_position = 0
    tiles:list[int] = [-1 for i in range(size[0] * size[1])] # output
    row_tries:list[int] = [0] * size[1]
    previous_states:set[str] = set()
    total_clears = 0
    expected_total_clears = (20 * (10 ** -colors))*math.exp((size[1]/colors)*(2.2 * colors - 2.6))
    while y_position < size[1]:
        # LevelPrinter.print_board([tile + 1 for tile in tiles], size)
        row_tries[y_position] += 1
        
        current_row = valid_rows.popleft()
        tiles[y_position * size[0]:(y_position + 1) * size[0]] = current_row

        if grid_is_valid(size, colors, y_position, max_per_column, tiles, y_position == size[1] - 1):
            y_position += 1
        else:
            clear_row_from_tiles(size, tiles, valid_rows, y_position)
            if row_tries[y_position] >= len(valid_rows):
                this_state = tuple([tuple(valid_row) for valid_row in valid_rows])
                if this_state in previous_states: random.shuffle(valid_rows) # TODO: this could be a potentially slow algorithm for queues. See https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle
                previous_states.add(this_state)
                row_tries[y_position] = 0
                for remove_index in range(1, y_position):
                    clear_row_from_tiles(size, tiles, valid_rows, remove_index)
                    row_tries[remove_index] = 0
                y_position = 1
            if gen_info is not None:
                if gen_info.breaker: return None
                gen_info.generation_progress = ((-expected_total_clears / (total_clears + expected_total_clears)) + 1.0) * 0.9
                gen_info.total_clears += 1
            total_clears += 1
    random.seed(after_seed)
    tiles = [tile + 1 for tile in tiles]
    return tiles

if __name__ == "__main__":
    SIZE = 6
    SEED = None
    COLORS = 2

    full = generate_solution(SIZE, SEED, COLORS)
    LU.print_board(full, SIZE)
