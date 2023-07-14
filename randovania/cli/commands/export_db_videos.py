from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from randovania.game_description import default_database
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.base.trick_level import LayoutTrickLevel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from randovania.game_description.requirements.base import Requirement
    from randovania.games.game import RandovaniaGame

# (tab title, page title, time)
HTML_HEADER_FORMAT = '''
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>%s</title>
        <style type="text/css">

            body{
                margin:30px auto;max-width:1000px;line-height:1.6;font-size:19px;padding:0 10px
            }
            h1,h2,h3{line-height:1.2}

            #toc_container {
                background: #f9f9f9 none repeat scroll 0 0;
                border: 1px solid #aaa;
                display: table;
                font-size: 95%%;
                margin-bottom: 1em;
                padding: 20px;
                width: auto;
            }

            .toc_title {
                font-weight: 700;
                text-align: center;
            }

            #toc_container li, #toc_container ul, #toc_container ul li{
                list-style: outside none none !important;
            }
        </style>
    </head>
    <body>
        <h1>%s</h1>
        <p><i>File generated on %s by <a href="https://github.com/randovania/randovania">Randovania</a></i></p>
'''

HTML_AREA_FORMAT = '''
        <strong><h2 id="%s">%s</h2></strong>\n
'''

HTML_CONNECTION_FORMAT = '''
        <h4 id="%s">%s</h4>\n
'''

HTML_VIDEO_FORMAT = '''
        <p><i>%s</i></p>
        <iframe width="560" height="420" src="https://www.youtube.com/embed/%s?start=%d" title="YouTube video player"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope;
            picture-in-picture" allowfullscreen></iframe>\n
'''

HTML_FOOTER = '''
    </body>
</html>
'''


def get_date():
    return str(datetime.datetime.now()).split('.')[0].split(" ")[0]


def get_difficulty(req: Requirement) -> int | None:
    # if, trick, return max(this_diff, curr_diff)
    if isinstance(req, ResourceRequirement) and req.resource.resource_type == ResourceType.TRICK:
        return req.amount

    # return the highest diff of all "and" paths
    if isinstance(req, RequirementAnd):
        max_diff = 0
        for element in req.items:
            if (diff := get_difficulty(element)) is not None and diff > max_diff:
                max_diff = diff

        return max_diff

    # return the lowest diff of all "or" paths
    elif isinstance(req, RequirementOr):
        min_diff = None
        for element in req.items:
            if (diff := get_difficulty(element)) is not None and (min_diff is None or diff < min_diff):
                min_diff = diff

        return min_diff

    return None


def get_yt_ids(req: Requirement, highest_diff: int) -> Iterable[tuple[str, int, int]]:
    if not isinstance(req, RequirementArrayBase):
        return

    if (diff := get_difficulty(req)) is not None and diff > highest_diff:
        highest_diff = diff

    if req.comment is not None:
        if "youtu" in req.comment:
            for word in req.comment.split(" "):
                if "youtu" not in word:
                    continue

                # Parse Video ID
                video_id = word.split("/")[-1].split("watch?v=")[-1].split(" ")[0]
                start_time = 0
                if "?t=" in word:
                    start_time = int(video_id.split("?t=")[-1])
                video_id = video_id.split("?t=")[0]

                yield video_id, start_time, highest_diff

    for i in req.items:
        yield from get_yt_ids(i, highest_diff)


def collect_game_info(game: RandovaniaGame) -> dict[str, dict[str, dict[str, dict[str, list[tuple[str, int, int]]]]]]:
    db = default_database.game_description_for(game)

    regions = {}
    for region in db.region_list.regions:
        areas = {}
        for area in region.areas:
            nodes = {}
            for node in area.nodes:
                connections = {}

                for target, requirement in area.connections.get(node, {}).items():
                    yt_ids = list(get_yt_ids(requirement, 0))
                    if yt_ids:
                        connections[target.name] = yt_ids

                if connections:
                    nodes[node.name] = connections

            if nodes:
                areas[area.name] = nodes

        if areas:
            regions[region.name] = areas

    return regions


def generate_region_html(name: str, areas: dict[str, dict[str, dict[str, list[tuple[str, int, int]]]]]) -> str:
    body = ""
    toc = """
    <div id="toc_container">
        <ul class="toc_list">
    """

    TOC_AREA_FORMAT = '''
            <li><strong><a>%s</a></strong>
                <ul>
                    %s
                </ul>
            </li>
    '''

    TOC_CONNECTION_FORMAT = '''
                <li><a href="#%s">%s</a></li>\n
    '''

    for area in sorted(areas.keys()):
        area_body = HTML_AREA_FORMAT % (area, area)
        nodes = areas[area]
        toc_connections = ""
        for node in sorted(nodes):
            connections = nodes[node]
            for connection in sorted(connections):
                connection_name = f"{node} -> {connection}"
                area_body += HTML_CONNECTION_FORMAT % (connection_name, connection_name)
                yt_ids = connections[connection]
                for (id, start_time, highest_diff) in sorted(yt_ids, key=lambda x: x[2]):
                    if "https://www.youtube.com/embed/%s?start=%d" % (id, start_time) in area_body:
                        continue
                    area_body += HTML_VIDEO_FORMAT % (
                        LayoutTrickLevel.from_number(highest_diff).long_name, id, start_time)
                toc_connections += TOC_CONNECTION_FORMAT % (connection_name, connection_name)
        toc += TOC_AREA_FORMAT % (area, toc_connections)
        body += area_body

    toc += """
        </ul>
    </div>
    """

    header = HTML_HEADER_FORMAT % (name, name, get_date())

    return header + toc + body + HTML_FOOTER


def filename_friendly_game_name(game: RandovaniaGame):
    return "".join(
        x for x in game.long_name
        if x.isalnum() or x in [" "]
    )


def export_videos(game: RandovaniaGame, out_dir: Path):
    regions = collect_game_info(game)
    if not regions:
        return  # no youtube videos in this game's database

    out_dir_game = out_dir.joinpath(filename_friendly_game_name(game))
    out_dir_game.mkdir(exist_ok=True, parents=True)

    for region_name, area in regions.items():
        html = generate_region_html(region_name, area)
        out_dir_game.joinpath(region_name + ".html").write_text(html)

    full_name = game.long_name
    html = HTML_HEADER_FORMAT % ("Index - " + full_name, full_name, get_date())

    toc = """
    <div>
        <ul>
    """

    toc_region_format = '''
        <li><a href="%s">%s</a>\n
    '''

    for region_name in sorted(regions):
        toc += toc_region_format % (region_name + ".html", region_name)

    toc += """
        </ul>
    </div>
    """

    html += toc
    html += HTML_FOOTER
    out_dir_game.joinpath("index.html").write_text(html)
