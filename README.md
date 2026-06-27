# Description
A Civilization IV mapscript which procedurally generates maps with quasi-realistic Mediterranean geography, climate, and historical starting locations.

![StandardSizeThumb](png/StandardSizeThumb.png)
<details>
<summary><h3>Screenshots</h3></summary>
<img src="png/Italy.png">
<img src="png/Greece.png">
<img src="png/Danube.png">
<img src="png/Levant_Egypt.png">
</details>


# Instructions
Download Mediterranean_Sea.py from the latest [release.](https://github.com/AineiasStymphalios/Mediterranean_Sea.py/releases)

Add Mediterranean_sea.py to:
- CD version:
```
C:\Program Files\Firaxis Games\Civilization 4\Beyond the Sword\PublicMaps
```

- Steam version:
```
C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\PublicMaps
```
## Version support
This mapscript supports Civ4 Beyond the Sword, Warlords, and Vanilla.

## Mod support
This mapscript should work with most vanilla-like mods (e.g. BUG, BAT, AdvCiv ...).
Mods that _remove_ Civilizations, Bonuses, Terrain etc. may cause unexpected behavior.

# Features

## Starting Location Options
- Historical: If there are any map-appropriate Vanilla BTS Civilizations in the playerlist, they are placed on fixed regions. Remaining players are randomly placed in 5 primary, 5 secondary, and 8 tertiary locations, in order of priority.
- Vanilla: Default behavior



### Civilizations supported by Fixed-spawn mode
If you include these civilizations to the player list in **Custom Game** and select Historical (fixed) starting locations, they will always start in the following areas of the map.

| Playthrough | Game Identifier | Region | Notes |
| :--- | :--- | :--- | :--- |
| **Classical Civs** | `CIVILIZATION_ROME` | Italy | |
|  | `CIVILIZATION_GREECE` | Greece | |
|  | `CIVILIZATION_CARTHAGE` | Tunisia | |
|  | `CIVILIZATION_PERSIA` | Levant | |
|  | `CIVILIZATION_SPAIN` | Spain | Classical Iberians|
|  | `CIVILIZATION_CELT` | Gaul | |
|  | `CIVILIZATION_EGYPT` | Egypt | |
|  | `CIVILIZATION_MONGOL` | Steppe | Thracians, Scythians, Huns |
| **Medieval Civs** 
| `CIVILIZATION_PORTUGAL` | Portugal | |
|  | `CIVILIZATION_VIKING` | Sicilies | Norman Kingdom of Sicily |
|  | `CIVILIZATION_FRANCE` | Gaul | |
|  | `CIVILIZATION_HOLY_ROMAN` | Germania | |
|  | `CIVILIZATION_GERMANY` | Germania | |
|  | `CIVILIZATION_RUSSIA` | Steppe | |
|  | `CIVILIZATION_BYZANTIUM` | Bosporus | |
|  | `CIVILIZATION_OTTOMAN` | Bosporus | |
|  | `CIVILIZATION_MALI` | Morocco | |
|  | `CIVILIZATION_ETHIOPIA` | Morocco | |

## Bonus generation options
- Vanilla: Default behavior (Runs strategic and food bonus checks / additions near starting plots)
- Optional: Semi-historical resource placement
    - Swaps / removes ahistoric resources
      - Removes or Replaces New World, Silk Road, and African resources
    - Region specific bonus placement
      - e.g. adds Silk Road resources in the Levant, Stone to Egypt, Marble to Rome and Greece, Ivory to Carthage

## Landmass Options
Default options are recommended unless one is running AI improvement mods (e.g. k-mod, AdvCiv), as landmasses could become completely blocked.
- Option: Open or close the following straits / Ithmus:
  - Suez
  - Bosporus
  - Gibraltar
- Option: Mountain range settings
  - Realistic: Stronger mountain ranges (Alps, Pyrenees, etc.)
  - Reduced (default): Nerfs mountain ranges

<details>
<summary><h3>Landmass variations</h3></summary>
<img src="png/suez.png">
<img src="png/marmara.png">
<img src="png/gibraltar.png">
<img src="png/ItalyAlps.png">
</details>

## Miscellaneous
- Based on [GeometricMultiFractal)](https://github.com/AineiasStymphalios/GeometricMultiFractal) 

