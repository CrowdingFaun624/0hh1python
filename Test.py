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

def time_test(specified_colors:list[int]|None=None, usable_rules:list[bool]|None=None) -> dict[int,dict[str,any]]:
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
            all_total_clears:list[int] = []
            for i in range(REPEAT_COUNT[colors][size]):
                percentage = round(i / REPEAT_COUNT[colors][size] * 100)
                print(size, ": ", percentage, "%, seed ", i, sep="")
                start_time = time.perf_counter()
                gen_info = LU.GenerationInfo()
                full, empty, other_data = LevelCreator.generate(size, i, colors, usable_rules, gen_info=gen_info)
                all_qualities.append(other_data["quality"])
                all_total_clears.append(gen_info.total_clears)
                end_time = time.perf_counter()
                time_elapsed = end_time - start_time
                all_times_generator.append(time_elapsed)
                solved = LU.expand_board(colors, empty)
                start_time = time.perf_counter()
                try:
                    LevelSolver.solve(size, colors, solved, None, None, True, usable_rules=usable_rules)
                except RuntimeError:
                    raise_error("Failed to solve board!")
                end_time = time.perf_counter()
                time_elapsed = end_time - start_time
                all_times_solver.append(time_elapsed)
                solved = LU.collapse_board(solved, colors, True)
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

def get_seed_hashes(size:int=4, count:int|None=None, colors:int=0, usable_rules:list[bool]|None=None, file:str|None=None) -> None:
    '''Generates a list of "hashes", which are recorded in the file. if `colors` is 0, then it uses the default LevelCreator; otherwise, it uses the color one'''
    if file is not None and os.path.exists(file): raise FileExistsError("Cannot write to existing file!")
    color = 2 if colors == 0 else colors
    if count is None: count = REPEAT_COUNT[color][size]
    output:dict[int,int] = {}
    for seed in range(count):
        print(seed)
        full, empty, data = LevelCreator.generate(size, seed, color, usable_rules)
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

def test_level_solver() -> None:
    rule_4_tests:dict[int,list[tuple[str,str]]] = {2:
        [
            ("02121212121200122102", "12121212121200122112"),
            ("01221212210012210212", "11221212210012211212"),
            ("11210211212100201221", "11212211212121221221"),
            ("21212112001021121001", "21212112001221121221"),
            ("20000121021122122122", "21121121121122122122"),
            ("12212122102010212102", "12212122112010212112"),
            ("21120122122112212100", "21121122122112212100"),
            ("02012210210212112212", "02012210210212112212"), # same
            ("11221212210020021221", "11221212210021121221"),
            ("01212120012212121221", "11212120012212121221"),
            ("01221212210001021212", "11221212210001021212"),
            ("00012211212112211200", "00012211212112211200"), # same
            ("12100121120100012121", "12122121122100012121"),
            ("21212120102121122120", "21212120102121122121"),
            ("22121210001212211212", "22121211211212211212"),
            ("01212121212100212210", "01212121212100212210"), # same
            ("21212121212100211210", "21212121212100211212"),
            ("11212121221002120121", "11212121221002122121"),
            ("21211212212100021121", "21211212212120021121"),
            ("22112122112010211201", "22112122112010211201"), # same
            ("22121212102001211212", "22121212112001211212"),
            ("00212122100212212121", "11212122100212212121"),
            ("21121021120100212112", "21121221122100212112"),
            ("22112121120000121121", "22112121122122121121"),
            ("12112012210001212121", "12112212210001212121")
        ]
    }
    for color, tests in rule_4_tests.items():
        for index, test in enumerate(tests):
            tiles = LU.expand_board(color, [int(i) for i in test[0]])
            start = LU.copy_tiles(tiles)
            required_output = LU.expand_board(color, [int(i) for i in test[1]])
            dependencies:list[list[int]] = [[] for i in range(len(tiles))]
            LevelSolver.solve_rule_4(len(tiles), color, list(range(len(tiles))), tiles, dependencies)
            LevelSolver.solve_three_in_a_row(color, list(range(len(tiles))), tiles, dependencies)
            LevelSolver.solve_balancing(len(tiles), color, list(range(len(tiles))), tiles, dependencies)
            if tiles != required_output:
                print("Start:")
                LU.print_board(start, (len(tiles), 1))
                print("Required finish:")
                LU.print_board(required_output, (len(tiles), 1))
                print("Actual finish:")
                LU.print_board(tiles, (len(tiles), 1))
                raise RuntimeError("Failed to solve rule 4 test index %i (%i colors)!" % (index, color))

if __name__ == "__main__":
    # time_test_rectangle()
    time_test()
    # time_distribution(12, 8, 3)
    # get_seed_hashes(6, colors=2, None, file="C:/Users/ander/Downloads/0hh1_6_2_without_change.json")
    # test_a_lot()
    # time_distribution(12, file="C:/Users/ander/Downloads/0hh1_12_distributions.json")
    # test_level_solver()
