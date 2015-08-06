import arcpy, os

#existing fields expected from input segments
USRAP_SEGMENT_FIELDNAME = "USRAP_SEGMENT"
CRASH_COUNT_FIELDNAME = "TOTAL_CRASH"
USRAP_AADT_YYYY = "USRAP_AADT_*"
USRAP_AVG_AADT_FIELDNAME = "USRAP_AVG_AADT"
USRAP_ROADWAY_TYPE_FIELDNAME = "USRAP_ROADWAY_TYPE"

#new fields to be added to segments for calcs
CRASH_DENSITY_FIELDNAME = "CRASH_DENSITY"
CRASH_RATE_FIELDNAME = "CRASH_RATE"
CRASH_RATE_RATIO_FIELDNAME = "CRASH_RATE_RATIO"
CRASH_POTENTIAL_SAVINGS_FIELDNAME = "POTENTIAL_CRASH_SAVINGS"

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

SEG_SUMMARY_TABLE_NAME = "SegmentBySegmentSummary"

#new fields to be added for segment-by-segment summary table
SEG_SUMMARY_ROUTE_FIELDNAME = "ROUTE"
SEG_SUMMARY_COUNTY_FIELDNAME = "COUNTY"
SEG_SUMMARY_MILEPOSTS_FIELDNAME = "MILEPOSTS"
SEG_SUMMARY_ROADWAY_TYPE_FIELDNAME = "ROADWAY_TYPE"
SEG_SUMMARY_AADT_FIELDNAME = "AADT"
SEG_SUMMARY_CRASH_COUNT_FIELDNAME = "CRASHES_PER_100_MILLION"
SEG_SUMMARY_RISK_LEVEL_FIELDNAME = "RISK_LEVEL"

crash_rate_for_road_type = {}

def add_text_fields(layer, fields):
    for field in fields:
        arcpy.AddField_management(layer, field, "TEXT")

def calculate_density_and_rate(layer, fields, number_of_years_in_study):
    previous_roadway_type = ""
    sum = 0
    cnt = 0
    sum_length = 0
    sum_avg_aadt = 0
    sum_crashes = 0
    sum_density = 0
    sum_rate = 0

    summary_table_values = {}
    segment_by_segment_summary_values = {}

    with arcpy.da.UpdateCursor(layer, fields, sql_clause=(None, 'ORDER BY ' + USRAP_ROADWAY_TYPE_FIELDNAME + " ASC")) as update_cursor:
        for row in update_cursor: 
            # Crash Density = (# of Crashes)/(Length of Segment)
            num_crashes = float(row[fields.index(CRASH_COUNT_FIELDNAME)])
            length = float(row[-1])
            crash_density = num_crashes / length
            row[fields.index(CRASH_DENSITY_FIELDNAME)] = crash_density

            #Crash Rate = ((# of Crashes)*100,000,000)/
            # ((Length of Segment)*(AADT)*(# of days in year)*(# of years in study)))
            aadt = float(row[fields.index(USRAP_AVG_AADT_FIELDNAME)])
            num_days_in_year = 365
            crash_rate = (num_crashes*100000000)/(length * aadt * num_days_in_year * number_of_years_in_study)
            row[fields.index(CRASH_RATE_FIELDNAME)] = crash_rate

            update_cursor.updateRow(row)

            #Create crash rate ratio value dict
            current_roadway_type = row[fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)]

            if previous_roadway_type == "":
                previous_roadway_type = current_roadway_type

            if previous_roadway_type != current_roadway_type:
                #not sure this is the correct calculation
                crash_rate_for_road_type[str(previous_roadway_type)] = sum / cnt
                

                num_segments = cnt
                avg_length = sum_length / num_segments
                avg_aadt_by_type = sum_avg_aadt / num_segments
                total_freq = sum_crashes
                annual_freq_per_seg = (total_freq / num_segments)/ number_of_years_in_study
                annual_density_per_mile = (sum_density/num_segments) / number_of_years_in_study
                avg_rate = sum_rate / num_segments
                summary_table_values[str(previous_roadway_type)] = [num_segments, sum_length,
                                                                avg_length, avg_aadt_by_type,
                                                                total_freq, annual_freq_per_seg,
                                                                annual_density_per_mile, avg_rate]
                previous_roadway_type = current_roadway_type
                #reset counters
                sum = 0
                sum_length = 0
                cnt = 0
                sum_avg_aadt = 0
                sum_crashes = 0
                sum_density = 0
                sum_rate = 0

            sum += crash_rate
            cnt += 1
            sum_length += float(row[-1])
            sum_avg_aadt += float(row[fields.index(USRAP_AVG_AADT_FIELDNAME)])
            sum_crashes += float(row[fields.index(CRASH_COUNT_FIELDNAME)])
            sum_density += float(row[fields.index(CRASH_DENSITY_FIELDNAME)])
            sum_rate += float(row[fields.index(CRASH_RATE_FIELDNAME)])
    return summary_table_values, segment_by_segment_summary_values, crash_rate_for_road_type

def calculate_ratio_and_potential_crash_savings(layer, fields, crash_rate_for_road_type, number_of_years_in_study):
    with arcpy.da.UpdateCursor(layer, fields) as update_cursor:
        for row in update_cursor:        
            crash_rate = float(row[fields.index(CRASH_RATE_FIELDNAME)])

            current_roadway_type = row[fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)]

            ########################################
            if crash_rate_for_road_type.keys().count(current_roadway_type) > 0:
                avg_crash_rate = float(crash_rate_for_road_type[current_roadway_type])

                crash_rate_ratio = crash_rate / avg_crash_rate
                row[fields.index(CRASH_RATE_RATIO_FIELDNAME)] = crash_rate_ratio

                cr_diff =  crash_rate - float(crash_rate_for_road_type[current_roadway_type])
                aadt = float(row[fields.index(USRAP_AVG_AADT_FIELDNAME)])
                num_days_in_year = 365

                potential_crash_savings = (cr_diff * aadt * num_days_in_year * number_of_years_in_study)/100000000

                row[fields.index(CRASH_POTENTIAL_SAVINGS_FIELDNAME)] = potential_crash_savings
                update_cursor.updateRow(row)

def calculate_risk_values(layer):
    #get number of years in study
    number_of_years_in_study = len(arcpy.ListFields(layer, USRAP_AADT_YYYY))

    #add fields for crash density, rate, ratio, and potential crash savings values 
    add_text_fields(layer, [CRASH_DENSITY_FIELDNAME, CRASH_RATE_FIELDNAME,
                             CRASH_RATE_RATIO_FIELDNAME, CRASH_POTENTIAL_SAVINGS_FIELDNAME])

    #key fields for calculations and results
    fields = [CRASH_DENSITY_FIELDNAME, CRASH_RATE_FIELDNAME, 
              CRASH_COUNT_FIELDNAME, USRAP_AVG_AADT_FIELDNAME, 
              CRASH_RATE_RATIO_FIELDNAME, USRAP_ROADWAY_TYPE_FIELDNAME,
              CRASH_POTENTIAL_SAVINGS_FIELDNAME, "SHAPE@LENGTH" ]

    #summary_table_values: data for final summary table see pg. ? whitepaper
    #summary_table_values: {key:value}
    #crash_rate_for_road_type: summarized values by roadway type
    #crash_rate_for_road_type: {key:[values]}
    summary_table_values, segment_by_segment_summary_values, crash_rate_for_road_type = calculate_density_and_rate(layer, fields, number_of_years_in_study)

    calculate_ratio_and_potential_crash_savings(layer, fields, crash_rate_for_road_type, number_of_years_in_study)

    return summary_table_values, segment_by_segment_summary_values 

def create_summary_tables(layer, summary_table_values, segment_by_segment_summary_values):
    #pg 16 of whitepaper

    #Create Summary Table
    # fields must be in the same order as values in summary_table_values
    fields = [SUMMARY_ROADWAY_TYPE_FIELDNAME, SUMMARY_SEGMENT_COUNT_FIELDNAME,
              SUMMARY_TOTAL_LENGTH_FIELDNAME, SUMMARY_AVG_LENGTH_FIELDNAME,
              SUMMARY_AVG_AADT_FIELDNAME, SUMMARY_TOTAL_FREQ_FIELDNAME,
              SUMMARY_ANNUAL_FREQ_FIELDNAME, SUMMARY_ANNUAL_DENSITY_FIELDNAME,
              SUMMARY_AVG_RATE_FIELDNAME]

    populate_summary_table(layer, SUMMARY_TABLE_NAME, fields, summary_table_values)

    #Create seg by seg summary table
    # fields must be in the same order as values in segment_by_segment_summary_values
    fields = [SEG_SUMMARY_ROUTE_FIELDNAME, SEG_SUMMARY_COUNTY_FIELDNAME,
              SEG_SUMMARY_MILEPOSTS_FIELDNAME, SEG_SUMMARY_ROADWAY_TYPE_FIELDNAME,
              SEG_SUMMARY_AADT_FIELDNAME, SEG_SUMMARY_CRASH_COUNT_FIELDNAME,
              SEG_SUMMARY_RISK_LEVEL_FIELDNAME]

    populate_summary_table(layer, SEG_SUMMARY_TABLE_NAME, fields, segment_by_segment_summary_values)

def populate_summary_table(layer, table_name, fields, summary_table_values):
    #create summary table
    table = create_table(table_name, fields)
    #insert the values into the output table
    with arcpy.da.InsertCursor(table, fields) as insert_cursor:
        for v in summary_table_values.items():
            insert_cursor.insertRow([v[0]] + v[1])

def create_table(name, fields):
    table = arcpy.CreateTable_management(arcpy.env.workspace, name)
    for field in fields:
        arcpy.AddField_management(str(table), field, "TEXT")
    return table

#def assign_risk_levels():
    #need to understand this still
def get_workspace(feature_class):
    """ returns the workspace for the feature class """
    if arcpy.Describe(os.path.dirname(feature_class)).dataType != 'Workspace':
        return get_workspace(os.path.dirname(feature_class))
    return os.path.dirname(feature_class)

def main():
    ##segments = r"C:\Solutions\CrashTools\VDOT_Data\data_\CrashAssignmentOutput.gdb\SegmentOutput"
    segments = arcpy.GetParameterAsText(0)

    arcpy.env.workspace = get_workspace(segments)
    arcpy.env.overwriteOutput = True

    segments_layer = "RiskMapSegments"

    #only process on usRAP segments
    where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELDNAME)
    layer = arcpy.MakeFeatureLayer_management(segments, segments_layer, where)

    #Handles 4 calculations whose values are written to...
    # Also genrates and populates the summary tables
    summary_table_values, segment_by_segment_summary_values = calculate_risk_values(layer)
    create_summary_tables(layer, summary_table_values, segment_by_segment_summary_values)

if __name__ == '__main__':
    main()
