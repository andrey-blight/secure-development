# Non-Functional Requirements (NFR)

Документ описывает измеримые и проверяемые нефункциональные требования к системе.

## Таблица NFR

| ID | Название | Описание | Метрика/Порог | Проверка (чем/где) | Компонент | Приоритет |
|----|----------|----------|---------------|-------------------|-----------|-----------|
| NFR-001 | Время ответа API | API должен возвращать ответ в пределах приемлемого времени для обеспечения хорошего UX | p95 ≤ 300ms для GET-запросов<br>p95 ≤ 500ms для POST/PUT/DELETE | Load testing: Locust/k6<br>Мониторинг: Prometheus + Grafana<br>APM: FastAPI middleware с логированием времени запросов | API Gateway, Backend Service | HIGH |
| NFR-002 | Пропускная способность | Система должна выдерживать ожидаемую нагрузку без деградации производительности | Минимум 100 RPS на одну инстанцию<br>При 100 RPS: p95 ≤ 500ms | Load testing: k6/Locust с постепенным увеличением нагрузки<br>CI/CD: Performance tests в pipeline | Backend Service, Database | HIGH |
| NFR-003 | Уровень ошибок | Система должна быть надежной и минимизировать количество ошибок | HTTP 5xx ≤ 0.1% от всех запросов<br>HTTP 4xx ≤ 5% от всех запросов | Мониторинг: Prometheus counter metrics<br>Alerting: Alert при превышении порога<br>Логирование: ELK/Loki для анализа | Все API endpoints | CRITICAL |
| NFR-004 | Время жизни токенов | JWT токены должны иметь ограниченное время жизни для минимизации риска компрометации | Access Token TTL ≤ 15 минут<br>Refresh Token TTL ≤ 7 дней<br>Использование alg=RS256 или ES256 | Code review: проверка settings<br>Integration tests: проверка истечения токенов<br>Security audit: проверка JWT claims и алгоритмов | Authentication Service | HIGH |
| NFR-005 | Управление уязвимостями | Критические уязвимости должны устраняться в установленные сроки | High уязвимости: устранение ≤ 7 дней с момента обнаружения<br>Critical уязвимости: устранение ≤ 24 часа с момента обнаружения | Dependency scanning: pip-audit, Safety, Dependabot<br>CI/CD: автоматический scan в pipeline<br>SAST/DAST: Semgrep, Bandit<br>Трекинг: GitHub Security Advisories | Dependencies, Application Code | CRITICAL |
| NFR-006 | Отказоустойчивость внешних сервисов | Запросы к внешним сервисам должны быть защищены от сбоев и таймаутов | Retry policy:<br>• max_retries = 3<br>• backoff_factor = 2<br>• timeout ≤ 1 секуны для внешних API<br>• timeout ≤ 5 секунд для DB запросов<br>Circuit breaker: open после 5 последовательных ошибок | Unit tests: mock внешних сервисов<br>Integration tests: тестирование retry логики<br>Chaos engineering: fault injection tests | External API Client, Database Client | HIGH |
| NFR-007 | Ротация секретов | Критичные секреты должны регулярно обновляться для снижения риска утечки | SLA для ротации:<br>• DB credentials: ротация каждые 90 дней<br>• JWT signing keys: ротация каждые 180 дней<br>• API keys: ротация каждые 90 дней<br>• Автоматическое оповещение за 7 дней до истечения | Vault/Secret Manager: AWS Secrets Manager / HashiCorp Vault<br>Alerting: автоматические уведомления<br>Audit log: логирование ротаций<br>Runbook: документация процедуры | Secrets Management, Infrastructure | HIGH |
| NFR-008 | Логирование и аудит | Критичные события должны логироваться для анализа безопасности и отладки | Логирование:<br>• 100% аутентификационных событий<br>• 100% авторизационных отказов<br>• 100% изменений данных (audit trail)<br>• Retention: ≥ 90 дней<br>• Log level: INFO для prod, DEBUG для dev | Code review: проверка logging statements<br>Log aggregation: ELK/Loki/CloudWatch<br>SIEM: корреляция событий безопасности<br>Compliance: соответствие требованиям аудита | Logging Module, All Services | HIGH |

## Категории приоритетов

- **CRITICAL** — требования, критичные для безопасности и работоспособности системы. Нарушение ведет к серьезным последствиям.
- **HIGH** — важные требования, влияющие на производительность, надежность и UX. Должны быть выполнены для production-ready системы.
- **MEDIUM** — желательные требования, улучшающие качество системы.
- **LOW** — опциональные улучшения, не критичные для первых релизов.
