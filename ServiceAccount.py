import oci
import pymysql 
from datetime import datetime, timedelta
import database_password
import details 

def get_service_account_details():
    details.logger.info("start fetching details from cmdb_ci_cloud_service_account")
    account_list = []
    try:
        # Load the configuration and initialize signer
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        
        # Initialize the IdentityClient to fetch service account details
        identity_client = oci.identity.IdentityClient({}, signer=signer)

        # Get details of the tenancy
        tenancy = identity_client.get_tenancy(signer.tenancy_id).data
        # Convert object into dictionary type
        tenancy_response = tenancy.__dict__
        tenancy_id = tenancy.id
        # Check if the tenancy is the master account
        master_account = "Yes" if tenancy_id == signer.tenancy_id else "No"
        
        # Append tenancy details to account_list
        account_list.append({
            'Name': tenancy_response.get('_name',' '),
            'Account_id': tenancy_response.get('_id',' '),
            'Object_id': tenancy_response.get('_id',' '),
            'Organization_id': tenancy_response.get('_id',' '),
            'Is_master_account': master_account ,
            'Tags': str(tenancy_response.get('_defined_tags',' ').get('Oracle-Tags',' '))
        })
        
        # Get the list of compartments
        compartments = identity_client.list_compartments(signer.tenancy_id)
        
        # Iterate through compartments
        for compartment in compartments.data:  
            # Convert object into dictionary type
            compartment_response = compartment.__dict__
            compartment_id=compartment.id

            # Check if the compartment is the master account
            master_account = "Yes" if compartment_id == signer.tenancy_id else "No"

            # Check if compartment is active
            if compartment_response.get('_lifecycle_state', ' ') == "ACTIVE": 
                # Append compartment details to account_list
                account_list.append(
                    {
                        'Name': compartment_response.get('_name', ' '),
                        'Account_id': compartment_response.get('_id', ' '),
                        'Object_id':  compartment_response.get('_name', ' '),
                        'Organization_id': tenancy_response.get('_id',' '),
                        'Is_master_account': master_account ,
                        'Tags': str(compartment_response.get('_defined_tags',' ').get('Oracle-Tags',' '))
                    }
                )
        # Insert service account details into the database
        insert_service_account_details_into_database(account_list)
    except oci.exceptions.ServiceError as e:
        print("Error fetching active compartments", e)

# Function to insert service account details into the database
def insert_service_account_details_into_database(account_list):
    db_host = "10.0.1.56"
    db_user = "admin"
    db_pass = database_password.get_secret_from_vault()
    db_name = "oci"    
    try:
        # Establish database connection
        connection = pymysql.connect(host=db_host, user=db_user, password=db_pass, database=db_name, cursorclass=pymysql.cursors.DictCursor)
        table_name = 'cmdb_ci_cloud_service_account'

        cursor = connection.cursor()

        # Get current time and previous date
        current_time = datetime.now().strftime("%H:%M:%S")
        previous_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        
        # Check if table exists and rename if it does
        show_table = f"SHOW TABLES LIKE '{table_name}'"
        cursor.execute(show_table)
        tb = cursor.fetchone()
        if tb:
            rename_table_query = f"ALTER TABLE `{table_name}` RENAME TO `{table_name}_{previous_date}_{current_time}`"
            cursor.execute(rename_table_query)

        # Create table if not exists
        create_table = """
        CREATE TABLE IF NOT EXISTS cmdb_ci_cloud_service_account (
            Name varchar(100),
            Account_id varchar(100),
            Object_id varchar(100),
            Is_master_account varchar(10),
            Organization_id varchar(100),
            Tags varchar(200)
         );"""

        cursor.execute(create_table)
        
        # Insert data into database
        for item in account_list:
            insert_query = """
                INSERT INTO cmdb_ci_cloud_service_account(Name,Account_id,Object_id,Is_master_account,Organization_id,Tags) 
                values(%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(item['Name'], item['Account_id'], item['Object_id'], item['Is_master_account'], item['Organization_id'], item['Tags']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_cloud_service_account is successful")

        connection.commit()

        connection.close()

    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")  
    
# Call function to fetch service account details
if __name__=="__main__":
    get_service_account_details()
