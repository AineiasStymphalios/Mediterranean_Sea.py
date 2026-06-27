from CvPythonExtensions import *
import CvUtil
import CvMapGeneratorUtil
from CvMapGeneratorUtil import MultilayeredFractal
from CvMapGeneratorUtil import TerrainGenerator
from CvMapGeneratorUtil import FeatureGenerator
import math

'''
##############################################################################
GEOMETRIC MULTIFRACTAL NOTES

This mapscript was based on Earth2.py.

Below are its main features:
- GeometricMultiFractal Genrator: an improved MultilayeredFractal generator
	- Takes matrix inputs
	- More property inputs for regions
	- Allows Rectangular, Elliptical, and Triangular fractal masks with rotation.
- Custom Climate Generator
	- Generates terrain and features based on custom-placed temperature and moisture vectors.
- Bonus generator
	- Rewrote Vanilla's strategic and food bonus additions to starting plots
	- Option: Historical resource placement
		- Swaps / removes ahistoric resources
		- Region specific bonus placement
- Custom River / Waterway Generator
	- Allows generation of rivers and waterways through map coordinates.
- "Historical" Starting Locations
	- Allows one to force specific civilizations to spawn within a specified region

- AineiasStymph, April 29, 2026
##############################################################################
'''


	
def getDescription():
	desc = "A procedurally generated Chinese Central Plains map, inspired by the Chinese Unification mod-scenario in Warlords."
	desc += "Features options for geography and climate."
	return desc

def isAdvancedMap():
	"This map should show up in simple mode"
	return 0


# -----------------------------------------------------------------------------
# Custom Options
# -----------------------------------------------------------------------------
def getNumCustomMapOptions():
	return 10

def getCustomMapOptionName(argsList):
	index = argsList[0]
	names = [
		"World Wrap",
		"Suez",
		"Bosporos",
		"Gibraltar",
		"Peak Reduction",
		"Reduce Coastal Peaks",
		"Historical Resources",
		"Land Food Across Map",
		"Minimum land food at start",
		"Start Options"
	]
	if index < len(names):
		return names[index]
	return ""

def getNumCustomMapOptionValues(argsList):
	index = argsList[0]
	if index == 0: return 3 # World Wrap
	if index == 1: return 2 # Suez: Closed, Open
	if index == 2: return 2 # Bosporos: Closed, Open
	if index == 3: return 2 # Gibraltar: Closed, Open
	if index == 4: return 3 # Peaks: Flatten Alpine, Highland, Disabled
	if index == 5: return 3 # Coastal Peaks: Disabled, Reduce 50%, Reduce 100%
	if index == 6: return 2 # Historical Resources: Yes/No
	if index == 7: return 4 # Map Food: Disabled, 4x4, 5x5, 6x6
	if index == 8: return 3 # Start Food: 0, 1, 2
	if index == 9: return 2 # Start Options: Default, Fixed
	return 0

def getCustomMapOptionDescAt(argsList):
	index = argsList[0]
	selection = argsList[1]
	if index == 0: # World Wrap
		if selection == 0: return "Flat"
		elif selection == 1: return "Cylindrical"
		return "Toroidal"
	if index == 1: # Suez
		if selection == 0: return "Closed (Historical)"
		return "Open"
	if index == 2: # Bosporos
		if selection == 0: return "Closed (Historical)"
		return "Open"
	if index == 3: # Gibraltar
		if selection == 0: return "Closed"
		return "Open (Historical)"
	if index == 4: # Peaks
		if selection == 0: return "Flatten Alpine Regions"
		if selection == 1: return "Flatten Alpine and Highland Regions"
		return "Disabled (Allow all)"
	if index == 5: # Coastal Peaks
		if selection == 0: return "Disabled"
		elif selection == 1: return "Reduce 50%"
		return "Reduce 100%"
	if index == 6: # Historical Resources
		if selection == 0: return "Vanilla Distribution"
		return "Historical Placement"
	if index == 7: # Map Food
		if selection == 0: return "Disabled"
		elif selection == 1: return "1 per 4x4 tiles"
		elif selection == 2: return "1 per 5x5 tiles"
		return "1 per 6x6 tiles"
	if index == 8: # Start Food
		if selection == 0: return "Disabled"
		if selection == 1: return "At least 1"
		return "At least 2"
	if index == 9: # Start Options
		if selection == 0: return "Vanilla"
		return "Historical"
	return ""

def getCustomMapOptionDefault(argsList):
	index = argsList[0]
	if index == 0: return 0 # World Wrap: Flat
	if index == 1: return 0 # Suez: Closed
	if index == 2: return 0 # Bosporos: Closed
	if index == 3: return 1 # Gibraltar: Open
	if index == 4: return 2 # Peak Reduction: Disabled
	if index == 5: return 0 # Coastal Peaks: Disabled
	if index == 6: return 1 # Historical Resources
	if index == 7: return 3 # Map Food
	if index == 8: return 1 # 1 Food at starts
	if index == 9: return 1 # starts
	return 0

# -----------------------------------------------------------------------------
# Map Properties
# -----------------------------------------------------------------------------

def getGridSize(argsList):
	# Sse map sizes here. Multiply each dimension by 4x to get map width and height.
	grid_sizes = {
		WorldSizeTypes.WORLDSIZE_DUEL:		(7, 4),
		WorldSizeTypes.WORLDSIZE_TINY:		(8, 5),
		WorldSizeTypes.WORLDSIZE_SMALL:		(10, 6),
		WorldSizeTypes.WORLDSIZE_STANDARD:	(12, 7),
		WorldSizeTypes.WORLDSIZE_LARGE:		(14, 8),
		WorldSizeTypes.WORLDSIZE_HUGE:		(15, 9),
	}
	if argsList[0] == -1:
		return []
	return grid_sizes[argsList[0]]

def isSeaLevelMap():
	return 0

def getWrapX():
	map = CyMap()
	return (map.getCustomMapOption(0) == 1 or map.getCustomMapOption(0) == 2)

def getWrapY():
	map = CyMap()
	return (map.getCustomMapOption(0) == 2)

def isClimateMap():
	return 1

def getClimate():
	"""This is now ignored by the engine because isClimateMap is 1, 
	but we keep it for safety."""
	return ClimateTypes.CLIMATE_TEMPERATE

_all_start_coords = [] # Store player start coords
def beforeGeneration():
	"""
	Official Civ4 hook called before map generation starts.
	Guaranteed to run on Map Regeneration and New Games.
	"""
	# Clear the starting plot cache
	global _START_PLOT_MAP
	_START_PLOT_MAP = None
	
	# RESET CLIMATE GLOBALS HERE to prevent settings from "sticking"
	global _CLIMATE_ENGINE
	_CLIMATE_ENGINE = None
	
	return None

_DEBUG_REGIONS = [] # Global to store regions for sign placement

def _add_region_signs(region_data):
	"""Adds map signs to the center of each fractal region."""
	m = CyMap()
	engine = CyEngine()
	iW = m.getGridWidth()
	iH = m.getGridHeight()
	
	for data in region_data:
		name = data[0]
		cx = data[2]
		cy = data[3]
		
		# Convert fractional center to plot coordinates
		iX = int(iW * cx)
		iY = int(iH * cy)
		
		pPlot = m.plot(iX, iY)
		if pPlot and not pPlot.isNone():
			# -1 makes the sign visible to all players (global)
			engine.addSign(pPlot, -1, str(name))



# -----------------------------------------------------------------------------
# GeometricMultiFractal Generator
# -----------------------------------------------------------------------------
class GeometricMultiFractal(CvMapGeneratorUtil.MultilayeredFractal):
	"""
	Fractal generator supporting geometric masking and rotation.
	Shapes: RECT, ELLIPSE, ISOTRI.
	"""
	def getReducedEdgeWaterThreshold(self, r_type, water_prc, iWaterThreshold, iWaterThresholds,
	                                 rx, ry, invRxSq, invRySq, radius_x, radius_y,
	                                 height_tiles, b_dist, v_dist, max_rx):
		fCenterInner = 0.45
		fCenterOuter = 0.65
		fCenterMultiplier = 2.0
		fEdgeInner = 0.80
		fEdgeOuter = 1.00
		fEdgeMultiplier = 1.0
		fIsotriEdgeBand = 0.20
		edgeStrength = 0.0
		centerStrength = 0.0
		shape_fill = 0.0
		if r_type == "ELLIPSE":
			shape_fill = math.sqrt((rx*rx * invRxSq) + (ry*ry * invRySq))
		elif r_type == "ISOTRI":
			edgeBand = min(radius_x, height_tiles) * fIsotriEdgeBand
			edgeMargin = min(ry + b_dist, v_dist - ry, max_rx - abs(rx))
			if edgeBand <= 0:
				shape_fill = 1.0
			else:
				shape_fill = 1.0 - (edgeMargin / edgeBand)
		else:
			if radius_x > 0: shape_fill = abs(rx) / radius_x
			if radius_y > 0:
				y_fill = abs(ry) / radius_y
				if y_fill > shape_fill: shape_fill = y_fill
		if shape_fill < fCenterInner:
			centerStrength = 1.0 * fCenterMultiplier
		elif shape_fill < fCenterOuter:
			if fCenterOuter > fCenterInner:
				centerStrength = ((fCenterOuter - shape_fill) / (fCenterOuter - fCenterInner)) * fCenterMultiplier
		if shape_fill > fEdgeInner:
			if fEdgeOuter > fEdgeInner:
				edgeStrength = ((shape_fill - fEdgeInner) / (fEdgeOuter - fEdgeInner)) * fEdgeMultiplier
		if edgeStrength > 1.0: edgeStrength = 1.0
		if centerStrength > 1.0: centerStrength = 1.0
		if edgeStrength > 0.0:
			iLocalWaterPercent = water_prc + int((100 - water_prc) * edgeStrength)
			if iLocalWaterPercent > 100: iLocalWaterPercent = 100
			return iWaterThresholds[iLocalWaterPercent]
		elif centerStrength > 0.0:
			iLocalWaterPercent = int(water_prc * (1.0 - centerStrength))
			if iLocalWaterPercent < 0: iLocalWaterPercent = 0
			return iWaterThresholds[iLocalWaterPercent]

		return iWaterThreshold

	def generatePlotsByRegion(self, region_data):
		sea = 0 
		
		# Define Terrain Profiles: (HillDensity%, PeakDensity%_of_Hills)
		terrain_profiles = {
			"flat":         (15, 1),
			"plateau":      (60, 25),
			"highland":     (75, 40),
			"alpine":       (95, 60),
			"default":      (30, 20)
		}
		
		gc = CyGlobalContext()
		m = CyMap()
		iRocky = gc.getInfoTypeForString("CLIMATE_ROCKY")
		if m.getClimate() == iRocky:
			for key in terrain_profiles.keys():
				h_dens, p_dens = terrain_profiles[key]
				new_h = int(h_dens * 1.2)
				new_p = int(p_dens * 1.1)
				if new_h > 100: new_h = 100
				if new_p > 100: new_p = 100
				terrain_profiles[key] = (new_h, new_p)

		for data in region_data:
			name, r_type_raw, cx, cy, d1, d2, d3, terrain, grain, h_grain, water_prc, bReduceEdges = data
			r_type = r_type_raw.upper()
			
			# 1. Coordinate Math
			center_x = cx * self.iW
			center_y = cy * self.iH
			radius_x = (d1 / 2.0) * self.iW
			radius_y = (d2 / 2.0) * self.iH
			height_tiles = d2 * self.iH

			# Rotation/Geometry Math
			rad = -math.radians(d3)
			cosA, sinA = math.cos(rad), math.sin(rad)
			v_dist, b_dist = (2.0 / 3.0) * height_tiles, (1.0 / 3.0) * height_tiles
			invRxSq, invRySq = 0.0, 0.0
			if radius_x > 0: invRxSq = 1.0 / (radius_x * radius_x)
			if radius_y > 0: invRySq = 1.0 / (radius_y * radius_y)

			if r_type == "ELLIPSE":
				x_extent = math.sqrt((radius_x * cosA) * (radius_x * cosA) + (radius_y * sinA) * (radius_y * sinA))
				y_extent = math.sqrt((radius_x * sinA) * (radius_x * sinA) + (radius_y * cosA) * (radius_y * cosA))
				min_x = -x_extent
				max_x = x_extent
				min_y = -y_extent
				max_y = y_extent
			elif r_type == "ISOTRI":
				points = [(-radius_x, -b_dist), (radius_x, -b_dist), (0.0, v_dist)]
				min_x = 0.0
				max_x = 0.0
				min_y = 0.0
				max_y = 0.0
				for iPoint in range(len(points)):
					local_x, local_y = points[iPoint]
					world_dx = local_x * cosA + local_y * sinA
					world_dy = -local_x * sinA + local_y * cosA
					if iPoint == 0 or world_dx < min_x: min_x = world_dx
					if iPoint == 0 or world_dx > max_x: max_x = world_dx
					if iPoint == 0 or world_dy < min_y: min_y = world_dy
					if iPoint == 0 or world_dy > max_y: max_y = world_dy
			else:
				x_extent = abs(radius_x * cosA) + abs(radius_y * sinA)
				y_extent = abs(radius_x * sinA) + abs(radius_y * cosA)
				min_x = -x_extent
				max_x = x_extent
				min_y = -y_extent
				max_y = y_extent
			
			iWest = max(0, int(center_x + min_x))
			iEast = min(self.iW - 1, int(center_x + max_x))
			iSouth = max(0, int(center_y + min_y))
			iNorth = min(self.iH - 1, int(center_y + max_y))
			
			reg_w, reg_h = iEast - iWest + 1, iNorth - iSouth + 1
			if reg_w <= 0 or reg_h <= 0: continue

			# 2. Fractal Initialization
			NiTextOut("Generating %s (Geometric Fractal) ..." % name)
			
			# This fractal is now shared by BOTH Land and Water regions
			regionContFrac = CyFractal()
			regionContFrac.fracInit(reg_w, reg_h, grain, self.dice, self.iFlags, -1, -1)
			
			# Calculate threshold for the "Active" part of the fractal
			if water_prc <= 0:
				iWaterThreshold = -1
			elif water_prc >= 100:
				iWaterThreshold = 255
			else:
				iWaterThreshold = regionContFrac.getHeightFromPercent(water_prc + sea)

			is_subtractive = (terrain == "water")
			iWaterThresholds = []
			if bReduceEdges and not is_subtractive and water_prc > 0 and water_prc < 100:
				for iPercent in range(101):
					iWaterThresholds.append(regionContFrac.getHeightFromPercent(iPercent))
			
			# Only Land regions need Hill/Peak fractals
			if not is_subtractive:
				regionHillsFrac = CyFractal()
				regionPeaksFrac = CyFractal()
				regionHillsFrac.fracInit(reg_w, reg_h, h_grain, self.dice, 0, -1, -1)
				regionPeaksFrac.fracInit(reg_w, reg_h, h_grain+1, self.dice, 0, -1, -1)

				h_dens, p_dens = terrain_profiles.get(terrain, terrain_profiles["default"])
				iHillThreshold = regionHillsFrac.getHeightFromPercent(100 - h_dens)
				iPeakThreshold = regionPeaksFrac.getHeightFromPercent(100 - p_dens)

			# 3. Iterate over the grid
			for x in range(reg_w):
				world_x = x + iWest
				# Add 0.5 to world_x to get the center of the tile
				dx = (float(world_x) + 0.5) - center_x
				for y in range(reg_h):
					world_y = y + iSouth
					# Add 0.5 to world_y to get the center of the tile
					dy = (float(world_y) + 0.5) - center_y

					# Now, tiles on either side of an even-numbered split will have 
					# identical distance values (e.g., -0.5 and 0.5).
					# Geometry Check
					rx = dx * cosA - dy * sinA
					ry = dx * sinA + dy * cosA
					is_inside = False
					max_rx = 0.0
					if r_type == "ELLIPSE":
						if (rx*rx * invRxSq) + (ry*ry * invRySq) <= 1.0: is_inside = True
					elif r_type == "ISOTRI":
						if ry >= -b_dist and ry <= v_dist:
							max_rx = radius_x * (v_dist - ry) / height_tiles
							if abs(rx) <= max_rx: is_inside = True
					else: # RECT
						if abs(rx) <= radius_x and abs(ry) <= radius_y: is_inside = True

					if not is_inside: continue
						
					# Decide plot type
					world_i = world_y * self.iW + world_x
					val = regionContFrac.getHeight(x, y)
					# Edge reduction
					iLocalWaterThreshold = iWaterThreshold
					if bReduceEdges and not is_subtractive and water_prc > 0 and water_prc < 100:
						iLocalWaterThreshold = self.getReducedEdgeWaterThreshold(
							r_type, water_prc, iWaterThreshold, iWaterThresholds,
							rx, ry, invRxSq, invRySq, radius_x, radius_y,
							height_tiles, b_dist, v_dist, max_rx)
					
					if is_subtractive:
						# WATER REGION: If fractal roll is within the water percent, punch a hole.
						# Setting water_prc=100 will now correctly turn every tile to ocean.
						if val <= iLocalWaterThreshold:
							self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_OCEAN
					else:
						# LAND REGION: Skip tiles within the water percent threshold (remains ocean).
						if val <= iLocalWaterThreshold: 
							continue
						
						# Process Hills and Peaks for land
						if regionHillsFrac.getHeight(x, y) >= iHillThreshold:
							if regionPeaksFrac.getHeight(x, y) >= iPeakThreshold:
								self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_PEAK
							else:
								self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_HILLS
						else:
							self.wholeworldPlotTypes[world_i] = PlotTypes.PLOT_LAND
							
		return self.wholeworldPlotTypes

def _is_coastal_peak_plot(plotTypes, x, y, iW, iH):
	i = y * iW + x
	if plotTypes[i] != PlotTypes.PLOT_PEAK:
		return False

	for dx in range(-1, 2):
		for dy in range(-1, 2):
			if dx == 0 and dy == 0: continue
			adjX = x + dx
			adjY = y + dy
			if adjX < 0 or adjX >= iW: continue
			if adjY < 0 or adjY >= iH: continue
			if plotTypes[adjY * iW + adjX] == PlotTypes.PLOT_OCEAN:
				return True

	return False

def _reduce_coastal_peaks(plotTypes, iW, iH, iReductionOption, dice):
	if plotTypes is None:
		return None
	if iReductionOption <= 0:
		return plotTypes

	reducedPlots = []
	for x in range(iW):
		for y in range(iH):
			if not _is_coastal_peak_plot(plotTypes, x, y, iW, iH): continue
			bReduce = False
			if iReductionOption == 1:
				if dice.get(100, "Mediterranean Reduce Coastal Peak") < 50:
					bReduce = True
			else:
				bReduce = True

			if bReduce:
				reducedPlots.append(y * iW + x)

	for i in reducedPlots:
		plotTypes[i] = PlotTypes.PLOT_HILLS

	if len(reducedPlots) > 0:
		print "Mediterranean reduced %d coastal peaks to hills" % len(reducedPlots)

	return plotTypes

def generatePlotTypes():
	"""Specify map regions here."""
	NiTextOut("Setting Plot Types (Python Central Plains) ...")
	
	global _START_PLOT_MAP, _DEBUG_REGIONS
	_START_PLOT_MAP = None

	gc = CyGlobalContext()
	m = CyMap()
	dice = gc.getGame().getMapRand()
	climate = m.getClimate()
	
	accuracy = 0 # High geographic accuracy
	peak_opt = m.getCustomMapOption(4)
	coastal_peak_opt = m.getCustomMapOption(5)
	
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
	ZeroGrain = 0
	
	regions = []
	# Name, Type, CX, CY, W, H, Angle, Terrain, Grain, Hills, Water%, bReduceEdges
	regions = [
		("Italy", "Rect", 0.456, 0.655, 0.065, 0.407, 37, "default", BalanceGrain, ScatterGrain, 5, True),
		("Sicily", "Isotri", 0.460, 0.450, 0.115, 0.099, 181, "default", ScatterGrain, ScatterGrain, 10, False),
		("PoValley", "Ellipse", 0.412, 0.776, 0.125, 0.106, 12, "flat", GatherGrain, ScatterGrain, 0, False),
		("GulfofTaranto", "Ellipse", 0.525, 0.517, 0.035, 0.079, 29, "water", GatherGrain, ScatterGrain, 80, False),
		("Taranto", "Rect", 0.542, 0.545, 0.068, 0.032, 316, "default", GatherGrain, ScatterGrain, 0, True),
		("Malta", "Ellipse", 0.459, 0.320, 0.038, 0.053, 0, "default", ScatterGrain, ScatterGrain, 85, False),
		("Crete", "Rect", 0.683, 0.313, 0.084, 0.043, 0, "default", GatherGrain, ScatterGrain, 0, False),
		("Sardinia", "Rect", 0.366, 0.540, 0.039, 0.082, 0, "plateau", GatherGrain, ScatterGrain, 10, False),
		("Corsica", "Rect", 0.365, 0.658, 0.028, 0.060, 0, "plateau", GatherGrain, ScatterGrain, 10, False),
		("Baleares", "Rect", 0.259, 0.540, 0.062, 0.057, 22, "default", ScatterGrain, ScatterGrain, 75, False),
		("Iberia", "Rect", 0.095, 0.659, 0.163, 0.319, 341, "default", GatherGrain, ScatterGrain, 5, True),
		("Pyrenees", "Rect", 0.163, 0.764, 0.205, 0.056, 340, "alpine", GatherGrain, ScatterGrain, 0, False),
		("Aragon", "Rect", 0.180, 0.623, 0.070, 0.277, 321, "plateau", GatherGrain, ScatterGrain, 0, True),
		("Atlantic", "Rect", 0.003, 0.610, 0.034, 0.168, 359, "water", GatherGrain, ScatterGrain, 100, True),
		("Gallia", "Rect", 0.260, 0.840, 0.108, 0.339, 345, "flat", GatherGrain, ScatterGrain, 5, True),
		("Germania", "Rect", 0.388, 0.900, 0.177, 0.147, 8, "plateau", GatherGrain, ScatterGrain, 0, False),
		("EuropeNorthBorder", "Rect", 0.586, 0.993, 0.828, 0.087, 0, "default", GatherGrain, ScatterGrain, 0, False),
		("BalkansBase", "Rect", 0.598, 0.844, 0.299, 0.382, 319, "default", GatherGrain, ScatterGrain, 0, False),
		("Ukraine", "Rect", 0.843, 0.919, 0.350, 0.166, 360, "flat", GatherGrain, ScatterGrain, 0, False),
		("Alps_South", "Ellipse", 0.322, 0.772, 0.102, 0.123, 345, "highland", GatherGrain, ScatterGrain, 5, False),
		("Alps_North", "Ellipse", 0.408, 0.856, 0.222, 0.094, 9, "alpine", GatherGrain, ScatterGrain, 10, False),
		("DinaricAlps", "Rect", 0.563, 0.717, 0.172, 0.055, 321, "highland", ScatterGrain, ScatterGrain, 5, False),
		("CarpathiansNorth", "Rect", 0.601, 0.933, 0.103, 0.058, 354, "alpine", ScatterGrain, ScatterGrain, 0, False),
		("CarpathiansSouth", "Rect", 0.646, 0.767, 0.111, 0.052, 6, "highland", ScatterGrain, ScatterGrain, 0, False),
		("CarpathiansWest", "Rect", 0.681, 0.852, 0.087, 0.047, 303, "highland", ScatterGrain, ScatterGrain, 0, False),
		("Balkan Mts", "Rect", 0.663, 0.643, 0.119, 0.102, 4, "plateau", GatherGrain, ScatterGrain, 0, False),
		("Caucasus", "Isotri", 0.985, 0.798, 0.102, 0.305, 84, "highland", GatherGrain, ScatterGrain, 0, False),
		("Crimea", "Ellipse", 0.838, 0.799, 0.061, 0.105, 0, "default", GatherGrain, ScatterGrain, 10, False),
		("Azov_Sea", "Ellipse", 0.890, 0.856, 0.076, 0.079, 25, "water", GatherGrain, ScatterGrain, 80, False),
		("Epirus", "Rect", 0.609, 0.558, 0.057, 0.156, 16, "plateau", ScatterGrain, ScatterGrain, 10, False),
		("Peloponnese", "Ellipse", 0.633, 0.405, 0.072, 0.090, 20, "default", ScatterGrain, ScatterGrain, 10, False),
		("Boeotia", "Rect", 0.655, 0.470, 0.033, 0.117, 36, "default", BalanceGrain, ScatterGrain, 0, False),
		("Rhodes", "Rect", 0.774, 0.333, 0.039, 0.056, 9, "plateau", ScatterGrain, ScatterGrain, 90, False),
		("AsiaMinor", "Rect", 0.837, 0.517, 0.266, 0.185, 16, "default", BalanceGrain, ScatterGrain, 5, True),
		("Levant", "Rect", 0.994, 0.397, 0.158, 0.446, -10, "default", BalanceGrain, ScatterGrain, 0, True),
		("Pontus", "Rect", 0.883, 0.620, 0.242, 0.071, 0, "highland", BalanceGrain, ScatterGrain, 30, True),
		("Tartus", "Rect", 0.893, 0.480, 0.099, 0.079, 23, "highland", GatherGrain, ScatterGrain, 0, False),
		("Asad Lake", "Ellipse", 0.993, 0.393, 0.038, 0.079, 354, "water", ScatterGrain, ScatterGrain, 80, False),
		("Dead_Sea", "Ellipse", 0.928, 0.224, 0.025, 0.079, 354, "water", GatherGrain, ScatterGrain, 80, False),
		("Sinai", "Isotri", 0.892, 0.150, 0.103, 0.158, 194, "flat", GatherGrain, ScatterGrain, 0, True),
		("Arabia", "Rect", 0.992, 0.103, 0.169, 0.140, 307, "default", GatherGrain, ScatterGrain, 10, True),
		("Egypt", "Rect", 0.715, 0.087, 0.262, 0.228, 355, "flat", GatherGrain, ScatterGrain, 0, True),
		("Egypt_RedSea", "Rect", 0.824, 0.078, 0.086, 0.297, 7, "default", GatherGrain, ScatterGrain, 0, True),
		("Cyrenaica", "Ellipse", 0.627, 0.180, 0.106, 0.120, 351, "default", GatherGrain, ScatterGrain, 20, False),
		("WesternSahara", "Rect", 0.171, 0.148, 0.399, 0.385, 11, "flat", GatherGrain, ScatterGrain, 0, False),
		("Libya", "Rect", 0.451, 0.072, 0.317, 0.214, 338, "flat", GatherGrain, ScatterGrain, 10, True),
		("Tunisia", "Ellipse", 0.357, 0.325, 0.078, 0.200, 346, "default", BalanceGrain, ScatterGrain, 20, False),
		("AfricaSouthBorder", "Rect", 0.435, 0.009, 0.887, 0.109, 0, "flat", GatherGrain, ScatterGrain, 0, False),
		("Algeria", "Ellipse", 0.211, 0.356, 0.206, 0.109, 4, "plateau", GatherGrain, ScatterGrain, 10, False),
		("Cyprus", "Rect", 0.848, 0.326, 0.046, 0.053, 34, "default", GatherGrain, ScatterGrain, 10, False),
		("Morocco", "Ellipse", 0.063, 0.358, 0.206, 0.129, 11, "plateau", GatherGrain, ScatterGrain, 0, False),
		("AtlasEast", "Rect", 0.216, 0.291, 0.188, 0.050, 359, "alpine", GatherGrain, ScatterGrain, 0, False),
		("AtlasWest", "Ellipse", 0.040, 0.250, 0.163, 0.059, 26, "alpine", GatherGrain, ScatterGrain, 0, False),
		("HerculesPillars", "Isotri", 0.066, 0.451, 0.092, 0.219, 355, "plateau", ScatterGrain, ScatterGrain, 10, False),
	]
	# Strait Options: 0 = Closed, 1 = Open
	if m.getCustomMapOption(1) == 1:
		regions.append(("Suez", "Rect", 0.878, 0.117, 0.166, 0.059, 291, "water", GatherGrain, ScatterGrain, 100, False))
	if m.getCustomMapOption(2) == 0:
		regions.append(("Bosporos", "Isotri", 0.723, 0.622, 0.075, 0.179, 242, "default", ScatterGrain, ScatterGrain, 5, False))
	if m.getCustomMapOption(3) == 1:
		regions.append(("Gibraltar", "Rect", 0.063, 0.471, 0.096, 0.051, 349, "water", GatherGrain, ScatterGrain, 100, False))

	# Peak Reduction Logic
	processed_regions = []
	for r in regions:
		r_list = list(r)
		terrain = r_list[7]
		if peak_opt == 0: # Flatten Alpine
			if terrain == "alpine": r_list[7] = "highland"
		elif peak_opt == 1: # Flatten Highland
			if terrain == "highland": r_list[7] = "plateau"
			if terrain == "alpine": r_list[7] = "highland"
		processed_regions.append(tuple(r_list))

	# Store the list for the debug sign placer
	_DEBUG_REGIONS = regions


	global plotgen
	plotgen = GeometricMultiFractal()
	plotTypes = plotgen.generatePlotsByRegion(regions)
	return _reduce_coastal_peaks(plotTypes, m.getGridWidth(), m.getGridHeight(), coastal_peak_opt, dice)


# -----------------------------------------------------------------------------
# Custom Climate Generation
# -----------------------------------------------------------------------------
_CLIMATE_ENGINE = None

def get_climate_engine():
	global _CLIMATE_ENGINE
	if _CLIMATE_ENGINE is None:
		m = CyMap()
		iW = m.getGridWidth()
		iH = m.getGridHeight()
		
		accuracy = 0 # High geographic accuracy
		
		manager = CustomClimateManager(m)
		_CLIMATE_ENGINE = CustomClimateGenerator(manager, iW, iH, accuracy)
		
	return _CLIMATE_ENGINE

class ClimateDriver:
	"""
	Data structure representing a single climate influence vector.
	target: "TEMP" or "MOISTURE"
	type: "LINEAR", "MIRRORED", "RADIAL"
	origin: Tuple (cX, cY)
	start_val: Float. Influence at the origin.
	end_val: Float. Influence at the radius boundary.
	radius: Float. The distance of the transition.
	angle: Rotation of the vector (for Linear/Mirrored).
	"""
	def __init__(self, target, type, origin, start_val, end_val, radius, angle=0.0):
		self.target = target
		self.type = type
		self.origin = origin
		self.start_val = start_val
		self.end_val = end_val
		self.radius = radius
		self.angle = angle

class CustomClimateGenerator:
	"""
	The engine that processes a specific X, Y coordinate against the Driver Stack.
	"""
	def __init__(self, manager, iW, iH, accuracy):
		self.manager = manager
		self.iW = float(iW)
		self.iH = float(iH)
		self.accuracy = accuracy
		
		# Initialize fractal noise for jitter (Increased grain for visible scatter)
		gc = CyGlobalContext()
		self.noise = CyFractal()
		self.noise.fracInit(int(iW), int(iH), 3, gc.getGame().getMapRand(), 0, -1, -1)

	def get_climate_at(self, iX, iY):
		fx = float(iX) / self.iW
		fy = float(iY) / self.iH
		
		temp = self.manager.base_temp
		moisture = self.manager.base_moisture
		
		for driver in self.manager.drivers:
			# Vector from driver origin to current plot
			dx = fx - driver.origin[0]
			dy = fy - driver.origin[1]
			
			# 1. Determine Distance Factor (0.0 to 1.0)
			factor = 1.1 # Default to "Outside Radius"
			
			if driver.type == "RADIAL":
				dist = math.sqrt(dx*dx + dy*dy)
				factor = dist / driver.radius
				
			else: # LINEAR or MIRRORED
				rad = math.radians(driver.angle)
				cosA, sinA = math.cos(rad), math.sin(rad)
				
				# Dot Product: Projects the distance vector onto the angle's direction
				proj_dist = (dx * cosA) + (dy * sinA)
				
				if driver.type == "LINEAR":
					# Tiles behind the origin are outside the linear influence.
					if proj_dist >= -1e-12:
						factor = max(0.0, proj_dist) / driver.radius
						
				elif driver.type == "MIRRORED":
					# Symmetrical falloff on both sides of the axis
					factor = abs(proj_dist) / driver.radius
			
			# 2. Only apply if within radius
			if factor <= 1.0:
				# Linear Interpolation: Start + (Percentage * Difference)
				val_change = driver.start_val + (factor * (driver.end_val - driver.start_val))
				
				if driver.target == "TEMP":
					temp += val_change
				elif driver.target == "MOISTURE":
					moisture += val_change
				
		# --- Fractal Noise / Jitter Section ---
		# (Keep your existing jitter logic here...)
		offset_X = (iX + 50) % int(self.iW)
		offset_Y = (iY + 50) % int(self.iH)
		noise_t = (float(self.noise.getHeight(iX, iY)) / 255.0) - 0.5
		noise_m = (float(self.noise.getHeight(offset_X, offset_Y)) / 255.0) - 0.5
		
		noise_mult = 0.25 
		if self.accuracy == 1: noise_mult = 0.25
		elif self.accuracy == 2: noise_mult = 0.3 
			
		temp += (noise_t * noise_mult)
		moisture += (noise_m * noise_mult)
		
		# Final Clamp to 0.0 - 1.0
		if temp < 0.0: temp = 0.0
		if temp > 1.0: temp = 1.0
		if moisture < 0.0: moisture = 0.0
		if moisture > 1.0: moisture = 1.0
		
		return temp, moisture

class CustomClimateManager: # <- CLIMATE DRIVERS HERE
	"""
	Holds the Driver Stack. You can define multiple profiles here and select
	them based on map options or climate settings.
	"""
	def __init__(self, map_obj):
		self.map = map_obj
		self.drivers = []
		self.base_temp = 0.3
		self.base_moisture = 0.3
		
		# Load the profile
		self.setup_profile()

	def setup_profile(self):
		"""
		Set climate drivers here.
		Note: In Civ4, Y=0.0 is the South (bottom), Y=1.0 is the North (top).
		"""
		gc = CyGlobalContext()
		m = CyMap()
		iClimateIndex = m.getClimate()
		climate_info = gc.getClimateInfo(iClimateIndex)
		climate_type = climate_info.getType() # e.g., "CLIMATE_TROPICAL"

		# Initialize Base Values (Temperate Defaults)
		self.base_temp = 0.3
		self.base_moisture = 0.2
		
		# Apply Climate selection modifiers
		if climate_type == "CLIMATE_TROPICAL":
			self.base_temp = 0.5
			self.base_moisture = 0.45
			
		elif climate_type == "CLIMATE_COLD":
			self.base_temp = 0.05
			self.base_moisture = 0.15
			
		elif climate_type == "CLIMATE_ARID":
			self.base_temp = 0.2
			self.base_moisture = 0.05
			

		self.drivers.append(ClimateDriver("TEMP", "LINEAR", (0.5, 1.0), 0.0, 0.5, 1.0, -90.0))
		self.drivers.append(ClimateDriver("MOISTURE", "LINEAR", (0.551, 0.996), 0.6, 0.15, 0.887, -90.0))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.862, 0.708), 0.5, 0.0, 0.128))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.71, 0.36), 0.3, 0.0, 0.135))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.449, 0.772), 0.1, 0.0, 0.107))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.358, 0.352), 0.25, 0.0, 0.14))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.184, 0.084), -0.6, 0.0, 0.223))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.879, 0.066), -0.2, 0.0, 0.128))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.643, 0.025), -0.2, 0.0, 0.128))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.006, 0.376), 0.4, 0.0, 0.126))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.139, 0.595), -0.1, 0.0, 0.095))
		self.drivers.append(ClimateDriver("MOISTURE", "RADIAL", (0.883, 0.53), -0.2, 0.0, 0.082))

# -----------------------------------------------------------------------------
# Terrain & Feature Generation (Downstream of Climate Gen)
# -----------------------------------------------------------------------------
TEMP_THRESHOLDS = [0.10, 0.20, 0.75]
MOISTURE_THRESHOLDS = [0.20, 0.45, 0.70]

# Rows = Temperature (0:Arctic, 1:Cold, 2:Temperate, 3:Tropical)
# Cols = Moisture (0:Arid, 1:Dry, 2:Humid, 3:Wet)
BIOME_TABLE = [
	["Snow", "Snow", "Snow", "Tundra"],
	["Snow", "Tundra", "Tundra", [("Tundra", 80), ("Grassland", 20)]],
	["Desert", [("Desert", 40), ("Plains", 60)], [("Plains", 30), ("Grassland", 70)], [("Plains", 15), ("Grassland", 85)]],
	["Desert", [("Desert", 60), ("Plains", 40)], [("Plains", 30), ("Grassland", 70)], "Grassland"]
]

FEATURE_TABLE = [
	[None, None, None, "Snow"],
	[None, None, "Snow", [("Snow", 60), ("Pine", 40)]],
	[None, None, [("Deciduous", 30), ("Pine", 70)], [("Deciduous", 70), ("Pine", 30)]],
	[None, [(None, 70), ("Deciduous", 30)], [("Deciduous", 70), ("Jungle", 30)], [("Deciduous", 20), ("Jungle", 80)]]
]

def _get_climate_band(value, thresholds):
	i = 0
	while i < len(thresholds):
		if value < thresholds[i]:
			return i
		i += 1
	return len(thresholds)

def _resolve_table_entry(entry, mapRand, log_label):
	if entry is None:
		return None

	if isinstance(entry, list):
		if len(entry) == 0:
			return None

		first = entry[0]
		if isinstance(first, tuple):
			total = 0
			for item, weight in entry:
				total += weight

			if total <= 0:
				return None

			roll = mapRand.get(total, log_label)
			running = 0
			for item, weight in entry:
				running += weight
				if roll < running:
					return item
			return entry[len(entry) - 1][0]

		roll = mapRand.get(len(entry), log_label)
		return entry[roll]

	return entry

class TerrainGenerator(CvMapGeneratorUtil.TerrainGenerator):
	def __init__(self, fGrassMoistureThreshold=0.5, fDesertMoistureThreshold=0.2):
		# We call the parent but we will use our own logic in generateTerrainAtPlot
		CvMapGeneratorUtil.TerrainGenerator.__init__(self)
		self.fGrassThreshold = fGrassMoistureThreshold
		self.fDesertThreshold = fDesertMoistureThreshold
		self.terrainMap = {
			"Snow": self.gc.getInfoTypeForString("TERRAIN_SNOW"),
			"Tundra": self.gc.getInfoTypeForString("TERRAIN_TUNDRA"),
			"Plains": self.gc.getInfoTypeForString("TERRAIN_PLAINS"),
			"Desert": self.gc.getInfoTypeForString("TERRAIN_DESERT"),
			"Grassland": self.gc.getInfoTypeForString("TERRAIN_GRASS")
		}

	def generateTerrainAtPlot(self, iX, iY):
		pPlot = self.map.plot(iX, iY)
		
		# 1. Handle Water (Early Exit)
		if pPlot.isWater():
			return pPlot.getTerrainType()

		# 2. Fetch climate
		engine = get_climate_engine()
		temp, moisture = engine.get_climate_at(iX, iY)

		temp_band = _get_climate_band(temp, TEMP_THRESHOLDS)
		moisture_band = _get_climate_band(moisture, MOISTURE_THRESHOLDS)
		terrain_name = _resolve_table_entry(BIOME_TABLE[temp_band][moisture_band], self.mapRand, "Terrain Table")

		if self.terrainMap.has_key(terrain_name):
			return self.terrainMap[terrain_name]
		return pPlot.getTerrainType()

def generateTerrainTypes():
	NiTextOut("Generating Terrain (Python Central Plains) ...")
	
	# We no longer need iDesertPercent or iPlainsPercent because we
	# define the climate via the piecewise moisture gradient.
	# We only pass the thresholds for the terrain bands.
	
	terraingen = TerrainGenerator(
		fGrassMoistureThreshold = 0.5, 
		fDesertMoistureThreshold = 0.2
	)
	
	terrainTypes = terraingen.generateTerrain()
	return terrainTypes

class FeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
	def __init__(self, iJunglePercent=60, iForestPercent=40):
		CvMapGeneratorUtil.FeatureGenerator.__init__(self, iJunglePercent, iForestPercent)
		
		self.gc = CyGlobalContext()
		self.terrainDesert = self.gc.getInfoTypeForString("TERRAIN_DESERT")
		self.terrainPlains = self.gc.getInfoTypeForString("TERRAIN_PLAINS")
		self.terrainGrass = self.gc.getInfoTypeForString("TERRAIN_GRASS")
		self.featureFloodPlains = self.gc.getInfoTypeForString("FEATURE_FLOOD_PLAINS")
		
		# Initialize fractal for moisture noise
		self.moisture_noise = CyFractal()
		self.moisture_noise.fracInit(self.iGridW, self.iGridH, 3, self.mapRand, 0, -1, -1)

	def addIceAtPlot(self, pPlot, iX, iY, lat):
		# Do nothing - prevents ice placement
		pass

	def addClimateFeature(self, pPlot, feature_name):
		if feature_name is None:
			return False

		if feature_name == "Jungle":
			if self.mapRand.get(100, "J") < self.iJunglePercent:
				if pPlot.canHaveFeature(self.featureJungle):
					pPlot.setFeatureType(self.featureJungle, -1)
					return True
			return False

		iVariety = -1
		if feature_name == "Deciduous":
			iVariety = 0
		elif feature_name == "Pine":
			iVariety = 1
		elif feature_name == "Snow":
			iVariety = 2
		else:
			return False

		if self.mapRand.get(100, "F") < self.iForestPercent:
			if pPlot.canHaveFeature(self.featureForest):
				pPlot.setFeatureType(self.featureForest, iVariety)
				return True

		return False

	def addFeaturesAtPlot(self, iX, iY):
		pPlot = self.map.sPlot(iX, iY)
		if pPlot.isWater() or pPlot.getFeatureType() != -1: return

		engine = get_climate_engine()
		temp, moisture = engine.get_climate_at(iX, iY)

		temp_band = _get_climate_band(temp, TEMP_THRESHOLDS)
		moisture_band = _get_climate_band(moisture, MOISTURE_THRESHOLDS)
		feature_name = _resolve_table_entry(FEATURE_TABLE[temp_band][moisture_band], self.mapRand, "Feature Table")

		if self.addClimateFeature(pPlot, feature_name):
			return

		# 3. Desert Features
		if pPlot.getTerrainType() == self.terrainDesert:
			if pPlot.isRiver():
				# Floodplains only go on Desert tiles with no other features
				if pPlot.getFeatureType() == -1:
					if pPlot.canHaveFeature(self.featureFloodPlains):
						pPlot.setFeatureType(self.featureFloodPlains, -1)
			if self.mapRand.get(100, "O") < 5:
				if pPlot.canHaveFeature(self.featureOasis):
					pPlot.setFeatureType(self.featureOasis, -1)

def addFeatures():
	NiTextOut("Adding Features (Python Central Plains) ...")
	featuregen = FeatureGenerator()
	featuregen.addFeatures()
	# expandCoastToTwoTiles()
	
	# Debug for fractal regions
	global _DEBUG_REGIONS
	# if _DEBUG_REGIONS:
		# _add_region_signs(_DEBUG_REGIONS)
	
	return 0

# -----------------------------------------------------------------------------
# Coast distance
# -----------------------------------------------------------------------------
def expandCoastToTwoTiles():
	"""Convert all water tiles within a BFC (Big Fat Cross) radius of land to coast."""
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

	# Mark water plots within BFC range
	coast_plots = set()
	for lx, ly in land_plots:
		for dx in range(-2, 3):
			for dy in range(-2, 3):
				# BFC Logic: Skip the four corner tiles of the 5x5 area
				# (where both dx and dy are 2 or -2)
				if abs(dx) == 2 and abs(dy) == 2:
					continue
				
				nx = lx + dx
				ny = ly + dy
				
				# Check bounds
				if 0 <= nx < iW and 0 <= ny < iH:
					pPlot = map.plot(nx, ny)
					if pPlot.isWater():
						coast_plots.add((nx, ny))

	# Apply coast terrain
	for x, y in coast_plots:
		map.plot(x, y).setTerrainType(coast_id, True, True)
		

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
		

# -----------------------------------------------------------------------------
# Custom River Generator
# -----------------------------------------------------------------------------
"""Custom generator for drawing rivers / waterways running through specified coordinates."""
class PathNavigator:
	def __init__(self, map, dice):
		self.map = map
		self.dice = dice
		self.iW = map.getGridWidth()
		self.iH = map.getGridHeight()
		self.noise = CyFractal()
		self.noise.fracInit(self.iW, self.iH, 2, self.dice, 0, -1, -1)
		self.size_factor = float(self.iW + self.iH) / 64.0

	def is_ocean(self, x, y):
		if x < 0 or x >= self.iW or y < 0 or y >= self.iH: return False
		pPlot = self.map.plot(x, y)
		if pPlot.isWater():
			pArea = pPlot.area()
			if pArea:
				if pArea.getNumTiles() >= 10: return True
		return False

	def is_any_water(self, x, y):
		if x < 0 or x >= self.iW or y < 0 or y >= self.iH: return False
		return self.map.plot(x, y).isWater()

	def get_best_move(self, cx, cy, tx, ty, visited, is_water_path, meander):
		best_score = 999999.0
		best_move = None
		accuracy = 0 # High geographic accuracy
		dist_to_target = math.sqrt((cx - tx)**2 + (cy - ty)**2)

		if is_water_path:
			moves = [(1,0), (-1,0), (0,1), (0,-1)]
		else:
			moves = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
			
		for move in moves:
			nx, ny = cx + move[0], cy + move[1]
			if nx < 0 or nx >= self.iW or ny < 0 or ny >= self.iH: continue
			
			bVisited = False
			for v in visited:
				if nx == v[0] and ny == v[1]:
					bVisited = True
					break
			if bVisited: continue
			
			if is_water_path:
				bSkip2x2 = False
				if accuracy == 2 or dist_to_target < 4:
					bSkip2x2 = True
				else:
					for adj in [(1,0), (-1,0), (0,1), (0,-1)]:
						if self.is_ocean(nx + adj[0], ny + adj[1]):
							bSkip2x2 = True
							break
				
				if not bSkip2x2:
					if self.is_any_water(nx-1, ny) and self.is_any_water(nx, ny-1) and self.is_any_water(nx-1, ny-1): continue
					if self.is_any_water(nx+1, ny) and self.is_any_water(nx, ny-1) and self.is_any_water(nx+1, ny-1): continue
					if self.is_any_water(nx-1, ny) and self.is_any_water(nx, ny+1) and self.is_any_water(nx-1, ny+1): continue
					if self.is_any_water(nx+1, ny) and self.is_any_water(nx, ny+1) and self.is_any_water(nx+1, ny+1): continue

			dist = math.sqrt((nx - tx)**2 + (ny - ty)**2)
			n_val = (self.noise.getHeight(nx, ny) / 100.0) - 0.5
			score = dist * (1.0 + (n_val * meander))
			
			if score < best_score:
				best_score = score
				best_move = (nx, ny, move[0], move[1])
		return best_move

	def generate_path(self, start, end, meander, is_water_path):
		curr_x, curr_y = start
		path = [(curr_x, curr_y)]
		visited = [(curr_x, curr_y)]
		
		max_steps = (abs(curr_x - end[0]) + abs(curr_y - end[1])) * 4
		for i in range(max_steps):
			if curr_x == end[0] and curr_y == end[1]: break
			move = self.get_best_move(curr_x, curr_y, end[0], end[1], visited, is_water_path, meander)
			if not move: break
			curr_x, curr_y = move[0], move[1]
			path.append((curr_x, curr_y))
			visited.append((curr_x, curr_y))
			
			if is_water_path:
				if self.is_ocean(curr_x, curr_y):
					break
			else:
				# Standard River: Stop if we hit ANY water
				# We skip i=0 to allow rivers to start adjacent to water
				if i > 0:
					if self.is_any_water(curr_x, curr_y):
						break
		return path
	
class WaterwayMaker:
	def __init__(self, navigator):
		self.nav = navigator
		self.map = navigator.map

	def build(self, checkpoints, meander, bridge_spacing, bBridgesEnabled=True):
		full_path = []
		for i in range(len(checkpoints) - 1):
			start = (int(self.nav.iW * checkpoints[i][0]), int(self.nav.iH * checkpoints[i][1]))
			end = (int(self.nav.iW * checkpoints[i+1][0]), int(self.nav.iH * checkpoints[i+1][1]))
			segment = self.nav.generate_path(start, end, meander, True)
			if i == 0:
				full_path.extend(segment)
			else:
				full_path.extend(segment[1:])
			if segment:
				if self.nav.is_ocean(segment[-1][0], segment[-1][1]):
					break
		
		self._apply_to_map(full_path, bridge_spacing, bBridgesEnabled)

	def _apply_to_map(self, path, bridge_spacing, bBridgesEnabled):
		if not path: return
		riverID = self.map.getNextRiverID()
		self.map.incrementNextRiverID()
		step_count = 0
		next_gap = int((self.nav.dice.get(3, "G") + bridge_spacing) * self.nav.size_factor)
		if next_gap < 2: next_gap = 2

		for i in range(len(path)):
			x, y = path[i]
			pPlot = self.map.plot(x, y)
			
			# Force Ocean on last tile or existing ocean
			if i == len(path) - 1 or self.nav.is_ocean(x, y):
				pPlot.setPlotType(PlotTypes.PLOT_OCEAN, True, True)
				step_count = 0
				continue

			bIsBridge = False
			# Only evaluate bridge logic if bBridgesEnabled is True
			if bBridgesEnabled:
				if step_count >= next_gap:
					bNearOcean = False
					for adj in [(1,0), (-1,0), (0,1), (0,-1)]:
						if self.nav.is_ocean(x+adj[0], y+adj[1]):
							bNearOcean = True
							break
					if not bNearOcean:
						bIsBridge = True

			if bIsBridge:
				pPlot.setPlotType(PlotTypes.PLOT_LAND, True, True)
				pPlot.setFeatureType(FeatureTypes.NO_FEATURE, -1)
				
				# Flatten 8-way adjacent peaks
				for adj_x in range(-1, 2):
					for adj_y in range(-1, 2):
						if adj_x == 0 and adj_y == 0: continue
						nx, ny = x + adj_x, y + adj_y
						if nx >= 0 and nx < self.nav.iW and ny >= 0 and ny < self.nav.iH:
							pAdj = self.map.plot(nx, ny)
							if pAdj.getPlotType() == PlotTypes.PLOT_PEAK:
								pAdj.setPlotType(PlotTypes.PLOT_HILLS, True, True)
				
				dx, dy, ndx, ndy = 0, 0, 0, 0
				if i > 0: dx, dy = x - path[i-1][0], y - path[i-1][1]
				if i < len(path)-1: ndx, ndy = path[i+1][0] - x, path[i+1][1] - y
				self._apply_bridge_flags(x, y, dx, dy, ndx, ndy, riverID)
				step_count = 0
				next_gap = int((self.nav.dice.get(3, "G") + bridge_spacing) * self.nav.size_factor)
				if next_gap < 2: next_gap = 2
			else:
				pPlot.setPlotType(PlotTypes.PLOT_OCEAN, True, True)
				step_count += 1

	def _apply_bridge_flags(self, x, y, dx, dy, ndx, ndy, rID):
		N, S, E, W = CardinalDirectionTypes.CARDINALDIRECTION_NORTH, CardinalDirectionTypes.CARDINALDIRECTION_SOUTH, CardinalDirectionTypes.CARDINALDIRECTION_EAST, CardinalDirectionTypes.CARDINALDIRECTION_WEST
		corner = "STRAIGHT"
		if dy==1 and ndx==1: corner="S_E"
		elif dy==1 and ndx==-1: corner="S_W"
		elif dy==-1 and ndx==1: corner="N_E"
		elif dy==-1 and ndx==-1: corner="N_W"
		elif dx==-1 and ndy==-1: corner="E_S"
		elif dx==1 and ndy==-1: corner="W_S"
		elif dx==-1 and ndy==1: corner="E_N"
		elif dx==1 and ndy==1: corner="W_N"

		if corner == "STRAIGHT":
			p = self.map.plot(x, y)
			if dx != 0:
				flow = E
				if dx != 1: flow = W
				p.setNOfRiver(True, flow)
			elif dy != 0:
				flow = N
				if dy != 1: flow = S
				p.setWOfRiver(True, flow)
			p.setRiverID(rID)
		elif corner == "S_E":
			p=self.map.plot(x-1, y); p.setWOfRiver(True, N); p.setRiverID(rID)
			p=self.map.plot(x, y+1); p.setNOfRiver(True, E); p.setRiverID(rID)
		elif corner == "S_W":
			p=self.map.plot(x, y); p.setWOfRiver(True, N); p.setRiverID(rID)
			p=self.map.plot(x, y+1); p.setNOfRiver(True, W); p.setRiverID(rID)
		elif corner == "N_E":
			p=self.map.plot(x-1, y); p.setWOfRiver(True, S); p.setRiverID(rID)
			p=self.map.plot(x, y); p.setNOfRiver(True, E); p.setRiverID(rID)
		elif corner == "N_W":
			p=self.map.plot(x, y); p.setWOfRiver(True, S); p.setNOfRiver(True, W); p.setRiverID(rID)
		elif corner == "E_S":
			p=self.map.plot(x-1, y); p.setWOfRiver(True, S); p.setRiverID(rID)
			p=self.map.plot(x, y+1); p.setNOfRiver(True, W); p.setRiverID(rID)
		elif corner == "W_S":
			# --- INCORPORATED YOUR FIX ---
			p=self.map.plot(x, y); p.setWOfRiver(True, S); p.setRiverID(rID)
			p=self.map.plot(x, y+1); p.setNOfRiver(True, E); p.setRiverID(rID)
		elif corner == "E_N":
			p=self.map.plot(x-1, y); p.setWOfRiver(True, N); p.setRiverID(rID)
			p=self.map.plot(x, y); p.setNOfRiver(True, W); p.setRiverID(rID)
		elif corner == "W_N":
			p=self.map.plot(x, y); p.setWOfRiver(True, N); p.setNOfRiver(True, E); p.setRiverID(rID)

class StandardRiverMaker:
	def __init__(self, navigator):
		self.nav = navigator
		self.map = navigator.map

	def build(self, checkpoints, meander):
		riverID = self.map.getNextRiverID()
		self.map.incrementNextRiverID()
		for i in range(len(checkpoints) - 1):
			start = (int(self.nav.iW * checkpoints[i][0]), int(self.nav.iH * checkpoints[i][1]))
			end = (int(self.nav.iW * checkpoints[i+1][0]), int(self.nav.iH * checkpoints[i+1][1]))
			path = self.nav.generate_path(start, end, meander, False)
			if not path: break
			
			for j in range(len(path)-1):
				curr, next = path[j], path[j+1]
				dx, dy = next[0]-curr[0], next[1]-curr[1]
				bStop = self._apply_river_flags(curr[0], curr[1], dx, dy, riverID)
				if bStop: return

	def _apply_river_flags(self, x, y, dx, dy, rID):
		N, S, E, W = CardinalDirectionTypes.CARDINALDIRECTION_NORTH, CardinalDirectionTypes.CARDINALDIRECTION_SOUTH, CardinalDirectionTypes.CARDINALDIRECTION_EAST, CardinalDirectionTypes.CARDINALDIRECTION_WEST
		bStop = False
		
		# Horizontal
		if dx != 0:
			if dx == 1:
				tx = x
				flow = E
				look_x = tx + 1
			else:
				tx = x - 1
				flow = W
				look_x = tx - 1
			
			# Stop at ANY water (Lake or Coast)
			if self.nav.is_any_water(look_x, y) or self.nav.is_any_water(look_x, y-1):
				bStop = True
			
			p = self.map.plot(tx, y)
			if p:
				if not self.nav.is_any_water(tx, y):
					if not self.nav.is_any_water(tx, y-1):
						if self._check_merge(tx, y, False, flow): 
							bStop = True
						p.setNOfRiver(True, flow)
						p.setRiverID(rID)
			if bStop: return True

		# Vertical
		if dy != 0:
			tx = x + dx - 1
			if dy == 1:
				ty = y
				flow = N
				look_y = ty + 1
			else:
				ty = y - 1
				flow = S
				look_y = ty - 1
			
			# Stop at ANY water (Lake or Coast)
			if self.nav.is_any_water(tx, look_y) or self.nav.is_any_water(tx+1, look_y):
				bStop = True
				
			p = self.map.plot(tx, ty)
			if p:
				if not self.nav.is_any_water(tx, ty):
					if not self.nav.is_any_water(tx+1, ty):
						if self._check_merge(tx, ty, True, flow): 
							bStop = True
						p.setWOfRiver(True, flow)
						p.setRiverID(rID)
		return bStop

	def _check_merge(self, x, y, is_vertical, flow):
		N, S, E, W = CardinalDirectionTypes.CARDINALDIRECTION_NORTH, CardinalDirectionTypes.CARDINALDIRECTION_SOUTH, CardinalDirectionTypes.CARDINALDIRECTION_EAST, CardinalDirectionTypes.CARDINALDIRECTION_WEST
		if is_vertical:
			if flow == N:
				p=self.map.plot(x, y+1)
				if p and ((p.isWOfRiver() and p.getRiverNSDirection()==N) or (p.isNOfRiver() and p.getRiverWEDirection()==W)): return True
				p=self.map.plot(x+1, y+1)
				if p and (p.isNOfRiver() and p.getRiverWEDirection()==E): return True
			else:
				p=self.map.plot(x, y)
				if p and (p.isNOfRiver() and p.getRiverWEDirection()==W): return True
				p=self.map.plot(x, y-1)
				if p and (p.isWOfRiver() and p.getRiverNSDirection()==S): return True
				p=self.map.plot(x+1, y)
				if p and (p.isNOfRiver() and p.getRiverWEDirection()==E): return True
		else:
			if flow == E:
				p=self.map.plot(x, y)
				if p and (p.isWOfRiver() and p.getRiverNSDirection()==N): return True
				p=self.map.plot(x, y-1)
				if p and (p.isWOfRiver() and p.getRiverNSDirection()==S): return True
				p=self.map.plot(x+1, y)
				if p and (p.isNOfRiver() and p.getRiverWEDirection()==E): return True
			else: # W
				p=self.map.plot(x-1, y)
				if p and ((p.isNOfRiver() and p.getRiverWEDirection()==W) or (p.isWOfRiver() and p.getRiverNSDirection()==N)): return True
				p=self.map.plot(x-1, y-1)
				if p and (p.isWOfRiver() and p.getRiverNSDirection()==S): return True
		return False

def addRivers(): # <- Add Custom Rivers Here
	"""Specify custom rivers here."""
	m = CyMap()
	m.recalculateAreas()
	gc = CyGlobalContext()
	dice = gc.getGame().getMapRand()
	
	# Initialize the new Class-based system
	nav = PathNavigator(m, dice)
	waterways = WaterwayMaker(nav)
	rivers = StandardRiverMaker(nav)
	
	###########################################################################################
	# 1. Historical Rivers
	###########################################################################################
	Vjosa = [(0.299, 0.815), (0.309, 0.938), (0.21, 0.942)]
	Garomme = [(0.265, 0.755), (0.201, 0.87)]
	Rhone = [(0.377, 0.858), (0.337, 0.847), (0.331, 0.673)]
	Ebro = [(0.152, 0.705), (0.242, 0.567)]
	Douro = [(0.125, 0.685), (0.007, 0.72)]
	Tagus = [(0.114, 0.602), (0.002, 0.614)]
	Po = [(0.382, 0.803), (0.433, 0.758), (0.467, 0.752)]
	Tiber = [(0.45, 0.699), (0.408, 0.61)]
	Volturno = [(0.496, 0.605), (0.458, 0.513)]
	Danube = [(0.389, 0.912), (0.458, 0.945), (0.547, 0.904), (0.563, 0.803), (0.64, 0.753), (0.711, 0.717), (0.727, 0.788), (0.794, 0.748)]
	Dniester = [(0.629, 0.952), (0.712, 0.928), (0.778, 0.817)]
	Dnieper = [(0.772, 0.993), (0.843, 0.945), (0.849, 0.897), (0.799, 0.832)]
	Don = [(0.987, 0.997), (0.884, 0.885)]
	Vardar = [(0.623, 0.657), (0.698, 0.527)]
	Vjosa = [(0.621, 0.549), (0.569, 0.575)]
	Halys = [(0.907, 0.54), (0.848, 0.531), (0.839, 0.605), (0.897, 0.705)]
	Gediz = [(0.804, 0.487), (0.714, 0.44)]
	Euphrates = [(0.98, 0.552), (0.94, 0.515), (0.984, 0.387)]
	Orontes = [(0.941, 0.278), (0.945, 0.35), (0.912, 0.357)]
	Nile_Delta = [(0.812, 0.129), (0.843, 0.259)]
	Nile = [(0.814, 0.0), (0.815, 0.284)]
	Moulouya = [(0.028, 0.302), (0.069, 0.352), (0.096, 0.47)]
	Medjerda = [(0.313, 0.328), (0.418, 0.336)]

	rivers.build(Vjosa, meander=0.2)
	rivers.build(Garomme, meander=0.2)
	rivers.build(Rhone, meander=0.2)
	rivers.build(Ebro, meander=0.2)
	rivers.build(Douro, meander=0.2)
	rivers.build(Tagus, meander=0.2)
	rivers.build(Po, meander=0.2)
	rivers.build(Tiber, meander=0.2)
	rivers.build(Volturno, meander=0.2)
	rivers.build(Danube, meander=0.2)
	rivers.build(Dniester, meander=0.2)
	rivers.build(Dnieper, meander=0.2)
	rivers.build(Don, meander=0.2)
	rivers.build(Vardar, meander=0.2)
	rivers.build(Vjosa, meander=0.2)
	rivers.build(Halys, meander=0.2)
	rivers.build(Gediz, meander=0.2)
	rivers.build(Euphrates, meander=0.2)
	rivers.build(Orontes, meander=0.2)
	rivers.build(Nile_Delta, meander=0.2)
	rivers.build(Nile, meander=0.1)
	rivers.build(Moulouya, meander=0.2)
	rivers.build(Medjerda, meander=0.2)
	


	##############################
	# 2. Standard River Generation
	##############################

	rand_river_density = 0.2
	riverGen = RiverGenerator(river_density=rand_river_density)
	riverGen.seedRivers()

	return None

# -----------------------------------------------------------------------------
# Starting plot
# -----------------------------------------------------------------------------

_START_PLOT_MAP = None
START_EDGE_MARGIN = 3

def minStartingDistanceModifier():
	return 15

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

def _synced_shuffle(dice, lst):
	result = lst[:]
	for i in range(len(result) - 1, 0, -1):
		j = dice.get(i + 1, "Synced Shuffle")
		result[i], result[j] = result[j], result[i]
	return result

def _is_start_edge_safe(x, y, iW, iH):
	"""Return True if a start is at least three tiles from every map edge."""
	if x < START_EDGE_MARGIN: return False
	if y < START_EDGE_MARGIN: return False
	if x >= iW - START_EDGE_MARGIN: return False
	if y >= iH - START_EDGE_MARGIN: return False
	return True

def _find_plot_in_rect(rect, region_name, assigned_coords, min_landmass=4, bPreferCoast=False, bPreferRiver=False):
	"""
	Return a plot index of a land tile inside the rectangle.
	rect format: (cX, cY, width, height)
	"""
	map = CyMap()
	dice = CyGlobalContext().getGame().getMapRand()
	iW, iH = map.getGridWidth(), map.getGridHeight()

	cX, cY, width, height = rect
	west_x = max(0, int(iW * (cX - (width / 2.0))))
	east_x = min(iW - 1, int(iW * (cX + (width / 2.0))))
	south_y = max(0, int(iH * (cY - (height / 2.0))))
	north_y = min(iH - 1, int(iH * (cY + (height / 2.0))))

	# Determine dynamic minimum distance based on map size
	min_dist = 6
	if map.getWorldSize() >= WorldSizeTypes.WORLDSIZE_LARGE:
		min_dist = 9

	# Step 1: Find all valid land plots in the rectangle
	base_eligible = []
	for x in range(west_x, east_x + 1):
		for y in range(south_y, north_y + 1):
			if not _is_start_edge_safe(x, y, iW, iH): continue
			pPlot = map.plot(x, y)
			if pPlot and not pPlot.isWater() and not pPlot.isPeak():
				area = pPlot.area()
				if area and area.getNumTiles() >= min_landmass:
					base_eligible.append(pPlot)
	
	if not base_eligible: return -1

	# Step 2: Filter for Distance Safety (Best Effort)
	safe_eligible = []
	for pPlot in base_eligible:
		is_safe = True
		for (ax, ay) in assigned_coords:
			# plotDistance is the Civ4 standard for circular radius
			if plotDistance(pPlot.getX(), pPlot.getY(), ax, ay) < min_dist:
				is_safe = False
				break
		if is_safe:
			safe_eligible.append(pPlot)
			
	# If we found safe plots, they become our new candidates. 
	# If not, we use the original list (ignoring distance).
	if len(safe_eligible) > 0:
		candidates = safe_eligible
	else:
		candidates = base_eligible

	# Step 3: Apply Coast Preference
	if bPreferCoast:
		coastal_eligible = []
		for pPlot in candidates:
			if _is_real_coast(pPlot, 5):
				coastal_eligible.append(pPlot)
		if len(coastal_eligible) > 0:
			candidates = coastal_eligible

	# Step 4: Apply River Preference
	if bPreferRiver:
		river_eligible = []
		for pPlot in candidates:
			if pPlot.isRiver():
				river_eligible.append(pPlot)
		if len(river_eligible) > 0:
			candidates = river_eligible

	# Step 5: Final Selection
	idx = dice.get(len(candidates), "Historical start: %s" % region_name)
	target_plot = candidates[idx]
	return map.plotNum(target_plot.getX(), target_plot.getY())

def _fallback_start_placement(playerID, existing_coords):
	map = CyMap()
	gc = CyGlobalContext()
	dice = gc.getGame().getMapRand()
	player = gc.getPlayer(playerID)
	player.AI_updateFoundValues(True)

	COASTAL_START_BIAS = 1.35 

	# Gather the top 3 largest areas
	all_areas = []
	for i in range(map.getIndexAfterLastArea()):
		pArea = map.getArea(i)
		if pArea and not pArea.isNone() and not pArea.isWater():
			all_areas.append((pArea.getNumTiles(), pArea.getID()))
			
	# Sort largest to smallest, keep top 3
	all_areas.sort(key=lambda item: -item[0])
	valid_area_ids = []
	for i in range(min(3, len(all_areas))):
		valid_area_ids.append(all_areas[i][1])

	if not valid_area_ids:
		return -1 # Map has no land at all

	iW, iH = map.getGridWidth(), map.getGridHeight()
	
	# Start with a generous distance
	min_dist = 15
	if map.getWorldSize() >= WorldSizeTypes.WORLDSIZE_LARGE: 
		min_dist = 20

	candidates = []
	
	# Loop to progressively lower the distance requirement if the map is crowded
	while min_dist >= 0:
		
		# Iterate through the top 3 areas in order of size
		for target_area_id in valid_area_ids:
			for x in range(iW):
				for y in range(iH):
					if not _is_start_edge_safe(x, y, iW, iH): continue
					pPlot = map.plot(x, y)
					
					# HARD CHECK: No Water, No Peaks, must be on Target Area
					if not pPlot or pPlot.isWater() or pPlot.isPeak(): continue
					if pPlot.getArea() != target_area_id: continue

					# Distance check using stepDistance (Chebyshev)
					is_too_close = False
					if min_dist > 0:
						for (ax, ay) in existing_coords:
							if stepDistance(x, y, ax, ay) < min_dist:
								is_too_close = True
								break
					if is_too_close: continue

					val = pPlot.getFoundValue(playerID)
					if val > 0:
						# Use the "Real Coast" check (adjacent to water body >= 10 tiles)
						# We use 10 here so they don't spawn on a tiny 2-tile lake
						if _is_real_coast(pPlot, 10):
							val *= COASTAL_START_BIAS
						candidates.append((val, map.plotNum(x, y)))
			
			# If we found at least one candidate in this area, we stop checking smaller areas
			if len(candidates) > 0:
				break
				
		# If we found at least one candidate across any area, break out of the distance loop
		if len(candidates) > 0:
			break
			
		# If no spots found on any of the top 3 continents, shrink the minimum distance and try again
		if min_dist == 0:
			break # Give up if even 0 distance fails
			
		min_dist -= 3 # Shrink requirement by 3 tiles and rescan
		if min_dist < 0:
			min_dist = 0

	# Absolute emergency fallback if a civilization literally values NO land plot
	if not candidates:
		for x in range(iW):
			for y in range(iH):
				if not _is_start_edge_safe(x, y, iW, iH): continue
				pPlot = map.plot(x, y)
				if pPlot and not pPlot.isWater() and not pPlot.isPeak() and pPlot.getArea() in valid_area_ids:
					candidates.append((10, map.plotNum(x, y)))

		if not candidates:
			# Search every landmass, but never relax the map-edge restriction.
			for x in range(iW):
				for y in range(iH):
					if not _is_start_edge_safe(x, y, iW, iH): continue
					pPlot = map.plot(x, y)
					if pPlot and not pPlot.isWater() and not pPlot.isPeak():
						candidates.append((10, map.plotNum(x, y)))

		if not candidates:
			return -1

	# Sort by highest found value
	candidates.sort(key=lambda item: -item[0])
	num_best_choices = min(5, len(candidates))
	return candidates[dice.get(num_best_choices, "Fallback Start Choice")][1]

def _add_spawn_signs(spawn_dict):
	"""Adds map signs to the center of each historical spawn region."""
	m = CyMap()
	engine = CyEngine()
	iW = m.getGridWidth()
	iH = m.getGridHeight()
	
	# In Python 2.4, iterating over keys is the safest method
	for name in spawn_dict.keys():
		data = spawn_dict[name]
		cx = data[0]
		cy = data[1]
		
		# Convert fractional center to plot coordinates
		iX = int(iW * cx)
		iY = int(iH * cy)
		
		pPlot = m.plot(iX, iY)
		if pPlot:
			if not pPlot.isNone():
				# -1 makes the sign visible to all players
				# engine.addSign(pPlot, -1, "Spawn: " + str(name))
				engine.addSign(pPlot, -1, str(name))


def _assign_all_starting_plots(): # <- Starting Plot Assignments Here
	print "PY: Assigning all starting plots..."
	map = CyMap()
	gc = CyGlobalContext()
	dice = gc.getGame().getMapRand()
	# Force a recalculation of areas to ensure 'isWater' and 'area size' are accurate
	map.recalculateAreas()
	
	start_option = map.getCustomMapOption(9)

	final_assignments = {} 
	assigned_coords = []   
	used_regions = set()
	unassigned_players = []

	# Format: (cX, cY, width, height, bPreferCoast, bPreferRiver)
	SPAWN_REGIONS = {
		"Egypt": (0.813, 0.154, 0.109, 0.22, False, True),
		"Syria": (0.947, 0.367, 0.109, 0.244, True, False),
		"Greece": (0.628, 0.461, 0.109, 0.22, True, False),
		"Rome": (0.433, 0.679, 0.08, 0.199, True, True),
		"Gaul": (0.268, 0.907, 0.147, 0.189, False, False),
		"Germania": (0.485, 0.946, 0.194, 0.107, False, False),
		"Dacia": (0.697, 0.788, 0.132, 0.132, False, False),
		"Steppe": (0.892, 0.872, 0.207, 0.246, False, False),
		"Iberia": (0.143, 0.638, 0.113, 0.292, False, False),
		"Africa": (0.347, 0.332, 0.126, 0.224, True, True),
		"Morocco": (0.052, 0.38, 0.098, 0.2, True, False),
		"Bosporus": (0.77, 0.583, 0.106, 0.174, False, False),
		"Portugal": (0.038, 0.656, 0.073, 0.257, True, False),
		"Sicilies": (0.491, 0.464, 0.118, 0.185, True, False),
	}


	primary_regions = ["Egypt", "Syria", "Greece", "Rome", "Gaul", "Africa"]
	secondary_regions = ["Germania", "Steppe", "Iberia"]
	tertiary_regions = ["Dacia", "Morocco", "Bosporus", "Portugal", "Sicilies"]

	civ_mapping = {
		# for Classical games
		"CIVILIZATION_ROME":	"Rome",
		"CIVILIZATION_GREECE":	"Greece",
		"CIVILIZATION_CARTHAGE":	"Africa",
		"CIVILIZATION_PERSIA":	"Syria",
		"CIVILIZATION_CELT":	"Gaul",
		"CIVILIZATION_EGYPT":	"Egypt",
		"CIVILIZATION_MONGOL":	"Steppe",
		
		# for medieval games
		"CIVILIZATION_SPAIN":	"Iberia",
		"CIVILIZATION_HOLY_ROME":	"Germania",
		"CIVILIZATION_GERMANY":	"Germania",
		"CIVILIZATION_MALI":	"Morocco",
		"CIVILIZATION_ETHIOPIA":	"Morocco",
		"CIVILIZATION_PORTUGAL":	"Portugal",
		"CIVILIZATION_VIKING":	"Sicilies",	# Norman Kingdoms of Sicily
		"CIVILIZATION_FRANCE":	"Gaul",
		"CIVILIZATION_BYZANTINE":	"Bosporus",
		"CIVILIZATION_OTTOMAN":	"Bosporus",
		"CIVILIZATION_RUSSIA":	"Steppe",
	}

	all_players = []
	for i in range(gc.getMAX_CIV_PLAYERS()):
		player = gc.getPlayer(i)
		if player.isEverAlive():
			all_players.append(i)
	
	# --- PHASE 1: Fixed Assignments ---
	if start_option == 1:
		# Call this here to place Debug signs on the map
		_add_spawn_signs(SPAWN_REGIONS)
		
		for playerID in all_players:
			civ_str = gc.getCivilizationInfo(gc.getPlayer(playerID).getCivilizationType()).getType()
			region_name = civ_mapping.get(civ_str)
			
			if region_name and region_name not in used_regions:
				data = SPAWN_REGIONS[region_name]
				# Center-based rect: (cX, cY, w, h)
				rect = (data[0], data[1], data[2], data[3])
				plot_index = _find_plot_in_rect(rect, "Fixed: " + region_name, assigned_coords, 4, data[4], data[5])
				
				if plot_index != -1:
					final_assignments[playerID] = plot_index
					print "MAP DEBUG: Fixed Start - %s assigned to %s" % (civ_str, region_name)
					p = map.plotByIndex(plot_index)
					assigned_coords.append((p.getX(), p.getY()))
					used_regions.add(region_name)
					continue 
			unassigned_players.append(playerID)
	else:
		unassigned_players = all_players

	# --- PHASE 2: Prioritized Regional Shuffle ---
	if start_option == 1 and unassigned_players:
		print "MAP DEBUG: Attempting prioritized historical region assignment"
		unassigned_players = _synced_shuffle(dice, unassigned_players)
		
		p_avail = []
		for r in primary_regions:
			if r not in used_regions: p_avail.append(r)
		s_avail = []
		for r in secondary_regions:
			if r not in used_regions: s_avail.append(r)
			
		available_regions = _synced_shuffle(dice, p_avail) + _synced_shuffle(dice, s_avail)
		
		still_unassigned = []
		for playerID in unassigned_players:
			civ_str = gc.getCivilizationInfo(gc.getPlayer(playerID).getCivilizationType()).getType()
			if available_regions:
				fallback_region = available_regions.pop(0)
				data = SPAWN_REGIONS[fallback_region]
				rect = (data[0], data[1], data[2], data[3])
				plot_index = _find_plot_in_rect(rect, "Region-Shuffle: " + fallback_region, assigned_coords, 4, data[4], data[5])
				if plot_index != -1:
					final_assignments[playerID] = plot_index
					print "MAP DEBUG: Region-Shuffle - %s assigned to %s" % (civ_str, fallback_region)
					p = map.plotByIndex(plot_index)
					assigned_coords.append((p.getX(), p.getY()))
				else:
					still_unassigned.append(playerID)
			else:
				still_unassigned.append(playerID)
		unassigned_players = still_unassigned

	# --- PHASE 3: Generic Fallback ---
	if unassigned_players:
		for playerID in unassigned_players:
			plot_index = _fallback_start_placement(playerID, assigned_coords)
			if plot_index != -1:
				final_assignments[playerID] = plot_index
				civ_str = gc.getCivilizationInfo(gc.getPlayer(playerID).getCivilizationType()).getType()
				p = map.plotByIndex(plot_index)
				print "MAP DEBUG: Generic Fallback - %s assigned to (%d, %d)" % (civ_str, p.getX(), p.getY())
				assigned_coords.append((p.getX(), p.getY()))
				
	return final_assignments


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
			WorldSizeTypes.WORLDSIZE_DUEL:     0.5,
			WorldSizeTypes.WORLDSIZE_TINY:     0.5,
			WorldSizeTypes.WORLDSIZE_SMALL:    1,
			WorldSizeTypes.WORLDSIZE_STANDARD: 1,
			WorldSizeTypes.WORLDSIZE_LARGE:    1.34,
			WorldSizeTypes.WORLDSIZE_HUGE:     1.5,
		}

	def _bonus_id(self, name):
		if name in self._cache: return self._cache[name]
		bid = self.gc.getInfoTypeForString(name)
		self._cache[name] = bid
		return bid

	def ensure_bonus_per_grid(self, bonus_names, iGridSize):
		"""Ensure each map-grid block contains at least one listed bonus."""
		if iGridSize <= 0:
			return

		bonus_ids = []
		bonus_lookup = {}
		for bonus_name in bonus_names:
			bonus_id = self._bonus_id(bonus_name)
			bonus_ids.append(bonus_id)
			bonus_lookup[bonus_id] = 1

		start_lookup = {}
		for iPlayer in range(self.gc.getMAX_CIV_PLAYERS()):
			pPlayer = self.gc.getPlayer(iPlayer)
			if pPlayer.isEverAlive():
				pStart = pPlayer.getStartingPlot()
				if pStart and not pStart.isNone():
					start_lookup[(pStart.getX(), pStart.getY())] = 1

		iBlocksChecked = 0
		iBlocksSatisfied = 0
		iPlaced = 0
		iBlocked = 0

		for xMin in range(0, self.iW, iGridSize):
			for yMin in range(0, self.iH, iGridSize):
				iBlocksChecked += 1
				xMax = xMin + iGridSize
				yMax = yMin + iGridSize
				if xMax > self.iW: xMax = self.iW
				if yMax > self.iH: yMax = self.iH

				iExisting = 0
				plots = []
				for x in range(xMin, xMax):
					for y in range(yMin, yMax):
						pPlot = self.map.plot(x, y)
						if bonus_lookup.has_key(pPlot.getBonusType(-1)):
							iExisting += 1
						plots.append(pPlot)

				if iExisting > 0:
					iBlocksSatisfied += 1
					continue

				plots = _synced_shuffle(self.dice, plots)
				shuffled_bonus_ids = _synced_shuffle(self.dice, bonus_ids)
				bPlaced = False
				for pPlot in plots:
					if pPlot.getBonusType(-1) != -1: continue
					if pPlot.isWater() or pPlot.isPeak(): continue
					if pPlot.isStartingPlot(): continue
					if start_lookup.has_key((pPlot.getX(), pPlot.getY())): continue
					for bonus_id in shuffled_bonus_ids:
						if pPlot.canHaveBonus(bonus_id, True):
							pPlot.setBonusType(bonus_id)
							iPlaced += 1
							bPlaced = True
							break
					if bPlaced:
						break

				if not bPlaced:
					iBlocked += 1

		print "Mediterranean map food scan: checked %d blocks, satisfied %d, placed %d, blocked %d" % (iBlocksChecked, iBlocksSatisfied, iPlaced, iBlocked)

	def _is_bonus_appropriate_for_plot(self, bonus_id, pPlot):
		"""
		Checks if the bonus is physically compatible with the plot's 
		terrain, topography, and feature, ignoring proximity and latitude.
		"""
		info = self.gc.getBonusInfo(bonus_id)
		
		# 1. Check Topography (Hills vs Flat)
		if pPlot.isHills():
			if not info.isHills(): return False
		else:
			if not info.isFlatlands(): return False
			
		# 2. Check Terrain
		if not info.isTerrain(pPlot.getTerrainType()):
			return False
			
		# 3. Check Feature
		iFeature = pPlot.getFeatureType()
		if iFeature != -1:
			if not info.isFeature(iFeature):
				# Special case: If it's a feature we are willing to clear (Forest/Jungle)
				# and the bonus is valid on the underlying terrain, we count it as 'appropriate'
				# because our placement logic handles the clearing.
				iFloodplains = self.gc.getInfoTypeForString("FEATURE_FLOOD_PLAINS")
				if iFeature == iFloodplains: return False # Floodplains usually strictly defined in XML
				
				# If the bonus can't exist with the feature AND we aren't allowed to clear it, return False
				# But for your script, we usually assume we can clear Forest/Jungle for a Tier 1 match.
				if not info.isTerrain(pPlot.getTerrainType()):
					return False

		return True

	def _is_bonus_appropriate_plot_type(self, bonus_id, pPlot):
		"""
		Checks only whether the bonus can use this plot's topography.
		Used as the fallback tier for region-specific placement.
		"""
		if pPlot.isWater(): return False
		if pPlot.getPlotType() == PlotTypes.PLOT_PEAK: return False

		info = self.gc.getBonusInfo(bonus_id)
		if pPlot.isHills():
			if not info.isHills(): return False
		else:
			if not info.isFlatlands(): return False

		return True
	
	def place_bonus_in_BFC(self, bonus_list, count=1, check_existence=False):
		"""
		Tiered placement logic for LAND starting resources.
		1. Natural Fit: Shuffles bonuses and finds a tile that matches terrain requirements.
		2. Emergency: Terraforms a foodless tile to Plains Flat and picks a valid bonus.
		"""
		ids = []
		for b in bonus_list:
			ids.append(self._bonus_id(b))

		iPlains = self.gc.getInfoTypeForString("TERRAIN_PLAINS")
		iDesert = self.gc.getInfoTypeForString("TERRAIN_DESERT")
		iFloodplains = self.gc.getInfoTypeForString("FEATURE_FLOOD_PLAINS")

		players = []
		for i in range(self.gc.getMAX_CIV_PLAYERS()):
			player = self.gc.getPlayer(i)
			if player.isEverAlive():
				pStart = player.getStartingPlot()
				if pStart and not pStart.isNone():
					players.append((player.getID(), pStart.getX(), pStart.getY()))

		for (pid, sx, sy) in players:
			# 1. Define the Big Fat Cross (21 tiles)
			bfc_offsets = []
			for dx in range(-2, 3):
				for dy in range(-2, 3):
					if dx == 0 and dy == 0: continue 
					if abs(dx) == 2 and abs(dy) == 2: continue 
					bfc_offsets.append((dx, dy))

			# 2. Count existing resources from the list in the BFC (Exclude the center tile)
			existing_count = 0
			if check_existence:
				for dx, dy in bfc_offsets:
					nx, ny = sx + dx, sy + dy
					if 0 <= nx < self.iW and 0 <= ny < self.iH:
						pPlot = self.map.plot(nx, ny)
						if pPlot.isStartingPlot(): continue
						if pPlot.getBonusType(-1) in ids:
							existing_count += 1
			
			needed = count - existing_count
			
			# 3. Placement Loop: Run for every bonus still required
			for i in range(needed):
				# Shuffle the full list for every individual placement attempt
				shuffled_ids = _synced_shuffle(self.dice, ids[:])
				placed_successfully = False

				# --- TIER 1: NATURAL FIT ---
				# We iterate through the shuffled bonuses. If Bonus A doesn't fit 
				# anywhere in the BFC, we move to Bonus B.
				for chosen_id in shuffled_ids:
					tier1_plots = []
					for dx, dy in bfc_offsets:
						nx, ny = sx + dx, sy + dy
						if 0 <= nx < self.iW and 0 <= ny < self.iH:
							pPlot = self.map.plot(nx, ny)
							
							# Filter: No starts, no existing bonuses, NO WATER, NO PEAKS
							if pPlot.isStartingPlot() or pPlot.getBonusType(-1) != -1: continue
							if pPlot.isWater() or pPlot.isPeak(): continue

							# Use our manual check to see if the bonus fits this tile's terrain
							if self._is_bonus_appropriate_for_plot(chosen_id, pPlot):
								tier1_plots.append(pPlot)

					if len(tier1_plots) > 0:
						target_plot = tier1_plots[self.dice.get(len(tier1_plots), "T1 Plot")]
						
						# Handle feature clearing (Forest/Jungle), but keep Floodplains
						current_feature = target_plot.getFeatureType()
						if current_feature != -1 and current_feature != iFloodplains:
							# Clear feature if the bonus can't naturally sit on it (e.g. Wheat in Forest)
							if not target_plot.canHaveBonus(chosen_id, True):
								target_plot.setFeatureType(FeatureTypes.NO_FEATURE, -1)

						target_plot.setBonusType(chosen_id)
						placed_successfully = True
						break # Successfully placed a Tier 1 bonus, move to next 'needed'

				# --- TIER 2: EMERGENCY TERRAFORM ---
				# Runs only if NO bonus in the list fits naturally anywhere in the BFC
				if not placed_successfully:
					emergency_plots = []
					for dx, dy in bfc_offsets:
						nx, ny = sx + dx, sy + dy
						if 0 <= nx < self.iW and 0 <= ny < self.iH:
							pPlot = self.map.plot(nx, ny)
							if pPlot.isStartingPlot() or pPlot.getBonusType(-1) != -1: continue
							if pPlot.isWater() or pPlot.isPeak(): continue

							# Target: Desert, Hills, or Floodplains (all considered 'foodless' candidates)
							# calculateNatureYield(Yield, Team, bIgnoreFeature)
							if pPlot.calculateNatureYield(YieldTypes.YIELD_FOOD, TeamTypes.NO_TEAM, False) == 0:
								emergency_plots.append(pPlot)
							elif pPlot.getFeatureType() == iFloodplains:
								emergency_plots.append(pPlot)

					if len(emergency_plots) > 0:
						target_plot = emergency_plots[self.dice.get(len(emergency_plots), "Emergency Plot")]
						
						# 1. Terraform to Plains Flatland
						target_plot.setPlotType(PlotTypes.PLOT_LAND, True, True)
						target_plot.setTerrainType(iPlains, True, True)
						target_plot.setFeatureType(FeatureTypes.NO_FEATURE, -1)

						# 2. Re-filter the shuffled list for the new Plains Flatland tile
						for b_id in shuffled_ids:
							if self._is_bonus_appropriate_for_plot(b_id, target_plot):
								target_plot.setBonusType(b_id)
								placed_successfully = True
								break
						
						# 3. Brute Force: If for some reason nothing fit the manual check, force the first one
						if not placed_successfully:
							target_plot.setBonusType(shuffled_ids[0])

	def place_bonus_in_radius(self, bonus_list, iTargetCount, iCopies, radius):
		if iTargetCount < 1: iTargetCount = 1
		if iCopies < 1: iCopies = 1

		ids = []
		for b in bonus_list:
			ids.append(self._bonus_id(b))

		players = []
		start_lookup = {}
		for i in range(self.gc.getMAX_CIV_PLAYERS()):
			player = self.gc.getPlayer(i)
			if player.isEverAlive():
				pStart = player.getStartingPlot()
				if pStart and not pStart.isNone():
					players.append((player.getID(), pStart.getX(), pStart.getY(), pStart.getArea()))
					start_lookup[(pStart.getX(), pStart.getY())] = 1

		for (pid, sx, sy, iStartArea) in players:
			present = {}

			for dx in range(-radius, radius + 1):
				for dy in range(-radius, radius + 1):
					nx, ny = sx + dx, sy + dy
					if 0 <= nx < self.iW and 0 <= ny < self.iH:
						if plotDistance(sx, sy, nx, ny) <= radius:
							pPlot = self.map.plot(nx, ny)
							if pPlot.getArea() != iStartArea: continue
							iBonus = pPlot.getBonusType(TeamTypes.NO_TEAM)
							if iBonus in ids:
								present[iBonus] = 1

			iPresent = len(present.keys())
			if iPresent >= iTargetCount:
				print "Mediterranean radius bonus skipped player %d. Found %d existing bonus types" % (pid, iPresent)
				continue

			missing_ids = []
			for iBonus in ids:
				if not present.has_key(iBonus):
					missing_ids.append(iBonus)

			missing_ids = _synced_shuffle(self.dice, missing_ids)
			iNeededTypes = iTargetCount - iPresent
			if iNeededTypes > len(missing_ids): iNeededTypes = len(missing_ids)

			for iType in range(iNeededTypes):
				chosen_id = missing_ids[iType]
				placed = 0

				for iCopy in range(iCopies):
					tier1_plots = []
					for dx in range(-radius, radius + 1):
						for dy in range(-radius, radius + 1):
							nx, ny = sx + dx, sy + dy
							if 0 <= nx < self.iW and 0 <= ny < self.iH:
								if plotDistance(sx, sy, nx, ny) <= radius:
									pPlot = self.map.plot(nx, ny)
									if pPlot.getArea() != iStartArea: continue
									if pPlot.isStartingPlot() or start_lookup.has_key((nx, ny)): continue
									if pPlot.getBonusType(-1) != -1: continue
									if pPlot.isWater() or pPlot.isPeak(): continue
									if self._is_bonus_appropriate_for_plot(chosen_id, pPlot):
										tier1_plots.append(pPlot)

					target_plot = None
					if len(tier1_plots) > 0:
						target_plot = tier1_plots[self.dice.get(len(tier1_plots), "Mediterranean Radius T1")]
					else:
						emergency_plots = []
						for dx in range(-radius, radius + 1):
							for dy in range(-radius, radius + 1):
								nx, ny = sx + dx, sy + dy
								if 0 <= nx < self.iW and 0 <= ny < self.iH:
									if plotDistance(sx, sy, nx, ny) <= radius:
										pPlot = self.map.plot(nx, ny)
										if pPlot.getArea() != iStartArea: continue
										if pPlot.isWater() or pPlot.isPeak(): continue
										if pPlot.isStartingPlot() or start_lookup.has_key((nx, ny)): continue
										if pPlot.getBonusType(-1) != -1: continue
										if pPlot.getFeatureType() != -1: continue
										emergency_plots.append(pPlot)

						if len(emergency_plots) > 0:
							target_plot = emergency_plots[self.dice.get(len(emergency_plots), "Mediterranean Radius Emergency")]

					if target_plot:
						target_plot.setBonusType(chosen_id)
						bonus_name = self.gc.getBonusInfo(chosen_id).getType()
						print "Mediterranean radius placed %s for player %d at (%d, %d)" % (bonus_name, pid, target_plot.getX(), target_plot.getY())
						placed += 1

				if placed < iCopies:
					print "Mediterranean radius placed only %d of %d copies for player %d" % (placed, iCopies, pid)


	def swap_resources(self, swap_rules, clear_feature=False):
		"""
		Swaps resources globally. Now explicitly skips starting plots to 
		prevent accidental changes to the capital's immediate tile.
		"""
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
				# EXCLUDE starting plots from global swaps
				if pPlot.isStartingPlot(): continue
				
				if pPlot.getY() >= y_thresh and pPlot.getBonusType(-1) == old_id:
					if new_name:
						pPlot.setBonusType(self._bonus_id(new_name))
					else:
						pPlot.setBonusType(-1)
					
					if clear_feature:
						pPlot.setFeatureType(FeatureTypes.NO_FEATURE, -1)

	def _is_feature_allowed_for_bonus(self, bonus_id, feature_id):
		if feature_id == -1:
			return True

		bonusInfo = self.gc.getBonusInfo(bonus_id)
		iFeatureCount = self.gc.getNumFeatureInfos()
		for i in range(iFeatureCount):
			if i == feature_id:
				if bonusInfo.isFeature(i):
					return True
				return False

		return False

	def _is_clearable_bonus_feature(self, feature_id):
		if feature_id == -1:
			return False

		iForest = self.gc.getInfoTypeForString("FEATURE_FOREST")
		iJungle = self.gc.getInfoTypeForString("FEATURE_JUNGLE")
		return (feature_id == iForest or feature_id == iJungle)

	def add_region_specific(self, region_specs, bChangePlains=False):
		"""
		Place bonuses in specified regions using center-based coordinates. 
		region["rect"] format: (cX, cY, width, height)
		region["bonuses"] entry format: (bonus_type, count, bChangePlains)
		"""
		multiplier = self.size_multiplier[self.world_size]
		iPlains = self.gc.getInfoTypeForString("TERRAIN_PLAINS")
		
		for region in region_specs:
			# Unpack center-based coordinates
			cX, cY, width, height = region["rect"]
			
			# Calculate pixel-grid boundaries from center
			west_x = int(self.iW * (cX - (width / 2.0)))
			east_x = int(self.iW * (cX + (width / 2.0)))
			south_y = int(self.iH * (cY - (height / 2.0)))
			north_y = int(self.iH * (cY + (height / 2.0)))

			# Clamp to map edges
			iWest = max(0, west_x)
			iEast = min(self.iW - 1, east_x)
			iSouth = max(0, south_y)
			iNorth = min(self.iH - 1, north_y)

			for bonus_entry in region["bonuses"]:
				scaled_count = int(bonus_entry[1] * multiplier)
				if scaled_count == 0: 
					continue
					
				bonus_id = self._bonus_id(bonus_entry[0])
				if len(bonus_entry) > 2:
					bBonusChangePlains = bonus_entry[2]
				else:
					bBonusChangePlains = False
				
				eligible = []
				feature_fallback = []
				plot_type_fallback = []
				
				# Scan the calculated rectangle
				for x in range(iWest, iEast + 1):
					for y in range(iSouth, iNorth + 1):
						pPlot = self.map.plot(x, y)
						
						# EXCLUDE starting plots from region-specific placement
						if pPlot.isStartingPlot(): 
							continue
						
						if pPlot.getBonusType(-1) == -1:
							if pPlot.canHaveBonus(bonus_id, True):
								eligible.append((x, y))
							else:
								iFeature = pPlot.getFeatureType()
								bFeatureAllowed = self._is_feature_allowed_for_bonus(bonus_id, iFeature)
								bClearableFeature = self._is_clearable_bonus_feature(iFeature)

								if (not bFeatureAllowed and bClearableFeature and
									self._is_bonus_appropriate_for_plot(bonus_id, pPlot)):
									feature_fallback.append((x, y))
								elif bBonusChangePlains and self._is_bonus_appropriate_plot_type(bonus_id, pPlot):
									# Terrain fallback may keep a supported feature or clear Forest/Jungle only.
									if bFeatureAllowed or bClearableFeature:
										plot_type_fallback.append((x, y))

				# Placement Loop
				placed = 0
				for _ in range(scaled_count):
					choice = None
					bChangeTerrain = False
					bClearFeature = False
					if eligible:
						choice = eligible.pop(self.dice.get(len(eligible), "Region Bonus"))
					elif feature_fallback:
						choice = feature_fallback.pop(self.dice.get(len(feature_fallback), "Feature Fallback Bonus"))
						bClearFeature = True
					elif plot_type_fallback:
						choice = plot_type_fallback.pop(self.dice.get(len(plot_type_fallback), "Fallback Bonus"))
						bChangeTerrain = True
					
					if choice:
						p = self.map.plot(choice[0], choice[1])
						if bChangeTerrain:
							p.setTerrainType(iPlains, True, True)
						if bClearFeature or bChangeTerrain:
							iFeature = p.getFeatureType()
							if (not self._is_feature_allowed_for_bonus(bonus_id, iFeature) and
								self._is_clearable_bonus_feature(iFeature)):
								p.setFeatureType(FeatureTypes.NO_FEATURE, -1)
						p.setBonusType(bonus_id)
						placed += 1

def addCustomResources(): # <- Add Custom Resources Here
	m = CyMap()
	gc = CyGlobalContext()
	dice = gc.getGame().getMapRand()
	iW = m.getGridWidth()
	iH = m.getGridHeight()
	rm = ResourceManager(m, gc, dice, iW, iH)
	
	# Custom Options
	map_food_option = m.getCustomMapOption(7)
	food_count = m.getCustomMapOption(8) # 0, 1, or 2
	bHistorical = (m.getCustomMapOption(6) == 1)

	# Strategic resources
	Strategics = ["BONUS_COPPER", "BONUS_IRON", "BONUS_HORSE"]
	Late_Strategics = ["BONUS_COAL", "BONUS_URANIUM", "BONUS_ALUMINUM", "BONUS_OIL"]
	rm.place_bonus_in_radius(Strategics, 3, 1, 4)
	rm.place_bonus_in_radius(Late_Strategics, 4, 1, 5)

	# Map-wide Swaps
	if bHistorical:  
		swap_rules =[]
		swap_rules.append(("BONUS_CORN", "BONUS_WHEAT")) # Swap corn for wheat
		swap_rules.append(("BONUS_SILK", None)) # Wipe
		swap_rules.append(("BONUS_SPICES", None)) # Wipe
		swap_rules.append(("BONUS_SUGAR", None)) # Wipe
		swap_rules.append(("BONUS_IVORY", None)) # Wipe
		rm.swap_resources(swap_rules)
	
	# Region-specific resources
	if bHistorical:
		region_specs = [
			{
				"name": "Egypt",
				"rect": (0.812, 0.133, 0.11, 0.217),
				"bonuses": [
					("BONUS_STONE", 1, True),
					("BONUS_WHEAT", 2, True),
					("BONUS_IVORY", 1, False),
				]
			},
			{
				"name": "Syria",
				"rect": (0.965, 0.383, 0.13, 0.215),
				"bonuses": [
					("BONUS_DYE", 2, True),
					("BONUS_SPICES", 2, False),
					("BONUS_SUGAR", 2, True),
					("BONUS_SILK", 2, False),
					("BONUS_WHEAT", 2, False),
				]
			},
			{
				"name": "Po_Valley",
				"rect": (0.419, 0.761, 0.133, 0.115),
				"bonuses": [
					("BONUS_WHEAT", 2, False),
					("BONUS_WINE", 1, False),
				]
			},
			{
				"name": "Greece",
				"rect": (0.627, 0.453, 0.112, 0.238),
				"bonuses": [
					("BONUS_SHEEP", 1, False),
					("BONUS_WINE", 2, False),
					("BONUS_MARBLE", 1, False),
					("BONUS_SILVER", 1, False),
				]
			},
			{
				"name": "Carthage",
				"rect": (0.362, 0.334, 0.112, 0.227),
				"bonuses": [
					("BONUS_WHEAT", 1, False),
					("BONUS_MARBLE", 1, False),
					("BONUS_IVORY", 1, False),
				]
			},
			{
				"name": "Iberia",
				"rect": (0.11, 0.656, 0.169, 0.33),
				"bonuses": [
					("BONUS_GEMS", 1, True),
					("BONUS_SILVER", 1, True),
					("BONUS_WINE", 1, False),
				]
			},
			{
				"name": "Germania",
				"rect": (0.483, 0.935, 0.215, 0.149),
				"bonuses": [
					("BONUS_GOLD", 1, False),
					("BONUS_GEMS", 1, True),
					("BONUS_FUR", 1, False),
				]
			},
			{
				"name": "Gaul",
				"rect": (0.266, 0.882, 0.137, 0.262),
				"bonuses": [
					("BONUS_PIG", 2, False),
					("BONUS_WINE", 1, False),
					("BONUS_GEMS", 1, False),
				]
			},
			{
				"name": "Italy",
				"rect": (0.459, 0.574, 0.103, 0.194),
				"bonuses": [
					("BONUS_IRON", 1, False),
					("BONUS_WINE", 1, False),
					("BONUS_MARBLE", 1, False),
				]
			},
			{
				"name": "Morocco",
				"rect": (0.069, 0.32, 0.132, 0.183),
				"bonuses": [
					("BONUS_GOLD", 1, False),
					("BONUS_FUR", 1, True),
				]
			},
			{
				"name": "Libya",
				"rect": (0.525, 0.138, 0.189, 0.186),
				"bonuses": [
					("BONUS_WINE", 2, True),
					("BONUS_FUR", 1, True),
				]
			},
			{
				"name": "Steppe",
				"rect": (0.858, 0.847, 0.215, 0.215),
				"bonuses": [
					("BONUS_FUR", 2, False),
					("BONUS_SHEEP", 1, False),
				]
			},
			{
				"name": "Arabia",
				"rect": (0.957, 0.111, 0.103, 0.195),
				"bonuses": [
					("BONUS_SHEEP", 1, True),
					("BONUS_INCENSE", 2, False),
					("BONUS_CLAM", 1, False),
				]
			},
			{
				"name": "Pontus",
				"rect": (0.886, 0.623, 0.146, 0.126),
				"bonuses": [
					("BONUS_SILVER", 1, False),
				]
			},
			{
				"name": "Asia",
				"rect": (0.801, 0.467, 0.104, 0.152),
				"bonuses": [
					("BONUS_MARBLE", 1, False),
				]
			},
			{
				"name": "Cyprus",
				"rect": (0.848, 0.327, 0.082, 0.11),
				"bonuses": [
					("BONUS_COPPER", 1, False),
				]
			},
			{
				"name": "Carpathia",
				"rect": (0.646, 0.796, 0.12, 0.126),
				"bonuses": [
					("BONUS_GOLD", 1, True),
				]
			},
		]
		rm.add_region_specific(region_specs, bChangePlains=True)

	# Food resources
	food_list = ["BONUS_WHEAT", "BONUS_RICE", "BONUS_COW", "BONUS_SHEEP", "BONUS_PIG", "BONUS_DEER"]
	if map_food_option != 0:
		map_food_list = food_list 
		rm.ensure_bonus_per_grid(map_food_list, map_food_option + 3)
	rm.place_bonus_in_BFC(food_list, count=food_count, check_existence=True)
