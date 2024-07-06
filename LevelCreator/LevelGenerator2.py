import random

try:
    import LevelCreator.LevelSolver as LevelSolver
    import LevelCreator.LevelUtilities as LU
    import LevelCreator.LevelValidator as LevelValidator
except ImportError:
    import LevelSolver
    import LevelUtilities as LU
    import LevelValidator

def generate_solution(size:tuple[int,int], seed:int=None, colors:int=2) -> list[int]:
    # wave collapse algorithm
    random_range = list(range(size[0] * size[1]))
    random.shuffle(random_range)
    DEFAULT = list(range(1, colors + 1))
    tiles = [DEFAULT[:] for i in random_range]
    tiles_tries = [DEFAULT[:] for i in random_range] # pops from here each time a tile is collapsed
    for tiles_try in tiles_tries: random.shuffle(tiles_try)
    tiles_tries_originals = [tile_try[:] for tile_try in tiles_tries] # for restoration upon backtracking
    dependencies = [[] for i in random_range] # TODO: instead of dependencies, store a copy of the tiles at each tile.
    collapsed_tiles:list[tuple[int,int]] = [] # stack containing tile indexes that were collapsed and their position in random_range
    index = 0
    while index < len(random_range):
        tile_index = random_range[index]
        # tile_index = index # TODO: measure performance impact of this instead of line above.
        if len(tiles[tile_index]) == 1: index += 1; continue
        collapsed_tiles.append((tile_index, index))
        success = False
        while not success:
            if len(tiles_tries[index]) == 0: break
            for pick_value in tiles_tries[index]:
                if pick_value in tiles[tile_index]: break
            else: assert False
            tiles_tries[index].remove(pick_value)
            tiles[tile_index] = [pick_value]
            # print("Before %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            LevelSolver.solve(size, colors, tiles, None, dependencies) # TODO: make the starting rows_to_solve and columns_to_solve be only the ones with the set tile.
            # print("After: %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            if LevelValidator.is_valid(tiles, size, colors):
                index += 1
                # print("+%i" % index)
                success = True
                break
            else:
                LU.strip_dependencies(dependencies, tile_index, tiles, colors)
                continue
        if not success:
            # print("Before strip: %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            # print(collapsed_tiles)
            collapsed_tiles.pop() # current tile; can be discarded
            backtrack_amount = 1 # int(len(collapsed_tiles) * 0.5)
            for i in range(backtrack_amount):
                tiles_tries[index] = tiles_tries_originals[index][:]
                tile_index, index = collapsed_tiles.pop()
                LU.strip_dependencies(dependencies, tile_index, tiles, colors) # TODO: consider different amounts of backtracking, such as halfway, two, four, etc.
            # print("After strip: %i (%i):" % (tile_index, index))
            # LevelPrinter.print_board(tiles, size)
            # print(collapsed_tiles)
    if not LevelValidator.is_valid(tiles, size, colors):
        LU.print_board(tiles, size)
        raise RuntimeError("An invalid board was generated!")
    tiles = LU.collapse_board(tiles, colors, True)
    if 0 in tiles:
        LU.print_board(tiles, size)
        raise RuntimeError("The board has empty tiles!")
    return tiles