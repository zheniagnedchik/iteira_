#!/usr/bin/env python3
"""
Скрипт для переключения на новую систему диалогов
"""

import os

# Читаем текущий .env
env_path = '.env'
env_lines = []

try:
    with open(env_path, 'r') as f:
        env_lines = f.readlines()
except FileNotFoundError:
    print("Файл .env не найден")
    exit(1)

# Ищем строку USE_NEW_DIALOG_SYSTEM или добавляем её
found = False
for i, line in enumerate(env_lines):
    if line.startswith('USE_NEW_DIALOG_SYSTEM='):
        env_lines[i] = 'USE_NEW_DIALOG_SYSTEM=true\n'
        found = True
        break

if not found:
    env_lines.append('USE_NEW_DIALOG_SYSTEM=true\n')

# Записываем обратно
with open(env_path, 'w') as f:
    f.writelines(env_lines)

print("✅ Система переключена на новую архитектуру диалогов!")
print("🔧 Переменная USE_NEW_DIALOG_SYSTEM=true добавлена в .env")
print("\n📋 Особенности новой системы:")
print("   • Структурированные этапы диалога по шаблону")
print("   • Динамическая память (имя, услуга, локация)")
print("   • Проверка доступности онлайн-записи")
print("   • Использование существующего поисковика")
print("   • Премиум-тональность общения")
print("\n🚀 Перезапустите бота для применения изменений")
