import arcpy, os, sys, decimal

#existing fields expected from input segments
USRAP_SEGMENT_FIELDNAME = "USRAP_SEGMENT"
CRASH_COUNT_FIELDNAME = "TOTAL_CRASH"
USRAP_AADT_YYYY = "USRAP_AADT_*"
USRAP_AVG_AADT_FIELDNAME = "USRAP_AVG_AADT"
USRAP_ROADWAY_TYPE_FIELDNAME = "USRAP_ROADWAY_TYPE"
USRAP_COUNTY_FIELDNAME = "USRAP_COUNTY"

#new fields to be added to segments for calcs
CRASH_DENSITY_FIELDNAME = "CRASH_DENSITY"
CRASH_RATE_FIELDNAME = "CRASH_RATE"
CRASH_RATE_RATIO_FIELDNAME = "CRASH_RATE_RATIO"
CRASH_POTENTIAL_SAVINGS_FIELDNAME = "POTENTIAL_CRASH_SAVINGS"
CRASH_CALC_FIELDS = [CRASH_DENSITY_FIELDNAME, CRASH_RATE_FIELDNAME, CRASH_RATE_RATIO_FIELDNAME, CRASH_POTENTIAL_SAVINGS_FIELDNAME]

SUMMARY_TABLE_NAME = "SummaryTable"

#new fields to be added for Summary table
SUMMARY_ROADWAY_TYPE_FIELDNAME = "ROADWAY_TYPE"
SUMMARY_SEGMENT_COUNT_FIELDNAME = "NUMBER_OF_SEGMENTS"
SUMMARY_TOTAL_LENGTH_FIELDNAME = "TOTAL_LENGTH"
SUMMARY_AVG_LENGTH_FIELDNAME = "AVG_LENGTH"
SUMMARY_AVG_AADT_FIELDNAME = "AVG_AADT"
SUMMARY_TOTAL_FREQ_FIELDNAME = "TOTAL_FREQUENCY"
SUMMARY_ANNUAL_FREQ_FIELDNAME = "ANNUAL_FREQUENCY"
SUMMARY_ANNUAL_DENSITY_FIELDNAME = "ANNUAL_DENSITY"
SUMMARY_AVG_RATE_FIELDNAME = "AVG_RATE"
SUMMARY_FIELDS = [SUMMARY_ROADWAY_TYPE_FIELDNAME, SUMMARY_SEGMENT_COUNT_FIELDNAME, SUMMARY_TOTAL_LENGTH_FIELDNAME,
                  SUMMARY_AVG_LENGTH_FIELDNAME, SUMMARY_AVG_AADT_FIELDNAME, SUMMARY_TOTAL_FREQ_FIELDNAME,
                  SUMMARY_ANNUAL_FREQ_FIELDNAME, SUMMARY_ANNUAL_DENSITY_FIELDNAME, SUMMARY_AVG_RATE_FIELDNAME]

SEG_SUMMARY_TABLE_NAME = "SegmentBySegmentSummary"

#risk level assignment
RISK_LEVEL_CATEGORIES = { 0: ["Lowest risk", 40], 1: ["Medium-low risk", 25], 2: ["Medium risk", 20], 3: ["Medium-high risk", 10], 4:["Highest risk", 5]}
CRASH_DENSITY_RISK_CATEGORY_FIELDNAME = "CRASH_DENSITY_RISK"
CRASH_RATE_RISK_CATEGORY_FIELDNAME = "CRASH_RATE_RISK"
CRASH_RATE_RATIO_RISK_CATEGORY_FIELDNAME = "CRASH_RATE_RATIO_RISK"
CRASH_POTENTIAL_SAVINGS_RISK_CATEGORY_FIELDNAME = "POTENTIAL_CRASH_SAVINGS_RISK"
RISK_FIELDS = [CRASH_DENSITY_RISK_CATEGORY_FIELDNAME, CRASH_RATE_RISK_CATEGORY_FIELDNAME, 
               CRASH_RATE_RATIO_RISK_CATEGORY_FIELDNAME, CRASH_POTENTIAL_SAVINGS_RISK_CATEGORY_FIELDNAME]

#lookup dict to map value field to risk category field
RISK_FIELD_VALUE_FIELD_FIELDS = { CRASH_DENSITY_FIELDNAME: CRASH_DENSITY_RISK_CATEGORY_FIELDNAME,
                                 CRASH_RATE_FIELDNAME: CRASH_RATE_RISK_CATEGORY_FIELDNAME,
                                 CRASH_RATE_RATIO_FIELDNAME: CRASH_RATE_RATIO_RISK_CATEGORY_FIELDNAME,
                                 CRASH_POTENTIAL_SAVINGS_FIELDNAME: CRASH_POTENTIAL_SAVINGS_RISK_CATEGORY_FIELDNAME}

crash_rate_for_road_type = {}

def add_fields(layer, fields, type, scale):
    """
    This function will add a new field with the defined name if it does not exist
    """
    current_fields = arcpy.ListFields(layer)
    current_field_names = [f.name for f in current_fields]
    for field in fields:
        if field not in current_field_names:
            if scale:
                arcpy.AddField_management(layer, field, type, field_scale=scale)
            else:
                arcpy.AddField_management(layer, field, type)
        #TODO elif verify if the field type matches...if it does not add
        # a new field with the correct type and a new name and broadcast this to the user

def calculate_density_and_rate(layer, fields, number_of_years_in_study):
    """
    This function calculates crash density, crash rate, and overall USRAP road network length.
    This function also determines the summary table values
    """
    arcpy.AddMessage("Calculating {0} and {1} for analysis segments".format(CRASH_DENSITY_FIELDNAME, CRASH_RATE_FIELDNAME))

    previous_roadway_type = ""
    num_segments = 0
    sum_length = 0
    sum_avg_aadt = 0
    sum_crashes = 0
    sum_density = 0
    sum_crash_rate = 0
    sum_vh_miles = 0
    overall_length = 0

    summary_table_values = {}

    crash_count_index = fields.index(CRASH_COUNT_FIELDNAME)
    avg_aadt_index = fields.index(USRAP_AVG_AADT_FIELDNAME)
    roadway_type_index = fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)
    crash_density_index = fields.index(CRASH_DENSITY_FIELDNAME)
    crash_rate_index = fields.index(CRASH_RATE_FIELDNAME)

    with arcpy.da.UpdateCursor(layer, fields, sql_clause=(None, 'ORDER BY ' + USRAP_ROADWAY_TYPE_FIELDNAME + " ASC")) as update_cursor:
        for row in update_cursor: 
            # Crash Density = (# of Crashes)/(Length of Segment)
            num_crashes = round(decimal.Decimal(row[crash_count_index]), 5)
            length = round(decimal.Decimal(row[-1]),5)
            crash_density = num_crashes / length
            row[fields.index(CRASH_DENSITY_FIELDNAME)] = crash_density

            #Crash Rate = ((# of Crashes)*100,000,000)/
            # ((Length of Segment)*(AADT)*(# of days in year)*(# of years in study)))
            aadt = round(decimal.Decimal(row[avg_aadt_index]),5)
            num_days_in_year = 365
            crash_rate = (num_crashes*100000000)/(length * aadt * num_days_in_year * number_of_years_in_study)
            row[fields.index(CRASH_RATE_FIELDNAME)] = crash_rate

            update_cursor.updateRow(row)

            #Create crash rate ratio value dict
            current_roadway_type = row[roadway_type_index]

            if previous_roadway_type == "":
                previous_roadway_type = current_roadway_type

            if previous_roadway_type != current_roadway_type:
                crash_rate_for_road_type[str(previous_roadway_type)] = (sum_crashes*100000000) / sum_vh_miles

                avg_length = sum_length / num_segments
                avg_aadt_by_type = sum_avg_aadt / num_segments
                total_freq = sum_crashes
                annual_freq_per_seg = (total_freq / num_segments)/ number_of_years_in_study
                annual_density_per_mile = (sum_density/num_segments) / number_of_years_in_study
                avg_rate = sum_crash_rate / num_segments
                summary_table_values[str(previous_roadway_type)] = [num_segments, sum_length,
                                                                avg_length, avg_aadt_by_type,
                                                                total_freq, annual_freq_per_seg,
                                                                annual_density_per_mile, avg_rate]
                previous_roadway_type = current_roadway_type
                #reset counters
                sum_length = 0
                num_segments = 0
                sum_avg_aadt = 0
                sum_crashes = 0
                sum_density = 0
                sum_crash_rate = 0
                sum_vh_miles = 0

            #increment the counter and summerization values
            num_segments += 1
            length = round(decimal.Decimal(row[-1]),5)
            sum_length += length
            sum_avg_aadt += round(decimal.Decimal(row[avg_aadt_index]),5)
            sum_crashes += round(decimal.Decimal(row[crash_count_index]),5)
            sum_density += round(decimal.Decimal(row[crash_density_index]),5)
            sum_crash_rate += round(decimal.Decimal(row[crash_rate_index]),5)
            sum_vh_miles += length * aadt * num_days_in_year * number_of_years_in_study
            overall_length += length
    return summary_table_values, crash_rate_for_road_type, overall_length

def calculate_ratio_and_potential_crash_savings(layer, fields, crash_rate_for_road_type, number_of_years_in_study):
    """
    This function calculates crash rate ratio and potential crash savings
    """
    arcpy.AddMessage("Calculating {0} and {1} for analysis segments".format(CRASH_RATE_RATIO_FIELDNAME, CRASH_POTENTIAL_SAVINGS_FIELDNAME))

    #get all of the field indexs up front
    crash_density_index = fields.index(CRASH_DENSITY_FIELDNAME)
    crash_rate_index = fields.index(CRASH_RATE_FIELDNAME)
    crash_rate_ratio_index = fields.index(CRASH_RATE_RATIO_FIELDNAME)
    potential_crash_savings_index = fields.index(CRASH_POTENTIAL_SAVINGS_FIELDNAME)
    roadway_type_index = fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)
    avg_aadt_index = fields.index(USRAP_AVG_AADT_FIELDNAME)

    with arcpy.da.UpdateCursor(layer, fields) as update_cursor:
        for row in update_cursor:        
            crash_rate = round(decimal.Decimal(row[crash_rate_index]),5)

            current_roadway_type = row[roadway_type_index]

            if crash_rate_for_road_type.keys().count(current_roadway_type) > 0:
                avg_crash_rate = round(decimal.Decimal(crash_rate_for_road_type[current_roadway_type]),5)

                crash_rate_ratio = crash_rate / avg_crash_rate
                row[crash_rate_ratio_index] = crash_rate_ratio

                cr_diff = crash_rate - avg_crash_rate
                aadt = round(decimal.Decimal(row[avg_aadt_index]),5)
                num_days_in_year = 365

                potential_crash_savings = (cr_diff * aadt * num_days_in_year * number_of_years_in_study)/100000000

                row[potential_crash_savings_index] = potential_crash_savings
                update_cursor.updateRow(row)

def calculate_risk_values(layer):
    """
    This function adds required fields and then calls the two calculate functions
    """
    #get number of years in study
    number_of_years_in_study = len(arcpy.ListFields(layer, USRAP_AADT_YYYY))

    #add fields for crash density, rate, ratio, and potential crash savings values 
    add_fields(layer, CRASH_CALC_FIELDS, "DOUBLE", 6)

    #key fields for calculations and results
    fields = [CRASH_DENSITY_FIELDNAME, CRASH_RATE_FIELDNAME, 
              CRASH_COUNT_FIELDNAME, USRAP_AVG_AADT_FIELDNAME, 
              CRASH_RATE_RATIO_FIELDNAME, USRAP_ROADWAY_TYPE_FIELDNAME,
              CRASH_POTENTIAL_SAVINGS_FIELDNAME, "SHAPE@LENGTH" ]

    #summary_table_values: data for final summary table see pg. ? whitepaper
    #summary_table_values: {key:value}
    #crash_rate_for_road_type: summarized values by roadway type
    #crash_rate_for_road_type: {key:[values]}
    summary_table_values, crash_rate_for_road_type, overall_length = calculate_density_and_rate(layer, fields, number_of_years_in_study)

    #risk_threshold_values = calculate_ratio_and_potential_crash_savings(layer, fields, crash_rate_for_road_type, number_of_years_in_study)
    calculate_ratio_and_potential_crash_savings(layer, fields, crash_rate_for_road_type, number_of_years_in_study)

    #return summary_table_values, segment_by_segment_summary_values, risk_threshold_values, overall_length, fields
    return summary_table_values, overall_length, fields

def create_summary_tables(layer, summary_table_values, route_name_field):
    """
    This function generates the summary tables as described on pg 16 of whitepaper
    """
    arcpy.AddMessage("Generating and populating final summary tables")

    #Create Summary Table
    # fields must be in the same order as values in summary_table_values
    populate_summary_table(SUMMARY_TABLE_NAME, SUMMARY_FIELDS, summary_table_values)

    #Create seg by seg summary table
    # This is just an export of [Route_Name, County, Mileposts, Roadway_Type, aadt, crash_rate, risk_level fields]
    fields = [route_name_field, USRAP_COUNTY_FIELDNAME, USRAP_ROADWAY_TYPE_FIELDNAME, USRAP_AVG_AADT_FIELDNAME, CRASH_RATE_FIELDNAME]
    fields.extend(RISK_FIELDS)
    arcpy.CopyRows_management(layer, SEG_SUMMARY_TABLE_NAME)
    delete_fields = [f.name for f in arcpy.ListFields(SEG_SUMMARY_TABLE_NAME) if f.name not in fields and f.required != True]
    arcpy.DeleteField_management(SEG_SUMMARY_TABLE_NAME, ";".join(delete_fields))

def populate_summary_table(table_name, fields, summary_table_values):
    """
    Helper function to update the summary table with the provided values
    """
    #create summary table
    table = create_table(table_name, fields)
    #insert the values into the output table
    with arcpy.da.InsertCursor(table, fields) as insert_cursor:
        for v in summary_table_values.items():
            insert_cursor.insertRow([v[0]] + v[1])

def create_table(name, fields):
    """
    Helper function to create the tables
    """
    table = arcpy.CreateTable_management(arcpy.env.workspace, name)
    for field in fields:
        arcpy.AddField_management(str(table), field, "TEXT")
    return table

def percentage(percent, whole):
    """
    Helper function to get <what> percent of whole
    """
    return (percent * whole) / 100.0

def assign_risk_levels(overall_length, fields, layer):  
    """
    This function assigns risk level based on the determined thresholds 
     as described on pg 14 of the whitepaper.  
    """
    #add fields for eash category
    add_fields(layer, RISK_FIELDS, "TEXT", None)
    for f in RISK_FIELDS:
        fields.insert(0, f)

    percentage_lengths = {}

    sum_percentage_length = 0
    for p in RISK_LEVEL_CATEGORIES:
        percent = RISK_LEVEL_CATEGORIES[p][1]
        sum_percentage_length += percentage(percent, overall_length)
        percentage_lengths[p] = sum_percentage_length

    risk_level = -1
    for risk_value_field_name in RISK_FIELD_VALUE_FIELD_FIELDS.keys():
        risk_level += 1
        arcpy.AddMessage("Assigning {0} risk level values".format(risk_value_field_name))
        risk_level_field_index = fields.index(RISK_FIELD_VALUE_FIELD_FIELDS[risk_value_field_name])
        risk_value_field_index = fields.index(risk_value_field_name)

        sum_length = 0
        current_value = None
        previous_value = -9999
        risk_category_index = 0
        #the percentage_lengths list and RISK_LEVEL_CATEGORIES need to be the same length
        # they should represent the percentage breakpoints and text descriptions respectively 
        with arcpy.da.UpdateCursor(layer, fields, sql_clause=(None, 'ORDER BY ' + risk_value_field_name + " ASC")) as update_cursor:           
            for row in update_cursor: 
                length = float(row[-1])
                sum_length += length
                current_value = row[risk_value_field_index]
                if previous_value == -9999:
                    previous_value = current_value

                if sum_length > percentage_lengths[risk_category_index]:
                    if previous_value == current_value:
                        # need to handle tie breakers
                        # if the current value and prevoius value match we need to assign 
                        #the same risk category
                        # however we would also want to be aware if the next categories thresholds 
                        #so we could properly handle a situation where a category is completely skipped
                        # TODO...think about this section more...may want to update the summary table
                        # to indicate that this situation occured
                        temp_next_threshold_value = risk_category_index + 1
                        temp_next_percentage_length = percentage_lengths[temp_next_threshold_value]
                        if sum_length > temp_next_percentage_length:
                            arcpy.AddMessage(RISK_LEVEL_CATEGORIES[risk_category_index + 1][0] + " level has no assigned values")
                    else:
                        #don't increment for the final row otherwise increment to the next category
                        if risk_category_index + 1 < len(RISK_LEVEL_CATEGORIES):
                            risk_category_index += 1
                row[risk_level_field_index] = RISK_LEVEL_CATEGORIES[risk_category_index][0]
                update_cursor.updateRow(row)
                previous_value = current_value

def get_workspace(feature_class):
    """
    Helper function that returns the workspace for the feature class 
    """
    if arcpy.Describe(os.path.dirname(feature_class)).dataType != 'Workspace':
        return get_workspace(os.path.dirname(feature_class))
    return os.path.dirname(feature_class)

def main():
    #inputs from the user
    segments = arcpy.GetParameterAsText(0)
    route_name_field = arcpy.GetParameterAsText(1)

    #get the defined workspace
    arcpy.env.workspace = get_workspace(segments)
    arcpy.env.overwriteOutput = True

    segments_layer = "RiskMapSegments"

    #only process on usRAP segments
    where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELDNAME)
    layer = arcpy.MakeFeatureLayer_management(segments, segments_layer, where)

    #handle the inital 4 calculations 
    summary_table_values, overall_length, fields = calculate_risk_values(layer)

    #assign risk levels after the values have been calculated 
    # and the overall length of the road network is known
    assign_risk_levels(overall_length, fields, layer)

    #Create and populate the summary tables
    create_summary_tables(layer, summary_table_values, route_name_field)

if __name__ == '__main__':
    try:
        main()
    except Exception, ex:
        arcpy.AddError(ex.args)
