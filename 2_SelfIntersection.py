#===============================================================================
# JTVD - 2017
#===============================================================================

#===============================================================================
# SET PARAMETERS
#===============================================================================

#Import modules
import arcpy, os
from arcpy import env

#Set start folder and workspace accordingly
tracks = r"path to folder where to save tracks between origin / destination locatoins"
env.workspace = tracks

#Set coordinate system tracks
hart94 = "PROJCS['Hartebeesthoek94_Lo19',GEOGCS['GCS_Hartebeesthoek_1994',DATUM['D_Hartebeesthoek_1994',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',19.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"

#Set environment
env.overwriteOutput = True
env.parallelProcessingFactor = "4"

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
# FIND SELF-INTERSECTION LINES AND REMOVE SELF INTERSECTING LINES
#===============================================================================

#Set counter
line_fc = arcpy.ListFeatureClasses("LINE*")

#Generate activities within Study Area
for line in line_fc:

        #Line to polygon
        poly = os.path.join("in_memory", "poly")
        arcpy.FeatureToPolygon_management(line, poly)

        #Check for self-intersection
        if arcpy.management.GetCount(poly)[0] == "0":
            print "No self-intersection:", line

        #If self-intersection
        if not arcpy.management.GetCount(poly)[0] == "0":
            print "Self-intersection:", line

            #Split line
            split = os.path.join("in_memory", "split")
            arcpy.SplitLine_management(line, split)

            #Make selectable layers
            poly_layer = arcpy.MakeFeatureLayer_management(poly, "poly")
            split_layer = arcpy.MakeFeatureLayer_management(split, "split")

            #Select self-intersection
            arcpy.SelectLayerByLocation_management("split", "SHARE_A_LINE_SEGMENT_WITH", "poly", "", "", "INVERT")

            #Delete original
            arcpy.Delete_management(line)

            #Export path to memory
            arcpy.FeatureClassToFeatureClass_conversion("split", "in_memory", "sel_split")

            #Dissolve path
            sel_split = os.path.join("in_memory", "sel_split")
            out_fc = os.path.join(tracks, line)
            arcpy.Dissolve_management(sel_split, out_fc, "", "", "", "DISSOLVE_LINES")

            #Delete feature layer
            arcpy.Delete_management("poly")
            arcpy.Delete_management("split")

        #Empty memory
        arcpy.Delete_management("in_memory")


     
