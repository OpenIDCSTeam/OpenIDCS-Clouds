chmod +x ./ServerInit
chmod +x ./ServerInit.service
mkdir                -p /opt/ServerInit/
cp ./ServerInit         /opt/ServerInit/
cp ./ServerInit.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ServerInit

# 配置 systemd-networkd 网络
echo "[网络配置] 启用 systemd-networkd"
systemctl enable --now systemd-networkd

# 创建网络配置文件
mkdir -p /etc/systemd/network
cat > /etc/systemd/network/99-dhcp-any.network << 'EOF'
[Match]
Name=*

[Network]
DHCP=yes
EOF

echo "[网络配置] 网络配置文件已创建: /etc/systemd/network/99-dhcp-any.network"
systemctl restart systemd-networkd
echo "[网络配置] systemd-networkd 已重启"

# 1. 清用户级 bash 历史（当前会话也清）
history -c && history -w

# 2. 清系统级历史记录（/root 和所有普通用户）
find /home /root -maxdepth 1 -type f -name '.bash_history' -exec truncate -s 0 {} \;

# 3. 清 /tmp、/var/tmp（跳过正在使用的文件）
find /tmp /var/tmp -type f -delete 2>/dev/null
find /tmp /var/tmp -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null

# 4. 清 apt 缓存（Debian/Ubuntu 系列）
command -v apt >/dev/null && apt clean

# 5. 清 yum/dnf 缓存（RHEL/CentOS/Fedora/Alma/Rocky）
command -v yum  >/dev/null && yum clean all
command -v dnf  >/dev/null && dnf clean all

# 6. 清 zypper 缓存（openSUSE）
command -v zypper >/dev/null && zypper clean --all

# 7. 清 pacman 缓存（Arch）
command -v pacman >/dev/null && pacman -Scc --noconfirm

# 8. 清 snap 旧版本（Ubuntu 等）
command -v snap >/dev/null && snap list --all | awk '/disabled/{print $1,$2}' | while read snapname revision; do snap remove "$snapname" --revision="$revision"; done 2>/dev/null

# 9. 清 journal 日志（保留最近 24 小时）
journalctl --vacuum-time=1d

# 10. 清回收站（所有用户）
find /home /root -type d -name '.local' -exec find {}/Share/Trash -mindepth 1 -delete \; 2>/dev/null
