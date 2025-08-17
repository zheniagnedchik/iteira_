#!/usr/bin/env python3
"""
Простой скрипт для проверки и перезапуска системы
"""

import sys
import subprocess

def main():
    """Запускает проверку и перезапуск системы."""
    print("🔧 Проверка и перезапуск RAG-системы салона красоты")
    print("=" * 60)
    
    try:
        # Запускаем system_manager с проверкой и перезапуском
        result = subprocess.run([
            sys.executable, "system_manager.py", "--check-and-restart", "--save-report"
        ], check=False)
        
        if result.returncode == 0:
            print("\n🎉 Система работает нормально!")
        else:
            print("\n💥 Обнаружены проблемы с системой")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Ошибка при запуске проверки: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())