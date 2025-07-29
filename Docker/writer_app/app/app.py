from flask import Flask, request, redirect, render_template
import psycopg2
from psycopg2 import sql
import os

app = Flask(__name__)

DB_CONFIG = {
    'dbname': os.environ['DATABASE_NAME'],
    'user': os.environ['DATABASE_USER'],
    'password': os.environ['DATABASE_PASSWORD'],
    'host': os.environ['DATABASE_HOST'],
    'port': os.environ['DATABASE_PORT']
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def check_db_status():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (os.environ['DATABASE_TABLE_NAME'],))
                return cur.fetchone()[0]
    except Exception as e:
        raise RuntimeError(f"❌ DB error: {e}")

@app.route('/health')
def health():
    return "OK", 200

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if not check_db_status():
            return f"❌ Table '{os.environ['DATABASE_TABLE_NAME']}' does not exist in database.", 500

        if request.method == 'POST':
            msg = request.form['message']
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("INSERT INTO {} (content) VALUES (%s)").format(
                        sql.Identifier(os.environ['DATABASE_TABLE_NAME'])
                    ), [msg])
                    conn.commit()
            return redirect('/')

        # Get pod or container ID (in Kubernetes, HOSTNAME is typically the pod name)
        return render_template('index.html', container_id=os.environ.get('HOSTNAME', 'Unknown'))
    except Exception as e:
        return f"❌ Route: index(): {e}", 500

if __name__ == '__main__':
    # ⚠️ No DB check here — app will start regardless of DB state
    app.run(host='0.0.0.0', port=os.environ['WRITER_PORT'])