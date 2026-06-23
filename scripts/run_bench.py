#!/usr/bin/env python3
import subprocess
import json
import os
import datetime
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(BASE_DIR, "docs", "score_history.csv")
SSH_KEY = os.path.expanduser("~/.ssh/ws-default-keypair.pem")
SSH_HOST = "isucon@54.150.95.245"
SSH_BASE = ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", SSH_HOST]

def get_latest_commit_message():
    try:
        msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], cwd=BASE_DIR).decode('utf-8').strip()
        return msg.split('\n')[0]
    except Exception:
        return "Unknown change"

def get_git_revision():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=BASE_DIR, text=True).strip()
    except Exception:
        return "unknown"

def get_git_dirty():
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=BASE_DIR, text=True).strip()
        return bool(status)
    except Exception:
        return True

def get_system_metrics():
    # Returns (cpu_user, cpu_system, cpu_idle, cpu_iowait, net_rx, net_tx, loadavg)
    cmd = SSH_BASE + ["cat /proc/stat | grep '^cpu '; grep -E 'eth0|ens5' /proc/net/dev; cat /proc/loadavg"]
    try:
        out = subprocess.check_output(cmd, text=True).strip().split('\n')
        # out[0]: cpu  234 0 123 456 ...
        # out[1]: ens5: 1234 10 ...
        # out[2]: 0.10 0.15 0.20 1/150 1234
        cpu_parts = out[0].split()[1:]
        cpu_user = int(cpu_parts[0]) + int(cpu_parts[1]) # user + nice
        cpu_system = int(cpu_parts[2]) + int(cpu_parts[5]) + int(cpu_parts[6]) # system + irq + softirq
        cpu_idle = int(cpu_parts[3])
        cpu_iowait = int(cpu_parts[4])
        
        net_parts = out[1].split(':')[1].split()
        net_rx = int(net_parts[0])
        net_tx = int(net_parts[8])
        
        loadavg = out[2].split()[0]
        
        return (cpu_user, cpu_system, cpu_idle, cpu_iowait, net_rx, net_tx, loadavg)
    except Exception as e:
        print(f"Warning: Failed to get metrics: {e}")
        return (0, 0, 0, 0, 0, 0, "0.00")

def write_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    headers = ["DateTime", "Commit", "Dirty", "Score", "Pass", "CPU_User(%)", "CPU_Sys(%)", "CPU_Idle(%)", "CPU_IOWait(%)", "Net_RX(MB)", "Net_TX(MB)", "LoadAvg", "Change"]
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)

def main():
    print("=========================================")
    print("  RUNNING BENCHMARKER (CSV + Metrics wrapper)")
    print("=========================================")
    
    print("Fetching initial metrics...")
    u1, s1, i1, w1, rx1, tx1, _ = get_system_metrics()
    
    ssh_cmd = SSH_BASE + ["/home/isucon/private_isu/benchmarker/bin/benchmarker -u /home/isucon/private_isu/benchmarker/userdata -t http://127.0.0.1"]
    
    process = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    output_line = ""
    for line in process.stdout:
        print(line, end="")
        if line.strip().startswith("{"):
            output_line = line.strip()
            
    process.wait()
    
    print("Fetching final metrics...")
    u2, s2, i2, w2, rx2, tx2, loadavg = get_system_metrics()
    
    du = u2 - u1
    ds = s2 - s1
    di = i2 - i1
    dw = w2 - w1
    dtot = du + ds + di + dw
    if dtot == 0: dtot = 1 # prevent div by zero
    
    cpu_user_pct = round(100.0 * du / dtot, 1)
    cpu_sys_pct = round(100.0 * ds / dtot, 1)
    cpu_idle_pct = round(100.0 * di / dtot, 1)
    cpu_iowait_pct = round(100.0 * dw / dtot, 1)
    
    net_rx_mb = round((rx2 - rx1) / (1024*1024), 2)
    net_tx_mb = round((tx2 - tx1) / (1024*1024), 2)
    
    if output_line:
        try:
            result = json.loads(output_line)
            score = result.get("score", 0)
            is_pass = result.get("pass", False)
            
            commit_msg = get_latest_commit_message()
            commit_sha = get_git_revision()
            dirty = get_git_dirty()
            dt_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row = [dt_str, commit_sha, dirty, score, is_pass, cpu_user_pct, cpu_sys_pct, cpu_idle_pct, cpu_iowait_pct, net_rx_mb, net_tx_mb, loadavg, commit_msg]
            write_csv(row)
            
            print(f"\\n✅ Score {score} recorded to docs/score_history.csv")
            print(f"🔖 Commit: {commit_sha} / Dirty: {dirty}")
            print(f"📊 CPU: User {cpu_user_pct}% / Sys {cpu_sys_pct}% / IOWait {cpu_iowait_pct}%")
            print(f"🌐 Net: RX {net_rx_mb}MB / TX {net_tx_mb}MB")
            
        except json.JSONDecodeError:
            print("\\n❌ Failed to parse benchmarker output as JSON.")
    else:
        print("\\n❌ No JSON output found from benchmarker.")

if __name__ == "__main__":
    main()
