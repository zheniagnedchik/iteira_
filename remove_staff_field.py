import json

def create_services_no_staff(input_file, output_file):
    """
    Создает файл без ВСЕХ полей 'staff' - как из основных объектов услуг,
    так и из объектов companies
    
    Args:
        input_file (str): Путь к исходному JSON файлу
        output_file (str): Путь к выходному JSON файлу
    """
    # Читаем JSON файл
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Создаем копию данных
    import copy
    data_copy = copy.deepcopy(data)
    
    def remove_staff_recursive(obj):
        """Рекурсивно удаляет все поля 'staff' из объекта."""
        if isinstance(obj, dict):
            # Сначала рекурсивно обрабатываем все значения
            for key, value in list(obj.items()):
                remove_staff_recursive(value)
            
            # Затем удаляем поле staff если оно есть
            if 'staff' in obj:
                del obj['staff']
        elif isinstance(obj, list):
            # Рекурсивно обрабатываем все элементы списка
            for item in obj:
                remove_staff_recursive(item)
    
    # Удаляем все поля staff рекурсивно
    remove_staff_recursive(data_copy)
    
    # Также удаляем поле staff из field_statistics если оно есть
    if 'data' in data_copy and 'field_statistics' in data_copy['data']:
        if 'staff' in data_copy['data']['field_statistics']:
            del data_copy['data']['field_statistics']['staff']
    
    # Записываем обновленные данные в новый файл
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data_copy, file, ensure_ascii=False, indent=2)
    
    print(f"Файл {output_file} успешно создан без ВСЕХ полей 'staff'")

# Использование функции
if __name__ == "__main__":
    create_services_no_staff('services.json', 'services_no_staff.json')