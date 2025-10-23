# ADR-002: HTTP Client Resilience Policies
Дата: 2025-10-22
Статус: Accepted

## Context
Микросервисы часто взаимодействуют с внешними API (сторонние сервисы, другие микросервисы). Без контроля исходящих HTTP-запросов возникают риски:
- Cascading failures: сбой одного сервиса может парализовать всю систему
- Resource exhaustion: зависшие запросы потребляют connections, memory, threads
- Denial of Service: отсутствие таймаутов может привести к исчерпанию ресурсов
- Непредсказуемое поведение: транзиентные ошибки (network glitches) требуют retry логики

Варианты:
1. Полагаться на дефолтные настройки HTTP-клиента (небезопасно)
2. Настраивать таймауты и retry индивидуально для каждого запроса (неконсистентно)
3. Централизованная политика с разумными дефолтами и переопределением при необходимости (выбрано)

## Decision
Все исходящие HTTP-запросы используют `httpx.AsyncClient` с обязательными resilience policies:

**Таймауты (httpx.Timeout):**
- `connect`: 5 секунд (время на установку соединения)
- `read`: 10 секунд (время на чтение ответа)
- `write`: 5 секунд (время на отправку запроса)
- `pool`: 10 секунд (время ожидания свободного соединения из пула)

**Connection Pooling:**
- `max_connections`: 100 (общий лимит соединений)
- `max_keepalive_connections`: 20 (keep-alive соединений)
- `keepalive_expiry`: 30 секунд

**Retry Policy (tenacity):**
- Автоматические retry для HTTP 5xx и network errors (ConnectionError, TimeoutError)
- Стратегия: exponential backoff с jitter
- Параметры:
  - `max_attempts`: 3 (включая первую попытку)
  - `initial_wait`: 1 секунда
  - `max_wait`: 10 секунд
  - `multiplier`: 2 (1s → 2s → 4s)
- НЕ ретраим: 4xx ошибки (client errors), успешные ответы

**Circuit Breaker (опционально для критичных зависимостей):**
- `failure_threshold`: 5 ошибок
- `timeout`: 60 секунд (время в состоянии "open")
- `half_open_max_calls`: 3 (попыток проверки восстановления)

**Конфигурация:**
Параметры настраиваются через environment variables:
```
HTTP_CLIENT_CONNECT_TIMEOUT=5
HTTP_CLIENT_READ_TIMEOUT=10
HTTP_CLIENT_MAX_RETRIES=3
HTTP_CLIENT_BACKOFF_MULTIPLIER=2
```

## Consequences
**Плюсы:**
- Предотвращение cascading failures и resource exhaustion
- Автоматическое восстановление от транзиентных ошибок (improved reliability)
- Предсказуемое время отклика: запрос не зависнет на неопределённое время
- Защита от медленных/неотвечающих upstream сервисов (DoS mitigation)

**Минусы:**
- Увеличение сложности конфигурации и тестирования
- Дополнительная латентность из-за retry (в случае ошибок)
- Circuit breaker требует state management (память/Redis для distributed setup)

**Компромиссы:**
- Короткие таймауты улучшают responsiveness, но могут приводить к ложным ошибкам при медленных сетях
- Retry увеличивает resilience, но может создавать дополнительную нагрузку на upstream
- Конфигурация через env vars улучшает flexibility, но усложняет debugging (требуется проверка конфигурации)

**Влияние на производительность:**
- Overhead от retry middleware: ~1-2ms на запрос
- Потенциальная задержка при retry: до 15 секунд (1s + 2s + 4s + processing)
- Снижение memory footprint за счёт connection pooling

## Links
- NFR-04: Resilience and Fault Tolerance
- NFR-07: Availability (99.9% uptime requirement)
- STRIDE Analysis: D1 (Denial of Service via resource exhaustion)
- Threat Model: R2 (Repudiation - logging retry attempts)
- Implementation: `app/db/session.py`
- Related patterns: Circuit Breaker, Bulkhead Isolation
