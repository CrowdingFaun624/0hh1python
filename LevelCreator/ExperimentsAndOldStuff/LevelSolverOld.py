def get_tile_order(current_tile_index:int, size:tuple[int,int], colors:int) -> list[int]:
    current_tile_pos = get_pos(current_tile_index, size)
    same_row = [tile_index for tile_index in get_row(current_tile_pos[1], size) if tile_index != current_tile_index]
    same_column = [tile_index for tile_index in get_column(current_tile_pos[0], size) if tile_index != current_tile_index]
    other_tiles = [tile_index for tile_index in range(size[0] * size[1]) if tile_index != current_tile_index and tile_index not in same_row and tile_index not in same_column]
    if size[0] * size[1] * colors < 392:
        output = [current_tile_index] + same_row + same_column + other_tiles
    else: output = same_row + same_column + [current_tile_index] + other_tiles
    return output

def solve(size:tuple[int,int], tiles_values:list[list[int]], current_tile_index:int, dependencies:list[list[int]], colors:int) -> bool:
    '''This function goes through all of the tiles, attempting to solve empty ones. If it does and it is the wanted
    tile, then hurray, return True. If it isn't, continue. It continues to grow the found tiles until it can finally
    solve the desired tile.'''
    tile_order = get_tile_order(current_tile_index, size, colors) # the order it solves tiles in. Tiles at beginning are looked at first and more often.
    previous_tile = None
    for total_tries in range(size[0] * size[1] * 50): # it can loop around again and continue trying to solve if it fails the first time.
        # this range can theoretically be extended to infinity, since it will break if it can't find any tile at all.
        # It is not necessary to raise for bigger boards (probably), since it scales with the area.
        was_successful = False
        for tile_index in tile_order: # the index of this resets every time it finds a tile's value, since it breaks.
            if len(tiles_values[tile_index]) != 1 and previous_tile != tile_index:
                if breakdown_tile(size, tiles_values, tile_index, dependencies, colors): # setting of the tile's type occurs in here. Tile's type is set to default in `breakdown`
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

def breakdown_tile(size:tuple[int,int], tiles_values:list[list[int]], tile_index:int, dependencies:list[list[int]], colors:int=2) -> bool:
    '''Sets a tile to its value; returns if it did that. This does not receive the `current_tile`, but instead a (probably)
    different, empty tile determined by the `solve` function.'''
    # NOTE: if you wish to make the produced puzzles harder, modify this function to include additional rules.
    was_successful = False
    collection_success, empty_row_pair_with_index, empty_column_pair_with_index = collect(size, tiles_values, tile_index, dependencies, colors)
    if collection_success: was_successful = True
    if empty_column_pair_with_index is not None and len(tiles_values[tile_index]) != 1 and see_if_it_has_a_clone(tiles_values, tile_index, empty_column_pair_with_index, size, dependencies, colors):
        was_successful = True # TODO: check for len(tiles_values[empty_column_pair_with_index]) too
    if empty_row_pair_with_index is not None and len(tiles_values[tile_index]) != 1 and see_if_it_has_a_clone(tiles_values, tile_index, empty_row_pair_with_index, size, dependencies, colors):
        was_successful = True # TODO: check for len(tiles_values[empty_column_pair_with_index]) too
    return was_successful

def see_if_it_has_a_clone(tiles_values:list[list[int]], tile_index:int, other_tile_index:int, size:tuple[int,int], dependencies:list[list[int]], colors:int) -> bool:
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
    this_row_or_column_values = get_values(tiles_values, this_row_or_column_indexes) # TODO: this isn't even used.
    max_per_row_or_column = size[int(is_row)] // colors
    for value in DEFAULT:
        if value not in tiles_values[tile_index]: continue
        # if this_row_or_column_values.count([value]) >= max_per_row_or_column: continue
        for other_value in DEFAULT:
            if value == other_value: continue
            if other_value not in tiles_values[other_tile_index]: continue
            # if this_row_or_column_values.count([value]) >= max_per_row_or_column: continue
            # print(value, other_value, tiles_values[tile_index], tiles_values[other_tile_index], tile_index, other_tile_index)
            temp_tile = tiles_values[tile_index][:]; temp_other_tile = tiles_values[other_tile_index][:]
            tiles_values[tile_index] = [value]; tiles_values[other_tile_index] = [other_value]
            index_carrier:list[int] = [] # will contain the indexes of the cloned row/column after row_or_column_is_cloning
            is_cloning = row_or_column_is_cloning(tiles_values, tile_index, other_tile_index, size, colors, index_carrier)
            tiles_values[tile_index] = temp_tile; tiles_values[other_tile_index] = temp_other_tile
            if is_cloning:
                dependencies_copy = index_carrier
                dependencies[tile_index].extend(dependencies_copy) # TODO: make it extend instead
                dependencies[other_tile_index].extend(dependencies_copy)
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

def collect(size:tuple[int,int], tiles_values:list[list[int]], tile_index:int, dependencies:list[list[int]], colors:int) -> tuple[bool, int|None,int|None]:
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
                rule_out_value(tiles_values[tile_index], testing_value)
                did_something = True # TODO: add break
    left_tile, right_tile, down_tile, up_tile = directional_tiles
    for testing_value in tiles_values[tile_index][:]:
        if left_tile is not None and right_tile is not None and tiles_values[left_tile] == [testing_value] and tiles_values[right_tile] == [testing_value]:
            dependencies[tile_index].extend([left_tile, right_tile])
            rule_out_value(tiles_values[tile_index], testing_value)
            did_something = True
            if colors == 2: break
            continue
        if down_tile is not None and up_tile is not None and tiles_values[down_tile] == [testing_value] and tiles_values[up_tile] == [testing_value]:
            dependencies[tile_index].extend([up_tile, down_tile])
            rule_out_value(tiles_values[tile_index], testing_value)
            did_something = True
            if colors == 2: break
            continue
    tile_pos = get_pos(tile_index, size)
    max_per_row = size[0] // colors; max_per_column = size[1] // colors
    empty_row_pair_with = None; empty_column_pair_with = None

    def add_dependencies(index_list:list[int], value:int) -> list[int]:
        '''Returns all items that are the given value within the given index list. Is used for dependencies of in-a-row-or-column.'''
        return [index for index in index_list if tiles_values[index] == [value]]
    def apply_dependencies(index_list:list[int], dependency:list[int], value:int) -> bool:
        '''Applies dependencies, caching, and possibilities to all possible tiles in the row/column. Returns if it actually did anything or not.'''
        was_successful = False
        for index in index_list:
            if value not in tiles_values[index] or len(tiles_values[index]) == 1: continue # NOTE: I am having a brain fart with this and this line may be wrong. Original is if it's not empty
            dependencies[index].extend(dependency)
            rule_out_value(tiles_values[index], value)
            was_successful = True
        return was_successful
    def add_dependencies_rule_5(index_list:list[int], value:int) -> list[int]:
        return [index for index in index_list if value not in tiles_values[index]]
    def apply_dependencies_rule_5(index_list:list[int], dependency:list[int], value:int) -> bool:
        was_successful = False
        for index in index_list:
            if len(tiles_values[index]) > 1 and value in tiles_values[index]:
                dependencies[index].extend(dependency)
                tiles_values[index] = [value]
                was_successful = True
        return was_successful

    row_indexes = get_row(tile_pos[1], size)
    row_values = get_values(tiles_values, row_indexes)
    row_values_counts = [row_values.count([color]) for color in DEFAULT]
    if colors != 2: row_values_counts_empty = [[color in tile and len(tile) != 1 for tile in row_values].count(True) for color in DEFAULT] # count of colors in possibilities only
    if row_values_counts.count(max_per_row) != colors: # if the row is not full
        for color in DEFAULT:
            if row_values_counts[color - 1] >= max_per_row: # minus one because `row_values_counts` doesn't start at index 1
                dependency = add_dependencies(row_indexes, color)
                was_successful = apply_dependencies(row_indexes, dependency, color)
                if was_successful: did_something = True
                continue
            if colors == 2: continue # rule is specific to >= 3 colors
            if row_values_counts_empty[color - 1] + row_values_counts[color - 1] == max_per_row:
                dependency = add_dependencies_rule_5(row_indexes, color)
                was_successful = apply_dependencies_rule_5(row_indexes, dependency, color)
                if was_successful: did_something = True # TODO: add a break here because it sets the tile's value anyways (and test performance)
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
    if colors != 2: column_values_counts_empty = [[color in tile and len(tile) != 1 for tile in column_values].count(True) for color in DEFAULT] # count of colors in possibilities only
    if column_values_counts.count(max_per_column) != colors: # if the column is not full
        for color in DEFAULT:
            if column_values_counts[color - 1] >= max_per_column:  # minus one because `column_values_counts` doesn't start at index 1
                dependency = add_dependencies(column_indexes, color)
                was_successful = apply_dependencies(column_indexes, dependency, color)
                if was_successful: did_something = True
                continue
            if colors == 2: continue # rule is specific to >= 3 colors
            if column_values_counts_empty[color - 1] + column_values_counts[color - 1] == max_per_column:
                dependency = add_dependencies_rule_5(column_indexes, color)
                was_successful = apply_dependencies_rule_5(column_indexes, dependency, color)
                if was_successful: did_something = True # TODO: add a break here because it sets the tile's value anyways (and test performance)
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

def count_empty_tiles(tiles:list[int]) -> int:
    return tiles.count(0)
def count_unknown_tiles(tiles:list[list[int]]) -> int:
    '''Returns the number of tiles whose values are not completely known.'''
    return [len(tile) == 1 for tile in tiles].count(False)
