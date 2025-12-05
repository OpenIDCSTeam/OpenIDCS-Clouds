import os
import sys

from NICManager.NCManage import NCManage
import yaml
class NCCreate:
    def __init__(self):
        self.nic_list: dict[str, NCConfig] = {}
        self.set_list: dict[str, dict] = {}
        self.nic_data = NCManage()

    @staticmethod
    # 将MAC地址的后32位转换为IP地址 ####################################
    def mac_ip4(mac_addr):
        mac_part = mac_addr.split(":")
        ip4_part = mac_part[-4:]  # 取MAC地址的后4个部分
        ip4_addr = ".".join(str(int(part, 16)) for part in ip4_part)
        return ip4_addr

    @staticmethod
    def ip_cidr(mask: str) -> str:
        """根据子网掩码计算CIDR"""
        mask_map = {
            "255.255.255.0": "24",
            "255.255.0.0": "16",
            "255.0.0.0": "8",
        }
        return mask_map.get(mask, "24")  # 默认/24

    # 设置网卡信息 #####################################################
    def set_nic(self, platform="windows"):
        self.nic_data.get_nic()
        self.nic_list = self.nic_data.nic_list
        for nic in self.nic_list:
            self.set_list[nic] = {
                "ip": self.mac_ip4(self.nic_list[nic].mac_addr),
                "mask": "255.255.255.0",
                "gateway": self.nic_list[nic].ip4_gate,
            }

        config_data = self.set_txt(platform)
        if not config_data:
            return "# 错误：未找到网卡数据，请先调用 set_nic() 方法"

        # 使用 yaml.dump 生成格式化的 YAML
        yaml_content = yaml.dump(
            config_data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2
        )

        return f"#cloud-config\n{yaml_content}"

    # 生成统一的网络配置数据结构 #######################################
    def set_txt(self, platform: str) -> dict:
        if not self.set_list or not self.nic_list:
            return {}
        # 根据平台生成不同的配置数据 ====================================
        if platform.lower() == "windows":  # CloudBase 格式
            config = []
            for nic_name, set_data in self.set_list.items():
                if not set_data.get('gateway'):
                    continue
                cidr = self.ip_cidr(set_data['mask'])
                config.append({
                    "type": "physical",
                    "name": nic_name,
                    "mac_address": self.nic_list[nic_name].mac_addr,
                    "subnets": [{
                        "type": "static",
                        "address": f"{set_data['ip']}/{cidr}",
                        "gateway": set_data['gateway'],
                        "dns_nameservers": ["8.8.8.8", "8.8.4.4"]
                    }]
                })
            return {"network": {"version": 1, "config": config}}
        else:  # Cloud-Init =============================================
            ethernet = {}
            for nic_name, set_data in self.set_list.items():
                if not set_data.get('gateway'):
                    continue

                cidr = self.ip_cidr(set_data['mask'])
                ethernet[nic_name] = {
                    "match": {
                        "macaddress": self.nic_list[nic_name].mac_addr
                    },
                    "addresses": [f"{set_data['ip']}/{cidr}"],
                    "routes": [{
                        "to": "default",
                        "via": set_data['gateway']}
                    ],
                    "nameservers": {
                        "addresses": ["8.8.8.8", "8.8.4.4"]
                    }
                }
            return {"network": {"version": 2, "ethernets": ethernet}}

    # 设置所有网卡信息 #################################################
    def set_all(self):
        platform = "windows" if os.name == "nt" else "linux"
        ipconfig = self.set_nic(platform)
        if platform == "windows":
            exe_path = "C:\\Program Files\\Cloudbase Solutions\\Cloudbase-Init\\conf\\"
            win_path = exe_path + "cloudbase-init.conf"
            if not os.path.exists(exe_path):
                os.makedirs(exe_path)
            with open(win_path, "w") as save_file:
                save_file.write(
                    "[DEFAULT]\n"
                    "network_config_path = C:\\Program Files\\Cloudbase Solutions\\Cloudbase-Init\\conf\\network.cfg")
            nic_path = exe_path + "network.cfg"
        else:

            elf_path = "/etc/cloud/cloud.cfg.d/"
            if not os.path.exists(elf_path):
                os.makedirs(elf_path)
            nic_path = elf_path + "99-network.cfg"
        with open(nic_path, "w") as save_file:
            save_file.write(ipconfig)
        print(ipconfig)


if __name__ == "__main__":
    nc_create = NCCreate()
    nc_create.set_all()
