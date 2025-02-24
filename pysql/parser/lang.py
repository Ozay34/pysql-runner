import ply.lex as lex

states = (
    ("pycode", "exclusive"),
)

tokens = (
    "SQL",
    "PYCODE",
    "PYVAR",
    "PYVAL",
    "CONN",
    "PYCONN"

)
literals = ";"

# SQL

def t_sql(t):
    r"[^@\&\{\};]+"
    t.type = "SQL"
    t.lexer.lineno += t.value.count("\n")
    return t

def t_conn(t):
    r"@[^\{\}\s]+\s?"
    t.type = "CONN"
    t.lexer.lineno += t.value.count("\n")
    t.value = t.value.strip()[1:]
    return t

# Python code

def t_pycode(t):
    r"\{"
    t.lexer.pycode_start = t.lexer.lexpos
    t.lexer.level = 1
    t.lexer.pytype = "PYCODE"
    t.lexer.begin("pycode")
    pass

def t_pycode_code(t):
    r"[^\{\}]"
    pass

def t_pycode_lbrace(t):
    r"\{"
    t.lexer.level += 1

def t_pycode_rbrace(t):
    r"\}"
    t.lexer.level -= 1

    # Final closing brace
    if t.lexer.level == 0:
        t.lexer.sql_start = t.lexer.lexpos
        t.lexer.begin("INITIAL")

        t.value = t.lexer.lexdata[t.lexer.pycode_start:t.lexer.lexpos-1]
        t.type = t.lexer.pytype
        t.lexer.lineno += t.value.count("\n")
        return t

# Python inserts

def t_pyvar(t):
    r"&\w+"
    t.type = "PYVAR"
    t.value = t.value[1:]
    return t

def t_pyval(t):
    r"&\{"
    t.lexer.pycode_start = t.lexer.lexpos
    t.lexer.level = 1
    t.lexer.pytype = "PYVAL"
    t.lexer.begin("pycode")
    pass

def t_pyconn(t):
    r"@\{"
    t.lexer.pycode_start = t.lexer.lexpos
    t.lexer.level = 1
    t.lexer.pytype = "PYCONN"
    t.lexer.begin("pycode")
    pass

# Error handling

def t_error(t):
    print(f"Illegal character: {t.value}")
    t.lexer.skip(1)

def t_pycode_error(t):
    print(f"Illegal character encountered in python: {t.value}")
    t.lexer.skip(1)


lexer = lex.lex()
