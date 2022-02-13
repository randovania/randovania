Echoes Menu for Metroid Prime 2: Echoes, created by Claris.

1. PREREQUISITES
2. PROGRAM USAGE
3. LIMITATIONS
4. REDUCED MEMORY USAGE MODE
5. ACCESSING THE MENU
6. MENU OPTIONS
7. VERSION HISTORY



1. PREREQUISITES

This program cannot edit an ISO directly; you need to extract the files from the Echoes ISO. This can be done with Dolphin (right-click the game > Filesystem > right-click Disc > Extract All Files...), or using a program such as GC Rebuilder.

Due to the amount of additions made to the game, the game's size will likely be too large to properly rebuild an ISO and/or play the game on console. If this is an issue, you can use the accompanying "Disable Echoes Attract Videos" program to reduce the game's file size.



2. PROGRAM USAGE

You can run the program with no arguments provided; in which case it will first check the current folder for the game's files, and if not found, will prompt you to provide a folder path. Otherwise:

EchoesMenu [Folder] [-e]

[Folder]: The folder that contains the game's files.
[-e:] Do not do exceptions. Exceptions are done to avoid crashes or other issues; you should not use this option when modifying the original game.



3. LIMITATIONS

A major concern with the Menu is avoiding crashes from using too much memory. There are some restrictions because of this:
- Opening the Menu will unload all connected areas. Avoid standing close to shot closed doors when opening the Menu, as they may still load and crash the game.
- Every submenu is placed on its own layer, which is loaded when needed.
- As I do not know how to properly unload layers without unloading the entire area, it's not possible to backtrack from submenus; pressing B will exit the Menu completely.

Some areas have specific exceptions done to avoid crashes or other issues:
- A few places use "Reduced Memory Usage Mode"; see below.
- Too many additional instances will make it impossible to go from Central Area Transport West to Main Research without crashing, before Caretaker Drone is defeated. Because of this:
-- Main Research cannot check which layers are currently active when entering the Layers submenu, and are instead reverted to their defaults.
-- The "Echo Bot" layer in Central Area Transport West (requiring you to shoot an invisible Echo Bot before you can use the cannon) is off by default.
- Aerie Access will reload Aerie when exiting the Menu, otherwise it would never try to reload.

Other various limitations include:
- Saves are not compatible with the unmodified game, due to adding a ton of new Room Layers. (This does not apply to the entire memory card file; just an individual save slot.) Make sure you start from a new file instead of a 0:00 Temple Grounds file.
- The game does not pause while you're in the Menu, so enemies, platforms, etc. can still move. (Due to the Menu's camera, it's treated like a cutscene, so you can't take damage and the in-game timer doesn't pass.)
- Anything that shakes the screen will shake the Menu as well.
- Some graphical effects, such as fog, will appear over the Menu.



4. REDUCED MEMORY USAGE MODE

In specific places, even with all of the restrictions in place, there's too much loaded to be able to use all functions of the Menu without crashing. These places switch the Menu to "Reduced Memory Usage Mode", where the Warp and Inventory options are limited. This is currently used in:
- The Spider Guardian boss fight
- The Dark Samus 2 boss fight



5. ACCESSING THE MENU

The Menu can be opened at almost any time by quickly pressing Up on the D-Pad 4 times. The count will be reset if you wait more than half a second between each press.

The Menu, with somewhat accurate loading times, takes about half a second to load after inputting the command. If the Menu doesn't come up, just try again; if it still doesn't come up, it's probably a bug and should be reported.

You can bring up the Menu during cutscenes, but cutscene cameras will interfere with the Menu's camera, so it's highly recommended you avoid doing so.



6. MENU OPTIONS


--- Warp ---
Allows you to warp to any Area in the game (that's part of Single Player). 

In "Reduced Memory Usage" mode, this is replaced with an option to warp to the first Area in the game (Landing Site).


--- Inventory ---
Allows you to manage your items. This is divided into 4 submenus. In each submenu except for Expansions, items colored Green indicate they're turned On, while items colored Red indicate they're turned Off.

In "Reduced Memory Usage" mode, this is replaced with an option to refill your health and ammo.

-- Upgrades --
Lets you turn On/Off all major upgrades. This includes some upgrades that cannot be removed in normal gameplay, such as the Power Beam and Morph Ball. Note that the Dark and Light Beams will give you 50 ammo of each, and Seeker Launcher will give you 5 Missiles.

-- Expansions --
Lets you set the specific amount of Energy Tanks, Power Bombs, Missiles, and Beam Ammo you have.
- Pressing Left/Right on the D-Pad will alter the amount by 1.
- Pressing Left/Right on the Analog Stick will alter the amount by 10.
- Pressing X will set it to the maximum possible, while pressing Y will set it to 0.
As a side effect of how this is set up, entering this submenu will automatically refill your ammo. Note that the "Unlimited Missiles" and "Unlimited Beam Ammo" items in Miscellaneous would crash this submenu, so they are removed when entering instead.

-- Temple Keys --
Lets you turn On/Off the Keys for each Dark Temple.

-- Miscellaneous --
Lets you turn On/Off various random "items", that are mostly from Multiplayer. Note that nothing on this submenu is kept when reloading a save.


--- Layers ---
You can switch which Room Layers in the current room are on/off; Green indicates On, while Red indicates Off. Be aware that switching too many layers on, or potentially certain combinations of layers, may crash the game.

The layer list excludes the Default layer in each room (not a good idea to turn off in general, but mainly because in most room it will screw up the Menu and cause it to constantly open), as well as any layers that do not actually have any objects.

Unlike the rest of the Menu, this submenu is actually included as part of the current room itself, due to the options being different in every room. Because of this, I'm unable to properly unload it if you were to exit out of the Menu; exiting out is therefore disabled, and instead the room must be reloaded, using the option at the top.

Additionally, there's an option to reset every loaded Memory Relay. Memory Relays are used for minor things that get saved, such as a Blast Shield being destroyed, a pickup being collected, etc. 

Note that, if any layers have been switched on or off after the room has been loaded, the current layer list will probably not accurately reflect which layers are currently loaded. If you wish to reset the Memory Relays on specific layers, then it's best to: 
1. Select which layers you want loaded
2. Reload the room
3. Reopen the Menu, select Layers, then select Reset Loaded Memory Relays
4. Reload the room again.


--- Save ---
Allows you to save the game in any room. If you say No, a Checkpoint is set regardless (i.e. the game is saved, but not actually written to the memory card, so you can reload this save upon death). As a side effect of the Save Special Function, your health is fully replenished. Keep in mind that saves are not compatible with the unmodified game.


--- Death ---
Kills Samus immediately. Useful for when you want to return to a previous Save/Checkpoint.



7. VERSION HISTORY

V1.0 - February 18th, 2016
Initial Release