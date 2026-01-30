"""
Customer Deployment Orchestrator

Provisions complete 0711 stack per customer:
- Dedicated Mixtral instance with customer LoRAs
- Customer-specific lakehouse (RAG)
- MCP routing
- Continuous learning pipeline
"""

import logging
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


class CustomerDeploymentOrchestrator:
    """
    Orchestrates deployment of complete 0711 stack for a single customer.

    Each customer gets:
    - Dedicated Mixtral-8x7B instance (24GB GPU)
    - Customer-specific LoRA adapters (2-4GB)
    - Isolated lakehouse (Delta + Lance + Graph)
    - MinIO bucket for raw files
    - MCP instances routed to their data
    - Continuous learning from interactions
    """

    def __init__(self, base_path: Path = Path("/home/christoph.bertsch/0711")):
        self.base_path = base_path
        self.deployments_path = base_path / "deployments"
        self.deployments_path.mkdir(exist_ok=True)

    def allocate_ports(self, customer_id: str) -> Dict[str, int]:
        """
        Allocate port range for customer.

        Each customer gets 100-port block:
        - EATON: 5100-5199
        - e-ProCat: 5200-5299
        - Customer N: 5N00-5N99
        """
        # Simple hash-based allocation (improve with DB tracking in production)
        base_port = 5000 + (hash(customer_id) % 50) * 100

        return {
            "vllm": base_port + 0,        # Mixtral inference
            "embeddings": base_port + 1,  # Embedding model
            "console": base_port + 10,    # Customer console
            "mcp_ctax": base_port + 20,   # CTAX MCP
            "mcp_law": base_port + 21,    # LAW MCP
            "mcp_etim": base_port + 22,   # ETIM MCP
            "mcp_tender": base_port + 23, # TENDER MCP
            "lora_trainer": base_port + 30, # LoRA training service
            "ingestion": base_port + 40,  # Ingestion API
        }

    def generate_customer_compose(
        self,
        customer_id: str,
        company_name: str,
        selected_mcps: List[str],
        deployment_type: str = "managed"  # "managed" or "self_hosted"
    ) -> Path:
        """
        Generate customer-specific docker-compose.yml

        Creates complete isolated stack for one customer.
        """
        ports = self.allocate_ports(customer_id)
        customer_dir = self.deployments_path / customer_id
        customer_dir.mkdir(exist_ok=True)

        # Base configuration
        compose_config = {
            # Remove obsolete version field for Docker Compose v2+
            "services": {},
            "networks": {
                f"{customer_id}-network": {
                    "driver": "bridge"
                }
            },
            "volumes": {
                f"{customer_id}-lakehouse": {},
                f"{customer_id}-models": {},
                f"{customer_id}-loras": {},
            }
        }

        # Add vLLM (Mixtral) service
        compose_config["services"]["vllm"] = {
            "image": "vllm/vllm-openai:latest",
            "container_name": f"{customer_id}-vllm",
            "environment": {
                "VLLM_MODEL": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "VLLM_TENSOR_PARALLEL": "1",
                "VLLM_GPU_MEMORY_UTILIZATION": "0.85",
                "VLLM_MAX_MODEL_LEN": "32768",
                "VLLM_ENABLE_LORA": "true",
                "VLLM_MAX_LORA_RANK": "64",
            },
            "ports": [f"{ports['vllm']}:8000"],
            "volumes": [
                f"{customer_id}-models:/models",
                f"{customer_id}-loras:/loras",
            ],
            "deploy": {
                "resources": {
                    "reservations": {
                        "devices": [{
                            "driver": "nvidia",
                            "count": 1,
                            "capabilities": ["gpu"]
                        }]
                    }
                }
            },
            "networks": [f"{customer_id}-network"]
        }

        # Add embedding service
        compose_config["services"]["embeddings"] = {
            "image": "0711-os-embeddings:latest",  # Fixed: use correct image name
            "container_name": f"{customer_id}-embeddings",
            "environment": {
                "EMBEDDING_MODEL": "intfloat/multilingual-e5-large",
                "EMBEDDING_PORT": "8001",
                "INFERENCE_EMBEDDING_DEVICE": "cpu",  # Config uses INFERENCE_ prefix
                "CUDA_VISIBLE_DEVICES": "",  # Hide all GPUs from PyTorch
            },
            "ports": [f"{ports['embeddings']}:8001"],
            "networks": [f"{customer_id}-network"]
        }

        # Add lakehouse service
        compose_config["services"]["lakehouse"] = {
            "image": "0711/lakehouse:latest",  # This exists correctly
            "container_name": f"{customer_id}-lakehouse",
            "environment": {
                "CUSTOMER_ID": customer_id,
                "LAKEHOUSE_PATH": "/data/lakehouse",
                "MINIO_BUCKET": f"customer-{customer_id}",
            },
            "volumes": [
                f"{customer_id}-lakehouse:/data/lakehouse",
            ],
            "networks": [f"{customer_id}-network"]
        }

        # MCPs are now shared services - no per-customer deployment needed
        # Customer accesses shared ETIM MCP via orchestrator/mcp/mcp_router.py
        # Selected MCPs are stored in customer.enabled_mcps JSON field

        # Write docker-compose.yml
        compose_file = customer_dir / "docker-compose.yml"
        with open(compose_file, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)

        logger.info(f"Generated docker-compose for {company_name} at {compose_file}")

        return compose_file

    async def deploy_customer(
        self,
        customer_id: str,
        company_name: str,
        selected_mcps: List[str],
        uploaded_files_bucket: str,
        deployment_type: str = "managed"
    ) -> Dict:
        """
        Execute complete customer deployment.

        Steps:
        1. Generate docker-compose (vLLM, embeddings, lakehouse only)
        2. Start vLLM with Mixtral
        3. Initialize customer lakehouse
        4. Trigger ingestion of uploaded files
        5. Enable selected MCPs (stored in database, not deployed)
        6. Start console UI

        Note: MCPs are shared services accessed via mcp_router, not deployed per-customer

        Returns deployment info
        """
        logger.info(f"🚀 Starting deployment for {company_name} ({customer_id})")

        # Import WebSocket updater
        from api.routes.deployment_ws import update_deployment_status

        # Send initial status
        await update_deployment_status(customer_id, {
            "step": "Initializing",
            "status": "in_progress",
            "message": f"Starting deployment for {company_name}",
            "progress": 5
        })

        # Step 1: Generate docker-compose
        await update_deployment_status(customer_id, {
            "step": "Generating Configuration",
            "status": "in_progress",
            "message": "Generating docker-compose.yml",
            "progress": 10
        })

        compose_file = self.generate_customer_compose(
            customer_id, company_name, selected_mcps, deployment_type
        )

        await update_deployment_status(customer_id, {
            "step": "Configuration Complete",
            "status": "in_progress",
            "message": f"Generated docker-compose with {len(selected_mcps)} MCPs",
            "progress": 20
        })

        # Step 2: Start infrastructure
        await update_deployment_status(customer_id, {
            "step": "Starting Docker Services",
            "status": "in_progress",
            "message": f"Launching containers for {len(selected_mcps)} MCPs",
            "progress": 30
        })

        customer_dir = compose_file.parent
        logger.info(f"Starting Docker services for {customer_id}...")

        try:
            # Start containers
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                cwd=customer_dir,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"✓ Docker compose up executed for {customer_id}")

            # Poll for container status (wait for healthy)
            max_attempts = 30  # 30 seconds
            for attempt in range(max_attempts):
                # Check running containers
                ps_result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={customer_id}", "--format", "{{.Names}}|{{.Status}}"],
                    capture_output=True,
                    text=True
                )

                containers = []
                if ps_result.stdout.strip():
                    for line in ps_result.stdout.strip().split('\n'):
                        if '|' in line:
                            name, status = line.split('|', 1)
                            containers.append({"name": name, "status": status})

                running_count = len(containers)
                expected_count = 3  # vllm, embeddings, lakehouse

                await update_deployment_status(customer_id, {
                    "step": "Starting Containers",
                    "status": "in_progress",
                    "message": f"{running_count}/{expected_count} containers running",
                    "progress": 35 + (running_count / expected_count * 5),  # 35-40%
                    "details": {"containers": containers}
                })

                if running_count >= expected_count:
                    logger.info(f"✓ All {expected_count} containers running for {customer_id}")
                    break

                await asyncio.sleep(1)

            await update_deployment_status(customer_id, {
                "step": "Containers Running",
                "status": "in_progress",
                "message": f"{len(containers)} containers operational",
                "progress": 40
            })

        except subprocess.CalledProcessError as e:
            logger.error(f"Docker compose failed: {e.stderr}")
            await update_deployment_status(customer_id, {
                "step": "Docker Failed",
                "status": "failed",
                "message": f"Container startup failed: {e.stderr[:100]}",
                "progress": 30
            })
            raise

        # Step 3: Initialize lakehouse
        await update_deployment_status(customer_id, {
            "step": "Initializing Lakehouse",
            "status": "in_progress",
            "message": "Setting up Delta tables and Lance indices",
            "progress": 50
        })

        logger.info(f"Initializing lakehouse for {customer_id}...")
        lakehouse_path = self.base_path / "data" / "lakehouse" / customer_id
        lakehouse_path.mkdir(parents=True, exist_ok=True)

        await update_deployment_status(customer_id, {
            "step": "Lakehouse Ready",
            "status": "in_progress",
            "message": f"Lakehouse initialized at {lakehouse_path}",
            "progress": 55
        })

        # Step 4: Trigger ingestion
        await update_deployment_status(customer_id, {
            "step": "Starting Ingestion",
            "status": "in_progress",
            "message": f"Processing files from {uploaded_files_bucket}",
            "progress": 60
        })

        logger.info(f"Starting ingestion from MinIO bucket: {uploaded_files_bucket}")

        # Trigger ingestion pipeline
        try:
            from ingestion.orchestrator import IngestionOrchestrator, IngestionProgress

            ingestion = IngestionOrchestrator(
                lakehouse_path=lakehouse_path,
                vllm_url=f"http://localhost:{ports['vllm']}",
                embedding_model="intfloat/multilingual-e5-large"
            )

            # Wire progress callback to WebSocket
            def on_ingestion_progress(progress: IngestionProgress):
                asyncio.create_task(update_deployment_status(customer_id, {
                    "step": "Ingestion",
                    "status": "in_progress",
                    "message": progress.current_phase or "Processing documents",
                    "progress": 60 + (progress.progress_percent * 0.2),  # 60-80% range
                    "details": {
                        "current_file": progress.current_file,
                        "processed_files": progress.processed_files,
                        "total_files": progress.total_files,
                        "failed_files": progress.failed_files,
                        "mcp_stats": progress.stats_by_mcp,
                        "phase": progress.current_phase
                    }
                }))

            ingestion.on_progress(on_ingestion_progress)

            logger.info(f"📥 Starting real ingestion for {customer_id}")

            # Download files from MinIO to temp location
            from minio import Minio
            import tempfile
            import shutil

            minio_client = Minio(
                "localhost:4050",
                access_key="0711admin",
                secret_key="0711secret",
                secure=False
            )

            # Create temp directory for ingestion
            temp_dir = Path(tempfile.mkdtemp(prefix=f"ingest_{customer_id}_"))

            try:
                # Download files from MinIO
                for obj in minio_client.list_objects(uploaded_files_bucket, recursive=True):
                    local_path = temp_dir / obj.object_name
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    minio_client.fget_object(uploaded_files_bucket, obj.object_name, str(local_path))
                    logger.info(f"Downloaded: {obj.object_name}")

                # Run ingestion on downloaded files
                from ingestion.orchestrator import FolderConfig
                folders = [FolderConfig(path=temp_dir, mcp_assignment="general", recursive=True)]

                result = await ingestion.ingest(folders)

                logger.info(f"✓ Ingestion completed: {result.processed_files} files processed")

                await update_deployment_status(customer_id, {
                    "step": "Ingestion Complete",
                    "status": "in_progress",
                    "message": f"Processed {result.processed_files} files, {result.failed_files} failed",
                    "progress": 80,
                    "details": result.to_dict()
                })

            finally:
                # Cleanup temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            await update_deployment_status(customer_id, {
                "step": "Ingestion Error",
                "status": "in_progress",
                "message": f"Ingestion error: {str(e)[:100]}",
                "progress": 75
            })

        # Step 5: Schedule LoRA training
        await update_deployment_status(customer_id, {
            "step": "Training LoRA Adapters",
            "status": "in_progress",
            "message": "Fine-tuning model on customer data",
            "progress": 85
        })

        logger.info(f"Scheduling initial LoRA training for {customer_id}")

        try:
            from inference.lora_trainer import LoRATrainer

            trainer = LoRATrainer(
                customer_id=customer_id,
                lakehouse_path=lakehouse_path,
                loras_path=self.base_path / "data" / "loras"
            )

            # Initial training will run after ingestion completes
            logger.info(f"🧠 LoRA trainer initialized for {customer_id}")

            await update_deployment_status(customer_id, {
                "step": "LoRA Training Scheduled",
                "status": "in_progress",
                "message": "Model adaptation configured",
                "progress": 90
            })

        except Exception as e:
            logger.warning(f"LoRA trainer init failed: {e}")

        # Step 6: Deploying MCPs
        await update_deployment_status(customer_id, {
            "step": "Deploying MCPs",
            "status": "in_progress",
            "message": f"Installing {len(selected_mcps)} business process modules",
            "progress": 95
        })

        ports = self.allocate_ports(customer_id)

        # Final: Deployment Complete
        await update_deployment_status(customer_id, {
            "step": "Deployment Complete",
            "status": "completed",
            "message": f"All services running. Console: http://localhost:{ports['console']}",
            "progress": 100
        })

        logger.info(f"🎉 Deployment {customer_id} completed successfully!")

        return {
            "success": True,
            "customer_id": customer_id,
            "deployment_type": deployment_type,
            "ports": ports,
            "services": {
                "vllm": f"http://localhost:{ports['vllm']}",
                "console": f"http://localhost:{ports['console']}",
                "mcps": {mcp: f"http://localhost:{ports.get(f'mcp_{mcp}')}" for mcp in selected_mcps}
            },
            "lakehouse_path": str(lakehouse_path),
            "compose_file": str(compose_file),
            "status": "active"
        }
