-- Defines lookup tables, Location, Application, and 1NF join tables.
BEGIN;
-- =========================
-- Lookup / Code→Name tables
-- =========================
DROP TABLE IF EXISTS Agency CASCADE;
CREATE TABLE Agency (
agency_code SMALLINT PRIMARY KEY,
agency_name TEXT NOT NULL,
agency_abbr TEXT
);
DROP TABLE IF EXISTS Loan_Type CASCADE;
CREATE TABLE Loan_Type (
loan_type SMALLINT PRIMARY KEY,
loan_type_name TEXT NOT NULL
);
DROP TABLE IF EXISTS Property_Type CASCADE;
CREATE TABLE Property_Type (
property_type SMALLINT PRIMARY KEY,
property_type_name TEXT NOT NULL
);
DROP TABLE IF EXISTS Loan_Purpose CASCADE;
CREATE TABLE Loan_Purpose (
loan_purpose SMALLINT PRIMARY KEY,
loan_purpose_name TEXT NOT NULL
);
DROP TABLE IF EXISTS Owner_Occupancy CASCADE;
CREATE TABLE Owner_Occupancy (
owner_occupancy SMALLINT PRIMARY KEY,
owner_occupancy_name TEXT NOT NULL
);
DROP TABLE IF EXISTS Preapproval CASCADE;
CREATE TABLE Preapproval (
preapproval SMALLINT PRIMARY KEY,
preapproval_name TEXT NOT NULL
);
DROP TABLE IF EXISTS Action_Taken CASCADE;
CREATE TABLE Action_Taken (
action_taken SMALLINT PRIMARY KEY,
action_taken_name TEXT NOT NULL
);
DROP TABLE IF EXISTS Purchaser_Type CASCADE;
CREATE TABLE Purchaser_Type (
purchaser_type SMALLINT PRIMARY KEY,
purchaser_type_name TEXT NOT NULL
);
DROP TABLE IF EXISTS HOEPA_Status CASCADE;
CREATE TABLE HOEPA_Status (
hoepa_status SMALLINT PRIMARY KEY
-- add hoepa_status_name TEXT if present in your CSV
);
DROP TABLE IF EXISTS Lien_Status CASCADE;
CREATE TABLE Lien_Status (
lien_status SMALLINT PRIMARY KEY
-- add lien_status_name TEXT if present in your CSV
);
DROP TABLE IF EXISTS Sex CASCADE;
CREATE TABLE Sex (
sex_code SMALLINT PRIMARY KEY,
sex_name TEXT
);
DROP TABLE IF EXISTS Ethnicity CASCADE;
CREATE TABLE Ethnicity (
ethnicity_code SMALLINT PRIMARY KEY,
ethnicity_name TEXT
);
DROP TABLE IF EXISTS Race CASCADE;
CREATE TABLE Race (
race_code SMALLINT PRIMARY KEY,
race_name TEXT
);
DROP TABLE IF EXISTS Denial_Reason CASCADE;
CREATE TABLE Denial_Reason (
denial_reason SMALLINT PRIMARY KEY,
denial_reason_name TEXT
);
DROP TABLE IF EXISTS State CASCADE;
CREATE TABLE State (
state_code SMALLINT PRIMARY KEY,
state_name TEXT NOT NULL,
state_abbr TEXT NOT NULL
);
DROP TABLE IF EXISTS MSAMD CASCADE;
CREATE TABLE MSAMD (
msamd INTEGER PRIMARY KEY,
msamd_name TEXT
);
DROP TABLE IF EXISTS County CASCADE;
CREATE TABLE County (
state_code SMALLINT NOT NULL REFERENCES State(state_code),
county_code INTEGER NOT NULL,
county_name TEXT,
PRIMARY KEY (state_code, county_code)
);


-- =========================
-- Location (surrogate PK)
-- =========================
DROP TABLE IF EXISTS Location CASCADE;
CREATE TABLE Location (
location_id SERIAL PRIMARY KEY,
state_code SMALLINT,
county_code INTEGER,
msamd INTEGER,
census_tract_number TEXT,
population INTEGER,
minority_population NUMERIC(10,4),
hud_median_family_income INTEGER,
tract_to_msamd_income NUMERIC(10,4),
number_of_owner_occupied_units INTEGER,
number_of_1_to_4_family_units INTEGER,
UNIQUE (
state_code, county_code, msamd, census_tract_number,
population, minority_population, hud_median_family_income,
tract_to_msamd_income, number_of_owner_occupied_units,
number_of_1_to_4_family_units
),
FOREIGN KEY (state_code, county_code) REFERENCES County(state_code,
county_code),
FOREIGN KEY (msamd) REFERENCES MSAMD(msamd)
);
-- Optional helper index for fast composite lookups (used by Application load)
CREATE INDEX IF NOT EXISTS ix_location_composite ON Location (
state_code, county_code, msamd, census_tract_number,
population, minority_population, hud_median_family_income,
tract_to_msamd_income, number_of_owner_occupied_units,
number_of_1_to_4_family_units
);


-- =========================
-- Core Application table
-- =========================
DROP TABLE IF EXISTS Application CASCADE;
CREATE TABLE Application (
application_id BIGINT PRIMARY KEY, -- equals preliminary.id
as_of_year SMALLINT NOT NULL,
respondent_id TEXT,
agency_code SMALLINT REFERENCES Agency(agency_code),
loan_type SMALLINT REFERENCES Loan_Type(loan_type),
property_type SMALLINT REFERENCES Property_Type(property_type),
loan_purpose SMALLINT REFERENCES Loan_Purpose(loan_purpose),
owner_occupancy SMALLINT REFERENCES Owner_Occupancy(owner_occupancy),
loan_amount_000s INTEGER,
preapproval SMALLINT REFERENCES Preapproval(preapproval),
action_taken SMALLINT REFERENCES Action_Taken(action_taken),
applicant_sex SMALLINT REFERENCES Sex(sex_code),
co_applicant_sex SMALLINT REFERENCES Sex(sex_code),
applicant_ethnicity SMALLINT REFERENCES Ethnicity(ethnicity_code),
co_applicant_ethnicity SMALLINT REFERENCES Ethnicity(ethnicity_code),
applicant_income_000s INTEGER,
purchaser_type SMALLINT REFERENCES Purchaser_Type(purchaser_type),
rate_spread NUMERIC(10,4),
hoepa_status SMALLINT REFERENCES HOEPA_Status(hoepa_status),
lien_status SMALLINT REFERENCES Lien_Status(lien_status),
sequence_number INTEGER,
application_date_indicator SMALLINT,
location_id INTEGER NOT NULL REFERENCES Location(location_id)
);
CREATE INDEX IF NOT EXISTS ix_application_location ON Application(location_id);


-- ======================================
-- 1NF Join tables (repeating attributes)
-- ======================================
DROP TABLE IF EXISTS Applicant_Race CASCADE;
CREATE TABLE Applicant_Race (
application_id BIGINT REFERENCES Application(application_id) ON DELETE
CASCADE,
race_number SMALLINT CHECK (race_number BETWEEN 1 AND 5),
race_code SMALLINT REFERENCES Race(race_code),
PRIMARY KEY (application_id, race_number)
);
DROP TABLE IF EXISTS Co_Applicant_Race CASCADE;
CREATE TABLE Co_Applicant_Race (
application_id BIGINT REFERENCES Application(application_id) ON DELETE
CASCADE,
race_number SMALLINT CHECK (race_number BETWEEN 1 AND 5),
race_code SMALLINT REFERENCES Race(race_code),
PRIMARY KEY (application_id, race_number)
);
DROP TABLE IF EXISTS Application_Denial_Reason CASCADE;
CREATE TABLE Application_Denial_Reason (
application_id BIGINT REFERENCES Application(application_id) ON DELETE
CASCADE,
denial_number SMALLINT CHECK (denial_number BETWEEN 1 AND 3),
denial_reason SMALLINT REFERENCES Denial_Reason(denial_reason),
PRIMARY KEY (application_id, denial_number)
);


-- =========================
-- Optional: All-null helper
-- =========================
DROP TABLE IF EXISTS Null_Columns CASCADE;
CREATE TABLE Null_Columns (
new_id SMALLINT PRIMARY KEY DEFAULT 1,
edit_status TEXT,
edit_status_name TEXT
);
COMMIT;