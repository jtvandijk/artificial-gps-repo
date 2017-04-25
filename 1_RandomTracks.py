#===============================================================================
# JTVD - 2017
#===============================================================================

#===============================================================================
# SET PARAMETERS
#===============================================================================

#Import modules
import arcpy, os, subprocess, shutil
import pandas as pd
import numpy as np
from arcpy import env

#Set start folder and workspace accordingly
start = r"path to folder with input files"
save = r"path to folder to save random origin / destination locations"
tracks = r"path to folder where to save tracks between origin / destination locations"
env.workspace = start

#Set coordinate system tracks
hart94 = "PROJCS['Hartebeesthoek94_Lo19',GEOGCS['GCS_Hartebeesthoek_1994',DATUM['D_Hartebeesthoek_1994',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',19.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"

#Set environment
env.overwriteOutput = True
env.parallelProcessingFactor = "4"

#Set study area
area = os.path.join(start, "CPT_OSM_POI_SEL.shp")
roads = os.path.join(start, "RoadsTracksSel.shp")

#Set number of tracks
#Maximum value of 999 in order to comply with Flowmap naming conventions
n_tracks = 100

#Set minimum number of activities
#Minimum value of 2 otherwise no track is generated
min_activities = 2

#Set maximum number of activities -- Maximum +1 (e.g. enter 9 for maximum 8 activities)
#Maximum value of 11 in order to comply with Flowmap naming conventions
max_activities = 9

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
# GENERATE START / STOP TRACKS
#===============================================================================

#Set counter
count = 0

#Make feature of Study Area
study_area = arcpy.MakeFeatureLayer_management(area, "study_area")

#Generate activities within Study Area
while count < (n_tracks):

    #Update counter
    count = count + 1

    #Select random number of activities
    activities = np.random.randint(min_activities, max_activities)
    print "Number of activities:", activities

    #Adjust numbers for saving activity file
    if len(str(count)) == 1:
        number = "00" + str(count)
    elif len(str(count)) == 2:
        number = "0" + str(count)
    elif len(str(count)) == 3:
        number = str(count)

    #Select random coordinates for activities
    arcpy.CreateRandomPoints_management(save, "AC_" + str(number) + ".shp", study_area, "", activities, "100 Meters")

    #Access random coordinates file
    random_coord = os.path.join(save, "AC_" + str(number) + ".shp")
    
    #Add field for Name
    if not FieldExist(random_coord, "NAME"):
        arcpy.AddField_management(random_coord, "NAME", "TEXT")

    #Set counter activity names
    ac_number = 0

    #Calculate field values activity names
    with arcpy.da.UpdateCursor(random_coord, "NAME") as cursor:
        for row in cursor:
            ac_number = ac_number + 1
            row[0] = "AC_" + str(ac_number)
            cursor.updateRow(row)
        
    #Import activities in Flowmap
    import_fm = os.path.join(start, "FM_Import.flg")
    export_fm = os.path.join(save, "FM_Import_" + str(number) + ".txt")
    shutil.copy(import_fm, export_fm)

    #Feed in activities in Flowmap
    f1 = open(export_fm, 'r')
    f2 = open(os.path.join(export_fm[:-4] + ".flg" ), 'w')

    for line in f1:
        f2.write(line.replace("001", str(number)))

    f1.close()
    f2.close()

    os.remove(export_fm)

    #Create path to created FM script
    import_flg = os.path.join(save, "FM_Import_" + str(number) + ".flg")
        
    #Import Origin and Destination in Flowmap
    executable = r"C:\Program Files\FLOWMAP\Flowmap742.exe /SHELL %s" % (import_flg)
    print executable

    #Execute FM
    subprocess.call(executable)

#===============================================================================
# GENERATE TRACK -- FLOWMAP
#===============================================================================

    #Get combinations for Flowfile
    for a in range(1, activities):

        #Create Flowfile
        export_fl = os.path.join(save, "F" + str(number) + "AC" + str(a) + "2.csv")
        flows = []
        headers = ["SCORE", "ORIG", "DEST"] 
        flows.append(headers)
        new_row = []
        new_row.append("2")
        new_row.append("AC_" + str(a))
        new_row.append("AC_" + str(a +1))
        flows.append(new_row)

        #Create dataframe of combinations for Flowfile
        flows_df = pd.DataFrame(flows)

        #Export dataframe of combinations to csv
        flows_df.to_csv(export_fl, mode = "w", index = False, header = None)

        #Create DBF flowfile
        export_dbf = os.path.join(save, "F" + str(number) + "AC" + str(a) + "2.csv")
        flow_dbf = os.path.join(save, "F" + str(number) + "AC" + str(a) + "2.dbf")
        if not arcpy.Exists(flow_dbf):
            arcpy.TableToDBASE_conversion(export_dbf, save)

        #Find shortest route Origin and Destination in Flowmap
        import_fm = os.path.join(start, "FM_Route.flg")
        export_fm = os.path.join(save, "FM_Route_" + str(number) + "AC" + str(a) + ".txt")
        shutil.copy(import_fm, export_fm)

        #Feed in Flowfile
        f1 = open(export_fm, 'r')
        f2 = open(os.path.join(export_fm[:-4] + ".flg" ), 'w')

        for line in f1:
            f2.write(line.replace("001AC1", str(number) + "AC" + str(a)))

        f1.close()
        f2.close()

        os.remove(export_fm)

        #Find shortest route Origin and Destination in Flowmap
        import_fm = os.path.join(save, "FM_Route_" + str(number) + "AC" + str(a) + ".flg")
        export_fm = os.path.join(save, "FM_Route_" + str(number) + "AC" + str(a) + ".txt")
        shutil.copy(import_fm, export_fm)

        #Feed in Origin and Destination
        f1 = open(export_fm, 'r')
        f2 = open(os.path.join(export_fm[:-4] + ".flg" ), 'w')

        for line in f1:
            f2.write(line.replace("001", str(number)))
            
        f1.close()
        f2.close()

        os.remove(export_fm)

        #Create path to created FM script
        route_flg = os.path.join(save, "FM_Route_" + str(number) + "AC" + str(a) + ".flg")
        
        #Calculate shortest path Origin and Destination
        executable = r"C:\Program Files\FLOWMAP\Flowmap742.exe /SHELL %s" % (route_flg)
        print "Executing: ", executable

        #Execute FM
        subprocess.call(executable)
        print "Success: ", executable

#===============================================================================
# GENERATE TRACK -- LINE
#===============================================================================

    #Gather path fields
    dropFields = []
 
    #Get combinations for Flowfile
    for a in range(1, activities):

        #Create Flowfile
        ac_path = "FP" + str(number) + "AC" + str(a)
        dropFields.append(ac_path)

        #Get path from DBF
        path = os.path.join(start, "ROADSTR3.DBF")
        selection = []
        fields = [ac_path, "LABEL"]
        with arcpy.da.SearchCursor(path, fields) as cursor:
            for row in cursor:
                if row[0] == 2:
                    selection.append(row[1])

        #Make feature layer
        arcpy.MakeFeatureLayer_management(roads, "roads")
        
        #Select path in SHP
        for f in selection:
            query = "\"JOIN\" = " + str(f)
            arcpy.SelectLayerByAttribute_management("roads", "ADD_TO_SELECTION", query)

        #Check for emtpy selection
        desc = arcpy.Describe("roads")
        sel_count = len(desc.fidset.split(";"))

        if sel_count > 0:
        
            #Export path to SHP in Memory
            arcpy.FeatureClassToFeatureClass_conversion("roads", "in_memory", "LINE" + str(number))

            #Dissolve path
            in_mem = os.path.join("in_memory", "LINE" + str(number))
            out_fc = os.path.join(tracks, "LINE" + str(number) + "AC" + str(a) + "AC" + str(a + 1) + ".shp")
            arcpy.Dissolve_management(in_mem, out_fc, "", "", "", "DISSOLVE_LINES")

            print out_fc

        #Delete feature layer
        arcpy.Delete_management("roads")
        arcpy.Delete_management("in_memory")

        #Delete path attributes
        arcpy.DeleteField_management(path, dropFields)

