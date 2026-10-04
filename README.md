# Vehicle Maintenance Tracker

A command-line tool, backed by a PostgreSQL database, that tracks vehicle maintenance and tells you what's **overdue**, what's **due soon**, and what's **OK**, based on both mileage and time.

I built this to track maintenance on my own two cars: a 2010 Honda Civic GX that runs on compressed natural gas (CNG) and a 2012 Chevrolet Equinox. Manufacturer schedules mix mileage-based and time-based intervals ("every 7,500 miles or 12 months, whichever comes first"), which makes it easy to lose track of what's actually due. This tool does that math for me.

## Features

- **Log service records** with input validation: IDs must exist, mileage must be a whole number, and dates must be real, correctly formatted, and not in the future.
- **Check maintenance status** for every vehicle, color-coded in the terminal: overdue in red, due soon (within 500 miles or 30 days) in yellow, OK in green, sorted so the most urgent items are on top.
- **View vehicles** with full specs, including the correct fuel unit per vehicle (gallons for gasoline, gasoline gallon equivalents for CNG).
- **Update mileage** and **add new vehicles** right from the menu, no SQL required.

## Example output

Status report, with the Civic's mileage set to 65,100 to show the "due soon" warning:

```
==============================================================================================================
VEHICLE                      SERVICE                        MILEAGE    NEXT DUE                   STATUS
==============================================================================================================
2010 Honda Civic GX          Oil Change (Synthetic)         65100      65500 mi / 2027-06-28      DUE SOON (mileage)
2010 Honda Civic GX          Cabin Air Filter               65100      75000 mi / 2027-09-28      OK
2012 Chevrolet Equinox LTZ   Cabin Air Filter               137500     152500 mi / 2027-09-28     OK
2012 Chevrolet Equinox LTZ   Oil Change (Synthetic)         137500     145000 mi / 2027-09-21     OK
==============================================================================================================
```

## Tech stack

- **Python 3** with **psycopg2** to connect to the database
- **PostgreSQL**, hosted on **Neon** (free cloud Postgres)
- **pgAdmin** for building and inspecting the database

## Project files

| File | Purpose |
|---|---|
| `car_tracker.py` | The command-line tool |
| `schema.sql` | Creates the three tables and loads the standard service intervals |
| `sample_data.sql` | Optional example data: my two vehicles and their service history |
| `status_query.sql` | The status report query, for running directly in pgAdmin |
| `requirements.txt` | Python dependencies |

## Setup

1. **Create an empty PostgreSQL database.** A free [Neon](https://neon.tech) project works well.
2. **Run `schema.sql`** in your database (for example, in pgAdmin's Query Tool).
3. **Optional:** run `sample_data.sql` to try the tool with example vehicles, or skip it and add your own vehicles from the menu.
4. **Install the dependency:**
   ```
   pip install -r requirements.txt
   ```
5. **Set your database connection string** as an environment variable. Never put it in the code.

   Windows (PowerShell):
   ```
   $env:DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
   ```
   macOS/Linux:
   ```
   export DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
   ```
6. **Run it:**
   ```
   python car_tracker.py
   ```

## How the status query works

The report is built in a chain of CTEs (common table expressions), each one handling one step:

1. **`latest_service`** finds the most recent service date for each vehicle and service type.
2. **`latest_with_mileage`** pulls the mileage recorded at that most recent service.
3. **`due_calc`** calculates the next due point by mileage *and* by date.
4. **`with_status`** labels each item OVERDUE, DUE SOON, or OK. The overdue checks run first, because anything overdue is also "within 500 miles" and would otherwise be mislabeled as due soon.
5. The final query sorts by urgency using a `CASE` expression, since the statuses don't sort correctly alphabetically.

## What I learned

- **Setting up a real database was the hardest part.** Getting a cloud PostgreSQL database running on Neon and connected to pgAdmin taught me a lot about how databases are actually set up, not just queried.
- **Changing a database as it grows.** I added features over time, so I used `ALTER TABLE` to add columns and `UPDATE` to fill in values, and I fixed a bug where Postgres wasn't auto-generating record IDs by attaching a sequence to the column.
- **How Python functions work together.** I wrote small helper functions for validating input and reused them throughout the program, which taught me how functions pass data to each other and how one change affects the rest of the code.
- **Running and debugging a script in PowerShell.** Running the tool after every change let me see exactly how my code changed the program. Along the way I learned to read error messages and track down bugs, like a misplaced set of triple quotes and a validation check comparing against the wrong list.
- **Data quality matters.** Validating every input before it reaches the database keeps bad data out in the first place.
- **Building for other people, not just myself.** The first version only worked with my own cars hardcoded in. I split the SQL into a schema and optional sample data and added an "Add a vehicle" option, so anyone can set it up with their own vehicles.

## Ideas for the future

- Add the remaining specs (weight, tank size, MPG, range) to the "Add a vehicle" prompts
- Edit or delete service records from the menu
- View the full service history for one vehicle
- A simple web dashboard instead of a terminal menu

## A note on service intervals

The intervals in `schema.sql` are general industry guidelines, not any one manufacturer's schedule. Always check your owner's manual for your specific vehicle.
