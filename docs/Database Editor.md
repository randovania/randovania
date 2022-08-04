## Introduction

This is the script for a video about how to use the Data Editor that was never recorded.
It's still a helpful read, though a bit outdated.

## Script

Hello, in this video I'll be talking about Randovania's data visualizer and editor, with a focus on the editor for Metroid Dread though the general idea still applies to any supported game as well as the visualizer.

The visualizer and editor are both the same tool, with slight variations for a better experience of their specific purpose. The visualizer is expected to be used by any Randovania user via a distributed executable.
Meanwhile, the editor is expected to be used by contributors running Randovania from the git repository.

You can open the visualizer via the Open -> Game -> Data Visualizer, while the editor is via Edit -> Database -> Internal -> Game.

The editor works by focusing on a single area at a time. Randovania divides the game into multiple worlds, each having multiple areas. What exactly each one means is arbitrarily defined per game. In Echoes, the worlds are Temple Grounds, Agon Wastes, etc, with the areas being each room being an area. In Dread, the worlds are Artaria, Burenia, etc, with areas being roughly the rooms, based on camera.

There are 3 sections which can be moved around if you want. On the right side are details of the selected node. In the middle is a map of the current area, sadly only for Dread and Cave Story at the moment. On the left is a list of nodes in the current area, as well as combo boxes for selecting the world and area to edit.
Still on the left side, there's a separate tab where you can edit the resource database - mostly events and templates, but more on this later.

The main focus of the editor is establishing connections between multiple nodes, effectively points of interest in each area.
You first select a node on the list on the left, or by double clicking it on the map. After this you select another node on the combo box on the right, or by right clicking a node on the map and selecting "View connections to this".
On the right you'll see the requirements for going from the first node to the second. In other words, what items Randovania considers necessary to navigate this part of the room. Clicking Edit opens a dialog for editing this particular connection.

A requirement can be one of 4 things: a certain quantity of a specific item (or another resource), some predefined template, and lastly: and/or - a list of other requirements where all/any of them must be satisfied.
There are two special values: empty or and empty and. Empty And is considered trivial - nothing needed at all, and Empty Or is considered impossible - these nodes aren't connected.
Most requirements are going to be a combination of And/Or and item requirements, however sometimes a path depends on some game state, like opening a lock somewhere else. This is implemented by using Events.

Events represent some sort of change in the game with a clear before and after. Most changes can be represented this way. If what you're trying to do doesn't seem to fit, think if there's a way of simplifying the problem so that it'd fit.
To create a new event, go back to the resource database editor and open the tab for events. Scroll all the way to the bottom and start writing on the last row. The long name can be changed freely, but changing the short name is tricky. Do try to keep it indicative.

After creating the event, it's already possible to use it in requirements but there needs to be at least one node that gives the event. In order to do that, you must first select a node, click Edit in the top-right, select Event in the combo below the "Extra" field and then select your event.

Most likely you'll want to make an entirely new node for the event. For this, you press the New Node button on the left but for games with maps it's recommended you right click on a spot and select "Create node here". In either case, write a name and then make sure to have connections to this new node.

While making connections for nodes, it's extremely common to have the path between two nodes be the special Trivial/Impossible. Right clicking a node in the map offers a shortcut to create a connection with these requirements. It can also be helpful to create additional nodes just to represent some location in the area in order to make the area easier to understand.

Right clicking and then enabling "Show all node connections" can be very helpful to find out which nodes connect to what, and which ones are missing connections.

In order to allow navigation between different areas, dock nodes are used. A dock has both a type - normal door, portal, hole - and a weakness - missile door, dark portal, blocked hole. The distinction between types is you were to change the dock for some preset setting, it only makes sense to change inside the same type.
Dock nodes come in pairs - one in each area, and they connect to each other. There's also an expected naming convention, but you can press the "Update node name" button to have it fill the template. If there's multiple docks of the same type to the same area, you'll need to write a suffix by yourself.

For Dread, the recommended way of creating a dock node is by right clicking a spot on the map where there's some overlap with an adjacent area. An option for creating a dock node to that area will show up and it automatically creates both docks with proper names. All that is left is selecting the proper type and weakness for these new docks.

When a dock or teleporter node is selected, you can see on the right where it connects to. Clicking this will select the connected area, allowing for quick navigation. For Dread, it's also possible to double click on where the nearby areas are visible in the map and swap to it. Sometimes there's an overlap of multiple areas in a location: you'll want to right click and select one area in this case.

It's possible to rename any node and area freely. Renaming a node or area automatically renames all references to it, like "Door to XXXX". Renaming areas and nodes will break existing rdvgame files and possibly presets, so for non-experimental games a migration script will also be needed.

For Dread, renaming areas, events and nodes to friendlier names is highly recommended.

Lastly, you can save your changes by clicking "Save as database" on the top left. Save often to make sure you don't lose your progress!


--- TODO: editing the resource db
