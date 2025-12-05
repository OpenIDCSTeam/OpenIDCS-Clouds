import netifaces as ni
from NICManager.NCConfig import NCConfig


class NCManage:
    def __init__(self):
        self.nic_list: dict[str, NCConfig] = {}
        self.get_nic()


    # 获取所有网络接口 ##################################################
    def get_nic(self):
        self.nic_list = {}

        # 获取默认网关信息
        gateways_info = ni.gateways()
        default_ipv4_gateway = gateways_info.get('default', {}).get(ni.AF_INET, (None, None))[0]
        default_ipv6_gateway = gateways_info.get('default', {}).get(ni.AF_INET6, (None, None))[0]

        # 获取每个接口的网关信息
        ipv4_gateways = gateways_info.get(ni.AF_INET, [])
        ipv6_gateways = gateways_info.get(ni.AF_INET6, [])

        # 创建网关映射字典 {接口名: 网关IP}
        ipv4_gateway_map = {gateway[1]: gateway[0] for gateway in ipv4_gateways}
        ipv6_gateway_map = {gateway[1]: gateway[0] for gateway in ipv6_gateways}

        # 使用集合来避免重复处理
        processed_interfaces = set()

        for nic_data in ni.interfaces():
            nic_key = nic_data.lower()

            # 避免重复处理同一个接口
            if nic_key in processed_interfaces:
                continue

            try:
                # 获取MAC地址
                mac = ni.ifaddresses(nic_data)[ni.AF_LINK][0]['addr']
                if mac == '00:00:00:00:00:00':  # 排除无效MAC地址
                    processed_interfaces.add(nic_key)
                    continue

                if mac == '':
                    mac = '00:00:00:00:00:00'
                # 获取IPv4地址信息
                ip4_info = ni.ifaddresses(nic_data).get(ni.AF_INET, [{}])
                ip4_addr = ip4_info[0].get('addr', '') if ip4_info and ip4_info[0] else ''

                # 获取IPv6地址信息
                ip6_info = ni.ifaddresses(nic_data).get(ni.AF_INET6, [{}])
                ip6_addr = ip6_info[0].get('addr', '') if ip6_info and ip6_info[0] else ''

                # 获取IPv4网关
                ip4_gate = ipv4_gateway_map.get(nic_data, '')
                if not ip4_gate and default_ipv4_gateway:
                    # 如果接口没有特定网关，使用默认网关
                    ip4_gate = default_ipv4_gateway

                # 获取IPv6网关
                ip6_gate = ipv6_gateway_map.get(nic_data, '')
                if not ip6_gate and default_ipv6_gateway:
                    # 如果接口没有特定网关，使用默认网关
                    ip6_gate = default_ipv6_gateway

                # 创建NCConfig对象
                nic_config = NCConfig(
                    mac_addr=mac,
                    nic_type=nic_data,
                    ip4_addr=ip4_addr,
                    ip6_addr=ip6_addr,
                    ip4_gate=ip4_gate,
                    ip6_gate=ip6_gate
                )

                # 将网卡配置添加到字典中
                self.nic_list[nic_key] = nic_config
                processed_interfaces.add(nic_key)
                print(
                    f"Interface {nic_data}: MAC={mac}, IPv4={ip4_addr}, IPv6={ip6_addr}, IPv4_GW={ip4_gate}, IPv6_GW={ip6_gate}")

            except (KeyError, IndexError) as e:
                print(f"Error getting info for interface {nic_data}: {e}")
                processed_interfaces.add(nic_key)
                continue

    def get_nic_info(self):
        """
        返回格式化的网卡信息
        """
        return {name: config.__dict__() for name, config in self.nic_list.items()}


if __name__ == "__main__":
    service = NCManage()
    service.get_nic()

    print("\n=== NCConfig格式的网卡信息 ===")
    nic_info = service.get_nic_info()
    for nic_name, config in nic_info.items():
        print(f"网卡名称: {nic_name}")
        print(f"  MAC-地址: {config['mac_addr']}")
        print(f"  网卡类型: {config['nic_type']}")
        print(f"  IPv4地址: {config['ip4_addr']}")
        print(f"  IPv4网关: {config['ip4_gate']}")
        print(f"  IPv6地址: {config['ip6_addr']}")
        print(f"  IPv6网关: {config['ip6_gate']}")
        print("-" * 40)
