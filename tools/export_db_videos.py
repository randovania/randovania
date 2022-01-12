# USAGE
# - No arguments to export all games to ./exported_db_videos
# - Single argument to export 1 game to ./exported_db_videos/{game}

import os
import sys
import json
import datetime

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
        <p>Date Generated: %s</p>
'''

HTML_AREA_FORMAT = '''
        <strong><h2 id="%s">%s</h2></strong>
'''

HTML_CONNECTION_FORMAT = '''
        <h4 id="%s">%s</h4>
'''

HTML_VIDEO_FORMAT = '''
        <iframe width="560" height="420" src="https://www.youtube.com/embed/%s?start=%d" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
'''

HTML_FOOTER = '''
	</body>
</html>
'''

def get_date():
    return str(datetime.datetime.now()).split('.')[0].split(" ")[0]

def games_dir():
    return os.path.abspath(__file__ + "/../../randovania/games")

def all_games():
    games = list()
    for _, dirs, _ in os.walk(games_dir()):
        for game in dirs:
            if game.startswith("__"):
                continue
            games.append(game)
        break

    return games

def get_yt_ids(item, ids):
    if item["type"] != "and" and item["type"] != "or":
        return

    data = item["data"]
    if data["comment"] is not None:
        comment = data["comment"]
        if "youtu" in comment:
            video_id = comment.split("/")[-1].split("watch?v=")[-1].split(" ")[0].split("?t=")[0]
            start_time = 0
            if "?t=" in comment:
                start_time = int(comment.split("?t=")[-1])
            ids.append((video_id, start_time))

    for i in data["items"]:
        get_yt_ids(i, ids)

def collect_game_info(game):
    json_data_dir = os.path.join(games_dir(), game, "json_data")

    world_names = list()
    for _, _, files in os.walk(json_data_dir):
        for file in files:
            if file.endswith(".json") and "header" not in file:
                world_names.append(file.split(".json")[0])

    worlds = dict()
    for world in world_names:
        file = open(os.path.join(json_data_dir, world + ".json"), "r")
        data = json.loads(file.read())
        file.close()

        areas = dict()
        for area in data["areas"]:
            nodes = dict()
            for node in data["areas"][area]["nodes"]:
                connections = dict()
                for connection in data["areas"][area]["nodes"][node]["connections"]:
                    yt_ids = list()
                    connection_data = data["areas"][area]["nodes"][node]["connections"][connection]
                    get_yt_ids(connection_data, yt_ids)
                    if len(yt_ids) > 0:
                        connections[connection] = yt_ids
                if len(connections) > 0:
                    nodes[node] = connections
            if len(nodes) > 0:
                areas[area] = nodes
        if len(areas) > 0:
            worlds[world] = areas
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
                <li><a href="#%s">%s</a></li>
    '''

    for area in sorted(areas):
        body += HTML_AREA_FORMAT % (area, area)
        nodes = areas[area]
        for node in sorted(nodes):
            connections = nodes[node]
            toc_connections = ""
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

def export_game(game, out_dir):
    worlds = collect_game_info(game)
    for world in worlds:
        html = generate_world_html(world, worlds[world])
        file = open(os.path.join(out_dir, world + ".html"), "w")
        file.write(html)
        file.close()
    
    html = HTML_HEADER_FORMAT % ("index", game, get_date())
    
    toc = """
    <div>
        <ul>
    """

    TOC_WORLD_FORMAT = '''
        <li><a href="%s">%s</a>
    '''

    for world in sorted(worlds):
        toc += TOC_WORLD_FORMAT % (world + ".html", world)
    toc += """
        </ul>
    </div>
    """

    html += toc

    html += HTML_FOOTER

    file = open(os.path.join(out_dir, "index.html"), "w")
    file.write(html)
    file.close()

def main():
    games = len(sys.argv) < 2
    games = list()
    if all_games:
        games = all_games()
    else:
        games.append(sys.argv[1])
    for game in games:
        export_dir = os.path.abspath(__file__ + "/../exported_db_videos" + "/" + game)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        export_game(game, export_dir)

if __name__ == "__main__":
    main()
