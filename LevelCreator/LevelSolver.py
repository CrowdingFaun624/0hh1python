try:
    import LevelCreator.LevelUtilities as LU
    import LevelCreator.LevelValidator as LevelValidator
except ImportError:
    import LevelUtilities as LU
    import LevelValidator

RETURN_NOW = "RETURN NOW"

# SOLVE UTILITIES

def get_rows_to_solve(size:tuple[int,int], tiles:list[list[int]]) -> list[int]:
    '''Returns the row indexes that contain at least one non-complete tile.'''
    return [row_index for row_index in range(size[1]) if LU.has_incomplete_tiles(values := LU.get_values(LU.get_row_indexes(size, row_index), tiles)) and LU.has_complete_tiles(values)]
def get_columns_to_solve(size:tuple[int,int], tiles:list[list[int]]) -> list[int]:
    '''Returns the column indexes that contain at least one non-complete tile.'''
    return [column_index for column_index in range(size[1]) if LU.has_incomplete_tiles(values := LU.get_values(LU.get_column_indexes(size, column_index), tiles)) and LU.has_complete_tiles(values)]

def add_full_rows(tiles:list[list[int]], size:tuple[int,int], rows_to_solve:list[int], columns_to_solve:list[int], unsolved_rows:set[int], unsolved_columns:set[int]) -> None:
    for row_index in rows_to_solve:
        values = LU.get_values(LU.get_row_indexes(size, row_index), tiles)
        if not LU.has_incomplete_tiles(values): unsolved_rows.add(row_index)
    for column_index in columns_to_solve:
        values = LU.get_values(LU.get_column_indexes(size, column_index), tiles)
        if not LU.has_incomplete_tiles(values): unsolved_columns.add(column_index)

def add_tiles_to_axes_to_solve(size, tiles_modified:list[int], rows_to_solves:list[list[int]], columns_to_solves:list[list[int]], unsolved_rows:set[int], unsolved_columns:set[int]) -> None:
    '''Appends to rows_to_solve and columns_to_solve using the modified tiles.'''
    rows = set([tile_modified // size[0] for tile_modified in tiles_modified])
    columns = set([tile_modified % size[0] for tile_modified in tiles_modified])
    if unsolved_rows is not None: unsolved_rows -= rows
    if unsolved_columns is not None: unsolved_columns -= columns

    for index, rows_to_solve in enumerate(rows_to_solves):
        not_in_rows_to_solve = rows - set(rows_to_solve)
        rows_to_solve.extend(sorted(list(not_in_rows_to_solve)))
    for index, columns_to_solve in enumerate(columns_to_solves):
        not_in_columns_to_solve = columns - set(columns_to_solve)
        columns_to_solve.extend(sorted(list(not_in_columns_to_solve)))

# SOLVERS

def solve_three_in_a_row(colors:int, indexes:list[int], tiles:list[list[int]], dependencies:list[list[int]]|None) -> tuple[bool,list[int]]:
    '''Solves for three-in-a-row on a row or column using the given indexes. Modifies the given values list. Returns if it changed a tile and the indexes of the tiles it modified.'''
    was_successful = False
    tiles_modified:list[int] = []

    POSSIBLE_VALUES = range(1, colors + 1)
    previous_tile1:int|None = None # tile before current
    previous_tile2:int|None = None # tile twice before current
    previous_tile3:int|None = None # tile thrice before current; used for finding value on other side of three-in-a-row

    def chain(*iterables) -> list[int]: # https://stackoverflow.com/questions/35205162/iterating-over-two-lists-one-after-another
        for iterable in iterables:
            yield from iterable
    for tile_index in chain(indexes, [None]):
        if previous_tile2 is not None:
            for color in POSSIBLE_VALUES: # TODO: this does stuff even when all relevant tiles are full.
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

    values = LU.get_values(indexes, tiles)
    max_per_row = size // colors
    did_something = False
    tiles_modified:list[int] = []
    for color in range(1, colors + 1):
        if values.count([color]) == max_per_row:
            dependency = create_dependency(color) if dependencies is not None else None
            was_successful = apply_dependencies(color, dependency)
            if was_successful: did_something = True
    return did_something, tiles_modified

def solve_cloning(size:tuple[int,int], tiles:list[list[int]], dependencies:list[list[int]]|None=None) -> tuple[bool,list[int]]: # TODO: optimize this to only test for rows/columns that have been updated.
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
    full_rows_values:list[list[list[int]]] = []
    was_successful = False
    tiles_modified:list[int] = []
    # FIND ROWS
    for row_y in range(size[1]):
        row_indexes = LU.get_row_indexes(size, row_y)
        unknown_tiles = LU.get_incomplete_tile_indexes_within(row_indexes, tiles) # index within row of unknown tiles
        row_values = LU.get_values(row_indexes, tiles)[:]
        match len(unknown_tiles):
            case 2:
                # if row_y not in rows_to_solve: continue
                tile1, tile2 = unknown_tiles
                for color1 in row_values[tile1]:
                    for color2 in row_values[tile2]:
                        if color1 == color2: continue
                        new_row = row_values[:]
                        new_row[tile1] = [color1]; new_row[tile2] = [color2]
                        missing_two_tiles_rows.append(new_row)
                        missing_two_tiles_rows_y.append(row_y)
                        missing_two_tiles_rows_x.append(unknown_tiles)
            case 0:
                if row_values in full_rows_values: continue # if the row is already existing
                full_rows_values.append(row_values)
                full_rows_y.append(row_y)
    # SOLVE ROWS
    for index, full_row_y in enumerate(full_rows_y): # TODO: redo this to iterate over the empty rows/columns instead and measure performance.
        full_row_indexes = LU.get_row_indexes(size, full_row_y)
        # row_values = get_values(full_row_indexes, tiles)
        row_values = full_rows_values[index]
        if row_values not in missing_two_tiles_rows: continue
        empty_row_index = missing_two_tiles_rows.index(row_values) # finds which empty row it can duplicate.
        y = missing_two_tiles_rows_y[empty_row_index]
        x1, x2 = missing_two_tiles_rows_x[empty_row_index]
        tile1_not = tiles[x1 + full_row_y * size[0]][0]
        tile2_not = tiles[x2 + full_row_y * size[0]][0]
        empty_index1 = x1 + y * size[0]; empty_index2 = x2 + y * size[0]
        tiles[empty_index1].remove(tile1_not)
        tiles[empty_index2].remove(tile2_not)
        empty_row_indexes = LU.get_row_indexes(size, y)
        if dependencies is not None: apply_dependencies(empty_row_indexes, full_row_indexes, empty_index1, empty_index2)
        was_successful = True
        if empty_index1 not in tiles_modified: tiles_modified.append(empty_index1)
        if empty_index2 not in tiles_modified: tiles_modified.append(empty_index2)
    # FIND COLUMNS
    missing_two_tiles_columns:list[list[list[int]]] = [] # stores values of columns
    missing_two_tiles_columns_x:list[int] = [] # stores x postion of columns
    missing_two_tiles_columns_y:list[list[int]] = [] # stores y positions of tiles
    full_columns_x:list[int] = []
    full_columns_values:list[list[list[int]]] = []
    for column_x in range(size[0]):
        column_indexes = LU.get_column_indexes(size, column_x)
        unknown_tiles = LU.get_incomplete_tile_indexes_within(column_indexes, tiles) # index within column of unknown tiles
        column_values = LU.get_values(column_indexes, tiles)[:]
        match len(unknown_tiles):
            case 2:
                # if column_x not in columns_to_solve: continue
                tile1, tile2 = unknown_tiles
                for color1 in column_values[tile1]:
                    for color2 in column_values[tile2]:
                        if color1 == color2: continue
                        new_column = column_values[:]
                        new_column[tile1] = [color1]; new_column[tile2] = [color2]
                        missing_two_tiles_columns.append(new_column)
                        missing_two_tiles_columns_x.append(column_x)
                        missing_two_tiles_columns_y.append(unknown_tiles)
            case 0:
                if column_values in full_columns_values: continue
                full_columns_values.append(column_values)
                full_columns_x.append(column_x)
    # SOLVE COLUMNS
    for index, full_column_x in enumerate(full_columns_x):
        full_column_indexes = LU.get_column_indexes(size, full_column_x)
        # column_values = get_values(full_column_indexes, tiles)
        column_values = full_columns_values[index]
        if column_values not in missing_two_tiles_columns: continue
        empty_column_index = missing_two_tiles_columns.index(column_values) # finds which empty column it can duplicate.
        y1, y2 = missing_two_tiles_columns_y[empty_column_index]
        x = missing_two_tiles_columns_x[empty_column_index]
        tile1_not = tiles[full_column_x + y1 * size[0]][0] # the value that the first unknown tile can't be
        tile2_not = tiles[full_column_x + y2 * size[0]][0] # the value that the second unknown tile can't be
        empty_index1 = x + y1 * size[0]; empty_index2 = x + y2 * size[0]
        tiles[empty_index1].remove(tile1_not)
        tiles[empty_index2].remove(tile2_not)
        empty_column_indexes = LU.get_column_indexes(size, x)
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

    full_colors_counts:list[int] = [0] * colors # tracks indexes of fully known.
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

def solve_rule_4(size:int, colors:int, indexes:list[int], tiles:list[list[int]], dependencies:list[list[int]]|None=None) -> tuple[bool,list[int]]:
    '''if the row contains the same amount of reds missing and blues missing, return without doing anything.
    Otherwise, for each empty tile, do the following: place the less common color there. Then for each other tile, place the more common color by default,
    but place the less common color if there would be a three-in-a-row error otherwise. If the number of additional less common tiles exceeds that color's
    original missing count, then the placed tile is not the less common color.'''
    full_color_counts:list[int] = [0] * colors
    all_color_counts:list[int] = [0] * colors
    full_tile_indexes:list[int] = []
    empty_tiles_indexes:list[int] = [] # index in `tiles`
    empty_indexes:list[int] = [] # indexes in `indexes`
    for index, tile_index in enumerate(indexes):
        if len(tiles[tile_index]) == 1:
            full_color_counts[tiles[tile_index][0] - 1] += 1
            full_tile_indexes.append(tile_index)
        else:
            empty_indexes.append(index)
            empty_tiles_indexes.append(tile_index)
        for color in tiles[tile_index]:
            all_color_counts[color - 1] += 1
    if all_color_counts.count(0) != colors - 2: return False, []
    if full_color_counts.count(0) != colors - 2: return False, []
    more_common_color = None; less_common_color = None
    for color_index, amount in enumerate(full_color_counts):
        if amount == 0: continue
        if more_common_color is None: more_common_color = color_index + 1
        else:
            if full_color_counts[more_common_color - 1] > amount: less_common_color = color_index + 1
            else: more_common_color, less_common_color = color_index + 1, more_common_color
    if full_color_counts[more_common_color - 1] == full_color_counts[less_common_color - 1]: return False, []
    max_per_row = size // colors
    if full_color_counts[more_common_color - 1] == max_per_row or full_color_counts[less_common_color - 1] == max_per_row: return False, []
    def add_to_involved(indexes:list[int]) -> None:
        for index in indexes:
            if index not in tiles_involved_in_error: tiles_involved_in_error.append(index)
        testing_row[empty_index] = [more_common_color]
    
    testing_row = LU.copy_tiles(LU.get_values(indexes, tiles))
    tiles_involved_in_error:list[int] = [] # indexes with `indexes` that were involved in an error.
    error_count = 0 # how many times it did a bad.
    for index in range(len(empty_indexes)):
        empty_index = empty_indexes[index]
        previous_index1 = empty_index - 1
        previous_index2 = empty_index - 2
        next_index1 = empty_index + 1
        next_index2 = empty_index + 2
        if previous_index1 >= 0 and next_index1 < size and testing_row[previous_index1] == [less_common_color] and testing_row[next_index1] == [less_common_color]:
            add_to_involved([previous_index1, next_index1, empty_index]); error_count += 1
        elif previous_index2 >= 0 and testing_row[previous_index2] == [less_common_color] and testing_row[previous_index1] == [less_common_color]:
            add_to_involved([previous_index2, previous_index1, empty_index]); error_count += 1
        elif next_index2 < size and testing_row[next_index2] == [less_common_color] and testing_row[next_index1] == [less_common_color]:
            add_to_involved([next_index2, next_index1, empty_index]); error_count += 1
        else:
            testing_row[empty_index] = [less_common_color]
    tiles_modified:list[int] = []
    if error_count >= max_per_row - (full_color_counts[more_common_color - 1]):
        for index, empty_index in enumerate(empty_indexes):
            if empty_index in tiles_involved_in_error: continue
            tile_index = empty_tiles_indexes[index]
            tiles_modified.append(tile_index)
            tiles[tile_index] = [less_common_color]
            if dependencies is not None: dependencies[tile_index] = full_tile_indexes[:]
    return len(tiles_modified) > 0, tiles_modified

def solve(size:tuple[int,int]|int, colors:int, tiles:list[list[int]], desired_tile_index:int|None=None, dependencies:list[list[int]]|None=None, error_on_failure:bool=False, return_on_find:bool=False, hard_mode:bool=True) -> bool|int:
    '''Solves a board, and returns the tiles list. If `desired_tile_index` is specified or `return_on_find` is True, it will break early.
    If `dependencies` is specified, it will extend items of the list with the tiles required to find them. Returns
    if it was able to find the desired tile or not.'''
    if isinstance(size, int): size = (size, size)
    rows_to_solve = get_rows_to_solve(size, tiles)
    columns_to_solve = get_columns_to_solve(size, tiles)
    rows_to_solve_expensive = rows_to_solve[:]
    columns_to_solve_expensive = columns_to_solve[:]
    def init_solve_row(row_index:int) -> tuple[list[int],bool]:
        '''Initializing stuff within a for loop. Returns the index list and if it should continue or not.'''
        index_list = LU.get_row_indexes(size, row_index)
        if not LU.has_incomplete_tiles(LU.get_values(index_list, tiles)):
            return index_list, True
        return index_list, False
    def init_solve_column(column_index:int) -> tuple[list[int],bool]:
        index_list = LU.get_column_indexes(size, column_index)
        if not LU.has_incomplete_tiles(LU.get_values(index_list, tiles)):
            return index_list, True
        return index_list, False
    def finalize_solve(row_index:int, was_successful:bool, unsolved_axis:set[int], tiles_modified:list[int]) -> None:
        if was_successful: unsolved_axis.discard(row_index)
        add_tiles_to_axes_to_solve(size, tiles_modified, [rows_to_solve, rows_to_solve_expensive], [columns_to_solve, columns_to_solve_expensive], unsolved_rows, unsolved_columns)
    def got_desired_tile() -> bool:
        return was_successful and desired_tile_index is not None and len(tiles[desired_tile_index]) == 1
    
    def three_in_a_row() -> tuple[bool,None|int]:
        did_something = False
        tiles_modified:list[int] = []
        for row_index in rows_to_solve:
            index_list, should_continue = init_solve_row(row_index)
            if should_continue: continue
            was_successful, tiles_modified = solve_three_in_a_row(colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            if return_on_find and was_successful: return did_something, tiles_modified[0]
            finalize_solve(row_index, was_successful, unsolved_rows, tiles_modified)
        for column_index in columns_to_solve:
            index_list, should_continue = init_solve_column(column_index)
            if should_continue: continue
            was_successful, tiles_modified = solve_three_in_a_row(colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            if return_on_find and was_successful: return did_something, tiles_modified[0]
            finalize_solve(column_index, was_successful, unsolved_columns, tiles_modified)
        return did_something, None
    def balancing() -> tuple[bool,None|int]:
        did_something = False
        tiles_modified:list[int] = []
        for row_index in rows_to_solve:
            index_list, should_continue = init_solve_row(row_index)
            if should_continue: continue
            was_successful, tiles_modified = solve_balancing(size[0], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            if return_on_find and was_successful: return did_something, tiles_modified[0]
            finalize_solve(row_index, was_successful, unsolved_rows, tiles_modified)
        for column_index in columns_to_solve:
            index_list, should_continue = init_solve_column(column_index)
            if should_continue: continue
            was_successful, tiles_modified = solve_balancing(size[1], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            if return_on_find and was_successful: return did_something, tiles_modified[0]
            finalize_solve(column_index, was_successful, unsolved_columns, tiles_modified)
        return did_something, None
    def balancing_possibilities() -> tuple[bool,None|int]:
        did_something = False
        tiles_modified:list[int] = []
        for row_index in rows_to_solve:
            index_list, should_continue = init_solve_row(row_index)
            if should_continue: continue
            was_successful, tiles_modified = solve_balancing_possibilities(size[0], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            if return_on_find and was_successful: return did_something, tiles_modified[0]
            finalize_solve(row_index, was_successful, unsolved_rows, tiles_modified)
        for column_index in columns_to_solve:
            index_list, should_continue = init_solve_column(column_index)
            if should_continue: continue
            was_successful, tiles_modified = solve_balancing_possibilities(size[1], colors, index_list, tiles, dependencies)
            if was_successful: did_something = True
            if return_on_find and was_successful: return did_something, tiles_modified[0]
            finalize_solve(column_index, was_successful, unsolved_columns, tiles_modified)
        return did_something, None
    def rule_4() -> tuple[bool,None|int]:
        did_something = False
        tiles_modified:list[int] = []
        if size[1] // colors > 2:
            # for row_index in rows_to_solve:
            for row_index in rows_to_solve_expensive:
                index_list, should_continue = init_solve_row(row_index)
                if should_continue: continue
                was_successful, tiles_modified = solve_rule_4(size[0], colors, index_list, tiles, dependencies)
                if was_successful: did_something = True
                if return_on_find and was_successful: return did_something, tiles_modified[0]
                finalize_solve(row_index, was_successful, unsolved_rows, tiles_modified)
        if size[0] // colors > 2:
            # for column_index in columns_to_solve:
            for column_index in columns_to_solve_expensive:
                index_list, should_continue = init_solve_column(column_index)
                if should_continue: continue
                was_successful, tiles_modified = solve_rule_4(size[1], colors, index_list, tiles, dependencies)
                if was_successful: did_something = True
                if return_on_find and was_successful: return did_something, tiles_modified[0]
                finalize_solve(column_index, was_successful, unsolved_columns, tiles_modified)
        return did_something, None

    total_tries = 0
    while LU.has_incomplete_tiles(tiles):
        # LevelPrinter.print_board(tiles, size)
        if total_tries != 0 and not did_something:
            if error_on_failure:
                LU.print_board(tiles, size)
                raise RuntimeError("Failed to solve board!")
            else: return False
        total_tries += 1
        did_something = False
        
        while len(rows_to_solve) != 0 or len(columns_to_solve) != 0:
            unsolved_rows = set(rows_to_solve)
            unsolved_columns = set(columns_to_solve)

            was_successful, return_now_value = three_in_a_row()
            if return_now_value is not None: return return_now_value
            if got_desired_tile(): return True
            if was_successful: did_something = True

            was_successful, return_now_value = balancing()
            if return_now_value is not None: return return_now_value
            if got_desired_tile(): return True
            if was_successful: did_something = True

            if colors != 2:
                was_successful, return_now_value = balancing_possibilities()
                if return_now_value is not None: return return_now_value
                if got_desired_tile(): return True
                if was_successful: did_something = True
            
            add_full_rows(tiles, size, rows_to_solve, columns_to_solve, unsolved_rows, unsolved_columns)
            for unsolved_row in unsolved_rows: rows_to_solve.remove(unsolved_row)
            for unsolved_column in unsolved_columns: columns_to_solve.remove(unsolved_column)

        # expensive rules go down here.

        unsolved_rows = set(rows_to_solve_expensive)
        unsolved_columns = set(columns_to_solve_expensive)
        if hard_mode:
            was_successful, return_now_value = rule_4()
            if return_now_value is not None: return return_now_value
            if got_desired_tile(): return True
            if was_successful: did_something = True

        was_successful, tiles_modified = solve_cloning(size, tiles, dependencies)
        if return_on_find and len(tiles_modified) > 0: return tiles_modified[0]
        if was_successful: did_something = True
        if got_desired_tile(): return True
        add_tiles_to_axes_to_solve(size, tiles_modified, [rows_to_solve, rows_to_solve_expensive], [columns_to_solve, columns_to_solve_expensive], unsolved_rows, unsolved_columns)

        for unsolved_row in unsolved_rows: rows_to_solve_expensive.remove(unsolved_row)
        for unsolved_column in unsolved_columns: columns_to_solve_expensive.remove(unsolved_column)

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
    # tiles = LU.expand_board(2, [ # board from extreme setting on App "Binairio" (chaotic evil)
    #     0, 0, 0, 2, 0, 2, 0, 0, 0, 0, 2, 0,
    #     0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2,
    #     0, 0, 0, 0, 0, 0, 1, 0, 0, 2, 0, 0,
    #     0, 2, 2, 0, 2, 0, 0, 0, 1, 0, 0, 1,
    #     0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2,
    #     0, 0, 0, 1, 0, 2, 2, 0, 0, 2, 0, 0,
    #     2, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 1,
    #     0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2,
    #     0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0,
    #     1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1,
    #     0, 0, 0, 0, 2, 0, 2, 1, 0, 0, 0, 0,
    #     0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0
    # ])
    # tiles = LU.expand_board(2, [int(i) for i in # board from hard setting on App "Binairio" (chaotic evil)
    # '''
    # 001010010020
    # 100000001000
    # 002122001001
    # 010102000002
    # 200000002000
    # 000101201101
    # 000100000001
    # 000002020210
    # 220000000010
    # 000022022000
    # 002202000020
    # 210000020001
    # '''.replace("\n", "").replace("\t", "").replace(" ", "")])
    # size = (12, 12)
    # colors = 2
    # tiles = LU.expand_board(2, [int(i) for i in # board from average setting on App "Binairio" (chaotic evil)
    # '''
    # 000100022000
    # 000010010000
    # 010220000120
    # 210001010200
    # 001100001000
    # 010101000002
    # 002000120210
    # 000002000002
    # 000001101000
    # 002202000200
    # 122000000002
    # 000002001002
    # '''.replace("\n", "").replace("\t", "").replace(" ", "")])
    # size = (12, 12)
    # colors = 2
    # tiles = LU.expand_board(2, [int(i) for i in # board from easy setting on App "Binairio" (chaotic evil)
    # '''
    # 010000022002
    # 000110001000
    # 000102110020
    # 000000020011
    # 020000200000
    # 200211001001
    # 000001000201
    # 101010000100
    # 002002001020
    # 210000100000
    # 220020000110
    # 020001020010
    # '''.replace("\n", "").replace("\t", "").replace(" ", "")])
    # size = (12, 12)
    # colors = 2
    # tiles = LU.expand_board(2, [int(i) for i in # this board is chaotic evil.
    # '''
    # 021200
    # 012100
    # 012100
    # 221211
    # 121122
    # 212211
    # '''.replace("\n", "").replace("\t", "").replace(" ", "")])
    # size = (6, 6)
    # colors = 2

    LU.print_board(tiles, size)
    if not LevelValidator.is_valid(tiles, size, colors):
        print("The starting board is not valid")
    dependencies = [[] for i in range(size[0] * size[1])]
    solve(size, colors, tiles, None, dependencies, hard_mode=False)
    LU.print_board(tiles, size)
    if not LevelValidator.is_valid(tiles, size, colors):
        print("The solved board is not valid")

# TODO: replace sets with lists and see if it's faster.

# TODO: for rule 4, establish a maximum missing tile amount for it to be invalid. Also determine if an equal more than/less than is actually not do anything.
