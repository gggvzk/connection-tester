from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import socket
import re
import platform
import time
import psutil
import requests

try:
    import stun
except Exception:
    stun = None

app = Flask(__name__)
CORS(app)

def run_command(args):
    try:
        p = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="cp932",
            errors="replace",
            timeout=5
        )
        return p.stdout
    except Exception:
        return ""

def get_wifi():
    if platform.system() != "Windows":
        return {"error": "Wi-Fi詳細取得は現在Windows向けです"}

    text = run_command(["netsh", "wlan", "show", "interfaces"])

    def value(pattern):
        m = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        return m.group(1).strip() if m else None

    signal = value(r"^\s*Signal\s*:\s*(\d+)%")
    channel = value(r"^\s*Channel\s*:\s*(\d+)")
    return {
        "ssid": value(r"^\s*SSID\s*:\s*(.+)$"),
        "bssid": value(r"^\s*BSSID\s*:\s*(.+)$"),
        "signal_percent": int(signal) if signal else None,
        "channel": int(channel) if channel else None,
        "radio_type": value(r"^\s*Radio type\s*:\s*(.+)$"),
        "receive_mbps": value(r"^\s*Receive rate \(Mbps\)\s*:\s*(.+)$"),
        "transmit_mbps": value(r"^\s*Transmit rate \(Mbps\)\s*:\s*(.+)$"),
        "authentication": value(r"^\s*Authentication\s*:\s*(.+)$"),
        "cipher": value(r"^\s*Cipher\s*:\s*(.+)$"),
    }

def get_interfaces():
    result = []
    for name, addrs in psutil.net_if_addrs().items():
        item = {"name": name, "mac": None, "ipv4": [], "ipv6": []}
        for a in addrs:
            family = str(a.family)
            if family.endswith("AF_LINK") or family.endswith("AF_PACKET"):
                item["mac"] = a.address
            elif a.family == socket.AF_INET:
                item["ipv4"].append(a.address)
            elif a.family == socket.AF_INET6:
                item["ipv6"].append(a.address.split("%")[0])
        result.append(item)
    return result

def get_default_gateway():
    if platform.system() != "Windows":
        return None
    text = run_command(["route", "print", "-4"])
    for line in text.splitlines():
        m = re.match(r"\s*0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)\s+\S+\s+\S+\s+\d+", line)
        if m:
            return m.group(1)
    return None

def get_dns():
    if platform.system() != "Windows":
        return []
    text = run_command(["ipconfig", "/all"])
    dns = []
    in_dns = False
    for line in text.splitlines():
        if "DNS Servers" in line:
            in_dns = True
            m = re.search(r":\s*(.+)$", line)
            if m:
                dns.append(m.group(1).strip())
            continue
        if in_dns:
            if line.startswith(" ") or line.startswith("\t"):
                s = line.strip()
                if re.match(r"^[0-9a-fA-F:.]+$", s):
                    dns.append(s)
            else:
                in_dns = False
    return list(dict.fromkeys(dns))

def ping_host(host="1.1.1.1"):
    count_flag = "-n" if platform.system() == "Windows" else "-c"
    try:
        start = time.perf_counter()
        p = subprocess.run(
            ["ping", count_flag, "1", "-w", "1500", host],
            capture_output=True,
            text=True,
            encoding="cp932",
            errors="replace",
            timeout=3
        )
        elapsed = round((time.perf_counter() - start) * 1000, 1)
        m = re.search(r"[=<]\s*(\d+)\s*ms", p.stdout, re.I)
        return {
            "host": host,
            "success": p.returncode == 0,
            "ms": float(m.group(1)) if m else (elapsed if p.returncode == 0 else None)
        }
    except Exception:
        return {"host": host, "success": False, "ms": None}

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org?format=json", timeout=3).json().get("ip")
    except Exception:
        return None

def get_nat():
    if stun is None:
        return {"type": "Unknown", "detail": "pystun3 が利用できません"}
    try:
        nat_type, external_ip, external_port = stun.get_ip_info(
            stun_host="stun.l.google.com",
            stun_port=19302
        )
        return {
            "type": str(nat_type),
            "external_ip": external_ip,
            "external_port": external_port
        }
    except Exception as e:
        return {"type": "Unknown", "detail": "STUN判定に失敗しました"}

@app.get("/api/health")
def health():
    return jsonify({"ok": True})

@app.get("/api/network")
def network():
    interfaces = get_interfaces()
    wifi = get_wifi()
    gateway = get_default_gateway()
    dns = get_dns()
    p = ping_host()

    primary = next(
        (x for x in interfaces if x["ipv4"] and x["name"].lower() not in ("loopback",)),
        None
    )

    return jsonify({
        "timestamp": time.time(),
        "platform": platform.platform(),
        "wifi": wifi,
        "network": {
            "mac": primary["mac"] if primary else None,
            "ipv4": primary["ipv4"] if primary else [],
            "ipv6": primary["ipv6"] if primary else [],
            "gateway": gateway,
            "dns": dns,
            "interfaces": interfaces
        },
        "connection": {
            "ping": p,
            "public_ip": get_public_ip(),
            "nat": get_nat()
        }
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
