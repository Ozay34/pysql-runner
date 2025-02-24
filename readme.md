# PYSQL
Pysql is a custom parser that can execute both SQL statements and python
statements in the same file.  Syntax is defined below.

## Installation

1. Clone the repository to your local machine.
2. Run `pip install .` in the top level directory to install the command line tool and dependencies.

Note: If your system path does not contain a reference to your python installs
`\Scripts` folder, you will not be able to use the command line option.
(This is the same folder as your pip command is located in)

## Usage

### Command line
Run the following command to execute a pysql script:

`pysql <file> [-v, -c]`

- -v Verbose mode, log out every statement as it is executed
- -c Default connection, if no connection hint is defined in the script, use this connection

To interface with saved presets, use the following command:

`pysql preset <command> [options]`

- list - Lists all saved connections
- add - Adds a new connection to the saved list
- remove - Removes a connection from the saved list
- update - Update an existing connection with new values
- import - Import all connections defined in a JSON document

For more information, use `pysql preset --help` or `pysql preset <command> --help`

### Import
You can use the pysql library in any normal python script.  If it is installed,
simply add the following import to your normal python script:

`from pysql import ...`

## Syntax

### SQL
All code written in a pysql file is by default assumed to be SQL of some variety.
These statements will be passed directly to whatever SQL driver the connection they
are configured to run on is associated with.  Just like a SQL script, statements are
delimited by semicolons ";".

For example, if you have a saved connection "local" and you run the command
`pysql script.pysql -c local`, all sql statements will be executed against your
local database.  See the command line usage section for interfacing with saved
connections.

E.g.

```
SELECT * FROM table;
SELECT * FROM another_table;
```

### Python
Curly brackets "{ ... }" contain python code.  If curly brackets are placed, the
proceeding SQL is considered to be ended (if a semicolon is present or not) and
python code will instead be interpreted until the closing curly bracket.  After
the closing curly bracket, a new SQL statement will begin.

E.g.

```
SELECT * FROM table
{
print("python code")
}
SELECT * FROM another_table
```

### Inserts
Python variables and expressions can be inserted in the middle of SQL statements
without ending them by using the ampersand "&" character.  Text following the
ampersand will be evaluated as a variable by default.  If curly brackets follow
the ampersand, pysql will instead attempt to evaluate the expression and concat
the result to the SQL statement instead.

E.g.
```
{
column = 'id'
}
SELECT &column FROM table
```

or

```
SELECT &{'id' if True else 'fk'} FROM table
```


### Connections
If you do not want to pass a connection through the command line argument when
executing a script, you can instead define the connection right in the script
using connection hints with the "@" character.  E.g.

`@<connection>` A string that resolves a connection

or

`@{python code}` Python code that will be evaluated into a string that resolves a connection

A connection string can be one of several things, and will be evaluated in this order.
These same rules apply to the connection parameter -c on the command line.

1. "default" - whatever connection was passed in the -c parameter for command line executions
2. A string matching the name of a saved connection
3. A file relative to the working directory with connection JSON in this format:
```json
{
  "name": "A unique name that specifies this connection",
  "driver": "The driver to use for this connection (e.g. oracledb)",
  "connection": "The connection string passed to the driver",
  "username": "The username to log in with",
  "password": "The password to lof in with"
}
```
4. A comma seperated list of other connection strings to form a group (see below)

E.g.

```
@local
SELECT * FROM table

@local,database.json
SELECT * FROM another_table

@{'database.json' if True else 'local'}
SELECT * FROM yet_another_table
```

#### Connection groups
If multiple connections are listed, either as a comma seperated list, or as a
saved connection group, sql statements following that connection will be executed
against multiple data sources.  Directives can be used to specify how the results
should be combined and displayed, but the "name" that each connection specifies
will be used to distinguish the results.

### Directives
TODO