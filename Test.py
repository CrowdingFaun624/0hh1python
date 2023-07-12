import json
import os
import random
from statistics import mean, median
import time

import Utilities.LevelCreator as LevelCreator

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
        LevelCreator.print_board(full, pattern[index])
        LevelCreator.print_board(empty, pattern[index])
        print(other_data)
        print()
        index += 1
        index = index % pattern_length

def time_test(specified_colors:list[int]|None=None) -> dict[int,dict[str,any]]:
    SIZES = {2: [4, 6, 8, 10, 12, 14, 16], 3: [3, 6, 9, 12]}
    if specified_colors is None: specified_colors = list(SIZES.keys())
    output:dict[int,dict[str,any]] = {}
    for color in SIZES: output[color] = {}
    for colors in specified_colors:
        sizes = SIZES[colors]
        for size in sizes:
            all_times:list[int] = []
            for i in range(REPEAT_COUNT[colors][size]):
                percentage = round(i / REPEAT_COUNT[colors][size] * 100)
                print(size, ": ", percentage, "%, seed ", i, sep="")
                start_time = time.perf_counter()
                LevelCreator.generate(size, i, colors)
                end_time = time.perf_counter()
                time_elapsed = end_time - start_time
                all_times.append(time_elapsed)
            output[colors][size] = ({"mean": mean(all_times), "median": median(all_times)})
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
    # get_seed_hashes(6, colors=2, file="C:/Users/ander/Downloads/0hh1_with_change.json")
    # test_a_lot()
    # time_distribution(12, file="C:/Users/ander/Downloads/0hh1_12_distributions.json")