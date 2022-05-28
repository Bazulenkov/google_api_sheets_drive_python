import logging
import os

from apiclient import discovery
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

load_dotenv()

EMAIL_USER = os.environ["EMAIL"]

info = {
    "type": os.environ["TYPE"],
    "project_id": os.environ["PROJECT_ID"],
    "private_key_id": os.environ["PRIVATE_KEY_ID"],
    "private_key": os.environ["PRIVATE_KEY"],
    "client_email": os.environ["CLIENT_EMAIL"],
    "client_id": os.environ["CLIENT_ID"],
    "auth_uri": os.environ["AUTH_URI"],
    "token_uri": os.environ["TOKEN_URI"],
    "auth_provider_x509_cert_url": os.environ["AUTH_PROVIDER_X509_CERT_URL"],
    "client_x509_cert_url": os.environ["CLIENT_X509_CERT_URL"],
}


# CREDENTIALS_FILE = 'admin5-stat-4a27fb190068.json'


def auth():
    credentials = Credentials.from_service_account_info(info=info, scopes=SCOPES)
    service = discovery.build("sheets", "v4", credentials=credentials)
    return service, credentials


def create_spreadsheet(service):
    # Тело spreadsheet
    spreadsheet_body = {
        # Свойства spreadsheet
        "properties": {"title": "Бюджет путешествий", "locale": "ru_RU"},
        # Свойства sheet
        "sheets": [
            {
                "properties": {
                    "sheetType": "GRID",
                    "sheetId": 0,
                    "title": "Отпуск 2077",
                    "gridProperties": {"rowCount": 100, "columnCount": 100},
                }
            }
        ],
    }

    request = service.spreadsheets().create(body=spreadsheet_body)
    response = request.execute()
    spreadsheet_id = response["spreadsheetId"]
    logger.info("https://docs.google.com/spreadsheets/d/" + spreadsheet_id)
    return spreadsheet_id


def set_user_permissions(spreadsheet_id, credentials):
    permissions_body = {
        "type": "user",  # Тип учетных данных
        "role": "writer",  # Права доступа для учётной записи
        "emailAddress": EMAIL_USER,  # Ваш личный гугл-аккаунт
    }

    # Создаётся экземпляр класса Resource для Google Drive API
    drive_service = discovery.build("drive", "v3", credentials=credentials)

    # Формируется и сразу выполняется запрос на выдачу прав вашему аккаунту
    drive_service.permissions().create(
        fileId=spreadsheet_id, body=permissions_body, fields="id"
    ).execute()


def spreadsheet_update_values(service, spreadsheet_id):
    # Данные для заполнения: выводятся в таблице сверху вниз, слева направо
    table_values = [
        ["Бюджет путешествий"],
        ["Весь бюджет", "5000"],
        ["Все расходы", "=SUM(E7:E30)"],
        ["Остаток", "=B2-B3"],
        ["Расходы"],
        ["Описание", "Тип", "Кол-во", "Цена", "Стоимость"],
        ["Перелет", "Транспорт", "2", "400", "=C7*D7"],
    ]

    # Тело запроса
    request_body = {"majorDimension": "ROWS", "values": table_values}
    # Формирование запроса к Google Sheets API.
    request = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range="Отпуск 2077!A1:F20",
            valueInputOption="USER_ENTERED",
            body=request_body,
        )
    )
    # Выполнение запроса
    request.execute()


def read_values(service, spreadsheetId):
    range = "Отпуск 2077!A1:F20"
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheetId, range=range)
        .execute()
    )
    return response["values"]


def update_ranges_values(service, spreadsheetId):
    mon_menu = [
        ["Понедельник"],
        ["Салат из свеклы", "100г"],
        ["Борщ", "250гр"],
        ["Плов", "150гр"],
    ]
    mon_range = "Лист1!B1:C4"
    wed_menu = [
        ["Среда"],
        ["Оливье", "100г"],
        ["Куриная лапша", "250гр"],
        ["Спагетти", "150гр"],
    ]
    wed_range = "Лист1!E1:F4"
    fri_menu = [
        ["Пятница"],
        ["Витаминный", "100г"],
        ["Харчо", "250гр"],
        ["Тушеный картофель", "150гр"],
    ]
    fri_range = "Лист1!H1:I4"

    request = (
        service.spreadsheets()
        .values()
        .batchUpdate(
            spreadsheetId=spreadsheetId,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": mon_range, "majorDimension": "ROWS", "values": mon_menu},
                    {"range": wed_range, "majorDimension": "ROWS", "values": wed_menu},
                    {"range": fri_range, "majorDimension": "ROWS", "values": fri_menu},
                ],
            },
        )
    )
    request.execute()


def main() -> None:
    service, credentials = auth()
    spreadsheet_id = create_spreadsheet(service)
    set_user_permissions(spreadsheet_id, credentials)
    spreadsheet_update_values(service, spreadsheet_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
