try:
    import Utilities.LevelPrinter as LevelPrinter
except ImportError:
    import LevelPrinter

# TILE UTILITIES

def get_row_indexes(size:tuple[int,int], y_position:int) -> list[int]:
    '''Returns a list of indexes in the row.'''
    return list(range(y_position * size[0], (y_position + 1) * size[0], 1))
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
def get_incomplete_tile_indexes(index_list:list[int], tiles:list[list[int]]) -> list[int]:
    '''Returns tiles in the index list whose values are not compeltely known.'''
    return [tile_index for tile_index in index_list if len(tiles[tile_index]) != 1]
def get_incomplete_tile_indexes_within(index_list:list[int], tiles:list[list[int]]) -> list[int]:
    '''Returns position of tile within the index list (not index within `tiles`) from tiles in the index list whose values are not compeltely known.'''
    return [index for index, tile_index in enumerate(index_list) if len(tiles[tile_index]) != 1]

# SOLVE UTILITIES

def get_rows_to_solve(size:tuple[int,int], tiles:list[list[int]]) -> list[int]:
    '''Returns the row indexes that contain at least one non-complete tile.'''
    return [row_index for row_index in range(size[1]) if has_incomplete_tiles(get_values(get_row_indexes(size, row_index), tiles))]
def get_columns_to_solve(size:tuple[int,int], tiles:list[list[int]]) -> list[int]:
    '''Returns the column indexes that contain at least one non-complete tile.'''
    return [column_index for column_index in range(size[1]) if has_incomplete_tiles(get_values(get_column_indexes(size, column_index), tiles))]

def add_tiles_to_axes_to_solve(size, tiles_modified:list[int], rows_to_solve:list[int], columns_to_solve:list[int], rows_to_solve_copy:list[int]|None, columns_to_solve_copy:list[int]|None) -> None:
    '''Appends to rows_to_solve and columns_to_solve using the modified tiles.''' # TODO: make it do local *and* copy
    rows = set([tile_modified // size[0] for tile_modified in tiles_modified])
    columns = set([tile_modified % size[0] for tile_modified in tiles_modified])

    not_in_rows_to_solve = rows - set(rows_to_solve)
    not_in_columns_to_solve = columns - set(columns_to_solve)
    rows_to_solve.extend(sorted(list(not_in_rows_to_solve)))
    columns_to_solve.extend(sorted(list(not_in_columns_to_solve)))

    if rows_to_solve_copy is not None:
        not_in_rows_to_solve_copy = rows - set(rows_to_solve_copy)
        rows_to_solve_copy.extend(sorted(list(not_in_rows_to_solve_copy)))
    if columns_to_solve_copy is not None:
        not_in_columns_to_solve_copy = columns - set(columns_to_solve_copy)
        columns_to_solve_copy.extend(sorted(list(not_in_columns_to_solve_copy)))

# SOLVERS

def solve_three_in_a_row(colors:int, indexes:list[int], tiles:list[list[int]], dependencies:list[list[int]]|None) -> tuple[bool,list[int]]:
    '''Solves for three-in-a-row on a row or column using the given indexes. Modifies the given values list. Returns if it changed a tile and the indexes of the tiles it modified.'''
    was_successful = False
    tiles_modified:list[int] = []

    POSSIBLE_VALUES = range(1, colors + 1)
    previous_tile1:int|None = None # tile before current
    previous_tile2:int|None = None # tile twice before current
    previous_tile3:int|None = None # tile thrice before current; used for finding value on other side of three-in-a-row

    def chain(*iterables): # https://stackoverflow.com/questions/35205162/iterating-over-two-lists-one-after-another # TODO: make this say it returns an int
        for iterable in iterables:
            yield from iterable
    for tile_index in chain(indexes, [None]):
        tile_index:int # TODO remove line
        if previous_tile2 is not None:
            for color in POSSIBLE_VALUES: # TODO: if color not in tiles[tile_index] and color not in tiles[previous_tile1] and color not in tiles[previous_tile3]: continue
                if tiles[previous_tile1] == [color] and tiles[previous_tile2] == [color]: # caps
                    if tile_index is not None and color in tiles[tile_index]: # tile after cap
                        tiles[tile_index].remove(color)
                        if dependencies is not None: dependencies[tile_index].extend([previous_tile1, previous_tile2])
                        was_successful = True
                        tiles_modified.append(tile_index)
                    if previous_tile3 is not None and color in tiles[previous_tile3]: # tile before cap
                        tiles[previous_tile3].remove(color)
                        if dependencies is not None: dependencies[previous_tile3].extend([previous_tile1, previous_tile2])
                        was_successful = True
                        tiles_modified.append(previous_tile3)

                if tile_index is not None and tiles[tile_index] == [color] and tiles[previous_tile2] == [color]: # between
                    if color in tiles[previous_tile1]:
                        previous_tile1:int
                        tiles[previous_tile1].remove(color)
                        if dependencies is not None: dependencies[previous_tile1].extend([tile_index, previous_tile2])
                        was_successful = True
                        tiles_modified.append(previous_tile1)

        previous_tile3 = previous_tile2
        previous_tile2 = previous_tile1
        previous_tile1 = tile_index
    return was_successful, tiles_modified

def solve_balancing(size:int, colors:int, indexes:list[int], tiles:list[list[int]], dependencies:list[list[int]]|None) -> tuple[bool,list[int]]:
    def create_dependency(color:int) -> list[int]:
        '''Creates a list of values that are known to be `color`.'''
        return [tile_index for tile_index in indexes if tiles[tile_index] == [color]]
    def apply_dependencies(color:int, dependency:list[int]|None) -> bool:
        '''Applies dependencies and sets tiles to their possible values. Returns if anything changed or not.'''
        was_successful = False
        for tile_index in indexes:
            if len(tiles[tile_index]) != 1 and color in tiles[tile_index]:
                tiles[tile_index].remove(color)
                if tile_index not in tiles_modified: tiles_modified.append(tile_index)
                if dependencies is not None: dependencies[tile_index].extend(dependency)
                was_successful = True
        return was_successful

    values = get_values(indexes, tiles)
    max_per_row = size // colors
    did_something = False
    tiles_modified:list[int] = []
    for color in range(1, colors + 1):
        if values.count([color]) == max_per_row:
            dependency = create_dependency(color) if dependencies is not None else None
            was_successful = apply_dependencies(color, dependency)
            if was_successful: did_something = True
    return did_something, tiles_modified

def solve_cloning(size:tuple[int,int], tiles:list[list[int]], dependencies:list[list[int]]) -> tuple[bool,list[int]]: # TODO: optimize this to only test for rows/columns that have been updated.
    def apply_dependencies(empty_row_indexes:list[int], full_row_indexes:list[int], empty_tile1:int, empty_tile2:int) -> None:
        dependency = empty_row_indexes[:]
        dependency.extend(full_row_indexes)
        dependency.remove(empty_tile1)
        dependency.remove(empty_tile2)
        dependencies[empty_tile1].extend(dependency)
        dependencies[empty_tile2].extend(dependency[:])
    # TODO: reduce code duplication
    missing_two_tiles_rows:list[list[list[int]]] = [] # stores values of rows
    missing_two_tiles_rows_y:list[int] = [] # stores y postion of rows
    missing_two_tiles_rows_x:list[list[int]] = [] # stores x positions of tiles
    full_rows_y:list[int] = []
    was_successful = False
    tiles_modified:list[int] = []
    # FIND ROWS
    for row_y in range(size[1]):
        row_indexes = get_row_indexes(size, row_y)
        unknown_tiles = get_incomplete_tile_indexes_within(row_indexes, tiles) # index within row of unknown tiles
        match len(unknown_tiles):
            case 2:
                row_values = get_values(row_indexes, tiles)[:]
                tile1, tile2 = unknown_tiles
                for color1 in row_values[tile1]:
                    for color2 in row_values[tile2]: # TODO: they can't be the same
                        if color1 == color2: continue
                        new_row = row_values[:]
                        new_row[tile1] = [color1]; new_row[tile2] = [color2]
                        missing_two_tiles_rows.append(new_row)
                        missing_two_tiles_rows_y.append(row_y)
                        missing_two_tiles_rows_x.append(unknown_tiles)
            case 0: full_rows_y.append(row_y)
    # SOLVE ROWS
    for full_row_y in full_rows_y: # TODO: redo this to iterate over the empty rows/columns instead and measure performance.
        full_row_indexes = get_row_indexes(size, full_row_y)
        row_values = get_values(full_row_indexes, tiles)
        if row_values not in missing_two_tiles_rows: continue
        empty_row_index = missing_two_tiles_rows.index(row_values) # finds which empty row it can duplicate.
        y = missing_two_tiles_rows_y[empty_row_index]
        x1, x2 = missing_two_tiles_rows_x[empty_row_index]
        tile1_not = tiles[x1 + full_row_y * size[0]][0]
        tile2_not = tiles[x2 + full_row_y * size[0]][0]
        empty_index1 = x1 + y * size[0]; empty_index2 = x2 + y * size[0]
        tiles[empty_index1].remove(tile1_not)
        tiles[empty_index2].remove(tile2_not)
        empty_row_indexes = get_row_indexes(size, y)
        if dependencies is not None: apply_dependencies(empty_row_indexes, full_row_indexes, empty_index1, empty_index2)
        was_successful = True
        if empty_index1 not in tiles_modified: tiles_modified.append(empty_index1)
        if empty_index2 not in tiles_modified: tiles_modified.append(empty_index2)
    # FIND COLUMNS
    missing_two_tiles_columns:list[list[list[int]]] = [] # stores values of columns
    missing_two_tiles_columns_x:list[int] = [] # stores x postion of columns
    missing_two_tiles_columns_y:list[list[int]] = [] # stores y positions of tiles
    full_columns_x:list[int] = []
    for column_x in range(size[0]):
        column_indexes = get_column_indexes(size, column_x)
        unknown_tiles = get_incomplete_tile_indexes_within(column_indexes, tiles) # index within column of unknown tiles
        match len(unknown_tiles):
            case 2:
                column_values = get_values(column_indexes, tiles)[:]
                tile1, tile2 = unknown_tiles
                for color1 in column_values[tile1]:
                    for color2 in column_values[tile2]:
                        if color1 == color2: continue
                        new_column = column_values[:]
                        new_column[tile1] = [color1]; new_column[tile2] = [color2]
                        missing_two_tiles_columns.append(new_column)
                        missing_two_tiles_columns_x.append(column_x)
                        missing_two_tiles_columns_y.append(unknown_tiles)
            case 0: full_columns_x.append(column_x)
    # SOLVE COLUMNS
    for full_column_x in full_columns_x:
        full_column_indexes = get_column_indexes(size, full_column_x)
        column_values = get_values(full_column_indexes, tiles)
        if column_values not in missing_two_tiles_columns: continue
        empty_column_index = missing_two_tiles_columns.index(column_values) # finds which empty column it can duplicate.
        y1, y2 = missing_two_tiles_columns_y[empty_column_index]
        x = missing_two_tiles_columns_x[empty_column_index]
        tile1_not = tiles[full_column_x + y1 * size[0]][0] # the value that the first unknown tile can't be
        tile2_not = tiles[full_column_x + y2 * size[0]][0] # the value that the second unknown tile can't be
        empty_index1 = x + y1 * size[0]; empty_index2 = x + y2 * size[0]
        tiles[empty_index1].remove(tile1_not)
        tiles[empty_index2].remove(tile2_not)
        empty_column_indexes = get_column_indexes(size, x)
        if dependencies is not None: apply_dependencies(empty_column_indexes, full_column_indexes, empty_index1, empty_index2)
        was_successful = True
        if empty_index1 not in tiles_modified: tiles_modified.append(empty_index1)
        if empty_index2 not in tiles_modified: tiles_modified.append(empty_index2)
    return was_successful, tiles_modified

def solve_balancing_possibilities(size:int, colors:int, indexes:list[int], tiles:list[list[int]], dependencies:list[list[int]]|None) -> tuple[bool,list[int]]:
    '''if the sum of the number of tiles that could be a certain color and the number of tiles that are known to be that color is the maximum that can be in that row or column,
    then all tiles that can possibly be that color are and only are that color.'''
    DEFAULT = list(range(1, colors + 1))
    other_colors:list[list[int]] = [[color2 for color2 in DEFAULT if color2 != color] for color in DEFAULT] # used as a cache

    full_colors_counts:list[int] = [0 for i in range(colors)] # tracks indexes of fully known.
    empty_colors:list[list[int]] = [[] for i in range(colors)] # tracks indexes of possibilities.
    not_colors:list[list[int]] = [[] for i in range(colors)] # tracks tiles that can not be a certain color.
    for tile_index in indexes:
        if len(tiles[tile_index]) == 1:
            color_index = tiles[tile_index][0] - 1 # -1 to get usable index
            full_colors_counts[color_index] += 1
            if dependencies is not None:
                for other_color in other_colors[color_index]: not_colors[other_color - 1].append(tile_index)
        else:
            for color in DEFAULT:
                if color in tiles[tile_index]: empty_colors[color - 1].append(tile_index)
                elif dependencies is not None: not_colors[color - 1].append(tile_index)
    max_per_row = size // colors
    was_successful = False
    tiles_modified:list[int] = []
    for color_index in range(colors):
        if full_colors_counts[color_index] == max_per_row: continue
        if full_colors_counts[color_index] + len(empty_colors[color_index]) == max_per_row:
            if dependencies is not None: dependency = not_colors[color_index]
            for tile_index in empty_colors[color_index]:
                tiles[tile_index] = [color_index + 1] # +1 to get color from index
                if dependencies is not None: dependencies[tile_index].extend(dependency)
            tiles_modified.extend(empty_colors[color_index])
            was_successful = True
            if max_per_row <= 2: break
    return was_successful, tiles_modified

def solve(size:tuple[int,int]|int, colors:int, tiles:list[list[int]], desired_tile_index:int|None=None, dependencies:list[list[int]]|None=None, error_on_failure:bool=False) -> bool:
    '''Solves a board, and returns the tiles list. If `desired_tile_index` is specified, it will break early.
    If `dependencies` is specified, it will extend items of the list with the tiles required to find them. Returns
    if it was able to find the desired tile or not.'''
    if isinstance(size, int): size = (size, size)
    rows_to_solve = get_rows_to_solve(size, tiles)
    columns_to_solve = get_columns_to_solve(size, tiles)
    def init_solve_row(row_index:int, unsolved_rows:set[int]) -> tuple[list[int],bool]:
        '''Initializing stuff within a for loop. Returns the index list and if it should continue or not.'''
        index_list = get_row_indexes(size, row_index)
        if not has_incomplete_tiles(get_values(index_list, tiles)):
            unsolved_rows.add(row_index)
            return index_list, True
        return index_list, False
    def init_solve_column(column_index:int, unsolved_columns:set[int]) -> tuple[list[int],bool]:
        index_list = get_column_indexes(size, column_index)
        if not has_incomplete_tiles(get_values(index_list, tiles)):
            unsolved_columns.add(column_index)
            return index_list, True
        return index_list, False
    def finalize_solve(row_index:int, was_successful:bool, unsolved_rows:set[int], tiles_modified:list[int]) -> None:
        if was_successful: unsolved_rows.discard(row_index)
        else: unsolved_rows.add(row_index)
        add_tiles_to_axes_to_solve(size, tiles_modified, rows_to_solve, columns_to_solve, rows_to_solve_local, columns_to_solve_local)
    def got_desired_tile() -> bool:
        return was_successful and desired_tile_index is not None and len(tiles[desired_tile_index]) == 1
    
    def three_in_a_row() -> bool:
        did_something = False
        for row_index in rows_to_solve_local:
            index_list, should_continue = init_solve_row(row_index, unsolved_rows)
            if should_continue: continue
            was_successful, tiles_modified = solve_three_in_a_row(colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            finalize_solve(row_index, was_successful, unsolved_rows, tiles_modified)
        for column_index in columns_to_solve_local:
            index_list, should_continue = init_solve_column(column_index, unsolved_columns)
            was_successful, tiles_modified = solve_three_in_a_row(colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            finalize_solve(column_index, was_successful, unsolved_columns, tiles_modified)
        return did_something
    def balancing() -> bool:
        did_something = False
        for row_index in rows_to_solve_local:
            index_list, should_continue = init_solve_row(row_index, unsolved_rows)
            if should_continue: continue
            was_successful, tiles_modified = solve_balancing(size[0], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            else: unsolved_rows.add(row_index)
            finalize_solve(row_index, was_successful, unsolved_rows, tiles_modified)
        for column_index in columns_to_solve_local:
            index_list, should_continue = init_solve_column(column_index, unsolved_columns)
            was_successful, tiles_modified = solve_balancing(size[1], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            finalize_solve(column_index, was_successful, unsolved_columns, tiles_modified)
        return did_something
    def balancing_possibilities() -> bool:
        did_something = False
        for row_index in rows_to_solve_local:
            index_list, should_continue = init_solve_row(row_index, unsolved_rows)
            if should_continue: continue
            was_successful, tiles_modified = solve_balancing_possibilities(size[0], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            finalize_solve(row_index, was_successful, unsolved_rows, tiles_modified)
        for column_index in columns_to_solve_local:
            index_list, should_continue = init_solve_column(column_index, unsolved_columns)
            if should_continue: continue
            was_successful, tiles_modified = solve_balancing_possibilities(size[1], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            finalize_solve(column_index, was_successful, unsolved_columns, tiles_modified)
        return did_something

    total_tries = 0
    while has_incomplete_tiles(tiles):
        # LevelPrinter.print_board(tiles, size)
        if total_tries != 0 and not did_something:
            if error_on_failure:
                LevelPrinter.print_board(tiles, size)
                raise RuntimeError("Failed to solve board!")
            else: return False
        total_tries += 1
        did_something = False
        # while len(rows_to_solve) != 0 and len(columns_to_solve) != 0:
        rows_to_solve_copy = rows_to_solve[:]
        columns_to_solve_copy = columns_to_solve[:]
        rows_to_solve = []
        columns_to_solve = []
        
        # rows_to_solve_local = rows_to_solve_copy[:]
        # columns_to_solve_local = columns_to_solve_copy[:]
        # while len(rows_to_solve_local) != 0 and len(columns_to_solve_local) != 0: # THREE-IN-A-ROW
            # unsolved_rows:set[int] = set()
            # unsolved_columns:set[int] = set()
            # was_successful = three_in_a_row()
            # if got_desired_tile(): return True
            # if was_successful: did_something = True
            # for unsolved_row in unsolved_rows: rows_to_solve_local.remove(unsolved_row)
            # for unsolved_column in unsolved_columns: columns_to_solve_local.remove(unsolved_column)
        # rows_to_solve_local = rows_to_solve_copy[:]
        # columns_to_solve_local = columns_to_solve_copy[:]
        # while len(rows_to_solve_local) != 0 and len(columns_to_solve_local) != 0: # BALANCING
            # unsolved_rows:set[int] = set()
            # unsolved_columns:set[int] = set()
            # was_successful = balancing()
            # if got_desired_tile(): return True
            # if was_successful: did_something = True
            # for unsolved_row in unsolved_rows: rows_to_solve_local.remove(unsolved_row)
            # for unsolved_column in unsolved_columns: columns_to_solve_local.remove(unsolved_column)
        # if colors != 2:
            # rows_to_solve_local = rows_to_solve_copy[:]
            # columns_to_solve_local = columns_to_solve_copy[:]
            # while len(rows_to_solve_local) != 0 and len(columns_to_solve_local) != 0: # BALANCE POSSIBILITIES
                # unsolved_rows:set[int] = set()
                # unsolved_columns:set[int] = set()
                # was_successful = balancing_possibilities()
                # if got_desired_tile(): return True
                # if was_successful: did_something = True
                # for unsolved_row in unsolved_rows: rows_to_solve_local.remove(unsolved_row)
                # for unsolved_column in unsolved_columns: columns_to_solve_local.remove(unsolved_column)
        rows_to_solve_local = rows_to_solve_copy[:]
        columns_to_solve_local = columns_to_solve_copy[:]
        while len(rows_to_solve_local) != 0 and len(columns_to_solve_local) != 0:
            unsolved_rows:set[int] = set()
            unsolved_columns:set[int] = set()
            was_successful = three_in_a_row()
            if got_desired_tile(): return True
            if was_successful: did_something = True
            was_successful = balancing()
            if got_desired_tile(): return True
            if was_successful: did_something = True
            if colors != 2:
                was_successful = balancing_possibilities()
                if got_desired_tile(): return True
                if was_successful: did_something = True
            for unsolved_row in unsolved_rows: rows_to_solve_local.remove(unsolved_row)
            for unsolved_column in unsolved_columns: columns_to_solve_local.remove(unsolved_column)

        if len(rows_to_solve) != 0 or len(columns_to_solve) != 0: continue

        # expensive rules go down here.
        
        # CLONING

        was_successful, tiles_modified = solve_cloning(size, tiles, dependencies)
        if was_successful: did_something = True
        if was_successful and desired_tile_index is not None and len(tiles[desired_tile_index]) == 1: return True
        add_tiles_to_axes_to_solve(size, tiles_modified, rows_to_solve, columns_to_solve, None, None)
    if desired_tile_index is not None: return len(tiles[desired_tile_index]) == 1

if __name__ == "__main__":

    # tiles = [
        # [1,2,3],[2],[1],[1,2,3],[1,2,3],[2],
        # [3],[1,2,3],[1,2,3],[1,2,3],[2],[1,2,3],
        # [1,2,3],[1,2,3],[1,2,3],[2],[1,2,3],[1],
        # [1,2,3],[3],[1],[1,2,3],[1,2,3],[1],
        # [1],[1,2,3],[1,2,3],[1,2,3],[2],[3],
        # [1],[1,2,3],[3],[1],[1,2,3],[1,2,3]
        # ]
    # size = (6, 6)
    # colors = 3

    # tiles = [
        # [1,2],[1,2],[1,2],[1,2],[1,2],[1,2],
        # [1,2],[1],[1,2],[1],[1,2],[1,2],
        # [1,2],[1,2],[2],[1],[1,2],[2],
        # [1,2],[2],[1,2],[1,2],[1],[1,2],
        # [1,2],[1,2],[1,2],[1,2],[2],[1],
        # [1],[1,2],[1],[1,2],[1,2],[1,2]
    # ]
    # size = (6, 6)
    # colors = 2

    # tiles = [ # (6, 29, 3) before fix 1
    #     [1],[1],[1,2,3],[3],[2],[3],
    #     [1,2,3],[1],[1,2,3],[1,2,3],[2],[3],
    #     [2],[1,2,3],[1],[1],[1,2,3],[1,2,3],
    #     [3],[1,2,3],[3],[1,2,3],[1,2,3],[1,2,3],
    #     [1,2,3],[1,2,3],[1,2,3],[1],[3],[2],
    #     [1,2,3],[1,2,3],[1,2,3],[1,2,3],[1,2,3],[1,2,3]
    # ]
    # size = (6, 6)
    # colors = 3

    tiles = [ # (6, 29, 3) after fix 1
        [1,2,3],[1],[1,2,3],[3],[2],[3],
        [1,2,3],[1],[1,2,3],[1,2,3],[2],[1,2,3],
        [2],[3],[1,2,3],[1],[3],[1,2,3],
        [3],[1,2,3],[3],[1,2,3],[1,2,3],[1,2,3],
        [1,2,3],[1,2,3],[1],[1],[1,2,3],[2],
        [1,2,3],[1,2,3],[1,2,3],[1,2,3],[1,2,3],[1]
    ]
    size = (6, 6)
    colors = 3

    LevelPrinter.print_board(tiles, 6)
    print(tiles)
    dependencies = [[] for i in range(size[0] * size[1])]
    solve(size, colors, tiles, None, dependencies)
    LevelPrinter.print_board(tiles, 6)
    print(tiles)
    print(dependencies)

# TODO: replace shit with sets and see if it's faster.