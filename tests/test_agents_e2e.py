"""
E2E Tests for Concierge and Import Agent System

Tests the full flow:
1. Create sample BMECat XML and CSV test data
2. Initialize OnboardingWizard
3. Upload test files via wizard.upload_file()
4. Check file analysis results
5. Create Context Brief
6. Pass to ImportAgent.process_import()
7. Verify products are mapped to 0711 schema
8. Assert all fields mapped correctly
"""

import asyncio
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

# Import agents
from agents.concierge import OnboardingWizard, ConciergeAgent, ContextBrief
from agents.concierge.agent import FileType, BusinessType, UploadedFile
from agents.import_agent import ImportAgent
from agents.import_agent.parsers import BMECatParser, CSVParser, ParserFactory
from agents.import_agent.schema_mapper import SchemaMapper


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_bmecat_xml() -> bytes:
    """Create sample BMECat XML test data."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<BMECAT version="2005">
    <HEADER>
        <SUPPLIER>
            <SUPPLIER_NAME>Test Elektro GmbH</SUPPLIER_NAME>
        </SUPPLIER>
        <CATALOG>
            <LANGUAGE>deu</LANGUAGE>
            <CATALOG_ID>TEST2024</CATALOG_ID>
        </CATALOG>
    </HEADER>
    <T_NEW_CATALOG>
        <ARTICLE>
            <SUPPLIER_AID>EL-001</SUPPLIER_AID>
            <ARTICLE_DETAILS>
                <DESCRIPTION_SHORT>LED Einbauleuchte 10W</DESCRIPTION_SHORT>
                <DESCRIPTION_LONG>LED Einbauleuchte 10W warmweiss 3000K mit hoher Lichtausbeute</DESCRIPTION_LONG>
                <EAN>4012345678901</EAN>
                <MANUFACTURER_AID>MFR-LED-001</MANUFACTURER_AID>
                <MANUFACTURER_NAME>LightMaster AG</MANUFACTURER_NAME>
            </ARTICLE_DETAILS>
            <ARTICLE_ORDER_DETAILS>
                <ORDER_UNIT>PCE</ORDER_UNIT>
                <CONTENT_UNIT>PCE</CONTENT_UNIT>
                <NO_CU_PER_OU>1</NO_CU_PER_OU>
                <PRICE_QUANTITY>1</PRICE_QUANTITY>
            </ARTICLE_ORDER_DETAILS>
            <ARTICLE_PRICE_DETAILS>
                <ARTICLE_PRICE>
                    <PRICE_TYPE>net_list</PRICE_TYPE>
                    <PRICE_AMOUNT>24.90</PRICE_AMOUNT>
                    <PRICE_CURRENCY>EUR</PRICE_CURRENCY>
                </ARTICLE_PRICE>
            </ARTICLE_PRICE_DETAILS>
            <ARTICLE_REFERENCE type="etim_class">
                <ART_ID_TO>EC000003</ART_ID_TO>
            </ARTICLE_REFERENCE>
        </ARTICLE>
        <ARTICLE>
            <SUPPLIER_AID>EL-002</SUPPLIER_AID>
            <ARTICLE_DETAILS>
                <DESCRIPTION_SHORT>NYM-J 3x1,5 Kabel</DESCRIPTION_SHORT>
                <DESCRIPTION_LONG>Mantelleitung NYM-J 3x1,5mm2 grau 100m Ring</DESCRIPTION_LONG>
                <EAN>4012345678902</EAN>
                <MANUFACTURER_AID>MFR-NYM-002</MANUFACTURER_AID>
                <MANUFACTURER_NAME>KabelWerk GmbH</MANUFACTURER_NAME>
            </ARTICLE_DETAILS>
            <ARTICLE_ORDER_DETAILS>
                <ORDER_UNIT>M</ORDER_UNIT>
                <CONTENT_UNIT>M</CONTENT_UNIT>
                <NO_CU_PER_OU>100</NO_CU_PER_OU>
                <PRICE_QUANTITY>1</PRICE_QUANTITY>
            </ARTICLE_ORDER_DETAILS>
            <ARTICLE_PRICE_DETAILS>
                <ARTICLE_PRICE>
                    <PRICE_TYPE>net_list</PRICE_TYPE>
                    <PRICE_AMOUNT>89.50</PRICE_AMOUNT>
                    <PRICE_CURRENCY>EUR</PRICE_CURRENCY>
                </ARTICLE_PRICE>
            </ARTICLE_PRICE_DETAILS>
            <ARTICLE_REFERENCE type="etim_class">
                <ART_ID_TO>EC000001</ART_ID_TO>
            </ARTICLE_REFERENCE>
        </ARTICLE>
        <ARTICLE>
            <SUPPLIER_AID>EL-003</SUPPLIER_AID>
            <ARTICLE_DETAILS>
                <DESCRIPTION_SHORT>Lichtschalter Wippe weiss</DESCRIPTION_SHORT>
                <DESCRIPTION_LONG>Unterputz Lichtschalter mit Wippe in weiss, Rahmen separat</DESCRIPTION_LONG>
                <EAN>4012345678903</EAN>
                <MANUFACTURER_AID>MFR-SCH-003</MANUFACTURER_AID>
                <MANUFACTURER_NAME>Schaltbau AG</MANUFACTURER_NAME>
            </ARTICLE_DETAILS>
            <ARTICLE_ORDER_DETAILS>
                <ORDER_UNIT>PCE</ORDER_UNIT>
                <CONTENT_UNIT>PCE</CONTENT_UNIT>
            </ARTICLE_ORDER_DETAILS>
            <ARTICLE_PRICE_DETAILS>
                <ARTICLE_PRICE>
                    <PRICE_TYPE>net_list</PRICE_TYPE>
                    <PRICE_AMOUNT>5.95</PRICE_AMOUNT>
                    <PRICE_CURRENCY>EUR</PRICE_CURRENCY>
                </ARTICLE_PRICE>
            </ARTICLE_PRICE_DETAILS>
            <ARTICLE_REFERENCE type="etim_class">
                <ART_ID_TO>EC000002</ART_ID_TO>
            </ARTICLE_REFERENCE>
        </ARTICLE>
    </T_NEW_CATALOG>
</BMECAT>
"""


@pytest.fixture
def sample_csv_data() -> bytes:
    """Create sample CSV test data with German headers."""
    return b"""Artikelnummer;Bezeichnung;Langtext;EAN;Preis;Hersteller;ETIM_Klasse
CSV-001;Steckdose 2-fach;Unterputz Doppelsteckdose mit Kinderschutz;4012345678904;8.50;Schaltbau AG;EC000002
CSV-002;Sicherungsautomat B16;Leitungsschutzschalter B16A 1-polig;4012345678905;4.20;Hager GmbH;EC000001
CSV-003;LED Panel 40W;LED Panel 60x60cm 40W neutralweiss 4000K;4012345678906;45.00;LightMaster AG;EC000003
"""


@pytest.fixture
def lakehouse_path():
    """Provide temporary lakehouse path for tests."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Parser Tests
# ============================================================================

class TestParsers:
    """Test individual parsers."""

    def test_bmecat_parser_can_parse(self, sample_bmecat_xml):
        """Test BMECat parser detection."""
        parser = BMECatParser()
        assert parser.can_parse("catalog.xml", sample_bmecat_xml)
        assert not parser.can_parse("catalog.csv", sample_bmecat_xml)
        assert not parser.can_parse("catalog.xml", b"plain text")

    def test_bmecat_parser_analyze(self, sample_bmecat_xml):
        """Test BMECat file analysis."""
        parser = BMECatParser()
        result = parser.analyze(sample_bmecat_xml)

        assert result.success
        assert result.format_detected == "BMECat"
        assert result.version == "2005"
        assert result.record_count == 3
        assert "Test Elektro GmbH" in result.metadata.get("supplier", "")

    def test_bmecat_parser_parse(self, sample_bmecat_xml):
        """Test BMECat product parsing."""
        parser = BMECatParser()
        products = list(parser.parse(sample_bmecat_xml))

        assert len(products) == 3

        # Check first product
        p1 = products[0]
        assert p1["sku"] == "EL-001"
        assert p1["name"] == "LED Einbauleuchte 10W"
        assert p1["gtin"] == "4012345678901"
        assert p1["manufacturer"] == "LightMaster AG"
        assert p1["order_unit"] == "PCE"

        # Check price
        assert len(p1["prices"]) > 0
        assert p1["prices"][0]["amount"] == 24.90

        # Check classification
        assert p1["classifications"]["etim"] == "EC000003"

    def test_csv_parser_can_parse(self, sample_csv_data):
        """Test CSV parser detection."""
        parser = CSVParser()
        assert parser.can_parse("products.csv", sample_csv_data)
        assert not parser.can_parse("products.xml", sample_csv_data)

    def test_csv_parser_analyze(self, sample_csv_data):
        """Test CSV file analysis."""
        parser = CSVParser()
        result = parser.analyze(sample_csv_data)

        assert result.success
        assert result.format_detected == "CSV"
        assert result.record_count == 3
        assert result.metadata["delimiter"] == ";"
        assert "Artikelnummer" in result.fields
        assert "Bezeichnung" in result.fields

        # Check field suggestions
        suggestions = result.metadata.get("field_suggestions", {})
        assert "Artikelnummer" in suggestions
        assert suggestions["Artikelnummer"] == "sku"

    def test_csv_parser_parse(self, sample_csv_data):
        """Test CSV product parsing."""
        parser = CSVParser()
        products = list(parser.parse(sample_csv_data))

        assert len(products) == 3

        # Check first product
        p1 = products[0]
        assert p1["Artikelnummer"] == "CSV-001"
        assert p1["Bezeichnung"] == "Steckdose 2-fach"
        assert p1["EAN"] == "4012345678904"
        assert p1["Preis"] == "8.50"

    def test_parser_factory(self, sample_bmecat_xml, sample_csv_data):
        """Test parser factory."""
        # BMECat
        parser = ParserFactory.get_parser("catalog.xml", sample_bmecat_xml)
        assert isinstance(parser, BMECatParser)

        # CSV
        parser = ParserFactory.get_parser("products.csv", sample_csv_data)
        assert isinstance(parser, CSVParser)

        # Unknown
        parser = ParserFactory.get_parser("unknown.txt", b"random data")
        assert parser is None


# ============================================================================
# Schema Mapper Tests
# ============================================================================

class TestSchemaMapper:
    """Test schema mapper functionality."""

    def test_detect_field_mapping_german(self):
        """Test field mapping with German headers."""
        mapper = SchemaMapper()
        fields = ["Artikelnummer", "Bezeichnung", "EAN", "Preis", "Hersteller"]

        mappings = mapper.detect_field_mapping(fields)

        assert "Artikelnummer" in mappings
        assert mappings["Artikelnummer"].target_field == "sku"

        assert "Bezeichnung" in mappings
        assert mappings["Bezeichnung"].target_field == "name"

        assert "EAN" in mappings
        assert mappings["EAN"].target_field == "gtin"

    def test_detect_field_mapping_english(self):
        """Test field mapping with English headers."""
        mapper = SchemaMapper()
        fields = ["product_id", "name", "gtin", "price_net", "manufacturer"]

        mappings = mapper.detect_field_mapping(fields)

        assert "product_id" in mappings
        assert mappings["product_id"].target_field == "sku"

        assert "name" in mappings
        assert mappings["name"].target_field == "name"

    def test_map_product(self):
        """Test product mapping to 0711 schema."""
        mapper = SchemaMapper()

        source_data = {
            "_source": "csv",
            "Artikelnummer": "TEST-001",
            "Bezeichnung": "Test Product",
            "EAN": "1234567890123",
            "Preis": "12.50",
            "custom_field": "custom value"
        }

        mappings = mapper.detect_field_mapping(list(source_data.keys()))
        product = mapper.map_product(source_data, mappings)

        assert product["sku"] == "TEST-001"
        assert product["name"] == "Test Product"
        assert product["gtin"] == "1234567890123"
        assert product["_source"] == "csv"
        assert "_extra" in product
        assert product["_extra"]["custom_field"] == "custom value"

    def test_transform_german_number(self):
        """Test German number format transformation."""
        mapper = SchemaMapper()

        # German format: 1.234,56
        assert mapper._to_float("1.234,56") == 1234.56

        # Standard format
        assert mapper._to_float("1234.56") == 1234.56

        # German with comma decimal
        assert mapper._to_float("12,50") == 12.50

    def test_validate_product(self):
        """Test product validation."""
        mapper = SchemaMapper()

        # Valid product
        valid_product = {
            "sku": "TEST-001",
            "name": "Test Product"
        }
        is_valid, errors = mapper.validate_product(valid_product)
        assert is_valid
        assert len(errors) == 0

        # Missing required field
        invalid_product = {
            "name": "Test Product"
        }
        is_valid, errors = mapper.validate_product(invalid_product)
        assert not is_valid
        assert any("sku" in e for e in errors)


# ============================================================================
# Concierge Agent Tests
# ============================================================================

class TestConciergeAgent:
    """Test Concierge Agent functionality."""

    @pytest.mark.asyncio
    async def test_analyze_bmecat_file(self, sample_bmecat_xml):
        """Test file analysis for BMECat."""
        customer_id = uuid4()
        agent = ConciergeAgent(customer_id)

        result = await agent.analyze_file("catalog.xml", sample_bmecat_xml)

        assert isinstance(result, UploadedFile)
        assert result.filename == "catalog.xml"
        assert result.file_type == FileType.BMECAT_XML
        assert result.size_bytes == len(sample_bmecat_xml)
        assert result.quality_score > 0

    @pytest.mark.asyncio
    async def test_analyze_csv_file(self, sample_csv_data):
        """Test file analysis for CSV."""
        customer_id = uuid4()
        agent = ConciergeAgent(customer_id)

        result = await agent.analyze_file("products.csv", sample_csv_data)

        assert isinstance(result, UploadedFile)
        assert result.filename == "products.csv"
        assert result.file_type == FileType.CSV_PRODUCTS
        assert result.record_count == 3

    def test_detect_file_type(self, sample_bmecat_xml, sample_csv_data):
        """Test file type detection."""
        customer_id = uuid4()
        agent = ConciergeAgent(customer_id)

        assert agent._detect_file_type("catalog.xml", sample_bmecat_xml) == FileType.BMECAT_XML
        assert agent._detect_file_type("products.csv", sample_csv_data) == FileType.CSV_PRODUCTS
        assert agent._detect_file_type("images.zip", b"PK...") == FileType.IMAGES_ZIP
        assert agent._detect_file_type("catalog.pdf", b"%PDF") == FileType.PDF_CATALOG


# ============================================================================
# Onboarding Wizard Tests
# ============================================================================

class TestOnboardingWizard:
    """Test Onboarding Wizard functionality."""

    @pytest.mark.asyncio
    async def test_wizard_initialization(self):
        """Test wizard initialization."""
        customer_id = uuid4()
        wizard = OnboardingWizard(customer_id)

        state = wizard.get_state()

        assert state.customer_id == customer_id
        assert state.current_step == 0
        assert len(state.steps) == 8
        assert state.steps[0].is_current
        assert state.steps[0].id == "welcome"

    @pytest.mark.asyncio
    async def test_wizard_upload_file(self, sample_bmecat_xml):
        """Test file upload through wizard."""
        wizard = OnboardingWizard()

        result = await wizard.upload_file("catalog.xml", sample_bmecat_xml)

        assert "file" in result
        assert result["file"]["filename"] == "catalog.xml"
        assert result["file"]["type"] == "bmecat_xml"
        assert result["total_files"] == 1

        # Check wizard state updated
        assert len(wizard.uploaded_files) == 1

    @pytest.mark.asyncio
    async def test_wizard_upload_multiple_files(self, sample_bmecat_xml, sample_csv_data):
        """Test uploading multiple files."""
        wizard = OnboardingWizard()

        result1 = await wizard.upload_file("catalog.xml", sample_bmecat_xml)
        result2 = await wizard.upload_file("products.csv", sample_csv_data)

        assert result1["total_files"] == 1
        assert result2["total_files"] == 2
        assert len(wizard.uploaded_files) == 2

    @pytest.mark.asyncio
    async def test_wizard_generates_suggestions(self, sample_bmecat_xml):
        """Test connector suggestions are generated after file upload."""
        wizard = OnboardingWizard()

        result = await wizard.upload_file("catalog.xml", sample_bmecat_xml)

        suggestions = result.get("connector_suggestions", [])
        assert len(suggestions) > 0

        # Should suggest DATANORM for product data
        suggestion_ids = [s["id"] for s in suggestions]
        assert "datanorm" in suggestion_ids

    @pytest.mark.asyncio
    async def test_wizard_step_navigation(self):
        """Test wizard step navigation."""
        wizard = OnboardingWizard()

        # Go to next step
        result = await wizard.next_step()
        assert wizard.current_step == 1
        assert wizard.steps[1].is_current
        assert wizard.steps[0].is_complete

        # Go back
        result = await wizard.previous_step()
        assert wizard.current_step == 0
        assert wizard.steps[0].is_current

    @pytest.mark.asyncio
    async def test_wizard_start_import(self, sample_bmecat_xml):
        """Test starting import from wizard."""
        wizard = OnboardingWizard()

        # Upload file first
        await wizard.upload_file("catalog.xml", sample_bmecat_xml)

        # Start import
        result = await wizard.start_import()

        assert "import_job_id" in result
        assert result["status"] == "started"


# ============================================================================
# Import Agent Tests
# ============================================================================

class TestImportAgent:
    """Test Import Agent functionality."""

    @pytest.mark.asyncio
    async def test_import_agent_initialization(self, lakehouse_path):
        """Test Import Agent initialization."""
        agent = ImportAgent(lakehouse_path=lakehouse_path)

        assert agent.lakehouse_path == lakehouse_path
        assert len(agent.category_tree) > 0

    @pytest.mark.asyncio
    async def test_parse_bmecat_file(self, sample_bmecat_xml, lakehouse_path):
        """Test parsing BMECat file."""
        agent = ImportAgent(lakehouse_path=lakehouse_path)

        products = await agent._parse_file("catalog.xml", sample_bmecat_xml)

        assert len(products) == 3
        assert products[0]["_source"] == "bmecat"
        assert "supplier_aid" in products[0] or "sku" in products[0]

    @pytest.mark.asyncio
    async def test_parse_csv_file(self, sample_csv_data, lakehouse_path):
        """Test parsing CSV file."""
        agent = ImportAgent(lakehouse_path=lakehouse_path)

        products = await agent._parse_file("products.csv", sample_csv_data)

        assert len(products) == 3
        assert products[0]["_source"] == "csv"

    @pytest.mark.asyncio
    async def test_map_product_to_0711_schema(self, sample_bmecat_xml, lakehouse_path):
        """Test mapping products to 0711 schema."""
        agent = ImportAgent(lakehouse_path=lakehouse_path)
        customer_id = uuid4()

        # Parse first
        raw_products = await agent._parse_file("catalog.xml", sample_bmecat_xml)

        # Map first product
        context_brief = {
            "customer_id": str(customer_id),
            "business_type": "b2b_distributor",
            "industry": "Elektro"
        }

        product = await agent._map_to_0711_schema(
            raw_products[0],
            customer_id,
            {},  # field hints
            context_brief
        )

        # Check mapping
        assert product.customer_id == customer_id
        assert product.sku == "EL-001"
        assert product.name == "LED Einbauleuchte 10W"
        assert product.gtin == "4012345678901"
        assert product.etim_class == "EC000003"
        assert product.source_format == "bmecat"


# ============================================================================
# Full E2E Test
# ============================================================================

class TestE2EAgentFlow:
    """Full E2E test of Concierge -> Import Agent flow."""

    @pytest.mark.asyncio
    async def test_full_onboarding_flow_bmecat(self, sample_bmecat_xml, lakehouse_path):
        """Test complete onboarding flow with BMECat data."""
        customer_id = uuid4()

        # Step 1: Initialize wizard
        wizard = OnboardingWizard(customer_id)
        assert wizard.current_step == 0

        # Step 2: Upload BMECat file
        upload_result = await wizard.upload_file("catalog.xml", sample_bmecat_xml)

        assert upload_result["file"]["type"] == "bmecat_xml"
        assert upload_result["total_files"] == 1
        assert len(wizard.uploaded_files) == 1

        # Step 3: Check file analysis
        uploaded_file = wizard.uploaded_files[0]
        assert uploaded_file.file_type == FileType.BMECAT_XML
        assert uploaded_file.quality_score > 0

        # Step 4: Create context brief
        wizard.agent.company_profile = {
            "company_name": "Test Elektro GmbH",
            "business_type": "b2b_distributor",
            "industry": "Elektro",
            "product_count": 3
        }
        brief = wizard.agent._create_context_brief()

        assert isinstance(brief, ContextBrief)
        assert brief.customer_id == customer_id
        assert brief.company_name == "Test Elektro GmbH"
        assert brief.business_type == BusinessType.B2B_DISTRIBUTOR

        # Step 5: Pass to Import Agent
        import_agent = ImportAgent(lakehouse_path=lakehouse_path)

        context_brief_dict = {
            "customer_id": str(customer_id),
            "company_name": brief.company_name,
            "business_type": brief.business_type.value,
            "industry": brief.industry,
            "field_mapping_hints": {},
            "notes": "Test import"
        }

        files = {"catalog.xml": sample_bmecat_xml}

        progress = await import_agent.process_import(context_brief_dict, files)

        # Step 6: Verify results
        assert progress.total_records == 3
        assert progress.processed_records == 3
        assert progress.current_phase.value == "complete"

        # Step 7: Check products mapped correctly
        assert len(import_agent.products) == 3

        p1 = import_agent.products[0]
        assert p1.sku == "EL-001"
        assert p1.name == "LED Einbauleuchte 10W"
        assert p1.gtin == "4012345678901"
        assert p1.etim_class == "EC000003"
        assert p1.category_id is not None
        assert len(p1.category_path) > 0

        p2 = import_agent.products[1]
        assert p2.sku == "EL-002"
        assert p2.etim_class == "EC000001"

        p3 = import_agent.products[2]
        assert p3.sku == "EL-003"
        assert p3.etim_class == "EC000002"

    @pytest.mark.asyncio
    async def test_full_onboarding_flow_csv(self, sample_csv_data, lakehouse_path):
        """Test complete onboarding flow with CSV data."""
        customer_id = uuid4()

        # Step 1: Initialize wizard
        wizard = OnboardingWizard(customer_id)

        # Step 2: Upload CSV file
        upload_result = await wizard.upload_file("products.csv", sample_csv_data)

        assert upload_result["file"]["type"] == "csv_products"
        assert upload_result["file"]["records"] == 3

        # Step 3: Check analysis
        uploaded_file = wizard.uploaded_files[0]
        assert uploaded_file.file_type == FileType.CSV_PRODUCTS
        assert uploaded_file.record_count == 3

        # Step 4: Create context brief
        wizard.agent.company_profile = {
            "company_name": "CSV Test GmbH",
            "business_type": "b2b_distributor",
            "industry": "Elektro",
            "product_count": 3
        }
        brief = wizard.agent._create_context_brief()

        # Step 5: Import with Import Agent
        import_agent = ImportAgent(lakehouse_path=lakehouse_path)

        context_brief_dict = {
            "customer_id": str(customer_id),
            "company_name": brief.company_name,
            "business_type": brief.business_type.value,
            "industry": brief.industry,
            "field_mapping_hints": {
                "Artikelnummer": "sku",
                "Bezeichnung": "name",
                "Langtext": "description_long",
                "EAN": "gtin",
                "Preis": "price_net",
                "Hersteller": "manufacturer",
                "ETIM_Klasse": "etim_class"
            },
            "notes": "CSV Test import"
        }

        files = {"products.csv": sample_csv_data}

        progress = await import_agent.process_import(context_brief_dict, files)

        # Step 6: Verify results
        assert progress.total_records == 3
        assert progress.processed_records == 3

        # Step 7: Check products
        assert len(import_agent.products) == 3

        p1 = import_agent.products[0]
        assert p1.sku == "CSV-001"
        assert p1.name == "Steckdose 2-fach"
        assert p1.gtin == "4012345678904"

    @pytest.mark.asyncio
    async def test_full_flow_mixed_files(self, sample_bmecat_xml, sample_csv_data, lakehouse_path):
        """Test onboarding with both BMECat and CSV files."""
        customer_id = uuid4()

        # Initialize
        wizard = OnboardingWizard(customer_id)

        # Upload both files
        result1 = await wizard.upload_file("catalog.xml", sample_bmecat_xml)
        result2 = await wizard.upload_file("products.csv", sample_csv_data)

        assert len(wizard.uploaded_files) == 2

        # Create context brief
        wizard.agent.company_profile = {
            "company_name": "Mixed Test GmbH",
            "business_type": "b2b_distributor",
            "industry": "Elektro",
            "product_count": 6
        }
        brief = wizard.agent._create_context_brief()

        # Import
        import_agent = ImportAgent(lakehouse_path=lakehouse_path)

        context_brief_dict = {
            "customer_id": str(customer_id),
            "company_name": brief.company_name,
            "business_type": brief.business_type.value,
            "industry": brief.industry,
            "field_mapping_hints": {
                "Artikelnummer": "sku",
                "Bezeichnung": "name",
                "Langtext": "description_long",
                "EAN": "gtin",
                "Preis": "price_net",
            },
            "notes": "Mixed files test"
        }

        files = {
            "catalog.xml": sample_bmecat_xml,
            "products.csv": sample_csv_data
        }

        progress = await import_agent.process_import(context_brief_dict, files)

        # Should have all 6 products (3 from each file)
        assert progress.total_records == 6
        assert len(import_agent.products) == 6

        # Check both sources represented
        sources = {p.source_format for p in import_agent.products}
        assert "bmecat" in sources
        assert "csv" in sources

    @pytest.mark.asyncio
    async def test_import_writes_to_lakehouse(self, sample_bmecat_xml, lakehouse_path):
        """Test that import correctly writes to lakehouse."""
        customer_id = uuid4()

        import_agent = ImportAgent(lakehouse_path=lakehouse_path)

        context_brief_dict = {
            "customer_id": str(customer_id),
            "company_name": "Lakehouse Test",
            "business_type": "b2b_distributor",
            "industry": "Elektro",
            "field_mapping_hints": {},
            "notes": ""
        }

        files = {"catalog.xml": sample_bmecat_xml}

        await import_agent.process_import(context_brief_dict, files)

        # Check lakehouse structure
        customer_path = lakehouse_path / str(customer_id)
        assert customer_path.exists()

        products_path = customer_path / "products"
        assert products_path.exists()

        # Find import file
        import_files = list(products_path.glob("import_*.json"))
        assert len(import_files) == 1

        # Verify content
        with open(import_files[0]) as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]["sku"] == "EL-001"
        assert data[0]["name"] == "LED Einbauleuchte 10W"
        assert data[0]["etim_class"] == "EC000003"

    @pytest.mark.asyncio
    async def test_validation_flags_incomplete_products(self, lakehouse_path):
        """Test that validation flags products with issues."""
        customer_id = uuid4()

        # Create CSV with missing data
        incomplete_csv = b"""Artikelnummer;Bezeichnung
INC-001;Product without price
INC-002;
"""

        import_agent = ImportAgent(lakehouse_path=lakehouse_path)

        context_brief_dict = {
            "customer_id": str(customer_id),
            "company_name": "Validation Test",
            "business_type": "b2b_distributor",
            "industry": "Elektro",
            "field_mapping_hints": {
                "Artikelnummer": "sku",
                "Bezeichnung": "name"
            },
            "notes": ""
        }

        files = {"incomplete.csv": incomplete_csv}

        progress = await import_agent.process_import(context_brief_dict, files)

        # All products should need review due to missing price
        assert progress.needs_review > 0

        # Check review reasons
        for product in import_agent.products:
            if product.needs_review:
                assert len(product.review_reasons) > 0


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in agents."""

    @pytest.mark.asyncio
    async def test_invalid_xml_handling(self, lakehouse_path):
        """Test handling of invalid XML."""
        invalid_xml = b"<invalid><not closed"

        import_agent = ImportAgent(lakehouse_path=lakehouse_path)

        # Should not crash, returns empty list
        products = await import_agent._parse_file("bad.xml", invalid_xml)
        assert products == []

    @pytest.mark.asyncio
    async def test_empty_csv_handling(self, lakehouse_path):
        """Test handling of empty CSV."""
        empty_csv = b"header1;header2\n"

        import_agent = ImportAgent(lakehouse_path=lakehouse_path)
        products = await import_agent._parse_file("empty.csv", empty_csv)
        assert products == []

    def test_unknown_file_type(self):
        """Test handling of unknown file types."""
        customer_id = uuid4()
        agent = ConciergeAgent(customer_id)

        result = agent._detect_file_type("unknown.xyz", b"random content")
        assert result == FileType.UNKNOWN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
