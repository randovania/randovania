from randovania.game_description import data_reader
from randovania.games.game import RandovaniaGame
from randovania.games.prime import default_data

data = default_data.read_json_then_binary(RandovaniaGame.PRIME3)[1]
game = data_reader.decode_data(data)

for world in game.world_list.worlds:
    print(f"\n## {world.name}")
    for area in world.areas:
        flag = "X" if any(con for con in area.connections.values()) else " "
        name = area.name.replace('\n', '\\n')
        print(f"* [{flag}] {name}")