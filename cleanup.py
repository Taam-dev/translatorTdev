"""
cleanup.py
----------
OCR text reconstruction and AI-based cleanup.

This module:
1. Reconstructs broken OCR lines into proper sentences.
2. Repairs common OCR character mistakes.
3. Handles manga/webtoon/novel style layouts.
4. Optionally uses OpenAI for advanced cleanup.
"""

import re
from typing import Optional
from settings import settings


# ==================================================
# COMMON OCR CHARACTER SUBSTITUTION RULES
# ==================================================

# Character-level OCR common mistakes
CHAR_SUBSTITUTIONS = [
    # Common character confusion pairs
    (r'\b0\b', 'O'),           # standalone 0 -> O (context-dependent)
    (r'(?<=[a-z])l(?=[a-z])', 'l'),  # keep internal l
    (r'\brn\b', 'm'),          # rn -> m (word boundary)
    (r'(?<!\w)l(?=\s)', 'I'), # leading l followed by space -> I
]

# Word-level OCR common mistakes
WORD_CORRECTIONS = {
    "cant": "can't",
    "wont": "won't",
    "dont": "don't",
    "didnt": "didn't",
    "doesnt": "doesn't",
    "isnt": "isn't",
    "wasnt": "wasn't",
    "werent": "weren't",
    "arent": "aren't",
    "couldnt": "couldn't",
    "wouldnt": "wouldn't",
    "shouldnt": "shouldn't",
    "hadnt": "hadn't",
    "havent": "haven't",
    "hasnt": "hasn't",
    "im": "I'm",
    "ive": "I've",
    "id": "I'd",
    "ill": "I'll",
    "belive": "believe",
    "recieve": "receive",
    "occured": "occurred",
    "untill": "until",
    "wich": "which",
    "teh": "the",
    "thier": "their",
    "freind": "friend",
    "wierd": "weird",
    "definately": "definitely",
    "seperate": "separate",
    "occassion": "occasion",
    "neccessary": "necessary",
    "accomodate": "accommodate",
    "begining": "beginning",
    "beleive": "believe",
    "calender": "calendar",
    "comming": "coming",
    "completly": "completely",
    "concious": "conscious",
    "enviroment": "environment",
    "existance": "existence",
    "experiece": "experience",
    "goverment": "government",
    "grammer": "grammar",
    "independance": "independence",
    "knowlege": "knowledge",
    "lenght": "length",
    "lieing": "lying",
    "managment": "management",
    "millenium": "millennium",
    "mispell": "misspell",
    "nieghbor": "neighbor",
    "noticable": "noticeable",
    "ocasion": "occasion",
    "occurance": "occurrence",
    "persue": "pursue",
    "pospone": "postpone",
    "potatos": "potatoes",
    "privelege": "privilege",
    "profesional": "professional",
    "pronounciation": "pronunciation",
    "publically": "publicly",
    "realy": "really",
    "relevent": "relevant",
    "religous": "religious",
    "remeber": "remember",
    "repitition": "repetition",
    "sence": "sense",
    "sieze": "seize",
    "similer": "similar",
    "studing": "studying",
    "succesful": "successful",
    "suprise": "surprise",
    "tatoo": "tattoo",
    "temperament": "temperament",
    "tendancy": "tendency",
    "tomatos": "tomatoes",
    "tounge": "tongue",
    "truely": "truly",
    "tomorow": "tomorrow",
    "upto": "up to",
    "untill": "until",
    "vaccuum": "vacuum",
    "visable": "visible",
    "wether": "whether",
    "writting": "writing",
    "yesturday": "yesterday",
}


class OCRReconstructor:
    """
    Reconstructs OCR output into clean, readable text.

    Handles:
    - Broken line merging
    - Hyphen split repair
    - Paragraph grouping by coordinates
    - Common OCR character mistakes
    """

    # Sentence-ending punctuation - do NOT merge lines after these
    SENTENCE_ENDINGS = re.compile(r'[.!?:;…]$')
    # Dialogue endings in manga/novels
    DIALOGUE_ENDINGS = re.compile(r'[""\'»›]$')
    # Hyphenated word split at end of line
    HYPHEN_SPLIT = re.compile(r'-$')

    def __init__(self):
        pass

    def reconstruct(self, ocr_results: list[dict]) -> list[str]:
        """
        Main entry point.

        Takes raw OCR results (list of {text, confidence, box})
        and returns list of reconstructed paragraph strings.

        Args:
            ocr_results: Raw OCR output from engine

        Returns:
            List of paragraph strings, ready for translation
        """
        if not ocr_results:
            return []

        # Step 1: Sort OCR boxes top-to-bottom, then left-to-right
        sorted_results = self._sort_by_reading_order(ocr_results)

        # Step 2: Group into paragraph blocks by vertical proximity
        paragraph_groups = self._group_into_paragraphs(sorted_results)

        # Step 3: Merge lines within each paragraph
        paragraphs = []
        for group in paragraph_groups:
            merged = self._merge_lines(group)
            if merged.strip():
                paragraphs.append(merged)

        # Step 4: Apply word-level corrections
        paragraphs = [self._apply_word_corrections(p) for p in paragraphs]

        return paragraphs

    def _sort_by_reading_order(self, results: list[dict]) -> list[dict]:
        """Sort OCR boxes by reading order (top-to-bottom, left-to-right)."""
        def sort_key(item):
            box = item["box"]
            # Use top-left corner Y, then X
            top_y = min(pt[1] for pt in box)
            left_x = min(pt[0] for pt in box)
            return (top_y, left_x)

        return sorted(results, key=sort_key)

    def _get_box_metrics(self, box: list) -> dict:
        """Extract useful metrics from a bounding box."""
        xs = [pt[0] for pt in box]
        ys = [pt[1] for pt in box]
        return {
            "x1": min(xs),
            "y1": min(ys),
            "x2": max(xs),
            "y2": max(ys),
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys),
            "center_y": (min(ys) + max(ys)) / 2,
            "center_x": (min(xs) + max(xs)) / 2,
        }

    def _group_into_paragraphs(
        self, results: list[dict], gap_multiplier: float = 1.8
    ) -> list[list[dict]]:
        """
        Group OCR results into paragraph blocks based on vertical gaps.

        Lines with a vertical gap larger than `gap_multiplier * avg_line_height`
        are considered separate paragraphs.

        Args:
            results: Sorted OCR results
            gap_multiplier: How much gap indicates a paragraph break

        Returns:
            List of groups, each group is a list of OCR result dicts
        """
        if not results:
            return []

        # Calculate average line height from all boxes
        heights = []
        for r in results:
            m = self._get_box_metrics(r["box"])
            heights.append(m["height"])
        avg_height = sum(heights) / len(heights) if heights else 20
        gap_threshold = avg_height * gap_multiplier

        groups = []
        current_group = [results[0]]

        for i in range(1, len(results)):
            prev_metrics = self._get_box_metrics(results[i - 1]["box"])
            curr_metrics = self._get_box_metrics(results[i]["box"])

            # Vertical gap between previous line bottom and current line top
            vertical_gap = curr_metrics["y1"] - prev_metrics["y2"]

            if vertical_gap > gap_threshold:
                # Large gap = new paragraph
                groups.append(current_group)
                current_group = [results[i]]
            else:
                current_group.append(results[i])

        if current_group:
            groups.append(current_group)

        return groups

    def _merge_lines(self, group: list[dict]) -> str:
        """
        Merge OCR lines in a paragraph group into a single clean string.

        Rules:
        - Repair hyphen splits (beauti- + ful -> beautiful)
        - Merge lines unless previous ends with sentence-ending punctuation
        - Add space between merged lines
        - If next line starts lowercase and prev doesn't end with '.', merge
        """
        if not group:
            return ""

        lines = [item["text"].strip() for item in group]
        merged = ""

        for i, line in enumerate(lines):
            if not line:
                continue

            if i == 0:
                merged = line
                continue

            prev = merged

            # Rule 1: Repair hyphen split
            if self.HYPHEN_SPLIT.search(prev):
                # Remove hyphen and join directly
                merged = prev[:-1] + line
                continue

            # Rule 2: If previous line ends with sentence-ending punctuation
            # -> new sentence, add space and capitalize
            if self.SENTENCE_ENDINGS.search(prev) or self.DIALOGUE_ENDINGS.search(prev):
                merged = prev + " " + line
                continue

            # Rule 3: Next line starts lowercase -> continuation
            if line and line[0].islower():
                merged = prev + " " + line
                continue

            # Rule 4: Previous line seems incomplete (no punctuation, ends mid-word)
            # and next line starts uppercase -> likely still same sentence
            # (common in manga panel text)
            if not self.SENTENCE_ENDINGS.search(prev):
                merged = prev + " " + line
                continue

            # Default: separate with space
            merged = prev + " " + line

        return merged.strip()

    def _apply_word_corrections(self, text: str) -> str:
        """Apply common OCR word-level corrections."""
        # Fix common OCR character issues first
        text = self._fix_ocr_chars(text)

        # Apply word corrections (case-insensitive, whole word)
        words = text.split()
        corrected_words = []
        for word in words:
            # Strip punctuation for lookup
            stripped = word.strip('.,!?;:"\'"\'()-[]{}')
            lower = stripped.lower()

            if lower in WORD_CORRECTIONS:
                correction = WORD_CORRECTIONS[lower]
                # Preserve surrounding punctuation
                prefix = word[: len(word) - len(word.lstrip('.,!?;:"\'"\'()-[]{}'))]
                suffix = word[len(word.rstrip('.,!?;:"\'"\'()-[]{}')):]
                # Preserve capitalization if original was capitalized
                if stripped and stripped[0].isupper() and not correction[0].isupper():
                    correction = correction[0].upper() + correction[1:]
                corrected_words.append(prefix + correction + suffix)
            else:
                corrected_words.append(word)

        return " ".join(corrected_words)

    def _fix_ocr_chars(self, text: str) -> str:
        """Fix common single-character OCR substitution errors."""
        # Fix standalone 'l' that should be 'I' (pronoun)
        # e.g., "l can't" -> "I can't"
        text = re.sub(r'\bl\b(?=\s+[a-z])', 'I', text)
        text = re.sub(r'(?<=\s)l(?=\s)', 'I', text)

        # Fix "0" in common words (context-aware)
        # This is very conservative to avoid false positives
        text = re.sub(r'\bG0\b', 'GO', text)
        text = re.sub(r'\bd0\b', 'do', text)
        text = re.sub(r'\bn0\b', 'no', text)
        text = re.sub(r'\bt0\b', 'to', text)
        text = re.sub(r'\bs0\b', 'so', text)

        # Fix "rn" -> "m" in common words
        text = re.sub(r'\bforrn\b', 'form', text)
        text = re.sub(r'\bforrned\b', 'formed', text)
        text = re.sub(r'\bseern\b', 'seem', text)
        text = re.sub(r'\bcorne\b', 'come', text)
        text = re.sub(r'\bsorne\b', 'some', text)
        text = re.sub(r'\bhorne\b', 'home', text)
        text = re.sub(r'\bfrorn\b', 'from', text)
        text = re.sub(r'\bwarn\b', 'warm', text)

        return text


class AICleanup:
    """
    Optional AI-based OCR cleanup using OpenAI API.
    Falls back gracefully if API is unavailable.
    """

    CLEANUP_PROMPT = (
        "You are an OCR text correction assistant. "
        "Fix OCR mistakes in the following text. "
        "Reconstruct proper English sentences while preserving the original meaning. "
        "Fix character substitution errors (l->I, 0->O, rn->m), "
        "fix missing apostrophes (cant->can't), fix spelling mistakes. "
        "Do NOT add new content or change the meaning. "
        "Return ONLY the corrected text, nothing else.\n\n"
        "Text to fix:\n{text}"
    )

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("openai package not installed.")
        return self._client

    def cleanup(self, text: str) -> str:
        """
        Use OpenAI to clean up OCR text.

        Args:
            text: Raw OCR text to clean

        Returns:
            Cleaned text, or original text if API call fails
        """
        if not self.api_key or not text.strip():
            return text

        try:
            client = self._get_client()
            prompt = self.CLEANUP_PROMPT.format(text=text)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1,  # Low temperature for factual correction
            )
            cleaned = response.choices[0].message.content.strip()
            return cleaned if cleaned else text
        except Exception as e:
            print(f"[Cleanup] AI cleanup failed: {e}. Using original text.")
            return text


def reconstruct_ocr_text(ocr_results: list[dict]) -> list[str]:
    """
    Main OCR reconstruction function.

    Args:
        ocr_results: Raw OCR output

    Returns:
        List of clean paragraph strings
    """
    reconstructor = OCRReconstructor()
    paragraphs = reconstructor.reconstruct(ocr_results)

    # Optional AI cleanup
    if settings.get("cleanup_with_ai") and settings.get("openai_api_key"):
        cleaner = AICleanup(
            api_key=settings.get("openai_api_key"),
            model=settings.get("openai_model", "gpt-4o-mini")
        )
        cleaned = []
        for para in paragraphs:
            cleaned.append(cleaner.cleanup(para))
        return cleaned

    return paragraphs