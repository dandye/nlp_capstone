"""
Per-label format validators for structured CTI entity types.

The 300-span gold audit (2026-07-19) found that most bad training labels
in structured types are mechanically detectable: hash fragments with
invalid lengths (PDF line-wrap splits), the literal word 'Ipv4' labeled
as an IP, phone numbers as email addresses, 'CWE-22:' with trailing
punctuation, shell/code fragments as file paths. These types have
grammars — a label that fails its grammar is noise by construction.

Used as a GENERATION gate (llm_gold drops failing spans
before they become training labels), not just an eval-time flag.
Semantic types with no grammar (malware family, threat actor group,
hacking tool, product, tactic/technique names) validate as True — noise
there needs context, not format checks.

validate(label_or_prefix, text) accepts either the GLiNER label name
("file hash") or the annotation prefix ("SHA256") — both vocabularies
exist in the pipeline (PREFIX_TO_LABEL / LABEL_PREFIX).
"""

from __future__ import annotations

import re

# Defanged forms are standard in CTI text: 1.2.3[.]4, user@dom[.]com,
# hxxp://... — validators must accept them (they are real, extractable
# indicators), so [.] is normalized to . before matching.


def _refang(t: str) -> str:
    return t.replace("[.]", ".").replace("[@]", "@").replace("hxxp", "http")


def _clean(t: str) -> str:
    """Strip wrapping punctuation the tokenizer drags along."""
    return _refang(t.strip()).strip(".,;:!?\"'()[]{}<>")


_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_VALID_HASH_LENS = frozenset({32, 40, 64, 128})
_IPV4_RE = re.compile(
    r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(:\d+)?(/\S*)?$"
)
_IPV6_RE = re.compile(r"^[0-9a-fA-F:]+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,7}$", re.IGNORECASE)
_CWE_RE = re.compile(r"^CWE-\d{1,4}$", re.IGNORECASE)
_TCODE_RE = re.compile(r"^T\d{4}(\.\d{3})?$", re.IGNORECASE)
_TACODE_RE = re.compile(r"^TA\d{4}$", re.IGNORECASE)
_TLP_RE = re.compile(
    r"^(CISA\s+)?TLP\s*:?\s*(CLEAR|WHITE|GREEN|AMBER(\+STRICT)?|RED)$",
    re.IGNORECASE,
)


def _valid_hash(t: str) -> bool:
    t = _clean(t)
    return bool(_HEX_RE.match(t)) and len(t) in _VALID_HASH_LENS


def _valid_ip(t: str) -> bool:
    t = _clean(t)
    m = _IPV4_RE.match(t)
    if m:
        return all(int(m.group(i)) <= 255 for i in range(1, 5))
    # IPv6: needs at least two colons and hex groups
    return t.count(":") >= 2 and bool(_IPV6_RE.match(t))


def _valid_email(t: str) -> bool:
    return bool(_EMAIL_RE.match(_clean(t)))


def _valid_cve(t: str) -> bool:
    return bool(_CVE_RE.match(_clean(t)))


def _valid_cwe(t: str) -> bool:
    # audit case 'CWE-22:' — _clean strips the colon; 'CWE-89: SQL' fails (space)
    return bool(_CWE_RE.match(_clean(t)))


def _valid_technique_id(t: str) -> bool:
    t = _clean(t)
    return bool(_TCODE_RE.match(t)) or bool(_TACODE_RE.match(t))


def _valid_tlp(t: str) -> bool:
    return bool(_TLP_RE.match(_clean(t)))


# Keyed by BOTH the GLiNER label name and the annotation prefixes that
# map to it, so callers can use whichever vocabulary they hold.
_VALIDATORS = {
    "file hash": _valid_hash,
    "MD5": _valid_hash, "SHA1": _valid_hash, "SHA256": _valid_hash,
    "SHA512": _valid_hash, "HASH": _valid_hash,
    "ip address": _valid_ip,
    "IP": _valid_ip, "IPV6": _valid_ip,
    "email address": _valid_email,
    "EMAIL": _valid_email,
    "cve identifier": _valid_cve,
    "CVE": _valid_cve, "VULN": _valid_cve,
    "cwe identifier": _valid_cwe,
    "CWE": _valid_cwe,
    "attack technique id": _valid_technique_id,
    "ATTACK": _valid_technique_id,
    "tlp classification": _valid_tlp,
    "TLP": _valid_tlp,
}

# Regex-derived types easily fooled by code fragments (audit: os.path...
# as file path, PGPASSWORD={};echo as email). These are suppressed when a
# candidate value appears ONLY inside code regions. Types with strong
# validators (hash, IP, CVE...) are exempt — a valid hash in a script IS
# an indicator worth keeping.
CODE_FRAGILE_PREFIXES = frozenset(
    {"FILEPATH", "FILENAME", "EMAIL", "DOMAIN", "URL"}
)


def validate(label_or_prefix: str, text: str) -> bool:
    """True if text is a plausible instance of the label. Labels without
    a format grammar always validate (format can't judge them)."""
    fn = _VALIDATORS.get(label_or_prefix)
    if fn is None:
        return True
    return fn(text)
