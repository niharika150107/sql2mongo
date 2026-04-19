import pytest
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sql2mongo.parser.sql_parser import get_parser
from sql2mongo.ast.nodes import SelectQuery, LogicalCondition, Comparison

@pytest.fixture
def parser():
    return get_parser()

def test_simple_select(parser):
    sql = "SELECT name, age FROM users;"
    ast = parser.parse(sql)
    
    assert isinstance(ast, SelectQuery)
    assert ast.columns == ['name', 'age']
    assert ast.table == 'users'
    assert ast.where is None

def test_select_all(parser):
    sql = "SELECT * FROM items;"
    ast = parser.parse(sql)
    
    assert ast.columns == ['*']

def test_where_single_condition(parser):
    sql = "SELECT * FROM users WHERE age > 18;"
    ast = parser.parse(sql)
    
    assert isinstance(ast.where, Comparison)
    assert ast.where.identifier == 'age'
    assert ast.where.operator == '>'
    assert ast.where.value == 18

def test_where_and_condition(parser):
    sql = "SELECT * FROM users WHERE age > 18 AND city = 'NY';"
    ast = parser.parse(sql)
    
    assert isinstance(ast.where, LogicalCondition)
    assert ast.where.operator == 'AND'
    assert isinstance(ast.where.left, Comparison)
    assert isinstance(ast.where.right, Comparison)

def test_precedence(parser):
    # AND should bind tighter than OR
    sql = "SELECT * FROM t WHERE a=1 OR b=2 AND c=3;"
    ast = parser.parse(sql)
    
    # Expected structure: (a=1) OR ((b=2) AND (c=3))
    assert ast.where.operator == 'OR'
    assert isinstance(ast.where.left, Comparison)
    assert isinstance(ast.where.right, LogicalCondition)
    assert ast.where.right.operator == 'AND'

def test_syntax_error(parser):
    sql = "SELECT FROM users;" # Missing column list
    with pytest.raises(SyntaxError):
        parser.parse(sql)

def test_invalid_operator(parser):
    # Lexer might catch this first, but if it passes lexer, parser should fail grammar if structure is wrong
    # But here, let's test a structure error
    sql = "SELECT * FROM users WHERE age 18;" # Missing operator
    with pytest.raises(SyntaxError):
        parser.parse(sql)
