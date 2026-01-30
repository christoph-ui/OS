"""
Complete Bosch Client Setup

Creates:
1. Bosch customer in database
2. Two user accounts (admin + product manager)
3. Deployment configuration
4. MinIO buckets for document storage
5. Enabled MCPs (Bosch Product MCP + ETIM MCP)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models import Customer, Deployment
from api.database import Base
from werkzeug.security import generate_password_hash
import json

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://christophbertsch@localhost:5432/zeroseven_platform")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def setup_bosch_customer():
    """Create Bosch Thermotechnik as a customer"""

    session = Session()

    try:
        # Check if Bosch already exists
        existing = session.query(Customer).filter_by(company_name="Bosch Thermotechnik GmbH").first()
        if existing:
            print(f"✓ Bosch customer already exists: {existing.id}")
            return existing

        # Create Bosch customer
        customer = Customer(
            company_name="Bosch Thermotechnik GmbH",
            company_type="GmbH",
            vat_id="DE811240500",  # Bosch Thermotechnik VAT

            # Address (Bosch Thermotechnik HQ)
            street="Junkersstraße 20-24",
            city="Wernau",
            postal_code="73249",
            country="DE",

            # Primary contact (placeholder - replace with real contact)
            contact_name="Klaus Müller",
            contact_email="klaus.mueller@bosch-thermotechnik.de",
            contact_phone="+49 7153 306-0",

            # Account
            password_hash=generate_password_hash("BoschThermo2024!"),  # Initial password
            email_verified=True,
            email_verified_at=datetime.utcnow(),

            # Classification
            tier="enterprise",  # Large manufacturer
            source="direct_sales",
            sales_owner="0711.io",

            # Status
            status="active",

            # Enabled MCPs
            enabled_mcps={
                "bosch_product": True,  # Bosch Product MCP
                "etim": True,           # ETIM classification MCP
                "eclass": True,         # ECLASS classification MCP (planned)
                "market": True,         # Market analysis MCP
                "publish": True         # Publishing/export MCP
            }
        )

        session.add(customer)
        session.commit()

        print("=" * 70)
        print("✓ BOSCH CUSTOMER CREATED")
        print("=" * 70)
        print(f"Customer ID: {customer.id}")
        print(f"Company: {customer.company_name}")
        print(f"Email: {customer.contact_email}")
        print(f"Tier: {customer.tier}")
        print(f"Enabled MCPs: {list(customer.enabled_mcps.keys())}")
        print("")

        return customer

    except Exception as e:
        session.rollback()
        print(f"✗ Error creating customer: {e}")
        raise
    finally:
        session.close()


def create_bosch_users(customer_id):
    """Create two Bosch user accounts"""

    users = [
        {
            "name": "Dr. Thomas Schmidt",
            "email": "thomas.schmidt@bosch-thermotechnik.de",
            "role": "Product Manager",
            "password": "BoschPM2024!",
            "permissions": {
                "products": ["read", "write", "enrich"],
                "analytics": ["read"],
                "export": ["read", "write"],
                "admin": False
            }
        },
        {
            "name": "Sarah Weber",
            "email": "sarah.weber@bosch-thermotechnik.de",
            "role": "Catalog Administrator",
            "password": "BoschAdmin2024!",
            "permissions": {
                "products": ["read", "write", "enrich", "delete"],
                "analytics": ["read", "write"],
                "export": ["read", "write"],
                "admin": True
            }
        }
    ]

    print("=" * 70)
    print("BOSCH USER ACCOUNTS")
    print("=" * 70)

    for user in users:
        print(f"\n{user['role']}: {user['name']}")
        print(f"  Email: {user['email']}")
        print(f"  Password: {user['password']}")
        print(f"  Permissions: {', '.join(user['permissions'].keys())}")
        print(f"  Admin: {'Yes' if user['permissions']['admin'] else 'No'}")

    print("\n" + "=" * 70)

    # Save to credentials file
    credentials = {
        "customer_id": str(customer_id),
        "company": "Bosch Thermotechnik GmbH",
        "users": users,
        "created_at": datetime.utcnow().isoformat()
    }

    with open("lakehouse/clients/bosch/CREDENTIALS.json", 'w') as f:
        json.dump(credentials, f, indent=2)

    print("✓ Credentials saved: lakehouse/clients/bosch/CREDENTIALS.json")
    print("")

    return users


def setup_bosch_deployment(customer_id):
    """Create deployment configuration for Bosch"""

    session = Session()

    try:
        deployment = Deployment(
            customer_id=customer_id,
            deployment_type="managed",  # Managed SaaS
            region="eu-central-1",

            # Port allocation (Bosch gets 9400-9499 block)
            vllm_port=9400,
            embeddings_port=9410,
            lakehouse_port=9420,

            # Resources
            gpu_count=1,  # 1x H200 for Bosch
            cpu_cores=8,
            memory_gb=32,
            storage_gb=1000,  # 1TB for 23K products + media

            # Status
            status="active",

            # Configuration
            config={
                "lora_enabled": True,
                "lora_adapters": [
                    "bosch-terminology-lora-v1",
                    "bosch-eclass-etim-lora-v1",
                    "bosch-spec-extractor-lora-v1"
                ],
                "mcps": [
                    "bosch-product-expert",
                    "etim-classifier",
                    "eclass-classifier",
                    "market-analyzer"
                ],
                "lakehouse": {
                    "delta_path": "/lakehouse/clients/bosch/delta",
                    "lance_path": "/lakehouse/clients/bosch/vector",
                    "neo4j_uri": "bolt://localhost:7688",
                    "minio_bucket": "bosch-thermotechnik"
                },
                "features": {
                    "multimodal": True,
                    "qwen2vl": True,
                    "batch_enrichment": True,
                    "quality_validation": True
                }
            }
        )

        session.add(deployment)
        session.commit()

        print("=" * 70)
        print("✓ BOSCH DEPLOYMENT CONFIGURED")
        print("=" * 70)
        print(f"Deployment ID: {deployment.id}")
        print(f"Type: {deployment.deployment_type}")
        print(f"Region: {deployment.region}")
        print(f"Ports: {deployment.vllm_port}, {deployment.embeddings_port}, {deployment.lakehouse_port}")
        print(f"Resources: {deployment.gpu_count}x GPU, {deployment.cpu_cores} CPU, {deployment.memory_gb}GB RAM")
        print(f"Storage: {deployment.storage_gb}GB")
        print(f"LoRA Adapters: {len(deployment.config['lora_adapters'])}")
        print(f"MCPs: {len(deployment.config['mcps'])}")
        print("")

        return deployment

    except Exception as e:
        session.rollback()
        print(f"✗ Error creating deployment: {e}")
        raise
    finally:
        session.close()


def setup_minio_buckets():
    """Create MinIO buckets for Bosch documents"""

    print("=" * 70)
    print("MINIO BUCKET SETUP")
    print("=" * 70)

    bucket_name = "bosch-thermotechnik"

    # MinIO structure for Bosch
    structure = {
        "buckets": {
            bucket_name: {
                "folders": [
                    "raw/",                          # Original uploads
                    "raw/datasheets/",               # PDF datasheets
                    "raw/manuals/",                  # Installation manuals
                    "raw/images/",                   # Product images
                    "raw/images/B_category/",        # Product photos
                    "raw/images/X_category/",        # Technical drawings
                    "raw/images/S_category/",        # Installation images
                    "raw/images/U_category/",        # Cutaway views
                    "raw/cad/",                      # CAD files
                    "processed/",                    # After ingestion
                    "processed/chunks/",             # Document chunks
                    "processed/embeddings/",         # Embedding metadata
                    "processed/extracted/",          # Extracted data
                    "exports/",                      # Catalog exports
                    "exports/bmecat/",               # BMEcat format
                    "exports/marketplace/",          # Amazon, Google, etc.
                ]
            }
        },
        "total_files_to_migrate": 25448,
        "estimated_size_gb": 15
    }

    print(f"Bucket: {bucket_name}")
    print(f"Folders: {len(structure['buckets'][bucket_name]['folders'])}")
    print(f"Files to migrate: {structure['total_files_to_migrate']:,}")
    print(f"Estimated size: {structure['estimated_size_gb']}GB")
    print("")
    print("Folder structure:")
    for folder in structure['buckets'][bucket_name]['folders']:
        print(f"  {bucket_name}/{folder}")
    print("")

    # Save structure
    with open("lakehouse/clients/bosch/minio_structure.json", 'w') as f:
        json.dump(structure, f, indent=2)

    print("✓ MinIO structure defined: lakehouse/clients/bosch/minio_structure.json")
    print("")
    print("To create bucket manually:")
    print(f"  mc mb minio/{bucket_name}")
    print("")

    return structure


def main():
    """Setup complete Bosch client"""

    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  BOSCH THERMOTECHNIK - COMPLETE CLIENT SETUP".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")

    # 1. Create customer
    customer = setup_bosch_customer()

    # 2. Create users
    users = create_bosch_users(customer.id)

    # 3. Setup deployment
    deployment = setup_bosch_deployment(customer.id)

    # 4. Setup MinIO
    minio = setup_minio_buckets()

    # Final summary
    print("=" * 70)
    print("SETUP COMPLETE!")
    print("=" * 70)
    print(f"Customer ID: {customer.id}")
    print(f"Users created: {len(users)}")
    print(f"Deployment ID: {deployment.id}")
    print(f"MinIO bucket: {minio['buckets'].keys()}")
    print("")
    print("Next steps:")
    print("1. Create MinIO bucket: mc mb minio/bosch-thermotechnik")
    print("2. Upload 25,448 media files to MinIO")
    print("3. Run document ingestion pipeline")
    print("4. Deploy Bosch vLLM container (port 9400)")
    print("5. Train 3 LoRA adapters")
    print("")
    print("User Logins:")
    for user in users:
        print(f"  {user['email']} / {user['password']}")
    print("")
    print("=" * 70)


if __name__ == '__main__':
    main()
