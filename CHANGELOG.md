# Version 0.4.0

* Generated for BuildingSync 2.7.0 (52 new elements, none removed), including:
    * Condition elements for envelope, HVAC, lighting, and other systems
    * Files / LinkedFiles and related file metadata elements
    * Federal facility identifiers (FederalFacility, FacilityNumber, SubAgency, ...)
    * Life-cycle savings elements (LifeCycleSavingsEnergy, LifeCycleSavingsWater, ...)
    * AuditCycleStartDate / AuditCycleEndDate
* Require Python 3.11+ (tested on 3.11, 3.12, 3.13, and 3.14)
* Allow lxml 5 and 6 (previously limited to lxml 4, which has no wheels for Python 3.13+)
* Moved packaging metadata to the standard `[project]` table (Poetry 2)
* Updated CI (Python matrix, generator checks for BuildingSync 2.3 through 2.7 and develop branches) and added Dependabot
* Updated black to 26.10.1

# Version 0.3.0

* Generated for BuildingSync 2.5 (which is currently develop-v2)
    * Added GHG emission metrics
    * Changed UsefulLife type
    * Added DiscountRate
    * Added EquipmentID
    * Updated MeasureSavingsAnalysis
    * Added and sorted enumerations in AuditorQualificationType
    * Added PrincipalHVACSystemType, PrincipalLightingSystemType, CondenserType
    * Added FacilityEvaluationAuditDefinition
    * Added AuditCycle
    * Added WCM categories and measures

# Version 0.2.0

* Generated for BuildingSync 2.4
* Renamed project folder to bsyncpy to follow Python package conventions
* Updated Poetry/Python dependencies

# Version 0.1.1

* Updated dependencies and regenerated bsync.py

# Version 0.1.0

* Generated for BuildingSync 2.3