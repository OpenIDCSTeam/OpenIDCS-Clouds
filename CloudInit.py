import time
import platform
import requests
import subprocess

from loguru import logger
from NICManager.NCManage import NCManage
from VMUploader.VMStatus import VMStatus


class Cloudinit:
    def __init__(self):
        self.vm_status = VMStatus()
        self.vm_config = {
            "hs_name": "",
            "vm_uuid": "",
            "vm_pass": "",
        }

    def server(self):
        time_last = 0
        nets_apis = NCManage()
        nets_apis.get_nic()
        nets_list = nets_apis.nic_list
        while True:  # 每60秒上报一次 ===========================================
            time.sleep(1)
            time_data = time.time()
            if time_data - time_last > 60:
                self.vm_status.status()
                vm_status = self.vm_status.__dict__()
                for nic_name in nets_list:
                    nic_gate = nets_list[nic_name].ip4_gate
                    if nic_gate == "" or not nic_gate.endswith(".1"):
                        continue
                    nic_gate = ".".join(nic_gate.split(".")[:-1]) + ".2"
                    url_post = f"http://{nic_gate}:1880/api/client/upload"
                    url_post += f"?nic={nets_list[nic_name].mac_addr}"

                    try:  # 上报虚拟机状态 ====================================
                        logger.info("[上报虚拟机状态地址] {}", url_post)
                        logger.debug("[上报虚拟机状态数据] {}", vm_status)
                        vm_result = requests.post(
                            url=url_post, json=vm_status, timeout=5)
                        logger.info("[上报虚拟机状态结果] {}", vm_result.text)
                        if vm_result.status_code == 200:
                            logger.info("[上报虚拟机状态成功]")
                            vm_data = vm_result.json()['data']
                            if not vm_data:
                                continue
                            self.vm_config["vm_uuid"] = vm_data["vm_uuid"]
                            self.vm_config["vm_pass"] = vm_data["vm_pass"]
                            self.manage()
                    except requests.exceptions.ConnectionError as e:
                        print("[上报虚拟机状态异常]", e)
                        continue
                    except requests.exceptions.Timeout as e:
                        print("[上报虚拟机状态异常]", e)
                        continue
                    except Exception as e:
                        logger.error("[上报虚拟机状态异常] {}", e)
                time_last = time_data

    def manage(self):
        """管理虚拟机配置，设置主机名和管理员密码"""
        if not self.vm_config.get("vm_uuid") or not self.vm_config.get("vm_pass"):
            logger.warning("[管理虚拟机配置] 虚拟机UUID或密码为空，跳过配置")
            return

        vm_uuid = self.vm_config["vm_uuid"]
        vm_pass = self.vm_config["vm_pass"]

        # 检测操作系统类型
        system = platform.system().lower()
        logger.info("[管理虚拟机配置] 检测到操作系统: {}", system)

        try:
            if system == "linux":
                logger.info("[Linux配置] 开始设置Linux系统配置")

                # 设置主机名
                logger.info("[Linux主机名] 设置主机名为: {}", vm_uuid)
                
                # 获取当前主机名
                current_hostname_result = subprocess.run(["hostname"], capture_output=True, text=True)
                current_hostname = current_hostname_result.stdout.strip()
                
                if current_hostname == vm_uuid:
                    logger.info("[Linux主机名] 当前主机名已经是: {}，无需修改", vm_uuid)
                else:
                    logger.info("[Linux主机名] 当前主机名: {}，需要修改为: {}", current_hostname, vm_uuid)
                    result = subprocess.run(["sudo", "hostnamectl", "set-hostname", vm_uuid], capture_output=True,
                                            text=True)
                    if result.returncode == 0:
                        logger.info("[Linux主机名] 主机名设置成功: {}", vm_uuid)
                    else:
                        # 备用方式
                        with open("/etc/hostname", "w") as f:
                            f.write(vm_uuid + "\n")
                        subprocess.run(["sudo", "hostname", vm_uuid], check=True)
                        logger.info("[Linux主机名] 传统方式设置成功: {}", vm_uuid)

                # 设置root密码
                logger.info("[Linux密码] 设置root密码")
                process = subprocess.Popen(["sudo", "chpasswd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate(input=f"root:{vm_pass}")
                if process.returncode == 0:
                    logger.info("[Linux密码] root密码设置成功")
                else:
                    logger.error("[Linux密码] 设置失败: {}", stderr)

                logger.info("[Linux配置] Linux系统配置完成")

            elif system == "windows":
                logger.info("[Windows配置] 开始设置Windows系统配置")

                # 设置主机名
                logger.info("[Windows主机名] 设置主机名为: {}", vm_uuid)
                
                # 获取当前主机名
                current_hostname_result = subprocess.run(["hostname"], capture_output=True, text=True, shell=True)
                current_hostname = current_hostname_result.stdout.strip()
                
                if current_hostname.lower() == vm_uuid.lower():
                    logger.info("[Windows主机名] 当前主机名已经是: {}，无需修改", vm_uuid)
                else:
                    logger.info("[Windows主机名] 当前主机名: {}，需要修改为: {}", current_hostname, vm_uuid)
                    result = subprocess.run(["wmic", "computersystem", "where", "name='%computername%'", "rename", vm_uuid],
                                            capture_output=True, text=True, shell=True)
                    if result.returncode == 0:
                        logger.info("[Windows主机名] 主机名设置成功，需要重启后生效: {}", vm_uuid)
                    else:
                        logger.error("[Windows主机名] 设置失败: {}", result.stderr)

                # 设置administrator密码
                logger.info("[Windows密码] 设置administrator密码")
                result = subprocess.run(["net", "user", "administrator", vm_pass], capture_output=True, text=True)
                print(result.stdout)
                if result.returncode == 0:
                    logger.info("[Windows密码] administrator密码设置成功")
                else:
                    logger.error("[Windows密码] 设置失败: {}", result.stderr)

                logger.info("[Windows配置] Windows系统配置完成")
            else:
                logger.warning("[管理虚拟机配置] 不支持的操作系统: {}", system)

        except Exception as e:
            logger.error("[管理虚拟机配置] 配置失败: {}", e)


if __name__ == "__main__":
    ci = Cloudinit()
    ci.server()
