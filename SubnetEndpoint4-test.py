import oci
import pymysql 
from datetime import datetime, timedelta
import database_password

# Set up configuration
# config = oci.config.from_file()  # Reads the default configuration file
# print(config)
# config = oci.config.from_file()  # Reads the default configuration file

# Initialize the ComputeClient to interact with Compute service
# subnet_client = oci.core.VirtualNetworkClient({}, signer=signer)
# Initialize the ComputeClient to interact with Compute service
# compute_client = oci.core.ComputeClient({}, signer=signer)
l =[]
subnet_list=[]
# Function to get all VM names in a compartment
def get_all_vm_names():
    try:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        identity_client = oci.identity.IdentityClient({}, signer=signer)
        compartments = identity_client.list_compartments(signer.tenancy_id)
        
        
        subscribed_regions = identity_client.list_region_subscriptions(signer.tenancy_id).data
        
        region_list=[reg.region_name for reg in subscribed_regions]

        for compartment in compartments.data:
            if compartment.lifecycle_state == "ACTIVE":
                # print(compartment.name)
                compartment_id=compartment.id
                try:                    
                    for regions in region_list:
                        signer.region=regions
                        print(compartment.name,signer.region)

                        compute_client = oci.core.ComputeClient({}, signer=signer)


                        subnet_client = oci.core.VirtualNetworkClient({}, signer=signer)
                        # List all instances in the compartment
                        list_subnets_response = subnet_client.list_subnets(compartment_id).data
                        # print(list_subnets_response)
                        for subnets in list_subnets_response:
                            check=0
                            # print(subnets)
                            list_instances_response = compute_client.list_vnic_attachments(compartment_id).data
                            # print(list_instances_response)
                            print(compartment.name,signer.region,subnets.display_name)
                            if not list_instances_response:
                                print("kkkkkkkkk")
                                subnet_list.append({
                                                'Account_ID' : compartment_id,
                                                'Subnet_Object_ID'  : subnets.id,
                                                'VM_Object_ID':' ',
                                                'Data_Center'  : signer.region,
                                                'Vnic_attachment_id':' '
                                                

                                                })
                            else:
                                for attach in list_instances_response:
                                    
                                    if subnets.id==attach.subnet_id:
                                        check=1
                                        print("okokok")
                                        subnet_list.append({
                                                    'Account_ID' : compartment_id,
                                                    'Subnet_Object_ID'  : subnets.id,
                                                    'VM_Object_ID':attach.instance_id,
                                                    'Data_Center'  : signer.region,
                                                    'Vnic_attachment_id': attach.id

                                                    

                                                    }) 
                                if check==0:
                                    print("gggggggg")
                                    subnet_list.append({
                                            'Account_ID' : compartment_id,
                                            'Subnet_Object_ID'  : subnets.id,
                                            'VM_Object_ID':' ',
                                            'Data_Center'  : signer.region,
                                            'Vnic_attachment_id':' '
                                            

                                            })
                                
                except Exception as e:
                    print(f"Account name = {compartment.name} is not authorized:", e)
        # print(subnet_list)
        insert_storage_volume_into_db(subnet_list)   
    except Exception as e:
        print("Error fetching instance data:", e)
    # print(l)

# Example compartment OCID (change this to your actual compartment OCID)
# compartment_ocid = 'ocid1.compartment.oc1..aaaaaaaa7nxivmvn7wff2j4azbwncx4ywnmfuhx4eugo55huwwuozxysdw4a'
# instance_id1="ocid1.instance.oc1.ap-mumbai-1.anrg6ljrbfgevmacj46t7f674z57agreer4o27sp2rposus5564npuxtrkoq"
# Call the function to print all VM names in the compartment


def insert_storage_volume_into_db(storage_list):
    db_host="10.0.1.56"
    # db_port=3306
    db_user="admin"
    db_pass=database_password.get_secret_from_vault()
    db_name="oci"
    try:
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_endpoint_subnet'

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
        CREATE TABLE IF NOT EXISTS cmdb_ci_endpoint_subnet (
            Account_ID varchar(100),
            Subnet_Object_ID varchar(100),
            VM_Object_ID varchar(1000),
            Data_Center varchar(50),
            Vnic_attachment_id varchar(100)
        

        );"""


        cursor.execute(create_table)
    
        
        for iteam in storage_list:
            insert_query = """
                INSERT INTO cmdb_ci_endpoint_subnet(Account_ID,Subnet_Object_ID,VM_Object_ID,Data_Center,Vnic_attachment_id) 
                values(%s,%s,%s,%s,%s);
            """
        
            try:
                cursor.execute(insert_query,(iteam['Account_ID'],iteam['Subnet_Object_ID'],iteam['VM_Object_ID'],iteam['Data_Center'],iteam['Vnic_attachment_id']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_endpoint_subnet is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}") 
get_all_vm_names()

