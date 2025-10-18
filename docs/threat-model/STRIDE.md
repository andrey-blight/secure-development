# STRIDE Threat Analysis

Документ содержит анализ угроз по методологии STRIDE для ключевых потоков данных и компонентов системы.

## Анализ угроз

| Поток/Элемент | Угроза (STRIDE) | Риск | Описание угрозы | Контроль | Ссылка на NFR | Проверка/Артефакт |
|---------------|------------------|------|-----------------|----------|---------------|-------------------|
| **F1** (User → API) | **S**: Spoofing Identity | R1 | Злоумышленник может использовать украденный или подделанный JWT токен для доступа от имени другого пользователя | JWT с подписью RS256/ES256, короткий TTL (15 мин), валидация подписи на каждом запросе | NFR-004 | Integration tests: `test_expired_token_rejected`, `test_invalid_signature_rejected` |
| **F1** (User → API) | **D**: Denial of Service | R2 | Массовые запросы могут перегрузить систему и сделать её недоступной для легитимных пользователей | Rate limiting (100 RPS), timeout на запросы, мониторинг нагрузки | NFR-002, NFR-003 | Load testing: k6/Locust с проверкой 100+ RPS, метрики Prometheus |
| **F2** (API → Auth) | **E**: Elevation of Privilege | R3 | Уязвимость в логике валидации JWT может позволить получить доступ с расширенными правами | Строгая валидация JWT claims (exp, iat, iss), проверка ролей, запрет алгоритма "none" | NFR-004 | Unit tests: `test_jwt_validation_logic`, SAST: Bandit/Semgrep для проверки JWT |
| **F4** (Logic → DB) | **T**: SQL Injection | R4 | Злоумышленник может внедрить SQL код через параметры запроса и получить/изменить данные БД | Использование ORM (SQLAlchemy), параметризованные запросы, input validation | NFR-005 | SAST: Bandit, Semgrep rules для SQL injection, pytest с malicious inputs |
| **F4** (Logic → DB) | **I**: Information Disclosure | R5 | Ошибки SQL могут раскрывать структуру БД и конфиденциальные данные в логах | Обработка исключений, generic error messages для клиента, sanitize логов | NFR-008 | Code review: проверка exception handlers, unit tests для error responses |
| **F8** (User → API /login) | **S**: Credential Stuffing | R6 | Атакующий использует украденные пары логин/пароль с других сервисов для попытки входа | Rate limiting на `/login` (5 попыток/мин), CAPTCHA после 3 неудачных попыток, логирование всех попыток | NFR-008 | Integration tests: `test_rate_limit_on_login`, мониторинг логов failed auth |
| **F8** (User → API /login) | **I**: Credentials in Transit | R7 | Перехват credentials при передаче по незащищенному каналу | Обязательный HTTPS/TLS 1.3, HSTS header, отказ от HTTP | NFR-004 | Integration tests: проверка TLS, DAST: ZAP baseline scan для SSL/TLS |
| **F9** (API → Auth) | **R**: Repudiation | R8 | Пользователь может отрицать факт входа или выполнения действий | Audit logging всех authentication событий (success/failure) с timestamp, user_id, IP, user-agent | NFR-008 | Code review: проверка logging statements, pytest для audit trail |
| **F10** (Auth → DB) | **D**: Database Unavailable | R9 | Сбой БД или сетевые проблемы могут сделать невозможным аутентификацию и работу системы | Retry policy (3 попытки с backoff), timeout (5s), circuit breaker, health checks | NFR-006 | Unit tests: mock DB failures, chaos engineering: fault injection |
| **PostgreSQL DB** | **T**: Unauthorized Data Modification | R10 | Компрометация credentials БД позволяет изменять данные напрямую в обход приложения | Least privilege для DB user, регулярная ротация credentials (90 дней), network isolation, audit logging | NFR-007 | Secret scanning: detect-secrets, Vault integration, DB audit logs review |

## Матрица рисков

| Риск ID | Приоритет | Вероятность | Воздействие | Статус |
|---------|-----------|-------------|-------------|--------|
| R1 | HIGH | Medium | High | Mitigated (NFR-004) |
| R2 | HIGH | High | Medium | Mitigated (NFR-002, NFR-003) |
| R3 | CRITICAL | Low | Critical | Mitigated (NFR-004) |
| R4 | CRITICAL | Medium | Critical | Mitigated (NFR-005) |
| R5 | MEDIUM | Medium | Medium | Mitigated (NFR-008) |
| R6 | HIGH | High | High | Mitigated (NFR-008) |
| R7 | CRITICAL | Medium | Critical | Mitigated (NFR-004) |
| R8 | MEDIUM | Low | Medium | Mitigated (NFR-008) |
| R9 | HIGH | Medium | High | Mitigated (NFR-006) |
| R10 | CRITICAL | Low | Critical | Mitigated (NFR-007) |

## Связь STRIDE категорий с компонентами

| Компонент | S | T | R | I | D | E |
|-----------|---|---|---|---|---|---|
| **API (FastAPI)** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Auth Service** | ✓ | - | ✓ | ✓ | - | ✓ |
| **Business Logic** | - | ✓ | - | ✓ | - | - |
| **PostgreSQL DB** | - | ✓ | ✓ | ✓ | ✓ | - |

## Детальное описание контролей

### R1: JWT Token Spoofing
**Контроль:**
- Использование асимметричной криптографии (RS256/ES256)
- Валидация подписи на каждом запросе
- Проверка claims: `exp` (expiration), `iat` (issued at), `iss` (issuer)
- TTL = 15 минут для минимизации окна компрометации

**Проверка:**
```python
# tests/test_auth.py
def test_expired_token_rejected():
    token = create_expired_token()
    response = client.get("/api/v1/features", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_expired"
```

### R2: Denial of Service
**Контроль:**
- Rate limiting: максимум 100 RPS на инстанцию
- Request timeout: 5 секунд для DB запросов
- Мониторинг метрик: HTTP 5xx должно быть ≤ 0.1%

**Проверка:**
- Load testing: k6/Locust скрипты в CI/CD
- Prometheus alerts при превышении порогов

### R4: SQL Injection
**Контроль:**
- ORM (SQLAlchemy) для построения запросов
- Параметризованные запросы, запрет конкатенации SQL
- Input validation на уровне Pydantic schemas

**Проверка:**
```python
# SAST: Bandit rule B608
def test_sql_injection_prevention():
    malicious_input = "'; DROP TABLE users; --"
    response = client.get(f"/api/v1/features?name={malicious_input}")
    # Должен вернуть 400 или пустой результат, но не выполнить SQL injection
    assert response.status_code in [200, 400]
```

### R6: Credential Stuffing on /login
**Контроль:**
- Rate limiting: 5 попыток входа в минуту с одного IP
- Логирование всех неудачных попыток аутентификации
- Alert при подозрительной активности (>10 failed logins за 5 минут)

**Проверка:**
```python
# tests/test_auth.py
def test_rate_limit_on_login():
    for i in range(6):
        response = client.post("/auth/login", json={"username": "test", "password": "wrong"})
    assert response.status_code == 429  # Too Many Requests
```

### R9: Database Circuit Breaker
**Контроль:**
- Retry policy: 3 попытки с exponential backoff (1s, 2s, 4s)
- Circuit breaker: открывается после 5 последовательных ошибок
- Health check endpoint для мониторинга состояния БД

**Проверка:**
```python
# tests/test_resilience.py
def test_db_retry_on_transient_failure(mock_db):
    mock_db.side_effect = [ConnectionError, ConnectionError, {"id": 1}]  # Fail twice, succeed
    result = repository.get_feature(1)
    assert result["id"] == 1
    assert mock_db.call_count == 3
```

## Артефакты для проверки

| Тип проверки | Инструмент | Что проверяет | Связь с рисками |
|--------------|------------|---------------|-----------------|
| **Unit Tests** | pytest | Логика валидации, обработка ошибок, retry policy | R1, R3, R5, R9 |
| **Integration Tests** | pytest + TestClient | E2E flow аутентификации, rate limiting | R1, R2, R6, R8 |
| **Load Testing** | k6 / Locust | Производительность, DoS устойчивость | R2 |
| **SAST** | Bandit, Semgrep | SQL injection, JWT vulnerabilities, hardcoded secrets | R3, R4, R10 |
| **DAST** | OWASP ZAP | SSL/TLS configuration, common web vulnerabilities | R7 |
| **Dependency Scan** | pip-audit, Safety | Known vulnerabilities in dependencies | R4, R10 |
| **Secret Scanning** | detect-secrets, git-secrets | Hardcoded credentials, API keys | R10 |
| **Linting** | ruff, pylint | Code quality, security anti-patterns | R4, R5 |

## Остаточные риски

| Риск | Описание | Причина | Митигация |
|------|----------|---------|-----------|
| **Insider Threat** | Разработчик с доступом к production может скомпрометировать систему | Доверие к команде, сложность технического контроля | Code review, audit logs, принцип least privilege |
| **Zero-Day в зависимостях** | Неизвестная уязвимость в FastAPI/SQLAlchemy/PostgreSQL | Зависимость от третьих сторон | Регулярные обновления (NFR-005), мониторинг CVE, WAF |
| **Social Engineering** | Фишинг для получения credentials пользователей | Человеческий фактор | Security awareness training, MFA (будущее улучшение) |
