# Creating Artificial GPS-tracks

This collection of python script allows for the creation of artificial GPS tracks. It builds on the ideas of Thierry, Chaix, and Kestens (2013) they put forward in "Detecting activity locations from raw GPS data: a novel kernel-based algorith" (International Journal of Health Geography. The workflow of Ian Broad (http://ianbroad.com/download/script/CreatePointsLines.py) is used and adjusted to transform polylines (step 4; see below) to points.

## Requirements
1) Python with the following packages:
- arcpy
- pandas
- numpy

2) Flowmap (http://flowmap.geo.uu.nl/). Alternatively the ArcGIS network analysist can be used; but this requries an adjustment of the code. Script requires base Flomwap scripts to import points and execute shortest path analysis; examples attached.

3) Road network (topologically correct) with attribute values for shortest path analysis.

## Usage
Adjust files, pathnames according to needs (for each script), and run scripts in order. 

## Steps
1.	Selection of a random number of random activity location (minimum of two, maximum of nine) within a set study area.

2.	Random assignment of a duration classification to each of the activities (short, medium, long). After randomly assigning a duration classification to each activity, the actual duration of the activity is determined using a Poisson distribution. The seed value is randomly drawn from a normal distribution with the following parameters:

- A mean of 8 minutes and a standard deviation of 3 minutes for activities with a short duration (e.g. picking someone up).
-	A mean of 50 minutes and a standard deviation of 10 minutes for activities with a medium duration (e.g. buying groceries).
- A mean of 300 and a standard deviation of 60 minutes for activities with a long duration (e.g. work, school).

3.	Generation of activity points (one every 30 seconds) around the activity locations. GPS noise is simulated by shifting the coordinates from the original identified activity location. The shifts follow a bi-dimensional normal distribution centred around 0 with a standard deviation that is randomly drawn from a uniform distribution ranging from 10 to 200 meter.

4.	Connection of the generated activity locations sequence (e.g. Activity 1 to Activity 2, Activity 2 to Activity 3, etc.) using shortest path analysis in Flowmap.

5.	Transformation of the resulting polylines into points and a random assignment of a transport mode. The spacing of the points is based on the measurement frequency (30 seconds) as well as the speed of the assigned transport mode. The speeds for each point are recursively drawn from a normal distribution with the following parameters:

-	A mean of 80 km/h and a standard deviation of 10 km/h for a car driving fast (e.g. freeway).
-	A mean of 60 km/h and a standard deviation of 5 km/h for a car driving normally (e.g. urban setting).
-	A mean of 20 km/h and a standard deviation of 5 km/h for a car driving slowly (e.g. in a living area).
-	A mean of 15 km/h and a standard deviation of 3 km/h for cycling.
-	A mean of 5 km/h and a standard deviation of 2 km/h for walking. 
 
6.	Introduction of noise in GPS tracks by randomly shifting the trip points along their X and Y axes; the shifts followed a bi-dimensional normal distribution with a mean of 0 metres and a standard deviation of 10 metres.

7.	Merging of the activity points and the track points to get the artificial activity travel sequence. 

8.	Calculation of attribute values (e.g. speed, acceleration, distance to road network, etc.).

Author: Justin van Dijk

Created: 25/04/2017
