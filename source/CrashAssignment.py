import arcpy
import os
import sys

# pylint: disable = E1103, E1101, R0914, W0703, R0911, R0912, R0915, C0302

arcpy.env.overwriteOutput = True

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

#   Set increment value for progressor while merging segments
SEGMENT_INCREMENT = 10

#   Crash error table fields
CRASH_ERROR_TABLE_FIELDS = [["CrashOID", "SHORT"], ["CrashYear", "SHORT"],
                            ["CrashRouteName", "TEXT"], ["USRAP_SEGID", "TEXT"],
                            ["SegmentRouteName", "TEXT"],
                            ["ErrorMessage", "TEXT"]]

#   Segment error table fields
SEGMENT_ERROR_TABLE_FIELDS = [["SegmentOID", "SHORT"], ["USRAP_SEGID", "TEXT"],
                              ["AVG_CRASH", "TEXT"], ["ErrorMessage", "TEXT"]]

#   Error Summary Table fields
SUMMARY_ERROR_TABLE_FIELDS = [["ErrorType", "TEXT", 500], ["Count", "TEXT", 50],
                              ["Percentage", "TEXT", 50]]

#   Specify name for the error log tables
CRASH_ERROR_TABLE_NAME = "CrashErrorTable"
SEGMENT_ERROR_TABLE_NAME = "SegmentErrorTable"
ERROR_SUMMARY_TABLE_NAME = "SummaryErrorTable"

#===================== Assignment =============================================#
def check_unique_segmentids(input_segment_fc):
    """
    This function checks for Unique segment IDs for USRAP segments.
    If any NULL value found, it stops the further processing.
    """
    try:
        arcpy.SetProgressor("step", "Checking reqiured values..", 0, 6, 1)
        arcpy.AddMessage("\nChecking for unique segment ids..")
        segmentids = []
        where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
        with arcpy.da.SearchCursor(input_segment_fc, [SEGMENTID_FIELD_NAME,
                                                      USRAP_SEGMENT_FIELD_NAME],
                                   where) as seg_cursor:
            for seg_row in seg_cursor:
                if seg_row[0] in ["", None, " "]:
                    err_msg = ("One of the {0} found to be NULL. Can not" +
                               " proceed further.").format(SEGMENTID_FIELD_NAME)
                    arcpy.AddError(err_msg)
                    return False
                segmentids.append(int(seg_row[0]))

        #   Set of segmentids will give unique ids
        unique_segment_ids = set(segmentids)
        if len(unique_segment_ids) != len(segmentids):
            arcpy.AddError(("{0}s are not unique.Can not proceed" +
                            " further").format(SEGMENTID_FIELD_NAME))
            return False
        return True

    except arcpy.ExecuteError:
        arcpy.AddError("Error occurred while checking for unique USRAP_SEGIDs.")
        return False

    except Exception:
        arcpy.AddError("Error occurred while checking for unique USRAP_SEGIDs.")
        return False

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
    This function seperate out the USRAP Segments.
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
        return segment_layer, count

    except arcpy.ExecuteError:
        arcpy.AddError("Error occurred while getting USRAP_SEGMENT.")
        return []

    except Exception:
        arcpy.AddError("Error occurred while getting USRAP_SEGMENT.")
        return []

def assign_segid_to_crashes(max_dist, usrap_segment_layer, input_crash_fc):
    """
    This function first create the Field mapping and then performs the
    spatial join for Crash Feature Class
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
        arcpy.CopyFeatures_management(input_segment_fc, SEGMENT_OUTPUT_NAME)

        arcpy.AddMessage("Adding crash year fields in input segment" +
                         " feature class...")

        #   Add fields for each crash year in the segment feature class
        for year in crash_years:
            arcpy.AddField_management(SEGMENT_OUTPUT_NAME,
                                      "{0}{1}".format(CRASH_YEAR_FIELD,
                                                      str(year)), "SHORT")

            arcpy.CalculateField_management(SEGMENT_OUTPUT_NAME,
                                            "{0}{1}".format(CRASH_YEAR_FIELD,
                                                            str(year)), 0, "PYTHON_9.3")

        #   Add fields for Total and Average crashes in the
        #   segment feature class
        arcpy.AddField_management(SEGMENT_OUTPUT_NAME, TOTAL_CRASH_FIELD_NAME,
                                  "LONG")

        arcpy.AddField_management(SEGMENT_OUTPUT_NAME, AVG_CRASHES_FIELD_NAME,
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
        with arcpy.da.SearchCursor(CRASH_OUTPUT_NAME,
                                   [SEGMENTID_FIELD_NAME, crash_year_field])\
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

                    with arcpy.da.UpdateCursor(SEGMENT_OUTPUT_NAME,
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

    except arcpy.ExecuteError:
        arcpy.AddError("Error occurred while adding count of crashes to the" +
                       " segments")
        return False

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
        with arcpy.da.UpdateCursor(SEGMENT_OUTPUT_NAME,
                                   update_fields) as update_cursor:
            for row in update_cursor:
                total_count = 0
                num_div_years = 0
                for i in xrange(len(crash_years)):
                    if row[i] != 0:
                        total_count += row[i]
                        num_div_years += 1
                if num_div_years == 0:
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
    This function first checks for all required values are valid or not. Then it
    assigns the segment ids to crashes ans also crash count to segments.
    """
    #   Check for duplicate segment Ids
    unique_segmentids = check_unique_segmentids(input_segment_fc)
    if not unique_segmentids:
        return []
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
        arcpy.SetProgressorPosition()

        #   Get AADT years
        arcpy.AddMessage("Getting AADT years..")
        field_type = "{0}*".format(AADT_FIELD_NAME)
        segment_fields = arcpy.ListFields(input_segment_fc, field_type)
        aadt_years = [int(str(field.name).split("_")[AADT_YEAR_INDEX])
                      for field in segment_fields]
        arcpy.SetProgressorPosition()

    except arcpy.ExecuteError:
        arcpy.AddError("Error occured while getting AADT or Crash Years.")
        return []

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
    #   Perform Sptial Join with Crash Feature class
    crash_output_fc = assign_segid_to_crashes(max_dist, usrap_segment_layer,
                                              input_crash_fc)
    if not crash_output_fc:
        return []
    arcpy.SetProgressorPosition()

    #   Assign crash count per year to each segment
    segment_output_fc = assign_crashes_to_segments(
        input_segment_fc, crash_years, crash_year_field)
    if not segment_output_fc:
        return []
    else:
        return crash_years, aadt_years, usrap_count

#===================== Merging Segments =======================================#

def check_criteria(sorted_features_layer, condition, criteria, check_fields):
    """
    This function is used for performing merging of the segments.
    It first merge the segments by relaxing speed limit and then relaxing AADT.
    """
    try:
        check_condition_with_aadt = build_check_condition(
            sorted_features_layer, condition, criteria, "")
        #   Merging by relaxing Speed Limit. Include AVG_AADT value check
        if check_condition_with_aadt and condition != "end_result":
            arcpy.AddMessage("Merging by relaxing Speed Limit..")
            arcpy.SetProgressorLabel("Merging by relaxing Speed Limit..")
            step_count = 1
            next_step_count = apply_merging(sorted_features_layer, check_fields,
                                            "with_aadt", step_count, condition)

            check_condition_without_aadt = build_check_condition(
                sorted_features_layer, condition, criteria, "relax_aadt")

            #   Merging with relaxing AADT. Exclude AVG_AADT value check
            if check_condition_without_aadt:
                arcpy.AddMessage("Merging by relaxing AADT..")
                arcpy.SetProgressorLabel("Merging by relaxing AADT..")
                _ = apply_merging(sorted_features_layer, check_fields,
                                  "without_aadt", next_step_count, condition)

                _ = build_check_condition(sorted_features_layer, condition,
                                          criteria, "end_result")
            else:
                arcpy.AddMessage("It is satisfying the criteria." +
                             " Merging will not be performed further.")

    except Exception:
        arcpy.AddError("Error occurred while checking conditions..")
        sys.exit()

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
        else:
            crash_where = "{0} <= 3".format(AVG_CRASHES_FIELD_NAME)

        result_features = arcpy.SelectLayerByAttribute_management(
            sorted_features_layer, "SUBSET_SELECTION", crash_where)
        selected_count = int(arcpy.GetCount_management(result_features)[0])

        #   Check the condition and display the appropriate message
        if criteria.upper() == "min average".upper():
            if param.upper() == "relax_aadt".upper():
                msg = (("Number of segments having crashes <= {0} after" +
                        " relaxing speed limit : {1} out of {2} USRAP segments")
                       .format(condition, selected_count, usrap_count))
            elif param.upper() == "end_result".upper():
                msg = (("Number of segments having crashes <= {0} after" +
                        " relaxing AADT : {1} out of {2} USRAP segments")
                       .format(condition, selected_count, usrap_count))
            else:
                msg = (("Number of segments having crashes <= {0} : " +
                        " {1} out of {2} USRAP segments")
                       .format(condition, selected_count, usrap_count))
            arcpy.AddMessage(msg)
            if_condition = int(selected_count) > 0

        else:
            # Calculating percentage with respect to USRAP segment count
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
            if not if_condition:
                arcpy.AddMessage("Speed Limit and AADT have been relaxed.\n" +
                                 "The {0}% max for segments with < 3 crashes was not met.\n".format(condition) +   
                                "Merging will not be performed further.\n" +
                                "Please review the output Error tables.")
            else:
                arcpy.AddMessage("{0}% max for segments with < 3 crashes was  met.\n".format(condition) +
                             " Merging will not be performed further.")
        return if_condition

    except Exception:
        arcpy.AddError("Error occurred while checking conditions..")
        sys.exit()

def apply_merging(sorted_features_layer, check_fields, aadt_check, step_count,
                  condition):
    """
    This function apply merging process on reqiured segments
    """
    try:
        area_type_index = check_fields.index(AREA_TYPE_FIELD)
        county_index = check_fields.index(COUNTY_FIELD_NAME)
        row_count = 0
        count = 0
        with arcpy.da.UpdateCursor(sorted_features_layer,
                                   check_fields) as update_cursor:
            for uc_row in update_cursor:
                row_count += 1
                count += 1
                if SEGMENT_INCREMENT - count == 0:
                    count = 0
                    step_count += 1
                    arcpy.SetProgressorLabel(("Finished checking {0} " +
                                              "segments").format(row_count))
                    arcpy.SetProgressorPosition(step_count)
                #   Check if neccessary fields have blank values
                if (not set(uc_row[county_index:(area_type_index + 1)])
                        .isdisjoint(set(["", None, " "]))):
                    continue

                merge_segments(uc_row, update_cursor, sorted_features_layer,
                               check_fields, aadt_check, condition)
        arcpy.SetProgressorPosition(step_count)
        return step_count

    except Exception:
        arcpy.AddError("Error while applying merging")
        sys.exit()

def merge_segments(*args):
    """
    This function merge the segments meeting all neccessary condtions
    """
    try:
        uc_row, update_cursor = args[0], args[1]
        sorted_features_layer, check_fields = args[2], args[3]
        aadt_condition, condition = args[4], args[5]
        merge_oid = []
        avg_crash_index = check_fields.index(AVG_CRASHES_FIELD_NAME)
        area_index = check_fields.index(AREA_TYPE_FIELD)
        county_index = check_fields.index(COUNTY_FIELD_NAME)

        #   Find out the adjcent USRAP segments
        adjcent_segments = arcpy.SelectLayerByLocation_management(
            sorted_features_layer, "BOUNDARY_TOUCHES", uc_row[-1], "",
            "NEW_SELECTION")

        usrap_where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
        valid_adjcent_segments = arcpy.SelectLayerByAttribute_management(
            adjcent_segments, "SUBSET_SELECTION", usrap_where)

        #   For each adjcent USRAP segment check whether it satisfies all the
        #   neccessary conditions
        with arcpy.da.SearchCursor(valid_adjcent_segments,
                                   check_fields) as search_cursor:
            avg_length_list = []
            is_row_updated = False

            for search_row in search_cursor:
                s_avg = search_row[avg_crash_index]

                if not is_row_updated:
                    mis_match_found = False

                    #   Check for all neccessary fields
                    for field in check_fields[county_index:area_index]:
                        uc_val = uc_row[check_fields.index(field)]
                        search_val = search_row[check_fields.index(field)]
                        if (search_val in ["", " ", None, 0] or
                                uc_val != search_val):
                            mis_match_found = True
                            break

                    #   Check for AVG_AADT value (if neccessary)
                    uc_aadt = uc_row[check_fields.index(AVG_AADT_FIELD_NAME)]
                    s_aadt = search_row[check_fields.index(AVG_AADT_FIELD_NAME)]
                    if (aadt_condition == "with_aadt" and
                            uc_aadt not in [s_aadt, "", " ", None, 0] and
                            not mis_match_found):
                        mis_match_found = True

                    #   If all field values of any adjcent USRAP segment are
                    #   satisfying take its AVG_CRASH and Shape Length
                    if not mis_match_found:
                        avg_length_list.append([s_avg, search_row[-1].length])
                    else:
                        avg_length_list.append([None, 0])

                    #   When check is done for all adjcent USRAP segment reset
                    #   the cursor and take find the segment with maximum
                    #   AVG_CRASH and Shape Length
                    #   (with which the required segment will be merged)
                    if (len(avg_length_list) == (int(arcpy.GetCount_management(
                            valid_adjcent_segments)[0]))):
                        search_cursor.reset()
                        max_avg_crash = max(avg_length_list)
                        is_row_updated = True
                else:
                    #   Once the cursor is reset, find the row matching with
                    #   maximum AVG_CRASH and ShapeLength
                    if [s_avg, search_row[-1].length] == max_avg_crash:
                        if s_avg == None:
                            break
                        #   Calculate the crash count and AADT values
                        update_row_values = calculate_row_values(
                            uc_row, search_row, check_fields)
                        if not update_row_values:
                            break
                        else:
                            update_cursor.updateRow(update_row_values)
                            #   After updating the required row delete the
                            #   segment with which it is merged
                            merge_oid.append(search_row[0])
                            del_feat = arcpy.SelectLayerByAttribute_management(
                                sorted_features_layer, "NEW_SELECTION",
                                "OBJECTID = {0}".format(search_row[0]))
                            arcpy.DeleteRows_management(del_feat)

                            #   If USRAP_SEGID to be deleted is assigned to any
                            #   crash, update it with the USRAP_SEGID of the
                            #   segment which is getting merged
                            s_segid = search_row[check_fields.index(
                                SEGMENTID_FIELD_NAME)]
                            uc_segid = uc_row[check_fields.index(
                                SEGMENTID_FIELD_NAME)]
                            update_crash_segid(s_segid, uc_segid)
                            break

        #   Clear the selection from segments for next itration.
        #   Send the updated segment back to the merging process to check if it
        #   can be merged further
        arcpy.SelectLayerByAttribute_management(sorted_features_layer,
                                                "CLEAR_SELECTION")
        if (len(merge_oid) > 0 and
                update_row_values[avg_crash_index] <= condition):
            return merge_segments(update_row_values, update_cursor,
                                  sorted_features_layer, check_fields,
                                  aadt_condition, condition)

    except arcpy.ExecuteError:
        arcpy.AddWarning("Error occurred while merging segments with" +
                         " OBJECTID {0}.".format(uc_row[0]))
        add_calculate_error(uc_row, check_fields)

    except Exception:
        add_calculate_error(uc_row, check_fields)
        arcpy.AddWarning("Error occurred while merging segments with" +
                         " OBJECTID {0}.".format(uc_row[0]))

def calculate_row_values(uc_row, search_row, check_fields):
    """
    This function calculates the required values to be updated for the Merged
    segment.
    """
    try:
        #   Merge the geometries of 2 segments
        uc_row[-1] = uc_row[-1].union(search_row[-1])

        #   Calculate crash values for each year along with total and avg
        c_values = get_total_count(
            search_row, uc_row, check_fields.index(AREA_TYPE_FIELD) + 1,
            check_fields.index(TOTAL_CRASH_FIELD_NAME), check_fields)
        if not c_values:
            return []

        uc_row, total_crash, crash_years = c_values[0], c_values[1], c_values[2]

        uc_row[check_fields.index(TOTAL_CRASH_FIELD_NAME)] = total_crash

        avg_crashes = float(total_crash) / float(crash_years)
        uc_row[check_fields.index(AVG_CRASHES_FIELD_NAME)] = avg_crashes

        #   Calculate AADT values for each year along with avg
        a_values = get_total_count(
            search_row, uc_row, check_fields.index(AVG_CRASHES_FIELD_NAME) + 1,
            check_fields.index(AVG_AADT_FIELD_NAME), check_fields)
        if not a_values:
            return []

        uc_row, total_aadt, aadt_years = a_values[0], a_values[1], a_values[2]

        if(float(total_aadt) >0 and float(aadt_years) > 0):
            avg_aadt = float(total_aadt) / float(aadt_years)
        else:
            avg_aadt = 0
        uc_row[check_fields.index(AVG_AADT_FIELD_NAME)] = avg_aadt

        return uc_row

    except Exception:
        add_calculate_error(uc_row, check_fields)
        arcpy.AddWarning("Error occurred while calculating update row " +
                         "values for OBJECTID {0}.".format(uc_row[0]))
        return []

def get_total_count(search_row, update_row, start_index, end_index,
                    check_fields):
    """
    This function calculates the crash and AADT values for each year.
    Dividnig the total number for number of years for which data is provided.
    """
    try:
        years = 0
        total = 0

        #   If one value is blank, update it with the other.
        #   If both are blank, keep it None
        #   If both have values, update it with their sum
        for i in xrange(start_index, end_index):
            if update_row[i]  in ("", None, 0) and\
                    search_row[i] in ("", None, 0):
                update_row[i] = 0

            elif search_row[i] in ("", None, 0) and\
                     update_row[i] not in ("", None, 0):
                total += update_row[i]
                years += 1

            elif update_row[i] in ("", None, 0) and\
                     search_row[i] not in ("", None, 0):
                update_row[i] = search_row[i]
                total += update_row[i]
                years += 1

            elif update_row[i] not in ("", None, 0) and\
                     search_row[i] not in ("", None, 0):
                update_row[i] = search_row[i] + update_row[i]
                total += update_row[i]
                years += 1

        return update_row, total, years

    except Exception:
        arcpy.AddWarning("Error occurred while calculating update row " +
                         "values for OBJECTID {0}.".format(update_row[0]))
        add_calculate_error(update_row, check_fields)
        return []


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


def update_crash_segid(search_segid, uc_segid):
    """
    If USRAP_SEGID to be deleted is assigned to any crash, this function updates
    it with the USRAP_SEGID of the segment which is getting merged
    """
    try:
        where = "{0} = {1}".format(SEGMENTID_FIELD_NAME, search_segid)
        with arcpy.da.UpdateCursor(CRASH_OUTPUT_NAME, [SEGMENTID_FIELD_NAME],
                                   where) as crash_uc:
            for row in crash_uc:
                row[0] = uc_segid
                crash_uc.updateRow(row)

    except Exception:
        arcpy.AddWarning(("Error occurred while updating USRAP_SEGID for {0}")
                         .format(search_segid))
        return False

#===================== Creating Error Logs ====================================#

def create_error_tables():
    """
    This function creates the Error Tables needed to log the errors
    """
    try:
        #   Crash error table
        arcpy.CreateTable_management(arcpy.env.workspace,
                                     CRASH_ERROR_TABLE_NAME)

        for field in CRASH_ERROR_TABLE_FIELDS:
            arcpy.AddField_management(CRASH_ERROR_TABLE_NAME, field[0],
                                      field[1], field_alias=field[0])

        #   Segment error table
        arcpy.CreateTable_management(arcpy.env.workspace,
                                     SEGMENT_ERROR_TABLE_NAME)

        for field in SEGMENT_ERROR_TABLE_FIELDS:
            arcpy.AddField_management(SEGMENT_ERROR_TABLE_NAME, field[0],
                                      field[1], field_alias=field[0])

        #   Summary error table
        arcpy.CreateTable_management(arcpy.env.workspace,
                                     ERROR_SUMMARY_TABLE_NAME)

        for field in SUMMARY_ERROR_TABLE_FIELDS:
            arcpy.AddField_management(ERROR_SUMMARY_TABLE_NAME, field[0],
                                      field[1], field_length=field[2],
                                      field_alias=field[0])
        return True

    except Exception:
        return False

def get_segment_error(min_avg_crashes):
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
                                   ["OID@", SEGMENTID_FIELD_NAME,
                                    AVG_CRASHES_FIELD_NAME],
                                   where) as segment_cursor:
            for segment_row in segment_cursor:
                if (int(segment_row[-1]) in xrange(0, 4) and
                        segment_row[-1] <= 3):
                    error_msg = "Average crash <= 3"
                    per_of_segment += 1

                elif (int(avg_check) > 3 and
                        int(segment_row[-1]) in xrange(3, int(avg_check) + 1) and 
                            segment_row[-1] <= int(avg_check)):
                    error_msg = "Average crash <= {0}".format(min_avg_crashes)
                    crash_per_seg += 1

                else:
                    continue

                error_row = (segment_row[0], segment_row[1], segment_row[2],
                             error_msg)

                with arcpy.da.InsertCursor(SEGMENT_ERROR_TABLE_NAME,
                                           segment_insert_fields)\
                                           as insert_cursor:
                        insert_cursor.insertRow(error_row)

        #   First get USRAP Segment count
        usrap_where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELD_NAME)
        usrap_segments = arcpy.MakeFeatureLayer_management(
            SEGMENT_OUTPUT_NAME, "usrap_layer", usrap_where)
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
                    error_row = (crash_row[0], crash_row[1], crash_row[2],
                                 "-", "-", error_msg)
                    insert_crash_error(error_row)

                else:
                    where = "{0} = {1}".format(SEGMENTID_FIELD_NAME,
                                               crash_row[-1])
                    with arcpy.da.SearchCursor(SEGMENT_OUTPUT_NAME,
                                               [segment_route_name_field],
                                               where) as seg_search_cursor:
                        for row in seg_search_cursor:
                            seg_route_name = row[0]
                    #   Check for the crash for which year not maintained
                    if crash_row[1] in ["", None]:
                        blank_year += 1
                        error_msg = "Crash year is not specified."
                        error_row = (crash_row[0], crash_row[1], crash_row[2],
                                     crash_row[3], seg_route_name, error_msg)
                        insert_crash_error(error_row)

                    if crash_row[2] in ["", None]:
                        #   Check for the crash for which Route Name not
                        #   maintained
                        blank_route += 1
                        error_msg = "Crash Route Name is not specified."
                        error_row = (crash_row[0], crash_row[1], crash_row[2],
                                     crash_row[3], seg_route_name, error_msg)
                        insert_crash_error(error_row)
                    else:
                        #   Check the Route name of crash with the route of
                        #   segment to which it is assigned. Log the crash if it
                        #   doesn't matched in error table
                        if seg_route_name == crash_row[2]:
                            continue
                        else:
                            unmatched_routes += 1
                            error_msg = ("Crash Route Name does" +
                                         " not match with" +
                                         " Segment Route Name.")
                            error_row = (crash_row[0], crash_row[1],
                                         crash_row[2], crash_row[3],
                                         seg_route_name, error_msg)
                            insert_crash_error(error_row)

        #   Calculate the percentage of each type of crash error and make an
        #   entry into Error Summary table
        crash_count = int(arcpy.GetCount_management(CRASH_OUTPUT_NAME)[0])
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

    finally:
        arcpy.Delete_management("in_memory")

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

    except Exception:
        arcpy.AddError("Error occurred while inserting crash error.")

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

def main():
    """
    Main Function
    """
    #   Get all the parameter
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

    #   Create Errors Log tables
    table_created = create_error_tables()

#------------------- Merging Segments -----------------------------------------#

    arcpy.AddMessage("Merging segments. This may take a while...")
    steps = usrap_count / SEGMENT_INCREMENT
    if usrap_count % SEGMENT_INCREMENT != 0:
        steps += 1
    steps = (steps * 2) + 2
    arcpy.ResetProgressor()
    arcpy.SetProgressor("step", "Merging segments..", 0, steps,
                        SEGMENT_INCREMENT)
    try:
        sorted_segments = arcpy.Sort_management(
            SEGMENT_OUTPUT_NAME, os.path.join("in_memory", "sorted_segments"),
            [["SHAPE_Length", "ASCENDING"]])
        sorted_features_layer = arcpy.MakeFeatureLayer_management(
            sorted_segments, "sorted_features_layer")
        #   Delete the previous Segment Feature Class as it is no longer needed
        arcpy.Delete_management(SEGMENT_OUTPUT_NAME)

        #   Sequence of fields in check_fields is very important.
        #   If more fields need to be checked, add it after "COUNTY_FIELD_NAME"
        #   and before "AREA_TYPE_FIELD".
        #   This will help maintain the sequence of field checking
        check_fields = ["OID@", SEGMENTID_FIELD_NAME, COUNTY_FIELD_NAME,
                        segment_route_name_field, segment_route_type_field,
                        LANES_FIELD_NAME, MEDIANS_FIELD_NAME, AREA_TYPE_FIELD]

        for year in crash_years:
            check_fields += ["{0}{1}".format(CRASH_YEAR_FIELD, year)]

        check_fields += [TOTAL_CRASH_FIELD_NAME, AVG_CRASHES_FIELD_NAME]

        for year in aadt_years:
            check_fields += ["{0}{1}".format(AADT_FIELD_NAME, year)]

        check_fields += [AVG_AADT_FIELD_NAME, "SHAPE@"]

        arcpy.SetProgressorPosition(1)

        #   Check for number of crashes per segment < min_avg_per_segment
        msg = ("Checking for minimum number of crashes per segment criteria.")
        arcpy.AddMessage(msg)
        arcpy.SetProgressorLabel(msg)

        check_criteria(sorted_features_layer, min_avg_crashes, "min average",
                       check_fields)
        arcpy.AddMessage("-" * 80)
        #   Check for number of crashes per segment < per_of_segments
        msg = ("Checking for percentage of segments with AVG_CRASH <= 3 " +
               "criteria...")
        arcpy.AddMessage(msg)
        arcpy.SetProgressorLabel(msg)

        check_criteria(sorted_features_layer, per_of_segments, "per segments",
                       check_fields)
        arcpy.SetProgressorPosition(steps - 1)
        arcpy.AddMessage("Merging of segments completed.")
        arcpy.SetProgressorLabel("Merging of segments Completed")

        #   Clear the selection from the layer and copy it as new feature class
        #   in output Geodatabase
        arcpy.SelectLayerByAttribute_management(sorted_features_layer,
                                                "CLEAR_SELECTION")
        arcpy.CopyFeatures_management(sorted_features_layer,
                                      SEGMENT_OUTPUT_NAME)
        arcpy.SetProgressorPosition(steps)
        arcpy.AddMessage("-" * 80)

    except arcpy.ExecuteError:
        arcpy.AddError("Error occured while Merging segments..")

    except Exception:
        arcpy.AddError("Error occured while Merging segments..")

    finally:
        arcpy.Delete_management("in_memory")

#------------------- Assign Segment IDs to Crashes from mergerd segments ------#

    if not table_created:
        arcpy.AddError("Error occurred while creating error log tables.")
        return

    msg = "Checking errors.."

    arcpy.SetProgressor("step", msg, 0, 3, 1)
    arcpy.AddMessage(msg)

    #   Check for faults in segment feature class output
    segment_error_added = get_segment_error(min_avg_crashes)

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

    #   Check if Unassigned crashes and Assigned crashe are equal to Total
    #   crashes in input dataset
    check_total_crashes(unassigned_crashes)
    arcpy.ResetProgressor()

if __name__ == '__main__':
    main()

