import time

import Utilities.LevelCreator as LevelCreator

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
