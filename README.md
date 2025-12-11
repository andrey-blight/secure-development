# SecDev Course Template

Стартовый шаблон для студенческого репозитория (HSE SecDev 2025).

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
uvicorn app.main:app --reload
```

## Ритуал перед PR
```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## Тесты
```bash
pytest -q
```

## CI
В репозитории настроен workflow **CI** (GitHub Actions) — required check для `main`.
Badge добавится автоматически после загрузки шаблона в GitHub.

## Контейнеры
```bash
docker build -t secdev-app .
docker run --rm -p 8000:8000 secdev-app
# или
docker compose up --build
```

## Эндпойнты
- `GET /health` → `{"status": "ok"}`
- `POST /items?name=...` — демо-сущность
- `GET /items/{id}`

## Формат ошибок
Все ошибки — JSON-обёртка:
```json
{
  "error": {"code": "not_found", "message": "item not found"}
}
```

## Security: SBOM & SCA (P09)

Автоматическая генерация SBOM и сканирование уязвимостей зависимостей.

### Артефакты (`EVIDENCE/P09/`)

| Файл | Описание |
|------|----------|
| `sbom.json` | Software Bill of Materials (CycloneDX JSON) — полный список зависимостей |
| `sca_report.json` | Детальный отчёт SCA от Grype — все найденные уязвимости |
| `sca_summary.md` | Агрегированная сводка: счётчики по severity, список Critical/High, план действий |

### Инструменты

- **SBOM**: [Syft](https://github.com/anchore/syft) v0.17.8
- **SCA**: [Grype](https://github.com/anchore/grype) v5.3.0

### Политика исключений

Файл `policy/waivers.yml` содержит документированные исключения для уязвимостей, которые не могут быть исправлены немедленно. См. SLA:
- Critical: фикс в течение 7 дней
- High: фикс в течение 30 дней или waiver
- Medium: фикс в течение 90 дней

### Запуск

Workflow запускается автоматически при изменениях в `requirements*.txt`, `**/*.py`, или вручную через Actions → `Security - SBOM & SCA` → Run workflow.

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
