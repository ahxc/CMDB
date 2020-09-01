import platform
import win32com
import wmi

"""
本模块基于windows操作系统，依赖wmi和win32com库
"""


class Win32Info(object):

    def __init__(self):
        # 固定用法
        self.wmi_obj = wmi.WMI()
        self.wmi_service_obj = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        self.wmi_service_connector = self.wmi_service_obj.ConnectServer(".", "root\cimv2")

    def collect(self):
        data = {
            'os_type': platform.system(),
            'os_release': "%s %s %s " % (platform.release(), platform.architecture()[0], platform.version()),
            'os_distribution': 'Microsoft',
            'asset_type': 'server'
        }

        data.update(self.get_cpu_info())
        data.update(self.get_ram_info())
        data.update(self.get_motherboard_info())
        data.update(self.get_disk_info())
        data.update(self.get_nic_info())

        return data

    def get_cpu_info(self):
        """
        获取CPU的相关数据
        """
        data = {}
        cpu_lists = self.wmi_obj.Win32_Processor()# 若干个被list包裹的wmi对象，一个对象对应一个u
        cpu_core_count = 0
        for cpu in cpu_lists:
            # 统计所有cpu核数，测试机单u四核
            cpu_core_count += cpu.NumberOfCores

        data = {
            'cpu_model': cpu_lists[0].Name, # cpu型号一致
            'cpu_count': len(cpu_lists),
            'cpu_core_count': cpu_core_count,
            'cpu_core': cpu_core_count/len(cpu_lists),
        }

        return data

    def get_ram_info(self):
        """
        收集内存信息
        """
        data = []
        # 这个模块用SQL语言获取数据
        # 若干个被list包裹的com32对象，一个对象对应一个内存条，win32对象无法打印观测其属性
        ram_collections = self.wmi_service_connector.ExecQuery("Select * from Win32_PhysicalMemory")
        for ram in ram_collections:    # 主机中存在很多根内存，要循环所有的内存数据
            ram_size = int(int(ram.Capacity) / (1024**3))  # 转换内存单位为GB
            item_data = {
                "slot": ram.DeviceLocator.strip(),
                "capacity": ram_size,
                "model": ram.Caption,
                "manufacturer": ram.Manufacturer,
                "sn": ram. SerialNumber,
            }
            data.append(item_data)  # 将每条内存的信息，添加到一个列表里

        return {"ram": data}

    def get_motherboard_info(self):
        """
        获取主板信息
        """
        computer_info = self.wmi_obj.Win32_ComputerSystem()[0]
        system_info = self.wmi_obj.Win32_OperatingSystem()[0]
        data = {
            'manufacturer': computer_info.Manufacturer,
            'model': computer_info.Model,
            'wake_up_type': computer_info.WakeUpType,
            'sn': system_info.SerialNumber,
        }
        
        return data

    def get_disk_info(self):
        """
        硬盘信息
        """
        data = []
        interface_choices = ["SAS", "SCSI", "SATA", "SSD"]
        for disk in self.wmi_obj.Win32_DiskDrive():     # 每块硬盘都要获取相应信息
            disk_data = {
                'slot': disk.Index,
                'sn': disk.SerialNumber,
                'model': disk.Model,
                'manufacturer': disk.Caption.split()[0],
                'capacity': int(int(disk.Size)/(1024**3)),
            }
            for interface in interface_choices:
                if interface in disk.Model:
                    disk_data['interface_type'] = interface
                    break
            else:
                disk_data['interface_type'] = 'unknown'

            data.append(disk_data)

        return {'physical_disk_driver': data}

    def get_nic_info(self):
        """
        网卡信息
        """
        data = []
        for nic in self.wmi_obj.Win32_NetworkAdapterConfiguration():
            if nic.MACAddress:
                nic_data = {
                    'mac': nic.MACAddress,
                    'model': nic.Description,
                    'name': nic.Index,
                }
                if nic.IPAddress:
                    nic_data['ip_address'] = nic.IPAddress[0]
                    nic_data['net_mask'] = nic.IPSubnet[0]
                else:
                    nic_data['ip_address'] = ''
                    nic_data['net_mask'] = ''
                data.append(nic_data)

        return {'nic': data}


if __name__ == "__main__":
    # 测试代码
    data = Win32Info().collect()
    print(data)