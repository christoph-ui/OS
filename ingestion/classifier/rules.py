"""
Rule-Based Classifier - Fast classification using pattern matching

Uses filename patterns and path heuristics to classify documents.
This is the first-pass, fast classification before LLM classification.
"""

import re
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RuleBasedClassifier:
    """
    Rule-based document classifier.

    Uses path patterns and keywords to quickly classify documents
    into MCP categories without LLM inference.
    """

    # Category patterns (German + English)
    PATTERNS = {
        'tax': [
            # German tax keywords
            r'steuer',
            r'finanzamt',
            r'umsatzsteuer',
            r'ust',
            r'\best\b',  # Einkommensteuer
            r'gewerbesteuer',
            r'buchung',
            r'buchhaltung',
            r'bilanz',
            r'jahresabschluss',
            r'datev',
            r'elster',
            r'steuerbescheid',
            r'steuererklärung',
            r'vorsteuer',

            # English tax keywords
            r'\btax\b',
            r'taxation',
            r'revenue',
            r'accounting',
            r'bookkeeping',
            r'financial\s+statement',
            r'balance\s+sheet',
        ],

        'legal': [
            # German legal keywords
            r'vertrag',
            r'verträge',
            r'vereinbarung',
            r'agb',
            r'rechnung',
            r'mahnung',
            r'anwalt',
            r'recht',
            r'klage',
            r'gericht',
            r'urteil',
            r'beschluss',
            r'satzung',
            r'geschäftsordnung',
            r'compliance',
            r'datenschutz',
            r'dsgvo',

            # English legal keywords
            r'contract',
            r'agreement',
            r'legal',
            r'law',
            r'invoice',
            r'terms',
            r'conditions',
            r'lawsuit',
            r'court',
            r'judgment',
            r'compliance',
            r'gdpr',
        ],

        'products': [
            # German product keywords
            r'produkt',
            r'artikel',
            r'etim',
            r'eclass',
            r'bmcat',
            r'katalog',
            r'stammdaten',
            r'material',
            r'warengruppe',
            r'produktdaten',
            r'artikelnummer',
            r'ean',
            r'gtin',
            r'produktkatalog',

            # English product keywords
            r'product',
            r'item',
            r'catalog',
            r'catalogue',
            r'master\s+data',
            r'sku',
            r'material',
            r'parts',
            r'inventory',
        ],

        'hr': [
            # German HR keywords
            r'personal',
            r'mitarbeiter',
            r'employee',
            r'bewerbung',
            r'gehalt',
            r'salary',
            r'lohn',
            r'arbeitsvertrag',
            r'zeugnis',
            r'kündigung',
            r'urlaub',
            r'vacation',
            r'weiterbildung',
            r'training',
            r'qualifikation',
            r'lebenslauf',
            r'cv',
            r'resume',

            # English HR keywords
            r'\bhr\b',
            r'human\s+resources',
            r'recruitment',
            r'hiring',
            r'payroll',
            r'benefits',
            r'onboarding',
        ],

        'correspondence': [
            # Email/correspondence keywords
            r'korrespondenz',
            r'email',
            r'e-mail',
            r'brief',
            r'schreiben',
            r'anfrage',
            r'angebot',
            r'bestellung',
            r'lieferung',
            r'versand',
            r'letter',
            r'correspondence',
            r'inquiry',
            r'quotation',
            r'order',
            r'delivery',
        ],
    }

    def __init__(self):
        """Initialize classifier with compiled patterns"""
        self._compiled_patterns = {}

        for category, patterns in self.PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in patterns
            ]

    def classify(self, file_path: Path) -> Optional[str]:
        """
        Classify a document based on its path and filename.

        Args:
            file_path: Path to the document

        Returns:
            Category name ('tax', 'legal', 'products', 'hr', 'correspondence'),
            or None if uncertain
        """
        # Get full path as lowercase string
        path_str = str(file_path).lower()
        filename = file_path.name.lower()

        # Score each category
        scores = {category: 0 for category in self._compiled_patterns}

        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                # Match in full path
                if pattern.search(path_str):
                    scores[category] += 2  # Path match is strong signal

                # Match in filename only
                elif pattern.search(filename):
                    scores[category] += 1  # Filename match is moderate signal

        # Get best category
        if not any(scores.values()):
            return None  # No matches, uncertain

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        # Require minimum confidence
        if best_score < 1:
            return None

        # Check if another category is very close
        second_best_score = sorted(scores.values(), reverse=True)[1]
        if best_score - second_best_score < 2:
            # Too close, uncertain
            return None

        logger.debug(
            f"Rule-based classification: {file_path.name} → {best_category} "
            f"(score: {best_score})"
        )

        return best_category

    def classify_with_confidence(self, file_path: Path) -> tuple[Optional[str], float]:
        """
        Classify with confidence score.

        Args:
            file_path: Path to document

        Returns:
            Tuple of (category, confidence) where confidence is 0-1
        """
        path_str = str(file_path).lower()
        filename = file_path.name.lower()

        scores = {category: 0 for category in self._compiled_patterns}

        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(path_str):
                    scores[category] += 2
                elif pattern.search(filename):
                    scores[category] += 1

        if not any(scores.values()):
            return None, 0.0

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        # Normalize confidence (max score typically ~10)
        confidence = min(best_score / 10.0, 1.0)

        return best_category, confidence
