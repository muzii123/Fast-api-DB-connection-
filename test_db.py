import psycopg2

# ⚠️ UPDATE THESE 3 VALUES TO MATCH YOUR POSTGRESQL SETUP
DB_NAME = "cartdb"
DB_USER = "postgres"       # Change to "mil123" if you created that user
DB_PASS = "YOUR_PASSWORD"  # Change this to your actual PostgreSQL password

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password="password123",
        host="localhost",
        port="5432"
    )
    print("✅ SUCCESS! Connected to PostgreSQL.")
    conn.close()
except Exception as e:
    print(f"❌ FAILED! Error: {e}")