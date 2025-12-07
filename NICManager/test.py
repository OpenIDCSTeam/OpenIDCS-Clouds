# -*- coding: utf-8 -*-
"""
优雅地获取
  1) 所有网卡中英文友好名称
  2) 当前“真正上网”的那张网卡
  3) 其 MAC 地址
  4) 默认网关 IP
仅依赖 psutil（pip install psutil）
"""
import socket
import platform
import psutil
from typing import Dict, Optional, Tuple


def _friendly_name(if_name: str) -> str:
    """尽量返回人类可读名称"""
    if platform.system() == "Windows":
        # 利用注册表把“{xxxxx}”转成“以太网”、“Ethernet 3”等
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Control\Network"
                                r"\{4D36E972-E325-11CE-BFC1-08002BE10318}"
                                rf"\{if_name}\Connection") as key:
                return winreg.QueryValueEx(key, "Name")[0]
        except Exception:
            pass
    # Linux/macOS 直接返回内核名字即可
    return if_name


def get_default_gateway() -> Optional[str]:
    """跨平台取默认网关 IPv4"""
    gw = None
    try:
        if platform.system() == "Windows":
            for route in psutil.net_if_stats().values():
                proc = psutil.Popen(["route", "print", "0.0.0.0"], stdout=psutil.PIPE)
                stdout, _ = proc.communicate()
                for line in stdout.decode("gbk", errors="ignore").splitlines():
                    if "0.0.0.0" in line and "Gateway" not in line:
                        gw = line.split()[2]
                        break
                break
        else:
            with open("/proc/net/route") as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[1] == "00000000" and fields[2] != "00000000":
                        gw = socket.inet_ntoa(int(fields[2], 16).to_bytes(4, "little"))
                        break
    except Exception:
        pass
    return gw


def get_active_nic() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    返回 (网卡友好名称, MAC地址, 网关IP)
    找不到就返回 None
    """
    gateway = get_default_gateway()
    if not gateway:
        return None, None, None

    # 先拿一张“有默认网关的 NIC”
    gateways = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    for nic, snics in addrs.items():
        for snic in snics:
            if snic.family == socket.AF_INET and snic.address:
                # 简单判定：能 ping 通网关即认为“活跃”
                try:
                    # Windows 用 ping -n 1，Linux/mac 用 -c 1
                    param = "-n" if platform.system() == "Windows" else "-c"
                    psutil.Popen(["ping", param, "1", gateway],
                                 stdout=psutil.PIPE).wait(2)
                    mac = None
                    for s in addrs[nic]:
                        if s.family == psutil.AF_LINK:
                            mac = s.address
                            break
                    return _friendly_name(nic), mac, gateway
                except Exception:
                    continue
    return None, None, gateway


# ----------------- DEMO -----------------
if __name__ == "__main__":
    name, mac, gw = get_active_nic()
    print("当前上网网卡 :", name)
    print("MAC 地址     :", mac)
    print("默认网关     :", gw)