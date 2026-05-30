# Titanic Star Schema Project

## Overview
This project converts the Titanic passenger CSV files into an analytics-oriented star schema.

## Source Files Used
- `train.csv`
- `test.csv`
- `gender_submission.csv`

## Modeling Goal
Create a dimensional model that supports questions such as:
- What is the survival rate by passenger class?
- How does survival vary by age band, sex, or family size?
- How does embarkation point relate to fare and survival?

## Grain
The grain of the fact table is **one row per passenger in the Titanic manifest dataset**.

## Star Schema
### Fact Table
- `fact_passenger_outcome`
  - Measures: `PassengerCount`, `SurvivedFlag`, `DiedFlag`, `FareAmount`

### Dimensions
- `dim_passenger`
- `dim_class`
- `dim_embarkation`
- `dim_cabin`
- `dim_ticket`
- `dim_family`
- `dim_age_band`
- `dim_fare_band`
- `dim_source`

## Business Rules / Assumptions
- `test.csv` was joined to `gender_submission.csv` on `PassengerId` to append survival outcomes.
- Missing `Embarked`, `Cabin`, and `Ticket` values were standardized to `Unknown`.
- `FamilySize = SibSp + Parch + 1`.
- `IsAlone = 1` when `FamilySize = 1`, otherwise `0`.
- `AgeBand` and `FareBand` were derived for easier reporting.
- Surrogate keys were generated for every dimension and the fact table.

## Files Included
- `dim_passenger.csv`
- `dim_class.csv`
- `dim_embarkation.csv`
- `dim_cabin.csv`
- `dim_ticket.csv`
- `dim_family.csv`
- `dim_age_band.csv`
- `dim_fare_band.csv`
- `dim_source.csv`
- `fact_passenger_outcome.csv`
- `titanic_star_schema_source_combined.csv`
- `titanic_star_schema_ddl.sql`
- `titanic_star_schema_queries.sql`

## Quick ERD (text)
```text
                     dim_class
                         |
                     dim_embarkation
                         |
 dim_passenger ---- fact_passenger_outcome ---- dim_ticket
                         |                     |
                      dim_family            dim_cabin
                         |
                     dim_age_band
                         |
                     dim_fare_band
                         |
                       dim_source
```

## Row Counts
- Combined source rows: 1,309
- Fact rows: 1,309
- Passenger dimension rows: 1,309
- Ticket dimension rows: 929
- Cabin dimension rows: 187
- Family dimension rows: 25

## Next Steps
- Load the CSVs into SQL Server / PostgreSQL / Snowflake.
- Run the DDL and use the sample queries.
- Build a Power BI or Tableau dashboard on top of the fact table.