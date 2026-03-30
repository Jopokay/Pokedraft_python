"""
transitions.py — Simple fade-in / fade-out transitions for Pygame screens.
Usage:
    from transitions import fade_out, fade_in, fade_between

    fade_out(screen, clock, duration_ms=400)
    fade_in(screen, clock, duration_ms=400)
    # or combined:
    fade_between(screen, clock, duration_ms=300)
"""

import pygame


def fade_out(screen: pygame.Surface, clock, duration_ms: int = 400):
    """Fade the current screen to black."""
    overlay = pygame.Surface(screen.get_size())
    overlay.fill((0, 0, 0))
    steps = max(1, duration_ms // 16)  # ~60fps
    for i in range(steps + 1):
        alpha = int(255 * i / steps)
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        # Drain event queue so window doesn't appear frozen
        pygame.event.pump()


def fade_in(screen: pygame.Surface, clock, duration_ms: int = 400,
            bg_color=(0, 0, 0)):
    """Fade in from black — call this after drawing the new scene once."""
    overlay = pygame.Surface(screen.get_size())
    overlay.fill(bg_color)
    # Snapshot the new scene
    snapshot = screen.copy()
    steps = max(1, duration_ms // 16)
    for i in range(steps + 1):
        alpha = int(255 * (1 - i / steps))
        screen.blit(snapshot, (0, 0))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        pygame.event.pump()


def phase_transition(screen: pygame.Surface, clock,
                     label: str = "",
                     out_ms: int = 300, hold_ms: int = 500, in_ms: int = 300):
    """
    Fade out → show a centered label on black → fade in.
    Call this BETWEEN two phases before drawing the new phase.

    Example:
        phase_transition(screen, clock, "Move Selection")
        move_picker.run()
    """
    font = pygame.font.Font(None, 52)

    # --- Fade out ---
    fade_out(screen, clock, out_ms)

    # --- Hold frame with label ---
    screen.fill((0, 0, 0))
    if label:
        text = font.render(label, True, (200, 200, 200))
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2,
                           screen.get_height() // 2 - text.get_height() // 2))
    pygame.display.flip()
    pygame.time.delay(hold_ms)
    pygame.event.pump()

    # --- Fade in from black (caller will draw new scene in its first frame) ---
    # We do a brief fade-in from the label screen
    fade_in(screen, clock, in_ms)
