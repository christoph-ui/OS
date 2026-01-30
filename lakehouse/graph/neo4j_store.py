"""
Neo4j Graph Store - Store and query entities and relationships

Manages customer-specific knowledge graphs in Neo4j:
- Nodes: Document, Company, Product, Person, Date
- Relationships: MENTIONS, PRODUCED_BY, WORKS_AT, LOCATED_IN
- Queries: Find related entities, graph traversal
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from neo4j import GraphDatabase, Driver
    from neo4j.exceptions import ServiceUnavailable
except ImportError:
    raise ImportError("Neo4j driver not installed. Run: pip install neo4j")

logger = logging.getLogger(__name__)


@dataclass
class GraphConfig:
    """Neo4j connection configuration"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "zeroseven2024"
    database: str = "neo4j"  # or customer-specific DB


class Neo4jStore:
    """
    Neo4j graph database interface for 0711 Platform.

    Manages entity and relationship storage with customer isolation.
    """

    def __init__(self, config: Optional[GraphConfig] = None, customer_id: Optional[str] = None):
        """
        Args:
            config: Neo4j connection config
            customer_id: Customer ID for data isolation
        """
        self.config = config or GraphConfig()
        self.customer_id = customer_id
        self.driver: Optional[Driver] = None

        self._connect()

    def _connect(self):
        """Establish Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )

            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info(f"✓ Connected to Neo4j: {self.config.uri}")

            # Create constraints
            self._create_constraints()

        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def _create_constraints(self):
        """Create unique constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE INDEX entity_customer IF NOT EXISTS FOR (e:Entity) ON (e.customer_id)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX document_customer IF NOT EXISTS FOR (d:Document) ON (d.customer_id)",
        ]

        with self.driver.session(database=self.config.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint may already exist
                    logger.debug(f"Constraint creation skipped: {e}")

        logger.info("✓ Neo4j constraints verified")

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_document_node(self, doc_id: str, filename: str, mcp: str, metadata: Optional[Dict] = None) -> str:
        """
        Create Document node.

        Args:
            doc_id: Document identifier
            filename: Original filename
            mcp: MCP classification (ctax, law, etim, general)
            metadata: Additional metadata

        Returns:
            Neo4j node ID
        """
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MERGE (d:Document {id: $doc_id})
                ON CREATE SET
                    d.filename = $filename,
                    d.mcp = $mcp,
                    d.customer_id = $customer_id,
                    d.created_at = datetime(),
                    d.metadata = $metadata
                RETURN id(d) as node_id
                """,
                doc_id=doc_id,
                filename=filename,
                mcp=mcp,
                customer_id=self.customer_id,
                metadata=metadata or {}
            )

            record = result.single()
            node_id = record["node_id"]
            logger.debug(f"Created Document node: {doc_id}")
            return str(node_id)

    def create_entity_node(self, entity: Dict) -> str:
        """
        Create Entity node.

        Args:
            entity: Entity dict from entity_extractor
                {text, type, start, end, context, confidence, metadata}

        Returns:
            Neo4j node ID
        """
        # Generate entity ID (hash of text + type)
        import hashlib
        entity_id = hashlib.md5(
            f"{entity['text']}:{entity['type']}".encode()
        ).hexdigest()

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MERGE (e:Entity {id: $entity_id})
                ON CREATE SET
                    e.text = $text,
                    e.type = $type,
                    e.customer_id = $customer_id,
                    e.first_seen = datetime(),
                    e.confidence = $confidence,
                    e.count = 1
                ON MATCH SET
                    e.count = e.count + 1,
                    e.last_seen = datetime()
                RETURN id(e) as node_id
                """,
                entity_id=entity_id,
                text=entity['text'],
                type=entity['type'],
                customer_id=self.customer_id,
                confidence=entity.get('confidence', 1.0)
            )

            record = result.single()
            node_id = record["node_id"]
            logger.debug(f"Created Entity node: {entity['text']} ({entity['type']})")
            return entity_id

    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict] = None
    ):
        """
        Create relationship between entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            rel_type: Relationship type (MENTIONS, PRODUCES, WORKS_AT, etc.)
            properties: Additional properties
        """
        with self.driver.session(database=self.config.database) as session:
            session.run(
                f"""
                MATCH (s {{id: $source_id}}), (t {{id: $target_id}})
                MERGE (s)-[r:{rel_type}]->(t)
                ON CREATE SET
                    r.created_at = datetime(),
                    r.customer_id = $customer_id,
                    r.properties = $properties
                """,
                source_id=source_id,
                target_id=target_id,
                customer_id=self.customer_id,
                properties=properties or {}
            )

            logger.debug(f"Created relationship: {source_id} --[{rel_type}]--> {target_id}")

    def link_document_to_entities(self, doc_id: str, entity_ids: List[str]):
        """
        Create MENTIONS relationships from Document to Entities.

        Args:
            doc_id: Document ID
            entity_ids: List of entity IDs mentioned in document
        """
        with self.driver.session(database=self.config.database) as session:
            for entity_id in entity_ids:
                session.run(
                    """
                    MATCH (d:Document {id: $doc_id}), (e:Entity {id: $entity_id})
                    MERGE (d)-[r:MENTIONS]->(e)
                    ON CREATE SET r.created_at = datetime()
                    """,
                    doc_id=doc_id,
                    entity_id=entity_id
                )

        logger.info(f"Linked document {doc_id} to {len(entity_ids)} entities")

    def load_entities_from_extraction(
        self,
        doc_id: str,
        filename: str,
        mcp: str,
        entities: List[Dict],
        relationships: List[Dict]
    ) -> Dict[str, Any]:
        """
        Load complete extraction result into Neo4j.

        Args:
            doc_id: Document identifier
            filename: Original filename
            mcp: MCP classification
            entities: List of entity dicts from entity_extractor
            relationships: List of relationship dicts

        Returns:
            Statistics dict
        """
        stats = {
            "documents": 0,
            "entities": 0,
            "relationships": 0,
            "doc_entity_links": 0
        }

        # Create document node
        self.create_document_node(doc_id, filename, mcp)
        stats["documents"] = 1

        # Create entity nodes
        entity_id_map = {}  # text -> neo4j_id
        for entity in entities:
            entity_id = self.create_entity_node(entity)
            entity_id_map[entity['text']] = entity_id
            stats["entities"] += 1

        # Link document to entities
        self.link_document_to_entities(doc_id, list(entity_id_map.values()))
        stats["doc_entity_links"] = len(entity_id_map)

        # Create relationships between entities
        for rel in relationships:
            source_text = rel['source']['text']
            target_text = rel['target']['text']

            if source_text in entity_id_map and target_text in entity_id_map:
                self.create_relationship(
                    source_id=entity_id_map[source_text],
                    target_id=entity_id_map[target_text],
                    rel_type=rel['type'],
                    properties={"confidence": rel.get('confidence', 0.8)}
                )
                stats["relationships"] += 1

        logger.info(f"Loaded {stats['entities']} entities, {stats['relationships']} relationships")
        return stats

    # =======================
    # Query Methods
    # =======================

    def get_all_entities(self, customer_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get all entities for customer.

        Args:
            customer_id: Customer ID (defaults to self.customer_id)
            limit: Max entities to return

        Returns:
            List of entity dicts
        """
        cid = customer_id or self.customer_id

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MATCH (e:Entity {customer_id: $customer_id})
                RETURN e.id as id, e.text as text, e.type as type,
                       e.count as count, e.confidence as confidence
                ORDER BY e.count DESC
                LIMIT $limit
                """,
                customer_id=cid,
                limit=limit
            )

            entities = []
            for record in result:
                entities.append({
                    "id": record["id"],
                    "text": record["text"],
                    "type": record["type"],
                    "count": record["count"],
                    "confidence": record["confidence"]
                })

            return entities

    def get_related_entities(self, entity_id: str, max_hops: int = 2) -> List[Dict]:
        """
        Find entities related to given entity (up to N hops).

        Args:
            entity_id: Source entity ID
            max_hops: Maximum relationship hops

        Returns:
            List of related entities with relationships
        """
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MATCH path = (source:Entity {id: $entity_id})-[*1..$max_hops]-(related:Entity)
                WHERE source.customer_id = $customer_id
                  AND related.customer_id = $customer_id
                RETURN DISTINCT related.id as id, related.text as text,
                       related.type as type, length(path) as distance
                ORDER BY distance, related.count DESC
                LIMIT 50
                """,
                entity_id=entity_id,
                customer_id=self.customer_id,
                max_hops=max_hops
            )

            related = []
            for record in result:
                related.append({
                    "id": record["id"],
                    "text": record["text"],
                    "type": record["type"],
                    "distance": record["distance"]
                })

            return related

    def query_cypher(self, cypher_query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute custom Cypher query.

        Args:
            cypher_query: Cypher query string
            params: Query parameters

        Returns:
            List of result records as dicts
        """
        with self.driver.session(database=self.config.database) as session:
            result = session.run(cypher_query, params or {})

            records = []
            for record in result:
                records.append(dict(record))

            return records

    def get_graph_stats(self, customer_id: Optional[str] = None) -> Dict:
        """
        Get graph statistics for customer.

        Args:
            customer_id: Customer ID (defaults to self.customer_id)

        Returns:
            Statistics dict
        """
        cid = customer_id or self.customer_id

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MATCH (e:Entity {customer_id: $customer_id})
                WITH count(e) as entity_count

                MATCH (d:Document {customer_id: $customer_id})
                WITH entity_count, count(d) as doc_count

                MATCH ()-[r {customer_id: $customer_id}]->()
                RETURN entity_count, doc_count, count(r) as rel_count
                """,
                customer_id=cid
            )

            record = result.single()
            if record:
                return {
                    "entities": record["entity_count"],
                    "documents": record["doc_count"],
                    "relationships": record["rel_count"]
                }
            else:
                return {"entities": 0, "documents": 0, "relationships": 0}

    def delete_customer_data(self, customer_id: Optional[str] = None):
        """
        Delete all data for customer (DANGEROUS!).

        Args:
            customer_id: Customer ID to delete (requires explicit confirmation)
        """
        cid = customer_id or self.customer_id

        if not cid:
            raise ValueError("customer_id required for deletion")

        with self.driver.session(database=self.config.database) as session:
            # Delete all nodes and relationships for customer
            result = session.run(
                """
                MATCH (n {customer_id: $customer_id})
                DETACH DELETE n
                RETURN count(n) as deleted_count
                """,
                customer_id=cid
            )

            record = result.single()
            deleted = record["deleted_count"]
            logger.warning(f"⚠️  Deleted {deleted} nodes for customer {cid}")
            return deleted


if __name__ == "__main__":
    # CLI testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python neo4j_store.py <command> [args...]")
        print("Commands:")
        print("  stats <customer_id>           - Get graph stats")
        print("  entities <customer_id>        - List entities")
        print("  related <entity_id>           - Find related entities")
        sys.exit(1)

    command = sys.argv[1]

    if command == "stats":
        customer_id = sys.argv[2] if len(sys.argv) > 2 else None
        store = Neo4jStore(customer_id=customer_id)
        stats = store.get_graph_stats()
        print(f"\nGraph Stats ({customer_id}):")
        print(f"  Documents: {stats['documents']}")
        print(f"  Entities: {stats['entities']}")
        print(f"  Relationships: {stats['relationships']}")

    elif command == "entities":
        customer_id = sys.argv[2] if len(sys.argv) > 2 else None
        store = Neo4jStore(customer_id=customer_id)
        entities = store.get_all_entities(limit=20)
        print(f"\nEntities ({len(entities)}):")
        for e in entities:
            print(f"  [{e['type']}] {e['text']} (count: {e['count']})")

    elif command == "related":
        if len(sys.argv) < 3:
            print("Error: entity_id required")
            sys.exit(1)
        entity_id = sys.argv[2]
        customer_id = sys.argv[3] if len(sys.argv) > 3 else None
        store = Neo4jStore(customer_id=customer_id)
        related = store.get_related_entities(entity_id)
        print(f"\nRelated Entities ({len(related)}):")
        for r in related:
            print(f"  [{r['type']}] {r['text']} (distance: {r['distance']})")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
