"""
test_source_watch_rate_limiter.py — Tests unitaires RISK-002
TricorderKit v0.9

Couvre RateLimiter, Debouncer et CycleGuard extraits de source_watch.workflow.ts.
Aucune dépendance réseau — pytest pur, temps simulé via paramètre `now`.
"""

import sys
import os

# Assure l'import sans installation du package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'workflow-engine'))

import pytest
from rate_limiter import RateLimiter, Debouncer, CycleGuard


# ── Fixtures ───────────────────────────────────────────────────────────────────

BASE_TIME = 1_700_000_000.0   # timestamp fixe pour les tests
ONE_HOUR  = 3600.0
ONE_MIN   = 60.0


# ── RateLimiter ────────────────────────────────────────────────────────────────

class TestRateLimiter:

    def test_premier_cycle_autorise(self):
        """Un RateLimiter vide autorise le premier cycle."""
        rl = RateLimiter(max_per_hour=10)
        assert rl.is_allowed(now=BASE_TIME) is True

    def test_cycle_enregistre_incremente_compteur(self):
        rl = RateLimiter(max_per_hour=10)
        rl.record_cycle(now=BASE_TIME)
        assert rl.cycles_in_window(now=BASE_TIME) == 1

    def test_limite_atteinte_bloque(self):
        """Après max_per_hour cycles, is_allowed retourne False."""
        rl = RateLimiter(max_per_hour=3)
        for i in range(3):
            rl.record_cycle(now=BASE_TIME + i)
        assert rl.is_allowed(now=BASE_TIME + 3) is False

    def test_cycles_hors_fenetre_expires(self):
        """Les cycles enregistrés il y a plus d'une heure n'entrent plus dans le compteur."""
        rl = RateLimiter(max_per_hour=3)
        for i in range(3):
            rl.record_cycle(now=BASE_TIME + i)
        # Avancer d'une heure + 1 seconde
        assert rl.is_allowed(now=BASE_TIME + ONE_HOUR + 1) is True

    def test_fenetre_glissante_partielle(self):
        """Seuls les cycles dans la fenêtre comptent."""
        rl = RateLimiter(max_per_hour=5)
        # 2 cycles anciens (hors fenêtre)
        rl.record_cycle(now=BASE_TIME)
        rl.record_cycle(now=BASE_TIME + 10)
        # 2 cycles récents (dans la fenêtre)
        now = BASE_TIME + ONE_HOUR + 100
        rl.record_cycle(now=now - 100)
        rl.record_cycle(now=now - 50)
        assert rl.cycles_in_window(now=now) == 2
        assert rl.remaining(now=now) == 3

    def test_reset_vide_le_compteur(self):
        rl = RateLimiter(max_per_hour=2)
        rl.record_cycle(now=BASE_TIME)
        rl.record_cycle(now=BASE_TIME + 1)
        assert rl.is_allowed(now=BASE_TIME + 2) is False
        rl.reset()
        assert rl.is_allowed(now=BASE_TIME + 2) is True


# ── Debouncer ──────────────────────────────────────────────────────────────────

class TestDebouncer:

    def test_sans_trigger_should_process_false(self):
        d = Debouncer(window_seconds=300)
        assert d.should_process(now=BASE_TIME) is False

    def test_trigger_avant_fenetre_not_ready(self):
        """Trigger reçu, fenêtre pas encore écoulée → should_process False."""
        d = Debouncer(window_seconds=300)
        d.trigger(now=BASE_TIME)
        assert d.should_process(now=BASE_TIME + 100) is False

    def test_trigger_apres_fenetre_ready(self):
        """Trigger reçu, fenêtre écoulée → should_process True."""
        d = Debouncer(window_seconds=300)
        d.trigger(now=BASE_TIME)
        assert d.should_process(now=BASE_TIME + 300) is True

    def test_rafale_n_etend_pas_la_fenetre(self):
        """Un 2e trigger dans la fenêtre ne repousse PAS l'horloge."""
        d = Debouncer(window_seconds=300)
        d.trigger(now=BASE_TIME)       # t=0 : premier trigger
        d.trigger(now=BASE_TIME + 200) # t=200 : rafale
        # t=310 : fenêtre du premier trigger écoulée → doit être prêt
        assert d.should_process(now=BASE_TIME + 310) is True

    def test_consume_remet_a_zero(self):
        d = Debouncer(window_seconds=300)
        d.trigger(now=BASE_TIME)
        d.consume()
        assert d.pending is False
        assert d.should_process(now=BASE_TIME + 400) is False

    def test_pending_flag(self):
        d = Debouncer(window_seconds=60)
        assert d.pending is False
        d.trigger(now=BASE_TIME)
        assert d.pending is True
        d.consume()
        assert d.pending is False


# ── CycleGuard ─────────────────────────────────────────────────────────────────

class TestCycleGuard:

    def test_acquire_libre(self):
        g = CycleGuard()
        assert g.acquire() is True
        assert g.locked is True

    def test_acquire_deja_locked(self):
        """Le 2e acquire échoue si déjà en cours."""
        g = CycleGuard()
        g.acquire()
        assert g.acquire() is False

    def test_release_debloque(self):
        g = CycleGuard()
        g.acquire()
        g.release()
        assert g.locked is False
        assert g.acquire() is True

    def test_trigger_ignore_si_cycle_en_cours(self):
        """
        Simule le comportement du workflow : un trigger externe est ignoré
        si cycleInProgress est True (CycleGuard verrouillé).
        """
        rl = RateLimiter(max_per_hour=10)
        d  = Debouncer(window_seconds=60)
        g  = CycleGuard()

        g.acquire()          # cycle en cours
        d.trigger(now=BASE_TIME)

        # Même si le trigger arrive, on ne doit pas démarrer un cycle
        # (le workflow vérifie g.locked avant d'appeler execute)
        can_start = not g.locked and d.should_process(now=BASE_TIME + 100) and rl.is_allowed(now=BASE_TIME + 100)
        assert can_start is False

    def test_cycle_autorise_apres_release(self):
        """Après release + debounce écoulé + rate ok → cycle autorisé."""
        rl = RateLimiter(max_per_hour=10)
        d  = Debouncer(window_seconds=60)
        g  = CycleGuard()

        g.acquire()
        d.trigger(now=BASE_TIME)
        g.release()

        can_start = not g.locked and d.should_process(now=BASE_TIME + 61) and rl.is_allowed(now=BASE_TIME + 61)
        assert can_start is True
