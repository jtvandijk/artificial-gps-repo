# JTVD - 2017

#Parts of this code have been borrowd from:
#http://ianbroad.com/download/script/CreatePointsLines.py

#Import modules
import arcpy, os
from arcpy import env
import numpy as np

#Set start folder and workspace accordingly
start = r"path to folder where to save tracks between origin / destination locations"
save = r"path to folder to save random origin / destination locations"
env.workspace = start

#Set coordinate system tracks
wgs84 = arcpy.SpatialReference(4326)
hart94 = "PROJCS['Hartebeesthoek94_Lo19',GEOGCS['GCS_Hartebeesthoek_1994',DATUM['D_Hartebeesthoek_1994',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',19.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
transformation = "Hartebeesthoek94_To_WGS_1984"

#Set environment
env.overwriteOutput = True
env.parallelProcessingFactor = "4"

#Set speeds transport modes
car_slow = 20
car_slow_dev = 5
car_med = 60
car_med_dev = 5
car_fast = 80
car_fast_dev = 10 

bike = 15
bike_dev = 3

walk = 5
walk_dev = 2

#Set distance interval (MEASUREMENT FREQUENCY)
#Example: 10 meter -- 1 second (36km/h)
#Example: 100 meter -- 10 seconds (36 km/h)
#1 km/h = (1000/3600) m/s
#Times speed
#Times measurement frequency (30s)

measurement_frequency = 30.0

#Functions
def FieldExist(featureclass, fieldname):
    fieldList = arcpy.ListFields(featureclass, fieldname)

    fieldCount = len(fieldList)

    if (fieldCount == 1):
        return True
    else:
        return False
    
#Transform polyline into points

#Get tracks
line_fc = arcpy.ListFeatureClasses("LINE*")

#Loop through tracks
for line in line_fc:

    #Get number of activities
    name = str(line[4:7])

    #Set output
    output = os.path.join(start, "POINTS" + str(line[4:]))
    print output

    #Identify random transport mode
    transport_mode = np.random.randint(1,6)

    if transport_mode == 1:
        mode = "CAR"
        mu = car_slow
        sigma = car_slow_dev
    if transport_mode == 2:
        mode = "CAR"
        mu = car_med
        sigma = car_med_dev
    if transport_mode == 3:
        mode = "CAR"
        mu = car_fast
        sigma = car_fast_dev
    if transport_mode == 4:
        mode = "BIKE"
        mu = bike
        sigma = bike_dev
    if transport_mode == 5:
        mode = "WALK"
        mu = walk
        sigma = walk_dev

    print mode, mu, sigma

    #Get parameters
    spatial_ref = arcpy.Describe(line).spatialReference
    mem_point = arcpy.CreateFeatureclass_management("in_memory", "mem_point", "POINT", "", "DISABLED", "DISABLED", line)
    arcpy.AddField_management(mem_point, "LineOID", "LONG")
    arcpy.AddField_management(mem_point, "Value", "FLOAT")
    arcpy.AddField_management(mem_point, "COUNTID", "DOUBLE")

    #Set fields
    search_fields = ["SHAPE@", "OID@"]
    insert_fields = ["SHAPE@", "LineOID", "Value", "COUNTID"]

    #Access line and point
    with arcpy.da.SearchCursor(line, (search_fields)) as search:
        with arcpy.da.InsertCursor(mem_point, (insert_fields)) as insert:
            for row in search:
                try:

                    #Access line geometry
                    line_geom = row[0]
                    p1 = line_geom.firstPoint
                    p2 = line_geom.lastPoint

                    #Get length of line
                    length = float(line_geom.length)
                    count = 10
                    oid = str(row[1])
                    countid = 0

                    #Loop through line
                    while count <= length:
                        speed = np.random.normal(mu, sigma)
                        distance = ((1000.0/3600.0)*speed)*measurement_frequency
                        point = line_geom.positionAlongLine(count, False)
                        countid += 1
                        insert.insertRow((point, oid, count, countid))
                        count += distance

                    #Get faulty tracks (topology)
                    if p1.equals(p2):
                        faulty.append(line)
                        
                except:
                    print arcpy.GetMessages()

    line_keyfield = str(arcpy.ListFields(line, "", "OID")[0].name)
    mem_point_fl = arcpy.MakeFeatureLayer_management(mem_point, "Points_memory")

    #Add line attributes
    arcpy.AddJoin_management(mem_point_fl, "LineOID", line, line_keyfield)

    #Flip direction of line if necessary
    fields = ["SHAPE@XY"]
    points = [point for point in arcpy.da.SearchCursor(mem_point_fl, fields)]

    startp = arcpy.Point(points[0][0][0], points[0][0][1])
    endp = arcpy.Point(points[-1][0][0], points[-1][0][1])

    start_point = arcpy.PointGeometry(startp, hart94)
    end_point = arcpy.PointGeometry(endp, hart94)

    fields = ["SHAPE@XY", "NAME"]
    activ_coord = os.path.join(save, "AC_" + str(name) + ".shp")
    with arcpy.da.SearchCursor(activ_coord, fields) as cursor:
        for row in cursor:
            if row[1] == "AC_" + str(line[9]):
                starta = arcpy.Point(row[0][0], row[0][1])
                start_activity = arcpy.PointGeometry(starta, hart94)
                
                dist_to_start = start_activity.distanceTo(startp)
                dist_to_end = start_activity.distanceTo(endp)
    print dist_to_start, dist_to_end
    if dist_to_start > dist_to_end:
        arcpy.Sort_management(mem_point_fl, output, [["mem_point.COUNTID", "DESCENDING"]])
        print "...direction of line changed"
    else:
        arcpy.CopyFeatures_management(mem_point_fl, output)

    #Add field transport mode
    if not FieldExist(output, "MODE"):
        arcpy.AddField_management(output, "MODE", "TEXT")

    #Add transport mode to field
    fields = ["MODE"]
    with arcpy.da.UpdateCursor(output, fields) as cursor:
        for row in cursor:
            row[0] = mode
            cursor.updateRow(row)

    #Clean up
    arcpy.Delete_management(mem_point)
    arcpy.Delete_management(mem_point_fl)
