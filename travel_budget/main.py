import argparse
import logging

from services import DRIVE_SERVICE, EMAIL_USER, SHEETS_SERVICE

logger = logging.getLogger(__name__)


# Функция чтения списка документов с таблицами
def get_list_obj(service):
    response = (
        service.files()
        .list(q="mimeType= 'application/vnd.google-apps.spreadsheet'")
        .execute()
    )
    return response["files"]


# Функция удаления всех документов с таблицами
def clear_disk(service):
    spreadsheets = get_list_obj(service)
    if spreadsheets:
        for spreadsheet in spreadsheets:
            response = service.files().delete(fileId=spreadsheet["id"])
        response.execute()
    return "Документы удалены"


# Выдаём права личному гугл-аккаунту на доступ к документу
def set_user_permissions(service, spreadsheetId):
    permissions_body = {
        "type": "user",
        "role": "writer",
        "emailAddress": EMAIL_USER,
    }
    service.permissions().create(
        fileId=spreadsheetId, body=permissions_body, fields="id"
    ).execute()


# Создаём документ с таблицами
def create_spreadsheet(service, data):
    # Тут будет распаковываться значение аргумента, которое состоит
    # из двух частей, записанных через запятую: название документа, сумма
    title, cash = data.split(",")
    spreadsheet_body = {
        "properties": {
            # Название таблицы из значения аргумента
            "title": title,
            "locale": "ru_RU",
        },
        "sheets": [
            {
                "properties": {
                    "sheetType": "GRID",
                    "sheetId": 0,
                    "title": "Отпуск",
                    "gridProperties": {"rowCount": 100, "columnCount": 100},
                }
            }
        ],
    }
    request = service.spreadsheets().create(body=spreadsheet_body)
    response = request.execute()
    spreadsheet_id = response["spreadsheetId"]
    # Вызываем функцию выдачи прав
    set_user_permissions(DRIVE_SERVICE, spreadsheet_id)
    spreadsheet_update_values(
        SHEETS_SERVICE, spreadsheet_id, cash, default=True
    )
    print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    return f"Был создан документ с ID {spreadsheet_id}"


def read_values(service, spreadsheetId):
    range = "A1:I10"
    response = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheetId,
            range=range,
        )
        .execute()
    )
    return response["values"]


def spreadsheet_update_values(service, spreadsheetId, data, default=False):
    # Если параметр default=True в документ добавится шапка
    if default:
        table_values = [
            ["Бюджет путешествия"],
            ["Весь бюджет", data],
            ["Все расходы", "=SUM(E7:E30)"],
            ["Остаток", "=B2-B3"],
            ["Расходы"],
            ["Описание", "Тип", "Кол-во", "Цена", "Стоимость"],
        ]
    # Иначе к текущему содержимому добавится новая строка
    else:
        table_values = read_values(service, spreadsheetId)
        table_values.append(data.split(","))
    request_body = {"majorDimension": "ROWS", "values": table_values}
    request = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheetId,
            range="A1:E30",
            valueInputOption="USER_ENTERED",
            body=request_body,
        )
    )
    request.execute()
    return "Документ обновлен"


def main(args):
    # Аргумент для функции, которая выводит список
    # всех документов с таблицами
    if args.list:
        return get_list_obj(DRIVE_SERVICE)
    # Аргумент для функции, которая удаляет
    # все документы с таблицами
    if args.clear_all:
        return clear_disk(DRIVE_SERVICE)
    if args.create is not None:
        return create_spreadsheet(SHEETS_SERVICE, args.create)
    # Объявляем переменную для хранения ID документа
    spreadsheet_id = None
    if args.id is not None:
        spreadsheet_id = args.id
    else:
        # Получаем список всех таблиц
        spreadsheets = get_list_obj(DRIVE_SERVICE)
        if spreadsheets:
            spreadsheet_id = spreadsheets[0]["id"]
    if args.update is not None:
        return spreadsheet_update_values(
            SHEETS_SERVICE, spreadsheet_id, args.update
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Экземпляра класса ArgumentParser
    parser = argparse.ArgumentParser(description="Бюджет путешествий")
    # Аргументы командной строки
    parser.add_argument("-c", "--create", help="Создать файл — введите имя")
    parser.add_argument(
        "-cl",
        "--clear_all",
        action="store_true",
        help="Удалить все spreadsheets",
    )
    parser.add_argument("-i", "--id", help="Указать id spreadsheet")
    parser.add_argument(
        "-ls", "--list", action="store_true", help="Вывести все spreadsheets"
    )
    parser.add_argument("-u", "--update", help="Обновить данные таблицы")
    # Парсинг аргументов командной строки
    args = parser.parse_args()

    print(main(args))
