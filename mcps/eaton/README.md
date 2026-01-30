# EATON Intelligence Platform MCP Server

Connect Claude Desktop to EATON's customer data in the 0711 Intelligence Platform.

## 📊 What You Get Access To

- **62,136 embeddings** - Semantic search across all EATON data
- **327 products** - UPS systems, circuit breakers, fuses, electrical components
- **344 documents** - ECLASS catalogs, 3D models, PDFs, technical specs
- **246 product images** - Product photos with metadata

## 🚀 Quick Start

### 1. Ensure EATON Lakehouse is Running

```bash
# Check if lakehouse is up
curl http://localhost:9302/health

# If not running, start EATON deployment
cd /home/christoph.bertsch/0711/deployments/eaton
docker compose up -d eaton-lakehouse eaton-embeddings
```

### 2. Test the MCP Server

```bash
cd /home/christoph.bertsch/0711/0711-OS/mcps/eaton
./start.sh
```

You should see:
```
Starting EATON Intelligence Platform MCP Server
✓ Lakehouse connected
✓ Python 3.10.12
✓ MCP SDK installed
✓ httpx installed
Starting MCP server...
```

Press Ctrl+C to stop the test.

### 3. Configure Claude Desktop

**Location:** `~/.config/Claude/claude_desktop_config.json`

Add this to your config:

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

**Full example config:**

```json
{
  "mcpServers": {
    "eaton-intelligence": {
      "command": "/home/christoph.bertsch/0711/0711-OS/mcps/eaton/start.sh",
      "args": []
    }
  },
  "globalShortcut": "Ctrl+Space"
}
```

### 4. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

### 5. Verify Connection

In Claude Desktop, look for the MCP server icon (🔌) in the bottom bar. You should see "eaton-intelligence" listed.

---

## 🛠️ Available Tools

### 1. `search_products`

Search EATON product catalog by name, ID, or description.

**Example prompts:**
- "Search for UPS products"
- "Find circuit breakers"
- "Show me all 4-pole products"

**Arguments:**
- `query` (string, required) - Search keywords
- `limit` (number, optional) - Max results (default: 20, max: 100)

**Returns:**
- Product ID, name, description
- Specifications and attributes
- Image count

---

### 2. `get_product`

Get detailed product information with images.

**Example prompts:**
- "Get product details for 167885"
- "Show me the FRCDM-40/4/03-G/B+ specifications"
- "What images are available for product 5E1100IUSB-AR?"

**Arguments:**
- `product_id` (string, required) - Product ID (supplier_pid)

---

### 3. `semantic_search`

Semantic search across all EATON documents using vector embeddings.

**Example prompts:**
- "Find information about Type B residual current devices"
- "What are the specifications for 40A circuit breakers?"
- "Search for ECLASS 13 classification examples"

**Arguments:**
- `query` (string, required) - Natural language question
- `limit` (number, optional) - Max results (default: 5, max: 20)

---

### 4. `query_documents`

List ingested documents (catalogs, 3D models, PDFs).

**Example prompts:**
- "List all documents"
- "Show me the ingested files"

**Arguments:**
- `limit` (number, optional) - Max documents (default: 10, max: 50)

---

### 5. `list_tables`

List available data tables in the lakehouse.

**Example prompts:**
- "What tables are available?"
- "Show me the lakehouse structure"

**Arguments:** None

---

### 6. `get_stats`

Get lakehouse statistics.

**Example prompts:**
- "Show EATON data statistics"
- "How much data is in the lakehouse?"

**Arguments:** None

---

### 7. `list_syndication_formats`

List all 8 available export formats for distributors.

**Example prompts:**
- "What syndication formats are available?"
- "Show me all export formats"
- "List distributor formats"

**Arguments:** None

**Returns:**
- 8 format cards with details (file type, languages, use case, complexity)

---

### 8. `get_syndication_products`

Get products available for content syndication (109 products with full PIM data).

**Example prompts:**
- "Show me all products available for syndication"
- "List UPS products for export"
- "Which products can I syndicate?"

**Arguments:**
- `category` (string, optional) - Filter by product type (UPS, MCB, Fuse, etc.)
- `limit` (number, optional) - Max results (default: 20, max: 100)

**Returns:**
- Product list with SKU, GTIN, ETIM class, features

---

### 9. `generate_syndication`

Generate distributor-ready export file in specified format.

**Example prompts:**
- "Generate Amazon export for product 5SC750"
- "Create BMEcat XML for all UPS products"
- "Export FAB-DIS format in French"

**Arguments:**
- `format` (required) - One of: `bmecat`, `amazon`, `cnet`, `fabdis`, `td_synnex`, `1worldsync`, `etim_json`, `amer_xml`
- `product_ids` (optional, array) - List of SKUs (empty = all 109 products)
- `language` (optional) - `en`, `de`, `fr` (default: `en`)

**Returns:**
- Generation confirmation with filename, product count, file size
- Instructions to download from console UI

**Supported Formats:**
- 🇪🇺 **bmecat** - BMEcat XML (ECLASS/ETIM, European distributors)
- 📦 **amazon** - Amazon Vendor Central XLSX (B2B e-commerce)
- 📡 **cnet** - CNET Content Feed XML (Retail syndication)
- 🇫🇷 **fabdis** - FAB-DIS XLSX (French translation + metric units)
- 💻 **td_synnex** - TD Synnex XLSX (IT distribution)
- 🌐 **1worldsync** - 1WorldSync GDSN XLSX (Global sync)
- ⚡ **etim_json** - ETIM xChange JSON (ETIM-10 standard)
- 🇺🇸 **amer_xml** - AMER Vendor XML (US distributors)

---

### 10. `preview_syndication`

Preview what a syndication format looks like (first 50 lines).

**Example prompts:**
- "Show me a preview of Amazon format"
- "What does CNET XML look like?"
- "Preview BMEcat export"

**Arguments:**
- `format` (required) - Format to preview

**Returns:**
- First 50 lines of generated output for sample product
- Format structure overview

---

## 📝 Example Conversations

### Example 1: Product Discovery

**You:** What UPS models does EATON have?

**Claude:** *Uses `search_products(query="UPS", limit=20)`*

Returns:
- EATON 5E UPS
- Eaton 5SC UPS 750 120V
- 5E1100IUSB-AR
- (+ more)

---

### Example 2: Technical Specifications

**You:** What are the specifications for product 167885?

**Claude:** *Uses `get_product(product_id="167885")`*

Returns:
- Product: FRCDM-40/4/03-G/B+ Digital RCD
- Rated current: 40A
- Poles: 4-pole
- Type: B+ (AC/DC sensitive)
- Residual current: 300mA
- Standards: IEC/EN 61008-1
- Images: 3 available

---

### Example 3: Knowledge Search

**You:** Find information about ECLASS product classification

**Claude:** *Uses `semantic_search(query="ECLASS product classification", limit=5)`*

Returns relevant chunks from:
- ECLASS 13 Examples.xml
- Standard BMECat 2005 ETIM catalogs
- Product classification data

---

## 🔧 Troubleshooting

### Error: "Lakehouse not responding on port 9302"

**Solution:**
```bash
cd /home/christoph.bertsch/0711/deployments/eaton
docker compose up -d eaton-lakehouse eaton-embeddings
```

### Error: "MCP SDK not installed"

**Solution:**
```bash
pip3 install mcp httpx
```

### Claude Desktop doesn't show the MCP server

**Solutions:**
1. Check config path: `~/.config/Claude/claude_desktop_config.json`
2. Verify JSON syntax (use `jq . < config.json`)
3. Check startup script path is absolute
4. Restart Claude Desktop completely (Quit, not just close window)
5. Check Claude Desktop logs (if available)

### Semantic search returns "Embeddings service unavailable"

**Solution:**
```bash
# Start embeddings service
cd /home/christoph.bertsch/0711/deployments/eaton
docker compose up -d eaton-embeddings

# Verify it's running
curl http://localhost:9301/health
```

---

## 📂 File Structure

```
/home/christoph.bertsch/0711/0711-OS/mcps/eaton/
├── server.py       # MCP server implementation
├── start.sh        # Startup script
└── README.md       # This file
```

---

## 🔍 How It Works

```
Claude Desktop (Your Mac)
    ↓ (MCP Protocol via stdio)
EATON MCP Server (server.py)
    ↓ (HTTP API calls)
EATON Lakehouse Service (localhost:9302)
    ↓ (Reads from)
Docker Volumes
    ├── eaton-lakehouse-data/ (Delta Lake + LanceDB)
    └── customer-eaton/ (MinIO bucket)
```

---

## 📊 Data Sources

All data comes from the EATON customer deployment ingested on **November 25, 2025**:

- **617 files** uploaded to MinIO
- **10 file types**: XML, XLSX, PDF, CSV, JPG, STP, ZIP, XLSM
- **Key catalogs**:
  - ECLASS 13 Examples
  - Standard BMECat 2005 ETIM-10
  - PDH Extract
  - MediaAssets catalogs
  - 3D CAD models (STEP format)
  - ETIM guidelines

---

## 🎯 Use Cases

1. **Product Research** - "What UPS models are available?"
2. **Technical Support** - "What are the specs for this circuit breaker?"
3. **Catalog Browsing** - "Show me all 4-pole products"
4. **Knowledge Search** - "Find ECLASS classification examples"
5. **Data Discovery** - "What documents are in the system?"

---

## 🔒 Security Notes

- MCP server runs **locally on your machine**
- All data stays **within the 0711 platform**
- No external API calls (except to localhost:9302)
- Read-only access to EATON data
- No authentication required (localhost only)

---

## 📞 Support

**Issues?**
- Check EATON lakehouse: `curl http://localhost:9302/health`
- Check logs: Run `./start.sh` manually to see errors
- Verify containers: `docker ps | grep eaton`

**Want more MCPs?**
Create similar servers for other customers by copying this directory and changing the lakehouse URL.

---

**Version:** 1.0.0
**Customer:** EATON
**Data Updated:** 2025-11-25
**Platform:** 0711 Intelligence Platform
