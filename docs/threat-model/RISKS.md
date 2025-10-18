# Risk Register (Реестр рисков)

Документ содержит реестр рисков информационной безопасности с оценкой вероятности, влияния и стратегиями митигации.

## Реестр рисков

| RiskID | Описание | Связь (F/NFR) | L | I | Risk | Стратегия | Владелец | Срок | Критерий закрытия |
|--------|----------|---------------|---|---|------|-----------|----------|------|-------------------|
| R1 | **JWT Token Spoofing**: использование украденного/поддельного токена для доступа от чужого имени | F1, F2, NFR-004 | 3 | 4 | **12** | Снизить | @security-team | 2025-10-25 | ✅ JWT использует RS256/ES256<br>✅ TTL = 15 мин<br>✅ Тесты: `test_expired_token_rejected`, `test_invalid_signature_rejected` |
| R2 | **Denial of Service**: массовые запросы перегружают систему и делают её недоступной | F1, F7, NFR-002, NFR-003 | 4 | 3 | **12** | Снизить | @devops-team | 2025-10-30 | ✅ Rate limiting: 100 RPS<br>✅ Load testing: k6 в CI<br>✅ Метрика: HTTP 5xx ≤ 0.1% |
| R3 | **Elevation of Privilege**: обход JWT валидации для получения расширенных прав | F2, F15, NFR-004 | 2 | 5 | **10** | Снизить | @backend-team | 2025-10-27 | ✅ Валидация JWT claims (exp, iat, iss)<br>✅ Запрет алгоритма "none"<br>✅ SAST: Bandit/Semgrep в CI |
| R4 | **SQL Injection**: внедрение SQL кода через параметры для доступа к БД | F4, F10, NFR-005 | 3 | 5 | **15** | Снизить | @backend-team | 2025-10-28 | ✅ ORM (SQLAlchemy) для всех запросов<br>✅ Pydantic валидация входных данных<br>✅ Тесты: `test_sql_injection_prevention`<br>✅ SAST: Semgrep SQL injection rules |
| R5 | **Information Disclosure**: утечка структуры БД и данных через error messages | F4, F5, NFR-008 | 3 | 3 | **9** | Снизить | @backend-team | 2025-11-01 | ✅ Generic error responses (RFC7807)<br>✅ Exception handling без stack traces<br>✅ Тесты: `test_error_responses_sanitized` |
| R6 | **Credential Stuffing**: брутфорс /login с использованием украденных credentials | F8, F9, NFR-008 | 4 | 4 | **16** | Снизить | @security-team | 2025-10-26 | ✅ Rate limit на /login: 5 req/min<br>✅ Логирование failed auth (100%)<br>✅ Тесты: `test_rate_limit_on_login`<br>✅ Alert при >10 failed logins за 5 мин |
| R7 | **Credentials in Transit**: перехват credentials при передаче по незащищённому каналу | F8, F13, NFR-004 | 2 | 5 | **10** | Снизить | @devops-team | 2025-10-22 | ✅ Обязательный HTTPS/TLS 1.3<br>✅ HSTS header включён<br>✅ DAST: ZAP baseline в CI<br>✅ Тесты: `test_https_enforced` |
| R8 | **Repudiation**: отрицание факта входа или выполнения действий | F9, F15, NFR-008 | 2 | 3 | **6** | Снизить | @backend-team | 2025-11-05 | ✅ Audit log всех auth событий<br>✅ Логи содержат: timestamp, user_id, IP, user-agent<br>✅ Retention ≥ 90 дней<br>✅ Тесты: `test_audit_trail_completeness` |
| R9 | **Database Unavailable**: сбой БД делает систему неработоспособной | F4, F5, F10, F11, NFR-006 | 3 | 4 | **12** | Снизить | @devops-team | 2025-11-03 | ✅ Retry policy: 3 attempts, backoff<br>✅ Circuit breaker после 5 ошибок<br>✅ Timeout: 5s для DB запросов<br>✅ Тесты: `test_db_retry_logic`, chaos tests |
| R10 | **Unauthorized DB Modification**: компрометация DB credentials для прямого доступа к данным | PostgreSQL, NFR-007 | 2 | 5 | **10** | Снизить | @devops-team | 2025-11-10 | ✅ Ротация DB credentials каждые 90 дней<br>✅ Least privilege для DB user<br>✅ Secret scanning: detect-secrets в CI<br>✅ Secrets в Vault/env, не в коде |
| R11 | **Dependency Vulnerabilities**: критические уязвимости в FastAPI/SQLAlchemy/PostgreSQL | All components, NFR-005 | 3 | 4 | **12** | Снизить | @security-team | 2025-11-01 | ✅ pip-audit/Safety в CI<br>✅ Dependabot alerts enabled<br>✅ Critical: fix ≤ 24h, High: ≤ 7d<br>✅ Автоматические PR для обновлений |
| R12 | **Unvalidated Input**: XSS, command injection через некорректную валидацию пользовательского ввода | F1, F3, NFR-005 | 3 | 3 | **9** | Снизить | @backend-team | 2025-10-29 | ✅ Pydantic schemas для всех endpoints<br>✅ Input sanitization<br>✅ Content-Type validation<br>✅ Тесты: `test_input_validation` с malicious payloads |

## Матрица рисков (Heat Map)

```
Impact (I)
  5 |           R3    R4    R7   R10
  4 |     R1    R2              R9   R11
  3 |                 R5   R8   R12
  2 |
  1 |
    +----------------------------------
      1    2    3    4    5
              Likelihood (L)
```

**Критичные риски (≥15):** R4
**Высокие риски (10-16):** R1, R2, R3, R6, R7, R9, R10, R11
**Средние риски (5-9):** R5, R8, R12

## Стратегии обработки рисков

| Стратегия | Риски | Описание |
|-----------|-------|----------|
| **Снизить** (Mitigate) | R1-R12 | Реализовать контрольные меры для уменьшения вероятности или влияния риска |
| **Избежать** (Avoid) | - | Не применимо для текущих рисков |
| **Перенести** (Transfer) | - | Страхование, SLA с провайдерами (не применимо для учебного проекта) |
| **Принять** (Accept) | - | Остаточные риски после митигации |

## Владельцы рисков

| Команда | Ответственность | Риски |
|---------|-----------------|-------|
| **@security-team** | Аутентификация, авторизация, мониторинг угроз | R1, R3, R6, R11 |
| **@backend-team** | Разработка API, валидация данных, бизнес-логика | R3, R4, R5, R8, R12 |
| **@devops-team** | Инфраструктура, доступность, секреты | R2, R7, R9, R10 |

## Критерии закрытия (Acceptance Criteria)

### R1: JWT Token Spoofing
- [x] JWT подписывается алгоритмом RS256 или ES256
- [x] Access token TTL = 15 минут (реализовано в `app.core.settings`)
- [ ] Integration tests: `test_expired_token_rejected`, `test_invalid_signature_rejected`
- [ ] Code review: валидация JWT в middleware

### R2: Denial of Service
- [ ] Rate limiting middleware реализован (100 RPS)
- [ ] Load testing в CI: k6 script проверяет 100+ RPS
- [ ] Prometheus metrics: `http_requests_total`, `http_request_duration_seconds`
- [ ] Alert rule: `rate(http_errors_5xx[5m]) > 0.001` (0.1%)

### R3: Elevation of Privilege
- [ ] JWT validation проверяет: `exp`, `iat`, `iss`, `aud`
- [ ] Алгоритм "none" явно запрещён в JWT library config
- [ ] SAST в CI: Bandit, Semgrep с правилами для JWT
- [ ] Unit tests: `test_jwt_none_algorithm_rejected`

### R4: SQL Injection
- [x] SQLAlchemy ORM используется для всех DB запросов
- [x] Pydantic schemas валидируют все входные данные
- [ ] Запрет сырых SQL запросов (`.execute()` только с parameters)
- [ ] SAST: Semgrep rule `python.sqlalchemy.security.sqlalchemy-execute-raw-query`
- [ ] Тесты: `test_sql_injection_attempts` с OWASP payloads

### R5: Information Disclosure
- [ ] Generic error responses: HTTP 400/401/403/404/500 без stack traces
- [ ] RFC7807 Problem Details для ошибок
- [ ] Exception handler не раскрывает внутренние детали
- [ ] Тесты: `test_error_responses_no_sensitive_info`

### R6: Credential Stuffing
- [ ] Rate limiter на POST /auth/login: 5 requests/minute per IP
- [ ] Logging всех failed authentication attempts
- [ ] Alert в мониторинге: >10 failed logins за 5 минут
- [ ] Тесты: `test_rate_limit_on_login_endpoint`

### R7: Credentials in Transit
- [ ] HTTPS/TLS 1.3 обязателен (redirect HTTP → HTTPS)
- [ ] HSTS header: `Strict-Transport-Security: max-age=31536000`
- [ ] DAST: OWASP ZAP baseline scan в CI
- [ ] Тесты: `test_hsts_header_present`, `test_tls_version`

### R8: Repudiation
- [ ] Audit log для auth events: login success, login failed, token refresh
- [ ] Log format: `{"timestamp": "...", "event": "login", "user_id": "...", "ip": "...", "user_agent": "..."}`
- [ ] Log retention: ≥ 90 дней
- [ ] Тесты: `test_login_events_logged`

### R9: Database Unavailable
- [ ] Retry decorator на DB operations: `@retry(tries=3, delay=1, backoff=2)`
- [ ] Circuit breaker pattern реализован
- [ ] DB query timeout: 5 секунд
- [ ] Health check endpoint: `/health` проверяет DB connectivity
- [ ] Chaos tests: simulate DB failure

### R10: Unauthorized DB Modification
- [ ] DB credentials в environment variables (не в коде)
- [ ] Secret scanning в CI: `detect-secrets`, `git-secrets`
- [ ] Ротация credentials: reminder каждые 90 дней
- [ ] DB user с минимальными привилегиями (no DROP, no ALTER)

### R11: Dependency Vulnerabilities
- [x] Dependabot enabled в GitHub
- [ ] CI job: `pip-audit` или `safety check`
- [ ] Policy: Critical vulnerabilities fix ≤ 24 hours
- [ ] Policy: High vulnerabilities fix ≤ 7 days
- [ ] Автоматические dependency update PRs

### R12: Unvalidated Input
- [x] Pydantic BaseModel для всех request/response schemas
- [ ] Whitelist validation (не blacklist)
- [ ] Content-Type validation в middleware
- [ ] Тесты: `test_malicious_input_rejected` с XSS/injection payloads

## Трекинг прогресса

| Риск | Статус | Прогресс | Последнее обновление |
|------|--------|----------|----------------------|
| R1 | 🟡 In Progress | 50% (2/4 критериев) | 2025-10-18 |
| R2 | 🔴 Not Started | 0% (0/4) | - |
| R3 | 🔴 Not Started | 0% (0/4) | - |
| R4 | 🟡 In Progress | 40% (2/5) | 2025-10-18 |
| R5 | 🔴 Not Started | 0% (0/4) | - |
| R6 | 🔴 Not Started | 0% (0/4) | - |
| R7 | 🔴 Not Started | 0% (0/4) | - |
| R8 | 🔴 Not Started | 0% (0/4) | - |
| R9 | 🔴 Not Started | 0% (0/5) | - |
| R10 | 🔴 Not Started | 0% (0/4) | - |
| R11 | 🟡 In Progress | 25% (1/4) | 2025-10-18 |
| R12 | 🟡 In Progress | 33% (1/3) | 2025-10-18 |

**Легенда:**
🟢 Completed | 🟡 In Progress | 🔴 Not Started | ⚠️ Blocked

## Остаточные риски (Residual Risks)

После реализации всех контрольных мер остаются следующие риски:

| Риск | L | I | Risk | Обоснование | Стратегия |
|------|---|---|------|-------------|-----------|
| **Zero-Day в зависимостях** | 1 | 5 | 5 | Невозможно предотвратить неизвестные уязвимости | **Принять** + мониторинг CVE |
| **Insider Threat** | 1 | 4 | 4 | Доверенные разработчики с доступом к production | **Принять** + audit logs + code review |
| **Social Engineering** | 2 | 4 | 8 | Фишинг пользователей вне контроля приложения | **Принять** + security awareness (будущее) |

## Приоритизация работ

### Критический приоритет (срок: до 2025-10-28)
1. **R4** — SQL Injection (Risk=15)
2. **R6** — Credential Stuffing (Risk=16)
3. **R7** — Credentials in Transit (Risk=10)

### Высокий приоритет (срок: до 2025-11-03)
4. **R1** — JWT Token Spoofing
5. **R2** — Denial of Service
6. **R9** — Database Unavailable

### Средний приоритет (срок: до 2025-11-10)
7. **R3** — Elevation of Privilege
8. **R10** — Unauthorized DB Modification
9. **R11** — Dependency Vulnerabilities

### Низкий приоритет (срок: до 2025-11-15)
10. **R5** — Information Disclosure
11. **R8** — Repudiation
12. **R12** — Unvalidated Input
