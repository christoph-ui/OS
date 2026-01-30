# EATON MCP Server - Setup Guide

## ✅ Installation Complete!

Your EATON Intelligence Platform MCP server is ready to connect to Claude Desktop.

---

## 📍 Quick Start (3 Steps)

### Step 1: Add to Claude Desktop Config

**File location:** `~/.config/Claude/claude_desktop_config.json`

**Add this configuration:**

```json
{
  "mcpServers": {
    "eaton-intelligence": {
      "command": "/home/christoph.bertsch/0711/0711-OS/mcps/eaton/start.sh",
      "args": []
    }
  }
}
```

**Or copy the pre-made config:**

```bash
cat /home/christoph.bertsch/0711/0711-OS/mcps/eaton/claude_desktop_config.json
```

---

### Step 2: Ensure EATON Lakehouse is Running

```bash
# Check if running
curl http://localhost:9302/health

# If not running, start it
cd /home/christoph.bertsch/0711/deployments/eaton
docker compose up -d eaton-lakehouse eaton-embeddings

# Verify (should show "healthy")
curl http://localhost:9302/health | jq .
```

---

### Step 3: Restart Claude Desktop

1. Completely quit Claude Desktop (not just close the window)
2. Reopen Claude Desktop
3. Look for the MCP icon (🔌) in the bottom bar
4. You should see "eaton-intelligence" listed

---

## 🎯 Test Your Setup

In Claude Desktop, try these prompts:

### Test 1: Check Connection
```
What tables are available in the EATON lakehouse?
```

**Expected:** Claude uses `list_tables` tool and shows:
- general_documents
- eaton_products
- general_chunks
- product_images
- embeddings.lance

---

### Test 2: Search Products
```
Search for UPS products in EATON catalog
```

**Expected:** Claude uses `search_products` tool and shows:
- EATON 5E UPS
- Eaton 5SC UPS 750 120V
- 5E1100IUSB-AR
- (+ more)

---

### Test 3: Get Statistics
```
Show me EATON data statistics
```

**Expected:** Claude uses `get_stats` tool and shows:
- 62,136 embeddings
- 327 products
- 344 documents
- 326.88 MB total size

---

## 🛠️ Available Tools (6)

| Tool | Description | Example Use |
|------|-------------|-------------|
| `search_products` | Search 327 products | "Find circuit breakers" |
| `get_product` | Get product details | "Show product 167885" |
| `semantic_search` | Vector search 62K chunks | "Find Type B RCD info" |
| `query_documents` | List 344 documents | "List all documents" |
| `list_tables` | Show lakehouse structure | "What tables exist?" |
| `get_stats` | Lakehouse statistics | "Show data stats" |

---

## 🔍 What Data You Have Access To

### Products (327 items)
- **UPS Systems**: 5E series, 5SC series
- **Circuit Breakers**: FAZ MCB (1-4 pole)
- **Residual Current Devices**: FRCDM RCCB
- **Fuses**: FUSETRON series
- **Electrical Components**: Various industrial products

### Documents (344 files)
- ECLASS 13 Examples
- Standard BMECat 2005 ETIM catalogs
- PDH Extract (Product Data Hub)
- ETIM xChange Guidelines
- 3D CAD models (.stp files)
- Product images (570 JPG files)

### Standards Coverage
- **ECLASS 13.0**: European product classification
- **ETIM**: International electrotechnical model
- **BMEcat 2005**: Electronic catalog format
- **IEC/EN 61008**: Electrical safety standards

---

## 🚨 Troubleshooting

### Problem: Claude Desktop doesn't show the MCP server

**Solutions:**

1. **Check config file exists:**
   ```bash
   ls -la ~/.config/Claude/claude_desktop_config.json
   ```

2. **Validate JSON syntax:**
   ```bash
   jq . < ~/.config/Claude/claude_desktop_config.json
   ```

3. **Verify absolute path:**
   ```bash
   ls -la /home/christoph.bertsch/0711/0711-OS/mcps/eaton/start.sh
   ```

4. **Test server manually:**
   ```bash
   cd /home/christoph.bertsch/0711/0711-OS/mcps/eaton
   ./start.sh
   # Press Ctrl+C to stop
   ```

5. **Restart Claude Desktop completely** (Quit from menu, not just close window)

---

### Problem: "Lakehouse not responding"

**Solution:**
```bash
# Check lakehouse container
docker ps | grep eaton-lakehouse

# If not running
cd /home/christoph.bertsch/0711/deployments/eaton
docker compose up -d eaton-lakehouse

# Verify health
curl http://localhost:9302/health
```

---

### Problem: Semantic search doesn't work

**Solution:**
```bash
# Embeddings service must be running
docker ps | grep eaton-embeddings

# If not running
cd /home/christoph.bertsch/0711/deployments/eaton
docker compose up -d eaton-embeddings

# Test embeddings service
curl http://localhost:9301/health
```

---

## 📁 Files Created

```
/home/christoph.bertsch/0711/0711-OS/mcps/eaton/
├── server.py                      # MCP server (Python)
├── start.sh                       # Startup script
├── README.md                      # Complete documentation
├── SETUP_GUIDE.md                # This file
└── claude_desktop_config.json    # Config template
```

---

## 🔒 Security Notes

- ✅ Runs **locally only** (no external network access)
- ✅ **Read-only** access to EATON data
- ✅ No authentication needed (localhost only)
- ✅ Data stays within 0711 platform
- ✅ No API keys or credentials required

---

## 📊 System Requirements

- ✅ Python 3.10+
- ✅ MCP SDK (`pip3 install mcp`)
- ✅ httpx (`pip3 install httpx`)
- ✅ EATON lakehouse running (port 9302)
- ✅ Claude Desktop (macOS/Linux)

---

## 🎓 Example Conversations

### Conversation 1: Product Discovery

**You:** What products does EATON have for circuit protection?

**Claude:** Let me search the EATON catalog for circuit protection products.

*[Uses search_products(query="circuit protection")]*

I found several circuit protection products:

1. **FAZ MCB Series** - Miniature circuit breakers (1-4 pole)
2. **FRCDM RCCB** - Residual current devices
3. **FUSETRON Dual Element** - Fuses

Would you like details on any specific product?

---

### Conversation 2: Technical Specifications

**You:** Tell me about product 167885

**Claude:** *[Uses get_product(product_id="167885")]*

**Product: FRCDM-40/4/03-G/B+**

This is a digital residual current device (RCD) with these specifications:

**Key Specs:**
- Rated Current: 40A
- Poles: 4-pole
- Residual Current: 300mA
- Type: G/B+ (AC/DC sensitive)
- Standards: IEC/EN 61008-1, IEC/EN 61008-2-1

**Classification:**
- ECLASS: 27142201 (RCCBs)
- ETIM: Compliant

**Images:** 3 product images available

---

### Conversation 3: Knowledge Search

**You:** How are products classified according to ECLASS?

**Claude:** *[Uses semantic_search(query="ECLASS product classification")]*

Based on EATON's documentation:

ECLASS is a hierarchical product classification standard used in Europe. For EATON products:

- **Class 27**: Electrical engineering
- **Subclass 142201**: Residual current protective devices

Each product has:
- Classification ID (e.g., 0173-1#01-...)
- Feature groups
- Technical attributes
- Standard values

The FRCDM series RCCBs use ECLASS 13.0 classification with detailed electrical specifications.

---

## 🚀 Next Steps

1. ✅ **Test the setup** - Try the example prompts above
2. ✅ **Explore products** - Ask about specific EATON products
3. ✅ **Search documents** - Use semantic search for technical info
4. ✅ **Get product details** - Dive deep into specifications

---

## 📞 Support

**Questions?**
- Read the full docs: `/home/christoph.bertsch/0711/0711-OS/mcps/eaton/README.md`
- Test manually: `./start.sh`
- Check logs: Server outputs to console when run manually

**Want to create MCPs for other customers?**
Copy this directory and modify:
- Server name
- Lakehouse URL
- Product descriptions

---

**Status:** ✅ Ready to use
**Version:** 1.0.0
**Customer:** EATON
**Platform:** 0711 Intelligence Platform
