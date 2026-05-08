"""
Persistent player state shared across all levels and game sessions.

All variables survive level transitions and player death.
Imported as a module reference ('import systems.player_state as ps') so
that mutations in one module are immediately visible everywhere else.

Variables:
    player_coins (int):
        Current coin balance. Increases when Pacman eats dots (+1),
        power pellets (+5), bonus items (+8 to +60), or kills a ghost
        with Fire Sword (+5). Never resets between levels.

    equipped_weapon (str | None):
        The weapon currently in use. Affects Pacman colour, speed, and
        combat effects while powered. One of:
            'DAGGER' – increases Pacman speed by 0.5 when powered.
            'FIRE'   – doubles points and coins on kills and bonus items.
            'ICE'    – halves ghost movement speed while frightened.
            'AXE'    – extends frightened timer by 1.5 s on each ghost kill.
        None if no weapon is equipped.

    owned_weapons (list[str]):
        Weapons already purchased in the shop. Used to skip re-purchase
        and allow free re-equip. Maximum 4 entries.

    equipped_bike (str | None):
        The vehicle currently in use. Adds a flat speed bonus to Pacman.
        One of:
            'VESPA' – +0.5 speed.
            'SPORT' – +0.75 speed.
        None if no bike is equipped.

    owned_bikes (list[str]):
        Bikes already purchased. Maximum 2 entries.
"""

player_coins      =  1000
equipped_weapon   =  None
owned_weapons     =  []

equipped_bike     =  None
owned_bikes       =  []     