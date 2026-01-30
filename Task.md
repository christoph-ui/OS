# Task: Console Improvements + Connector Seeding

**Priority:** HIGH  
**Updated:** 2026-01-30

---

## ✅ COMPLETED

- [x] E2E Tests passing (33/33)
- [x] vLLM Multi-GPU setup on H200 ✅
- [x] Website deployed
- [x] Sidebar color softened (slate-800)
- [x] Connector seeding fix pushed (`26ed086`) - GitHub Issue #1

---

## 🔧 TASK A: Connector Seeding (waiting on H200)

**Fix pushed** - H200 agent needs to pull and run:

```bash
git pull origin main
python scripts/seed_connectors_focused.py
```

GitHub Issue: https://github.com/christoph-ui/OS/issues/1

---

## 🎨 TASK B: Theme Consolidation

Theme file created (`src/lib/theme.ts`). Migration of 51 files pending.

**Done:**
- [x] Created `console/frontend/src/lib/theme.ts`
- [x] Includes all colors: dark, light, midGray, lightGray, orange, red, blue, green

**Remaining:**
- [ ] Migrate 51 files to import from theme.ts
- [ ] Remove inline `const colors = {...}` definitions

---

## 📊 Status

| Task | Status |
|------|--------|
| A: Connector Seeding | 🟡 Fix pushed, awaiting H200 |
| B: Theme Consolidation | 🟡 Theme created, migration pending |
