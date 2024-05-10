import oci
import pymysql 
from datetime import datetime, timedelta
import database_password
import details
# Define a function to retrieve details of all VMs
def get_virtual_machine_details():
    details.logger.info("start fetching details from cmdb_ci_vm_instance")
    try:
        # Initialize lists to store subnet and VM details    
        vm_list=[] 

        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

        identity_client = oci.identity.IdentityClient({}, signer=signer)

        compartments = identity_client.list_compartments(signer.tenancy_id)
        # Use Instance Principals Security Token Signer for authentication
        subscribed_regions = identity_client.list_region_subscriptions(signer.tenancy_id).data        
        region_list=[reg.region_name for reg in subscribed_regions]
        
        
        # Loop through each compartment to get VM details
        for compartment in compartments.data:
            if compartment.lifecycle_state == "ACTIVE":  
                try:
                    for regions in region_list:
                        signer.region=regions
                        compute_client = oci.core.ComputeClient({}, signer=signer)
                        # Get list of instances (VMs) in the compartment
                        identity_client = oci.identity.IdentityClient({}, signer=signer)      
                        # Initialize the availability_domains to fetch zone details
                        compartment_id=signer.tenancy_id
                        # compartments = identity_client.list_compartments(signer.tenancy_id)
                        
                        availability_domains = identity_client.list_availability_domains(compartment_id).data
                        list_instances_response = compute_client.list_instances(compartment.id)

                        # Loop through each instance (VM) in the compartment
                        # print(list_instances_response.data)

                        for instance in list_instances_response.data:
                        
                            print(compartment.name,instance.display_name,signer.region)
                            instance_response = instance.__dict__
                            # Instance_id=instance.id
                            list_subnet = compute_client.list_vnic_attachments(compartment.id,instance_id=instance.id) 
                            print(list_subnet.data) 
                            for m in list_subnet.data:
                                print(m.id)
                            
                            # for subnets in list_subnet.data:
                            #     print(subnets)  

                            # print(list_subnet.data)
                            # Append VM details to vm_list
                                for availability_domain in availability_domains:
                                    if instance.availability_domain==availability_domain.name:
                                        Availability_Zone_objectid= availability_domain.id
                                        break
                                fault_domains = identity_client.list_fault_domains(compartment_id, instance.availability_domain).data
                                for fd in fault_domains:
                                    if instance.fault_domain==fd.name:
                                        Fault_domain=fd.id
                                        break
                                vm_list.append({
                                    'Object_id' :         instance_response.get('_id',' '),
                                    'Name'  :             instance_response.get('_display_name',' '),
                                    'Avalibility_zone':   instance_response.get('_availability_domain',' '),
                                    'State'   :           instance_response.get('_lifecycle_state',' '),
                                    'Memory' :            instance_response.get('_shape_config',' ').__dict__.get('_memory_in_gbs',' '),
                                    "Cpu":                instance_response.get('_shape_config',' ').__dict__.get('_ocpus',' '),
                                    "Account_id" :        compartment.id or ' ',
                                    'Datacenter':         signer.region or ' ',
                                    'Subnet':             m.subnet_id,
                                    'Tags':               str(instance_response.get('_defined_tags',' ').get('Oracle-Tags',' ')),
                                    'Vnic_attachment_id': m.id,
                                    "Availability_Zone_objectid": Availability_Zone_objectid,
                                    "Fault_domain":Fault_domain,
                                    "Fault_domain_name":instance.fault_domain


                                })
                    print(vm_list)    

                except Exception as e:
                    print(f"Account name = {compartment.name} is not authorized:", e)

                # Call function to insert VM details into database
        insert_vm_details_into_database(vm_list)

    except Exception as e:
        print("Error fetching instance data:", e)
        
# Define a function to insert VM details into the database
def insert_vm_details_into_database(final_list):
    db_host="10.0.1.56"
    db_user="admin"
    db_pass=database_password.get_secret_from_vault()
    db_name="oci"
    
    try:
        # Connect to the MySQL database
        connection=pymysql.connect(host=db_host,user=db_user,password=db_pass,database=db_name,cursorclass=pymysql.cursors.DictCursor)
       
        table_name = 'cmdb_ci_vm_instance'

        cursor = connection.cursor()

        # Get current date and time for renaming the table
        current_date = datetime.now()
        current_time = datetime.now().strftime("%H:%M:%S")
        previous_date = (current_date - timedelta(days=1)).strftime("%d-%m-%Y")

        # Check if table exists, if yes rename it
        show_table = f"SHOW TABLES LIKE '{table_name}'"
        cursor.execute(show_table)
        tb = cursor.fetchone()
        if tb:
            rename_table_query = f"ALTER TABLE `{table_name}` RENAME TO `{table_name}_{previous_date}_{current_time}`"
            cursor.execute(rename_table_query)

        # Create table if not exists
        create_table = """
        CREATE TABLE IF NOT EXISTS cmdb_ci_vm_instance (
            Name varchar(100),
            Object_id varchar(100),
            State varchar(100),
            Memory varchar(100),
            Cpu varchar(100),
            Account_id varchar(100),
            Datacenter varchar(100),
            Avalibility_zone varchar(100),
            Subnet varchar(100),
            Tags varchar(200),
            Vnic_attachment_id varchar(100),
            Availability_Zone_objectid varchar(100),
            Fault_domain varchar(100),
            Fault_domain_name varchar(100)
        );"""

        cursor.execute(create_table)
    
        # Insert VM details into the database
        for item in final_list:
            insert_query = """
                INSERT INTO cmdb_ci_vm_instance(Name,Object_id,State,Memory,Cpu,Account_id,Datacenter,Avalibility_zone,Subnet,Tags,Vnic_attachment_id,Availability_Zone_objectid,Fault_domain,Fault_domain_name) 
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """
            try:
                cursor.execute(insert_query,(item['Name'],item['Object_id'],item['State'],item['Memory'],item['Cpu'],item['Account_id'],item['Datacenter'],item['Avalibility_zone'],item['Subnet'],item['Tags'],item['Vnic_attachment_id'],item['Availability_Zone_objectid'],item['Fault_domain'],item['Fault_domain_name']))
                
            except pymysql.Error as e:
                print(f"Error: {e}")
        print(f"Data INSERT INTO cmdb_ci_vm_instance is successful")
        connection.commit()
        connection.close()
    except Exception as e:
        raise Exception(f"Error inserting data into RDS: {str(e)}")   

# Call the function to get VM details and insert into database
if __name__=="__main__":
    get_virtual_machine_details()
