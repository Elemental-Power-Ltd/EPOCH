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

### Optimisation Tasks

Optimisation tasks are filed in the database when they enter the queue, and their results are also added to the database.
The current structure is to have an `optimisation` _schema_ with tables `task_config` and `results`.
The `task_config` table contains a specification of the task that was entered into the queue, with a JSONB column for the search space parameters (these may change over time as the software develops, so don't have their own columns).
The `results` table is then each result from the task with its own row.
A given result has a unique ID so they can be accessed independently (e.g. a client may wish to recall a specific best configuration), and a task ID linking them all together to the task that created them.
