"""
BuildingSync Python Module

This module contains class names for each of the BuildingSync elements to make
it easier to build BuildingSync XML files.
"""

from datetime import datetime
from lxml import etree

from typing import Any, List, Tuple


class BSElement:
    element_type: str = ""
    element_attributes: List[str] = []
    element_enumerations: List[str] = []
    element_children: List[Tuple[str, type]] = []
    element_union: List[type] = []

    def __init__(self, *args, **kwargs):
        """Create an instance of a BuildingSync element."""
        self._children_by_name = dict(self.element_children)
        self._children_values = {}
        self._text = None

        if args:
            arg_value = args[0]
            if self.element_enumerations:
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if args[0] not in self.element_enumerations:
                    raise ValueError("invalid enumeration")
                self._text = args[0]

            elif self.element_union:
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                for subtype in self.element_union:
                    try:
                        value = subtype(args[0])
                        self._text = value._text
                        break
                    except (ValueError, TypeError):
                        pass
                else:
                    raise ValueError("invalid argument")

            elif self.element_type == "xs:boolean":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, bool):
                    raise TypeError("boolean expected")
                self._text = "true" if args[0] else "false"

            elif self.element_type == "xs:integer" or self.element_type == "xs:int":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, int):
                    raise TypeError("integer expected")
                self._text = f"{arg_value:d}"

            elif self.element_type == "xs:nonNegativeInteger":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, int):
                    raise TypeError("integer expected")
                if arg_value < 0:
                    raise ValueError("non-negative integer expected")
                self._text = f"{arg_value:d}"

            elif self.element_type == "xs:decimal":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, float):
                    raise TypeError("decimal (float) expected")
                self._text = f"{arg_value:f}"

            elif self.element_type == "xs:float":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, float):
                    raise TypeError("float expected")
                self._text = f"{arg_value:G}"

            elif self.element_type == "xs:string":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, str):
                    raise TypeError("string expected")
                self._text = arg_value

            elif self.element_type == "xs:date":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, datetime):
                    raise TypeError("date (datetime) expected")
                formatted = arg_value.isoformat()
                self._text = formatted[: formatted.find("T")]

            elif self.element_type == "xs:time":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, str):
                    raise TypeError("time (datetime) expected")
                formatted = arg_value.isoformat()
                self._text = formatted[formatted.find("T") + 1 :]

            elif self.element_type == "xs:dateTime":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, str):
                    raise TypeError("datetime expected")
                self._text = arg_value.isoformat()

            elif self.element_type == "xs:gMonthDay":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, str):
                    raise TypeError("datetime expected")
                self._text = arg_value.strftime("%m-%d")

            elif self.element_type == "xs:gYear":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, int):
                    raise TypeError("integer expected")
                self._text = f"{arg_value:d}"

            else:
                # add the args as child elements
                for arg_value in args:
                    self += arg_value

        self._attributes = kwargs

    def __getattr__(self, attr):
        """Get the value of a child element."""
        if attr.startswith("_"):
            return object.__getattribute__(self, attr)

        # make sure the attribute exists and it has been given a value
        if attr not in self._children_by_name:
            raise AttributeError(
                f"{repr(self.__class__.__name__)} object has no child {repr(attr)}"
            )
        if attr not in self._children_values:
            raise ValueError(f"{repr(attr)} not set")

        # most of the time the elements are provided once, so returning the
        # one that was provided is easier, but if there is more than one
        # this returns the entire list
        values = self._children_values[attr]
        if len(values) == 1:
            return values[0]
        else:
            return values

    def __setattr__(self, attr, value):
        """Set the value of a child element."""
        if attr.startswith("_"):
            return super().__setattr__(attr, value)

        # make sure the attribute exists and the value is the correct type
        if attr not in self._children_by_name:
            raise AttributeError(
                f"{repr(self.__class__.__name__)} object has no child {repr(attr)}"
            )
        if not isinstance(value, self._children_by_name[attr]):
            raise ValueError(
                f"{repr(attr)} invalid type, expecting {self._children_by_name[attr]}"
            )

        # setting an attribute value is an error if there is already a value
        # that has been set
        if attr in self._children_values:
            raise ValueError(f"{repr(attr)} already set")

        # save the value
        self._children_values[attr] = [value]

    def __add__(self, value):
        """Add an element value by finding the child element name with the
        correct class.  Return this element so other child element values can
        be added like 'thing + Child1() + Child2()'.
        """
        for child_name, child_type in self.element_children:
            if isinstance(value, child_type):
                break
        else:
            child_type_names = list(
                child_type.__name__ for child_name, child_type in self.element_children
            )
            raise ValueError(f"expecting one of: {', '.join(child_type_names)}")

        # if this child already has a value, add this to the end
        if child_name in self._children_values:
            self._children_values[child_name].append(value)
        else:
            self._children_values[child_name] = [value]

        return self

    def __iadd__(self, value) -> None:
        """Statment form of 'add'."""
        return self + value

    def set(self, attr: str, value: str) -> None:
        """Set an XML attribute value for the element."""
        assert isinstance(value, str)
        self._attributes[attr] = value

    def __setitem__(self, item: str, value: str) -> None:
        """Array form 'element[attr] = value' of 'element.set(attr, value)."""
        assert isinstance(value, str)
        self._attributes[item] = value

    def get(self, attr: str) -> Any:
        """Return an XML attribute value for the element."""
        return self._attributes[attr]

    def __getitem__(self, item: str) -> str:
        """Array form of 'element.get(attr)'."""
        return self._attributes[item]

    def toxml(self, root=None, child_name=None) -> Any:
        """Return an ElementTree element.  If the root is provided the element
        will be a child of the root (a subelement).  If the child_name is
        provided it will be used for the element name, otherwise it defaults
        to the class name.
        """
        # if child name was provided, this element was part of a complex type
        # where the element name doesn't match the element type name
        element_name = child_name or self.__class__.__name__

        # if no root was provided, make one, otherwise this is a child
        # element of the root
        if root is None:
            myroot = etree.Element(element_name)
        else:
            myroot = etree.SubElement(root, element_name)

        # maybe I have a value
        if self._text:
            myroot.text = str(self._text)

        # maybe I have attributes
        for k, v in self._attributes.items():
            myroot.set(k, v)

        # maybe I have children
        for child_name, child_type in self.element_children:
            for child_value in self._children_values.get(child_name, []):
                child_value.toxml(myroot, child_name)

        # return this "root" element
        return myroot

    def __str__(self):
        """Convert the element into a string."""
        return etree.tostring(self.toxml(), pretty_print=True).decode()


# BuildingSync.Programs.Program.ProgramDate
class ProgramDate(BSElement):
    """Date associated with the program."""

    element_type = "xs:date"


# BuildingSync.Programs.Program.ProgramFundingSource
class ProgramFundingSource(BSElement):
    """The source of funding or sponsor of the program."""

    element_type = "xs:string"


# BuildingSync.Programs.Program.ProgramClassification
class ProgramClassification(BSElement):
    """The classification or type of the program."""

    element_type = "xs:string"
    element_enumerations = [
        "Audit",
        "Performance",
        "Deemed",
        "Retrofit",
        "Rebate",
        "Other",
        "Not Applicable",
    ]


# Tightness
class Tightness(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Very Tight",
        "Tight",
        "Average",
        "Leaky",
        "Very Leaky",
        "Unknown",
    ]


# BuildingSync.Facilities.Facility.Systems.AirInfiltrationSystems.AirInfiltrationSystem.AirInfiltrationNotes
class AirInfiltrationNotes(BSElement):
    """Details about the the assessment. This might include methods used, criteria, evidence, or basis of evaluation."""

    element_type = "xs:string"


# BuildingSync.Facilities.Facility.Systems.AirInfiltrationSystems.AirInfiltrationSystem.AirInfiltrationValue
class AirInfiltrationValue(BSElement):
    """The measured value from the Air Infiltration test."""

    element_type = "xs:decimal"


# BuildingSync.Facilities.Facility.Systems.AirInfiltrationSystems.AirInfiltrationSystem.AirInfiltrationValueUnits
class AirInfiltrationValueUnits(BSElement):
    """Units associated with Air Infiltration Value."""

    element_type = "xs:string"
    element_enumerations = [
        "CFM25",
        "CFM50",
        "CFM75",
        "CFMnatural",
        "ACH50",
        "ACHnatural",
        "Effective Leakage Area",
        "Other",
    ]


# BuildingSync.Facilities.Facility.Systems.AirInfiltrationSystems.AirInfiltrationSystem.AirInfiltrationTest
class AirInfiltrationTest(BSElement):
    """Type of air infiltration test performed on the building."""

    element_type = "xs:string"
    element_enumerations = ["Blower door", "Tracer gas", "Checklist", "Other"]


# BuildingSync.Facilities.Facility.Systems.WaterInfiltrationSystems.WaterInfiltrationSystem.LocationsOfExteriorWaterIntrusionDamages.LocationsOfExteriorWaterIntrusionDamage
class LocationsOfExteriorWaterIntrusionDamage(BSElement):
    """Location of observed moisture problems on the outside of the building."""

    element_type = "xs:string"
    element_enumerations = [
        "Roof",
        "Interior ceiling",
        "Foundation",
        "Basement",
        "Crawlspace",
        "Walls",
        "Around windows",
        "Other",
    ]


# BuildingSync.Facilities.Facility.Systems.WaterInfiltrationSystems.WaterInfiltrationSystem.LocationsOfInteriorWaterIntrusionDamages.LocationsOfInteriorWaterIntrusionDamage
class LocationsOfInteriorWaterIntrusionDamage(BSElement):
    """Location of observed moisture problems on the inside of the building."""

    element_type = "xs:string"
    element_enumerations = ["Kitchen", "Bathroom", "Basement", "Other"]


# BuildingSync.Facilities.Facility.Systems.WaterInfiltrationSystems.WaterInfiltrationSystem.WaterInfiltrationNotes
class WaterInfiltrationNotes(BSElement):
    """Details about the the assessment. This might include methods used, criteria, evidence, or basis of evaluation."""

    element_type = "xs:string"


# PremisesName
class PremisesName(BSElement):
    """Name identifying the premises. This could be the name of the complex, the building, or the space within a building, such as a classroom number."""

    element_type = "xs:string"


# PremisesNotes
class PremisesNotes(BSElement):
    """Details about the premises."""

    element_type = "xs:string"


# eGRIDRegionCode
class eGRIDRegionCode(BSElement):
    """The eGRID (Emissions and Generation Resource Database) region code associated with the data being described. WARNING: Element MORE was a typo and will be removed, use MROE."""

    element_type = "xs:string"
    element_enumerations = [
        "AKGD",
        "AKMS",
        "AZNM",
        "CAMX",
        "ERCT",
        "FRCC",
        "HIMS",
        "HIOA",
        "MORE",
        "MROE",
        "MROW",
        "NEWE",
        "NWPP",
        "NYCW",
        "NYLI",
        "NYUP",
        "RFCE",
        "RFCM",
        "RFCW",
        "RMPA",
        "SPNO",
        "SPSO",
        "SRMV",
        "SRMW",
        "SRSO",
        "SRTV",
        "SRVC",
        "Other",
    ]


# Longitude
class Longitude(BSElement):
    """Distance measured in degrees east or west from an imaginary line (called the prime meridian) that goes from the North Pole to the South Pole and that passes through Greenwich, England. (degrees)"""

    element_type = "xs:decimal"


# Latitude
class Latitude(BSElement):
    """Distance north or south of the equator measured in degrees up to 90 degrees. (degrees)"""

    element_type = "xs:decimal"


# Ownership
class Ownership(BSElement):
    """The type of organization, association, business, etc. that owns the premises."""

    element_type = "xs:string"
    element_enumerations = [
        "Property management company",
        "Corporation/partnership/LLC",
        "Privately owned",
        "Individual",
        "Franchise",
        "Religious organization",
        "Non-profit organization",
        "Other non-government",
        "Government",
        "Federal government",
        "State government",
        "Local government",
        "Other",
        "Unknown",
    ]


# OwnershipStatus
class OwnershipStatus(BSElement):
    """Ownership status of the premises with respect to the occupant."""

    element_type = "xs:string"
    element_enumerations = [
        "Owned",
        "Mortgaged",
        "Leased",
        "Rented",
        "Occupied without payment of rent",
        "Other",
        "Unknown",
    ]


# PrimaryContactID
class PrimaryContactID(BSElement):
    """Primary contact ID number for the premises."""


PrimaryContactID.element_attributes = [
    "IDref",  # IDREF
]

# BuildingType.BuildingClassification
class BuildingClassification(BSElement):
    """Specify the type of building."""

    element_type = "xs:string"
    element_enumerations = [
        "Commercial",
        "Residential",
        "Mixed use commercial",
        "Other",
    ]


# BuildingType.NAICSCode
class NAICSCode(BSElement):
    """North American Industry Classification System (NAICS) code."""

    element_type = "xs:string"


# BuildingType.PubliclySubsidized
class PubliclySubsidized(BSElement):
    """Does the building include multi-family housing that receives or received public funding for construction or operations (this does not include Housing Choice Voucher Program Section 8 or similar vouchers received by individual tenants)?"""

    element_type = "xs:boolean"


# BuildingType.NumberOfBusinesses
class NumberOfBusinesses(BSElement):
    """Number of separate business tenants within the premises."""

    element_type = "xs:integer"


# BuildingType.ConditionedFloorsAboveGrade
class ConditionedFloorsAboveGrade(BSElement):
    """Nominal number of floors which are fully above ground and are conditioned."""

    element_type = "xs:integer"


# BuildingType.ConditionedFloorsBelowGrade
class ConditionedFloorsBelowGrade(BSElement):
    """Nominal number of floors which are fully underground and are conditioned."""

    element_type = "xs:integer"


# BuildingType.UnconditionedFloorsAboveGrade
class UnconditionedFloorsAboveGrade(BSElement):
    """Nominal number of floors which are fully above ground and are unconditioned."""

    element_type = "xs:integer"


# BuildingType.UnconditionedFloorsBelowGrade
class UnconditionedFloorsBelowGrade(BSElement):
    """Nominal number of floors which are fully underground and are unconditioned."""

    element_type = "xs:integer"


# BuildingAutomationSystem
class BuildingAutomationSystem(BSElement):
    """Does the building include a building automation or management system?"""

    element_type = "xs:boolean"


# LightingAutomationSystem
class LightingAutomationSystem(BSElement):
    """Does the building include a lighting automation or management system?"""

    element_type = "xs:boolean"


# BuildingType.HistoricalLandmark
class HistoricalLandmark(BSElement):
    """Does the facility have historical landmark status (e.g., is the facility listed in the National Register of Historic Places)?"""

    element_type = "xs:boolean"


# BuildingType.AspectRatio
class AspectRatio(BSElement):
    """The ratio of width to length, of a premises."""

    element_type = "xs:decimal"


# BuildingType.Perimeter
class Perimeter(BSElement):
    """Length of a line forming the boundary around the premises. (ft)"""

    element_type = "xs:integer"


# BuildingType.TotalExteriorAboveGradeWallArea
class TotalExteriorAboveGradeWallArea(BSElement):
    """Above grade wall area exposed to the elements. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.TotalExteriorBelowGradeWallArea
class TotalExteriorBelowGradeWallArea(BSElement):
    """Below grade wall area exposed to the ground. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.HeightDistribution
class HeightDistribution(BSElement):
    """Uniformity of building height."""

    element_type = "xs:string"
    element_enumerations = ["Multiple Heights", "Uniform Height"]


# BuildingType.HorizontalSurroundings
class HorizontalSurroundings(BSElement):
    """Attachments to the outermost horizontal surfaces of the premises."""

    element_type = "xs:string"
    element_enumerations = [
        "No abutments",
        "Attached from Above",
        "Attached from Below",
        "Attached from Above and Below",
        "Unknown",
    ]


# BuildingType.VerticalSurroundings
class VerticalSurroundings(BSElement):
    """Attachments to the outermost vertical surfaces of the premises. This can be used if the more detailed input for Surface Exposure is not known. Illustrations for the constrained list choices will be provided when the web site is developed."""

    element_type = "xs:string"
    element_enumerations = [
        "Stand-alone",
        "Attached on one side",
        "Attached on two sides",
        "Attached on three sides",
        "Within a building",
        "Unknown",
    ]


# BuildingType.YearOccupied
class YearOccupied(BSElement):
    """Year in which the premises was first occupied. (CCYY)"""

    element_type = "xs:gYear"


# BuildingType.YearOfLastEnergyAudit
class YearOfLastEnergyAudit(BSElement):
    """Year of the most recent energy audit for this building. (CCYY)"""

    element_type = "xs:gYear"


# BuildingType.RetrocommissioningDate
class RetrocommissioningDate(BSElement):
    """Date retro-commissioning or recommissioning was last conducted. (CCYY-MM-DD)"""

    element_type = "xs:date"


# BuildingType.YearOfLatestRetrofit
class YearOfLatestRetrofit(BSElement):
    """Year an energy retrofit of the building was last completed. (CCYY)"""

    element_type = "xs:gYear"


# BuildingType.YearOfLastMajorRemodel
class YearOfLastMajorRemodel(BSElement):
    """Year of the most recent major remodel. For a remodel to be considered major, the work undertaken must have required a permit from the building department, or an inspection by a governing authority. (CCYY)"""

    element_type = "xs:gYear"


# BuildingType.PercentOccupiedByOwner
class PercentOccupiedByOwner(BSElement):
    """The percentage of gross floor area that is occupied by the owner of the premises and affiliates. (0-100) (%)"""

    element_type = "xs:decimal"


# BuildingType.PercentLeasedByOwner
class PercentLeasedByOwner(BSElement):
    """The percentage of gross floor area that is leased by the owner of the premises and affiliates. (0-100) (%)"""

    element_type = "xs:decimal"


# BuildingType.NumberOfFacilitiesOnSite
class NumberOfFacilitiesOnSite(BSElement):
    """Number of facilities on the site."""

    element_type = "xs:integer"


# BuildingType.OperatorType
class OperatorType(BSElement):
    """Entity responsible for the operation of the facility."""

    element_type = "xs:string"
    element_enumerations = [
        "Owner",
        "Occupant",
        "Tenant",
        "Landlord",
        "Other",
        "Unknown",
    ]


# BuildingType.SpatialUnits.SpatialUnit.SpatialUnitType
class SpatialUnitType(BSElement):
    """Unit type within the premises."""

    element_type = "xs:string"
    element_enumerations = [
        "Lots",
        "Parking spaces",
        "Apartment units",
        "Businesses",
        "Guest rooms",
        "Stations",
        "Buildings",
        "Areas",
        "Thermal Zones",
        "Floors",
        "Rooms",
        "Bedrooms",
        "Other",
        "Unknown",
    ]


# BuildingType.SpatialUnits.SpatialUnit.NumberOfUnits
class NumberOfUnits(BSElement):
    """Number of individual units within the premises."""

    element_type = "xs:integer"


# BuildingType.SpatialUnits.SpatialUnit.UnitDensity
class UnitDensity(BSElement):
    """Number of units per 1,000 square feet."""

    element_type = "xs:decimal"


# BuildingType.SpatialUnits.SpatialUnit.SpatialUnitOccupiedPercentage
class SpatialUnitOccupiedPercentage(BSElement):
    """Percentage of the spatial units that are occupied. (0-100) (%)"""

    element_type = "xs:decimal"


# BuildingType.FederalBuilding.Agency
class Agency(BSElement):
    """Federal agency, required to designate a building as a federal property in ENERGY STAR Portfolio Manager."""

    element_type = "xs:string"


# BuildingType.FederalBuilding.DepartmentRegion
class DepartmentRegion(BSElement):
    """Federal department/region, required to designate a building as a federal property in ENERGY STAR Portfolio Manager."""

    element_type = "xs:string"


# BuildingType.Assessments.Assessment.AssessmentProgram
class AssessmentProgram(BSElement):
    """Program which issues energy labels, ratings, or sustainability certifications."""

    element_type = "xs:string"
    element_enumerations = [
        "ENERGY STAR",
        "ENERGY STAR Certified Homes",
        "LEED",
        "Home Energy Upgrade Certificate of Energy Efficiency Performance",
        "Home Energy Upgrade Certificate of Energy Efficiency Improvements",
        "Passive House",
        "Living Building Challenge",
        "Green Globes",
        "Challenge Home",
        "WaterSense",
        "Indoor airPLUS",
        "NGBS ICC 700",
        "CMP Green Value Score",
        "RESNET HERS",
        "Home Energy Score",
        "ASHRAE Building EQ",
        "Commercial Building Energy Asset Score",
        "Other",
        "Unknown",
    ]


# BuildingType.Assessments.Assessment.AssessmentLevel
class AssessmentLevel(BSElement):
    """Value from assessment program, such as LEED "Platinum"."""

    element_type = "xs:string"
    element_enumerations = [
        "Bronze",
        "Silver",
        "Gold",
        "Emerald",
        "Certified",
        "Platinum",
        "One Star",
        "Two Star",
        "Three Star",
        "Four Star",
        "Other",
    ]


# BuildingType.Assessments.Assessment.AssessmentValue
class AssessmentValue(BSElement):
    """Value from certifications that produce a numeric metric, such as ENERGY STAR Score, Home Energy Rating System (HERS) Index Score, Home Energy Score."""

    element_type = "xs:decimal"


# BuildingType.Assessments.Assessment.AssessmentYear
class AssessmentYear(BSElement):
    """Year the assessment qualifications for recognition were documented. (CCYY)"""

    element_type = "xs:gYear"


# BuildingType.Assessments.Assessment.AssessmentVersion
class AssessmentVersion(BSElement):
    """Version of the assessment documentation, such as "2.0"."""

    element_type = "xs:string"


# BuildingType.Sections.Section.Sides.Side.SideNumber
class SideNumber(BSElement):
    """Alphanumeric designation of the side of the section as defined in the BuildingSync Geometry Reference Sheet."""

    element_type = "xs:string"
    element_enumerations = [
        "A1",
        "A2",
        "A3",
        "B1",
        "B2",
        "B3",
        "C1",
        "C2",
        "C3",
        "D1",
        "D2",
        "D3",
        "AO1",
        "BO1",
    ]


# BuildingType.Sections.Section.Sides.Side.SideLength
class SideLength(BSElement):
    """Length of a particular side of the section as defined in the BuildingSync Geometry Reference Sheet. (ft)"""

    element_type = "xs:decimal"


# EquipmentCondition
class EquipmentCondition(BSElement):
    """Assessed condition of equipment or system."""

    element_type = "xs:string"
    element_enumerations = ["Excellent", "Good", "Average", "Poor", "Other", "Unknown"]


# BuildingType.Sections.Section.Roofs.Roof.RoofID.SkylightIDs.SkylightID.PercentSkylightArea
class PercentSkylightArea(BSElement):
    """The percentage of the skylight area relative to the roof area. (0-100) (%)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.Roofs.Roof.RoofID.RoofArea
class RoofArea(BSElement):
    """Surface area of roof. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.Roofs.Roof.RoofID.RoofInsulatedArea
class RoofInsulatedArea(BSElement):
    """Insulated area of roof or ceiling. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.Ceilings.Ceiling.CeilingID.CeilingArea
class CeilingArea(BSElement):
    """Surface area of roof. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.Ceilings.Ceiling.CeilingID.CeilingInsulatedArea
class CeilingInsulatedArea(BSElement):
    """Insulated area of roof or ceiling. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.ExteriorFloors.ExteriorFloor.ExteriorFloorID.ExteriorFloorArea
class ExteriorFloorArea(BSElement):
    """Area of slab-on-grade, basement slab, or other floor over unconditioned space. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.Foundations.Foundation.FoundationID.FoundationArea
class FoundationArea(BSElement):
    """Area of slab-on-grade, basement slab, or other floor over unconditioned space. (ft2)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.SectionType
class SectionType(BSElement):
    """The type of section such as Whole building, Space function data, or other types. * Whole building - describes the whole building, Space function - describes a space function (refer to SPC 211 Standard for Commercial Building Energy Audits), Component - describes a subspace of a primary premises such as HVAC zone, retails shops in a mall, etc., Tenant - describes a section for a tenant, Virtual - describes a section loosely with potentially overlap with other sections and section types, Other - not well-described by other types."""

    element_type = "xs:string"
    element_enumerations = [
        "Whole building",
        "Space function",
        "Component",
        "Tenant",
        "Virtual",
        "Other",
    ]


# BuildingType.Sections.Section.FootprintShape
class FootprintShape(BSElement):
    """General shape of the section of the building as a footprint defined in the BuildingSync Geometry Reference Sheet."""

    element_type = "xs:string"
    element_enumerations = [
        "Rectangular",
        "L-Shape",
        "U-Shape",
        "H-Shape",
        "T-Shape",
        "O-Shape",
        "Other",
        "Unknown",
    ]


# BuildingType.Sections.Section.NumberOfSides
class NumberOfSides(BSElement):
    """Number of sides of the section of the building. Inclusion of this element is recommended when auc:FootprintShape is Other."""

    element_type = "xs:integer"


# BuildingType.Sections.Section.ThermalZoneLayout
class ThermalZoneLayout(BSElement):
    """Type of zoning used for space conditioning."""

    element_type = "xs:string"
    element_enumerations = [
        "Perimeter",
        "Perimeter and core",
        "Single zone",
        "Other",
        "Unknown",
    ]


# BuildingType.Sections.Section.PerimeterZoneDepth
class PerimeterZoneDepth(BSElement):
    """Depth of perimeter zone relative to the outside walls. (ft)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.SideA1Orientation
class SideA1Orientation(BSElement):
    """The orientation of the canonical A1 side of the shape, as defined in the BuildingSync Geometry Reference Sheet. (degrees clockwise from north)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.XOffset
class XOffset(BSElement):
    """X offset of the origin of the section, defined as the counter-clockwise vertex of the A1 side on the bottom floor, relative to an arbitrary fixed origin established for the facility. (See BuildingSync Geometry Reference Sheet). (ft)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.YOffset
class YOffset(BSElement):
    """Y offset of the origin of the section, defined as the counter-clockwise vertex of the A1 side on the bottom floor, relative to an arbitrary fixed origin established for the facility (see BuildingSync Geometry Reference Sheet). (ft)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.ZOffset
class ZOffset(BSElement):
    """Z offset of the origin of the section, defined as the counter-clockwise vertex of the A1 side on the bottom floor, relative to an arbitrary fixed origin established for the facility (see BuildingSync Geometry Reference Sheet). (ft)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.FloorsPartiallyBelowGrade
class FloorsPartiallyBelowGrade(BSElement):
    """Number of floors which are partially underground."""

    element_type = "xs:integer"


# BuildingType.Sections.Section.FloorToFloorHeight
class FloorToFloorHeight(BSElement):
    """Average height of the floors in a premises, measured from floor to floor. (ft)"""

    element_type = "xs:decimal"


# BuildingType.Sections.Section.FloorToCeilingHeight
class FloorToCeilingHeight(BSElement):
    """Floor to ceiling height for a premises. (ft)"""

    element_type = "xs:decimal"


# ThermalZoneType.SetpointTemperatureHeating
class SetpointTemperatureHeating(BSElement):
    """The lowest allowed range in setpoint. If there is no range, then the low and high setpoints are the same. (°F)"""

    element_type = "xs:decimal"


# ThermalZoneType.SetbackTemperatureHeating
class SetbackTemperatureHeating(BSElement):
    """Room temperature setting during reset periods. (°F)"""

    element_type = "xs:decimal"


# ThermalZoneType.HeatLowered
class HeatLowered(BSElement):
    """Times when the HVAC equipment is setback. For example, when the heat is lowered during the heating season, or the cooling setpoint increased during the cooling season."""

    element_type = "xs:string"
    element_enumerations = [
        "During the day",
        "At night",
        "During sleeping and unoccupied hours",
        "Never / rarely",
        "Other",
        "Unknown",
    ]


# ThermalZoneType.SetpointTemperatureCooling
class SetpointTemperatureCooling(BSElement):
    """The lowest allowed range in setpoint. If there is no range, then the low and high setpoints are the same. (°F)"""

    element_type = "xs:decimal"


# ThermalZoneType.SetupTemperatureCooling
class SetupTemperatureCooling(BSElement):
    """Room temperature setting during reset periods. (°F)"""

    element_type = "xs:decimal"


# ThermalZoneType.ACAdjusted
class ACAdjusted(BSElement):
    """Times when the HVAC equipment is setback. For example, when the heat is lowered during the heating season, or the cooling setpoint increased during the cooling season."""

    element_type = "xs:string"
    element_enumerations = [
        "During the day",
        "At night",
        "During sleeping and unoccupied hours",
        "Seasonal",
        "Never-rarely",
        "Other",
        "Unknown",
    ]


# ThermalZoneType.DeliveryIDs.DeliveryID
class DeliveryID(BSElement):
    """ID number of HVAC delivery systems supporting the zone."""


DeliveryID.element_attributes = [
    "IDref",  # IDREF
]

# ThermalZoneType.HVACScheduleIDs.HVACScheduleID
class HVACScheduleID(BSElement):
    """ID numbers of the heating, cooling, or other HVAC schedules associated with the zone."""


HVACScheduleID.element_attributes = [
    "IDref",  # IDREF
]

# SpaceType.OccupantsActivityLevel
class OccupantsActivityLevel(BSElement):
    """The activity level that drives the amount of internal gains due to occupants. "Low" corresponds to typical office/retail work (Sensible load 250 Btu/hr, Latent load 200 Btu/hr), "High" corresponds to heavier factory work or gymnasiums (Sensible load 580 Btu/hr, Latent load 870 Btu/hr)."""

    element_type = "xs:string"
    element_enumerations = ["Low", "High", "Unknown"]


# SpaceType.DaylitFloorArea
class DaylitFloorArea(BSElement):
    """Area of the space that is daylit. (ft2)"""

    element_type = "xs:decimal"


# SpaceType.DaylightingIlluminanceSetpoint
class DaylightingIlluminanceSetpoint(BSElement):
    """Lighting level used for controlling electric lights when daylighting is available. (foot-candles)"""

    element_type = "xs:decimal"


# SpaceType.PercentageOfCommonSpace
class PercentageOfCommonSpace(BSElement):
    """Percentage of gross floor area that is common space only. (0-100) (%)"""

    element_type = "xs:decimal"


# SpaceType.ConditionedVolume
class ConditionedVolume(BSElement):
    """Heated or cooled air volume of a premises. (ft3)"""

    element_type = "xs:integer"


# SpaceType.OccupancyScheduleIDs.OccupancyScheduleID
class OccupancyScheduleID(BSElement):
    """ID numbers of the occupancy schedules associated with the space."""


OccupancyScheduleID.element_attributes = [
    "IDref",  # IDREF
]

# ScheduleType.SchedulePeriodBeginDate
class SchedulePeriodBeginDate(BSElement):
    """Date when the schedule begins. (CCYY-MM-DD)"""

    element_type = "xs:date"


# ScheduleType.SchedulePeriodEndDate
class SchedulePeriodEndDate(BSElement):
    """Date when the schedule ends. (CCYY-MM-DD)"""

    element_type = "xs:date"


# ScheduleType.ScheduleDetails.ScheduleDetail.DayType
class DayType(BSElement):
    """Type of day for which the schedule will be specified."""

    element_type = "xs:string"
    element_enumerations = [
        "All week",
        "Weekday",
        "Weekend",
        "Saturday",
        "Sunday",
        "Holiday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]


# ScheduleType.ScheduleDetails.ScheduleDetail.ScheduleCategory
class ScheduleCategory(BSElement):
    """Type of schedule (e.g., occupancy, lighting, heating, etc.) that will be specified."""

    element_type = "xs:string"
    element_enumerations = [
        "Business",
        "Occupied",
        "Unoccupied",
        "Sleeping",
        "Public access",
        "Setback",
        "Operating",
        "HVAC equipment",
        "Cooling equipment",
        "Heating equipment",
        "Lighting",
        "Cooking equipment",
        "Miscellaneous equipment",
        "On-peak",
        "Off-peak",
        "Super off-peak",
        "Other",
    ]


# ScheduleType.ScheduleDetails.ScheduleDetail.DayStartTime
class DayStartTime(BSElement):
    """In military time (00 start of day). If the night before the schedule runs into this day, then start time is 00, while yesterday's end time is 24. For example, a night club may be open from 8PM Friday to 2AM Saturday, then on Friday: Start Hour is 20 and End Hour is 24, and on Saturday: Start hour is 00 and End Hour is 02. (hh:mm:ss.zzz)"""

    element_type = "xs:time"


# ScheduleType.ScheduleDetails.ScheduleDetail.DayEndTime
class DayEndTime(BSElement):
    """In military time (00 start of day). If the end hour is the next day, then this day ends at 24 and the next starts at 00 and ends at closing time. For example, a night club may be open from 8PM Friday to 2AM Saturday, then on Friday: Start Hour is 20 and End Hour is 24, and on Saturday: Start hour is 00 and End Hour is 02. (hh:mm:ss.zzz)"""

    element_type = "xs:time"


# ScheduleType.ScheduleDetails.ScheduleDetail.PartialOperationPercentage
class PartialOperationPercentage(BSElement):
    """Percent of category that is in operation. If Schedule Category is Occupancy, then the percent of occupants from typical max. If Schedule Category is equipment, then power as a percent of installed capacity. This field is not used for temperature or relative humidity settings. (0-100) (%)"""

    element_type = "xs:decimal"


# ContactType.ContactName
class ContactName(BSElement):
    """The name, first and last, associated with the contact."""

    element_type = "xs:string"


# ContactType.ContactCompany
class ContactCompany(BSElement):
    """Company name associated with the contact, if applicable."""

    element_type = "xs:string"


# ContactType.ContactTitle
class ContactTitle(BSElement):
    """The title or position of the contact within their organization."""

    element_type = "xs:string"


# ContactType.ContactRoles.ContactRole
class ContactRole(BSElement):
    """Characterization of the contact."""

    element_type = "xs:string"
    element_enumerations = [
        "Premises",
        "Occupant",
        "Agency",
        "Owner",
        "Customer",
        "Customer agreement",
        "Administrator",
        "Qualified Assessor",
        "Contributor",
        "Property Management Company",
        "Operator",
        "Energy Auditor",
        "Energy Modeler",
        "Contractor",
        "Implementer",
        "Financier",
        "Commissioning Agent",
        "MV Agent",
        "Evaluator",
        "Builder",
        "Service",
        "Billing",
        "Architect",
        "Mechanical Engineer",
        "Energy Consultant",
        "Service and Product Provider",
        "Authority Having Jurisdiction",
        "Utility",
        "Power plant",
        "Electric Distribution Utility (EDU)",
        "ESCO",
        "Facilitator",
        "Facility Manager",
        "Trainer",
        "Electrical Engineer",
        "Controls Engineer",
        "Lender",
        "Servicer",
        "Originator",
        "Submitter",
        "Other",
    ]


# ContactType.ContactTelephoneNumbers.ContactTelephoneNumber.ContactTelephoneNumberLabel
class ContactTelephoneNumberLabel(BSElement):
    """The type of telephone number, to distinguish between multiple instances of Telephone Number."""

    element_type = "xs:string"
    element_enumerations = ["Days", "Evenings", "Cell", "Other"]


# TelephoneNumber
class TelephoneNumber(BSElement):
    """Telephone Number."""

    element_type = "xs:string"


# ContactType.ContactEmailAddresses.ContactEmailAddress.ContactEmailAddressLabel
class ContactEmailAddressLabel(BSElement):
    """The type of email address, to distinguish between multiple instances of Email Address."""

    element_type = "xs:string"
    element_enumerations = ["Personal", "Work", "Other"]


# EmailAddress
class EmailAddress(BSElement):
    """Email address may be specified for customer, contractors, and other contacts or businesses."""

    element_type = "xs:string"


# TenantType.TenantName
class TenantName(BSElement):
    """The name of the tenant."""

    element_type = "xs:string"


# TenantType.TenantTelephoneNumbers.TenantTelephoneNumber.TenantTelephoneNumberLabel
class TenantTelephoneNumberLabel(BSElement):
    """The type of telephone number, to distinguish between multiple instances of Telephone Number."""

    element_type = "xs:string"
    element_enumerations = ["Days", "Evenings", "Cell", "Other"]


# TenantType.TenantEmailAddresses.TenantEmailAddress.TenantEmailAddressLabel
class TenantEmailAddressLabel(BSElement):
    """The type of email address, to distinguish between multiple instances of Email Address."""

    element_type = "xs:string"
    element_enumerations = ["Personal", "Work", "Other"]


# TenantType.ContactIDs.ContactID
class ContactID(BSElement):
    pass


ContactID.element_attributes = [
    "IDref",  # IDREF
]

# ScenarioType.ScenarioName
class ScenarioName(BSElement):
    """Name of the scenario for which energy use data is included. This may include benchmarks, baselines, and improved cases. For retrofits, each package represents a different scenario."""

    element_type = "xs:string"


# ScenarioType.ScenarioNotes
class ScenarioNotes(BSElement):
    """Details about the scenario."""

    element_type = "xs:string"


# TemporalStatus
class TemporalStatus(BSElement):
    """Temporal characteristic of this measurement."""

    element_type = "xs:string"
    element_enumerations = [
        "Pre retrofit",
        "Post retrofit",
        "Baseline",
        "Current",
        "Target",
        "Design Target",
        "Last billing period",
        "Additional to last billing period",
        "Current billing period",
        "Billed to date",
        "Current day",
        "Current day last year",
        "Previous day",
        "Previous day last year",
        "Other",
    ]


# ScenarioType.Normalization
class Normalization(BSElement):
    """Normalization criteria to shift or scaled the measurement, where the intention is that these normalized values allow the comparison of corresponding normalized values for different datasets."""

    element_type = "xs:string"
    element_enumerations = [
        "National Median",
        "Regional Median",
        "Adjusted to specific year",
        "Weather normalized",
        "Other",
    ]


# ScenarioType.AnnualHeatingDegreeDays
class AnnualHeatingDegreeDays(BSElement):
    """Heating degree days are calculated as the sum of the differences between daily average temperatures and the base temperature, calculated at the ASHRAE base temperature of 50F, unless otherwise specified. Use the Interval Frequency term to characterize whether the HDD calculation is for annual or monthly intervals. (°F-days)"""

    element_type = "xs:decimal"


# ScenarioType.AnnualCoolingDegreeDays
class AnnualCoolingDegreeDays(BSElement):
    """Cooling degree days are calculated as the sum of the differences between daily average temperatures and the base temperature, calculated at the ASHRAE base temperature of 65F, unless otherwise specified. Use the Interval Frequency term to characterize whether the HDD calculation is for annual or monthly intervals. (°F-days)"""

    element_type = "xs:decimal"


# ENERGYSTARScore
class ENERGYSTARScore(BSElement):
    """If "Custom" is used as an Identifier Type, this term can be used to specify the name of the Custom ID. This would be used to specify the name of the specific program that this identifier applies to, for example "Wisconsin Weatherization Program". It can also be used for the ENERGY STAR Portfolio Manager Standard IDs that are assigned to different Portfolio Manager programs, such as "NYC Building Identification Number (BIN)"."""

    element_type = "xs:decimal"


# ScenarioType.ScenarioType.Benchmark.BenchmarkType.CodeMinimum.CodeName
class CodeName(BSElement):
    """The name of an energy efficiency code or standard that is applied to building construction requirements."""

    element_type = "xs:string"
    element_enumerations = ["ASHRAE", "IECC", "California Title 24", "IgCC", "Other"]


# ScenarioType.ScenarioType.Benchmark.BenchmarkType.CodeMinimum.CodeVersion
class CodeVersion(BSElement):
    """The version number, such as "90.1" for ASHRAE Standard."""

    element_type = "xs:string"


# ScenarioType.ScenarioType.Benchmark.BenchmarkType.CodeMinimum.CodeYear
class CodeYear(BSElement):
    """Date for the Energy Code or Standard used with the Energy Code term. As the energy codes and standards are updated, dates are assigned for version control. There can be significant changes between different year versions, so it is important to capture the year of the standard as it applies to the building in question. (CCYY)"""

    element_type = "xs:gYear"


# ScenarioType.ScenarioType.Benchmark.BenchmarkType.StandardPractice.StandardPracticeDescription
class StandardPracticeDescription(BSElement):
    """General description of the standard practice represented by this scenario (e.g., builder standard practice, portfolio average, local practice)."""

    element_type = "xs:string"


# ScenarioType.ScenarioType.Benchmark.BenchmarkType.Other.OtherBenchmarkDescription
class OtherBenchmarkDescription(BSElement):
    """General description of the benchmark scenario (e.g., original design, building next door)."""

    element_type = "xs:string"


# ScenarioType.ScenarioType.Benchmark.BenchmarkTool
class BenchmarkTool(BSElement):
    """Benchmarking tools provide a performance ranking based on a peer group of similar buildings."""

    element_type = "xs:string"
    element_enumerations = [
        "Portfolio Manager",
        "Buildings Performance Database Tool",
        "EnergyIQ",
        "Labs21",
        "Fabs21",
        "Other",
    ]


# ScenarioType.ScenarioType.Benchmark.BenchmarkYear
class BenchmarkYear(BSElement):
    element_type = "xs:gYear"


# ScenarioType.ScenarioType.Benchmark.BenchmarkValue
class BenchmarkValue(BSElement):
    """The calculated score or rating for the benchmark scenario."""

    element_type = "xs:decimal"


# ReferenceCase
class ReferenceCase(BSElement):
    """ID number for scenario that serves as the reference case for calculating energy savings, simple payback, etc."""


ReferenceCase.element_attributes = [
    "IDref",  # IDREF
]

# ScenarioType.ScenarioType.PackageOfMeasures.MeasureIDs.MeasureID
class MeasureID(BSElement):
    """ID number of measure."""


MeasureID.element_attributes = [
    "IDref",  # IDREF
]

# LowMedHigh
class LowMedHigh(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Low", "Medium", "High"]


# ScenarioType.ScenarioType.PackageOfMeasures.SimpleImpactAnalysis.EstimatedAnnualSavings
class EstimatedAnnualSavings(LowMedHigh):
    """See SPC 211 Standard for Commercial Building Energy Audits section 6.1.5(e)"""


# ScenarioType.ScenarioType.PackageOfMeasures.SimpleImpactAnalysis.EstimatedROI
class EstimatedROI(LowMedHigh):
    """See SPC 211 Standard for Commercial Building Energy Audits section 6.1.5(f)"""


# ScenarioType.ScenarioType.PackageOfMeasures.SimpleImpactAnalysis.ImpactOnOccupantComfort
class ImpactOnOccupantComfort(BSElement):
    """See SPC 211 Standard for Commercial Building Energy Audits section 6.1.5(c)"""

    element_type = "xs:string"


# ResourceUnits
class ResourceUnits(BSElement):
    """Units for resource consumption or generation."""

    element_type = "xs:string"
    element_enumerations = [
        "Cubic Meters",
        "kcf",
        "MCF",
        "Gallons",
        "Wh",
        "kWh",
        "MWh",
        "Btu",
        "kBtu",
        "MMBtu",
        "therms",
        "lbs",
        "Klbs",
        "Mlbs",
        "Mass ton",
        "Ton-hour",
        "Other",
        "Unknown",
        "None",
    ]


# ScenarioType.ScenarioType.PackageOfMeasures.CostCategory
class CostCategory(BSElement):
    """Classification of the cost of the package (per SPC 211 Standard for Commercial Building Energy Audits sections 5.3.5 and 5.3.6)"""

    element_type = "xs:string"
    element_enumerations = ["Low-Cost or No-Cost", "Capital"]


# ScenarioType.ScenarioType.PackageOfMeasures.ImplementationPeriod
class ImplementationPeriod(BSElement):
    """Total period of time necessary to implement all measures in the package. (months)"""

    element_type = "xs:integer"


# ScenarioType.ScenarioType.PackageOfMeasures.PackageFirstCost
class PackageFirstCost(BSElement):
    """The sum of the initial expenditures to implement the package of measures; includes items such as equipment, transportation, installation, preparation for service, as well as other related costs for planning, designing, training, and managing the project during the first year. ($)"""

    element_type = "xs:decimal"


# ScenarioType.ScenarioType.PackageOfMeasures.ImplementationPeriodCostSavings
class ImplementationPeriodCostSavings(BSElement):
    """Total cost savings during the project implementation period. ($)"""

    element_type = "xs:decimal"


# ScenarioType.ScenarioType.PackageOfMeasures.PercentGuaranteedSavings
class PercentGuaranteedSavings(BSElement):
    """Percentage of cost savings guaranteed by the contractor. (%)"""

    element_type = "xs:decimal"


# ScenarioType.ScenarioType.PackageOfMeasures.ProjectMarkup
class ProjectMarkup(BSElement):
    """Percent markup applied to implementation costs, if any. (%)"""

    element_type = "xs:decimal"


# ScenarioType.ScenarioType.PackageOfMeasures.OtherFinancialIncentives
class OtherFinancialIncentives(BSElement):
    """Present value of funding gained from other financial incentives over the life of the project. ($)"""

    element_type = "xs:integer"


# ScenarioType.ScenarioType.PackageOfMeasures.RecurringIncentives
class RecurringIncentives(BSElement):
    """Funding gained from recurring financial incentives. ($/year)"""

    element_type = "xs:integer"


# CostEffectivenessScreeningMethod
class CostEffectivenessScreeningMethod(BSElement):
    """Method for calculating cost-effectiveness for measures or project."""

    element_type = "xs:string"
    element_enumerations = [
        "Simple payback",
        "Return on investment",
        "Lifecycle cost",
        "Net present value",
        "Internal rate of return",
        "Modified internal rate of return",
        "Levelized cost of energy",
        "Savings to investment ratio",
        "Other",
    ]


# ScenarioType.ScenarioType.PackageOfMeasures.NonquantifiableFactors
class NonquantifiableFactors(BSElement):
    """Description of the nonquantifiable factors. This might include improvements to indoor air quality, improvements to occupant comfort, improvements to occupant satisfaction, reducing glare, improvements to access to daylight, etc."""

    element_type = "xs:string"


# ScenarioType.WeatherType.Normalized.NormalizationYears
class NormalizationYears(BSElement):
    """Number of years included in normalized weather data."""

    element_type = "xs:integer"


# ScenarioType.WeatherType.Normalized.NormalizationStartYear
class NormalizationStartYear(BSElement):
    """First year included in normalized weather data."""

    element_type = "xs:gYear"


# WeatherDataSource
class WeatherDataSource(BSElement):
    """Method for determining weather data associated with the time series."""

    element_type = "xs:string"
    element_enumerations = [
        "On Site Measurement",
        "Weather Station",
        "TMY",
        "TMY2",
        "TMY3",
        "IWEC",
        "CWEC",
        "CZRV2",
        "Other",
    ]


# ScenarioType.WeatherType.AdjustedToYear.WeatherYear
class WeatherYear(BSElement):
    """Year to which the weather conditions are adjusted. (CCYY)"""

    element_type = "xs:gYear"


# ScenarioType.WeatherType.Actual
class Actual(BSElement):
    pass


Actual.element_children = [
    ("WeatherDataSource", WeatherDataSource),
]

# OtherType
class OtherType(BSElement):
    pass


# UtilityType.MeteringConfiguration
class MeteringConfiguration(BSElement):
    """The structure of how the various meters are arranged."""

    element_type = "xs:string"
    element_enumerations = [
        "Direct metering",
        "Master meter without sub metering",
        "Master meter with sub metering",
        "Other",
        "Unknown",
    ]


# UtilityType.TypeOfResourceMeter
class TypeOfResourceMeter(BSElement):
    """Meters can be divided into several categories based on their capabilities."""

    element_type = "xs:string"
    element_enumerations = [
        "Revenue grade meter",
        "Advanced resource meter",
        "Analog",
        "Interval",
        "Net",
        "Smart meter",
        "PDU input meter",
        "IT equipment input meter",
        "Supply UPS output meter",
        "PDU output meter",
        "Other",
        "Unknown",
    ]


# UtilityType.FuelInterruptibility
class FuelInterruptibility(BSElement):
    """This refers to the practice of supplementing fuel (electricity, natural gas, fuel oil.) by other means when there are interruptions in supply from the utility."""

    element_type = "xs:string"
    element_enumerations = ["Interruptible", "Firm", "Other", "Unknown"]


# UtilityType.EIAUtilityID
class EIAUtilityID(BSElement):
    """EIA Utility ID as found in EIA-861 and as available in OpenEI."""

    element_type = "xs:nonNegativeInteger"


# UtilityType.UtilityName
class UtilityName(BSElement):
    """Name of utility company billing a Resource."""

    element_type = "xs:string"


# UtilityType.PowerPlant
class PowerPlant(BSElement):
    """Name of an individual power plant to which the property is directly connected."""

    element_type = "xs:string"


# UtilityType.ElectricDistributionUtility
class ElectricDistributionUtility(BSElement):
    """The company responsible for maintaining the utility lines and the electric distribution to the property. Note that the EDU is not the just "the utility company." In some states the energy markets are deregulated. This means that a property may contract with Company A to provide the power supply (energy from the power plant), while Company B will continue to provide the electric distribution (Company B is the EDU)."""

    element_type = "xs:string"


# UtilityType.SourceSiteRatio
class SourceSiteRatio(BSElement):
    """Ratio of energy consumed at a central power plant to that delivered to a customer."""

    element_type = "xs:decimal"


# ApplicableStartDateForEnergyRate
class ApplicableStartDateForEnergyRate(BSElement):
    """The date from which the rate is applicable. (MM-DD)"""

    element_type = "xs:gMonthDay"


# ApplicableEndDateForEnergyRate
class ApplicableEndDateForEnergyRate(BSElement):
    """The date after which the rate is not applicable. (MM-DD)"""

    element_type = "xs:gMonthDay"


# ApplicableStartDateForDemandRate
class ApplicableStartDateForDemandRate(BSElement):
    """The date from which the rate is applicable. (MM-DD)"""

    element_type = "xs:gMonthDay"


# ApplicableEndDateForDemandRate
class ApplicableEndDateForDemandRate(BSElement):
    """The date after which the rate is not applicable. (MM-DD)"""

    element_type = "xs:gMonthDay"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate.RatePeriods.RatePeriod.TimeOfUsePeriods.TimeOfUsePeriod.TOUNumberForRateStructure
class TOUNumberForRateStructure(BSElement):
    """The number associated with the TOU period."""

    element_type = "xs:int"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate.RatePeriods.RatePeriod.TimeOfUsePeriods.TimeOfUsePeriod.ApplicableStartTimeForEnergyRate
class ApplicableStartTimeForEnergyRate(BSElement):
    """The time of day from which the rate is applicable. (hh:mm:ss)"""

    element_type = "xs:time"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate.RatePeriods.RatePeriod.TimeOfUsePeriods.TimeOfUsePeriod.ApplicableEndTimeForEnergyRate
class ApplicableEndTimeForEnergyRate(BSElement):
    """The time of day after which the rate is not applicable. (hh:mm:ss)"""

    element_type = "xs:time"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate.RatePeriods.RatePeriod.TimeOfUsePeriods.TimeOfUsePeriod.ApplicableStartTimeForDemandRate
class ApplicableStartTimeForDemandRate(BSElement):
    """The time of day from which the rate is applicable. (hh:mm:ss)"""

    element_type = "xs:time"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate.RatePeriods.RatePeriod.TimeOfUsePeriods.TimeOfUsePeriod.ApplicableEndTimeForDemandRate
class ApplicableEndTimeForDemandRate(BSElement):
    """The time of day after which the rate is not applicable. (hh:mm:ss)"""

    element_type = "xs:time"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates.TieredRate.RatePeriods.RatePeriod.RateTiers.RateTier.ConsumptionEnergyTierDesignation
class ConsumptionEnergyTierDesignation(BSElement):
    """For electricity pricing that is based on tiered pricing, each tier is allotted a certain maximum (kWh), above which the user is moved to the next tier that has a different unit pricing."""

    element_type = "xs:integer"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates.TieredRate.RatePeriods.RatePeriod.RateTiers.RateTier.MaxkWhUsage
class MaxkWhUsage(BSElement):
    """The maximum amount of kWh used at which a kWh rate is applied. (kWh)"""

    element_type = "xs:decimal"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates.TieredRate.RatePeriods.RatePeriod.RateTiers.RateTier.MaxkWUsage
class MaxkWUsage(BSElement):
    """The maximum amount of kW used at which a kW rate is applied. (kW)"""

    element_type = "xs:decimal"


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates.TieredRate.TierDirection
class TierDirection(BSElement):
    """Whether the rates increase or decrease as energy use increases."""

    element_type = "xs:string"
    element_enumerations = ["Increasing", "Decreasing", "Other"]


# UnknownType
class UnknownType(BSElement):
    pass


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.RealTimePricing
class RealTimePricing(BSElement):
    """(RTP) - pricing rates generally apply to usage on an hourly basis."""


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.VariablePeakPricing
class VariablePeakPricing(BSElement):
    """(VPP) - a hybrid of time-of-use and real-time pricing where the different periods for pricing are defined in advance (e.g., on-peak=6 hours for summer weekday afternoon; off-peak = all other hours in the summer months), but the price established for the on-peak period varies by utility and market conditions."""


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.CriticalPeakPricing
class CriticalPeakPricing(BSElement):
    """(CPP) - when utilities observe or anticipate high wholesale market prices or power system emergency conditions, they may call critical events during a specified time period (e.g., 3 p.m.—6 p.m. on a hot summer weekday), the price for electricity during these time periods is substantially raised. Two variants of this type of rate design exist: one where the time and duration of the price increase are predetermined when events are called and another where the time and duration of the price increase may vary based on the electric grid’s need to have loads reduced."""


# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.CriticalPeakRebates
class CriticalPeakRebates(BSElement):
    """(CPR) - when utilities observe or anticipate high wholesale market prices or power system emergency conditions, they may call critical events during pre-specified time periods (e.g., 3 p.m.—6 p.m. summer weekday afternoons), the price for electricity during these time periods remains the same but the customer is refunded at a single, predetermined value for any reduction in consumption relative to what the utility deemed the customer was expected to consume."""


# UtilityType.RateSchedules.RateSchedule.NetMetering.AverageMarginalSellRate
class AverageMarginalSellRate(BSElement):
    """Annual average rate to sell a unit of electricity back to the utility from customer site electricity generation through PV, wind etc. ($/kWh)"""

    element_type = "xs:decimal"


# UtilityType.RateSchedules.RateSchedule.RateStructureName
class RateStructureName(BSElement):
    """The name or title of the rate structure."""

    element_type = "xs:string"


# UtilityType.RateSchedules.RateSchedule.RateStructureSector
class RateStructureSector(BSElement):
    """Sector to which the rate structure is applicable."""

    element_type = "xs:string"
    element_enumerations = ["Residential", "Commercial", "Industrial", "Other"]


# UtilityType.RateSchedules.RateSchedule.ReferenceForRateStructure
class ReferenceForRateStructure(BSElement):
    """Reference or hyper link for the rate schedule, tariff book."""

    element_type = "xs:string"


# UtilityType.RateSchedules.RateSchedule.RateStructureEffectiveDate
class RateStructureEffectiveDate(BSElement):
    """The first date the rate schedule becomes applicable. (CCYY-MM-DD)"""

    element_type = "xs:date"


# UtilityType.RateSchedules.RateSchedule.RateStructureEndDate
class RateStructureEndDate(BSElement):
    """The date at which the rate schedule is no longer applicable. (CCYY-MM-DD)"""

    element_type = "xs:date"


# UtilityType.RateSchedules.RateSchedule.ReactivePowerCharge
class ReactivePowerCharge(BSElement):
    """The additional charge for low power factor. ($/kVAR)"""

    element_type = "xs:decimal"


# UtilityType.RateSchedules.RateSchedule.MinimumPowerFactorWithoutPenalty
class MinimumPowerFactorWithoutPenalty(BSElement):
    """Minimum power factor that needs to maintained without any penalties. (0-1) (fraction)"""

    element_type = "xs:decimal"


# UtilityType.RateSchedules.RateSchedule.FixedMonthlyCharge
class FixedMonthlyCharge(BSElement):
    """The fixed charge or fee billed monthly regardless of consumption. ($/month)"""

    element_type = "xs:decimal"


# UtilityType.RateSchedules.RateSchedule.AverageMarginalCostRate
class AverageMarginalCostRate(BSElement):
    """The annual average cost of providing an additional unit of energy or water. Units should be consistent with Resource Units. ($/unit)"""

    element_type = "xs:decimal"


# ResourceUseType.ResourceUseNotes
class ResourceUseNotes(BSElement):
    """Details about the resource use. For Level 1 Audits, this should include notes on meter sampling methodology (if sampling was used) and identification of irregularities in monthly energy use (SPC 211 Standard for Commercial Building Energy Audits sections 6.1.2.1.d and 6.1.2.1.j)."""

    element_type = "xs:string"


# ResourceBoundary
class ResourceBoundary(BSElement):
    """The boundary that encompasses the measured resource."""

    element_type = "xs:string"
    element_enumerations = [
        "Site",
        "Source",
        "Onsite",
        "Offsite",
        "Net",
        "Gross",
        "Other",
    ]


# WaterResource
class WaterResource(BSElement):
    """Water type used as a resource on the premises."""

    element_type = "xs:string"
    element_enumerations = [
        "Potable water",
        "Wastewater",
        "Greywater",
        "Reclaimed water",
        "Captured rainwater",
        "Alternative water",
        "Other",
    ]


# ResourceUseType.PercentResource
class PercentResource(BSElement):
    """Percentage of total consumption of this fuel type represented by this Resource Use record. (%)"""

    element_type = "xs:decimal"


# ResourceUseType.SharedResourceSystem
class SharedResourceSystem(BSElement):
    """Situation that applies if a resource is shared with multiple premises, such as shared chilled water among buildings."""

    element_type = "xs:string"
    element_enumerations = [
        "Multiple buildings on a single lot",
        "Multiple buildings on multiple lots",
        "Not shared",
        "Other",
        "Unknown",
    ]


# ResourceUseType.PercentEndUse
class PercentEndUse(BSElement):
    """Percentage of total consumption of this fuel type for the specified end use represented by this Energy Use record. (%)"""

    element_type = "xs:decimal"


# ResourceUseType.AnnualFuelUseNativeUnits
class AnnualFuelUseNativeUnits(BSElement):
    """Sum of all time series values for the past year, in the original units. (units/yr)"""

    element_type = "xs:decimal"


# ResourceUseType.AnnualFuelUseConsistentUnits
class AnnualFuelUseConsistentUnits(BSElement):
    """Sum of all time series values for a particular or typical year, converted into million Btu of site energy. (MMBtu/yr)"""

    element_type = "xs:decimal"


# ResourceUseType.PeakResourceUnits
class PeakResourceUnits(BSElement):
    """Units for peak demand."""

    element_type = "xs:string"
    element_enumerations = ["kW", "MMBtu/day"]


# ResourceUseType.AnnualPeakNativeUnits
class AnnualPeakNativeUnits(BSElement):
    """Largest 15-min peak. (units)"""

    element_type = "xs:decimal"


# ResourceUseType.AnnualPeakConsistentUnits
class AnnualPeakConsistentUnits(BSElement):
    """Largest 15-min peak. (kW)"""

    element_type = "xs:decimal"


# ResourceUseType.AnnualFuelCost
class AnnualFuelCost(BSElement):
    """Annual cost of the resource ($)"""

    element_type = "xs:decimal"


# ResourceUseType.FuelUseIntensity
class FuelUseIntensity(BSElement):
    """Fuel use intensity is the energy associated with the selected fuel type divided by the gross floor area. (units/ft2/yr)"""

    element_type = "xs:decimal"


# ResourceUseType.MeterID
class MeterID(BSElement):
    """ID of the associated meter as seen by the facility manager"""

    element_type = "xs:string"


# ResourceUseType.ParentResourceUseID
class ParentResourceUseID(BSElement):
    """If this ResourceUse is intended to represent a submetered end use ('Total Lighting', 'Heating', 'Plug load', etc.), this ResourceUse should link to a parent ResourceUse that this would 'roll up to'."""


ParentResourceUseID.element_attributes = [
    "IDref",  # IDREF
]

# EndUse
class EndUse(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "All end uses",
        "Total lighting",
        "Interior lighting",
        "Exterior lighting",
        "Heating",
        "Cooling",
        "Ventilation",
        "Pump",
        "IT equipment",
        "Plug in electric vehicle",
        "Plug load",
        "Process load",
        "Conveyance",
        "Domestic hot water",
        "Refrigeration",
        "Cooking",
        "Dishwasher",
        "Laundry",
        "Pool heating",
        "On site generation",
    ]


# ResourceUseType.AnnualFuelUseLinkedTimeSeriesIDs.LinkedTimeSeriesID
class LinkedTimeSeriesID(BSElement):
    pass


LinkedTimeSeriesID.element_attributes = [
    "IDref",  # IDREF
]

# ResourceUseType.UtilityIDs.UtilityID
class UtilityID(BSElement):
    """ID of utility associated with this resource use."""


UtilityID.element_attributes = [
    "IDref",  # IDREF
]

# ResourceUseType.Emissions.Emission.EmissionBoundary
class EmissionBoundary(BSElement):
    """The boundary that encompasses the measured emissions."""

    element_type = "xs:string"
    element_enumerations = ["Direct", "Indirect", "Net", "Other"]


# ResourceUseType.Emissions.Emission.EmissionsType
class EmissionsType(BSElement):
    """Category of greenhouse gas or other emission."""

    element_type = "xs:string"
    element_enumerations = ["CO2e", "CO2", "CH4", "N2O", "NOx", "SO2", "Other"]


# ResourceUseType.Emissions.Emission.EmissionsFactor
class EmissionsFactor(BSElement):
    """Emissions factor associated with a Resource. (kg/MMBtu)"""

    element_type = "xs:decimal"


# ResourceUseType.Emissions.Emission.EmissionsFactorSource
class EmissionsFactorSource(BSElement):
    """Data source for emissions factors."""

    element_type = "xs:string"
    element_enumerations = ["US EIA", "US EPA", "Utility", "Other"]


# ResourceUseType.Emissions.Emission.GHGEmissions
class GHGEmissions(BSElement):
    """Emissions that result in gases that trap heat in the atmosphere. (kgCO2e)"""

    element_type = "xs:decimal"


# ResourceUseType.Emissions.Emission.AvoidedEmissions
class AvoidedEmissions(BSElement):
    """The avoided Greenhouse gas (GHG) emissions resulting from a renewable energy source or a system. (kgCO2e)"""

    element_type = "xs:decimal"


# AllResourceTotalType.SiteEnergyUseIntensity
class SiteEnergyUseIntensity(BSElement):
    """The Site Energy Use divided by the premises gross floor area. (kBtu/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.BuildingEnergyUse
class BuildingEnergyUse(BSElement):
    """The annual amount of all the energy the building consumes onsite. Calculated as imported energy (Eimp) + onsite renewable energy (Eg) - exported energy (Eexp) - net increase in stored imported energy (Es) (per ASHRAE 105-2014 Figure 5.6). (kBtu)"""

    element_type = "xs:decimal"


# AllResourceTotalType.BuildingEnergyUseIntensity
class BuildingEnergyUseIntensity(BSElement):
    """The Building Energy Use divided by the premises gross floor area. (kBtu/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.ImportedEnergyConsistentUnits
class ImportedEnergyConsistentUnits(BSElement):
    """Energy imported annually (per ASHRAE 105-2014 Figure 5.6). (MMbtu/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.OnsiteEnergyProductionConsistentUnits
class OnsiteEnergyProductionConsistentUnits(BSElement):
    """Energy produced onsite annually (per ASHRAE 105-2014 Figure 5.6). (MMbtu/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.ExportedEnergyConsistentUnits
class ExportedEnergyConsistentUnits(BSElement):
    """Energy exported annually (per ASHRAE 105-2014 Figure 5.6). (MMbtu/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.NetIncreaseInStoredEnergyConsistentUnits
class NetIncreaseInStoredEnergyConsistentUnits(BSElement):
    """Net increase in stored energy annually (per ASHRAE 105-2014 Figure 5.6). (MMbtu/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.EnergyCost
class EnergyCost(BSElement):
    """The annual cost associated with a selected 12 month time period for a premises. It can be an individual value for different energy types, and can also be an aggregated value across all energy types. ($)"""

    element_type = "xs:decimal"


# AllResourceTotalType.EnergyCostIndex
class EnergyCostIndex(BSElement):
    """The Energy Cost divided by the premises gross floor area. ($/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.OnsiteRenewableSystemElectricityExported
class OnsiteRenewableSystemElectricityExported(BSElement):
    """The portion of energy produced from the onsite renewable energy system(s) that is exported (not used onsite). (kWh)"""

    element_type = "xs:decimal"


# AllResourceTotalType.ElectricitySourcedFromOnsiteRenewableSystems
class ElectricitySourcedFromOnsiteRenewableSystems(BSElement):
    """Total electricity produced from resources that do not deplete when their energy is harnessed, such as sunlight, wind, waves, water flow, biological processes such as anaerobic digestion and geothermal energy. (kWh)"""

    element_type = "xs:decimal"


# AllResourceTotalType.SummerPeak
class SummerPeak(BSElement):
    """Peak demand in the summer. (kW)"""

    element_type = "xs:decimal"


# AllResourceTotalType.WinterPeak
class WinterPeak(BSElement):
    """Peak demand in the winter. (kW)"""

    element_type = "xs:decimal"


# AllResourceTotalType.WaterIntensity
class WaterIntensity(BSElement):
    """Water use from different sources divided by the premises gross floor area. (kgal/ft2)"""

    element_type = "xs:decimal"


# AllResourceTotalType.WaterCost
class WaterCost(BSElement):
    """Annual cost of water. ($)"""

    element_type = "xs:decimal"


# AllResourceTotalType.WasteWaterVolume
class WasteWaterVolume(BSElement):
    """Annual volume of water that is returned to a wastewater treatment facility. (kgal)"""

    element_type = "xs:decimal"


# TimeSeriesType.ReadingType
class ReadingType(BSElement):
    """Type of data recorded by the meter or other source."""

    element_type = "xs:string"
    element_enumerations = [
        "Point",
        "Median",
        "Average",
        "Total",
        "Peak",
        "Minimum",
        "Load factor",
        "Cost",
        "Unknown",
    ]


# TimeSeriesType.PeakType
class PeakType(BSElement):
    """When ReadingType is "Peak", this element specifies when the peak occurred."""

    element_type = "xs:string"
    element_enumerations = ["On-peak", "Off-peak", "Mid-peak", "Unknown"]


# TimeSeriesType.TimeSeriesReadingQuantity
class TimeSeriesReadingQuantity(BSElement):
    """Type of energy, water, power, weather metric included in the time series."""

    element_type = "xs:string"
    element_enumerations = [
        "Currency",
        "Cost",
        "Current",
        "Current Angle",
        "Demand",
        "Frequency",
        "Power",
        "Power Factor",
        "Energy",
        "Voltage",
        "Voltage Angle",
        "Distortion Power Factor",
        "Volumetric Flow",
        "Humidity ratio",
        "Relative humidity",
        "Diffuse Horizontal Radiation",
        "Direct Normal Radiation",
        "Global Horizontal Radiation",
        "Dry Bulb Temperature",
        "Wet Bulb Temperature",
        "Wind Speed",
        "Other",
    ]


# TimeSeriesType.IntervalDuration
class IntervalDuration(BSElement):
    """The duration of the time series in the units provided by IntervalDurationUnits"""

    element_type = "xs:integer"


# TimeSeriesType.IntervalReading
class IntervalReading(BSElement):
    """The numerical value of the reading. This has to be paired with Reading Type to specify whether this reading is mean, point, median, peak or minimum."""

    element_type = "xs:decimal"


# TimeSeriesType.Phase
class Phase(BSElement):
    """Phase information associated with electricity readings."""

    element_type = "xs:string"
    element_enumerations = [
        "Phase AN",
        "Phase A",
        "Phase AB",
        "Phase BN",
        "Phase B",
        "Phase CN",
        "Phase C",
        "Phase ABC",
        "Phase BC",
        "Phase CA",
        "Phase S1",
        "Phase S2",
        "Phase S1S2",
        "Phase S1N",
        "Phase S2N",
        "Phase S1S2N",
        "Other",
        "Unknown",
    ]


# TimeSeriesType.EnergyFlowDirection
class EnergyFlowDirection(BSElement):
    """Direction associated with current related time series data."""

    element_type = "xs:string"
    element_enumerations = ["Forward", "Reverse", "Unknown"]


# TimeSeriesType.HeatingDegreeDays
class HeatingDegreeDays(BSElement):
    """Heating degree days are calculated as the sum of the differences between daily average temperatures and the base temperature, calculated at the ASHRAE base temperature of 50F, unless otherwise specified. Use the Interval Frequency term to characterize whether the HDD calculation is for annual or monthly intervals. (°F-days)"""

    element_type = "xs:decimal"


# TimeSeriesType.CoolingDegreeDays
class CoolingDegreeDays(BSElement):
    """Cooling degree days are calculated as the sum of the differences between daily average temperatures and the base temperature, calculated at the ASHRAE base temperature of 65F, unless otherwise specified. Use the Interval Frequency term to characterize whether the HDD calculation is for annual or monthly intervals. (°F-days)"""

    element_type = "xs:decimal"


# TimeSeriesType.ResourceUseID
class ResourceUseID(BSElement):
    """ID number of resource use that this time series contributes to. This field is not used for non-energy data such as weather."""


ResourceUseID.element_attributes = [
    "IDref",  # IDREF
]

# TimeSeriesType.WeatherStationID
class WeatherStationID(BSElement):
    """ID number of weather station this time series contributes to."""


WeatherStationID.element_attributes = [
    "IDref",  # IDREF
]

# IntervalTime
class IntervalTime(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "1 minute",
        "10 minute",
        "15 minute",
        "30 minute",
        "Hour",
        "Day",
        "Week",
        "Month",
        "Annual",
        "Quarter",
        "Other",
        "Unknown",
    ]


# MeasureType.SystemCategoryAffected
class SystemCategoryAffected(BSElement):
    """Category of building system(s) affected by the measure. In some cases a single measure may include multiple components affecting multiple systems."""

    element_type = "xs:string"
    element_enumerations = [
        "Air Distribution",
        "Heating System",
        "Cooling System",
        "Other HVAC",
        "Lighting",
        "Domestic Hot Water",
        "Cooking",
        "Refrigeration",
        "Dishwasher",
        "Laundry",
        "Pump",
        "Fan",
        "Motor",
        "Heat Recovery",
        "Wall",
        "Roof",
        "Ceiling",
        "Fenestration",
        "Foundation",
        "General Controls and Operations",
        "Critical IT System",
        "Plug Load",
        "Process Load",
        "Conveyance",
        "Onsite Storage, Transmission, Generation",
        "Pool",
        "Water Use",
        "Other",
    ]


# MeasureType.MeasureScaleOfApplication
class MeasureScaleOfApplication(BSElement):
    """Scale at which the measure is applied, such as an individual system, multiple systems, or entire facility."""

    element_type = "xs:string"
    element_enumerations = [
        "Individual system",
        "Multiple systems",
        "Individual premise",
        "Multiple premises",
        "Entire facility",
        "Entire site",
        "Entire building",
        "Common areas",
        "Tenant areas",
    ]


# MeasureType.CustomMeasureName
class CustomMeasureName(BSElement):
    """Custom name of the measure, i.e. the name of the simulated measure."""

    element_type = "xs:string"


# MeasureType.LongDescription
class LongDescription(BSElement):
    """Long description of measure."""

    element_type = "xs:string"


# MeasureType.MVOption
class MVOption(BSElement):
    """Recommended approach for verification of energy savings for this measure, based on the International Performance Measurement and Verification Protocol (IPMVP)."""

    element_type = "xs:string"
    element_enumerations = [
        "Option A: Retrofit Isolation With Partial Measurement",
        "Option B: Retrofit Isolation With Full Measurement",
        "Option C: Whole Building Measurement",
        "Option D: Calibrated Simulation",
        "Combination",
        "Other",
    ]


# MeasureType.UsefulLife
class UsefulLife(BSElement):
    """Productive life that can be expected of measure or a project. (yrs)"""

    element_type = "xs:decimal"


# MeasureType.MeasureTotalFirstCost
class MeasureTotalFirstCost(BSElement):
    """The sum of the initial expenditures to implement each occurrence of the measure; includes items such as equipment, transportation, installation, preparation for service, as well as other costs directly related to the measure. Soft costs related to project planning and management should not be included for individual measures. ($)"""

    element_type = "xs:decimal"


# MeasureType.MeasureInstallationCost
class MeasureInstallationCost(BSElement):
    """Cost of measure installation activity. ($)"""

    element_type = "xs:decimal"


# MeasureType.MeasureMaterialCost
class MeasureMaterialCost(BSElement):
    """Costs of material needed to implement the measure. ($)"""

    element_type = "xs:decimal"


# MeasureType.CapitalReplacementCost
class CapitalReplacementCost(BSElement):
    """Estimated cost of replacing the measure at the end of its useful life, in current year dollars. ($)"""

    element_type = "xs:decimal"


# MeasureType.ResidualValue
class ResidualValue(BSElement):
    """The remaining value of the equipment associated with a measure or package at the end of the analysis period. ($)"""

    element_type = "xs:integer"


# MeasureType.Recommended
class Recommended(BSElement):
    """True if measure is recommended."""

    element_type = "xs:boolean"


# MeasureType.StartDate
class StartDate(BSElement):
    """Start date for implementation of a project or a measure. (CCYY-MM-DD)"""

    element_type = "xs:date"


# MeasureType.EndDate
class EndDate(BSElement):
    """Date when majority of the project or measure was completed and implemented (substantial completion). (CCYY-MM-DD)"""

    element_type = "xs:date"


# MeasureType.ImplementationStatus
class ImplementationStatus(BSElement):
    """Implementation status of measure."""

    element_type = "xs:string"
    element_enumerations = [
        "Proposed",
        "Evaluated",
        "Selected",
        "Initiated",
        "Discarded",
        "In Progress",
        "Completed",
        "MV",
        "Verified",
        "Unsatisfactory",
        "Other",
        "Unknown",
    ]


# MeasureType.DiscardReason
class DiscardReason(BSElement):
    """Reason why the proposed measure was discarded, if appropriate."""

    element_type = "xs:string"
    element_enumerations = ["Long payback", "Requires permit", "Other", "Unknown"]


# MeasureType.TypeOfMeasure.Replacements.Replacement.ExistingSystemReplaced
class ExistingSystemReplaced(BSElement):
    """ID numbers of any existing systems replaced by the measure."""


ExistingSystemReplaced.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.Replacements.Replacement.AlternativeSystemReplacement
class AlternativeSystemReplacement(BSElement):
    """ID numbers of alternative systems that would replace the existing systems."""


AlternativeSystemReplacement.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.ModificationRetrocommissions.ModificationRetrocommissioning.ExistingSystemAffected
class ExistingSystemAffected(BSElement):
    """ID numbers of any existing systems affected by the measure."""


ExistingSystemAffected.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.ModificationRetrocommissions.ModificationRetrocommissioning.ModifiedSystem
class ModifiedSystem(BSElement):
    """ID numbers of alternative systems that represent "improvements" to existing systems."""


ModifiedSystem.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.Additions.Addition.AlternativeSystemAdded
class AlternativeSystemAdded(BSElement):
    """ID numbers of alternative systems that would be added as part of the measure."""


AlternativeSystemAdded.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.Removals.Removal.ExistingSystemRemoved
class ExistingSystemRemoved(BSElement):
    """ID numbers of any existing systems removed as part of the measure."""


ExistingSystemRemoved.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.MeasureSavingsAnalysis.MeasureRank
class MeasureRank(BSElement):
    """Sequence in which the measure was analyzed relative to other measures. Ranking should be 1 if it is analyzed first, 2 if analyzed after Measure 1 is applied, etc. This accounts for interactive effects between measures. Ranking may be 1 for all measures if they are not analyzed as a package."""

    element_type = "xs:integer"


# MeasureType.MeasureSavingsAnalysis.OtherCostAnnualSavings
class OtherCostAnnualSavings(BSElement):
    """Annual savings for other non-energy costs, or increased revenue caused by measure implementation. ($)"""

    element_type = "xs:decimal"


# ReportType.ASHRAEAuditLevel
class ASHRAEAuditLevel(BSElement):
    """Energy audit level as defined in SPC 211 Standard for Commercial Building Energy Audits."""

    element_type = "xs:string"
    element_enumerations = [
        "Preliminary Energy-Use Analysis",
        "Level 1: Walk-through",
        "Level 2: Energy Survey and Analysis",
        "Level 3: Detailed Survey and Analysis",
    ]


# ReportType.RetrocommissioningAudit
class RetrocommissioningAudit(BSElement):
    """True if an assessment of retro- or re-commissioning measures was completed as part of the audit."""

    element_type = "xs:boolean"


# ReportType.AuditCost
class AuditCost(BSElement):
    """Total cost associated with the audit. ($)"""

    element_type = "xs:decimal"


# ReportType.DiscountFactor
class DiscountFactor(BSElement):
    """Discount factor applied to calculate present values of future cash flows. (0-100) (%)"""

    element_type = "xs:decimal"


# ReportType.AnalysisPeriod
class AnalysisPeriod(BSElement):
    """Period used for financial analysis. Can be combined with IntervalFrequency to specify the units. (yrs)"""

    element_type = "xs:decimal"


# ReportType.GasPriceEscalationRate
class GasPriceEscalationRate(BSElement):
    """Assumed annual increase in natural gas price. (%)"""

    element_type = "xs:decimal"


# ReportType.ElectricityPriceEscalationRate
class ElectricityPriceEscalationRate(BSElement):
    """Assumed annual increase in electricity price. (%)"""

    element_type = "xs:decimal"


# ReportType.WaterPriceEscalationRate
class WaterPriceEscalationRate(BSElement):
    """Assumed annual increase in water price. (%)"""

    element_type = "xs:decimal"


# ReportType.InflationRate
class InflationRate(BSElement):
    """Assumed annual inflation rate for non-energy costs. (%)"""

    element_type = "xs:decimal"


# ReportType.AuditExemption
class AuditExemption(BSElement):
    """Conditions under which the building is exempt from a mandated audit."""

    element_type = "xs:string"
    element_enumerations = [
        "EPA ENERGY STAR certified",
        "LEED certified",
        "Simple building",
        "Class 1 building",
        "Other",
        "None",
    ]


# ReportType.AuditorContactID
class AuditorContactID(BSElement):
    """Contact ID of auditor responsible for the audit report."""


AuditorContactID.element_attributes = [
    "IDref",  # IDREF
]

# ReportType.AuditDates.AuditDate.Date
class Date(BSElement):
    """Date of DateType enumeration. (CCYY-MM-DD)"""

    element_type = "xs:date"


# ReportType.AuditDates.AuditDate.DateType
class DateType(BSElement):
    """Type of AuditDate."""

    element_type = "xs:string"
    element_enumerations = ["Site Visit", "Conducted", "Completion", "Custom", "Other"]


# ReportType.AuditDates.AuditDate.CustomDateType
class CustomDateType(BSElement):
    """Custom name if DateType is Custom."""

    element_type = "xs:string"


# ReportType.OtherEscalationRates.OtherEscalationRate.EscalationRate
class EscalationRate(BSElement):
    """Assumed annual increase in price for the specified resource. (0-100) (%)"""

    element_type = "xs:decimal"


# AuditorQualificationType
class AuditorQualificationType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Professional Engineer (PE)",
        "Associated Air Balance Council (AABC) Certified Member Agency",
        "Associated Air Balance Council (AABC) Test and Balance Technician",
        "Association of Energy Engineers Certified Carbon Reduction Manager (CRM)",
        "Association of Energy Engineers Certified Sustainable Development Professional (CSDP)",
        "Association of Energy Engineers Certified Power Quality Professional (CPQ)",
        "Association of Energy Engineers Certified Demand Side Manager (CDSM)",
        "Association of Energy Engineers Certified Energy Procurement Professional (CEP)",
        "Association of Energy Engineers Certified Lighting Efficiency Professional (CLEP)",
        "Association of Energy Engineers Certified Measurement & Verification Professional (CMVP)",
        "Association of Energy Engineers Certified GeoExchange Designer Program (CGD)",
        "Association of Energy Engineers Certified Business Energy Professional (BEP)",
        "Association of Energy Engineers Certified Industrial Energy Professional (CIEP)",
        "Association of Energy Engineers Certified Water Efficiency Professional (CWEP)",
        "Association of Energy Engineers Energy Efficiency Practitioner (EEP)",
        "Association of Energy Engineers Renewable Energy Professional (REP)",
        "Association of Energy Engineers Distributed Generation Certified Professional (DGCP)",
        "Association of Energy Engineers Certified Building Energy Simulation Analyst (BESA)",
        "Association of Energy Engineers Performance Contracting and Funding Professional (PCF)",
        "Association of Energy Engineers Certified Residential Energy Auditor (REA)",
        "Association of Energy Engineers Certified Building Commissioning Firm Program (CBCF)",
        "Association of Energy Engineers Certified Green Building Engineer (GBE)",
        "Association of Energy Engineers Certified Energy Manager (CEM)",
        "Association of Energy Engineers Certified Energy Auditor (CEA)",
        "Association of Energy Engineers Certified Building Commissioning Professional (CBCP)",
        "Building Operator Certification (BOC): Level 1",
        "Building Operator Certification (BOC): Level 2",
        "Building Performance Institute (BPI) Certification",
        "Building Performance Institute (BPI): Building Analyst (BA)",
        "Building Performance Institute (BPI): Advanced Home Energy Professional (HEP)",
        "Building Performance Institute (BPI): Advanced Home Energy Professional - Energy Auditor (HEP-EA)",
        "Building Performance Institute (BPI): Advanced Home Energy Professional - Quality Control Inspector (HEP-QCI)",
        "Building Performance Institute (BPI): Advanced Home Energy Professional - Retrofit Installer (HEP-RI)",
        "Building Performance Institute (BPI): Advanced Home Energy Professional - Crew Leader (HEP-CL)",
        "Building Performance Institute (BPI): Multifamily Building Analyst",
        "Residential Energy Services Network (RESNET) Certification",
        "Residential Energy Services Network (RESNET) - Home Partner",
        "Registered Architect (RA)",
        "Refrigerating System Operating Engineer",
        "High Pressure Boiler Operating Engineer",
        "Certified Commissioning Professional (CCP)",
        "Associate Commissioning Professional (ACP)",
        "Existing Building Commissioning Professional (EBCP)",
        "Commissioning Process Management Professional (CPMP)",
        "Accredited Commissioning Process Authority Professional (CxAP)",
        "NYSERDA FlexTech Consultant",
        "ASHRAE Building Commissioning Professional (BCxP)",
        "ASHRAE Building Energy Assessment Professional (BEAP)",
        "ASHRAE Building Energy Modeling Professional (BEMP)",
        "Department of Buildings (DOB) Approved Agent",
        "High-Performance Building Design Professional (HBDP)",
        "GreenPoint Rater Existing Home Multifamily Rater",
        "HERS Whole House (HERS II) Rater",
        "International Union of Operating Engineers Certified Energy Specialist",
        "Northwest Energy Education Institute Energy Management Certification",
        "PhD in Mechanical Engineering",
        "Other",
        "None",
    ]


# State
class State(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "AA",
        "AE",
        "AL",
        "AK",
        "AP",
        "AS",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "DC",
        "FM",
        "FL",
        "GA",
        "GU",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MH",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "MP",
        "OH",
        "OK",
        "OR",
        "PW",
        "PA",
        "PR",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VI",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "AB",
        "BC",
        "MB",
        "NB",
        "NL",
        "NS",
        "ON",
        "PE",
        "QC",
        "SK",
        "NT",
        "NU",
        "YT",
    ]


# ReportType.Qualifications.Qualification.AuditTeamMemberCertificationType
class AuditTeamMemberCertificationType(AuditorQualificationType):
    """Type of certification held by an auditor team member."""


# ReportType.Qualifications.Qualification.AuditorQualificationNumber
class AuditorQualificationNumber(BSElement):
    """Certificate number, license number, etc., of AuditorQualification."""

    element_type = "xs:string"


# ReportType.Qualifications.Qualification.CertificationExpirationDate
class CertificationExpirationDate(BSElement):
    """Date that the AuditorQualification expires. (CCYY-MM-DD)"""

    element_type = "xs:date"


# ReportType.Qualifications.Qualification.CertifiedAuditTeamMemberContactID
class CertifiedAuditTeamMemberContactID(BSElement):
    """Contact ID of auditor team member with certification."""


CertifiedAuditTeamMemberContactID.element_attributes = [
    "IDref",  # IDREF
]

# Location
class Location(BSElement):
    """Location of system."""

    element_type = "xs:string"
    element_enumerations = [
        "Roof",
        "Mechanical Room",
        "Mechanical Floor",
        "Penthouse",
        "Interior",
        "Exterior",
        "Closet",
        "Garage",
        "Attic",
        "Other",
        "Unknown",
    ]


# Priority
class Priority(BSElement):
    """Order of precedence relative to other applicable systems. Enter Primary if this is the only system."""

    element_type = "xs:string"
    element_enumerations = ["Primary", "Secondary", "Tertiary", "Back-up", "Other"]


# HVACSystemType.FrequencyOfMaintenance
class FrequencyOfMaintenance(BSElement):
    """Frequency of maintenance on the premises or equipment."""

    element_type = "xs:string"
    element_enumerations = [
        "As needed",
        "Daily",
        "Weekly",
        "Bi-weekly",
        "Monthly",
        "Semi-quarterly",
        "Quarterly",
        "Semi-annually",
        "Annually",
        "Unknown",
    ]


# Quantity
class Quantity(BSElement):
    """Number of systems of this type."""

    element_type = "xs:integer"


# ElectricResistanceType
class ElectricResistanceType(BSElement):
    pass


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.Furnace.FurnaceType
class FurnaceType(BSElement):
    """General type of furnace used for space heating."""

    element_type = "xs:string"
    element_enumerations = [
        "Warm air",
        "Fireplace",
        "Heating stove",
        "Built-in heater",
        "Individual space heater",
        "Other",
        "Unknown",
    ]


# BurnerType
class BurnerType(BSElement):
    """Type of burner on boiler or furnace, if applicable."""

    element_type = "xs:string"
    element_enumerations = [
        "Atmospheric",
        "Power",
        "Sealed Combustion",
        "Rotary Cup",
        "Other",
        "Unknown",
    ]


# BurnerControlType
class BurnerControlType(BSElement):
    """Control type of burner, if applicable."""

    element_type = "xs:string"
    element_enumerations = [
        "Full Modulation Manual",
        "Full Modulation Automatic",
        "Step Modulation",
        "High Low",
        "On Off",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.Furnace.BurnerQuantity
class BurnerQuantity(BSElement):
    """The number of burners."""

    element_type = "xs:integer"


# BurnerYearInstalled
class BurnerYearInstalled(BSElement):
    """Year that the burner was installed"""

    element_type = "xs:gYear"


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.Furnace.BurnerTurndownRatio
class BurnerTurndownRatio(BSElement):
    """If applicable, the turndown ratio for the burner. (full input/minimum input)"""

    element_type = "xs:decimal"


# IgnitionType
class IgnitionType(BSElement):
    """Ignition mechanism in gas heating equipment. Either pilot light or an intermittent ignition device (IID)."""

    element_type = "xs:string"
    element_enumerations = [
        "Intermittent ignition device",
        "Pilot light",
        "Other",
        "Unknown",
    ]


# DraftType
class DraftType(BSElement):
    """Draft mechanism used for drawing air through the boiler or furnace."""

    element_type = "xs:string"
    element_enumerations = [
        "Natural",
        "Mechanical forced",
        "Mechanical induced",
        "Other",
        "Unknown",
    ]


# DraftBoundary
class DraftBoundary(BSElement):
    """The boundary that encompasses the draft mechanism used for drawing air through the boiler or furnace."""

    element_type = "xs:string"
    element_enumerations = ["Direct", "Direct indirect", "Indirect", "Other"]


# CondensingOperation
class CondensingOperation(BSElement):
    """The capability of the boiler or furnace to condense water vapor in the exhaust flue gas to obtain a higher efficiency."""

    element_type = "xs:string"
    element_enumerations = [
        "Condensing",
        "Near-Condensing",
        "Non-Condensing",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.Furnace.CombustionEfficiency
class CombustionEfficiency(BSElement):
    """The measure of how much energy is extracted from the fuel and is the ratio of heat transferred to the combustion air divided by the heat input of the fuel. (0-1) (fraction)"""

    element_type = "xs:decimal"


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.Furnace.ThermalEfficiency
class ThermalEfficiency(BSElement):
    """The efficiency of heat transfer between the combustion process and the heated steam, water, or air. (0-1) (fraction)"""

    element_type = "xs:decimal"


# ThirdPartyCertification
class ThirdPartyCertification(BSElement):
    """Independent organization has verified that product or appliance meets or exceeds the standard in question (ENERGY STAR, CEE, or other)."""

    element_type = "xs:string"
    element_enumerations = [
        "ENERGY STAR",
        "ENERGY STAR Most Efficient",
        "FEMP Designated",
        "CEE Tier 1",
        "CEE Tier 2",
        "CEE Tier 3",
        "Other",
        "None",
        "Unknown",
    ]


# FuelTypes
class FuelTypes(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Electricity",
        "Electricity-Exported",
        "Electricity-Onsite generated",
        "Natural gas",
        "Fuel oil",
        "Fuel oil no 1",
        "Fuel oil no 2",
        "Fuel oil no 4",
        "Fuel oil no 5",
        "Fuel oil no 5 (light)",
        "Fuel oil no 5 (heavy)",
        "Fuel oil no 6",
        "Fuel oil no 5 and no 6",
        "District steam",
        "District hot water",
        "District chilled water",
        "Propane",
        "Liquid propane",
        "Kerosene",
        "Diesel",
        "Coal",
        "Coal anthracite",
        "Coal bituminous",
        "Coke",
        "Wood",
        "Wood pellets",
        "Hydropower",
        "Biofuel",
        "Biofuel B5",
        "Biofuel B10",
        "Biofuel B20",
        "Wind",
        "Geothermal",
        "Solar",
        "Biomass",
        "Hydrothermal",
        "Dry steam",
        "Flash steam",
        "Ethanol",
        "Biodiesel",
        "Waste heat",
        "Dual fuel",
        "Gasoline",
        "Thermal-Exported",
        "Thermal-Onsite generated",
        "Other delivered-Exported",
        "Other delivered-Onsite generated",
        "Other metered-Exported",
        "Other metered-Onsite generated",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.HeatPump.HeatPumpType
class HeatPumpType(BSElement):
    """General type of heat pump used for space heating."""

    element_type = "xs:string"
    element_enumerations = [
        "Split",
        "Packaged Terminal",
        "Packaged Unitary",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.HeatPump.HeatPumpBackupHeatingSwitchoverTemperature
class HeatPumpBackupHeatingSwitchoverTemperature(BSElement):
    """Minimum outside temperature at which the heat pump can operate. (°F)"""

    element_type = "xs:decimal"


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.HeatPump.HeatPumpBackupAFUE
class HeatPumpBackupAFUE(BSElement):
    """Annual Fuel Utilization Efficiency (AFUE) of backup system for heat pump."""

    element_type = "xs:decimal"


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.HeatPump.LinkedHeatingPlantID
class LinkedHeatingPlantID(BSElement):
    """ID number of HeatingPlant serving as the source for this heat pump."""


LinkedHeatingPlantID.element_attributes = [
    "IDref",  # IDREF
]

# OtherCombinationType
class OtherCombinationType(BSElement):
    pass


# NoHeatingType
class NoHeatingType(BSElement):
    pass


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.SourceHeatingPlantID
class SourceHeatingPlantID(BSElement):
    """ID number of HeatingPlant serving as the source for this zonal system."""


SourceHeatingPlantID.element_attributes = [
    "IDref",  # IDREF
]

# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceCondition
class HeatingSourceCondition(EquipmentCondition):
    pass


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingMedium
class HeatingMedium(BSElement):
    """Medium used to transport heat from a central heating system to individual zones."""

    element_type = "xs:string"
    element_enumerations = [
        "Hot water",
        "Steam",
        "Refrigerant",
        "Air",
        "Glycol",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.AnnualHeatingEfficiencyValue
class AnnualHeatingEfficiencyValue(BSElement):
    """Overall annual efficiency of a heating system."""

    element_type = "xs:decimal"


# AnnualHeatingEfficiencyUnits
class AnnualHeatingEfficiencyUnits(BSElement):
    """The measure used to quantify efficiency."""

    element_type = "xs:string"
    element_enumerations = [
        "COP",
        "AFUE",
        "HSPF",
        "Thermal Efficiency",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.InputCapacity
class InputCapacity(BSElement):
    """The rate of energy consumption of the heating equipment at full load."""

    element_type = "xs:decimal"


# CapacityUnits
class CapacityUnits(BSElement):
    """Units used to measure capacity."""

    element_type = "xs:string"
    element_enumerations = [
        "cfh",
        "ft3/min",
        "kcf/h",
        "MCF/day",
        "gpm",
        "W",
        "kW",
        "hp",
        "MW",
        "Btu/hr",
        "cal/h",
        "ft-lbf/h",
        "ft-lbf/min",
        "Btu/s",
        "kBtu/hr",
        "MMBtu/hr",
        "therms/h",
        "lbs/h",
        "Klbs/h",
        "Mlbs/h",
        "Cooling ton",
        "Other",
    ]


# HeatingStaging
class HeatingStaging(BSElement):
    """The method of heating staging used by the unit. Select "Single Stage" for units with single stage (on/off) control. Select "Multiple, Discrete Stages" for units with multiple discrete stages (low-fire / high-fire). Select "Modulating" for units which contain modulating burners."""

    element_type = "xs:string"
    element_enumerations = [
        "Single stage",
        "Multiple discrete stages",
        "Variable",
        "Modulating",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.NumberOfHeatingStages
class NumberOfHeatingStages(BSElement):
    """The number of heating stages, excluding "off." """

    element_type = "xs:integer"


# PrimaryFuel
class PrimaryFuel(FuelTypes):
    """Main fuel used by the system."""


# YearInstalled
class YearInstalled(BSElement):
    """Year the system was originally installed in the building. Equipment age may be used as a proxy."""

    element_type = "xs:gYear"


# YearOfManufacture
class YearOfManufacture(BSElement):
    """Year system was manufactured."""

    element_type = "xs:gYear"


# Manufacturer
class Manufacturer(BSElement):
    """Company that manufactured the equipment."""

    element_type = "xs:string"


# ModelNumber
class ModelNumber(BSElement):
    """Model or catalog number that can be used to identify more detailed system characteristics."""

    element_type = "xs:string"


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.DX.DXSystemType
class DXSystemType(BSElement):
    """General type of heat pump used for space heating."""

    element_type = "xs:string"
    element_enumerations = [
        "Split DX air conditioner",
        "Packaged terminal air conditioner (PTAC)",
        "Split heat pump",
        "Packaged terminal heat pump (PTHP)",
        "Variable refrigerant flow",
        "Packaged/unitary direct expansion/RTU",
        "Packaged/unitary heat pump",
        "Single package vertical air conditioner",
        "Single package vertical heat pump",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.DX.CompressorType
class CompressorType(BSElement):
    """Type of compressor in the chiller."""

    element_type = "xs:string"
    element_enumerations = [
        "Reciprocating",
        "Screw",
        "Scroll",
        "Centrifugal",
        "Other",
        "Unknown",
    ]


# CompressorStaging
class CompressorStaging(BSElement):
    """The compressor staging for the unit. Select "Single Stage" for units with single stage (on/off) control. Select "Multiple, Discrete Stages" for units with multiple compressors, discrete unloading stages, or compressors with stepped speed motors that are controlled to operate at discrete stages. Select "Variable" for compressors that operate at variable speeds or with modulating unloading."""

    element_type = "xs:string"
    element_enumerations = [
        "Single stage",
        "Multiple discrete stages",
        "Variable",
        "Modulating",
        "Other",
        "Unknown",
    ]


# Refrigerant
class Refrigerant(BSElement):
    """The type of refrigerant used in the system."""

    element_type = "xs:string"
    element_enumerations = [
        "R134a",
        "R123",
        "R22",
        "R290",
        "R401a",
        "R404a",
        "R407a",
        "R407c",
        "R408a",
        "R409a",
        "R410a",
        "R500",
        "R502",
        "R600a",
        "R744",
        "R717",
        "R718",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.DX.RefrigerantChargeFactor
class RefrigerantChargeFactor(BSElement):
    """Used to adjust cooling efficiency for assumed slightly degraded performance if refrigerant charge is not verified through acceptance test procedures. (0-1) (fraction)"""

    element_type = "xs:decimal"


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.DX.ActiveDehumidification
class ActiveDehumidification(BSElement):
    """True if an active dehumidification system is available (in addition to the dehumidification that takes place during normal direct expansion (DX) cooling operation)."""

    element_type = "xs:boolean"


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.EvaporativeCooler.EvaporativeCoolingType
class EvaporativeCoolingType(BSElement):
    """Defines the type of evaporative cooler operation."""

    element_type = "xs:string"
    element_enumerations = ["Direct", "Direct indirect", "Indirect", "Other"]


# NoCoolingType
class NoCoolingType(BSElement):
    pass


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.CoolingPlantID
class CoolingPlantID(BSElement):
    """ID number of CoolingPlant serving as the source for this zonal system."""


CoolingPlantID.element_attributes = [
    "IDref",  # IDREF
]

# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceCondition
class CoolingSourceCondition(EquipmentCondition):
    pass


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingMedium
class CoolingMedium(BSElement):
    """Medium used to transport cooling energy from a central cooling system to individual zones."""

    element_type = "xs:string"
    element_enumerations = [
        "Chilled water",
        "Refrigerant",
        "Air",
        "Glycol",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.AnnualCoolingEfficiencyValue
class AnnualCoolingEfficiencyValue(BSElement):
    """Overall annual efficiency of a cooling system."""

    element_type = "xs:decimal"


# AnnualCoolingEfficiencyUnits
class AnnualCoolingEfficiencyUnits(BSElement):
    """The measure used to quantify efficiency."""

    element_type = "xs:string"
    element_enumerations = ["COP", "EER", "SEER", "kW/ton", "Other"]


# Capacity
class Capacity(BSElement):
    """Capacity of the system at rated conditions."""

    element_type = "xs:decimal"


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.NumberOfDiscreteCoolingStages
class NumberOfDiscreteCoolingStages(BSElement):
    """The number of discrete operating stages, excluding "off." """

    element_type = "xs:integer"


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingStageCapacity
class CoolingStageCapacity(BSElement):
    """Average capacity of each cooling stage, at Air-Conditioning, Heating, and Refrigeration Institute (AHRI) rated conditions, expressed as a fraction of total capacity. (0-1) (fraction)"""

    element_type = "xs:decimal"


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.ZoneEquipment.Convection.ConvectionType
class ConvectionType(BSElement):
    """Type of convection equipment used for heating and cooling at the zone."""

    element_type = "xs:string"
    element_enumerations = ["Perimeter baseboard", "Chilled beam", "Other", "Unknown"]


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.ZoneEquipment.Radiant.RadiantType
class RadiantType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Radiator", "Radiant floor or ceiling", "Other", "Unknown"]


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.CentralAirDistribution.AirDeliveryType
class AirDeliveryType(BSElement):
    """Method for delivering air for heating and cooling to the zone."""

    element_type = "xs:string"
    element_enumerations = [
        "Central fan",
        "Induction units",
        "Low pressure under floor",
        "Local fan",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.CentralAirDistribution.TerminalUnit
class TerminalUnit(BSElement):
    """Type of terminal unit serving each zone of a central air distribution system."""

    element_type = "xs:string"
    element_enumerations = [
        "CAV terminal box no reheat",
        "CAV terminal box with reheat",
        "VAV terminal box fan powered no reheat",
        "VAV terminal box fan powered with reheat",
        "VAV terminal box not fan powered no reheat",
        "VAV terminal box not fan powered with reheat",
        "Powered induction unit",
        "Automatically controlled register",
        "Manually controlled register",
        "Uncontrolled register",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.CentralAirDistribution.ReheatSource
class ReheatSource(BSElement):
    """Energy source used to provide reheat energy at a terminal unit."""

    element_type = "xs:string"
    element_enumerations = [
        "Heating plant",
        "Local electric resistance",
        "Local gas",
        "None",
        "Other",
        "Unknown",
    ]


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.CentralAirDistribution.ReheatControlMethod
class ReheatControlMethod(BSElement):
    """The air/temperature control strategy for VAV systems with reheat boxes."""

    element_type = "xs:string"
    element_enumerations = ["Dual Maximum", "Single Maximum", "Other", "Unknown"]


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.CentralAirDistribution.ReheatPlantID
class ReheatPlantID(BSElement):
    pass


ReheatPlantID.element_attributes = [
    "IDref",  # IDREF
]

# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryCondition
class DeliveryCondition(EquipmentCondition):
    pass


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.HeatingSourceID
class HeatingSourceID(BSElement):
    """ID number of the HeatingSource associated with this delivery mechanism."""


HeatingSourceID.element_attributes = [
    "IDref",  # IDREF
]

# HVACSystemType.HeatingAndCoolingSystems.ZoningSystemType
class ZoningSystemType(BSElement):
    """Identifies whether a system is single or multi-zone."""

    element_type = "xs:string"
    element_enumerations = ["Single zone", "Multi zone", "Unknown"]


# HVACSystemType.HVACControlSystemTypes.HVACControlSystemType
class HVACControlSystemType(BSElement):
    """HVAC equipment control strategy."""

    element_type = "xs:string"
    element_enumerations = ["Analog", "Digital", "Pneumatic", "Other", "Unknown"]


# DuctSystemType.DuctConfiguration
class DuctConfiguration(BSElement):
    """Configuration of ducts."""

    element_type = "xs:string"
    element_enumerations = ["Single", "Dual", "Three", "Ductless", "Other", "Unknown"]


# DuctSystemType.MinimumOutsideAirPercentage
class MinimumOutsideAirPercentage(BSElement):
    """Minimum outside air percentage allowed."""

    element_type = "xs:decimal"


# DuctSystemType.MaximumOAFlowRate
class MaximumOAFlowRate(BSElement):
    """The maximum flow rate of outside air that the system is able to deliver. For systems with economizing or demand controlled ventilation capability, this is the outdoor air flow rate when the outdoor air (OA) damper is fully open and the fan speed is at maximum. (cfm)"""

    element_type = "xs:decimal"


# DuctSystemType.DuctSealing
class DuctSealing(BSElement):
    """Condition of duct sealing."""

    element_type = "xs:string"
    element_enumerations = [
        "Connections sealed with mastic",
        "No observable leaks",
        "Some observable leaks",
        "Significant leaks",
        "Catastrophic leaks",
        "Unknown",
    ]


# DuctSystemType.DuctInsulationRValue
class DuctInsulationRValue(BSElement):
    """R-value of duct insulation. (ft2-F-hr/Btu)"""

    element_type = "xs:decimal"


# DuctSystemType.DuctSurfaceArea
class DuctSurfaceArea(BSElement):
    """Total surface area of ducts associated with this air distribution system. (ft2)"""

    element_type = "xs:decimal"


# DuctSystemType.SupplyDuctPercentConditionedSpace
class SupplyDuctPercentConditionedSpace(BSElement):
    """Percentage of supply duct surface area that is located within conditioned space. (0-100) (%)"""

    element_type = "xs:decimal"


# DuctSystemType.ReturnDuctPercentConditionedSpace
class ReturnDuctPercentConditionedSpace(BSElement):
    """Percentage of return duct surface area, including the air handler, that is located within conditioned space. (0-100) (%)"""

    element_type = "xs:decimal"


# DuctSystemType.StaticPressureInstalled
class StaticPressureInstalled(BSElement):
    """The expected or installed internal static pressure of the system at full supply fan speed including all filters, coils, and accessories. (Pa)"""

    element_type = "xs:decimal"


# DuctSystemType.DuctType
class DuctType(BSElement):
    """Type of duct material."""

    element_type = "xs:string"
    element_enumerations = [
        "Flex uncategorized",
        "Grey flex",
        "Mylar flex",
        "Duct board",
        "Sheet metal",
        "Galvanized",
        "Flexible",
        "Fiberboard",
        "No ducting",
        "Other",
        "Unknown",
    ]


# DuctSystemType.DuctLeakageTestMethod
class DuctLeakageTestMethod(BSElement):
    """Method used to estimate duct leakage."""

    element_type = "xs:string"
    element_enumerations = [
        "Duct leakage tester",
        "Blower door subtract",
        "Pressure pan",
        "Visual inspection",
        "Other",
    ]


# DuctSystemType.DuctPressureTestLeakageRate
class DuctPressureTestLeakageRate(BSElement):
    """Duct leakage found from pressure test. (cfm)"""

    element_type = "xs:decimal"


# DuctSystemType.DuctPressureTestLeakagePercentage
class DuctPressureTestLeakagePercentage(BSElement):
    """Duct leakage found from pressure test. Reported as a percentage. (0-100) (%)"""

    element_type = "xs:decimal"


# DuctSystemType.HeatingDeliveryID
class HeatingDeliveryID(BSElement):
    """Heating delivery system supported by the air-distribution system."""


HeatingDeliveryID.element_attributes = [
    "IDref",  # IDREF
]

# DuctSystemType.CoolingDeliveryID
class CoolingDeliveryID(BSElement):
    """Cooling delivery system supported by the air-distribution system."""


CoolingDeliveryID.element_attributes = [
    "IDref",  # IDREF
]

# InsulationCondition
class InsulationCondition(BSElement):
    """Assessed condition of installed insulation."""

    element_type = "xs:string"
    element_enumerations = [
        "Excellent",
        "Good",
        "Average",
        "Poor",
        "Other",
        "Unknown",
        "None",
    ]


# HeatingPlantType.HeatingPlantCondition
class HeatingPlantCondition(EquipmentCondition):
    pass


# CoolingPlantType.CoolingPlantCondition
class CoolingPlantCondition(EquipmentCondition):
    pass


# CondenserPlantType.CondenserPlantCondition
class CondenserPlantCondition(EquipmentCondition):
    pass


# OtherHVACSystemType.OtherHVACSystemCondition
class OtherHVACSystemCondition(EquipmentCondition):
    pass


# OtherHVACSystemType.Integration
class Integration(BSElement):
    """Level of integration with primary heating and cooling sources and delivery systems."""

    element_type = "xs:string"
    element_enumerations = [
        "Integrated with central air distribution",
        "Integrated with local air distribution",
        "Stand-alone",
        "Other",
        "Unknown",
    ]


# OtherHVACSystemType.OtherHVACType.Humidifier.HumidificationType
class HumidificationType(BSElement):
    """Humidification type in air-distribution system."""

    element_type = "xs:string"
    element_enumerations = ["Steam", "Water Spray", "Other", "Unknown"]


# OtherHVACSystemType.OtherHVACType.Humidifier.HumidityControlMinimum
class HumidityControlMinimum(BSElement):
    """Relative humidity below which moisture is added to the space. (0-100) (%)"""

    element_type = "xs:decimal"


# DutyCycle
class DutyCycle(BSElement):
    """Percent of time the system operates. (0-100) (%)"""

    element_type = "xs:decimal"


# SystemPerformanceRatio
class SystemPerformanceRatio(BSElement):
    """Ratio of annual system load to the annual system energy consumption (similar to a whole system COP). A higher value indicates less heating and/or cooling energy use to meet the loads, and therefore represents a more efficient HVAC system. SPR can be used to describe the heating, cooling, and overall HVAC systems."""

    element_type = "xs:decimal"


# OtherHVACSystemType.OtherHVACType.Dehumidifier.DehumidificationType
class DehumidificationType(BSElement):
    """Dehumidification type in air-distribution system."""

    element_type = "xs:string"
    element_enumerations = ["Desiccant wheel", "Liquid desiccant", "Other", "Unknown"]


# OtherHVACSystemType.OtherHVACType.Dehumidifier.HumidityControlMaximum
class HumidityControlMaximum(BSElement):
    """Relative humidity above which moisture is removed from the space. (0-100) (%)"""

    element_type = "xs:decimal"


# OtherHVACSystemType.OtherHVACType.AirCleaner
class AirCleaner(BSElement):
    pass


AirCleaner.element_children = [
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("DutyCycle", DutyCycle),
    ("SystemPerformanceRatio", SystemPerformanceRatio),
]

# VentilationControlMethod
class VentilationControlMethod(BSElement):
    """The method used to control the rate of outside air ventilation."""

    element_type = "xs:string"
    element_enumerations = [
        "CO2 Sensors",
        "Fixed",
        "Occupancy Sensors",
        "Scheduled",
        "Other",
        "Unknown",
    ]


# OtherHVACSystemType.OtherHVACType.MechanicalVentilation.VentilationType
class VentilationType(BSElement):
    """Type of ventilation, and use of heat recovery."""

    element_type = "xs:string"
    element_enumerations = [
        "Exhaust only",
        "Supply only",
        "Dedicated outdoor air system",
        "Heat recovery ventilator",
        "Energy recovery ventilator",
        "None",
        "Other",
        "Unknown",
    ]


# OtherHVACSystemType.OtherHVACType.MechanicalVentilation.DemandControlVentilation
class DemandControlVentilation(BSElement):
    """True if ventilation system is controlled based on level of occupancy or pollutants, false otherwise."""

    element_type = "xs:boolean"


# OtherHVACSystemType.OtherHVACType.MechanicalVentilation.VentilationZoneControl
class VentilationZoneControl(BSElement):
    """Method used to determine overall ventilation rate for multiple zones."""

    element_type = "xs:string"
    element_enumerations = ["Average Flow", "Critical Zone", "Other", "Unknown"]


# OtherHVACSystemType.OtherHVACType.SpotExhaust.ExhaustLocation
class ExhaustLocation(BSElement):
    """Location of spot exhaust ventilation system."""

    element_type = "xs:string"
    element_enumerations = [
        "Bathroom",
        "Kitchen hood",
        "Laboratory hood",
        "Other",
        "Unknown",
    ]


# OtherHVACSystemType.OtherHVACType.NaturalVentilation.NaturalVentilationRate
class NaturalVentilationRate(BSElement):
    """Average rate of natural ventilation when used. Units depend on ventilation method. (cfm)"""

    element_type = "xs:decimal"


# OtherHVACSystemType.OtherHVACType.NaturalVentilation.NaturalVentilationMethod
class NaturalVentilationMethod(BSElement):
    """Strategy for introducing natural ventilation."""

    element_type = "xs:string"
    element_enumerations = [
        "Air changes per hour",
        "Flow per area",
        "Flow per person",
        "Flow per zone",
        "Wind and stack open area",
        "Other",
        "Unknown",
    ]


# OtherHVACSystemType.LinkedDeliveryIDs.LinkedDeliveryID
class LinkedDeliveryID(BSElement):
    """Connect to an air distribution system"""


LinkedDeliveryID.element_attributes = [
    "IDref",  # IDREF
]

# LightingSystemType.BallastType
class BallastType(BSElement):
    """A ballast is a piece of equipment required to control the starting and operating voltages of electrical gas discharge lights."""

    element_type = "xs:string"
    element_enumerations = [
        "Electromagnetic",
        "Standard Electronic",
        "Premium Electronic",
        "Integrated",
        "Core and Coil",
        "F-Can",
        "Other",
        "No Ballast",
    ]


# LightingSystemType.InputVoltage
class InputVoltage(BSElement):
    """Voltage rating for this LightingSystem."""

    element_type = "xs:string"
    element_enumerations = [
        "120",
        "208",
        "240",
        "277",
        "347",
        "480",
        "120/277 (dual)",
        "120-277 (universal)",
        "347-480 (high voltage)",
        "Other",
        "Unknown",
    ]


# LightingSystemType.InstallationType
class InstallationType(BSElement):
    """Installation of lamp relative to mounting surface."""

    element_type = "xs:string"
    element_enumerations = [
        "Plug-in",
        "Recessed",
        "Surface",
        "Suspended",
        "Other",
        "Unknown",
    ]


# LightingSystemType.LightingDirection
class LightingDirection(BSElement):
    """Directional characteristics of lighting fixtures."""

    element_type = "xs:string"
    element_enumerations = [
        "Direct",
        "Indirect",
        "Direct-Indirect",
        "Spotlight",
        "Floodlighting",
        "Omnidirectional",
        "Other",
        "Unknown",
    ]


# LightingSystemType.PercentPremisesServed
class PercentPremisesServed(BSElement):
    """The percentage of the premises that the LightingSystem applies to. This may be for the whole building or an individual space, depending on the LinkedPremises field."""

    element_type = "xs:decimal"


# LightingSystemType.InstalledPower
class InstalledPower(BSElement):
    """Installed power for this system. (kW)"""

    element_type = "xs:decimal"


# LightingSystemType.NumberOfLampsPerLuminaire
class NumberOfLampsPerLuminaire(BSElement):
    """The number of lamps in the luminaire."""

    element_type = "xs:integer"


# LightingSystemType.NumberOfLampsPerBallast
class NumberOfLampsPerBallast(BSElement):
    """The number of lamps driven by the ballast."""

    element_type = "xs:integer"


# LightingSystemType.NumberOfBallastsPerLuminaire
class NumberOfBallastsPerLuminaire(BSElement):
    """The number of ballasts installed in each luminaire or fixture."""

    element_type = "xs:decimal"


# LightingSystemType.NumberOfLuminaires
class NumberOfLuminaires(BSElement):
    """Total number of luminaires/fixtures in this system."""

    element_type = "xs:integer"


# LightingSystemType.OutsideLighting
class OutsideLighting(BSElement):
    """True if lighting system is primarily for outside lighting, false otherwise."""

    element_type = "xs:boolean"


# LightingSystemType.ReflectorType
class ReflectorType(BSElement):
    """Type of reflector used to distribute light to the space."""

    element_type = "xs:string"
    element_enumerations = [
        "Specular Reflector",
        "Prismatic Reflector",
        "Other",
        "Unknown",
        "None",
    ]


# LightingSystemType.LightingEfficacy
class LightingEfficacy(BSElement):
    """The amount of light (luminous flux) produced by a light source, usually measured in lumens, as a ratio of the amount of power consumed to produce it, usually measured in watts. (lm/W)"""

    element_type = "xs:decimal"


# LightingSystemType.WorkPlaneHeight
class WorkPlaneHeight(BSElement):
    """Distance from the finished floor to the work plane. Used to calculate vertical distance from the work plane to the centerline of the lighting fixture. (ft)"""

    element_type = "xs:decimal"


# LightingSystemType.LuminaireHeight
class LuminaireHeight(BSElement):
    """Vertical height of luminaire above the finished floor/ground. (ft)"""

    element_type = "xs:decimal"


# LightingSystemType.FixtureSpacing
class FixtureSpacing(BSElement):
    """Average horizontal spacing of fixtures. (ft)"""

    element_type = "xs:decimal"


# LightingSystemType.RatedLampLife
class RatedLampLife(BSElement):
    """The expected remaining service life of a component. (hrs)"""

    element_type = "xs:decimal"


# LightingSystemType.LampType.LinearFluorescent.LampLength
class LampLength(BSElement):
    """Length of fluorescent lamps."""

    element_type = "xs:string"
    element_enumerations = ["2 ft", "4 ft", "Other", "Unknown"]


# FluorescentStartType
class FluorescentStartType(BSElement):
    """Start technology used with fluorescent ballasts."""

    element_type = "xs:string"
    element_enumerations = [
        "Instant start",
        "Rapid start",
        "Programmed start",
        "Other",
        "Unknown",
    ]


# LightingSystemType.LampType.HighIntensityDischarge.MetalHalideStartType
class MetalHalideStartType(BSElement):
    """Start technology used with metal halide ballasts."""

    element_type = "xs:string"
    element_enumerations = ["Probe start", "Pulse start", "Other", "Unknown"]


# LightingSystemType.LampType.Induction
class Induction(BSElement):
    pass


Induction.element_children = [
    ("FluorescentStartType", FluorescentStartType),
]

# NeonType
class NeonType(BSElement):
    pass


# PlasmaType
class PlasmaType(BSElement):
    pass


# PhotoluminescentType
class PhotoluminescentType(BSElement):
    pass


# SelfLuminousType
class SelfLuminousType(BSElement):
    pass


# DomesticHotWaterSystemType.DomesticHotWaterSystemNotes
class DomesticHotWaterSystemNotes(BSElement):
    """Details about the DHW system. For example, methods of evaluation used to determine condition or efficiency."""

    element_type = "xs:string"


# DomesticHotWaterSystemType.HotWaterDistributionType
class HotWaterDistributionType(BSElement):
    """Manner in which hot water is distributed."""

    element_type = "xs:string"
    element_enumerations = ["Looped", "Distributed", "Point-of-use", "Other", "Unknown"]


# DomesticHotWaterSystemType.WaterHeaterEfficiencyType
class WaterHeaterEfficiencyType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Energy Factor", "Thermal Efficiency", "AFUE", "COP"]


# DomesticHotWaterSystemType.WaterHeaterEfficiency
class WaterHeaterEfficiency(BSElement):
    """A factor is used to compare the relative efficiency of water heaters, dishwashers, clothes washers, and clothes dryers."""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DailyHotWaterDraw
class DailyHotWaterDraw(BSElement):
    """Average daily volume of hot water provided by this system. (gal)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.HotWaterSetpointTemperature
class HotWaterSetpointTemperature(BSElement):
    """The water temperature that the equipment supplies, such as the chilled water temperature setpoint for a chiller, or hot water temperature setpoint for water leaving a boiler. (°F)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.ParasiticFuelConsumptionRate
class ParasiticFuelConsumptionRate(BSElement):
    """A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. (Btu/hr)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterSystemCondition
class DomesticHotWaterSystemCondition(EquipmentCondition):
    pass


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Direct.DirectTankHeatingSource
class DirectTankHeatingSource(BSElement):
    """Direct source of heat for hot water tank."""

    class ElectricResistance(ElectricResistanceType):
        pass

    class Combustion(BSElement):
        pass

    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


DirectTankHeatingSource.element_children = [
    ("ElectricResistance", DirectTankHeatingSource.ElectricResistance),
    ("Combustion", DirectTankHeatingSource.Combustion),
    ("Other", DirectTankHeatingSource.Other),
    ("Unknown", DirectTankHeatingSource.Unknown),
]
DirectTankHeatingSource.Combustion.element_children = [
    ("DraftType", DraftType),
    ("DraftBoundary", DraftBoundary),
    ("CondensingOperation", CondensingOperation),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Direct
class Direct(BSElement):
    pass


Direct.element_children = [
    ("DirectTankHeatingSource", DirectTankHeatingSource),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.HeatPump.HPWHMinimumAirTemperature
class HPWHMinimumAirTemperature(BSElement):
    """The minimum ambient operating temperature for the compressor. This can be inferred from the operating range of the heat pump. Below this value, the heat pump will not operate and the supplemental heating system is required to produce hot water, thus reducing the efficiency of the heat pump water heater. (°F)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar.SolarThermalSystemType
class SolarThermalSystemType(BSElement):
    """Basic function of solar thermal system."""

    element_type = "xs:string"
    element_enumerations = [
        "Hot water",
        "Hot water and space heating",
        "Space heating",
        "Hybrid system",
        "Other",
        "Unknown",
    ]


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar.SolarThermalSystemCollectorArea
class SolarThermalSystemCollectorArea(BSElement):
    """Area of solar collector exposed to solar radiation. (ft2)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar.SolarThermalSystemCollectorLoopType
class SolarThermalSystemCollectorLoopType(BSElement):
    """Heat transfer medium and controls used for the solar collector loop."""

    element_type = "xs:string"
    element_enumerations = [
        "Air direct",
        "Air indirect",
        "Liquid direct",
        "Liquid indirect",
        "Passive thermosyphon",
        "Other",
        "Unknown",
    ]


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar.SolarThermalSystemCollectorType
class SolarThermalSystemCollectorType(BSElement):
    """Type of solar energy collector used in a solar hot water or space heating system."""

    element_type = "xs:string"
    element_enumerations = [
        "Single glazing black",
        "Single glazing selective",
        "Double glazing black",
        "Double glazing selective",
        "Evacuated tube",
        "Integrated collector storage",
        "Other",
        "Unknown",
    ]


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar.SolarThermalSystemCollectorAzimuth
class SolarThermalSystemCollectorAzimuth(BSElement):
    """Degrees clockwise from North. For a premises, it is the azimuth of the front facing element. It can also be applied to envelope components, such as walls, windows (fenestration), as well as onsite generation technologies, such as photovoltaic panels. (0 - 360) (degrees)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar.SolarThermalSystemCollectorTilt
class SolarThermalSystemCollectorTilt(BSElement):
    """The angle from a horizontal surface; can be applied to an opaque surface, a fenestration unit, a solar panel, etc. (degrees)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar.SolarThermalSystemStorageVolume
class SolarThermalSystemStorageVolume(BSElement):
    """Volume of any separate solar energy storage tank, not the primary service hot water tank. (gal)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.SpaceHeatingSystem.HeatingPlantID
class HeatingPlantID(BSElement):
    """ID number of HeatingPlant serving as the source for this hot water system."""


HeatingPlantID.element_attributes = [
    "IDref",  # IDREF
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankVolume
class TankVolume(BSElement):
    """Hot water tank volume. (gal)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeight
class TankHeight(BSElement):
    """Vertical height of hot water tank. (in.)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankPerimeter
class TankPerimeter(BSElement):
    """Perimeter of hot water tank. (in.)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.RecoveryEfficiency
class RecoveryEfficiency(BSElement):
    """The ratio of energy delivered to heat cold water compared to the energy consumed by the water heater, as determined following standardized DOE testing procedure. (0-1) (fraction)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.StorageTankInsulationRValue
class StorageTankInsulationRValue(BSElement):
    """(Also known as thermal resistance), quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.StorageTankInsulationThickness
class StorageTankInsulationThickness(BSElement):
    """Insulation thickness of hot water storage tank. (in.)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.OffCycleHeatLossCoefficient
class OffCycleHeatLossCoefficient(BSElement):
    """The heat loss coefficient to ambient conditions. (UA) (Btu/hr/ft2/°F)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.DomesticHotWaterType.Instantaneous.InstantaneousWaterHeatingSource
class InstantaneousWaterHeatingSource(BSElement):
    """Source of heat for instantaneous water heater."""

    class ElectricResistance(ElectricResistanceType):
        pass

    class Combustion(BSElement):
        pass

    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


InstantaneousWaterHeatingSource.element_children = [
    ("ElectricResistance", InstantaneousWaterHeatingSource.ElectricResistance),
    ("Combustion", InstantaneousWaterHeatingSource.Combustion),
    ("Other", InstantaneousWaterHeatingSource.Other),
    ("Unknown", InstantaneousWaterHeatingSource.Unknown),
]
InstantaneousWaterHeatingSource.Combustion.element_children = [
    ("DraftType", DraftType),
    ("DraftBoundary", DraftBoundary),
    ("CondensingOperation", CondensingOperation),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.Instantaneous
class Instantaneous(BSElement):
    pass


Instantaneous.element_children = [
    ("InstantaneousWaterHeatingSource", InstantaneousWaterHeatingSource),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.HeatExchanger
class HeatExchanger(BSElement):
    pass


# DomesticHotWaterSystemType.Recirculation.RecirculationLoopCount
class RecirculationLoopCount(BSElement):
    """The total number of hot water recirculation loops coming from and returning to a specific water heater."""

    element_type = "xs:integer"


# DomesticHotWaterSystemType.Recirculation.RecirculationFlowRate
class RecirculationFlowRate(BSElement):
    """Flow rate in primary hot water recirculation loop. Zero or blank if there is no recirculation loop. (gal/hr)"""

    element_type = "xs:decimal"


# DomesticHotWaterSystemType.Recirculation.RecirculationControlType
class RecirculationControlType(BSElement):
    """Type of control for recirculation loop."""

    element_type = "xs:string"
    element_enumerations = [
        "Continuous",
        "Temperature",
        "Timer",
        "Demand",
        "Other",
        "Unknown",
    ]


# DomesticHotWaterSystemType.Recirculation.RecirculationEnergyLossRate
class RecirculationEnergyLossRate(BSElement):
    """Rate of heat loss from the recirculation loop when operating. (MMBtu/hr)"""

    element_type = "xs:decimal"


# CookingSystemType.TypeOfCookingEquipment
class TypeOfCookingEquipment(BSElement):
    """Short description of the type and purpose of cooking equipment."""

    element_type = "xs:string"
    element_enumerations = [
        "Hot top range",
        "Open burner range",
        "Wok range",
        "Braising pan",
        "Underfired broiler",
        "Overfired broiler",
        "Conveyor broiler",
        "Salamander broiler",
        "Broiler",
        "Microwave oven",
        "Toaster",
        "Standard fryer",
        "Large vat fryer",
        "Split vat fryer",
        "Convection oven",
        "Combination oven",
        "Standard oven",
        "Conveyor oven",
        "Slow cook-and-hold oven",
        "Deck oven",
        "Mini-Rack oven",
        "Rack (Roll-In) oven",
        "Range oven",
        "Rapid cook oven",
        "Rotisserie oven",
        "Retherm oven",
        "Convection toaster oven",
        "Steam cooker",
        "Steam kettle",
        "Drawer warmer",
        "Heated transparent merchandising cabinets",
        "Cook-and-hold appliance",
        "Proofing cabinet",
        "Single-sided griddle",
        "Double-sided griddle",
        "Griddle",
        "Fry-top griddle",
        "Automatic drip filter coffee maker",
        "Single-serve coffee maker",
        "Espresso machine",
        "Other",
        "Unknown",
    ]


# CookingSystemType.NumberOfMeals
class NumberOfMeals(BSElement):
    """Number of meals cooked per year using this equipment."""

    element_type = "xs:integer"


# CookingSystemType.CookingEnergyPerMeal
class CookingEnergyPerMeal(BSElement):
    """Energy use per meal for this equipment. (Btu)"""

    element_type = "xs:decimal"


# CookingSystemType.DailyWaterUse
class DailyWaterUse(BSElement):
    """Total volume of water (hot and cold) used per day for this equipment. (gal/day)"""

    element_type = "xs:decimal"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.RefrigerationCompressor.CompressorUnloader.CompressorUnloaderStages
class CompressorUnloaderStages(BSElement):
    """Number of stages available for unloading the compressor."""

    element_type = "xs:integer"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.RefrigerationCompressor.RefrigerationCompressorType
class RefrigerationCompressorType(BSElement):
    """Type of compressor in the refrigeration system."""

    element_type = "xs:string"
    element_enumerations = [
        "Reciprocating",
        "Screw",
        "Scroll",
        "Centrifugal",
        "Other",
        "Unknown",
    ]


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.RefrigerationCompressor.DesuperheatValve
class DesuperheatValve(BSElement):
    """True if the level of refrigerant superheat is controlled using a desuperheat valve."""

    element_type = "xs:boolean"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.RefrigerationCompressor.CrankcaseHeater
class CrankcaseHeater(BSElement):
    """True if a crankcase heater is used to prevent condensation when the unit is off."""

    element_type = "xs:boolean"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.NetRefrigerationCapacity
class NetRefrigerationCapacity(BSElement):
    """That portion of the total refrigeration capacity of a liquid cooler that produces useful cooling. This is the product of the mass flow rate of liquid, specific heat of the liquid, and the difference between entering and leaving liquid temperatures, expressed in energy units per unit of time. It is represented also by the total refrigeration capacity less the heat leakage rate. (MMBtu/hr)"""

    element_type = "xs:decimal"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.TotalHeatRejection
class TotalHeatRejection(BSElement):
    """Amount of heat energy rejected to its surroundings by a condenser. (MMBtu/hr)"""

    element_type = "xs:decimal"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.SuctionVaporTemperature
class SuctionVaporTemperature(BSElement):
    """The temperature of the refrigerant vapor returning to the compressor or condensing unit. (°F)"""

    element_type = "xs:decimal"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.NumberOfRefrigerantReturnLines
class NumberOfRefrigerantReturnLines(BSElement):
    """Number of return lines from refrigerated cases to the compressor."""

    element_type = "xs:integer"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.EvaporatorPressureRegulators
class EvaporatorPressureRegulators(BSElement):
    """True if mechanical or electronic regulators are used to maintain the suction temperature in the individual cases."""

    element_type = "xs:boolean"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.RefrigerantSubcooler
class RefrigerantSubcooler(BSElement):
    """True if there is a heat exchanger, after the condenser, for subcooling the condensed refrigerant."""

    element_type = "xs:boolean"


# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.CaseReturnLineDiameter
class CaseReturnLineDiameter(BSElement):
    """Diameter of the refrigerant return line exiting refrigerated cases. (in.)"""

    element_type = "xs:decimal"


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.AntiSweatHeaters.AntiSweatHeaterPower
class AntiSweatHeaterPower(BSElement):
    """The total power associated with anti-sweat heaters for glass display doors for a refrigerated cases of this type. (W)"""

    element_type = "xs:decimal"


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.AntiSweatHeaters.AntiSweatHeaterControls
class AntiSweatHeaterControls(BSElement):
    """True if anti-sweat heaters are controlled to minimize energy use."""

    element_type = "xs:boolean"


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.RefrigerationUnitType
class RefrigerationUnitType(BSElement):
    """Refrigeration equipment includes a refrigerator or freezer used for storing food products at specified temperatures, with the condensing unit and compressor built into the cabinet, and designed for use by commercial or institutional premises, other than laboratory settings. These units may be vertical or chest configurations and may contain a worktop surface."""

    element_type = "xs:string"
    element_enumerations = [
        "Refrigerator",
        "Freezer",
        "Combination",
        "Other",
        "Unknown",
    ]


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.DoorConfiguration
class DoorConfiguration(BSElement):
    """Door configuration of the refrigerator/freezer unit."""

    element_type = "xs:string"
    element_enumerations = [
        "Side-by-side",
        "Top and bottom",
        "Walk-in",
        "Other",
        "Unknown",
    ]


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.RefrigeratedCaseDoors
class RefrigeratedCaseDoors(BSElement):
    """True if refrigerated equipment has doors, false if not."""

    element_type = "xs:boolean"


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.CaseDoorOrientation
class CaseDoorOrientation(BSElement):
    """Orientation of refrigerated case doors used for display cases at stores, food-service establishments."""

    element_type = "xs:string"
    element_enumerations = ["Horizontal", "Vertical", "Combination", "Unknown"]


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.DefrostingType
class DefrostingType(BSElement):
    """Type of defrost strategy used for refrigerated cases."""

    element_type = "xs:string"
    element_enumerations = [
        "Electric",
        "Off cycle",
        "Hot gas",
        "Reverse cycle",
        "Water",
        "Cool gas",
        "None",
        "Other",
        "Unknown",
    ]


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.RefrigerationUnitSize
class RefrigerationUnitSize(BSElement):
    """Size of refrigeration equipment. (ft3)"""

    element_type = "xs:decimal"


# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.RefrigerationEnergy
class RefrigerationEnergy(BSElement):
    """Power for refrigeration equipment. (W)"""

    element_type = "xs:decimal"


# DishwasherSystemType.DishwasherMachineType
class DishwasherMachineType(BSElement):
    """They type of dishwasher machine such as being either stationary rack or conveyor."""

    element_type = "xs:string"
    element_enumerations = ["Stationary Rack", "Conveyor", "Other", "Unknown"]


# DishwasherSystemType.DishwasherConfiguration
class DishwasherConfiguration(BSElement):
    """A machine designed to clean and sanitize plates, pots, pans, glasses, cups, bowls, utensils, and trays by applying sprays of detergent solution (with or without blasting media granules) and a sanitizing rinse."""

    element_type = "xs:string"
    element_enumerations = [
        "Counter top",
        "Stationary Under Counter",
        "Stationary Single Tank Door Type",
        "Stationary Pot Pan Utensil",
        "Stationary glasswashing",
        "Single Tank Conveyor",
        "Multiple Tank Conveyor",
        "Single Tank Flight Conveyor",
        "Multiple Tank Flight Conveyor",
        "Other",
        "Unknown",
    ]


# DishwasherSystemType.DishwasherClassification
class DishwasherClassification(BSElement):
    """The sector where dishwasher equipment is commonly used."""

    element_type = "xs:string"
    element_enumerations = [
        "Industrial",
        "Commercial",
        "Residential",
        "Other",
        "Unknown",
    ]


# DishwasherSystemType.DishwasherLoadsPerWeek
class DishwasherLoadsPerWeek(BSElement):
    """Average number of loads of dishes washed per week."""

    element_type = "xs:decimal"


# DishwasherSystemType.DishwasherEnergyFactor
class DishwasherEnergyFactor(BSElement):
    """Energy Factor (EF) was the ENERGY STAR dishwasher energy performance metric prior to 2009. EF is expressed in cycles per kWh. A higher EF value means a dishwasher is more efficient. EF is the reciprocal of the sum of the machine electrical energy per cycle, M, plus the water heating energy consumption per cycle, W: EF = 1/(M + W). This equation may vary based on dishwasher features such as water heating boosters or truncated cycles. The federal EnergyGuide label on dishwashers shows the annual energy consumption and cost, which use the energy factor, average cycles per year, and the average cost of energy. The EF does not appear on the EnergyGuide label. Unlike annual energy use, the EF does not take into account the estimated annual energy use in standby mode. (cycles/kWh)"""

    element_type = "xs:decimal"


# DishwasherSystemType.DishwasherHotWaterUse
class DishwasherHotWaterUse(BSElement):
    """The estimated per cycle water of a dishwasher under typical conditions, expressed as the number of gallons of water delivered to the machine during one cycle. Measured by DOE test procedure. Water use depends on settings chosen. (gal/cycle)"""

    element_type = "xs:decimal"


# LaundrySystemType.QuantityOfLaundry
class QuantityOfLaundry(BSElement):
    """Quantity of laundry processed onsite annually. (lb/yr)"""

    element_type = "xs:decimal"


# LaundrySystemType.LaundryEquipmentUsage
class LaundryEquipmentUsage(BSElement):
    """Number of loads of laundry per week. (loads/wk)"""

    element_type = "xs:decimal"


# ClothesWasherClassification
class ClothesWasherClassification(BSElement):
    """The sector where clothes washer is commonly used."""

    element_type = "xs:string"
    element_enumerations = [
        "Residential",
        "Commercial",
        "Industrial",
        "Other",
        "Unknown",
    ]


# ClothesWasherLoaderType
class ClothesWasherLoaderType(BSElement):
    """The type of configuration of a laundry appliance. Such as front and top loading clothes washers."""

    element_type = "xs:string"
    element_enumerations = ["Front", "Top", "Other", "Unknown"]


# DryerType
class DryerType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Residential",
        "Commercial",
        "Industrial",
        "Other",
        "Unknown",
    ]


# LaundrySystemType.LaundryType.Combination.WasherDryerType
class WasherDryerType(BSElement):
    """Type of washer/dryer combination unit."""

    element_type = "xs:string"
    element_enumerations = [
        "Combination All In One Clothes Washer Dryer",
        "Unitized Stacked Washer Dryer Pair",
        "Other",
        "Unknown",
    ]


# PumpSystemType.PumpEfficiency
class PumpEfficiency(BSElement):
    """Efficiency of the pump under rated conditions. (0-1) (fraction)"""

    element_type = "xs:decimal"


# PumpSystemType.PumpMaximumFlowRate
class PumpMaximumFlowRate(BSElement):
    """The maximum flow rate of fluid through the pump in gallons per minute. (gal/min)"""

    element_type = "xs:decimal"


# PumpSystemType.PumpMinimumFlowRate
class PumpMinimumFlowRate(BSElement):
    """The minimum flow rate of fluid through the pump in gallons per minute. (gal/min)"""

    element_type = "xs:decimal"


# PumpSystemType.PumpInstalledFlowRate
class PumpInstalledFlowRate(BSElement):
    """Actual flow rate of pump under normal operating conditions. (gal/min)"""

    element_type = "xs:decimal"


# PumpSystemType.PumpPowerDemand
class PumpPowerDemand(BSElement):
    """Pump power at maximum flow rate. (kW)"""

    element_type = "xs:decimal"


# PumpSystemType.PumpControlType
class PumpControlType(BSElement):
    """Type of pump speed control."""

    element_type = "xs:string"
    element_enumerations = [
        "Constant Volume",
        "Variable Volume",
        "VFD",
        "Multi-Speed",
        "Other",
        "Unknown",
    ]


# PumpSystemType.PumpOperation
class PumpOperation(BSElement):
    """Defines how pump operation is controlled."""

    element_type = "xs:string"
    element_enumerations = ["On Demand", "Standby", "Schedule", "Other", "Unknown"]


# PumpSystemType.PumpingConfiguration
class PumpingConfiguration(BSElement):
    """Primary, secondary, or tertiary pump."""

    element_type = "xs:string"
    element_enumerations = [
        "Primary",
        "Secondary",
        "Tertiary",
        "Backup",
        "Other",
        "Unknown",
    ]


# PumpSystemType.PumpApplication
class PumpApplication(BSElement):
    """Type of system served by the pump."""

    element_type = "xs:string"
    element_enumerations = [
        "Boiler",
        "Chilled Water",
        "Domestic Hot Water",
        "Solar Hot Water",
        "Condenser",
        "Cooling Tower",
        "Ground Loop",
        "Pool",
        "Recirculation",
        "Process Hot Water",
        "Process Cold Water",
        "Potable Cold Water",
        "Refrigerant",
        "Air",
        "Other",
        "Unknown",
    ]


# FanSystemType.FanEfficiency
class FanEfficiency(BSElement):
    """Efficiency of the fan, excluding motor and drive. (0-1) (fraction)"""

    element_type = "xs:decimal"


# FanSystemType.FanSize
class FanSize(BSElement):
    """Maximum air flow produced by the fan. (cfm)"""

    element_type = "xs:decimal"


# FanSystemType.MinimumFlowRate
class MinimumFlowRate(BSElement):
    """The lowest rated flow rate for a fan. (cfm)"""

    element_type = "xs:decimal"


# FanSystemType.MaximumFanPower
class MaximumFanPower(BSElement):
    """Fan power at maximum flow rate (full load). (W)"""

    element_type = "xs:decimal"


# FanSystemType.FanType
class FanType(BSElement):
    """Method of generating air flow."""

    element_type = "xs:string"
    element_enumerations = ["Axial", "Centrifugal", "Other", "Unknown"]


# FanSystemType.BeltType
class BeltType(BSElement):
    """Type of belt drive in fan unit."""

    element_type = "xs:string"
    element_enumerations = [
        "Direct drive",
        "Standard belt",
        "Cogged belt",
        "Synchronous belts",
        "Other",
        "Unknown",
    ]


# FanSystemType.FanApplication
class FanApplication(BSElement):
    """Application of fan (supply, return, or exhaust)."""

    element_type = "xs:string"
    element_enumerations = ["Supply", "Return", "Exhaust", "Other", "Unknown"]


# FanSystemType.FanControlType
class FanControlType(BSElement):
    """Type of air flow control."""

    element_type = "xs:string"
    element_enumerations = [
        "Variable Volume",
        "Stepped",
        "Constant Volume",
        "Other",
        "Unknown",
    ]


# FanSystemType.FanPlacement
class FanPlacement(BSElement):
    """Placement of fan relative to the air stream."""

    element_type = "xs:string"
    element_enumerations = [
        "Series",
        "Parallel",
        "Draw Through",
        "Blow Through",
        "Other",
        "Unknown",
    ]


# FanSystemType.MotorLocationRelativeToAirStream
class MotorLocationRelativeToAirStream(BSElement):
    """True if the fan motor is located within the air stream."""

    element_type = "xs:boolean"


# FanSystemType.DesignStaticPressure
class DesignStaticPressure(BSElement):
    """The design static pressure for the fan. (Pa)"""

    element_type = "xs:decimal"


# FanSystemType.NumberOfDiscreteFanSpeedsCooling
class NumberOfDiscreteFanSpeedsCooling(BSElement):
    """The number of discrete operating speeds for the supply-fan motor when the unit is in cooling mode, excluding "off." Only used if flow control is "stepped." """

    element_type = "xs:integer"


# FanSystemType.NumberOfDiscreteFanSpeedsHeating
class NumberOfDiscreteFanSpeedsHeating(BSElement):
    """The number of discrete operating speeds for the supply-fan motor when the unit is in heating mode, excluding "off." Only used if flow control is "stepped." """

    element_type = "xs:integer"


# MotorSystemType.MotorRPM
class MotorRPM(BSElement):
    """The number of full revolutions in a unit of time and is used to assign MotorEfficiency. 2008 NR ACM table N2-20 has four speeds: 3600 rpm, 1800 rpm, 1200 rpm, 900 rpm."""

    element_type = "xs:integer"


# MotorSystemType.MotorBrakeHP
class MotorBrakeHP(BSElement):
    """The brake horsepower of the motor before the loss in power caused by the gearbox, alternator, differential, water pump, and other auxiliary components. (hp)"""

    element_type = "xs:decimal"


# MotorSystemType.MotorHP
class MotorHP(BSElement):
    """The nameplate (rated) horsepower of the motor. (hp)"""

    element_type = "xs:decimal"


# MotorSystemType.MotorEfficiency
class MotorEfficiency(BSElement):
    """Indicates how well the motor converts electrical power into mechanical power and is defined as output power divided by input power expressed as a percentage. (0-100) (%)"""

    element_type = "xs:decimal"


# MotorSystemType.DriveEfficiency
class DriveEfficiency(BSElement):
    """A measure of how much power transferred through the drive is lost as heat, expressed as a percentage. (0-100) (%)"""

    element_type = "xs:decimal"


# MotorSystemType.FullLoadAmps
class FullLoadAmps(BSElement):
    """Current draw of motor at full capacity. (amps)"""

    element_type = "xs:decimal"


# MotorSystemType.MotorPoleCount
class MotorPoleCount(BSElement):
    """The number of pole electromagnetic windings in the motor's stator and used to assign MotorEfficiency. Pole count is always a multiple of 2."""

    element_type = "xs:integer"


# MotorSystemType.MotorEnclosureType
class MotorEnclosureType(BSElement):
    """Defines if the motor is open or enclosed."""

    element_type = "xs:string"
    element_enumerations = ["Open", "Enclosed", "Other", "Unknown"]


# MotorSystemType.MotorApplication
class MotorApplication(BSElement):
    """Type of system served by the motor."""

    element_type = "xs:string"
    element_enumerations = [
        "Fan",
        "Pump",
        "Conveyance",
        "Plug Load",
        "Process Load",
        "Compressor",
        "Other",
        "Unknown",
    ]


# HeatRecoverySystemType.HeatRecoveryEfficiency
class HeatRecoveryEfficiency(BSElement):
    """Efficiency of sensible heat recovery as a percentage. (0-100) (%)"""

    element_type = "xs:decimal"


# HeatRecoverySystemType.EnergyRecoveryEfficiency
class EnergyRecoveryEfficiency(BSElement):
    """The net total energy (sensible plus latent, also called enthalpy) recovered by the supply airstream adjusted by electric consumption, case heat loss or heat gain, air leakage and airflow mass imbalance between the two airstreams, as a percent of the potential total energy that could be recovered plus associated fan energy. (0-100) (%)"""

    element_type = "xs:decimal"


# HeatRecoverySystemType.HeatRecoveryType
class HeatRecoveryType(BSElement):
    """Type of heat recovery between two systems."""

    element_type = "xs:string"
    element_enumerations = [
        "Run around coil",
        "Thermal wheel",
        "Heat pipe",
        "Water to air heat exchanger",
        "Water to water heat exchanger",
        "Air to air heat exchanger",
        "Earth to air heat exchanger",
        "Earth to water heat exchanger",
        "Other",
        "Unknown",
    ]


# HeatRecoverySystemType.SystemIDReceivingHeat
class SystemIDReceivingHeat(BSElement):
    """ID number of the system that usually receives heat from another system."""


SystemIDReceivingHeat.element_attributes = [
    "IDref",  # IDREF
]

# HeatRecoverySystemType.SystemIDProvidingHeat
class SystemIDProvidingHeat(BSElement):
    """ID number of the system that usually provides heat to another system."""


SystemIDProvidingHeat.element_attributes = [
    "IDref",  # IDREF
]

# WallSystemType.WallRValue
class WallRValue(BSElement):
    """(Also known as thermal resistance), quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include the interior and exterior air film coefficients. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# WallSystemType.WallUFactor
class WallUFactor(BSElement):
    """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

    element_type = "xs:decimal"


# WallSystemType.WallFramingSpacing
class WallFramingSpacing(BSElement):
    """Dimension of the distance between two components. Framing spacing: the dimension from centerline to centerline of a surface framing material. (in.)"""

    element_type = "xs:decimal"


# WallSystemType.WallFramingDepth
class WallFramingDepth(BSElement):
    """Dimension of the distance from the front to the back, such as the depth of structural framing in a wall or floor. It can also be the distance from the top to the bottom, such as the depth of a tank or pool of a component or material, such as the depth of the structural framing. (in.)"""

    element_type = "xs:decimal"


# WallSystemType.WallFramingFactor
class WallFramingFactor(BSElement):
    """Fraction of the surface that is composed of structural framing material. (0-1) (fraction)"""

    element_type = "xs:decimal"


# WallSystemType.CMUFill
class CMUFill(BSElement):
    """
    The fill condition of hollow unit masonry walls. The definitions correspond to the following conditions -- Solid: Where every cell is grouted, Empty: Where the cells are partially grouted and the remaining cells are left empty, Insulated: Where the cells are partially grouted and the remaining cells are filled with insulating material.

    """

    element_type = "xs:string"
    element_enumerations = ["Empty", "Insulated", "Solid", "Unknown", "Not Applicable"]


# WallSystemType.WallExteriorSolarAbsorptance
class WallExteriorSolarAbsorptance(BSElement):
    """The fraction of incident radiation in the solar spectrum that is absorbed by the material or surface. (0-1) (fraction)"""

    element_type = "xs:decimal"


# WallSystemType.WallExteriorThermalAbsorptance
class WallExteriorThermalAbsorptance(BSElement):
    """The fraction of incident long wavelength infrared radiation that is absorbed by the material or surface. (0-1) (fraction)"""

    element_type = "xs:decimal"


# EnvelopeConstructionType
class EnvelopeConstructionType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Masonry",
        "Structural brick",
        "Stone",
        "Concrete masonry unit",
        "Concrete solid",
        "Concrete lightweight",
        "Concrete panels",
        "Concrete poured",
        "Concrete load bearing",
        "Concrete insulated forms",
        "Concrete aerated",
        "Steel frame",
        "Wood frame",
        "Double wood frame",
        "Structural insulated panel",
        "Log solid wood",
        "Straw bale",
        "Built up",
        "Other",
        "Unknown",
    ]


# Finish
class Finish(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Wood",
        "Masonite",
        "Stone",
        "Tile",
        "Brick",
        "Masonry",
        "Concrete",
        "Fiber cement",
        "Metal",
        "Metal panel",
        "Metal panel standing seam",
        "Sheet metal",
        "EIFS",
        "Shingles asphalt",
        "Shingles composition",
        "Shingles wood",
        "Shingles asbestos",
        "Shingles slate or tile",
        "Shakes wood",
        "Carpet",
        "Linoleum",
        "Asphalt or fiberglass",
        "Plastic rubber synthetic sheeting",
        "Other",
        "Unknown",
    ]


# Color
class Color(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "White",
        "Light",
        "Medium",
        "Medium dark",
        "Dark",
        "Reflective",
        "Other",
        "Unknown",
    ]


# InsulationMaterialType
class InsulationMaterialType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Fiberglass",
        "Cellulose",
        "EPS",
        "XPS",
        "Rock wool",
        "Insulsafe",
        "Recycled cotton",
        "ISOCY",
        "Icynene",
        "Closed cell",
        "Vermiculite",
        "Other",
        "Unknown",
        "None",
    ]


# WallSystemType.WallInsulations.WallInsulation.WallInsulationCondition
class WallInsulationCondition(InsulationCondition):
    pass


# WallSystemType.WallInsulations.WallInsulation.WallInsulationApplication
class WallInsulationApplication(BSElement):
    """A description of the type of insulation and how it is applied."""

    element_type = "xs:string"
    element_enumerations = [
        "Loose fill",
        "Batt",
        "Spray on",
        "Rigid",
        "Other",
        "Unknown",
        "None",
    ]


# WallSystemType.WallInsulations.WallInsulation.WallInsulationThickness
class WallInsulationThickness(BSElement):
    """Thickness of wall insulation. (in.)"""

    element_type = "xs:decimal"


# WallSystemType.WallInsulations.WallInsulation.WallInsulationContinuity
class WallInsulationContinuity(BSElement):
    """Insulation installation type."""

    element_type = "xs:string"
    element_enumerations = ["Cavity", "Continuous", "Other", "Unknown", "None"]


# WallSystemType.WallInsulations.WallInsulation.WallInsulationLocation
class WallInsulationLocation(BSElement):
    """Whether wall insulation is on the inside or outside of the wall."""

    element_type = "xs:string"
    element_enumerations = ["Interior", "Exterior", "Unknown", "None"]


# WallSystemType.WallInsulations.WallInsulation.WallInsulationRValue
class WallInsulationRValue(BSElement):
    """Insulation R Value of the layer. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# FramingMaterial
class FramingMaterial(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Wood",
        "Steel",
        "Concrete",
        "Brick",
        "Masonry",
        "Other",
        "Unknown",
        "None",
    ]


# ExteriorRoughness
class ExteriorRoughness(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Very rough",
        "Rough",
        "Medium rough",
        "Medium smooth",
        "Smooth",
        "Very smooth",
        "Unknown",
    ]


# CeilingSystemType.CeilingConstruction
class CeilingConstruction(EnvelopeConstructionType):
    """The general description of the main structural construction method used for an opaque surface."""


# CeilingSystemType.CeilingFinish
class CeilingFinish(Finish):
    """The final material applied to a surface, either interior or exterior. Some structural components don't have an exterior finish, such as unfinished poured concrete."""


# CeilingSystemType.CeilingColor
class CeilingColor(Color):
    """Color of a material or component. Can be applied to opaque surfaces, materials, and so forth."""


# CeilingSystemType.CeilingRValue
class CeilingRValue(BSElement):
    """(Also known as thermal resistance), quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include the interior and exterior air film coefficients. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# CeilingSystemType.CeilingUFactor
class CeilingUFactor(BSElement):
    """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

    element_type = "xs:decimal"


# CeilingSystemType.CeilingFramingMaterial
class CeilingFramingMaterial(FramingMaterial):
    """The material used to create the structural integrity in an opaque surface. In many cases the framing material is not continuous across the construction."""


# CeilingSystemType.CeilingFramingSpacing
class CeilingFramingSpacing(BSElement):
    """
    Dimension of the distance between two components. Examples include: Framing spacing: the dimension from centerline to centerline of a surface framing material. Window spacing: the dimension between windows in a discrete window layout. (in.)

    """

    element_type = "xs:decimal"


# CeilingSystemType.CeilingFramingDepth
class CeilingFramingDepth(BSElement):
    """Dimension of the distance from the front to the back, such as the depth of structural framing in a wall or floor. It can also be the distance from the top to the bottom, such as the depth of a tank or pool of a component or material, such as the depth of the structural framing. (in.)"""

    element_type = "xs:decimal"


# CeilingSystemType.CeilingFramingFactor
class CeilingFramingFactor(BSElement):
    """Fraction of the surface that is composed of structural framing material. (0-1) (fraction)"""

    element_type = "xs:decimal"


# CeilingSystemType.CeilingVisibleAbsorptance
class CeilingVisibleAbsorptance(BSElement):
    """The fraction of incident visible wavelength radiation that is absorbed by the material or surface. (0-1) (fraction)"""

    element_type = "xs:decimal"


# CeilingSystemType.CeilingInsulations.CeilingInsulation.CeilingInsulationMaterial
class CeilingInsulationMaterial(InsulationMaterialType):
    """Material used for the structural component of the surface."""


# CeilingSystemType.CeilingInsulations.CeilingInsulation.CeilingInsulationCondition
class CeilingInsulationCondition(InsulationCondition):
    pass


# CeilingSystemType.CeilingInsulations.CeilingInsulation.CeilingInsulationApplication
class CeilingInsulationApplication(BSElement):
    """A description of the type of insulation and how it is applied."""

    element_type = "xs:string"
    element_enumerations = [
        "Loose fill",
        "Batt",
        "Spray on",
        "Rigid",
        "Other",
        "Unknown",
        "None",
    ]


# CeilingSystemType.CeilingInsulations.CeilingInsulation.CeilingInsulationThickness
class CeilingInsulationThickness(BSElement):
    """Thickness of roof insulation. (in.)"""

    element_type = "xs:decimal"


# CeilingSystemType.CeilingInsulations.CeilingInsulation.CeilingInsulationContinuity
class CeilingInsulationContinuity(BSElement):
    """Insulation installation type."""

    element_type = "xs:string"
    element_enumerations = ["Cavity", "Continuous", "Other", "Unknown", "None"]


# RoofSystemType.RoofConstruction
class RoofConstruction(EnvelopeConstructionType):
    """The general description of the main structural construction method used for an opaque surface."""


# RoofSystemType.BlueRoof
class BlueRoof(BSElement):
    """A blue roof is a roof design that is explicitly intended to store water, typically rainfall."""

    element_type = "xs:boolean"


# RoofSystemType.CoolRoof
class CoolRoof(BSElement):
    """A cool roof reduces roof temperature with a high solar reflectance (or albedo) material that helps to reflect sunlight and heat away from a building."""

    element_type = "xs:boolean"


# RoofSystemType.GreenRoof
class GreenRoof(BSElement):
    """A green roof or living roof is a roof of a building that is partially or completely covered with vegetation and a growing medium, planted over a waterproofing membrane."""

    element_type = "xs:boolean"


# RoofSystemType.RoofFinish
class RoofFinish(Finish):
    """The final material applied to a surface, either interior or exterior. Some structural components don't have an exterior finish, such as unfinished poured concrete."""


# RoofSystemType.RoofColor
class RoofColor(Color):
    """Color of a material or component. Can be applied to opaque surfaces, materials, and so forth."""


# RoofSystemType.DeckType
class DeckType(BSElement):
    """The material used to create the structural integrity in an opaque surface. In many cases the framing material is not continuous across the construction."""

    element_type = "xs:string"
    element_enumerations = [
        "Wood",
        "Steel",
        "Concrete",
        "Brick",
        "Masonry",
        "Other",
        "Unknown",
        "None",
    ]


# RoofSystemType.RoofRValue
class RoofRValue(BSElement):
    """(Also known as thermal resistance), quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include the interior and exterior air film coefficients. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofUFactor
class RoofUFactor(BSElement):
    """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofFramingMaterial
class RoofFramingMaterial(FramingMaterial):
    """The material used to create the structural integrity in an opaque surface. In many cases the framing material is not continuous across the construction."""


# RoofSystemType.RoofFramingSpacing
class RoofFramingSpacing(BSElement):
    """Dimension of the distance between two components. Examples include: Framing spacing: the dimension from centerline to centerline of a surface framing material. (in.)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofFramingDepth
class RoofFramingDepth(BSElement):
    """Dimension of the distance from the front to the back, such as the depth of structural framing in a wall or floor. It can also be the distance from the top to the bottom, such as the depth of a tank or pool of a component or material, such as the depth of the structural framing. (in.)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofFramingFactor
class RoofFramingFactor(BSElement):
    """Fraction of the surface that is composed of structural framing material. (0-1) (fraction)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofSlope
class RoofSlope(BSElement):
    """A descriptive value for tilt, when an exact numeric angle is not known."""

    element_type = "xs:string"
    element_enumerations = [
        "Flat",
        "Sloped",
        "Greater than 2 to 12",
        "Less than 2 to 12",
        "Other",
        "Unknown",
    ]


# RoofSystemType.RadiantBarrier
class RadiantBarrier(BSElement):
    """True if a radiant barrier is installed, false otherwise."""

    element_type = "xs:boolean"


# RoofSystemType.RoofExteriorSolarAbsorptance
class RoofExteriorSolarAbsorptance(BSElement):
    """The fraction of incident radiation in the solar spectrum that is absorbed by the material or surface. (0-1) (fraction)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofExteriorSolarReflectanceIndex
class RoofExteriorSolarReflectanceIndex(BSElement):
    """A measure of a roof's ability to reject solar heat, as shown by a small temperature rise. It is defined so that a standard black (reflectance 0.05, emittance 0.90) is 0 and a standard white (reflectance 0.80, emittance 0.90) is 100."""

    element_type = "xs:integer"


# RoofSystemType.RoofExteriorThermalAbsorptance
class RoofExteriorThermalAbsorptance(BSElement):
    """The fraction of incident long wavelength infrared radiation that is absorbed by the material or surface. (0-1) (fraction)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofInsulations.RoofInsulation.RoofInsulationMaterial
class RoofInsulationMaterial(InsulationMaterialType):
    """Material used for the structural component of the surface."""


# RoofSystemType.RoofInsulations.RoofInsulation.RoofInsulationCondition
class RoofInsulationCondition(InsulationCondition):
    pass


# RoofSystemType.RoofInsulations.RoofInsulation.RoofInsulationApplication
class RoofInsulationApplication(BSElement):
    """A description of the type of insulation and how it is applied."""

    element_type = "xs:string"
    element_enumerations = [
        "Loose fill",
        "Batt",
        "Spray on",
        "Rigid",
        "Other",
        "Unknown",
        "None",
    ]


# RoofSystemType.RoofInsulations.RoofInsulation.RoofInsulationThickness
class RoofInsulationThickness(BSElement):
    """Thickness of roof insulation. (in.)"""

    element_type = "xs:decimal"


# RoofSystemType.RoofInsulations.RoofInsulation.RoofInsulationContinuity
class RoofInsulationContinuity(BSElement):
    """Insulation installation type."""

    element_type = "xs:string"
    element_enumerations = ["Cavity", "Continuous", "Other", "Unknown", "None"]


# RoofSystemType.RoofInsulations.RoofInsulation.RoofInsulationRValue
class RoofInsulationRValue(BSElement):
    """Insulation R Value of the layer. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationFrameMaterial
class FenestrationFrameMaterial(BSElement):
    """The construction and material used in the frame of the fenestration product. Some frames are made of combinations of materials. This characterization also include whether an aluminum frame has a thermal break as part of the construction."""

    element_type = "xs:string"
    element_enumerations = [
        "Aluminum uncategorized",
        "Aluminum no thermal break",
        "Aluminum thermal break",
        "Clad",
        "Composite",
        "Fiberglass",
        "Steel",
        "Vinyl",
        "Wood",
        "Other",
        "Unknown",
    ]


# FenestrationSystemType.FenestrationOperation
class FenestrationOperation(BSElement):
    """True if the fenestration product can be opened and closed as desired by the occupant to provide better control of office space conditions."""

    element_type = "xs:boolean"


# FenestrationSystemType.Weatherstripped
class Weatherstripped(BSElement):
    """True if fenestration is weatherstripped, false otherwise."""

    element_type = "xs:boolean"


# FenestrationSystemType.TightnessFitCondition
class TightnessFitCondition(Tightness):
    """Indicator of expected air leakage through fenestration."""


# FenestrationSystemType.GlassType
class GlassType(BSElement):
    """Type of glass used in this fenestration group."""

    element_type = "xs:string"
    element_enumerations = [
        "Clear uncoated",
        "Low e",
        "Tinted",
        "Tinted plus low e",
        "Reflective",
        "Reflective on tint",
        "High performance tint",
        "Sunbelt low E low SHGC",
        "Suspended film",
        "Plastic",
        "Other",
        "Unknown",
    ]


# FenestrationSystemType.FenestrationGasFill
class FenestrationGasFill(BSElement):
    """For a sealed glazing system (commonly called an Insulated Glass Unit (IGU)), the gas that is found between the panes of glass."""

    element_type = "xs:string"
    element_enumerations = [
        "Argon",
        "Krypton",
        "Other Insulating Gas",
        "Air",
        "Other",
        "Unknown",
    ]


# FenestrationSystemType.FenestrationGlassLayers
class FenestrationGlassLayers(BSElement):
    """A description of the number of layers of glass in a fenestration glazing system."""

    element_type = "xs:string"
    element_enumerations = [
        "Single pane",
        "Double pane",
        "Triple pane",
        "Single paned with storm panel",
        "Unknown",
    ]


# FenestrationSystemType.FenestrationRValue
class FenestrationRValue(BSElement):
    """(Also known as thermal resistance), quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include the interior and exterior air film coefficients. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationUFactor
class FenestrationUFactor(BSElement):
    """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

    element_type = "xs:decimal"


# FenestrationSystemType.SolarHeatGainCoefficient
class SolarHeatGainCoefficient(BSElement):
    """The ratio of the solar heat gain entering the space through the fenestration product to the incident solar radiation. Solar heat gain includes directly transmitted solar heat and that portion of the absorbed solar radiation which is then reradiated, conducted, or convected into the space. (0-1) (fraction)"""

    element_type = "xs:decimal"


# FenestrationSystemType.VisibleTransmittance
class VisibleTransmittance(BSElement):
    """The fraction of radiation in the visible solar spectrum (0.4 to 0.7 micrometers) that passes through a the glazed portion of fenestration. (0-1) (fraction)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.LightShelves.LightShelfDistanceFromTop
class LightShelfDistanceFromTop(BSElement):
    """Vertical distance from top of window to the light shelf. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.LightShelves.LightShelfExteriorProtrusion
class LightShelfExteriorProtrusion(BSElement):
    """Horizontal distance that the light shelf extends exterior to the window. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.LightShelves.LightShelfInteriorProtrusion
class LightShelfInteriorProtrusion(BSElement):
    """Horizontal distance that the light shelf extends interior to the window. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.WindowLayout
class WindowLayout(BSElement):
    """The pattern of distribution of the fenestration system on the wall."""

    element_type = "xs:string"
    element_enumerations = ["Continuous", "Discrete", "Unknown"]


# FenestrationSystemType.FenestrationType.Window.WindowOrientation
class WindowOrientation(BSElement):
    """Orientation of a surface or premises in terms of the attributes of North, South, East and West. Can be applied to the orientation of the front of the building, of a specific surface (wall, roof), window or skylight, or onsite generation technology, such as photovoltaic panels."""

    element_type = "xs:string"
    element_enumerations = [
        "North",
        "Northeast",
        "East",
        "Southeast",
        "South",
        "Southwest",
        "West",
        "Northwest",
        "Unknown",
    ]


# FenestrationSystemType.FenestrationType.Window.WindowSillHeight
class WindowSillHeight(BSElement):
    """Vertical distance from the floor to the window sill. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.WindowHeight
class WindowHeight(BSElement):
    """Vertical height of each window. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.WindowWidth
class WindowWidth(BSElement):
    """Horizontal width of each window. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.WindowHorizontalSpacing
class WindowHorizontalSpacing(BSElement):
    """Horizontal distance between the centers of adjacent windows. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.ExteriorShadingType
class ExteriorShadingType(BSElement):
    """Any type of overhang or awning on the outside of the building designed to limit solar penetration."""

    element_type = "xs:string"
    element_enumerations = [
        "Overhang",
        "Fin",
        "Awning",
        "Solar screen",
        "Solar film",
        "Louver",
        "Screen",
        "Deciduous foliage",
        "Evergreen foliage",
        "Neighboring building",
        "None",
        "Other",
        "Unknown",
    ]


# FenestrationSystemType.FenestrationType.Window.OverhangHeightAboveWindow
class OverhangHeightAboveWindow(BSElement):
    """Vertical distance from top of window to base of overhang. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.OverhangProjection
class OverhangProjection(BSElement):
    """Horizontal distance that the overhang extends beyond the wall. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.VerticalFinDepth
class VerticalFinDepth(BSElement):
    """Horizontal distance that the fins extend beyond the wall. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.DistanceBetweenVerticalFins
class DistanceBetweenVerticalFins(BSElement):
    """Horizontal spacing between individual fins. (ft)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Window.VerticalEdgeFinOnly
class VerticalEdgeFinOnly(BSElement):
    """True if edge fins, otherwise false."""

    element_type = "xs:boolean"


# FenestrationSystemType.FenestrationType.Window.InteriorShadingType
class InteriorShadingType(BSElement):
    """Type of interior shading."""

    element_type = "xs:string"
    element_enumerations = ["Blind", "Curtain", "Shade", "None", "Other", "Unknown"]


# FenestrationSystemType.FenestrationType.Skylight.SkylightLayout
class SkylightLayout(BSElement):
    """Zones daylit by skylights."""

    element_type = "xs:string"
    element_enumerations = ["All Zones", "Core Only", "Other", "Unknown"]


# FenestrationSystemType.FenestrationType.Skylight.SkylightPitch
class SkylightPitch(BSElement):
    """Skylight angle from horizontal expressed as height over horizontal distance. (degrees)"""

    element_type = "xs:decimal"


# FenestrationSystemType.FenestrationType.Skylight.SkylightWindowTreatments
class SkylightWindowTreatments(BSElement):
    """Type of film or shading applied to skylight."""

    element_type = "xs:string"
    element_enumerations = ["Solar film", "Solar screen", "Shade", "None", "Unknown"]


# FenestrationSystemType.FenestrationType.Skylight.SkylightSolarTube
class SkylightSolarTube(BSElement):
    """True if skylights are solar tubes or tubular daylighting devices, false otherwise."""

    element_type = "xs:boolean"


# FenestrationSystemType.FenestrationType.Door.ExteriorDoorType
class ExteriorDoorType(BSElement):
    """Type of door construction."""

    element_type = "xs:string"
    element_enumerations = [
        "Solid wood",
        "Hollow wood",
        "Uninsulated metal",
        "Insulated metal",
        "Glass",
        "Other",
        "Unknown",
    ]


# FenestrationSystemType.FenestrationType.Door.Vestibule
class Vestibule(BSElement):
    """True if door is connected to a vestibule."""

    element_type = "xs:boolean"


# FenestrationSystemType.FenestrationType.Door.DoorOperation
class DoorOperation(BSElement):
    """Non-swinging includes sliding doors and roll-up doors."""

    element_type = "xs:string"
    element_enumerations = ["NonSwinging", "Swinging", "Unknown"]


# ExteriorFloorSystemType.ExteriorFloorConstruction
class ExteriorFloorConstruction(EnvelopeConstructionType):
    """The general description of the main structural construction method used for an opaque surface."""


# ExteriorFloorSystemType.ExteriorFloorFinish
class ExteriorFloorFinish(Finish):
    """The final material applied to a surface, either interior or exterior. Some structural components don't have an exterior finish, such as unfinished poured concrete."""


# ExteriorFloorSystemType.ExteriorFloorColor
class ExteriorFloorColor(Color):
    """Color of a material or component. Can be applied to opaque surfaces, materials, and so forth."""


# ExteriorFloorSystemType.ExteriorFloorRValue
class ExteriorFloorRValue(BSElement):
    """R-value of exterior floor. (ft2-F-hr/Btu)"""

    element_type = "xs:decimal"


# ExteriorFloorSystemType.ExteriorFloorUFactor
class ExteriorFloorUFactor(BSElement):
    """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

    element_type = "xs:decimal"


# ExteriorFloorSystemType.ExteriorFloorFramingMaterial
class ExteriorFloorFramingMaterial(FramingMaterial):
    """The material used to create the structural integrity in an opaque surface. In many cases the framing material is not continuous across the construction."""


# ExteriorFloorSystemType.ExteriorFloorFramingSpacing
class ExteriorFloorFramingSpacing(BSElement):
    """Dimension of the distance between two components. Framing spacing: the dimension from centerline to centerline of a surface framing material. (in.)"""

    element_type = "xs:decimal"


# ExteriorFloorSystemType.ExteriorFloorFramingDepth
class ExteriorFloorFramingDepth(BSElement):
    """Dimension of the distance from the front to the back, such as the depth of structural framing in a wall or floor. It can also be the distance from the top to the bottom, such as the depth of a tank or pool of a component or material, such as the depth of the structural framing. (in.)"""

    element_type = "xs:decimal"


# ExteriorFloorSystemType.ExteriorFloorFramingFactor
class ExteriorFloorFramingFactor(BSElement):
    """Fraction of the surface that is composed of structural framing material. (0-1) (fraction)"""

    element_type = "xs:decimal"


# ExteriorFloorSystemType.ExteriorFloorExteriorSolarAbsorptance
class ExteriorFloorExteriorSolarAbsorptance(BSElement):
    """The fraction of incident radiation in the solar spectrum that is absorbed by the material or surface. (0-1) (fraction)"""

    element_type = "xs:decimal"


# ExteriorFloorSystemType.ExteriorFloorExteriorThermalAbsorptance
class ExteriorFloorExteriorThermalAbsorptance(BSElement):
    """The fraction of incident long wavelength infrared radiation that is absorbed by the material or surface. (0-1) (fraction)"""

    element_type = "xs:decimal"


# FoundationSystemType.FloorCovering
class FloorCovering(BSElement):
    """Material covering the slab or floor over unconditioned space."""

    element_type = "xs:string"
    element_enumerations = [
        "Carpet",
        "Tile",
        "Hardwood",
        "Vinyl",
        "Linoleum",
        "Other",
        "Unknown",
    ]


# FoundationSystemType.FloorConstructionType
class FloorConstructionType(EnvelopeConstructionType):
    """Construction type for floors over unconditioned space."""


# FoundationSystemType.PlumbingPenetrationSealing
class PlumbingPenetrationSealing(BSElement):
    """Type of plumbing penetration sealing."""

    element_type = "xs:string"
    element_enumerations = ["Flashing", "Fitting", "Other", "Unknown"]


# SlabInsulationOrientation
class SlabInsulationOrientation(BSElement):
    """The location and extent of slab-on-grade floor insulation."""

    element_type = "xs:string"
    element_enumerations = [
        "12 in Horizontal",
        "12 in Vertical",
        "24 in Horizontal",
        "24 in Vertical",
        "36 in Horizontal",
        "36 in Vertical",
        "48 in Horizontal",
        "48 in Vertical",
        "Fully Insulated Slab",
        "None",
        "Unknown",
    ]


# FoundationSystemType.GroundCouplings.GroundCoupling.SlabOnGrade.SlabRValue
class SlabRValue(BSElement):
    """Also known as thermal resistance, quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include air film coefficients. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# FoundationSystemType.GroundCouplings.GroundCoupling.SlabOnGrade.SlabUFactor
class SlabUFactor(BSElement):
    """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

    element_type = "xs:decimal"


# SlabHeating
class SlabHeating(BSElement):
    """The classifications for floors in contact with the ground."""

    element_type = "xs:string"
    element_enumerations = ["Heated", "Unheated", "Other", "Unknown"]


# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated.FloorInsulationCondition
class FloorInsulationCondition(InsulationCondition):
    pass


# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated.FloorInsulationThickness
class FloorInsulationThickness(BSElement):
    """Thickness of insulation under floor over unconditioned space. (in.)"""

    element_type = "xs:decimal"


# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated.FloorRValue
class FloorRValue(BSElement):
    """(Also known as thermal resistance), quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include the interior and exterior air film coefficients. (hr-ft2-F/Btu)"""

    element_type = "xs:decimal"


# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated.FloorUFactor
class FloorUFactor(BSElement):
    """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

    element_type = "xs:decimal"


# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated.FloorFramingSpacing
class FloorFramingSpacing(BSElement):
    """Dimension of the distance between two components. Examples include--Framing spacing: the dimension from centerline to centerline of a surface framing material. Window spacing: the dimension between windows in a discrete window layout. (in.)"""

    element_type = "xs:decimal"


# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated.FloorFramingDepth
class FloorFramingDepth(BSElement):
    """Dimension of the distance from the front to the back, such as the depth of structural framing in a wall or floor. It can also be the distance from the top to the bottom, such as the depth of a tank or pool of a component or material, such as the depth of the structural framing. (in.)"""

    element_type = "xs:decimal"


# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated.FloorFramingFactor
class FloorFramingFactor(BSElement):
    """Fraction of the surface that is composed of structural framing material. (0-1) (fraction)"""

    element_type = "xs:decimal"


# FoundationWallInsulationContinuity
class FoundationWallInsulationContinuity(BSElement):
    """Insulation installation type."""

    element_type = "xs:string"
    element_enumerations = ["Cavity", "Continuous", "Other", "Unknown", "None"]


# FoundationSystemType.GroundCouplings.GroundCoupling.Basement.BasementConditioning
class BasementConditioning(BSElement):
    """Extent of space conditioning in basement."""

    element_type = "xs:string"
    element_enumerations = [
        "Conditioned",
        "Unconditioned",
        "Semi conditioned",
        "Other",
        "Unknown",
    ]


# CriticalITSystemType.ITSystemType
class ITSystemType(BSElement):
    """Type of critical information technology (IT) system, including data centers, network, and security systems."""

    element_type = "xs:string"
    element_enumerations = [
        "Building Automation System",
        "Server",
        "Networking",
        "Security",
        "Telephoning",
        "UPS",
        "Other",
        "Unknown",
    ]


# CriticalITSystemType.ITPeakPower
class ITPeakPower(BSElement):
    """The maximum instantaneous power use (ASHRAE Guideline 14-2014 section E1.2.2)."""

    element_type = "xs:decimal"


# CriticalITSystemType.ITStandbyPower
class ITStandbyPower(BSElement):
    """Electric power consumed by while the equipment is switched off or in a standby mode. (W)"""

    element_type = "xs:decimal"


# CriticalITSystemType.ITNominalPower
class ITNominalPower(BSElement):
    """Average electrical load for critical IT system category. (W)"""

    element_type = "xs:decimal"


# PlugElectricLoadType.PlugLoadType
class PlugLoadType(BSElement):
    """General category of plug load, including non-critical IT systems, task lighting, and other small electronic loads."""

    element_type = "xs:string"
    element_enumerations = [
        "Personal Computer",
        "Task Lighting",
        "Printing",
        "Cash Register",
        "Audio",
        "Display",
        "Set Top Box",
        "Business Equipment",
        "Broadcast Antenna",
        "Kitchen Equipment",
        "Signage Display",
        "Miscellaneous Electric Load",
        "Other",
        "Unknown",
    ]


# PlugElectricLoadType.PlugLoadPeakPower
class PlugLoadPeakPower(BSElement):
    """The maximum instantaneous power use (ASHRAE Guideline 14-2014 section E1.2.2)."""

    element_type = "xs:decimal"


# PlugElectricLoadType.PlugLoadStandbyPower
class PlugLoadStandbyPower(BSElement):
    """Electric power consumed by while the equipment is switched off or in a standby mode. (W)"""

    element_type = "xs:decimal"


# PlugElectricLoadType.PlugLoadNominalPower
class PlugLoadNominalPower(BSElement):
    """Nominal electrical load for plug load category. (W)"""

    element_type = "xs:decimal"


# ProcessGasElectricLoadType.ProcessLoadType
class ProcessLoadType(BSElement):
    """Type of gas or electric equipment not categorized elsewhere."""

    element_type = "xs:string"
    element_enumerations = [
        "Medical Equipment",
        "Laboratory Equipment",
        "Machinery",
        "Air Compressor",
        "Fume Hood",
        "Appliance",
        "Gaming/Hobby/Leisure",
        "Infrastructure",
        "Electric Vehicle Charging",
        "Miscellaneous Gas Load",
        "Other",
        "Unknown",
    ]


# ProcessGasElectricLoadType.ProcessLoadPeakPower
class ProcessLoadPeakPower(BSElement):
    """The maximum instantaneous power use (ASHRAE Guideline 14-2014 section E1.2.2)."""

    element_type = "xs:decimal"


# ProcessGasElectricLoadType.ProcessLoadStandbyPower
class ProcessLoadStandbyPower(BSElement):
    """Electric power consumed by while the equipment is switched off or in a standby mode. (W)"""

    element_type = "xs:decimal"


# ConveyanceSystemType.ConveyanceLoadType
class ConveyanceLoadType(BSElement):
    """Type of load that the conveyance system usually transports."""

    element_type = "xs:string"
    element_enumerations = ["People", "Freight", "Goods", "Other", "Unknown"]


# ConveyanceSystemType.ConveyancePeakPower
class ConveyancePeakPower(BSElement):
    """The maximum instantaneous power use (ASHRAE Guideline 14-2014 section E1.2.2)."""

    element_type = "xs:decimal"


# ConveyanceSystemType.ConveyanceStandbyPower
class ConveyanceStandbyPower(BSElement):
    """Electric power consumed by while the equipment is switched off or in a standby mode. (W)"""

    element_type = "xs:decimal"


# ConveyanceSystemType.ConveyanceSystemCondition
class ConveyanceSystemCondition(EquipmentCondition):
    """Description of the conveyance system's condition."""


# OnsiteStorageTransmissionGenerationSystemType.BackupGenerator
class BackupGenerator(BSElement):
    """True if system is only used for backup purposes."""

    element_type = "xs:boolean"


# OnsiteStorageTransmissionGenerationSystemType.DemandReduction
class DemandReduction(BSElement):
    """True if system is used for demand reduction purposes."""

    element_type = "xs:boolean"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Storage.EnergyStorageTechnology
class EnergyStorageTechnology(BSElement):
    """A few different forms of energy storage systems exist including: potential, kinetic, chemical and thermal. The critical factors of any storage device are application (type and size), costs, cycle efficiency and longevity."""

    element_type = "xs:string"
    element_enumerations = [
        "Battery",
        "Thermal Energy Storage",
        "Pumped-Storage Hydroelectricity",
        "Flywheel",
        "Other",
        "Unknown",
    ]


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Storage.ThermalMedium
class ThermalMedium(BSElement):
    """Type of material used in thermal energy storage technology."""

    element_type = "xs:string"
    element_enumerations = [
        "Air",
        "Ice",
        "Pool water",
        "Domestic water",
        "Molten salt",
        "Sand",
        "Rock",
        "Chemical oxides",
        "Other",
        "Unknown",
    ]


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemNumberOfModulesPerArray
class PhotovoltaicSystemNumberOfModulesPerArray(BSElement):
    """Number of modules in each array of a photovoltaic system."""

    element_type = "xs:integer"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemNumberOfArrays
class PhotovoltaicSystemNumberOfArrays(BSElement):
    """Number of arrays in a photovoltaic system."""

    element_type = "xs:integer"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemMaximumPowerOutput
class PhotovoltaicSystemMaximumPowerOutput(BSElement):
    """Peak power as supplied by the manufacturer. (Wdc)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemInverterEfficiency
class PhotovoltaicSystemInverterEfficiency(BSElement):
    """Fraction of power that is converted to usable AC efficiency. (0-1) (fraction)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemArrayAzimuth
class PhotovoltaicSystemArrayAzimuth(BSElement):
    """Degrees clockwise from North. For a premises, it is the azimuth of the front facing element. It can also be applied to envelope components, such as walls, windows (fenestration), as well as onsite generation technologies, such as photovoltaic panels. Legal Values: 0 - 360. (degrees)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemRackingSystemTiltAngleMin
class PhotovoltaicSystemRackingSystemTiltAngleMin(BSElement):
    """Minimum PV mounting angle relative to horizontal. Minimum and maximum tilt angles are the same for fixed systems. (degrees)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemRackingSystemTiltAngleMax
class PhotovoltaicSystemRackingSystemTiltAngleMax(BSElement):
    """Maximum PV mounting angle relative to horizontal. Minimum and maximum tilt angles are the same for fixed systems. (degrees)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicSystemLocation
class PhotovoltaicSystemLocation(BSElement):
    """Location where PV system is mounted."""

    element_type = "xs:string"
    element_enumerations = [
        "Roof",
        "On grade",
        "Building integrated",
        "Other",
        "Unknown",
    ]


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicModuleRatedPower
class PhotovoltaicModuleRatedPower(BSElement):
    """The module's rated, maximum-power-point power at standard testing conditions (STC) (SAM Help, 2013). Where STC is defined as light spectrum AM 1.5, cell temperature of 25 degrees Celsius, and irradiance of 1000 W/m2 (IEC 61853-1 Standard 7.2-2010). (W)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicModuleLength
class PhotovoltaicModuleLength(BSElement):
    """The total length of the module including the frame. Length here is defined as the longest side of the module. (in.)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV.PhotovoltaicModuleWidth
class PhotovoltaicModuleWidth(BSElement):
    """The total width of the module including the frame. Width is here defined as the distance between the two longest module sides. (in.)"""

    element_type = "xs:decimal"


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.Other.OutputResourceType
class OutputResourceType(FuelTypes):
    """Resource or fuel produced by the generation system and used as energy on the premises."""


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.Other.OtherEnergyGenerationTechnology
class OtherEnergyGenerationTechnology(BSElement):
    """Technology utilized on the premises to generate non-purchased energy, including renewable energy that is passively collected. This includes energy collected from the environment such as air, water, or ground-source heat pump systems. Technology equipment may exist as facade systems and roofing systems. Technology equipment may also exist on a premises off of a building envelope including on the ground, awnings, or carports as well as underground."""

    element_type = "xs:string"
    element_enumerations = [
        "Standby generator",
        "Turbine",
        "Microturbine",
        "Reciprocating engine",
        "Fuel cell",
        "Gasification",
        "Binary Cycle",
        "Anaerobic biodigester",
        "Hydrokinetic",
        "Solar parabolic trough",
        "Solar power tower",
        "Wind",
        "Other",
        "Unknown",
    ]


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.ExternalPowerSupply
class ExternalPowerSupply(BSElement):
    """Designed to convert line voltage ac input into lower voltage ac or dc output, convert to only one output voltage at a time, contained in a separate physical enclosure from the end-use product, and does not have batteries or battery packs that physically attach directly (including those that are removable) to the power supply unit."""

    element_type = "xs:string"
    element_enumerations = [
        "AC to AC",
        "AC to DC",
        "Low Voltage",
        "No Load",
        "Other",
        "Unknown",
    ]


# PoolType.PoolSizeCategory
class PoolSizeCategory(BSElement):
    """Classification of the pool size."""

    element_type = "xs:string"
    element_enumerations = [
        "Olympic",
        "Recreational",
        "Short Course",
        "Other",
        "Unknown",
    ]


# PoolType.PoolArea
class PoolArea(BSElement):
    """Surface area of pool. (ft2)"""

    element_type = "xs:decimal"


# PoolType.PoolVolume
class PoolVolume(BSElement):
    """Volume of the pool. (gal)"""

    element_type = "xs:decimal"


# PoolType.PumpDutyCycle
class PumpDutyCycle(BSElement):
    """Average duty cycle of pool pump, represented as percentage. (0-100) (%)"""

    element_type = "xs:decimal"


# PoolType.Heated.WaterTemperature
class WaterTemperature(BSElement):
    """Set point for pool heating. (°F)"""

    element_type = "xs:decimal"


# PoolType.Heated.HoursUncovered
class HoursUncovered(BSElement):
    """Average hours per day the pool is uncovered. (hrs/day)"""

    element_type = "xs:decimal"


# WaterUseType.LowFlowFixtures
class LowFlowFixtures(BSElement):
    """True if the fixtures used for this application include aerators, low flow toilets, or showerheads with flow restrictors."""

    element_type = "xs:boolean"


# WaterUseType.WaterFixtureRatedFlowRate
class WaterFixtureRatedFlowRate(BSElement):
    """Rated volumetric flow rate of the water fixture. (gpm)"""

    element_type = "xs:decimal"


# WaterUseType.WaterFixtureVolumePerCycle
class WaterFixtureVolumePerCycle(BSElement):
    """Average amount of water used per cycle of the fixture. (gal/cycle)"""

    element_type = "xs:decimal"


# WaterUseType.WaterFixtureCyclesPerDay
class WaterFixtureCyclesPerDay(BSElement):
    """Average number of draws per day for this fixture. (cycles/day)"""

    element_type = "xs:decimal"


# CalculationMethodType.Modeled.SoftwareProgramUsed
class SoftwareProgramUsed(BSElement):
    """Building energy modeling software used to estimate energy savings."""

    element_type = "xs:string"


# CalculationMethodType.Modeled.SoftwareProgramVersion
class SoftwareProgramVersion(BSElement):
    """Version number of building energy modeling software."""

    element_type = "xs:string"


# CalculationMethodType.Modeled.WeatherDataType
class WeatherDataType(BSElement):
    """Type of weather data used for the simulation."""

    element_type = "xs:string"
    element_enumerations = [
        "CWEC",
        "CZRV2",
        "IWEC",
        "Onsite Measurement",
        "TMY",
        "TMY2",
        "TMY3",
        "Weather Station",
        "Other",
        "Unknown",
    ]


# CalculationMethodType.Modeled.SimulationCompletionStatus
class SimulationCompletionStatus(BSElement):
    """Status of the simulation."""

    element_type = "xs:string"
    element_enumerations = ["Not Started", "Started", "Finished", "Failed", "Unknown"]


# CalculationMethodType.Measured.MeasuredEnergySource.DirectMeasurement
class DirectMeasurement(BSElement):
    pass


# EstimatedType
class EstimatedType(BSElement):
    pass


# EngineeringCalculationType
class EngineeringCalculationType(BSElement):
    pass


# Address.StreetAddressDetail.Simplified.StreetAddress
class StreetAddress(BSElement):
    """Street Address. This address can be defined multiple times for situations where that is needed for one premises, such as a complex of buildings. This address represents a complete street address, including street number, street name, prefixes, suffixes, modifiers, and unit number. It is assumed that a street address is either represented in this way, as a complete address, or is broken up into it's various components, using the terms"Street Number", "Street Number Numeric", "Street Dir Prefix", "Street Name", "Street Additional Info", "Street Suffix", "Street Suffix Modifier", "Street Dir Suffix", and "Unit Number"."""

    element_type = "xs:string"


# Address.StreetAddressDetail.Complex.StreetNumberPrefix
class StreetNumberPrefix(BSElement):
    """The portion of the complete address number which precedes the Address Number itself."""

    element_type = "xs:string"


# Address.StreetAddressDetail.Complex.StreetNumberNumeric
class StreetNumberNumeric(BSElement):
    """The numeric identifier for a land parcel, house, building, or other location along a thoroughfare or within a community."""

    element_type = "xs:integer"


# Address.StreetAddressDetail.Complex.StreetNumberSuffix
class StreetNumberSuffix(BSElement):
    """The portion of the complete address number which follows the Address Number itself. In some areas the street number may contain non-numeric characters. This field can also contain extensions and modifiers to the street number, such as "1/2" or "-B". This street number field should not include Prefixes, Direction or Suffixes."""

    element_type = "xs:string"


# Address.StreetAddressDetail.Complex.StreetDirPrefix
class StreetDirPrefix(BSElement):
    """The direction indicator that precedes the street name."""

    element_type = "xs:string"
    element_enumerations = [
        "North",
        "Northeast",
        "East",
        "Southeast",
        "South",
        "Southwest",
        "West",
        "Northwest",
    ]


# Address.StreetAddressDetail.Complex.StreetName
class StreetName(BSElement):
    """The street name portion of a street address."""

    element_type = "xs:string"


# Address.StreetAddressDetail.Complex.StreetSuffix
class StreetSuffix(BSElement):
    """The suffix portion of a street address."""

    element_type = "xs:string"
    element_enumerations = [
        "Alley",
        "Annex",
        "Arcade",
        "Avenue",
        "Bayou",
        "Beach",
        "Bend",
        "Bluff",
        "Bluffs",
        "Bottom",
        "Boulevard",
        "Branch",
        "Bridge",
        "Brook",
        "Brooks",
        "Burg",
        "Burgs",
        "Bypass",
        "Camp",
        "Canyon",
        "Cape",
        "Causeway",
        "Center",
        "Centers",
        "Circle",
        "Circles",
        "Cliff",
        "Club",
        "Common",
        "Commons",
        "Corner",
        "Corners",
        "Course",
        "Court",
        "Courts",
        "Cove",
        "Coves",
        "Creek",
        "Crescent",
        "Crest",
        "Crossing",
        "Crossroad",
        "Crossroads",
        "Curve",
        "Dale",
        "Dam",
        "Divide",
        "Drive",
        "Drives",
        "Estate",
        "Estates",
        "Expressway",
        "Extension",
        "Extensions",
        "Fall",
        "Falls",
        "Ferry",
        "Field",
        "Fields",
        "Flat",
        "Flats",
        "Ford",
        "Fords",
        "Forest",
        "Forge",
        "Forges",
        "Fork",
        "Forks",
        "Fort",
        "Freeway",
        "Garden",
        "Gardens",
        "Gateway",
        "Glen",
        "Glens",
        "Green",
        "Greens",
        "Grove",
        "Groves",
        "Harbor",
        "Harbors",
        "Haven",
        "Heights",
        "Highway",
        "Hill",
        "Hills",
        "Hollow",
        "Inlet",
        "Island",
        "Islands",
        "Isle",
        "Junction",
        "Junctions",
        "Key",
        "Keys",
        "Knoll",
        "Knolls",
        "Lake",
        "Lakes",
        "Land",
        "Landing",
        "Lane",
        "Light",
        "Lights",
        "Loaf",
        "Lock",
        "Locks",
        "Lodge",
        "Loop",
        "Mall",
        "Manor",
        "Manors",
        "Meadow",
        "Meadows",
        "Mews",
        "Mill",
        "Mills",
        "Mission",
        "Motorway",
        "Mount",
        "Mountain",
        "Mountains",
        "Neck",
        "Orchard",
        "Oval",
        "Overpass",
        "Park",
        "Parks",
        "Parkway",
        "Parkways",
        "Pass",
        "Passage",
        "Path",
        "Pike",
        "Pine",
        "Pines",
        "Place",
        "Plain",
        "Plains",
        "Plaza",
        "Point",
        "Points",
        "Port",
        "Ports",
        "Prairie",
        "Radial",
        "Ramp",
        "Ranch",
        "Rapid",
        "Rapids",
        "Rest",
        "Ridge",
        "Ridges",
        "River",
        "Road",
        "Roads",
        "Route",
        "Row",
        "Rue",
        "Run",
        "Shoal",
        "Shoals",
        "Shore",
        "Shores",
        "Skyway",
        "Spring",
        "Springs",
        "Spur",
        "Spurs",
        "Square",
        "Squares",
        "Station",
        "Stravenue",
        "Stream",
        "Street",
        "Streets",
        "Summit",
        "Terrace",
        "Throughway",
        "Trace",
        "Track",
        "Trafficway",
        "Trail",
        "Trailer",
        "Tunnel",
        "Turnpike",
        "Underpass",
        "Union",
        "Unions",
        "Valley",
        "Valleys",
        "Viaduct",
        "View",
        "Views",
        "Village",
        "Villages",
        "Ville",
        "Vista",
        "Walk",
        "Walks",
        "Wall",
        "Way",
        "Ways",
        "Well",
        "Wells",
    ]


# Address.StreetAddressDetail.Complex.StreetSuffixModifier
class StreetSuffixModifier(BSElement):
    """An extension or prefix for the street suffix."""

    element_type = "xs:string"


# Address.StreetAddressDetail.Complex.StreetDirSuffix
class StreetDirSuffix(BSElement):
    """The direction indicator that follows a street address."""

    element_type = "xs:string"
    element_enumerations = [
        "North",
        "Northeast",
        "East",
        "Southeast",
        "South",
        "Southwest",
        "West",
        "Northwest",
    ]


# Address.StreetAddressDetail.Complex.SubaddressType
class SubaddressType(BSElement):
    """The type of subaddress to which the associated Subaddress Identifier applies."""

    element_type = "xs:string"
    element_enumerations = [
        "Apartment",
        "Basement",
        "Berth",
        "Block",
        "Building",
        "Corridor",
        "Cubicle",
        "Department",
        "Floor",
        "Front",
        "Hanger",
        "Key",
        "Lobby",
        "Lot",
        "Lower",
        "Office",
        "Penthouse",
        "Pier",
        "PO Box",
        "Rear",
        "Room",
        "Seat",
        "Side",
        "Slip",
        "Space",
        "Stop",
        "Suite",
        "Terminal",
        "Tower",
        "Trailer",
        "Unit",
        "Upper",
        "Wing",
    ]


# Address.StreetAddressDetail.Complex.SubaddressIdentifier
class SubaddressIdentifier(BSElement):
    """The letters, numbers, words, or combination thereof used to distinguish different subaddresses of the same type when several occur within the same feature. For example, in subaddress "Building 4", the Subaddress Identifier = "4". Subaddress Identifier can also be parts of a building, for example "Penthouse" or "Mezzanine"."""

    element_type = "xs:string"


# Address.City
class City(BSElement):
    """The city for the Address Type."""

    element_type = "xs:string"


# Address.PostalCode
class PostalCode(BSElement):
    """The 5 digit postal code for the Address Type. Format: NNNNN"""

    element_type = "xs:string"


# Address.PostalCodePlus4
class PostalCodePlus4(BSElement):
    """The 4 digit add-on to the postal code in which the state is located. Format: NNNN"""

    element_type = "xs:string"


# Address.County
class County(BSElement):
    """The county for the Address Type."""

    element_type = "xs:string"


# Address.Country
class Country(BSElement):
    """Country of the Address."""

    element_type = "xs:string"


# IdentifierLabel
class IdentifierLabel(BSElement):
    """Identifier used in a specific program or dataset. There can be multiple instances of Identifier Types within a dataset, such as a Listing ID, a Tax Map Number ID, and a Custom ID."""

    element_type = "xs:string"
    element_enumerations = [
        "Premises",
        "Listing",
        "Name",
        "Portfolio Manager Property ID",
        "Portfolio Manager Standard",
        "Federal real property",
        "Tax book number",
        "Tax map number",
        "Assessor parcel number",
        "Tax parcel letter",
        "UBID",
        "Custom",
        "Other",
    ]


# IdentifierCustomName
class IdentifierCustomName(BSElement):
    """If "Custom" is used as an Identifier Type, this term can be used to specify the name of the Custom ID. This would be used to specify the name of the specific program that this identifier applies to, for example "Wisconsin Weatherization Program". It can also be used for the Portfolio Manager Standard IDs that are assigned to different Portfolio Manager programs, such as "NYC Building Identification Number (BIN)"."""

    element_type = "xs:string"


# IdentifierValue
class IdentifierValue(BSElement):
    """The identifying value associated with the Identifier Type. There can be many Identifier Types and Values associated with an individual premises."""

    element_type = "xs:string"


# OccupancyClassificationType
class OccupancyClassificationType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Manufactured home",
        "Single family",
        "Multifamily",
        "Multifamily with commercial",
        "Multifamily individual unit",
        "Public housing",
        "Residential",
        "Health care-Pharmacy",
        "Health care-Skilled nursing facility",
        "Health care-Residential treatment center",
        "Health care-Inpatient hospital",
        "Health care-Outpatient rehabilitation",
        "Health care-Diagnostic center",
        "Health care-Outpatient facility",
        "Health care-Outpatient non-diagnostic",
        "Health care-Outpatient surgical",
        "Health care-Veterinary",
        "Health care-Morgue or mortuary",
        "Health care",
        "Gas station",
        "Convenience store",
        "Food sales-Grocery store",
        "Food sales",
        "Laboratory-Testing",
        "Laboratory-Medical",
        "Laboratory",
        "Vivarium",
        "Zoo",
        "Office-Financial",
        "Office",
        "Bank",
        "Courthouse",
        "Public safety station-Fire",
        "Public safety station-Police",
        "Public safety station",
        "Public safety-Detention center",
        "Public safety-Correctional facility",
        "Public safety",
        "Warehouse-Refrigerated",
        "Warehouse-Unrefrigerated",
        "Warehouse-Self-storage",
        "Warehouse",
        "Assembly-Religious",
        "Assembly-Cultural entertainment",
        "Assembly-Social entertainment",
        "Assembly-Arcade or casino without lodging",
        "Assembly-Convention center",
        "Assembly-Indoor arena",
        "Assembly-Race track",
        "Assembly-Stadium",
        "Assembly-Stadium (closed)",
        "Assembly-Stadium (open)",
        "Assembly-Public",
        "Recreation-Pool",
        "Recreation-Bowling alley",
        "Recreation-Fitness center",
        "Recreation-Ice rink",
        "Recreation-Roller rink",
        "Recreation-Indoor sport",
        "Recreation",
        "Education-Adult",
        "Education-Higher",
        "Education-Secondary",
        "Education-Primary",
        "Education-Preschool or daycare",
        "Education-Vocational",
        "Education",
        "Food service-Fast",
        "Food service-Full",
        "Food service-Limited",
        "Food service-Institutional",
        "Food service",
        "Lodging-Barracks",
        "Lodging-Institutional",
        "Lodging with extended amenities",
        "Lodging with limited amenities",
        "Lodging",
        "Retail-Automobile dealership",
        "Retail-Mall",
        "Retail-Strip mall",
        "Retail-Enclosed mall",
        "Retail-Dry goods retail",
        "Retail-Hypermarket",
        "Retail",
        "Service-Postal",
        "Service-Repair",
        "Service-Laundry or dry cleaning",
        "Service-Studio",
        "Service-Beauty and health",
        "Service-Production and assembly",
        "Service",
        "Transportation terminal",
        "Central Plant",
        "Water treatment-Wastewater",
        "Water treatment-Drinking water and distribution",
        "Water treatment",
        "Energy generation plant",
        "Industrial manufacturing plant",
        "Utility",
        "Industrial",
        "Agricultural estate",
        "Mixed-use commercial",
        "Parking",
        "Attic",
        "Basement",
        "Dining area",
        "Living area",
        "Sleeping area",
        "Laundry area",
        "Lodging area",
        "Dressing area",
        "Restroom",
        "Auditorium",
        "Classroom",
        "Day room",
        "Sport play area",
        "Stage",
        "Spectator area",
        "Office work area",
        "Non-office work area",
        "Common area",
        "Reception area",
        "Waiting area",
        "Transportation waiting area",
        "Lobby",
        "Conference room",
        "Computer lab",
        "Data center",
        "Printing room",
        "Media center",
        "Telephone data entry",
        "Darkroom",
        "Courtroom",
        "Kitchen",
        "Kitchenette",
        "Refrigerated storage",
        "Bar-Nightclub",
        "Bar",
        "Dance floor",
        "Trading floor",
        "TV studio",
        "Security room",
        "Shipping and receiving",
        "Mechanical room",
        "Chemical storage room",
        "Non-chemical storage room",
        "Janitorial closet",
        "Vault",
        "Corridor",
        "Deck",
        "Courtyard",
        "Atrium",
        "Science park",
        "Other",
        "Unknown",
    ]


# TypicalOccupantUsages.TypicalOccupantUsage.TypicalOccupantUsageValue
class TypicalOccupantUsageValue(BSElement):
    element_type = "xs:decimal"


# TypicalOccupantUsages.TypicalOccupantUsage.TypicalOccupantUsageUnits
class TypicalOccupantUsageUnits(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Hours per day",
        "Hours per week",
        "Hours per month",
        "Hours per year",
        "Days per week",
        "Days per month",
        "Days per year",
        "Weeks per month",
        "Weeks per year",
        "Months per year",
    ]


# UserDefinedFields.UserDefinedField.FieldName
class FieldName(BSElement):
    element_type = "xs:string"


# UserDefinedFields.UserDefinedField.FieldValue
class FieldValue(BSElement):
    element_type = "xs:string"


# TenantIDs.TenantID
class TenantID(BSElement):
    """Tenant ID number for the premises."""


TenantID.element_attributes = [
    "IDref",  # IDREF
]

# FloorAreas.FloorArea.ExcludedSectionIDs.ExcludedSectionID
class ExcludedSectionID(BSElement):
    pass


ExcludedSectionID.element_attributes = [
    "IDref",  # IDREF
]

# FloorAreas.FloorArea.FloorAreaType
class FloorAreaType(BSElement):
    """Floor area can be defined and described in many different ways for different purposes. This type field allows multiple types of floor area definitions to exist in the same dataset."""

    element_type = "xs:string"
    element_enumerations = [
        "Tenant",
        "Common",
        "Gross",
        "Net",
        "Finished",
        "Footprint",
        "Rentable",
        "Occupied",
        "Lighted",
        "Daylit",
        "Heated",
        "Cooled",
        "Conditioned",
        "Unconditioned",
        "Semi-conditioned",
        "Heated and Cooled",
        "Heated only",
        "Cooled only",
        "Ventilated",
        "Enclosed",
        "Non-Enclosed",
        "Open",
        "Lot",
        "Custom",
    ]


# FloorAreas.FloorArea.FloorAreaCustomName
class FloorAreaCustomName(BSElement):
    """If "Custom" is used as the Floor Area Type, this term can be used to name and identify the custom floor area."""

    element_type = "xs:string"


# FloorAreas.FloorArea.FloorAreaValue
class FloorAreaValue(BSElement):
    """The floor area numeric value. (ft2)"""

    element_type = "xs:decimal"


# FloorAreas.FloorArea.FloorAreaPercentage
class FloorAreaPercentage(BSElement):
    """The percentage of floor area that belongs to a FloorAreaType. (0-100) (%)"""

    element_type = "xs:float"


# OccupancyLevels.OccupancyLevel.OccupantType
class OccupantType(BSElement):
    """Type of occupants who are permanently resident in a premises."""

    element_type = "xs:string"
    element_enumerations = [
        "Family household",
        "Married couple, no children",
        "Male householder, no spouse",
        "Female householder, no spouse",
        "Cooperative household",
        "Nonfamily household",
        "Single male",
        "Single female",
        "Student community",
        "Military community",
        "Independent seniors community",
        "Special accessibility needs community",
        "Government subsidized community",
        "Therapeutic community",
        "No specific occupant type",
        "For-profit organization",
        "Religious organization",
        "Non-profit organization",
        "Government organization",
        "Federal government",
        "State government",
        "Local government",
        "Property",
        "Animals",
        "Other",
        "Vacant",
        "Unknown",
    ]


# OccupancyLevels.OccupancyLevel.OccupantQuantityType
class OccupantQuantityType(BSElement):
    """Type of quantitative measure for capturing occupant information about the premises. The value is captured by the Occupant Quantity term."""

    element_type = "xs:string"
    element_enumerations = [
        "Peak total occupants",
        "Adults",
        "Children",
        "Average residents",
        "Workers on main shift",
        "Full-time equivalent workers",
        "Average daily salaried labor hours",
        "Registered students",
        "Staffed beds",
        "Licensed beds",
        "Capacity",
        "Capacity percentage",
        "Normal occupancy",
    ]


# OccupancyLevels.OccupancyLevel.OccupantQuantity
class OccupantQuantity(BSElement):
    """The value associated with the Occupant Quantity Type term."""

    element_type = "xs:decimal"


# AssetScoreData.Score
class Score(BSElement):
    """An individual use type's Asset Score within a commercial building."""

    element_type = "xs:decimal"


# AssetScore.WholeBuilding.Rankings.Ranking.Type.SystemsType
class SystemsType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Cooling",
        "Heating",
        "Hot Water",
        "Interior Lighting",
        "Overall HVAC Systems",
    ]


# AssetScore.WholeBuilding.Rankings.Ranking.Type.EnvelopeType
class EnvelopeType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Floor U-Value, Mass",
        "Roof U-Value, Non-Attic",
        "Walls U-Value, Framed",
        "Walls + Windows U-Value",
        "Window Solar Heat Gain Coefficient",
        "Windows U-Value",
    ]


# RankType
class RankType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Fair", "Good", "Superior"]


# AssetScore.UseTypes.UseType.AssetScoreUseType
class AssetScoreUseType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Assisted Living Facility",
        "City Hall",
        "Community Center",
        "Courthouse",
        "Education",
        "Library",
        "Lodging",
        "Medical Office",
        "Multi-family (4 floors or greater)",
        "Multi-family (fewer than 4 floors)",
        "Office",
        "Parking Garage (Ventilation Only)",
        "Police Station",
        "Post Office",
        "Religious Building",
        "Retail",
        "Senior Center",
        "Warehouse non-refrigerated",
    ]


# PortfolioManagerType.PMBenchmarkDate
class PMBenchmarkDate(BSElement):
    """Date that the building was benchmarked in ENERGY STAR Portfolio Manager. (CCYY-MM-DD)"""

    element_type = "xs:date"


# PortfolioManagerType.BuildingProfileStatus
class BuildingProfileStatus(BSElement):
    """The status of the building profile submission process for ENERGY STAR Portfolio Manager."""

    element_type = "xs:string"
    element_enumerations = [
        "Draft",
        "Received",
        "Under Review",
        "On Hold",
        "Reviewed and Approved",
        "Reviewed and Not Approved",
    ]


# PortfolioManagerType.FederalSustainabilityChecklistCompletionPercentage
class FederalSustainabilityChecklistCompletionPercentage(BSElement):
    """Percentage of the Federal High Performance Sustainability Checklist that has been completed for federal building in ENERGY STAR Portfolio Manager. (0-100) (%)"""

    element_type = "xs:decimal"


# FanBasedDistributionTypeType.FanCoil.FanCoilType
class FanCoilType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Mini-split",
        "Multi-split",
        "Terminal reheat",
        "Fan coil 2 pipe",
        "Fan coil 4 pipe",
        "VRF terminal units",
        "Other",
        "Unknown",
    ]


# FanBasedDistributionTypeType.FanCoil.HVACPipeConfiguration
class HVACPipeConfiguration(BSElement):
    """Number of pipes for distributing steam, refrigerant, or water to individual zones."""

    element_type = "xs:string"
    element_enumerations = ["1 pipe", "2 pipe", "3 pipe", "4 pipe", "Other", "Unknown"]


# FanBasedType.HeatingSupplyAirTemperatureControl
class HeatingSupplyAirTemperatureControl(BSElement):
    """Defines the control method for heating supply air temperature."""

    element_type = "xs:string"
    element_enumerations = [
        "Coldest Reset",
        "Fixed",
        "Outside Air Reset",
        "Scheduled",
        "Staged Setpoint",
        "Other",
        "Unknown",
    ]


# FanBasedType.CoolingSupplyAirTemperature
class CoolingSupplyAirTemperature(BSElement):
    """Temperature setting of supply air for cooling under normal conditions. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.CoolingSupplyAirTemperatureControlType
class CoolingSupplyAirTemperatureControlType(BSElement):
    """Defines the control method for controlling cooling supply air temperature."""

    element_type = "xs:string"
    element_enumerations = [
        "Fixed",
        "Outside Air Reset",
        "Scheduled",
        "Warmest Reset",
        "Other",
        "Unknown",
    ]


# FanBasedType.OutsideAirResetMaximumHeatingSupplyTemperature
class OutsideAirResetMaximumHeatingSupplyTemperature(BSElement):
    """Maximum temperature setting of supply air for heating during outside air reset. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.OutsideAirResetMinimumHeatingSupplyTemperature
class OutsideAirResetMinimumHeatingSupplyTemperature(BSElement):
    """Minimum temperature setting of supply air for heating during outside air reset. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.OutsideAirTemperatureUpperLimitHeatingResetControl
class OutsideAirTemperatureUpperLimitHeatingResetControl(BSElement):
    """Maximum outside air temperature where supply air temperature is reset for heating. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.OutsideAirTemperatureLowerLimitHeatingResetControl
class OutsideAirTemperatureLowerLimitHeatingResetControl(BSElement):
    """Minimum outside air temperature where supply air temperature is reset for heating. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.OutsideAirResetMaximumCoolingSupplyTemperature
class OutsideAirResetMaximumCoolingSupplyTemperature(BSElement):
    """Maximum temperature setting of supply air for cooling during outside air reset. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.OutsideAirResetMinimumCoolingSupplyTemperature
class OutsideAirResetMinimumCoolingSupplyTemperature(BSElement):
    """Minimum temperature setting of supply air for cooling during outside air reset. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.OutsideAirTemperatureUpperLimitCoolingResetControl
class OutsideAirTemperatureUpperLimitCoolingResetControl(BSElement):
    """Maximum outside air temperature where supply air temperature is reset for cooling. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.OutsideAirTemperatureLowerLimitCoolingResetControl
class OutsideAirTemperatureLowerLimitCoolingResetControl(BSElement):
    """Minimum outside air temperature where supply air temperature is reset for cooling. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.HeatingSupplyAirTemperature
class HeatingSupplyAirTemperature(BSElement):
    """Temperature setting of supply air for heating or cooling. (°F)"""

    element_type = "xs:decimal"


# FanBasedType.SupplyAirTemperatureResetControl
class SupplyAirTemperatureResetControl(BSElement):
    """True if the supply-air-temperature set point can be reset based on the outside air temperature, false otherwise."""

    element_type = "xs:boolean"


# FanBasedType.StaticPressureResetControl
class StaticPressureResetControl(BSElement):
    """True if duct static pressure can be reset to keep it only as high as is needed to satisfy the neediest zone, false otherwise."""

    element_type = "xs:boolean"


# FanBasedType.AirSideEconomizer.AirSideEconomizerType
class AirSideEconomizerType(BSElement):
    """Type of air economizer system associated with a cooling system."""

    element_type = "xs:string"
    element_enumerations = [
        "Dry bulb temperature",
        "Enthalpy",
        "Demand controlled ventilation",
        "Nonintegrated",
        "None",
        "Other",
        "Unknown",
    ]


# FanBasedType.AirSideEconomizer.EconomizerControl
class EconomizerControl(BSElement):
    """Logic used for economizer control."""

    element_type = "xs:string"
    element_enumerations = ["Fixed", "Differential", "Other", "Unknown"]


# FanBasedType.AirSideEconomizer.EconomizerDryBulbControlPoint
class EconomizerDryBulbControlPoint(BSElement):
    """Dry bulb temperature setting for use of economizer for cooling (fixed or differential). (°F)"""

    element_type = "xs:decimal"


# FanBasedType.AirSideEconomizer.EconomizerEnthalpyControlPoint
class EconomizerEnthalpyControlPoint(BSElement):
    """Maximum enthalpy setting for use of economizer for cooling (fixed or differential). (Btu/lb)"""

    element_type = "xs:decimal"


# FanBasedType.AirSideEconomizer.EconomizerLowTemperatureLockout
class EconomizerLowTemperatureLockout(BSElement):
    """The outside air temperature below which the economizer will return to the minimum position. (°F)"""

    element_type = "xs:decimal"


# ControlStrategyGeneralType
class ControlStrategyGeneralType(BSElement):
    """Enumerations for general control strategies."""

    element_type = "xs:string"
    element_enumerations = [
        "Always On",
        "Aquastat",
        "Astronomical",
        "Chronological",
        "EMCS",
        "Demand",
        "Manual",
        "Programmable",
        "Timer",
        "Other",
        "Unknown",
        "None",
    ]


# ControlSensorOccupancyType
class ControlSensorOccupancyType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Passive infrared",
        "Ultrasonic",
        "Passive infrared and ultrasonic",
        "Microwave",
        "Camera",
        "Other",
        "Unknown",
    ]


# ControlStrategyOccupancyType
class ControlStrategyOccupancyType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Occupancy Sensors",
        "Vacancy Sensors",
        "Other",
        "None",
        "Unknown",
    ]


# ControlStrategyLightingType
class ControlStrategyLightingType(BSElement):
    """Enumerations for lighting control strategies."""

    element_type = "xs:string"
    element_enumerations = [
        "Advanced",
        "Always On",
        "Astronomical",
        "Chronological",
        "Demand",
        "EMCS",
        "Manual",
        "Programmable",
        "Timer",
        "Other",
        "Unknown",
        "None",
    ]


# ControlSensorDaylightingType
class ControlSensorDaylightingType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Camera", "Photocell", "Other", "Unknown"]


# ControlStrategyDaylightingType
class ControlStrategyDaylightingType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Continuous",
        "Continuous Plus Off",
        "Stepped Dimming",
        "Stepped Switching",
        "Other",
        "None",
        "Unknown",
    ]


# ControlLightingType.Daylighting.ControlSteps
class ControlSteps(BSElement):
    """For stepped dimming, the number of equally spaced control steps."""

    element_type = "xs:integer"


# CommunicationProtocolAnalogType
class CommunicationProtocolAnalogType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "AMX192",
        "Current",
        "D54",
        "Voltage",
        "Other",
        "Unknown",
        "None",
    ]


# CommunicationProtocolDigitalType
class CommunicationProtocolDigitalType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "BACnet",
        "DALI",
        "DMX512",
        "DSI ",
        "EnOcean",
        "KMX",
        "Konnex",
        "LonTalk",
        "MODBUS",
        "PROFIBUS FMS",
        "X10",
        "ZigBee",
        "Other",
        "Unknown",
        "None",
    ]


# ControlSystemType.Other.OtherCommunicationProtocolName
class OtherCommunicationProtocolName(BSElement):
    """Name of the other communication protocal that is being used to communicate data over a computer network."""

    element_type = "xs:string"


# ControlSystemType.Pneumatic
class Pneumatic(BSElement):
    """Pneumatic-based controls."""


# BoundedDecimalZeroToOne
class BoundedDecimalZeroToOne(BSElement):
    element_type = "xs:decimal"


# WallID.WallArea
class WallArea(BSElement):
    """Exposed, above-grade, opaque wall area of this type. (ft2)"""

    element_type = "xs:decimal"


# WindowID.PercentOfWindowAreaShaded
class PercentOfWindowAreaShaded(BSElement):
    """The percentage of the fenestration area that is shaded by exterior objects such as trees or other buildings. (0-100) (%)"""

    element_type = "xs:decimal"


# DerivedModelType.DerivedModelName
class DerivedModelName(BSElement):
    element_type = "xs:string"


# DerivedModelType.MeasuredScenarioID
class MeasuredScenarioID(BSElement):
    pass


MeasuredScenarioID.element_attributes = [
    "IDref",  # IDREF
]

# IntervalFrequencyType
class IntervalFrequencyType(BSElement):
    """Indicates frequency of data that's available for a given variable. Data that's available can range from 1 minute interval to annual. This interval frequency can be applied to resource or other time series data like weather."""

    element_type = "xs:string"
    element_enumerations = [
        "1 minute",
        "10 minute",
        "15 minute",
        "30 minute",
        "Hour",
        "Day",
        "Week",
        "Month",
        "Annual",
        "Quarter",
        "Other",
        "Unknown",
    ]


# DerivedModelType.Models.Model.DerivedModelInputs.ResponseVariable.ResponseVariableName
class ResponseVariableName(FuelTypes):
    pass


# DerivedModelType.Models.Model.DerivedModelInputs.ResponseVariable.ResponseVariableEndUse
class ResponseVariableEndUse(EndUse):
    pass


# DerivedModelType.Models.Model.DerivedModelInputs.ExplanatoryVariables.ExplanatoryVariable.ExplanatoryVariableName
class ExplanatoryVariableName(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Drybulb Temperature",
        "Wetbulb Temperature",
        "Relative Humidity",
        "Global Horizontal Irradiance (GHI)",
        "Diffuse Horizontal Irradiance (DHI)",
        "Direct Normal Irradiance (DNI)",
        "Hour of week",
        "Hour of day",
        "Day of week",
        "Day of month",
        "Day of year",
        "Week of year",
        "Month of year",
        "Fifteen minute interval of week",
        "Fifteen minute interval of day",
        "Season",
        "Weekday / Weekend",
        "Holiday",
        "Other",
    ]


# DerivedModelType.Models.Model.DerivedModelCoefficients.Guideline14Model.ModelType
class ModelType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "2 parameter simple linear regression",
        "3 parameter heating change point model",
        "3 parameter cooling change point model",
        "4 parameter change point model",
        "5 parameter change point model",
    ]


# DerivedModelType.Models.Model.DerivedModelCoefficients.Guideline14Model.Intercept
class Intercept(BSElement):
    """The 'y-intercept' value.  In Figure D-1 (a), this is Eb.  In Figure D-1 (a)-(g), this is C."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelCoefficients.Guideline14Model.Beta1
class Beta1(BSElement):
    """In a two and three parameter model, this is the slope of the line (Figure D-1 (a)-(d)).  If the model type is a 3p heating model, this is referred to as beta_hdd, whereas for a 3p cooling model, this is referred to as beta_cdd (per CalTRACK terminology).  In the 4p and 5p models, this is beta_hdd."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelCoefficients.Guideline14Model.Beta2
class Beta2(BSElement):
    """In both three parameter models, this is the change point.  In the 4p and 5p models, this is beta_cdd."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelCoefficients.Guideline14Model.Beta3
class Beta3(BSElement):
    """In the 4p models, this is the change point (as there is only one change point).  In the 5p models, this is the lower value change point, which in CalTRACK terms is referred to as the heating change point."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelCoefficients.Guideline14Model.Beta4
class Beta4(BSElement):
    """In the 5p model, this is the upper value change point, which in CalTRACK terms is referred to as the cooling change point."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelCoefficients.TimeOfWeekTemperatureModel
class TimeOfWeekTemperatureModel(BSElement):
    pass


# DerivedModelType.Models.Model.DerivedModelPerformance.RSquared
class RSquared(BSElement):
    """Also referred to as the coefficient of determination, R-Squared is a measure of the extent to which variations in the dependent variable from its mean value are explained by the regression model (ASHRAE Guideline 14-2014). Specifics for the calculation can be found in Guideline 14, or calculated as: R-Squared = 1 - (SS_resid / SS_total). Here, SS_resid is the sum of the squared residuals from the regression, and SS_total is the sum of the squared differences from the mean of the dependent variable (total sum of squares). See: https://www.mathworks.com/help/matlab/data_analysis/linear-regression.html#f1-15010."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelPerformance.AdjustedRSquared
class AdjustedRSquared(BSElement):
    """Adjusted R-Squared is typically used to compare model fits across models generated with different numbers of parameters, since R-Squared is unable to account for model complexity (i.e. quadratic, cubic, etc.). It uses a penalty for the number of terms in a model, and can be calculated as: Adj-R-Squared = 1 - (SS_resid / SS_total) * ((n - 1) / (n - d - 1)). Here, SS_resid is the sum of the squared residuals from the regression, and SS_total is the sum of the squared differences from the mean of the dependent variable (total sum of squares). n is the number of observations in the data, and d is the degree of the polynomial. See: https://www.mathworks.com/help/matlab/data_analysis/linear-regression.html#f1-15010."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelPerformance.RMSE
class RMSE(BSElement):
    """The Root Mean Square Error (RMSE) is the standard deviation of the residuals. It is calculated as follows: RMSE = sqrt( sum((y_i - yhat_i)^2) / (n - p) ). Here, y_i is the ith observation of the dependent variable, yhat_i is the regression models predicted value of y_i, n is the number of data points or periods in the baseline period, and p is the number of parameters or terms in the baseline model (ASHRAE Guideline 14-2014)."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelPerformance.CVRMSE
class CVRMSE(BSElement):
    """The Coefficient of Variation of the Root Mean Square Error expressed as a percentage."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelPerformance.NDBE
class NDBE(BSElement):
    """The Net Determination Bias Error expressed as a percentage."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelPerformance.MBE
class MBE(BSElement):
    """The Mean Bias Error."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.DerivedModelPerformance.NMBE
class NMBE(BSElement):
    """The Normalized Mean Bias Error expressed as a percentage."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.SummaryInformation.NumberOfDataPoints
class NumberOfDataPoints(BSElement):
    """As documented in Annex B4 of ASRHAE Guideline 14-2018, this refers to the total number of periods in the Baseline period data.  It is denoted as "n" throughout B4.  A "period" refers to a measurement of the ResponseVariable.  For example, 24 hours worth of data collected at hourly intervals would have 24 "periods"."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.SummaryInformation.NumberOfParameters
class NumberOfParameters(BSElement):
    """As documented in Annex B4 of ASRHAE Guideline 14-2018, this refers to the total number of parameters in the model.  It is denoted as "p" throughout B4.  The number of parameters is not necessarily equal to the number of auc:ExplanatoryVariable elements.  For example, a 5 parameter change point model has 5 parameters, even though there is only a single ExplanatoryVariable (likely Drybulb Temperature).  In certain cases, this is used in the calculation of the degrees of freedom for the t-statistic."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.SummaryInformation.DegreesOfFreedom
class DegreesOfFreedom(BSElement):
    """Degrees of Freedom as used in the context of a t-distribution."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.SummaryInformation.AggregateActualEnergyUse
class AggregateActualEnergyUse(BSElement):
    """This value represents the actual energy use for the building / premise over the defined period. It is an aggregate number and should be of the same units defined by the ResponseVariable/ResponseVariableUnits. See: the Retrofit Isolation Approach (G-14 4.1.1) and Whole Facility Approach (G-14 4.1.2) of ASHRAE Guideline 14-2018."""

    element_type = "xs:decimal"


# DerivedModelType.Models.Model.SummaryInformation.AggregateModeledEnergyUse
class AggregateModeledEnergyUse(BSElement):
    """This value represents the model estimated energy use for the building / premise over the defined period. It is an aggregate number and should be of the same units defined by the ResponseVariable/ResponseVariableUnits."""

    element_type = "xs:decimal"


# DerivedModelType.SavingsSummaries.SavingsSummary.ConfidenceLevel
class ConfidenceLevel(BoundedDecimalZeroToOne):
    """The confidence level represented as a decimal between zero and one."""


# DerivedModelType.SavingsSummaries.SavingsSummary.BaselinePeriodModelID
class BaselinePeriodModelID(BSElement):
    """Applicable when the NormalizationMethod is Forecast or Standard Conditions. Define a link to the ID of the Model considered as the baseline period Model. In the event it is Forecast, the reporting period and comparison period are considered synonymous."""


BaselinePeriodModelID.element_attributes = [
    "IDref",  # IDREF
]

# DerivedModelType.SavingsSummaries.SavingsSummary.ReportingPeriodModelID
class ReportingPeriodModelID(BSElement):
    """Applicable when the NormalizationMethod is Backcast or Standard Conditions. Define a link to the ID of the Model considered as the reporting period Model. In the event it is Backcast, the baseline period and comparison period are considered synonymous."""


ReportingPeriodModelID.element_attributes = [
    "IDref",  # IDREF
]

# DerivedModelType.SavingsSummaries.SavingsSummary.NormalizationMethod
class NormalizationMethod(BSElement):
    """'Forecast' is the most common normalization method. It implies creation of a single Model using data from a baseline period (i.e. preconditions). 'Standard Conditions' is used to compare building performance of, say, two particular years to a 'typical' year. In this event, two models are created, one for the baseline and one for the reporting period, and input data is fed into each for a 'typical year' (TMY3, etc.) and performance compared.  'Backcast' is not used often, but makes sense in the event that finer temporal data is available in the reporting period to train the Model. A single Model is also created in this case."""

    element_type = "xs:string"
    element_enumerations = ["Forecast", "Backcast", "Standard Conditions"]


# DerivedModelType.SavingsSummaries.SavingsSummary.ComparisonPeriodStartTimestamp
class ComparisonPeriodStartTimestamp(BSElement):
    """Applicable regardless of the NormalizationMethod. The beginning of the time period used for comparison."""

    element_type = "xs:dateTime"


# DerivedModelType.SavingsSummaries.SavingsSummary.ComparisonPeriodEndTimestamp
class ComparisonPeriodEndTimestamp(BSElement):
    """Applicable regardless of the NormalizationMethod. The end of the time period used for comparison."""

    element_type = "xs:dateTime"


# DerivedModelType.SavingsSummaries.SavingsSummary.ComparisonPeriodAggregateActualEnergyUse
class ComparisonPeriodAggregateActualEnergyUse(BSElement):
    """Applicable when the NormalizationMethod is Forecast or Backcast. This value represents the actual energy use for the building / premise during the period of comparison. It is an aggregate number and should be of the same units defined by the ResponseVariable/ResponseVariableUnits."""

    element_type = "xs:decimal"


# DerivedModelType.SavingsSummaries.SavingsSummary.ComparisonPeriodAggregateModeledEnergyUse
class ComparisonPeriodAggregateModeledEnergyUse(BSElement):
    """Applicable when the NormalizationMethod is Forecast or Backcast. This value represents the model estimated energy use for the building / premise during the period of comparison. It is an aggregate number and should be of the same units defined by the ResponseVariable/ResponseVariableUnits."""

    element_type = "xs:decimal"


# DerivedModelType.SavingsSummaries.SavingsSummary.AvoidedEnergyUse
class AvoidedEnergyUse(BSElement):
    """Applicable when the NormalizationMethod is Forecast or Backcast. As documented in Annex B4.1g and the result of Equation B-14 of ASHRAE Guideline 14-2018 (E_save,m), this value represents the 'actual savings'.  It is calculated via the following: E_save,m = Ehat_base,m - E_meas,m.  In BuildingSync terms, the AvoidedEnergyUse = ComparisonPeriodAggregateModeledEnergyUse - ComparisonPeriodAggregateActualEnergyUse."""

    element_type = "xs:decimal"


# DerivedModelType.SavingsSummaries.SavingsSummary.SavingsUncertainty
class SavingsUncertainty(BSElement):
    """The savings uncertainty represented as a decimal."""

    element_type = "xs:decimal"


# DerivedModelType.SavingsSummaries.SavingsSummary.StandardConditionsBaselinePeriodAggregateModeledEnergyUse
class StandardConditionsBaselinePeriodAggregateModeledEnergyUse(BSElement):
    """Applicable when the NormalizationMethod is Standard Conditions.  As documented in Annex B4.5 of ASRHAE Guideline 14-2018: "In many cases, it is necessary to normalize the savings to a typical or average period (usually a year) at the site. It was shown in Section B4.3 that when measurement errors are negligible, the uncertainty in calculating actual savings using a weather-based regression is due to the error in normalizing the baseline energy use to the postretrofit period. Normalized savings requires two regression equations: one that correlates baseline energy use with baseline weather conditions and one that correlates postretrofit energy use with postretrofit weather conditions.  This value represents the "normalized baseline energy use", or the predicted energy consumption using the Baseline model when data from a standard year (or typical year) is supplied to it."""

    element_type = "xs:decimal"


# DerivedModelType.SavingsSummaries.SavingsSummary.StandardConditionsReportingPeriodAggregateModeledEnergyUse
class StandardConditionsReportingPeriodAggregateModeledEnergyUse(BSElement):
    """Applicable when the NormalizationMethod is Standard Conditions.  As documented in Annex B4.5 of ASRHAE Guideline 14-2018: "In many cases, it is necessary to normalize the savings to a typical or average period (usually a year) at the site. It was shown in Section B4.3 that when measurement errors are negligible, the uncertainty in calculating actual savings using a weather-based regression is due to the error in normalizing the baseline energy use to the postretrofit period. Normalized savings requires two regression equations: one that correlates baseline energy use with baseline weather conditions and one that correlates postretrofit energy use with postretrofit weather conditions.  This value represents the "normalized postretrofit energy use", or the predicted energy consumption using the Reporting (or postretrofit) model when data from a standard year (or typical year) is supplied to it."""

    element_type = "xs:decimal"


# DerivedModelType.SavingsSummaries.SavingsSummary.StandardConditionsAvoidedEnergyUse
class StandardConditionsAvoidedEnergyUse(BSElement):
    """Applicable when the NormalizationMethod is Standard Conditions. As documented in Annex B4.5 of ASRHAE Guideline 14-2018: "normalized savings is then defined as the normalized baseline energy use minus the normalized postretrofit energy use".  The "normalized baseline energy use" referred to in G-14 is captured by the auc:BaselinePeriodCalculatedEnergyUseStandardConditions element, while the "normalized postretrofit energy use" is captured by the auc:ReportingPeriodCalculatedEnergyUseStandardConditions element."""

    element_type = "xs:decimal"


# OtherUnitsType
class OtherUnitsType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Other", "Unknown", "None"]


# DimensionlessUnitsBaseType
class DimensionlessUnitsBaseType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Percent, %", "Percent Relative Humidity, %RH"]


# PeakResourceUnitsBaseType
class PeakResourceUnitsBaseType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["kW", "MMBtu/day"]


# PressureUnitsBaseType
class PressureUnitsBaseType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Bar", "Atmosphere, atm", "Pounds per Square Inch, psi"]


# ResourceUnitsBaseType
class ResourceUnitsBaseType(BSElement):
    element_type = "xs:string"
    element_enumerations = [
        "Cubic Meters",
        "kcf",
        "MCF",
        "Gallons",
        "Wh",
        "kWh",
        "MWh",
        "Btu",
        "kBtu",
        "MMBtu",
        "therms",
        "lbs",
        "Klbs",
        "Mlbs",
        "Mass ton",
        "Ton-hour",
    ]


# TemperatureUnitsBaseType
class TemperatureUnitsBaseType(BSElement):
    element_type = "xs:string"
    element_enumerations = ["Fahrenheit, F"]


# WeatherDataStationID
class WeatherDataStationID(BSElement):
    """For an actual weather station, this is the ID assigned by National Oceanic and Atmospheric Administration (NOAA). For hourly energy simulations, this is the six digit code associated with the hourly weather data, generally found in the name of the weather data file, as well as in the header of the data file. (NNNNNN) WARNING: This element is being deprecated, use WeatherStations/WeatherStation/WeatherDataStationID instead"""

    element_type = "xs:string"


# WeatherStationName
class WeatherStationName(BSElement):
    """The name of the weather station associated with this premises, which could be used for simulations, weather normalization, anomaly resolution, etc. For simulations, this is usually the name of the weather file, but the name is also in the header of the data file (TMY, IWEC), such as USA_CO_Denver.Intl.AP. WARNING: This element is being deprecated, use WeatherStations/WeatherStation/WeatherStationName instead"""

    element_type = "xs:string"


# WeatherStationCategory
class WeatherStationCategory(BSElement):
    """Describes the type of weather station used to specify the site's weather. WARNING: This element is being deprecated, use WeatherStations/WeatherStation/WeatherStationCategory instead"""

    element_type = "xs:string"
    element_enumerations = ["FAA", "ICAO", "NWS", "WBAN", "WMO", "Other"]


# BuildingSync.Programs.Program
class Program(BSElement):
    """Authorized or supported program such as rebate or audit."""


Program.element_children = [
    ("ProgramDate", ProgramDate),
    ("ProgramFundingSource", ProgramFundingSource),
    ("ProgramClassification", ProgramClassification),
]

# BuildingSync.Programs
class Programs(BSElement):
    pass


Programs.element_children = [
    ("Program", Program),
]

# BuildingSync.Facilities.Facility.Systems.WaterInfiltrationSystems.WaterInfiltrationSystem.LocationsOfExteriorWaterIntrusionDamages
class LocationsOfExteriorWaterIntrusionDamages(BSElement):
    pass


LocationsOfExteriorWaterIntrusionDamages.element_children = [
    (
        "LocationsOfExteriorWaterIntrusionDamage",
        LocationsOfExteriorWaterIntrusionDamage,
    ),
]

# BuildingSync.Facilities.Facility.Systems.WaterInfiltrationSystems.WaterInfiltrationSystem.LocationsOfInteriorWaterIntrusionDamages
class LocationsOfInteriorWaterIntrusionDamages(BSElement):
    pass


LocationsOfInteriorWaterIntrusionDamages.element_children = [
    (
        "LocationsOfInteriorWaterIntrusionDamage",
        LocationsOfInteriorWaterIntrusionDamage,
    ),
]

# OccupancyClassification
class OccupancyClassification(OccupancyClassificationType):
    """Classification of the space (complex, whole building, or section) tasks by building occupants."""


# TenantIDs
class TenantIDs(BSElement):
    pass


TenantIDs.element_children = [
    ("TenantID", TenantID),
]

# BuildingType.FederalBuilding
class FederalBuilding(BSElement):
    """If exists then the building is owned by the federal government."""


FederalBuilding.element_children = [
    ("Agency", Agency),
    ("DepartmentRegion", DepartmentRegion),
]

# BuildingType.SpatialUnits.SpatialUnit
class SpatialUnit(BSElement):
    pass


SpatialUnit.element_children = [
    ("SpatialUnitType", SpatialUnitType),
    ("NumberOfUnits", NumberOfUnits),
    ("UnitDensity", UnitDensity),
    ("SpatialUnitOccupiedPercentage", SpatialUnitOccupiedPercentage),
]

# PortfolioManagerType
class PortfolioManagerType(BSElement):
    pass


PortfolioManagerType.element_children = [
    ("PMBenchmarkDate", PMBenchmarkDate),
    ("BuildingProfileStatus", BuildingProfileStatus),
    (
        "FederalSustainabilityChecklistCompletionPercentage",
        FederalSustainabilityChecklistCompletionPercentage,
    ),
]

# BoundedDecimalZeroToOneWithSourceAttribute
class BoundedDecimalZeroToOneWithSourceAttribute(BoundedDecimalZeroToOne):
    pass


# BuildingType.Assessments.Assessment
class Assessment(BSElement):
    pass


Assessment.element_children = [
    ("AssessmentProgram", AssessmentProgram),
    ("AssessmentLevel", AssessmentLevel),
    ("AssessmentValue", AssessmentValue),
    ("AssessmentYear", AssessmentYear),
    ("AssessmentVersion", AssessmentVersion),
]

# BuildingType.Sections.Section.Sides.Side
class Side(BSElement):
    class ThermalZoneIDs(BSElement):
        """List of thermal zone IDs."""

        class ThermalZoneID(BSElement):
            """ID number of the zone type associated with this space or side of the section."""


Side.element_children = [
    ("SideNumber", SideNumber),
    ("SideLength", SideLength),
    ("ThermalZoneIDs", Side.ThermalZoneIDs),
]
Side.ThermalZoneIDs.element_children = [
    ("ThermalZoneID", Side.ThermalZoneIDs.ThermalZoneID),
]
Side.ThermalZoneIDs.ThermalZoneID.element_attributes = [
    "IDref",  # IDREF
]

# BuildingType.Sections.Section.Sides
class Sides(BSElement):
    """List of sides."""


Sides.element_children = [
    ("Side", Side),
]

# BuildingType.Sections.Section.Roofs.Roof.RoofID.RoofCondition
class RoofCondition(EquipmentCondition):
    """Description of the roof's condition."""


# BuildingType.Sections.Section.Roofs.Roof.RoofID.SkylightIDs.SkylightID
class SkylightID(BSElement):
    """ID number of the skylight type associated with this side of the section."""


SkylightID.element_attributes = [
    "IDref",  # IDREF
]
SkylightID.element_children = [
    ("PercentSkylightArea", PercentSkylightArea),
]

# BuildingType.Sections.Section.Roofs.Roof.RoofID.SkylightIDs
class SkylightIDs(BSElement):
    """List of Skylight IDs."""


SkylightIDs.element_children = [
    ("SkylightID", SkylightID),
]

# BuildingType.Sections.Section.Roofs.Roof.RoofID
class RoofID(BSElement):
    """ID number of the roof type associated with this section."""


RoofID.element_attributes = [
    "IDref",  # IDREF
]
RoofID.element_children = [
    ("RoofArea", RoofArea),
    ("RoofInsulatedArea", RoofInsulatedArea),
    ("RoofCondition", RoofCondition),
    ("SkylightIDs", SkylightIDs),
]

# BuildingType.Sections.Section.Roofs.Roof
class Roof(BSElement):
    """A roof structure that forms the exterior upper covering of a premises."""


Roof.element_children = [
    ("RoofID", RoofID),
]

# BuildingType.Sections.Section.Roofs
class Roofs(BSElement):
    """List of roofs."""


Roofs.element_children = [
    ("Roof", Roof),
]

# BuildingType.Sections.Section.Ceilings.Ceiling.CeilingID
class CeilingID(BSElement):
    """ID number of the roof/ceiling type associated with this section."""

    class ThermalZoneIDs(BSElement):
        class ThermalZoneID(BSElement):
            """ID number of the zone type associated with this space or side of the section."""

    class SpaceIDs(BSElement):
        class SpaceID(BSElement):
            """ID number of the space type associated with this side of the section."""


CeilingID.element_attributes = [
    "IDref",  # IDREF
]
CeilingID.element_children = [
    ("CeilingArea", CeilingArea),
    ("CeilingInsulatedArea", CeilingInsulatedArea),
    ("ThermalZoneIDs", CeilingID.ThermalZoneIDs),
    ("SpaceIDs", CeilingID.SpaceIDs),
]
CeilingID.ThermalZoneIDs.element_children = [
    ("ThermalZoneID", CeilingID.ThermalZoneIDs.ThermalZoneID),
]
CeilingID.ThermalZoneIDs.ThermalZoneID.element_attributes = [
    "IDref",  # IDREF
]
CeilingID.SpaceIDs.element_children = [
    ("SpaceID", CeilingID.SpaceIDs.SpaceID),
]
CeilingID.SpaceIDs.SpaceID.element_attributes = [
    "IDref",  # IDREF
]

# BuildingType.Sections.Section.Ceilings.Ceiling
class Ceiling(BSElement):
    """A finished construction under the roof or adjacent floor."""


Ceiling.element_children = [
    ("CeilingID", CeilingID),
]

# BuildingType.Sections.Section.Ceilings
class Ceilings(BSElement):
    """List of ceilings."""


Ceilings.element_children = [
    ("Ceiling", Ceiling),
]

# BuildingType.Sections.Section.ExteriorFloors.ExteriorFloor.ExteriorFloorID
class ExteriorFloorID(BSElement):
    """ID number of the exterior floor type associated with this section."""

    class ThermalZoneIDs(BSElement):
        class ThermalZoneID(BSElement):
            """ID number of the zone type associated with this space or side of the section."""

    class SpaceIDs(BSElement):
        class SpaceID(BSElement):
            """ID number of the space type associated with this side of the section."""


ExteriorFloorID.element_attributes = [
    "IDref",  # IDREF
]
ExteriorFloorID.element_children = [
    ("ExteriorFloorArea", ExteriorFloorArea),
    ("ThermalZoneIDs", ExteriorFloorID.ThermalZoneIDs),
    ("SpaceIDs", ExteriorFloorID.SpaceIDs),
]
ExteriorFloorID.ThermalZoneIDs.element_children = [
    ("ThermalZoneID", ExteriorFloorID.ThermalZoneIDs.ThermalZoneID),
]
ExteriorFloorID.ThermalZoneIDs.ThermalZoneID.element_attributes = [
    "IDref",  # IDREF
]
ExteriorFloorID.SpaceIDs.element_children = [
    ("SpaceID", ExteriorFloorID.SpaceIDs.SpaceID),
]
ExteriorFloorID.SpaceIDs.SpaceID.element_attributes = [
    "IDref",  # IDREF
]

# BuildingType.Sections.Section.ExteriorFloors.ExteriorFloor
class ExteriorFloor(BSElement):
    """A raised floor exposed to air. For example, the top floor of a multistory parking structure."""


ExteriorFloor.element_children = [
    ("ExteriorFloorID", ExteriorFloorID),
]

# BuildingType.Sections.Section.ExteriorFloors
class ExteriorFloors(BSElement):
    """List of exterior floors."""


ExteriorFloors.element_children = [
    ("ExteriorFloor", ExteriorFloor),
]

# BuildingType.Sections.Section.Foundations.Foundation.FoundationID
class FoundationID(BSElement):
    """ID number of the foundation type associated with this section."""

    class ThermalZoneIDs(BSElement):
        class ThermalZoneID(BSElement):
            """ID number of the zone type associated with this space or side of the section."""

    class SpaceIDs(BSElement):
        class SpaceID(BSElement):
            """ID number of the space type associated with this side of the section."""


FoundationID.element_attributes = [
    "IDref",  # IDREF
]
FoundationID.element_children = [
    ("FoundationArea", FoundationArea),
    ("ThermalZoneIDs", FoundationID.ThermalZoneIDs),
    ("SpaceIDs", FoundationID.SpaceIDs),
]
FoundationID.ThermalZoneIDs.element_children = [
    ("ThermalZoneID", FoundationID.ThermalZoneIDs.ThermalZoneID),
]
FoundationID.ThermalZoneIDs.ThermalZoneID.element_attributes = [
    "IDref",  # IDREF
]
FoundationID.SpaceIDs.element_children = [
    ("SpaceID", FoundationID.SpaceIDs.SpaceID),
]
FoundationID.SpaceIDs.SpaceID.element_attributes = [
    "IDref",  # IDREF
]

# BuildingType.Sections.Section.Foundations.Foundation
class Foundation(BSElement):
    """A construction element that supports the structure of the premises. In general it is made of masonry or concrete."""


Foundation.element_children = [
    ("FoundationID", FoundationID),
]

# BuildingType.Sections.Section.Foundations
class Foundations(BSElement):
    """List of foundations."""


Foundations.element_children = [
    ("Foundation", Foundation),
]

# OriginalOccupancyClassification
class OriginalOccupancyClassification(OccupancyClassificationType):
    """Original classification of the space (complex, whole building, or section) tasks by building occupants."""


# ThermalZoneType.DeliveryIDs
class DeliveryIDs(BSElement):
    pass


DeliveryIDs.element_children = [
    ("DeliveryID", DeliveryID),
]

# ThermalZoneType.HVACScheduleIDs
class HVACScheduleIDs(BSElement):
    pass


HVACScheduleIDs.element_children = [
    ("HVACScheduleID", HVACScheduleID),
]

# SpaceType.OccupancyScheduleIDs
class OccupancyScheduleIDs(BSElement):
    pass


OccupancyScheduleIDs.element_children = [
    ("OccupancyScheduleID", OccupancyScheduleID),
]

# ScheduleType.ScheduleDetails.ScheduleDetail
class ScheduleDetail(BSElement):
    """Type of day for which the schedule will be specified."""


ScheduleDetail.element_children = [
    ("DayType", DayType),
    ("ScheduleCategory", ScheduleCategory),
    ("DayStartTime", DayStartTime),
    ("DayEndTime", DayEndTime),
    ("PartialOperationPercentage", PartialOperationPercentage),
]

# ContactType.ContactRoles
class ContactRoles(BSElement):
    """Container for the a list of roles that a contact can have."""


ContactRoles.element_children = [
    ("ContactRole", ContactRole),
]

# ContactType.ContactTelephoneNumbers.ContactTelephoneNumber
class ContactTelephoneNumber(BSElement):
    pass


ContactTelephoneNumber.element_children = [
    ("ContactTelephoneNumberLabel", ContactTelephoneNumberLabel),
    ("TelephoneNumber", TelephoneNumber),
]

# ContactType.ContactEmailAddresses.ContactEmailAddress
class ContactEmailAddress(BSElement):
    pass


ContactEmailAddress.element_children = [
    ("ContactEmailAddressLabel", ContactEmailAddressLabel),
    ("EmailAddress", EmailAddress),
]

# TenantType.ContactIDs
class ContactIDs(BSElement):
    pass


ContactIDs.element_children = [
    ("ContactID", ContactID),
]

# TenantType.TenantTelephoneNumbers.TenantTelephoneNumber
class TenantTelephoneNumber(BSElement):
    pass


TenantTelephoneNumber.element_children = [
    ("TenantTelephoneNumberLabel", TenantTelephoneNumberLabel),
    ("TelephoneNumber", TelephoneNumber),
]

# TenantType.TenantEmailAddresses.TenantEmailAddress
class TenantEmailAddress(BSElement):
    pass


TenantEmailAddress.element_children = [
    ("TenantEmailAddressLabel", TenantEmailAddressLabel),
    ("EmailAddress", EmailAddress),
]

# CBECSType
class CBECSType(BSElement):
    class ClimateZone(BSElement):
        """Based on the Climate Zone Type term, this is the climate zone designation."""

        element_type = "xs:string"
        element_enumerations = ["1", "2", "3", "4", "5"]


CBECSType.element_children = [
    ("ClimateZone", CBECSType.ClimateZone),
]

# ScenarioType.ScenarioType.PackageOfMeasures.MeasureIDs
class MeasureIDs(BSElement):
    """ID numbers for measures included in the package. Multiple items may be selected."""


MeasureIDs.element_children = [
    ("MeasureID", MeasureID),
]

# ScenarioType.ScenarioType.PackageOfMeasures.SimpleImpactAnalysis.EstimatedCost
class EstimatedCost(LowMedHigh):
    """See SPC 211 Standard for Commercial Building Energy Audits section 6.1.5(d)"""


# ScenarioType.ScenarioType.PackageOfMeasures.SimpleImpactAnalysis
class SimpleImpactAnalysis(BSElement):
    class Priority(LowMedHigh):
        """See SPC 211 Standard for Commercial Building Energy Audits section 6.1.5(g)"""


SimpleImpactAnalysis.element_children = [
    ("ImpactOnOccupantComfort", ImpactOnOccupantComfort),
    ("EstimatedCost", EstimatedCost),
    ("EstimatedAnnualSavings", EstimatedAnnualSavings),
    ("EstimatedROI", EstimatedROI),
    ("Priority", SimpleImpactAnalysis.Priority),
]

# EnergyResource
class EnergyResource(FuelTypes):
    """Type of energy resource fuel. This can be applied at the premises or individual system or equipment level."""


# ScenarioType.WeatherType.Normalized
class Normalized(BSElement):
    pass


Normalized.element_children = [
    ("NormalizationYears", NormalizationYears),
    ("NormalizationStartYear", NormalizationStartYear),
    ("WeatherDataSource", WeatherDataSource),
]

# ScenarioType.WeatherType.AdjustedToYear
class AdjustedToYear(BSElement):
    pass


AdjustedToYear.element_children = [
    ("WeatherYear", WeatherYear),
    ("WeatherDataSource", WeatherDataSource),
]

# UtilityType.UtilityMeterNumbers
class UtilityMeterNumbers(BSElement):
    class UtilityMeterNumber(BSElement):
        """Unique identification number for the meter."""

        element_type = "xs:string"


UtilityMeterNumbers.element_children = [
    ("UtilityMeterNumber", UtilityMeterNumbers.UtilityMeterNumber),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.FlatRate
class FlatRate(BSElement):
    """A consumer will pay one flat rate no matter what the usage level is."""

    class RatePeriods(BSElement):
        class RatePeriod(BSElement):
            class RatePeriodName(BSElement):
                """The name or title of rate period.This is intended to capture the seasonal changes in rates."""

                element_type = "xs:string"

            class DemandWindow(BSElement):
                """The time period of measurement through which the demand is established. (min)"""

                element_type = "xs:integer"

            class DemandRatchetPercentage(BSElement):
                """Certain rate schedules incorporate demand ratchet percentage to ensure minimum billing demands based on historical peak demands. Billing demand in these cases is based comparing the month's demand and maximum of previous 11 month's demand times the demand ratchet percentage. (0-100) (%)"""

                element_type = "xs:decimal"

            class EnergyCostRate(BSElement):
                """Energy rate to buy a unit of energy consumption. ($/unit)"""

                element_type = "xs:decimal"

            class EnergyRateAdjustment(BSElement):
                """Energy rate adjustment for any fees, riders, fuel adjustments. ($/unit)"""

                element_type = "xs:decimal"

            class ElectricDemandRate(BSElement):
                """The rate to buy electric demand from the utility. ($/kW)"""

                element_type = "xs:decimal"

            class DemandRateAdjustment(BSElement):
                """The rate for any fees, riders, fuel adjustments. ($/kW)"""

                element_type = "xs:decimal"

            class EnergySellRate(BSElement):
                """Energy rate to sell a unit of electricity back to the utility from customer site generation through PV, wind etc. ($/kWh)"""

                element_type = "xs:decimal"


FlatRate.element_children = [
    ("RatePeriods", FlatRate.RatePeriods),
]
FlatRate.RatePeriods.element_children = [
    ("RatePeriod", FlatRate.RatePeriods.RatePeriod),
]
FlatRate.RatePeriods.RatePeriod.element_children = [
    ("RatePeriodName", FlatRate.RatePeriods.RatePeriod.RatePeriodName),
    ("ApplicableStartDateForEnergyRate", ApplicableStartDateForEnergyRate),
    ("ApplicableEndDateForEnergyRate", ApplicableEndDateForEnergyRate),
    ("ApplicableStartDateForDemandRate", ApplicableStartDateForDemandRate),
    ("ApplicableEndDateForDemandRate", ApplicableEndDateForDemandRate),
    ("DemandWindow", FlatRate.RatePeriods.RatePeriod.DemandWindow),
    (
        "DemandRatchetPercentage",
        FlatRate.RatePeriods.RatePeriod.DemandRatchetPercentage,
    ),
    ("EnergyCostRate", FlatRate.RatePeriods.RatePeriod.EnergyCostRate),
    ("EnergyRateAdjustment", FlatRate.RatePeriods.RatePeriod.EnergyRateAdjustment),
    ("ElectricDemandRate", FlatRate.RatePeriods.RatePeriod.ElectricDemandRate),
    ("DemandRateAdjustment", FlatRate.RatePeriods.RatePeriod.DemandRateAdjustment),
    ("EnergySellRate", FlatRate.RatePeriods.RatePeriod.EnergySellRate),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate.RatePeriods.RatePeriod.TimeOfUsePeriods.TimeOfUsePeriod
class TimeOfUsePeriod(BSElement):
    class EnergyCostRate(BSElement):
        """Energy rate to buy a unit of energy consumption. ($/unit)"""

        element_type = "xs:decimal"

    class ElectricDemandRate(BSElement):
        """The rate to buy electric demand from the utility. ($/kW)"""

        element_type = "xs:decimal"

    class EnergyRateAdjustment(BSElement):
        """Energy rate adjustment for any fees, riders, fuel adjustments. ($/unit)"""

        element_type = "xs:decimal"

    class DemandRateAdjustment(BSElement):
        """The rate for any fees, riders, fuel adjustments. ($/kW)"""

        element_type = "xs:decimal"

    class DemandWindow(BSElement):
        """The time period of measurement through which the demand is established. (min)"""

        element_type = "xs:integer"

    class DemandRatchetPercentage(BSElement):
        """Certain rate schedules incorporate demand ratchet percentage to ensure minimum billing demands based on historical peak demands. Billing demand in these cases is based comparing the month's demand and maximum of previous 11 month's demand times the demand ratchet percentage. (0-100) (%)"""

        element_type = "xs:decimal"


TimeOfUsePeriod.element_children = [
    ("TOUNumberForRateStructure", TOUNumberForRateStructure),
    ("ApplicableStartTimeForEnergyRate", ApplicableStartTimeForEnergyRate),
    ("ApplicableEndTimeForEnergyRate", ApplicableEndTimeForEnergyRate),
    ("ApplicableStartTimeForDemandRate", ApplicableStartTimeForDemandRate),
    ("ApplicableEndTimeForDemandRate", ApplicableEndTimeForDemandRate),
    ("EnergyCostRate", TimeOfUsePeriod.EnergyCostRate),
    ("ElectricDemandRate", TimeOfUsePeriod.ElectricDemandRate),
    ("EnergyRateAdjustment", TimeOfUsePeriod.EnergyRateAdjustment),
    ("DemandRateAdjustment", TimeOfUsePeriod.DemandRateAdjustment),
    ("DemandWindow", TimeOfUsePeriod.DemandWindow),
    ("DemandRatchetPercentage", TimeOfUsePeriod.DemandRatchetPercentage),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate.RatePeriods.RatePeriod.TimeOfUsePeriods
class TimeOfUsePeriods(BSElement):
    pass


TimeOfUsePeriods.element_children = [
    ("TimeOfUsePeriod", TimeOfUsePeriod),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TimeOfUseRate
class TimeOfUseRate(BSElement):
    """TOU rates vary by time of day and time of year."""

    class RatePeriods(BSElement):
        class RatePeriod(BSElement):
            class RatePeriodName(BSElement):
                """The name or title of rate period.This is intended to capture the seasonal changes in rates."""

                element_type = "xs:string"

            class EnergySellRate(BSElement):
                """Energy rate to sell a unit of electricity back to the utility from customer site generation through PV, wind etc. ($/kWh)"""

                element_type = "xs:decimal"


TimeOfUseRate.element_children = [
    ("RatePeriods", TimeOfUseRate.RatePeriods),
]
TimeOfUseRate.RatePeriods.element_children = [
    ("RatePeriod", TimeOfUseRate.RatePeriods.RatePeriod),
]
TimeOfUseRate.RatePeriods.RatePeriod.element_children = [
    ("RatePeriodName", TimeOfUseRate.RatePeriods.RatePeriod.RatePeriodName),
    ("ApplicableStartDateForEnergyRate", ApplicableStartDateForEnergyRate),
    ("ApplicableEndDateForEnergyRate", ApplicableEndDateForEnergyRate),
    ("ApplicableStartDateForDemandRate", ApplicableStartDateForDemandRate),
    ("ApplicableEndDateForDemandRate", ApplicableEndDateForDemandRate),
    ("TimeOfUsePeriods", TimeOfUsePeriods),
    ("EnergySellRate", TimeOfUseRate.RatePeriods.RatePeriod.EnergySellRate),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates.TieredRate.RatePeriods.RatePeriod.RateTiers.RateTier
class RateTier(BSElement):
    class EnergyCostRate(BSElement):
        """Energy rate to buy a unit of energy consumption. ($/unit)"""

        element_type = "xs:decimal"

    class ElectricDemandRate(BSElement):
        """The rate to buy electric demand from the utility. ($/kW)"""

        element_type = "xs:decimal"

    class EnergyRateAdjustment(BSElement):
        """Energy rate adjustment for any fees, riders, fuel adjustments. ($/unit)"""

        element_type = "xs:decimal"

    class DemandRateAdjustment(BSElement):
        """The rate for any fees, riders, fuel adjustments. ($/kW)"""

        element_type = "xs:decimal"

    class DemandWindow(BSElement):
        """The time period of measurement through which the demand is established. (min)"""

        element_type = "xs:integer"

    class DemandRatchetPercentage(BSElement):
        """Certain rate schedules incorporate demand ratchet percentage to ensure minimum billing demands based on historical peak demands. Billing demand in these cases is based comparing the month's demand and maximum of previous 11 month's demand times the demand ratchet percentage. (0-100) (%)"""

        element_type = "xs:decimal"


RateTier.element_children = [
    ("ConsumptionEnergyTierDesignation", ConsumptionEnergyTierDesignation),
    ("MaxkWhUsage", MaxkWhUsage),
    ("MaxkWUsage", MaxkWUsage),
    ("EnergyCostRate", RateTier.EnergyCostRate),
    ("ElectricDemandRate", RateTier.ElectricDemandRate),
    ("EnergyRateAdjustment", RateTier.EnergyRateAdjustment),
    ("DemandRateAdjustment", RateTier.DemandRateAdjustment),
    ("DemandWindow", RateTier.DemandWindow),
    ("DemandRatchetPercentage", RateTier.DemandRatchetPercentage),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates.TieredRate.RatePeriods.RatePeriod.RateTiers
class RateTiers(BSElement):
    pass


RateTiers.element_children = [
    ("RateTier", RateTier),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates.TieredRate
class TieredRate(BSElement):
    """Tiered rates increase the per-unit price of a utility as usage increases."""

    class RatePeriods(BSElement):
        class RatePeriod(BSElement):
            class RatePeriodName(BSElement):
                """The name or title of rate period.This is intended to capture the seasonal changes in rates."""

                element_type = "xs:string"

            class EnergySellRate(BSElement):
                """Energy rate to sell a unit of electricity back to the utility from customer site generation through PV, wind etc. ($/kWh)"""

                element_type = "xs:decimal"


TieredRate.element_children = [
    ("RatePeriods", TieredRate.RatePeriods),
    ("TierDirection", TierDirection),
]
TieredRate.RatePeriods.element_children = [
    ("RatePeriod", TieredRate.RatePeriods.RatePeriod),
]
TieredRate.RatePeriods.RatePeriod.element_children = [
    ("RatePeriodName", TieredRate.RatePeriods.RatePeriod.RatePeriodName),
    ("ApplicableStartDateForEnergyRate", ApplicableStartDateForEnergyRate),
    ("ApplicableEndDateForEnergyRate", ApplicableEndDateForEnergyRate),
    ("ApplicableStartDateForDemandRate", ApplicableStartDateForDemandRate),
    ("ApplicableEndDateForDemandRate", ApplicableEndDateForDemandRate),
    ("RateTiers", RateTiers),
    ("EnergySellRate", TieredRate.RatePeriods.RatePeriod.EnergySellRate),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure.TieredRates
class TieredRates(BSElement):
    pass


TieredRates.element_children = [
    ("TieredRate", TieredRate),
]

# UtilityType.RateSchedules.RateSchedule.TypeOfRateStructure
class TypeOfRateStructure(BSElement):
    """Basic type of rate structure used by the utility."""

    class Other(OtherType):
        """Other type of rate structure, or combination of other types."""

    class Unknown(UnknownType):
        pass


TypeOfRateStructure.element_children = [
    ("FlatRate", FlatRate),
    ("TimeOfUseRate", TimeOfUseRate),
    ("TieredRates", TieredRates),
    ("RealTimePricing", RealTimePricing),
    ("VariablePeakPricing", VariablePeakPricing),
    ("CriticalPeakPricing", CriticalPeakPricing),
    ("CriticalPeakRebates", CriticalPeakRebates),
    ("Other", TypeOfRateStructure.Other),
    ("Unknown", TypeOfRateStructure.Unknown),
]

# UtilityType.RateSchedules.RateSchedule.NetMetering
class NetMetering(BSElement):
    """Present if a billing mechanism is employed by utilities to credit onsite energy generation for this rate structure."""


NetMetering.element_children = [
    ("AverageMarginalSellRate", AverageMarginalSellRate),
]

# UtilityType.RateSchedules.RateSchedule
class RateSchedule(BSElement):
    """Rate structure characteristics."""


RateSchedule.element_attributes = [
    "ID",  # ID
]
RateSchedule.element_children = [
    ("RateStructureName", RateStructureName),
    ("TypeOfRateStructure", TypeOfRateStructure),
    ("RateStructureSector", RateStructureSector),
    ("ReferenceForRateStructure", ReferenceForRateStructure),
    ("RateStructureEffectiveDate", RateStructureEffectiveDate),
    ("RateStructureEndDate", RateStructureEndDate),
    ("ReactivePowerCharge", ReactivePowerCharge),
    ("MinimumPowerFactorWithoutPenalty", MinimumPowerFactorWithoutPenalty),
    ("FixedMonthlyCharge", FixedMonthlyCharge),
    ("NetMetering", NetMetering),
    ("AverageMarginalCostRate", AverageMarginalCostRate),
]

# ResourceUseType.AnnualFuelUseLinkedTimeSeriesIDs
class AnnualFuelUseLinkedTimeSeriesIDs(BSElement):
    """Links to all time series data used to calculate the AnnualFuelUse values."""


AnnualFuelUseLinkedTimeSeriesIDs.element_children = [
    ("LinkedTimeSeriesID", LinkedTimeSeriesID),
]

# ResourceUseType.UtilityIDs
class UtilityIDs(BSElement):
    pass


UtilityIDs.element_children = [
    ("UtilityID", UtilityID),
]

# ResourceUseType.Emissions.Emission
class Emission(BSElement):
    pass


Emission.element_children = [
    ("EmissionBoundary", EmissionBoundary),
    ("EmissionsType", EmissionsType),
    ("EmissionsFactor", EmissionsFactor),
    ("EmissionsFactorSource", EmissionsFactorSource),
    ("GHGEmissions", GHGEmissions),
    ("AvoidedEmissions", AvoidedEmissions),
]

# TimeSeriesType.IntervalDurationUnits
class IntervalDurationUnits(IntervalTime):
    """The units of the time series IntervalDuration"""


# MeasureType.TypeOfMeasure.Replacements.Replacement
class Replacement(BSElement):
    class ExistingScheduleAffected(BSElement):
        """ID numbers of schedules replaced by the measure."""

    class ModifiedSchedule(BSElement):
        """ID numbers of schedules associated with the improved systems."""


Replacement.element_children = [
    ("ExistingSystemReplaced", ExistingSystemReplaced),
    ("AlternativeSystemReplacement", AlternativeSystemReplacement),
    ("ExistingScheduleAffected", Replacement.ExistingScheduleAffected),
    ("ModifiedSchedule", Replacement.ModifiedSchedule),
]
Replacement.ExistingScheduleAffected.element_attributes = [
    "IDref",  # IDREF
]
Replacement.ModifiedSchedule.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.Replacements
class Replacements(BSElement):
    pass


Replacements.element_children = [
    ("Replacement", Replacement),
]

# MeasureType.TypeOfMeasure.ModificationRetrocommissions.ModificationRetrocommissioning
class ModificationRetrocommissioning(BSElement):
    class ExistingScheduleAffected(BSElement):
        """ID numbers of schedules replaced by the measure."""

    class ModifiedSchedule(BSElement):
        """ID numbers of schedules associated with the improved systems."""


ModificationRetrocommissioning.element_children = [
    ("ExistingSystemAffected", ExistingSystemAffected),
    ("ModifiedSystem", ModifiedSystem),
    (
        "ExistingScheduleAffected",
        ModificationRetrocommissioning.ExistingScheduleAffected,
    ),
    ("ModifiedSchedule", ModificationRetrocommissioning.ModifiedSchedule),
]
ModificationRetrocommissioning.ExistingScheduleAffected.element_attributes = [
    "IDref",  # IDREF
]
ModificationRetrocommissioning.ModifiedSchedule.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.ModificationRetrocommissions
class ModificationRetrocommissions(BSElement):
    pass


ModificationRetrocommissions.element_children = [
    ("ModificationRetrocommissioning", ModificationRetrocommissioning),
]

# MeasureType.TypeOfMeasure.Additions.Addition
class Addition(BSElement):
    class ExistingScheduleAffected(BSElement):
        """ID numbers of schedules replaced by the measure."""

    class ModifiedSchedule(BSElement):
        """ID numbers of schedules associated with the improved systems."""


Addition.element_children = [
    ("AlternativeSystemAdded", AlternativeSystemAdded),
    ("ExistingScheduleAffected", Addition.ExistingScheduleAffected),
    ("ModifiedSchedule", Addition.ModifiedSchedule),
]
Addition.ExistingScheduleAffected.element_attributes = [
    "IDref",  # IDREF
]
Addition.ModifiedSchedule.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.Additions
class Additions(BSElement):
    pass


Additions.element_children = [
    ("Addition", Addition),
]

# MeasureType.TypeOfMeasure.Removals.Removal
class Removal(BSElement):
    class ExistingScheduleAffected(BSElement):
        """ID numbers of schedules replaced by the measure."""

    class ModifiedSchedule(BSElement):
        """ID numbers of schedules associated with the improved systems."""


Removal.element_children = [
    ("ExistingSystemRemoved", ExistingSystemRemoved),
    ("ExistingScheduleAffected", Removal.ExistingScheduleAffected),
    ("ModifiedSchedule", Removal.ModifiedSchedule),
]
Removal.ExistingScheduleAffected.element_attributes = [
    "IDref",  # IDREF
]
Removal.ModifiedSchedule.element_attributes = [
    "IDref",  # IDREF
]

# MeasureType.TypeOfMeasure.Removals
class Removals(BSElement):
    pass


Removals.element_children = [
    ("Removal", Removal),
]

# MeasureType.TechnologyCategories.TechnologyCategory.BoilerPlantImprovements
class BoilerPlantImprovements(BSElement):
    """Boiler plant improvements."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Replace boiler",
            "Replace burner",
            "Decentralize boiler",
            "Insulate boiler room",
            "Add energy recovery",
            "Convert gas-fired unit to boiler loop",
            "Convert system from steam to hot water",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Convert to Cleaner Fuels",
            "Other",
        ]


BoilerPlantImprovements.element_children = [
    ("MeasureName", BoilerPlantImprovements.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.ChillerPlantImprovements
class ChillerPlantImprovements(BSElement):
    """Chiller plant improvements."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Add energy recovery",
            "Install VSD on electric centrifugal chillers",
            "Replace chiller",
            "Install gas cooling",
            "Add or repair economizer cycle",
            "Add or replace cooling tower",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


ChillerPlantImprovements.element_children = [
    ("MeasureName", ChillerPlantImprovements.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.BuildingAutomationSystems
class BuildingAutomationSystems(BSElement):
    """Building Automation Systems (BAS) or Energy Management Control Systems (EMCS)."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Add heat recovery",
            "Add or upgrade BAS/EMS/EMCS",
            "Add or upgrade controls",
            "Convert pneumatic controls to DDC",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


BuildingAutomationSystems.element_children = [
    ("MeasureName", BuildingAutomationSystems.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.OtherHVAC
class OtherHVAC(BSElement):
    """Other measure related to heating, ventilating, and air conditioning (HVAC)."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Replace or modify AHU",
            "Improve distribution fans",
            "Improve ventilation fans",
            "Convert CV system to VAV system",
            "Repair leaks / seal ducts",
            "Add duct insulation",
            "Balance ventilation/distribution system",
            "Repair or replace HVAC damper and controller",
            "Replace burner",
            "Replace package units",
            "Replace packaged terminal units",
            "Install passive solar heating",
            "Replace AC and heating units with ground coupled heat pump systems",
            "Add enhanced dehumidification",
            "Install solar ventilation preheating system",
            "Add or repair economizer",
            "Add energy recovery",
            "Add or replace cooling tower",
            "Install thermal destratification fans",
            "Install demand control ventilation",
            "Install gas cooling",
            "Install air source heat pump",
            "Install variable refrigerant flow system",
            "Capture and return condensate",
            "Install or Upgrade Master Venting",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other heating",
            "Other cooling",
            "Other ventilation",
            "Other distribution",
            "Other",
        ]


OtherHVAC.element_children = [
    ("MeasureName", OtherHVAC.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.LightingImprovements
class LightingImprovements(BSElement):
    """Lighting improvements."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Retrofit with CFLs",
            "Retrofit with T-5",
            "Retrofit with T-8",
            "Install spectrally enhanced lighting",
            "Retrofit with fiber optic lighting technologies",
            "Retrofit with light emitting diode technologies",
            "Add daylight controls",
            "Add occupancy sensors",
            "Install photocell control",
            "Install timers",
            "Replace diffusers",
            "Upgrade exit signs to LED",
            "Upgrade exterior lighting",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


LightingImprovements.element_children = [
    ("MeasureName", LightingImprovements.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.BuildingEnvelopeModifications
class BuildingEnvelopeModifications(BSElement):
    """Building envelope modifications."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Air seal envelope",
            "Increase wall insulation",
            "Insulate thermal bypasses",
            "Increase ceiling insulation",
            "Increase roof insulation",
            "Insulate attic hatch / stair box",
            "Add attic/knee wall insulation",
            "Install cool/green roof",
            "Add shading devices",
            "Add window films",
            "Install or replace solar screens",
            "Replace glazing",
            "Replace windows",
            "Increase floor insulation",
            "Insulate foundation",
            "Clean and/or repair",
            "Close elevator and/or stairwell shaft vents",
            "Other",
        ]


BuildingEnvelopeModifications.element_children = [
    ("MeasureName", BuildingEnvelopeModifications.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.ChilledWaterHotWaterAndSteamDistributionSystems
class ChilledWaterHotWaterAndSteamDistributionSystems(BSElement):
    """Chilled water, hot water, and steam distribution systems."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Add pipe insulation",
            "Repair and/or replace steam traps",
            "Retrofit and replace chiller plant pumping, piping, and controls",
            "Repair or replace existing condensate return systems or install new condensate return systems",
            "Add recirculating pumps",
            "Replace or upgrade water heater",
            "Add energy recovery",
            "Install solar hot water system",
            "Separate SHW from heating",
            "Replace with higher efficiency pump",
            "Replace with variable speed pump",
            "Install or upgrade master venting",
            "Replace steam traps with orifice plates",
            "Install steam condensate heat recovery",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


ChilledWaterHotWaterAndSteamDistributionSystems.element_children = [
    ("MeasureName", ChilledWaterHotWaterAndSteamDistributionSystems.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.OtherElectricMotorsAndDrives
class OtherElectricMotorsAndDrives(BSElement):
    """Electric motors and drives other than those for conveyance systems."""

    class MeasureName(BSElement):
        """Short description of measure"""

        element_type = "xs:string"
        element_enumerations = [
            "Add drive controls",
            "Replace with higher efficiency",
            "Add VSD motor controller",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


OtherElectricMotorsAndDrives.element_children = [
    ("MeasureName", OtherElectricMotorsAndDrives.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.Refrigeration
class Refrigeration(BSElement):
    """Refrigeration."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Replace ice/refrigeration equipment with high efficiency units",
            "Replace air-cooled ice/refrigeration equipment",
            "Replace refrigerators",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


Refrigeration.element_children = [
    ("MeasureName", Refrigeration.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.DistributedGeneration
class DistributedGeneration(BSElement):
    """Distributed generation."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Install CHP/cogeneration systems",
            "Install fuel cells",
            "Install microturbines",
            "Convert fuels",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


DistributedGeneration.element_children = [
    ("MeasureName", DistributedGeneration.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.RenewableEnergySystems
class RenewableEnergySystems(BSElement):
    """Renewable energy systems."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Install landfill gas, wastewater treatment plant digester gas, or coal bed methane power plant",
            "Install photovoltaic system",
            "Install wind energy system",
            "Install wood waste or other organic waste stream heating or power plant",
            "Install electrical storage",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


RenewableEnergySystems.element_children = [
    ("MeasureName", RenewableEnergySystems.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.EnergyDistributionSystems
class EnergyDistributionSystems(BSElement):
    """Energy and utility distribution systems."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Implement power factor corrections",
            "Implement power quality upgrades",
            "Upgrade transformers",
            "Install gas distribution systems",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


EnergyDistributionSystems.element_children = [
    ("MeasureName", EnergyDistributionSystems.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.ServiceHotWaterSystems
class ServiceHotWaterSystems(BSElement):
    """Service hot water (SHW) and domestic hot water (DHW) systems."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Decrease SHW temperature",
            "Install SHW controls",
            "Install solar thermal SHW",
            "Install water pressure booster",
            "Insulate SHW piping",
            "Insulate SHW tank",
            "Replace piping",
            "Replace tankless coil",
            "Separate SHW from heating",
            "Upgrade SHW boiler",
            "Install heat pump SHW system",
            "Install tankless water heaters",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


ServiceHotWaterSystems.element_children = [
    ("MeasureName", ServiceHotWaterSystems.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.WaterAndSewerConservationSystems
class WaterAndSewerConservationSystems(BSElement):
    """Water and sewer conservation systems."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Install low-flow faucets and showerheads",
            "Install low-flow plumbing equipment",
            "Install onsite sewer treatment systems",
            "Implement water efficient irrigation",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


WaterAndSewerConservationSystems.element_children = [
    ("MeasureName", WaterAndSewerConservationSystems.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.ElectricalPeakShavingLoadShifting
class ElectricalPeakShavingLoadShifting(BSElement):
    """Electrical peak shaving and load shifting."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Install thermal energy storage",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


ElectricalPeakShavingLoadShifting.element_children = [
    ("MeasureName", ElectricalPeakShavingLoadShifting.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.EnergyCostReductionThroughRateAdjustments
class EnergyCostReductionThroughRateAdjustments(BSElement):
    """Energy cost reduction through rate adjustments."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Change to more favorable rate schedule",
            "Energy cost reduction through rate adjustments - uncategorized",
            "Energy service billing and meter auditing recommendations",
            "Change to lower energy cost supplier(s)",
            "Other",
        ]


EnergyCostReductionThroughRateAdjustments.element_children = [
    ("MeasureName", EnergyCostReductionThroughRateAdjustments.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.EnergyRelatedProcessImprovements
class EnergyRelatedProcessImprovements(BSElement):
    """Energy related process improvements."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Implement industrial process improvements",
            "Implement production and/or manufacturing improvements",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


EnergyRelatedProcessImprovements.element_children = [
    ("MeasureName", EnergyRelatedProcessImprovements.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.AdvancedMeteringSystems
class AdvancedMeteringSystems(BSElement):
    """Advanced metering systems."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Install advanced metering systems",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


AdvancedMeteringSystems.element_children = [
    ("MeasureName", AdvancedMeteringSystems.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.PlugLoadReductions
class PlugLoadReductions(BSElement):
    """Appliance and plug-load reductions."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Replace with ENERGY STAR rated",
            "Install plug load controls",
            "Automatic shutdown or sleep mode for computers",
            "De-lamp vending machines",
            "Replace clothes dryers",
            "Replace washing machines",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


PlugLoadReductions.element_children = [
    ("MeasureName", PlugLoadReductions.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.DataCenterImprovements
class DataCenterImprovements(BSElement):
    """Data center energy conservation improvements."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = [
            "Improve data center efficiency",
            "Implement hot aisle hold aisle design",
            "Implement server virtualization",
            "Upgrade servers",
            "Clean and/or repair",
            "Implement training and/or documentation",
            "Upgrade operating protocols, calibration, and/or sequencing",
            "Other",
        ]


DataCenterImprovements.element_children = [
    ("MeasureName", DataCenterImprovements.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.FutureOtherECMs
class FutureOtherECMs(BSElement):
    """Measures reserved for future and other ECMs."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = ["Other"]


FutureOtherECMs.element_children = [
    ("MeasureName", FutureOtherECMs.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.HealthAndSafety
class HealthAndSafety(BSElement):
    """Category heading for measures that are necessary for health, comfort, or safety reasons, not for energy efficiency reasons."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"


HealthAndSafety.element_children = [
    ("MeasureName", HealthAndSafety.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory.Uncategorized
class Uncategorized(BSElement):
    """Category heading for measures that don't fit into another category."""

    class MeasureName(BSElement):
        """Short description of measure."""

        element_type = "xs:string"
        element_enumerations = ["Other"]


Uncategorized.element_children = [
    ("MeasureName", Uncategorized.MeasureName),
]

# MeasureType.TechnologyCategories.TechnologyCategory
class TechnologyCategory(BSElement):
    """Authorized technology category as defined by the Federal Energy Management Program (FEMP). In some cases a single measure may include multiple components affecting multiple categories."""

    class ConveyanceSystems(BSElement):
        """Conveyance systems such as elevators and escalators."""

        class MeasureName(BSElement):
            """Short description of measure."""

            element_type = "xs:string"
            element_enumerations = [
                "Add elevator regenerative drives",
                "Upgrade controls",
                "Upgrade motors",
                "Clean and/or repair",
                "Implement training and/or documentation",
                "Upgrade operating protocols, calibration, and/or sequencing",
                "Other",
            ]


TechnologyCategory.element_children = [
    ("BoilerPlantImprovements", BoilerPlantImprovements),
    ("ChillerPlantImprovements", ChillerPlantImprovements),
    ("BuildingAutomationSystems", BuildingAutomationSystems),
    ("OtherHVAC", OtherHVAC),
    ("LightingImprovements", LightingImprovements),
    ("BuildingEnvelopeModifications", BuildingEnvelopeModifications),
    (
        "ChilledWaterHotWaterAndSteamDistributionSystems",
        ChilledWaterHotWaterAndSteamDistributionSystems,
    ),
    ("ConveyanceSystems", TechnologyCategory.ConveyanceSystems),
    ("OtherElectricMotorsAndDrives", OtherElectricMotorsAndDrives),
    ("Refrigeration", Refrigeration),
    ("DistributedGeneration", DistributedGeneration),
    ("RenewableEnergySystems", RenewableEnergySystems),
    ("EnergyDistributionSystems", EnergyDistributionSystems),
    ("ServiceHotWaterSystems", ServiceHotWaterSystems),
    ("WaterAndSewerConservationSystems", WaterAndSewerConservationSystems),
    ("ElectricalPeakShavingLoadShifting", ElectricalPeakShavingLoadShifting),
    (
        "EnergyCostReductionThroughRateAdjustments",
        EnergyCostReductionThroughRateAdjustments,
    ),
    ("EnergyRelatedProcessImprovements", EnergyRelatedProcessImprovements),
    ("AdvancedMeteringSystems", AdvancedMeteringSystems),
    ("PlugLoadReductions", PlugLoadReductions),
    ("DataCenterImprovements", DataCenterImprovements),
    ("FutureOtherECMs", FutureOtherECMs),
    ("HealthAndSafety", HealthAndSafety),
    ("Uncategorized", Uncategorized),
]
TechnologyCategory.ConveyanceSystems.element_children = [
    ("MeasureName", TechnologyCategory.ConveyanceSystems.MeasureName),
]

# ReportType.AuditDates.AuditDate
class AuditDate(BSElement):
    pass


AuditDate.element_children = [
    ("Date", Date),
    ("DateType", DateType),
    ("CustomDateType", CustomDateType),
]

# ReportType.OtherEscalationRates.OtherEscalationRate
class OtherEscalationRate(BSElement):
    pass


OtherEscalationRate.element_attributes = [
    "Source",  # Source
]
OtherEscalationRate.element_children = [
    ("EnergyResource", EnergyResource),
    ("EscalationRate", EscalationRate),
]

# ReportType.Qualifications.Qualification.AuditorQualification
class AuditorQualification(AuditorQualificationType):
    """Qualification of auditor responsible for the audit report."""


# ReportType.Qualifications.Qualification.AuditorQualificationState
class AuditorQualificationState(State):
    """If AuditorQualification is state-issued, the state the qualification is from."""


# ReportType.Qualifications.Qualification
class Qualification(BSElement):
    """Qualifications of audit team."""


Qualification.element_attributes = [
    "ID",  # ID
]
Qualification.element_children = [
    ("AuditorQualification", AuditorQualification),
    ("AuditorQualificationNumber", AuditorQualificationNumber),
    ("AuditorQualificationState", AuditorQualificationState),
    ("CertificationExpirationDate", CertificationExpirationDate),
    ("CertifiedAuditTeamMemberContactID", CertifiedAuditTeamMemberContactID),
    ("AuditTeamMemberCertificationType", AuditTeamMemberCertificationType),
]

# HVACSystemType.HVACControlSystemTypes
class HVACControlSystemTypes(BSElement):
    """HVAC equipment control strategies."""


HVACControlSystemTypes.element_children = [
    ("HVACControlSystemType", HVACControlSystemType),
]

# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.Furnace
class Furnace(BSElement):
    pass


Furnace.element_children = [
    ("FurnaceType", FurnaceType),
    ("BurnerType", BurnerType),
    ("BurnerControlType", BurnerControlType),
    ("BurnerQuantity", BurnerQuantity),
    ("BurnerYearInstalled", BurnerYearInstalled),
    ("BurnerTurndownRatio", BurnerTurndownRatio),
    ("IgnitionType", IgnitionType),
    ("DraftType", DraftType),
    ("DraftBoundary", DraftBoundary),
    ("CondensingOperation", CondensingOperation),
    ("CombustionEfficiency", CombustionEfficiency),
    ("ThermalEfficiency", ThermalEfficiency),
    ("ThirdPartyCertification", ThirdPartyCertification),
]

# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.HeatPump.HeatPumpBackupSystemFuel
class HeatPumpBackupSystemFuel(FuelTypes):
    """Backup fuel used by the heat pump."""


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType.NoHeating
class NoHeating(NoHeatingType):
    pass


# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingSourceType
class HeatingSourceType(BSElement):
    """Source of energy used for heating the zone."""

    class ElectricResistance(ElectricResistanceType):
        pass

    class HeatPump(BSElement):
        class CoolingSourceID(BSElement):
            """ID number of the CoolingSource with the cooling mode performance characteristics of this heat pump."""

    class OtherCombination(OtherCombinationType):
        pass

    class Unknown(UnknownType):
        pass


HeatingSourceType.element_children = [
    ("SourceHeatingPlantID", SourceHeatingPlantID),
    ("ElectricResistance", HeatingSourceType.ElectricResistance),
    ("Furnace", Furnace),
    ("HeatPump", HeatingSourceType.HeatPump),
    ("OtherCombination", HeatingSourceType.OtherCombination),
    ("NoHeating", NoHeating),
    ("Unknown", HeatingSourceType.Unknown),
]
HeatingSourceType.HeatPump.element_children = [
    ("HeatPumpType", HeatPumpType),
    (
        "HeatPumpBackupHeatingSwitchoverTemperature",
        HeatPumpBackupHeatingSwitchoverTemperature,
    ),
    ("HeatPumpBackupSystemFuel", HeatPumpBackupSystemFuel),
    ("HeatPumpBackupAFUE", HeatPumpBackupAFUE),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("CoolingSourceID", HeatingSourceType.HeatPump.CoolingSourceID),
    ("LinkedHeatingPlantID", LinkedHeatingPlantID),
]
HeatingSourceType.HeatPump.CoolingSourceID.element_attributes = [
    "IDref",  # IDREF
]

# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource.HeatingStageCapacityFraction
class HeatingStageCapacityFraction(BoundedDecimalZeroToOneWithSourceAttribute):
    """Average capacity of each heating stage, at Air-Conditioning, Heating, and Refrigeration Institute (AHRI) rated conditions, expressed as a fraction of total capacity. (0-1) (fraction)"""


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.DX
class DX(BSElement):
    class CondenserPlantIDs(BSElement):
        class CondenserPlantID(BSElement):
            """ID number of the central CondenserPlant serving as the source for this cooling system."""


DX.element_children = [
    ("DXSystemType", DXSystemType),
    ("CompressorType", CompressorType),
    ("CompressorStaging", CompressorStaging),
    ("CondenserPlantIDs", DX.CondenserPlantIDs),
    ("Refrigerant", Refrigerant),
    ("RefrigerantChargeFactor", RefrigerantChargeFactor),
    ("ActiveDehumidification", ActiveDehumidification),
]
DX.CondenserPlantIDs.element_children = [
    ("CondenserPlantID", DX.CondenserPlantIDs.CondenserPlantID),
]
DX.CondenserPlantIDs.CondenserPlantID.element_attributes = [
    "IDref",  # IDREF
]

# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.EvaporativeCooler
class EvaporativeCooler(BSElement):
    pass


EvaporativeCooler.element_children = [
    ("EvaporativeCoolingType", EvaporativeCoolingType),
]

# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType.NoCooling
class NoCooling(NoCoolingType):
    pass


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.CoolingSourceType
class CoolingSourceType(BSElement):
    """Source of energy used for cooling the zone."""

    class OtherCombination(OtherCombinationType):
        pass

    class Unknown(UnknownType):
        pass


CoolingSourceType.element_children = [
    ("CoolingPlantID", CoolingPlantID),
    ("DX", DX),
    ("EvaporativeCooler", EvaporativeCooler),
    ("OtherCombination", CoolingSourceType.OtherCombination),
    ("NoCooling", NoCooling),
    ("Unknown", CoolingSourceType.Unknown),
]

# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.MinimumPartLoadRatio
class MinimumPartLoadRatio(BoundedDecimalZeroToOneWithSourceAttribute):
    """The minimum part load ratio at which the system is able to operate. (0-1) (fraction)"""


# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource.RatedCoolingSensibleHeatRatio
class RatedCoolingSensibleHeatRatio(BoundedDecimalZeroToOneWithSourceAttribute):
    """The fraction of total energy transfer between the evaporator coil and air that is associated with sensible capacity (change in air temperature) expressed as a dimensionless value, and at the rated conditions prescribed for this system. (0-1) (fraction)"""


# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.ZoneEquipment.Convection
class Convection(BSElement):
    class PipeInsulationThickness(BSElement):
        """Defines how thick insulation on pipes in a heating, cooling, water heating system is. (in.)"""

        element_type = "xs:decimal"

    class PipeLocation(BSElement):
        """Percent of pipe length in conditioned space. (0-100) (%)"""

        element_type = "xs:decimal"


Convection.element_children = [
    ("ConvectionType", ConvectionType),
    ("PipeInsulationThickness", Convection.PipeInsulationThickness),
    ("PipeLocation", Convection.PipeLocation),
]

# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.ZoneEquipment.Radiant
class Radiant(BSElement):
    class PipeInsulationThickness(BSElement):
        """Defines how thick insulation on pipes in a heating, cooling, water heating system is. (in.)"""

        element_type = "xs:decimal"

    class PipeLocation(BSElement):
        """Percent of pipe length in conditioned space. (0-100) (%)"""

        element_type = "xs:decimal"


Radiant.element_children = [
    ("RadiantType", RadiantType),
    ("PipeInsulationThickness", Radiant.PipeInsulationThickness),
    ("PipeLocation", Radiant.PipeLocation),
]

# DuctSystemType.DuctInsulationCondition
class DuctInsulationCondition(InsulationCondition):
    pass


# DuctSystemType.SupplyFractionOfDuctLeakage
class SupplyFractionOfDuctLeakage(BoundedDecimalZeroToOneWithSourceAttribute):
    """Fraction of total duct leakage that is on the supply side. Remainder is assumed to be on the return side. (0-1) (fraction)"""


# OtherHVACSystemType.LinkedDeliveryIDs
class LinkedDeliveryIDs(BSElement):
    """List of connections to air distribution systems."""


LinkedDeliveryIDs.element_children = [
    ("LinkedDeliveryID", LinkedDeliveryID),
]

# OtherHVACSystemType.OtherHVACType.Humidifier
class Humidifier(BSElement):
    pass


Humidifier.element_children = [
    ("HumidificationType", HumidificationType),
    ("HumidityControlMinimum", HumidityControlMinimum),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("DutyCycle", DutyCycle),
    ("SystemPerformanceRatio", SystemPerformanceRatio),
]

# OtherHVACSystemType.OtherHVACType.Dehumidifier
class Dehumidifier(BSElement):
    pass


Dehumidifier.element_children = [
    ("DehumidificationType", DehumidificationType),
    ("HumidityControlMaximum", HumidityControlMaximum),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("DutyCycle", DutyCycle),
    ("SystemPerformanceRatio", SystemPerformanceRatio),
    ("ThirdPartyCertification", ThirdPartyCertification),
]

# OtherHVACSystemType.OtherHVACType.MechanicalVentilation
class MechanicalVentilation(BSElement):
    class VentilationRate(BSElement):
        """Installed flow rate for mechanical ventilation system. (cfm)"""

        element_type = "xs:decimal"

    class RequiredVentilationRate(BSElement):
        """Minimum ventilation rate required by local code. (cfm)"""

        element_type = "xs:decimal"

    class VentilationControlMethods(BSElement):
        """List of ventilation control methods."""

    class MakeupAirSourceID(BSElement):
        """ID number of the Space that provides makeup air for exhaust ventilation."""

        element_type = "xs:IDREF"


MechanicalVentilation.element_children = [
    ("VentilationRate", MechanicalVentilation.VentilationRate),
    ("RequiredVentilationRate", MechanicalVentilation.RequiredVentilationRate),
    ("VentilationType", VentilationType),
    ("DemandControlVentilation", DemandControlVentilation),
    ("VentilationControlMethods", MechanicalVentilation.VentilationControlMethods),
    ("VentilationZoneControl", VentilationZoneControl),
    ("MakeupAirSourceID", MechanicalVentilation.MakeupAirSourceID),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("DutyCycle", DutyCycle),
    ("SystemPerformanceRatio", SystemPerformanceRatio),
    ("ThirdPartyCertification", ThirdPartyCertification),
]
MechanicalVentilation.VentilationControlMethods.element_children = [
    ("VentilationControlMethod", VentilationControlMethod),
]

# OtherHVACSystemType.OtherHVACType.SpotExhaust
class SpotExhaust(BSElement):
    class VentilationRate(BSElement):
        """Installed flow rate for mechanical ventilation system. (cfm)"""

        element_type = "xs:decimal"

    class RequiredVentilationRate(BSElement):
        """Minimum ventilation rate required by local code. (cfm)"""

        element_type = "xs:decimal"

    class VentilationControlMethods(BSElement):
        """List of ventilation control methods."""

    class MakeupAirSourceID(BSElement):
        """ID number of the Space that provides makeup air for exhaust ventilation."""

        element_type = "xs:IDREF"


SpotExhaust.element_children = [
    ("ExhaustLocation", ExhaustLocation),
    ("VentilationRate", SpotExhaust.VentilationRate),
    ("RequiredVentilationRate", SpotExhaust.RequiredVentilationRate),
    ("VentilationControlMethods", SpotExhaust.VentilationControlMethods),
    ("MakeupAirSourceID", SpotExhaust.MakeupAirSourceID),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("DutyCycle", DutyCycle),
    ("SystemPerformanceRatio", SystemPerformanceRatio),
    ("ThirdPartyCertification", ThirdPartyCertification),
]
SpotExhaust.VentilationControlMethods.element_children = [
    ("VentilationControlMethod", VentilationControlMethod),
]

# OtherHVACSystemType.OtherHVACType.NaturalVentilation
class NaturalVentilation(BSElement):
    class VentilationControlMethods(BSElement):
        """List of ventilation control methods."""


NaturalVentilation.element_children = [
    ("NaturalVentilationRate", NaturalVentilationRate),
    ("NaturalVentilationMethod", NaturalVentilationMethod),
    ("VentilationControlMethods", NaturalVentilation.VentilationControlMethods),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("DutyCycle", DutyCycle),
]
NaturalVentilation.VentilationControlMethods.element_children = [
    ("VentilationControlMethod", VentilationControlMethod),
]

# LightingSystemType.LampType.Incandescent
class Incandescent(BSElement):
    class LampLabel(BSElement):
        """Specific lamp subtype used in the luminaire."""

        element_type = "xs:string"
        element_enumerations = [
            "A19",
            "A21",
            "G16C",
            "G25M",
            "G40M",
            "MR16",
            "PAR16",
            "PAR20",
            "PAR30",
            "PAR38",
            "PS-Series",
            "R20",
            "R30",
            "R40",
            "TC",
            "TM",
            "Other",
            "Unknown",
        ]


Incandescent.element_children = [
    ("LampLabel", Incandescent.LampLabel),
]

# LightingSystemType.LampType.LinearFluorescent
class LinearFluorescent(BSElement):
    class LampLabel(BSElement):
        """Specific lamp subtype used in the luminaire."""

        element_type = "xs:string"
        element_enumerations = [
            "Super T8",
            "T12",
            "T12HO",
            "T5",
            "T5HO",
            "T8",
            "T12U",
            "T8U",
            "Other",
            "Unknown",
        ]


LinearFluorescent.element_children = [
    ("LampLabel", LinearFluorescent.LampLabel),
    ("LampLength", LampLength),
]

# LightingSystemType.LampType.CompactFluorescent
class CompactFluorescent(BSElement):
    class LampLabel(BSElement):
        """Specific lamp subtype used in the luminaire."""

        element_type = "xs:string"
        element_enumerations = [
            "2D",
            "A-series",
            "Circline",
            "Spiral",
            "Other",
            "Unknown",
        ]


CompactFluorescent.element_children = [
    ("LampLabel", CompactFluorescent.LampLabel),
    ("FluorescentStartType", FluorescentStartType),
]

# LightingSystemType.LampType.Halogen
class Halogen(BSElement):
    class LampLabel(BSElement):
        """Specific lamp subtype used in the luminaire."""

        element_type = "xs:string"
        element_enumerations = [
            "A-shape",
            "BR30",
            "BR40",
            "MR11",
            "MR16",
            "MR8",
            "PAR20",
            "PAR30",
            "PAR38",
            "Pin Base",
            "R20",
            "Other",
            "Unknown",
        ]

    class TransformerNeeded(BSElement):
        """True if the lamps require a transformer to lower the voltage (such as halogen or LEDs)."""

        element_type = "xs:boolean"


Halogen.element_children = [
    ("LampLabel", Halogen.LampLabel),
    ("TransformerNeeded", Halogen.TransformerNeeded),
]

# LightingSystemType.LampType.HighIntensityDischarge
class HighIntensityDischarge(BSElement):
    class LampLabel(BSElement):
        """Specific lamp subtype used in the luminaire."""

        element_type = "xs:string"
        element_enumerations = [
            "Sodium Vapor High Pressure",
            "Sodium Vapor Low Pressure",
            "Metal Halide",
            "Mercury Vapor",
            "Other",
            "Unknown",
        ]


HighIntensityDischarge.element_children = [
    ("LampLabel", HighIntensityDischarge.LampLabel),
    ("MetalHalideStartType", MetalHalideStartType),
]

# LightingSystemType.LampType.SolidStateLighting
class SolidStateLighting(BSElement):
    class LampLabel(BSElement):
        """Specific lamp subtype used in the luminaire."""

        element_type = "xs:string"
        element_enumerations = ["LED", "Other"]

    class TransformerNeeded(BSElement):
        """True if the lamps require a transformer to lower the voltage (such as halogen or LEDs)."""

        element_type = "xs:boolean"


SolidStateLighting.element_children = [
    ("LampLabel", SolidStateLighting.LampLabel),
    ("TransformerNeeded", SolidStateLighting.TransformerNeeded),
]

# LightingSystemType.LampType.Neon
class Neon(NeonType):
    pass


# LightingSystemType.LampType.Plasma
class Plasma(PlasmaType):
    pass


# LightingSystemType.LampType.Photoluminescent
class Photoluminescent(PhotoluminescentType):
    pass


# LightingSystemType.LampType.SelfLuminous
class SelfLuminous(SelfLuminousType):
    pass


# LightingSystemType.DimmingCapability.MinimumDimmingLightFraction
class MinimumDimmingLightFraction(BoundedDecimalZeroToOneWithSourceAttribute):
    """Minimum light output of controlled lighting when fully dimmed. Minimum light fraction = (Minimum light output) / (Rated light output). (0-1) (fraction)"""


# LightingSystemType.DimmingCapability.MinimumDimmingPowerFraction
class MinimumDimmingPowerFraction(BoundedDecimalZeroToOneWithSourceAttribute):
    """The minimum power fraction when controlled lighting is fully dimmed. Minimum power fraction = (Minimum power) / (Full rated power). (0-1) (fraction)"""


# DomesticHotWaterSystemType.Recirculation
class Recirculation(BSElement):
    """If exists then recirculation loops are used to minimize wait times for hot water."""

    class PipeInsulationThickness(BSElement):
        """Defines how thick insulation on pipes in a heating, cooling, water heating system is. (in.)"""

        element_type = "xs:decimal"

    class PipeLocation(BSElement):
        """Percent of pipe length in conditioned space. (0-100) (%)"""

        element_type = "xs:decimal"


Recirculation.element_children = [
    ("RecirculationLoopCount", RecirculationLoopCount),
    ("RecirculationFlowRate", RecirculationFlowRate),
    ("RecirculationControlType", RecirculationControlType),
    ("PipeInsulationThickness", Recirculation.PipeInsulationThickness),
    ("PipeLocation", Recirculation.PipeLocation),
    ("RecirculationEnergyLossRate", RecirculationEnergyLossRate),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.HeatPump.RatedHeatPumpSensibleHeatRatio
class RatedHeatPumpSensibleHeatRatio(BoundedDecimalZeroToOneWithSourceAttribute):
    """The fraction of total energy transfer between the evaporator coil and air that is associated with sensible capacity (change in air temperature) expressed as a dimensionless value, and at the rated conditions prescribed for this system. (0-1) (fraction)"""


# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.SpaceHeatingSystem
class SpaceHeatingSystem(BSElement):
    pass


SpaceHeatingSystem.element_children = [
    ("HeatingPlantID", HeatingPlantID),
]

# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.RefrigerationCompressor.CompressorUnloader
class CompressorUnloader(BSElement):
    """If exists then a device is used for controlling compressor capacity by rendering one or more cylinders ineffective."""


CompressorUnloader.element_children = [
    ("CompressorUnloaderStages", CompressorUnloaderStages),
]

# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem.RefrigerationCompressor
class RefrigerationCompressor(BSElement):
    pass


RefrigerationCompressor.element_attributes = [
    "ID",  # ID
]
RefrigerationCompressor.element_children = [
    ("RefrigerationCompressorType", RefrigerationCompressorType),
    ("CompressorUnloader", CompressorUnloader),
    ("DesuperheatValve", DesuperheatValve),
    ("CrankcaseHeater", CrankcaseHeater),
]

# RefrigerationSystemType.RefrigerationSystemCategory.CentralRefrigerationSystem
class CentralRefrigerationSystem(BSElement):
    class CondenserPlantIDs(BSElement):
        class CondenserPlantID(BSElement):
            """ID number of the CondenserPlant serving as the source for this cooling system."""


CentralRefrigerationSystem.element_children = [
    ("NetRefrigerationCapacity", NetRefrigerationCapacity),
    ("TotalHeatRejection", TotalHeatRejection),
    ("Refrigerant", Refrigerant),
    ("SuctionVaporTemperature", SuctionVaporTemperature),
    ("NumberOfRefrigerantReturnLines", NumberOfRefrigerantReturnLines),
    ("EvaporatorPressureRegulators", EvaporatorPressureRegulators),
    ("RefrigerantSubcooler", RefrigerantSubcooler),
    ("CaseReturnLineDiameter", CaseReturnLineDiameter),
    ("RefrigerationCompressor", RefrigerationCompressor),
    ("CondenserPlantIDs", CentralRefrigerationSystem.CondenserPlantIDs),
]
CentralRefrigerationSystem.CondenserPlantIDs.element_children = [
    ("CondenserPlantID", CentralRefrigerationSystem.CondenserPlantIDs.CondenserPlantID),
]
CentralRefrigerationSystem.CondenserPlantIDs.CondenserPlantID.element_attributes = [
    "IDref",  # IDREF
]

# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit.AntiSweatHeaters
class AntiSweatHeaters(BSElement):
    """If exists then refrigerated cases include anti-sweat heaters."""


AntiSweatHeaters.element_children = [
    ("AntiSweatHeaterPower", AntiSweatHeaterPower),
    ("AntiSweatHeaterControls", AntiSweatHeaterControls),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
]

# RefrigerationSystemType.RefrigerationSystemCategory.RefrigerationUnit
class RefrigerationUnit(BSElement):
    class LampPower(BSElement):
        """Average power used by lamps in refrigerated cases. (W)"""

        element_type = "xs:decimal"


RefrigerationUnit.element_children = [
    ("RefrigerationUnitType", RefrigerationUnitType),
    ("DoorConfiguration", DoorConfiguration),
    ("RefrigeratedCaseDoors", RefrigeratedCaseDoors),
    ("CaseDoorOrientation", CaseDoorOrientation),
    ("DefrostingType", DefrostingType),
    ("LampPower", RefrigerationUnit.LampPower),
    ("RefrigerationUnitSize", RefrigerationUnitSize),
    ("AntiSweatHeaters", AntiSweatHeaters),
    ("RefrigerationEnergy", RefrigerationEnergy),
]

# LaundrySystemType.LaundryType.Washer
class Washer(BSElement):
    class ClothesWasherModifiedEnergyFactor(BSElement):
        """Modified Energy Factor (MEF) is the energy performance metric for ENERGY STAR qualified clothes washers and all clothes washers as of February 1, 2013. MEF is the quotient of the capacity of the clothes container, C, divided by the total clothes washer energy consumption per cycle, with such energy consumption expressed as the sum of the machine electrical energy consumption, M, the hot water energy consumption, E, and the energy required for removal of the remaining moisture in the wash load, D. The higher MEF, the more efficient the clothes washer. The equation is: MEF = C/(M + E + D)."""

        element_type = "xs:decimal"

    class ClothesWasherWaterFactor(BSElement):
        """Water Factor (WF) is the quotient of the total weighted per-cycle water consumption, Q, divided by the capacity of the clothes washer, C. The lower the value, the more water efficient the clothes washer is. The equation is: WF = Q/C. WF is the ENERGY STAR water performance metric that allows the comparison of clothes washer water consumption independent of clothes washer capacity. (gal/cycle/ft3)"""

        element_type = "xs:decimal"

    class ClothesWasherCapacity(BSElement):
        """Volume of clothes washer tub. (ft3)"""

        element_type = "xs:decimal"


Washer.element_children = [
    ("ClothesWasherClassification", ClothesWasherClassification),
    ("ClothesWasherLoaderType", ClothesWasherLoaderType),
    ("ClothesWasherModifiedEnergyFactor", Washer.ClothesWasherModifiedEnergyFactor),
    ("ClothesWasherWaterFactor", Washer.ClothesWasherWaterFactor),
    ("ClothesWasherCapacity", Washer.ClothesWasherCapacity),
]

# LaundrySystemType.LaundryType.Dryer
class Dryer(BSElement):
    class DryerElectricEnergyUsePerLoad(BSElement):
        """Measure of dryer efficiency based on electricity. (kWh/load)"""

        element_type = "xs:decimal"

    class DryerGasEnergyUsePerLoad(BSElement):
        """Measure of dryer efficiency based on natural gas. (Btu/load)"""

        element_type = "xs:decimal"


Dryer.element_children = [
    ("DryerType", DryerType),
    ("DryerElectricEnergyUsePerLoad", Dryer.DryerElectricEnergyUsePerLoad),
    ("DryerGasEnergyUsePerLoad", Dryer.DryerGasEnergyUsePerLoad),
]

# LaundrySystemType.LaundryType.Combination
class Combination(BSElement):
    class ClothesWasherModifiedEnergyFactor(BSElement):
        """Modified Energy Factor (MEF) is the energy performance metric for ENERGY STAR qualified clothes washers and all clothes washers as of February 1, 2013. MEF is the quotient of the capacity of the clothes container, C, divided by the total clothes washer energy consumption per cycle, with such energy consumption expressed as the sum of the machine electrical energy consumption, M, the hot water energy consumption, E, and the energy required for removal of the remaining moisture in the wash load, D. The higher MEF, the more efficient the clothes washer. The equation is: MEF = C/(M + E + D)."""

        element_type = "xs:decimal"

    class ClothesWasherWaterFactor(BSElement):
        """Water Factor (WF) is the quotient of the total weighted per-cycle water consumption, Q, divided by the capacity of the clothes washer, C. The lower the value, the more water efficient the clothes washer is. The equation is: WF = Q/C. WF is the ENERGY STAR water performance metric that allows the comparison of clothes washer water consumption independent of clothes washer capacity. (gal/cycle/ft3)"""

        element_type = "xs:decimal"

    class ClothesWasherCapacity(BSElement):
        """Volume of clothes washer tub. (ft3)"""

        element_type = "xs:decimal"

    class DryerElectricEnergyUsePerLoad(BSElement):
        """Measure of dryer efficiency based on electricity. (kWh/load)"""

        element_type = "xs:decimal"

    class DryerGasEnergyUsePerLoad(BSElement):
        """Measure of dryer efficiency based on natural gas. (Btu/load)"""

        element_type = "xs:decimal"


Combination.element_children = [
    ("WasherDryerType", WasherDryerType),
    ("ClothesWasherClassification", ClothesWasherClassification),
    ("ClothesWasherLoaderType", ClothesWasherLoaderType),
    (
        "ClothesWasherModifiedEnergyFactor",
        Combination.ClothesWasherModifiedEnergyFactor,
    ),
    ("ClothesWasherWaterFactor", Combination.ClothesWasherWaterFactor),
    ("ClothesWasherCapacity", Combination.ClothesWasherCapacity),
    ("DryerType", DryerType),
    ("DryerElectricEnergyUsePerLoad", Combination.DryerElectricEnergyUsePerLoad),
    ("DryerGasEnergyUsePerLoad", Combination.DryerGasEnergyUsePerLoad),
]

# FanSystemType.FanPowerMinimumRatio
class FanPowerMinimumRatio(BoundedDecimalZeroToOneWithSourceAttribute):
    """The minimum power draw of the fan, expressed as a ratio of the full load fan power. (0-1) (fraction)"""


# WallSystemType.ExteriorWallConstruction
class ExteriorWallConstruction(EnvelopeConstructionType):
    """The general description of the main structural construction method used for an opaque surface."""


# WallSystemType.ExteriorWallFinish
class ExteriorWallFinish(Finish):
    """The final material applied to a surface, either interior or exterior. Some structural components don't have an exterior finish, such as unfinished poured concrete."""


# WallSystemType.ExteriorWallColor
class ExteriorWallColor(Color):
    """Color of a material or component. Can be applied to opaque surfaces, materials, and so forth."""


# WallSystemType.WallFramingMaterial
class WallFramingMaterial(FramingMaterial):
    """The material used to create the structural integrity in an opaque surface. In many cases the framing material is not continuous across the construction."""


# WallSystemType.WallInsulations.WallInsulation.WallInsulationMaterial
class WallInsulationMaterial(InsulationMaterialType):
    """Material used for the structural component of the surface."""


# WallSystemType.WallInsulations.WallInsulation
class WallInsulation(BSElement):
    pass


WallInsulation.element_children = [
    ("WallInsulationApplication", WallInsulationApplication),
    ("WallInsulationMaterial", WallInsulationMaterial),
    ("WallInsulationThickness", WallInsulationThickness),
    ("WallInsulationContinuity", WallInsulationContinuity),
    ("WallInsulationCondition", WallInsulationCondition),
    ("WallInsulationLocation", WallInsulationLocation),
    ("WallInsulationRValue", WallInsulationRValue),
]

# CeilingSystemType.CeilingInsulations.CeilingInsulation
class CeilingInsulation(BSElement):
    pass


CeilingInsulation.element_children = [
    ("CeilingInsulationApplication", CeilingInsulationApplication),
    ("CeilingInsulationMaterial", CeilingInsulationMaterial),
    ("CeilingInsulationThickness", CeilingInsulationThickness),
    ("CeilingInsulationContinuity", CeilingInsulationContinuity),
    ("CeilingInsulationCondition", CeilingInsulationCondition),
]

# RoofSystemType.RoofInsulations.RoofInsulation
class RoofInsulation(BSElement):
    pass


RoofInsulation.element_children = [
    ("RoofInsulationApplication", RoofInsulationApplication),
    ("RoofInsulationMaterial", RoofInsulationMaterial),
    ("RoofInsulationThickness", RoofInsulationThickness),
    ("RoofInsulationContinuity", RoofInsulationContinuity),
    ("RoofInsulationCondition", RoofInsulationCondition),
    ("RoofInsulationRValue", RoofInsulationRValue),
]

# FenestrationSystemType.FenestrationType.Window.LightShelves
class LightShelves(BSElement):
    """If exists then light shelves are used with this window group, otherwise false."""


LightShelves.element_children = [
    ("LightShelfDistanceFromTop", LightShelfDistanceFromTop),
    ("LightShelfExteriorProtrusion", LightShelfExteriorProtrusion),
    ("LightShelfInteriorProtrusion", LightShelfInteriorProtrusion),
]

# FenestrationSystemType.FenestrationType.Window
class Window(BSElement):
    class AssemblyType(BSElement):
        """Window assembly type."""

        element_type = "xs:string"
        element_enumerations = ["Double Hung"]


Window.element_children = [
    ("WindowLayout", WindowLayout),
    ("WindowOrientation", WindowOrientation),
    ("WindowSillHeight", WindowSillHeight),
    ("AssemblyType", Window.AssemblyType),
    ("WindowHeight", WindowHeight),
    ("WindowWidth", WindowWidth),
    ("WindowHorizontalSpacing", WindowHorizontalSpacing),
    ("ExteriorShadingType", ExteriorShadingType),
    ("OverhangHeightAboveWindow", OverhangHeightAboveWindow),
    ("OverhangProjection", OverhangProjection),
    ("VerticalFinDepth", VerticalFinDepth),
    ("DistanceBetweenVerticalFins", DistanceBetweenVerticalFins),
    ("VerticalEdgeFinOnly", VerticalEdgeFinOnly),
    ("LightShelves", LightShelves),
    ("InteriorShadingType", InteriorShadingType),
]

# FenestrationSystemType.FenestrationType.Skylight
class Skylight(BSElement):
    class AssemblyType(BSElement):
        """Skylight assembly type."""

        element_type = "xs:string"
        element_enumerations = ["Curbed Mounted"]


Skylight.element_children = [
    ("SkylightLayout", SkylightLayout),
    ("AssemblyType", Skylight.AssemblyType),
    ("SkylightPitch", SkylightPitch),
    ("SkylightWindowTreatments", SkylightWindowTreatments),
    ("SkylightSolarTube", SkylightSolarTube),
]

# FenestrationSystemType.FenestrationType.Door.DoorGlazedAreaFraction
class DoorGlazedAreaFraction(BoundedDecimalZeroToOneWithSourceAttribute):
    """Fraction of door area that is glazed. (0-1) (fraction)"""


# FenestrationSystemType.FenestrationType.Door
class Door(BSElement):
    pass


Door.element_children = [
    ("ExteriorDoorType", ExteriorDoorType),
    ("Vestibule", Vestibule),
    ("DoorOperation", DoorOperation),
    ("DoorGlazedAreaFraction", DoorGlazedAreaFraction),
]

# FoundationSystemType.GroundCouplings.GroundCoupling.SlabOnGrade
class SlabOnGrade(BSElement):
    class SlabArea(BSElement):
        """Area of slab-on-grade, basement slab, or other floor over unconditioned space. (ft2)"""

        element_type = "xs:decimal"

    class SlabPerimeter(BSElement):
        """Total perimeter of slab-on-grade or basement slab. (ft)"""

        element_type = "xs:decimal"

    class SlabExposedPerimeter(BSElement):
        """Perimeter of slab-on-grade or basement slab exposed to outside air conditions. (ft)"""

        element_type = "xs:decimal"

    class SlabInsulationThickness(BSElement):
        """Thickness of insulation around perimeter or under slab. (in.)"""

        element_type = "xs:decimal"

    class SlabInsulationCondition(InsulationCondition):
        pass


SlabOnGrade.element_children = [
    ("SlabInsulationOrientation", SlabInsulationOrientation),
    ("SlabArea", SlabOnGrade.SlabArea),
    ("SlabPerimeter", SlabOnGrade.SlabPerimeter),
    ("SlabExposedPerimeter", SlabOnGrade.SlabExposedPerimeter),
    ("SlabInsulationThickness", SlabOnGrade.SlabInsulationThickness),
    ("SlabRValue", SlabRValue),
    ("SlabUFactor", SlabUFactor),
    ("SlabInsulationCondition", SlabOnGrade.SlabInsulationCondition),
    ("SlabHeating", SlabHeating),
]

# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Ventilated
class Ventilated(BSElement):
    pass


Ventilated.element_children = [
    ("FloorInsulationThickness", FloorInsulationThickness),
    ("FloorInsulationCondition", FloorInsulationCondition),
    ("FloorRValue", FloorRValue),
    ("FloorUFactor", FloorUFactor),
    ("FloorFramingSpacing", FloorFramingSpacing),
    ("FloorFramingDepth", FloorFramingDepth),
    ("FloorFramingFactor", FloorFramingFactor),
]

# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting.Unventilated
class Unventilated(BSElement):
    class FoundationWallConstruction(EnvelopeConstructionType):
        """Basement or crawlspace wall construction."""

    class FoundationHeightAboveGrade(BSElement):
        """Height of the building foundation that is above the ground. (ft)"""

        element_type = "xs:decimal"

    class FoundationWallInsulationThickness(BSElement):
        """Thickness of insulation at basement or crawlspace wall. (in.)"""

        element_type = "xs:decimal"

    class FoundationWallRValue(BSElement):
        """(Also known as thermal resistance), quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include the interior and exterior air film coefficients. (hr-ft2-F/Btu)"""

        element_type = "xs:decimal"

    class FoundationWallUFactor(BSElement):
        """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

        element_type = "xs:decimal"

    class FoundationWallInsulationCondition(InsulationCondition):
        pass


Unventilated.element_children = [
    ("FoundationWallConstruction", Unventilated.FoundationWallConstruction),
    ("FoundationHeightAboveGrade", Unventilated.FoundationHeightAboveGrade),
    (
        "FoundationWallInsulationThickness",
        Unventilated.FoundationWallInsulationThickness,
    ),
    ("FoundationWallRValue", Unventilated.FoundationWallRValue),
    ("FoundationWallUFactor", Unventilated.FoundationWallUFactor),
    ("FoundationWallInsulationContinuity", FoundationWallInsulationContinuity),
    (
        "FoundationWallInsulationCondition",
        Unventilated.FoundationWallInsulationCondition,
    ),
]

# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace.CrawlspaceVenting
class CrawlspaceVenting(BSElement):
    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


CrawlspaceVenting.element_children = [
    ("Ventilated", Ventilated),
    ("Unventilated", Unventilated),
    ("Other", CrawlspaceVenting.Other),
    ("Unknown", CrawlspaceVenting.Unknown),
]

# FoundationSystemType.GroundCouplings.GroundCoupling.Crawlspace
class Crawlspace(BSElement):
    pass


Crawlspace.element_children = [
    ("CrawlspaceVenting", CrawlspaceVenting),
]

# FoundationSystemType.GroundCouplings.GroundCoupling.Basement
class Basement(BSElement):
    class FoundationWallConstruction(EnvelopeConstructionType):
        """Basement or crawlspace wall construction."""

    class FoundationHeightAboveGrade(BSElement):
        """Height of the building foundation that is above the ground. (ft)"""

        element_type = "xs:decimal"

    class FoundationWallInsulationThickness(BSElement):
        """Thickness of insulation at basement or crawlspace wall. (in.)"""

        element_type = "xs:decimal"

    class FoundationWallRValue(BSElement):
        """Also known as thermal resistance, quantity determined by the temperature difference, at steady state, between two defined surfaces of a material or construction that induces a unit heat flow rate through unit area (R = ΔT/q). R-value is the reciprocal of thermal conductance. A unit of thermal resistance used for comparing insulating values of different materials, for the specific thickness of the material. The higher the R-value number, a material, the greater its insulating properties and the slower the heat flow through it. This R-value does not include the interior and exterior air film coefficients. (hr-ft2-F/Btu)"""

        element_type = "xs:decimal"

    class FoundationWallUFactor(BSElement):
        """The thermal transmission in unit time through a unit area of a particular body or assembly, including its boundary films, divided by the difference between the environmental temperatures on either side of the body or assembly. Note that the U-factor for a construction assembly, including fenestration, includes the interior and exterior film coefficients (the boundary films referenced above). (Btu/hr·ft2·°F)"""

        element_type = "xs:decimal"

    class FoundationWallInsulationCondition(InsulationCondition):
        pass

    class SlabArea(BSElement):
        """Area of slab-on-grade, basement slab, or other floor over unconditioned space. (ft2)"""

        element_type = "xs:decimal"

    class SlabPerimeter(BSElement):
        """Total perimeter of slab-on-grade or basement slab. (ft)"""

        element_type = "xs:decimal"

    class SlabExposedPerimeter(BSElement):
        """Perimeter of slab-on-grade or basement slab exposed to outside air conditions. (ft)"""

        element_type = "xs:decimal"

    class SlabInsulationThickness(BSElement):
        """Thickness of insulation around perimeter or under slab. (in.)"""

        element_type = "xs:decimal"

    class SlabInsulationCondition(InsulationCondition):
        pass


Basement.element_children = [
    ("BasementConditioning", BasementConditioning),
    ("FoundationWallConstruction", Basement.FoundationWallConstruction),
    ("FoundationHeightAboveGrade", Basement.FoundationHeightAboveGrade),
    ("FoundationWallInsulationThickness", Basement.FoundationWallInsulationThickness),
    ("FoundationWallRValue", Basement.FoundationWallRValue),
    ("FoundationWallUFactor", Basement.FoundationWallUFactor),
    ("FoundationWallInsulationContinuity", FoundationWallInsulationContinuity),
    ("FoundationWallInsulationCondition", Basement.FoundationWallInsulationCondition),
    ("SlabInsulationOrientation", SlabInsulationOrientation),
    ("SlabArea", Basement.SlabArea),
    ("SlabPerimeter", Basement.SlabPerimeter),
    ("SlabExposedPerimeter", Basement.SlabExposedPerimeter),
    ("SlabInsulationThickness", Basement.SlabInsulationThickness),
    ("SlabInsulationCondition", Basement.SlabInsulationCondition),
    ("SlabHeating", SlabHeating),
]

# FoundationSystemType.GroundCouplings.GroundCoupling
class GroundCoupling(BSElement):
    """The manner in which the building is connected to the ground."""

    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


GroundCoupling.element_children = [
    ("SlabOnGrade", SlabOnGrade),
    ("Crawlspace", Crawlspace),
    ("Basement", Basement),
    ("Other", GroundCoupling.Other),
    ("Unknown", GroundCoupling.Unknown),
]

# ProcessGasElectricLoadType.HeatGainFraction
class HeatGainFraction(BoundedDecimalZeroToOneWithSourceAttribute):
    """Fraction of installed power that results in heat gain to the space. (0-1) (fraction)"""


# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Storage
class Storage(BSElement):
    pass


Storage.element_children = [
    ("EnergyStorageTechnology", EnergyStorageTechnology),
    ("ThermalMedium", ThermalMedium),
]

# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType.PV
class PV(BSElement):
    pass


PV.element_children = [
    (
        "PhotovoltaicSystemNumberOfModulesPerArray",
        PhotovoltaicSystemNumberOfModulesPerArray,
    ),
    ("PhotovoltaicSystemNumberOfArrays", PhotovoltaicSystemNumberOfArrays),
    ("PhotovoltaicSystemMaximumPowerOutput", PhotovoltaicSystemMaximumPowerOutput),
    ("PhotovoltaicSystemInverterEfficiency", PhotovoltaicSystemInverterEfficiency),
    ("PhotovoltaicSystemArrayAzimuth", PhotovoltaicSystemArrayAzimuth),
    (
        "PhotovoltaicSystemRackingSystemTiltAngleMin",
        PhotovoltaicSystemRackingSystemTiltAngleMin,
    ),
    (
        "PhotovoltaicSystemRackingSystemTiltAngleMax",
        PhotovoltaicSystemRackingSystemTiltAngleMax,
    ),
    ("PhotovoltaicSystemLocation", PhotovoltaicSystemLocation),
    ("PhotovoltaicModuleRatedPower", PhotovoltaicModuleRatedPower),
    ("PhotovoltaicModuleLength", PhotovoltaicModuleLength),
    ("PhotovoltaicModuleWidth", PhotovoltaicModuleWidth),
]

# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation.OnsiteGenerationType
class OnsiteGenerationType(BSElement):
    """Identifies whether the onsite generation is provided by a photovoltaic system or by another technology."""

    class Other(BSElement):
        pass


OnsiteGenerationType.element_children = [
    ("PV", PV),
    ("Other", OnsiteGenerationType.Other),
]
OnsiteGenerationType.Other.element_children = [
    ("OtherEnergyGenerationTechnology", OtherEnergyGenerationTechnology),
    ("OutputResourceType", OutputResourceType),
]

# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType.Generation
class Generation(BSElement):
    pass


Generation.element_children = [
    ("OnsiteGenerationType", OnsiteGenerationType),
    ("ExternalPowerSupply", ExternalPowerSupply),
]

# WaterUseType.WaterFixtureFractionHotWater
class WaterFixtureFractionHotWater(BoundedDecimalZeroToOneWithSourceAttribute):
    """Average fraction of water use for this application that is drawn from the hot water system. (0-1) (fraction)"""


# CalculationMethodType.Modeled
class Modeled(BSElement):
    """The 'Modeled' calculation method is used to represent a scenario in which a building energy modeling software was used to derive data represented by this scenario type."""


Modeled.element_children = [
    ("SoftwareProgramUsed", SoftwareProgramUsed),
    ("SoftwareProgramVersion", SoftwareProgramVersion),
    ("WeatherDataType", WeatherDataType),
    ("SimulationCompletionStatus", SimulationCompletionStatus),
]

# CalculationMethodType.Estimated
class Estimated(EstimatedType):
    """The 'Estimated' calculation method is used to represent a scenario in which a guess or judgement call was used to derive data represented by this scenario type."""


# CalculationMethodType.EngineeringCalculation
class EngineeringCalculation(EngineeringCalculationType):
    """The 'EngineeringCalculation' calculation method is used to represent a scenario in which a spreadsheet style calculation, or some other modeling approach that is not full building energy modeling, was used to derive data represented by this scenario type."""


# CalculationMethodType.Measured.MeasuredEnergySource.UtilityBills
class UtilityBills(BSElement):
    class UtilityMeterNumber(BSElement):
        """Unique identification number for the meter."""

        element_type = "xs:string"

    class UtilityAccountNumber(BSElement):
        """Unique account number designated by the utility."""

        element_type = "xs:string"

    class UtilityBillpayer(BSElement):
        """Organization that is responsible for paying the bills associated with this meter."""

        element_type = "xs:string"


UtilityBills.element_children = [
    ("UtilityMeterNumber", UtilityBills.UtilityMeterNumber),
    ("UtilityAccountNumber", UtilityBills.UtilityAccountNumber),
    ("UtilityBillpayer", UtilityBills.UtilityBillpayer),
]

# CalculationMethodType.Measured.MeasuredEnergySource
class MeasuredEnergySource(BSElement):
    class Other(OtherType):
        pass


MeasuredEnergySource.element_children = [
    ("UtilityBills", UtilityBills),
    ("DirectMeasurement", DirectMeasurement),
    ("Other", MeasuredEnergySource.Other),
]

# LinkedPremisesOrSystem.System
class System(BSElement):
    class LinkedSystemID(BSElement):
        """ID numbers of associated systems."""


System.element_children = [
    ("LinkedSystemID", System.LinkedSystemID),
]
System.LinkedSystemID.element_attributes = [
    "IDref",  # IDREF
]

# Address.StreetAddressDetail.Simplified
class Simplified(BSElement):
    class StreetAdditionalInfo(BSElement):
        """Information other than a prefix or suffix for the street portion of a postal address."""

        element_type = "xs:string"


Simplified.element_children = [
    ("StreetAddress", StreetAddress),
    ("StreetAdditionalInfo", Simplified.StreetAdditionalInfo),
]

# Address.StreetAddressDetail.Complex
class Complex(BSElement):
    class StreetAdditionalInfo(BSElement):
        """Information other than a prefix or suffix for the street portion of a postal address."""

        element_type = "xs:string"


Complex.element_children = [
    ("StreetNumberPrefix", StreetNumberPrefix),
    ("StreetNumberNumeric", StreetNumberNumeric),
    ("StreetNumberSuffix", StreetNumberSuffix),
    ("StreetDirPrefix", StreetDirPrefix),
    ("StreetName", StreetName),
    ("StreetAdditionalInfo", Complex.StreetAdditionalInfo),
    ("StreetSuffix", StreetSuffix),
    ("StreetSuffixModifier", StreetSuffixModifier),
    ("StreetDirSuffix", StreetDirSuffix),
    ("SubaddressType", SubaddressType),
    ("SubaddressIdentifier", SubaddressIdentifier),
]

# Address.StreetAddressDetail
class StreetAddressDetail(BSElement):
    """Choice of simplified or more complex address format."""


StreetAddressDetail.element_children = [
    ("Simplified", Simplified),
    ("Complex", Complex),
]

# PremisesIdentifiers.PremisesIdentifier
class PremisesIdentifier(BSElement):
    pass


PremisesIdentifier.element_children = [
    ("IdentifierLabel", IdentifierLabel),
    ("IdentifierCustomName", IdentifierCustomName),
    ("IdentifierValue", IdentifierValue),
]

# TypicalOccupantUsages.TypicalOccupantUsage
class TypicalOccupantUsage(BSElement):
    pass


TypicalOccupantUsage.element_children = [
    ("TypicalOccupantUsageValue", TypicalOccupantUsageValue),
    ("TypicalOccupantUsageUnits", TypicalOccupantUsageUnits),
]

# UserDefinedFields.UserDefinedField
class UserDefinedField(BSElement):
    pass


UserDefinedField.element_children = [
    ("FieldName", FieldName),
    ("FieldValue", FieldValue),
]

# FloorAreas.FloorArea.ExcludedSectionIDs
class ExcludedSectionIDs(BSElement):
    """Links to Sections not included in the floor area calculation."""


ExcludedSectionIDs.element_children = [
    ("ExcludedSectionID", ExcludedSectionID),
]

# FloorAreas.FloorArea
class FloorArea(BSElement):
    class Story(BSElement):
        """The story of the given floor area type."""

        element_type = "xs:int"


FloorArea.element_children = [
    ("FloorAreaType", FloorAreaType),
    ("FloorAreaCustomName", FloorAreaCustomName),
    ("FloorAreaValue", FloorAreaValue),
    ("FloorAreaPercentage", FloorAreaPercentage),
    ("Story", FloorArea.Story),
    ("ExcludedSectionIDs", ExcludedSectionIDs),
]

# OccupancyLevels.OccupancyLevel
class OccupancyLevel(BSElement):
    pass


OccupancyLevel.element_children = [
    ("OccupantType", OccupantType),
    ("OccupantQuantityType", OccupantQuantityType),
    ("OccupantQuantity", OccupantQuantity),
]

# EnergyUseByFuelTypes.EnergyUseByFuelType
class EnergyUseByFuelType(BSElement):
    class EnergyUse(BSElement):
        element_type = "xs:decimal"


EnergyUseByFuelType.element_children = [
    ("PrimaryFuel", PrimaryFuel),
    ("EnergyUse", EnergyUseByFuelType.EnergyUse),
]

# EnergyUseByFuelTypes
class EnergyUseByFuelTypes(BSElement):
    pass


EnergyUseByFuelTypes.element_children = [
    ("EnergyUseByFuelType", EnergyUseByFuelType),
]

# AssetScoreData
class AssetScoreData(BSElement):
    """A facility's Commercial Building Energy Asset Score, and optional Site/Source energy use by fuel type."""

    class SiteEnergyUse(BSElement):
        pass

    class SourceEnergyUse(BSElement):
        class SourceEnergyUseIntensity(BSElement):
            """The Source Energy Use divided by the premises gross floor area. (kBtu/ft2)"""

            element_type = "xs:decimal"


AssetScoreData.element_children = [
    ("Score", Score),
    ("SiteEnergyUse", AssetScoreData.SiteEnergyUse),
    ("SourceEnergyUse", AssetScoreData.SourceEnergyUse),
]
AssetScoreData.SiteEnergyUse.element_children = [
    ("EnergyUseByFuelTypes", EnergyUseByFuelTypes),
]
AssetScoreData.SourceEnergyUse.element_children = [
    ("EnergyUseByFuelTypes", EnergyUseByFuelTypes),
    (
        "SourceEnergyUseIntensity",
        AssetScoreData.SourceEnergyUse.SourceEnergyUseIntensity,
    ),
]

# AssetScore.WholeBuilding.EnergyUseByEndUses.EnergyUseByEndUse
class EnergyUseByEndUse(BSElement):
    class EnergyUse(BSElement):
        element_type = "xs:decimal"

    class EndUse(EndUse):
        """End use for which data is included."""


EnergyUseByEndUse.element_children = [
    ("EnergyUse", EnergyUseByEndUse.EnergyUse),
    ("EndUse", EnergyUseByEndUse.EndUse),
]

# AssetScore.WholeBuilding.EnergyUseByEndUses
class EnergyUseByEndUses(BSElement):
    pass


EnergyUseByEndUses.element_children = [
    ("EnergyUseByEndUse", EnergyUseByEndUse),
]

# AssetScore.WholeBuilding.Rankings.Ranking.Type
class Type(BSElement):
    pass


Type.element_children = [
    ("SystemsType", SystemsType),
    ("EnvelopeType", EnvelopeType),
]

# AssetScore.WholeBuilding.Rankings.Ranking.Rank
class Rank(RankType):
    pass


# AssetScore.WholeBuilding.Rankings.Ranking
class Ranking(BSElement):
    pass


Ranking.element_children = [
    ("Type", Type),
    ("Rank", Rank),
]

# AssetScore.WholeBuilding.Rankings
class Rankings(BSElement):
    pass


Rankings.element_children = [
    ("Ranking", Ranking),
]

# AssetScore.WholeBuilding
class WholeBuilding(BSElement):
    pass


WholeBuilding.element_children = [
    ("AssetScoreData", AssetScoreData),
    ("EnergyUseByEndUses", EnergyUseByEndUses),
    ("Rankings", Rankings),
]

# AssetScore.UseTypes.UseType
class UseType(BSElement):
    pass


UseType.element_children = [
    ("AssetScoreData", AssetScoreData),
    ("AssetScoreUseType", AssetScoreUseType),
]

# AssetScore.UseTypes
class UseTypes(BSElement):
    pass


UseTypes.element_children = [
    ("UseType", UseType),
]

# FanBasedDistributionTypeType.FanCoil
class FanCoil(BSElement):
    class PipeInsulationThickness(BSElement):
        """Defines how thick insulation on pipes in a heating, cooling, water heating system is. (in.)"""

        element_type = "xs:decimal"

    class PipeLocation(BSElement):
        """Percent of pipe length in conditioned space. (0-100) (%)"""

        element_type = "xs:decimal"


FanCoil.element_children = [
    ("FanCoilType", FanCoilType),
    ("HVACPipeConfiguration", HVACPipeConfiguration),
    ("PipeInsulationThickness", FanCoil.PipeInsulationThickness),
    ("PipeLocation", FanCoil.PipeLocation),
]

# FanBasedType.AirSideEconomizer
class AirSideEconomizer(BSElement):
    pass


AirSideEconomizer.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
AirSideEconomizer.element_children = [
    ("AirSideEconomizerType", AirSideEconomizerType),
    ("EconomizerControl", EconomizerControl),
    ("EconomizerDryBulbControlPoint", EconomizerDryBulbControlPoint),
    ("EconomizerEnthalpyControlPoint", EconomizerEnthalpyControlPoint),
    ("EconomizerLowTemperatureLockout", EconomizerLowTemperatureLockout),
]

# ControlSystemType.Analog
class Analog(BSElement):
    """Analog control system."""

    class CommunicationProtocol(CommunicationProtocolAnalogType):
        """Method of communicating data over an analog network."""


Analog.element_children = [
    ("CommunicationProtocol", Analog.CommunicationProtocol),
]

# ControlSystemType.Digital
class Digital(BSElement):
    """Digital (or Direct Digital Control [DDC]) system."""

    class CommunicationProtocol(CommunicationProtocolDigitalType):
        """Method of communicating data over a digital computer network."""


Digital.element_children = [
    ("CommunicationProtocol", Digital.CommunicationProtocol),
]

# ClimateZoneType.ASHRAE
class ASHRAE(BSElement):
    class ClimateZone(BSElement):
        """Based on the ClimateZoneType term, this is the climate zone designation."""

        element_type = "xs:string"
        element_enumerations = [
            "1A",
            "1B",
            "2A",
            "2B",
            "3A",
            "3B",
            "3C",
            "4A",
            "4B",
            "4C",
            "5A",
            "5B",
            "5C",
            "6A",
            "6B",
            "7",
            "8",
        ]


ASHRAE.element_children = [
    ("ClimateZone", ASHRAE.ClimateZone),
]

# ClimateZoneType.EnergyStar
class EnergyStar(BSElement):
    class ClimateZone(BSElement):
        """Based on the ClimateZoneType term, this is the climate zone designation."""

        element_type = "xs:string"
        element_enumerations = [
            "Northern",
            "North-Central",
            "South-Central",
            "Southern",
        ]


EnergyStar.element_children = [
    ("ClimateZone", EnergyStar.ClimateZone),
]

# ClimateZoneType.CaliforniaTitle24
class CaliforniaTitle24(BSElement):
    class ClimateZone(BSElement):
        """Based on the ClimateZoneType term, this is the climate zone designation."""

        element_type = "xs:string"
        element_enumerations = [
            "Climate Zone 1",
            "Climate Zone 2",
            "Climate Zone 3",
            "Climate Zone 4",
            "Climate Zone 5",
            "Climate Zone 6",
            "Climate Zone 7",
            "Climate Zone 8",
            "Climate Zone 9",
            "Climate Zone 10",
            "Climate Zone 11",
            "Climate Zone 12",
            "Climate Zone 13",
            "Climate Zone 14",
            "Climate Zone 15",
            "Climate Zone 16",
        ]


CaliforniaTitle24.element_children = [
    ("ClimateZone", CaliforniaTitle24.ClimateZone),
]

# ClimateZoneType.IECC
class IECC(BSElement):
    class ClimateZone(BSElement):
        """Based on the ClimateZoneType term, this is the climate zone designation."""

        element_type = "xs:string"
        element_enumerations = [
            "1",
            "2",
            "3",
            "4 (Except Marine)",
            "4 (Marine)",
            "5",
            "6",
            "7",
            "8",
        ]


IECC.element_children = [
    ("ClimateZone", IECC.ClimateZone),
]

# ClimateZoneType.BuildingAmerica
class BuildingAmerica(BSElement):
    class ClimateZone(BSElement):
        """Based on the ClimateZoneType term, this is the climate zone designation."""

        element_type = "xs:string"
        element_enumerations = [
            "Subarctic",
            "Marine",
            "Hot-dry",
            "Mixed-dry",
            "Hot-humid",
            "Mixed-humid",
            "Cold",
            "Very cold",
        ]


BuildingAmerica.element_children = [
    ("ClimateZone", BuildingAmerica.ClimateZone),
]

# ClimateZoneType.DOE
class DOE(BSElement):
    class ClimateZone(BSElement):
        """Based on the ClimateZoneType term, this is the climate zone designation."""

        element_type = "xs:string"
        element_enumerations = [
            "Subarctic",
            "Marine",
            "Hot-dry",
            "Mixed-dry",
            "Hot-humid",
            "Mixed-humid",
            "Cold",
            "Very cold",
        ]


DOE.element_children = [
    ("ClimateZone", DOE.ClimateZone),
]

# WallID
class WallID(BSElement):
    """ID number of the wall type associated with this side of the section."""


WallID.element_attributes = [
    "IDref",  # IDREF
]
WallID.element_children = [
    ("WallArea", WallArea),
]

# DoorID
class DoorID(BSElement):
    """ID number of the door type associated with this side of the section."""

    class FenestrationArea(BSElement):
        """Total area of this fenestration type. (ft2)"""

        element_type = "xs:decimal"


DoorID.element_attributes = [
    "IDref",  # IDREF
]
DoorID.element_children = [
    ("FenestrationArea", DoorID.FenestrationArea),
]

# WindowID.WindowToWallRatio
class WindowToWallRatio(BoundedDecimalZeroToOneWithSourceAttribute):
    """Ratio of total window area to total wall area. (0-1) (fraction)"""


# WindowID
class WindowID(BSElement):
    """ID number of the window type associated with this side of the section."""

    class FenestrationArea(BSElement):
        """Total area of this fenestration type. (ft2)"""

        element_type = "xs:decimal"


WindowID.element_attributes = [
    "IDref",  # IDREF
]
WindowID.element_children = [
    ("FenestrationArea", WindowID.FenestrationArea),
    ("WindowToWallRatio", WindowToWallRatio),
    ("PercentOfWindowAreaShaded", PercentOfWindowAreaShaded),
]

# ResourceUnitsType
class ResourceUnitsType(BSElement):
    pass


ResourceUnitsType.element_union = [
    OtherUnitsType,
    ResourceUnitsBaseType,
]

# DerivedModelType.Models.Model.DerivedModelCoefficients.Guideline14Model
class Guideline14Model(BSElement):
    """Defined parameters are based on those available in ASHRAE Guideline 14-2014 Table D-1 and Figure D-1.  Concepts and nomenclature is also adopted from the CalTRACK methodology.  Attempts to generalize these parameters are made."""


Guideline14Model.element_children = [
    ("ModelType", ModelType),
    ("Intercept", Intercept),
    ("Beta1", Beta1),
    ("Beta2", Beta2),
    ("Beta3", Beta3),
    ("Beta4", Beta4),
]

# DerivedModelType.Models.Model.DerivedModelCoefficients
class DerivedModelCoefficients(BSElement):
    pass


DerivedModelCoefficients.element_children = [
    ("Guideline14Model", Guideline14Model),
    ("TimeOfWeekTemperatureModel", TimeOfWeekTemperatureModel),
]

# DerivedModelType.Models.Model.DerivedModelPerformance
class DerivedModelPerformance(BSElement):
    """Characterization of the performance of the model."""


DerivedModelPerformance.element_children = [
    ("RSquared", RSquared),
    ("AdjustedRSquared", AdjustedRSquared),
    ("RMSE", RMSE),
    ("CVRMSE", CVRMSE),
    ("NDBE", NDBE),
    ("MBE", MBE),
    ("NMBE", NMBE),
]

# DerivedModelType.Models.Model.SummaryInformation
class SummaryInformation(BSElement):
    pass


SummaryInformation.element_children = [
    ("NumberOfDataPoints", NumberOfDataPoints),
    ("NumberOfParameters", NumberOfParameters),
    ("DegreesOfFreedom", DegreesOfFreedom),
    ("AggregateActualEnergyUse", AggregateActualEnergyUse),
    ("AggregateModeledEnergyUse", AggregateModeledEnergyUse),
]

# PressureUnitsType
class PressureUnitsType(BSElement):
    pass


PressureUnitsType.element_union = [
    OtherUnitsType,
    PressureUnitsBaseType,
]

# PeakResourceUnitsType
class PeakResourceUnitsType(BSElement):
    pass


PeakResourceUnitsType.element_union = [
    OtherUnitsType,
    PeakResourceUnitsBaseType,
]

# TemperatureUnitsType
class TemperatureUnitsType(BSElement):
    pass


TemperatureUnitsType.element_union = [
    OtherUnitsType,
    TemperatureUnitsBaseType,
]

# DimensionlessUnitsType
class DimensionlessUnitsType(BSElement):
    pass


DimensionlessUnitsType.element_union = [
    OtherUnitsType,
    DimensionlessUnitsBaseType,
]

# WeatherStations.WeatherStation
class WeatherStation(BSElement):
    pass


WeatherStation.element_attributes = [
    "ID",  # ID
]
WeatherStation.element_children = [
    ("WeatherDataStationID", WeatherDataStationID),
    ("WeatherStationName", WeatherStationName),
    ("WeatherStationCategory", WeatherStationCategory),
]

# WeatherStations
class WeatherStations(BSElement):
    pass


WeatherStations.element_children = [
    ("WeatherStation", WeatherStation),
]

# UserDefinedFields
class UserDefinedFields(BSElement):
    pass


UserDefinedFields.element_children = [
    ("UserDefinedField", UserDefinedField),
]

# PremisesIdentifiers
class PremisesIdentifiers(BSElement):
    """Identifier used in a specific program or dataset. There can be multiple instances of Identifier Types within a dataset."""


PremisesIdentifiers.element_children = [
    ("PremisesIdentifier", PremisesIdentifier),
]

# Address
class Address(BSElement):
    class State(State):
        """The state for the address type, following the ISO 3166-2 Region code for US states."""


Address.element_children = [
    ("StreetAddressDetail", StreetAddressDetail),
    ("City", City),
    ("State", Address.State),
    ("PostalCode", PostalCode),
    ("PostalCodePlus4", PostalCodePlus4),
    ("County", County),
    ("Country", Country),
]

# ClimateZoneType
class ClimateZoneType(BSElement):
    """The climate zone type, based on the organization defining it. Many different organizations have implemented different climate zone definitions based on their needs. The list below represents the current list. This list can be added to over time based on the collaborative BEDES development process."""

    class CBECS(CBECSType):
        pass

    class Other(BSElement):
        class ClimateZone(BSElement):
            """Based on the ClimateZoneType term, this is the climate zone designation."""

            element_type = "xs:string"


ClimateZoneType.element_children = [
    ("ASHRAE", ASHRAE),
    ("EnergyStar", EnergyStar),
    ("CaliforniaTitle24", CaliforniaTitle24),
    ("IECC", IECC),
    ("BuildingAmerica", BuildingAmerica),
    ("CBECS", ClimateZoneType.CBECS),
    ("DOE", DOE),
    ("Other", ClimateZoneType.Other),
]
ClimateZoneType.Other.element_children = [
    ("ClimateZone", ClimateZoneType.Other.ClimateZone),
]

# FloorAreas
class FloorAreas(BSElement):
    pass


FloorAreas.element_children = [
    ("FloorArea", FloorArea),
]

# OccupancyLevels
class OccupancyLevels(BSElement):
    pass


OccupancyLevels.element_children = [
    ("OccupancyLevel", OccupancyLevel),
]

# TypicalOccupantUsages
class TypicalOccupantUsages(BSElement):
    """Characterization of the usage of the space (complex, whole building, or section) by building occupants."""


TypicalOccupantUsages.element_children = [
    ("TypicalOccupantUsage", TypicalOccupantUsage),
]

# BuildingType.SpatialUnits
class SpatialUnits(BSElement):
    pass


SpatialUnits.element_children = [
    ("SpatialUnit", SpatialUnit),
]

# BuildingType.OverallWindowToWallRatio
class OverallWindowToWallRatio(BoundedDecimalZeroToOneWithSourceAttribute):
    """Overall window to wall ratio of the facility. (0-1) (fraction)"""


# BuildingType.OverallDoorToWallRatio
class OverallDoorToWallRatio(BoundedDecimalZeroToOneWithSourceAttribute):
    """Overall door to wall ratio of the facility. (0-1) (fraction)"""


# BuildingType.Assessments
class Assessments(BSElement):
    pass


Assessments.element_children = [
    ("Assessment", Assessment),
]

# SpaceType
class SpaceType(BSElement):
    pass


SpaceType.element_attributes = [
    "ID",  # ID
]
SpaceType.element_children = [
    ("PremisesName", PremisesName),
    ("PremisesNotes", PremisesNotes),
    ("PremisesIdentifiers", PremisesIdentifiers),
    ("OccupancyClassification", OccupancyClassification),
    ("OccupancyLevels", OccupancyLevels),
    ("TypicalOccupantUsages", TypicalOccupantUsages),
    ("OccupancyScheduleIDs", OccupancyScheduleIDs),
    ("OccupantsActivityLevel", OccupantsActivityLevel),
    ("DaylitFloorArea", DaylitFloorArea),
    ("DaylightingIlluminanceSetpoint", DaylightingIlluminanceSetpoint),
    ("PrimaryContactID", PrimaryContactID),
    ("TenantIDs", TenantIDs),
    ("FloorAreas", FloorAreas),
    ("PercentageOfCommonSpace", PercentageOfCommonSpace),
    ("ConditionedVolume", ConditionedVolume),
    ("UserDefinedFields", UserDefinedFields),
]

# ScheduleType.ScheduleDetails
class ScheduleDetails(BSElement):
    pass


ScheduleDetails.element_children = [
    ("ScheduleDetail", ScheduleDetail),
]

# ContactType.ContactTelephoneNumbers
class ContactTelephoneNumbers(BSElement):
    pass


ContactTelephoneNumbers.element_children = [
    ("ContactTelephoneNumber", ContactTelephoneNumber),
]

# ContactType.ContactEmailAddresses
class ContactEmailAddresses(BSElement):
    pass


ContactEmailAddresses.element_children = [
    ("ContactEmailAddress", ContactEmailAddress),
]

# TenantType.TenantTelephoneNumbers
class TenantTelephoneNumbers(BSElement):
    pass


TenantTelephoneNumbers.element_children = [
    ("TenantTelephoneNumber", TenantTelephoneNumber),
]

# TenantType.TenantEmailAddresses
class TenantEmailAddresses(BSElement):
    pass


TenantEmailAddresses.element_children = [
    ("TenantEmailAddress", TenantEmailAddress),
]

# ScenarioType.WeatherType
class WeatherType(BSElement):
    """Weather conditions associated with the scenario."""

    class Other(OtherType):
        pass


WeatherType.element_children = [
    ("Normalized", Normalized),
    ("AdjustedToYear", AdjustedToYear),
    ("Actual", Actual),
    ("Other", WeatherType.Other),
]

# AssetScore
class AssetScore(BSElement):
    """A facility's Commercial Building Energy Asset Score Data."""


AssetScore.element_children = [
    ("WholeBuilding", WholeBuilding),
    ("UseTypes", UseTypes),
]

# ScenarioType.ScenarioType.Target
class Target(BSElement):
    class AnnualSavingsSiteEnergy(BSElement):
        """Site energy savings per year. (MMBtu/year)"""

        element_type = "xs:decimal"

    class AnnualSavingsSourceEnergy(BSElement):
        """Source energy savings per year. (MMBtu/year)"""

        element_type = "xs:decimal"

    class AnnualSavingsCost(BSElement):
        """Cost savings per year, including energy, demand, change in rate schedule, and other cost impacts on utility bills. ($/year)"""

        element_type = "xs:integer"

    class SummerPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the summer months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class WinterPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the winter months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class AnnualPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the year as defined in the utility rate schedule (for electrical energy use only) .(kW)"""

        element_type = "xs:decimal"

    class AnnualWaterSavings(BSElement):
        """Total annual water savings (hot and cold). (gal/year)"""

        element_type = "xs:decimal"

    class AnnualWaterCostSavings(BSElement):
        """Total annual reduction in water costs, not including water heating costs (hot and cold). ($/year)"""

        element_type = "xs:decimal"

    class SimplePayback(BSElement):
        """The length of time required for the investment to pay for itself. (yrs)"""

        element_type = "xs:decimal"

    class NetPresentValue(BSElement):
        """Net Present Value (NPV) of measure or package ($)."""

        element_type = "xs:decimal"

    class InternalRateOfReturn(BSElement):
        """Internal rate of return (IRR) of measure or package (0-100) (%)."""

        element_type = "xs:decimal"


Target.element_children = [
    ("ReferenceCase", ReferenceCase),
    ("AnnualSavingsSiteEnergy", Target.AnnualSavingsSiteEnergy),
    ("AnnualSavingsSourceEnergy", Target.AnnualSavingsSourceEnergy),
    ("AnnualSavingsCost", Target.AnnualSavingsCost),
    ("SummerPeakElectricityReduction", Target.SummerPeakElectricityReduction),
    ("WinterPeakElectricityReduction", Target.WinterPeakElectricityReduction),
    ("AnnualPeakElectricityReduction", Target.AnnualPeakElectricityReduction),
    ("AnnualWaterSavings", Target.AnnualWaterSavings),
    ("AnnualWaterCostSavings", Target.AnnualWaterCostSavings),
    ("SimplePayback", Target.SimplePayback),
    ("NetPresentValue", Target.NetPresentValue),
    ("InternalRateOfReturn", Target.InternalRateOfReturn),
    ("AssetScore", AssetScore),
    ("ENERGYSTARScore", ENERGYSTARScore),
]

# TimeSeriesType
class TimeSeriesType(BSElement):
    class StartTimestamp(BSElement):
        """The timestamp that marks the beginning of the time series. (CCYY-MM-DDThh:mm:ss.zzz)"""

        element_type = "xs:dateTime"

    class EndTimestamp(BSElement):
        """The timestamp that marks the end of the time series. (CCYY-MM-DDThh:mm:ss.zzz)"""

        element_type = "xs:dateTime"

    class IntervalFrequency(IntervalTime):
        """Indicates frequency of data that's available for a given variable. Data that's available can range from 1 minute interval to annual. This interval frequency can be applied to resource or other time series data like weather."""

    class HDDBaseTemperature(BSElement):
        """Reference temperature for calculating Heating Degree Days (HDD). (°F)"""

        element_type = "xs:decimal"

    class CDDBaseTemperature(BSElement):
        """Reference temperature for calculating Cooling Degree Days (CDD). (°F)"""

        element_type = "xs:decimal"


TimeSeriesType.element_attributes = [
    "ID",  # ID
]
TimeSeriesType.element_children = [
    ("ReadingType", ReadingType),
    ("PeakType", PeakType),
    ("TimeSeriesReadingQuantity", TimeSeriesReadingQuantity),
    ("StartTimestamp", TimeSeriesType.StartTimestamp),
    ("EndTimestamp", TimeSeriesType.EndTimestamp),
    ("IntervalDuration", IntervalDuration),
    ("IntervalDurationUnits", IntervalDurationUnits),
    ("IntervalFrequency", TimeSeriesType.IntervalFrequency),
    ("IntervalReading", IntervalReading),
    ("Phase", Phase),
    ("EnergyFlowDirection", EnergyFlowDirection),
    ("HeatingDegreeDays", HeatingDegreeDays),
    ("CoolingDegreeDays", CoolingDegreeDays),
    ("HDDBaseTemperature", TimeSeriesType.HDDBaseTemperature),
    ("CDDBaseTemperature", TimeSeriesType.CDDBaseTemperature),
    ("ResourceUseID", ResourceUseID),
    ("WeatherStationID", WeatherStationID),
    ("UserDefinedFields", UserDefinedFields),
]

# AllResourceTotalType
class AllResourceTotalType(BSElement):
    class EndUse(EndUse):
        """End use for which data is included."""

    class SiteEnergyUse(BSElement):
        """The annual amount of all the energy the premises consumes onsite, as reported on the utility bills. Calculated as imported energy (Eimp) - exported energy (Eexp) - net increase in stored imported energy (Es) (per ASHRAE 105-2014 Figure 5.6). (kBtu)"""

        element_type = "xs:decimal"

    class SourceEnergyUse(BSElement):
        """The total annual amount of all the raw resource required to operate the premises, including losses that take place during generation, transmission, and distribution of the energy. (kBtu)"""

        element_type = "xs:decimal"

    class SourceEnergyUseIntensity(BSElement):
        """The Source Energy Use divided by the premises gross floor area. (kBtu/ft2)"""

        element_type = "xs:decimal"

    class WaterUse(BSElement):
        """Annual water use from different sources. (kgal)"""

        element_type = "xs:decimal"


AllResourceTotalType.element_attributes = [
    "ID",  # ID
]
AllResourceTotalType.element_children = [
    ("EndUse", AllResourceTotalType.EndUse),
    ("TemporalStatus", TemporalStatus),
    ("ResourceBoundary", ResourceBoundary),
    ("SiteEnergyUse", AllResourceTotalType.SiteEnergyUse),
    ("SiteEnergyUseIntensity", SiteEnergyUseIntensity),
    ("SourceEnergyUse", AllResourceTotalType.SourceEnergyUse),
    ("SourceEnergyUseIntensity", AllResourceTotalType.SourceEnergyUseIntensity),
    ("BuildingEnergyUse", BuildingEnergyUse),
    ("BuildingEnergyUseIntensity", BuildingEnergyUseIntensity),
    ("ImportedEnergyConsistentUnits", ImportedEnergyConsistentUnits),
    ("OnsiteEnergyProductionConsistentUnits", OnsiteEnergyProductionConsistentUnits),
    ("ExportedEnergyConsistentUnits", ExportedEnergyConsistentUnits),
    (
        "NetIncreaseInStoredEnergyConsistentUnits",
        NetIncreaseInStoredEnergyConsistentUnits,
    ),
    ("EnergyCost", EnergyCost),
    ("EnergyCostIndex", EnergyCostIndex),
    (
        "OnsiteRenewableSystemElectricityExported",
        OnsiteRenewableSystemElectricityExported,
    ),
    (
        "ElectricitySourcedFromOnsiteRenewableSystems",
        ElectricitySourcedFromOnsiteRenewableSystems,
    ),
    ("SummerPeak", SummerPeak),
    ("WinterPeak", WinterPeak),
    ("WaterResource", WaterResource),
    ("WaterUse", AllResourceTotalType.WaterUse),
    ("WaterIntensity", WaterIntensity),
    ("WaterCost", WaterCost),
    ("WasteWaterVolume", WasteWaterVolume),
    ("UserDefinedFields", UserDefinedFields),
]

# UtilityType.RateSchedules
class RateSchedules(BSElement):
    pass


RateSchedules.element_children = [
    ("RateSchedule", RateSchedule),
]

# ResourceUseType.Emissions
class Emissions(BSElement):
    pass


Emissions.element_children = [
    ("Emission", Emission),
]

# MeasureType.TypeOfMeasure
class TypeOfMeasure(BSElement):
    """Type of action associated with the measure."""


TypeOfMeasure.element_children = [
    ("Replacements", Replacements),
    ("ModificationRetrocommissions", ModificationRetrocommissions),
    ("Additions", Additions),
    ("Removals", Removals),
]

# MeasureType.TechnologyCategories
class TechnologyCategories(BSElement):
    pass


TechnologyCategories.element_children = [
    ("TechnologyCategory", TechnologyCategory),
]

# ReportType.AuditDates
class AuditDates(BSElement):
    pass


AuditDates.element_children = [
    ("AuditDate", AuditDate),
]

# ReportType.OtherEscalationRates
class OtherEscalationRates(BSElement):
    pass


OtherEscalationRates.element_children = [
    ("OtherEscalationRate", OtherEscalationRate),
]

# ReportType.Qualifications
class Qualifications(BSElement):
    pass


Qualifications.element_children = [
    ("Qualification", Qualification),
]

# ControlSystemType
class ControlSystemType(BSElement):
    """Identifier for the type of control (e.g., Pneumatic, Analog, Digital)."""

    class Other(BSElement):
        """Other type of control system."""


ControlSystemType.element_children = [
    ("Analog", Analog),
    ("Digital", Digital),
    ("Pneumatic", Pneumatic),
    ("Other", ControlSystemType.Other),
]
ControlSystemType.Other.element_children = [
    ("OtherCommunicationProtocolName", OtherCommunicationProtocolName),
]

# OtherHVACSystemType.OtherHVACType
class OtherHVACType(BSElement):
    """Type of space conditioning equipment that is not classified as heating, cooling, or air-distribution. This category includes ventilation, dehumidification, humidification, and air cleaning systems."""

    class OtherCombination(OtherCombinationType):
        pass

    class Unknown(UnknownType):
        pass


OtherHVACType.element_children = [
    ("Humidifier", Humidifier),
    ("Dehumidifier", Dehumidifier),
    ("AirCleaner", AirCleaner),
    ("MechanicalVentilation", MechanicalVentilation),
    ("SpotExhaust", SpotExhaust),
    ("NaturalVentilation", NaturalVentilation),
    ("OtherCombination", OtherHVACType.OtherCombination),
    ("Unknown", OtherHVACType.Unknown),
]

# LightingSystemType.LampType
class LampType(BSElement):
    """A lamp is a replaceable component, or bulb, which is designed to produce light from electricity, though, non-electric lamps also exist."""

    class OtherCombination(OtherCombinationType):
        pass

    class Unknown(UnknownType):
        pass


LampType.element_children = [
    ("Incandescent", Incandescent),
    ("LinearFluorescent", LinearFluorescent),
    ("CompactFluorescent", CompactFluorescent),
    ("Halogen", Halogen),
    ("HighIntensityDischarge", HighIntensityDischarge),
    ("SolidStateLighting", SolidStateLighting),
    ("Induction", Induction),
    ("Neon", Neon),
    ("Plasma", Plasma),
    ("Photoluminescent", Photoluminescent),
    ("SelfLuminous", SelfLuminous),
    ("OtherCombination", LampType.OtherCombination),
    ("Unknown", LampType.Unknown),
]

# LightingSystemType.DimmingCapability
class DimmingCapability(BSElement):
    """If exists then the lighting system can be dimmed across a range of outputs."""


DimmingCapability.element_children = [
    ("MinimumDimmingLightFraction", MinimumDimmingLightFraction),
    ("MinimumDimmingPowerFraction", MinimumDimmingPowerFraction),
]

# RefrigerationSystemType.RefrigerationSystemCategory
class RefrigerationSystemCategory(BSElement):
    """Basic type of refrigeration equipment."""


RefrigerationSystemCategory.element_children = [
    ("CentralRefrigerationSystem", CentralRefrigerationSystem),
    ("RefrigerationUnit", RefrigerationUnit),
]

# LaundrySystemType.LaundryType
class LaundryType(BSElement):
    """Type of laundry system."""

    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


LaundryType.element_children = [
    ("Washer", Washer),
    ("Dryer", Dryer),
    ("Combination", Combination),
    ("Other", LaundryType.Other),
    ("Unknown", LaundryType.Unknown),
]

# WallSystemType.WallInsulations
class WallInsulations(BSElement):
    """A description of the type of insulation and how it is applied."""


WallInsulations.element_children = [
    ("WallInsulation", WallInsulation),
]

# CeilingSystemType.CeilingInsulations
class CeilingInsulations(BSElement):
    pass


CeilingInsulations.element_children = [
    ("CeilingInsulation", CeilingInsulation),
]

# RoofSystemType.RoofInsulations
class RoofInsulations(BSElement):
    pass


RoofInsulations.element_children = [
    ("RoofInsulation", RoofInsulation),
]

# FenestrationSystemType.FenestrationType
class FenestrationType(BSElement):
    """Type of fenestration in this group (windows, skylights, doors)."""

    class Other(OtherType):
        pass


FenestrationType.element_children = [
    ("Window", Window),
    ("Skylight", Skylight),
    ("Door", Door),
    ("Other", FenestrationType.Other),
]

# FoundationSystemType.GroundCouplings
class GroundCouplings(BSElement):
    pass


GroundCouplings.element_children = [
    ("GroundCoupling", GroundCoupling),
]

# OnsiteStorageTransmissionGenerationSystemType.EnergyConversionType
class EnergyConversionType(BSElement):
    """Type of energy conversion provided by the system."""


EnergyConversionType.element_children = [
    ("Storage", Storage),
    ("Generation", Generation),
]

# CalculationMethodType.Measured
class Measured(BSElement):
    """The 'Measured' calculation method is used to represent a scenario in which actual measurements were used to derive data represented by this scenario type."""


Measured.element_children = [
    ("MeasuredEnergySource", MeasuredEnergySource),
]

# FanBasedDistributionTypeType
class FanBasedDistributionTypeType(BSElement):
    pass


FanBasedDistributionTypeType.element_children = [
    ("FanCoil", FanCoil),
]

# FanBasedType.FanBasedDistributionType
class FanBasedDistributionType(FanBasedDistributionTypeType):
    pass


# ControlGeneralType.Thermostat
class Thermostat(BSElement):
    """Thermostat-based control technology."""

    class ControlStrategy(ControlStrategyGeneralType):
        """Thermostat controller strategy."""

    class OtherControlStrategyName(BSElement):
        """If ControlStrategy is other, then the name of the strategy used."""

        element_type = "xs:string"


Thermostat.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlStrategy", Thermostat.ControlStrategy),
    ("OtherControlStrategyName", Thermostat.OtherControlStrategyName),
]

# ControlLightingType.Daylighting
class Daylighting(BSElement):
    """Type of daylighting controls used to manage lighting."""

    class ControlSensor(ControlSensorDaylightingType):
        """Type of sensor for daylighting."""

    class ControlStrategy(ControlStrategyDaylightingType):
        """Daylighting control strategy."""

    class OtherControlStrategyName(BSElement):
        """If ControlStrategy is other, then the name of the strategy used."""

        element_type = "xs:string"


Daylighting.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlSensor", Daylighting.ControlSensor),
    ("ControlSteps", ControlSteps),
    ("ControlStrategy", Daylighting.ControlStrategy),
    ("OtherControlStrategyName", Daylighting.OtherControlStrategyName),
]

# DerivedModelType.Models.Model.DerivedModelInputs.ResponseVariable.ResponseVariableUnits
class ResponseVariableUnits(ResourceUnitsType):
    pass


# DerivedModelType.Models.Model.DerivedModelInputs.ResponseVariable
class ResponseVariable(BSElement):
    pass


ResponseVariable.element_children = [
    ("ResponseVariableName", ResponseVariableName),
    ("ResponseVariableUnits", ResponseVariableUnits),
    ("ResponseVariableEndUse", ResponseVariableEndUse),
]

# UnitsType
class UnitsType(BSElement):
    """Enumeration for different potential units."""


UnitsType.element_union = [
    ResourceUnitsType,
    PressureUnitsType,
    PeakResourceUnitsType,
    TemperatureUnitsType,
]

# DerivedModelType.Models.Model.ModeledTimeSeriesData
class ModeledTimeSeriesData(BSElement):
    """This element stores the timeseries data generated when the model is applied to the training data, oftentimes referred to as yhat. The difference between each pairwise element in this series with its corresponding data from the Current Building Modeled Scenario would generate the residuals."""

    class TimeSeries(TimeSeriesType):
        pass


ModeledTimeSeriesData.element_children = [
    ("TimeSeries", ModeledTimeSeriesData.TimeSeries),
]

# DerivedModelType.SavingsSummaries.SavingsSummary.ComparisonPeriodModeledTimeSeriesData
class ComparisonPeriodModeledTimeSeriesData(BSElement):
    """Applicable when the NormalizationMethod is Forecast or Backcast. Used to capture the modeled timeseries data associated with the comparison period."""

    class TimeSeries(TimeSeriesType):
        pass


ComparisonPeriodModeledTimeSeriesData.element_children = [
    ("TimeSeries", ComparisonPeriodModeledTimeSeriesData.TimeSeries),
]

# DerivedModelType.SavingsSummaries.SavingsSummary.StandardConditionsBaselinePeriodModeledTimeSeriesData
class StandardConditionsBaselinePeriodModeledTimeSeriesData(BSElement):
    """Applicable when the NormalizationMethod is Standard Conditions. Used to capture the modeled timeseries data associated with the baseline period at standard conditions."""

    class TimeSeries(TimeSeriesType):
        pass


StandardConditionsBaselinePeriodModeledTimeSeriesData.element_children = [
    ("TimeSeries", StandardConditionsBaselinePeriodModeledTimeSeriesData.TimeSeries),
]

# DerivedModelType.SavingsSummaries.SavingsSummary.StandardConditionsReportingPeriodModeledTimeSeriesData
class StandardConditionsReportingPeriodModeledTimeSeriesData(BSElement):
    """Applicable when the NormalizationMethod is Standard Conditions. Used to capture the modeled timeseries data associated with the reporting period at standard conditions."""

    class TimeSeries(TimeSeriesType):
        pass


StandardConditionsReportingPeriodModeledTimeSeriesData.element_children = [
    ("TimeSeries", StandardConditionsReportingPeriodModeledTimeSeriesData.TimeSeries),
]

# DerivedModelType.SavingsSummaries.SavingsSummary.StandardConditionsTimeSeriesData
class StandardConditionsTimeSeriesData(BSElement):
    """Applicable when the NormalizationMethod is Standard Conditions. Used to capture timeseries data inputs (i.e. temperature or weather data from a TMY3 file, etc.)."""

    class TimeSeries(TimeSeriesType):
        pass


StandardConditionsTimeSeriesData.element_children = [
    ("TimeSeries", StandardConditionsTimeSeriesData.TimeSeries),
]

# DerivedModelType.SavingsSummaries.SavingsSummary
class SavingsSummary(BSElement):
    pass


SavingsSummary.element_attributes = [
    "ID",  # ID
]
SavingsSummary.element_children = [
    ("BaselinePeriodModelID", BaselinePeriodModelID),
    ("ReportingPeriodModelID", ReportingPeriodModelID),
    ("NormalizationMethod", NormalizationMethod),
    ("ComparisonPeriodStartTimestamp", ComparisonPeriodStartTimestamp),
    ("ComparisonPeriodEndTimestamp", ComparisonPeriodEndTimestamp),
    (
        "ComparisonPeriodAggregateActualEnergyUse",
        ComparisonPeriodAggregateActualEnergyUse,
    ),
    (
        "ComparisonPeriodAggregateModeledEnergyUse",
        ComparisonPeriodAggregateModeledEnergyUse,
    ),
    ("AvoidedEnergyUse", AvoidedEnergyUse),
    ("SavingsUncertainty", SavingsUncertainty),
    ("ConfidenceLevel", ConfidenceLevel),
    (
        "StandardConditionsBaselinePeriodAggregateModeledEnergyUse",
        StandardConditionsBaselinePeriodAggregateModeledEnergyUse,
    ),
    (
        "StandardConditionsReportingPeriodAggregateModeledEnergyUse",
        StandardConditionsReportingPeriodAggregateModeledEnergyUse,
    ),
    ("StandardConditionsAvoidedEnergyUse", StandardConditionsAvoidedEnergyUse),
    ("ComparisonPeriodModeledTimeSeriesData", ComparisonPeriodModeledTimeSeriesData),
    (
        "StandardConditionsBaselinePeriodModeledTimeSeriesData",
        StandardConditionsBaselinePeriodModeledTimeSeriesData,
    ),
    (
        "StandardConditionsReportingPeriodModeledTimeSeriesData",
        StandardConditionsReportingPeriodModeledTimeSeriesData,
    ),
    ("StandardConditionsTimeSeriesData", StandardConditionsTimeSeriesData),
]

# WallSystemType
class WallSystemType(BSElement):
    class InteriorVisibleAbsorptance(BSElement):
        """The fraction of incident visible wavelength radiation that is absorbed by the material or surface. (0-1) (fraction)"""

        element_type = "xs:decimal"

    class ExteriorRoughness(ExteriorRoughness):
        """A description of the roughness of the exposed surface of a material. This property is used to approximate the effect of the surface condition on the convection of air across the surface. In energy simulation models, it is used to help determine the convection coefficients for a surface."""


WallSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
WallSystemType.element_children = [
    ("ExteriorWallConstruction", ExteriorWallConstruction),
    ("ExteriorWallFinish", ExteriorWallFinish),
    ("ExteriorWallColor", ExteriorWallColor),
    ("WallInsulations", WallInsulations),
    ("WallRValue", WallRValue),
    ("WallUFactor", WallUFactor),
    ("WallFramingMaterial", WallFramingMaterial),
    ("WallFramingSpacing", WallFramingSpacing),
    ("WallFramingDepth", WallFramingDepth),
    ("WallFramingFactor", WallFramingFactor),
    ("CMUFill", CMUFill),
    ("WallExteriorSolarAbsorptance", WallExteriorSolarAbsorptance),
    ("WallExteriorThermalAbsorptance", WallExteriorThermalAbsorptance),
    ("InteriorVisibleAbsorptance", WallSystemType.InteriorVisibleAbsorptance),
    ("ExteriorRoughness", WallSystemType.ExteriorRoughness),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("UserDefinedFields", UserDefinedFields),
]

# RoofSystemType
class RoofSystemType(BSElement):
    pass


RoofSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
RoofSystemType.element_children = [
    ("RoofConstruction", RoofConstruction),
    ("BlueRoof", BlueRoof),
    ("CoolRoof", CoolRoof),
    ("GreenRoof", GreenRoof),
    ("RoofFinish", RoofFinish),
    ("RoofColor", RoofColor),
    ("RoofInsulations", RoofInsulations),
    ("DeckType", DeckType),
    ("RoofRValue", RoofRValue),
    ("RoofUFactor", RoofUFactor),
    ("RoofFramingMaterial", RoofFramingMaterial),
    ("RoofFramingSpacing", RoofFramingSpacing),
    ("RoofFramingDepth", RoofFramingDepth),
    ("RoofFramingFactor", RoofFramingFactor),
    ("RoofSlope", RoofSlope),
    ("RadiantBarrier", RadiantBarrier),
    ("RoofExteriorSolarAbsorptance", RoofExteriorSolarAbsorptance),
    ("RoofExteriorSolarReflectanceIndex", RoofExteriorSolarReflectanceIndex),
    ("RoofExteriorThermalAbsorptance", RoofExteriorThermalAbsorptance),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("UserDefinedFields", UserDefinedFields),
]

# CeilingSystemType
class CeilingSystemType(BSElement):
    pass


CeilingSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
CeilingSystemType.element_children = [
    ("CeilingConstruction", CeilingConstruction),
    ("CeilingFinish", CeilingFinish),
    ("CeilingColor", CeilingColor),
    ("CeilingInsulations", CeilingInsulations),
    ("CeilingRValue", CeilingRValue),
    ("CeilingUFactor", CeilingUFactor),
    ("CeilingFramingMaterial", CeilingFramingMaterial),
    ("CeilingFramingSpacing", CeilingFramingSpacing),
    ("CeilingFramingDepth", CeilingFramingDepth),
    ("CeilingFramingFactor", CeilingFramingFactor),
    ("CeilingVisibleAbsorptance", CeilingVisibleAbsorptance),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("UserDefinedFields", UserDefinedFields),
]

# FenestrationSystemType
class FenestrationSystemType(BSElement):
    pass


FenestrationSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
FenestrationSystemType.element_children = [
    ("FenestrationType", FenestrationType),
    ("FenestrationFrameMaterial", FenestrationFrameMaterial),
    ("FenestrationOperation", FenestrationOperation),
    ("Weatherstripped", Weatherstripped),
    ("TightnessFitCondition", TightnessFitCondition),
    ("GlassType", GlassType),
    ("FenestrationGasFill", FenestrationGasFill),
    ("FenestrationGlassLayers", FenestrationGlassLayers),
    ("FenestrationRValue", FenestrationRValue),
    ("FenestrationUFactor", FenestrationUFactor),
    ("SolarHeatGainCoefficient", SolarHeatGainCoefficient),
    ("VisibleTransmittance", VisibleTransmittance),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("UserDefinedFields", UserDefinedFields),
]

# ExteriorFloorSystemType
class ExteriorFloorSystemType(BSElement):
    class InteriorVisibleAbsorptance(BSElement):
        """The fraction of incident visible wavelength radiation that is absorbed by the material or surface. (0-1) (fraction)"""

        element_type = "xs:decimal"

    class ExteriorRoughness(ExteriorRoughness):
        """A description of the roughness of the exposed surface of a material. This property is used to approximate the effect of the surface condition on the convection of air across the surface. In energy simulation models, it is used to help determine the convection coefficients for a surface."""


ExteriorFloorSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
ExteriorFloorSystemType.element_children = [
    ("ExteriorFloorConstruction", ExteriorFloorConstruction),
    ("ExteriorFloorFinish", ExteriorFloorFinish),
    ("ExteriorFloorColor", ExteriorFloorColor),
    ("ExteriorFloorRValue", ExteriorFloorRValue),
    ("ExteriorFloorUFactor", ExteriorFloorUFactor),
    ("ExteriorFloorFramingMaterial", ExteriorFloorFramingMaterial),
    ("ExteriorFloorFramingSpacing", ExteriorFloorFramingSpacing),
    ("ExteriorFloorFramingDepth", ExteriorFloorFramingDepth),
    ("ExteriorFloorFramingFactor", ExteriorFloorFramingFactor),
    ("ExteriorFloorExteriorSolarAbsorptance", ExteriorFloorExteriorSolarAbsorptance),
    (
        "ExteriorFloorExteriorThermalAbsorptance",
        ExteriorFloorExteriorThermalAbsorptance,
    ),
    ("InteriorVisibleAbsorptance", ExteriorFloorSystemType.InteriorVisibleAbsorptance),
    ("ExteriorRoughness", ExteriorFloorSystemType.ExteriorRoughness),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("UserDefinedFields", UserDefinedFields),
]

# FoundationSystemType
class FoundationSystemType(BSElement):
    pass


FoundationSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
FoundationSystemType.element_children = [
    ("GroundCouplings", GroundCouplings),
    ("FloorCovering", FloorCovering),
    ("FloorConstructionType", FloorConstructionType),
    ("PlumbingPenetrationSealing", PlumbingPenetrationSealing),
    ("YearInstalled", YearInstalled),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]

# LinkedPremises
class LinkedPremises(BSElement):
    """Establishes whether the system applies to one or more entire buildings, sections, spaces, or zones within buildings. Power consuming system loads should be distributed in proportion to the floor areas of linked premises. Envelope systems should be distributed in proportion to the exterior surface areas of linked premises."""

    class Facility(BSElement):
        class LinkedFacilityID(BSElement):
            """ID numbers of the facilities associated with the system."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply to this system type in the context of the linked premise."""

    class Site(BSElement):
        class LinkedSiteID(BSElement):
            """ID numbers of the sites associated with the system."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply to this system type in the context of the linked premise."""

    class Building(BSElement):
        class LinkedBuildingID(BSElement):
            """ID numbers of the buildings associated with the system."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply to this system type in the context of the linked premise."""

    class Section(BSElement):
        class LinkedSectionID(BSElement):
            """ID numbers of the sections associated with the system."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply to this system type in the context of the linked premise."""

    class ThermalZone(BSElement):
        class LinkedThermalZoneID(BSElement):
            """ID numbers of the zones associated with the system."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply to this system type in the context of the linked premise."""

    class Space(BSElement):
        class LinkedSpaceID(BSElement):
            """ID numbers of the spaces associated with the system."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply to this system type in the context of the linked premise."""


LinkedPremises.element_children = [
    ("Facility", LinkedPremises.Facility),
    ("Site", LinkedPremises.Site),
    ("Building", LinkedPremises.Building),
    ("Section", LinkedPremises.Section),
    ("ThermalZone", LinkedPremises.ThermalZone),
    ("Space", LinkedPremises.Space),
]
LinkedPremises.Facility.element_children = [
    ("LinkedFacilityID", LinkedPremises.Facility.LinkedFacilityID),
]
LinkedPremises.Facility.LinkedFacilityID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Facility.LinkedFacilityID.element_children = [
    ("LinkedScheduleIDs", LinkedPremises.Facility.LinkedFacilityID.LinkedScheduleIDs),
    ("FloorAreas", FloorAreas),
]
LinkedPremises.Facility.LinkedFacilityID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremises.Facility.LinkedFacilityID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremises.Facility.LinkedFacilityID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Site.element_children = [
    ("LinkedSiteID", LinkedPremises.Site.LinkedSiteID),
]
LinkedPremises.Site.LinkedSiteID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Site.LinkedSiteID.element_children = [
    ("LinkedScheduleIDs", LinkedPremises.Site.LinkedSiteID.LinkedScheduleIDs),
    ("FloorAreas", FloorAreas),
]
LinkedPremises.Site.LinkedSiteID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremises.Site.LinkedSiteID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremises.Site.LinkedSiteID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Building.element_children = [
    ("LinkedBuildingID", LinkedPremises.Building.LinkedBuildingID),
]
LinkedPremises.Building.LinkedBuildingID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Building.LinkedBuildingID.element_children = [
    ("LinkedScheduleIDs", LinkedPremises.Building.LinkedBuildingID.LinkedScheduleIDs),
    ("FloorAreas", FloorAreas),
]
LinkedPremises.Building.LinkedBuildingID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremises.Building.LinkedBuildingID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremises.Building.LinkedBuildingID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Section.element_children = [
    ("LinkedSectionID", LinkedPremises.Section.LinkedSectionID),
]
LinkedPremises.Section.LinkedSectionID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Section.LinkedSectionID.element_children = [
    ("LinkedScheduleIDs", LinkedPremises.Section.LinkedSectionID.LinkedScheduleIDs),
    ("FloorAreas", FloorAreas),
]
LinkedPremises.Section.LinkedSectionID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremises.Section.LinkedSectionID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremises.Section.LinkedSectionID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.ThermalZone.element_children = [
    ("LinkedThermalZoneID", LinkedPremises.ThermalZone.LinkedThermalZoneID),
]
LinkedPremises.ThermalZone.LinkedThermalZoneID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.ThermalZone.LinkedThermalZoneID.element_children = [
    (
        "LinkedScheduleIDs",
        LinkedPremises.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs,
    ),
    ("FloorAreas", FloorAreas),
]
LinkedPremises.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremises.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremises.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Space.element_children = [
    ("LinkedSpaceID", LinkedPremises.Space.LinkedSpaceID),
]
LinkedPremises.Space.LinkedSpaceID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremises.Space.LinkedSpaceID.element_children = [
    ("LinkedScheduleIDs", LinkedPremises.Space.LinkedSpaceID.LinkedScheduleIDs),
    ("FloorAreas", FloorAreas),
]
LinkedPremises.Space.LinkedSpaceID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremises.Space.LinkedSpaceID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremises.Space.LinkedSpaceID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]

# BuildingSync.Facilities.Facility.Systems.WaterInfiltrationSystems.WaterInfiltrationSystem
class WaterInfiltrationSystem(BSElement):
    """Description of the infiltration characteristics for an opaque surface, fenestration unit, a thermal zone."""


WaterInfiltrationSystem.element_children = [
    ("WaterInfiltrationNotes", WaterInfiltrationNotes),
    (
        "LocationsOfExteriorWaterIntrusionDamages",
        LocationsOfExteriorWaterIntrusionDamages,
    ),
    (
        "LocationsOfInteriorWaterIntrusionDamages",
        LocationsOfInteriorWaterIntrusionDamages,
    ),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
]

# BuildingSync.Facilities.Facility.Systems.WaterInfiltrationSystems
class WaterInfiltrationSystems(BSElement):
    pass


WaterInfiltrationSystems.element_children = [
    ("WaterInfiltrationSystem", WaterInfiltrationSystem),
]

# ScheduleType
class ScheduleType(BSElement):
    pass


ScheduleType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
ScheduleType.element_children = [
    ("SchedulePeriodBeginDate", SchedulePeriodBeginDate),
    ("SchedulePeriodEndDate", SchedulePeriodEndDate),
    ("ScheduleDetails", ScheduleDetails),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
]

# ContactType
class ContactType(BSElement):
    pass


ContactType.element_attributes = [
    "ID",  # ID
]
ContactType.element_children = [
    ("ContactRoles", ContactRoles),
    ("ContactName", ContactName),
    ("ContactCompany", ContactCompany),
    ("ContactTitle", ContactTitle),
    ("Address", Address),
    ("ContactTelephoneNumbers", ContactTelephoneNumbers),
    ("ContactEmailAddresses", ContactEmailAddresses),
    ("UserDefinedFields", UserDefinedFields),
]

# TenantType
class TenantType(BSElement):
    pass


TenantType.element_attributes = [
    "ID",  # ID
]
TenantType.element_children = [
    ("TenantName", TenantName),
    ("Address", Address),
    ("TenantTelephoneNumbers", TenantTelephoneNumbers),
    ("TenantEmailAddresses", TenantEmailAddresses),
    ("ContactIDs", ContactIDs),
    ("UserDefinedFields", UserDefinedFields),
]

# ResourceUseType
class ResourceUseType(BSElement):
    class EndUse(EndUse):
        """End use that the resource primarily applies to."""


ResourceUseType.element_attributes = [
    "ID",  # ID
]
ResourceUseType.element_children = [
    ("EnergyResource", EnergyResource),
    ("ResourceUseNotes", ResourceUseNotes),
    ("ResourceBoundary", ResourceBoundary),
    ("WaterResource", WaterResource),
    ("ResourceUnits", ResourceUnits),
    ("PercentResource", PercentResource),
    ("SharedResourceSystem", SharedResourceSystem),
    ("EndUse", ResourceUseType.EndUse),
    ("PercentEndUse", PercentEndUse),
    ("AnnualFuelUseNativeUnits", AnnualFuelUseNativeUnits),
    ("AnnualFuelUseConsistentUnits", AnnualFuelUseConsistentUnits),
    ("AnnualFuelUseLinkedTimeSeriesIDs", AnnualFuelUseLinkedTimeSeriesIDs),
    ("PeakResourceUnits", PeakResourceUnits),
    ("AnnualPeakNativeUnits", AnnualPeakNativeUnits),
    ("AnnualPeakConsistentUnits", AnnualPeakConsistentUnits),
    ("AnnualFuelCost", AnnualFuelCost),
    ("FuelUseIntensity", FuelUseIntensity),
    ("UtilityIDs", UtilityIDs),
    ("Emissions", Emissions),
    ("MeterID", MeterID),
    ("ParentResourceUseID", ParentResourceUseID),
    ("UserDefinedFields", UserDefinedFields),
]

# ScenarioType.AllResourceTotals.AllResourceTotal
class AllResourceTotal(AllResourceTotalType):
    pass


# UtilityType
class UtilityType(BSElement):
    class UtilityAccountNumber(BSElement):
        """Unique account number designated by the utility."""

        element_type = "xs:string"

    class UtilityBillpayer(BSElement):
        """Organization that is responsible for paying the bills associated with this meter."""

        element_type = "xs:string"


UtilityType.element_attributes = [
    "ID",  # ID
]
UtilityType.element_children = [
    ("RateSchedules", RateSchedules),
    ("MeteringConfiguration", MeteringConfiguration),
    ("TypeOfResourceMeter", TypeOfResourceMeter),
    ("FuelInterruptibility", FuelInterruptibility),
    ("EIAUtilityID", EIAUtilityID),
    ("UtilityName", UtilityName),
    ("PowerPlant", PowerPlant),
    ("UtilityMeterNumbers", UtilityMeterNumbers),
    ("UtilityAccountNumber", UtilityType.UtilityAccountNumber),
    ("UtilityBillpayer", UtilityType.UtilityBillpayer),
    ("ElectricDistributionUtility", ElectricDistributionUtility),
    ("SourceSiteRatio", SourceSiteRatio),
]

# LinkedPremisesOrSystem
class LinkedPremisesOrSystem(BSElement):
    """Establishes whether an item applies to one or more systems, entire buildings, sections, spaces, or zones within buildings. Developer note: the XSD should be done as a union, but cannot due to limitations of automatic processors."""

    class Facility(BSElement):
        class LinkedFacilityID(BSElement):
            """ID numbers of the associated facilities."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply in the context of the linked premise."""

    class Site(BSElement):
        class LinkedSiteID(BSElement):
            """ID numbers of the associated sites associated."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply in the context of the linked premise."""

    class Building(BSElement):
        class LinkedBuildingID(BSElement):
            """ID numbers of the associated buildings."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply in the context of the linked premise."""

    class Section(BSElement):
        class LinkedSectionID(BSElement):
            """ID numbers of the associated sections."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply in the context of the linked premise."""

    class ThermalZone(BSElement):
        class LinkedThermalZoneID(BSElement):
            """ID numbers of the associated zones."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply type in the context of the linked premise."""

    class Space(BSElement):
        class LinkedSpaceID(BSElement):
            """ID numbers of the associated spaces."""

            class LinkedScheduleIDs(BSElement):
                class LinkedScheduleID(BSElement):
                    """ID numbers of one or more schedules that apply to this system type in the context of the linked premise."""


LinkedPremisesOrSystem.element_children = [
    ("Facility", LinkedPremisesOrSystem.Facility),
    ("Site", LinkedPremisesOrSystem.Site),
    ("Building", LinkedPremisesOrSystem.Building),
    ("Section", LinkedPremisesOrSystem.Section),
    ("ThermalZone", LinkedPremisesOrSystem.ThermalZone),
    ("Space", LinkedPremisesOrSystem.Space),
    ("System", System),
]
LinkedPremisesOrSystem.Facility.element_children = [
    ("LinkedFacilityID", LinkedPremisesOrSystem.Facility.LinkedFacilityID),
]
LinkedPremisesOrSystem.Facility.LinkedFacilityID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Facility.LinkedFacilityID.element_children = [
    (
        "LinkedScheduleIDs",
        LinkedPremisesOrSystem.Facility.LinkedFacilityID.LinkedScheduleIDs,
    ),
    ("FloorAreas", FloorAreas),
]
LinkedPremisesOrSystem.Facility.LinkedFacilityID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremisesOrSystem.Facility.LinkedFacilityID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremisesOrSystem.Facility.LinkedFacilityID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Site.element_children = [
    ("LinkedSiteID", LinkedPremisesOrSystem.Site.LinkedSiteID),
]
LinkedPremisesOrSystem.Site.LinkedSiteID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Site.LinkedSiteID.element_children = [
    ("LinkedScheduleIDs", LinkedPremisesOrSystem.Site.LinkedSiteID.LinkedScheduleIDs),
    ("FloorAreas", FloorAreas),
]
LinkedPremisesOrSystem.Site.LinkedSiteID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremisesOrSystem.Site.LinkedSiteID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremisesOrSystem.Site.LinkedSiteID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Building.element_children = [
    ("LinkedBuildingID", LinkedPremisesOrSystem.Building.LinkedBuildingID),
]
LinkedPremisesOrSystem.Building.LinkedBuildingID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Building.LinkedBuildingID.element_children = [
    (
        "LinkedScheduleIDs",
        LinkedPremisesOrSystem.Building.LinkedBuildingID.LinkedScheduleIDs,
    ),
    ("FloorAreas", FloorAreas),
]
LinkedPremisesOrSystem.Building.LinkedBuildingID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremisesOrSystem.Building.LinkedBuildingID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremisesOrSystem.Building.LinkedBuildingID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Section.element_children = [
    ("LinkedSectionID", LinkedPremisesOrSystem.Section.LinkedSectionID),
]
LinkedPremisesOrSystem.Section.LinkedSectionID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Section.LinkedSectionID.element_children = [
    (
        "LinkedScheduleIDs",
        LinkedPremisesOrSystem.Section.LinkedSectionID.LinkedScheduleIDs,
    ),
    ("FloorAreas", FloorAreas),
]
LinkedPremisesOrSystem.Section.LinkedSectionID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremisesOrSystem.Section.LinkedSectionID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremisesOrSystem.Section.LinkedSectionID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.ThermalZone.element_children = [
    ("LinkedThermalZoneID", LinkedPremisesOrSystem.ThermalZone.LinkedThermalZoneID),
]
LinkedPremisesOrSystem.ThermalZone.LinkedThermalZoneID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.ThermalZone.LinkedThermalZoneID.element_children = [
    (
        "LinkedScheduleIDs",
        LinkedPremisesOrSystem.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs,
    ),
    ("FloorAreas", FloorAreas),
]
LinkedPremisesOrSystem.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremisesOrSystem.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremisesOrSystem.ThermalZone.LinkedThermalZoneID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Space.element_children = [
    ("LinkedSpaceID", LinkedPremisesOrSystem.Space.LinkedSpaceID),
]
LinkedPremisesOrSystem.Space.LinkedSpaceID.element_attributes = [
    "IDref",  # IDREF
]
LinkedPremisesOrSystem.Space.LinkedSpaceID.element_children = [
    ("LinkedScheduleIDs", LinkedPremisesOrSystem.Space.LinkedSpaceID.LinkedScheduleIDs),
    ("FloorAreas", FloorAreas),
]
LinkedPremisesOrSystem.Space.LinkedSpaceID.LinkedScheduleIDs.element_children = [
    (
        "LinkedScheduleID",
        LinkedPremisesOrSystem.Space.LinkedSpaceID.LinkedScheduleIDs.LinkedScheduleID,
    ),
]
LinkedPremisesOrSystem.Space.LinkedSpaceID.LinkedScheduleIDs.LinkedScheduleID.element_attributes = [
    "IDref",  # IDREF
]

# ReportType.Utilities.Utility
class Utility(UtilityType):
    """Utility associated with a scenario or scenarios."""


# CoolingPlantType
class CoolingPlantType(BSElement):
    class PrimaryFuel(FuelTypes):
        """Main fuel used by the CooiingPlant."""

    class ControlSystemTypes(BSElement):
        """CoolingPlant equipment control strategies."""


CoolingPlantType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
CoolingPlantType.element_children = [
    ("CoolingPlantCondition", CoolingPlantCondition),
    ("Location", Location),
    ("YearInstalled", YearInstalled),
    ("PrimaryFuel", CoolingPlantType.PrimaryFuel),
    ("BuildingAutomationSystem", BuildingAutomationSystem),
    ("ControlSystemTypes", CoolingPlantType.ControlSystemTypes),
    ("UserDefinedFields", UserDefinedFields),
]
CoolingPlantType.ControlSystemTypes.element_children = [
    ("ControlSystemType", ControlSystemType),
]

# CondenserPlantType
class CondenserPlantType(BSElement):
    class PrimaryFuel(FuelTypes):
        """Main fuel used by the CondenserPlant."""

    class ControlSystemTypes(BSElement):
        """CondenserPlant equipment control strategies."""


CondenserPlantType.element_attributes = [
    "ID",  # ID
]
CondenserPlantType.element_children = [
    ("CondenserPlantCondition", CondenserPlantCondition),
    ("Location", Location),
    ("YearInstalled", YearInstalled),
    ("PrimaryFuel", CondenserPlantType.PrimaryFuel),
    ("BuildingAutomationSystem", BuildingAutomationSystem),
    ("ControlSystemTypes", CondenserPlantType.ControlSystemTypes),
    ("UserDefinedFields", UserDefinedFields),
]
CondenserPlantType.ControlSystemTypes.element_children = [
    ("ControlSystemType", ControlSystemType),
]

# ControlGeneralType
class ControlGeneralType(BSElement):
    """An instance of a general control technology."""

    class AdvancedPowerStrip(BSElement):
        """Control by means of advanced power strip."""

        class ControlStrategy(ControlStrategyGeneralType):
            """Control strategy for advanced power strip."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class Manual(BSElement):
        """Manual operation of system."""

        class ControlStrategy(ControlStrategyGeneralType):
            """Control strategy for manual control."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class Occupancy(BSElement):
        """Occupancy-based controls."""

        class ControlSensor(ControlSensorOccupancyType):
            """Type of sensor for detecting occupancy."""

        class ControlStrategy(ControlStrategyOccupancyType):
            """Occupancy-based control strategy."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class Timer(BSElement):
        """Timer-based controls for specified timed intervals."""

        class ControlStrategy(ControlStrategyGeneralType):
            """Timer-based control strategy for lighting."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class OtherControlTechnology(BSElement):
        """Other control technology."""

        class OtherControlTechnologyName(BSElement):
            """Custom defined name for the type of control technology used."""

            element_type = "xs:string"

        class ControlStrategy(ControlStrategyGeneralType):
            """HVAC control strategy for other control technology."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"


ControlGeneralType.element_children = [
    ("AdvancedPowerStrip", ControlGeneralType.AdvancedPowerStrip),
    ("Manual", ControlGeneralType.Manual),
    ("Occupancy", ControlGeneralType.Occupancy),
    ("Timer", ControlGeneralType.Timer),
    ("Thermostat", Thermostat),
    ("OtherControlTechnology", ControlGeneralType.OtherControlTechnology),
]
ControlGeneralType.AdvancedPowerStrip.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlStrategy", ControlGeneralType.AdvancedPowerStrip.ControlStrategy),
    (
        "OtherControlStrategyName",
        ControlGeneralType.AdvancedPowerStrip.OtherControlStrategyName,
    ),
]
ControlGeneralType.Manual.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlStrategy", ControlGeneralType.Manual.ControlStrategy),
    ("OtherControlStrategyName", ControlGeneralType.Manual.OtherControlStrategyName),
]
ControlGeneralType.Occupancy.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlSensor", ControlGeneralType.Occupancy.ControlSensor),
    ("ControlStrategy", ControlGeneralType.Occupancy.ControlStrategy),
    ("OtherControlStrategyName", ControlGeneralType.Occupancy.OtherControlStrategyName),
]
ControlGeneralType.Timer.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlStrategy", ControlGeneralType.Timer.ControlStrategy),
    ("OtherControlStrategyName", ControlGeneralType.Timer.OtherControlStrategyName),
]
ControlGeneralType.OtherControlTechnology.element_children = [
    ("ControlSystemType", ControlSystemType),
    (
        "OtherControlTechnologyName",
        ControlGeneralType.OtherControlTechnology.OtherControlTechnologyName,
    ),
    ("ControlStrategy", ControlGeneralType.OtherControlTechnology.ControlStrategy),
    (
        "OtherControlStrategyName",
        ControlGeneralType.OtherControlTechnology.OtherControlStrategyName,
    ),
]

# HVACSystemType.HeatingAndCoolingSystems.CoolingSources.CoolingSource
class CoolingSource(BSElement):
    class Controls(BSElement):
        """List of controls for CoolingSource."""

        class Control(ControlGeneralType):
            """CoolingSource control."""


CoolingSource.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
CoolingSource.element_children = [
    ("CoolingSourceType", CoolingSourceType),
    ("CoolingMedium", CoolingMedium),
    ("AnnualCoolingEfficiencyValue", AnnualCoolingEfficiencyValue),
    ("AnnualCoolingEfficiencyUnits", AnnualCoolingEfficiencyUnits),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("NumberOfDiscreteCoolingStages", NumberOfDiscreteCoolingStages),
    ("CoolingStageCapacity", CoolingStageCapacity),
    ("MinimumPartLoadRatio", MinimumPartLoadRatio),
    ("RatedCoolingSensibleHeatRatio", RatedCoolingSensibleHeatRatio),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("PrimaryFuel", PrimaryFuel),
    ("CoolingSourceCondition", CoolingSourceCondition),
    ("Controls", CoolingSource.Controls),
    ("Location", Location),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
CoolingSource.Controls.element_children = [
    ("Control", CoolingSource.Controls.Control),
]

# HVACSystemType.HeatingAndCoolingSystems.CoolingSources
class CoolingSources(BSElement):
    pass


CoolingSources.element_children = [
    ("CoolingSource", CoolingSource),
]

# FanBasedType
class FanBasedType(BSElement):
    pass


FanBasedType.element_children = [
    ("FanBasedDistributionType", FanBasedDistributionType),
    ("AirSideEconomizer", AirSideEconomizer),
    ("HeatingSupplyAirTemperatureControl", HeatingSupplyAirTemperatureControl),
    ("CoolingSupplyAirTemperature", CoolingSupplyAirTemperature),
    ("CoolingSupplyAirTemperatureControlType", CoolingSupplyAirTemperatureControlType),
    (
        "OutsideAirResetMaximumHeatingSupplyTemperature",
        OutsideAirResetMaximumHeatingSupplyTemperature,
    ),
    (
        "OutsideAirResetMinimumHeatingSupplyTemperature",
        OutsideAirResetMinimumHeatingSupplyTemperature,
    ),
    (
        "OutsideAirTemperatureUpperLimitHeatingResetControl",
        OutsideAirTemperatureUpperLimitHeatingResetControl,
    ),
    (
        "OutsideAirTemperatureLowerLimitHeatingResetControl",
        OutsideAirTemperatureLowerLimitHeatingResetControl,
    ),
    (
        "OutsideAirResetMaximumCoolingSupplyTemperature",
        OutsideAirResetMaximumCoolingSupplyTemperature,
    ),
    (
        "OutsideAirResetMinimumCoolingSupplyTemperature",
        OutsideAirResetMinimumCoolingSupplyTemperature,
    ),
    (
        "OutsideAirTemperatureUpperLimitCoolingResetControl",
        OutsideAirTemperatureUpperLimitCoolingResetControl,
    ),
    (
        "OutsideAirTemperatureLowerLimitCoolingResetControl",
        OutsideAirTemperatureLowerLimitCoolingResetControl,
    ),
    ("HeatingSupplyAirTemperature", HeatingSupplyAirTemperature),
    ("SupplyAirTemperatureResetControl", SupplyAirTemperatureResetControl),
    ("StaticPressureResetControl", StaticPressureResetControl),
]

# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.CentralAirDistribution
class CentralAirDistribution(BSElement):
    class FanBased(FanBasedType):
        pass


CentralAirDistribution.element_children = [
    ("AirDeliveryType", AirDeliveryType),
    ("TerminalUnit", TerminalUnit),
    ("ReheatSource", ReheatSource),
    ("ReheatControlMethod", ReheatControlMethod),
    ("ReheatPlantID", ReheatPlantID),
    ("FanBased", CentralAirDistribution.FanBased),
]

# DuctSystemType
class DuctSystemType(BSElement):
    pass


DuctSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
DuctSystemType.element_children = [
    ("DuctConfiguration", DuctConfiguration),
    ("MinimumOutsideAirPercentage", MinimumOutsideAirPercentage),
    ("MaximumOAFlowRate", MaximumOAFlowRate),
    ("DuctInsulationCondition", DuctInsulationCondition),
    ("DuctSealing", DuctSealing),
    ("DuctInsulationRValue", DuctInsulationRValue),
    ("DuctSurfaceArea", DuctSurfaceArea),
    ("SupplyDuctPercentConditionedSpace", SupplyDuctPercentConditionedSpace),
    ("ReturnDuctPercentConditionedSpace", ReturnDuctPercentConditionedSpace),
    ("StaticPressureInstalled", StaticPressureInstalled),
    ("DuctType", DuctType),
    ("DuctLeakageTestMethod", DuctLeakageTestMethod),
    ("DuctPressureTestLeakageRate", DuctPressureTestLeakageRate),
    ("SupplyFractionOfDuctLeakage", SupplyFractionOfDuctLeakage),
    ("DuctPressureTestLeakagePercentage", DuctPressureTestLeakagePercentage),
    ("Quantity", Quantity),
    ("Location", Location),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("HeatingDeliveryID", HeatingDeliveryID),
    ("CoolingDeliveryID", CoolingDeliveryID),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
]

# ControlLightingType
class ControlLightingType(BSElement):
    """An instance of a lighting control technology."""

    class AdvancedPowerStrip(BSElement):
        class ControlStrategy(ControlStrategyLightingType):
            """Controller strategy."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class Manual(BSElement):
        """Type of manual controls used to manage lighting."""

        class ControlStrategy(BSElement):
            """Manual lighting control strategy."""

            element_type = "xs:string"
            element_enumerations = [
                "Always On",
                "Always Off",
                "Manual On/Off",
                "Manual Dimming",
                "Bi-level Control",
                "Tri-level Control",
                "Other",
                "None",
                "Unknown",
            ]

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class Occupancy(BSElement):
        """Type of occupancy controls used to manage lighting."""

        class ControlSensor(BSElement):
            """Type of sensor for detecting occupancy."""

            element_type = "xs:string"
            element_enumerations = [
                "Passive infrared",
                "Ultrasonic",
                "Passive infrared and ultrasonic",
                "Microwave",
                "Camera",
                "Other",
                "Unknown",
            ]

        class ControlStrategy(ControlStrategyOccupancyType):
            """Occupancy-based control strategy."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class Timer(BSElement):
        """Type of timer-based controls for managing lighting on specified timed intervals."""

        class ControlStrategy(ControlStrategyLightingType):
            """Timer-based control strategy for lighting."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"

    class OtherControlTechnology(BSElement):
        class OtherControlTechnologyName(BSElement):
            """Name of the other control technology used."""

            element_type = "xs:string"

        class ControlStrategy(ControlStrategyLightingType):
            """Control strategy used for other control technology."""

        class OtherControlStrategyName(BSElement):
            """If ControlStrategy is other, then the name of the strategy used."""

            element_type = "xs:string"


ControlLightingType.element_children = [
    ("AdvancedPowerStrip", ControlLightingType.AdvancedPowerStrip),
    ("Daylighting", Daylighting),
    ("Manual", ControlLightingType.Manual),
    ("Occupancy", ControlLightingType.Occupancy),
    ("Timer", ControlLightingType.Timer),
    ("OtherControlTechnology", ControlLightingType.OtherControlTechnology),
]
ControlLightingType.AdvancedPowerStrip.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlStrategy", ControlLightingType.AdvancedPowerStrip.ControlStrategy),
    (
        "OtherControlStrategyName",
        ControlLightingType.AdvancedPowerStrip.OtherControlStrategyName,
    ),
]
ControlLightingType.Manual.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlStrategy", ControlLightingType.Manual.ControlStrategy),
    ("OtherControlStrategyName", ControlLightingType.Manual.OtherControlStrategyName),
]
ControlLightingType.Occupancy.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlSensor", ControlLightingType.Occupancy.ControlSensor),
    ("ControlStrategy", ControlLightingType.Occupancy.ControlStrategy),
    (
        "OtherControlStrategyName",
        ControlLightingType.Occupancy.OtherControlStrategyName,
    ),
]
ControlLightingType.Timer.element_children = [
    ("ControlSystemType", ControlSystemType),
    ("ControlStrategy", ControlLightingType.Timer.ControlStrategy),
    ("OtherControlStrategyName", ControlLightingType.Timer.OtherControlStrategyName),
]
ControlLightingType.OtherControlTechnology.element_children = [
    ("ControlSystemType", ControlSystemType),
    (
        "OtherControlTechnologyName",
        ControlLightingType.OtherControlTechnology.OtherControlTechnologyName,
    ),
    ("ControlStrategy", ControlLightingType.OtherControlTechnology.ControlStrategy),
    (
        "OtherControlStrategyName",
        ControlLightingType.OtherControlTechnology.OtherControlStrategyName,
    ),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource.Solar
class Solar(BSElement):
    class Controls(BSElement):
        """List of controls for solar hot water."""

        class Control(ControlGeneralType):
            """Solar hot water control."""


Solar.element_children = [
    ("SolarThermalSystemType", SolarThermalSystemType),
    ("SolarThermalSystemCollectorArea", SolarThermalSystemCollectorArea),
    ("SolarThermalSystemCollectorLoopType", SolarThermalSystemCollectorLoopType),
    ("SolarThermalSystemCollectorType", SolarThermalSystemCollectorType),
    ("SolarThermalSystemCollectorAzimuth", SolarThermalSystemCollectorAzimuth),
    ("SolarThermalSystemCollectorTilt", SolarThermalSystemCollectorTilt),
    ("SolarThermalSystemStorageVolume", SolarThermalSystemStorageVolume),
    ("Controls", Solar.Controls),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
]
Solar.Controls.element_children = [
    ("Control", Solar.Controls.Control),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect.IndirectTankHeatingSource
class IndirectTankHeatingSource(BSElement):
    """Source of heat for indirect-fired hot water tank."""

    class HeatPump(BSElement):
        pass

    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


IndirectTankHeatingSource.element_children = [
    ("HeatPump", IndirectTankHeatingSource.HeatPump),
    ("Solar", Solar),
    ("SpaceHeatingSystem", SpaceHeatingSystem),
    ("Other", IndirectTankHeatingSource.Other),
    ("Unknown", IndirectTankHeatingSource.Unknown),
]
IndirectTankHeatingSource.HeatPump.element_children = [
    ("RatedHeatPumpSensibleHeatRatio", RatedHeatPumpSensibleHeatRatio),
    ("HPWHMinimumAirTemperature", HPWHMinimumAirTemperature),
    ("Refrigerant", Refrigerant),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType.Indirect
class Indirect(BSElement):
    pass


Indirect.element_children = [
    ("IndirectTankHeatingSource", IndirectTankHeatingSource),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank.TankHeatingType
class TankHeatingType(BSElement):
    """Direct or indirect heating of hot water tank."""

    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


TankHeatingType.element_children = [
    ("Direct", Direct),
    ("Indirect", Indirect),
    ("Other", TankHeatingType.Other),
    ("Unknown", TankHeatingType.Unknown),
]

# DomesticHotWaterSystemType.DomesticHotWaterType.StorageTank
class StorageTank(BSElement):
    pass


StorageTank.element_children = [
    ("TankHeatingType", TankHeatingType),
    ("TankVolume", TankVolume),
    ("TankHeight", TankHeight),
    ("TankPerimeter", TankPerimeter),
    ("RecoveryEfficiency", RecoveryEfficiency),
    ("StorageTankInsulationRValue", StorageTankInsulationRValue),
    ("StorageTankInsulationThickness", StorageTankInsulationThickness),
    ("OffCycleHeatLossCoefficient", OffCycleHeatLossCoefficient),
]

# CalculationMethodType
class CalculationMethodType(BSElement):
    class Other(OtherType):
        pass


CalculationMethodType.element_children = [
    ("Modeled", Modeled),
    ("Measured", Measured),
    ("Estimated", Estimated),
    ("EngineeringCalculation", EngineeringCalculation),
    ("Other", CalculationMethodType.Other),
]

# DerivedModelType.SavingsSummaries
class SavingsSummaries(BSElement):
    pass


SavingsSummaries.element_children = [
    ("SavingsSummary", SavingsSummary),
]

# DerivedModelType.Models.Model.DerivedModelInputs.ExplanatoryVariables.ExplanatoryVariable.ExplanatoryVariableUnits
class ExplanatoryVariableUnits(UnitsType):
    pass


# DerivedModelType.Models.Model.DerivedModelInputs.ExplanatoryVariables.ExplanatoryVariable
class ExplanatoryVariable(BSElement):
    pass


ExplanatoryVariable.element_children = [
    ("ExplanatoryVariableName", ExplanatoryVariableName),
    ("ExplanatoryVariableUnits", ExplanatoryVariableUnits),
]

# DerivedModelType.Models.Model.DerivedModelInputs.ExplanatoryVariables
class ExplanatoryVariables(BSElement):
    pass


ExplanatoryVariables.element_children = [
    ("ExplanatoryVariable", ExplanatoryVariable),
]

# DerivedModelType.Models.Model.DerivedModelInputs
class DerivedModelInputs(BSElement):
    class IntervalFrequency(IntervalFrequencyType):
        pass


DerivedModelInputs.element_children = [
    ("IntervalFrequency", DerivedModelInputs.IntervalFrequency),
    ("ResponseVariable", ResponseVariable),
    ("ExplanatoryVariables", ExplanatoryVariables),
]

# DerivedModelType.Models.Model
class Model(BSElement):
    class StartTimestamp(BSElement):
        element_type = "xs:dateTime"

    class EndTimestamp(BSElement):
        element_type = "xs:dateTime"


Model.element_attributes = [
    "ID",  # ID
]
Model.element_children = [
    ("StartTimestamp", Model.StartTimestamp),
    ("EndTimestamp", Model.EndTimestamp),
    ("DerivedModelInputs", DerivedModelInputs),
    ("DerivedModelCoefficients", DerivedModelCoefficients),
    ("DerivedModelPerformance", DerivedModelPerformance),
    ("SummaryInformation", SummaryInformation),
    ("ModeledTimeSeriesData", ModeledTimeSeriesData),
]

# CookingSystemType
class CookingSystemType(BSElement):
    pass


CookingSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
CookingSystemType.element_children = [
    ("TypeOfCookingEquipment", TypeOfCookingEquipment),
    ("NumberOfMeals", NumberOfMeals),
    ("CookingEnergyPerMeal", CookingEnergyPerMeal),
    ("DailyWaterUse", DailyWaterUse),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]

# RefrigerationSystemType
class RefrigerationSystemType(BSElement):
    pass


RefrigerationSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
RefrigerationSystemType.element_children = [
    ("RefrigerationSystemCategory", RefrigerationSystemCategory),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]

# BuildingSync.Facilities.Facility.Systems.WallSystems.WallSystem
class WallSystem(WallSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.WallSystems
class WallSystems(BSElement):
    pass


WallSystems.element_children = [
    ("WallSystem", WallSystem),
]

# BuildingSync.Facilities.Facility.Systems.RoofSystems.RoofSystem
class RoofSystem(RoofSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.RoofSystems
class RoofSystems(BSElement):
    pass


RoofSystems.element_children = [
    ("RoofSystem", RoofSystem),
]

# BuildingSync.Facilities.Facility.Systems.CeilingSystems.CeilingSystem
class CeilingSystem(CeilingSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.CeilingSystems
class CeilingSystems(BSElement):
    pass


CeilingSystems.element_children = [
    ("CeilingSystem", CeilingSystem),
]

# BuildingSync.Facilities.Facility.Systems.FenestrationSystems.FenestrationSystem
class FenestrationSystem(FenestrationSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.FenestrationSystems
class FenestrationSystems(BSElement):
    pass


FenestrationSystems.element_children = [
    ("FenestrationSystem", FenestrationSystem),
]

# BuildingSync.Facilities.Facility.Systems.ExteriorFloorSystems.ExteriorFloorSystem
class ExteriorFloorSystem(ExteriorFloorSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.ExteriorFloorSystems
class ExteriorFloorSystems(BSElement):
    pass


ExteriorFloorSystems.element_children = [
    ("ExteriorFloorSystem", ExteriorFloorSystem),
]

# BuildingSync.Facilities.Facility.Systems.FoundationSystems.FoundationSystem
class FoundationSystem(FoundationSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.FoundationSystems
class FoundationSystems(BSElement):
    pass


FoundationSystems.element_children = [
    ("FoundationSystem", FoundationSystem),
]

# BuildingSync.Facilities.Facility.Systems.AirInfiltrationSystems.AirInfiltrationSystem
class AirInfiltrationSystem(BSElement):
    """Description of the infiltration characteristics for an opaque surface, fenestration unit, a thermal zone."""

    class Tightness(Tightness):
        """Description of the infiltration characteristics for an opaque surface, fenestration unit, a thermal zone."""


AirInfiltrationSystem.element_attributes = [
    "ID",  # ID
]
AirInfiltrationSystem.element_children = [
    ("AirInfiltrationNotes", AirInfiltrationNotes),
    ("Tightness", AirInfiltrationSystem.Tightness),
    ("AirInfiltrationValue", AirInfiltrationValue),
    ("AirInfiltrationValueUnits", AirInfiltrationValueUnits),
    ("AirInfiltrationTest", AirInfiltrationTest),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
]

# BuildingSync.Facilities.Facility.Systems.AirInfiltrationSystems
class AirInfiltrationSystems(BSElement):
    pass


AirInfiltrationSystems.element_children = [
    ("AirInfiltrationSystem", AirInfiltrationSystem),
]

# BuildingSync.Facilities.Facility.Schedules.Schedule
class Schedule(ScheduleType):
    pass


# BuildingSync.Facilities.Facility.Schedules
class Schedules(BSElement):
    pass


Schedules.element_children = [
    ("Schedule", Schedule),
]

# BuildingSync.Facilities.Facility.Contacts.Contact
class Contact(ContactType):
    pass


# BuildingSync.Facilities.Facility.Contacts
class Contacts(BSElement):
    pass


Contacts.element_children = [
    ("Contact", Contact),
]

# BuildingSync.Facilities.Facility.Tenants.Tenant
class Tenant(TenantType):
    pass


# BuildingSync.Facilities.Facility.Tenants
class Tenants(BSElement):
    pass


Tenants.element_children = [
    ("Tenant", Tenant),
]

# ThermalZoneType.Spaces
class Spaces(BSElement):
    """Areas of a building that share systems characteristics such as occupancy, plug loads, or lighting."""

    class Space(SpaceType):
        pass


Spaces.element_children = [
    ("Space", Spaces.Space),
]

# ScenarioType.TimeSeriesData
class TimeSeriesData(BSElement):
    class TimeSeries(TimeSeriesType):
        pass


TimeSeriesData.element_children = [
    ("TimeSeries", TimeSeriesData.TimeSeries),
]

# ScenarioType.AllResourceTotals
class AllResourceTotals(BSElement):
    pass


AllResourceTotals.element_children = [
    ("AllResourceTotal", AllResourceTotal),
]

# CalculationMethod
class CalculationMethod(CalculationMethodType):
    """Method used to determine energy use."""


# ScenarioType.ScenarioType.Benchmark.BenchmarkType.CodeMinimum
class CodeMinimum(BSElement):
    pass


CodeMinimum.element_children = [
    ("CodeName", CodeName),
    ("CodeVersion", CodeVersion),
    ("CodeYear", CodeYear),
    ("CalculationMethod", CalculationMethod),
]

# ScenarioType.ScenarioType.Benchmark.BenchmarkType.StandardPractice
class StandardPractice(BSElement):
    pass


StandardPractice.element_children = [
    ("StandardPracticeDescription", StandardPracticeDescription),
    ("CalculationMethod", CalculationMethod),
]

# ScenarioType.ScenarioType.Benchmark.BenchmarkType
class BenchmarkType(BSElement):
    """Source of energy data or building characteristics for benchmarking energy performance."""

    class PortfolioManager(PortfolioManagerType):
        pass

    class CBECS(CBECSType):
        pass

    class Other(BSElement):
        pass


BenchmarkType.element_children = [
    ("PortfolioManager", BenchmarkType.PortfolioManager),
    ("CBECS", BenchmarkType.CBECS),
    ("CodeMinimum", CodeMinimum),
    ("StandardPractice", StandardPractice),
    ("Other", BenchmarkType.Other),
]
BenchmarkType.Other.element_children = [
    ("OtherBenchmarkDescription", OtherBenchmarkDescription),
    ("CalculationMethod", CalculationMethod),
]

# ScenarioType.ScenarioType.Benchmark
class Benchmark(BSElement):
    pass


Benchmark.element_children = [
    ("BenchmarkType", BenchmarkType),
    ("BenchmarkTool", BenchmarkTool),
    ("BenchmarkYear", BenchmarkYear),
    ("BenchmarkValue", BenchmarkValue),
    ("LinkedPremises", LinkedPremises),
]

# ScenarioType.ScenarioType.PackageOfMeasures
class PackageOfMeasures(BSElement):
    class AnnualSavingsSiteEnergy(BSElement):
        """Site energy savings per year. (MMBtu/year)"""

        element_type = "xs:decimal"

    class AnnualSavingsSourceEnergy(BSElement):
        """Source energy savings per year. (MMBtu/year)"""

        element_type = "xs:decimal"

    class AnnualSavingsCost(BSElement):
        """Cost savings per year, including energy, demand, change in rate schedule, and other cost impacts on utility bills. ($/year)"""

        element_type = "xs:integer"

    class AnnualSavingsByFuels(BSElement):
        class AnnualSavingsByFuel(BSElement):
            class AnnualSavingsNativeUnits(BSElement):
                """Site energy savings per year for this resource type, in the original units. (units/yr)"""

                element_type = "xs:decimal"

    class SummerPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the summer months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class WinterPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the winter months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class AnnualPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the year as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class AnnualDemandSavingsCost(BSElement):
        """Cost savings per year due to reduction in peak electricity demand. ($/year)"""

        element_type = "xs:integer"

    class AnnualWaterSavings(BSElement):
        """Total annual water savings (hot and cold). (gal/year)"""

        element_type = "xs:decimal"

    class AnnualWaterCostSavings(BSElement):
        """Total annual reduction in water costs, not including water heating costs (hot and cold). ($/year)"""

        element_type = "xs:decimal"

    class MVCost(BSElement):
        """Annual cost to verify energy savings. ($/year)"""

        element_type = "xs:decimal"

    class OMCostAnnualSavings(BSElement):
        """Annual cost savings for operation, maintenance, and repair. ($)"""

        element_type = "xs:decimal"

    class EquipmentDisposalAndSalvageCosts(BSElement):
        """The net cost of disposing of equipment being replaced or removed. In some cases the salvage value may exceed disposal costs, resulting in a negative value. ($)"""

        element_type = "xs:decimal"

    class FundingFromIncentives(BSElement):
        """Funding obtained through incentives to implement the measure or project. ($)"""

        element_type = "xs:decimal"

    class FundingFromTaxCredits(BSElement):
        """Funding obtained through utility or state tax credits to implement the measure or project. ($)"""

        element_type = "xs:decimal"

    class NPVofTaxImplications(BSElement):
        """Net present value of impacts on depreciation and other tax deductions. ($)"""

        element_type = "xs:decimal"

    class SimplePayback(BSElement):
        """The length of time required for the investment to pay for itself. (yrs)"""

        element_type = "xs:decimal"

    class NetPresentValue(BSElement):
        """Net Present Value (NPV) of measure or package. ($)"""

        element_type = "xs:decimal"

    class InternalRateOfReturn(BSElement):
        """Internal rate of return (IRR) of measure or package. (%)"""

        element_type = "xs:decimal"


PackageOfMeasures.element_attributes = [
    "ID",  # ID
]
PackageOfMeasures.element_children = [
    ("ReferenceCase", ReferenceCase),
    ("MeasureIDs", MeasureIDs),
    ("CostCategory", CostCategory),
    ("SimpleImpactAnalysis", SimpleImpactAnalysis),
    ("CalculationMethod", CalculationMethod),
    ("AnnualSavingsSiteEnergy", PackageOfMeasures.AnnualSavingsSiteEnergy),
    ("AnnualSavingsSourceEnergy", PackageOfMeasures.AnnualSavingsSourceEnergy),
    ("AnnualSavingsCost", PackageOfMeasures.AnnualSavingsCost),
    ("AnnualSavingsByFuels", PackageOfMeasures.AnnualSavingsByFuels),
    (
        "SummerPeakElectricityReduction",
        PackageOfMeasures.SummerPeakElectricityReduction,
    ),
    (
        "WinterPeakElectricityReduction",
        PackageOfMeasures.WinterPeakElectricityReduction,
    ),
    (
        "AnnualPeakElectricityReduction",
        PackageOfMeasures.AnnualPeakElectricityReduction,
    ),
    ("AnnualDemandSavingsCost", PackageOfMeasures.AnnualDemandSavingsCost),
    ("AnnualWaterSavings", PackageOfMeasures.AnnualWaterSavings),
    ("AnnualWaterCostSavings", PackageOfMeasures.AnnualWaterCostSavings),
    ("ImplementationPeriod", ImplementationPeriod),
    ("PackageFirstCost", PackageFirstCost),
    ("MVCost", PackageOfMeasures.MVCost),
    ("OMCostAnnualSavings", PackageOfMeasures.OMCostAnnualSavings),
    (
        "EquipmentDisposalAndSalvageCosts",
        PackageOfMeasures.EquipmentDisposalAndSalvageCosts,
    ),
    ("ImplementationPeriodCostSavings", ImplementationPeriodCostSavings),
    ("PercentGuaranteedSavings", PercentGuaranteedSavings),
    ("ProjectMarkup", ProjectMarkup),
    ("FundingFromIncentives", PackageOfMeasures.FundingFromIncentives),
    ("FundingFromTaxCredits", PackageOfMeasures.FundingFromTaxCredits),
    ("OtherFinancialIncentives", OtherFinancialIncentives),
    ("RecurringIncentives", RecurringIncentives),
    ("NPVofTaxImplications", PackageOfMeasures.NPVofTaxImplications),
    ("CostEffectivenessScreeningMethod", CostEffectivenessScreeningMethod),
    ("SimplePayback", PackageOfMeasures.SimplePayback),
    ("NetPresentValue", PackageOfMeasures.NetPresentValue),
    ("InternalRateOfReturn", PackageOfMeasures.InternalRateOfReturn),
    ("NonquantifiableFactors", NonquantifiableFactors),
    ("AssetScore", AssetScore),
    ("ENERGYSTARScore", ENERGYSTARScore),
    ("UserDefinedFields", UserDefinedFields),
]
PackageOfMeasures.AnnualSavingsByFuels.element_children = [
    ("AnnualSavingsByFuel", PackageOfMeasures.AnnualSavingsByFuels.AnnualSavingsByFuel),
]
PackageOfMeasures.AnnualSavingsByFuels.AnnualSavingsByFuel.element_children = [
    ("EnergyResource", EnergyResource),
    ("ResourceUnits", ResourceUnits),
    (
        "AnnualSavingsNativeUnits",
        PackageOfMeasures.AnnualSavingsByFuels.AnnualSavingsByFuel.AnnualSavingsNativeUnits,
    ),
]

# ScenarioType.ResourceUses.ResourceUse
class ResourceUse(ResourceUseType):
    pass


# MeasureType.MeasureSavingsAnalysis
class MeasureSavingsAnalysis(BSElement):
    """Energy and cost effectiveness data for an individual measure. In most cases, this data depends on the other measures included in the package, and should be entered at the package level under Scenarios."""

    class AnnualSavingsSiteEnergy(BSElement):
        """Site energy savings per year. (MMBtu/year)"""

        element_type = "xs:decimal"

    class AnnualSavingsSourceEnergy(BSElement):
        """Source energy savings per year. (MMBtu/year)"""

        element_type = "xs:decimal"

    class AnnualSavingsCost(BSElement):
        """Cost savings per year, including energy, demand, change in rate schedule, and other cost impacts on utility bills. ($/year)"""

        element_type = "xs:integer"

    class AnnualSavingsByFuels(BSElement):
        class AnnualSavingsByFuel(BSElement):
            class AnnualSavingsNativeUnits(BSElement):
                """Site energy savings per year for this resource type, in the original units. (units/yr)"""

                element_type = "xs:decimal"

    class SummerPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the summer months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class WinterPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the winter months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class AnnualPeakElectricityReduction(BSElement):
        """Reduction in largest 15 minute peak demand for the year as defined in the utility rate schedule (for electrical energy use only). (kW)"""

        element_type = "xs:decimal"

    class AnnualDemandSavingsCost(BSElement):
        """Cost savings per year due to reduction in peak electricity demand. ($/year)"""

        element_type = "xs:integer"

    class AnnualWaterSavings(BSElement):
        """Total annual water savings (hot and cold). (gal/year)"""

        element_type = "xs:decimal"

    class AnnualWaterCostSavings(BSElement):
        """Total annual reduction in water costs, not including water heating costs (hot and cold). ($/year)"""

        element_type = "xs:decimal"

    class OMCostAnnualSavings(BSElement):
        """Annual cost savings for operation, maintenance, and repair. ($)"""

        element_type = "xs:decimal"

    class EquipmentDisposalAndSalvageCosts(BSElement):
        """The net cost of disposing of equipment being replaced or removed. In some cases the salvage value may exceed disposal costs, resulting in a negative value. ($)"""

        element_type = "xs:decimal"

    class FundingFromIncentives(BSElement):
        """Funding obtained through incentives to implement the measure or project. ($)"""

        element_type = "xs:decimal"

    class FundingFromTaxCredits(BSElement):
        """Funding obtained through utility or state tax credits to implement the measure or project. ($)"""

        element_type = "xs:decimal"

    class NPVofTaxImplications(BSElement):
        """Net present value of impacts on depreciation and other tax deductions. ($)"""

        element_type = "xs:decimal"

    class SimplePayback(BSElement):
        """The length of time required for the investment to pay for itself. (yrs)"""

        element_type = "xs:decimal"

    class NetPresentValue(BSElement):
        """Net Present Value (NPV) of measure or package. ($)"""

        element_type = "xs:decimal"

    class InternalRateOfReturn(BSElement):
        """Internal rate of return (IRR) of measure or package. (%)"""

        element_type = "xs:decimal"


MeasureSavingsAnalysis.element_children = [
    ("MeasureRank", MeasureRank),
    ("ReferenceCase", ReferenceCase),
    ("CalculationMethod", CalculationMethod),
    ("AnnualSavingsSiteEnergy", MeasureSavingsAnalysis.AnnualSavingsSiteEnergy),
    ("AnnualSavingsSourceEnergy", MeasureSavingsAnalysis.AnnualSavingsSourceEnergy),
    ("AnnualSavingsCost", MeasureSavingsAnalysis.AnnualSavingsCost),
    ("AnnualSavingsByFuels", MeasureSavingsAnalysis.AnnualSavingsByFuels),
    (
        "SummerPeakElectricityReduction",
        MeasureSavingsAnalysis.SummerPeakElectricityReduction,
    ),
    (
        "WinterPeakElectricityReduction",
        MeasureSavingsAnalysis.WinterPeakElectricityReduction,
    ),
    (
        "AnnualPeakElectricityReduction",
        MeasureSavingsAnalysis.AnnualPeakElectricityReduction,
    ),
    ("AnnualDemandSavingsCost", MeasureSavingsAnalysis.AnnualDemandSavingsCost),
    ("AnnualWaterSavings", MeasureSavingsAnalysis.AnnualWaterSavings),
    ("AnnualWaterCostSavings", MeasureSavingsAnalysis.AnnualWaterCostSavings),
    ("OMCostAnnualSavings", MeasureSavingsAnalysis.OMCostAnnualSavings),
    ("OtherCostAnnualSavings", OtherCostAnnualSavings),
    (
        "EquipmentDisposalAndSalvageCosts",
        MeasureSavingsAnalysis.EquipmentDisposalAndSalvageCosts,
    ),
    ("FundingFromIncentives", MeasureSavingsAnalysis.FundingFromIncentives),
    ("FundingFromTaxCredits", MeasureSavingsAnalysis.FundingFromTaxCredits),
    ("NPVofTaxImplications", MeasureSavingsAnalysis.NPVofTaxImplications),
    ("CostEffectivenessScreeningMethod", CostEffectivenessScreeningMethod),
    ("SimplePayback", MeasureSavingsAnalysis.SimplePayback),
    ("NetPresentValue", MeasureSavingsAnalysis.NetPresentValue),
    ("InternalRateOfReturn", MeasureSavingsAnalysis.InternalRateOfReturn),
]
MeasureSavingsAnalysis.AnnualSavingsByFuels.element_children = [
    (
        "AnnualSavingsByFuel",
        MeasureSavingsAnalysis.AnnualSavingsByFuels.AnnualSavingsByFuel,
    ),
]
MeasureSavingsAnalysis.AnnualSavingsByFuels.AnnualSavingsByFuel.element_children = [
    ("EnergyResource", EnergyResource),
    ("ResourceUnits", ResourceUnits),
    (
        "AnnualSavingsNativeUnits",
        MeasureSavingsAnalysis.AnnualSavingsByFuels.AnnualSavingsByFuel.AnnualSavingsNativeUnits,
    ),
]

# ReportType.Utilities
class Utilities(BSElement):
    pass


Utilities.element_children = [
    ("Utility", Utility),
]

# HeatingPlantType
class HeatingPlantType(BSElement):
    class PrimaryFuel(FuelTypes):
        """Main fuel used by the HeatingPlant."""

    class ControlSystemTypes(BSElement):
        """HeatingPlant equipment control strategies."""


HeatingPlantType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
HeatingPlantType.element_children = [
    ("HeatingPlantCondition", HeatingPlantCondition),
    ("Location", Location),
    ("YearInstalled", YearInstalled),
    ("PrimaryFuel", HeatingPlantType.PrimaryFuel),
    ("BuildingAutomationSystem", BuildingAutomationSystem),
    ("ControlSystemTypes", HeatingPlantType.ControlSystemTypes),
    ("UserDefinedFields", UserDefinedFields),
]
HeatingPlantType.ControlSystemTypes.element_children = [
    ("ControlSystemType", ControlSystemType),
]

# HVACSystemType.Plants.CoolingPlants.CoolingPlant
class CoolingPlant(CoolingPlantType):
    """Type of cooling plant. Zonal cooling is recorded in a separate data field. Use of fans or blowers by themselves without chilled air or water is not included in this definition of cooling. Stand-alone dehumidifiers are also not included."""


# HVACSystemType.Plants.CoolingPlants
class CoolingPlants(BSElement):
    pass


CoolingPlants.element_children = [
    ("CoolingPlant", CoolingPlant),
]

# HVACSystemType.Plants.CondenserPlants.CondenserPlant
class CondenserPlant(CondenserPlantType):
    """Type of condenser used for refrigerant-based systems."""


# HVACSystemType.Plants.CondenserPlants
class CondenserPlants(BSElement):
    pass


CondenserPlants.element_children = [
    ("CondenserPlant", CondenserPlant),
]

# HVACSystemType.HeatingAndCoolingSystems.HeatingSources.HeatingSource
class HeatingSource(BSElement):
    class Controls(BSElement):
        """List of controls for HeatingSource."""

        class Control(ControlGeneralType):
            """Control for HeatingSource."""


HeatingSource.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
HeatingSource.element_children = [
    ("HeatingSourceType", HeatingSourceType),
    ("HeatingMedium", HeatingMedium),
    ("AnnualHeatingEfficiencyValue", AnnualHeatingEfficiencyValue),
    ("AnnualHeatingEfficiencyUnits", AnnualHeatingEfficiencyUnits),
    ("InputCapacity", InputCapacity),
    ("CapacityUnits", CapacityUnits),
    ("HeatingStaging", HeatingStaging),
    ("NumberOfHeatingStages", NumberOfHeatingStages),
    ("HeatingStageCapacityFraction", HeatingStageCapacityFraction),
    ("PrimaryFuel", PrimaryFuel),
    ("HeatingSourceCondition", HeatingSourceCondition),
    ("Controls", HeatingSource.Controls),
    ("Location", Location),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
HeatingSource.Controls.element_children = [
    ("Control", HeatingSource.Controls.Control),
]

# HVACSystemType.HeatingAndCoolingSystems.HeatingSources
class HeatingSources(BSElement):
    pass


HeatingSources.element_children = [
    ("HeatingSource", HeatingSource),
]

# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType.ZoneEquipment
class ZoneEquipment(BSElement):
    """A type of HVAC equipment serving a single thermal zone, such as a hotel room PTHP/PTAC."""

    class FanBased(FanBasedType):
        pass

    class Other(OtherType):
        pass


ZoneEquipment.element_children = [
    ("FanBased", ZoneEquipment.FanBased),
    ("Convection", Convection),
    ("Radiant", Radiant),
    ("Other", ZoneEquipment.Other),
]

# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery.DeliveryType
class DeliveryType(BSElement):
    class Other(OtherType):
        pass


DeliveryType.element_children = [
    ("ZoneEquipment", ZoneEquipment),
    ("CentralAirDistribution", CentralAirDistribution),
    ("Other", DeliveryType.Other),
]

# HVACSystemType.HeatingAndCoolingSystems.Deliveries.Delivery
class Delivery(BSElement):
    class CoolingSourceID(BSElement):
        """ID number of the CoolingSource associated with this delivery mechanism."""

    class Controls(BSElement):
        """List of controls for DeliverySystem."""

        class Control(ControlGeneralType):
            """DeliverySystem control."""


Delivery.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
Delivery.element_children = [
    ("DeliveryType", DeliveryType),
    ("HeatingSourceID", HeatingSourceID),
    ("CoolingSourceID", Delivery.CoolingSourceID),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("PrimaryFuel", PrimaryFuel),
    ("Controls", Delivery.Controls),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("DeliveryCondition", DeliveryCondition),
]
Delivery.CoolingSourceID.element_attributes = [
    "IDref",  # IDREF
]
Delivery.Controls.element_children = [
    ("Control", Delivery.Controls.Control),
]

# HVACSystemType.HeatingAndCoolingSystems.Deliveries
class Deliveries(BSElement):
    pass


Deliveries.element_children = [
    ("Delivery", Delivery),
]

# HVACSystemType.DuctSystems.DuctSystem
class DuctSystem(DuctSystemType):
    pass


# DomesticHotWaterSystemType.DomesticHotWaterType
class DomesticHotWaterType(BSElement):
    """Type of water heating equipment for hot running water."""

    class Other(OtherType):
        pass

    class Unknown(UnknownType):
        pass


DomesticHotWaterType.element_children = [
    ("StorageTank", StorageTank),
    ("Instantaneous", Instantaneous),
    ("HeatExchanger", HeatExchanger),
    ("Other", DomesticHotWaterType.Other),
    ("Unknown", DomesticHotWaterType.Unknown),
]

# PoolType.Heated
class Heated(BSElement):
    """If exists then the pool is heated."""

    class Controls(BSElement):
        """List of controls for heated pool."""

        class Control(ControlGeneralType):
            """Heated pool control."""


Heated.element_children = [
    ("PrimaryFuel", PrimaryFuel),
    ("WaterTemperature", WaterTemperature),
    ("HoursUncovered", HoursUncovered),
    ("Controls", Heated.Controls),
]
Heated.Controls.element_children = [
    ("Control", Heated.Controls.Control),
]

# DerivedModelType.Models
class Models(BSElement):
    pass


Models.element_children = [
    ("Model", Model),
]

# DomesticHotWaterSystemType
class DomesticHotWaterSystemType(BSElement):
    class Controls(BSElement):
        """List of controls for domestic hot water."""

        class Control(ControlGeneralType):
            """Domestic hot water control."""


DomesticHotWaterSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
DomesticHotWaterSystemType.element_children = [
    ("DomesticHotWaterType", DomesticHotWaterType),
    ("DomesticHotWaterSystemNotes", DomesticHotWaterSystemNotes),
    ("Recirculation", Recirculation),
    ("HotWaterDistributionType", HotWaterDistributionType),
    ("WaterHeaterEfficiencyType", WaterHeaterEfficiencyType),
    ("WaterHeaterEfficiency", WaterHeaterEfficiency),
    ("DailyHotWaterDraw", DailyHotWaterDraw),
    ("HotWaterSetpointTemperature", HotWaterSetpointTemperature),
    ("ParasiticFuelConsumptionRate", ParasiticFuelConsumptionRate),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Controls", DomesticHotWaterSystemType.Controls),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("DomesticHotWaterSystemCondition", DomesticHotWaterSystemCondition),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
DomesticHotWaterSystemType.Controls.element_children = [
    ("Control", DomesticHotWaterSystemType.Controls.Control),
]

# BuildingSync.Facilities.Facility.Systems.CookingSystems.CookingSystem
class CookingSystem(CookingSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.CookingSystems
class CookingSystems(BSElement):
    pass


CookingSystems.element_children = [
    ("CookingSystem", CookingSystem),
]

# BuildingSync.Facilities.Facility.Systems.RefrigerationSystems.RefrigerationSystem
class RefrigerationSystem(RefrigerationSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.RefrigerationSystems
class RefrigerationSystems(BSElement):
    pass


RefrigerationSystems.element_children = [
    ("RefrigerationSystem", RefrigerationSystem),
]

# DishwasherSystemType
class DishwasherSystemType(BSElement):
    class Controls(BSElement):
        """List of controls for dishwasher."""

        class Control(ControlGeneralType):
            """Dishwasher control."""


DishwasherSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
DishwasherSystemType.element_children = [
    ("DishwasherMachineType", DishwasherMachineType),
    ("DishwasherConfiguration", DishwasherConfiguration),
    ("DishwasherClassification", DishwasherClassification),
    ("DishwasherLoadsPerWeek", DishwasherLoadsPerWeek),
    ("DishwasherEnergyFactor", DishwasherEnergyFactor),
    ("DishwasherHotWaterUse", DishwasherHotWaterUse),
    ("Controls", DishwasherSystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
DishwasherSystemType.Controls.element_children = [
    ("Control", DishwasherSystemType.Controls.Control),
]

# LaundrySystemType
class LaundrySystemType(BSElement):
    class Controls(BSElement):
        """List of controls for laundry system."""

        class Control(ControlGeneralType):
            """LaundrySystem control."""


LaundrySystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
LaundrySystemType.element_children = [
    ("LaundryType", LaundryType),
    ("QuantityOfLaundry", QuantityOfLaundry),
    ("LaundryEquipmentUsage", LaundryEquipmentUsage),
    ("Controls", LaundrySystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
LaundrySystemType.Controls.element_children = [
    ("Control", LaundrySystemType.Controls.Control),
]

# PumpSystemType
class PumpSystemType(BSElement):
    class Controls(BSElement):
        """List of controls for pump system."""

        class Control(ControlGeneralType):
            """Pump system control."""

    class LinkedSystemIDs(BSElement):
        class LinkedSystemID(BSElement):
            """ID number of system(s) supported by this equipment."""


PumpSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
PumpSystemType.element_children = [
    ("PumpEfficiency", PumpEfficiency),
    ("PumpMaximumFlowRate", PumpMaximumFlowRate),
    ("PumpMinimumFlowRate", PumpMinimumFlowRate),
    ("PumpInstalledFlowRate", PumpInstalledFlowRate),
    ("PumpPowerDemand", PumpPowerDemand),
    ("PumpControlType", PumpControlType),
    ("PumpOperation", PumpOperation),
    ("PumpingConfiguration", PumpingConfiguration),
    ("PumpApplication", PumpApplication),
    ("Controls", PumpSystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedSystemIDs", PumpSystemType.LinkedSystemIDs),
    ("UserDefinedFields", UserDefinedFields),
]
PumpSystemType.Controls.element_children = [
    ("Control", PumpSystemType.Controls.Control),
]
PumpSystemType.LinkedSystemIDs.element_children = [
    ("LinkedSystemID", PumpSystemType.LinkedSystemIDs.LinkedSystemID),
]
PumpSystemType.LinkedSystemIDs.LinkedSystemID.element_attributes = [
    "IDref",  # IDREF
]

# FanSystemType
class FanSystemType(BSElement):
    class Controls(BSElement):
        """List of controls for FanSystem."""

        class Control(ControlGeneralType):
            """FanSystem control."""

    class LinkedSystemIDs(BSElement):
        class LinkedSystemID(BSElement):
            """ID number of system(s) supported by this equipment."""


FanSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
FanSystemType.element_children = [
    ("FanEfficiency", FanEfficiency),
    ("FanSize", FanSize),
    ("MinimumFlowRate", MinimumFlowRate),
    ("MaximumFanPower", MaximumFanPower),
    ("FanPowerMinimumRatio", FanPowerMinimumRatio),
    ("FanType", FanType),
    ("BeltType", BeltType),
    ("FanApplication", FanApplication),
    ("FanControlType", FanControlType),
    ("FanPlacement", FanPlacement),
    ("MotorLocationRelativeToAirStream", MotorLocationRelativeToAirStream),
    ("DesignStaticPressure", DesignStaticPressure),
    ("NumberOfDiscreteFanSpeedsCooling", NumberOfDiscreteFanSpeedsCooling),
    ("NumberOfDiscreteFanSpeedsHeating", NumberOfDiscreteFanSpeedsHeating),
    ("Controls", FanSystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("LinkedSystemIDs", FanSystemType.LinkedSystemIDs),
    ("UserDefinedFields", UserDefinedFields),
]
FanSystemType.Controls.element_children = [
    ("Control", FanSystemType.Controls.Control),
]
FanSystemType.LinkedSystemIDs.element_children = [
    ("LinkedSystemID", FanSystemType.LinkedSystemIDs.LinkedSystemID),
]
FanSystemType.LinkedSystemIDs.LinkedSystemID.element_attributes = [
    "IDref",  # IDREF
]

# MotorSystemType
class MotorSystemType(BSElement):
    class Controls(BSElement):
        """List of controls for MotorSystem."""

        class Control(ControlGeneralType):
            """MotorSystem control."""

    class LinkedSystemIDs(BSElement):
        class LinkedSystemID(BSElement):
            """ID number of system(s) supported by this equipment."""


MotorSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
MotorSystemType.element_children = [
    ("MotorRPM", MotorRPM),
    ("MotorBrakeHP", MotorBrakeHP),
    ("MotorHP", MotorHP),
    ("MotorEfficiency", MotorEfficiency),
    ("DriveEfficiency", DriveEfficiency),
    ("FullLoadAmps", FullLoadAmps),
    ("MotorPoleCount", MotorPoleCount),
    ("MotorEnclosureType", MotorEnclosureType),
    ("MotorApplication", MotorApplication),
    ("Controls", MotorSystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("LinkedSystemIDs", MotorSystemType.LinkedSystemIDs),
    ("UserDefinedFields", UserDefinedFields),
]
MotorSystemType.Controls.element_children = [
    ("Control", MotorSystemType.Controls.Control),
]
MotorSystemType.LinkedSystemIDs.element_children = [
    ("LinkedSystemID", MotorSystemType.LinkedSystemIDs.LinkedSystemID),
]
MotorSystemType.LinkedSystemIDs.LinkedSystemID.element_attributes = [
    "IDref",  # IDREF
]

# HeatRecoverySystemType
class HeatRecoverySystemType(BSElement):
    class Controls(BSElement):
        """List of controls for heat recovery system."""

        class Control(ControlGeneralType):
            """Heat recovery system control."""


HeatRecoverySystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
HeatRecoverySystemType.element_children = [
    ("HeatRecoveryEfficiency", HeatRecoveryEfficiency),
    ("EnergyRecoveryEfficiency", EnergyRecoveryEfficiency),
    ("HeatRecoveryType", HeatRecoveryType),
    ("SystemIDReceivingHeat", SystemIDReceivingHeat),
    ("SystemIDProvidingHeat", SystemIDProvidingHeat),
    ("Controls", HeatRecoverySystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("UserDefinedFields", UserDefinedFields),
]
HeatRecoverySystemType.Controls.element_children = [
    ("Control", HeatRecoverySystemType.Controls.Control),
]

# CriticalITSystemType
class CriticalITSystemType(BSElement):
    class Controls(BSElement):
        """List of controls for critical IT system."""

        class Control(ControlGeneralType):
            """Critical IT system control."""


CriticalITSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
CriticalITSystemType.element_children = [
    ("ITSystemType", ITSystemType),
    ("ITPeakPower", ITPeakPower),
    ("ITStandbyPower", ITStandbyPower),
    ("ITNominalPower", ITNominalPower),
    ("Controls", CriticalITSystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
CriticalITSystemType.Controls.element_children = [
    ("Control", CriticalITSystemType.Controls.Control),
]

# PlugElectricLoadType
class PlugElectricLoadType(BSElement):
    class WeightedAverageLoad(BSElement):
        """Weighted average electric load. (W/ft2)"""

        element_type = "xs:decimal"

    class Controls(BSElement):
        """List of plug load controls."""

        class Control(ControlGeneralType):
            """Plug load control."""


PlugElectricLoadType.element_attributes = [
    "ID",  # ID
    "Source",  # Source
    "Status",  # Status
]
PlugElectricLoadType.element_children = [
    ("PlugLoadType", PlugLoadType),
    ("PlugLoadPeakPower", PlugLoadPeakPower),
    ("PlugLoadStandbyPower", PlugLoadStandbyPower),
    ("PlugLoadNominalPower", PlugLoadNominalPower),
    ("WeightedAverageLoad", PlugElectricLoadType.WeightedAverageLoad),
    ("Controls", PlugElectricLoadType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
PlugElectricLoadType.Controls.element_children = [
    ("Control", PlugElectricLoadType.Controls.Control),
]

# ProcessGasElectricLoadType
class ProcessGasElectricLoadType(BSElement):
    class WeightedAverageLoad(BSElement):
        """Weighted average process load. (W/ft2)"""

        element_type = "xs:decimal"

    class Controls(BSElement):
        """List of process load controls."""

        class Control(ControlGeneralType):
            """Process load control."""


ProcessGasElectricLoadType.element_attributes = [
    "ID",  # ID
    "Source",  # Source
    "Status",  # Status
]
ProcessGasElectricLoadType.element_children = [
    ("ProcessLoadType", ProcessLoadType),
    ("ProcessLoadPeakPower", ProcessLoadPeakPower),
    ("ProcessLoadStandbyPower", ProcessLoadStandbyPower),
    ("WeightedAverageLoad", ProcessGasElectricLoadType.WeightedAverageLoad),
    ("HeatGainFraction", HeatGainFraction),
    ("DutyCycle", DutyCycle),
    ("Controls", ProcessGasElectricLoadType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
ProcessGasElectricLoadType.Controls.element_children = [
    ("Control", ProcessGasElectricLoadType.Controls.Control),
]

# ConveyanceSystemType
class ConveyanceSystemType(BSElement):
    class ConveyanceSystemType(BSElement):
        """Type of vertical or horizontal transportation equipment that moves people or goods between levels, floors, or sections."""

        element_type = "xs:string"
        element_enumerations = [
            "Escalator",
            "Elevator",
            "Conveyor Belt",
            "Overhead Conveyor",
            "Other",
            "Unknown",
        ]

    class Controls(BSElement):
        """List of conveyance system controls."""

        class Control(ControlGeneralType):
            """Conveyance system control."""


ConveyanceSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
ConveyanceSystemType.element_children = [
    ("ConveyanceSystemType", ConveyanceSystemType.ConveyanceSystemType),
    ("ConveyanceLoadType", ConveyanceLoadType),
    ("ConveyancePeakPower", ConveyancePeakPower),
    ("ConveyanceStandbyPower", ConveyanceStandbyPower),
    ("Controls", ConveyanceSystemType.Controls),
    ("ConveyanceSystemCondition", ConveyanceSystemCondition),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("PrimaryFuel", PrimaryFuel),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
]
ConveyanceSystemType.Controls.element_children = [
    ("Control", ConveyanceSystemType.Controls.Control),
]

# OnsiteStorageTransmissionGenerationSystemType
class OnsiteStorageTransmissionGenerationSystemType(BSElement):
    class Controls(BSElement):
        """List of onsite storage transmission controls."""

        class Control(ControlGeneralType):
            """Onsite storage transmission control."""


OnsiteStorageTransmissionGenerationSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
OnsiteStorageTransmissionGenerationSystemType.element_children = [
    ("EnergyConversionType", EnergyConversionType),
    ("BackupGenerator", BackupGenerator),
    ("DemandReduction", DemandReduction),
    ("Capacity", Capacity),
    ("CapacityUnits", CapacityUnits),
    ("Controls", OnsiteStorageTransmissionGenerationSystemType.Controls),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
OnsiteStorageTransmissionGenerationSystemType.Controls.element_children = [
    ("Control", OnsiteStorageTransmissionGenerationSystemType.Controls.Control),
]

# PoolType
class PoolType(BSElement):
    class PoolType(BSElement):
        """General category of the pool."""

        element_type = "xs:string"
        element_enumerations = ["Hot Tub", "Pool", "Other", "Unknown"]


PoolType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
PoolType.element_children = [
    ("PoolType", PoolType.PoolType),
    ("PoolSizeCategory", PoolSizeCategory),
    ("PoolArea", PoolArea),
    ("PoolVolume", PoolVolume),
    ("PumpDutyCycle", PumpDutyCycle),
    ("Heated", Heated),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Quantity", Quantity),
    ("YearInstalled", YearInstalled),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
]

# WaterUseType
class WaterUseType(BSElement):
    class WaterUseType(BSElement):
        """Short description of the water fixture or application."""

        element_type = "xs:string"
        element_enumerations = [
            "Restroom Sink Use",
            "Restroom Toilet/Urinal Water Use",
            "Kitchen Water Use",
            "Shower Facility Water Use",
            "Drinking Fountain Water Use",
            "Janitorial Water Use",
            "Laundry Water Use",
            "Indoor Washdown Water Use (if indoor)",
            "Outdoor Landscape Water Use",
            "Outdoor Non-Landscape Water Use",
            "Outdoor Washdown Water Use (if outdoor)",
            "Cooling Tower Make-up Water Use",
            "Hydronic Loop Make-up Water Use",
            "Evaporative Cooling System Water Use",
            "Pre-Treatment Process Water Use",
            "Captured Rain Water",
            "Recycled Greywater",
            "Condensate Recovery",
            "Stormwater Sewer Production",
            "Stormwater Discharge",
            "Other",
            "Unknown",
        ]

    class Controls(BSElement):
        """List of controls for water use system."""

        class Control(ControlGeneralType):
            """Control for water use."""


WaterUseType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
WaterUseType.element_children = [
    ("WaterUseType", WaterUseType.WaterUseType),
    ("WaterResource", WaterResource),
    ("LowFlowFixtures", LowFlowFixtures),
    ("WaterFixtureRatedFlowRate", WaterFixtureRatedFlowRate),
    ("WaterFixtureVolumePerCycle", WaterFixtureVolumePerCycle),
    ("WaterFixtureCyclesPerDay", WaterFixtureCyclesPerDay),
    ("WaterFixtureFractionHotWater", WaterFixtureFractionHotWater),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("Controls", WaterUseType.Controls),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
WaterUseType.Controls.element_children = [
    ("Control", WaterUseType.Controls.Control),
]

# MeasureType
class MeasureType(BSElement):
    class MVCost(BSElement):
        """Annual cost to verify energy savings. ($/year)"""

        element_type = "xs:decimal"


MeasureType.element_attributes = [
    "ID",  # ID
]
MeasureType.element_children = [
    ("TypeOfMeasure", TypeOfMeasure),
    ("SystemCategoryAffected", SystemCategoryAffected),
    ("LinkedPremises", LinkedPremises),
    ("TechnologyCategories", TechnologyCategories),
    ("MeasureScaleOfApplication", MeasureScaleOfApplication),
    ("CustomMeasureName", CustomMeasureName),
    ("LongDescription", LongDescription),
    ("MeasureSavingsAnalysis", MeasureSavingsAnalysis),
    ("MVCost", MeasureType.MVCost),
    ("MVOption", MVOption),
    ("UsefulLife", UsefulLife),
    ("MeasureTotalFirstCost", MeasureTotalFirstCost),
    ("MeasureInstallationCost", MeasureInstallationCost),
    ("MeasureMaterialCost", MeasureMaterialCost),
    ("CapitalReplacementCost", CapitalReplacementCost),
    ("ResidualValue", ResidualValue),
    ("Recommended", Recommended),
    ("StartDate", StartDate),
    ("EndDate", EndDate),
    ("ImplementationStatus", ImplementationStatus),
    ("DiscardReason", DiscardReason),
    ("UserDefinedFields", UserDefinedFields),
]

# ThermalZoneType
class ThermalZoneType(BSElement):
    pass


ThermalZoneType.element_attributes = [
    "ID",  # ID
]
ThermalZoneType.element_children = [
    ("PremisesName", PremisesName),
    ("DeliveryIDs", DeliveryIDs),
    ("HVACScheduleIDs", HVACScheduleIDs),
    ("SetpointTemperatureHeating", SetpointTemperatureHeating),
    ("SetbackTemperatureHeating", SetbackTemperatureHeating),
    ("HeatLowered", HeatLowered),
    ("SetpointTemperatureCooling", SetpointTemperatureCooling),
    ("SetupTemperatureCooling", SetupTemperatureCooling),
    ("ACAdjusted", ACAdjusted),
    ("Spaces", Spaces),
    ("UserDefinedFields", UserDefinedFields),
]

# ScenarioType.ResourceUses
class ResourceUses(BSElement):
    pass


ResourceUses.element_children = [
    ("ResourceUse", ResourceUse),
]

# ScenarioType.ScenarioType.CurrentBuilding
class CurrentBuilding(BSElement):
    pass


CurrentBuilding.element_children = [
    ("CalculationMethod", CalculationMethod),
    ("AssetScore", AssetScore),
    ("ENERGYSTARScore", ENERGYSTARScore),
]

# DerivedModelType
class DerivedModelType(BSElement):
    """A derived model represents a supervised or unsupervised learning model derived from data presented in a scenario."""


DerivedModelType.element_attributes = [
    "ID",  # ID
]
DerivedModelType.element_children = [
    ("DerivedModelName", DerivedModelName),
    ("MeasuredScenarioID", MeasuredScenarioID),
    ("Models", Models),
    ("SavingsSummaries", SavingsSummaries),
    ("UserDefinedFields", UserDefinedFields),
]

# HVACSystemType.HeatingAndCoolingSystems
class HeatingAndCoolingSystems(BSElement):
    pass


HeatingAndCoolingSystems.element_children = [
    ("ZoningSystemType", ZoningSystemType),
    ("HeatingSources", HeatingSources),
    ("CoolingSources", CoolingSources),
    ("Deliveries", Deliveries),
]

# HVACSystemType.DuctSystems
class DuctSystems(BSElement):
    pass


DuctSystems.element_children = [
    ("DuctSystem", DuctSystem),
]

# HVACSystemType.Plants.HeatingPlants.HeatingPlant
class HeatingPlant(HeatingPlantType):
    """Type of central heating system, defined as any source of heating energy separate from the zone being heated. Local heating systems (such as packaged systems and fan-coils) are recorded in a separate data field."""


# HVACSystemType.Plants.HeatingPlants
class HeatingPlants(BSElement):
    pass


HeatingPlants.element_children = [
    ("HeatingPlant", HeatingPlant),
]

# OtherHVACSystemType
class OtherHVACSystemType(BSElement):
    class Controls(BSElement):
        """List of controls for other HVAC systems."""

        class Control(ControlGeneralType):
            """Other HVAC system control."""


OtherHVACSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
OtherHVACSystemType.element_children = [
    ("OtherHVACType", OtherHVACType),
    ("Location", Location),
    ("PrimaryFuel", PrimaryFuel),
    ("OtherHVACSystemCondition", OtherHVACSystemCondition),
    ("Controls", OtherHVACSystemType.Controls),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("YearOfManufacture", YearOfManufacture),
    ("YearInstalled", YearInstalled),
    ("LinkedPremises", LinkedPremises),
    ("Integration", Integration),
    ("LinkedDeliveryIDs", LinkedDeliveryIDs),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
OtherHVACSystemType.Controls.element_children = [
    ("Control", OtherHVACSystemType.Controls.Control),
]

# LightingSystemType
class LightingSystemType(BSElement):
    class LampPower(BSElement):
        """The number of watts per lamp. (W)"""

        element_type = "xs:decimal"

    class Controls(BSElement):
        """List of system operation controls."""

        class Control(ControlLightingType):
            """Type of system operation control."""


LightingSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
LightingSystemType.element_children = [
    ("LampType", LampType),
    ("BallastType", BallastType),
    ("InputVoltage", InputVoltage),
    ("InstallationType", InstallationType),
    ("LightingDirection", LightingDirection),
    ("DimmingCapability", DimmingCapability),
    ("PercentPremisesServed", PercentPremisesServed),
    ("InstalledPower", InstalledPower),
    ("LampPower", LightingSystemType.LampPower),
    ("NumberOfLampsPerLuminaire", NumberOfLampsPerLuminaire),
    ("NumberOfLampsPerBallast", NumberOfLampsPerBallast),
    ("NumberOfBallastsPerLuminaire", NumberOfBallastsPerLuminaire),
    ("NumberOfLuminaires", NumberOfLuminaires),
    ("OutsideLighting", OutsideLighting),
    ("ReflectorType", ReflectorType),
    ("LightingEfficacy", LightingEfficacy),
    ("WorkPlaneHeight", WorkPlaneHeight),
    ("LuminaireHeight", LuminaireHeight),
    ("FixtureSpacing", FixtureSpacing),
    ("RatedLampLife", RatedLampLife),
    ("Controls", LightingSystemType.Controls),
    ("LightingAutomationSystem", LightingAutomationSystem),
    ("ThirdPartyCertification", ThirdPartyCertification),
    ("PrimaryFuel", PrimaryFuel),
    ("YearInstalled", YearInstalled),
    ("YearOfManufacture", YearOfManufacture),
    ("Manufacturer", Manufacturer),
    ("ModelNumber", ModelNumber),
    ("Location", Location),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]
LightingSystemType.Controls.element_children = [
    ("Control", LightingSystemType.Controls.Control),
]

# BuildingSync.Facilities.Facility.Systems.DomesticHotWaterSystems.DomesticHotWaterSystem
class DomesticHotWaterSystem(DomesticHotWaterSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.DomesticHotWaterSystems
class DomesticHotWaterSystems(BSElement):
    pass


DomesticHotWaterSystems.element_children = [
    ("DomesticHotWaterSystem", DomesticHotWaterSystem),
]

# BuildingSync.Facilities.Facility.Systems.DishwasherSystems.DishwasherSystem
class DishwasherSystem(DishwasherSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.DishwasherSystems
class DishwasherSystems(BSElement):
    pass


DishwasherSystems.element_children = [
    ("DishwasherSystem", DishwasherSystem),
]

# BuildingSync.Facilities.Facility.Systems.LaundrySystems.LaundrySystem
class LaundrySystem(LaundrySystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.LaundrySystems
class LaundrySystems(BSElement):
    pass


LaundrySystems.element_children = [
    ("LaundrySystem", LaundrySystem),
]

# BuildingSync.Facilities.Facility.Systems.PumpSystems.PumpSystem
class PumpSystem(PumpSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.PumpSystems
class PumpSystems(BSElement):
    pass


PumpSystems.element_children = [
    ("PumpSystem", PumpSystem),
]

# BuildingSync.Facilities.Facility.Systems.FanSystems.FanSystem
class FanSystem(FanSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.FanSystems
class FanSystems(BSElement):
    pass


FanSystems.element_children = [
    ("FanSystem", FanSystem),
]

# BuildingSync.Facilities.Facility.Systems.MotorSystems.MotorSystem
class MotorSystem(MotorSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.MotorSystems
class MotorSystems(BSElement):
    pass


MotorSystems.element_children = [
    ("MotorSystem", MotorSystem),
]

# BuildingSync.Facilities.Facility.Systems.HeatRecoverySystems.HeatRecoverySystem
class HeatRecoverySystem(HeatRecoverySystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.HeatRecoverySystems
class HeatRecoverySystems(BSElement):
    pass


HeatRecoverySystems.element_children = [
    ("HeatRecoverySystem", HeatRecoverySystem),
]

# BuildingSync.Facilities.Facility.Systems.CriticalITSystems.CriticalITSystem
class CriticalITSystem(CriticalITSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.CriticalITSystems
class CriticalITSystems(BSElement):
    pass


CriticalITSystems.element_children = [
    ("CriticalITSystem", CriticalITSystem),
]

# BuildingSync.Facilities.Facility.Systems.PlugLoads.PlugLoad
class PlugLoad(PlugElectricLoadType):
    pass


# BuildingSync.Facilities.Facility.Systems.PlugLoads
class PlugLoads(BSElement):
    pass


PlugLoads.element_children = [
    ("PlugLoad", PlugLoad),
]

# BuildingSync.Facilities.Facility.Systems.ProcessLoads.ProcessLoad
class ProcessLoad(ProcessGasElectricLoadType):
    pass


# BuildingSync.Facilities.Facility.Systems.ProcessLoads
class ProcessLoads(BSElement):
    pass


ProcessLoads.element_children = [
    ("ProcessLoad", ProcessLoad),
]

# BuildingSync.Facilities.Facility.Systems.ConveyanceSystems.ConveyanceSystem
class ConveyanceSystem(ConveyanceSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.OnsiteStorageTransmissionGenerationSystems.OnsiteStorageTransmissionGenerationSystem
class OnsiteStorageTransmissionGenerationSystem(
    OnsiteStorageTransmissionGenerationSystemType
):
    pass


# BuildingSync.Facilities.Facility.Systems.OnsiteStorageTransmissionGenerationSystems
class OnsiteStorageTransmissionGenerationSystems(BSElement):
    pass


OnsiteStorageTransmissionGenerationSystems.element_children = [
    (
        "OnsiteStorageTransmissionGenerationSystem",
        OnsiteStorageTransmissionGenerationSystem,
    ),
]

# BuildingSync.Facilities.Facility.Systems.Pools.Pool
class Pool(PoolType):
    pass


# BuildingSync.Facilities.Facility.Systems.Pools
class Pools(BSElement):
    pass


Pools.element_children = [
    ("Pool", Pool),
]

# BuildingSync.Facilities.Facility.Systems.WaterUses
class WaterUses(BSElement):
    class WaterUse(WaterUseType):
        pass


WaterUses.element_children = [
    ("WaterUse", WaterUses.WaterUse),
]

# BuildingSync.Facilities.Facility.Measures.Measure
class Measure(MeasureType):
    pass


# BuildingSync.Facilities.Facility.Measures
class Measures(BSElement):
    pass


Measures.element_children = [
    ("Measure", Measure),
]

# BuildingType.Sections.Section.ThermalZones
class ThermalZones(BSElement):
    """Section of a building that share thermal control characteristics. May be one or many."""

    class ThermalZone(ThermalZoneType):
        pass


ThermalZones.element_children = [
    ("ThermalZone", ThermalZones.ThermalZone),
]

# ScenarioType.ScenarioType.DerivedModel
class DerivedModel(DerivedModelType):
    pass


# HVACSystemType.Plants
class Plants(BSElement):
    pass


Plants.element_children = [
    ("HeatingPlants", HeatingPlants),
    ("CoolingPlants", CoolingPlants),
    ("CondenserPlants", CondenserPlants),
]

# HVACSystemType.OtherHVACSystems.OtherHVACSystem
class OtherHVACSystem(OtherHVACSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.LightingSystems.LightingSystem
class LightingSystem(LightingSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.LightingSystems
class LightingSystems(BSElement):
    pass


LightingSystems.element_children = [
    ("LightingSystem", LightingSystem),
]

# BuildingType.Sections
class Sections(BSElement):
    class Section(BSElement):
        """Physical section of building for which features are defined. May be one or many."""

        class YearOfConstruction(BSElement):
            """Year in which construction was completed on the premise. (CCYY)"""

            element_type = "xs:gYear"

        class Story(BSElement):
            """The story of the given section."""

            element_type = "xs:int"

        class FloorsAboveGrade(BSElement):
            """Number of floors which are fully above ground."""

            element_type = "xs:integer"

        class FloorsBelowGrade(BSElement):
            """Number of floors which are fully underground."""

            element_type = "xs:integer"


Sections.element_children = [
    ("Section", Sections.Section),
]
Sections.Section.element_attributes = [
    "ID",  # ID
]
Sections.Section.element_children = [
    ("PremisesName", PremisesName),
    ("SectionType", SectionType),
    ("PremisesNotes", PremisesNotes),
    ("PremisesIdentifiers", PremisesIdentifiers),
    ("OccupancyClassification", OccupancyClassification),
    ("OriginalOccupancyClassification", OriginalOccupancyClassification),
    ("OccupancyLevels", OccupancyLevels),
    ("TypicalOccupantUsages", TypicalOccupantUsages),
    ("PrimaryContactID", PrimaryContactID),
    ("TenantIDs", TenantIDs),
    ("YearOfConstruction", Sections.Section.YearOfConstruction),
    ("FootprintShape", FootprintShape),
    ("NumberOfSides", NumberOfSides),
    ("Story", Sections.Section.Story),
    ("FloorAreas", FloorAreas),
    ("ThermalZoneLayout", ThermalZoneLayout),
    ("PerimeterZoneDepth", PerimeterZoneDepth),
    ("SideA1Orientation", SideA1Orientation),
    ("Sides", Sides),
    ("Roofs", Roofs),
    ("Ceilings", Ceilings),
    ("ExteriorFloors", ExteriorFloors),
    ("Foundations", Foundations),
    ("XOffset", XOffset),
    ("YOffset", YOffset),
    ("ZOffset", ZOffset),
    ("FloorsAboveGrade", Sections.Section.FloorsAboveGrade),
    ("FloorsBelowGrade", Sections.Section.FloorsBelowGrade),
    ("FloorsPartiallyBelowGrade", FloorsPartiallyBelowGrade),
    ("FloorToFloorHeight", FloorToFloorHeight),
    ("FloorToCeilingHeight", FloorToCeilingHeight),
    ("UserDefinedFields", UserDefinedFields),
    ("ThermalZones", ThermalZones),
]

# HVACSystemType.OtherHVACSystems
class OtherHVACSystems(BSElement):
    pass


OtherHVACSystems.element_children = [
    ("OtherHVACSystem", OtherHVACSystem),
]

# HVACSystemType
class HVACSystemType(BSElement):
    pass


HVACSystemType.element_attributes = [
    "ID",  # ID
    "Status",  # Status
]
HVACSystemType.element_children = [
    ("Plants", Plants),
    ("HeatingAndCoolingSystems", HeatingAndCoolingSystems),
    ("DuctSystems", DuctSystems),
    ("OtherHVACSystems", OtherHVACSystems),
    ("Location", Location),
    ("Priority", Priority),
    ("FrequencyOfMaintenance", FrequencyOfMaintenance),
    ("HVACControlSystemTypes", HVACControlSystemTypes),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
    ("Quantity", Quantity),
]

# BuildingType
class BuildingType(BSElement):
    class PortfolioManager(PortfolioManagerType):
        """If exists then the data for this building is included in ENERGY STAR Portfolio Manager."""

    class FloorsAboveGrade(BSElement):
        """Nominal number of floors which are fully above ground."""

        element_type = "xs:integer"

    class FloorsBelowGrade(BSElement):
        """Nominal number of floors which are fully underground."""

        element_type = "xs:integer"

    class YearOfConstruction(BSElement):
        """Year in which construction was completed on the premise. (CCYY)"""

        element_type = "xs:gYear"


BuildingType.element_attributes = [
    "ID",  # ID
]
BuildingType.element_children = [
    ("PremisesName", PremisesName),
    ("PremisesNotes", PremisesNotes),
    ("PremisesIdentifiers", PremisesIdentifiers),
    ("Address", Address),
    ("ClimateZoneType", ClimateZoneType),
    ("eGRIDRegionCode", eGRIDRegionCode),
    ("Longitude", Longitude),
    ("Latitude", Latitude),
    ("BuildingClassification", BuildingClassification),
    ("OccupancyClassification", OccupancyClassification),
    ("OccupancyLevels", OccupancyLevels),
    ("TypicalOccupantUsages", TypicalOccupantUsages),
    ("SpatialUnits", SpatialUnits),
    ("Ownership", Ownership),
    ("OwnershipStatus", OwnershipStatus),
    ("PrimaryContactID", PrimaryContactID),
    ("TenantIDs", TenantIDs),
    ("NAICSCode", NAICSCode),
    ("PubliclySubsidized", PubliclySubsidized),
    ("FederalBuilding", FederalBuilding),
    ("PortfolioManager", BuildingType.PortfolioManager),
    ("NumberOfBusinesses", NumberOfBusinesses),
    ("FloorsAboveGrade", BuildingType.FloorsAboveGrade),
    ("FloorsBelowGrade", BuildingType.FloorsBelowGrade),
    ("ConditionedFloorsAboveGrade", ConditionedFloorsAboveGrade),
    ("ConditionedFloorsBelowGrade", ConditionedFloorsBelowGrade),
    ("UnconditionedFloorsAboveGrade", UnconditionedFloorsAboveGrade),
    ("UnconditionedFloorsBelowGrade", UnconditionedFloorsBelowGrade),
    ("BuildingAutomationSystem", BuildingAutomationSystem),
    ("LightingAutomationSystem", LightingAutomationSystem),
    ("HistoricalLandmark", HistoricalLandmark),
    ("FloorAreas", FloorAreas),
    ("AspectRatio", AspectRatio),
    ("Perimeter", Perimeter),
    ("TotalExteriorAboveGradeWallArea", TotalExteriorAboveGradeWallArea),
    ("TotalExteriorBelowGradeWallArea", TotalExteriorBelowGradeWallArea),
    ("OverallWindowToWallRatio", OverallWindowToWallRatio),
    ("OverallDoorToWallRatio", OverallDoorToWallRatio),
    ("HeightDistribution", HeightDistribution),
    ("HorizontalSurroundings", HorizontalSurroundings),
    ("VerticalSurroundings", VerticalSurroundings),
    ("Assessments", Assessments),
    ("YearOfConstruction", BuildingType.YearOfConstruction),
    ("YearOccupied", YearOccupied),
    ("YearOfLastEnergyAudit", YearOfLastEnergyAudit),
    ("RetrocommissioningDate", RetrocommissioningDate),
    ("YearOfLatestRetrofit", YearOfLatestRetrofit),
    ("YearOfLastMajorRemodel", YearOfLastMajorRemodel),
    ("PercentOccupiedByOwner", PercentOccupiedByOwner),
    ("PercentLeasedByOwner", PercentLeasedByOwner),
    ("NumberOfFacilitiesOnSite", NumberOfFacilitiesOnSite),
    ("OperatorType", OperatorType),
    ("Sections", Sections),
    ("UserDefinedFields", UserDefinedFields),
]

# ScenarioType
class ScenarioType(BSElement):
    class Other(BSElement):
        class AnnualSavingsSiteEnergy(BSElement):
            """Site energy savings per year. (MMBtu/year)"""

            element_type = "xs:decimal"

        class AnnualSavingsSourceEnergy(BSElement):
            """Source energy savings per year. (MMBtu/year)"""

            element_type = "xs:decimal"

        class AnnualSavingsCost(BSElement):
            """Cost savings per year, including energy, demand, change in rate schedule, and other cost impacts on utility bills. ($/year)"""

            element_type = "xs:integer"

        class SummerPeakElectricityReduction(BSElement):
            """Reduction in largest 15 minute peak demand for the summer months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

            element_type = "xs:decimal"

        class WinterPeakElectricityReduction(BSElement):
            """Reduction in largest 15 minute peak demand for the winter months as defined in the utility rate schedule (for electrical energy use only). (kW)"""

            element_type = "xs:decimal"

        class AnnualPeakElectricityReduction(BSElement):
            """Reduction in largest 15 minute peak demand for the year as defined in the utility rate schedule (for electrical energy use only). (kW)"""

            element_type = "xs:decimal"

        class AnnualWaterSavings(BSElement):
            """Total annual water savings (hot and cold). (gal/year)"""

            element_type = "xs:decimal"

        class AnnualWaterCostSavings(BSElement):
            """Total annual reduction in water costs, not including water heating costs (hot and cold). ($/year)"""

            element_type = "xs:decimal"

        class SimplePayback(BSElement):
            """The length of time required for the investment to pay for itself. (yrs)"""

            element_type = "xs:decimal"

        class NetPresentValue(BSElement):
            """Net Present Value (NPV) of measure or package ($)."""

            element_type = "xs:decimal"

        class InternalRateOfReturn(BSElement):
            """Internal rate of return (IRR) of measure or package (%)."""

            element_type = "xs:decimal"

    class ScenarioType(BSElement):
        """Type of scenario for which energy use is presented."""

    class HDDBaseTemperature(BSElement):
        """Reference temperature for calculating Heating Degree Days (HDD). (°F)"""

        element_type = "xs:decimal"

    class CDDBaseTemperature(BSElement):
        """Reference temperature for calculating Cooling Degree Days (CDD). (°F)"""

        element_type = "xs:decimal"


ScenarioType.element_attributes = [
    "ID",  # ID
]
ScenarioType.element_children = [
    ("ScenarioName", ScenarioName),
    ("ScenarioNotes", ScenarioNotes),
    ("TemporalStatus", TemporalStatus),
    ("Normalization", Normalization),
    ("ScenarioType", ScenarioType.ScenarioType),
    ("WeatherType", WeatherType),
    ("ResourceUses", ResourceUses),
    ("TimeSeriesData", TimeSeriesData),
    ("AllResourceTotals", AllResourceTotals),
    ("AnnualHeatingDegreeDays", AnnualHeatingDegreeDays),
    ("AnnualCoolingDegreeDays", AnnualCoolingDegreeDays),
    ("HDDBaseTemperature", ScenarioType.HDDBaseTemperature),
    ("CDDBaseTemperature", ScenarioType.CDDBaseTemperature),
    ("LinkedPremises", LinkedPremises),
    ("UserDefinedFields", UserDefinedFields),
]
ScenarioType.Other.element_children = [
    ("ReferenceCase", ReferenceCase),
    ("AnnualSavingsSiteEnergy", ScenarioType.Other.AnnualSavingsSiteEnergy),
    ("AnnualSavingsSourceEnergy", ScenarioType.Other.AnnualSavingsSourceEnergy),
    ("AnnualSavingsCost", ScenarioType.Other.AnnualSavingsCost),
    (
        "SummerPeakElectricityReduction",
        ScenarioType.Other.SummerPeakElectricityReduction,
    ),
    (
        "WinterPeakElectricityReduction",
        ScenarioType.Other.WinterPeakElectricityReduction,
    ),
    (
        "AnnualPeakElectricityReduction",
        ScenarioType.Other.AnnualPeakElectricityReduction,
    ),
    ("AnnualWaterSavings", ScenarioType.Other.AnnualWaterSavings),
    ("AnnualWaterCostSavings", ScenarioType.Other.AnnualWaterCostSavings),
    ("SimplePayback", ScenarioType.Other.SimplePayback),
    ("NetPresentValue", ScenarioType.Other.NetPresentValue),
    ("InternalRateOfReturn", ScenarioType.Other.InternalRateOfReturn),
    ("AssetScore", AssetScore),
    ("ENERGYSTARScore", ENERGYSTARScore),
]
ScenarioType.ScenarioType.element_children = [
    ("CurrentBuilding", CurrentBuilding),
    ("Benchmark", Benchmark),
    ("Target", Target),
    ("PackageOfMeasures", PackageOfMeasures),
    ("DerivedModel", DerivedModel),
    ("Other", ScenarioType.Other),
]

# ReportType.Scenarios.Scenario
class Scenario(ScenarioType):
    pass


# BuildingSync.Facilities.Facility.Systems.HVACSystems.HVACSystem
class HVACSystem(HVACSystemType):
    pass


# BuildingSync.Facilities.Facility.Systems.HVACSystems
class HVACSystems(BSElement):
    pass


HVACSystems.element_children = [
    ("HVACSystem", HVACSystem),
]

# BuildingSync.Facilities.Facility.Systems
class Systems(BSElement):
    class ConveyanceSystems(BSElement):
        pass


Systems.element_children = [
    ("HVACSystems", HVACSystems),
    ("LightingSystems", LightingSystems),
    ("DomesticHotWaterSystems", DomesticHotWaterSystems),
    ("CookingSystems", CookingSystems),
    ("RefrigerationSystems", RefrigerationSystems),
    ("DishwasherSystems", DishwasherSystems),
    ("LaundrySystems", LaundrySystems),
    ("PumpSystems", PumpSystems),
    ("FanSystems", FanSystems),
    ("MotorSystems", MotorSystems),
    ("HeatRecoverySystems", HeatRecoverySystems),
    ("WallSystems", WallSystems),
    ("RoofSystems", RoofSystems),
    ("CeilingSystems", CeilingSystems),
    ("FenestrationSystems", FenestrationSystems),
    ("ExteriorFloorSystems", ExteriorFloorSystems),
    ("FoundationSystems", FoundationSystems),
    ("CriticalITSystems", CriticalITSystems),
    ("PlugLoads", PlugLoads),
    ("ProcessLoads", ProcessLoads),
    ("ConveyanceSystems", Systems.ConveyanceSystems),
    (
        "OnsiteStorageTransmissionGenerationSystems",
        OnsiteStorageTransmissionGenerationSystems,
    ),
    ("Pools", Pools),
    ("WaterUses", WaterUses),
    ("AirInfiltrationSystems", AirInfiltrationSystems),
    ("WaterInfiltrationSystems", WaterInfiltrationSystems),
]
Systems.ConveyanceSystems.element_children = [
    ("ConveyanceSystem", ConveyanceSystem),
]

# ReportType.Scenarios
class Scenarios(BSElement):
    pass


Scenarios.element_children = [
    ("Scenario", Scenario),
]

# ReportType
class ReportType(BSElement):
    pass


ReportType.element_attributes = [
    "ID",  # ID
]
ReportType.element_children = [
    ("Scenarios", Scenarios),
    ("AuditDates", AuditDates),
    ("ASHRAEAuditLevel", ASHRAEAuditLevel),
    ("RetrocommissioningAudit", RetrocommissioningAudit),
    ("AuditCost", AuditCost),
    ("DiscountFactor", DiscountFactor),
    ("AnalysisPeriod", AnalysisPeriod),
    ("GasPriceEscalationRate", GasPriceEscalationRate),
    ("ElectricityPriceEscalationRate", ElectricityPriceEscalationRate),
    ("WaterPriceEscalationRate", WaterPriceEscalationRate),
    ("OtherEscalationRates", OtherEscalationRates),
    ("InflationRate", InflationRate),
    ("Qualifications", Qualifications),
    ("AuditExemption", AuditExemption),
    ("Utilities", Utilities),
    ("AuditorContactID", AuditorContactID),
    ("LinkedPremisesOrSystem", LinkedPremisesOrSystem),
    ("UserDefinedFields", UserDefinedFields),
]

# SiteType.Buildings
class Buildings(BSElement):
    class Building(BuildingType):
        """A building is a single structure wholly or partially enclosed within exterior walls, or within exterior and abutment walls (party walls), and a roof, affording shelter to persons, animals, or property. A building can be two or more units held in the condominium form of ownership that are governed by the same board of managers."""


Buildings.element_children = [
    ("Building", Buildings.Building),
]

# SiteType
class SiteType(BSElement):
    pass


SiteType.element_attributes = [
    "ID",  # ID
]
SiteType.element_children = [
    ("PremisesIdentifiers", PremisesIdentifiers),
    ("PremisesName", PremisesName),
    ("PremisesNotes", PremisesNotes),
    ("OccupancyClassification", OccupancyClassification),
    ("Address", Address),
    ("ClimateZoneType", ClimateZoneType),
    ("eGRIDRegionCode", eGRIDRegionCode),
    ("Longitude", Longitude),
    ("Latitude", Latitude),
    ("FloorAreas", FloorAreas),
    ("Ownership", Ownership),
    ("OwnershipStatus", OwnershipStatus),
    ("PrimaryContactID", PrimaryContactID),
    ("Buildings", Buildings),
    ("UserDefinedFields", UserDefinedFields),
]

# BuildingSync.Facilities.Facility.Reports.Report
class Report(ReportType):
    pass


# BuildingSync.Facilities.Facility.Reports
class Reports(BSElement):
    pass


Reports.element_children = [
    ("Report", Report),
]

# BuildingSync.Facilities.Facility.Sites
class Sites(BSElement):
    class Site(SiteType):
        pass


Sites.element_children = [
    ("Site", Sites.Site),
]

# BuildingSync.Facilities
class Facilities(BSElement):
    class Facility(BSElement):
        """A group of sites which contain buildings."""


Facilities.element_children = [
    ("Facility", Facilities.Facility),
]
Facilities.Facility.element_attributes = [
    "ID",  # ID
]
Facilities.Facility.element_children = [
    ("Sites", Sites),
    ("Systems", Systems),
    ("Schedules", Schedules),
    ("Measures", Measures),
    ("Reports", Reports),
    ("Contacts", Contacts),
    ("Tenants", Tenants),
    ("UserDefinedFields", UserDefinedFields),
]

# BuildingSync
class BuildingSync(BSElement):
    pass


BuildingSync.element_children = [
    ("Programs", Programs),
    ("Facilities", Facilities),
]
