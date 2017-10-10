from randovania.cli import echoes

games = [echoes]


def create_subparsers(root_parser):
    for game in games:
        game.create_subparsers(root_parser)
