import pytest
import sys
import os

# Add the project root to the python path to import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sql2mongo.lexer.sql_lexer import SqlLexer, LexerError

@pytest.fixture
def lexer():
    l = SqlLexer()
    l.build()
    return l

def test_simple_select(lexer):
    sql = "SELECT name, age FROM users;"
    tokens = lexer.tokenize(sql)
    
    expected_types = ['SELECT', 'IDENTIFIER', 'COMMA', 'IDENTIFIER', 'FROM', 'IDENTIFIER', 'SEMICOLON']
    assert [t.type for t in tokens] == expected_types
    assert [t.value for t in tokens] == ['SELECT', 'name', ',', 'age', 'FROM', 'users', ';']

def test_where_clause_comparisons(lexer):
    sql = "SELECT * FROM products WHERE price > 100;"
    tokens = lexer.tokenize(sql)
    
    expected_types = ['SELECT', 'STAR', 'FROM', 'IDENTIFIER', 'WHERE', 'IDENTIFIER', 'GT', 'NUMBER', 'SEMICOLON']
    assert [t.type for t in tokens] == expected_types
    assert tokens[7].value == 100

def test_string_literal(lexer):
    sql = "SELECT name FROM users WHERE city = 'Delhi';"
    tokens = lexer.tokenize(sql)
    
    expected_types = ['SELECT', 'IDENTIFIER', 'FROM', 'IDENTIFIER', 'WHERE', 'IDENTIFIER', 'EQ', 'STRING', 'SEMICOLON']
    assert [t.type for t in tokens] == expected_types
    assert tokens[7].value == 'Delhi'

def test_conjunctions(lexer):
    sql = "SELECT * FROM table WHERE a=1 AND b!=2 OR c<=3;"
    tokens = lexer.tokenize(sql)
    
    token_types = [t.type for t in tokens]
    assert 'AND' in token_types
    assert 'OR' in token_types
    assert 'EQ' in token_types
    assert 'NE' in token_types
    assert 'LE' in token_types

def test_case_insensitivity(lexer):
    sql = "select Name from Users where Age >= 18;"
    tokens = lexer.tokenize(sql)
    
    assert tokens[0].type == 'SELECT'
    assert tokens[2].type == 'FROM'
    assert tokens[4].type == 'WHERE'

def test_invalid_character_error(lexer):
    sql = "SELECT $ FROM users;"
    with pytest.raises(LexerError) as excinfo:
        lexer.tokenize(sql)
    
    assert "Illegal character '$'" in str(excinfo.value)

def test_all_operators(lexer):
    sql = "= != < > <= >="
    tokens = lexer.tokenize(sql)
    expected = ['EQ', 'NE', 'LT', 'GT', 'LE', 'GE']
    assert [t.type for t in tokens] == expected
