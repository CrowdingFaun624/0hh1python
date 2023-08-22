import LevelCreator.LevelSolver as LevelSolver
import LevelCreator.LevelUtilities as LU

WRONG = "WRONG"
HINT = "HINT"

class Hint():
    def __init__(self, type:str, tiles_affected:list[int], target_tile:int|None, is_incorrect:bool) -> None:
        self.type = type
        self.tiles_affected = tiles_affected
        self.target_tile = target_tile
        self.is_incorrect_hint = is_incorrect

def get_hint(size:tuple[int,int], colors:int, empty_board:list[list[int]|int], full_board:list[list[int]|int]) -> Hint:
    if isinstance(empty_board[0], int): empty_board:list[list[int]] = LU.expand_board(colors, empty_board)
    if isinstance(full_board[0], int): full_board:list[list[int]] = LU.expand_board(colors, full_board)
    if LU.boards_match(empty_board, full_board):
        dependencies = [[][:] for i in range(size[0] * size[1])]
        solved_board = LU.copy_tiles(empty_board)
        solver_result = LevelSolver.solve(size, colors, solved_board, None, dependencies, True, True)
        if solver_result is False:
            print("Full:"); LU.print_board(full_board, size)
            print("Empty:"); LU.print_board(empty_board, size)
            raise RuntimeError("Failed to find hint for board!")
        assert isinstance(solver_result, int)
        return Hint(HINT, dependencies[solver_result], solver_result, False)
    else:
        return Hint(WRONG, LU.get_not_matching_tiles(empty_board, full_board), None, True)
