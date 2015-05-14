import arcpy
import os
import sys
import math, time

# pylint: disable = E1103, E1101, R0914, W0703, R0911, R0912, R0915, C0302

arcpy.env.overwriteOutput = True

IN_MEMORY = 'in_memory'

#======================= Configuration Part ===================================#

#   Specify the name of the Crash Output Feature Class
CRASH_OUTPUT_NAME = "CrashOutput"

#   Specify the name of the Segment Output Feature Class
SEGMENT_OUTPUT_NAME = "SegmentOutput"

#   Specify the name of Output FileGeodatabase
OUTPUT_GDB_NAME = "CrashAssignmentOutput.gdb"

#   Specify names for required fields
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

#   Set increment value for progressor while merging segments
SEGMENT_INCREMENT = 10

#   Crash error table fields
CRASH_ERROR_TABLE_FIELDS = [["CrashOID", "LONG"], ["CrashYear", "SHORT"],
                            ["CrashRouteName", "TEXT"], [SEGMENTID_FIELD_NAME, "TEXT"],
                            ["SegmentRouteName", "TEXT"],
                            ["ErrorMessage", "TEXT"]]

#   Segment error table fields
SEGMENT_ERROR_TABLE_FIELDS = [["SegmentOID", "LONG"], [SEGMENTID_FIELD_NAME, "TEXT"],
                              ["AVG_CRASH", "TEXT"], [TOTAL_CRASH_FIELD_NAME, "TEXT"],
                              ["ErrorMessage", "TEXT"]]

#   Error Summary Table fields
SUMMARY_ERROR_TABLE_FIELDS = [["ErrorType", "TEXT", 500], ["Count", "TEXT", 50],
                              ["Percentage", "TEXT", 50]]

#   Specify name for the error log tables
CRASH_ERROR_TABLE_NAME = "CrashErrorTable"
SEGMENT_ERROR_TABLE_NAME = "SegmentErrorTable"
ERROR_SUMMARY_TABLE_NAME = "SummaryErrorTable"

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
        arcpy.env.workspace = IN_MEMORY
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
        #   Check if "USRAP_SEGMENT" field exist in segment feature class
        segment_fields = [(field.name).upper() for field
                          in arcpy.ListFields(input_segment_fc)]
        if USRAP_SEGMENT_FIELD_NAME not in segment_fields:
            arcpy.AddMessage("{0} field not found in input segment feature " +
                             "class.".format(USRAP_SEGMENT_FIELD_NAME))
            return []

        #   Make the selection
        total_segments = int(arcpy.GetCount_management(input_segment_fc)[0])
        where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
        segment_layer = arcpy.MakeFeatureLayer_management(
            input_segment_fc, "segment_layer", where)[0]
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

def assign_segid_to_crashes(max_dist, usrap_segment_layer, input_crash_fc):
    """
    This function first creates the Field mapping and then performs a
    spatial join between Crash Feature Class and Segment Feature Class
    """
    try:
        arcpy.AddMessage(("Assigning {0} to crashes... ")
                         .format(SEGMENTID_FIELD_NAME))
        #   Specify target features, join features
        target_features = input_crash_fc
        join_features = usrap_segment_layer

        #   Create a new fieldmappings and add the two input feature classes.
        field_mappings = arcpy.FieldMappings()
        field_mappings.addTable(target_features)
        field_mappings.addTable(join_features.dataSource)

        #   Retain all the fields from crash feature class from field mappings
        #   and remove all fields from segment feature class except
        #   SEGMENTID_FIELD_NAME
        desc = arcpy.Describe(target_features)
        retained_fields = [(fld.name).upper() for fld in desc.fields]
        retained_fields += [SEGMENTID_FIELD_NAME]

        for map_field in field_mappings.fields:
            if (map_field.name).upper() in retained_fields:
                continue
            field_index = field_mappings.findFieldMapIndex(map_field.name)
            field_mappings.removeFieldMap(field_index)

        arcpy.SpatialJoin_analysis(
            target_features, join_features, CRASH_OUTPUT_NAME,
            "JOIN_ONE_TO_ONE", "KEEP_ALL", field_mappings, "CLOSEST", max_dist)

        #   Delete the fields "JOIN_COUNT" and "TARGET_FID" which get added to
        #   the output feature class from spatial join
        arcpy.DeleteField_management(CRASH_OUTPUT_NAME, ["JOIN_COUNT",
                                                         "TARGET_FID"])
        return True

    except arcpy.ExecuteError:
        arcpy.AddError("Error occured while performing Spatial Join for " +
                       "Crash Feature Class.")
        return False

    except Exception:
        arcpy.AddError("Error occured while performing Spatial Join for " +
                       "Crash Feature Class.")
        return False

def assign_crashes_to_segments(input_segment_fc, crash_years, crash_year_field):
    """
    This function first adds the fields for each year to get the crash count.
    Fields for total and average crashes are also added.

    """
    try:
        arcpy.AddMessage("Assigning crash count to segments...")
        #   Count is required only for the progressor labeling
        c_count = int(arcpy.GetCount_management(CRASH_OUTPUT_NAME)[0])

        arcpy.ResetProgressor()
        arcpy.SetProgressor("step", "Assigning crash count to segments..",
                            0, c_count + 1, 1)

        #   Copy the features into New Feature Class in output File GDB
        in_mem_segs = IN_MEMORY + os.sep + SEGMENT_OUTPUT_NAME
        arcpy.CopyFeatures_management(input_segment_fc, in_mem_segs)

        arcpy.AddMessage("Adding crash year fields in input segment" +
                         " feature class...")

        #   Add fields for each crash year in the segment feature class
        for year in crash_years:
            arcpy.AddField_management(in_mem_segs,
                                      "{0}{1}".format(CRASH_YEAR_FIELD,
                                                      str(year)), "SHORT")

            arcpy.CalculateField_management(in_mem_segs,
                                            "{0}{1}".format(CRASH_YEAR_FIELD,
                                                            str(year)), 0, "PYTHON_9.3")

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
                        for per_num in xrange(10, 110, 10)]
        perc = 10

        #TODO this section needs to speed up! are only USRAP sections reviewed..make sure!
        with arcpy.da.SearchCursor(CRASH_OUTPUT_NAME,
                                   [SEGMENTID_FIELD_NAME, crash_year_field], SEGMENTID_FIELD_NAME + " IS NOT NULL AND " + crash_year_field + " IS NOT NULL")\
                                   as crash_cursor:
            for row in crash_cursor:
                row_count += 1
                arcpy.SetProgressorLabel(("Finished assigning {0} crashes out" +
                                          " of {1}").format(row_count, c_count))
                arcpy.SetProgressorPosition()

                if row_count in per_val_list:
                    arcpy.AddMessage("Assignment progress : {0}%".format(perc))
                    perc += 10
                #   Skip the crashes not having segment id assigned to it
                #   and crashes for which year is not maintioned.
                if row[0] not in ["", None] and row[1] not in ["", None]:
                    where_clause = "{0} = {1}".format(SEGMENTID_FIELD_NAME,
                                                      row[0])

                    with arcpy.da.UpdateCursor(in_mem_segs,
                                               ["{0}{1}".format(\
                                               CRASH_YEAR_FIELD, int(row[1]))],
                                               where_clause) as segment_cursor:
                        for update_row in segment_cursor:
                            update_row[0] += 1
                            segment_cursor.updateRow(update_row)

        arcpy.SetProgressorPosition()
        arcpy.AddMessage("Adding total crashes and average crashes in the " +
                         "output")
        #   Calculate the total crashes and average crashes for each segment
        segment_output_fc = caluculate_sum_avg_field(crash_years)
        if not segment_output_fc:
            return False
        arcpy.AddMessage("Assignment process completed.")
        arcpy.AddMessage("-" * 80)
        return True

    except Exception:
        arcpy.AddError("Error occurred while adding count of crashes to the" +
                       " segments")
        return False

def caluculate_sum_avg_field(crash_years):
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
        with arcpy.da.UpdateCursor(IN_MEMORY + os.sep + SEGMENT_OUTPUT_NAME,
                                   update_fields) as update_cursor:
            for row in update_cursor:
                total_count = 0
                num_div_years = 0
                for i in xrange(len(crash_years)):
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

    #   Create new File Geodatabase
    out_gdb = create_gdb(output_folder)
    if not out_gdb:
        return []
    arcpy.SetProgressorPosition()

    try:
        #   Get Crash years
        arcpy.AddMessage("Getting crash years..")
        crash_years = set()
        with arcpy.da.SearchCursor(input_crash_fc,
                                   [crash_year_field]) as crash_search_cursor:
            for row in crash_search_cursor:
                if row[0] not in ["", None, " "]:
                    crash_years.add(int(row[0]))
        crash_years = sorted(crash_years)
        arcpy.SetProgressorPosition()

        #   Get AADT years
        arcpy.AddMessage("Getting AADT years..")
        field_type = "{0}*".format(AADT_FIELD_NAME)
        segment_fields = arcpy.ListFields(input_segment_fc, field_type)
        aadt_years = [int(str(field.name).split("_")[AADT_YEAR_INDEX])
                      for field in segment_fields]
        arcpy.SetProgressorPosition()

    except Exception:
        arcpy.AddError("Error occured while getting AADT or Crash Years.")
        return []

    #   Get USRAP segements
    values = get_usrap_segments(input_segment_fc)
    if not values:
        return []
    usrap_segment_layer, usrap_count = values[0], values[1]
    arcpy.SetProgressorPosition()
    arcpy.SetProgressorLabel("Assigning {0} to crashes... ".format(\
                             SEGMENTID_FIELD_NAME))

    pts = IN_MEMORY + os.sep + "validPTS"
    arcpy.MakeFeatureLayer_management(input_crash_fc, pts)

    #   Perform Sptial Join with Crash Feature class
    crash_output_fc = assign_segid_to_crashes(max_dist, usrap_segment_layer,
                                              pts)
    if not crash_output_fc:
        return []
    arcpy.SetProgressorPosition()

    #   Assign crash count per year to each segment
    segment_output_fc = assign_crashes_to_segments(
        input_segment_fc, crash_years, crash_year_field)
    if not segment_output_fc:
        return []
    else:
        return crash_years, aadt_years, usrap_count, out_gdb

#===================== Merging =================================================#
def check_criteria(sorted_features_layer, conditions, criterias, check_fields, segment_route_name_field, crash_fields):
    """
    This function is used for performing merging of the segments.
    It first merge the segments by relaxing speed limit and then relaxing AADT.
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

        #   Check for number of crashes per segment < per_of_segments       
        if False in condition_checks and condition != "end_result":
            condition = conditions[0]
            #   Merging by relaxing Speed Limit. Include AVG_AADT value check
            add_message("-" * 80)
            add_message("Merging by relaxing Speed Limit...")
            add_message("-" * 80)
            step_count = 1
            usrap_where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
            #arcpy.RepairGeometry_management(sorted_features_layer)
            flds=[f.name for f in arcpy.ListFields(sorted_features_layer)]
            arcpy.DeleteIdentical_management(sorted_features_layer,flds)

            next_step_count = union_segments(sorted_features_layer, check_fields,
                                            "with_aadt", step_count, condition, segment_route_name_field,crash_fields, usrap_where)

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
                _ = union_segments(sorted_features_layer, check_fields,
                                    "without_aadt", next_step_count, condition, segment_route_name_field,crash_fields,usrap_where)

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
    except Exception:
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
        seg_ids = []
        arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION",where)
        with arcpy.da.UpdateCursor(sorted_features_layer, check_fields, sql_clause=(None, 'ORDER BY ' + USRAP_ROADWAY_TYPE_FIELDNAME + " ASC")) as update_cursor:
            for row in update_cursor:
                #select all usRAP segments
                arcpy.SelectLayerByAttribute_management(sorted_features_layer, "NEW_SELECTION",where)
                #for each usRAP segment query for additional segments that touch
                arcpy.SelectLayerByLocation_management(sorted_features_layer, "BOUNDARY_TOUCHES", row[-1], selection_type="SUBSET_SELECTION")
                with arcpy.da.SearchCursor(sorted_features_layer, check_fields) as search_cursor:
                    for search_row in search_cursor:
                        #get values from source feature
                        county_1 = row[check_fields.index(COUNTY_FIELD_NAME)]
                        road_name_1 = row[check_fields.index(segment_route_name_field)]
                        roadway_type_1 = row[check_fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)]
                        seg_id1 = row[check_fields.index(SEGMENTID_FIELD_NAME)]
                        aadt_1 = row[check_fields.index(AVG_AADT_FIELD_NAME)]

                        #get values from search feature
                        county_2 = search_row[check_fields.index(COUNTY_FIELD_NAME)]                  
                        road_name_2 = search_row[check_fields.index(segment_route_name_field)]                     
                        roadway_type_2 = search_row[check_fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)]                      
                        seg_id2 = search_row[check_fields.index(SEGMENTID_FIELD_NAME)]
                        aadt_2 = search_row[check_fields.index(AVG_AADT_FIELD_NAME)]

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
                                            seg_ids.append([seg_id2, seg_id1])
                                    else:
                                        #This is checked while relaxing AADT
                                        for crash_field in crash_fields:
                                            row_value = row[check_fields.index(crash_field)]
                                            search_row_value = search_row[check_fields.index(crash_field)]
                                            crash_field_values[crash_field] = float(row_value) + float(search_row_value)
                                        if aadt_change_percentage != 0:
                                            new_aadt = calculate_length_weighted_avg(aadt_1, row[-2], aadt_2, search_row[-2])
                                            row[check_fields.index(AVG_AADT_FIELD_NAME)] = new_aadt
                                            
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
                                        seg_ids.append([seg_id2, seg_id1])               

        #delete extras
        if len(delete_oids) > 0:
            deleted_oids = map(str, delete_oids)
            field_oid = str(arcpy.Describe(sorted_features_layer).OIDFieldName)
            where = field_oid +' = ' + ' OR {0} = '.format(field_oid).join(deleted_oids)
            arcpy.SelectLayerByAttribute_management(sorted_features_layer,
                                                            'NEW_SELECTION',
                                                            where)
            arcpy.DeleteRows_management(sorted_features_layer)
            for seg_values in seg_ids:
                #select the old segid
                where = '{0} = {1} '.format(SEGMENTID_FIELD_NAME, seg_values[0])
                with arcpy.da.UpdateCursor(CRASH_OUTPUT_NAME, [SEGMENTID_FIELD_NAME], where_clause=where) as update_points_cursor:
                    for u_row in update_points_cursor:
                        u_row[0] = seg_values[1]
                        update_points_cursor.updateRow(u_row)
                del update_points_cursor
        if len(union_geoms) > 0:
            try:
                union_geom_ids = map(str, union_geoms)
                field_oid = str(arcpy.Describe(sorted_features_layer).OIDFieldName)
                union_where = field_oid +' = ' + ' OR {0} = '.format(field_oid).join(union_geom_ids)
                union_segments(sorted_features_layer, check_fields, aadt_check, step_count,
                      condition, segment_route_name_field, crash_fields, union_where)
            except Exception as ex:
                arcpy.AddWarning("Error occured during union")
                if row != None:
                    arcpy.AddWarning("Error occurred while merging segments with" +
                                 " OBJECTID {0}.".format(row[0]))
                    add_calculate_error(row, check_fields)
                pass
    except Exception as ex:
        arcpy.AddError("Error while merging")
        if row != None:
            arcpy.AddWarning("Error occurred while merging segments with" +
                         " OBJECTID {0}.".format(row[0]))
            add_calculate_error(row, check_fields)
        sys.exit()

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

        where = "{0} <= {1}".format(AVG_CRASHES_FIELD_NAME, avg_check)
        with arcpy.da.SearchCursor(SEGMENT_OUTPUT_NAME,
                                   ["OID@", SEGMENTID_FIELD_NAME, TOTAL_CRASH_FIELD_NAME,
                                    AVG_CRASHES_FIELD_NAME],
                                   where) as segment_cursor:
            for segment_row in segment_cursor:
                if (int(segment_row[-2]) in xrange(0, 4) and
                        segment_row[-2] <= 3):
                    error_msg = "Total crash <= 3"
                    per_of_segment += 1
                elif (int(avg_check) > 3 and
                        int(segment_row[-1]) in xrange(3, int(avg_check) + 1) and 
                            segment_row[-1] <= int(avg_check)):
                    error_msg = "Average crash <= {0}".format(min_avg_crashes)
                    crash_per_seg += 1
                else:
                    continue
                error_row = (segment_row[0], segment_row[1], segment_row[3], segment_row[2], error_msg)
                with arcpy.da.InsertCursor(SEGMENT_ERROR_TABLE_NAME,
                                           segment_insert_fields)\
                                           as insert_cursor:
                        insert_cursor.insertRow(error_row)

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

    except Exception:
        arcpy.AddError("Error occurred while generating Segment Error table.")
        return False

def get_crash_errors(crash_year_field, crash_route_field,
                     segment_route_name_field):
    """
    This function checks the crashes for errors and add them to the crash error
    log table
    """
    try:
        unassigned_crashes = 0
        blank_year = 0
        blank_route = 0
        unmatched_routes = 0
        with arcpy.da.SearchCursor(CRASH_OUTPUT_NAME, ["OID@", crash_year_field,
                                                     crash_route_field,
                                                     SEGMENTID_FIELD_NAME])\
                                                     as crash_search_cursor:

            for crash_row in crash_search_cursor:
                #   Check for crash outside the proximity distance
                #   (USRAP_SEGID will not be assigned to it)
                if crash_row[-1] in ["", None]:
                    unassigned_crashes += 1
                    error_msg = ("Crash outside the user specified proximity" +
                                 " distance from segment.")

                    error_row = [crash_row[0], crash_row[1], crash_row[2],
                                 "-", "-", error_msg]
                    if crash_row[2] == None:
                        error_row[2] = ""
                    insert_crash_error(error_row)
                else:
                    where = "{0} = {1}".format(SEGMENTID_FIELD_NAME,
                                               crash_row[-1])
                    with arcpy.da.SearchCursor(SEGMENT_OUTPUT_NAME,
                                               [segment_route_name_field, SEGMENTID_FIELD_NAME],
                                               where) as seg_search_cursor:
                        seg_route_name = ""
                        for row in seg_search_cursor:
                            seg_route_name = row[0]
                    #   Check for the crash for which year not maintained
                    if crash_row[1] in ["", None]:
                        unassigned_crashes += 1
                        blank_year += 1
                        error_msg = "Crash year is not specified."
                        error_row = [crash_row[0], crash_row[1], crash_row[2],
                                     crash_row[3], seg_route_name, error_msg]
                        insert_crash_error(error_row)

                    if crash_row[2] in ["", None]:
                        #   Check for the crash for which Route Name not
                        #   maintained
                        blank_route += 1
                        error_msg = "Crash Route Name is not specified."
                        error_row = [int(crash_row[0]), int(crash_row[1]), str(crash_row[2]),
                                     str(crash_row[3]), str(seg_route_name), error_msg]
                        insert_crash_error(error_row)
                    else:
                        #   Check the Route name of crash with the route of
                        #   segment to which it is assigned. Log the crash if it
                        #   doesn't matched in error table
                        if seg_route_name != "":
                            if seg_route_name == crash_row[2]:
                                continue
                        else:
                            unmatched_routes += 1
                            error_msg = ("Crash Route Name does" +
                                            " not match with" +
                                            " Segment Route Name.")
                            error_row = [str(crash_row[0]), crash_row[1],
                                            crash_row[2], crash_row[3],
                                            seg_route_name, error_msg]
                            insert_crash_error(error_row)

        #   Calculate the percentage of each type of crash error and make an
        #   entry into Error Summary table
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

    except Exception:
        arcpy.AddError("Error occurred while generating crash error table.")
        return False

def insert_crash_error(error_row):
    """
    This function insert the crashes with erros in Crash Error log
    table
    """
    try:
        crash_insert_fields = [field[0] for field in CRASH_ERROR_TABLE_FIELDS]
        with arcpy.da.InsertCursor(CRASH_ERROR_TABLE_NAME,
                                   crash_insert_fields) as insert_cursor:
            insert_cursor.insertRow(error_row)
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

    except Exception:
        arcpy.AddError("Error occurred while generating error tables.")

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

def main():
    """
    Main Function
    """
    #   Get all the parameters
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

#------------------- Assigning Segmemnt IDs to Crashes ------------------------#
#------------------- and crash count to Segments ------------------------------#

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

#------------------- Merging Segments -----------------------------------------#
    steps = usrap_count / SEGMENT_INCREMENT
    if usrap_count % SEGMENT_INCREMENT != 0:
        steps += 1
    steps = (steps * 2) + 2
    arcpy.ResetProgressor()
    arcpy.SetProgressor("step", "Merging segments..", 0, steps,
                        SEGMENT_INCREMENT)
    try:
        temp_seg = output_folder + os.sep + OUTPUT_GDB_NAME + os.sep + SEGMENT_OUTPUT_NAME
        arcpy.CopyFeatures_management(IN_MEMORY + os.sep + SEGMENT_OUTPUT_NAME, temp_seg)
        arcpy.RepairGeometry_management(temp_seg)
        sorted_segments = arcpy.Sort_management(temp_seg, os.path.join(IN_MEMORY, "sorted_segments"),
                                                [["SHAPE_Length", "ASCENDING"]])
        sorted_features_layer = arcpy.MakeFeatureLayer_management(
            sorted_segments, "sorted_features_layer")
        #   Delete the previous Segment Feature Class as it is no longer needed
        arcpy.Delete_management(temp_seg)

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
        check_criteria(sorted_features_layer, [min_avg_crashes, per_of_segments],
                       ["min average", "per segments"],
                       check_fields, segment_route_name_field, crash_fields)

        arcpy.SetProgressorPosition(steps - 1)
        add_message("Merging of segments completed.")

        #   Clear the selection from the layer and copy it as new feature class
        #   in output Geodatabase
        arcpy.SelectLayerByAttribute_management(sorted_features_layer,
                                                "CLEAR_SELECTION")

        full_out_path = output_folder + os.sep + OUTPUT_GDB_NAME + os.sep + SEGMENT_OUTPUT_NAME

        arcpy.SetProgressorPosition(steps)
        add_message("-" * 80)

    except arcpy.ExecuteError:
        arcpy.AddError("Error occured while Merging segments..")

    except Exception:
        arcpy.AddError("Error occured while Merging segments..")
    pass

#------------------- Assign Segment IDs to Crashes from mergerd segments ------#

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

    arcpy.CopyFeatures_management(CRASH_OUTPUT_NAME, out_gdb + os.sep + CRASH_OUTPUT_NAME)
    arcpy.CopyFeatures_management(sorted_features_layer, full_out_path)

    arcpy.CopyRows_management(CRASH_ERROR_TABLE_NAME, out_gdb + os.sep + CRASH_ERROR_TABLE_NAME)
    arcpy.CopyRows_management(SEGMENT_ERROR_TABLE_NAME, out_gdb + os.sep + SEGMENT_ERROR_TABLE_NAME)
    arcpy.CopyRows_management(ERROR_SUMMARY_TABLE_NAME, out_gdb + os.sep + ERROR_SUMMARY_TABLE_NAME)

    arcpy.Delete_management(IN_MEMORY)

    arcpy.ResetProgressor()

if __name__ == '__main__':
    main()