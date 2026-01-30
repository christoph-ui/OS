"""
Docker Manager for Tests

Utilities for managing Docker containers during testing.
"""

import subprocess
import time
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DockerManager:
    """
    Manage Docker containers for testing.

    Example:
        manager = DockerManager()
        manager.start_postgres()
        manager.wait_for_healthy("0711-postgres")
        # Run tests...
        manager.stop_all()
    """

    def __init__(self):
        """Initialize Docker manager."""
        self.started_containers: List[str] = []

    def run_command(self, cmd: List[str], capture: bool = True) -> Optional[str]:
        """
        Run a Docker command.

        Args:
            cmd: Command as list (e.g., ["docker", "ps"])
            capture: Capture output

        Returns:
            Command output if capture=True
        """
        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.stdout.strip()
            else:
                subprocess.run(cmd, timeout=30)
                return None
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            return None
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)}: {e}")
            return None

    def is_running(self, container_name: str) -> bool:
        """
        Check if a container is running.

        Args:
            container_name: Container name

        Returns:
            True if running
        """
        output = self.run_command(["docker", "ps", "-q", "-f", f"name={container_name}"])
        return bool(output and output.strip())

    def container_exists(self, container_name: str) -> bool:
        """
        Check if a container exists (running or stopped).

        Args:
            container_name: Container name

        Returns:
            True if exists
        """
        output = self.run_command(["docker", "ps", "-a", "-q", "-f", f"name={container_name}"])
        return bool(output and output.strip())

    def start_container(self, container_name: str):
        """
        Start an existing container.

        Args:
            container_name: Container name
        """
        logger.info(f"Starting container: {container_name}")
        self.run_command(["docker", "start", container_name])
        self.started_containers.append(container_name)

    def stop_container(self, container_name: str):
        """
        Stop a container.

        Args:
            container_name: Container name
        """
        logger.info(f"Stopping container: {container_name}")
        self.run_command(["docker", "stop", container_name])

    def remove_container(self, container_name: str, force: bool = True):
        """
        Remove a container.

        Args:
            container_name: Container name
            force: Force removal
        """
        logger.info(f"Removing container: {container_name}")
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_name)
        self.run_command(cmd)

    def start_postgres(
        self,
        name: str = "0711-postgres-test",
        port: int = 5433,
        password: str = "test_password"
    ) -> str:
        """
        Start PostgreSQL container for testing.

        Args:
            name: Container name
            port: Host port
            password: PostgreSQL password

        Returns:
            Container name
        """
        if self.is_running(name):
            logger.info(f"PostgreSQL already running: {name}")
            return name

        if self.container_exists(name):
            self.start_container(name)
            return name

        logger.info(f"Creating PostgreSQL container: {name}")
        self.run_command([
            "docker", "run", "-d",
            "--name", name,
            "-e", "POSTGRES_USER=0711",
            "-e", f"POSTGRES_PASSWORD={password}",
            "-e", "POSTGRES_DB=0711_test",
            "-p", f"{port}:5432",
            "postgres:16"
        ])

        self.started_containers.append(name)
        return name

    def start_redis(
        self,
        name: str = "0711-redis-test",
        port: int = 6380
    ) -> str:
        """
        Start Redis container for testing.

        Args:
            name: Container name
            port: Host port

        Returns:
            Container name
        """
        if self.is_running(name):
            logger.info(f"Redis already running: {name}")
            return name

        if self.container_exists(name):
            self.start_container(name)
            return name

        logger.info(f"Creating Redis container: {name}")
        self.run_command([
            "docker", "run", "-d",
            "--name", name,
            "-p", f"{port}:6379",
            "redis:7-alpine"
        ])

        self.started_containers.append(name)
        return name

    def start_minio(
        self,
        name: str = "0711-minio-test",
        port: int = 9001,
        console_port: int = 9002,
        access_key: str = "test_access",
        secret_key: str = "test_secret"
    ) -> str:
        """
        Start MinIO container for testing.

        Args:
            name: Container name
            port: API port
            console_port: Console port
            access_key: MinIO access key
            secret_key: MinIO secret key

        Returns:
            Container name
        """
        if self.is_running(name):
            logger.info(f"MinIO already running: {name}")
            return name

        if self.container_exists(name):
            self.start_container(name)
            return name

        logger.info(f"Creating MinIO container: {name}")
        self.run_command([
            "docker", "run", "-d",
            "--name", name,
            "-e", f"MINIO_ROOT_USER={access_key}",
            "-e", f"MINIO_ROOT_PASSWORD={secret_key}",
            "-p", f"{port}:9000",
            "-p", f"{console_port}:9001",
            "minio/minio",
            "server", "/data",
            "--console-address", ":9001"
        ])

        self.started_containers.append(name)
        return name

    def wait_for_healthy(
        self,
        container_name: str,
        timeout: int = 60,
        check_interval: float = 1.0
    ) -> bool:
        """
        Wait for a container to be healthy.

        Args:
            container_name: Container name
            timeout: Maximum seconds to wait
            check_interval: Seconds between checks

        Returns:
            True if healthy, False if timeout
        """
        logger.info(f"Waiting for {container_name} to be healthy...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if container is running
            if not self.is_running(container_name):
                time.sleep(check_interval)
                continue

            # Check health status
            output = self.run_command([
                "docker", "inspect",
                "--format", "{{.State.Health.Status}}",
                container_name
            ])

            if output == "healthy":
                logger.info(f"{container_name} is healthy")
                return True

            # If no health check, just check if running
            if output == "":
                output = self.run_command([
                    "docker", "inspect",
                    "--format", "{{.State.Running}}",
                    container_name
                ])
                if output == "true":
                    logger.info(f"{container_name} is running (no health check)")
                    return True

            time.sleep(check_interval)

        logger.error(f"{container_name} did not become healthy within {timeout}s")
        return False

    def stop_all(self):
        """Stop all containers started by this manager."""
        for container in self.started_containers:
            self.stop_container(container)
        self.started_containers.clear()

    def cleanup_all(self, force: bool = True):
        """
        Stop and remove all containers started by this manager.

        Args:
            force: Force removal
        """
        for container in self.started_containers:
            self.stop_container(container)
            self.remove_container(container, force=force)
        self.started_containers.clear()

    def get_logs(self, container_name: str, tail: int = 100) -> Optional[str]:
        """
        Get container logs.

        Args:
            container_name: Container name
            tail: Number of lines to show

        Returns:
            Log output
        """
        return self.run_command([
            "docker", "logs",
            "--tail", str(tail),
            container_name
        ])
