# JTVD - 2017

#Parts of this code have been borrowd from:
#http://ianbroad.com/download/script/CreatePointsLines.py

#Import modules
import arcpy, os
from arcpy import env
import numpy as np

#Set start folder and workspace accordingly
start = r"path to folder where to save tracks between origin / destination locations"
env.workspace = start

#Set environment
env.overwriteOutput = True
env.parallelProcessingFactor = "4"

#Set distance interval
standard_dev = 1
scale_f = 10

#Functions
def FieldExist(featureclass, fieldname):
    fieldList = arcpy.ListFields(featureclass, fieldname)

    fieldCount = len(fieldList)

    if (fieldCount == 1):
        return True
    else:
        return False

#Introduce noise into points
    
#Get tracks
point_fc = arcpy.ListFeatureClasses("POINTS*")

#Loop through tracks
for p in point_fc:

    #Add XY
    arcpy.AddXY_management(p)

    #Get number of points
    n = int(arcpy.GetCount_management(p).getOutput(0))

    print p, n

    #Add New XY Fields
    if not FieldExist(p, "POINT_X_N"):
        arcpy.AddField_management(p, "POINT_X_N", "DOUBLE")
        
    if not FieldExist(p, "POINT_Y_N"):
        arcpy.AddField_management(p, "POINT_Y_N", "DOUBLE")

    #Calculate Shifts following bi-dimensional normal distribution
    mean = [0,0]
    cov = [[standard_dev, 0], [0, standard_dev]]
    x,y = np.random.multivariate_normal(mean,cov,n).T

    #Create New Empty FC
    mem_point = arcpy.CreateFeatureclass_management("in_memory", "mem_point", "POINT", "", "DISABLED", "DISABLED", p)
    insert_fields = ["SHAPE@", "XSHIFT", "YSHIFT", "MODE"]

    #Add insert fields
    arcpy.AddField_management(mem_point, "XSHIFT", "DOUBLE")
    arcpy.AddField_management(mem_point, "YSHIFT", "DOUBLE")
    arcpy.AddField_management(mem_point, "MODE", "TEXT")

    #Calculate New XY
    fields = ["POINT_X", "POINT_X_N", "POINT_Y", "POINT_Y_N", "MODE"]
    with arcpy.da.UpdateCursor(p,fields) as rows:
        with arcpy.da.InsertCursor(mem_point, insert_fields) as insert:
            for j,row in enumerate(rows):
                row[1] = row[0] + (x[j]*scale_f)
                row[3] = row[2] + (y[j]*scale_f)
                new_coord = [row[1],row[3]]
                xshift = x[j]*scale_f
                yshift = y[j]*scale_f
                mode = row[4]
                new_row = (new_coord, xshift, yshift, mode)
                insert.insertRow(new_row)
                rows.updateRow(row)

    #Save New Point FC
    output = os.path.join(start, "NOISE_" + p)
    print output
    arcpy.CopyFeatures_management(mem_point, output)            



            
    
