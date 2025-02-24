import ply.yacc as yacc
from .lang import tokens


def p_run(p):
    """run : run sequence
           | sequence"""

def p_sequence(p):
    """sequence : group
                | connection
                | python"""

def p_connection(p):
    """connection : CONN
                  | pyconnection"""
    print(f"Connecting to database: {p[1]}")

def p_group_statements(p):
    """group : group statement
             | statement"""

def p_statement(p):
    """statement : fragment
                 | fragment ';'
                 | fragment python
                 | fragment python ';'"""
    statement = p[1].strip()
    if len(statement) == 0:
        return
    print(f"Executing sql:", "\t"+"\t".join(statement.splitlines(True)), sep="\n")
    #TODO: Execute the sql statement

def p_fragment_insert(p):
    """fragment : fragment SQL
                | fragment insert"""

    p[0] = p[1] + p[2]

def p_fragment_standalone(p):
    """fragment : SQL
                | insert"""
    p[0] = p[1]

def p_insert_var(p):
    """insert : PYVAR"""
    var = p[1].strip()
    print(f"Resolving python variable: {var}")
    p[0] = "{Python variable: " + var + "}"
    #TODO: Eval the python variable

def p_insert_eval(p):
    """insert : PYVAL"""
    insert = p[1].strip()
    print(f"Resolving python value: {insert}")
    p[0] = "{Python expression: " + insert + "}"
    #TODO: Eval the python expression

def p_python_exec(p):
    """python : PYCODE"""
    code = p[1].strip()
    print(f"Executing python:", "\t"+"\t".join(code.splitlines(True)), sep="\n")
    #TODO: Exec the python code

def p_pyconnection_eval(p):
    """pyconnection : PYCONN"""
    connection = p[1].strip()
    print(f"Resolving python connection: {connection}")
    p[0] = "{Python connection: " + connection + "}"
    #TODO: Eval the python connection

def p_error(p):
    print(f"Parser error: {p}")


parser = yacc.yacc()
