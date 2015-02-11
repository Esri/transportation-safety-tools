"""
#-------------------------------------------------------------------------------
# Name:        BasicSegmentation.py
# Purpose:     This tool is used to prepare the baseline routes dataset with
#              all necessary attributes (route name, route type, county,
#              access control, medians, travel lanes, area type, speed limit
#              and AADT.
#
# Author:      CyberTech Systems and Software Ltd.
#
#-------------------------------------------------------------------------------
"""
# pylint: disable = C0103, R0912, R0914, R0915, E1103, W0703, W0612, E1101
# required imports
import arcpy
import os

arcpy.env.overwriteOutput = True

IN_MEMORY = 'in_memory'

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
    return (domain.codedValues for domain in arcpy.da.ListDomains(workspace)
            if domain.name == domain_name).next()

def get_field_values(feature_class, field_name):
    """ takes feature class and field object as input
        and return unique field values list """
    return sorted(set(row[0] for row in arcpy.da.SearchCursor(feature_class,
                                                              [field_name])))

def get_field_object(feature_class, field_name):
    """ takes feature class and field name as input and
        return field object for the given field name"""
    return (field for field in arcpy.Describe(feature_class).fields
            if field.name == field_name).next()

def disable_m_value(feature_class):
    """ Disable M value of feature class """
    arcpy.env.outputMFlag = 'Disabled'
    fc_name = os.path.basename(str(feature_class))
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

def identity(target_ftrs, identity_ftrs, output_name=None, output_folder=None):
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

        # Add 'identity' in output feature class name if not present
        if out_ftrs.find('_identity') == -1:
            out_ftrs += '_identity'
        out_ftrs = check_name_length(out_ftrs)

        # Identity operation to combine attributes
        result = arcpy.Identity_analysis(target_ftrs, identity_ftrs, out_ftrs,
                                         "NO_FID")[0]
        feature_name = check_name_length("sp" + os.path.basename(str(result)))
        if output_name:
            feature_name = output_name

        # Convert multiparts to single part, if any
        path = os.path.join(output_location, feature_name)
        result_singlepart = arcpy.MultipartToSinglepart_management(result, path)
        arcpy.Delete_management(result)
        return result_singlepart

    except Exception as e:
        arcpy.AddError(str(e))

def calculate_average(feature_class, existing_fields, new_field):
    """ calculate the average of AADT fields for fields that have
        valid value """

    arcpy.AddField_management(feature_class, new_field, 'DOUBLE',
                              field_alias=new_field)
    fields = list(existing_fields)
    fields.append(new_field)
    with arcpy.da.UpdateCursor(feature_class, fields) as cursor:
        for row in cursor:
            try:
                # calculate the average based on only those fields that
                # have valid values
                dividend = sum([float(value) for value in row[:-1]
                                if value != None])
                divisor = sum([1 for value in row[:-1] if value != None])
                row[-1] = round((dividend / divisor), 1)
            except (ValueError, ZeroDivisionError):
                row[-1] = None
            cursor.updateRow(row)
    return feature_class

def copy_fields(feature_class, fields_name_info, fc_source):
    """ create new fields and copy records to it """
    try:
        domain_lu = None
        field_type = None
        for existing_field, new_field in fields_name_info.items():
            # get the field object of existing field in baseline feature class
            field = get_field_object(feature_class, existing_field)
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
                       new_field_name, output_name=None, output_folder=None):
    """ combines the required fields from other feature classes with
        baseline feature class """
    try:

        if arcpy.Describe(fc_target).hasM:
            fc_target = disable_m_value(fc_target)

        # keep the feature class to find domain in copy_fields function
        fc_source = fc_identity
        if arcpy.Describe(fc_identity).hasM:
            fc_identity = disable_m_value(fc_identity)
            fc_identity_name = os.path.basename(fc_identity[0])
        else:
            fc_identity_name = os.path.basename(fc_identity)

        # keep required fields in list to find newly added fields after identity
        # operation
        fc_target_fields = [field.name for field in
                            arcpy.Describe(fc_target).fields]

        #   Make a copy of identity feature class
        copy_output_name = os.path.join(IN_MEMORY, "_".join([fc_identity_name,
                                                             "copy"]))
        fc_identity_copy = arcpy.CopyFeatures_management(fc_identity,
                                                         copy_output_name)
        fc_identity_fields = [field.name for field in \
                              arcpy.Describe(fc_identity_copy).fields \
                              if field.name != fc_identity_field_name and \
                              not field.required and \
                              not field.name.lower().startswith('shape')]

        # delete unncessary fields coming from identity feature class
        if len(fc_identity_fields) > 0:
            arcpy.DeleteField_management(fc_identity_copy, fc_identity_fields)


        # identity analysis to combine attributes of identity feature class
        # into baseline
        baseline_routes = identity(fc_target, fc_identity_copy,
                                   output_name, output_folder)

        fields_to_delete = []
        baseline_output_fields = []
        for field in arcpy.Describe(baseline_routes).fields:
            if field.name not in fc_target_fields and \
                    not field.name.startswith(fc_identity_field_name) and \
                    not field.required:
                fields_to_delete.append(field.name)
            else:
                baseline_output_fields.append(field.name)

        # delete unncessary fields coming from identity feature class
        if len(fields_to_delete) > 0:
            arcpy.DeleteField_management(baseline_routes, fields_to_delete)

        # Get the newly added field to baseline routes
        if fc_identity_field_name in fc_target_fields:
            baseline_set = set(baseline_output_fields)
            fc_target_set = set(fc_target_fields)
            newly_added_field = list(baseline_set - fc_target_set)[0]
        else:
            newly_added_field = fc_identity_field_name

        # operation
        # copy existing field rows into a new field added in
        # baseline feature class
        field_dict = {newly_added_field: new_field_name}

        baseline_routes = copy_fields(baseline_routes, field_dict, fc_source)
        # delete the previous field from which rows has beed copied to new field
        arcpy.DeleteField_management(baseline_routes, newly_added_field)
        return baseline_routes

    except Exception as e:
        arcpy.AddError(str(e))

def identify_usrap_segment(feature_class, roadway_types):
    """ create new field 'USRAP_SEGMENT' and assign 'YES' or 'NO' value
        according to roadway type """
    # field name for USRAP segments
    fields = list(set([k for d in roadway_types for k in d.keys()]))
    fields.append(USRAP_SEGMENT)

    # create new field to identify USRAP Segments
    arcpy.AddField_management(feature_class, USRAP_SEGMENT, 'TEXT',
                              field_length=3, field_alias=USRAP_SEGMENT)
    # Take a segment to from baseline route feature class
    with arcpy.da.UpdateCursor(feature_class, fields) as cursor:
        for row in cursor:
            for roadway_type in roadway_types:
                truth_table = []
                if '' in row:
                    truth_table.append(False)
                    break

                # Test a segment on roadway type to identify it as usrap segment
                for field in roadway_type.keys():
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
                if False not in truth_table:
                    # mark segment as usrap segment 'YES' if it fulfill the
                    # roadway type condition
                    row[fields.index(USRAP_SEGMENT)] = 'YES'
                    cursor.updateRow(row)
                    break
            if truth_table and False in truth_table:
                # mark segment as usrap segment 'NO' if it does not fulfill the
                # roadway type condition
                row[fields.index(USRAP_SEGMENT)] = 'NO'
                cursor.updateRow(row)
    return feature_class

def merge_segments(update_row, update_cursor, fields, feature_class, condition):
    """ merge the adjacent segments according to condition provided and
        update its field value  """
    try:
        # find the adjacent segments
        oid_field_name = arcpy.Describe(feature_class).OIDFieldName
        adjacent = arcpy.SelectLayerByLocation_management(
            feature_class,
            'BOUNDARY_TOUCHES',
            update_row[-1],
            selection_type='NEW_SELECTION')
        OID_merged = []

        # take a adjacent segment to merge on merge condition fulfill
        where = "{0} <> 'NO'".format(USRAP_SEGMENT)
        with arcpy.da.SearchCursor(adjacent, fields, where) as cursor:
            for current in cursor:
                if '' in current:
                    continue
                # truth_table contains boolean value for each condition
                truth_table = []
                avg_aadt = []
                for tup in condition:
                    pre_val = update_row[fields.index(tup[0])]
                    cur_val = current[fields.index(tup[0])]
                    # check for 'EQUAL_TO' condition
                    if tup[1] == EQUAL_TO:
                        truth_table.append(pre_val == cur_val)
                        continue
                    # check for 'LESS_THAN_EQUAL_TO' condition
                    elif tup[1] == LESS_THAN_EQUAL_TO:
                        if tup[0] == USRAP_AVG_AADT:
                            sort = sorted([pre_val, cur_val])
                            avg_aadt.append(fields.index(tup[0]))
                            # get length of segments
                            update_row_length = update_row[-1].getLength()
                            current_row_length = current[-1].getLength()
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
                                weighted_avrg = (((pre_val*update_row_length) +
                                                  (cur_val*current_row_length))/
                                                 (update_row_length +
                                                  current_row_length))
                                weighted_avrg = round(weighted_avrg, 1)
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
                    update_row[avg_aadt[0]] = avg_aadt[1]
                    try:
                        update_row[-1] = update_row[-1].union(current[-1])
                        update_cursor.updateRow(update_row)
                        OID_merged.append(current[0])
                        global DELETE_OIDS
                        DELETE_OIDS.append(current[0])
                    except ValueError:
                        msg = "Merge failed for ObjectId {0} and {1}".format(\
                                update_row[0], current[0])
                        arcpy.AddMessage(msg)
            # delete the redundant records which are merged with others
            where = ''
            if len(OID_merged) > 0:
                merged_oids = map(str, OID_merged)
                oidFieldName = arcpy.Describe(feature_class).oidFieldName
                where = "{0} = ".format(oidFieldName) + \
                        " OR {0} = ".format(oidFieldName).join(merged_oids)
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
        arcpy.SelectLayerByAttribute_management(feature_class,
                                                'CLEAR_SELECTION')
        arcpy.AddField_management(feature_class, field_name, 'LONG',
                                  field_alias=field_name)
        segment_id = USRAP_SEGID_START_FROM
        with arcpy.da.UpdateCursor(feature_class, [field_name]) \
                as update_cur:
            for row in update_cur:
                row[0] = segment_id
                segment_id += 1
                update_cur.updateRow(row)
        return feature_class
    except Exception as e:
        arcpy.AddError(str(e))

def main():
    """ main function """
    # Basic segmentation tool's inputs (arranged in accending order)
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

    ftrclass_route = arcpy.GetParameterAsText(0)
    field_route_name = arcpy.GetParameterAsText(1)
    field_route_type = arcpy.GetParameterAsText(2)
    value_route_type = arcpy.GetParameter(3)
    ftrclass_county = arcpy.GetParameterAsText(4)
    field_county_name = arcpy.GetParameterAsText(5)
    ftrclass_access_control = arcpy.GetParameterAsText(6)
    field_access_control_info = arcpy.GetParameterAsText(7)

    workspace = get_workspace(ftrclass_access_control)
    field = get_field_object(ftrclass_access_control, field_access_control_info)
    dom_code = get_domain_values(workspace, field.domain)

    if len(dom_code.keys()) != 3:
        msg = "Domain to denote Access Controls must contain three coded values"
        raise arcpy.ExecuteError(msg)

    if value_access_control_full.lower() not in (des.lower()
                                                 for des in dom_code.values()):
        message = "is only accepted for Full Access Control description"
        msg = "Description: '{0}' {1}".format(value_access_control_full, message)
        raise arcpy.ExecuteError(msg)

    if value_access_control_partial.lower() not in (des.lower() for des in
                                                    dom_code.values()):
        message = "is only accepted for Partial Access Control description"
        msg = "Description: '{0}' {1}".format(value_access_control_partial,
                                              message)
        raise arcpy.ExecuteError(msg)

    if value_access_control_no.lower() not in (des.lower()
                                               for des in dom_code.values()):
        message = "is only accepted for No Access Control description"
        msg = "Description: '{0}' {1}".format(value_access_control_no, message)
        raise arcpy.ExecuteError(msg)

    ftrclass_median = arcpy.GetParameterAsText(8)
    field_median_info = arcpy.GetParameterAsText(9)
    workspace = get_workspace(ftrclass_median)
    field = get_field_object(ftrclass_median, field_median_info)
    dom_code = get_domain_values(workspace, field.domain)

    if len(dom_code.keys()) != 2:
        msg = "Domain to denote Medians must contain two coded values"
        raise arcpy.ExecuteError(msg)

    if value_median_divided.lower() not in (des.lower()
                                            for des in dom_code.values()):
        message = "is only accepted for Divided Roadway description"
        msg = "Description: '{0}' {1}".format(value_median_divided, message)
        raise arcpy.ExecuteError(msg)

    if value_median_undivided.lower() not in (des.lower()
                                              for des in dom_code.values()):
        message = "is only accepted for Undivided Roadway description"
        msg = "Description: '{0}' {1}".format(value_median_undivided, message)
        raise arcpy.ExecuteError(msg)

    ftrclass_travel_lanes = arcpy.GetParameterAsText(10)
    field_travel_lanes_info = arcpy.GetParameterAsText(11)
    ftrclass_area_type = arcpy.GetParameterAsText(12)
    field_area_type_info = arcpy.GetParameterAsText(13)

    workspace = get_workspace(ftrclass_area_type)
    field = get_field_object(ftrclass_area_type, field_area_type_info)
    dom_code = get_domain_values(workspace, field.domain)

    if len(dom_code.keys()) != 2:
        msg = "Domain to denote Area Type must contain two coded values"
        raise arcpy.ExecuteError(msg)

    if value_area_type_urban.lower() not in (des.lower()
                                             for des in dom_code.values()):
        message = "is only accepted for Urban Area description"
        msg = "Description: '{0}' {1}".format(value_area_type_urban, message)
        raise arcpy.ExecuteError(msg)

    if value_area_type_rural.lower() not in (des.lower()
                                             for des in dom_code.values()):
        message = "is only accepted for Rural Area description"
        msg = "Description: '{0}' {1}".format(value_area_type_rural, message)
        raise arcpy.ExecuteError(msg)

    ftrclass_speed_limit = arcpy.GetParameterAsText(14)
    field_speed_limit_info = arcpy.GetParameterAsText(15)
    ftrclass_aadt_multi_layers = arcpy.GetParameter(16)
    field_aadt_multi_layers_value = arcpy.GetParameterAsText(17)
    output_folder = arcpy.GetParameterAsText(18)

    try:
        max_val = 9 + len(ftrclass_aadt_multi_layers)
        arcpy.SetProgressor("step", "Initializing...", 0, max_val, 1)
        msg = "Preparing output workspace"
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
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
            fc_baseline = arcpy.MakeFeatureLayer_management(ftrclass_route,
                                                            'baseline_selected')
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
            baseline_selected = arcpy.SelectLayerByAttribute_management(\
                                                            fc_baseline,
                                                            'NEW_SELECTION',
                                                            where)
        # set label to notify user if no route type is selected
        if len(value_route_type) == 0:
            msg = "No route type selected. Taking all route types for analysis."
            arcpy.SetProgressorLabel(msg)
            arcpy.AddMessage(msg)
        if not baseline_selected:
            baseline_selected = ftrclass_route
        arcpy.SetProgressorPosition()

        # combine attributes of simple route and county
        fc_name = os.path.basename(ftrclass_county)
        msg = "Combining {0} into baseline".format(fc_name)
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
        baseline_selected = combine_attributes(baseline_selected,
                                               ftrclass_county,
                                               field_county_name,
                                               USRAP_COUNTY)
        arcpy.SetProgressorPosition()

        # combine attributes of identity result and access control
        fc_name = os.path.basename(ftrclass_access_control)
        msg = "Combining {0} into baseline".format(fc_name)
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
        baseline_selected = combine_attributes(baseline_selected,
                                               ftrclass_access_control,
                                               field_access_control_info,
                                               USRAP_ACCESS_CONTROL)
        arcpy.SetProgressorPosition()

        # combine attributes of identity result and medians
        fc_name = os.path.basename(ftrclass_median)
        msg = "Combining {0} into baseline".format(fc_name)
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
        baseline_selected = combine_attributes(baseline_selected,
                                               ftrclass_median,
                                               field_median_info,
                                               USRAP_MEDIAN)
        arcpy.SetProgressorPosition()
        # combine attributes of identity result and travel lanes
        fc_name = os.path.basename(ftrclass_travel_lanes)
        msg = "Combining {0} into baseline".format(fc_name)
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
        baseline_selected = combine_attributes(baseline_selected,
                                               ftrclass_travel_lanes,
                                               field_travel_lanes_info,
                                               USRAP_LANES)
        arcpy.SetProgressorPosition()
        # combine attributes of identity result and area type
        fc_name = os.path.basename(ftrclass_area_type)
        msg = "Combining {0} into baseline".format(fc_name)
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
        baseline_selected = combine_attributes(baseline_selected,
                                               ftrclass_area_type,
                                               field_area_type_info,
                                               USRAP_AREA_TYPE)
        arcpy.SetProgressorPosition()
        # combine attributes of identity result and speed limit
        # and save the usrap segment feature class to gdb
        fc_name = os.path.basename(ftrclass_speed_limit)
        msg = "Combining {0} into baseline".format(fc_name)
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
        baseline_selected = combine_attributes(baseline_selected,
                                               ftrclass_speed_limit,
                                               field_speed_limit_info,
                                               USRAP_SPEED_LIMIT)
        arcpy.SetProgressorPosition()

        if len(ftrclass_aadt_multi_layers) > 0:
            # combine attributes of identity result and AADT
            new_fields = []
            for ftr in ftrclass_aadt_multi_layers:
                fc_name = os.path.basename(ftr.value)
                msg = "Combining {0} into baseline".format(fc_name)
                arcpy.SetProgressorLabel(msg)
                arcpy.AddMessage(msg)
                new_field = USRAP_AADT_YYYY + '_' + \
                            os.path.basename(ftr.value)[-4:]

                new_fields.append(new_field)
                seg_name = None
                out_gdb = None
                if ftr == ftrclass_aadt_multi_layers[-1]:
                    seg_name = OUTPUT_SEGMENT_NAME
                    out_gdb = output_folder

                baseline_selected = combine_attributes(baseline_selected,
                                                       ftr.value,\
                                                field_aadt_multi_layers_value,
                                                       new_field,
                                                       seg_name,
                                                       out_gdb)
                arcpy.SetProgressorPosition()

            # calculate the average of all supplied years of AADT
            msg = "Calculating average AADT for each segment"
            arcpy.SetProgressorLabel(msg)
            arcpy.AddMessage(msg)
            baseline_selected = calculate_average(baseline_selected,
                                                  new_fields,
                                                  USRAP_AVG_AADT)
            arcpy.SetProgressorPosition()
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
                                                value_access_control_partial]},
                        {USRAP_AREA_TYPE: value_area_type_rural,
                         USRAP_LANES: MORE_THAN_2_LANES,
                         USRAP_MEDIAN: value_median_undivided,
                         USRAP_ACCESS_CONTROL: [value_access_control_no,
                                                value_access_control_partial]},
                        {USRAP_AREA_TYPE: value_area_type_rural,
                         USRAP_LANES: MORE_THAN_2_LANES,
                         USRAP_MEDIAN: value_median_divided,
                         USRAP_ACCESS_CONTROL: [value_access_control_no,
                                                value_access_control_partial]},
                        {USRAP_AREA_TYPE: value_area_type_rural,
                         USRAP_LANES: MORE_THAN_2_LANES,
                         USRAP_MEDIAN: value_median_divided,
                         USRAP_ACCESS_CONTROL: [value_access_control_full]},
                        {USRAP_AREA_TYPE: value_area_type_urban,
                         USRAP_LANES: EQUAL_TO_2_LANES,
                         USRAP_MEDIAN: value_median_undivided,
                         USRAP_ACCESS_CONTROL: [value_access_control_no,
                                                value_access_control_partial]},
                        {USRAP_AREA_TYPE: value_area_type_urban,
                         USRAP_LANES: MORE_THAN_2_LANES,
                         USRAP_MEDIAN: value_median_undivided,
                         USRAP_ACCESS_CONTROL: [value_access_control_no,
                                                value_access_control_partial]},
                        {USRAP_AREA_TYPE: value_area_type_urban,
                         USRAP_LANES: MORE_THAN_2_LANES,
                         USRAP_MEDIAN: value_median_divided,
                         USRAP_ACCESS_CONTROL: [value_access_control_no,
                                                value_access_control_partial]},
                        {USRAP_AREA_TYPE: value_area_type_urban,
                         USRAP_LANES: MORE_THAN_2_LANES,
                         USRAP_MEDIAN: value_median_divided,
                         USRAP_ACCESS_CONTROL: [value_access_control_full]}]

        # baseline segment will be identified as usrap segment
        msg = "Identifying USRAP segments..."
        arcpy.SetProgressorLabel(msg)
        arcpy.AddMessage(msg)
        baseline_selected = identify_usrap_segment(baseline_selected,
                                                   roadway_type)
        # delete duplicate records
        fields = [f.name for f in arcpy.ListFields(baseline_selected)
                  if f.type != "OID"]
        baseline_selected = arcpy.DeleteIdentical_management(baseline_selected,
                                                             fields)

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

        arcpy.ResetProgressor()

        max_val = int(arcpy.GetCount_management(baseline_selected)[0])
        msg = '{0} segments present after combining attributes'.format(max_val)
        arcpy.AddMessage(msg)
        msg = "Merging features... this may take a while"
        arcpy.AddMessage(msg)
        arcpy.SetProgressorLabel(msg)

        layer = arcpy.MakeFeatureLayer_management(baseline_selected, 'layer')

        usrap_where = "{0} = 'YES'".format(USRAP_SEGMENT)
        usrap_segments = arcpy.SelectLayerByAttribute_management(
            layer, 'NEW_SELECTION', usrap_where)
        usrap_count = int(arcpy.GetCount_management(usrap_segments)[0])
        arcpy.SelectLayerByAttribute_management(layer, 'CLEAR_SELECTION')

        # variables for progressor and message
        stepper = 0
        lower = 10

        arcpy.SetProgressor('step', msg, 0, usrap_count, 1)
        # collect field names on which conditions would be checked
        fields = [field[0] for field in condition]
        # insert required field names
        fields.insert(0, 'OID@')
        fields += [USRAP_SEGMENT, 'SHAPE@']

        global DELETE_OIDS

        where = "{0} <> 'NO'".format(USRAP_SEGMENT)
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
                percent = round(int((stepper/float(usrap_count))*100))
                if lower <= percent < 100:
                    arcpy.AddMessage('Merging completed {0}%'.format(lower))
                    lower += 10
                arcpy.SetProgressorPosition(stepper)

        arcpy.AddMessage('Merging completed {0}%'.format('100'))
        merged_count = int(arcpy.GetCount_management(baseline_selected)[0])
        diff = max_val - merged_count
        arcpy.AddMessage('{0} are merged out of {1} segments'.format(diff,
                                                                     max_val))

        # Add USRAP_SEGID to usrap_route feature class
        arcpy.ResetProgressor()
        msg = "Assigning USRAP_SEGID to segments"
        arcpy.AddMessage(msg)
        arcpy.SetProgressor('step', msg, 0, 2, 1)
        baseline_selected = add_segids(layer, USRAP_SEGID)
        arcpy.SetProgressorPosition()

        # copy the rest of data when partial road types are selected for
        # analysis
        if fc_baseline:
            arcpy.SetProgressorLabel("copying non-usrap segments to output")
            baseline_invert_selected = arcpy.SelectLayerByAttribute_management(
                fc_baseline, 'SWITCH_SELECTION')
            arcpy.Append_management(baseline_invert_selected, baseline_selected,
                                    'NO_TEST')
            arcpy.AddMessage(int(arcpy.GetCount_management(\
                             baseline_selected)[0]))
        arcpy.SetProgressorPosition()

    except Exception as error:
        arcpy.AddError(str(error))

    finally:
        # ensure the in_memory workspace is cleared to free up memory
        arcpy.Delete_management("in_memory")
        arcpy.ResetProgressor()

if __name__ == '__main__':
    main()
