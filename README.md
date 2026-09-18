# ARP Spoofing Tool

![Python](https://img.shields.io/badge/python-3.11-blue)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)
![Scapy](https://img.shields.io/badge/scapy-2.5%2B-orange)
![Conda](https://img.shields.io/badge/conda-arp__spoof-green)
![License](https://img.shields.io/badge/license-MIT-green)

Простой ARP-spoofing инструмент для проведения MITM-атак в локальной сети.
Написан на Python 3.11 с использованием [Scapy](https://scapy.net/).

> ⚠️ **Только для образовательных целей и легального пентеста.**
> Использование против сетей без письменного разрешения владельца
> преследуется по закону (ст. 272 УК РФ и аналоги в других странах).

---

## Содержание

- [🛠 Что делает](#-что-делает)
- [📌 Требования](#-требования)
- [⚙ Установка](#-установка)
- [⚔ Использование](#-использование)
- [📑 Пример вывода](#-пример-вывода)
- [💊 Как остановить и восстановить сеть](#-как-остановить-и-восстановить-сеть)
- [🔗 Ограничения](#-ограничения)
- [FAQ](#faq)
- [⚠ Дисклеймер](#-дисклеймер)

---

## 🛠 Что делает

Скрипт проводит **ARP-spoofing** между жертвой и шлюзом:

1. Отправляет жертве фальшивый ARP-ответ: «IP шлюза теперь на моём MAC».
2. Отправляет шлюзу фальшивый ARP-ответ: «IP жертвы теперь на моём MAC».
3. Включает `ip_forward`, чтобы трафик жертвы шёл через вашу машину дальше в интернет.
4. При `Ctrl+C` восстанавливает исходные ARP-таблицы и выключает `ip_forward`.

Результат — весь трафик жертвы проходит через вашу машину. Дальше его можно:

- смотреть (`tcpdump -i eth0 -A`);
- анализировать (`wireshark`, `mitmproxy`);
- модифицировать (`ettercap`, `bettercap`);
- резать (`iptables -A FORWARD -j DROP`).

---

## 📌 Требования

| Компонент | Версия | Зачем |
|---|---|---|
| **Linux** | любая современная | Windows/macOS не подходят (см. [Ограничения](#ограничения)) |
| **Python** | 3.11 | зафиксирован в `environment.yml` |
| **Scapy** | 2.5+ | работа с L2-пакетами |
| **Conda** | любая | для установки окружения `arp_spoof` |
| **root** | обязателен | raw-сокеты и запись в `/proc/sys/` |
| **libpcap** | обычно предустановлен | Scapy использует для захвата |

---

## ⚙ Установка

### Вариант 1: conda + environment.yml (рекомендуется)

В репозитории лежит environment.yml — он создаёт окружение arp_spoof
со всеми зависимостями.
```bash
git clone https://github.com/<ваш-ник>/arp-spoofing.git
cd arp-spoofing

conda env create -f environment.yml
conda activate arp_spoof
```
### Вариант 2: venv + pip

Если conda нет под рукой:
```bash
git clone https://github.com/<ваш-ник>/arp-spoofing.git
cd arp-spoofing

python3 -m venv venv
source venv/bin/activate

pip install scapy
```
### Вариант 3: системный Python
```bash

sudo apt update
sudo apt install python3 python3-pip
pip3 install --user scapy
```

---

## ⚔ Использование

Скрипт требует root (raw-сокеты + запись в /proc/sys/):
```bash

sudo python3 arp_spoof.py -t <IP жертвы> -g <IP шлюза> [-i <интерфейс>]
```
Если работаете в conda-окружении — не забудьте его активировать до sudo:
```bash

conda activate arp_spoof
sudo $(which python3) arp_spoof.py -t 192.168.1.100 -g 192.168.1.1 -i eth0
```

### Аргументы
| Флаг | Обязателен | По умолчанию | Описание |
|---|---|---|---|
| **-t, --target** | да | — | IP-адрес жертвы |
| **-g, --gateway** | да | — | IP-адрес шлюза |
| **-i, --interface** | нет | eth0 | Сетевой интерфейс |

### Примеры
```bash

# Классический сценарий
sudo python3 arp_spoof.py -t 192.168.1.100 -g 192.168.1.1

# Свой интерфейс
sudo python3 arp_spoof.py -t 192.168.1.100 -g 192.168.1.1 -i enp3s0

# Виртуалка VirtualBox
sudo python3 arp_spoof.py -t 10.0.2.15 -g 10.0.2.2 -i eth0

# Из conda-окружения
conda activate arp_spoof
sudo $(which python3) arp_spoof.py -t 192.168.1.100 -g 192.168.1.1 -i eth0
```

---

## 📑 Пример вывода
```text

[*] Получение MAC-адреса жертвы...
[+] MAC жертвы: 08:00:27:1a:2b:3c
[*] Получение MAC-адреса шлюза...
[+] MAC шлюза: 52:54:00:12:34:56

[+] Запуск ARP Spoofing на интерфейсе eth0...
[+] Нажми Ctrl+C для остановки

[+] Отправлено пакетов: 42
^C

[!] Останавливаем атаку и восстанавливаем ARP-таблицы...
[+] Атака завершена. ARP-таблицы восстановлены.
```

---

## 💊 Как остановить и восстановить сеть

Обычный случай: нажать Ctrl+C в терминале — скрипт сам восстановит ARP-таблицы.

Если скрипт упал с `kill -9` (или выключилось питание) — ARP-таблицы
жертвы и шлюза останутся отравленными. Восстановить вручную:
```bash

# На машине атакующего: узнать MAC шлюза
arping -I eth0 192.168.1.1

# С машины жертвы (или через ssh): сбросить ARP-кэш
sudo ip -s -s neigh flush all
# или конкретно:
sudo arp -d 192.168.1.1
```
Проверить, что ip_forward выключен:
```bash

cat /proc/sys/net/ipv4/ip_forward
# должно быть 0
```
Если не 0 — выключить:
```bash

echo 0 | sudo tee /proc/sys/net/ipv4/ip_forward
```

---

## 🔗 Ограничения
🔹 Не работает на Windows и macOS  

- os.geteuid() — только POSIX.
- /proc/sys/net/ipv4/ip_forward — только Linux.
- sendp на Windows требует Npcap, но L2-пакеты уходят нестабильно.
- ARP-стек Windows игнорирует gratuitous ARP без правки реестра.

Решение: запускать на Linux. На Windows — Linux-виртуалка с bridged-сетью
(VirtualBox/VMware) или Live-USB Kali.  

🔹 Не работает по Wi-Fi (обычно)  

На Wi-Fi нужен monitor mode и кадры Dot11, а не Ether. Проводной eth0/enp3s0
надёжнее.  

🔹 Не работает в WSL2  

WSL2 использует NAT-сеть — ваш ARP-spoofing из WSL2 не пойдёт в реальный L2-сегмент.
Не работает в контейнерах (Docker)

🔹 /proc/sys/net/ipv4/ip_forward внутри контейнера может быть read-only или
отражать состояние хоста.  

🔹 IPv6 не поддерживается  

Скрипт работает только с IPv4. Если в сети есть IPv6, жертва может ходить
через него мимо вас.  

🔹 HTTPS не расшифровывается  

MITM даёт видеть только метаданные HTTPS (IP, порт, SNI). Тело — шифровано.
Для расшифровки нужны дополнительные инструменты (sslstrip, mitmproxy с
подменой сертификата, HSTS-обход и т.д.).

---

## FAQ

**Q: Скрипт запустился, но у жертвы пропал интернет.**  
A: Скорее всего, ip_forward не включился. Проверьте ```cat /proc/sys/net/ipv4/ip_forward.```
Должно быть 1 во время атаки.

**Q: [!] Ошибка: [Errno 1] Operation not permitted.**  
A: Запускайте от root.

**Q: Не удалось получить MAC для жертвы.**  
A: Либо жертва не в той же подсети, либо неправильный интерфейс.
Проверьте `-i` — на современных Linux интерфейс называется не eth0, а enp3s0/ens33.

**Q: conda env create -f environment.yml падает с argparse-1.4.0-py26_0.**  
A: В `environment.yml` попали встроенные модули (argparse, os, sys, time).
Их там быть не должно — они часть стандартной библиотеки. Правильный файл — см. выше.

**Q: ModuleNotFoundError: No module named 'scapy' при запуске из PyCharm.**  
A: PyCharm использует не то окружение. `File → Settings → Project → Python Interpreter
→ выбрать arp_spoof` (или указать путь .../miniconda3/envs/arp_spoof/bin/python3).

**Q: Жертва — Windows, атака не работает.**  
A: Windows-ARP-стек игнорирует часть gratuitous ARP. Иногда помогает
`arp -d` на жертве перед атакой или увеличение частоты пакетов.

**Q: Как увидеть трафик жертвы?**  
A: ```sudo tcpdump -i eth0 -A 'host 192.168.1.100'```. Или запустите Wireshark
на интерфейсе и фильтруйте по IP жертвы.

**Q: Как модифицировать трафик?**  
A: Это уже за рамками скрипта. Смотрите bettercap, mitmproxy, ettercap.

**Q: Можно ли добавить IPv6?**  
A: Да, но это отдельный скрипт — IPv6 использует NDP (Neighbor Discovery),
а не ARP. Замените ARP на ICMPv6ND_NA и добавьте `sysctl net.ipv6.conf.all.forwarding=1`.

---

## ⚠ Дисклеймер

Данный инструмент предоставлен исключительно в образовательных целях.

Автор не несёт ответственности за любое использование в противоправных целях.
Применение ARP-spoofing без явного письменного согласия владельца сети
нарушает:

✅ УК РФ, ст. 272 — неправомерный доступ к компьютерной информации;  
✅ CFAA (США) — Computer Fraud and Abuse Act;  
✅ Computer Misuse Act (Великобритания);  
    и аналогичные законы в других странах.

Используйте только:

✅ в своей домашней сети;  
✅ в изолированной лаборатории (виртуалки, GNS3, EVE-NG);  
✅ на пентесте с подписанным scope и разрешением;  
✅ в учебном курсе с санкционированной сетью.
