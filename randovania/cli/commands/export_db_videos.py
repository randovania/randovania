from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

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

# ruff: noqa: E731

# (tab title, page title, time)
HTML_HEADER_FORMAT = """
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>%s</title>
        <style type="text/css">
            body {
                font-family: 'Helvetica Neue', sans-serif;
                background-color: #f5f5f5;
                color: #333;
                margin: 30px auto;
                max-width: 1000px;
                line-height: 1.6;
                font-size: 19px;
                padding: 0 10px;
            }
            h2 {
                font-size: 46px;
                margin-top: 100px;
                margin-bottom: 0px;
            }
            h3 {
                margin-top: 46px;
                margin-bottom: 0;
            }
            .header {
                background-color: #3498db;
                color: #fff;
            }
            a {
                text-decoration: none;
                color: #3498db;
            }
            p {
                margin-top: 10px;
                margin-bottom: 4px;
            }
            #toc_container {
                background: #f9f9f9 none repeat scroll 0 0;
                border: 1px solid #aaa;
                display: table;
                font-size: 95%%;
                margin-bottom: 1em;
                padding: 36px;
                width: 600px;
            }
            #toc_container li, #toc_container ul, #toc_container ul li {
                list-style: outside none none !important;
            }
            #toc_container ul {
                margin-bottom: 40px;
            }
            ul, ol {
                list-style-type: none;
                padding: 0;
                margin: 0;
            }
            ul {
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <h1>%s</h1>
        <p><i>File generated on %s by <a href="https://github.com/randovania/randovania">Randovania</a></i></p>
"""

HTML_AREA_FORMAT = """
        <h2 id="%s">%s</h2>\n
"""

HTML_CONNECTION_FORMAT = """
        <h3 id="%s">%s</h3>\n
"""

HTML_VIDEO_FORMAT = """
<p><i> {} </i></p>
<iframe
width="728"
height="410"
src="https://www.youtube.com/embed/{}?start={}&autoplay=1"
srcdoc="<style>*{{padding:0;margin:0;overflow:hidden}}html,body{{height:100%}}
img,span{{position:absolute;width:100%;top:0;bottom:0;margin:auto}}
span{{height:1.5em;text-align:center;font:48px/1.5 sans-serif;color:white;text-shadow:0 0 0.5em black}}
</style><a href=https://www.youtube.com/embed/{}?start={}&autoplay=1>
<img src=https://img.youtube.com/vi/{}/hqdefault.jpg alt='vid'><span>▶️</span></a>"
frameborder="0"
allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
allowfullscreen
title="vid"
></iframe>
"""

HTML_FOOTER = """
    </body>
</html>
"""


def get_date():
    return str(datetime.datetime.now()).split(".")[0].split(" ")[0]


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

    TOC_AREA_FORMAT = """
            <li><strong>%s</strong>
                <ul>
                    %s
                </ul>
            </li>
    """

    TOC_CONNECTION_FORMAT = """
                <li><a href="#%s">%s</a></li>\n
    """

    for area in sorted(areas.keys()):
        area_body = HTML_AREA_FORMAT % (area, area)
        nodes = areas[area]
        toc_connections = ""
        for node in sorted(nodes):
            connections = nodes[node]
            for connection in sorted(connections):
                connection_name = f"{node} -> {connection}"

                connection_body = HTML_CONNECTION_FORMAT % (connection_name, connection_name)
                yt_ids = connections[connection]

                any = False

                for id, start_time, highest_diff in sorted(yt_ids, key=lambda x: x[2]):
                    if "%s?start=%d" % (id, start_time) in area_body:
                        # video already used for another connection in this room
                        continue

                    any = True

                    difficulty = LayoutTrickLevel.from_number(highest_diff).long_name

                    connection_body += HTML_VIDEO_FORMAT.format(
                        difficulty,
                        id,
                        start_time,
                        id,
                        start_time,
                        id,
                    )

                if not any:
                    # no videos for this connection after filtering out duplicates
                    continue

                area_body += connection_body

                toc_connections += TOC_CONNECTION_FORMAT % (connection_name, connection_name)
        toc += TOC_AREA_FORMAT % (area, toc_connections)
        body += area_body

    toc += """
        </ul>
    </div>
    """

    header = HTML_HEADER_FORMAT % (name, name, get_date())

    html = header + toc + body + HTML_FOOTER

    from htmlmin import minify

    return minify(html, remove_comments=True, remove_all_empty_space=True)


def filename_friendly_game_name(game: RandovaniaGame):
    return "".join(x for x in game.long_name if x.isalnum() or x in [" "])


def export_as_yaml(game: RandovaniaGame, out_dir: Path, as_frontmatter: bool):
    def add_entry(arr: list, key: str, value: Any):
        arr.append({"key": key, "value": value})

    regions = collect_game_info(game)

    output = []
    for region, areas in sorted(regions.items()):
        sorted_region = []
        add_entry(output, region, sorted_region)
        for area, nodes in sorted(areas.items()):
            sorted_area = []
            add_entry(sorted_region, area, sorted_area)
            all_area_vids = set()
            for node, connections in sorted(nodes.items()):
                sorted_node = []

                for connection, videos in sorted(connections.items()):
                    sorted_vids = []

                    for video in sorted(videos, key=lambda x: x[2]):
                        if video in all_area_vids:
                            continue
                        all_area_vids.add(video)

                        yt_id, start_time, highest_diff = video
                        sorted_vids.append(
                            {
                                "video_id": yt_id,
                                "start_time": start_time,
                                "difficulty": LayoutTrickLevel.from_number(highest_diff).long_name,
                            }
                        )

                    if sorted_vids:
                        add_entry(sorted_node, connection, sorted_vids)

                if sorted_node:
                    add_entry(sorted_area, node, sorted_node)

    output = {"regions": output}

    tr = lambda s: s
    fmt = "yml"
    if as_frontmatter:
        tr = lambda s: f"---\n{s}---\n"
        fmt = "md"

    from ruamel.yaml import YAML

    yaml = YAML(typ="safe")
    with out_dir.joinpath(f"{game.value}.{fmt}").open("w") as out_file:
        yaml.dump(output, out_file, transform=tr)


def export_videos(game: RandovaniaGame, out_dir: Path):
    regions = collect_game_info(game)
    if not regions:
        return  # no youtube videos in this game's database

    out_dir_game = out_dir.joinpath(filename_friendly_game_name(game))
    out_dir_game.mkdir(exist_ok=True, parents=True)

    for region_name, area in regions.items():
        html = generate_region_html(region_name, area)
        out_dir_game.joinpath(region_name + ".html").write_text(html, encoding="utf-8")

    full_name = game.long_name
    html = HTML_HEADER_FORMAT % ("Index - " + full_name, full_name, get_date())

    toc = """
    <div>
        <ul>
    """

    toc_region_format = """
        <li><a href="%s">%s</a>\n
    """

    for region_name in sorted(regions):
        toc += toc_region_format % (region_name + ".html", region_name)

    toc += """
        </ul>
    </div>
    """

    html += toc
    html += HTML_FOOTER
    out_dir_game.joinpath("index.html").write_text(html)
