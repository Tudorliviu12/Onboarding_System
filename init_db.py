import psycopg2
import bcrypt

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="onboarding",
    user="postgres",
    password="parola"
)

conn.autocommit = True
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS users(
          id SERIAL PRIMARY KEY,
          username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL)
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS tickets(
        id SERIAL PRIMARY KEY,
        employee_name TEXT NOT NULL,
        role TEXT NOT NULL,
        start_date DATE NOT NULL,
        hardware TEXT NOT NULL,
        status TEXT NOT NULL,
        created_by INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS history(
          id SERIAL PRIMARY KEY,
          ticket_id INTEGER REFERENCES tickets(id),
          user_id INTEGER REFERENCES users(id),
          stage TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT NOW()
          )
""")

hash_hr = bcrypt.hashpw(b"parola_hr", bcrypt.gensalt()).decode("utf-8")
hash_manager = bcrypt.hashpw(b"parola_manager", bcrypt.gensalt()).decode("utf-8")
hash_finance = bcrypt.hashpw(b"parola_finance", bcrypt.gensalt()).decode("utf-8")
hash_it = bcrypt.hashpw(b"parola_it", bcrypt.gensalt()).decode("utf-8")

c.execute("DELETE FROM users;")
c.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", ("hr_user", hash_hr, "HR"))
c.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", ("manager_user", hash_manager, "Manager"))
c.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", ("finance_user", hash_finance, "Finance"))
c.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", ("it_user", hash_it, "IT"))

conn.commit()
c.close()
conn.close()

print("tables created")