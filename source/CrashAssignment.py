import arcpy
import os
import sys
import math, time

# pylint: disable = E1103, E1101, R0914, W0703, R0911, R0912, R0915, C0302

arcpy.env.overwriteOutput = True

IN_MEMORY = 'in_memory'

#======================= Configuration ===================================#

# Specify the name of the Crash Output Feature Class
CRASH_OUTPUT_NAME = "CrashOutput"
CRASH_OUTPUT_PATH = ""

# Specify the name of the Segment Output Feature Class
SEGMENT_OUTPUT_NAME = "SegmentOutput"
SEGMENT_OUTPUT_PATH = ""

# Specify the name of Output FileGeodatabase
OUTPUT_GDB_NAME = "CrashAssignmentOutput.gdb"

# Specify names for required fields
CRASH_YEAR_FIELD = "CRASH_"
TOTAL_CRASH_FIELD_NAME = "TOTAL_CRASH"
AVG_CRASHES_FIELD_NAME = "AVG_CRASH"
SEGMENTID_FIELD_NAME = "USRAP_SEGID"
USRAP_SEGMENT_FIELD_NAME = "USRAP_SEGMENT"
COUNTY_FIELD_NAME = "USRAP_COUNTY"
AADT_FIELD_NAME = "USRAP_AADT_"
AADT_YEAR_INDEX = 2
AVG_AADT_FIELD_NAME = "USRAP_AVG_AADT"
LANES_FIELD_NAME = "USRAP_LANES"
MEDIANS_FIELD_NAME = "USRAP_MEDIAN"
AREA_TYPE_FIELD = "USRAP_AREA_TYPE"
USRAP_ROADWAY_TYPE_FIELDNAME = 'USRAP_ROADWAY_TYPE'

# Set increment value for progressor while merging segments
SEGMENT_INCREMENT = 10

# Crash error table fields
CRASH_ERROR_TABLE_FIELDS = [["CrashOID", "LONG"], ["CrashYear", "SHORT"],
                            ["CrashRouteName", "TEXT"], [SEGMENTID_FIELD_NAME, "TEXT"],
                            ["SegmentRouteName", "TEXT"],
                            ["ErrorMessage", "TEXT"]]

# Segment error table fields
SEGMENT_ERROR_TABLE_FIELDS = [["SegmentOID", "LONG"], [SEGMENTID_FIELD_NAME, "TEXT"],
                              ["AVG_CRASH", "TEXT"], [TOTAL_CRASH_FIELD_NAME, "TEXT"],
                              ["ErrorMessage", "TEXT"]]

# Error Summary Table fields
SUMMARY_ERROR_TABLE_FIELDS = [["ErrorType", "TEXT", 500], ["Count", "TEXT", 50],
                              ["Percentage", "TEXT", 50]]

# Specify name for the error log tables
CRASH_ERROR_TABLE_NAME = "CrashErrorTable"
SEGMENT_ERROR_TABLE_NAME = "SegmentErrorTable"
ERROR_SUMMARY_TABLE_NAME = "SummaryErrorTable"

USRAP_WHERE = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)

VERSION_USED = str(arcpy.GetInstallInfo()['Version'])

#===================== Assignment =============================================#
def create_gdb(output_folder):
    """
    This function creates the new file geodatabase to store the analysis output
    """
    try:
        #   If geodatabase with specified name already exists, return the
        #   existing gdb path else create a new one.
        if os.path.exists(os.path.join(output_folder, OUTPUT_GDB_NAME)):
            output_gdb = os.path.join(output_folder, OUTPUT_GDB_NAME)
        else:
            output_gdb = arcpy.CreateFileGDB_management(output_folder,
                                                        OUTPUT_GDB_NAME[:-4])[0]

        arcpy.env.workspace = output_gdb
        arcpy.AddMessage("Output geodatabase created.")

        return output_gdb

    except arcpy.ExecuteError:
        arcpy.AddError("Error occurred while creating new File Geodatabase.")
        return False

    except Exception:
        arcpy.AddError("Error occurred while creating new File Geodatabase.")
        return False

def get_usrap_segments(input_segment_fc):
    """
    This function seperates out the USRAP Segments.
    Only these segments need to be considered while assigning crashes.
    """
    try:
        # Check if "USRAP_SEGMENT" field exist in segment feature class
        segment_fields = [(field.name).upper() for field
                          in arcpy.ListFields(input_segment_fc)]
        if USRAP_SEGMENT_FIELD_NAME not in segment_fields:
            add_formatted_message("{0} field not found in input segment feature class.", 
                                  USRAP_SEGMENT_FIELD_NAME)
            return []
        del segment_fields

        # Make the selection
        total_segments = int(arcpy.GetCount_management(input_segment_fc)[0])
        segment_layer = arcpy.MakeFeatureLayer_management(
            input_segment_fc, "segment_layer", USRAP_WHERE)[0]
        count = int(arcpy.GetCount_management(segment_layer)[0])
        arcpy.AddMessage(("{0} USRAP segments found out of {1}.")
                         .format(count, total_segments))
        if count > 0:
            return segment_layer, count
        else:
            arcpy.AddError("No valid USRAP segments found. \nFurther processing will not be performed.")
            sys.exit()

    except arcpy.ExecuteError:
        arcpy.AddError("Error occurred while getting USRAP_SEGMENT.")
        return []

    except Exception:
        arcpy.AddError("Error occurred while getting USRAP_SEGMENT.")
        return []

def assign_segid_to_crashes(max_dist, usrap_segment_layer, input_crash_fc, out_gdb):
    """
    This function first creates the Field mapping and then performs a
    spatial join between Crash Feature Class and Segment Feature Class
    """
    try:
        add_formatted_message("Assigning {0} to crashes... ", SEGMENTID_FIELD_NAME)
        # Specify target features, join features
        target_features = input_crash_fc
        join_features = usrap_segment_layer

        # Create a new fieldmappings and add the two input feature classes.
        field_mappings = arcpy.FieldMappings()
        field_mappings.addTable(target_features)
        field_mappings.addTable(join_features.dataSource)

        # Retain all the fields from crash feature class from field mappings and
        # remove all fields from segment feature class except SEGMENTID_FIELD_NAME
        desc = arcpy.Describe(target_features)
        retained_fields = [(fld.name).upper() for fld in desc.fields]
        retained_fields += [SEGMENTID_FIELD_NAME]
        del desc

        for map_field in field_mappings.fields:
            if (map_field.name).upper() in retained_fields:
                continue
            field_index = field_mappings.findFieldMapIndex(map_field.name)
            field_mappings.removeFieldMap(field_index)

        CRASH_OUTPUT_PATH = out_gdb + os.sep + CRASH_OUTPUT_NAME
        arcpy.SpatialJoin_analysis( target_features, join_features, CRASH_OUTPUT_PATH,
            "JOIN_ONE_TO_ONE", "KEEP_ALL", field_mappings, "CLOSEST", max_dist)

        # Delete the fields "JOIN_COUNT" and "TARGET_FID" which get added to
        # the output feature class from spatial join
        arcpy.DeleteField_management(CRASH_OUTPUT_PATH, ["JOIN_COUNT", "TARGET_FID"])
        del retained_fields
        return True

    except arcpy.ExecuteError:
        arcpy.AddError("Error occured while performing Spatial Join for " +
                       "Crash Feature Class.")
        return False

    except Exception:
        arcpy.AddError("Error occured while performing Spatial Join for " +
                       "Crash Feature Class.")
        return False

def assign_crashes_to_segments(input_segment_fc, crash_years, crash_year_field, pts, out_gdb):
    """
    This function first adds the fields for each year to get the crash count.
    Fields for total and average crashes are also added.
    """
    try:
        arcpy.AddMessage("Assigning crash count to segments...")
        crash_where = SEGMENTID_FIELD_NAME + " IS NOT NULL AND " + crash_year_field + " IS NOT NULL"
        tl = "W"
        arcpy.MakeFeatureLayer_management(pts, tl, crash_where)
        pts = tl
        # Count is required only for the progressor labeling
        c_count = int(arcpy.GetCount_management(pts)[0])

        arcpy.ResetProgressor()
        arcpy.SetProgressor("step", "Assigning crash count to segments..",
                            0, c_count + 1, 1)

        #   Copy the features into memory for faster writes
        in_mem_segs = "in_memory" + os.sep + SEGMENT_OUTPUT_NAME
        arcpy.CopyFeatures_management(input_segment_fc, in_mem_segs)

        arcpy.AddMessage("Adding crash year fields in input segment" +
                         " feature class...")

        fields = []

        #   Add fields for each crash year in the segment feature class
        for year in crash_years:
            year_field = "{0}{1}".format(CRASH_YEAR_FIELD, str(year))
            arcpy.AddField_management(in_mem_segs, year_field, "SHORT")
            fields.append(year_field)

            arcpy.CalculateField_management(in_mem_segs, year_field, 0, "PYTHON_9.3")
        fields.append(SEGMENTID_FIELD_NAME)

        #   Add fields for Total and Average crashes in the
        #   segment feature class
        arcpy.AddField_management(in_mem_segs, TOTAL_CRASH_FIELD_NAME,
                                  "LONG")

        arcpy.AddField_management(in_mem_segs, AVG_CRASHES_FIELD_NAME,
                                  "DOUBLE")

        arcpy.SetProgressorPosition(1)
        arcpy.AddMessage("Assignment process started..")

        #   Take segment id assign to each crash from crash spatial join output,
        #   increment the crash count by 1 for that segment id
        #   for specified year
        row_count = 0
        per_val_list = [int(round((c_count * per_num) / 100))
                        for per_num in range(10, 110, 10)]
        perc = 10

        test = {}
        with arcpy.da.SearchCursor(pts, [SEGMENTID_FIELD_NAME, crash_year_field]) as crash_cursor:
            for row in crash_cursor:
                row_count += 1
                #arcpy.SetProgressorLabel(("Finished assigning {0} crashes out" +
                #                          " of {1}").format(row_count, c_count))
                #arcpy.SetProgressorPosition()

                if row_count in per_val_list:
                    arcpy.AddMessage("Reading values progress : {0}%".format(perc))
                    perc += 10
                field = "{0}{1}".format(CRASH_YEAR_FIELD, int(row[1]))
                if test.keys().count(row[0]) > 0:
                    updated = False 
                    for r in test[row[0]]:              
                        if r.count(field) > 0:
                            r[1] += 1
                            updated = True
                            break
                    if updated != True:
                        test[row[0]].append([field, 1])
                else:
                    test[row[0]] = [[field, 1]]
        del crash_cursor

        with arcpy.da.UpdateCursor(in_mem_segs, fields, SEGMENTID_FIELD_NAME + " IS NOT NULL") as segment_cursor:
            for update_row in segment_cursor:
                if test.keys().count(update_row[-1]) > 0:
                    row = test[update_row[-1]]
                    for r in row:
                        year = r[0]
                        val = r[1]
                        update_row[fields.index(year)] = val
                    segment_cursor.updateRow(update_row)
                    del row
        del segment_cursor, test

        arcpy.SetProgressorPosition()
        arcpy.AddMessage("Adding total crashes and average crashes in the " +
                         "output")
        #   Calculate the total crashes and average crashes for each segment
        segment_output_fc = caluculate_sum_avg_field(crash_years, in_mem_segs)
        if not segment_output_fc:
            return False

        # copy the updated segments to a physical class
        global SEGMENT_OUTPUT_PATH
        SEGMENT_OUTPUT_PATH = out_gdb + os.sep + "temp" + SEGMENT_OUTPUT_NAME
        arcpy.CopyFeatures_management(in_mem_segs, SEGMENT_OUTPUT_PATH)

        arcpy.Delete_management(in_mem_segs)
        del in_mem_segs

        arcpy.AddMessage("Assignment process completed.")
        arcpy.AddMessage("-" * 80)

        return True

    except Exception as ex:
        arcpy.AddError("Error occurred while adding count of crashes to the" +
                       " segments")
        return False

def caluculate_sum_avg_field(crash_years, segs):
    """
    Count the total and average crashes for each year and update the values
    """
    try:
        #   Make a list for all year's crashes fields
        update_fields = []
        for year in crash_years:
            update_fields.append("{0}{1}".format(CRASH_YEAR_FIELD, str(year)))

        #   Add 2 fields to the list for Total Crash Count and Average Crashes
        update_fields.append(TOTAL_CRASH_FIELD_NAME)
        update_fields.append(AVG_CRASHES_FIELD_NAME)

        #   Calculate total crash count and average crashes for each segment.
        #   To calculate the average crashes, dividing by the number of years
        #   for which it has count
        with arcpy.da.UpdateCursor(segs, update_fields) as update_cursor:
            for row in update_cursor:
                total_count = 0
                num_div_years = 0
                for i in range(len(crash_years)):
                    total_count += row[i]
                    num_div_years += 1
                if total_count == 0:
                    row[-1] = None
                    row[-2] = 0
                    update_cursor.updateRow(row)
                else:
                    avg_crashes = float(total_count) / float(num_div_years)
                    row[-1] = round(avg_crashes, 4)
                    row[-2] = total_count
                    update_cursor.updateRow(row)
        del update_cursor
        return True

    except Exception:
        arcpy.AddError("Error occured while calculating Total Crashes and " +
                       "Average Crashes")
        return False

def assign_values(input_segment_fc, input_crash_fc, crash_year_field, max_dist,
                  output_folder):
    """
    Assigns the segment id to crashes and crash count to segments
    """
    arcpy.SetProgressorPosition()

    # Create new File Geodatabase
    out_gdb = create_gdb(output_folder)
    if not out_gdb:
        return []
    arcpy.SetProgressorPosition()

    try:
        # Get Crash years
        arcpy.AddMessage("Getting crash years..")
        crash_years = set()
        with arcpy.da.SearchCursor(input_crash_fc,
                                   [crash_year_field]) as crash_search_cursor:
            for row in crash_search_cursor:
                if row[0] not in ["", None, " "]:
                    crash_years.add(int(row[0]))
        crash_years = sorted(crash_years)
        del crash_search_cursor

        arcpy.SetProgressorPosition()

        # Get AADT years
        arcpy.AddMessage("Getting AADT years..")
        field_type = "{0}*".format(AADT_FIELD_NAME)
        segment_fields = arcpy.ListFields(input_segment_fc, field_type)
        aadt_years = [int(str(field.name).split("_")[AADT_YEAR_INDEX])
                      for field in segment_fields]
        arcpy.SetProgressorPosition()

    except Exception:
        arcpy.AddError("Error occured while getting AADT or Crash Years.")
        return []

    # Get USRAP segements
    values = get_usrap_segments(input_segment_fc)
    if not values:
        return []
    usrap_segment_layer, usrap_count = values[0], values[1]
    arcpy.SetProgressorPosition()
    arcpy.SetProgressorLabel("Assigning {0} to crashes... ".format(SEGMENTID_FIELD_NAME))

    # Perform Sptial Join with Crash Feature class
    crash_output_fc = assign_segid_to_crashes(max_dist, usrap_segment_layer,
                                              input_crash_fc, out_gdb)

    arcpy.Delete_management(usrap_segment_layer)

    if not crash_output_fc:
        return []
    arcpy.SetProgressorPosition()

    # Assign crash count per year to each segment
    segment_output_fc = assign_crashes_to_segments(
        input_segment_fc, crash_years, crash_year_field, CRASH_OUTPUT_NAME, out_gdb)

    # TODO look to see if the class behind usrap_segment_layer needs to be deleted also 
    # if its a mem class yes if its the final out no
    del usrap_segment_layer, field_type, segment_fields, values, crash_output_fc

    if not segment_output_fc:
        return []
    else:
        return crash_years, aadt_years, usrap_count, out_gdb

#===================== Merging =================================================#
def check_criteria(sorted_features_layer, conditions, criterias, check_fields, segment_route_name_field, crash_fields, temp_seg):
    """
    This function is used for performing merging of the segments.
    It first merges the segments by relaxing speed limit and then by relaxing AADT.
    """
    try:
        x=0
        condition_checks = []
        
        for condition in conditions:
            criteria = criterias[x]
            check_condition_with_aadt = build_check_condition(
                sorted_features_layer, condition, criteria, "")
            condition_checks.append(check_condition_with_aadt)
            x+=1

        #NEW FOR BY-COUNTY
        county_name_list = set([row.getValue(COUNTY_FIELD_NAME) for row in arcpy.SearchCursor(sorted_features_layer, fields=COUNTY_FIELD_NAME)])

        # Check for number of crashes per segment < per_of_segments       
        if False in condition_checks and condition != "end_result":
            condition = conditions[0]
            # Merging by relaxing Speed Limit. Include AVG_AADT value check
            add_message("-" * 80)
            add_message("Merging by relaxing Speed Limit...")
            add_message("-" * 80)
            step_count = 1
            #usrap_where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
            #arcpy.RepairGeometry_management(sorted_features_layer)
            flds = [f.name for f in arcpy.ListFields(sorted_features_layer)]
            arcpy.DeleteIdentical_management(sorted_features_layer, flds)
            del flds

            # Check select and copy to mem the unique vals from COUNTY_FIELD_NAME
            iii=0
            arcpy.CopyFeatures_management(sorted_features_layer, temp_seg)
            arcpy.MakeFeatureLayer_management(temp_seg, "tempSegLayer", "1=1")
            arcpy.DeleteFeatures_management(temp_seg)
            arcpy.Delete_management("tempSegLayer")

            for county_name in county_name_list:
                iii+=1
                add_message("Merging segments in " + str(county_name))
                w = USRAP_WHERE + " AND " + COUNTY_FIELD_NAME + " = '" + str(county_name) + "'"
                arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION", w)
                in_mem_class = r"in_memory\c" + str(iii)
                in_mem_layer = "fl" + str(iii)
                arcpy.CopyFeatures_management(sorted_features_layer, in_mem_class)
                if VERSION_USED != "10.2":
                    arcpy.RepairGeometry_management(in_mem_class, "DELETE_NULL")

                arcpy.MakeFeatureLayer_management(in_mem_class, in_mem_layer)

                next_step_count = union_segments(in_mem_layer, check_fields,
                                                "with_aadt", step_count, condition, segment_route_name_field,crash_fields, USRAP_WHERE)
                
                arcpy.SelectLayerByAttribute_management(in_mem_layer,"CLEAR_SELECTION")
                arcpy.Append_management(in_mem_layer, temp_seg)

            arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION", "{0} <> 'YES'".format(USRAP_SEGMENT_FIELD_NAME))

            arcpy.Append_management(sorted_features_layer, temp_seg)
            
            desc_fc = arcpy.Describe(sorted_features_layer)
            if hasattr(desc_fc, 'featureClass'):
                arcpy.AddMessage("Deleting: " + str(desc_fc.featureClass.catalogPath))
                arcpy.Delete_management(desc_fc.featureClass.catalogPath)
            del desc_fc
            
            arcpy.Delete_management(sorted_features_layer)
            sorted_features_layer = arcpy.MakeFeatureLayer_management(temp_seg, "sorted_features_layer")
            #check both conditions again
            x=0
            condition_checks = []
            for condition in conditions:
                criteria = criterias[x]
                check_condition_with_aadt = build_check_condition(
                    sorted_features_layer, condition, criteria, "")
                condition_checks.append(check_condition_with_aadt)
                x+=1
            if False in condition_checks and condition != "end_result":
                add_message("-" * 80)
                add_message("Merging by relaxing AADT...")
                add_message("-" * 80)

                temp_seg2 = temp_seg + "2"
                arcpy.CopyFeatures_management(sorted_features_layer, temp_seg2)
                arcpy.MakeFeatureLayer_management(temp_seg2, "tempSegLayer2", "1 = 1")
                arcpy.DeleteFeatures_management(temp_seg2)
                arcpy.Delete_management("tempSegLayer2")

                for county_name in county_name_list:
                    iii+=1
                    add_message("Merging segments in " + str(county_name))

                    w= USRAP_WHERE + " AND " + COUNTY_FIELD_NAME + " = '" + str(county_name) + "'"
                    arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION", w)
                    in_mem_class = r"in_memory\c" + str(iii)
                    arcpy.CopyFeatures_management(sorted_features_layer, in_mem_class)
                    in_mem_layer = "fl" + str(iii)
                    arcpy.MakeFeatureLayer_management(in_mem_class, in_mem_layer)

                    _ = union_segments(in_mem_layer, check_fields,
                                    "without_aadt", next_step_count, condition, segment_route_name_field,crash_fields, USRAP_WHERE)
                    arcpy.SelectLayerByAttribute_management(in_mem_layer,"CLEAR_SELECTION")
                    arcpy.Append_management(in_mem_layer, temp_seg2)


                arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION", "{0} <> 'YES'".format(USRAP_SEGMENT_FIELD_NAME))
                arcpy.Append_management(sorted_features_layer, temp_seg2)

                desc_fc = arcpy.Describe(sorted_features_layer)
                if hasattr(desc_fc, 'featureClass'):
                    arcpy.AddMessage("Deleting: " + str(desc_fc.featureClass.catalogPath))
                    arcpy.Delete_management(desc_fc.featureClass.catalogPath)
                del desc_fc

                arcpy.Delete_management(sorted_features_layer)
                sorted_features_layer = arcpy.MakeFeatureLayer_management(temp_seg2, "sorted_features_layer")

                #check both conditions again
                x=0
                condition_checks = []
                for condition in conditions:
                    criteria = criterias[x]
                    check_condition_with_aadt = build_check_condition(
                        sorted_features_layer, condition, criteria, "end_result")
                    condition_checks.append(check_condition_with_aadt)
                    x+=1
                if False in condition_checks and condition != "end_result":
                    add_warning("Speed Limit and AADT have been relaxed but the criteria is still not met.\n" +"Merging will not be performed further.")
                    add_message("Please review output error tables...")
            else:
                add_message("Criteria met. Merging will not be performed further.")
        else:
            add_message("Criteria met. Merging will not be performed further.")
        add_message("-" * 80)
        return temp_seg2
    except Exception as ex:
        print(ex.message)
        arcpy.AddError("Error occurred while checking conditions..")
        sys.exit()

def get_avg_per_segment(layer):
    """
    This function called to check whether segment meeting the required criteria
    """
    cnt=0
    total=0
    with arcpy.da.SearchCursor(layer, [TOTAL_CRASH_FIELD_NAME]) as search_cursor:
        for row in search_cursor:
            total += float(row[0])
            cnt += 1
    return float(total/cnt)

def build_check_condition(sorted_features_layer, condition, criteria, param):
    """
    This function called to check whether segment meeting the required criteria
    """
    try:
        arcpy.SelectLayerByAttribute_management(sorted_features_layer,
                                                "CLEAR_SELECTION")
        #   First get USRAP Segment count
        usrap_where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
        usrap_segments = arcpy.SelectLayerByAttribute_management(
            sorted_features_layer, "NEW_SELECTION", usrap_where)
        usrap_count = int(arcpy.GetCount_management(usrap_segments)[0])

        #   Get segments satisfying criteria
        if criteria.upper() == "min average".upper():
            crash_where = "{0} <= {1}".format(AVG_CRASHES_FIELD_NAME, condition)
            add_message("Checking minimum average number of crashes per segment criteria.")
            avg_number_crashes = get_avg_per_segment(usrap_segments)
        else:
            crash_where = "{0} <= 3".format(AVG_CRASHES_FIELD_NAME)

        result_features = arcpy.SelectLayerByAttribute_management(
            sorted_features_layer, "SUBSET_SELECTION", crash_where)
        selected_count = int(arcpy.GetCount_management(result_features)[0])

        #   Check the condition and display the appropriate message
        if criteria.upper() == "min average".upper():
            if param.upper() == "relax_aadt".upper():
                msg = (("Average number of crashes per segment after" +
                        " relaxing speed limit: {0}")
                       .format(avg_number_crashes))
            elif param.upper() == "end_result".upper():
                msg = (("Average number of crashes per segment after" +
                        " relaxing AADT: {0}")
                       .format(avg_number_crashes))
            else:
                msg = (("Average number of crashes per segment: {0}")
                       .format(avg_number_crashes))
            arcpy.AddMessage(msg)
            #if_condition = int(selected_count) > 0
            if_condition = avg_number_crashes > int(condition)
            if if_condition:
                add_message("Expected Average: {0}, condition was met".format(condition))
            else:
                add_warning("Expected Average: {0}, condition was not met...".format(condition))
                
        else:
            # Calculating percentage with respect to USRAP segment count
            add_message("-" * 80)
            add_message("Checking for percentage of segments with TOTAL_CRASH <= 3 " +
               "criteria...")
            per_segments = (float(selected_count) * 100) / float(usrap_count)
            if param.upper() == "relax_aadt".upper():
                msg = (("% of USRAP segments having crashes <= 3 after " +
                        "relaxing speed limit : {0}%")
                       .format('%.3f' % per_segments))
            elif param.upper() == "end_result".upper():
                msg = (("% of USRAP segments having crashes <= 3 after "
                        "relaxing AADT : {0}%").format('%.3f' % per_segments))
            else:
                msg = (("% of USRAP segments having crashes <= 3 : {0}%")
                       .format('%.3f' % per_segments))
            arcpy.AddMessage(msg)
            if_condition = int(per_segments) < int(condition)
            if if_condition:
                add_message("{0}% max for segments with <= 3 crashes was met.".format(condition))
            else:
                add_warning("{0}% max for segments with <= 3 crashes was not met.".format(condition))
        
        arcpy.SelectLayerByAttribute_management(sorted_features_layer,
                                                "CLEAR_SELECTION")        
        return if_condition
     
    except Exception:
        arcpy.AddError("Error occurred while checking conditions..")
        sys.exit()

def calculate_percentage_change(val1, val2):
    return math.fabs(((val2-val1)/val1) * 100)

def calculate_length_weighted_avg(val1, length1, val2, length2):
    """
    Calculates the length weighted average
    """
    if val1 != None and length1 != None and val2 != None and length2 != None:
        a = ((float(val1)*float(length1)) + (float(val2)*float(length2)))
        b = (float(length1) + float(length2))
        return round(a/b, 1)
    elif val1 != None and val2 != None:
        return round((val1 + val2)/2, 1)

def union_segments(sorted_features_layer, check_fields, aadt_check, step_count,
                  condition, segment_route_name_field, crash_fields, where):
    """
    Unions reqiured segments
    """
    try:
        #get sorted cursor
        delete_oids = []
        union_geoms = []
        seg_ids = {}

        i=0

        # Get the field indexs up front so we don't have to re-check for each
        # iteration of the loop    
        county_field_index = check_fields.index(COUNTY_FIELD_NAME)
        road_name_field_index = check_fields.index(segment_route_name_field)
        roadway_type_field_index = check_fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)
        seg_id_field_index = check_fields.index(SEGMENTID_FIELD_NAME)
        aadt_field_index = check_fields.index(AVG_AADT_FIELD_NAME)

        arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION",where)
        with arcpy.da.UpdateCursor(sorted_features_layer, check_fields, sql_clause=(None, 'ORDER BY ' + USRAP_ROADWAY_TYPE_FIELDNAME + " DSC")) as update_cursor:
            for row in update_cursor:
                if row[0] not in delete_oids:
                    i+=1
                    if row[-1] in ["", None]:
                        continue

                    where2 = where + " AND {0} = '{1}' AND {2} = '{3}' AND {4} = '{5}'".format(check_fields[county_field_index], row[county_field_index], 
                                                                                         check_fields[road_name_field_index], row[road_name_field_index],
                                                                                         check_fields[roadway_type_field_index], row[roadway_type_field_index])

                    arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION", where2)

                    #for each usRAP segment query for additional segments that touch
                    arcpy.SelectLayerByLocation_management(sorted_features_layer, "INTERSECT", row[-1], selection_type="SUBSET_SELECTION")
                    with arcpy.da.SearchCursor(sorted_features_layer, check_fields) as search_cursor:
                        for search_row in search_cursor:
                            #get values from source feature
                            county_1 = row[county_field_index]
                            road_name_1 = row[road_name_field_index]
                            roadway_type_1 = row[roadway_type_field_index]
                            seg_id1 = row[seg_id_field_index]
                            aadt_1 = row[aadt_field_index]

                            #get values from search feature
                            county_2 = search_row[county_field_index]                  
                            road_name_2 = search_row[road_name_field_index]                     
                            roadway_type_2 = search_row[roadway_type_field_index]                      
                            seg_id2 = search_row[seg_id_field_index]
                            aadt_2 = search_row[aadt_field_index]

                            #if we have a geom and not previously flagged for deletion
                            if search_row[-1] != None and delete_oids.count(row[0]) == 0:
                                #verify that the values match between the source segment and the search segment
                                if county_1 == county_2 and road_name_1 == road_name_2 and roadway_type_1 == roadway_type_2:
                                    #verify the search row has not been flagged for deletion and is not the same as the source row
                                    if delete_oids.count(search_row[0]) == 0 and row[0] != search_row[0]:
                                        #check if AADT is within <user defined>% range...
                                        # if so calculate length weigthed average and union the segments
                                        aadt_change_percentage = calculate_percentage_change(aadt_1,aadt_2)
                                        new_aadt = 0
                                        crash_field_values = {}
                                        if aadt_check == "with_aadt":
                                            #This is checked while relaxing speed limit
                                            if aadt_change_percentage < 20:
                                                #need to maintain and update field values
                                                for crash_field in crash_fields:
                                                    row_value = row[check_fields.index(crash_field)]
                                                    search_row_value = search_row[check_fields.index(crash_field)]
                                                    crash_field_values[crash_field] = float(row_value) + float(search_row_value)
                                                if aadt_change_percentage != 0:
                                                    new_aadt = calculate_length_weighted_avg(aadt_1, row[-2], aadt_2, search_row[-2])
                                                    row[check_fields.index(AVG_AADT_FIELD_NAME)] = new_aadt
                                                try:
                                                    if row[-1] != None:
                                                        row[-1] = search_row[-1].union(row[-1])
                                                    else:
                                                        row[-1] = search_row[-1]
                                                except Exception as ex:
                                                    arcpy.AddWarning(ex.message)
                                                pass
                                            
                                                union_geoms.append(row[0])
                                                for f in crash_field_values.keys():
                                                    row[check_fields.index(f)] = crash_field_values[f]
                                                new_total = float(crash_field_values[TOTAL_CRASH_FIELD_NAME])
                                                new_avg = 0
                                                if new_total > 0:
                                                    new_avg = new_total / float(len(crash_fields) -1)
                                                row[check_fields.index(AVG_CRASHES_FIELD_NAME)] = new_avg
                                                update_cursor.updateRow(row)
                                                delete_oids.append(search_row[0])
                                                seg_ids[seg_id2] = seg_id1
                                        else:
                                            #This is checked while relaxing AADT
                                            for crash_field in crash_fields:
                                                row_value = row[check_fields.index(crash_field)]
                                                search_row_value = search_row[check_fields.index(crash_field)]
                                                crash_field_values[crash_field] = float(row_value) + float(search_row_value)
                                            if aadt_change_percentage != 0:
                                                new_aadt = calculate_length_weighted_avg(aadt_1, row[-2], aadt_2, search_row[-2])
                                                row[aadt_field_index] = new_aadt
                                            
                                            for f in crash_field_values.keys():
                                                row[check_fields.index(f)] = crash_field_values[f]    
                                            new_total = float(crash_field_values[TOTAL_CRASH_FIELD_NAME])
                                            new_avg = 0
                                            if new_total > 0:
                                                new_avg = new_total / float(len(crash_fields) -1)
                                            row[check_fields.index(AVG_CRASHES_FIELD_NAME)] = new_avg  
                                        
                                            try:    
                                                if row[-1] != None:
                                                    row[-1] = search_row[-1].union(row[-1])
                                                else:
                                                    row[-1] = search_row[-1]
                                            except Exception as ex:
                                                arcpy.AddWarning(ex.message)
                                            pass
                                            update_cursor.updateRow(row)
                                            delete_oids.append(search_row[0]) 
                                            seg_ids[seg_id2] = seg_id1               

        #delete extras
        if len(delete_oids) > 0:
            deleted_oids = map(str, delete_oids)
            field_oid = str(arcpy.Describe(sorted_features_layer).OIDFieldName)
            if len(deleted_oids) > 1000:
                x = 1000
                xx = 0
                p = 0
                sel = 'NEW_SELECTION'
                while x <= len(deleted_oids):
                    if xx > len(deleted_oids):
                        break
                    partial_oids = deleted_oids[p:x]
                    where = field_oid +' = ' + ' OR {0} = '.format(field_oid).join(partial_oids)
                    arcpy.SelectLayerByAttribute_management(sorted_features_layer, sel, where)
                    p = x
                    x += x
                    xx = x
                    if x > len(deleted_oids):
                        x = len(deleted_oids)
                    sel = 'ADD_TO_SELECTION'

            else:
                where = field_oid +' = ' + ' OR {0} = '.format(field_oid).join(deleted_oids)
                arcpy.SelectLayerByAttribute_management(sorted_features_layer,
                                                            'NEW_SELECTION',
                                                            where)
            arcpy.DeleteRows_management(sorted_features_layer)

            current_values = []
            for seg_value in seg_ids.keys():
                current_values.append(str(seg_value))

            where = SEGMENTID_FIELD_NAME +' = ' + ' OR {0} = '.format(SEGMENTID_FIELD_NAME).join(current_values)

            arcpy.AddMessage("Updating crash features...")
            with arcpy.da.UpdateCursor(CRASH_OUTPUT_NAME, [SEGMENTID_FIELD_NAME], where_clause=where) as update_points_cursor:
                for u_row in update_points_cursor:
                    u_row[0] = seg_ids[u_row[0]]
                    update_points_cursor.updateRow(u_row)

        if len(union_geoms) > 0:
            try:
                union_geom_ids = map(str, union_geoms)
                field_oid = str(arcpy.Describe(sorted_features_layer).OIDFieldName)
                union_where = field_oid +' = ' + ' OR {0} = '.format(field_oid).join(union_geom_ids)
                union_segments(sorted_features_layer, check_fields, aadt_check, step_count,
                      condition, segment_route_name_field, crash_fields, union_where)
            except Exception as ex:
                arcpy.AddWarning("Error occured during union")
                arcpy.AddWarning(ex.message)
                if row != None:
                    arcpy.AddWarning("Error occurred while merging segments with" +
                                 " OBJECTID {0}.".format(row[0]))
                    add_calculate_error(row, check_fields)
                pass
    except Exception as ex:
        arcpy.AddError("Error while merging: " + str(ex.message))
        arcpy.AddWarning(ex.message)
        if row != None:
            arcpy.AddWarning("Error occurred while merging segments with" +
                         " OBJECTID {0}.".format(row[0]))
            add_calculate_error(row, check_fields)
        pass
        #sys.exit()

def add_calculate_error(uc_row, check_fields):
    """
    This function adds the error in Segment Error Table if any ocurrs while
    calculating values for segments getting merged.
    """
    error_msg = "Error occurred while calculating update row values"
    error_row = (uc_row[0], uc_row[1],
                 uc_row[check_fields.index(AVG_CRASHES_FIELD_NAME)], error_msg)
    segment_insert_fields = [field[0]
                             for field in SEGMENT_ERROR_TABLE_FIELDS]
    with arcpy.da.InsertCursor(SEGMENT_ERROR_TABLE_NAME,
                               segment_insert_fields) as insert_cursor:
        insert_cursor.insertRow(error_row)

#===================== Creating Error Logs ====================================#
def create_error_tables(out_gdb):
    """
    This function creates the Error Tables needed to log the errors
    """
    try:
        #   Crash error table
        arcpy.CreateTable_management(arcpy.env.workspace,
                                     CRASH_ERROR_TABLE_NAME)

        for field in CRASH_ERROR_TABLE_FIELDS:
            arcpy.AddField_management(arcpy.env.workspace + os.sep + CRASH_ERROR_TABLE_NAME, field[0],
                                      field[1], field_alias=field[0])

        #   Segment error table
        arcpy.CreateTable_management(arcpy.env.workspace,
                                     SEGMENT_ERROR_TABLE_NAME)

        for field in SEGMENT_ERROR_TABLE_FIELDS:
            arcpy.AddField_management(arcpy.env.workspace + os.sep + SEGMENT_ERROR_TABLE_NAME, field[0],
                                      field[1], field_alias=field[0])

        #   Summary error table
        arcpy.CreateTable_management(arcpy.env.workspace,
                                     ERROR_SUMMARY_TABLE_NAME)

        for field in SUMMARY_ERROR_TABLE_FIELDS:
            arcpy.AddField_management(arcpy.env.workspace + os.sep + ERROR_SUMMARY_TABLE_NAME, field[0],
                                      field[1], field_length=field[2],
                                      field_alias=field[0])
        return True

    except Exception:
        return False

def get_segment_error(min_avg_crashes, full_out_path):
    """
    This function checks for Segment not meeting AVG_CRASH criteria and
    add them to the error log table.
    """
    try:
        segment_insert_fields = [field[0]
                                 for field in SEGMENT_ERROR_TABLE_FIELDS]
        crash_per_seg = 0
        per_of_segment = 0
        avg_check = min_avg_crashes if min_avg_crashes > 3 else 3

        segment_errors = []

        where = "{0} <= {1}".format(AVG_CRASHES_FIELD_NAME, avg_check)
        with arcpy.da.SearchCursor(SEGMENT_OUTPUT_NAME,
                                   ["OID@", SEGMENTID_FIELD_NAME, TOTAL_CRASH_FIELD_NAME,
                                    AVG_CRASHES_FIELD_NAME],
                                   where) as segment_cursor:
            for segment_row in segment_cursor:
                if (int(segment_row[-2]) in range(0, 4) and
                        segment_row[-2] <= 3):
                    error_msg = "Total crash <= 3"
                    per_of_segment += 1
                elif (int(avg_check) > 3 and
                        int(segment_row[-1]) in range(3, int(avg_check) + 1) and 
                            segment_row[-1] <= int(avg_check)):
                    error_msg = "Average crash <= {0}".format(min_avg_crashes)
                    crash_per_seg += 1
                else:
                    continue
                error_row = (segment_row[0], segment_row[1], segment_row[3], segment_row[2], error_msg)
                segment_errors.append(error_row)

        with arcpy.da.InsertCursor(SEGMENT_ERROR_TABLE_NAME,
                                segment_insert_fields)\
                                as insert_cursor:
            for error in segment_errors:
                insert_cursor.insertRow(error)
        del segment_errors

        #   First get USRAP Segment count
        usrap_where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
        usrap_segments = arcpy.MakeFeatureLayer_management(SEGMENT_OUTPUT_NAME, "usrap_layer", usrap_where)
        usrap_count = int(arcpy.GetCount_management(usrap_segments)[0])

        #   Calculate the percentage with respect to USRAP segment count
        criteria1_per = (float(crash_per_seg) / float(usrap_count)) * 100
        criteria2_per = (float(per_of_segment) / float(usrap_count)) * 100

        summary_error_list = [["% of Segments not meeting the 'minimum " +
                               "average number of crashes per segment " +
                               "criteria'", crash_per_seg,
                               "{0}%".format(round(criteria1_per, 4))],
                              ["% of Segments having crashes <= 3 ",
                               per_of_segment,
                               "{0}%".format(round(criteria2_per, 4))]]

        #   Insert the % of errors into summary error table
        insert_summary_errors(summary_error_list)
        return True

    except Exception as ex:
        arcpy.AddError("Error occurred while generating Segment Error table.")
        arcpy.AddWarning(ex.message)
        return False

def get_crash_errors(crash_year_field, crash_route_field,
                     segment_route_name_field):
    """
    This function checks crashes for errors and logs them to the crash error table
    """
    try:
        unassigned_crashes = 0
        blank_year = 0
        blank_route = 0
        unmatched_routes = 0

        crash_errors = []

        # DICT {SEGID : ROUTE_NAME}
        segment_details = {}
        with arcpy.da.SearchCursor(SEGMENT_OUTPUT_NAME,
                                    [segment_route_name_field, SEGMENTID_FIELD_NAME]) as seg_search_cursor:
            for row in seg_search_cursor:
                segment_details[row[1]] = row[0]

        with arcpy.da.SearchCursor(CRASH_OUTPUT_NAME, ["OID@", crash_year_field,
                                                     crash_route_field,
                                                     SEGMENTID_FIELD_NAME])\
                                                     as crash_search_cursor:

            for crash_row in crash_search_cursor:
                # If no USRAP_SEGID then the crash was not assigned to a segment
                if crash_row[-1] in ["", None]:
                    unassigned_crashes += 1
                    error_msg = ("Crash outside the user specified proximity distance from segment.")
                    error_row = [crash_row[0], crash_row[1], crash_row[2], "-", "-", error_msg]
                    if crash_row[2] == None:
                        error_row[2] = ""
                    crash_errors.append(error_row)
                else:
                    #get the route name by segid
                    if segment_details.keys().count(crash_row[3]) > 0:
                        seg_route_name = segment_details[crash_row[3]] 
                    else:
                        seg_route_name = ""

                    # Check if crash year is maintained
                    if crash_row[1] in ["", None]:
                        unassigned_crashes += 1
                        blank_year += 1
                        error_msg = "Crash year is not specified."
                        error_row = [crash_row[0], crash_row[1], crash_row[2], crash_row[3], seg_route_name, error_msg]
                        crash_errors.append(error_row)

                    # Check if route name is maintained
                    if crash_row[2] in ["", None]:
                        blank_route += 1
                        error_msg = "Crash Route Name is not specified."
                        error_row = [int(crash_row[0]), int(crash_row[1]), str(crash_row[2]),
                                     str(crash_row[3]), str(seg_route_name), error_msg]
                        crash_errors.append(error_row)

                    else:
                        # Verify if crash route-name matches route route-name
                        if seg_route_name != "":
                            if seg_route_name == crash_row[2]:
                                continue
                        else:
                            unmatched_routes += 1
                            error_msg = ("Crash Route Name does not match with" +
                                            " Segment Route Name.")
                            error_row = [str(crash_row[0]), crash_row[1],
                                            crash_row[2], crash_row[3],
                                            seg_route_name, error_msg]
                            crash_errors.append(error_row)

        insert_crash_error(crash_errors)
        del crash_errors
        # Calculate the percentage of each type of crash error and log to Error Summary table
        crash_count = int(arcpy.GetCount_management(CRASH_OUTPUT_NAME)[0])
        if crash_count > 0:
            unassigned_per = (float(unassigned_crashes) / float(crash_count) * 100)
            blank_year_per = (float(blank_year) / float(crash_count) * 100)
            blank_rt_per = (float(blank_route) / float(crash_count) * 100)
            unmatched_rt_per = (float(unmatched_routes) / float(crash_count) * 100)

            summary_error_list = [["% of Crashes outside proximity distance",
                                   unassigned_crashes,
                                   "{0}%".format(round(unassigned_per, 4))],

                                  ["% of Crashes with Year not maintained",
                                   blank_year,
                                   "{0}%".format(round(blank_year_per, 4))],

                                  ["% of Crashes with Route Name not maintained",
                                   blank_route,
                                   "{0}%".format(round(blank_rt_per, 4))],

                                  ["% of Crashes where Route Name does not" +
                                   " match Segment Route Name",
                                   unmatched_routes,
                                   "{0}%".format(round(unmatched_rt_per, 4))]]

            insert_summary_errors(summary_error_list)
        return unassigned_crashes

    except Exception as ex:
        arcpy.AddError("Error occurred while generating crash error table.")
        arcpy.AddWarning(ex.message)
        return False

def insert_crash_error(errors):
    """
    This function insert the crashes with erros in Crash Error log
    table
    """
    try:
        crash_insert_fields = [field[0] for field in CRASH_ERROR_TABLE_FIELDS]
        with arcpy.da.InsertCursor(CRASH_ERROR_TABLE_NAME,
                                   crash_insert_fields) as insert_cursor:
            for error in errors:
                insert_cursor.insertRow(error)
        del crash_insert_fields
    except Exception as ex:
        arcpy.AddError("Error occurred while inserting crash error.")
        arcpy.AddError(ex.message)

def insert_summary_errors(summary_error_list):
    """
    This function insert the % of each type of error into Summary Error Table
    """
    summary_insert_fields = [field[0] for field in SUMMARY_ERROR_TABLE_FIELDS]
    with arcpy.da.InsertCursor(ERROR_SUMMARY_TABLE_NAME,
                               summary_insert_fields) as summary_cursor:
        for error in summary_error_list:
            summary_cursor.insertRow(error)
    del summary_insert_fields

def check_total_crashes(unassigned_crashes):
    """
    This functions checks for total of all unassigned crashes and all assigned
    crashes is equal to the number of crashes in the input data set
    Unassigned Crashes - Crashes for which USRAP_SEGID is None
    Assigned Crashes - Sum of total crash field in segment feature class
    """
    try:
        #   Get total number of crashes
        crash_count = int(arcpy.GetCount_management(CRASH_OUTPUT_NAME)[0])

        #   Get number of assigned crashes
        assigned_crashes = 0
        where = "{0} <> 0".format(TOTAL_CRASH_FIELD_NAME)
        with arcpy.da.SearchCursor(SEGMENT_OUTPUT_NAME,
                                   [TOTAL_CRASH_FIELD_NAME], where)\
                                   as segment_search_cursor:
            for sc_row in segment_search_cursor:
                assigned_crashes += sc_row[0]
        #del segment_search_cursor

        arcpy.AddMessage(("Total number of assigned crashes : {0}")
                         .format(assigned_crashes))
        arcpy.AddMessage(("Total number of unassigned crashes : {0}")
                         .format(unassigned_crashes))
        arcpy.AddMessage(("Number of crashes in input feature class : {0}")
                         .format(crash_count))
        msg = ("The number of crashes assigned to all" +
               " segments on the network plus all unassigned" +
               " crashes is not equal to the total number of" +
               " crashes in the input data set.")

        if assigned_crashes + unassigned_crashes != crash_count:
            arcpy.AddWarning("\n{0}".format(msg))
        else:
            msg = msg.replace("not", "")
            arcpy.AddMessage("\n{0}".format(msg))

        summary_error_list = [[msg, "-", "-"]]
        insert_summary_errors(summary_error_list)

    except Exception as ex:
        arcpy.AddError("Error occurred while generating error tables.")
        arcpy.AddWarning(ex.message)

def add_warning(msg):
    arcpy.AddWarning(msg)

def add_message(msg):
    arcpy.SetProgressorLabel(msg)
    arcpy.AddMessage(msg)

def add_formatted_message(msg, fc):
    fc_name = os.path.basename(fc)
    msg = msg.format(fc_name)
    arcpy.SetProgressorLabel(msg)
    arcpy.AddMessage(msg)

def check_path(fc):
    desc = arcpy.Describe(fc)
    if hasattr(desc, 'featureClass'):
        fc = desc.featureClass.catalogPath
    del desc
    return fc

def main():
    """
    Main Function
    """
    # input parameters
    input_segment_fc = arcpy.GetParameterAsText(0)
    segment_route_name_field = arcpy.GetParameterAsText(1)
    segment_route_type_field = arcpy.GetParameterAsText(2)

    input_crash_fc = arcpy.GetParameterAsText(3)
    crash_route_field = arcpy.GetParameterAsText(4)
    crash_year_field = arcpy.GetParameterAsText(5)

    max_dist = arcpy.GetParameterAsText(6)
    min_avg_crashes = arcpy.GetParameter(7)
    per_of_segments = arcpy.GetParameter(8)

    output_folder = arcpy.GetParameterAsText(9)

    #get full path if FeatureLayer
    input_segment_fc = check_path(input_segment_fc)
    input_crash_fc = check_path(input_crash_fc)

    global SEGMENT_OUTPUT_PATH

    # Assigning Segmemnt IDs to Crashes and crash count to Segments
    returned_values = assign_values(input_segment_fc, input_crash_fc,
                                    crash_year_field, max_dist,
                                    output_folder)
    if not returned_values:
        return

    crash_years, aadt_years = returned_values[0], returned_values[1]
    usrap_count = returned_values[2]
    out_gdb = returned_values[3]

    #   Create Errors Log tables
    table_created = create_error_tables(out_gdb)

    # Merging Segments
    steps = usrap_count / SEGMENT_INCREMENT
    if usrap_count % SEGMENT_INCREMENT != 0:
        steps += 1
    steps = int((steps * 2) + 2)
    arcpy.ResetProgressor()
    arcpy.SetProgressor("step", "Merging segments..", 0, steps, int(SEGMENT_INCREMENT))
    try:
        temp_seg = SEGMENT_OUTPUT_PATH
        arcpy.RepairGeometry_management(temp_seg)
        sorted_path = os.path.join(out_gdb, "sorted_segments")
        sorted_segments = arcpy.Sort_management(temp_seg, sorted_path, [["SHAPE_Length", "DESCENDING"]])
        sorted_features_layer = arcpy.MakeFeatureLayer_management(sorted_segments, "sorted_features_layer")

        #   Delete the previous Segment Feature Class as it is no longer needed
        arcpy.Delete_management(temp_seg)
        del temp_seg
      
        SEGMENT_OUTPUT_PATH = sorted_path

        #   Sequence of fields in check_fields is very important.
        #   If more fields need to be checked, add it after "COUNTY_FIELD_NAME"
        #   and before "AREA_TYPE_FIELD".
        #   This will help maintain the sequence of field checking
        check_fields = ["OID@", SEGMENTID_FIELD_NAME, COUNTY_FIELD_NAME,
                        segment_route_name_field, segment_route_type_field,
                        LANES_FIELD_NAME, MEDIANS_FIELD_NAME, USRAP_ROADWAY_TYPE_FIELDNAME, AREA_TYPE_FIELD]
        crash_fields = []
        for year in crash_years:
            check_fields += ["{0}{1}".format(CRASH_YEAR_FIELD, year)]
            crash_fields += ["{0}{1}".format(CRASH_YEAR_FIELD, year)]
        crash_fields.append(TOTAL_CRASH_FIELD_NAME)

        check_fields += [TOTAL_CRASH_FIELD_NAME, AVG_CRASHES_FIELD_NAME]

        for year in aadt_years:
            check_fields += ["{0}{1}".format(AADT_FIELD_NAME, year)]

        check_fields += [AVG_AADT_FIELD_NAME, "SHAPE@LENGTH", "SHAPE@"]

        arcpy.SetProgressorPosition(1)

        #   Check for number of crashes per segment and min avg per segment
        #TODO make sure temp_seg is physical
        full_out_path = output_folder + os.sep + OUTPUT_GDB_NAME + os.sep + SEGMENT_OUTPUT_NAME
        ts = check_criteria(sorted_features_layer, [min_avg_crashes, per_of_segments],
                       ["min average", "per segments"],
                       check_fields, segment_route_name_field, crash_fields, full_out_path)

        arcpy.Delete_management(sorted_path)
        del sorted_path

        arcpy.SetProgressorPosition(int(steps) - 1)
        add_message("Merging of segments completed.")

        #   Clear the selection from the layer and copy it as new feature class
        #   in output Geodatabase
        sorted_features_layer = arcpy.MakeFeatureLayer_management(ts,"sorted_features_layer", "1=1")
        arcpy.CopyFeatures_management(sorted_features_layer, full_out_path)
        arcpy.Delete_management(sorted_features_layer)
        del sorted_features_layer
        arcpy.Delete_management(ts)
        del ts

        arcpy.SetProgressorPosition(steps)
        add_message("-" * 80)

    except arcpy.ExecuteError:
        arcpy.AddError("Error occured while Merging segments..")

    except Exception:
        arcpy.AddError("Error occured while Merging segments..")
        pass

    # Assign Segment IDs to Crashes from mergerd segments
    if not table_created:
        arcpy.AddError("Error occurred while creating error log tables.")
        return

    msg = "Checking errors.."
    arcpy.SetProgressor("step", msg, 0, 3, 1)
    add_message(msg)

    #   Check for faults in segment feature class output
    segment_error_added = get_segment_error(min_avg_crashes, full_out_path)

    if not segment_error_added:
        return

    arcpy.SetProgressorPosition(2)
    #   Check for faults in crashes feature class output
    unassigned_crashes = get_crash_errors(crash_year_field,
                                          crash_route_field,
                                          segment_route_name_field)
    if not unassigned_crashes:
        return
    arcpy.SetProgressorPosition(3)

    #   Check if Unassigned crashes and Assigned crashes are equal to Total
    #   crashes in input dataset
    check_total_crashes(unassigned_crashes)

    arcpy.Delete_management("in_memory")

    del input_segment_fc, segment_route_name_field, segment_route_type_field
    del SEGMENT_OUTPUT_PATH, sorted_segments, returned_values
    del input_crash_fc, crash_route_field, crash_year_field, max_dist
    del min_avg_crashes, per_of_segments, output_folder
    del crash_years, aadt_years, usrap_count, out_gdb, table_created, check_fields, crash_fields
    del unassigned_crashes, segment_error_added

    arcpy.env.workspace = None
    arcpy.ResetProgressor()

if __name__ == '__main__':
    main()