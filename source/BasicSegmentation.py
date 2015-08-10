# pylint: disable = C0103, R0912, R0914, R0915, E1103, W0703, W0612, E1101
# required imports
import arcpy
import os

arcpy.env.overwriteOutput = True

IN_MEMORY = 'in_memory'
TEMP_GDB = "TEMP_INPUTS_BASIC_SEG.gdb"

# feild names
USRAP_COUNTY = 'USRAP_COUNTY'
USRAP_ACCESS_CONTROL = 'USRAP_ACCESS_CONTROL'
USRAP_MEDIAN = 'USRAP_MEDIAN'
USRAP_LANES = 'USRAP_LANES'
USRAP_AREA_TYPE = 'USRAP_AREA_TYPE'
USRAP_SPEED_LIMIT = 'USRAP_SPEED_LIMIT'
USRAP_SEGMENT = 'USRAP_SEGMENT'
USRAP_AADT_YYYY = 'USRAP_AADT'
USRAP_AVG_AADT = 'USRAP_AVG_AADT'
USRAP_SEGID = 'USRAP_SEGID'
USRAP_ROADWAYTYPE = 'USRAP_ROADWAY_TYPE'
USRAP_CLASS_ERROR = "USRAP_CLASSIFICATION_ERROR"

# conditions constants
EQUAL_TO = 'EQUAL_TO'
LESS_THAN_EQUAL_TO = 'LESS_THAN_EQUAL_TO'
LESS_THAN_EQUAL_TO_OR_MORE_THAN_EQUAL_TO = 'LESS_THAN_EQUAL_TO_OR_MORE_THAN_\
EQUAL_TO'
MORE_THAN_EQUAL_TO = 'MORE_THAN_EQUAL_TO'
EQUAL_TO_2_LANES = 'EQUAL_TO_2_LANES'
MORE_THAN_2_LANES = 'MORE_THAN_2_LANES'

# prepare output file geodatabase to store results
OUTPUT_GDB_NAME = "BasicSegmentationOutput.gdb"

# USRAP_SEGID_START_FROM must be number
USRAP_SEGID_START_FROM = 1000

# keep the progressor at position
DELETE_OIDS = []

# Name of the final output feature class
OUTPUT_SEGMENT_NAME = 'Segments'

# Access Control domain description
value_access_control_full = "Full Access Control"
value_access_control_partial = "Partial Access Control"
value_access_control_no = "No Access Control"
# Median domain description
value_median_divided = "Divided Roadway"
value_median_undivided = "Undivided Roadway"
# AreaType domain description
value_area_type_urban = "Urban"
value_area_type_rural = "Rural"

# Roadway type shortnames
rural_freeway = "Rural Freeway"
rural_multi_divided = "Rural Multilane Divided"
rural_multi_undivided = "Rural Multilane Undivided"
rural_two_undivided = "Rural two-lane Undivided"

urban_freeway = "Urban Freeway"
urban_multi_divided = "Urban Multilane divided"
urban_multi_undivided = "Urban Multilane Undivided"
urban_two_undivided = "Urban two-lane Undivided"

VERSION_USED = str(arcpy.GetInstallInfo()['Version'])

# list of road types on which baseline segments will be
# identified as usrap segment
# dictionary elements description:-
#   key - field name from baseline route segment
#   value - on which that field value will be tested
#   only USRAP_ACCESS_CONTROL can have list of values
roadway_type = [{USRAP_AREA_TYPE: value_area_type_rural,
                    USRAP_LANES: EQUAL_TO_2_LANES,
                    USRAP_MEDIAN: value_median_undivided,
                    USRAP_ACCESS_CONTROL: [value_access_control_no,
                                           value_access_control_partial],
                    USRAP_ROADWAYTYPE: rural_two_undivided},
                {USRAP_AREA_TYPE: value_area_type_rural,
                    USRAP_LANES: MORE_THAN_2_LANES,
                    USRAP_MEDIAN: value_median_undivided,
                    USRAP_ACCESS_CONTROL: [value_access_control_no,
                                        value_access_control_partial],
                    USRAP_ROADWAYTYPE: rural_multi_undivided},
                {USRAP_AREA_TYPE: value_area_type_rural,
                    USRAP_LANES: MORE_THAN_2_LANES,
                    USRAP_MEDIAN: value_median_divided,
                    USRAP_ACCESS_CONTROL: [value_access_control_no,
                                        value_access_control_partial],
                    USRAP_ROADWAYTYPE: rural_multi_divided},
                {USRAP_AREA_TYPE: value_area_type_rural,
                    USRAP_LANES: MORE_THAN_2_LANES,
                    USRAP_MEDIAN: value_median_divided,
                    USRAP_ACCESS_CONTROL: [value_access_control_full],
                    USRAP_ROADWAYTYPE: rural_freeway},
                {USRAP_AREA_TYPE: value_area_type_urban,
                    USRAP_LANES: EQUAL_TO_2_LANES,
                    USRAP_MEDIAN: value_median_undivided,
                    USRAP_ACCESS_CONTROL: [value_access_control_no,
                                        value_access_control_partial],
                    USRAP_ROADWAYTYPE: urban_two_undivided},
                {USRAP_AREA_TYPE: value_area_type_urban,
                    USRAP_LANES: MORE_THAN_2_LANES,
                    USRAP_MEDIAN: value_median_undivided,
                    USRAP_ACCESS_CONTROL: [value_access_control_no,
                                        value_access_control_partial],
                    USRAP_ROADWAYTYPE: urban_multi_undivided},
                {USRAP_AREA_TYPE: value_area_type_urban,
                    USRAP_LANES: MORE_THAN_2_LANES,
                    USRAP_MEDIAN: value_median_divided,
                    USRAP_ACCESS_CONTROL: [value_access_control_no,
                                        value_access_control_partial],
                    USRAP_ROADWAYTYPE: urban_multi_divided},
                {USRAP_AREA_TYPE: value_area_type_urban,
                    USRAP_LANES: MORE_THAN_2_LANES,
                    USRAP_MEDIAN: value_median_divided,
                    USRAP_ACCESS_CONTROL: [value_access_control_full],
                    USRAP_ROADWAYTYPE: urban_freeway}]

def check_name_length(feature_name):
    """ check the maximum name length for file geodatabase feature classes,
        if exceed, 160 characters would be returned """
    if len(feature_name) > 160:
        feature_name = feature_name[:160]
    return feature_name

def get_workspace(feature_class):
    """ returns the workspace location of feature class """
    if arcpy.Describe(os.path.dirname(feature_class)).dataType != 'Workspace':
        return get_workspace(os.path.dirname(feature_class))
    return os.path.dirname(feature_class)

def get_domain_values(workspace, domain_name):
    """ takes gdb and domain name as input and return domain value dictinary """
    return next((domain.codedValues for domain in arcpy.da.ListDomains(workspace)
            if domain.name == domain_name))

def get_field_values(feature_class, field_name):
    """ takes feature class and field object as input
        and return unique field values list """
    return sorted(set(row[0] for row in arcpy.da.SearchCursor(feature_class,
                                                              [field_name])))

def get_field_object(feature_class, field_name):
    """ takes feature class and field name as input and
        return field object for the given field name"""
    return next((field for field in arcpy.Describe(feature_class).fields
            if field.name == field_name))

def disable_m_value(feature_class):
    """ Disable M value of feature class """
    arcpy.env.outputMFlag = 'Disabled'
    fc_name = os.path.basename(str(feature_class)) + "_noM"
    return arcpy.FeatureClassToFeatureClass_conversion(feature_class, IN_MEMORY,
                                                       fc_name)

def create_where_clause(field, route_types, lookup=None):
    """ create where clause """
    where_clause = ''
    quotes = ''
    if field.type == "String":
        quotes = "'"
    if lookup:
        # reverse the dictinary key, value pair to find domain code
        # for selected values
        lookup = dict(zip(lookup.values(), lookup.keys()))
    for route_type in route_types:
        if len(where_clause) > 0:
            where_clause += ' OR '
        if lookup:
            where_clause += '{0} = {1}{2}{1}'.format(field.name,
                                                     quotes,
                                                     lookup[route_type])
        else:
            where_clause += '{0} = {1}{2}{1}'.format(field.name,
                                                     quotes,
                                                     route_type)
    return where_clause

def identity(target_ftrs, identity_ftrs, output_name=None, output_folder=None, cluster_tolerance="",
             problem_fields={}, full_out_path=""):
    """ perform identity analysis on target feature class with identity
        feature class """
    try:
        output_location = IN_MEMORY
        out_ftrs = os.path.basename(str(identity_ftrs))
        if output_folder:
            output_location = output_folder
            out_ftrs = arcpy.CreateUniqueName(out_ftrs, output_location)
        else:
            out_ftrs = os.path.join(output_location, out_ftrs)
        # add 'identity' in output feature class name if not present
        if out_ftrs.find('_identity') == -1:
            out_ftrs += '_identity'
        out_ftrs = check_name_length(out_ftrs)
        # identity operation to combine attributes
        cnt = int(arcpy.GetCount_management(identity_ftrs)[0])
        if cnt > 0:
            arcpy.Identity_analysis(target_ftrs, identity_ftrs, out_ftrs,
                                    "NO_FID", cluster_tolerance)
            feature_name = check_name_length("sp" + os.path.basename(str(out_ftrs)))
            if output_name:
                feature_name = output_name
            # convert multiparts to single part, if any
            return out_ftrs
        return target_ftrs
    except Exception as e:
        arcpy.AddError(str(e))

def year(s):
    return s.split("_")[2]

def median(y, x):
    sortedList = sorted(y)
    mid = int(len(y)/2)
    if len(y) % 2 == 0:
        mid -= 1
    return str(sortedList[int(mid)+x])

def calculate_average(feature_class, existing_fields, new_field):
    """ calculate the average of AADT fields for fields that have
        valid value """

    add_message("   Calculating average AADT for each segment")

    arcpy.AddField_management(feature_class, new_field, 'DOUBLE', field_alias=new_field)
    fields = list(existing_fields)
    #create dict with 0 based index for the years location in the fields collection
    years = [year(field) for field in fields]
    indexes = [n for n in range(len(years))]
    field_order = dict(zip(indexes, years))
    fields.append(new_field)
    with arcpy.da.UpdateCursor(feature_class, fields) as cursor:
        for row in cursor:
            try:
                #Add all AADT values
                dividend = sum([float(value) for value in row[:-1] if value != None and float(value) > 0])
                #count number of years of AADT data for the row
                divisor = sum([1 for value in row[:-1] if value != None and float(value) > 0])
                #If data is not avalible for all years use the middle year
                # if at least one year is avalible
                if divisor < len(row[:-1]) and divisor > 0:
                    testIndex = 0
                    forwardTest = True
                    i = 0
                    while i < len(row[:-1]):
                        mid = median(list(field_order.values()), testIndex)
                        value = row[list(field_order.keys())[list(field_order.values()).index(mid)]]

                        if value != None and value != 0:
                            row[-1] = value
                            break
                        if forwardTest:
                            testIndex = abs(testIndex) + 1
                        else:
                            testIndex = -testIndex
                        i += 1
                        forwardTest = not forwardTest
                elif divisor == 0:
                    row[-1] = None
                else:
                    #actual average of the value is only calculated when we have
                    # continous values across all years in the study
                    row[-1] = round((dividend / divisor), 1)
            except (ValueError, ZeroDivisionError):
                row[-1] = None
            cursor.updateRow(row)
    arcpy.SetProgressorPosition()
    return feature_class

def copy_fields(feature_class, fields_name_info, fc_source):
    """ create new fields and copy records to it """
    try:
        domain_lu = None
        field_type = None
        update_rows = True
        for existing_field, new_field in list(fields_name_info.items()):
            # get the field object of existing field in baseline feature class
            field = get_field_object(fc_source, existing_field)
            if field.domain:
                # get the database of selected feature class
                database = get_workspace(fc_source)
                # get domains from geo-database for selected feature class
                # and field
                domain_lu = get_domain_values(database, field.domain)
                # field_length=50 from AddField_management
                arcpy.AddField_management(feature_class, new_field, 'TEXT',
                                          field_alias=new_field)
            else:
                # field_length=field.length,
                arcpy.AddField_management(feature_class, new_field, field.type,
                                          field_alias=new_field)

            if not [field.name for field in arcpy.Describe(feature_class).fields].count(existing_field) > 0:
                update_rows = False

            if update_rows:
                with arcpy.da.UpdateCursor(feature_class, [existing_field,
                                                           new_field]) as cursor:
                    for row in cursor:
                        # row[1] is newly created field and row[0] is added after
                        # identity operation
                        row[1] = row[0]
                        if domain_lu:
                            try:
                                row[1] = str(domain_lu[row[0]])
                            except KeyError:
                                row[1] = None
                        cursor.updateRow(row)
        return feature_class
    except Exception as error:
        arcpy.AddError(str(error))

def combine_attributes(fc_target, fc_identity, fc_identity_field_name,
                       new_field_name, output_name=None, output_folder=None, cluster_tolerance="", problem_fields={}, full_out_path="", fc_source=""):
    """ combines the required fields from other feature classes with
        baseline feature class """
    try:
        #add_formatted_message("   Combining {0} into routes", fc_identity_field_name)

        if arcpy.Describe(fc_target).hasM:
            fc_target = disable_m_value(fc_target)

        # keep the feature class to find domain in copy_fields function
        if arcpy.Describe(fc_identity).hasM:
            fc_identity = disable_m_value(fc_identity)
        # keep required fields in list to find newly added fields after identity
        # operation
        fc_target_fields = [field.name.lower() for field in
                            arcpy.Describe(fc_target).fields]

        # identity analysis to combine attributes of identity feature class
        baseline_routes = identity(fc_target, fc_identity,
                                   output_name, output_folder,
                                   cluster_tolerance, problem_fields, full_out_path)

        fc_identity_fields = []
        for field in arcpy.Describe(fc_identity).fields:
            if field.name != fc_identity_field_name and \
                    not field.required and \
                    not field.name.lower().startswith('shape') and \
                    not field.name.lower().startswith('objectid'):
                fc_identity_fields.append(field.name.lower())

        # delete unncessary fields coming from identity feature class
        if len(fc_identity_fields) > 0:
            arcpy.DeleteField_management(baseline_routes, fc_identity_fields)

        # find the fields newly added in baseline feature class after identity
        # operation
        baseline_route_fields = [field.name for field in
                                 arcpy.Describe(baseline_routes).fields
                                 if field.name.lower() not in
                                 fc_target_fields and not field.required]

        # copy existing feild rows into a new field added in
        # baseline feature class
        # this could be invalid still if fc_target and fc_identity share a
        # common field name...fc_identity_field_name...prior to identity operation
        field_dict = {fc_identity_field_name: new_field_name}

        baseline_routes = copy_fields(baseline_routes, field_dict, fc_source)

        #NOT WITH IN_MEM data
        #arcpy.AddIndex_management(baseline_routes, new_field_name, new_field_name, "NON_UNIQUE", "NON_ASCENDING")

        # delete the previous field from which rows has beed copied to new field
        if len(baseline_route_fields) > 0:
            arcpy.DeleteField_management(baseline_routes, baseline_route_fields)

        if not arcpy.Exists(full_out_path):
            if isinstance(baseline_routes, str) or isinstance(baseline_routes, unicode):
                name = str(baseline_routes)
            else:
                name = baseline_routes[0]

            n_d = arcpy.Describe(name)
            arcpy.CreateFeatureclass_management(os.path.dirname(full_out_path),
                                                os.path.basename(full_out_path),
                                                n_d.shapeType,
                                                name,
                                                spatial_reference=n_d.spatialReference)

        #verify it has the necessary USRAP fields
        domain_lu = None
        field_type = None

        for existing_field, new_field in field_dict.items():
            if not len([field.name for field in arcpy.ListFields(full_out_path) if field.name == new_field]) == 1:
                # get the field object of existing field in baseline feature class
                name = ""
                if isinstance(baseline_routes, str) or type(baseline_routes, unicode):
                    name = str(baseline_routes)
                else:
                    name = baseline_routes[0]
                field = get_field_object(name, new_field)
                if field.domain:
                    # get the database of selected feature class
                    database = get_workspace(fc_source)
                    # get domains from geo-database for selected feature class
                    # and field
                    domain_lu = get_domain_values(database, field.domain)
                    # field_length=50 from AddField_management
                    arcpy.AddField_management(full_out_path, new_field, 'TEXT',
                                                field_alias=new_field)
                else:
                    # field_length=field.length,
                    arcpy.AddField_management(full_out_path, new_field, field.type,
                                            field_alias=new_field)
        arcpy.SetProgressorPosition()
        return baseline_routes
    except Exception as e:
        arcpy.SetProgressorPosition()
        arcpy.AddError(str(e))

def identify_usrap_segment(feature_class, roadway_types, output_folder, field_route_name):
    """ create new field 'USRAP_SEGMENT' and assign 'YES' or 'NO' value
        according to roadway type """

    add_message("   Identifying USRAP segments...")
    # field name for USRAP segments
    fields = list(set([k for d in roadway_types for k in d.keys()]))
    fields.append(USRAP_SEGMENT)
    fields.append(USRAP_AVG_AADT)
    fields.append(USRAP_SPEED_LIMIT)
    fields.append(USRAP_CLASS_ERROR)
    fields.append(USRAP_COUNTY)
    fields.append(field_route_name)
    fields.append("OID@")
    # create new field to identify USRAP Segments
    arcpy.AddField_management(feature_class, USRAP_SEGMENT, 'TEXT',
                              field_length=3, field_alias=USRAP_SEGMENT)

    # create new field to store USRAP roadway type
    arcpy.AddField_management(feature_class, USRAP_ROADWAYTYPE, 'TEXT',
                              field_length=100, field_alias=USRAP_ROADWAYTYPE)

    # create new field to store USRAP classification error
    arcpy.AddField_management(feature_class, USRAP_CLASS_ERROR, 'TEXT',
                              field_length=200, field_alias=USRAP_CLASS_ERROR)

    workspace = os.path.dirname(str(feature_class))

    # take a segment to from baseline route feature class
    with arcpy.da.UpdateCursor(feature_class, fields) as cursor:
        for row in cursor:
            errors = {}
            for roadway_type in roadway_types:
                truth_table = []
                if '' in row:
                    truth_table.append(False)
                    break

                # test a segment on roadway type to identify it as usrap segment
                for field in roadway_type.keys():
                    if field != USRAP_ROADWAYTYPE:
                        try:
                            # check for access control
                            if field == USRAP_ACCESS_CONTROL:
                                truth_table.append(row[fields.index(field)] in
                                                   roadway_type[field])
                            # check for lanes
                            elif field == USRAP_LANES:
                                try:
                                    if roadway_type[field] == EQUAL_TO_2_LANES:
                                        val = float(row[fields.index(field)]) == 2
                                        truth_table.append(val)
                                    elif roadway_type[field] == MORE_THAN_2_LANES:
                                        val = float(row[fields.index(field)]) > 2
                                        truth_table.append(val)
                                except ValueError:
                                    truth_table.append(False)
                            else:
                                index = fields.index(field)
                                val = row[index] == roadway_type[field]
                                truth_table.append(val)
                        except IndexError:
                            continue
                        if False in truth_table:
                            break
                #No need to do the previous loop if this stuff is missing...TODO move before the previous loop
                # verify we have a value for USRAP_AREA_TYPE
                if row[fields.index(USRAP_AREA_TYPE)] in ["", " ", None, "0"]:
                    errors[USRAP_AREA_TYPE] = False
                    truth_table.append(False)

                # verify we have a value for USRAP_LANES
                if row[fields.index(USRAP_LANES)] in ["", " ", None, "0", 0]:
                    errors[USRAP_LANES] = False
                    truth_table.append(False)

                # verify we have a value for USRAP_MEDIAN
                if row[fields.index(USRAP_MEDIAN)] in ["", " ", None, "0", 0]:
                    errors[USRAP_MEDIAN] = False
                    truth_table.append(False)

                # verify we have a value for USRAP_COUNTY
                if row[fields.index(USRAP_COUNTY)] in ["", " ", None, "0"]:
                    errors[USRAP_COUNTY] = False
                    truth_table.append(False)

                # verify we have a value for USRAP_ACCESS_CONTROL
                if row[fields.index(USRAP_ACCESS_CONTROL)] in ["", " ", None, "0"]:
                    errors[USRAP_ACCESS_CONTROL] = False
                    truth_table.append(False)

                # verify we have a value for USRAP_SPEED_LIMIT
                if row[fields.index(USRAP_SPEED_LIMIT)] in ["", " ", None, "0", 0]:
                    errors[USRAP_SPEED_LIMIT] = False
                    truth_table.append(False)

                #verify we have a value for USRAP_AVG_AADT
                if row[fields.index(USRAP_AVG_AADT)] in ["", " ", None, "0", 0]:
                    errors[USRAP_AVG_AADT] = False
                    truth_table.append(False)

                #verify we have a value for ROUTE_NAME
                if row[fields.index(field_route_name)] in ["", " ", None, "0", 0]:
                    errors[field_route_name] = False
                    truth_table.append(False)

                if False not in truth_table:
                    # mark segment as usrap segment 'YES' if it fulfill the
                    # roadway type condition
                    row[fields.index(USRAP_SEGMENT)] = 'YES'
                    # write the short name for the roadway type to the table
                    row[fields.index(USRAP_ROADWAYTYPE)] = str(roadway_type[USRAP_ROADWAYTYPE])
                    cursor.updateRow(row)
                    break
            if truth_table and False in truth_table:
                #verify that the row has all necessary attributes
                # log error message is values are missing
                allTrue = True
                has_speed = True
                has_aadt = True
                has_county = True
                has_access_control = True
                has_median = True
                has_lanes = True
                has_area_type = True
                has_name = True
                for field in errors.keys():
                    if str(errors[field]) != 'True':
                        allTrue = False
                        if str(field) == USRAP_AVG_AADT:
                            has_aadt = False
                        if str(field) == USRAP_COUNTY:
                            has_county = False
                        if str(field) == USRAP_ACCESS_CONTROL:
                            has_access_control = False
                        if str(field) == USRAP_MEDIAN:
                            has_median = False
                        if str(field) == USRAP_LANES:
                            has_lanes = False
                        if str(field) == USRAP_AREA_TYPE:
                            has_area_type = False
                        if str(field) == USRAP_SPEED_LIMIT:
                            has_speed = False
                        if str(field) == field_route_name:
                            has_name = False

                error_message = ""
                error_messages = []
                classification_error_message = "Roadway not valid for roadway type classifications"
                if allTrue:
                    error_messages.append(classification_error_message)
                else:
                    if not has_aadt:
                        error_messages.append("AADT")
                    if not has_speed:
                        error_messages.append("Speed Limit")
                    if not has_county:
                        error_messages.append("County")
                    if not has_access_control:
                        error_messages.append("Access Control")
                    if not has_median:
                        error_messages.append("Median")
                    if not has_lanes:
                        error_messages.append("Lanes")
                    if not has_area_type:
                        error_messages.append("Area Type")
                    if not has_name:
                        error_messages.append("Route Name")

                if len(error_messages) > 1:
                    error_message = "Missing " + (' AND '.join(error_messages)) + " values"
                else:
                    if error_messages[0] == classification_error_message:
                        error_message = error_messages[0]
                    else:
                        error_message = "Missing {0} value".format(error_messages[0])

                row[fields.index(USRAP_CLASS_ERROR)] = error_message

                # mark segment as usrap segment 'NO' if it does not fulfill the
                # roadway type condition
                row[fields.index(USRAP_SEGMENT)] = 'NO'
                cursor.updateRow(row)
    return feature_class

def merge_segments(update_row, update_cursor, fields, feature_class, condition):
    """ merge the adjacent segments according to condition provided and
        update its field value  """
    if update_row[0] not in DELETE_OIDS:
        try:
            # find the adjacent segments
            adjacent = arcpy.SelectLayerByLocation_management(
                feature_class,
                'BOUNDARY_TOUCHES',
                update_row[-1],
                selection_type='NEW_SELECTION')
            OID_merged = []
            # take a adjacent segment to merge on merge condition fulfill
            where = "{0} = 'YES'".format(USRAP_SEGMENT)
            with arcpy.da.SearchCursor(adjacent, fields, where) as cursor:
                for current in cursor:
                    if '' in current or None in current:
                        continue
                    touches = update_row[-1].touches(current[-1])
                    if touches == False:
                        continue
                    # truth_table contains boolean value for each condition
                    truth_table = []
                    avg_aadt = []
                    for tup in condition:
                        pre_val = update_row[fields.index(tup[0])]
                        cur_val = current[fields.index(tup[0])]
                        # check for 'EQUAL_TO' condition
                        if tup[1] == EQUAL_TO:
                            if tup[0] == USRAP_ACCESS_CONTROL:
                                #no and partial access should be evaluated as the same
                                truth_table.append(pre_val == cur_val or
                                                   (str(pre_val) != value_access_control_full and
                                                    str(cur_val) != value_access_control_full))
                            else:
                                truth_table.append(pre_val == cur_val)
                            continue
                        # check for 'LESS_THAN_EQUAL_TO' condition
                        elif tup[1] == LESS_THAN_EQUAL_TO:
                            if tup[0] == USRAP_AVG_AADT:
                                sort = sorted([pre_val, cur_val])
                                avg_aadt.append(fields.index(tup[0]))
                                # get length of segments
                                if update_row != None:
                                    update_row_length = update_row[-1].getLength()
                                else:
                                    update_row_length = 0

                                if current[-1] != None:
                                    current_row_length = current[-1].getLength()
                                else:
                                    current_row_length = 0

                                if sort[0] == 0 or None in sort:
                                    truth_table.append(sort[1] <= tup[2])
                                else:
                                    percent_val = ((sort[1]-sort[0])/sort[0]) * 100
                                    truth_table.append(percent_val <= tup[2])

                                if pre_val == None and cur_val != None:
                                    pre_val = 0
                                elif cur_val == None and pre_val != None:
                                    cur_val = 0
                                if pre_val == cur_val == None:
                                    weighted_avrg = None
                                else:
                                    # calculate weighted average
                                    if (update_row_length + current_row_length) > 0:
                                        weighted_avrg = (((pre_val*update_row_length) +
			                                        (cur_val*current_row_length))/
			                                        (update_row_length +
			                                        current_row_length))
                                        weighted_avrg = round(weighted_avrg, 1)
                                    else:
                                        weighted_avrg = 0
                                    avg_aadt.append(weighted_avrg)
                                continue
                            else:
                                truth_table.append(float(pre_val) <= tup[2] and
                                                   float(cur_val) <= tup[2])
                        # check for 'LESS_THAN_EQUAL_TO_OR_MORE_THAN_EQUAL_TO'
                        # condition
                        elif tup[1] == LESS_THAN_EQUAL_TO_OR_MORE_THAN_EQUAL_TO:
                            truth_table.append((float(pre_val) <= tup[2] and
                                                float(cur_val) <= tup[2]) or
                                               (float(pre_val) >= tup[3] and
                                                float(cur_val) >= tup[3]))
                        # check for 'MORE_THAN_EQUAL_TO' condition
                        elif tup[1] == MORE_THAN_EQUAL_TO:
                            truth_table.append(float(pre_val >= tup[2] and
                                                     float(cur_val) >= tup[2]))

                    # proceed to merge geometry when all conditions are satisfied
                    if not False in truth_table:
                        #TODO look at adding current != update here if necessary
                        if update_row[0] not in DELETE_OIDS:
                            try:
                                update_row[avg_aadt[0]] = avg_aadt[1]        
                                update_row[-1] = update_row[-1].union(current[-1])

                                update_cursor.updateRow(update_row)

                                OID_merged.append(current[0])
                                DELETE_OIDS.append(current[0])

                            except Exception as re:
                                msg = "Merge failed for ObjectId {0} and {1}".format(\
                                        update_row[0], current[0])
                                arcpy.AddWarning(msg)
                                arcpy.AddWarning(re.message)
                # delete the redundant records which are merged with others
                where = ''
                if len(OID_merged) > 0:
                    merged_oids = map(str, OID_merged)
                    field_oid = str(arcpy.Describe(feature_class).OIDFieldName)
                    where = field_oid +' = ' + ' OR {0} = '.format(field_oid).join(merged_oids)
                    arcpy.SelectLayerByAttribute_management(feature_class,
                                                            'NEW_SELECTION',
                                                            where)
                    arcpy.DeleteRows_management(feature_class)

                    # Recursive call with updated row
                    return merge_segments(update_row, update_cursor, fields,
                                          feature_class, condition)
            return feature_class
        except RuntimeError as error:
            arcpy.AddError(str(error))
            raise arcpy.ExecuteError(error[0])

def add_segids(feature_class, field_name):
    """ add unique id to USRAP_SEGID in usrap feature class  """
    try:
        where = "{0} = 'YES'".format(USRAP_SEGMENT)
        arcpy.SelectLayerByAttribute_management(feature_class,
                                                'CLEAR_SELECTION')
        arcpy.SelectLayerByAttribute_management(feature_class, "NEW_SELECTION", where)
        arcpy.AddField_management(feature_class, field_name, 'LONG',
                                  field_alias=field_name)
        segment_id = USRAP_SEGID_START_FROM
        with arcpy.da.UpdateCursor(feature_class, [field_name]) as update_cur:
            for row in update_cur:
                row[0] = segment_id
                segment_id += 1
                update_cur.updateRow(row)
        arcpy.SelectLayerByAttribute_management(feature_class,
                                        'CLEAR_SELECTION')
        return feature_class
    except Exception as e:
        arcpy.AddError(str(e))

def check_domain(fc, fc_info, class_message, main_message):
    workspace = get_workspace(fc)
    field = get_field_object(fc, fc_info)
    dom_codes = get_domain_values(workspace, field.domain)

    if len(dom_codes.keys()) != len(class_message):
        raise arcpy.ExecuteError(main_message.format(len(class_message)))

    for message, desc in class_message.items():
        if desc.lower() not in (des.lower() for des in dom_codes.values()):
            raise arcpy.ExecuteError("Description: '{0}' {1}".format(desc, message))

def add_message(msg):
    arcpy.SetProgressorLabel(msg)
    arcpy.AddMessage(msg)

def add_formatted_message(msg, fc):
    fc_name = os.path.basename(fc)
    msg = msg.format(fc_name)
    arcpy.SetProgressorLabel(msg)
    arcpy.AddMessage(msg)

def check_key_fields(key_fields, aadt_layers, aadt_field):
    #verify that none of the other value layers contain a field with the same name
    # as another layers key field
    #if this condition exists it will cause the actual value field to have a new name
    # when identity is performed and prevent appropriate values from being transferred to
    # the target class
    for aadt_layer in aadt_layers:
        key_fields[aadt_layer] = [aadt_field]

    problem_fields = {}
    x = 0
    for kl in key_fields.keys():
        key_layer_fields = []
        for key_layer in key_fields.keys():
            if kl != key_layer:
                for f in key_fields[key_layer]:
                    key_layer_fields.append(str(f))
        fields = [f.name for f in arcpy.ListFields(kl)]
        for field in key_layer_fields:
            if fields.count(field) > 0 and key_fields[kl][0] != field:
                if problem_fields.keys().count(kl) > 0:
                    if not problem_fields[kl].count(field) > 0:
                        problem_fields[kl].append(field)
                else:
                    problem_fields[kl] = [field]
    return problem_fields

def combine_values(baseline_selected, value_set, cluster_tolerance, problem_fields, county_geom, full_out_path):
    shape_field_name = arcpy.Describe(baseline_selected).shapeFieldName
    check_list = [shape_field_name]
    for values in value_set:
        if isinstance(baseline_selected, str) or type(baseline_selected, unicode):
            sp = baseline_selected + "sp"
        else:
            sp = baseline_selected[0] + "sp"
        arcpy.MultipartToSinglepart_management(baseline_selected, sp)

        if VERSION_USED != "10.2":
            arcpy.RepairGeometry_management(sp)
            #TODO...why did I comment this out
            #arcpy.AddSpatialIndex_management(sp)

        clipped = IN_MEMORY + os.sep + os.path.basename(values[0]) + "Clip"
        arcpy.Clip_analysis(values[0], county_geom, clipped)

        clipped_sp = clipped + "sp"
        arcpy.MultipartToSinglepart_management(clipped, clipped_sp)

        if VERSION_USED != "10.2":
            arcpy.RepairGeometry_management(clipped_sp)

        baseline_selected = combine_attributes(sp,
                                    clipped_sp,
                                    values[1],
                                    values[2],
                                    None,
                                    None,
                                    cluster_tolerance,
                                    problem_fields, full_out_path, values[0])

        arcpy.Delete_management(clipped)
        if baseline_selected != sp:
            arcpy.Delete_management(sp)

        check_list.append(values[2])

        if arcpy.Exists(baseline_selected):
            arcpy.DeleteIdentical_management(baseline_selected, check_list)

    return baseline_selected

def repair_temp_data(out_temp_gdb, in_data):
    """ This function works around 2 issues at 10.2...not necessary at later releases """
    """ 1) RepairGeometry fails on datasets in in_memory workspaces """
    """ 2) Clip fails on z enabled line features when none of the line features intersect the clip geometry """ 
    out_temp_fc = os.path.join(out_temp_gdb, "temp_" + os.path.basename(in_data))
    arcpy.env.outputMFlag = 'Disabled'
    arcpy.env.outputZFlag = 'Disabled'
    arcpy.CopyFeatures_management(in_data, out_temp_fc)
    try:
        arcpy.RepairGeometry_management(out_temp_fc)
        arcpy.AddSpatialIndex_management(out_temp_fc)
    except:
        arcpy.AddWarning("Repair Geometry failed on " + str(out_temp_fc))
        pass
    return out_temp_fc

def main():
    """ main function """
    #Basic segmentation tool's inputs (arranged in accending order)
    ftrclass_route = arcpy.GetParameterAsText(0)
    field_route_name = arcpy.GetParameterAsText(1)
    field_route_type = arcpy.GetParameterAsText(2)
    value_route_type = arcpy.GetParameter(3)
    ftrclass_county = arcpy.GetParameterAsText(4)
    field_county_name = arcpy.GetParameterAsText(5)
    ftrclass_access_control = arcpy.GetParameterAsText(6)
    field_access_control_info = arcpy.GetParameterAsText(7)
    ftrclass_median = arcpy.GetParameterAsText(8)
    field_median_info = arcpy.GetParameterAsText(9)
    ftrclass_travel_lanes = arcpy.GetParameterAsText(10)
    field_travel_lanes_info = arcpy.GetParameterAsText(11)
    ftrclass_area_type = arcpy.GetParameterAsText(12)
    field_area_type_info = arcpy.GetParameterAsText(13)
    ftrclass_speed_limit = arcpy.GetParameterAsText(14)
    field_speed_limit_info = arcpy.GetParameterAsText(15)
    ftrclass_aadt_multi_layers = arcpy.GetParameter(16)
    field_aadt_multi_layers_value = arcpy.GetParameterAsText(17)
    output_folder = arcpy.GetParameterAsText(18)
    cluster_tolerance = arcpy.GetParameterAsText(19)

    #Create temp gdb to store all value classes
    # this is to work around issue with RepairGeometry not working
    # against in_memory datasets at 10.2
    if VERSION_USED == "10.2": 
        if not os.path.exists(os.path.join(output_folder, TEMP_GDB)):
            # create file geodatabase at output location, if not present
            arcpy.CreateFileGDB_management(output_folder, TEMP_GDB)
        out_temp_gdb = os.path.join(output_folder, TEMP_GDB)

        ftrclass_route = repair_temp_data(out_temp_gdb, ftrclass_route)
        ftrclass_county = repair_temp_data(out_temp_gdb, ftrclass_county)
        ftrclass_access_control = repair_temp_data(out_temp_gdb, ftrclass_access_control)
        ftrclass_median = repair_temp_data(out_temp_gdb, ftrclass_median)
        ftrclass_travel_lanes = repair_temp_data(out_temp_gdb, ftrclass_travel_lanes)
        ftrclass_area_type = repair_temp_data(out_temp_gdb, ftrclass_area_type)
        ftrclass_speed_limit = repair_temp_data(out_temp_gdb, ftrclass_speed_limit)

        t = []
        if len(ftrclass_aadt_multi_layers) > 0:
            for ftr in ftrclass_aadt_multi_layers:
                t.append(repair_temp_data(out_temp_gdb, ftr.value))
                #t.append(repair_temp_data(out_temp_gdb, ftr))

        ftrclass_aadt_multi_layers = t
        del t
    else:
        t = []
        if len(ftrclass_aadt_multi_layers) > 0:
            for ftr in ftrclass_aadt_multi_layers:
                t.append(ftr.value)
                #t.append(ftr)

        ftrclass_aadt_multi_layers = t
        del t


    full_out_path = output_folder + os.sep + OUTPUT_GDB_NAME + os.sep + OUTPUT_SEGMENT_NAME
    key_fields = {ftrclass_route : [field_route_name, field_route_type],
                  ftrclass_county : [field_county_name],
                  ftrclass_access_control : [field_access_control_info],
                  ftrclass_median : [field_median_info],
                  ftrclass_travel_lanes : [field_travel_lanes_info],
                  ftrclass_area_type : [field_area_type_info],
                  ftrclass_speed_limit : [field_speed_limit_info]}

    problem_fields = check_key_fields(key_fields, ftrclass_aadt_multi_layers, field_aadt_multi_layers_value)

    main_message = "Domain to denote Access Controls must contain {0} coded values"
    class_message = {
        "is only accepted for Full Access Control description": value_access_control_full,
        "is only accepted for Partial Access Control description": value_access_control_partial,
        "is only accepted for No Access Control description": value_access_control_no
    }
    check_domain(ftrclass_access_control, field_access_control_info, class_message, main_message)

    main_message = "Domain to denote Medians must contain {0} coded values"
    class_message = {
        "is only accepted for Divided Roadway description": value_median_divided,
        "is only accepted for Undivided Roadway description": value_median_undivided
    }
    check_domain(ftrclass_median, field_median_info, class_message, main_message)

    main_message = "Domain to denote Area Type must contain {0} coded values"
    class_message = {
        "is only accepted for Urban Area description": value_area_type_urban,
        "is only accepted for Rural Area description": value_area_type_rural
    }
    check_domain(ftrclass_area_type, field_area_type_info, class_message, main_message)

    # list of conditions on which two segments will be merged
    # tuple element description:-
    #   first element - field name in usrap route feature class
    #   second element - condition on which fields would tested
    #       'EQUAL_TO' - two segments must have same field values
    #       'LESS_THAN_EQUAL_TO_OR_MORE_THAN_EQUAL_TO' - two segment
    #           must have field values between third element (lower limit)
    #           and fourth element (upper limit) of same tuple
    #       LESS_THAN_EQUAL_TO - two segments must have field values
    #           less than or equal to third element (upper limit) of tuple
    #       MORE_THAN_EQUAL_TO - two segments must have field values more
    #           than or equal to the third element (lower limit) of tuple
    condition = [(USRAP_COUNTY, EQUAL_TO),
                    (field_route_name, EQUAL_TO),
                    (field_route_type, EQUAL_TO),
                    (USRAP_ACCESS_CONTROL, EQUAL_TO),
                    (USRAP_SPEED_LIMIT,
                    LESS_THAN_EQUAL_TO_OR_MORE_THAN_EQUAL_TO, 50, 55),
                    (USRAP_AVG_AADT, LESS_THAN_EQUAL_TO, 20)]

    try:
        max_val = 9 + len(ftrclass_aadt_multi_layers)
        arcpy.SetProgressor("step", "Initializing...", 0, max_val, 1)
        msg = "Preparing output workspace"
        add_message("Preparing output workspace")
        if not os.path.exists(os.path.join(output_folder, OUTPUT_GDB_NAME)):
            # create file geodatabase at output location, if not present
            arcpy.CreateFileGDB_management(output_folder, OUTPUT_GDB_NAME)
        output_folder = os.path.join(output_folder, OUTPUT_GDB_NAME)

        # finding unique field values for the baseline feature
        # class for route types
        baseline_values = get_field_values(ftrclass_route, field_route_type)
        # checking if route type is selected but not all
        baseline_selected = fc_baseline = None
        if (len(value_route_type) > 0 and
                len(value_route_type) != len(baseline_values)):
            field = get_field_object(ftrclass_route, field_route_type)
            lookup = None
            if field.domain:
                # find gdb for route feature class
                workspace = get_workspace(ftrclass_route)
                # create lookup for domain value
                lookup = get_domain_values(workspace, field.domain)
            where = create_where_clause(field, value_route_type, lookup)
            # use this tool once and create where condition such as
            # it cover all the selection parms.
            baseline_selected = arcpy.MakeFeatureLayer_management(ftrclass_route,
                                                           'baseline_selected', where)

        # set label to notify user if no route type is selected
        if len(value_route_type) == 0:
            add_message("No route type selected. Taking all route types for analysis.")
        if not baseline_selected:
            baseline_selected = ftrclass_route
        arcpy.SetProgressorPosition()

        #process by county
        with arcpy.da.SearchCursor(ftrclass_county, [field_county_name, "SHAPE@"]) as cursor:
            for row in cursor:
                county_name = str(row[0])
                county_geom = row[1]
                add_message("Processing " + county_name + " County")

                county_name = str(arcpy.ValidateTableName(county_name, IN_MEMORY))

                routes = IN_MEMORY + "\\clip" + county_name + "routes"
     
                arcpy.Clip_analysis(baseline_selected, county_geom, routes)

                for problem_field_key in problem_fields.keys():
                    arcpy.DeleteField_management(problem_field_key, problem_fields[problem_field_key])

                c = arcpy.GetCount_management(routes)
                add_message("   " + str(c[0]) + " routes in: " + county_name)

                if int(c[0]) > 0:
                    value_set = [[ftrclass_county, field_county_name, USRAP_COUNTY],
                                 [ftrclass_access_control, field_access_control_info, USRAP_ACCESS_CONTROL],
                                 [ftrclass_median, field_median_info, USRAP_MEDIAN],
                                 [ftrclass_travel_lanes, field_travel_lanes_info, USRAP_LANES],
                                 [ftrclass_area_type, field_area_type_info, USRAP_AREA_TYPE],
                                 [ftrclass_speed_limit, field_speed_limit_info, USRAP_SPEED_LIMIT]]
                    routes = combine_values(routes, value_set, cluster_tolerance, problem_fields, county_geom, full_out_path)

                    if len(ftrclass_aadt_multi_layers) > 0:
                        # combine attributes of identity result and AADT
                        shape_field_name = arcpy.Describe(routes).shapeFieldName
                        check_list = [shape_field_name]
                        new_fields = []
                        for ftr in ftrclass_aadt_multi_layers:
                            new_field = USRAP_AADT_YYYY + '_' + os.path.basename(ftr)[-4:]
                            new_fields.append(new_field)
                            seg_name = None
                            out_gdb = None

                            aadt_clipped = IN_MEMORY + "\\clip" + county_name + "aadt" + os.path.basename(ftr)[-4:]

                            arcpy.Clip_analysis(ftr, county_geom, aadt_clipped)
                            #arcpy.RepairGeometry_management(aadt_clipped)

                            routes = combine_attributes(routes,
                                                                   aadt_clipped,\
                                                            field_aadt_multi_layers_value,
                                                                   new_field,
                                                                   seg_name,
                                                                   out_gdb, cluster_tolerance, problem_fields, full_out_path, ftr)

                            check_list.append(new_field)

                            #TODO whats with the mix of routes and baseline...i forget
                            if arcpy.Exists(baseline_selected):
                                arcpy.DeleteIdentical_management(routes, check_list)
                            else:
                                arcpy.AddMessage(str(routes) + " DOES NOT EXIST")

                            arcpy.Delete_management(aadt_clipped)

                        # calculate the average of all supplied years of AADT
                        routes = calculate_average(routes, new_fields, USRAP_AVG_AADT)

                    # baseline segment will be identified as usrap segment
                    routes = identify_usrap_segment(routes, roadway_type, output_folder, field_route_name)

                    # delete duplicate records
                    fields = [f.name for f in arcpy.ListFields(routes)
                              if f.type != "OID"]
                    routes = arcpy.DeleteIdentical_management(routes, fields)

                    layer = arcpy.MakeFeatureLayer_management(routes, 'layer')
                    arcpy.ResetProgressor()

                    max_val = int(arcpy.GetCount_management(routes)[0])
                    add_message('   {0} segments present after combining attributes'.format(max_val))
                    add_message("   Merging features... this may take a while")
                    # variables for progressor and message
                    stepper = 0
                    lower = 10

                    arcpy.SetProgressor('step', msg, 0, max_val, 1)
                    # collect field names on which conditions would be checked
                    fields = [field[0] for field in condition]
                    # insert required field names
                    fields.insert(0, 'OID@')
                    fields += [USRAP_SEGMENT, 'SHAPE@']

                    global DELETE_OIDS

                    where = "{0} = 'YES'".format(USRAP_SEGMENT)
                    with arcpy.da.UpdateCursor(layer, fields, where) as update_cursor:
                        for row in update_cursor:
                            if '' in row:
                                continue
                            DELETE_OIDS = []

                            numfeatures = merge_segments(row, update_cursor, fields,
                                                         layer, condition)
                            if len(DELETE_OIDS) > 0:
                                stepper += (len(DELETE_OIDS)*2)
                            else:
                                stepper += 1
                            percent = round(int((stepper/float(max_val))*100))
                            if lower <= percent < 100:
                                arcpy.AddMessage('     Merging completed {0}%'.format(lower))
                                lower += 10
                            arcpy.SetProgressorPosition(stepper)
                    arcpy.AddMessage('     Merging completed {0}%'.format('100'))
                    merged_count = int(arcpy.GetCount_management(routes)[0])
                    diff = max_val - merged_count
                    arcpy.AddMessage('   {0} are merged out of {1} segments'.format(diff,
                                                                                 max_val))
                    arcpy.ResetProgressor()
                    msg = "   Assigning USRAP_SEGID to segments"
                    arcpy.AddMessage(msg)
                    arcpy.SetProgressor('step', msg, 0, 2, 1)

                    routes = add_segids('layer', USRAP_SEGID)
                    arcpy.SetProgressorPosition()

                existing_fields = [field.name for field in arcpy.Describe(full_out_path).fields]
                new_fields = [field for field in arcpy.Describe(routes).fields if field.name not in existing_fields and not field.required]

                for field in new_fields:
                    arcpy.AddField_management(full_out_path, field.name, field.type)


                oid_field_name = arcpy.Describe(routes).oidFieldName
                shp_field_name = arcpy.Describe(routes).shapeFieldName
                route_fields = [field.name for field in arcpy.ListFields(routes) if field.name != oid_field_name and field.name != shp_field_name]
                route_fields.append("SHAPE@")

                oid_field_name = arcpy.Describe(full_out_path).oidFieldName
                shp_field_name = arcpy.Describe(full_out_path).shapeFieldName
                out_fields = [field.name for field in arcpy.ListFields(full_out_path) if field.name != oid_field_name and field.name != shp_field_name]
                out_fields.append("SHAPE@")

                #can get around the append thing with this but loose
                # all of the inital field values
                with arcpy.da.SearchCursor(routes, route_fields) as ser_cur:
                    with arcpy.da.InsertCursor(full_out_path, out_fields) as in_cur:
                        for row in ser_cur:
                            new_row = []
                            used_indexes = []
                            for field in route_fields:
                                if out_fields.index(field) > -1:
                                    used_indexes.append(out_fields.index(field))
                                    new_row.insert(out_fields.index(field), row[route_fields.index(field)])
                            if len(new_row) != len(out_fields):
                                x = 0
                                while x < len(out_fields):
                                    if x not in used_indexes:
                                        new_row.insert(x, None)
                                    x += 1
                            in_cur.insertRow(new_row)

                #THIS ONLY INSERTS THE FIRST CHARACTER FROM STRING FIELDS WITH PY 3
                # FOR SOME REASON and thus replaced with the above cursors
                #arcpy.Append_management(routes, full_out_path, "NO_TEST")
                arcpy.Delete_management("in_memory")

        # copy the rest of data when partial road types are selected for
        # analysis
        if fc_baseline:
            arcpy.SetProgressorLabel("copying non-usrap segments to output")
            baseline_invert_selected = arcpy.SelectLayerByAttribute_management(\
                                                fc_baseline, 'SWITCH_SELECTION')
            arcpy.Append_management(baseline_invert_selected, baseline_selected,
                                    'NO_TEST')
        #Assign unique segIDs
        where = "{0} = 'YES'".format(USRAP_SEGMENT)
        l = arcpy.MakeFeatureLayer_management(full_out_path, "FINAL_OUTPUT_SEGMENTS")
        arcpy.SelectLayerByAttribute_management(str(l[0]), 'CLEAR_SELECTION')
        arcpy.SelectLayerByAttribute_management(str(l[0]), "NEW_SELECTION", where)

        segment_id = USRAP_SEGID_START_FROM
        with arcpy.da.UpdateCursor(str(l[0]), [USRAP_SEGID]) as update_cur:
            for row in update_cur:
                row[0] = segment_id
                segment_id += 1
                update_cur.updateRow(row)
        arcpy.SelectLayerByAttribute_management(str(l[0]),
                                        'CLEAR_SELECTION')
        arcpy.Delete_management(str(l[0]))

        arcpy.RepairGeometry_management(full_out_path)

        arcpy.DeleteIdentical_management(full_out_path, check_list)

        arcpy.AddSpatialIndex_management(full_out_path)

        del ftrclass_route, ftrclass_county, ftrclass_access_control, ftrclass_median
        del ftrclass_travel_lanes, ftrclass_area_type, ftrclass_speed_limit
        del aadt_clipped, baseline_selected, baseline_values, c, check_list, 
        del county_geom, cursor, fc_baseline, field, fields, full_out_path
        del problem_fields, update_cur, update_cursor, value_set, shape_field_name

        if len(ftrclass_aadt_multi_layers) > 0:
            for ftr in ftrclass_aadt_multi_layers:
                del ftr
        del ftrclass_aadt_multi_layers

        if VERSION_USED == "10.2":
            arcpy.Delete_management(out_temp_gdb)

        arcpy.SetProgressorPosition()
    except Exception as e:
        arcpy.AddError(str(e))
        print(e)
    finally:
        # ensure the in_memory workspace is cleared to free up memory
        arcpy.Delete_management(IN_MEMORY)
        if VERSION_USED == "10.2":
            if arcpy.Exists(out_temp_gdb):
                arcpy.Delete_management(out_temp_gdb)
                del out_temp_gdb

if __name__ == '__main__':
    main()
