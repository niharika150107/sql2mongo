import pytest
import sys
import os
import json

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sql2mongo.parser.sql_parser import get_parser
from sql2mongo.codegen.mongodb_generator import MongoDBGenerator

@pytest.fixture
def parser():
    return get_parser()

@pytest.fixture
def generator():
    return MongoDBGenerator()

def test_select_all(parser, generator):
    sql = "SELECT * FROM users;"
    ast = parser.parse(sql)
    query = generator.generate(ast)
    assert query == 'db.users.find({  })' # Empty dict might space out: "{ }" or "{  }" depending on logic

def test_select_columns(parser, generator):
    sql = "SELECT name, age FROM users;"
    ast = parser.parse(sql)
    query = generator.generate(ast)
    assert 'db.users.find({  },' in query
    assert 'name: 1' in query
    assert 'age: 1' in query

def test_simple_where(parser, generator):
    sql = "SELECT * FROM users WHERE age > 25;"
    ast = parser.parse(sql)
    query = generator.generate(ast)
    assert '{ age: { $gt: 25 } }' in query

def test_equality(parser, generator):
    sql = "SELECT * FROM users WHERE city = 'Delhi';"
    ast = parser.parse(sql)
    query = generator.generate(ast)
    assert '{ city: "Delhi" }' in query

def test_and_condition(parser, generator):
    sql = "SELECT * FROM users WHERE age >= 18 AND city = 'Delhi';"
    ast = parser.parse(sql)
    query = generator.generate(ast)
    assert '$and' in query
    assert '{ age: { $gte: 18 } }' in query
    assert '{ city: "Delhi" }' in query

def test_or_condition(parser, generator):
    sql = "SELECT * FROM users WHERE age < 18 OR age > 60;"
    ast = parser.parse(sql)
    query = generator.generate(ast)
    assert '$or' in query
    assert '{ age: { $lt: 18 } }' in query
    assert '{ age: { $gt: 60 } }' in query
