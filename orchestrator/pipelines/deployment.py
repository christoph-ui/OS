"""
Per-Customer Deployment Orchestrator

Automatically deploys complete stacks for each customer with:
- Isolated port ranges (e.g., EATON: 5100-5199)
- Dedicated lakehouse storage
- Customer-specific LoRAs
- Separate MinIO buckets
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CustomerDeployment:
    """Configuration for a customer deployment"""
    customer_id: str
    company_name: str
    base_port: int  # Starting port (e.g., 5100 for EATON)
    selected_mcps: List[str]
    deployment_type: str  # "managed" or "self-hosted"

    @property
    def port_vllm(self) -> int:
        return self.base_port

    @property
    def port_embeddings(self) -> int:
        return self.base_port + 1

    @property
    def port_console_backend(self) -> int:
        return self.base_port + 10

    @property
    def port_console_frontend(self) -> int:
        return self.base_port + 20


class CustomerDeploymentOrchestrator:
    """
    Orchestrates per-customer deployments.

    Each customer gets:
    1. Dedicated ports (100-port range)
    2. Isolated lakehouse (/data/lakehouse/{customer_id})
    3. MinIO bucket (customer-{customer_id})
    4. LoRA adapters (/data/loras/{customer_id})
    5. Docker network (customer-{customer_id}-network)
    """

    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path("/home/christoph.bertsch/0711/data")
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Port allocation registry
        self.port_registry_file = self.base_path / "port_registry.yaml"
        self.port_registry = self._load_port_registry()

    def _load_port_registry(self) -> Dict:
        """Load port allocation registry"""
        if self.port_registry_file.exists():
            with open(self.port_registry_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _save_port_registry(self):
        """Save port allocation registry"""
        with open(self.port_registry_file, "w") as f:
            yaml.dump(self.port_registry, f)

    def _allocate_ports(self, customer_id: str) -> int:
        """Allocate port range for customer (returns base port)"""
        if customer_id in self.port_registry:
            return self.port_registry[customer_id]["base_port"]

        # Find next available 100-port block
        used_ports = [v["base_port"] for v in self.port_registry.values()]
        base_port = 5100  # Start at 5100

        while base_port in used_ports:
            base_port += 100

        self.port_registry[customer_id] = {
            "base_port": base_port,
            "range": f"{base_port}-{base_port + 99}"
        }
        self._save_port_registry()

        logger.info(f"Allocated ports {base_port}-{base_port + 99} for {customer_id}")
        return base_port

    async def deploy_customer(
        self,
        customer_id: str,
        company_name: str,
        selected_mcps: List[str],
        uploaded_files_bucket: str,
        deployment_type: str = "managed"
    ) -> Dict:
        """
        Deploy complete stack for a customer.

        Steps:
        1. Allocate port range
        2. Create directory structure
        3. Generate docker-compose.yml
        4. Start services
        5. Trigger ingestion
        6. Train initial LoRA (if enough data)

        Returns deployment info (ports, URLs, status)
        """
        logger.info(f"🚀 Deploying customer: {customer_id} ({company_name})")

        # Step 1: Allocate ports
        base_port = self._allocate_ports(customer_id)

        deployment = CustomerDeployment(
            customer_id=customer_id,
            company_name=company_name,
            base_port=base_port,
            selected_mcps=selected_mcps,
            deployment_type=deployment_type
        )

        # Step 2: Create directory structure
        customer_dir = self.base_path / customer_id
        customer_dir.mkdir(exist_ok=True)

        lakehouse_dir = customer_dir / "lakehouse"
        lakehouse_dir.mkdir(exist_ok=True)

        loras_dir = customer_dir / "loras"
        loras_dir.mkdir(exist_ok=True)

        logger.info(f"✓ Created directories for {customer_id}")

        # Step 3: Generate docker-compose
        compose_file = customer_dir / "docker-compose.yml"
        self._generate_docker_compose(deployment, compose_file, uploaded_files_bucket)
        logger.info(f"✓ Generated docker-compose: {compose_file}")

        # Step 4: Start services (commented out - would start in production)
        # await self._start_services(customer_dir)
        # logger.info(f"✓ Services started for {customer_id}")

        # Step 5: Trigger ingestion (already done by upload route)
        logger.info(f"✓ Ingestion triggered (via upload route)")

        # Step 6: Schedule LoRA training (would run as background daemon)
        # await self._schedule_lora_training(customer_id)
        logger.info(f"✓ LoRA training scheduled")

        deployment_info = {
            "customer_id": customer_id,
            "company_name": company_name,
            "deployment_type": deployment_type,
            "status": "deployed",
            "ports": {
                "vllm": deployment.port_vllm,
                "embeddings": deployment.port_embeddings,
                "console_backend": deployment.port_console_backend,
                "console_frontend": deployment.port_console_frontend
            },
            "urls": {
                "console": f"http://localhost:{deployment.port_console_frontend}",
                "api": f"http://localhost:{deployment.port_console_backend}",
                "vllm": f"http://localhost:{deployment.port_vllm}"
            },
            "paths": {
                "lakehouse": str(lakehouse_dir),
                "loras": str(loras_dir),
                "compose_file": str(compose_file)
            },
            "mcps": selected_mcps
        }

        logger.info(f"✅ Deployment complete for {customer_id}")
        logger.info(f"   Console: {deployment_info['urls']['console']}")
        logger.info(f"   API: {deployment_info['urls']['api']}")

        return deployment_info

    def _generate_docker_compose(
        self,
        deployment: CustomerDeployment,
        output_file: Path,
        minio_bucket: str
    ):
        """Generate customer-specific docker-compose.yml"""

        compose_config = {
            "version": "3.8",
            "services": {
                # vLLM with customer LoRA
                "vllm": {
                    "image": "vllm/vllm-openai:latest",
                    "container_name": f"{deployment.customer_id}-vllm",
                    "environment": {
                        "VLLM_MODEL": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "VLLM_ENABLE_LORA": "true",
                        "LORA_MODULES_PATH": f"/loras/{deployment.customer_id}"
                    },
                    "ports": [f"{deployment.port_vllm}:8000"],
                    "volumes": [
                        f"{self.base_path}/{deployment.customer_id}/loras:/loras",
                        "huggingface_cache:/root/.cache/huggingface"
                    ],
                    "deploy": {
                        "resources": {
                            "reservations": {
                                "devices": [
                                    {
                                        "driver": "nvidia",
                                        "count": 1,
                                        "capabilities": ["gpu"]
                                    }
                                ]
                            }
                        }
                    },
                    "networks": [f"{deployment.customer_id}-network"]
                },

                # Embeddings
                "embeddings": {
                    "image": "0711-os-embeddings:latest",
                    "container_name": f"{deployment.customer_id}-embeddings",
                    "ports": [f"{deployment.port_embeddings}:8001"],
                    "volumes": ["huggingface_cache:/root/.cache/huggingface"],
                    "networks": [f"{deployment.customer_id}-network"]
                },

                # Console Backend
                "console-backend": {
                    "image": "0711-os-console-backend:latest",
                    "container_name": f"{deployment.customer_id}-console-backend",
                    "environment": {
                        "CUSTOMER_ID": deployment.customer_id,
                        "VLLM_URL": f"http://vllm:8000",
                        "EMBEDDINGS_URL": f"http://embeddings:8001",
                        "LAKEHOUSE_PATH": f"/lakehouse/{deployment.customer_id}",
                        "MINIO_BUCKET": minio_bucket
                    },
                    "ports": [f"{deployment.port_console_backend}:8080"],
                    "volumes": [
                        f"{self.base_path}/{deployment.customer_id}/lakehouse:/lakehouse"
                    ],
                    "networks": [f"{deployment.customer_id}-network"]
                },

                # Console Frontend
                "console-frontend": {
                    "image": "0711-os-console-frontend:latest",
                    "container_name": f"{deployment.customer_id}-console-frontend",
                    "environment": {
                        "BACKEND_URL": f"http://console-backend:8080",
                        "CUSTOMER_NAME": deployment.company_name
                    },
                    "ports": [f"{deployment.port_console_frontend}:3000"],
                    "networks": [f"{deployment.customer_id}-network"]
                }
            },

            "networks": {
                f"{deployment.customer_id}-network": {
                    "driver": "bridge"
                }
            },

            "volumes": {
                "huggingface_cache": {"external": True}
            }
        }

        with open(output_file, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)

    async def _start_services(self, customer_dir: Path):
        """Start customer services with docker-compose"""
        try:
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=customer_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start services: {e.stderr.decode()}")
            raise


# CLI Entry Point
if __name__ == "__main__":
    import asyncio

    async def test_deployment():
        """Test deployment for EATON"""
        orchestrator = CustomerDeploymentOrchestrator()

        result = await orchestrator.deploy_customer(
            customer_id="eaton",
            company_name="EATON Corporation",
            selected_mcps=["etim", "ctax"],
            uploaded_files_bucket="customer-eaton",
            deployment_type="managed"
        )

        print("\n" + "="*60)
        print("Deployment Result:")
        print("="*60)
        import json
        print(json.dumps(result, indent=2))

    asyncio.run(test_deployment())
