import datetime
import os

from randovania.games import default_data
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
    
            body{margin:30px auto;max-width:1000px;line-height:1.6;font-size:19px;padding:0 10px}h1,h2,h3{line-height:1.2}

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
        <iframe width="560" height="420" src="https://www.youtube.com/embed/%s?start=%d" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n
'''

HTML_FOOTER = '''
	</body>
</html>
'''


def get_date():
    return str(datetime.datetime.now()).split('.')[0].split(" ")[0]


def get_yt_ids(item, ids):
    if item["type"] != "and" and item["type"] != "or":
        return

    data = item["data"]
    if data["comment"] is not None:
        comment = data["comment"]
        if "youtu" in comment:
            video_id = comment.split("/")[-1].split("watch?v=")[-1].split(" ")[0]
            start_time = 0
            if "?t=" in comment:
                start_time = int(video_id.split("?t=")[-1])
            video_id = video_id.split("?t=")[0]
            ids.append((video_id, start_time))

    for i in data["items"]:
        get_yt_ids(i, ids)


def collect_game_info(game: RandovaniaGame):
    data = default_data.read_json_then_binary(game)[1]
    worlds = dict()
    for world in data["worlds"]:
        areas = dict()
        for area_name in world["areas"]:
            area = world["areas"][area_name]
            nodes = dict()
            for node_name in area["nodes"]:
                node = area["nodes"][node_name]
                connections = dict()
                for connection_name in node["connections"]:
                    connection = node["connections"][connection_name]
                    yt_ids = list()
                    get_yt_ids(connection, yt_ids)
                    if len(yt_ids) > 0:
                        connections[connection_name] = yt_ids
                if len(connections) > 0:
                    nodes[node_name] = connections
            if len(nodes) > 0:
                areas[area_name] = nodes
        if len(areas) > 0:
            worlds[world["name"]] = areas
    return worlds


def generate_world_html(name, areas):
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

    for area in sorted(areas):
        body += HTML_AREA_FORMAT % (area, area)
        nodes = areas[area]
        toc_connections = ""
        for node in sorted(nodes):
            connections = nodes[node]
            for connection in sorted(connections):
                connection_name = "%s -> %s" % (node, connection)
                body += HTML_CONNECTION_FORMAT % (connection_name, connection_name)
                yt_ids = connections[connection]
                for (id, start_time) in yt_ids:
                    body += HTML_VIDEO_FORMAT % (id, start_time)
                toc_connections += TOC_CONNECTION_FORMAT % (connection_name, connection_name)
        toc += TOC_AREA_FORMAT % (area, toc_connections)

    toc += """
        </ul>
    </div>
    """

    header = HTML_HEADER_FORMAT % (name, name, get_date())

    return header + toc + body + HTML_FOOTER


def export_videos(game: RandovaniaGame, out_dir):
    worlds = collect_game_info(game)
    if len(worlds) == 0:
        return  # no youtube videos in this game's database

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_dir_game = os.path.join(out_dir, game.long_name)
    if not os.path.exists(out_dir_game):
        os.makedirs(out_dir_game)

    for world in worlds:
        html = generate_world_html(world, worlds[world])
        file = open(os.path.join(out_dir_game, world + ".html"), "w")
        file.write(html)
        file.close()

    full_name = game.long_name
    header = HTML_HEADER_FORMAT % (full_name, full_name, get_date())
    html = HTML_HEADER_FORMAT % ("Index - " + full_name, full_name, get_date())

    toc = """
    <div>
        <ul>
    """

    TOC_WORLD_FORMAT = '''
        <li><a href="%s">%s</a>\n
    '''

    for world in sorted(worlds):
        toc += TOC_WORLD_FORMAT % (world + ".html", world)

    toc += """
        </ul>
    </div>
    """

    html += toc

    html += HTML_FOOTER

    file = open(os.path.join(out_dir_game, "index.html"), "w")
    file.write(html)
    file.close()
