"""Calcul du diff entre deux versions d'une source, et décision de significativité."""
import difflib
import hashlib
from dataclasses import dataclass


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class DiffResult:
    has_changed: bool
    is_significant: bool
    diff_text: str


def compute_diff(previous: str, current: str, min_changed_chars: int = 20) -> DiffResult:
    """Compare deux textes et renvoie un diff lisible (format unifié).

    `min_changed_chars` filtre les changements triviaux (espaces, détail isolé)
    pour éviter de déclencher une analyse IA — et une alerte — pour rien.
    """
    if previous == current:
        return DiffResult(has_changed=False, is_significant=False, diff_text="")

    diff_lines = list(
        difflib.unified_diff(previous.splitlines(), current.splitlines(), lineterm="", n=2)
    )
    diff_text = "\n".join(diff_lines)

    changed_chars = sum(
        len(line)
        for line in diff_lines
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    )
    is_significant = changed_chars >= min_changed_chars

    return DiffResult(has_changed=True, is_significant=is_significant, diff_text=diff_text)
