# Elemental Database

The database used in this repository is a PostgreSQL database hosted in a Docker container.
In this document the word _schema_ in italics refers to the PostgreSQL table namespace concept (e.g. `CREATE SCHEMA`),
and the word schema in roman type refers to the structure of a given table.

## Database Users

The main user that you will use is the `python` user. 
This is a relatively powerful superuser account, so please don't accidentally mangle any existing data.

## Database Structure

### Client Data
Client data is stored under the `client_info` _schema_.
This is split into two tables: `client_info.clients` and `client_info.site_info`.
The general structure is that a given client will have many sites, and will have a unique database ID and a human readable name.
Each site will also have a unique database ID, have a foreign key linking to a site, and some metadata about their position including an address and coordinates.
When creating a site ID, please pick something all lower case, joined by underscores, that is reasonably memorable from the name of the site.
For example, "Foobar House" might become `foobar_house`.
If there is a risk of name collision, please prefix with the name of the client (e.g. `quux_foobar_house`).

### Datasets

Most of the information in this database will be in the form of "datasets".
A single dataset is a grouping of generally timestamped data for a single source, for example a dataset might be gas meter readings from Foobar House from 2024-01-01 to 2025-01-01.
The datasets are stored by type under relevant named _schemas_, which tend to align with the endpoints that access them (but not perfectly).
The current _schemas_ are:
* `carbon_intensity`
* `client_meters`
* `heating`
* `renewables`
* `tariffs`
* `weather`

Each of these has a `metadata` table in it, which have varying schemas but will generally contain the site ID that this dataset was generated for, the time it was generated at and some hyperparameters used in the data generation.
The `metadata` table will contain unique dataset IDs, which are randomly generated UUIDv4s. 
These will key into another table in that _schema_, again with its own schema depending on the problem at hand (for example, a gas meter table might have columns `consumption_kwh`, but a solar PV table might have columns `generation_kwh`).
You should be prepared to write custom SQL queries for each type of table you have to access.
Each time series table uses the convention of `start_ts`, `end_ts` where a timestamp should be `start_ts <= timestamp < end_ts`.

### Optimisation Tasks

Optimisation tasks are filed in the database when they enter the queue, and their results are also added to the database.
The current structure is to have an `optimisation` _schema_ with tables 
* `task_config`
* `task_results`
* `portfolio_results`
* `site_results`

The `task_config` table contains a specification of the task that was entered into the queue, with a JSONB column for the search space parameters (these may change over time as the software develops, so don't have their own columns).
The `task_results` table then contains metadata about the completed optimisation task, e.g. how long it took and how many site combinations were assessed.
The `portfolio_results` table has rows with a unique _portfolio ID_ and a shared _task ID_ linking it back to the original optimisation task.
One task generates many portfolio results, which contain information about the optimisation metrics *e.g.* carbon balance, CAPEX.
The `site_results` table contains the individual site level optimistaion metrics for a given portfolio, one portfolio result links to many site results.
A given site result is uniquely identified by a _site ID_, _portfolio ID_ pair and sites must be unique within a portfolio.

## Migrations

Database updates are applied via migrations files, stored in the `./migrations/` directory.
These come as a pair of numbered up and down migration files, in the form `123456_your_migration.up.sql` and `123456_your_migration.down.sql`.
The up migrations will be applied in ascending numeric order, starting from a blank database.
The down migrations will only be used in case of emergencies, but should be correct SQL code to un-do the corresponding up changes.
Up migrations are applied by the test runner, and by the docker image builder, so you should get a database with consistent state.

### Client Data as Migration
You may need a database filled with client data for certain tests.
We don't want to commit client data to git, but we can treat it as a final stage migration.
To add customer data, get a database dump of the rows from the table in SQL format and place it in the migrations directory as `999999_client_data.up.sql`.

### Writing Migration Files

Migration files should contain the minimal SQL code required to change the database structure, and be checked into git.
All migration files should be wrapped in `BEGIN;` `END;` transaction blocks to ensure that a half-completed migration doesn't affect the database structure.
An ideal migration is idempotent, and can be applied twice without changing the database (this takes the form of lots of `IF EXISTS` statements, or similar).
Migrations should be minimally destructive, and favour renaming columns and tables over dropping and re-creating.
If you're adding a new column, think carefully about whether it should have a default entry for old rows.

### Applying Migrations to Production
To apply migrations to production, we have been using the `golang-migrate` package (https://github.com/golang-migrate/migrate).
This maintains a table in the production database that tracks which migrations have been applied and enables easy rollback.
To activate it, run this command
`migrate -database postgres://$PG_USERNAME:$PG_PASSWORD@localhost:5432/elementaldb -path ./migrations up`
from the data_elemental base directory (*i.e.* the migrations should be a subdirectory of where you are).
You may have to install the package, which is installed to `$HOME/go/bin` by default. 
Follow the instructions here:
https://github.com/golang-migrate/migrate/tree/master/cmd/migrate
