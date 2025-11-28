#!/usr/bin/env python3
import requests
import socket
import sys

def check_site():
    print("=== ДИАГНОСТИКА САЙТА MATRIX BLOG ===")
    
    urls = [
        "http://82.202.141.206",
        "http://82.202.141.206:80", 
        "http://82.202.141.206:8000",
        "http://localhost"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: HTTP {response.status_code} OK")
            if response.status_code == 200:
                print(f"   📄 Размер: {len(response.content)} байт")
                print(f"   🏷️  Заголовок: {response.headers.get('Server', 'N/A')}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url}: Ошибка соединения")
        except requests.exceptions.Timeout:
            print(f"⏰ {url}: Таймаут")
        except Exception as e:
            print(f"❌ {url}: {str(e)}")
        print()
    
    # Проверка портов
    print("=== ПРОВЕРКА ПОРТОВ ===")
    ports = [80, 8000, 443]
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('82.202.141.206', port))
        if result == 0:
            print(f"✅ Порт {port}: открыт")
        else:
            print(f"❌ Порт {port}: закрыт или недоступен")
        sock.close()
    
    print("\n=== РЕКОМЕНДАЦИИ ===")
    print("1. Если сайт не открывается, попробуйте:")
    print("   - Очистить кэш браузера (Ctrl+Shift+Delete)")
    print("   - Попробовать инкогнито/приватный режим")
    print("   - Отключить расширения браузера")
    print("2. Попробуйте альтернативные адреса:")
    print("   - http://82.202.141.206:8000")
    print("   - http://localhost (если вы на том же сервере)")
    print("3. Проверьте подключение:")
    print("   - ping 82.202.141.206")
    print("   - telnet 82.202.141.206 80")

if __name__ == "__main__":
    check_site()