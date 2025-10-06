# NFR BDD Scenarios

Документ описывает сценарии приемочного тестирования (BDD) для ключевых нефункциональных требований в формате Gherkin (Given/When/Then).

## NFR-001: Время ответа API

### Сценарий 1: GET запрос возвращается в пределах допустимого времени

```gherkin
Feature: API Response Time Performance
  Как пользователь системы
  Я хочу получать быстрые ответы от API
  Чтобы иметь хороший user experience

  Scenario: GET endpoint responds within acceptable time (p95)
    Given система работает в production режиме
    And база данных содержит 1000 записей features
    When я отправляю 1000 GET запросов к "/api/v1/features"
    Then p95 времени ответа должно быть <= 300ms
    And p99 времени ответа должно быть <= 500ms
    And медианное время ответа (p50) должно быть <= 150ms
```

### Сценарий 2: POST запрос возвращается в пределах допустимого времени

```gherkin
  Scenario: POST endpoint responds within acceptable time (p95)
    Given система работает в production режиме
    And я аутентифицирован как валидный пользователь
    When я отправляю 1000 POST запросов к "/api/v1/features" с валидными данными
    Then p95 времени ответа должно быть <= 500ms
    And p99 времени ответа должно быть <= 800ms
    And количество ошибок должно быть = 0
```

### Сценарий 3 (Негативный): Производительность при высокой нагрузке

```gherkin
  Scenario: API maintains performance under high load
    Given система работает в production режиме
    And текущая нагрузка составляет 80 RPS
    When нагрузка увеличивается до 120 RPS в течение 5 минут
    Then p95 времени ответа должно остаться <= 500ms
    And количество HTTP 5xx ошибок должно быть < 0.1%
    And система не должна падать или становиться недоступной
```

### Сценарий 4 (Негативный): Деградация при перегрузке

```gherkin
  Scenario: Graceful degradation when overloaded
    Given система работает в production режиме
    When нагрузка превышает 200 RPS (2x от допустимой)
    Then система должна возвращать HTTP 429 (Too Many Requests)
    And внутренние сервисы должны оставаться стабильными
    And после снижения нагрузки до 100 RPS система восстанавливается за <= 30 секунд
```

---

## NFR-002: Пропускная способность

### Сценарий 1: Система выдерживает минимальную требуемую нагрузку

```gherkin
Feature: System Throughput Capacity
  Как владелец системы
  Я хочу чтобы система выдерживала ожидаемую нагрузку
  Чтобы обслуживать всех пользователей без деградации

  Scenario: System handles 100 RPS on single instance
    Given система развернута на одной инстанции (2 vCPU, 4GB RAM)
    And база данных доступна и отвечает нормально
    When я генерирую постоянную нагрузку 100 RPS в течение 10 минут
    Then все запросы должны обрабатываться успешно
    And p95 времени ответа должно быть <= 500ms
    And CPU утилизация должна быть <= 80%
    And memory утилизация должна быть <= 75%
```

### Сценарий 2: Масштабирование при росте нагрузки

```gherkin
  Scenario: System scales horizontally with load increase
    Given система развернута с 2 инстанциями
    And load balancer настроен корректно
    When я генерирую нагрузку 200 RPS (100 RPS на инстанцию)
    Then все запросы распределяются равномерно между инстанциями
    And p95 времени ответа должно быть <= 500ms
    And количество ошибок должно быть < 0.1%
```

---

## NFR-004: Время жизни токенов

### Сценарий 1: Access token имеет ограниченное время жизни

```gherkin
Feature: JWT Token Lifetime Management
  Как security инженер
  Я хочу чтобы токены имели короткое время жизни
  Чтобы минимизировать риск компрометации

  Scenario: Access token expires after 15 minutes
    Given пользователь успешно аутентифицировался
    And получил access token с timestamp создания T0
    When проходит 15 минут (T0 + 900 секунд)
    And пользователь пытается использовать access token
    Then система должна вернуть HTTP 401 (Unauthorized)
    And error code должен быть "token_expired"
    And в логах должно быть зафиксировано событие "expired_token_used"
```

### Сценарий 2: Refresh token имеет время жизни 7 дней

```gherkin
  Scenario: Refresh token expires after 7 days
    Given пользователь успешно аутентифицировался
    And получил refresh token с timestamp создания T0
    When проходит 7 дней (T0 + 604800 секунд)
    And пользователь пытается обновить access token используя refresh token
    Then система должна вернуть HTTP 401 (Unauthorized)
    And error code должен быть "refresh_token_expired"
    And пользователь должен пройти аутентификацию заново
```

### Сценарий 3: JWT использует безопасный алгоритм подписи

```gherkin
  Scenario: JWT tokens use secure signing algorithm
    Given пользователь успешно аутентифицировался
    When система генерирует JWT токен
    Then токен должен быть подписан алгоритмом RS256 или ES256
    And заголовок "alg" в JWT должен быть "RS256" или "ES256"
    And токен НЕ должен использовать алгоритм "none" или "HS256"
```

### Сценарий 4 (Негативный): Попытка использовать токен с истекшим сроком

```gherkin
  Scenario: Expired token cannot be used for authentication
    Given пользователь имеет access token созданный 20 минут назад (TTL = 15 мин)
    When пользователь пытается получить доступ к защищенному endpoint "/api/v1/features"
    Then система должна вернуть HTTP 401 (Unauthorized)
    And response body должен содержать {"error": {"code": "token_expired", "message": "Access token has expired"}}
    And запрос НЕ должен быть обработан
    And событие должно быть залогировано с level WARNING
```

### Сценарий 5 (Негативный): Подделанный токен отклоняется

```gherkin
  Scenario: Tampered JWT token is rejected
    Given злоумышленник получил валидный JWT токен
    When злоумышленник изменяет payload токена (например, user_id)
    And пытается использовать измененный токен для доступа к API
    Then система должна вернуть HTTP 401 (Unauthorized)
    And error code должен быть "invalid_signature"
    And событие должно быть залогировано с level ERROR
    And alert должен быть отправлен security team
```

---

## NFR-006: Отказоустойчивость внешних сервисов

### Сценарий 1: Retry логика при временном сбое БД

```gherkin
Feature: Resilience to External Service Failures
  Как SRE инженер
  Я хочу чтобы система была устойчива к временным сбоям
  Чтобы обеспечить надежность сервиса

  Scenario: Database connection retry on transient failure
    Given система работает нормально
    When происходит временный сбой подключения к БД (connection timeout)
    Then система должна автоматически повторить запрос
    And количество попыток должно быть = 3
    And backoff между попытками должен быть экспоненциальным (1s, 2s, 4s)
    And если 3 попытка успешна, запрос завершается успешно
    And общее время retry не должно превышать 10 секунд
```

### Сценарий 2: Таймаут для DB запросов

```gherkin
  Scenario: Database query timeout is enforced
    Given система отправляет запрос к БД
    When запрос выполняется дольше 5 секунд
    Then система должна прервать запрос с timeout exception
    And вернуть клиенту HTTP 503 (Service Unavailable)
    And error message должен быть "database_timeout"
    And событие должно быть залогировано с level ERROR
```

### Сценарий 3: Circuit breaker открывается после множественных ошибок

```gherkin
  Scenario: Circuit breaker opens after consecutive failures
    Given circuit breaker для БД находится в состоянии CLOSED
    When происходит 5 последовательных ошибок при запросах к БД
    Then circuit breaker должен перейти в состояние OPEN
    And все последующие запросы должны немедленно возвращать HTTP 503
    And система НЕ должна пытаться подключиться к БД
    And метрика "circuit_breaker_open" должна быть установлена в 1
```

### Сценарий 4 (Негативный): Circuit breaker восстанавливается

```gherkin
  Scenario: Circuit breaker recovers after cooldown period
    Given circuit breaker находится в состоянии OPEN
    And прошло 60 секунд с момента открытия (cooldown period)
    When circuit breaker переходит в состояние HALF_OPEN
    And следующий запрос к БД выполняется успешно
    Then circuit breaker должен перейти в состояние CLOSED
    And нормальная обработка запросов возобновляется
    And alert "circuit_breaker_recovered" должен быть отправлен
```

### Сценарий 5 (Негативный): Система отклоняет медленные запросы

```gherkin
  Scenario: System rejects requests during database overload
    Given БД перегружена и отвечает медленно (> 5 секунд на запрос)
    When я отправляю 100 запросов к "/api/v1/features"
    Then большинство запросов должны завершиться с HTTP 503 по timeout
    And система НЕ должна накапливать pending соединения
    And memory и CPU утилизация должны оставаться стабильными
    And после восстановления БД система возвращается к нормальной работе
```
