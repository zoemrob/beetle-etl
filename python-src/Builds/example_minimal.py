
# 1) import the MongoToSQL Python package
from BeetleETL.Handlers import ETLHandler

# 2) setup a MongoToSQL program manager using a specified config
ETL = ETLHandler.ETLHandler("dist\\example.json") 
        
# 3) perform a data pull from MongoDB
ETL.get_from_mongo()
ETL.update_config()

# 4) push data to SQL Server
#ETL.push_to_sql()

# (Optional) send an email notification
#ETL.send_email_update()

print("BeetleETL has completed ETL Solution!")
