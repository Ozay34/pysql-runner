import pytest
from pysql.parser.lang import lexer as base_lexer
lexer = base_lexer.clone()


@pytest.fixture(autouse=True)
def setup():
    global lexer
    lexer = base_lexer.clone()


def assert_lex(*expected):
    global lexer
    result = [tok for tok in lexer]
    for result_tok, expected_tok in zip(result, expected):
        assert result_tok.type == expected_tok[0], "Token type does not match"
        assert result_tok.value == expected_tok[1], "Token value does not match"
        assert result_tok.lineno == expected_tok[2], "Token line number does not match"

# Plain SQL Tests

def test_single_statement():
    lexer.input("""SELECT * FROM table""")
    assert_lex(
        ("SQL", "SELECT * FROM table", 1)
    )

def test_multiple_statements():
    lexer.input("""SELECT * FROM table; SELECT * FROM another_table""")
    assert_lex(
        ("SQL", "SELECT * FROM table", 1),
        (";", ";", 1),
        ("SQL", " SELECT * FROM another_table", 1)
    )

def test_multiline_statement():
    lexer.input("""
        SELECT *
        FROM table
    """)
    assert_lex(
        ("SQL", "\n        SELECT *\n        FROM table\n    ", 1)
    )

def test_multiple_multiline_statements():
    lexer.input("""
        SELECT * FROM table;
        SELECT *
        FROM another_table;
    """)
    assert_lex(
        ("SQL", "\n        SELECT * FROM table", 1),
        (";", ";", 2),
        ("SQL", "\n        SELECT *\n        FROM another_table", 2),
        (";", ";", 4),
        ("SQL", "\n    ", 4)
    )

def test_ending_semicolon():
    lexer.input("""SELECT * FROM table;""")
    assert_lex(
        ("SQL", "SELECT * FROM table", 1),
        (";", ";", 1)
    )

# Python tests

def test_python():
    lexer.input("""{'Yes' if True else 'No'}""")
    assert_lex(
        ("PYCODE", "'Yes' if True else 'No'", 1)
    )

def test_multiline_python():
    lexer.input("""{
        def func():
            return False
    }""")
    assert_lex(
        ("PYCODE", "\n        def func():\n            return False\n    ", 1)
    )

def test_python_before_sql():
    lexer.input("""
        {thing.action()}
        SELECT * FROM table
    """)
    assert_lex(
        ("SQL", "\n        ", 1),
        ("PYCODE", "thing.action()", 2),
        ("SQL", "\n        SELECT * FROM table\n    ", 2)
    )

def test_python_after_sql():
    lexer.input("""
        SELECT * FROM table
        {thing.action()}
    """)
    assert_lex(
        ("SQL", "\n        SELECT * FROM table\n        ", 1),
        ("PYCODE", "thing.action()", 3),
        ("SQL", "\n    ", 3)
    )

def test_python_before_sql_with_semicolon():
    lexer.input("""
        {thing.action()}
        SELECT * FROM table;
    """)
    assert_lex(
        ("SQL", "\n        ", 1),
        ("PYCODE", "thing.action()", 2),
        ("SQL", "\n        SELECT * FROM table", 2),
        (";", ";", 3),
        ("SQL", "\n    ", 3)
    )

def test_python_after_sql_with_semicolon():
    lexer.input("""
        SELECT * FROM table;
        {thing.action()}
    """)
    assert_lex(
        ("SQL", "\n        SELECT * FROM table", 1),
        (";", ";", 2),
        ("SQL", "\n        ", 2),
        ("PYCODE", "thing.action()", 3),
        ("SQL", "\n    ", 3)
    )

# Python values and inserts

def test_python_value_before_sql():
    lexer.input("""&op table (SELECT * FROM another_table)""")
    assert_lex(
        ("PYVAR", "op", 1),
        ("SQL", " table (SELECT * FROM another_table)", 1)
    )

def test_python_value_between_sql():
    lexer.input("""SELECT &column FROM table""")
    assert_lex(
        ("SQL", "SELECT ", 1),
        ("PYVAR", "column", 1),
        ("SQL", " FROM table", 1)
    )

def test_python_value_after_sql():
    lexer.input("""SELECT * FROM &table""")
    assert_lex(
        ("SQL", "SELECT * FROM ", 1),
        ("PYVAR", "table", 1)
    )

def test_python_value_after_sql_with_semicolon():
    lexer.input("""SELECT * FROM &table;""")
    assert_lex(
        ("SQL", "SELECT * FROM ", 1),
        ("PYVAR", "table", 1),
        (";", ";", 1)
    )

def test_python_insert_before_sql():
    lexer.input("""&{'CREATE TABLE' if create else 'INSERT INTO'} table (SELECT * FROM another_table)""")
    assert_lex(
        ("PYVAL", "'CREATE TABLE' if create else 'INSERT INTO'", 1),
        ("SQL", " table (SELECT * FROM another_table)", 1)
    )

def test_python_insert_between_sql():
    lexer.input("""SELECT &{'*' if all else 'column'} FROM table""")
    assert_lex(
        ("SQL", "SELECT ", 1),
        ("PYVAL", "'*' if all else 'column'", 1),
        ("SQL", " FROM table", 1)
    )

def test_python_insert_after_sql():
    lexer.input("""SELECT * FROM &{'table' if table else 'another_table'}""")
    assert_lex(
        ("SQL", "SELECT * FROM ", 1),
        ("PYVAL", "'table' if table else 'another_table'", 1)
    )

def test_python_insert_after_sql_with_semicolon():
    lexer.input("""SELECT * FROM &{'table' if table else 'another_table'};""")
    assert_lex(
        ("SQL", "SELECT * FROM ", 1),
        ("PYVAL", "'table' if table else 'another_table'", 1),
        (";", ";", 1)
    )

def test_multiline_pyton_insert():
    lexer.input("""
        SELECT &{
            'column_a' if c1 else
            'column_b' if c2 else
            'column_c'
        } FROM table
    """)
    assert_lex(
        ("SQL", "\n        SELECT ", 1),
        ("PYVAL", "\n            'column_a' if c1 else\n            'column_b' if c2 else\n            'column_c'\n        ", 2),
        ("SQL", " FROM table\n    ", 6)
    )

# Connection strings
def test_conn_plain():
    lexer.input("""@database""")
    assert_lex(
        ("CONN", "database", 1)
    )

def test_conn_file():
    lexer.input("""@file.json""")
    assert_lex(
        ("CONN", "file.json", 1)
    )

def test_conn_path():
    lexer.input(r"""@C:\path\to\file.json""")
    assert_lex(
        ("CONN", r"C:\path\to\file.json", 1)
    )

def test_conn_before_sql():
    lexer.input("""
        @database
        SELECT * FROM table
    """)
    assert_lex(
        ("SQL", "\n        ", 1),
        ("CONN", "database", 2),
        ("SQL", "        SELECT * FROM table\n    ", 3)
    )

def test_conn_after_sql():
    lexer.input("""
        SELECT * FROM table
        @database
        SELECT * FROM another_table
    """)
    assert_lex(
        ("SQL", "\n        SELECT * FROM table\n        ", 1),
        ("CONN", "database", 3),
        ("SQL", "        SELECT * FROM another_table\n    ", 4)
    )

def test_pyconn_before_sql():
    lexer.input("""
        @{['db1', 'db2']}
        SELECT * FROM table
    """)
    assert_lex(
        ("SQL", "\n        ", 1),
        ("PYCONN", "['db1', 'db2']", 2),
        ("SQL", "\n        SELECT * FROM table\n    ", 2)
    )

def test_pyconn_after_sql():
    lexer.input("""
        SELECT * FROM table
        @{['db1', 'db2']}
        SELECT * FROM another_table
    """)
    assert_lex(
        ("SQL", "\n        SELECT * FROM table\n        ", 1),
        ("PYCONN", "['db1', 'db2']", 3),
        ("SQL", "\n        SELECT * FROM another_table\n    ", 3)
    )

# Larger combined cases

def test_combined_case_1():
    lexer.input("""
        {table_name = 'test_table'}

        @database
        &{'CREATE TABLE' if create else 'INSERT INTO'} &table_name (
            SELECT * FROM another_table
        );

        SELECT * FROM &table_name;

        {print(table_name)}
    """)
    assert_lex(
        ("SQL", "\n        ", 1),
        ("PYCODE", "table_name = 'test_table'", 2),
        ("SQL", "\n\n        ", 2),
        ("CONN", "database", 4),
        ("SQL", "        ", 5),
        ("PYVAL", "'CREATE TABLE' if create else 'INSERT INTO'", 5),
        ("SQL", " ", 5),
        ("PYVAR", "table_name", 5),
        ("SQL", " (\n            SELECT * FROM another_table\n        )", 5),
        (";", ";", 7),
        ("SQL", "\n\n        SELECT * FROM ", 7),
        ("PYVAR", "table_name", 9),
        (";", ";", 9),
        ("SQL", "\n\n        ", 9),
        ("PYCODE", "print(table_name)", 11),
        ("SQL", "\n    ", 11)
    )