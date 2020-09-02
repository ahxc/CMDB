import subprocess


def collect():
    """
    需要根据电脑实际情况，调整采集代码。
    """
    filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
    raw_data = {}

    for key in filter_keys:
        try:
            res = subprocess.Popen("sudo dmidecode -t system|grep '%s'" % key,
                                   stdout=subprocess.PIPE,
                                   shell=True)
            result = res.stdout.read().decode()
            data_list = result.split(':')

            if len(data_list) > 1:
                raw_data[key] = data_list[1].strip()
            else:
                data_list = result.split('：')
                raw_data[key] = data_list[1].strip()                
        except Exception as e:
            print(e)
            raw_data[key] = e

    data = {
        'asset_type': 'server',
        'manufacturer': raw_data['Manufacturer'],
        'sn': raw_data['Serial Number'],
        'model': raw_data['Product Name'],
        'uuid': raw_data['UUID'],
        'wake_up_type': raw_data['Wake-up Type']
    }

    data.update(get_os_info())
    data.update(get_cpu_info())
    data.update(get_ram_info())
    data.update(get_nic_info())
    data.update(get_disk_info())

    return data


def get_os_info():
    """
    获取操作系统信息
    """
    distributor = subprocess.Popen("lsb_release -a|grep 'Distributor ID'",
                                   stdout=subprocess.PIPE, shell=True)
    distributor = distributor.stdout.read().decode().split(":")
    release = subprocess.Popen("lsb_release -a|grep 'Description'",
                               stdout=subprocess.PIPE, shell=True)
    release = release.stdout.read().decode().split(":")
    data_dic = {
        "os_distribution": distributor[1].strip() if len(distributor) > 1 else "",
        "os_release": release[1].strip() if len(release) > 1 else "",
        "os_type": "Linux",
    }

    return data_dic


def get_cpu_info():
    """
    获取cpu信息
    """
    raw_cmd = 'cat /proc/cpuinfo'
    raw_data = {
        'cpu_model': "%s |grep 'model name' |head -1 " % raw_cmd,
        'cpu_count':  "%s |grep  'processor'|wc -l " % raw_cmd,
        'cpu_core_count': "%s |grep 'cpu cores' |awk -F: '{SUM +=$2} END {print SUM}'" % raw_cmd,
    }
    for key, cmd in raw_data.items():
        try:
            result = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            raw_data[key] = result.stdout.read().decode().strip()
        except ValueError as e:
            print(e)
            raw_data[key] = ""

    cpu_model = raw_data["cpu_model"].split(":")

    if len(cpu_model) > 1:
        raw_data["cpu_model"] = cpu_model[1].strip()
    else:
        raw_data["cpu_model"] = ''

    return raw_data


def get_ram_info():
    """
    获取内存信息
    """
    raw_data = subprocess.Popen("sudo dmidecode -t memory", stdout=subprocess.PIPE, shell=True)
    raw_data = raw_data.stdout.read().decode().split("\n")
    ram_dict = dict()
    ram_list = list()
    for item in raw_data:
        if item.strip('\t').startswith('Type'):
            ram_dict['model'] = item.split(':')[1].strip()
        if item.strip('\t').startswith('Size'):
            ram_dict['size'] = item.split(':')[1].strip()
        if item.strip('\t').startswith('Serial Number'):
            ram_dict['sn'] = item.split(':')[1].strip()
        if item.strip('\t').startswith('Manufacturer'):
            ram_dict['manufacturer'] = item.split(':')[1].strip()
        if item.strip('\t').startswith('Locator'):
            ram_dict['locator'] = item.split(':')[1].strip()
        if item.strip('\t').startswith('Asset Tag'):
            ram_dict['asset_tag'] = item.split(':')[1].strip()
        
        if len(ram_dict) == 6:
            ram_list.append(ram_dict)
            ram_dict = dict()
    
    ram_data = {
        'ram': ram_list,
    }

    return ram_data


def get_nic_info():
    """
    获取网卡信息
    """
    nmcli_raw = "nmcli device show|grep %s"
    ifconfig_raw = "ifconfig -a |grep broadcast"
    raw_data = {
        'name': nmcli_raw%'GENERAL.DEVICE',
        'mac': nmcli_raw%'GENERAL.HWADDR',
        'gateway': nmcli_raw%'IP4.GATEWAY',
    }
    for key, cmd in raw_data.items():
        raw_data[key] = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        raw_data[key] = raw_data[key].stdout.read().decode()
        raw_data[key] = raw_data[key].split('\n')[0].split()[1].strip()

    raw_data_ifconfig = subprocess.Popen(ifconfig_raw, stdout=subprocess.PIPE, shell=True)
    raw_data_ifconfig = raw_data_ifconfig.stdout.read().decode().split()
    raw_data_ifconfig = {
        'ip_address': raw_data_ifconfig[1],
        'netmask': raw_data_ifconfig[3],
        'broadcast': raw_data_ifconfig[5],
    }

    raw_data.update(raw_data_ifconfig)
    nic_dic = {'nic': list()}
    nic_dic['nic'].append(raw_data)

    return nic_dic


def get_disk_info():
    """
    获取硬盘型号大小等信息。
    一块硬盘，硬盘尺寸信息为中文。
    如果需要查看Raid信息，可以尝试MegaCli工具
    """
    raw_data = subprocess.Popen("sudo hdparm -i /dev/sda | grep Model", stdout=subprocess.PIPE, shell=True)
    raw_data = raw_data.stdout.read().decode()
    data_list = raw_data.split(",")
    model = data_list[0].split("=")[1]
    sn = data_list[2].split("=")[1].strip()
    size_data = subprocess.Popen("sudo fdisk -l /dev/sda | grep Disk|head -1", stdout=subprocess.PIPE, shell=True)
    size_data = size_data.stdout.read().decode()
    size = size_data.split("：")[1].strip().split("，")[0]
    
    disk_dict = {
        'model': model,
        'capacity': size,
        'sn': sn,
        'manufacturer': None,
        'slot': None,
        'interface_type': 'SATA',

    }

    disk_list=list()
    result = {
        'physical_disk_driver': disk_list.append(disk_dict),
    }

    return result


if __name__ == "__main__":
    # 收集信息功能测试
    data = collect()
    print(data)