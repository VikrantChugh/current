import oci
import pymysql 
from datetime import datetime, timedelta
import details
import database_password
    
def get_availability_zone_details():
    details.logger.info("start fetching details from cmdb_ci_availability_zone")
    zone_list=[]
    try:
        # Load the configuration
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        # Initialize the IdentityClient to fetch service account details
        identity_client = oci.identity.IdentityClient({}, signer=signer)
        subscribed_regions = identity_client.list_region_subscriptions(signer.tenancy_id).data
        compartments = identity_client.list_compartments(signer.tenancy_id)
        region_list=[reg.region_name for reg in subscribed_regions]
        
        for compartment in compartments.data:
            if compartment.lifecycle_state == "ACTIVE":
                for regions in region_list:
                    signer.region=regions
                    identity_client = oci.identity.IdentityClient({}, signer=signer)      
                    # Initialize the availability_domains to fetch zone details
                    compartment_id=signer.tenancy_id
                    # compartments = identity_client.list_compartments(signer.tenancy_id)
                    
                    availability_domains = identity_client.list_availability_domains(compartment_id).data

                    # List availability domains in the region    
                    for availability_domain in availability_domains:
                        # print(availability_domain)
                        # print("gggg")

                        availability_domain_id=availability_domain.id
                        availability_domain_name=availability_domain.name
                        # fault_domains = identity_client.list_fault_domains(signer.tenancy_id, availability_domain.name).data
                        # fd_list=[fd.name for fd in fault_domains]
                        # fd_str=str(fd_list)
                        # fd_list_id=[fd.id for fd in fault_domains]
                        # fd_str_id=str(fd_list_id)
                        # print(fd_str)
                        
                        # for fd in fault_domains:
                        #     print(" Fault Domain:", fd.name)
                            
                    # Extract the desired fields from the response data
                        zone_list.append({
                                'Object_id':availability_domain_id or ' ',
                                'Name':availability_domain_name or ' ',
                                'Account_id':compartment_id or ' ',
                                'Datacenter':signer.region or ' ',
                                'State': "Available" or ' '
                                
                            })
                # print(zone_list[0]['fault_domain'])
        # print(zone_list)
        insert_availability_zone_details_into_database(zone_list)
        # print(type(zone_list[0]['fault_domain']))
        
          
    except oci.exceptions.ServiceError as e:
        print("Error fetching availability domains:", e)


def insert_availability_zone_details_into_database(zone_list):
    db_host="10.0.1.56"
    # db_port=3306
    db_user="admin"
    db_pass=database_password.get_secret_from_vault()
    db_name="oci"
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_availability_zone'
        cursor = connection.cursor()
        current_date = datetime.now()
        current_time = datetime.now().strftime("%H:%M:%S")
        previous_date = (current_date - timedelta(days=1)).strftime("%d-%m-%Y")

        show_table = f"SHOW TABLES LIKE '{table_name}'"
        cursor.execute(show_table)
        tb = cursor.fetchone()
        if tb:
            rename_table_query = f"ALTER TABLE `{table_name}` RENAME TO `{table_name}_{previous_date}_{current_time}`"
            cursor.execute(rename_table_query)
 
        create_table = """
        CREATE TABLE IF NOT EXISTS cmdb_ci_availability_zone (
            Name varchar(50),
            Object_id varchar(100),
            Account_id varchar(100),
            Datacenter varchar(50),
            State varchar(50)
           
           
        );"""
        cursor.execute(create_table)
         
        for zones in zone_list:
            insert_query = """
                INSERT INTO cmdb_ci_availability_zone(Name,Object_id,Account_id,Datacenter,State) 
                values(%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(zones['Name'],zones['Object_id'],zones['Account_id'],zones['Datacenter'],zones['State']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_availability_zone is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")

if __name__=="__main__":
    get_availability_zone_details()
