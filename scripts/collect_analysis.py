#!/usr/bin/env python3
import datetime
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(BASE_DIR, "docs", "runs")
SSH_KEY = os.path.expanduser("~/.ssh/ws-default-keypair.pem")
SSH_HOST = "isucon@54.150.95.245"
SSH_BASE = ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", SSH_HOST]

COMMANDS = {
    "alp.txt": "sudo alp ltsv --file=/var/log/nginx/access.log --sort=sum -r -m '/image/[0-9]+,/posts/[0-9]+,/@.*'",
    "slow_query.txt": "sudo pt-query-digest /var/log/mysql/mysql-slow.log | head -n 120 | cut -c 1-4000",
    "system.txt": "date; uptime; free -h; df -h /; systemctl --no-pager --full status nginx mysql isu-python | head -n 80",
}


def git_output(args):
    try:
        return subprocess.check_output(["git"] + args, cwd=BASE_DIR, text=True).strip()
    except Exception as exc:
        return f"unknown ({exc})"


def run_remote(command):
    return subprocess.run(
        SSH_BASE + [command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        check=False,
    )


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(RUNS_DIR, timestamp)
    os.makedirs(run_dir, exist_ok=True)

    metadata = [
        f"timestamp={timestamp}",
        f"commit={git_output(['rev-parse', '--short', 'HEAD'])}",
        f"dirty={bool(git_output(['status', '--porcelain']))}",
        f"message={git_output(['log', '-1', '--pretty=%s'])}",
    ]
    with open(os.path.join(run_dir, "metadata.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(metadata) + "\n")

    for filename, command in COMMANDS.items():
        print(f"Collecting {filename}...")
        result = run_remote(command)
        with open(os.path.join(run_dir, filename), "w", encoding="utf-8") as f:
            f.write(result.stdout)
        if result.returncode != 0:
            print(f"Warning: {filename} exited with {result.returncode}")

    print(f"Analysis saved to {os.path.relpath(run_dir, BASE_DIR)}")


if __name__ == "__main__":
    main()
