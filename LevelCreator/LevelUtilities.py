import random
import re

from numpy import base_repr, binary_repr


def get_row_indexes(size:tuple[int,int], y_position:int) -> list[int]:
    '''Returns a list of indexes in the row.'''
    return list(range(y_position * size[0], (y_position + 1) * size[0]))
def get_column_indexes(size:tuple[int,int], x_position:int) -> list[int]:
    '''Returns a list of indexes in the column.'''
    return list(range(x_position, size[0] * size[1], size[0]))
def get_values(indexes:list[int], tiles:list[list[int]]) -> list[list[int]]:
    '''Gets the values of a list of indexes.'''
    return [tiles[index] for index in indexes]
def count_complete_tiles(tiles:list[list[int]]) -> int:
    '''Returns the number of tiles whose values are completely known.'''
    return [len(tile) == 1 for tile in tiles].count(True)
def has_incomplete_tiles(tiles:list[list[int]]) -> bool: # TODO: check the performance of this vs `count_complete_tiles`
    for tile in tiles:
        if len(tile) != 1: return True
    else: return False
def has_complete_tiles(tiles:list[list[int]]) -> bool:
    for tile in tiles:
        if len(tile) == 1: return True
    else: return False
def get_incomplete_tile_indexes(index_list:list[int], tiles:list[list[int]]) -> list[int]:
    '''Returns tiles in the index list whose values are not compeltely known.'''
    return [tile_index for tile_index in index_list if len(tiles[tile_index]) != 1]
def get_incomplete_tile_indexes_within(index_list:list[int], tiles:list[list[int]]) -> list[int]:
    '''Returns position of tile within the index list (not index within `tiles`) from tiles in the index list whose values are not completely known.'''
    return [index for index, tile_index in enumerate(index_list) if len(tiles[tile_index]) != 1]

def expand_board(colors:int, tiles:list[int]) -> list[list[int]]:
    '''Turns a list of integers into a list of lists of singular integers.'''
    DEFAULT = list(range(1, colors + 1))
    return [DEFAULT[:] if tile == 0 else [tile] for tile in tiles]

def collapse_board(tiles:list[list[int]], colors:int=None, strict:bool=False) -> list[int]:
    output:list[int] = []
    for tile_index, tile in enumerate(tiles):
        if strict and len(tile) == 0: raise ValueError("0-length tile at %s!" % tile_index)
        if len(tile) == 1: output.append(tile[0])
        elif strict and len(tile) < colors: raise ValueError("%s-length tile at %s!" % (len(tile), tile_index))
        else: output.append(0)
    return output

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
        # tiles[affected_tile] = 0

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

def copy_tiles(tiles:list[list[int]]) -> list[list[int]]:
    return [copy_tile[:] for copy_tile in tiles]

def boards_match(empty_board:list[list[int]], full_board:list[list[int]], colors:int|None=None) -> bool:
    '''Returns if the first board is valid according to the second board; i.e., all elements in the second board can be in the first board.'''
    if isinstance(empty_board[0], int): empty_board = expand_board(colors, empty_board)
    if isinstance(full_board[0], int): full_board = expand_board(colors, full_board)
    for tile_index in range(len(empty_board)):
        if full_board[tile_index][0] not in empty_board[tile_index]: return False
    else: return True
def get_not_matching_tiles(empty_board:list[list[int]], full_board:list[list[int]], colors:int|None=None) -> list[int]:
    '''Returns the indexes from empty_board that do not fit with full_board.'''
    if isinstance(empty_board[0], int): empty_board = expand_board(colors, empty_board)
    if isinstance(full_board[0], int): full_board = expand_board(colors, full_board)
    return [tile_index for tile_index in range(len(empty_board)) if full_board[tile_index][0] not in empty_board[tile_index]]

def check_for_duplicates(board:list[list[int]]) -> list[tuple[int,int]]:
    '''Returns the indexes of any objects that `is` another object within the list.'''
    output:list[tuple[int,int]] = []
    for index1, item1 in enumerate(board):
        if isinstance(item1, list): raise ValueError("Board is not expanded!")
        for index2, item2 in enumerate(board):
            if index1 == index2: continue
            if item1 is item2: output.append((index1, index2, item1, item2))
    return output

def get_seed() -> int:
    return random.randint(-2147483648, 2147483647)

class GenerationInfo(): # for communication between threads
    def __init__(self) -> None:
        self.breaker = False
        self.generation_progress = 0.0
        self.total_clears = 0
        self.seed = None
        self.exception_holder = None

def int_to_string(number:int, base:int) -> str: # https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base
    return binary_repr(number) if base == 2 else base_repr(number, base)

def is_invalid_string(colors:int, max_per_row:int, regular_expression:re.Pattern[str], row:str) -> bool:
    '''Detects the invalidity of a row or column if red is 0 and blue is 1'''
    for color in range(colors):
        if row.count(str(color)) > max_per_row: return True
    if bool(regular_expression.search(row)): return True
    return False

def fetch_greatest_valid_size(size:int, colors:int, max_size:int|None=None) -> int:
    regular_expression = re.compile("|".join([str(i) + "{3}" for i in range(colors)]))
    max_per_row = int(size // colors)
    total = 0
    for index in range(colors ** size):
        if not is_invalid_string(colors, max_per_row, regular_expression, int_to_string(index, colors).zfill(size)):
            total += 1
        if max_size is not None and total >= max_size: return max_size
    return total

def get_greatest_valid_size(size:int, colors:int, max_size:int|None=None) -> int:
    '''Returns the greatest vertical size for any given horizontal size. Will only return up to the max_size if specified. e.g. 6 -> 14'''
    data = { # pre-programmed values for speedy fast
            2: {2: 2, 4: 6, 6: 14, 8: 34, 10: 84, 12: 208, 14: 518, 16: 1296, 18: 3254, 20: 8196},
            3: {3: 6, 6: 90, 9: 1314, 12: 21084, 15: 353772},
            4: {4: 24, 8: 2520}
           }
    if colors in data and size in data[colors]:
        if max_size is None:
            return data[colors][size]
        else: return min(max_size, data[colors][size])
    else: return fetch_greatest_valid_size(size, colors, max_size)
