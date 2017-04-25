# -*- coding: utf-8 -*-
#===============================================================================
# JTVD - 2017
#===============================================================================

#===============================================================================
# SET PARAMETERS
#===============================================================================


#Import modules
import arcpy, os, datetime
from arcpy import env
from random import randrange
from math import hypot

#Set start folder and workspace accordingly
activities = r"path to folder where to save origin / destination locatins"
tracks = r"path to folder where to save tracks between origin / destination locatins"
save = r"path to folder where to save final output"
env.workspace = activities

#Set environment
env.overwriteOutput = True
env.parallelProcessingFactor = "4"

#Set coordinate system tracks
wgs84 = arcpy.SpatialReference(4326)
hart94 = "PROJCS['Hartebeesthoek94_Lo19',GEOGCS['GCS_Hartebeesthoek_1994',DATUM['D_Hartebeesthoek_1994',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',19.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
transformation = "Hartebeesthoek94_To_WGS_1984"

#Set track date
date = "04/02/1989"

#Set track start time
time_earliest = "06:00:00"
time_latest = "08:00:00"
measurement_freq = 30

#Set moving window (minutes)
window = 10

#===============================================================================
# DEFINE FUNCTIONS
#===============================================================================

def FieldExist(featureclass, fieldname):
    fieldList = arcpy.ListFields(featureclass, fieldname)

    fieldCount = len(fieldList)

    if (fieldCount == 1):
        return True
    else:
        return False

def calc_bearing(pointA, pointB):
    #https://gist.github.com/jeromer/2005586
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

#===============================================================================
# INTRODUCE NOISE STOP LOCATIONS
#===============================================================================

#Get tracks
activity_fc = arcpy.ListFeatureClasses("NOISE*")

#Loop through tracks
for p in activity_fc:
    
    merge = []
    merge.append(p)

    #Get number of unique activities in file
    stops = []
    with arcpy.da.SearchCursor(p, ["STOP"]) as cursor:
        for row in cursor:
            stops.append(row[0])

    #Set ID counter
    count = 0
    
    #Loop through and add ID's
    for i in range(1, int(max(stops))):

        #Get track
        track = os.path.join(tracks, "NOISE_POINTS" + str(p[9:12]) + "AC" + str(i) + "AC" + str(i+1) + ".shp")
        if arcpy.Exists(track):
            track_count = arcpy.GetCount_management(track).getOutput(0)
            merge.append(track)
            if not FieldExist(track, "POINT_ID_N"):
                arcpy.AddField_management(track, "POINT_ID_N", "DOUBLE")

            #Count activities
            fields = ["STOP", "POINT_ID_N"]
            with arcpy.da.UpdateCursor(p, fields) as cursor:
                for row in cursor:
                    if row[0] == i:
                        count = count + 1
                        row[1] = count
                    cursor.updateRow(row)

            #Count track
            fields = ["POINT_ID_N"]
            with arcpy.da.UpdateCursor(track, fields) as cursor:
                for row in cursor:
                    count = count + 1
                    row[0] = count
                    cursor.updateRow(row)
        
    #Count activities
    fields = ["STOP", "POINT_ID_N"]
    with arcpy.da.UpdateCursor(p, fields) as cursor:
        for row in cursor:
            if row[0] == int(max(stops)):
                count = count + 1
                row[1] = count
                cursor.updateRow(row)

    #Merge files
    output_memory = os.path.join("in_memory", "RANDOM_" + str(p[9:12]))
    arcpy.Merge_management(merge, output_memory)
    
    #Save output
    output = os.path.join(save, "RANDOM_" + str(p[9:12] + ".shp"))
    arcpy.Sort_management(output_memory, output, [["POINT_ID_N", "ASCENDING"]])
    print output

    #Add Date and Time variable
    if not FieldExist(output, "TIMESTAMP"):
        arcpy.AddField_management(output, "TIMESTAMP", "TEXT")

    if FieldExist(output, "DATETIME"):
        arcpy.DeleteField_management(output, "TIMESTAMP1")
        
    #Randomly select Start time 
    start_time = datetime.datetime.strptime(date + " " + time_earliest, "%d/%m/%Y %H:%M:%S")
    end_time = datetime.datetime.strptime(date + " " + time_latest, "%d/%m/%Y %H:%M:%S")
    delta = end_time - start_time
    int_delta = (delta.days *24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    stime = start_time + datetime.timedelta(seconds=random_second)

    #Calculate Date and Time variable
    fields = ["TIMESTAMP"]
    counttime = 0
    with arcpy.da.UpdateCursor(output, fields) as cursor:
        for row in cursor:
            seconds_dif = counttime*measurement_freq
            time1 = stime
            time2 = time1 + datetime.timedelta(seconds=seconds_dif)
            row[0] = time2
            counttime = counttime + 1
            cursor.updateRow(row)

    with arcpy.da.UpdateCursor(output, fields) as cursor:
        for row in cursor:
            if len(row[0]) == 10:
                row[0] = row[0] + " 00:00:00"
            cursor.updateRow(row)
            
    #Add TrackID
    if not FieldExist(output, "TRACK_ID"):
        arcpy.AddField_management(output, "TRACK_ID", "TEXT")
    arcpy.CalculateField_management(output, "TRACK_ID", '"'+p[9:12]+'"')
    
    #Get coordinates of each feature (in PCS) and store it as a list of tuples.
    coord = [x[0] for x in arcpy.da.SearchCursor(output, "SHAPE@XY")]

    #Compute distances between features
    distances = [hypot(coord[i+1][0]-coord[i][0],
                   coord[i+1][1]-coord[i][1]) for i,_ in enumerate(coord[:-1])]

    #Insert a 0 in the first position since it has nothing to measure against
    distances.insert(0, 0)

    #Add field to store distances
    if not FieldExist(output, "DIST"):
        arcpy.AddField_management(output, "DIST", "DOUBLE")

    #Write distances to shapefile.
    with arcpy.da.UpdateCursor(output, "DIST") as rows:
        for j,row in enumerate(rows):
            row[0] = distances[j]
            rows.updateRow(row)

    #Compute time between features
    tt = [x[0] for x in arcpy.da.SearchCursor(output, "TIMESTAMP")]

    #Calculate difference in time between consecutive points
    delta = [(datetime.datetime.strptime(tt[i+1], "%d/%m/%Y %H:%M:%S")) - (datetime.datetime.strptime(tt[i], "%d/%m/%Y %H:%M:%S")) for i,_ in enumerate(tt[:-1])]

    #Create new empty tuple to store the seconds
    deltasec = []

    #Append all values in seconds to new tuple
    for i in delta:
        deltasec.append((i).total_seconds())

    #Insert a 0 in the first position since it has nothing to measure against
    deltasec.insert(0,0)

    #Add field to store time differences
    if not FieldExist(output, "TIME_DIF"):
        arcpy.AddField_management(output, "TIMEDIF", "DOUBLE")

    #Write times back to shapefile
    with arcpy.da.UpdateCursor(output, "TIMEDIF") as rows:
        for j,row in enumerate(rows):
            row[0] = deltasec[j]
            rows.updateRow(row)

    #Add field to store speed
    if not FieldExist(output, "SPEED"):
        arcpy.AddField_management(output, "SPEED", "DOUBLE")

    #Calculate speed (KM/H)
    fields = ("DIST", "TIMEDIF", "SPEED")
    with arcpy.da.UpdateCursor(output, fields) as cursor:
        for row in cursor:
            if row[0] == 0 or row[1] == 0:
                row[2] = 0
            else:
                row[2] = (row[0]/row[1])*3.6
            cursor.updateRow(row)

    #Add field to store acceleration
    if not FieldExist(output, "ACC"):
        arcpy.AddField_management(output, "ACC", "DOUBLE")

    #Get speed
    speed = [x for x in arcpy.da.SearchCursor(output, "SPEED")]

    #Compute acceleration between features
    acceleration = [(speed[i+1][0] * (1000.0/ 3600.0)) - (speed[i][0] * (1000.0 / 3600.0)) for i,_ in enumerate(speed[:-1])]

    #Insert a 0 in the first position since it has nothing to measure against
    acceleration.insert(0, 0)

    #Write acceleration to shapefile.
    with arcpy.da.UpdateCursor(output, ["ACC", "TIMEDIF"]) as rows:
        for j,row in enumerate(rows):
            if not row[1] == 0:
                row[0] = acceleration[j] / float(row[1])
            else:
                row[0] = 0
            rows.updateRow(row)

    #Add field to store bearing
    if not FieldExist(output, "BEARING"):
        arcpy.AddField_management(output, "BEARING", "FLOAT")

    #Get coordinates of each feature (in WGS94) and store it as a list of tuples.
    coord = [x[0] for x in arcpy.da.SearchCursor(output, "SHAPE@XY", spatial_reference = wgs84)]

    #Compute bearing between features
    bearing = [calc_bearing(coord[i+1], coord[i]) for i,_ in enumerate(coord[:-1])]

    #Insert a 0 in the first position since it has nothing to measure against
    bearing.insert(0, 0)
    
    #Write bearing to shapefile.
    with arcpy.da.UpdateCursor(output, "BEARING") as rows:
        for j,row in enumerate(rows):
            row[0] = bearing[j]
            rows.updateRow(row)

    #Add field to store bearing change
    if not FieldExist(output, "DIR_CHANGE"):
        arcpy.AddField_management(output, "DIR_CHANGE", "FLOAT")

    #Get bearing of each feature
    bearing = [x[0] for x in arcpy.da.SearchCursor(output, "BEARING")]

    #Compute bearing changes between features
    dir_change = [abs(bearing[i+1] - bearing[i]) for i,_ in enumerate(bearing[:-1])]

    #Insert a 0 in the first position since it has nothing to measure against
    dir_change.insert(0, 0)

    #Write bearing change to shapefile
    with arcpy.da.UpdateCursor(output, "DIR_CHANGE") as rows:
        for j, row in enumerate(rows):
            row[0] = dir_change[j]
#            rows.updateRow(row)
