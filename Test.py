import json
import os
from statistics import mean, median
import time

import Utilities.LevelCreator as LevelCreator

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
        full, empty, other_data = LevelCreator.generate(pattern[index])
        LevelCreator.print_board(full)
        LevelCreator.print_board(empty)
        print(other_data)
        print()
        index += 1
        index = index % pattern_length

def time_test() -> dict[int,dict[str,any]]:
    SIZES = [4, 6, 8, 10, 12, 14, 16]
    REPEAT_COUNT = {4: 6487, 6: 869, 8: 183, 10: 52, 12: 18, 14: 8, 16: 2} # will take 2 minutes and 20 seconds
    output:dict[int,dict[str,any]] = {}
    for size in SIZES:
        all_times:list[int] = []
        for i in range(REPEAT_COUNT[size]):
            start_time = time.time()
            LevelCreator.generate(size, i)
            end_time = time.time()
            time_elapsed = end_time - start_time
            all_times.append(time_elapsed)
            percentage = round(i / REPEAT_COUNT[size] * 100)
            print(size, ": ", percentage, "%" , sep="")
        output[size] = ({"mean": mean(all_times), "median": median(all_times)})
    print(output)
    return output

def get_seed_hashes(size:int=4, count:int|None=None, file:str|None=None) -> None:
    if file is not None and os.path.exists(file): raise FileExistsError("Cannot write to existing file!")
    REPEAT_COUNT = {4: 6487, 6: 869, 8: 183, 10: 52, 12: 18, 14: 8, 16: 2} # will take 2 minutes and 20 seconds
    if count is None: count = REPEAT_COUNT[size]
    output:dict[int,int] = {}
    for seed in range(count):
        full, empty, data = LevelCreator.generate(size, seed)
        trinary_string = "".join([str(i) for i in empty])
        result_int = int(trinary_string, 3)
        output[seed] = result_int
    if file is not None:
        if file is not None and os.path.exists(file): raise FileExistsError("Cannot write to existing file!")
        with open(file, "wt") as f:
            f.write(json.dumps(output, indent=2))
    print(output)

if __name__ == "__main__":
    get_seed_hashes(file="C:/Users/ander/Downloads/0hh1_dump_with_positions.json")
