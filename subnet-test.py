import oci
import pymysql 
from datetime import datetime, timedelta
# Set up configuration
# config = oci.config.from_file() # Reads the default configuration file

# Initialize the ComputeClient to interact with Compute service
# subnet_client = oci.core.VirtualNetworkClient(config)
# subnet_list=[]
# Function to get all VM names in a compartment
def get_subnet_details():
    subnet_list=[]
    try:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        # subnet_client = oci.core.VirtualNetworkClient({}, signer=signer)
       
        identity_client = oci.identity.IdentityClient({}, signer=signer)
        subscribed_regions = identity_client.list_region_subscriptions(signer.tenancy_id).data
        
        region_list=[reg.region_name for reg in subscribed_regions] 
        compartments = identity_client.list_compartments(signer.tenancy_id)    
        
        # network_client = oci.core.VirtualNetworkClient({}, signer=signer)
        for compartment in compartments.data:
            if compartment.lifecycle_state == "ACTIVE":  
                try:
                    for regions in region_list:
                        signer.region=regions
                        subnet_client = oci.core.VirtualNetworkClient({}, signer=signer)
                        list_subnets_response = subnet_client.list_subnets(compartment_id=compartment.id)

                # Extract and print instance details
                        for subnet in list_subnets_response.data:
                            subnet_response=subnet.__dict__
                            # print(subnet)
                            subnet_response.get('_vcn_id',' ')
                            # print(subnet.vcn_id)
                            subnet_list.append({
                                'display_name' : subnet_response.get('_display_name',' '),
                                'id'  : subnet_response.get('_id',' '),
                                'cidr_block':subnet_response.get('_cidr_block',' '),
                                'domain_name'  : subnet_response.get('_subnet_domain_name',' '),
                                'State'   : subnet_response.get('_lifecycle_state',' '),
                                'account_id':compartment.id,
                                'Datacenter': signer.region,
                                'Network_Object_ID':subnet_response.get('_vcn_id',' '),
                                'Tags': str(subnet_response.get('_defined_tags',' ').get('Oracle-Tags',' '))

                                })
                except Exception as e:
                    print(f"Account name = {compartment.__dict__.get('_name',' ')} is not authorized:", e)
        insert_subnet(subnet_list)
      
    except Exception as e:
        print("Error fetching instance data:", e)
    # print(l)
# Example compartment OCID (change this to your actual compartment OCID)
# compartment_ocid = 'ocid1.compartment.oc1..aaaaaaaajnmd2vir2bjsphzpskjaz3gohvqy7w6xwaz3jqfkqeshuwolauqq'

# Call the function to print all VM names in the compartment

# print(subnet_list)


def insert_subnet(subnet_list):
    db_host="10.0.1.56"
    # db_port=3306
    db_user="admin"
    db_pass="AdminAdmin@123"
    db_name="oci"
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_cloud_subnet'

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
        CREATE TABLE IF NOT EXISTS cmdb_ci_cloud_subnet (
            Name varchar(100),
            Object_id varchar(100),
            cidr varchar(50),
            Domain_name varchar(100),
            state varchar(50),
            Account_ID varchar(100),
            Datacenter varchar(50),
            Network_Object_ID varchar(100),
            Tags varchar(200)

        );"""


        cursor.execute(create_table)
    
        
        for n in subnet_list:
            insert_query = """
                INSERT INTO cmdb_ci_cloud_subnet(Name,Object_id,cidr,Domain_name,state,Account_ID,Datacenter,Network_Object_ID,Tags) 
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(n['display_name'],n['id'],n['cidr_block'],n['domain_name'],n['State'],n['account_id'],n['Datacenter'],n['Network_Object_ID'],n['Tags']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_cloud_subnet is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")   


# insert_subnet(subnet_list)
if __name__=="__main__":
    get_subnet_details()
