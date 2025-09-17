# Optional Enhancements (Offers) — Full Project

This document outlines optional, modular enhancements across the whole application (resources, community, mapping, files, admin, security, and video). Each item lists what you get, a minimal technical approach, and concrete deliverables so you can choose what to prioritize.

## 1) Resource Catalog & Data Quality

- What you get
  - Rich resource profiles (attributes, attachments, geo, references, provenance)
  - Version history and change audit for resources
  - Tags and categories with browsing pages
  - Basic analytics: counts by category, district, status
- Technical approach
  - New tables: `ResourceTag`, `ResourceTagMap`, `ResourceVersion(id, resource_id, user_id, diff_json, created_at)`
  - Optional JSON column for flexible attributes (e.g., `extra_json`)
  - Add indexes on category, district, and updated_at
  - Server-side validation for required fields
- Deliverables
  - Models + migrations, CRUD routes, admin screens, and list/detail UI updates

## 2) Advanced Search & Discovery

- What you get
  - Full‑text search on resources, posts, files
  - Faceted filters (category, district, tags, date)
  - Synonyms/stemming and typo tolerance (configurable)
- Technical approach
  - Use SQLite FTS5 for an embedded solution; optional Elasticsearch in production
  - Materialized search table or triggers to keep FTS in sync
  - Query builder for facets + pagination
- Deliverables
  - Search service, endpoints, and updated `templates/main/search.html`

## 3) GIS & Mapping Improvements

- What you get
  - Marker clustering, heatmaps, and draw/edit shapes on the map
  - Import/export GeoJSON/GPX/KML
  - Optional PostGIS support for advanced queries
- Technical approach
  - Leaflet plugins (markercluster, heatmap, draw)
  - Store geometries as GeoJSON in DB; adapter for PostGIS when enabled
  - Server endpoints for geo upload/validation
- Deliverables
  - Map UI upgrades in `templates/main/map.html` and geo endpoints

## 4) File Handling & Compliance

- What you get
  - Safer uploads (type sniffing, max size, virus scanning optional)
  - Previews (PDF/image thumbnails), content hashing, duplicate detection
  - Retention policies, per-user quotas (admin-configurable)
- Technical approach
  - `python-magic` for MIME, `pdf2image/Pillow` for thumbnails, optional ClamAV
  - Store `sha256`, `content_type`, `size`, and preview path
  - Background task for thumbnail generation (sync first, async optional)
- Deliverables
  - Upload pipeline, previews on detail pages, admin report of large files

## 5) Community, Chat & Moderation

- What you get
  - Roles: `owner`, `moderator`, `member` for rooms
  - Membership management, invite links, and scoped visibility
  - Reporting, rate limits, message pinning, and soft‑mute
- Technical approach
  - `ChatRoomMember(id, room_id, user_id, role, created_at)`
  - Signed invite tokens (HMAC/JWT) with `room_id`, `exp`, optional `one_time`
  - Server checks in HTTP and Socket.IO; simple rate limiter (IP+user)
  - `Report(id, type, reporter_id, target_kind, target_id, reason, created_at)`
- Deliverables
  - Models + migrations, moderation endpoints, UI affordances in chat screens

## 6) Video Calls (JaaS) Enhancements

- What you get
  - Restrict calls to room members; call‑only invites with short expiry
  - Pre‑join lobby with device checks and display name rules
  - Optional meeting recording toggle and host‑only features
- Technical approach
  - Reuse room membership checks before generating JaaS tokens
  - Short‑lived invite tokens for calls; per‑meeting options in payload
- Deliverables
  - Token service updates, lobby UI, and call options in community pages

## 7) Campaigns & Awareness

- What you get
  - Scheduled campaign posts, progress tracking, and media galleries
  - Basic impact metrics (views, reactions, submissions)
- Technical approach
  - `Campaign(id, title, starts_at, ends_at, status, metrics_json)`
  - Hooks to increment metrics; simple scheduler (cron/Windows Task Scheduler)
- Deliverables
  - Campaign CRUD + list/detail UI and metrics widgets on admin dashboard

## 8) Admin & Analytics

- What you get
  - Audit log of sensitive actions and data changes
  - Dashboards: user growth, activity, uploads, top searches
  - CSV/JSON exports for resources and users
- Technical approach
  - `AuditEvent(id, type, actor_id, subject_kind, subject_id, payload_json, created_at)`
  - Aggregation queries; cached metrics; export endpoints with streaming
- Deliverables
  - Admin screens in `/admin`, charts, and export buttons

## 9) Authentication & Security

- What you get
  - Email verification, password reset, optional 2FA (TOTP)
  - Session security (IP/UA binding optional), strong password policy
- Technical approach
  - Email flows via existing mail config; `pyotp` for TOTP 2FA
  - Brute‑force protection and rate limits on auth routes
- Deliverables
  - Auth screens, tokens, and admin 2FA enforcement toggle

## 10) Public API & Integrations

- What you get
  - Read‑only REST API for resources, posts, and campaigns
  - API keys with per‑key rate limits, usage logs, and webhooks
- Technical approach
  - API blueprint with token auth; pagination; CORS
  - Webhook signing with shared secret
- Deliverables
  - `/api/*` endpoints, API key admin, and docs page

## 11) Performance & Caching

- What you get
  - Faster pages via query optimization, caching, and pagination
  - Optional Redis cache and CDN for static files
- Technical approach
  - Flask‑Caching (simple/Redis), cache keys per page + filters
  - Eliminate N+1 queries; add DB indexes; gzip and static versioning
- Deliverables
  - Cache layer, index migrations, perf checks on heavy views

## 12) Observability & Ops

- What you get
  - Structured logs, error reporting, uptime/health checks
  - Backup/restore script for SQLite and uploads
- Technical approach
  - JSON logs with correlation IDs; `/healthz` endpoint
  - Scheduled backup script; rotate logs and backups
- Deliverables
  - Logging config, health route, scripts, and admin ops page

## 13) Internationalization (i18n)

- What you get
  - Multi‑language UI (e.g., English, Urdu/Pashto)
  - Language switcher and translated content labels
- Technical approach
  - Flask‑Babel; extract strings; per‑locale templates for key pages
- Deliverables
  - i18n setup, translations, and switcher in `base.html`

## 14) Accessibility & UX Polish

- What you get
  - Better keyboard navigation, ARIA roles, and color contrast
  - Consistent empty states, loading skeletons, and toasts
- Technical approach
  - Audit with Lighthouse/axe; component updates; focus management
- Deliverables
  - Polished UI across `templates/*` and shared components

---

## Implementation Notes

- Migrations
  - Alembic migrations for new tables, fields, indexes
- Security
  - Enforce authorization in BOTH HTTP routes and Socket.IO handlers
  - Short‑lived signed tokens for invites; one‑time consumption flags
- Data
  - Backfill scripts for tags and search indexes where needed

## Configuration (env)

- Existing
  - `SECRET_KEY`, `DATABASE_URL`
  - Mail: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
  - JaaS: `JITSI_APP_ID`, `JITSI_KEY_ID`, `JITSI_APP_SECRET`
- New (optional, by feature)
  - Search: `SEARCH_BACKEND` (e.g., `sqlite_fts`, `elasticsearch`)
  - Files: `MAX_UPLOAD_SIZE_MB`, `ALLOWED_EXTENSIONS`, `CLAMAV_ENABLED`
  - Cache: `REDIS_URL`
  - API: `API_RATE_LIMIT_PER_MIN`, `API_WEBHOOK_SECRET`
  - Auth: `ENABLE_2FA`
  - Ops: `LOG_LEVEL`, `HEALTHCHECK_TOKEN`

## UI Touchpoints

- Search page with facets; resource list/detail; map with clustering/draw
- Chat: membership/invite controls; moderation menus; pinned messages
- Admin: dashboards, audit log, exports, API keys
- Campaigns: list/detail, schedule settings, progress widgets

## Suggested Delivery Order

1) Resource catalog upgrades + advanced search (high impact)
2) File safety/preview and map improvements
3) Community roles/moderation and video scoping
4) Admin analytics + audit log and API (read‑only)
5) Performance/caching, observability, and i18n/accessibility polish

## Next Steps

- Pick the items you want in the first milestone
- I’ll implement models/endpoints, then wire up UI progressively
- We’ll ship in small PRs for easier testing and rollback
