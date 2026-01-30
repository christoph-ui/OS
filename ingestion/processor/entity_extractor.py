"""
Entity Extractor - Extract entities and relationships from documents

Uses spaCy NER + custom rules to identify:
- Companies (ORG)
- Products (PRODUCT)
- People (PERSON)
- Dates (DATE)
- Money (MONEY)
- Locations (LOC)

Outputs structured entities + relationships for Neo4j graph loading.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import re

try:
    import spacy
    from spacy.tokens import Doc, Span
except ImportError:
    raise ImportError("spaCy not installed. Run: pip install spacy && python -m spacy download de_core_news_md")

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Extracted entity"""
    text: str
    type: str  # PERSON, ORG, PRODUCT, DATE, MONEY, LOC
    start: int
    end: int
    context: Optional[str] = None  # Surrounding text
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "type": self.type,
            "start": self.start,
            "end": self.end,
            "context": self.context,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class Relationship:
    """Relationship between entities"""
    source: Entity
    target: Entity
    type: str  # MENTIONS, PRODUCED_BY, RELATED_TO, LOCATED_IN
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        return {
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "type": self.type,
            "confidence": self.confidence
        }


class EntityExtractor:
    """
    Extract entities and relationships from text.

    Uses spaCy NER + custom patterns for domain-specific entities.
    """

    def __init__(
        self,
        language: str = "de",  # German by default (EATON docs)
        model: str = "de_core_news_md",
        enable_custom_rules: bool = True
    ):
        """
        Args:
            language: Language code (de, en)
            model: spaCy model name
            enable_custom_rules: Enable custom entity patterns
        """
        self.language = language
        self.model_name = model

        # Load spaCy model
        try:
            self.nlp = spacy.load(model)
        except OSError:
            logger.warning(f"Model {model} not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model], check=True)
            self.nlp = spacy.load(model)

        logger.info(f"Loaded spaCy model: {model}")

        # Custom patterns for industry-specific entities
        self.enable_custom_rules = enable_custom_rules
        if enable_custom_rules:
            self._add_custom_patterns()

    def _add_custom_patterns(self):
        """Add custom entity patterns (products, tech terms, etc.)"""
        # Add product pattern matcher
        from spacy.matcher import Matcher

        self.matcher = Matcher(self.nlp.vocab)

        # Product patterns (e.g., "Eaton 9PX", "Ellipse ECO 1200")
        product_patterns = [
            [{"ORTH": "Eaton"}, {"IS_ALPHA": True}, {"LIKE_NUM": True}],  # Eaton 9PX 1500
            [{"IS_ALPHA": True}, {"ORTH": "ECO"}, {"LIKE_NUM": True}],     # Ellipse ECO 1200
            [{"ORTH": "USV"}, {"LIKE_NUM": True}],                         # USV 5000
        ]

        self.matcher.add("PRODUCT", product_patterns)
        logger.info("Added custom product patterns")

    def extract(
        self,
        text: str,
        doc_id: Optional[str] = None,
        extract_relationships: bool = True
    ) -> Tuple[List[Entity], List[Relationship]]:
        """
        Extract entities and relationships from text.

        Args:
            text: Input text
            doc_id: Document identifier (for context)
            extract_relationships: Also extract relationships

        Returns:
            Tuple of (entities, relationships)
        """
        if not text or len(text.strip()) < 10:
            return [], []

        # Process with spaCy
        doc = self.nlp(text)

        # Extract entities
        entities = self._extract_entities(doc, doc_id)

        # Extract relationships
        relationships = []
        if extract_relationships:
            relationships = self._extract_relationships(entities, doc)

        logger.info(f"Extracted {len(entities)} entities, {len(relationships)} relationships")
        return entities, relationships

    def _extract_entities(self, doc: Doc, doc_id: Optional[str] = None) -> List[Entity]:
        """Extract entities from spaCy Doc"""
        entities = []

        # spaCy NER entities
        for ent in doc.ents:
            entity = Entity(
                text=ent.text,
                type=self._normalize_entity_type(ent.label_),
                start=ent.start_char,
                end=ent.end_char,
                context=self._get_context(doc, ent.start, ent.end),
                metadata={"doc_id": doc_id} if doc_id else {}
            )
            entities.append(entity)

        # Custom patterns (products)
        if self.enable_custom_rules:
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                entity = Entity(
                    text=span.text,
                    type="PRODUCT",
                    start=span.start_char,
                    end=span.end_char,
                    context=self._get_context(doc, start, end),
                    confidence=0.9,  # Custom patterns slightly lower confidence
                    metadata={"doc_id": doc_id, "source": "custom_pattern"} if doc_id else {"source": "custom_pattern"}
                )
                entities.append(entity)

        # Deduplicate overlapping entities
        entities = self._deduplicate_entities(entities)

        return entities

    def _normalize_entity_type(self, spacy_label: str) -> str:
        """Normalize spaCy entity labels to our types"""
        mapping = {
            "PER": "PERSON",
            "PERSON": "PERSON",
            "ORG": "ORG",
            "LOC": "LOC",
            "GPE": "LOC",  # Geopolitical entity
            "DATE": "DATE",
            "TIME": "DATE",
            "MONEY": "MONEY",
            "PRODUCT": "PRODUCT",
            "WORK_OF_ART": "PRODUCT",
        }
        return mapping.get(spacy_label, "MISC")

    def _get_context(self, doc: Doc, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for entity"""
        # Get character offsets
        start_char = doc[start].idx
        end_char = doc[end - 1].idx + len(doc[end - 1].text)

        # Get context window
        context_start = max(0, start_char - window)
        context_end = min(len(doc.text), end_char + window)

        context = doc.text[context_start:context_end]
        return context.strip()

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities (keep highest confidence)"""
        if not entities:
            return []

        # Sort by start position, then confidence
        sorted_entities = sorted(entities, key=lambda e: (e.start, -e.confidence))

        deduplicated = []
        last_end = -1

        for entity in sorted_entities:
            # Skip if overlaps with previous entity
            if entity.start < last_end:
                continue

            deduplicated.append(entity)
            last_end = entity.end

        return deduplicated

    def _extract_relationships(self, entities: List[Entity], doc: Doc) -> List[Relationship]:
        """
        Extract relationships between entities.

        Simple rule-based approach:
        - ORG + PRODUCT in same sentence → PRODUCED_BY
        - PERSON + ORG in same sentence → WORKS_AT
        - ORG + LOC in same sentence → LOCATED_IN
        """
        relationships = []

        # Group entities by sentence
        sentences = list(doc.sents)
        entity_by_sent = {}

        for entity in entities:
            # Find which sentence contains this entity
            for i, sent in enumerate(sentences):
                if sent.start_char <= entity.start < sent.end_char:
                    if i not in entity_by_sent:
                        entity_by_sent[i] = []
                    entity_by_sent[i].append(entity)
                    break

        # Extract relationships within sentences
        for sent_idx, sent_entities in entity_by_sent.items():
            for i, e1 in enumerate(sent_entities):
                for e2 in sent_entities[i + 1:]:
                    rel_type = self._infer_relationship(e1, e2)
                    if rel_type:
                        relationships.append(
                            Relationship(
                                source=e1,
                                target=e2,
                                type=rel_type,
                                confidence=0.8  # Rule-based, moderate confidence
                            )
                        )

        return relationships

    def _infer_relationship(self, e1: Entity, e2: Entity) -> Optional[str]:
        """Infer relationship type between two entities"""
        types = {e1.type, e2.type}

        # ORG + PRODUCT → PRODUCES
        if types == {"ORG", "PRODUCT"}:
            return "PRODUCES" if e1.type == "ORG" else "PRODUCED_BY"

        # PERSON + ORG → WORKS_AT
        if types == {"PERSON", "ORG"}:
            return "WORKS_AT" if e1.type == "PERSON" else "EMPLOYS"

        # ORG + LOC → LOCATED_IN
        if types == {"ORG", "LOC"}:
            return "LOCATED_IN" if e1.type == "ORG" else "HOSTS"

        # PRODUCT + DATE → RELEASED_ON
        if types == {"PRODUCT", "DATE"}:
            return "RELEASED_ON" if e1.type == "PRODUCT" else "RELEASE_DATE"

        # Generic MENTIONS relationship
        return "MENTIONS"


def extract_from_file(file_path: Path) -> Tuple[List[Entity], List[Relationship]]:
    """
    Extract entities from a file.

    Args:
        file_path: Path to text file

    Returns:
        Tuple of (entities, relationships)
    """
    extractor = EntityExtractor()

    text = file_path.read_text(encoding='utf-8', errors='ignore')
    entities, relationships = extractor.extract(text, doc_id=str(file_path))

    return entities, relationships


if __name__ == "__main__":
    # CLI for testing
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python entity_extractor.py <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"Extracting entities from: {file_path}")
    entities, relationships = extract_from_file(file_path)

    print(f"\n✓ Extracted {len(entities)} entities, {len(relationships)} relationships\n")

    print("Entities:")
    for e in entities[:20]:  # Show first 20
        print(f"  [{e.type}] {e.text}")

    print(f"\nRelationships:")
    for r in relationships[:10]:  # Show first 10
        print(f"  {r.source.text} --[{r.type}]--> {r.target.text}")

    # Save to JSON
    output = {
        "entities": [e.to_dict() for e in entities],
        "relationships": [r.to_dict() for r in relationships]
    }

    output_path = file_path.with_suffix('.entities.json')
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n✓ Saved to: {output_path}")
