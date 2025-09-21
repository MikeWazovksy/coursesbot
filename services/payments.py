# services/payments.py

import uuid
from yookassa import Configuration, Payment
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY


async def create_payment(amount: float, description: str, metadata: dict):
    # Создание платежа Юкасса
    idempotence_key = str(uuid.uuid4())

    payment = Payment.create(
        {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/testcourseEe_bot",  # Ссылка на бота или его имя
            },
            "capture": True,
            "description": description,
            "metadata": metadata,
        },
        idempotence_key,
    )

    return payment.confirmation.confirmation_url, payment.id
