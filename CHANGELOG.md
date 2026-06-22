# Changelog

Bu dosya projedeki önemli degisiklikleri takip etmek için tutulur.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
Versioning: [Semantic Versioning](https://semver.org/)

## [Unreleased]

### Added
- README kapsamli sekilde yeniden düzenlendi (mimari, servis manifesti, full env referansi, runbook, hardening checklist).
- `README.en.md` eklendi.
- `CONTRIBUTING.md` eklendi.
- Rozetler, ADR index ve changelog politikasi README'ye eklendi.
- Star-focused GitHub README vitrini eklendi: product positioning, screenshots, quick demo, architecture, showcase, release and contributor links.
- Local Docker demo seed script'i eklendi (`backend/scripts/seed_demo.py`).
- Docker Compose demo seed servisi eklendi (`backend-demo-seed`).
- Demo credentials ve showcase design seed env degiskenleri `.env.example` içine eklendi.
- `docs/ARCHITECTURE.md`, `docs/DEMO_SCRIPT.md`, `docs/SHOWCASE_EXAMPLES.md`, `docs/RELEASE_PROCESS.md`, `docs/GOOD_FIRST_ISSUES.md`, `docs/MAINTAINER_GUIDE.md` eklendi.
- README görselleri için logo ve product screenshot assetleri eklendi.
- Docker demo üzerinden doğrulanmış dashboard ve architecture review görselleri eklendi.
- `examples/` altına gerçek Docker Compose, Terraform, Kubernetes ve architecture showcase dosyalari eklendi.
- Release workflow'una Cosign keyless imza, SBOM/provenance, Helm paketi ve checksum üretimi eklendi.

### Changed
- README bilgi mimarisi profesyonel dokümantasyon formatina getirildi.
- `docs/QUICK_START.md` seeded demo akisi ile güncellendi.
- `docs/LOAD_TEST_REPORT.md` release-quality benchmark kanit formatina çevrildi.
- `ROADMAP.md` gerçekçi release gate durumunu yansitacak sekilde güncellendi.
- Frontend API erisimi same-origin `/api` proxy üzerinden çalisacak sekilde güncellendi.
- Frontend Docker kurulumu Node 22 Alpine üzerinde deterministik `npm ci` akışına geçirildi.

### Fixed
- README'deki kirik/missing logo ve demo görsel referanslari giderildi.
- API key metadata schema drift'i yeni Alembic migration ile giderildi.
- FastAPI router uyumsuzlugu nedeniyle tüm istekleri 500'e düsüren metrics middleware kaldirildi.
- Docker backend test fixture'lari güncel şemaya uyarlandi; 64 testin tamami geçiyor.

### Security
- Production hardening checklist dokümana eklendi.
- Prometheus metrics endpoint token korumali hale getirildi.
- Frontend dependency audit sonucu 0 vulnerability seviyesine indirildi.
