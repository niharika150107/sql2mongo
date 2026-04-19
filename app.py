from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import psycopg2
import json
import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

# ── LAZY GLOBALS ─────────────────────────────────────────
_parser = None
_generator = None
_mongo_db = None

def get_parser():
    global _parser
    if _parser is None:
        from sql2mongo.parser.sql_parser import SqlParser
        _parser = SqlParser()
    return _parser

def get_generator():
    global _generator
    if _generator is None:
        from sql2mongo.codegen.mongodb_generator import MongoDBGenerator
        _generator = MongoDBGenerator()
    return _generator

def get_mongo_db():
    global _mongo_db
    if _mongo_db is None:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise Exception("MONGO_URI not set")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        _mongo_db = client["transpiler_db"]
    return _mongo_db

# ── DB HELPERS ────────────────────────────────────────────
def get_pg_connection():
    return psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT", "5432")
    )

def run_sql(query):
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        return rows, columns
    finally:
        conn.close()

def run_mongo(collection, query, projection=None):
    db = get_mongo_db()
    return list(db[collection].find(query, projection))

# ── ROUTES ────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/schema")
def get_schema():
    try:
        with open("schema.json") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": f"Schema error: {str(e)}"}), 500

@app.route("/run", methods=["POST"])
def run_query():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        sql = data.get("sql", "").strip()
        schema = data.get("schema")

        if not sql or not schema:
            return jsonify({"error": "Missing sql or schema"}), 400

        print(f"[SQL] {sql}")

        # ── Transpile ──────────────────────────────────────
        from sql2mongo.semantic.semantic_analyzer import SemanticAnalyzer

        parser    = get_parser()
        generator = get_generator()
        analyzer  = SemanticAnalyzer(schema)

        ast        = parser.parse(sql)
        analyzer.validate_query(ast)
        mongo_data = generator.generate(ast)

        print(f"[MONGO] {mongo_data}")

        collection = mongo_data.get("collection")
        if not collection:
            return jsonify({"error": "No collection generated"}), 400

        # ── Run SQL ────────────────────────────────────────
        try:
            sql_rows, sql_columns = run_sql(sql)
        except Exception as e:
            return jsonify({"error": f"Postgres error: {str(e)}"}), 500

        # ── Run Mongo ──────────────────────────────────────
        try:
            db = get_mongo_db()
            if "filter" in mongo_data:
                mongo_result = run_mongo(
                    collection,
                    mongo_data["filter"],
                    mongo_data.get("projection")
                )
            else:
                mongo_result = list(db[collection].aggregate(mongo_data["pipeline"]))
        except Exception as e:
            return jsonify({"error": f"Mongo error: {str(e)}"}), 500

        # Clean _id from Mongo docs
        for doc in mongo_result:
            doc.pop("_id", None)

        return jsonify({
            "mongo":        mongo_data.get("string", str(mongo_data)),
            "columns":      sql_columns,
            "sql_result":   [list(row) for row in sql_rows],
            "mongo_result": mongo_result
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ── STARTUP ───────────────────────────────────────────────
if __name__ == "__main__":
    print("Pre-warming parser...")
    get_parser()
    get_generator()
    print("Parser ready.")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
