
# Description
A procedurally generated Mediterranean Sea mapscript with realistic geography, climate, and historical starting locations.
For Civilization IV.

# Instructions
_Steam version:_ Add Mediterranean_sea.py to
C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\PublicMaps

**Note: This mapscript is not compatible with the BUFFY Mod** (it tries to force the game into nonexistent options).
Other basic mods (e.g. BUG) should be fine.
Obviously mods that add Civilizations, Bonuses, Terrain etc. might cause it to behave incorrectly.

# Features
## Map dimensions
The script generates maps with ratios approximately 2.33:1.
Mapsizes:
  Duel	36×16
  Tiny	48×20
  Small	60×28
  Standard	72×32
  Large	84×36
  Huge	92×40
Gameplay-wise, this should result in empire sizes similar to that in Inland_Sea.py.

## Custom Options:
### Bonus generator
- Vanilla: Default behavior (Runs strategic and food bonus checks / additions near starting plots)
- Optional: Semi-historical resource placement
    - Swaps / removes ahistoric resources
    - Region specific bonus placement
### Historical starting locations
- Vanilla: Default behavior
- Historical (Shuffle): Randomly places all players in 5 primary, 5 secondary, and 8 tertiary locations, in order of priority. Remaining players are placed with default methods.
- Historical (Fixed): If there are any map-appropriate Vanilla BTS Civilizations in the playerlist, they are placed on fixed regions. Remaining players assignments fall back to the Shuffle method, and then to default methods.
- Details are in _class HistoricalStartAssigner_
- Option: Suez, Bosporus, Gibraltar straits
    - Open / Close
- Option: Mountain range settings
  - Realistic: Stronger mountain ranges (Alps, Pyrenees, etc.)
  - Reduced: Nerfs mountain ranges (recommended unless running AI improvement mods like AdvCiv, as landmasses could become completely blocked)

### Miscellaneous
- Improved MultilayeredFractal generator
  - Takes matrix inputs
  - More property inputs for regions
- Lattitude-band based Terrain overrides
- Bonus generator
  - Runs strategic and food bonus additions to starting plots
  - Option: Semi-historical resource placement
    - Swaps / removes ahistoric resources
    - Region specific bonus placement
- River generator based on that of Tectonics.py
  - Generates more realistic rivers
  - More control over river frequency
  - Features river deletion / reduction regions (used to reduce rivers in Sahara desert)
  - Custom north-flowing river generator (used for Nile river)
- Two tile coasts (expandCoastToTwoTiles)

