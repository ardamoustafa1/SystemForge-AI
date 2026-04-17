# Contributing to SystemForge AI

Katkilariniz için tesekkürler. Bu doküman, katkilarin hizli ve sorunsuz sekilde merge edilmesi için temel kurallari tanimlar.

## 1) Branch and PR Flow

- `main/master` üzerine dogrudan commit atmayin.
- Her degisiklik için feature branch acin:
  - `feat/<short-topic>`
  - `fix/<short-topic>`
  - `docs/<short-topic>`
- PR aciklamasinda su 3 basligi doldurun:
  - Ne degisti?
  - Neden degisti?
  - Nasil test edildi?

## 2) Development Setup

```bash
cp .env.example .env
docker compose up --build
```

Lokal backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Lokal frontend:

```bash
cd frontend
npm install
npm run dev
```

## 3) Required Quality Checks

PR öncesi minimum kontrol:

- Backend:
  - `pytest tests -q`
- Frontend:
  - `npm run build`
  - `npm run test`
  - `npm run test:e2e` (mümkünse)

CI pipeline su adimlari kosar:

- Backend lint (`ruff`)
- Backend typecheck (`pyre`)
- Backend Docker testleri
- Frontend type/build/E2E
- Security dependency audit

## 4) Code Style and Scope

- Degisiklikleri küçük ve odakli tutun.
- Ilgisiz refactor veya formatting degisikliklerini ayni PR'a eklemeyin.
- API kontrat degisikliginde endpoint docs/README güncellemelerini ekleyin.
- Migration gerekiyorsa Alembic migration dosyasi ekleyin.

## 5) Security and Secrets

- Secret dosyalarini veya kimlik bilgilerini commit etmeyin.
- `.env` degerlerini repository'ye eklemeyin.
- Güvenlik açigi bildirimi için `SECURITY.md` akisini kullanin.

## 6) Commit Message Guidance

Önerilen format:

- `feat: add workspace budget alert endpoint`
- `fix: prevent stale websocket reconnect loop`
- `docs: expand production hardening checklist`

## 7) Documentation Expectations

Asagidaki durumlarda dokümantasyon güncellemesi beklenir:

- Yeni endpoint/service/worker eklendiyse
- Env variable eklendiyse veya default degistiyse
- Davranissal degisiklik (user-facing) varsa

Minimum güncellenecek dosyalar:

- `README.md` (gerekiyorsa `README.en.md`)
- `docs/` altindaki ilgili tasarim/güvenlik belgeleri
- `CHANGELOG.md` (release etkili degisikliklerde)
