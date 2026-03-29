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
- Vanilla: Default behavior (Runs strategic and food bonus additions to starting plots)
- Optional: Semi-historical resource placement
    - Swaps / removes ahistoric resources
    - Region specific bonus placement
### Historical starting locations
- Vanilla: Default behavior
- Historical (Random): Randomly places all players in 4 primary and 6 secondary locations. Remaining players are placed with default methods.
- Historical (Fixed): If there are any map-appropriate Vanilla BTS Civilizations in the playerlist, they are placed on fixed regions. Remaining players are placed with default methods.
- Details are in _class HistoricalStartAssigner_
  
    


### Miscellaneous
- Improved MultilayeredFractal generator
    - Takes matrix inputs
    - More property inputs for regions
- Lattitude-band based Terrain overrides
- River generator based off of Tectonics.py
    - Generates more realistic rivers
    - More control over river frequency
    - Features river deletion / reduction regions (used to reduce rivers in Sahara desert)
    - Custom north-flowing river generator (used for Nile river)
- Two tile coasts (expandCoastToTwoTiles)
- Custom Bonus generator
- Custom Start location assigner
