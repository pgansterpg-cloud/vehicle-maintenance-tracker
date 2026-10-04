-- ============================================================
-- Vehicle Maintenance Tracker - Sample Data (PostgreSQL)
-- ============================================================
-- OPTIONAL. Two real example vehicles with real specs and service
-- history, so you can try the tool right away.
--
-- Run schema.sql first. Skip this file if you'd rather start
-- with your own vehicles.
-- ============================================================


-- ------------------------------------------------------------
-- VEHICLES
-- ------------------------------------------------------------
INSERT INTO vehicles (
    vehicle_id, year, make, model, nickname, current_mileage,
    drivetrain, engine, fuel_type, transmission,
    curb_weight_lbs, tire_size, fuel_tank_capacity, combined_mpg, estimated_range_miles
) VALUES
    (1, 2010, 'Honda', 'Civic GX', 'CNG Civic', 60000,
     'FWD', '1.8L I4 (CNG)', 'CNG', '5-speed automatic',
     2910, '195/65R15', 8.0, 31, 235),
    (2, 2012, 'Chevrolet', 'Equinox LTZ', 'Equinox', 137500,
     'FWD', '2.4L I4', 'Gasoline', '6-speed automatic',
     3777, '235/55R18', 18.8, 27, 508);


-- ------------------------------------------------------------
-- SERVICE HISTORY
-- record_id is left out on purpose: SERIAL fills it in.
-- ------------------------------------------------------------
INSERT INTO service_records (vehicle_id, service_type_id, service_date, mileage_at_service) VALUES
    (1, 2, '2026-06-28', 58000),    -- Civic: synthetic oil change
    (2, 2, '2026-09-21', 137500),   -- Equinox: synthetic oil change
    (1, 8, '2026-09-28', 60000),    -- Civic: cabin air filter
    (2, 8, '2026-09-28', 137500);   -- Equinox: cabin air filter
