# tgc1_for_home_assistant

Интеграция ТГК-1 для Home Assistant.

Сейчас реализовано:

- двухшаговая авторизация через `https://lk.tgc1.ru/`
- получение `session-cookie` из первичного ответа
- вход через `POST /api/security/auth/login/fl`
- получение списка лицевых счетов через `GET /api/fl/account`
- сохранение `accessToken`, `refreshToken` и `session-cookie` в config entry

Следующий шаг: добавить endpoint'ы с деталями по лицевым счетам и данными для сенсоров.
