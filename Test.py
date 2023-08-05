import json
import os
import random
from statistics import mean, median
import time

import LevelCreator.LevelCreator as LevelCreator
import LevelCreator.LevelUtilities as LU
import LevelCreator.LevelSolver as LevelSolver

REPEAT_COUNT = {2: {4: 11815, 6: 2303, 8: 629, 10: 202, 12: 82, 14: 16, 16: 2},
                3: {3: 13971, 6: 1251, 9: 142, 12: 2}} # will take 2 minutes and 40 seconds

def copy_tiles(tiles:list[list[int]]) -> list[list[int]]:
    return [copy_tile[:] for copy_tile in tiles]
def expand_tiles(tiles:list[int], colors:int) -> list[list[int]]:
    DEFAULT = list(range(1, colors + 1))
    return [(DEFAULT[:] if tile == 0 else [tile]) for tile in tiles]
def collapse_tiles(tiles:list[list[int]], colors:int=None, strict:bool=False) -> list[int]:
    output:list[int] = []
    for tile in tiles:
        if len(tile) == 0: raise ValueError("0-length tile!")
        if len(tile) == 1: output.append(tile[0])
        elif strict and len(tile) < colors: raise ValueError("%s-length tile!" % len(tile))
        else: output.append(0)
    return output
def has_incomplete_tiles(tiles:list[list[int]]) -> bool: # TODO: check the performance of this vs `count_complete_tiles`
    for tile in tiles:
        if len(tile) != 1: return True
    else: return False

def test_a_lot() -> None:
    SIZES = [4, 6, 8, 10, 12]
    pattern_length = 2 ** (len(SIZES)) - 1
    pattern = []
    index = 0
    for index in range(len(SIZES)):
        pattern.extend(pattern)
        pattern.append(SIZES[index])
    assert len(pattern) == pattern_length

    index = 0
    while True:
        seed = random.randint(-2147483648, 2147483647)
        print(seed, pattern[index])
        full, empty, other_data = LevelCreator.generate(pattern[index], seed)
        LU.print_board(full, pattern[index])
        LU.print_board(empty, pattern[index])
        print(other_data)
        print()
        index += 1
        index = index % pattern_length

def time_test(specified_colors:list[int]|None=None) -> dict[int,dict[str,any]]:
    def raise_error(message:str) -> None:
        print("FULL:")
        LU.print_board(full, size)
        print("EMPTY:")
        LU.print_board(empty, size)
        print("SOLVED:")
        LU.print_board(solved, size)
        raise RuntimeError(message)

    SIZES = {2: [4, 6, 8, 10, 12, 14, 16], 3: [3, 6, 9, 12]}
    if specified_colors is None: specified_colors = list(SIZES.keys())
    output:dict[int,dict[str,any]] = {}
    for color in SIZES: output[color] = {}
    for colors in specified_colors:
        sizes = SIZES[colors]
        for size in sizes:
            all_times_generator:list[float] = []
            all_times_solver:list[float] = []
            all_qualities:list[int] = []
            for i in range(REPEAT_COUNT[colors][size]):
                percentage = round(i / REPEAT_COUNT[colors][size] * 100)
                print(size, ": ", percentage, "%, seed ", i, sep="")
                start_time = time.perf_counter()
                full, empty, other_data = LevelCreator.generate(size, i, colors)
                all_qualities.append(other_data["quality"])
                end_time = time.perf_counter()
                time_elapsed = end_time - start_time
                all_times_generator.append(time_elapsed)
                solved = expand_tiles(empty, colors)
                start_time = time.perf_counter()
                LevelSolver.solve(size, colors, solved, None, None, True)
                end_time = time.perf_counter()
                time_elapsed = end_time - start_time
                all_times_solver.append(time_elapsed)
                solved = collapse_tiles(solved, colors, True)
                if 0 in solved: raise_error("The solved board is incomplete!")
                elif solved != full: raise_error("The full and solved boards are different!")
            output[colors][size] = ({"mean_gen": mean(all_times_generator), "median_gen": median(all_times_generator)})
    print(output)
    return output

def time_test_rectangle(specified_colors:list[int]|None=None) -> dict[int,dict[str,any]]:
    SIZES = {2: [(6, 4), (8, 6), (10, 6), (10, 8), (12, 6), (12, 8), (12, 10), (14, 8), (14, 10), (14, 12), (16, 8), (16, 10), (16, 12), (16, 14)],
             3: [(6, 3), (9, 6), (12, 6), (12, 9)]}
    if specified_colors is None: specified_colors = list(SIZES.keys())
    output:dict[int,dict[str,any]] = {}
    for color in SIZES: output[color] = {}
    for colors in specified_colors:
        sizes = SIZES[colors]
        for width, height in sizes:
            all_times:list[int] = []
            biggest_size = max(width, height)
            times = REPEAT_COUNT[colors][biggest_size]
            for i in range(times):
                percentage = round(i / times * 100)
                print((height, width), ": ", percentage, "%, seed ", i, sep="")
                start_time = time.perf_counter()
                LevelCreator.generate((height, width), i, colors)
                end_time = time.perf_counter()
                time_elapsed = end_time - start_time
                all_times.append(time_elapsed)
            output[colors][(height, width)] = ({"mean": mean(all_times), "median": median(all_times)})
    print(output)
    return output

def get_seed_hashes(size:int=4, count:int|None=None, colors:int=0, file:str|None=None) -> None:
    '''Generates a list of "hashes", which are recorded in the file. if `colors` is 0, then it uses the default LevelCreator; otherwise, it uses the color one'''
    if file is not None and os.path.exists(file): raise FileExistsError("Cannot write to existing file!")
    color = 2 if colors == 0 else colors
    if count is None: count = REPEAT_COUNT[color][size]
    output:dict[int,int] = {}
    for seed in range(count):
        print(seed)
        full, empty, data = LevelCreator.generate(size, seed, color)
        trinary_string = "".join([str(i) for i in empty])
        result_int = int(trinary_string, color + 1)
        output[seed] = result_int
    if file is not None:
        if file is not None and os.path.exists(file): raise FileExistsError("Cannot write to existing file!")
        with open(file, "wt") as f:
            f.write(json.dumps(output, indent=2))
    print(output)

def time_distribution(size:int=12, count:int|None=None, colors:int=2, file:str|None=None, predictable:bool=False) -> None:
    if file is not None and os.path.exists(file): raise FileExistsError("Cannot write to existing file!")
    if count is None: count = REPEAT_COUNT[2][size] * 30
    output:dict[int,dict[str,any]] = {}
    all_times:list[int] = []
    for i in range(count):
        if predictable: seed = i
        else: seed = random.randint(-2147483648, 2147483647)
        start_time = time.perf_counter()
        LevelCreator.generate(size, seed, colors)
        end_time = time.perf_counter()
        time_elapsed = end_time - start_time
        all_times.append(time_elapsed)
        percentage = round(i / count * 100)
        print(size, ": ", percentage, "%" , sep="")
    if file is not None:
        if file is not None and os.path.exists(file): raise FileExistsError("Cannot write to existing file!")
        with open(file, "wt") as f:
            f.write(json.dumps(all_times, indent=2))
    output[size] = ({"mean": mean(all_times), "median": median(all_times)})
    print(output)
    return output

if __name__ == "__main__":
    # time_test_rectangle()
    time_test()
    # time_distribution(12, 8, 3)
    # get_seed_hashes(6, colors=3, file="C:/Users/ander/Downloads/0hh1_with_change_3.json")
    # test_a_lot()
    # time_distribution(12, file="C:/Users/ander/Downloads/0hh1_12_distributions.json")