"""
rate_limiter.py — Logique pure de rate limiting et debouncing pour source_watch.
TricorderKit v0.9 — RISK-002

Extrait du workflow Temporal pour être testable indépendamment via pytest.
Miroir de la logique embarquée dans source_watch.workflow.ts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


# ── RateLimiter ────────────────────────────────────────────────────────────────


@dataclass
class RateLimiter:
    """
    Compteur de cycles sur fenêtre glissante d'une heure.
    Empêche les rafales de dépasser max_per_hour cycles.
    """

    max_per_hour: int = 10
    _cycle_timestamps: list[float] = field(default_factory=list, repr=False)

    def is_allowed(self, now: float | None = None) -> bool:
        """Retourne True si un nouveau cycle est autorisé."""
        now = now if now is not None else time.time()
        self._purge(now)
        return len(self._cycle_timestamps) < self.max_per_hour

    def record_cycle(self, now: float | None = None) -> None:
        """Enregistre un cycle comme exécuté."""
        now = now if now is not None else time.time()
        self._cycle_timestamps.append(now)

    def cycles_in_window(self, now: float | None = None) -> int:
        """Nombre de cycles dans la fenêtre actuelle."""
        now = now if now is not None else time.time()
        self._purge(now)
        return len(self._cycle_timestamps)

    def remaining(self, now: float | None = None) -> int:
        """Cycles restants autorisés dans la fenêtre."""
        return max(0, self.max_per_hour - self.cycles_in_window(now))

    def _purge(self, now: float) -> None:
        """Purge les timestamps hors fenêtre (> 1 heure)."""
        window_start = now - 3600.0
        self._cycle_timestamps = [t for t in self._cycle_timestamps if t > window_start]

    def reset(self) -> None:
        """Reset complet (pour tests)."""
        self._cycle_timestamps = []


# ── Debouncer ──────────────────────────────────────────────────────────────────


@dataclass
class Debouncer:
    """
    Absorbe les rafales d'événements en ne traitant qu'un seul événement
    par fenêtre de debounce.

    Fonctionnement :
      1. trigger()  → marque qu'un événement est en attente
      2. should_process()  → True uniquement si la fenêtre est écoulée
      3. consume()  → marque l'événement comme traité
    """

    window_seconds: float = 300.0  # 5 minutes par défaut
    _pending: bool = field(default=False, repr=False)
    _triggered_at: float | None = field(default=None, repr=False)

    def trigger(self, now: float | None = None) -> None:
        """
        Enregistre un événement externe.
        Si déjà en attente, refresh le timestamp (absorbe la rafale).
        """
        now = now if now is not None else time.time()
        if not self._pending:
            self._triggered_at = now
        self._pending = True

    def should_process(self, now: float | None = None) -> bool:
        """
        Retourne True si la fenêtre de debounce est écoulée ET qu'un
        événement est en attente.
        """
        if not self._pending or self._triggered_at is None:
            return False
        now = now if now is not None else time.time()
        return (now - self._triggered_at) >= self.window_seconds

    def consume(self) -> None:
        """Marque l'événement en attente comme traité."""
        self._pending = False
        self._triggered_at = None

    @property
    def pending(self) -> bool:
        return self._pending

    def reset(self) -> None:
        """Reset complet (pour tests)."""
        self._pending = False
        self._triggered_at = None


# ── CycleGuard : semaphore simple ──────────────────────────────────────────────


@dataclass
class CycleGuard:
    """
    Semaphore binaire : empêche l'exécution simultanée de deux cycles.
    Le workflow Temporal maintient `cycleInProgress` nativement ;
    cette classe miroir permet de tester la logique.
    """

    _in_progress: bool = field(default=False, repr=False)

    def acquire(self) -> bool:
        """
        Tente d'acquérir le verrou.
        Retourne True si acquis, False si déjà en cours.
        """
        if self._in_progress:
            return False
        self._in_progress = True
        return True

    def release(self) -> None:
        """Libère le verrou."""
        self._in_progress = False

    @property
    def locked(self) -> bool:
        return self._in_progress
