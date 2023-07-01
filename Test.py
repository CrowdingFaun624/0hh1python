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
        time.sleep(0.25)

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

if __name__ == "__main__":
    time_test()
