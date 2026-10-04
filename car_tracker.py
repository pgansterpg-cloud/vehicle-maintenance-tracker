"""
Vehicle Maintenance Tracker - CLI Tool
----------------------------------------
Connects to your real Postgres (Neon) database and lets you:
  1) Log a new service record (instead of hand-typing INSERT statements)
  2) Check what's due / overdue across all your vehicles
  3) View your vehicles and their specs
  4) Update a vehicle's current mileage
  5) Add a new vehicle 

SETUP:
  1. Install dependencies:
       pip install psycopg2-binary --break-system-packages

  2. Set your Neon connection string as an environment variable
     (never hardcode your password directly in this file):

     macOS/Linux:
       export DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"

     Windows (PowerShell):
       $env:DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"

     Grab the exact connection string from your Neon dashboard.

  3. Run it:
       python car_tracker.py
"""

import os
import sys
from datetime import date

try:
    import psycopg2
except ImportError:
    print("Missing dependency. Run: pip install psycopg2-binary --break-system-packages")
    sys.exit(1)


def get_connection():
    """Connect using the DATABASE_URL environment variable."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set.")
        print("See the setup instructions at the top of this file.")
        sys.exit(1)
    try:
        return psycopg2.connect(db_url)
    except psycopg2.OperationalError as e:
        print(f"Could not connect to the database:\n{e}")
        sys.exit(1)

def ask_for_int(prompt):
    while True:
        answer = input(prompt).strip()
        try:
            return int(answer)
        except ValueError:
            print("Please enter a whole number.")

def ask_for_valid_id(prompt,valid_ids):
    while True:
        choice = ask_for_int(prompt)
        if choice in valid_ids:
            return choice
        print(f"That ID doesn't exist. Choose from: {valid_ids}")

def get_vehicle_ids(conn):
    cur = conn.cursor()
    cur.execute("SELECT vehicle_id FROM vehicles")
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    return ids

def get_service_type_ids(conn):
    cur = conn.cursor()
    cur.execute("SELECT service_type_id FROM service_types")
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    return ids

def ask_for_date(prompt):
    while True:
        answer = input(prompt).strip()
        if not answer:
            return date.today().isoformat()
        try:
            entered = date.fromisoformat(answer) 
        except ValueError:
            print("Please use the format YYYY-MM-DD, like 2026-01-01.")
            continue
        if entered > date.today():
            print("Can't be a future date")
            continue
        return entered.isoformat()

def ask_for_text(prompt, required=True):
    while True:
        answer = input(prompt).strip()
        if answer:
            return answer
        if not required:
            return None
        print("This can't be blank.")


# ------------------------------------------------------------
# CORE QUERY - same logic as status_query.sql, just embedded here
# ------------------------------------------------------------
STATUS_QUERY = """
WITH latest_service AS (
    SELECT vehicle_id, service_type_id, MAX(service_date) AS last_service_date
    FROM service_records
    GROUP BY vehicle_id, service_type_id
),
latest_with_mileage AS (
    SELECT ls.vehicle_id, ls.service_type_id, ls.last_service_date,
           sr.mileage_at_service AS last_service_mileage
    FROM latest_service ls
    JOIN service_records sr
        ON sr.vehicle_id = ls.vehicle_id
        AND sr.service_type_id = ls.service_type_id
        AND sr.service_date = ls.last_service_date
),
due_calc AS (
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
        WHEN status LIKE 'OVERDUE%' THEN 1
        WHEN status LIKE 'DUE SOON%' THEN 2
        ELSE 3
    END,
    vehicle;
"""

# ANSI colors for terminal output (works on most terminals, harmless if not supported)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_status(conn):
    """Run the core query and print a readable report."""
    cur = conn.cursor()
    cur.execute(STATUS_QUERY)
    rows = cur.fetchall()
    cur.close()

    if not rows:
        print("No service records found yet. Log one first (option 1).")
        return

    print("\n" + "=" * 110)
    print(f"{'VEHICLE':<28} {'SERVICE':<30} {'MILEAGE':<10} {'NEXT DUE':<26} STATUS")
    print("=" * 110)
    for vehicle, service, mileage, next_mi, next_date, status in rows:
        due_str = ""
        if next_mi is not None:
            due_str += f"{next_mi} mi"
        if next_date is not None:
            due_str += f" / {next_date}" if due_str else str(next_date)
        if "OVERDUE" in status:
            color = RED
        elif "DUE SOON" in status:
            color = YELLOW
        else:
            color = GREEN
        print(f"{vehicle:<28} {service:<30} {mileage:<10} {due_str:<26} {color}{status}{RESET}")
    print("=" * 110 + "\n")


def list_vehicles(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT vehicle_id, year, make, model, nickname, current_mileage,
               drivetrain, engine, fuel_type, transmission, tire_size,
               curb_weight_lbs, fuel_tank_capacity, combined_mpg, estimated_range_miles
        FROM vehicles
        ORDER BY vehicle_id
    """)
    rows = cur.fetchall()
    cur.close()

    print("\nYour vehicles:")
    for r in rows:
        (vid, year, make, model, nickname, mileage, drivetrain, engine, fuel, trans, tires, weight,
        tank_capacity, mpg, range_mi) = r
        name = f" ({nickname})" if nickname else ""
        print(f"  [{vid}] {year} {make} {model}{name} - {mileage} mi")
        print(f"       {drivetrain or '?'} | {engine or '?'} | {fuel or '?'} | {trans or '?'}")
        tank_unit = "GGE" if fuel == "CNG" else "gal"
        print(f"       Tires: {tires or '?'} | Weight: {weight or '?'} lbs | Tank capacity: {tank_capacity or '?'} {tank_unit} | MPG: {mpg or '?'} | Range:  {range_mi or '?'} mi")
    print()


def list_service_types(conn):
    cur = conn.cursor()
    cur.execute("SELECT service_type_id, service_name FROM service_types ORDER BY service_type_id")
    rows = cur.fetchall()
    cur.close()
    print("\nService types:")
    for sid, name in rows:
        print(f"  [{sid}] {name}")
    print()


def log_service(conn):
    list_vehicles(conn)
    vehicle_id = ask_for_valid_id("Vehicle ID: ", get_vehicle_ids(conn))

    list_service_types(conn)
    service_type_id = ask_for_valid_id("Service type ID: ",get_service_type_ids(conn))

    mileage = ask_for_int("Mileage at service: ")

    service_date = ask_for_date("Date (YYYY-MM-DD, blank for today): ")

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO service_records (vehicle_id, service_type_id, service_date, mileage_at_service)
            VALUES (%s, %s, %s, %s)
            """,
            (vehicle_id, service_type_id, service_date, mileage),
        )
        conn.commit()
        print("Service record logged.\n")
    except Exception as e:
        conn.rollback()
        print(f"Something went wrong: {e}\n")
    finally:
        cur.close()


def update_mileage(conn):
    list_vehicles(conn)
    vehicle_id = ask_for_valid_id("Vehicle ID to update: ", get_vehicle_ids(conn))
    new_mileage = ask_for_int("New current mileage: ")

    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE vehicles SET current_mileage = %s WHERE vehicle_id = %s",
            (new_mileage, vehicle_id),
        )
        conn.commit()
        print("Mileage updated.\n")
    except Exception as e:
        conn.rollback()
        print(f"Something went wrong: {e}\n")
    finally:
        cur.close()

def add_vehicle(conn):
    print("\nAdd a new vehicle (press Enter to skip optional fields)")
    year = ask_for_int("Year: ")
    make = ask_for_text("Make: ")
    model = ask_for_text("Model: ")
    nickname = ask_for_text("Nickname (optional): ", required=False)
    mileage = ask_for_int("Current mileage: ")
    drivetrain = ask_for_text("Drivetrain - FWD/AWD/RWD (optional): ", required=False)
    engine = ask_for_text("Engine, like 2.4L I4 (optional): ", required=False)
    fuel = ask_for_text("Fuel type, like Gasoline (optional): ", required=False)
    trans = ask_for_text("Transmission (optional): ", required=False)

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO vehicles (vehicle_id, year, make, model, nickname, current_mileage,
                                  drivetrain, engine, fuel_type, transmission)
            VALUES ((SELECT COALESCE(MAX(vehicle_id), 0) + 1 FROM vehicles),
                    %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING vehicle_id
            """,
            (year, make, model, nickname, mileage, drivetrain, engine, fuel, trans),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"Vehicle added with ID {new_id}.\n")
    except Exception as e:
        conn.rollback()
        print(f"Something went wrong: {e}\n")
    finally:
        cur.close()

def main():
    conn = get_connection()
    print("Connected to your vehicle maintenance database.")

    menu = """
What do you want to do?
  1) Log a new service record
  2) Check maintenance status (what's due / overdue)
  3) View vehicles
  4) Update a vehicle's current mileage
  5) Add a vehicle
  6) Quit
"""
    while True:
        print(menu)
        choice = input("> ").strip()

        if choice == "1":
            log_service(conn)
        elif choice == "2":
            check_status(conn)
        elif choice == "3":
            list_vehicles(conn)
        elif choice == "4":
            update_mileage(conn)
        elif choice == "5":
            add_vehicle(conn)
        elif choice == "6":
            print("See you next oil change.")
            break
        else:
            print("Not a valid option, try again.\n")

    conn.close()


if __name__ == "__main__":
    main()
