def collapse_board(tiles:list[list[int]], colors:int=None, strict:bool=False) -> list[int]:
    output:list[int] = []
    for tile_index, tile in enumerate(tiles):
        if strict and len(tile) == 0: raise ValueError("0-length tile at %s!" % tile_index)
        if len(tile) == 1: output.append(tile[0])
        elif strict and len(tile) < colors: raise ValueError("%s-length tile at %s!" % (len(tile), tile_index))
        else: output.append(0)
    return output

def print_board(tiles:list[int]|list[list[int]]|str, size:tuple[int,int]|int) -> None:
    if isinstance(size, int): width = size
    else: width, height = size
    if isinstance(tiles[0], list): tiles = collapse_board(tiles, strict=False)
    emojis = {0: "⬛", 1: "🟥", 2: "🟦", 3: "🟨", 4: "🟩", 5: "🟪", 6: "🟧", 7: "🟫", 8: "⬜"}
    output = ""
    for index, tile in enumerate(tiles):
        output += emojis[int(tile)]
        if index % width == width - 1: output += "\n"
    print(output)
