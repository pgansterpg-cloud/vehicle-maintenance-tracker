-- ============================================================
-- Vehicle Maintenance Tracker - Status Report Query (PostgreSQL)
-- ============================================================
-- The same query car_tracker.py runs for menu option 2.
-- Run it directly in pgAdmin any time to see what's due.
--
-- Status priority: OVERDUE first, then DUE SOON (within 500 miles
-- or 30 days), then OK.
-- ============================================================


WITH latest_service AS (
    -- most recent service date per vehicle + service type
    SELECT vehicle_id, service_type_id, MAX(service_date) AS last_service_date
    FROM service_records
    GROUP BY vehicle_id, service_type_id
),
latest_with_mileage AS (
    -- the mileage logged on that most recent date
    SELECT ls.vehicle_id, ls.service_type_id, ls.last_service_date,
           sr.mileage_at_service AS last_service_mileage
    FROM latest_service ls
    JOIN service_records sr
        ON sr.vehicle_id = ls.vehicle_id
        AND sr.service_type_id = ls.service_type_id
        AND sr.service_date = ls.last_service_date
),
due_calc AS (
    -- next due point by mileage AND by date
    SELECT
        v.year || ' ' || v.make || ' ' || v.model AS vehicle,
        v.current_mileage,
        st.service_name,
        lwm.last_service_date,
        lwm.last_service_mileage,
        CASE WHEN st.interval_miles IS NOT NULL
             THEN lwm.last_service_mileage + st.interval_miles
             ELSE NULL END AS next_due_mileage,
        CASE WHEN st.interval_months IS NOT NULL
             THEN (lwm.last_service_date + (st.interval_months || ' months')::interval)::date
             ELSE NULL END AS next_due_date
    FROM latest_with_mileage lwm
    JOIN vehicles v ON lwm.vehicle_id = v.vehicle_id
    JOIN service_types st ON lwm.service_type_id = st.service_type_id
),
with_status AS (
    -- overdue checks come first, so they win over "due soon"
    SELECT
        vehicle,
        service_name,
        current_mileage,
        next_due_mileage,
        next_due_date,
        CASE
            WHEN next_due_mileage IS NOT NULL AND current_mileage >= next_due_mileage
                THEN 'OVERDUE (mileage)'
            WHEN next_due_date IS NOT NULL AND CURRENT_DATE >= next_due_date
                THEN 'OVERDUE (time)'
            WHEN next_due_mileage IS NOT NULL AND current_mileage >= next_due_mileage - 500
                THEN 'DUE SOON (mileage)'
            WHEN next_due_date IS NOT NULL AND CURRENT_DATE >= next_due_date - INTERVAL '30 days'
                THEN 'DUE SOON (time)'
            ELSE 'OK'
        END AS status
    FROM due_calc
)
SELECT *
FROM with_status
ORDER BY
    CASE
        WHEN status LIKE 'OVERDUE%'  THEN 1
        WHEN status LIKE 'DUE SOON%' THEN 2
        ELSE 3
    END,
    vehicle;
