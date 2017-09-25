import arcpy, os, sys, numpy, datetime


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Crash Analysis"
        self.alias = "crash"

        # List of tool classes associated with this toolbox
        self.tools = [HighInjuryNetwork]


class HighInjuryNetwork(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate High Injury Network"
        self.description = ""
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Input Crashes",
            name="input_crashes",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        param0.filter.list = ["Point"]

        param1 = arcpy.Parameter(
            displayName="Time Range",
            name="time_range",
            datatype="GPTimeUnit",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        param1.filter.list = ['Days', 'Weeks', 'Years']
        param1.value = 'Years'

        param2 = arcpy.Parameter(
            displayName="Weight Field",
            name="weight_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input",
            multiValue=False)
        param2.parameterDependencies = [param0.name]
        param2.filter.list = ['Short', 'Long', 'Single', 'Double', 'Text']

        param3 = arcpy.Parameter(
            displayName="Weight Table",
            name="weight_table",
            datatype="GPValueTable",
            parameterType="Optional",
            direction="Input",
            multiValue=False)
        param3.enabled = False
        param3.parameterDependencies = [param0.name]
        param3.columns = [['GPString', 'Value'], ['GPDouble', 'Weight']]

        param4 = arcpy.Parameter(
            displayName="Streets or Intersections",
            name="streets_intersections",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        param4.filter.list = ["Point", "Multipoint", "Polyline"]

        param5 = arcpy.Parameter(
            displayName="Snap Distance",
            name="snap_distance",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input",
            multiValue=False)
        param5.filter.list = ['Feet', 'Meters']
        param5.value = 'Feet'

        param6 = arcpy.Parameter(
            displayName="Average Daily Traffic",
            name="adt_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input",
            multiValue=False)
        param6.parameterDependencies = [param4.name]
        param6.filter.list = ['Short', 'Long', 'Single', 'Double']

        param7 = arcpy.Parameter(
            displayName="Output High Injury Network",
            name="output_high_injury_network",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
            multiValue=False)

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
                
        if not parameters[2].hasBeenValidated:
            if parameters[2].value:
                unique_values = []
                field_name = parameters[2].valueAsText
                features = parameters[0].valueAsText

                for field in arcpy.Describe(features).fields:
                    if field.name == field_name:                
                        if field.domain is not None and field.domain != '':
                            database = self.get_workspace(features)
                            if database is not None:
                                for domain in arcpy.da.ListDomains(database):
                                    if domain.name == field.domain:
                                        if domain.domainType == 'CodedValue':
                                            unique_values = [value for key, value in domain.codedValues.items()]
                                        break
                        if len(unique_values) == 0:
                            unique_values = sorted(set(row[0] for row in arcpy.da.SearchCursor(features, [field_name]))) 
                        break
        
                table_weights = []
                for i in range(0, len(unique_values)):
                    if i >= 25:
                        break;
                    table_weights.append((str(unique_values[i]), 1.0))
                parameters[3].value = table_weights
                parameters[3].enabled = True
            else:
                parameters[3].value = None
                parameters[3].enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def get_workspace(self, feature_class):
        """ Return workspace for provided feature class """
        try:
            desc= arcpy.Describe(feature_class)
            if hasattr(desc, 'featureClass'):
                feature_class = desc.featureClass.catalogPath
            if arcpy.Describe(os.path.dirname(feature_class)).dataType != 'Workspace':
                return self.get_workspace(os.path.dirname(feature_class))
            return os.path.dirname(feature_class)
        except:
            return None

    def execute(self, parameters, messages):
        """The source code of the tool."""

        scratch_datasets = []
        new_fields = ['Crash_Count', 'Crash_Count_Weight', 'Crash_Frequency', 'Crash_Rate', 'Weighted_Crash_Frequency', 'Weighted_Crash_Rate']

        try:
            crashes = parameters[0].valueAsText
            time_interval, time_unit = parameters[1].valueAsText.split(' ')
            time_interval = float(time_interval)
            if time_unit == 'Years':
                time_interval = time_interval * 365
            elif time_unit == 'Weeks':
                time_interval = time_interval * 7
            weight_field = parameters[2].valueAsText
            weight_table = parameters[3].value
            streets_intersection = parameters[4].valueAsText
            snap_distance = parameters[5].valueAsText
            adt_field = parameters[6].valueAsText
            high_injury_network = parameters[7].valueAsText
            shape_type = arcpy.Describe(streets_intersection).shapeType

            weight_provided = False
            if weight_field is not None and weight_field != '':
                weight_provided = True

            adt_provided = False
            if adt_field is not None and adt_field != '':
                adt_provided = True

            arcpy.SetProgressorLabel("Creating Temp Crash Layer...")
            arcpy.MakeFeatureLayer_management(crashes, "Crash Layer")
            crashes_snap = os.path.join(arcpy.env.scratchGDB, "Crash_Snap")
            if arcpy.Exists(crashes_snap):
                arcpy.Delete_management(crashes_snap)
            arcpy.CopyFeatures_management("Crash Layer", crashes_snap)
            scratch_datasets.append(crashes_snap)
            
            crash_count_field = new_fields[0]
            crash_count_weight_field = new_fields[1]
            arcpy.AddField_management(crashes_snap, crash_count_field, "Double", field_alias="Crash Count")       
            fields = [crash_count_field]
            if weight_provided:
                arcpy.AddField_management(crashes_snap, crash_count_weight_field, "Double", field_alias="Crash Count Weight")
                fields.append(crash_count_weight_field)               
                fields.append(weight_field)
                for field in arcpy.Describe(crashes).fields:
                    if field.name == weight_field:                
                        if field.domain is not None and field.domain != '':
                            database = self.get_workspace(crashes)
                            if database is not None:
                                for domain in arcpy.da.ListDomains(database):
                                    if domain.name == field.domain:
                                        if domain.domainType == 'CodedValue':
                                            for key, value in domain.codedValues.items():
                                                for weight_row in weight_table:
                                                    if weight_row[0] == value:
                                                        weight_row[0] = str(key)
                                        break

            with arcpy.da.UpdateCursor(crashes_snap, fields) as cursor:
                for row in cursor:
                    row[0] = 1.0
                    if len(fields) == 3:
                        value = str(row[2])
                        for weight_row in weight_table:
                            if value == weight_row[0]:
                                row[1] = weight_row[1]
                                break
                    cursor.updateRow(row)
           
            if (shape_type == "Polyline"):
                arcpy.SetProgressorLabel("Snapping Crashes to Nearest Street...")
            else:
                arcpy.SetProgressorLabel("Snapping Crashes to Nearest Intersection...")        
            snapEnv = [streets_intersection, "EDGE", snap_distance]
            arcpy.Snap_edit(crashes_snap, [snapEnv])   

            fms = arcpy.FieldMappings()
            desc = arcpy.Describe(streets_intersection)
            for field in desc.fields:
                if field.type == 'Geometry' or field.type == 'OID' or field.name in new_fields:
                    continue
                if shape_type == "Polyline" and field.name == desc.AreaFieldName:
                    continue
                fm = arcpy.FieldMap()  
                fm.addInputField(streets_intersection, field.name)
                fms.addFieldMap(fm)
            fm = arcpy.FieldMap()  
            fm.addInputField(crashes_snap, crash_count_field)
            fm.mergeRule = 'Sum'
            fms.addFieldMap(fm)
            if weight_provided:
                fm = arcpy.FieldMap()  
                fm.addInputField(crashes_snap, crash_count_weight_field)
                fm.mergeRule = 'Sum'
                fms.addFieldMap(fm)

            crashes_join = os.path.join(arcpy.env.scratchGDB, "Crash")
            if arcpy.Exists(crashes_join):
                arcpy.Delete_management(crashes_join)
            arcpy.SpatialJoin_analysis(streets_intersection, crashes_snap, crashes_join, "JOIN_ONE_TO_ONE", "KEEP_ALL", fms, "Intersect", "0 Feet" )        
            scratch_datasets.append(crashes_join)

            if weight_provided:
                with arcpy.da.UpdateCursor(crashes_join, [crash_count_weight_field]) as cursor:
                    for row in cursor:
                        if row[0] == 0:
                            row[0] = None
                        cursor.updateRow(row)

            arcpy.SetProgressorLabel("Calculating Crash Statistics")
            templateDir = os.path.dirname(__file__)
            crash_frequency_field = new_fields[2]   
            crash_rate_field = new_fields[3] 
            weighted_crash_frequency_field = new_fields[4] 
            weighted_crash_rate_field = new_fields[5]
            
            add_fields = []
            fields = [crash_count_field]

            if (shape_type == "Polyline"):
                fields.append('SHAPE@')
                parameters[7].symbology = os.path.join(templateDir, "HighInjuryNetworkPolylines.lyrx")      
                add_fields = [[crash_frequency_field, "Crashes Per Mile Per Year"], [crash_rate_field, "Crashes Per Million Vehicle Miles"],
                              [weighted_crash_frequency_field, "Weighted Crashes Per Mile Per Year"], [weighted_crash_rate_field, "Weighted Crashes Per Million Vehicle Miles"]] 
            else:
                parameters[7].symbology = os.path.join(templateDir, "HighInjuryNetworkPoints.lyrx")
                add_fields = [[crash_frequency_field, "Crashes Per Year"], [crash_rate_field, "Crashes Per Million Entering Vehicles"],
                              [weighted_crash_frequency_field, "Weighted Crashes Per Year"], [weighted_crash_rate_field, "Weighted Crashes Per Million Entering Vehicles"]] 

            arcpy.AddField_management(crashes_join, add_fields[0][0], "Double", field_alias=add_fields[0][1])
            fields.append(add_fields[0][0])
            if adt_provided:
                arcpy.AddField_management(crashes_join, add_fields[1][0], "Double", field_alias=add_fields[1][1])
                fields.append(add_fields[1][0])
                fields.append(adt_field)
            if weight_provided:
                fields.append(crash_count_weight_field)
                arcpy.AddField_management(crashes_join, add_fields[2][0], "Double", field_alias=add_fields[2][1])
                fields.append(add_fields[2][0])
                if adt_provided:
                    arcpy.AddField_management(crashes_join, add_fields[3][0], "Double", field_alias=add_fields[3][1])
                    fields.append(add_fields[3][0])

            with arcpy.da.UpdateCursor(crashes_join, fields) as cursor:
                for row in cursor:
                    if row[cursor.fields.index(crash_count_field)] is None:
                        continue
                    
                    miles = 1.0
                    if 'SHAPE@' in cursor.fields:
                        miles = row[cursor.fields.index('SHAPE@')].getLength('GEODESIC', 'MILES')
                    row[cursor.fields.index(crash_frequency_field)] = row[cursor.fields.index(crash_count_field)] / ((time_interval / 365) * miles)

                    if crash_count_weight_field in cursor.fields and row[cursor.fields.index(crash_count_weight_field)] is not None:
                           row[cursor.fields.index(weighted_crash_frequency_field)] = row[cursor.fields.index(crash_count_weight_field)] / ((time_interval / 365) * miles)

                    if adt_field in cursor.fields and row[cursor.fields.index(adt_field)] is not None:
                        row[cursor.fields.index(crash_rate_field)] = (row[cursor.fields.index(crash_count_field)] * 1000000) / (time_interval  * row[cursor.fields.index(adt_field)] * miles)
                        if crash_count_weight_field in cursor.fields and row[cursor.fields.index(crash_count_weight_field)] is not None:
                            row[cursor.fields.index(weighted_crash_rate_field)] = (row[cursor.fields.index(crash_count_weight_field)] * 1000000) / (time_interval  * row[cursor.fields.index(adt_field)] * miles)
                    cursor.updateRow(row)
            
            arcpy.SetProgressorLabel("Generating High Injury Network...")
            field_info = ""
            fields_to_hide = ['Join_Count', 'TARGET_FID', new_fields[0]]
            if weight_provided:
                fields_to_hide.append(new_fields[1])
            field_list = arcpy.ListFields(crashes_join)  
            for field in field_list:  
                if field.name in fields_to_hide:  
                    field_info = "{0}{1} {1} HIDDEN;".format(field_info, field.name)
                else:  
                    field_info = "{0}{1} {1} VISIBLE;".format(field_info, field.name)
            arcpy.MakeFeatureLayer_management(crashes_join, "High Injury Network", field_info=field_info[:-1])
            arcpy.SelectLayerByAttribute_management("High Injury Network", "NEW_SELECTION", '{0} IS NOT NULL'.format(new_fields[2]))
            arcpy.CopyFeatures_management("High Injury Network", high_injury_network)            

        finally:
            for dataset in scratch_datasets:
                if arcpy.Exists(dataset):
                    arcpy.Delete_management(dataset)
