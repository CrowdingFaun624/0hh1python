def get_row_indexes(size:tuple[int,int], y_position:int) -> list[int]:
    '''Returns a list of indexes in the row.'''
    return list(range(y_position * size[0], (y_position + 1) * size[0]))
def get_column_indexes(size:tuple[int,int], x_position:int) -> list[int]:
    '''Returns a list of indexes in the column.'''
    return list(range(x_position, size[0] * size[1], size[0]))
def get_values(indexes:list[int], tiles:list[list[int]]) -> list[list[int]]:
    '''Gets the values of a list of indexes.'''
    return [tiles[index] for index in indexes]

def is_valid(tiles:list[list[int]], size:tuple[int,int], colors:int) -> bool:
    '''Returns if the given tiles is valid or not.'''
    max_per_row = size[0] // colors
    max_per_column = size[1] // colors
    if [] in tiles: return False
    already_rows:list[list[int]] = []
    already_columns:list[list[int]] = []
    for row_index in range(size[1]):
        row_indexes = get_row_indexes(size, row_index)
        row_values = get_values(row_indexes, tiles)
        previous_tile2 = None; previous_tile1 = None
        full_counts = [0] * colors
        empty_counts = [0] * colors
        is_full_row = True
        for tile in row_values:
            if previous_tile2 is not None and tile == previous_tile1 and tile == previous_tile2 and len(tile) == 1: return False
            if len(tile) == 1: full_counts[tile[0] - 1] += 1
            else: is_full_row = False
            for color in tile: empty_counts[color - 1] += 1
            previous_tile2 = previous_tile1
            previous_tile1 = tile
        if is_full_row and row_values in already_rows: return False
        if is_full_row: already_rows.append(row_values)
        for color_index in range(colors):
            if full_counts[color_index] > max_per_row: return False
            if empty_counts[color_index] < max_per_row: return False
    for column_index in range(size[0]):
        column_indexes = get_column_indexes(size, column_index)
        column_values = get_values(column_indexes, tiles)
        previous_tile2 = None; previous_tile1 = None
        full_counts = [0] * colors
        empty_counts = [0] * colors
        is_full_column = True
        for tile in column_values:
            if previous_tile2 is not None and tile == previous_tile1 and tile == previous_tile2 and len(tile) == 1: return False
            if len(tile) == 1: full_counts[tile[0] - 1] += 1
            else: is_full_column = False
            for color in tile: empty_counts[color - 1] += 1
            previous_tile2 = previous_tile1
            previous_tile1 = tile
        if is_full_column and column_values in already_columns: return False
        if is_full_column: already_columns.append(column_values)
        for color_index in range(colors):
            if full_counts[color_index] > max_per_column: return False
            if empty_counts[color_index] < max_per_column: return False
    return True