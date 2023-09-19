from __future__ import annotations


def tuples() -> list[tuple[str, tuple[str, ...]]]:
    return [
        ("Progressive Missile", ("Ice Missile", "Seeker Missile")),
        ("Progressive Beam", ("Plasma Beam", "Nova Beam")),
    ]
