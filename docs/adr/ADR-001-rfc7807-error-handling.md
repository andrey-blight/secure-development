# ADR-001: RFC 7807 Error Response Format
Дата: 2025-10-22
Статус: Accepted

## Context
В микросервисной архитектуре критически важно обеспечить стандартизированный формат ошибок для клиентов API. Без единого формата:
- Клиенты не могут предсказуемо обрабатывать ошибки
- Утечка внутренних деталей (stack traces, SQL-запросы) создаёт угрозу безопасности
- Отсутствие корреляционных идентификаторов затрудняет отладку и трейсинг
- Разные типы ошибок требуют разной логики обработки на клиенте

RFC 7807 (Problem Details for HTTP APIs) предоставляет стандартизированный формат, но требует адаптации под требования безопасности и мониторинга.

Варианты:
1. Использовать стандартный JSON с произвольной структурой
2. RFC 7807 с полным раскрытием деталей
3. RFC 7807 с контролируемым маскированием чувствительной информации (выбрано)

## Decision
Все ошибки API возвращаются в формате RFC 7807 с обязательными полями:
- `type`: URI идентификатор типа ошибки (например, `/errors/validation-error`)
- `title`: Краткое человекочитаемое описание типа ошибки
- `status`: HTTP статус код
- `detail`: Маскированное описание конкретного экземпляра ошибки
- `instance`: Уникальный correlation_id для трейсинга запроса

**Карта типов ошибок:**
- `400 Bad Request` → `/errors/validation-error`
- `401 Unauthorized` → `/errors/authentication-required`
- `403 Forbidden` → `/errors/insufficient-permissions`
- `404 Not Found` → `/errors/resource-not-found`
- `429 Too Many Requests` → `/errors/rate-limit-exceeded`
- `500 Internal Server Error` → `/errors/internal-error`

**Правила маскирования:**
- Stack traces логируются на сервере, но НЕ возвращаются клиенту
- SQL-запросы и внутренние пути файловой системы маскируются
- Валидационные ошибки возвращаются в структурированном виде в поле `errors`
- В production все 5xx ошибки возвращают общее сообщение "Internal server error occurred"

**Correlation ID:**
- Генерируется для каждого запроса (middleware уровень)
- Передаётся в заголовке `X-Correlation-ID`
- Включается в поле `instance` ответа об ошибке
- Логируется на всех уровнях для end-to-end трейсинга

## Consequences
**Плюсы:**
- Стандартизированный формат упрощает интеграцию с клиентами
- Маскирование предотвращает информационные утечки (OWASP A01:2021)
- Correlation ID обеспечивает сквозной трейсинг для отладки
- Типизация ошибок позволяет клиентам реализовать умную обработку (retry, fallback)

**Минусы:**
- Дополнительная сложность в middleware для маскирования
- Необходимость поддержки карты типов ошибок
- Разработчики должны учиться работать с новым форматом (DX overhead)

**Компромиссы:**
- Менее детальные сообщения об ошибках в production могут замедлить отладку
- Требуется централизованный логирование для корреляции ошибок
- Небольшое снижение производительности из-за обработки в middleware (~5-10ms на запрос)

## Links
- NFR-03: Error Handling and Observability (RFC 7807 requirement)
- NFR-06: Information Disclosure Prevention
- STRIDE Analysis: F1 (Spoofing), T2 (Tampering via error messages)
- Implementation: `app/api/middleware/error_handler.py`
- Tests: `tests/test_errors.py::test_rfc7807_contract`
- RFC 7807 Spec: https://tools.ietf.org/html/rfc7807
