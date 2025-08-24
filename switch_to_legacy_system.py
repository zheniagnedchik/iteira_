#!/usr/bin/env python3
"""
Скрипт для переключения на старую (legacy) систему диалогов
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
        env_lines[i] = 'USE_NEW_DIALOG_SYSTEM=false\n'
        found = True
        break

if not found:
    env_lines.append('USE_NEW_DIALOG_SYSTEM=false\n')

# Записываем обратно
with open(env_path, 'w') as f:
    f.writelines(env_lines)

print("✅ Система переключена на старую (legacy) архитектуру!")
print("🔧 Переменная USE_NEW_DIALOG_SYSTEM=false добавлена в .env")
print("\n📋 Особенности legacy системы:")
print("   • UnifiedGPTOrchestrator")
print("   • Полностью GPT-driven без жестких этапов")
print("   • Гибкая обработка контекста")
print("\n🚀 Перезапустите бота для применения изменений")

