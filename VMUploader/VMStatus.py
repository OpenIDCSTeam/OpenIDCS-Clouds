import json
import time
import psutil
import GPUtil
import cpuinfo
import requests
from HWStatus import HWStatus
from NICManager.NCManage import NCManage
from VMPowers import VMPowers


class VMStatus:
    def __init__(self):
        self.vm_status = HWStatus()

    # 转换为字典 ============================================================
    def __dict__(self):
        return self.vm_status.__dict__()

    # 转换为文本 ============================================================
    def __str__(self):
        return json.dumps(self.__dict__())

    # 获取状态 ==============================================================
    def status(self):
        self.vm_status.ac_status = VMPowers.STARTED
        # 获取CPU信息 =======================================================
        # self.vm_status.cpu_model = cpuinfo.get_cpu_info()['brand_raw']
        self.vm_status.cpu_total = psutil.cpu_count(logical=True)
        self.vm_status.cpu_usage = int(psutil.cpu_percent(interval=1))
        # 获取内存信息 ======================================================
        mem = psutil.virtual_memory()
        self.vm_status.mem_total = int(mem.total / (1024 * 1024))  # 转换为MB
        self.vm_status.mem_usage = int(mem.percent)
        # 获取系统磁盘信息 ==================================================
        disk_usage = psutil.disk_usage('/')
        self.vm_status.hdd_total = int(disk_usage.total / (1024 * 1024))
        self.vm_status.hdd_usage = int(disk_usage.used / (1024 * 1024))
        # 获取其他磁盘信息 ==================================================
        for disk in psutil.disk_partitions():
            if disk.mountpoint != '/':
                usage = psutil.disk_usage(disk.mountpoint)
                self.vm_status.ext_usage[disk.mountpoint] = [
                    int(usage.total / (1024 * 1024)),  # 总空间MB
                    int(usage.used / (1024 * 1024))  # 已用空间MB
                ]
        # 获取GPU信息 =======================================================
        gpus = GPUtil.getGPUs()
        self.vm_status.gpu_total = len(gpus)
        for gpu in gpus:
            self.vm_status.gpu_usage[gpu.id] = int(gpu.load * 100)  # 使用率
        # 获取网络带宽 ======================================================
        net_io = psutil.net_io_counters()
        self.vm_status.network_u = int(net_io.bytes_sent / (1024 * 1024))
        self.vm_status.network_d = int(net_io.bytes_recv / (1024 * 1024))

    # 上报状态 ==============================================================
    def server(self):
        time_last = 0
        nets_apis = NCManage()
        nets_apis.get_nic()
        nets_list = nets_apis.nic_list
        while True:  # 每60秒上报一次 =======================================
            time.sleep(1)
            time_data = time.time()
            if time_data - time_last > 60:
                self.status()
                vm_status = self.vm_status.__dict__()
                for nic_name in nets_list:
                    nic_gate = nets_list[nic_name].ip4_gate
                    if nic_gate == "" or nic_gate is None:
                        continue
                    try:
                        vm_result = requests.post(
                        url=f"http://{nic_gate}:1880/api/vm/status",
                        json=vm_status, timeout=5)
                        print("[上报虚拟机状态结果]", vm_result.text)
                    except requests.exceptions.ConnectionError as e:
                        print("[上报虚拟机状态异常]", e)
                time_last = time_data


if __name__ == "__main__":
    hs = VMStatus()
    hs.server()
