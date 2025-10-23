# ADR-003: Secrets Management Strategy
Дата: 2025-10-22
Статус: Accepted

## Context
Приложение использует секреты (пароли БД, API ключи, JWT signing keys), которые требуют защиты. Неправильное обращение с секретами создаёт критические риски:
- Hardcoded secrets в коде → утечка через Git history, decompilation
- Секреты в логах → доступны через log aggregation системы
- Отсутствие ротации → компрометация одного секрета даёт перманентный доступ
- Секреты в plaintext → доступны при компрометации сервера/контейнера

Варианты хранения:
1. Hardcoded в коде (категорически неприемлемо)
2. Environment variables (базовый уровень безопасности)
3. Secrets management сервисы (AWS Secrets Manager, HashiCorp Vault)
4. Гибридный подход: env vars для локальной разработки, secrets manager для production (выбрано)

## Decision
Все секреты управляются согласно следующей стратегии:

**Источники секретов (по окружениям):**
- **Local/Development**: `.env` файлы (НЕ коммитятся в Git, добавлены в `.gitignore`)
- **CI/CD**: Encrypted secrets в GitHub Actions / GitLab CI
- **Staging/Production**: Environment variables, инжектируемые из secrets manager
  - Docker Compose: secrets в `secrets` секции
  - Kubernetes: `Secret` resources + RBAC
  - Cloud deployments: AWS Secrets Manager / GCP Secret Manager

**Список секретов:**
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Подписание JWT токенов
- `API_KEY_*`: Ключи для внешних API (если используются)
- `ENCRYPTION_KEY`: Для шифрования чувствительных данных at-rest

**Ротация секретов:**
- JWT keys: автоматическая ротация каждые 90 дней
- Database passwords: ротация каждые 180 дней (manual/automated)
- API keys: согласно политике провайдера (min 365 дней)
- Поддержка grace period: старый и новый секрет валидны одновременно 24 часа

**Запрет утечек:**
1. **В коде:**
   - Pre-commit hook (detect-secrets) сканирует коммиты
   - CI pipeline блокирует merge при обнаружении секретов

2. **В логах:**
   - Маскирование в log formatter: автоматическая замена паттернов (`password=`, `token=`, `key=`)
   - Запрет логирования raw request/response bodies с auth headers
   - Structured logging с explicit allow-list полей

3. **В Git:**
   - `.env`, `.env.*`, `secrets.*` в `.gitignore`
   - GitHub Secret Scanning включён для репозитория
   - Regular audit с `git log -S "password"` для проверки истории

**Загрузка секретов в приложении:**
```python
# app/core/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: SecretStr
    jwt_secret_key: SecretStr

    class Config:
        env_file = ".env"  # только для local dev
        env_file_encoding = "utf-8"
```

**Конфигурация:**
- `SECRETS_SOURCE`: "env" | "aws" | "vault" (по умолчанию "env")
- `SECRETS_AUTO_RELOAD`: автоматическая перезагрузка при ротации (default: false)

## Consequences
**Плюсы:**
- Предотвращение утечек секретов через Git, логи, error messages
- Автоматическая ротация снижает impact компрометации секрета
- Гибридный подход обеспечивает balance между security и DX
- Pre-commit hooks предотвращают случайные коммиты секретов

**Минусы:**
- Дополнительная инфраструктура для secrets manager в production
- Сложность setup для новых разработчиков (требуется инициализация .env)
- Ротация секретов требует координации и потенциально downtime

**Компромиссы:**
- Env variables в development: удобно для разработчиков, но менее безопасно
- Автоматическая ротация: повышает безопасность, но усложняет debugging при ошибках (expired secrets)
- Маскирование в логах: защищает секреты, но может скрыть полезную информацию для отладки

**Стоимость:**
- AWS Secrets Manager: ~$0.40/secret/month + $0.05/10k API calls
- Разработка и поддержка ротации: ~8-16 hours initially
- CI/CD overhead: +10-20 секунд на проверку secrets в pipeline

**Влияние на DX:**
- Initial setup: 10-15 минут (копирование .env.example, заполнение значений)
- Onboarding documentation требуется для новых разработчиков
- Потенциальные ошибки "secret not found" при неправильной конфигурации

## Links
- NFR-05: Secrets Management and Rotation
- NFR-06: Information Disclosure Prevention
- STRIDE Analysis: I1 (Information Disclosure via logs/code)
- Threat Model: E1 (Elevation of Privilege via leaked credentials)
- OWASP: A07:2021 – Identification and Authentication Failures
- Implementation: `app/core/settings.py`, `.gitignore`
- Pre-commit config: `.pre-commit-config.yaml`
- Tools: detect-secrets, git-secrets, GitHub Secret Scanning
