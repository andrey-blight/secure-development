# P12 - Hardening Summary

## Overview

Этот документ описывает меры по защите контейнера и инфраструктуры, реализованные в проекте SecDev Course App.

## Dockerfile Hardening

### До/После сравнение

| Аспект | До | После |
|--------|-----|--------|
| Base Image | `python:latest` | `python:3.11-slim@sha256:...` (pinned digest) |
| User | root (default) | non-root user `app` (UID 1000) |
| Build | single stage | multi-stage build |
| Packages | full install | `--no-install-recommends` + cleanup |
| Health | none | HEALTHCHECK instruction |

### Реализованные меры

1. **Фиксированная версия образа с digest**
   ```dockerfile
   FROM python:3.11-slim@sha256:e4676722fba839e2e5cdb844a52262b43e90e56dbd55b7ad953ee3615ad7534f
   ```
   - Защита от supply chain атак
   - Воспроизводимые сборки

2. **Non-root пользователь**
   ```dockerfile
   RUN groupadd -r app && \
       useradd -r -g app --home-dir=/app --shell=/sbin/nologin app
   USER app
   ```
   - Минимальные привилегии
   - Ограничение доступа к системным ресурсам

3. **Multi-stage build**
   - Уменьшение размера образа
   - Исключение build-зависимостей из финального образа
   - Снижение поверхности атаки

4. **Минимизация пакетов**
   ```dockerfile
   apt-get install -y --no-install-recommends
   rm -rf /var/lib/apt/lists/*
   apt-get clean
   ```

5. **HEALTHCHECK**
   ```dockerfile
   HEALTHCHECK --interval=60s --timeout=1s --start-period=60s --retries=3 \
       CMD curl -f http://localhost:8000/health || exit 1
   ```

6. **Правильные права на файлы**
   ```dockerfile
   COPY --chown=app:app app ./app
   ```

## Docker Compose Hardening

### Реализованные меры

1. **Security Options**
   ```yaml
   security_opt:
     - no-new-privileges:true
     - apparmor=docker-default
     - seccomp=./seccomp-profile.json
   ```

2. **Capabilities**
   ```yaml
   cap_drop:
     - ALL
   cap_add:
     - NET_BIND_SERVICE
     - CHOWN
     - SETGID
     - SETUID
   ```

3. **Read-only Filesystem**
   ```yaml
   read_only: true
   tmpfs:
     - /tmp:rw,noexec,nosuid,size=100m
   ```

4. **Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 1G
   ```

5. **Конфигурация через переменные окружения**
   - Все секреты передаются через переменные
   - Нет hardcoded значений в образе

## Kubernetes IaC Hardening

### Реализованные меры

1. **Pod Security Context**
   ```yaml
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
     seccompProfile:
       type: RuntimeDefault
   ```

2. **Container Security Context**
   ```yaml
   securityContext:
     allowPrivilegeEscalation: false
     readOnlyRootFilesystem: true
     capabilities:
       drop:
         - ALL
   ```

3. **Service Account**
   - Dedicated ServiceAccount
   - `automountServiceAccountToken: false`

4. **Network Policy**
   - Ограничение входящего трафика
   - Ограничение исходящего трафика только к DB и DNS

5. **Namespace with Pod Security Standards**
   ```yaml
   labels:
     pod-security.kubernetes.io/enforce: restricted
   ```

6. **Resource Requests/Limits**
   - CPU и Memory limits установлены
   - Защита от DoS и resource exhaustion

## Security Scanning Tools

### Hadolint
- Линтинг Dockerfile
- Проверка best practices
- Конфиг: `security/hadolint.yaml`

### Checkov
- Сканирование IaC на misconfigurations
- Поддержка Kubernetes, Docker Compose
- Конфиг: `security/checkov.yaml`

### Trivy
- Сканирование образа на уязвимости
- Проверка секретов и misconfigurations
- Конфиг: `security/trivy.yaml`

## Дальнейшие улучшения

- [ ] Внедрить сканирование на этапе сборки (shift-left)
- [ ] Настроить автоматическое обновление base image
- [ ] Добавить OPA/Gatekeeper для policy enforcement
- [ ] Интегрировать с vulnerability management системой
