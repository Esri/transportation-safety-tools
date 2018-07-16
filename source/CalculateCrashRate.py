"""
-------------------------------------------------------------------------------
 | Copyright 2017 Esri
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
import arcpy, os, tempfile

_CRASH_RATE_POLYLINE = r'{ "type" : "CIMLayerDocument", "version" : "1.3.0", "build" : 5861, "layers" : ["CIMPATH=crashes/streets_crashrate.xml"], "layerDefinitions" : [{ "type" : "CIMFeatureLayer", "name" : "Streets_CrashRate", "uRI" : "CIMPATH=crashes/streets_crashrate.xml", "sourceModifiedTime" : { "type" : "TimeInstant" }, "description" : "Streets_CrashRate", "layerElevation" : { "type" : "CIMLayerElevationSurface" }, "expanded" : true, "layer3DProperties" : { "type" : "CIM3DLayerProperties", "castShadows" : true, "isLayerLit" : true, "layerFaceCulling" : "None", "maxDistance" : 120000, "minDistance" : -1, "preloadTextureCutoffHigh" : 0, "preloadTextureCutoffLow" : 0.25, "textureCutoffHigh" : 0.25, "textureCutoffLow" : 1, "useCompressedTextures" : true, "verticalExaggeration" : 1, "verticalUnit" : { "uwkid" : 9003 }, "lighting" : "OneSideDataNormal" }, "layerType" : "Operational", "showLegends" : true, "visibility" : true, "displayCacheType" : "Permanent", "maxDisplayCacheAge" : 5, "showPopups" : true, "serviceLayerID" : -1, "autoGenerateFeatureTemplates" : true, "featureElevationExpression" : "Shape.Z", "featureTable" : { "type" : "CIMFeatureTable", "displayField" : "STREET_NAME", "editable" : true, "dataConnection" : { "type" : "CIMStandardDataConnection", "workspaceConnectionString" : "DATABASE=.\\CrashAnalysis.gdb", "workspaceFactory" : "FileGDB", "dataset" : "Streets_CrashRate", "datasetType" : "esriDTFeatureClass" }, "studyAreaSpatialRel" : "esriSpatialRelUndefined", "searchOrder" : "esriSearchOrderSpatial" }, "htmlPopupEnabled" : true, "selectable" : true, "featureCacheType" : "None", "labelClasses" : [{ "type" : "CIMLabelClass", "expression" : "[STREET_NAME]", "expressionEngine" : "VBScript", "featuresToLabel" : "AllVisibleFeatures", "maplexLabelPlacementProperties" : { "type" : "CIMMaplexLabelPlacementProperties", "featureType" : "Line", "avoidPolygonHoles" : true, "canOverrunFeature" : true, "canPlaceLabelOutsidePolygon" : true, "canRemoveOverlappingLabel" : true, "canStackLabel" : true, "connectionType" : "MinimizeLabels", "constrainOffset" : "AboveLine", "contourAlignmentType" : "Page", "contourLadderType" : "Straight", "contourMaximumAngle" : 90, "enableConnection" : true, "featureWeight" : 0, "fontHeightReductionLimit" : 4, "fontHeightReductionStep" : 0.5, "fontWidthReductionLimit" : 90, "fontWidthReductionStep" : 5, "graticuleAlignmentType" : "Straight", "keyNumberGroupName" : "Default", "labelBuffer" : 15, "labelLargestPolygon" : true, "labelPriority" : -1, "labelStackingProperties" : { "type" : "CIMMaplexLabelStackingProperties", "stackAlignment" : "ChooseBest", "maximumNumberOfLines" : 3, "minimumNumberOfCharsPerLine" : 3, "maximumNumberOfCharsPerLine" : 24, "separators" : [{ "type" : "CIMMaplexStackingSeparator", "separator" : " ", "splitAfter" : true }, { "type" : "CIMMaplexStackingSeparator", "separator" : ",", "visible" : true, "splitAfter" : true } ] }, "lineFeatureType" : "General", "linePlacementMethod" : "OffsetStraightFromLine", "maximumLabelOverrun" : 16, "maximumLabelOverrunUnit" : "Point", "minimumFeatureSizeUnit" : "Map", "multiPartOption" : "OneLabelPerFeature", "offsetAlongLineProperties" : { "type" : "CIMMaplexOffsetAlongLineProperties", "placementMethod" : "BestPositionAlongLine", "labelAnchorPoint" : "CenterOfLabel", "distanceUnit" : "Map", "useLineDirection" : true }, "pointExternalZonePriorities" : { "type" : "CIMMaplexExternalZonePriorities", "aboveLeft" : 4, "aboveCenter" : 2, "aboveRight" : 1, "centerRight" : 3, "belowRight" : 5, "belowCenter" : 7, "belowLeft" : 8, "centerLeft" : 6 }, "pointPlacementMethod" : "AroundPoint", "polygonAnchorPointType" : "GeometricCenter", "polygonBoundaryWeight" : 0, "polygonExternalZones" : { "type" : "CIMMaplexExternalZonePriorities", "aboveLeft" : 4, "aboveCenter" : 2, "aboveRight" : 1, "centerRight" : 3, "belowRight" : 5, "belowCenter" : 7, "belowLeft" : 8, "centerLeft" : 6 }, "polygonFeatureType" : "General", "polygonInternalZones" : { "type" : "CIMMaplexInternalZonePriorities", "center" : 1 }, "polygonPlacementMethod" : "CurvedInPolygon", "primaryOffset" : 1, "primaryOffsetUnit" : "Point", "removeExtraWhiteSpace" : true, "repetitionIntervalUnit" : "Map", "rotationProperties" : { "type" : "CIMMaplexRotationProperties", "rotationType" : "Arithmetic", "alignmentType" : "Straight" }, "secondaryOffset" : 100, "strategyPriorities" : { "type" : "CIMMaplexStrategyPriorities", "stacking" : 1, "overrun" : 2, "fontCompression" : 3, "fontReduction" : 4, "abbreviation" : 5 }, "thinningDistanceUnit" : "Point", "truncationMarkerCharacter" : ".", "truncationMinimumLength" : 1, "truncationPreferredCharacters" : "aeiou" }, "name" : "Class 1", "priority" : -1, "standardLabelPlacementProperties" : { "type" : "CIMStandardLabelPlacementProperties", "featureType" : "Line", "featureWeight" : "Low", "labelWeight" : "High", "numLabelsOption" : "OneLabelPerName", "lineLabelPosition" : { "type" : "CIMStandardLineLabelPosition", "above" : true, "inLine" : true, "parallel" : true }, "lineLabelPriorities" : { "type" : "CIMStandardLineLabelPriorities", "aboveStart" : 3, "aboveAlong" : 3, "aboveEnd" : 3, "centerStart" : 3, "centerAlong" : 3, "centerEnd" : 3, "belowStart" : 3, "belowAlong" : 3, "belowEnd" : 3 }, "pointPlacementMethod" : "AroundPoint", "pointPlacementPriorities" : { "type" : "CIMStandardPointPlacementPriorities", "aboveLeft" : 2, "aboveCenter" : 2, "aboveRight" : 1, "centerLeft" : 3, "centerRight" : 2, "belowLeft" : 3, "belowCenter" : 3, "belowRight" : 2 }, "rotationType" : "Arithmetic", "polygonPlacementMethod" : "AlwaysHorizontal" }, "textSymbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMTextSymbol", "blockProgression" : "TTB", "depth3D" : 1, "extrapolateBaselines" : true, "fontEffects" : "Normal", "fontEncoding" : "Unicode", "fontFamilyName" : "Tahoma", "fontStyleName" : "Regular", "fontType" : "Unspecified", "haloSize" : 1, "height" : 10, "hinting" : "Default", "horizontalAlignment" : "Left", "kerning" : true, "letterWidth" : 100, "ligatures" : true, "lineGapType" : "ExtraLeading", "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [{ "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMRGBColor", "values" : [0, 0, 0, 100] } } ] }, "textCase" : "Normal", "textDirection" : "LTR", "verticalAlignment" : "Bottom", "verticalGlyphOrientation" : "Right", "wordSpacing" : 100, "billboardMode3D" : "FaceNearPlane" } }, "useCodedValue" : true, "visibility" : true, "iD" : -1 } ], "renderer" : { "type" : "CIMClassBreaksRenderer", "barrierWeight" : "None", "breaks" : [{ "type" : "CIMClassBreak", "label" : "\u22642.513359", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMLineSymbol", "symbolLayers" : [{ "type" : "CIMSolidStroke", "enable" : true, "name" : "Group_0", "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 0, "color" : { "type" : "CIMHSVColor", "values" : [60, 100, 96, 0] } } ] }, "symbolName" : "Group_0" }, "upperBound" : 2.5133592903979509 }, { "type" : "CIMClassBreak", "label" : "\u22644.230509", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMLineSymbol", "symbolLayers" : [{ "type" : "CIMSolidStroke", "enable" : true, "name" : "Group_0", "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 0, "color" : { "type" : "CIMHSVColor", "values" : [45, 100, 96, 0] } } ] }, "symbolName" : "Group_0" }, "upperBound" : 4.2305092263641439 }, { "type" : "CIMClassBreak", "label" : "\u22646.348845", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMLineSymbol", "symbolLayers" : [{ "type" : "CIMSolidStroke", "enable" : true, "name" : "Group_0", "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 0, "color" : { "type" : "CIMHSVColor", "values" : [30, 100, 96, 0] } } ] }, "symbolName" : "Group_0" }, "upperBound" : 6.3488446517506096 }, { "type" : "CIMClassBreak", "label" : "\u226413.065343", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMLineSymbol", "symbolLayers" : [{ "type" : "CIMSolidStroke", "enable" : true, "name" : "Group_0", "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 2, "color" : { "type" : "CIMRGBColor", "values" : [255, 255, 0, 100] } } ] }, "symbolName" : "Group_0" }, "upperBound" : 13.065342959154151 }, { "type" : "CIMClassBreak", "label" : "\u2264179.839904", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMLineSymbol", "symbolLayers" : [{ "type" : "CIMSolidStroke", "enable" : true, "name" : "Group_0", "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 2, "color" : { "type" : "CIMHSVColor", "values" : [0, 100, 96, 100] } } ] }, "symbolName" : "Group_0" }, "upperBound" : 179.83990363869327 } ], "classBreakType" : "GraduatedColor", "classificationMethod" : "Quantile", "colorRamp" : { "type" : "CIMPolarContinuousColorRamp", "colorSpace" : { "type" : "CIMICCColorSpace", "url" : "Default RGB" }, "fromColor" : { "type" : "CIMHSVColor", "values" : [60, 100, 96, 100] }, "toColor" : { "type" : "CIMHSVColor", "values" : [0, 100, 96, 100] }, "interpolationSpace" : "HSV", "polarDirection" : "Auto" }, "field" : "c_freq", "minimumBreak" : 0.39842851747401187, "numberFormat" : { "type" : "CIMNumericFormat", "alignmentOption" : "esriAlignLeft", "alignmentWidth" : 0, "roundingOption" : "esriRoundNumberOfDecimals", "roundingValue" : 6, "zeroPad" : true }, "showInAscendingOrder" : true, "heading" : "Crashes Per Mile Per Year", "sampleSize" : 10000, "defaultSymbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMLineSymbol", "symbolLayers" : [{ "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 1, "color" : { "type" : "CIMRGBColor", "values" : [130, 130, 130, 100] } } ] } }, "defaultLabel" : "<out of range>", "exclusionLabel" : "<excluded>", "exclusionSymbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMLineSymbol", "symbolLayers" : [{ "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 1, "color" : { "type" : "CIMRGBColor", "values" : [255, 0, 0, 100] } } ] } }, "useExclusionSymbol" : false, "normalizationType" : "Nothing" }, "scaleSymbols" : true, "snappable" : true, "symbolLayerDrawing" : { "type" : "CIMSymbolLayerDrawing", "symbolLayers" : [{ "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_0" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_1" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_2" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_3" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_4" } ] } } ] }'
_CRASH_RATE_POINT = r'{ "type" : "CIMLayerDocument", "version" : "1.3.0", "build" : 5861, "layers" : [ "CIMPATH=map/intersections_crashrate.xml" ], "layerDefinitions" : [ { "type" : "CIMFeatureLayer", "name" : "Intersections", "uRI" : "CIMPATH=map/intersections_crashrate.xml", "sourceModifiedTime" : { "type" : "TimeInstant" }, "description" : "Intersections_CrashRate", "expanded" : true, "layer3DProperties" : { "type" : "CIM3DLayerProperties", "castShadows" : true, "isLayerLit" : true, "layerFaceCulling" : "None", "maxDistance" : -1, "minDistance" : -1, "preloadTextureCutoffHigh" : 0, "preloadTextureCutoffLow" : 0.25, "textureCutoffHigh" : 0.25, "textureCutoffLow" : 1, "useCompressedTextures" : true, "verticalExaggeration" : 1, "verticalUnit" : { "uwkid" : 9003 }, "lighting" : "OneSideDataNormal" }, "layerType" : "Operational", "showLegends" : true, "visibility" : true, "displayCacheType" : "Permanent", "maxDisplayCacheAge" : 5, "showPopups" : true, "serviceLayerID" : -1, "autoGenerateFeatureTemplates" : true, "featureElevationExpression" : "Shape.Z", "featureTable" : { "type" : "CIMFeatureTable", "displayField" : "streets", "editable" : true, "dataConnection" : { "type" : "CIMStandardDataConnection", "workspaceConnectionString" : "DATABASE=..\\CrashAnaysis.gdb", "workspaceFactory" : "FileGDB", "dataset" : "Intersections_CrashRate", "datasetType" : "esriDTFeatureClass" }, "studyAreaSpatialRel" : "esriSpatialRelUndefined", "searchOrder" : "esriSearchOrderSpatial" }, "htmlPopupEnabled" : true, "selectable" : true, "featureCacheType" : "None", "labelClasses" : [ { "type" : "CIMLabelClass", "expression" : "[streets]", "expressionEngine" : "VBScript", "featuresToLabel" : "AllVisibleFeatures", "maplexLabelPlacementProperties" : { "type" : "CIMMaplexLabelPlacementProperties", "featureType" : "Point", "avoidPolygonHoles" : true, "canOverrunFeature" : true, "canPlaceLabelOutsidePolygon" : true, "canRemoveOverlappingLabel" : true, "canStackLabel" : true, "connectionType" : "Unambiguous", "constrainOffset" : "NoConstraint", "contourAlignmentType" : "Page", "contourLadderType" : "Straight", "contourMaximumAngle" : 90, "enableConnection" : true, "enablePointPlacementPriorities" : true, "featureWeight" : 0, "fontHeightReductionLimit" : 4, "fontHeightReductionStep" : 0.5, "fontWidthReductionLimit" : 90, "fontWidthReductionStep" : 5, "graticuleAlignmentType" : "Straight", "keyNumberGroupName" : "Default", "labelBuffer" : 15, "labelLargestPolygon" : true, "labelPriority" : -1, "labelStackingProperties" : { "type" : "CIMMaplexLabelStackingProperties", "stackAlignment" : "ChooseBest", "maximumNumberOfLines" : 3, "minimumNumberOfCharsPerLine" : 3, "maximumNumberOfCharsPerLine" : 24, "separators" : [ { "type" : "CIMMaplexStackingSeparator", "separator" : " ", "splitAfter" : true }, { "type" : "CIMMaplexStackingSeparator", "separator" : ",", "visible" : true, "splitAfter" : true } ] }, "lineFeatureType" : "General", "linePlacementMethod" : "OffsetCurvedFromLine", "maximumLabelOverrun" : 36, "maximumLabelOverrunUnit" : "Point", "minimumFeatureSizeUnit" : "Map", "multiPartOption" : "OneLabelPerPart", "offsetAlongLineProperties" : { "type" : "CIMMaplexOffsetAlongLineProperties", "placementMethod" : "BestPositionAlongLine", "labelAnchorPoint" : "CenterOfLabel", "distanceUnit" : "Percentage", "useLineDirection" : true }, "pointExternalZonePriorities" : { "type" : "CIMMaplexExternalZonePriorities", "aboveLeft" : 4, "aboveCenter" : 2, "aboveRight" : 1, "centerRight" : 3, "belowRight" : 5, "belowCenter" : 7, "belowLeft" : 8, "centerLeft" : 6 }, "pointPlacementMethod" : "AroundPoint", "polygonAnchorPointType" : "GeometricCenter", "polygonBoundaryWeight" : 0, "polygonExternalZones" : { "type" : "CIMMaplexExternalZonePriorities", "aboveLeft" : 4, "aboveCenter" : 2, "aboveRight" : 1, "centerRight" : 3, "belowRight" : 5, "belowCenter" : 7, "belowLeft" : 8, "centerLeft" : 6 }, "polygonFeatureType" : "General", "polygonInternalZones" : { "type" : "CIMMaplexInternalZonePriorities", "center" : 1 }, "polygonPlacementMethod" : "CurvedInPolygon", "primaryOffset" : 1, "primaryOffsetUnit" : "Point", "removeExtraWhiteSpace" : true, "repetitionIntervalUnit" : "Map", "rotationProperties" : { "type" : "CIMMaplexRotationProperties", "rotationType" : "Arithmetic", "alignmentType" : "Straight" }, "secondaryOffset" : 100, "strategyPriorities" : { "type" : "CIMMaplexStrategyPriorities", "stacking" : 1, "overrun" : 2, "fontCompression" : 3, "fontReduction" : 4, "abbreviation" : 5 }, "thinningDistanceUnit" : "Point", "truncationMarkerCharacter" : ".", "truncationMinimumLength" : 1, "truncationPreferredCharacters" : "aeiou" }, "name" : "Class 1", "priority" : -1, "standardLabelPlacementProperties" : { "type" : "CIMStandardLabelPlacementProperties", "featureType" : "Line", "featureWeight" : "Low", "labelWeight" : "High", "numLabelsOption" : "OneLabelPerName", "lineLabelPosition" : { "type" : "CIMStandardLineLabelPosition", "above" : true, "inLine" : true, "parallel" : true }, "lineLabelPriorities" : { "type" : "CIMStandardLineLabelPriorities", "aboveStart" : 3, "aboveAlong" : 3, "aboveEnd" : 3, "centerStart" : 3, "centerAlong" : 3, "centerEnd" : 3, "belowStart" : 3, "belowAlong" : 3, "belowEnd" : 3 }, "pointPlacementMethod" : "AroundPoint", "pointPlacementPriorities" : { "type" : "CIMStandardPointPlacementPriorities", "aboveLeft" : 2, "aboveCenter" : 2, "aboveRight" : 1, "centerLeft" : 3, "centerRight" : 2, "belowLeft" : 3, "belowCenter" : 3, "belowRight" : 2 }, "rotationType" : "Arithmetic", "polygonPlacementMethod" : "AlwaysHorizontal" }, "textSymbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMTextSymbol", "blockProgression" : "TTB", "depth3D" : 1, "extrapolateBaselines" : true, "fontEffects" : "Normal", "fontEncoding" : "Unicode", "fontFamilyName" : "Tahoma", "fontStyleName" : "Regular", "fontType" : "Unspecified", "haloSize" : 1, "height" : 10, "hinting" : "Default", "horizontalAlignment" : "Left", "kerning" : true, "letterWidth" : 100, "ligatures" : true, "lineGapType" : "ExtraLeading", "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMRGBColor", "values" : [ 0, 0, 0, 100 ] } } ] }, "textCase" : "Normal", "textDirection" : "LTR", "verticalAlignment" : "Bottom", "verticalGlyphOrientation" : "Right", "wordSpacing" : 100, "billboardMode3D" : "FaceNearPlane" } }, "useCodedValue" : true, "visibility" : true, "iD" : -1 } ], "renderer" : { "type" : "CIMClassBreaksRenderer", "barrierWeight" : "None", "breaks" : [ { "type" : "CIMClassBreak", "label" : "\u22640.333333", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMPointSymbol", "symbolLayers" : [ { "type" : "CIMVectorMarker", "enable" : true, "name" : "Group_0", "anchorPointUnits" : "Relative", "dominantSizeAxis3D" : "Z", "size" : 1, "billboardMode3D" : "FaceNearPlane", "frame" : { "xmin" : -2, "ymin" : -2, "xmax" : 2, "ymax" : 2 }, "markerGraphics" : [ { "type" : "CIMMarkerGraphic", "geometry" : { "curveRings" : [ [ [ 1.2246467991473532e-016, 2 ], { "a" : [ [ 1.2246467991473532e-016, 2 ], [ 6.7466240421580192e-016, 0 ], 0, 1 ] } ] ] }, "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 8, "color" : { "type" : "CIMRGBColor", "values" : [ 0, 0, 0, 0 ] } }, { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMHSVColor", "values" : [ 60, 100, 96, 0 ] } } ] } } ], "respectFrame" : true } ], "haloSize" : 1, "scaleX" : 1, "angleAlignment" : "Display" }, "symbolName" : "Group_0" }, "upperBound" : 0.33333333333333331 }, { "type" : "CIMClassBreak", "label" : "\u22640.666667", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMPointSymbol", "symbolLayers" : [ { "type" : "CIMVectorMarker", "enable" : true, "name" : "Group_1", "anchorPointUnits" : "Relative", "dominantSizeAxis3D" : "Z", "size" : 1, "billboardMode3D" : "FaceNearPlane", "frame" : { "xmin" : -2, "ymin" : -2, "xmax" : 2, "ymax" : 2 }, "markerGraphics" : [ { "type" : "CIMMarkerGraphic", "geometry" : { "curveRings" : [ [ [ 1.2246467991473532e-016, 2 ], { "a" : [ [ 1.2246467991473532e-016, 2 ], [ 6.7466240421580192e-016, 0 ], 0, 1 ] } ] ] }, "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 8, "color" : { "type" : "CIMRGBColor", "values" : [ 0, 0, 0, 0 ] } }, { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMHSVColor", "values" : [ 45, 100, 96, 0 ] } } ] } } ], "respectFrame" : true } ], "haloSize" : 1, "scaleX" : 1, "angleAlignment" : "Display" }, "symbolName" : "Group_1" }, "upperBound" : 0.66666666666666663 }, { "type" : "CIMClassBreak", "label" : "\u22641.000000", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMPointSymbol", "symbolLayers" : [ { "type" : "CIMVectorMarker", "enable" : true, "name" : "Group_2", "anchorPointUnits" : "Relative", "dominantSizeAxis3D" : "Z", "size" : 1, "billboardMode3D" : "FaceNearPlane", "frame" : { "xmin" : -2, "ymin" : -2, "xmax" : 2, "ymax" : 2 }, "markerGraphics" : [ { "type" : "CIMMarkerGraphic", "geometry" : { "curveRings" : [ [ [ 1.2246467991473532e-016, 2 ], { "a" : [ [ 1.2246467991473532e-016, 2 ], [ 6.7466240421580192e-016, 0 ], 0, 1 ] } ] ] }, "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 8, "color" : { "type" : "CIMRGBColor", "values" : [ 0, 0, 0, 0 ] } }, { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMHSVColor", "values" : [ 30, 100, 96, 0 ] } } ] } } ], "respectFrame" : true } ], "haloSize" : 1, "scaleX" : 1, "angleAlignment" : "Display" }, "symbolName" : "Group_2" }, "upperBound" : 1 }, { "type" : "CIMClassBreak", "label" : "\u22641.666667", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMPointSymbol", "symbolLayers" : [ { "type" : "CIMVectorMarker", "enable" : true, "name" : "Group_3", "anchorPointUnits" : "Relative", "dominantSizeAxis3D" : "Z", "size" : 8, "billboardMode3D" : "FaceNearPlane", "frame" : { "xmin" : -2, "ymin" : -2, "xmax" : 2, "ymax" : 2 }, "markerGraphics" : [ { "type" : "CIMMarkerGraphic", "geometry" : { "curveRings" : [ [ [ 1.2246467991473532e-016, 2 ], { "a" : [ [ 1.2246467991473532e-016, 2 ], [ 6.6030623875207053e-016, 0 ], 0, 1 ] } ] ] }, "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 1, "color" : { "type" : "CIMRGBColor", "values" : [ 255, 255, 255, 100 ] } }, { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMRGBColor", "values" : [ 255, 255, 0, 100 ] } } ] } } ], "respectFrame" : true } ], "haloSize" : 1, "scaleX" : 1, "angleAlignment" : "Display" }, "symbolName" : "Group_3" }, "upperBound" : 1.6666666666666667 }, { "type" : "CIMClassBreak", "label" : "\u22643.666667", "patch" : "Default", "symbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMPointSymbol", "symbolLayers" : [ { "type" : "CIMVectorMarker", "enable" : true, "name" : "Group_4", "anchorPointUnits" : "Relative", "dominantSizeAxis3D" : "Z", "size" : 8, "billboardMode3D" : "FaceNearPlane", "frame" : { "xmin" : -2, "ymin" : -2, "xmax" : 2, "ymax" : 2 }, "markerGraphics" : [ { "type" : "CIMMarkerGraphic", "geometry" : { "curveRings" : [ [ [ 1.2246467991473532e-016, 2 ], { "a" : [ [ 1.2246467991473532e-016, 2 ], [ 6.7466240421580192e-016, 0 ], 0, 1 ] } ] ] }, "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 1, "color" : { "type" : "CIMRGBColor", "values" : [ 255, 255, 255, 100 ] } }, { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMHSVColor", "values" : [ 0, 100, 96, 100 ] } } ] } } ], "respectFrame" : true } ], "haloSize" : 1, "scaleX" : 1, "angleAlignment" : "Display" }, "symbolName" : "Group_4" }, "upperBound" : 3.6666666666666665 } ], "classBreakType" : "GraduatedColor", "classificationMethod" : "Quantile", "colorRamp" : { "type" : "CIMPolarContinuousColorRamp", "colorSpace" : { "type" : "CIMICCColorSpace", "url" : "Default RGB" }, "fromColor" : { "type" : "CIMHSVColor", "values" : [ 60, 100, 96, 100 ] }, "toColor" : { "type" : "CIMHSVColor", "values" : [ 0, 100, 96, 100 ] }, "interpolationSpace" : "HSV", "polarDirection" : "Auto" }, "field" : "c_freq", "minimumBreak" : 0.33333333333333331, "numberFormat" : { "type" : "CIMNumericFormat", "alignmentOption" : "esriAlignLeft", "alignmentWidth" : 0, "roundingOption" : "esriRoundNumberOfDecimals", "roundingValue" : 6, "zeroPad" : true }, "showInAscendingOrder" : true, "heading" : "Crashes Per Year", "sampleSize" : 10000, "defaultSymbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMPointSymbol", "symbolLayers" : [ { "type" : "CIMVectorMarker", "enable" : true, "anchorPointUnits" : "Relative", "dominantSizeAxis3D" : "Z", "size" : 4, "billboardMode3D" : "FaceNearPlane", "frame" : { "xmin" : -2, "ymin" : -2, "xmax" : 2, "ymax" : 2 }, "markerGraphics" : [ { "type" : "CIMMarkerGraphic", "geometry" : { "curveRings" : [ [ [ 1.2246467991473532e-016, 2 ], { "a" : [ [ 1.2246467991473532e-016, 2 ], [ 6.6030623875207053e-016, 0 ], 0, 1 ] } ] ] }, "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 0.69999999999999996, "color" : { "type" : "CIMRGBColor", "values" : [ 0, 0, 0, 100 ] } }, { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMRGBColor", "values" : [ 130, 130, 130, 100 ] } } ] } } ], "respectFrame" : true } ], "haloSize" : 1, "scaleX" : 1, "angleAlignment" : "Display" } }, "defaultLabel" : "<out of range>", "exclusionLabel" : "<excluded>", "exclusionSymbol" : { "type" : "CIMSymbolReference", "symbol" : { "type" : "CIMPointSymbol", "symbolLayers" : [ { "type" : "CIMVectorMarker", "enable" : true, "anchorPointUnits" : "Relative", "dominantSizeAxis3D" : "Z", "size" : 4, "billboardMode3D" : "FaceNearPlane", "frame" : { "xmin" : -2, "ymin" : -2, "xmax" : 2, "ymax" : 2 }, "markerGraphics" : [ { "type" : "CIMMarkerGraphic", "geometry" : { "curveRings" : [ [ [ 1.2246467991473532e-016, 2 ], { "a" : [ [ 1.2246467991473532e-016, 2 ], [ 6.6030623875207053e-016, 0 ], 0, 1 ] } ] ] }, "symbol" : { "type" : "CIMPolygonSymbol", "symbolLayers" : [ { "type" : "CIMSolidStroke", "enable" : true, "capStyle" : "Round", "joinStyle" : "Round", "lineStyle3D" : "Strip", "miterLimit" : 10, "width" : 0.69999999999999996, "color" : { "type" : "CIMRGBColor", "values" : [ 0, 0, 0, 100 ] } }, { "type" : "CIMSolidFill", "enable" : true, "color" : { "type" : "CIMRGBColor", "values" : [ 255, 0, 0, 100 ] } } ] } } ], "respectFrame" : true } ], "haloSize" : 1, "scaleX" : 1, "angleAlignment" : "Display" } }, "useExclusionSymbol" : false, "normalizationType" : "Nothing" }, "scaleSymbols" : true, "snappable" : true, "symbolLayerDrawing" : { "type" : "CIMSymbolLayerDrawing", "symbolLayers" : [ { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_0" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_1" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_2" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_3" }, { "type" : "CIMSymbolLayerIdentifier", "symbolReferenceName" : "RequiredForDraw", "symbolLayerName" : "Group_4" } ] } } ] }'

def get_workspace(feature_class):
    """ Return workspace for provided feature class """
    try:
        desc= arcpy.Describe(feature_class)
        if hasattr(desc, 'featureClass'):
            feature_class = desc.featureClass.catalogPath
        if arcpy.Describe(os.path.dirname(feature_class)).dataType != 'Workspace':
            return get_workspace(os.path.dirname(feature_class))
        return os.path.dirname(feature_class)
    except:
        return None

def main():
    scratch_datasets = []
    new_fields = ['c_count', 'c_weight', 'c_freq', 'c_rate', 'w_freq', 'w_rate']

    try:
        streets_intersection = arcpy.GetParameterAsText(0)
        crashes = arcpy.GetParameterAsText(1)
        time_interval, time_unit = arcpy.GetParameterAsText(2).split(' ')
        time_interval = float(time_interval)
        if time_unit == 'Years':
            time_interval = time_interval * 365
        elif time_unit == 'Weeks':
            time_interval = time_interval * 7
        snap_distance = arcpy.GetParameterAsText(3)
        weight_field = arcpy.GetParameterAsText(4)
        weight_table = arcpy.GetParameter(5)
        adt_field = arcpy.GetParameterAsText(6)
        output_crash_rates = arcpy.GetParameterAsText(7)
        params = arcpy.GetParameterInfo()
        shape_type = arcpy.Describe(streets_intersection).shapeType

        weight_provided = False
        if weight_field is not None and weight_field != '':
            weight_provided = True

        adt_provided = False
        if adt_field is not None and adt_field != '':
            adt_provided = True

        arcpy.SetProgressorLabel("Creating Temporary Crash Layer...")
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
                        database = get_workspace(crashes)
                        if database is not None:
                            for domain in arcpy.da.ListDomains(database):
                                if domain.name == field.domain:
                                    if domain.domainType == 'CodedValue':
                                        for key, value in domain.codedValues.items():
                                            for i in range(0, weight_table.rowCount):
                                                if weight_table.getValue(i, 0) == value:
                                                    weight_table.setValue(i, 0, str(key))
                                    break

        with arcpy.da.UpdateCursor(crashes_snap, fields) as cursor:
            for row in cursor:
                row[0] = 1.0
                if len(fields) == 3:
                    value = str(row[2])
                    for i in range(0, weight_table.rowCount):
                        if value == weight_table.getValue(i, 0):
                            row[1] = weight_table.getValue(i, 1)
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
            if shape_type == "Polyline" and hasattr(desc, 'lengthFieldName') and field.name == desc.lengthFieldName:
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
            add_fields = [[crash_frequency_field, "Crashes Per Mile Per Year"], [crash_rate_field, "Crashes Per Million Vehicle Miles"],
                            [weighted_crash_frequency_field, "Weighted Crashes Per Mile Per Year"], [weighted_crash_rate_field, "Weighted Crashes Per Million Vehicle Miles"]] 
        else:            
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
            
        arcpy.SetProgressorLabel("Creating Crash Rate Layer...")
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
        arcpy.MakeFeatureLayer_management(crashes_join, "Output Crash Layer", field_info=field_info[:-1])
        arcpy.SelectLayerByAttribute_management("Output Crash Layer", "NEW_SELECTION", '{0} IS NOT NULL'.format(new_fields[2]))
        arcpy.CopyFeatures_management("Output Crash Layer", output_crash_rates)
        
        lyrx_json = _CRASH_RATE_POINT
        if (shape_type == "Polyline"):
            lyrx_json = _CRASH_RATE_POLYLINE
        with tempfile.NamedTemporaryFile(delete=False) as temp_lyrx:
            temp_lyrx.write(lyrx_json.encode())
        lyrx_path = "{0}.lyrx".format(temp_lyrx.name)
        os.rename(temp_lyrx.name, lyrx_path)
        params[7].symbology = lyrx_path
        
    finally:
        for dataset in scratch_datasets:
            if arcpy.Exists(dataset):
                arcpy.Delete_management(dataset)

if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        raise
        arcpy.AddError(ex.args)
