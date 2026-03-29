#
#   FILE:    Mediterranean_Sea.py
#   AUTHOR:  AineiasStymph (Script adapted directly from GRM7584's Earth2, which was based on Sirian's Terra script)
#   PURPOSE: Global map script - Simulates Randomized Mediterranean Sea
#-----------------------------------------------------------------------------
#   Copyright (c) 2008 Firaxis Games, Inc. All rights reserved.
#-----------------------------------------------------------------------------
#

from CvPythonExtensions import *
import CvUtil
import CvMapGeneratorUtil
from CvMapGeneratorUtil import MultilayeredFractal
from CvMapGeneratorUtil import TerrainGenerator
from CvMapGeneratorUtil import FeatureGenerator

'''
##############################################################################
MULTILAYERED FRACTAL NOTES

The MultilayeredFractal class was created for use with this script.

I worked to make it adaptable to other scripts, though, and eventually it
migrated in to the MapUtil file along with the other primary map classes.

- Bob Thomas July 13, 2005


TERRA NOTES

Terra turns out to be our largest size map. This is the only map script
in the original release of Civ4 where the grids are this large!

This script is also the one that got me started in to map scripting. I had 
this idea early in the development cycle and just kept pestering until Soren 
turned me loose on it, finally. Once I got going, I just kept on going!

- Bob Thomas   September 20, 2005

EARTH2 NOTES

This is based purely on the Terra script, albeit with a lot more similarity
to Earth in terms of landmasses. Rocky Climate and Normal Sea Levels strongly
recommended for maximum earthiness.

##############################################################################
MEDITERRANEAN NOTES

This mapscript is based on Earth2.
Below are its features:
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
- Option: Historical starting locations
    - Random Historical: Randomly places all players in 4 primary and 6 secondary locations. 
    Remaining players are placed with default methods.
    - Fixed Historical: Places any map-appropriate Vanilla BTS Civilizations in the playerlist on fixed regions. 
    Remaining players are placed with default methods.
- Option: Open / close Suez, Bosporus, Gibraltar straits
- Option: Mountain range settings
    - Realistic: Stronger mountain ranges (Alps, Pyrenees, etc.)
    - Reduced: Nerfs mountain ranges (recommended, unless running AI improvement mods)

- AineiasStymph, March 28, 2026
##############################################################################
'''

    
def getDescription():
    desc = "A procedurally generated Mediterranean Sea map with realistic geography and climate. "
    desc += "Resources: 'Semi-historical' replaces Silk Road and New World resources with regional resources, "
    desc += "removes resources like Ivory from higher lattitudes, and places additional resources to specific historical regions. "
    desc += "Starting Positions: 'Historical (Shuffled)' randomly distributes players among tiered historical regions "
    desc += "(e.g., Italy, Greece, Levant). 'Historical (Fixed)' matches specific Civilizations to their real-world locations, "
    desc += "and shuffles the rest into open historical regions. "
    return desc

def isAdvancedMap():
    "This map should show up in simple mode"
    return 0

# -----------------------------------------------------------------------------
# Custom Options
# -----------------------------------------------------------------------------
def getNumCustomMapOptions():
    return 6

def getCustomMapOptionName(argsList):
    index = argsList[0]
    if index == 0:
        return "Resources"
    elif index == 1:
        return "Starting Positions"
    elif index == 2:
        return "Suez"
    elif index == 3:
        return "Dardanelles / Bosporus"
    elif index == 4:
        return "Gibraltar"
    elif index == 5:
        return "Mountain Ranges"
    return ""

def getNumCustomMapOptionValues(argsList):
    index = argsList[0]
    if index == 0:
        return 2          # Resources: Vanilla, Semi-historical
    elif index == 1:
        return 3          # Starting Positions: Vanilla, Historical (Shuffled), Historical
    elif index == 2:
        return 2          # Suez: Closed, Open
    elif index == 3:
        return 2          # Dardanelles / Bosporus: Closed, Open
    elif index == 4:
        return 2          # Gibraltar: Closed, Open
    elif index == 5:
        return 2          # Mountains: Realistic, reduced
    return 0

def getCustomMapOptionDescAt(argsList):
    index = argsList[0]
    selection = argsList[1]
    if index == 0:
        if selection == 0: return "Vanilla"
        else: return "Semi-historical"
    elif index == 1:
        if selection == 0: return "Vanilla"
        elif selection == 1: return "Historical (Shuffled)"
        else: return "Historical (fixed)"
    elif index == 2:
        if selection == 0: return "Closed (Historical)"
        else: return "Open"
    elif index == 3:
        if selection == 0: return "Closed (Historical)"
        else: return "Open"
    elif index == 4:
        if selection == 0: return "Closed"
        else: return "Open (Historical)"
    elif index == 5:
        if selection == 0: return "Realistic Mountain Ranges"
        else: return "Reduced (Recommended)"
    return ""

def getCustomMapOptionDefault(argsList):
    index = argsList[0]
    if index == 0: return 1 # Semi-historical
    elif index == 1: return 2 # Fixed
    elif index == 2: return 0 # Default to Closed
    elif index == 3: return 0 # Default to Closed
    elif index == 4: return 1 # Default to Open
    elif index == 5: return 1 # Default to Reduced
    return 0

# -----------------------------------------------------------------------------
# Map Properties
# -----------------------------------------------------------------------------

def getGridSize(argsList):
    # original map projection is 1050x450px = 2.33:1
    grid_sizes = {
        WorldSizeTypes.WORLDSIZE_DUEL:      (9, 4),
        WorldSizeTypes.WORLDSIZE_TINY:      (12, 5),
        WorldSizeTypes.WORLDSIZE_SMALL:     (15, 7),
        WorldSizeTypes.WORLDSIZE_STANDARD:  (18, 8),
        WorldSizeTypes.WORLDSIZE_LARGE:     (21, 9),
        WorldSizeTypes.WORLDSIZE_HUGE:      (23, 10),
    }
    if argsList[0] == -1:
        return []
    return grid_sizes[argsList[0]]

def isSeaLevelMap():
    return 0

def getWrapX():
    return False

def getWrapY():
    return False

def isClimateMap():
    return 0

def getClimate():
    return ClimateTypes.CLIMATE_TEMPERATE

_all_start_coords = [] # Store player start coords
def beforeGeneration():
    """
    Official Civ4 hook called before map generation starts.
    Guaranteed to run on Map Regeneration.
    """
    # Clear the starting plot cache so that regeneration reshuffles players
    global _START_PLOT_MAP
    _START_PLOT_MAP = None
    return None

# -----------------------------------------------------------------------------
# MultilayeredFractal Generator
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# MultilayeredFractal Generator
# -----------------------------------------------------------------------------
class MultilayeredFractal(CvMapGeneratorUtil.MultilayeredFractal):
    # Subclass. Only the controlling function overridden in this case.
    def generatePlotsByRegion(self, region_data):
        # Based on "Sirian's MultilayeredFractal class, controlling function."
        sizekey = self.map.getWorldSize()
        sizevalues = {
            WorldSizeTypes.WORLDSIZE_DUEL:      (3,2,1),
            WorldSizeTypes.WORLDSIZE_TINY:      (3,2,1),
            WorldSizeTypes.WORLDSIZE_SMALL:     (4,2,1),
            WorldSizeTypes.WORLDSIZE_STANDARD:  (4,2,1),
            WorldSizeTypes.WORLDSIZE_LARGE:     (4,2,1),
            WorldSizeTypes.WORLDSIZE_HUGE:      (5,2,1)
            }
        (ScatterGrain, BalanceGrain, GatherGrain) = sizevalues[sizekey]

        sea = 0
        
        for name, west, south, width, height, water, grain, hills_grain, terrain_type in region_data:
            NiTextOut("Generating %s (Python Mediterranean) ..." % name)

            # Convert to plot indices (0-based, bottom-left)
            west_x = int(self.iW * west)
            east_x = int(self.iW * (west + width))
            south_y = int(self.iH * south)
            north_y = int(self.iH * (south + height))

            # Clamp to valid map range [0, iW-1] and [0, iH-1]
            west_x = max(0, min(west_x, self.iW - 1))
            east_x = max(0, min(east_x, self.iW - 1))
            south_y = max(0, min(south_y, self.iH - 1))
            north_y = max(0, min(north_y, self.iH - 1))

            # Ensure west <= east and south <= north
            if west_x > east_x: west_x, east_x = east_x, west_x
            if south_y > north_y: south_y, north_y = north_y, south_y

            # Make sure region has at least one column and row
            if west_x == east_x:
                if west_x < self.iW - 1: east_x += 1
                else: west_x -= 1
            if south_y == north_y:
                if south_y < self.iH - 1: north_y += 1
                else: south_y -= 1

            reg_width = east_x - west_x + 1
            reg_height = north_y - south_y + 1

            regionContFrac = CyFractal()
            regionHillsFrac = CyFractal()
            regionPeaksFrac = CyFractal()

            regionContFrac.fracInit(reg_width, reg_height, grain, self.dice, self.iRoundFlags, -1, -1)
            regionHillsFrac.fracInit(reg_width, reg_height, hills_grain, self.dice, self.iTerrainFlags, -1, -1)
            regionPeaksFrac.fracInit(reg_width, reg_height, hills_grain+1, self.dice, self.iTerrainFlags, -1, -1)

            if water == 0: iWaterThreshold = -1   
            else: iWaterThreshold = regionContFrac.getHeightFromPercent(water + sea)

            hill_range = self.gc.getClimateInfo(self.map.getClimate()).getHillRange()
            default_peak = self.gc.getClimateInfo(self.map.getClimate()).getPeakPercent()

            if terrain_type == "flat":
                iHillsBottom1 = regionHillsFrac.getHeightFromPercent(25)
                iHillsTop1   = regionHillsFrac.getHeightFromPercent(30)
                iHillsBottom2 = regionHillsFrac.getHeightFromPercent(75)
                iHillsTop2   = regionHillsFrac.getHeightFromPercent(80)
                iPeakThreshold = regionPeaksFrac.getHeightFromPercent(5)
            elif terrain_type == "plateau":
                iHillsBottom1 = regionHillsFrac.getHeightFromPercent(10)
                iHillsTop1   = regionHillsFrac.getHeightFromPercent(40)
                iHillsBottom2 = regionHillsFrac.getHeightFromPercent(60)
                iHillsTop2   = regionHillsFrac.getHeightFromPercent(90)
                iPeakThreshold = regionPeaksFrac.getHeightFromPercent(20)
            elif terrain_type == "highland":
                iHillsBottom1 = regionHillsFrac.getHeightFromPercent(20)
                iHillsTop1    = regionHillsFrac.getHeightFromPercent(90)
                iHillsBottom2 = regionHillsFrac.getHeightFromPercent(20)
                iHillsTop2    = regionHillsFrac.getHeightFromPercent(90)
                iPeakThreshold = regionPeaksFrac.getHeightFromPercent(50)
            elif terrain_type == "mountainous":
                iHillsBottom1 = regionHillsFrac.getHeightFromPercent(10)
                iHillsTop1    = regionHillsFrac.getHeightFromPercent(90)
                iHillsBottom2 = regionHillsFrac.getHeightFromPercent(10)
                iHillsTop2    = regionHillsFrac.getHeightFromPercent(90)
                iPeakThreshold = regionPeaksFrac.getHeightFromPercent(70)
            else:  # "default"
                iHillsBottom1 = regionHillsFrac.getHeightFromPercent(max(25 - hill_range, 0))
                iHillsTop1    = regionHillsFrac.getHeightFromPercent(min(25 + hill_range, 100))
                iHillsBottom2 = regionHillsFrac.getHeightFromPercent(max(75 - hill_range, 0))
                iHillsTop2    = regionHillsFrac.getHeightFromPercent(min(75 + hill_range, 100))
                iPeakThreshold = regionPeaksFrac.getHeightFromPercent(default_peak)

            region_plot_types = [PlotTypes.PLOT_OCEAN] * (reg_width * reg_height)

            for x in range(reg_width):
                for y in range(reg_height):
                    i = y * reg_width + x
                    if regionContFrac.getHeight(x, y) <= iWaterThreshold:
                        continue
                    hillVal = regionHillsFrac.getHeight(x, y)
                    if ((hillVal >= iHillsBottom1 and hillVal <= iHillsTop1) or
                        (hillVal >= iHillsBottom2 and hillVal <= iHillsTop2)):
                        if regionPeaksFrac.getHeight(x, y) <= iPeakThreshold:
                            region_plot_types[i] = PlotTypes.PLOT_PEAK
                        else:
                            region_plot_types[i] = PlotTypes.PLOT_HILLS
                    else:
                        region_plot_types[i] = PlotTypes.PLOT_LAND

            for x in range(reg_width):
                world_x = x + west_x
                for y in range(reg_height):
                    i = y * reg_width + x
                    if region_plot_types[i] != PlotTypes.PLOT_OCEAN:
                        world_y = y + south_y
                        world_i = world_y * self.iW + world_x
                        self.wholeworldPlotTypes[world_i] = region_plot_types[i]

        return self.wholeworldPlotTypes

def generatePlotTypes():
    NiTextOut("Setting Plot Types (Python Mediterranean) ...")
    
    # Clear the starting plot cache so that regeneration reshuffles players
    global _START_PLOT_MAP
    _START_PLOT_MAP = None

    gc = CyGlobalContext()
    m = CyMap()
    sizekey = m.getWorldSize()
    sizevalues = {
        WorldSizeTypes.WORLDSIZE_DUEL:      (3,2,1),
        WorldSizeTypes.WORLDSIZE_TINY:      (3,2,1),
        WorldSizeTypes.WORLDSIZE_SMALL:     (4,2,1),
        WorldSizeTypes.WORLDSIZE_STANDARD:  (4,2,1),
        WorldSizeTypes.WORLDSIZE_LARGE:     (4,2,1),
        WorldSizeTypes.WORLDSIZE_HUGE:      (5,2,1)
    }
    (ScatterGrain, BalanceGrain, GatherGrain) = sizevalues[sizekey]

    # Define the base regions (excluding Sinai)
    regions = [
        # name, west, south, width, height, water, grain, hills_grain, terrain_type
        ("IberiaCantabrianMt", 0.02, 0.71, 0.14, 0.08, 30, BalanceGrain, GatherGrain, "highland"),
        ("IberiaCentral", 0.04, 0.56, 0.17, 0.16, 0, BalanceGrain, GatherGrain, "plateau"),
        ("IberiaAndalusia", 0.04, 0.39, 0.14, 0.17, 20, BalanceGrain, ScatterGrain, "plateau"),
        ("IberiaPyrenees", 0.13, 0.67, 0.13, 0.09, 20, BalanceGrain, ScatterGrain, "mountainous"),
        ("IberiaPortugal", 0.01, 0.42, 0.04, 0.31, 20, BalanceGrain, GatherGrain, "default"),
        #
        ("Baleares", 0.22, 0.47, 0.07, 0.09, 80, ScatterGrain, GatherGrain, "plateau"),
        ("Corsica", 0.35, 0.59, 0.03, 0.07, 20, BalanceGrain, GatherGrain, "plateau"),
        ("Sardinia", 0.35, 0.45, 0.03, 0.09, 20, BalanceGrain, GatherGrain, "plateau"),
        ("FrAquitaine", 0.17, 0.76, 0.06, 0.24, 10, BalanceGrain, GatherGrain, "flat"),
        ("FrBurgundy", 0.23, 0.77, 0.07, 0.23, 0, BalanceGrain, GatherGrain, "plateau"),
        ("WestAlps", 0.30, 0.73, 0.04, 0.15, 0, BalanceGrain, GatherGrain, "highland"),
        ("EastAlps", 0.30, 0.88, 0.17, 0.12, 0, GatherGrain, ScatterGrain, "mountainous"),
        ("ItaPo", 0.34, 0.78, 0.11, 0.10, 20, ScatterGrain, GatherGrain, "flat"),
        ("ItaTuscany", 0.39, 0.69, 0.05, 0.14, 20, GatherGrain, GatherGrain, "default"),
        ("ItaLazio", 0.43, 0.64, 0.04, 0.14, 20, GatherGrain, GatherGrain, "default"),
        ("ItaCampania", 0.45, 0.59, 0.07, 0.10, 20, GatherGrain, GatherGrain, "default"),
        ("ItaPuglia-Calabria", 0.49, 0.45, 0.05, 0.19, 30, ScatterGrain, GatherGrain, "default"),
        ("Sicily", 0.44, 0.36, 0.06, 0.08, 40, ScatterGrain, GatherGrain, "plateau"),
        ("Malta", 0.50, 0.24, 0.02, 0.04, 50, BalanceGrain, GatherGrain, "default"),
        #
        ("Pannonia-Dacia", 0.46, 0.82, 0.29, 0.19, 20, BalanceGrain, GatherGrain, "default"),
        ("DinaricAlps", 0.48, 0.76, 0.09, 0.10, 20, BalanceGrain, GatherGrain, "plateau"),
        ("BalkanMountains", 0.58, 0.68, 0.10, 0.18, 0, BalanceGrain, ScatterGrain, "highland"),
        ("CarpathiansSouth", 0.60, 0.92, 0.09, 0.07, 0, BalanceGrain, GatherGrain, "highland"),
        ("Epirus-Thessaly", 0.59, 0.52, 0.08, 0.16, 30, ScatterGrain, ScatterGrain, "plateau"),
        ("Peleponnese", 0.62, 0.38, 0.05, 0.15, 30, ScatterGrain, GatherGrain, "default"),
        ("Agean", 0.67, 0.41, 0.07, 0.23, 90, ScatterGrain, GatherGrain, "plateau"),
        ("Crete", 0.69, 0.31, 0.06, 0.04, 20, BalanceGrain, GatherGrain, "plateau"),
        ("Rhodes", 0.77, 0.41, 0.02, 0.04, 40, ScatterGrain, GatherGrain, "plateau"),
        ("Cyprus", 0.85, 0.41, 0.03, 0.04, 30, BalanceGrain, GatherGrain, "plateau"),
        ("Thrace", 0.67, 0.74, 0.06, 0.09, 10, BalanceGrain, GatherGrain, "flat"),
        #
        ("Bithynia", 0.76, 0.71, 0.07, 0.07, 10, ScatterGrain, GatherGrain, "flat"),
        ("AnatAsiaMinor", 0.73, 0.48, 0.09, 0.23, 20, BalanceGrain, GatherGrain, "plateau"),
        ("AnatTaurus", 0.90, 0.62, 0.10, 0.18, 0, BalanceGrain, GatherGrain, "highland"),
        ("AnatCentral", 0.82, 0.61, 0.10, 0.20, 10, BalanceGrain, GatherGrain, "plateau"),
        ("AnatPontus", 0.82, 0.80, 0.18, 0.07, 20, BalanceGrain, GatherGrain, "plateau"),
        ("AnatCilicia", 0.82, 0.52, 0.10, 0.09, 30, BalanceGrain, GatherGrain, "highland"),
        ("Levant", 0.93, 0.10, 0.07, 0.54, 25, ScatterGrain, GatherGrain, "default"),
        #
        ("Egypt", 0.83, 0.00, 0.08, 0.25, 30, BalanceGrain, GatherGrain, "flat"),
        ("Cyrenaica", 0.63, 0.00, 0.21, 0.18, 20, GatherGrain, GatherGrain, "flat"),
        ("Surt", 0.51, 0.00, 0.14, 0.10, 20, GatherGrain, GatherGrain, "flat"),
        ("Tripolitania", 0.17, 0.00, 0.34, 0.20, 20, GatherGrain, GatherGrain, "flat"),
        ("Tunisia", 0.35, 0.17, 0.06, 0.22, 10, BalanceGrain, GatherGrain, "plateau"),
        ("Algeria", 0.17, 0.17, 0.20, 0.18, 10, BalanceGrain, GatherGrain, "plateau"),
        ("Morocco", 0.00, 0.00, 0.17, 0.26, 10, BalanceGrain, GatherGrain, "default"),
        ("Tangiers", 0.04, 0.27, 0.04, 0.07, 30, BalanceGrain, GatherGrain, "default"),
        ("AuresAtlas", 0.25, 0.17, 0.12, 0.07, 0, BalanceGrain, GatherGrain, "highland"),
        ("SaharaAtlas", 0.15, 0.13, 0.10, 0.07, 0, BalanceGrain, GatherGrain, "mountainous"),
        ("HighAtlas", 0.00, 0.05, 0.15, 0.11, 0, BalanceGrain, ScatterGrain, "mountainous"),
        ("MapborderSouth", 0.00, 0.00, 0.95, 0.04, 0, GatherGrain, GatherGrain, "default"),
    ]

    # Strait Options:
    # Option 0 = Closed, Option 1 = Open
    if m.getCustomMapOption(2) == 0:
        regions.append(("Sinai", 0.90, 0.05, 0.08, 0.18, 30, ScatterGrain, GatherGrain, "flat"))
    if m.getCustomMapOption(3) == 0:
        regions.append(("Marmara", 0.71, 0.67, 0.08, 0.12, 30, ScatterGrain, GatherGrain, "flat"))
    if m.getCustomMapOption(4) == 0:
        regions.append(("Gibraltar", 0.05, 0.26, 0.03, 0.14, 20, ScatterGrain, GatherGrain, "flat"))

    # Mountain Reduction Option (Index 5)
    # 0 = Realistic Mountain Ranges, 1 = Reduced (Recommended)
    if m.getCustomMapOption(5) == 1:
        for i in range(len(regions)):
            # The terrain_type string is the 9th element (index 8)
            if regions[i][8] == "mountainous":
                # Tuples are immutable in Python, so we unpack and repack
                r_name, r_w, r_s, r_width, r_h, r_water, r_grain, r_hg, r_type = regions[i]
                regions[i] = (r_name, r_w, r_s, r_width, r_h, r_water, r_grain, r_hg, "highland")

    # Call generatePlotsByRegion() function, passing the dynamic list.
    global plotgen
    plotgen = MultilayeredFractal()
    return plotgen.generatePlotsByRegion(regions)
    
    

# -----------------------------------------------------------------------------
# Terrain Generator
# -----------------------------------------------------------------------------
class TerrainGenerator(CvMapGeneratorUtil.TerrainGenerator):
    def __init__(self, iDesertPercent=40, iPlainsPercent=26,
                 fSnowLatitude=1.1, fTundraLatitude=1.1,
                 fGrassLatitude=0.0, fDesertBottomLatitude=0.0,
                 fDesertTopLatitude=0.2, fracXExp=-1,
                 fracYExp=-1, grain_amount=3):
        # Let the base class handle all the fractal initialization
        CvMapGeneratorUtil.TerrainGenerator.__init__(
            self, iDesertPercent, iPlainsPercent,
            fSnowLatitude, fTundraLatitude,
            fGrassLatitude, fDesertBottomLatitude, fDesertTopLatitude,
            fracXExp, fracYExp, grain_amount
        )
        # Set your custom band boundaries (adjust as needed)
        self.south_band = 0.20   # bottom 20% is desert-predominant
        self.north_band = 0.7   # top 30% is grass-predominant

    def generateTerrainAtPlot(self, iX, iY):
        pPlot = self.map.plot(iX, iY)
        if pPlot.isWater():
            return pPlot.getTerrainType()

        y_frac = iY / float(self.iHeight)   # 0 = bottom, 1 = top
        # Number of rows in the map
        total_rows = self.iHeight
        south_rows = int(total_rows * self.south_band)
        north_rows = int(total_rows * (1 - self.north_band))   # rows from the top
        # iY = 0 at bottom, so bottom rows are iY < south_rows
        # top rows are iY >= total_rows - north_rows

        # ------------------- Southern band (mostly desert) -------------------
        if iY < south_rows:
            desertVal = self.deserts.getHeight(iX, iY)
            # Use top 90% of desert fractal values to become desert
            desert_thresh = self.deserts.getHeightFromPercent(10)
            if desertVal >= desert_thresh:
                return self.terrainDesert
            else:
                return self.terrainPlains


        # ------------------- Northern band (mostly grass) -------------------
        if iY >= total_rows - north_rows:
            plainsVal = self.plains.getHeight(iX, iY)
            # Use top 20% of plains fractal values to become plains (rest becomes grass)
            plains_thresh = self.plains.getHeightFromPercent(80)
            if plainsVal >= plains_thresh:
                return self.terrainPlains
            else:
                return self.terrainGrass

        # ------------------- Middle band (natural mix of plains and grass) -------------------
        # Middle band: 
        return self._middleBandTerrain(iX, iY)

    def _middleBandTerrain(self, iX, iY):
        plainsVal = self.plains.getHeight(iX, iY)
        if (plainsVal >= self.iPlainsBottom) and (plainsVal <= self.iPlainsTop):
            return self.terrainPlains
        else:
            return self.terrainGrass


def generateTerrainTypes():
    NiTextOut("Generating Terrain (Python Terra) ...")
    terraingen = TerrainGenerator()
    terrainTypes = terraingen.generateTerrain()
    return terrainTypes

# -----------------------------------------------------------------------------
# Feature Generator
# -----------------------------------------------------------------------------
class FeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
    def __init__(self, iJunglePercent=0, iForestPercent=70, jungle_grain=5, forest_grain=6, fracXExp=-1, fracYExp=-1):
        # Initialize the base class – this sets up fractals for jungles, forests, etc.
        CvMapGeneratorUtil.FeatureGenerator.__init__(self, iJunglePercent, iForestPercent, jungle_grain, forest_grain, fracXExp, fracYExp)
        # Band boundaries – match your terrain bands
        self.south_band = 0.30   # bottom 30%
        self.north_band = 0.7   # top 30%
    def addIceAtPlot(self, pPlot, iX, iY, lat):
        # Do nothing – no ice will be placed
        pass

    def addForestsAtPlot(self, pPlot, iX, iY, lat):
        # Do nothing – we'll place our own forests in addFeaturesAtPlot
        pass

    def addFeaturesAtPlot(self, iX, iY):
        # First, let the base class handle ice, jungles, oases (if any)
        CvMapGeneratorUtil.FeatureGenerator.addFeaturesAtPlot(self, iX, iY)

        # Now add our own forests
        pPlot = self.map.sPlot(iX, iY)
        # Only add if no feature already exists (forests, jungles, ice, etc.)
        if pPlot.getFeatureType() == FeatureTypes.NO_FEATURE:
            y_frac = iY / float(self.iGridH)   # 0 = bottom, 1 = top

            # Determine forest chance based on latitude band
            if y_frac < self.south_band:
                chance = 5      # southern desert/plains – very few forests
            elif y_frac > self.north_band:
                chance = 45     # northern temperate – many forests
            else:
                chance = 30     # central mixed – moderate forests

            # Only place if the plot can have a forest (e.g., not desert, water, etc.)
            if self.mapRand.get(100, "Med Forest") < chance and pPlot.canHaveFeature(self.featureForest):
                pPlot.setFeatureType(self.featureForest, -1)

def addFeatures():
    NiTextOut("Adding Features (Python Mediterranean) ...")
    featuregen = FeatureGenerator()
    featuregen.addFeatures()
    # After all features are placed, expand coast to 2 tiles
    expandCoastToTwoTiles()
    return 0

# -----------------------------------------------------------------------------
# River Generator
# -----------------------------------------------------------------------------
class RiverGenerator:
    """
    From Tectonics.py class riversFromSea.
    Added to generate more natural-looking rivers.
    Input exclude_rects to prevent river generation in certain regions (used for Sahara in this mapscript).
    """
    def __init__(self, river_density=1.0, exclude_rects=None, reduce_rects=None, survival_chance=20):
        """
        exclude_rects: list of (west, south, width, height) – rivers never start or flow here.
        reduce_rects: list of (west, south, width, height) – rivers have only `survival_chance`% chance to flow here.
        river_density: float > 0; 1.0 gives a moderate number of rivers (similar to old divider=2).
        """
        self.gc = CyGlobalContext()
        self.dice = self.gc.getGame().getMapRand()
        self.map = CyMap()
        self.width = self.map.getGridWidth()
        self.height = self.map.getGridHeight()
        self.straightThreshold = 3
        if (self.width * self.height > 400):
            self.straightThreshold = 2
        self.survival_chance = survival_chance
        self.river_density = river_density

        # Convert exclude rectangles
        self.exclude_rects = []
        if exclude_rects:
            for (west, south, width, height) in exclude_rects:
                west_x = int(self.width * west)
                east_x = int(self.width * (west + width))
                south_y = int(self.height * south)
                north_y = int(self.height * (south + height))
                self.exclude_rects.append((west_x, east_x, south_y, north_y))

        # Convert reduce rectangles
        self.reduce_rects = []
        if reduce_rects:
            for (west, south, width, height) in reduce_rects:
                west_x = int(self.width * west)
                east_x = int(self.width * (west + width))
                south_y = int(self.height * south)
                north_y = int(self.height * (south + height))
                self.reduce_rects.append((west_x, east_x, south_y, north_y))

    def is_excluded(self, x, y):
        for (west_x, east_x, south_y, north_y) in self.exclude_rects:
            if west_x <= x <= east_x and south_y <= y <= north_y:
                return True
        return False

    def is_reduced(self, x, y):
        """Return True if the plot lies in a reduce_rect; also roll for chance."""
        for (west_x, east_x, south_y, north_y) in self.reduce_rects:
            if west_x <= x <= east_x and south_y <= y <= north_y:
                # Roll the dice: return True if the roll is < survival_chance (i.e., allowed)
                return self.dice.get(100, "River reduction") < self.survival_chance
        return True   # not in any reduce_rect -> always allowed

    def collateCoasts(self):
        """Return list of land plots adjacent to a large water body."""
        result = []
        for x in range(self.width):
            for y in range(self.height):
                plot = self.map.plot(x, y)
                if plot.isCoastalLand():
                    # Check if any adjacent water plot is large enough
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            adj = self.map.plot(nx, ny)
                            if self.is_water_for_river(adj):
                                result.append(plot)
                                break
        return result

    def seedRivers(self):
        # Base number of rivers proportional to the map's perimeter (width+height)
        # For density 1.0, this gives about the same as the old divider=2.
        base = (self.width + self.height) / 2.0
        riversNumber = int(base * self.river_density) + 1

        self.coasts = self.collateCoasts()
        coastsNumber = len(self.coasts)
        if coastsNumber == 0:
            return

        # Cap to the number of available coastal plots to avoid excessive attempts
        riversNumber = min(riversNumber, coastsNumber)

        coastShare = coastsNumber / riversNumber
        for i in range(riversNumber):
            for attempt in range(50):
                choiceCoast = coastShare * i + self.dice.get(coastShare, "Pick a coast for the river")
                if choiceCoast >= coastsNumber:
                    choiceCoast = coastsNumber - 1
                plot = self.coasts[choiceCoast]
                x, y = plot.getX(), plot.getY()
                # Skip if excluded OR (reduced and dice fails)
                if self.is_excluded(x, y):
                    continue
                if not self.is_reduced(x, y):
                    continue
                (x, y, flow) = self.generateRiverFromPlot(plot, x, y)
                if flow != CardinalDirectionTypes.NO_CARDINALDIRECTION:
                    riverID = self.gc.getMap().getNextRiverID()
                    self.addRiverFrom(x, y, flow, riverID)
                break

    def canFlowFrom(self, plot, upperPlot):
        """Return True if water can flow from `plot` to `upperPlot`."""
        if self.is_water_for_river(plot):
            return False
        if plot.getPlotType() == PlotTypes.PLOT_PEAK:
            return False
        # If the upper plot is in an excluded rectangle, stop
        ux, uy = upperPlot.getX(), upperPlot.getY()
        if self.is_excluded(ux, uy):
            return False
        # If the upper plot is in a reduced rectangle, apply chance
        if not self.is_reduced(ux, uy):
            return False

        if plot.getPlotType() == PlotTypes.PLOT_HILLS:
            return True
        if plot.getPlotType() == PlotTypes.PLOT_LAND:
            if self.is_water_for_river(upperPlot):
                return False
            return True
        return False

    def is_water_for_river(self, plot):
        """Return True only if the plot is water and its area is large enough."""
        if not plot.isWater():
            return False
        area_id = plot.getArea()
        if area_id == -1:
            return False
        area = self.map.getArea(area_id)
        return area.getNumTiles() >= 5   # min_water_area_size fixed at 5

    def generateRiverFromPlot(self, plot, x, y):
        FlowDirection = CardinalDirectionTypes.NO_CARDINALDIRECTION
        if ((y < 1 or y >= self.height - 1) or plot.isNOfRiver() or plot.isWOfRiver()):
            return (x, y, FlowDirection)
        eastX = self.eastX(x)
        westX = self.westX(x)
        otherPlot = True
        eastPlot = self.map.plot(eastX, y)
        if eastPlot.isCoastalLand():
            # Check water using is_water_for_river
            if (self.is_water_for_river(self.map.plot(x, y+1)) or
                self.is_water_for_river(self.map.plot(eastX, y+1))):
                landPlot1 = self.map.plot(x, y-1)
                landPlot2 = self.map.plot(eastX, y-1)
                if landPlot1.isWater() or landPlot2.isWater():
                    otherPlot = True
                else:
                    FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_NORTH
                    otherPlot = False
            if otherPlot:
                if (self.is_water_for_river(self.map.plot(x, y-1)) or
                    self.is_water_for_river(self.map.plot(eastX, y-1))):
                    landPlot1 = self.map.plot(x, y+1)
                    landPlot2 = self.map.plot(eastX, y+1)
                    if landPlot1.isWater() or landPlot2.isWater():
                        otherPlot = True
                    else:
                        FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_SOUTH
                        otherPlot = False
        if otherPlot:
            southPlot = self.map.plot(x, y-1)
            if southPlot.isCoastalLand():
                if (self.is_water_for_river(self.map.plot(eastX, y)) or
                    self.is_water_for_river(self.map.plot(eastX, y-1))):
                    landPlot1 = self.map.plot(westX, y)
                    landPlot2 = self.map.plot(westX, y-1)
                    if landPlot1.isWater() or landPlot2.isWater():
                        otherPlot = True
                    else:
                        FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_EAST
                        otherPlot = False
                if otherPlot:
                    if (self.is_water_for_river(self.map.plot(westX, y)) or
                        self.is_water_for_river(self.map.plot(westX, y-1))):
                        landPlot1 = self.map.plot(eastX, y)
                        landPlot2 = self.map.plot(eastX, y-1)
                        if landPlot1.isWater() or landPlot2.isWater():
                            otherPlot = True
                        else:
                            FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_WEST
        return (x, y, FlowDirection)

    def addRiverFrom(self, x, y, flow, riverID):
        plot = self.map.plot(x, y)
        if self.is_water_for_river(plot):
            return
        eastX = self.eastX(x)
        westX = self.westX(x)
        if self.preventRiversFromCrossing(x, y, flow, riverID):
            return
        plot.setRiverID(riverID)
        if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST) or (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
            plot.setNOfRiver(True, flow)
        else:
            plot.setWOfRiver(True, flow)
        xShift = 0
        yShift = 0
        if flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST:
            xShift = 1
        elif flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST:
            xShift = -1
        elif flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH:
            yShift = -1
        elif flow == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH:
            yShift = 1
        nextX = x + xShift
        nextY = y + yShift
        if nextX >= self.width:
            nextX = 0
        if nextY >= self.height:
            return
        nextPlot = self.map.plot(nextX, nextY)
        if not self.canFlowFrom(plot, nextPlot):
            return
        if plot.getTerrainType() == CyGlobalContext().getInfoTypeForString("TERRAIN_SNOW") and self.dice.get(10, "Stop on ice") > 3:
            return
        flatDesert = (plot.getPlotType() == PlotTypes.PLOT_LAND) and (plot.getTerrainType() == CyGlobalContext().getInfoTypeForString("TERRAIN_DESERT"))
        turnThreshold = 16
        if flatDesert:
            turnThreshold = 18
        turned = False
        northY = y + 1
        southY = y - 1
        if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST) or (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
            if (northY < self.height) and (self.dice.get(20, "branch from north") > turnThreshold):
                if (self.canFlowFrom(plot, self.map.plot(x, northY)) and
                    self.canFlowFrom(self.map.plot(self.eastX(x), y), self.map.plot(self.eastX(x), northY))):
                    turned = True
                    if flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST:
                        self.addRiverFrom(x, y, CardinalDirectionTypes.CARDINALDIRECTION_SOUTH, riverID)
                    else:
                        westPlot = self.map.plot(westX, y)
                        westPlot.setRiverID(riverID)
                        self.addRiverFrom(westX, y, CardinalDirectionTypes.CARDINALDIRECTION_SOUTH, riverID)
            if (not turned) and (southY >= 0) and (self.dice.get(20, "branch from south") > turnThreshold):
                if (self.canFlowFrom(plot, self.map.plot(x, southY)) and
                    self.canFlowFrom(self.map.plot(self.eastX(x), y), self.map.plot(self.eastX(x), southY))):
                    turned = True
                    if flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST:
                        southPlot = self.map.plot(x, y-1)
                        southPlot.setRiverID(riverID)
                        self.addRiverFrom(x, southY, CardinalDirectionTypes.CARDINALDIRECTION_NORTH, riverID)
                    else:
                        westPlot = self.map.plot(westX, southY)
                        westPlot.setRiverID(riverID)
                        self.addRiverFrom(westX, southY, CardinalDirectionTypes.CARDINALDIRECTION_NORTH, riverID)
        else:
            if (self.canFlowFrom(plot, self.map.plot(eastX, y)) and
                self.canFlowFrom(self.map.plot(x, southY), self.map.plot(eastX, y)) and
                (self.dice.get(20, "branch from east") > turnThreshold)):
                turned = True
                if flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH:
                    eastPlot = self.map.plot(eastX, y)
                    eastPlot.setRiverID(riverID)
                    self.addRiverFrom(eastX, y, CardinalDirectionTypes.CARDINALDIRECTION_WEST, riverID)
                else:
                    northEastPlot = self.map.plot(eastX, y+1)
                    northEastPlot.setRiverID(riverID)
                    self.addRiverFrom(eastX, y+1, CardinalDirectionTypes.CARDINALDIRECTION_WEST, riverID)
            if (not turned) and (self.canFlowFrom(plot, self.map.plot(westX, y)) and
                self.canFlowFrom(self.map.plot(x, southY), self.map.plot(westX, southY)) and
                (self.dice.get(20, "branch from west") > turnThreshold)):
                turned = True
                if flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH:
                    self.addRiverFrom(x, y, CardinalDirectionTypes.CARDINALDIRECTION_EAST, riverID)
                else:
                    northPlot = self.map.plot(x, y+1)
                    northPlot.setRiverID(riverID)
                    self.addRiverFrom(x, y+1, CardinalDirectionTypes.CARDINALDIRECTION_EAST, riverID)
        spawnInDesert = (not turned) and flatDesert
        if (self.dice.get(10, "straight river") > self.straightThreshold) or spawnInDesert:
            self.addRiverFrom(nextX, nextY, flow, riverID)
        else:
            if not turned:
                plot = self.map.plot(nextX, nextY)
                if (plot.getPlotType() == PlotTypes.PLOT_LAND) and (self.dice.get(10, "Rivers start in hills") > 3):
                    plot.setPlotType(PlotTypes.PLOT_HILLS, True, True)
                    if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST) or (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
                        if southY > 0:
                            self.map.plot(nextX, southY).setPlotType(PlotTypes.PLOT_HILLS, True, True)
                    else:
                        self.map.plot(eastX, nextY).setPlotType(PlotTypes.PLOT_HILLS, True, True)

    def preventRiversFromCrossing(self, x, y, flow, riverID):
        plot = self.map.plot(x, y)
        eastX = self.eastX(x)
        westX = self.westX(x)
        if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
            if (plot.isNOfRiver()):
                return True
            if (self.map.plot(eastX, y).isNOfRiver()):
                return True
            southPlot = self.map.plot(x, y-1)
            if (southPlot.isWOfRiver() and southPlot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH):
                return True
            if (plot.isWOfRiver() and plot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
                return True
            if (self.map.plot(eastX, y).isWater()):
                return True
            if (self.map.plot(x, y-1).isWater()):
                return True
            if (self.map.plot(eastX, y-1).isWater()):
                return True
        if (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
            if (plot.isNOfRiver()):
                return True
            if (self.map.plot(westX, y).isNOfRiver()):
                return True
            southPlot = self.map.plot(westX, y-1)
            if (southPlot.isWOfRiver() and southPlot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH):
                return True
            westPlot = self.map.plot(westX, y)
            if (westPlot.isWOfRiver() and westPlot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
                return True
            if (self.map.plot(westX, y).isWater()):
                return True
            if (self.map.plot(x, y-1).isWater()):
                return True
            if (self.map.plot(westX, y-1).isWater()):
                return True
        if (flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
            if (plot.isWOfRiver()):
                return True
            eastPlot = self.map.plot(eastX, y)
            if (eastPlot.isNOfRiver() and eastPlot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
                return True
            if (plot.isNOfRiver() and plot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
                return True
            if (self.map.plot(x, y-1).isWOfRiver()):
                return True
            if (self.map.plot(x, y-1).isWater()):
                return True
            if (self.map.plot(x+1, y).isWater()):
                return True
            if (self.map.plot(x+1, y-1).isWater()):
                return True
        if (flow == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH):
            if (plot.isWOfRiver()):
                return True
            eastPlot = self.map.plot(eastX, y+1)
            if (eastPlot.isNOfRiver() and eastPlot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
                return True
            northPlot = self.map.plot(x, y+1)
            if (northPlot.isNOfRiver() and northPlot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
                return True
            if (self.map.plot(x, y+1).isWOfRiver()):
                return True
            if (self.map.plot(x, y+1).isWater()):
                return True
            if (self.map.plot(x+1, y).isWater()):
                return True
            if (self.map.plot(x+1, y+1).isWater()):
                return True
        return False

    def westX(self, x):
        westX = x - 1
        if (westX < 0):
            westX = self.width
        return westX

    def eastX(self, x):
        eastX = x + 1
        if (eastX >= self.width):
            eastX = 0
        return eastX
        
def addNorthFlowRiver(rect, min_water_area=5):
    """
    Creates a straight north-flowing river starting in the given rectangle.
    Skips over small lakes (area < min_water_area) and also skips tiles that have
    water directly east of them to avoid visual glitches.
    """
    map = CyMap()
    gc = CyGlobalContext()
    dice = gc.getGame().getMapRand()
    iW = map.getGridWidth()
    iH = map.getGridHeight()

    west, south, width, height = rect
    west_x = int(iW * west)
    east_x = int(iW * (west + width))
    south_y = int(iH * south)
    north_y = int(iH * (south + height))

    # Find a random land tile on the bottom row (south_y) that is eligible (no existing river)
    eligible = []
    for x in range(west_x, east_x + 1):
        pPlot = map.plot(x, south_y)
        if not pPlot.isWater() and pPlot.getRiverID() == -1:
            eligible.append(x)
    if eligible:
        start_x = eligible[dice.get(len(eligible), "Nile X")]
    else:
        # Fallback: any land tile on bottom row (even if it already has a river)
        for x in range(west_x, east_x + 1):
            pPlot = map.plot(x, south_y)
            if not pPlot.isWater():
                start_x = x
                break
    if start_x is None:
        return   # no land on bottom row

    start_y = south_y

    # Create river ID
    riverID = gc.getMap().getNextRiverID()
    gc.getMap().incrementNextRiverID()

    # Build the river flowing north
    x, y = start_x, start_y
    pPlot = map.plot(x, y)
    pPlot.setRiverID(riverID)
    pPlot.setWOfRiver(True, CardinalDirectionTypes.CARDINALDIRECTION_NORTH)

    while y < iH - 1:
        y += 1
        pNorth = map.plot(x, y)

        # If we hit water, decide whether to stop or skip
        if pNorth.isWater():
            area_id = pNorth.getArea()
            if area_id != -1:
                area = map.getArea(area_id)
                if area.getNumTiles() >= min_water_area:
                    # Large water body – stop the river
                    break
                else:
                    # Small water body – skip over it: continue north until we find land
                    while y < iH - 1:
                        y += 1
                        pNorth = map.plot(x, y)
                        if not pNorth.isWater():
                            # Found land after the lake
                            # Check lateral water on this new land tile
                            if x+1 < iW and map.plot(x+1, y).isWater():
                                continue
                            if x-1 >= 0 and map.plot(x-1, y).isWater():
                                continue
                            if pNorth.getRiverID() == -1:
                                pNorth.setRiverID(riverID)
                                pNorth.setWOfRiver(True, CardinalDirectionTypes.CARDINALDIRECTION_NORTH)
                            break
                    else:
                        # Reached top without finding land – stop
                        break
                    # Continue the outer loop (y is now the land tile after the lake)
                    continue
        else:
            # Check if there is water directly east of this tile
            if x+1 < iW:
                east_tile = map.plot(x+1, y)  
            else:
                None
            skip = False
            if east_tile and east_tile.isWater():
                area_id = east_tile.getArea()
                if area_id != -1:
                    area = map.getArea(area_id)
                    if area.getNumTiles() < min_water_area:
                        skip = True
            if skip:
                continue   # do not place river here

            if pNorth.getRiverID() != -1:
                break

            pNorth.setRiverID(riverID)
            pNorth.setWOfRiver(True, CardinalDirectionTypes.CARDINALDIRECTION_NORTH)
        
def addRivers():
    # Eliminate rivers in Egypt to clean for Nile (west, south, width, height)
    EgyptCleanRegion = [(0.80, 0.0, 0.15, 0.28)]
    # Reduce rivers in Sahara rectangle (west, south, width, height)
    saharaRegion = [(0.16, 0.0, 0.56, 0.169)]
    riverGen = RiverGenerator(
        river_density=1.5,
        exclude_rects=EgyptCleanRegion,           # rivers here will be removed
        reduce_rects=saharaRegion,        # rivers have reduced chance to flow here
        survival_chance=20            # 20% of rivers will survive the Sahara
    )
    riverGen.seedRivers()
    # Add the Nile after the main generation
    nile_rect = (0.85, 0.0, 0.035, 0.28)
    addNorthFlowRiver(nile_rect, min_water_area=5)
    

# -----------------------------------------------------------------------------
# Coast distance
# -----------------------------------------------------------------------------
def expandCoastToTwoTiles():
    """Convert all water tiles within 2 tiles of land to coast terrain."""
    map = CyMap()
    gc = CyGlobalContext()
    iW = map.getGridWidth()
    iH = map.getGridHeight()
    coast_id = gc.getInfoTypeForString("TERRAIN_COAST")

    # Collect all land plots
    land_plots = []
    for x in range(iW):
        for y in range(iH):
            if not map.plot(x, y).isWater():
                land_plots.append((x, y))

    # Mark water plots within Manhattan distance <= 2 of any land
    coast_plots = set()
    for lx, ly in land_plots:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if abs(dx) + abs(dy) <= 2:   # Manhattan distance
                    nx, ny = lx + dx, ly + dy
                    if 0 <= nx < iW and 0 <= ny < iH:
                        pPlot = map.plot(nx, ny)
                        if pPlot.isWater():
                            coast_plots.add((nx, ny))

    # Apply coast terrain
    for x, y in coast_plots:
        map.plot(x, y).setTerrainType(coast_id, True, True)
        

# -----------------------------------------------------------------------------
# Starting plot
# -----------------------------------------------------------------------------

_START_PLOT_MAP = None

def minStartingDistanceModifier():
    return 0

def findStartingPlot(argsList):
    [playerID] = argsList
    global _START_PLOT_MAP

    if _START_PLOT_MAP is None:
        _START_PLOT_MAP = _assign_all_starting_plots()

    return _START_PLOT_MAP.get(playerID, -1)

def _is_real_coast(pPlot, min_water_size=5):
    """
    Checks if a land plot is adjacent to a water body of at least min_water_size.
    This prevents players from being 'Coastal' next to a 1-tile desert pond.
    """
    if pPlot.isWater(): return False
    map = CyMap()
    # Check all 8 directions (including diagonals) for ocean-sized water
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == 0 and dy == 0: continue
            adj = map.plot(pPlot.getX() + dx, pPlot.getY() + dy)
            if adj and not adj.isNone():
                if adj.isWater():
                    area = adj.area()
                    if area and area.getNumTiles() >= min_water_size:
                        return True
    return False

def _assign_all_starting_plots():
    print "PY: Assigning all starting plots..."
    map = CyMap()
    gc = CyGlobalContext()
    dice = gc.getGame().getMapRand()
    # Force a recalculation of areas to ensure 'isWater' and 'area size' are accurate
    map.recalculateAreas()
    
    start_option = map.getCustomMapOption(1)

    final_assignments = {} 
    assigned_coords = []   
    unassigned_players = [] 

    SPAWN_REGIONS = {
        "Italy":    (0.38, 0.69, 0.07, 0.16),
        "Greece":   (0.61, 0.40, 0.09, 0.16),
        "Levant":   (0.93, 0.36, 0.06, 0.24),
        "Tunisia":  (0.34, 0.25, 0.10, 0.19),
        "Spain":    (0.12, 0.40, 0.09, 0.29),
        # Secondary
        "Gaul":     (0.16, 0.80, 0.14, 0.16),
        "Dacia":    (0.64, 0.83, 0.12, 0.13),
        "AsiaMinor":    (0.74, 0.50, 0.13, 0.13),
        "Egypt":    (0.85, 0.05, 0.035, 0.23),
        "Morocco":  (0.01, 0.14, 0.10, 0.13),
        # Tertiary
        "Portugal": (0.00, 0.40, 0.06, 0.35),
        "Sicilies": (0.47, 0.46, 0.08, 0.19),
        "Pannonia": (0.51, 0.83, 0.08, 0.13),
        "Epirus": (0.56, 0.66, 0.06, 0.13),
        "Bosporus": (0.70, 0.66, 0.11, 0.16),
        "Pontus":   (0.85, 0.79, 0.14, 0.13),
        "Cyrenaica":   (0.60, 0.14, 0.12, 0.10),
        "Algeria":   (0.17, 0.26, 0.11, 0.13),
    }

    primary_regions = ["Italy", "Greece", "Tunisia", "Levant", "Spain"]
    secondary_regions = ["Gaul", "Dacia", "AsiaMinor", "Egypt","Morocco",]
    tertiary_regions  = ["Portugal", "Sicilies", "Pannonia", "Epirus", "Bosporus", "Pontus", "Cyrenaica", "Algeria"]

    civ_mapping = {
        # for Classical games
        "CIVILIZATION_ROME":      "Italy",
        "CIVILIZATION_GREECE":    "Greece",
        "CIVILIZATION_CARTHAGE":  "Tunisia",
        "CIVILIZATION_PERSIA":    "Levant",
        "CIVILIZATION_SPAIN":     "Spain",
        #
        "CIVILIZATION_CELT":      "Gaul",
        "CIVILIZATION_MONGOL":    "Dacia",  # Thracians, Scythians, Huns ...
        "CIVILIZATION_BABYLON":   "AsiaMinor",  # Stand-in for Lydians, Phrygians, Trojans, etc.
        "CIVILIZATION_EGYPT":     "Egypt",
        "CIVILIZATION_MALI":      "Morocco",
        # for medieval games
        "CIVILIZATION_PORTUGAL":  "Portugal",
        "CIVILIZATION_VIKING":    "Sicilies",   # Norman Kingdoms of Sicily
        "CIVILIZATION_FRANCE":    "Gaul",
        "CIVILIZATION_HOLY_ROMAN":"Pannonia",   # Austria-Hungary
        "CIVILIZATION_BYZANTIUM": "Bosporus",
        "CIVILIZATION_OTTOMAN":   "AsiaMinor",
        "CIVILIZATION_ARABIA":    "Levant",
    }

    all_players = []
    for i in range(gc.getMAX_CIV_PLAYERS()):
        player = gc.getPlayer(i)
        if player.isEverAlive():
            all_players.append(i)
    
    if start_option == 2: # Historical (Fixed)
        used_regions = set()
        for playerID in all_players:
            civ_str = gc.getCivilizationInfo(gc.getPlayer(playerID).getCivilizationType()).getType()
            region_name = civ_mapping.get(civ_str)
            
            if region_name and region_name not in used_regions:
                rect = SPAWN_REGIONS[region_name]
                plot_index = _find_plot_in_rect(rect, "Fixed: " + region_name)
                
                if plot_index != -1:
                    final_assignments[playerID] = plot_index
                    print "MAP DEBUG: Fixed Start - %s assigned to %s" % (civ_str, region_name)
                    p = map.plotByIndex(plot_index)
                    assigned_coords.append((p.getX(), p.getY()))
                    used_regions.add(region_name)
                    continue 
            unassigned_players.append(playerID)

        if unassigned_players:
            # SHUFFLE leftover players so they don't always get regions in ID order
            unassigned_players = _synced_shuffle(dice, unassigned_players)
            available_regions = [r for r in (primary_regions + secondary_regions + tertiary_regions) if r not in used_regions]
            available_regions = _synced_shuffle(dice, available_regions)
            
            still_unassigned = []
            for playerID in unassigned_players:
                civ_str = gc.getCivilizationInfo(gc.getPlayer(playerID).getCivilizationType()).getType()
                if available_regions:
                    fallback_region = available_regions.pop(0)
                    plot_index = _find_plot_in_rect(SPAWN_REGIONS[fallback_region], "Fixed-Shuffle: " + fallback_region)
                    if plot_index != -1:
                        final_assignments[playerID] = plot_index
                        print "MAP DEBUG: Fixed-Shuffle Fallback - %s assigned to %s" % (civ_str, fallback_region)
                        p = map.plotByIndex(plot_index)
                        assigned_coords.append((p.getX(), p.getY()))
                    else:
                        still_unassigned.append(playerID)
                else:
                    still_unassigned.append(playerID)
            unassigned_players = still_unassigned

    elif start_option == 1: # Historical (Shuffle)
        shuffled_players = _synced_shuffle(dice, all_players)
        p_list = _synced_shuffle(dice, primary_regions[:])
        s_list = _synced_shuffle(dice, secondary_regions[:])
        t_list = _synced_shuffle(dice, tertiary_regions[:])
        all_region_names = p_list + s_list + t_list

        player_idx = 0
        for region_name in all_region_names:
            if player_idx >= len(shuffled_players): break
            playerID = shuffled_players[player_idx]
            plot_index = _find_plot_in_rect(SPAWN_REGIONS[region_name], "Shuffle: " + region_name)
            if plot_index != -1:
                final_assignments[playerID] = plot_index
                civ_str = gc.getCivilizationInfo(gc.getPlayer(playerID).getCivilizationType()).getType()
                print "MAP DEBUG: Shuffle Start - %s assigned to %s" % (civ_str, region_name)
                p = map.plotByIndex(plot_index)
                assigned_coords.append((p.getX(), p.getY()))
                player_idx += 1
        unassigned_players = shuffled_players[player_idx:]

    else: # Vanilla
        unassigned_players = all_players[:]

    if unassigned_players:
        for playerID in unassigned_players:
            plot_index = _fallback_start_placement(playerID, assigned_coords)
            if plot_index != -1:
                final_assignments[playerID] = plot_index
                civ_str = gc.getCivilizationInfo(gc.getPlayer(playerID).getCivilizationType()).getType()
                p = map.plotByIndex(plot_index)
                # Corrected: generic fallback doesn't have a region_name
                print "MAP DEBUG: Generic Fallback - %s assigned to (%d, %d)" % (civ_str, p.getX(), p.getY())
                assigned_coords.append((p.getX(), p.getY()))
                
    return final_assignments

def _synced_shuffle(dice, lst):
    result = lst[:]
    for i in range(len(result) - 1, 0, -1):
        j = dice.get(i + 1, "Synced Shuffle")
        result[i], result[j] = result[j], result[i]
    return result

def _find_plot_in_rect(rect, region_name, min_landmass=4):
    map = CyMap()
    dice = CyGlobalContext().getGame().getMapRand()
    iW, iH = map.getGridWidth(), map.getGridHeight()

    west, south, width, height = rect
    # Ensure clamping is inside bounds [0, W-1]
    west_x = max(0, int(iW * west))
    east_x = min(iW - 1, int(iW * (west + width)))
    south_y = max(0, int(iH * south))
    north_y = min(iH - 1, int(iH * (south + height)))

    eligible = []
    for x in range(west_x, east_x + 1):
        for y in range(south_y, north_y + 1):
            pPlot = map.plot(x, y)
            # HARD CHECK: Must not be water, must not be peak
            if pPlot and not pPlot.isWater() and not pPlot.isPeak():
                area = pPlot.area()
                if area and area.getNumTiles() >= min_landmass:
                    eligible.append(map.plotNum(x, y))
    
    if not eligible: return -1
    return eligible[dice.get(len(eligible), "Historical start")]

def _fallback_start_placement(playerID, existing_coords):
    map = CyMap()
    gc = CyGlobalContext()
    dice = gc.getGame().getMapRand()
    player = gc.getPlayer(playerID)
    player.AI_updateFoundValues(True)

    COASTAL_START_BIAS = 1.35 # Increased slightly

    # Only consider the largest landmass for fallback players
    best_area = map.findBiggestArea(False)
    if not best_area: return -1

    iW, iH = map.getGridWidth(), map.getGridHeight()
    min_dist = 7
    if map.getWorldSize() >= WorldSizeTypes.WORLDSIZE_LARGE: min_dist = 9

    candidates = []
    for x in range(iW):
        for y in range(iH):
            pPlot = map.plot(x, y)
            
            # HARD CHECK: No Water, No Peaks, must be on Biggest Area
            if not pPlot or pPlot.isWater() or pPlot.isPeak(): continue
            if pPlot.getArea() != best_area.getID(): continue

            is_too_close = False
            for (ax, ay) in existing_coords:
                if (abs(x - ax) + abs(y - ay)) < min_dist:
                    is_too_close = True
                    break
            if is_too_close: continue

            val = pPlot.getFoundValue(playerID)
            if val > 0:
                # Use the new "Real Coast" check (adjacent to water body >= 5 tiles)
                if _is_real_coast(pPlot, 5):
                    val *= COASTAL_START_BIAS
                candidates.append((val, map.plotNum(x, y)))

    if not candidates:
        # Final emergency fallback if the logic above is too restrictive
        return CvMapGeneratorUtil.findStartingPlot(playerID)

    candidates.sort(key=lambda item: -item[0])
    num_best_choices = min(5, len(candidates))
    return candidates[dice.get(num_best_choices, "Fallback Start Choice")][1]

# -----------------------------------------------------------------------------
# Normalization overrides
# -----------------------------------------------------------------------------
def normalizeAddRiver():
    return None

def normalizeRemovePeaks():
    """
    Remove peaks only from the 1-tile radius of each player's starting plot.
    This overrides the default peak removal that could strip too many peaks.
    """
    map = CyMap()
    gc = CyGlobalContext()
    iW = map.getGridWidth()
    iH = map.getGridHeight()

    # Collect all starting plots
    starts = []
    for i in range(gc.getMAX_CIV_PLAYERS()):
        player = gc.getPlayer(i)
        if player.isEverAlive():
            start_plot = player.getStartingPlot()
            if start_plot:
                starts.append((start_plot.getX(), start_plot.getY()))

    # For each start, look at plots within Chebyshev distance <= 1 (3x3 area)
    for sx, sy in starts:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                x = sx + dx
                y = sy + dy
                if 0 <= x < iW and 0 <= y < iH:
                    pPlot = map.plot(x, y)
                    if pPlot.getPlotType() == PlotTypes.PLOT_PEAK:
                        # Convert to hills
                        pPlot.setPlotType(PlotTypes.PLOT_HILLS, True, True)

def normalizeAddGoodTerrain():
    return None

def normalizeRemoveBadTerrain():
    return None

def normalizeRemoveBadFeatures():
    return None

def normalizeAddFoodBonuses():
    return None

def normalizeAddExtras():
    #CyPythonMgr().allowDefaultImpl() # disable default nomalizer
    addCustomResources() # custom Resource Generator

# -----------------------------------------------------------------------------
# Custom resource addition – Main entry point for all  resource handling
# -----------------------------------------------------------------------------

def addCustomResources():
    map = CyMap()
    gc = CyGlobalContext()
    dice = gc.getGame().getMapRand()
    iW = map.getGridWidth()
    iH = map.getGridHeight()
    option = CyMap().getCustomMapOption(0)

    rm = ResourceManager(map, gc, dice, iW, iH)

    # 1. Strategic resources: check_existence=True ensures we only add if one isn't already there
    strategic_list = ["BONUS_COPPER", "BONUS_IRON", "BONUS_HORSE"]
    rm.place_bonuses_near_players(strategic_list, count=1, min_dist=2, max_dist=4, check_existence=True, force_terrain=True)

    # 2. Food resources: check_existence=True ensures we don't crowd the start if food is already there
    food_list = ["BONUS_WHEAT", "BONUS_RICE", "BONUS_COW", "BONUS_SHEEP", "BONUS_PIG", "BONUS_DEER", "BONUS_FISH", "BONUS_CLAM", "BONUS_CRAB"]
    rm.place_bonuses_near_players(food_list, count=1, min_dist=1, max_dist=2, check_existence=True, force_terrain=True)
    
    if option == 1:  # Semi-historical
        
        # 3. Resource swaps
        swap_rules = [
            ("BONUS_IVORY", None, 0.4),          # remove ivory north of 40% height
            ("BONUS_CORN",   "BONUS_COW"),        # 
            ("BONUS_SPICES", "BONUS_WINE"),       # 
            ("BONUS_SILK",   "BONUS_FUR", 0.5),   # silk north of 50% becomes fur
            ("BONUS_SILK",   "BONUS_DYE"),        # Remaining silk becomes Dye
            ("BONUS_BANANA", None),      # 
            ("BONUS_SUGAR",  None),      # 
        ]
        rm.swap_resources(swap_rules, clear_feature=False)

        # 4. Region-specific resources
        region_specs = [
            {
                "name": "Egypt",
                "rect": (0.85, 0.05, 0.035, 0.284),
                "bonuses": [
                    ("BONUS_INCENSE", 1, False),
                    ("BONUS_GOLD", 1, False),
                    ("BONUS_STONE", 1, False),
                ]
            },
            {
                "name": "Levant",
                "rect": (0.930, 0.237, 0.066, 0.406),
                "bonuses": [
                    ("BONUS_WHEAT", 1, False),
                    ("BONUS_SILK", 2, False),
                    ("BONUS_DYE", 2, True), 
                    ("BONUS_SPICES", 2, True),
                    ("BONUS_INCENSE", 1, False),
                ]
            },
            {
                "name": "Italy",
                "rect": (0.37, 0.63, 0.10, 0.249),
                "bonuses": [
                    ("BONUS_WINE", 1, False),
                    ("BONUS_MARBLE", 1, False),
                ]
            },
            {
                "name": "Greece",
                "rect": (0.61, 0.35, 0.11, 0.222),
                "bonuses": [
                    ("BONUS_SHEEP", 1, False),
                    ("BONUS_WINE", 1, False),
                    ("BONUS_FISH", 1, False),
                    ("BONUS_MARBLE", 1, False),
                ]
            },
            {
                "name": "Tunisia",
                "rect": (0.35, 0.17, 0.08, 0.269),
                "bonuses": [
                    ("BONUS_IVORY", 1, False),
                    ("BONUS_MARBLE", 1, False),
                ]
            },
            {
                "name": "Iberia-Gaul",
                "rect": (0.0, 0.52, 0.27, 0.484),
                "bonuses": [
                    ("BONUS_GEMS", 2, True), 
                    ("BONUS_SILVER", 1, False),
                ]
            },
            {
                "name": "Cyrenaica",
                "rect": (0.60, 0.10, 0.10, 0.13),
                "bonuses": [
                    ("BONUS_WINE", 1, True),
                    ("BONUS_FISH", 1, False),
                ]
            },
        ]
        rm.add_region_specific(region_specs, force_placement=True)

class ResourceManager:
    """Manages custom resource placement for the Mediterranean map script."""
    def __init__(self, map, gc, dice, iW, iH):
        self.map = map
        self.gc = gc
        self.dice = dice
        self.iW = iW
        self.iH = iH
        self._cache = {}   
        
        self.world_size = self.map.getWorldSize()
        self.size_multiplier = {
            WorldSizeTypes.WORLDSIZE_DUEL:     1,
            WorldSizeTypes.WORLDSIZE_TINY:     1,
            WorldSizeTypes.WORLDSIZE_SMALL:    1,
            WorldSizeTypes.WORLDSIZE_STANDARD: 1,
            WorldSizeTypes.WORLDSIZE_LARGE:    1.5,
            WorldSizeTypes.WORLDSIZE_HUGE:     2,
        }

    def _bonus_id(self, name):
        if name in self._cache: return self._cache[name]
        bid = self.gc.getInfoTypeForString(name)
        self._cache[name] = bid
        return bid

    def place_bonuses_near_players(self, bonus_list, count=1, min_dist=2, max_dist=5, check_existence=False, force_placement=True, force_terrain=False):
        """
        Consolidated logic for strategic and food placement. 
        Always avoids placing directly on a player's starting plot.
        force_terrain: If True, will convert terrain to Plains if no valid land is found for the bonus.
        """
        water_bonus_names = ("BONUS_FISH", "BONUS_CLAM", "BONUS_CRAB", "BONUS_WHALE")
        ids = []
        is_water_bonus = []
        for b in bonus_list:
            ids.append(self._bonus_id(b))
            is_water_bonus.append(b in water_bonus_names)

        # Get terrain type for forcing
        iPlains = self.gc.getInfoTypeForString("TERRAIN_PLAINS")

        players = []
        for i in range(self.gc.getMAX_CIV_PLAYERS()):
            player = self.gc.getPlayer(i)
            if player.isEverAlive():
                pStart = player.getStartingPlot()
                if pStart and not pStart.isNone():
                    players.append((player.getID(), pStart.getX(), pStart.getY()))

        for (pid, sx, sy) in players:
            if check_existence:
                already_has = False
                for dx in range(-max_dist, max_dist+1):
                    for dy in range(-max_dist, max_dist+1):
                        if abs(dx) + abs(dy) > max_dist: continue
                        nx, ny = sx + dx, sy + dy
                        if 0 <= nx < self.iW and 0 <= ny < self.iH:
                            if self.map.plot(nx, ny).getBonusType(-1) in ids:
                                already_has = True
                                break
                    if already_has: break
                if already_has: continue

            placed = 0
            attempts = 0
            while placed < count and attempts < 30:
                attempts += 1
                b_idx = self.dice.get(len(ids), "Bonus Choice")
                chosen_id = ids[b_idx]
                is_water = is_water_bonus[b_idx]

                eligible = []
                fallback = []
                terrain_fallback = []
                
                for dx in range(-max_dist, max_dist+1):
                    for dy in range(-max_dist, max_dist+1):
                        d = abs(dx) + abs(dy)
                        if d < min_dist or d > max_dist: continue
                        nx, ny = sx + dx, sy + dy
                        if 0 <= nx < self.iW and 0 <= ny < self.iH:
                            pPlot = self.map.plot(nx, ny)
                            
                            # CRITICAL: Do not place on start plot
                            if pPlot.isStartingPlot(): continue
                            
                            if pPlot.getBonusType(-1) == -1:
                                # Tier 1: Natural placement
                                if pPlot.canHaveBonus(chosen_id, True):
                                    eligible.append((nx, ny))
                                # Tier 2: Any non-peak land (if enabled)
                                elif force_placement and not is_water:
                                    if not pPlot.isWater() and pPlot.getPlotType() != PlotTypes.PLOT_PEAK:
                                        fallback.append((nx, ny))
                                # Tier 3: Terrain override (if enabled)
                                elif force_terrain and not is_water:
                                    if not pPlot.isWater() and pPlot.getPlotType() != PlotTypes.PLOT_PEAK:
                                        terrain_fallback.append((nx, ny))
                
                target = None
                if eligible:
                    target = eligible[self.dice.get(len(eligible), "B")]
                elif fallback:
                    target = fallback[self.dice.get(len(fallback), "F")]
                elif terrain_fallback:
                    target = terrain_fallback[self.dice.get(len(terrain_fallback), "T")]
                    # Convert terrain to Plains to ensure the bonus works correctly
                    self.map.plot(target[0], target[1]).setTerrainType(iPlains, True, True)
                
                if target:
                    self.map.plot(target[0], target[1]).setBonusType(chosen_id)
                    placed += 1

    def swap_resources(self, swap_rules, clear_feature=False):
        for rule in swap_rules:
            old_name = rule[0]
            new_name = rule[1]
            if len(rule) > 2:
                min_y_fraction = rule[2]
            else:
                min_y_fraction = 0.0
            
            old_id = self._bonus_id(old_name)
            y_thresh = int(self.iH * min_y_fraction)

            for i in range(self.map.numPlots()):
                pPlot = self.map.plotByIndex(i)
                if pPlot.getY() >= y_thresh and pPlot.getBonusType(-1) == old_id:
                    if new_name:
                        pPlot.setBonusType(self._bonus_id(new_name))
                    else:
                        pPlot.setBonusType(-1)
                    
                    if clear_feature:
                        pPlot.setFeatureType(FeatureTypes.NO_FEATURE, -1)

    def add_region_specific(self, region_specs, force_placement=True):
        """
        Place bonuses in specified rectangular regions.
        region_specs: list of dicts with keys:
            'rect': (west, south, width, height) – fractional coordinates
            'bonuses': list of (bonus_name, count) or (bonus_name, count, clear_feature)
        If force_placement is True, when no eligible tile is found (using canHaveBonus),
        it will place the bonus on any non-peak land tile in the region.
        Bonus counts are scaled by map size (1x for Duel-Standard, 1.5x for Large, 2x for Huge).
        """
        multiplier = self.size_multiplier[self.world_size]
        for region in region_specs:
            west, south, width, height = region["rect"]
            west_x, east_x = int(self.iW * west), int(self.iW * (west + width))
            south_y, north_y = int(self.iH * south), int(self.iH * (south + height))

            for bonus_entry in region["bonuses"]:
                scaled_count = int(bonus_entry[1] * multiplier)
                if scaled_count == 0: continue
                bonus_id = self._bonus_id(bonus_entry[0])
                
                if len(bonus_entry) > 2:
                    clear_feat = bonus_entry[2]
                else:
                    clear_feat = False

                eligible = []
                fallback = []
                for x in range(max(0, west_x), min(self.iW, east_x + 1)):
                    for y in range(max(0, south_y), min(self.iH, north_y + 1)):
                        pPlot = self.map.plot(x, y)
                        if pPlot.isStartingPlot(): continue
                        if pPlot.getBonusType(-1) == -1:
                            if pPlot.canHaveBonus(bonus_id, True):
                                eligible.append((x, y))
                            elif force_placement and not pPlot.isWater() and pPlot.getPlotType() != PlotTypes.PLOT_PEAK:
                                fallback.append((x, y))

                placed = 0
                for _ in range(scaled_count):
                    choice = None
                    if eligible:
                        choice = eligible.pop(self.dice.get(len(eligible), "R"))
                    elif fallback:
                        choice = fallback.pop(self.dice.get(len(fallback), "RF"))
                    
                    if choice:
                        p = self.map.plot(choice[0], choice[1])
                        p.setBonusType(bonus_id)
                        if clear_feat:
                            p.setFeatureType(FeatureTypes.NO_FEATURE, -1)
                        placed += 1