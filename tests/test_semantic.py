import pytest
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sql2mongo.parser.sql_parser import get_parser
from sql2mongo.semantic.semantic_analyzer import SemanticAnalyzer, SemanticError

SCHEMA = {
    "users": {
        "id": "int",
        "name": "string",
        "age": "int",
        "city": "string"
    },
    "orders": {
        "order_id": "int",
        "user_id": "int",
        "amount": "int"
    }
}

@pytest.fixture
def parser():
    return get_parser()

@pytest.fixture
def analyzer():
    return SemanticAnalyzer(SCHEMA)

def test_valid_query(parser, analyzer):
    sql = "SELECT name, age FROM users WHERE age > 25;"
    ast = parser.parse(sql)
    analyzer.validate_query(ast) # Should not raise error

def test_valid_select_all(parser, analyzer):
    sql = "SELECT * FROM users;"
    ast = parser.parse(sql)
    analyzer.validate_query(ast)

def test_invalid_table(parser, analyzer):
    sql = "SELECT name FROM customers;"
    ast = parser.parse(sql)
    with pytest.raises(SemanticError, match="Table 'customers' does not exist"):
        analyzer.validate_query(ast)

def test_invalid_column_select(parser, analyzer):
    sql = "SELECT salary FROM users;"
    ast = parser.parse(sql)
    with pytest.raises(SemanticError, match="Column 'salary' does not exist"):
        analyzer.validate_query(ast)

def test_invalid_column_where(parser, analyzer):
    sql = "SELECT name FROM users WHERE salary > 1000;"
    ast = parser.parse(sql)
    with pytest.raises(SemanticError, match="Column 'salary' does not exist"):
        analyzer.validate_query(ast)

def test_type_mismatch_int_string(parser, analyzer):
    sql = "SELECT name FROM users WHERE age = 'twenty';"
    ast = parser.parse(sql)
    with pytest.raises(SemanticError, match="Type mismatch.*Expected int but got string"):
        analyzer.validate_query(ast)

def test_type_mismatch_string_int(parser, analyzer):
    sql = "SELECT name FROM users WHERE city = 123;"
    ast = parser.parse(sql)
    with pytest.raises(SemanticError, match="Type mismatch.*Expected string but got int"):
        analyzer.validate_query(ast)

def test_duplicate_columns(parser, analyzer):
    sql = "SELECT name, name FROM users;"
    ast = parser.parse(sql)
    with pytest.raises(SemanticError, match="Duplicate column 'name'"):
        analyzer.validate_query(ast)
