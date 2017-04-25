#===============================================================================
# JTVD - 2016
#===============================================================================

#SOURCE CODE:
#http://ianbroad.com/download/script/CreatePointsLines.py

#===============================================================================
# SET PARAMETERS
#===============================================================================

#Import modules
import arcpy
from arcpy import env
import numpy as np

#Set start folder and workspace accordingly
start = r"path to folder where to save tracks between origin / destination locations"
env.workspace = start

#Set environment
env.overwriteOutput = True
env.parallelProcessingFactor = "4"

#Set durations of activities
short_dur = 8
short_dur_dev = 3
med_dur = 50
med_dur_dev = 10
long_dur = 300
long_dur_dev = 60

#Set measurement frequency GPS
meas_freq = 30

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
    
#===============================================================================
# IDENTIFY STOP LOCATIONS
#===============================================================================

#Get tracks
point_fc = arcpy.ListFeatureClasses("AC*")

#Loop through tracks
for p in point_fc:

    print p

    #Add XY
    arcpy.AddXY_management(p)

    #Get number of points
    n = int(arcpy.GetCount_management(p).getOutput(0))

    #Add STOP ID
    if not FieldExist(p, "STOP"):
        arcpy.AddField_management(p, "STOP", "DOUBLE")

    #Add STOP Type
    if not FieldExist(p, "TYPE"):
        arcpy.AddField_management(p, "TYPE", "TEXT")

    #Add STOP Duration
    if not FieldExist(p, "DURATION"):
        arcpy.AddField_management(p, "DURATION", "DOUBLE")
        
    #Add New PointID Field
    if not FieldExist(p, "POINT_ID_N"):
        arcpy.AddField_management(p, "POINT_ID_N", "DOUBLE")           

    #Write Point ID
    fields = ["OID@", "STOP"]
    with arcpy.da.UpdateCursor(p, fields) as cursor:
        for row in cursor:
            row[1] = row[0] + 1
            cursor.updateRow(row)

    #Identify random Stop Durations
    for i in range(1, n+1):

        stop_dur = np.random.randint(1,4)

        #Identify random Short Stop Duration
        if stop_dur == 1:
            seed = -1
            while seed <= 0:
                seed = np.random.normal(short_dur,short_dur_dev)
            dur = np.random.poisson(seed)
            point_n = int((float(dur)*60)/meas_freq)
            print "SHORT", dur, point_n

            #Write Type to Short Stop
            fields = ["STOP", "TYPE", "DURATION"]
            with arcpy.da.UpdateCursor(p, fields) as cursor:
                for row in cursor:
                    if row[0] == i:
                        row[1] = "SHORT"
                        row[2] = point_n
                    cursor.updateRow(row)
                                     
        #Identify random Medium Stop Duration
        if stop_dur == 2:
            seed = -1
            while seed <= 0:
                seed = np.random.normal(med_dur,med_dur_dev)
            dur = np.random.poisson(seed)
            point_n = int((float(dur)*60)/meas_freq)
            print "MED", dur, point_n

            #Write Type to Short Stop
            fields = ["STOP", "TYPE", "DURATION"]
            with arcpy.da.UpdateCursor(p, fields) as cursor:
                for row in cursor:
                    if row[0] == i:
                        row[1] = "MEDIUM"
                        row[2] = point_n
                    cursor.updateRow(row)
                        
        #Identify random Long Stop Duration
        if stop_dur == 3:
            seed = -1
            while seed <= 0:
                seed = np.random.normal(long_dur,long_dur_dev)
            dur = np.random.poisson(seed)
            point_n = int((float(dur)*60)/meas_freq)
            print "LONG", dur, point_n

            #Write Type to Short Stop
            fields = ["STOP", "TYPE", "DURATION"]
            with arcpy.da.UpdateCursor(p, fields) as cursor:
                for row in cursor:
                    if row[0] == i:
                        row[1] = "LONG"
                        row[2] = point_n
                    cursor.updateRow(row)

    #Add new points at Stop Locations
    insert_fields = ["SHAPE@", "STOP", "TYPE", "DURATION", "POINT_ID_N", "POINT_X", "POINT_Y"]

    #Calculate New XY
    fields = ["STOP", "POINT_X", "POINT_Y", "POINT_ID_N", "TYPE", "DURATION"]
    count = 0
    with arcpy.da.UpdateCursor(p, fields) as cursor:
        with arcpy.da.InsertCursor(p, insert_fields) as insert:
            for row in cursor:
                count = count + 1
                row[3] = count
                if row[4] == "SHORT":
                    coord = (row[1],row[2])
                    stop = int(row[0])
                    stop_type = row[4]
                    duration = row[5]
                    point_x = row[1]
                    point_y = row[2]
                    for i in range(1, int(duration), 1):
                        count = count + 1
                        new_row = (coord, stop, stop_type, duration, count, point_x, point_y)
                        insert.insertRow(new_row)
    
                elif row[4] == "MEDIUM":
                    coord = (row[1],row[2])
                    stop = int(row[0])
                    stop_type = row[4]
                    duration = row[5]
                    point_x = row[1]
                    point_y = row[2]
                    for i in range(1, int(duration), 1):
                        count = count + 1
                        new_row = (coord, stop, stop_type, duration, count, point_x, point_y)
                        insert.insertRow(new_row)

                elif row[4] == "LONG":
                    coord = (row[1],row[2])
                    stop = int(row[0])
                    stop_type = row[4]
                    duration = row[5]
                    point_x = row[1]
                    point_y = row[2]
                    for i in range(1, int(duration), 1):
                        count = count + 1
                        new_row = (coord, stop, stop_type, duration, count, point_x, point_y)
                        insert.insertRow(new_row)
                cursor.updateRow(row)
