# JTVD - 2017

#Import modules
import arcpy, os, time, datetime
from arcpy import env
from random import randrange
import numpy as np

#Set start folder and workspace accordingly
start = r"path to folder where to save origin / destination locations""
env.workspace = start

#Set environment
env.overwriteOutput = True
env.parallelProcessingFactor = "4"

#Set measurement frequency
measurement_freq = 30

#Functions
def FieldExist(featureclass, fieldname):
    fieldList = arcpy.ListFields(featureclass, fieldname)

    fieldCount = len(fieldList)

    if (fieldCount == 1):
        return True
    else:
        return False
    
#Introduce noise in stop locations

#Get tracks
point_fc = arcpy.ListFeatureClasses("AC*")

#Loop through tracks
for p in point_fc:

    #Get number of points
    n = int(arcpy.GetCount_management(p).getOutput(0))

    print p,n

    #Create New Emtpy FC
    mem_point = arcpy.CreateFeatureclass_management("in_memory", "mem_point", "POINT", "", "DISABLED", "DISABLED", p)
    insert_fields = ["SHAPE@", "STOP", "TYPE", "DURATION", "POINT_ID_N", "POINT_X", "POINT_Y", "ST_DEV", "XSHIFT", "YSHIFT"]

    #Add insert_fields
    arcpy.AddField_management(mem_point, "STOP", "DOUBLE")
    arcpy.AddField_management(mem_point, "TYPE", "TEXT")
    arcpy.AddField_management(mem_point, "DURATION", "DOUBLE")
    arcpy.AddField_management(mem_point, "POINT_ID_N", "DOUBLE")
    arcpy.AddField_management(mem_point, "POINT_X", "DOUBLE")
    arcpy.AddField_management(mem_point, "POINT_Y", "DOUBLE")
    arcpy.AddField_management(mem_point, "ST_DEV", "DOUBLE")
    arcpy.AddField_management(mem_point, "XSHIFT", "DOUBLE")
    arcpy.AddField_management(mem_point, "YSHIFT", "DOUBLE")

    #Calculate Shifts following normal distribution
    mean = [0,0]
    st_dev = np.random.randint(10,200)
    cov = [[1, 0], [0, 1]]
    x,y = np.random.multivariate_normal(mean,cov,n).T

    #Calculate New XY
    fields = ["POINT_X", "POINT_Y", "STOP", "TYPE", "DURATION", "POINT_ID_N"]
    with arcpy.da.SearchCursor(p, fields) as rows:
        with arcpy.da.InsertCursor(mem_point, insert_fields) as insert:
            for j,row in enumerate(rows):
                x_shift = row[0] + (x[j]*st_dev)
                y_shift = row[1] + (y[j]*st_dev)
                coord = [x_shift, y_shift]
                stop = int(row[2])
                stop_type = row[3]
                duration = row[4]
                point = row[5]
                point_x = row[0]
                point_y = row[1]
                st_dev = st_dev
                xshift = (x[j]*st_dev)
                yshift = (y[j]*st_dev)
                new_row = (coord, stop, stop_type, duration, point, point_x, point_y, st_dev, xshift, yshift)
                insert.insertRow(new_row)

    #Save New Point FC
    output = os.path.join(start, "NOISE_" + p)
    print output
    arcpy.Sort_management(mem_point, output, [["POINT_ID_N", "ASCENDING"]])

    #Add Date and Time variable
    if not FieldExist(output, "TIMESTAMP"):
        arcpy.AddField_management(output, "TIMESTAMP", "TEXT")

