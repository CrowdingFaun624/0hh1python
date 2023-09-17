try:
    import LevelCreator.LevelSolver as LevelSolver
    import LevelCreator.LevelUtilities as LU
    import LevelCreator.LevelValidator as LevelValidator
except ImportError:
    import LevelSolver
    import LevelUtilities as LU
    import LevelValidator

def get_incrementing_tile_number(maximum_digits:list[int]) -> list[list[int]]:
    '''Generates a list of integers increasing from 0 in all to maximum in all, such that each digit is always less than its given maximum.'''
    number = [0] * len(maximum_digits)
    total_length = 1
    for digit in maximum_digits: total_length *= digit
    for i in range(total_length):
        yield number
        index = len(number) - 1
        number[index] += 1
        while True:
            if number[index] >= maximum_digits[index]:
                index -= 1
                number[index] += 1
                for zeroing_index in range(index + 1, len(maximum_digits)):
                    number[zeroing_index] = 0
            else: break
            if index < 0: break

def get_all_boards(size:tuple[int,int], colors:int, tiles:list[list[int]]) -> list[list[list[int]]]:
    '''Generates all boards whose tiles are within the possibility of the tiles given.'''
    empty_indexes = [index for index in range(size[0] * size[1]) if len(tiles[index]) > 1]
    tile_lengths = [len(tile) for tile in tiles]
    empty_tile_lengths = [tile_lengths[index] for index in empty_indexes]
    print(len(empty_tile_lengths))
    for new_tile_values in get_incrementing_tile_number(empty_tile_lengths):
        new_tiles = LU.copy_tiles(tiles)
        for tile_index, color_index in zip(empty_indexes, new_tile_values):
            # `color_index` describes the index within the tile's possible values to set the tile to.
            new_tiles[tile_index] = [tiles[tile_index][color_index]]
        yield new_tiles

def solve(size:tuple[int,int], colors:int, tiles:list[list[int]]) -> list[list[int]]:
    '''Returns a list of possible complete boards that match the given incomplete board.'''
    if [] in tiles: return []
    start_tiles = LU.copy_tiles(tiles)
    LevelSolver.solve(size, colors, start_tiles)
    get_all_boards(size, colors, start_tiles)
    yes_boards:list[list[int]] = []
    for new_board in get_all_boards(size, colors, start_tiles):
        assert all(len(tile) == 1 for tile in new_board)
        if LevelValidator.is_valid(new_board, size, colors):
            yes_boards.append(LU.collapse_board(new_board, colors, True))
    return yes_boards

if __name__ == "__main__":
    empty_tiles = {
        (12, 2): LU.board_from_string('''
        010000021002
        010120000002
        002000000000
        020000022002
        000000000100
        201000200000
        000000110000
        100020000000
        000201000202
        000000200010
        220000200200
        000220000000'''),
        (6, 2): LU.board_from_string('''
            020000
            000202
            100000
            100102
            000020
            100000
            '''),}
    full_tiles = {
        (12, 2): LU.board_from_string('''
        211212121212
        212121212112
        122112211221
        121212122112
        212121122121
        211212211221
        122112112212
        122121221121
        211221121212
        112212212112
        221121211221
        121221122121'''),
        (6, 2): LU.board_from_string('''
            221121
            211212
            122121
            122112
            211221
            112212'''),}
    trick_tiles = { # has one extra tile removed
        (12, 2): LU.board_from_string('''
        010000021002
        010120000002
        002000000000
        020000022002
        000000000100
        201000000000
        000000110000
        100020000000
        000201000202
        000000200010
        220000200200
        000220000000'''), # row 6
        (6, 2): LU.board_from_string('''
            020000
            000202
            100000
            100002
            000020
            100000'''), # row 4
    }
    size = 6
    colors = 2

    tuple_size = (size, size)
    for board in solve(tuple_size, colors, trick_tiles[(size, colors)]): LU.print_board(board, size) 
