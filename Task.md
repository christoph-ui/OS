# Task: Console Improvements + Connector Seeding

**Priority:** HIGH  
**Updated:** 2026-01-30

---

## ✅ COMPLETED

- [x] E2E Tests passing (33/33)
- [x] vLLM Multi-GPU setup on H200
- [x] Website deployed
- [x] Sidebar color softened (slate-800)

---

## 🔧 TASK A: Fix Connector Seeding

Connector seeding has model/schema errors. Fix them.

### Steps

```bash
cd ~/OS

# 1. Find the seeding script
ls scripts/seed_connectors*.py

# 2. Run with verbose output to see errors
python scripts/seed_connectors_focused.py 2>&1

# 3. Check the Connector model schema
cat api/models/connector.py  # or wherever models are

# 4. Fix mismatches between script and schema

# 5. Re-run seeding - should complete without errors
python scripts/seed_connectors_focused.py
```

### Expected
- All 18 connectors seeded successfully
- No schema/model errors

---

## 🎨 TASK B: Consolidate Theme System

53+ files have duplicate color definitions. Create single source of truth.

### Steps

1. **Create theme file:**
```typescript
// console/frontend/src/lib/theme.ts
export const colors = {
  dark: '#1e293b',      // slate-800
  light: '#faf9f5',
  midGray: '#94a3b8',   // slate-400
  lightGray: '#e8e6dc',
  orange: '#d97757',
  red: '#d75757',
} as const;

export type ColorKey = keyof typeof colors;
```

2. **Update all files to import:**
```typescript
import { colors } from '@/lib/theme';
// Then use: colors.dark, colors.orange, etc.
```

3. **Bulk update with sed/find:**
```bash
# Remove inline color definitions
# Replace with imports
```

### Expected
- Single theme.ts file
- All 53 files import from it
- No more inline `const colors = {...}`

---

## 📊 Status

| Task | Status |
|------|--------|
| A: Connector Seeding | 🔴 Blocked |
| B: Theme Consolidation | 🟡 Ready |
