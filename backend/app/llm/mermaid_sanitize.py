"""Normalize Mermaid node identifiers to ASCII-safe tokens; labels inside [] stay as-is."""

from __future__ import annotations

import re


def _clean_id(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token.strip()))


def sanitize_mermaid(diagram: str) -> str:
    if not diagram or not diagram.strip():
        return diagram

    id_map: dict[str, str] = {}
    n = 0

    def mapped(raw: str) -> str:
        nonlocal n
        t = raw.strip()
        if not t or _clean_id(t):
            return t
        if t not in id_map:
            n += 1
            id_map[t] = f"n{n}"
        return id_map[t]

    out_lines: list[str] = []
    for line in diagram.splitlines():
        # Node: something[label] or something(label)
        m = re.match(r"^(\s*)(\S+?)(\s*[\[\(])", line)
        if m:
            pre, nid, br = m.groups()
            new_id = mapped(nid)
            rest = line[m.end() :]
            line = f"{pre}{new_id}{br}{rest}"

        # Simple edges: token --> token (ignore lines with [ to avoid breaking labels)
        if "-->" in line and "[" not in line and "(" not in line:
            segs = re.split(r"(\s*-->\s*)", line)
            if len(segs) >= 3:
                fixed: list[str] = []
                for i, seg in enumerate(segs):
                    if i % 2 == 1:
                        fixed.append(seg)
                        continue
                    parts = re.split(r"(\s+)", seg)
                    buf: list[str] = []
                    for p in parts:
                        if not p.strip() or re.fullmatch(r"\s+", p):
                            buf.append(p)
                            continue
                        buf.append(mapped(p) if not _clean_id(p) else p)
                    fixed.append("".join(buf))
                line = "".join(fixed)

        out_lines.append(line)

    return "\n".join(out_lines)
