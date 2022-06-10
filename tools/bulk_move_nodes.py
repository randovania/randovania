import argparse
import logging

from randovania.game_description import data_reader
from randovania.game_description import data_writer
from randovania.game_description import pretty_print
from randovania.game_description.editor import Editor
from randovania.game_description.requirements.base import Requirement
from randovania.games import default_data
from randovania.games.game import RandovaniaGame


def bulk_move_node_logic(args):
    game = RandovaniaGame(args.game)

    path, data = default_data.read_json_then_binary(game)
    gd = data_reader.decode_data(data)

    # Make the changes
    editor = Editor(gd)
    world = gd.world_list.world_with_name(args.world)

    source_area = world.area_by_name(args.source_area)
    target_area = world.area_by_name(args.target_area)

    node_names = args.node_names

    requirements: dict[str, dict[str, Requirement]] = {
        node_name: {
            target.name: req
            for target, req in source_area.connections[source_area.node_with_name(node_name)].items()
        }
        for node_name in node_names
    }

    for node_name in node_names:
        logging.info("Moving node %s", node_name)
        editor.move_node_from_area_to_area(
            source_area,
            target_area,
            source_area.node_with_name(node_name)
        )

    for name, connections in requirements.items():
        source_node = target_area.node_with_name(name)
        for target, req in connections.items():
            editor.edit_connections(
                target_area,
                source_node,
                target_area.node_with_name(target),
                req,
            )

    # Write it back
    logging.info("Writing database files")
    new_data = data_writer.write_game_description(gd)
    data_writer.write_as_split_files(new_data, path)

    logging.info("Writing human readable")
    path.with_suffix("").mkdir(parents=True, exist_ok=True)
    pretty_print.write_human_readable_game(gd, path.with_suffix(""))


def bulk_move_node_command():
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", required=True)
    parser.add_argument("--source-area", required=True)
    parser.add_argument("--target-area", required=True)
    parser.add_argument("node_names", nargs="+")
    return parser


def main():
    args = bulk_move_node_command().parse_args()
    bulk_move_node_logic(args)


if __name__ == '__main__':
    main()
