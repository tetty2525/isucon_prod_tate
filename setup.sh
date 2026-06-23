#!/bin/bash
# ISUCON サーバー初期設定スクリプト

# 1. unattended-upgrades の無効化
echo "Disabling unattended-upgrades..."
sudo systemctl stop unattended-upgrades
sudo systemctl disable unattended-upgrades

# 2. Swap 1GB の作成
if [ ! -f /swapfile ]; then
  echo "Creating 1GB swapfile..."
  sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 3. 計測ツールのインストール (netdata, percona-toolkit, alp)
if ! command -v netdata &> /dev/null; then
  echo "Installing netdata..."
  wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh && sh /tmp/netdata-kickstart.sh --non-interactive
fi

if ! command -v pt-query-digest &> /dev/null; then
  echo "Installing percona-toolkit..."
  sudo apt-get update
  sudo apt-get install -y percona-toolkit unzip
fi

if ! command -v alp &> /dev/null; then
  echo "Installing alp..."
  wget https://github.com/tkuchiki/alp/releases/download/v1.0.21/alp_linux_amd64.zip
  unzip alp_linux_amd64.zip
  sudo install alp /usr/local/bin/alp
  rm alp alp_linux_amd64.zip
fi

# 4. isu-ruby停止とisu-python起動設定
echo "Switching to python app..."
sudo systemctl stop isu-ruby
sudo systemctl disable isu-ruby
sudo systemctl enable isu-python

echo "Setup Complete!"
