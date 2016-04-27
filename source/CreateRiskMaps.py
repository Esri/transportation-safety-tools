"""
-------------------------------------------------------------------------------
 | Copyright 2015 Esri
 |
 | Licensed under the Apache License, Version 2.0 (the "License");
 | you may not use this file except in compliance with the License.
 | You may obtain a copy of the License at
 |
 |    http://www.apache.org/licenses/LICENSE-2.0
 |
 | Unless required by applicable law or agreed to in writing, software
 | distributed under the License is distributed on an "AS IS" BASIS,
 | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 | See the License for the specific language governing permissions and
 | limitations under the License.
 ------------------------------------------------------------------------------
 """
import arcpy, os, sys, decimal, time, json, tempfile

#existing fields expected from input segments
USRAP_SEGMENT_FIELDNAME = "USRAP_SEGMENT"
USRAP_SEGMENT_ID_FIELDNAME = "USRAP_SEGID"
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

SUMMARY_TABLE_NAME = "SummaryOfCrashesByRoadwayTypesTable"

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

SEG_SUMMARY_TABLE_NAME = "SegmentBySegmentRiskSummaryTable"

#risk level assignment
RISK_LEVEL_CATEGORIES = { 0: ["Lowest risk", 40], 1: ["Medium-low risk", 25], 2: ["Medium risk", 20], 3: ["Medium-high risk", 10], 4:["Highest risk", 5]}
CRASH_DENSITY_RISK_CATEGORY_FIELDNAME = "CRASH_DENSITY_RISK"
CRASH_RATE_RISK_CATEGORY_FIELDNAME = "CRASH_RATE_RISK"
CRASH_RATE_RATIO_RISK_CATEGORY_FIELDNAME = "CRASH_RATE_RATIO_RISK"
CRASH_POTENTIAL_SAVINGS_RISK_CATEGORY_FIELDNAME = "POTENTIAL_CRASH_SAVINGS_RISK"
RISK_FIELDS = [CRASH_DENSITY_RISK_CATEGORY_FIELDNAME, CRASH_RATE_RISK_CATEGORY_FIELDNAME, 
               CRASH_RATE_RATIO_RISK_CATEGORY_FIELDNAME, CRASH_POTENTIAL_SAVINGS_RISK_CATEGORY_FIELDNAME]

#map and Layer file json
LAYER_JSON = r'{"layers": ["CIMPATH=risk_map/crash_density_risk_map.xml"], "version": "1.0.0", "type": "CIMLayerDocument", "layerDefinitions": [{"showPopups": true, "showLegends": true, "snappable": true, "uRI": "CIMPATH=risk_map/crash_density_risk_map.xml", "scaleSymbols": true, "maxDisplayCacheAge": 5, "displayCacheType": "Permanent", "selectionSymbol": {"symbol": {"type": "CIMLineSymbol", "symbolLayers": [{"enable": true, "color": {"type": "CIMRGBColor", "values": [0, 255, 255, 100]}, "lineStyle3D": "Strip", "joinStyle": "Round", "colorLocked": false, "width": 2, "miterLimit": 10, "capStyle": "Round", "type": "CIMSolidStroke"}]}, "type": "CIMSymbolReference", "symbolName": "Symbol_8"}, "visibility": true, "autoGenerateFeatureTemplates": true, "htmlPopupFormat": {"htmlPresentationStyle": "TwoColumnTable", "type": "CIMHtmlPopupFormat", "htmlUseCodedDomainValues": true}, "htmlPopupEnabled": true, "sourceModifiedTime": {"type": "TimeInstant"}, "labelClasses": [{"maplexLabelPlacementProperties": {"multiPartOption": "OneLabelPerPart", "lineFeatureType": "General", "pointExternalZonePriorities": {"aboveRight": 1, "aboveLeft": 4, "belowLeft": 8, "centerRight": 3, "aboveCenter": 2, "centerLeft": 6, "belowCenter": 7, "type": "CIMMaplexExternalZonePriorities", "belowRight": 5}, "featureType": "Line", "maximumLabelOverrunUnit": "Point", "labelPriority": -1, "enableConnection": true, "fontWidthReductionLimit": 90, "labelLargestPolygon": true, "connectionType": "Unambiguous", "fontWidthReductionStep": 5, "constrainOffset": "NoConstraint", "canStackLabel": true, "labelStackingProperties": {"stackAlignment": "ChooseBest", "maximumNumberOfLines": 3, "type": "CIMMaplexLabelStackingProperties", "maximumNumberOfCharsPerLine": 24, "minimumNumberOfCharsPerLine": 3}, "canPlaceLabelOutsidePolygon": true, "maximumLabelOverrun": 36, "polygonBoundaryWeight": 200, "pointPlacementMethod": "AroundPoint", "polygonFeatureType": "General", "fontHeightReductionLimit": 4, "graticuleAlignmentType": "Straight", "fontHeightReductionStep": 0.5, "removeExtraWhiteSpace": true, "repetitionIntervalUnit": "Map", "contourLadderType": "Straight", "offsetAlongLineProperties": {"useLineDirection": true, "type": "CIMMaplexOffsetAlongLineProperties", "placementMethod": "BestPositionAlongLine", "labelAnchorPoint": "CenterOfLabel", "distanceUnit": "Percentage"}, "polygonAnchorPointType": "GeometricCenter", "type": "CIMMaplexLabelPlacementProperties", "truncationMarkerCharacter": ".", "labelBuffer": 15, "truncationPreferredCharacters": "aeiou", "polygonInternalZones": {"type": "CIMMaplexInternalZonePriorities", "center": 1}, "polygonPlacementMethod": "CurvedInPolygon", "linePlacementMethod": "OffsetCurvedFromLine", "canRemoveOverlappingLabel": true, "featureWeight": 100, "canOverrunFeature": true, "contourAlignmentType": "Page", "primaryOffset": 1, "minimumFeatureSizeUnit": "Map", "primaryOffsetUnit": "Point", "truncationMinimumLength": 1, "thinningDistanceUnit": "Map", "contourMaximumAngle": 90, "avoidPolygonHoles": true, "polygonExternalZones": {"aboveRight": 1, "aboveLeft": 4, "belowLeft": 8, "centerRight": 3, "aboveCenter": 2, "centerLeft": 6, "belowCenter": 7, "type": "CIMMaplexExternalZonePriorities", "belowRight": 5}, "secondaryOffset": 100, "rotationProperties": {"alignmentType": "Straight", "type": "CIMMaplexRotationProperties", "rotationType": "Arithmetic"}, "strategyPriorities": {"fontCompression": 3, "stacking": 1, "abbreviation": 5, "fontReduction": 4, "type": "CIMMaplexStrategyPriorities", "overrun": 2}}, "name": "Default", "featuresToLabel": "AllVisibleFeatures", "useCodedValue": true, "visibility": true, "textSymbol": {"symbol": {"depth3D": 1, "billboardMode3D": "FaceNearPlane", "height": 8, "verticalGlyphOrientation": "Right", "fontFamilyName": "Arial", "fontEncoding": "Unicode", "flipAngle": 90, "blockProgression": "TTB", "haloSize": 1, "shadowColor": {"type": "CIMRGBColor", "values": [0, 0, 0, 100]}, "kerning": true, "verticalAlignment": "Bottom", "fontEffects": "Normal", "type": "CIMTextSymbol", "wordSpacing": 100, "symbol": {"type": "CIMPolygonSymbol", "symbolLayers": [{"colorLocked": false, "pattern": {"color": {"type": "CIMRGBColor", "values": [0, 0, 0, 100]}, "type": "CIMSolidPattern"}, "enable": true, "type": "CIMFill"}]}, "textCase": "Normal", "fontStyleName": "Regular", "ligatures": false, "horizontalAlignment": "Center", "drawSoftHyphen": true, "letterWidth": 100, "lineGapType": "ExtraLeading", "hinting": "Default", "textDirection": "LTR", "fontType": "Unspecified", "compatibilityMode": true, "extrapolateBaselines": true}, "type": "CIMSymbolReference", "symbolName": "Symbol_7"}, "priority": 2, "expression": "[ROUTE_NAME]", "expressionEngine": "VBScript", "type": "CIMLabelClass", "standardLabelPlacementProperties": {"lineLabelPosition": {"inLine": true, "type": "CIMStandardLineLabelPosition", "parallel": true, "above": true}, "featureType": "Line", "pointPlacementMethod": "AroundPoint", "numLabelsOption": "OneLabelPerName", "polygonPlacementMethod": "AlwaysHorizontal", "pointPlacementPriorities": {"aboveRight": 1, "aboveLeft": 2, "belowLeft": 3, "centerRight": 2, "aboveCenter": 2, "centerLeft": 3, "belowCenter": 3, "type": "CIMStandardPointPlacementPriorities", "belowRight": 2}, "rotationType": "Arithmetic", "featureWeight": "None", "labelWeight": "High", "lineLabelPriorities": {"aboveEnd": 3, "belowAlong": 3, "belowEnd": 3, "centerAlong": 3, "centerStart": 3, "belowStart": 3, "centerEnd": 3, "aboveStart": 3, "aboveAlong": 3, "type": "CIMStandardLineLabelPriorities"}, "type": "CIMStandardLabelPlacementProperties"}}], "layerType": "Operational", "exclusionSet": {}, "selectable": true, "type": "CIMFeatureLayer", "featureTable": {"timeFields": {"type": "CIMTimeTableDefinition"}, "editable": true, "searchOrder": "esriSearchOrderSpatial", "timeDisplayDefinition": {"timeInterval": 0, "timeIntervalUnits": "esriTimeUnitsHours", "timeOffsetUnits": "esriTimeUnitsYears", "type": "CIMTimeDisplayDefinition"}, "timeDefinition": {"type": "CIMTimeDataDefinition"}, "type": "CIMFeatureTable", "studyAreaSpatialRel": "esriSpatialRelUndefined", "dataConnection": {"workspaceFactory": "FileGDB", "datasetType": "esriDTFeatureClass", "type": "CIMStandardDataConnection", "workspaceConnectionString": "DATABASE=..\\MapsandGeodatabase\\BasicSegmentation\\CrashAssignmentOutput.gdb", "dataset": "SegmentOutput"}}, "isFlattened": true, "name": "Crash Density Risk Map"}]}'
RENDERER = r'{"type": "CIMUniqueValueRenderer", "defaultSymbol": {"symbol": {"type": "CIMLineSymbol", "symbolLayers": [{"enable": true, "color": {"values": [178, 178, 178, 100], "type": "CIMRGBColor"}, "lineStyle3D": "Strip", "miterLimit": 10, "width": 0.8, "joinStyle": "Round", "capStyle": "Butt", "type": "CIMSolidStroke"}]}, "type": "CIMSymbolReference", "symbolName": "Symbol_6"}, "useDefaultSymbol": true, "groups": [{"classes": [{"symbol": {"symbol": {"type": "CIMLineSymbol", "symbolLayers": [{"enable": true, "color": {"values": [100, 100, 66, 100], "type": "CIMHSVColor"}, "lineStyle3D": "Strip", "miterLimit": 10, "width": 1.5, "joinStyle": "Round", "capStyle": "Round", "type": "CIMSolidStroke"}]}, "type": "CIMSymbolReference", "symbolName": "Symbol_1"}, "patch": "Default", "visible": true, "values": [{"type": "CIMUniqueValue", "fieldValues": ["Lowest risk"]}], "label": "Lowest risk", "type": "CIMUniqueValueClass"}, {"symbol": {"symbol": {"type": "CIMLineSymbol", "symbolLayers": [{"enable": true, "color": {"values": [80, 100, 82, 100], "type": "CIMHSVColor"}, "lineStyle3D": "Strip", "miterLimit": 10, "width": 1.5, "joinStyle": "Round", "capStyle": "Round", "type": "CIMSolidStroke"}]}, "type": "CIMSymbolReference", "symbolName": "Symbol_2"}, "patch": "Default", "visible": true, "values": [{"type": "CIMUniqueValue", "fieldValues": ["Medium-low risk"]}], "label": "Medium-low risk", "type": "CIMUniqueValueClass"}, {"symbol": {"symbol": {"type": "CIMLineSymbol", "symbolLayers": [{"enable": true, "color": {"values": [60, 100, 100, 100], "type": "CIMHSVColor"}, "lineStyle3D": "Strip", "miterLimit": 10, "width": 1.5, "joinStyle": "Round", "capStyle": "Round", "type": "CIMSolidStroke"}]}, "type": "CIMSymbolReference", "symbolName": "Symbol_3"}, "patch": "Default", "visible": true, "values": [{"type": "CIMUniqueValue", "fieldValues": ["Medium risk"]}], "label": "Medium risk", "type": "CIMUniqueValueClass"}, {"symbol": {"symbol": {"type": "CIMLineSymbol", "symbolLayers": [{"enable": true, "color": {"values": [255, 0, 0, 100], "type": "CIMRGBColor"}, "lineStyle3D": "Strip", "miterLimit": 10, "width": 1.5, "joinStyle": "Round", "capStyle": "Round", "type": "CIMSolidStroke"}]}, "type": "CIMSymbolReference", "symbolName": "Symbol_4"}, "patch": "Default", "visible": true, "values": [{"type": "CIMUniqueValue", "fieldValues": ["Medium-high risk"]}], "label": "Medium-high risk", "type": "CIMUniqueValueClass"}, {"symbol": {"symbol": {"type": "CIMLineSymbol", "symbolLayers": [{"enable": true, "color": {"values": [0, 0, 0, 100], "type": "CIMRGBColor"}, "lineStyle3D": "Strip", "miterLimit": 10, "width": 1.5, "joinStyle": "Round", "capStyle": "Round", "type": "CIMSolidStroke"}]}, "type": "CIMSymbolReference", "symbolName": "Symbol_5"}, "patch": "Default", "visible": true, "values": [{"type": "CIMUniqueValue", "fieldValues": ["Highest risk"]}], "label": "Highest risk", "type": "CIMUniqueValueClass"}], "type": "CIMUniqueValueGroup", "heading": "CRASH_DENSITY_RISK"}], "fields": ["CRASH_DENSITY_RISK"], "defaultLabel": "Non-USRAP Segments", "colorRamp": {"maxS": 80, "maxAlpha": 100, "colorSpace": {"url": "Default RGB", "type": "CIMICCColorSpace"}, "maxV": 80, "maxH": 360, "minAlpha": 100, "minS": 60, "type": "CIMRandomHSVColorRamp", "minV": 60}}'
MAP_JSON = r'{"mapDefinition": {"layers": ["CIMPATH=risk_map/topographic.xml"], "viewingMode": "2D", "name": "Risk Map", "generalPlacementProperties": {"placementQuality": "High", "type": "CIMMaplexGeneralPlacementProperties", "keyNumberGroups": [{"maximumNumberOfLines": 20, "name": "Default", "minimumNumberOfLines": 2, "numberResetType": "None", "horizontalAlignment": "Left", "type": "CIMMaplexKeyNumberGroup", "delimiterCharacter": "."}], "invertedLabelTolerance": 2, "unplacedLabelColor": {"values": [255, 0, 0, 100], "type": "CIMRGBColor"}}, "snappingProperties": {"snapRequestType": "SnapRequestType_GeometricAndVisualSnapping", "xYToleranceUnit": "SnapXYToleranceUnitPixel", "type": "CIMSnappingProperties", "xYTolerance": 10}, "uRI": "CIMPATH=risk_map/risk_map.xml", "spatialReference": {"wkid": 102100, "latestWkid": 3857}, "elevationSurfaces": [{"verticalExaggeration": 1, "name": "Ground", "color": {"values": [255, 255, 255, 100], "type": "CIMRGBColor"}, "elevationMode": "BaseGlobeSurface", "mapElevationID": "{B57250DE-34AA-4E2A-AA33-E617B9CB83AB}", "type": "CIMMapElevationSurface"}], "sourceModifiedTime": {"type": "TimeInstant"}, "mapType": "Map", "defaultExtent": {"xmin": -13580977.87677731, "ymin": 3780199.250079251, "ymax": 4278985.857377536, "xmax": -12801741.44122452, "spatialReference": {"wkid": 102100, "latestWkid": 3857}}, "illumination": {"sunAzimuth": 315, "type": "CIMIlluminationProperties", "illuminationSource": "AbsoluteSunPosition", "ambientLight": 75, "sunAltitude": 30, "sunPositionY": 0.61237243569579, "sunPositionX": -0.61237243569579, "sunPositionZ": 0.5}, "type": "CIMMap"}, "version": "1.0.0", "type": "CIMMapDocument", "layerDefinitions": [{"showLegends": true, "showPopups": true, "layerElevation": {"type": "CIMLayerElevationSurface", "mapElevationID": "{B57250DE-34AA-4E2A-AA33-E617B9CB83AB}"}, "description": "Topographic", "transparentColor": {"values": [0, 0, 0, 100], "type": "CIMRGBColor"}, "displayCacheType": "Permanent", "uRI": "CIMPATH=risk_map/topographic.xml", "visibility": true, "serviceConnection": {"description": "BaseMap", "objectName": "World_Topo_Map", "url": "http://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer", "serverConnection": {"url": "http://services.arcgisonline.com/ArcGIS/services", "type": "CIMInternetServerConnection", "hideUserProperty": true, "anonymous": true}, "type": "CIMAGSServiceConnection", "objectType": "MapServer"}, "sourceModifiedTime": {"type": "TimeInstant"}, "layerType": "BasemapBackground", "type": "CIMTiledServiceLayer", "backgroundColor": {"values": [0, 0, 0, 100], "type": "CIMRGBColor"}, "name": "Topographic"}]}'
GROUP_LAYER_JSON = r'{"showLegends": true, "showPopups": true, "serviceLayerID": -1, "description": "Risk Map", "layers": [], "expanded": true, "displayCacheType": "Permanent", "uRI": "CIMPATH=risk_map/group_layer.xml", "visibility": true, "maxDisplayCacheAge": 5, "sourceModifiedTime": {"type": "TimeInstant"}, "layerType": "Operational", "type": "CIMGroupLayer", "name": "Risk"}'

#popup html
POPUP_DESCRIPTION_LOOKUP = { CRASH_DENSITY_FIELDNAME : '<span style=\"font-family: Calibri, sans-serif; font-size: 11pt;\"> {0}</span>'.format('crashes per mile of road'),
               CRASH_RATE_FIELDNAME : '<span style=\"font-family: Calibri, sans-serif; font-size: 11pt;\"> {0}</span>'.format('crashes per 100 million veh-mi of travel'),
               CRASH_RATE_RATIO_FIELDNAME : '<div><span style=\"font-family: Calibri, sans-serif; font-size: 11pt;\"><i>{0}</i></span></div>'.format('Risk expressed as the ratio of the crash rate for a particular analysis segment to the average crash rate for all segments of the same roadway type.'),
               CRASH_POTENTIAL_SAVINGS_FIELDNAME : '<div><span style=\"font-family: Calibri, sans-serif; font-size: 11pt;\"><i>{0}</i></span></div>'.format('<i>Estimate of the number of crashes per mile that would be reduced if the crash rate for the road segment could be reduced to the average crash rate for similar road segments.</i>') }

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
            if arcpy.TestSchemaLock(layer):
                if scale:
                    arcpy.AddField_management(layer, field, type, field_scale=scale)
                else:
                    arcpy.AddField_management(layer, field, type)
            else:
                arcpy.AddError("Cannot aquire a schema lock on: " + str(layer))
                
        #TODO elif verify if the field type matches...if it does not add
        # a new field with the correct type and a new name and tell the user

def calculate_density_and_rate(layer, fields, number_of_years_in_study):
    """
    calculates crash density, crash rate, and overall USRAP road network length.
    also determines the summary table values
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
            num_crashes = float(row[crash_count_index])
            length = float(row[-1])
            crash_density = num_crashes / length
            row[fields.index(CRASH_DENSITY_FIELDNAME)] = round(decimal.Decimal(crash_density), 5)

            #Crash Rate = ((# of Crashes)*100,000,000)/
            # ((Length of Segment)*(AADT)*(# of days in year)*(# of years in study)))
            aadt = float(row[avg_aadt_index])
            num_days_in_year = 365
            crash_rate = (num_crashes*100000000)/(length * aadt * num_days_in_year * number_of_years_in_study)
            row[fields.index(CRASH_RATE_FIELDNAME)] = round(decimal.Decimal(crash_rate), 5)

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
            length = float(row[-1])
            sum_length += length
            sum_avg_aadt += float(row[avg_aadt_index])
            sum_crashes += float(row[crash_count_index])
            sum_density += float(row[crash_density_index])
            sum_crash_rate += float(row[crash_rate_index])
            sum_vh_miles += length * aadt * num_days_in_year * number_of_years_in_study
            overall_length += length
    return summary_table_values, crash_rate_for_road_type, overall_length

def calculate_ratio_and_potential_crash_savings(layer, fields, crash_rate_for_road_type, number_of_years_in_study):
    """
    calculates crash rate ratio and potential crash savings
    """
    arcpy.AddMessage("Calculating {0} and {1} for analysis segments".format(CRASH_RATE_RATIO_FIELDNAME, CRASH_POTENTIAL_SAVINGS_FIELDNAME))

    #field indexs
    crash_density_index = fields.index(CRASH_DENSITY_FIELDNAME)
    crash_rate_index = fields.index(CRASH_RATE_FIELDNAME)
    crash_rate_ratio_index = fields.index(CRASH_RATE_RATIO_FIELDNAME)
    potential_crash_savings_index = fields.index(CRASH_POTENTIAL_SAVINGS_FIELDNAME)
    roadway_type_index = fields.index(USRAP_ROADWAY_TYPE_FIELDNAME)
    avg_aadt_index = fields.index(USRAP_AVG_AADT_FIELDNAME)

    with arcpy.da.UpdateCursor(layer, fields) as update_cursor:
        for row in update_cursor:        
            crash_rate = float(row[crash_rate_index])

            current_roadway_type = row[roadway_type_index]

            if list(crash_rate_for_road_type.keys()).count(current_roadway_type) > 0:
                avg_crash_rate = crash_rate_for_road_type[current_roadway_type]

                if avg_crash_rate not in [None, "", ' ', 0]:
                    crash_rate_ratio = crash_rate / avg_crash_rate
                else:
                    crash_rate_ratio = 0
                row[crash_rate_ratio_index] = crash_rate_ratio

                cr_diff = crash_rate - avg_crash_rate
                aadt = float(row[avg_aadt_index])
                num_days_in_year = 365

                potential_crash_savings = (cr_diff * aadt * num_days_in_year * number_of_years_in_study)/100000000

                row[potential_crash_savings_index] = round(decimal.Decimal(potential_crash_savings), 5)
                update_cursor.updateRow(row)

def calculate_risk_values(layer):
    """
    adds required fields and then calls the two calculate functions
    """
    #get number of years in study
    number_of_years_in_study = len(arcpy.ListFields(layer, USRAP_AADT_YYYY))

    #add fields for crash density, rate, ratio, and potential crash savings values 
    #add_fields(layer, CRASH_CALC_FIELDS, "DOUBLE", 6)

    #key fields for calculations and results
    fields = [CRASH_DENSITY_FIELDNAME, CRASH_RATE_FIELDNAME, 
              CRASH_COUNT_FIELDNAME, USRAP_AVG_AADT_FIELDNAME, 
              CRASH_RATE_RATIO_FIELDNAME, USRAP_ROADWAY_TYPE_FIELDNAME,
              CRASH_POTENTIAL_SAVINGS_FIELDNAME, "SHAPE@LENGTH" ]

    #summary_table_values: data for final summary table see pg. 22 whitepaper
    #summary_table_values: {key:value}
    #crash_rate_for_road_type: summarized values by roadway type
    #crash_rate_for_road_type: {key:[values]}
    #overall_length: sum of the length of all usRAP segments
    summary_table_values, crash_rate_for_road_type, overall_length = calculate_density_and_rate(layer, fields, number_of_years_in_study)

    calculate_ratio_and_potential_crash_savings(layer, fields, crash_rate_for_road_type, number_of_years_in_study)

    return summary_table_values, overall_length, fields

def create_summary_tables(layer, summary_table_values, route_name_field):
    """
    generates the summary tables. pg 16
    """
    arcpy.AddMessage("Generating and populating final summary tables")

    #Create Summary Table
    # fields must be in the same order as values in summary_table_values
    populate_summary_table(SUMMARY_TABLE_NAME, SUMMARY_FIELDS, summary_table_values)

    #Create seg by seg summary table
    # This is just an export of [Route_Name, County, Mileposts, Roadway_Type, aadt, crash_rate, risk_level fields]
    fields = [route_name_field, USRAP_COUNTY_FIELDNAME, USRAP_ROADWAY_TYPE_FIELDNAME, USRAP_AVG_AADT_FIELDNAME, CRASH_RATE_FIELDNAME]
    fields.extend(RISK_FIELDS)

    create_table(SEG_SUMMARY_TABLE_NAME, fields)
    if int(arcpy.GetCount_management(SEG_SUMMARY_TABLE_NAME)[0]) > 0:
        arcpy.DeleteRows_management(SEG_SUMMARY_TABLE_NAME)
    temp_table = "in_memory//" + SEG_SUMMARY_TABLE_NAME
    arcpy.CopyRows_management(layer, temp_table)
    arcpy.Append_management(temp_table, SEG_SUMMARY_TABLE_NAME, "NO_TEST")
    arcpy.Delete_management(temp_table)

def populate_summary_table(table_name, fields, summary_table_values):
    """
    update the summary table with the provided values
    """
    #create summary table
    table = create_table(table_name, fields)
    #insert the values into the output table
    with arcpy.da.InsertCursor(table, fields) as insert_cursor:
        for v in summary_table_values.items():
            insert_cursor.insertRow([v[0]] + v[1])

def create_table(name, fields):
    """
    create the table and add fields
    """
    table = arcpy.CreateTable_management(arcpy.env.workspace, name)
    for field in fields:
        arcpy.AddField_management(str(table), field, "TEXT")
    return table

def percentage(percent, whole):
    """
    get <what> for percent of whole
    """
    return (percent * whole) / 100.0

def assign_risk_levels(overall_length, fields, layer):  
    """
    assigns risk level based on the determined thresholds. pg 14  
    """
    #add fields for eash category
    #add_fields(layer, RISK_FIELDS, "TEXT", None)
    for f in RISK_FIELDS:
        fields.insert(0, f)

    percentage_lengths = {}

    sum_percentage_length = 0
    for p in RISK_LEVEL_CATEGORIES:
        percent = RISK_LEVEL_CATEGORIES[p][1]
        sum_percentage_length += percentage(percent, overall_length)
        percentage_lengths[p] = sum_percentage_length

    crash_count_field_index = fields.index(CRASH_COUNT_FIELDNAME)

    risk_level = -1
    for risk_value_field_name in list(RISK_FIELD_VALUE_FIELD_FIELDS.keys()):
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
                        # however we would also want to be aware of the next categories thresholds 
                        #so we could properly handle a situation where a category is completely skipped
                        temp_next_threshold_value = risk_category_index + 1
                        temp_next_percentage_length = percentage_lengths[temp_next_threshold_value]
                        #if sum_length > temp_next_percentage_length:
                        #    arcpy.AddWarning(RISK_LEVEL_CATEGORIES[risk_category_index + 1][0] + " level has no assigned values")
                    else:
                        #don't increment for the final row otherwise increment to the next category
                        if risk_category_index + 1 < len(RISK_LEVEL_CATEGORIES):
                            risk_category_index += 1

                if risk_category_index > 2:
                    #analysis segments with 2 or fewer crashes should never be assigned to the top two 
                    # risk categories. pg 15
                    if row[crash_count_field_index] < 3:
                        row[risk_level_field_index] = RISK_LEVEL_CATEGORIES[2][0]
                    else:
                        row[risk_level_field_index] = RISK_LEVEL_CATEGORIES[risk_category_index][0]
                else:
                    row[risk_level_field_index] = RISK_LEVEL_CATEGORIES[risk_category_index][0]
                update_cursor.updateRow(row)
                previous_value = current_value

def get_popup_html(calc_field, aadt_fields):
    html = '<b>{0}:</b> {{{1}}}{2}'.format(calc_field.replace('_', ' ').title(), calc_field, POPUP_DESCRIPTION_LOOKUP[calc_field])
    html += '<div><span style=\"font-family: Calibri, sans-serif; font-size: 11pt;\"><br /></span></div><div><span style=\"font-family: Calibri, sans-serif; font-size: 11pt;\"><b>Annual Average Daily Traffic Counts</b></span></div>'
    
    for aadt in aadt_fields:
        name = aadt.name
        html += '<div><span style=\"font-family: Calibri, sans-serif; font-size: 11pt;\">    {0}: </span>{{{1}}}</div><div>'.format(name[-4:], name)

    html += '<div><br /></div><div><b>Assigned Crash Count:</b> {{{0}}}</div><div><br /></div><div><b>USRAP Roadway Type:</b> {{{1}}}</div></div>'.format(CRASH_COUNT_FIELDNAME, USRAP_ROADWAY_TYPE_FIELDNAME)
    return html

def update_and_save_map(segments, route_name_field):
    """
    Create a new map in the project with risk map layers added.
    """
    import arcpy.mp as mapping
    prj = mapping.ArcGISProject('CURRENT')

    desc = arcpy.Describe(segments)
    aadt_fields = arcpy.ListFields(segments, USRAP_AADT_YYYY)
    
    layers = []
    for i in range(0, len(CRASH_CALC_FIELDS)):
        field =  RISK_FIELD_VALUE_FIELD_FIELDS[CRASH_CALC_FIELDS[i]]
        layer = json.loads(LAYER_JSON)
        layer_def = layer['layerDefinitions'][0]
        layer_def['name'] = field.replace('_', ' ').title()
        layer_def['uRI'] = "CIMPATH=risk_map/{0}.xml".format(field.lower())
        renderer = json.loads(RENDERER)
        renderer['fields'][0] = field
        renderer['groups'][0]['heading'] = field
        layer_def['renderer'] = renderer
        popup_info = {'type' : 'CIMPopupInfo', 'title' : '{{{0}}} (Segment ID: {{{1}}})'.format(route_name_field, USRAP_SEGMENT_ID_FIELDNAME), 'mediaInfos': []}
        popup_info['mediaInfos'].append({'type' : 'CIMTextMediaInfo', 'row' : 1, 'column' : 1, 'text' : get_popup_html(CRASH_CALC_FIELDS[i], aadt_fields)})    
        layer_def['popupInfo'] = popup_info
        layers.append(layer_def)

    map = json.loads(MAP_JSON)
    map_def = map['mapDefinition']
    extent = desc.extent
    extent = extent.projectAs(arcpy.SpatialReference(map_def['spatialReference']['wkid']))
    map_def['defaultExtent'] = { 'xmin' : extent.XMin, 'ymin' : extent.YMin, 'xmax' : extent.XMax, 'ymax' : extent.YMax, 'spatialReference' : map_def['spatialReference'] }
    map_name = "Risk Map {0}".format(time.strftime("%Y-%m-%d %H %M %S"))
    map_def['name'] = map_name
    
    for i in range(0, len(layers)):
        lyr = layers[i]
        map_def['layers'].insert(i, lyr['uRI'])
        map['layerDefinitions'].append(lyr)

    with tempfile.NamedTemporaryFile(delete=False) as temp_mapx:
        temp_mapx.write(json.dumps(map).encode())

    mapx_path = "{0}.mapx".format(temp_mapx.name)
    os.rename(temp_mapx.name, mapx_path)
    prj.importDocument(mapx_path)
    os.unlink(mapx_path)

    new_map = next((m for m in prj.listMaps() if m.name == map_name), None)
    if new_map is None:
        arcpy.AddError("Unable to create risk map.")       
    for layer in new_map.listLayers():
        if layer.isBroken:
            layer_connection = layer.connectionProperties['connection_info']['database']
            layer.updateConnectionProperties(layer_connection, desc.path)
    
    arcpy.AddMessage("Map: " + new_map.name + " was created successfully.")
    arcpy.AddMessage("Please check under the Maps entry in the Project pane.")

def get_workspace(feature_class):
    """
    returns the workspace for the feature class 
    """
    if arcpy.Describe(os.path.dirname(feature_class)).dataType != 'Workspace':
        return get_workspace(os.path.dirname(feature_class))
    return os.path.dirname(feature_class)

def check_path(fc):
    desc = arcpy.Describe(fc)
    if hasattr(desc, 'featureClass'):
        fc = desc.featureClass.catalogPath
    return fc

def main():
    #inputs from the user
    segments = arcpy.GetParameterAsText(0)
    route_name_field = arcpy.GetParameterAsText(1)

    segments = check_path(segments)

    add_fields(segments, CRASH_CALC_FIELDS, "DOUBLE", 6)
    add_fields(segments, RISK_FIELDS, "TEXT", None)

    ##set the env
    arcpy.env.workspace = get_workspace(segments)
    arcpy.env.overwriteOutput = True

    #only process on usRAP segments
    where = "{0} = 'YES'".format(USRAP_SEGMENT_FIELDNAME)
    layer = arcpy.MakeFeatureLayer_management(segments, "RiskMapSegments", where)

    #handle the inital 4 calculations 
    summary_table_values, overall_length, fields = calculate_risk_values(layer)

    #assign risk levels after the values have been calculated 
    # and the overall length of the road network is known
    assign_risk_levels(overall_length, fields, layer)

    #create and populate the summary tables
    create_summary_tables(layer, summary_table_values, route_name_field)

    #update the datasource for the layers in the map and save a new mxd
    update_and_save_map(segments, route_name_field)

if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        arcpy.AddError(ex.args)

