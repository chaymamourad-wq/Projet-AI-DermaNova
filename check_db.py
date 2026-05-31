import os, sys
sys.path.append('c:/Users/asus/Desktop/SKIN_CANCER_APP_AI')
import app
conn = app.get_db()
print('Connection OK, DB type:', app.DB_TYPE)
conn.close()
