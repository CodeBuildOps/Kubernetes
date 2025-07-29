from flask import Flask, render_template, jsonify
import psycopg2
from psycopg2 import sql
import os

app = Flask(__name__)

DB_CONFIG = {
    'dbname': os.environ['DATABASE_NAME'],
    'user': os.environ['DATABASE_USER'],
    'password': os.environ['DATABASE_PASSWORD'],
    'host': os.environ['DATABASE_HOST'], # Use the service name defined in docker-compose
    'port': os.environ['DATABASE_PORT']
}

def query_db(query, args=None, fetch=False):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(query).format(sql.Identifier(os.environ['DATABASE_TABLE_NAME'])), args or ())
            if fetch:
                return cur.fetchall()

@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
def index():
    try:
        # Check DB connection and table presence
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (os.environ['DATABASE_TABLE_NAME'],))
                table_exists = cur.fetchone()[0]

                if not table_exists:
                    return "❌ Table does not exist in the database.", 500
        
        # Get pod or container ID (in Kubernetes, HOSTNAME is typically the pod name)
        return render_template('index.html', container_id=os.environ.get('HOSTNAME', 'Unknown'))
    
    except Exception as e:
        return f"❌ Error connecting to database or checking table: {e}", 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    rows = query_db("SELECT id, content FROM {} ORDER BY id DESC", fetch=True)
    return jsonify([{'id': r[0], 'content': r[1]} for r in rows])

@app.route('/delete/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    query_db("DELETE FROM {} WHERE id = %s", (message_id,))
    return '', 204

@app.route('/delete_all', methods=['POST'])
def delete_all():
    query_db("DELETE FROM {}")
    return '', 204

if __name__ == '__main__':
    # ⚠️ No DB check here — app will start regardless of DB state
    app.run(host='0.0.0.0', port=os.environ['READER_PORT'])