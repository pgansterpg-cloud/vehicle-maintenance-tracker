-- ============================================================
-- Vehicle Maintenance Tracker - Schema (PostgreSQL)
-- ============================================================
-- Run this ONCE in a new, empty database. It creates the three
-- tables and loads the standard service intervals.
--
-- Next steps after running this:
--   * Optional: run sample_data.sql to try the tool with two
--     example vehicles, OR add your own vehicles.
--   * Then run car_tracker.py.
-- ============================================================


-- ------------------------------------------------------------
-- TABLES
-- ------------------------------------------------------------
CREATE TABLE vehicles (
    vehicle_id            INTEGER PRIMARY KEY,
    year                  INTEGER,
    make                  TEXT,
    model                 TEXT,
    nickname              TEXT,
    current_mileage       INTEGER,
    drivetrain            TEXT,      -- FWD, AWD, or RWD
    engine                TEXT,      -- e.g. '2.4L I4'
    fuel_type             TEXT,      -- e.g. 'Gasoline', 'CNG'
    transmission          TEXT,      -- e.g. '6-speed automatic'
    curb_weight_lbs       INTEGER,
    tire_size             TEXT,      -- e.g. '235/55R18'
    fuel_tank_capacity    NUMERIC,   -- gallons for gas, GGE for CNG
    combined_mpg          INTEGER,
    estimated_range_miles INTEGER
);

CREATE TABLE service_types (
    service_type_id INTEGER PRIMARY KEY,
    service_name    TEXT,
    interval_miles  INTEGER,   -- NULL if purely time-based
    interval_months INTEGER    -- NULL if purely mileage-based
);

CREATE TABLE service_records (
    record_id          SERIAL PRIMARY KEY,   -- Postgres auto-generates IDs
    vehicle_id         INTEGER REFERENCES vehicles(vehicle_id),
    service_type_id    INTEGER REFERENCES service_types(service_type_id),
    service_date       DATE,
    mileage_at_service INTEGER
);


-- ------------------------------------------------------------
-- REFERENCE DATA: standard service intervals
-- (due at whichever comes first: mileage or time)
-- ------------------------------------------------------------
INSERT INTO service_types (service_type_id, service_name, interval_miles, interval_months) VALUES
    (1,  'Oil Change (Conventional)',      5000,  6),
    (2,  'Oil Change (Synthetic)',         7500,  12),
    (3,  'Tire Rotation',                  6000,  6),
    (4,  'Transmission Fluid',             45000, 36),
    (5,  'Brake Fluid Flush',              NULL,  24),
    (6,  'Coolant Flush',                  60000, 60),
    (7,  'Engine Air Filter',              15000, 12),
    (8,  'Cabin Air Filter',               15000, 12),
    (9,  'Spark Plugs (Standard)',         30000, NULL),
    (10, 'Spark Plugs (Iridium/Platinum)', 80000, NULL),
    (11, 'Brake Pad Inspection',           15000, 12),
    (12, 'CNG Tank Recertification',       NULL,  36);
