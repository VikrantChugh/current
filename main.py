import threading
from ServiceAccount import get_service_account_details
from AvailabilityZones import get_availability_zone_details
from StorageVolume import get_storage_volume_details
from VirtualMachine import get_virtual_machine_details
from Network import get_network_details
from Subnet import get_subnet_details
import details 
# import details
# from details import *

def main():
    try:     
        details.account_region_details()          
        service_account_thread =threading.Thread(target=get_service_account_details)
        availability_zone_thread =threading.Thread(target=get_availability_zone_details)
        storage_volume_thread =threading.Thread(target=get_storage_volume_details)
        virtual_machine_thread =threading.Thread(target=get_virtual_machine_details)
        network_thread =threading.Thread(target=get_network_details)
        subnet_thread =threading.Thread(target=get_subnet_details)
        # # Zone =threading.Thread(target=get_availability_zone_details)
        # # Zone =threading.Thread(target=get_availability_zone_details)
        details.logger.info("output from main")
        service_account_thread.start()    
        availability_zone_thread.start()
        storage_volume_thread.start()
        
        service_account_thread.join()
        availability_zone_thread.join()
        storage_volume_thread.join()
        
        virtual_machine_thread.start()
        network_thread.start()
        subnet_thread.start()
        
        virtual_machine_thread.join()
        network_thread.join()
        subnet_thread.join()
    except Exception as e:
        print("Error fetching in main file:", e)

main()
