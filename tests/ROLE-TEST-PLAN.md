# Handball Manager - Role-Based Test Plan

## Überblick

Dieser Testplan deckt alle 5 Benutzerrollen und deren Berechtigungen im Handball Manager ab.

## Rollen im System

| Rolle | Beschreibung |
|-------|--------------|
| **ADMIN** | Vollzugriff auf alle Funktionen |
| **COACH** | Trainer: Teams, Spieler, Spiele, Termine verwalten |
| **SUPERVISOR** | Betreuer: Eingeschränkte Verwaltung |
| **PLAYER** | Spieler: Eigene Daten, Anwesenheit, Termine |
| **PARENT** | Eltern: Kinder verwalten, Anwesenheit |

---

## 1. ADMIN Tests

### 1.1 Navigation (Sidebar)
- [x] Alle Menüpunkte sichtbar
  - [x] Dashboard
  - [x] Mannschaften
  - [x] Spieler
  - [x] Spiele
  - [x] Termine
  - [x] Anwesenheit
  - [x] News
  - [x] Profil
  - [x] Einladungen (sollte sichtbar sein)
  - [x] Admin-Bereich

### 1.2 API-Endpunkte
- [x] **Dashboard**
  - [x] GET /api/v1/dashboard/stats
  - [x] GET /api/v1/dashboard/admin/summary
  - [x] GET /api/v1/dashboard/health
- [x] **Teams** (Vollzugriff)
  - [x] POST /api/v1/teams (create)
  - [x] PUT /api/v1/teams/{id} (update)
  - [x] DELETE /api/v1/teams/{id} (delete)
- [x] **Users** (Vollzugriff)
  - [x] GET /api/v1/users/ (list)
  - [x] PUT /api/v1/users/{id} (update)
  - [x] DELETE /api/v1/users/{id} (delete)
  - [x] POST /api/v1/users/{id}/restore (restore)
- [x] **Migrations**
  - [x] POST /api/v1/migrations/run
  - [x] GET /api/v1/migrations/status
- [x] **Parents**
  - [x] GET /api/v1/parents/children
  - [x] POST /api/v1/parents/children/{id}/verify

### 1.3 Frontend-Seiten
- [x] Dashboard mit Statistiken
- [x] Teams verwalten (CRUD)
- [x] Spieler verwalten (CRUD)
- [x] Spiele verwalten (CRUD)
- [x] Termine verwalten (CRUD)
- [x] Anwesenheit verwalten
- [x] News verwalten
- [x] Einladungen senden/verwalten
- [x] User-Verwaltung

**Status: ✅ ADMIN Tests vollständig**

---

## 2. COACH Tests

### 2.1 Navigation (Sidebar)
- [x] Alle Standard-Menüpunkte sichtbar
  - [x] Dashboard
  - [x] Mannschaften (nur eigene)
  - [x] Spieler (nur eigene Teams)
  - [x] Spiele (nur eigene Teams)
  - [x] Termine
  - [x] Anwesenheit
  - [x] News
  - [x] Profil

### 2.2 API-Endpunkte
- [x] **Teams** (Eingeschränkt)
  - [x] GET /api/v1/teams (nur als Coach zugewiesene)
  - [x] POST /api/v1/teams (❌ nicht erlaubt - nur Admin)
  - [x] PUT /api/v1/teams/{id} (nur eigene Teams)
  - [x] DELETE /api/v1/teams/{id} (❌ nicht erlaubt)
- [x] **Players**
  - [x] GET /api/v1/players (nur eigene Teams)
  - [x] POST /api/v1/players (nur für eigene Teams)
  - [x] PUT /api/v1/players/{id} (nur eigene Spieler)
- [x] **Games**
  - [x] GET /api/v1/games
  - [x] POST /api/v1/games (erlaubt)
  - [x] PUT /api/v1/games/{id} (erlaubt)
- [x] **Events**
  - [x] GET /api/v1/events
  - [x] POST /api/v1/events (erlaubt)
  - [x] PUT /api/v1/events/{id} (erlaubt)
  - [x] DELETE /api/v1/events/{id} (erlaubt)
- [x] **Attendance**
  - [x] GET /api/v1/attendance
  - [x] POST /api/v1/attendance (erlaubt)
- [x] **News**
  - [x] GET /api/v1/news
  - [x] POST /api/v1/news (erlaubt)
  - [x] PUT /api/v1/news/{id} (eigene News)
  - [x] DELETE /api/v1/news/{id} (eigene News)

### 2.3 Frontend-Seiten
- [x] Dashboard (eingeschränkte Stats)
- [x] Teams anzeigen/bearbeiten (nur eigene)
- [x] Spieler verwalten
- [x] Spiele verwalten
- [x] Termine verwalten
- [x] Anwesenheit verwalten
- [x] News erstellen/bearbeiten

**Status: 🟡 COACH Tests teilweise - weitere Tests nötig**

---

## 3. SUPERVISOR Tests

### 3.1 Navigation (Sidebar)
- [ ] Alle Standard-Menüpunkte sichtbar
  - [ ] Dashboard
  - [ ] Mannschaften
  - [ ] Spieler
  - [ ] Spiele
  - [ ] Termine
  - [ ] Anwesenheit
  - [ ] News
  - [ ] Profil

### 3.2 API-Endpunkte
- [ ] **Teams** (lesend + eingeschränkt schreibend)
  - [ ] GET /api/v1/teams
  - [ ] POST /api/v1/teams (❌ nicht erlaubt)
  - [ ] PUT /api/v1/teams/{id} (nur bestimmte Felder?)
- [ ] **Games** (mit Coach)
  - [ ] GET /api/v1/games
  - [ ] POST /api/v1/games (mit Coach-Rechten)
- [ ] **Events**
  - [ ] GET /api/v1/events
  - [ ] POST /api/v1/events (mit Coach-Rechten)
- [ ] **Attendance**
  - [ ] GET /api/v1/attendance
  - [ ] POST /api/v1/attendance (mit Coach-Rechten)

### 3.3 Frontend-Seiten
- [ ] Dashboard
- [ ] Teams anzeigen
- [ ] Spieler anzeigen
- [ ] Spiele anzeigen/bearbeiten
- [ ] Termine anzeigen/bearbeiten
- [ ] Anwesenheit verwalten
- [ ] News anzeigen

**Status: ⚠️ SUPERVISOR Tests noch nicht durchgeführt**

---

## 4. PLAYER Tests

### 4.1 Navigation (Sidebar)
- [ ] Eingeschränkte Menüpunkte
  - [ ] Dashboard (eingeschränkt)
  - [ ] Mannschaften (nur eigene)
  - [ ] Spieler (nur eigene Daten)
  - [ ] Spiele (nur eigene Teams)
  - [ ] Termine (nur eigene)
  - [ ] Anwesenheit (nur eigene)
  - [ ] News
  - [ ] Profil

### 4.2 API-Endpunkte
- [ ] **Teams** (nur lesend)
  - [ ] GET /api/v1/teams (nur eigene)
  - [ ] POST /api/v1/teams (❌ nicht erlaubt)
- [ ] **Players**
  - [ ] GET /api/v1/players/{id} (nur eigene ID)
  - [ ] PUT /api/v1/players/{id} (❌ nicht erlaubt?)
- [ ] **Games**
  - [ ] GET /api/v1/games (nur eigene)
- [ ] **Events**
  - [ ] GET /api/v1/events (nur eigene/öffentliche)
- [ ] **Attendance**
  - [ ] GET /api/v1/attendance (eigene)
  - [ ] POST /api/v1/attendance (nur eigene - Zu- / Absagen)

### 4.3 Frontend-Seiten
- [ ] Dashboard (eingeschränkt)
- [ ] Teams anzeigen
- [ ] Eigenes Profil
- [ ] Spiele anzeigen
- [ ] Termine anzeigen + Zu-/Absagen
- [ ] Anwesenheit (eigene)
- [ ] News anzeigen

**Status: ⚠️ PLAYER Tests noch nicht durchgeführt**

---

## 5. PARENT Tests

### 5.1 Navigation (Sidebar)
- [ ] Eingeschränkte Menüpunkte
  - [ ] Dashboard (eingeschränkt)
  - [ ] Mannschaften (Kinder)
  - [ ] Spieler (Kinder)
  - [ ] Spiele (Kinder)
  - [ ] Termine (Kinder)
  - [ ] Anwesenheit (Kinder)
  - [ ] News
  - [ ] Profil

### 5.2 API-Endpunkte
- [ ] **Teams** (nur lesend, Kinder)
- [ ] **Players** (nur Kinder)
- [ ] **Games** (nur Kinder)
- [ ] **Events** (nur Kinder)
- [ ] **Attendance** (nur für Kinder)

### 5.3 Frontend-Seiten
- [ ] Dashboard (eingeschränkt)
- [ ] Teams der Kinder
- [ ] Spieler-Profile der Kinder
- [ ] Spiele der Kinder
- [ ] Termine der Kinder
- [ ] Anwesenheit für Kinder verwalten
- [ ] News anzeigen

**Status: ⚠️ PARENT Tests noch nicht durchgeführt**

---

## Zusammenfassung

| Rolle | Test-Status | Letzter Test |
|-------|-------------|--------------|
| ADMIN | ✅ Vollständig | 2026-04-01 |
| COACH | 🟡 Teilweise | - |
| SUPERVISOR | ⚠️ Nicht getestet | - |
| PLAYER | ⚠️ Nicht getestet | - |
| PARENT | ⚠️ Nicht getestet | - |

## Empfohlene nächste Schritte

1. **Test-Accounts anlegen** für jede Rolle
   - coach@handball.de / coach123
   - supervisor@handball.de / supervisor123
   - player@handball.de / player123
   - parent@handball.de / parent123

2. **E2E Tests für COACH** mit dem neuen Skill durchführen

3. **SUPERVISOR, PLAYER, PARENT** testen und dokumentieren

4. **Negative Tests** hinzufügen (was sollte jede Rolle *nicht* können)
