
## Schema Migrations

Randovania has multiple file formats that are persisted to the user's computer.
Because of that, changes to these formats must also come with code that allows 
the older format version to be read.

In order to read these older file versions in a simple way, Randovania performs
manipulations on the raw json files read, before being decoded to the Python
classes. 

Each file format has a version number that is persisted with the other fields.
When reading a file, that version number is read and compared to the current
version for the format. If it's lower, a migration function is called to
adjust the data to the next version. This process is repeated until the current
version is reached.

## Formats with migration

Formats used by user data:

- Presets
- LayoutDescription

Formats only used in the repository itself:

- GameDescription
- ItemDatabase

## Best practices for migrations

- Avoid using any existing Randovania code, as these might change in the future
and break old migrations.
- If you depend on database fields, consider adding it to `migration_data.json`
as a way of ensure it can be easily accessible and won't be changed in the future.
