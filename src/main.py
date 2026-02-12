import os
import csv
import time
import random
import pygame
import math
from policy import FAMILIES, load_state, save_state


# -----------------------------
# Day 1: Baseline vertical slice
# -----------------------------

WIDTH, HEIGHT = 480, 720
FPS = 60

# Player physics
GRAVITY = 1800.0          # px/s^2
FLAP_VELOCITY = -520.0    # px/s (upwards)
PLAYER_SIZE = 34

# Obstacles (precision gaps)
PIPE_SPEED = 240.0        # px/s (to the left)
PIPE_WIDTH = 80
GAP_SIZE = 170
SPAWN_EVERY_S = 1.35

# Data logging
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "runs.csv")

CSV_FIELDS = [
    "timestamp_epoch",
    "player_id",
    "session_id",
    "run_id",
    "mode",
    "survival_time_s",
    "score_passed_pipes",
    "death_reason",
    "obstacle_family",
    "tap_count",
    "tap_mean_interval_ms",
    "tap_sd_interval_ms",
]

def ensure_csv_exists():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()

def safe_stats_intervals_ms(tap_times_s):
    """
    Convert tap timestamps into intervals (ms) and return mean & sd.
    If fewer than 2 taps, return blanks.
    """
    if len(tap_times_s) < 2:
        return "", ""
    intervals_ms = []
    for i in range(1, len(tap_times_s)):
        intervals_ms.append((tap_times_s[i] - tap_times_s[i - 1]) * 1000.0)

    mean = sum(intervals_ms) / len(intervals_ms)
    # population SD is fine for our purposes
    var = sum((x - mean) ** 2 for x in intervals_ms) / len(intervals_ms)
    sd = var ** 0.5
    return round(mean, 2), round(sd, 2)

def log_run(row: dict):
    ensure_csv_exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(row)

class Player:
    def __init__(self):
        self.x = int(WIDTH * 0.28)
        self.y = int(HEIGHT * 0.5)
        self.vy = 0.0

    @property
    def rect(self):
        return pygame.Rect(
            self.x - PLAYER_SIZE // 2,
            self.y - PLAYER_SIZE // 2,
            PLAYER_SIZE,
            PLAYER_SIZE
        )

    def flap(self):
        self.vy = FLAP_VELOCITY

    def update(self, dt):
        self.vy += GRAVITY * dt
        self.y += self.vy * dt

class PipePair:
    """
    One obstacle family for Day 1: precision gap pipes.
    Represented as two rects (top + bottom) with a gap.
    """
    def __init__(self, x):
        self.family = "precision_gap"
        self.gap = GAP_SIZE
        self.speed = PIPE_SPEED
        margin = 80
        gap_y = random.randint(margin + int(self.gap // 2), HEIGHT - margin - int(self.gap // 2))
        self.x = x
        self.gap_y = gap_y
        self.passed = False

    def update(self, dt):
        self.x -= self.speed * dt

    def is_offscreen(self):
        return self.x + PIPE_WIDTH < 0

    def rects(self):
        top_height = self.gap_y - self.gap / 2
        bot_y = self.gap_y + self.gap / 2
        bot_height = HEIGHT - bot_y

        top = pygame.Rect(int(self.x), 0, PIPE_WIDTH, int(top_height))
        bottom = pygame.Rect(int(self.x), int(bot_y), PIPE_WIDTH, int(bot_height))
        return top, bottom
    
class TimingGatePair:
    """
    Timing family: the gap 'breathes' (opens/closes) over time.
    Same shape as pipes, but the window pulses, so timing matters.
    """
    def __init__(self, x):
        self.family = "timing_gate"
        self.gap = GAP_SIZE
        self.speed = PIPE_SPEED
        margin = 90
        self.gap_y = random.randint(margin + int(self.gap // 2), HEIGHT - margin - int(self.gap // 2))

        self.x = x
        self.passed = False

        # Gap breathing params
        self.base_gap = self.gap          # centered around Day 1 gap size
        self.amp = 70                     # how much it opens/closes
        self.omega = 2 * math.pi * 0.8    # ~0.8 cycles/sec
        self.t0 = time.time()

    def update(self, dt):
        self.x -= self.speed * dt

    def is_offscreen(self):
        return self.x + PIPE_WIDTH < 0

    def current_gap(self):
        g = self.base_gap + self.amp * math.sin(self.omega * (time.time() - self.t0))
        return max(110, min(260, g))  # clamp so it never becomes impossible or too wide

    def rects(self):
        self.gap = self.current_gap()
        top_height = self.gap_y - self.gap / 2
        bot_y = self.gap_y + self.gap / 2
        bot_height = HEIGHT - bot_y

        top = pygame.Rect(int(self.x), 0, PIPE_WIDTH, int(top_height))
        bottom = pygame.Rect(int(self.x), int(bot_y), PIPE_WIDTH, int(bot_height))
        return top, bottom

class RhythmWavePair:
    """
    Rhythm family: the gap center moves in a predictable wave.
    Player can lock into the pattern if they learn the cadence.
    """
    def __init__(self, x):
        self.family = "rhythm_wave"
        self.x = x
        self.passed = False

        self.base_gap = GAP_SIZE
        self.gap = self.base_gap  # constant gap size, but moving center
        self.speed = PIPE_SPEED

        # Wave center motion
        self.center_base = HEIGHT * 0.5
        self.amp_y = 170                  # how far the gap center swings
        self.omega = 2 * math.pi * 0.65   # cycles/sec
        self.t0 = time.time()

    def update(self, dt):
        self.x -= self.speed * dt

    def is_offscreen(self):
        return self.x + PIPE_WIDTH < 0

    def rects(self):
        # Oscillating gap center
        center = self.center_base + self.amp_y * math.sin(self.omega * (time.time() - self.t0))

        # Clamp center so the gap stays on-screen
        margin = 90
        center = max(margin + self.gap / 2, min(HEIGHT - margin - self.gap / 2, center))

        top_height = center - self.gap / 2
        bot_y = center + self.gap / 2
        bot_height = HEIGHT - bot_y

        top = pygame.Rect(int(self.x), 0, PIPE_WIDTH, int(top_height))
        bottom = pygame.Rect(int(self.x), int(bot_y), PIPE_WIDTH, int(bot_height))
        return top, bottom

def enforce_variety(choice, recent, window=10):
    if len(recent) < window:
        return choice

    last2_same = len(recent) >= 2 and recent[-1] == recent[-2]
    if last2_same and choice == recent[-1]:
        # force a different family
        for f in ["precision_gap", "timing_gate", "rhythm_wave"]:
            if f != choice:
                return f

    # ensure coverage in window
    seen = set(recent[-window:])
    if len(seen) < 3:
        missing = [f for f in ["precision_gap", "timing_gate", "rhythm_wave"] if f not in seen]
        if missing:
            return missing[0]

    return choice


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    DAY_LABEL = "Day 3 â€” Rhythm Waves"
    pygame.display.set_caption(f"PUFF+ {DAY_LABEL}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)

    # Session + identity
    player_id = "farrah"  # keep simple for now
    session_id = str(int(time.time()))

    skill, bandit = load_state()        # <- loading state happens here
    recent_families = []
    difficulty = 0.0
    
    run_id = 0
    mode = "baseline"

    def reset_run():
        nonlocal run_id
        run_id += 1
        return {
            "player": Player(),
            "obstacles": [],
            "spawn_timer": 0.0,
            "start_time": time.time(),
            "alive": True,
            "death_reason": "", 
            "death_family": "",
            "score_passed": 0,
            "tap_times": [],
            "spawn_count": 0,
            "last_why": "",
            "why_timer": 0.0,
            "last_spawn_family": "",
        }

    state = "RUNNING"  # RUNNING | GAME_OVER
    run = reset_run()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ---- Events
        for event in pygame.event.get():    # <- THIS is the event loop
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    mode = "personalised" if mode == "baseline" else "baseline"

            # One-button: space or left mouse click
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if state == "RUNNING":
                        run["player"].flap()
                        run["tap_times"].append(time.time())
                    elif state == "GAME_OVER":
                        state = "RUNNING"
                        run = reset_run()

                if event.key == pygame.K_ESCAPE:
                    running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if state == "RUNNING":
                        run["player"].flap()
                        run["tap_times"].append(time.time())
                    elif state == "GAME_OVER":
                        state = "RUNNING"
                        run = reset_run()

        # ---- Update
        if state == "RUNNING":
            run["player"].update(dt)

            # Spawn obstacles (3 families)
            run["spawn_timer"] += dt
            if run["spawn_timer"] >= SPAWN_EVERY_S:
                run["spawn_timer"] = 0.0
                # after you set `family` and `why`...
                d_eff = difficulty if mode == "personalised" else 0.0  # keep baseline clean for A/B

                gap_scale   = 1.0 - 0.18 * d_eff
                speed_scale = 1.0 + 0.20 * d_eff

                # 1) decide family
                if mode == "baseline":
                    # fixed cycle (still good for A/B comparisons)
                    if run["spawn_count"] % 3 == 0:
                        family = "precision_gap"
                    elif run["spawn_count"] % 3 == 1:
                        family = "timing_gate"
                    else:
                        family = "rhythm_wave"
                    run["spawn_count"] += 1
                    why = "baseline cycle"
                else:
                    skill_bin = skill.bin()
                    family, scores = bandit.choose_family(skill_bin, recent_families)
                    
                    family2 = enforce_variety(family, recent_families, window=10)
                    if family2 != family:
                        family = family2
                        why = f"TS({skill_bin}) picked {family} (variety override)"
                    else:
                        why = f"TS({skill_bin}) picked {family}"

                run["last_spawn_family"] = family

                # create obstacle instance + apply per-instance tuning
                d_eff = difficulty if mode == "personalised" else 0.0
                gap_scale   = 1.0 - 0.18 * d_eff
                speed_scale = 1.0 + 0.20 * d_eff

                if family == "precision_gap":
                    o = PipePair(WIDTH + 10)
                    o.gap = GAP_SIZE * gap_scale
                    o.speed = PIPE_SPEED * speed_scale
                elif family == "timing_gate":
                    o = TimingGatePair(WIDTH + 10)
                    o.base_gap = GAP_SIZE * gap_scale
                    o.speed = PIPE_SPEED * speed_scale
                    o.amp = 70 * (1.0 + 0.3 * d_eff)
                else:
                    o = RhythmWavePair(WIDTH + 10)
                    o.gap = GAP_SIZE * gap_scale
                    o.speed = PIPE_SPEED * speed_scale
                    o.amp_y = 170 * (1.0 + 0.3 * d_eff)

                run["obstacles"].append(o)
                
                recent_families.append(family)
                if len(recent_families) > 20:
                    recent_families.pop(0)

                # store last 'why' to display briefly
                run["last_why"] = why
                run["why_timer"] = 2.0

                
            # Update pipes
            for o in run["obstacles"]:
                o.update(dt)

            # Remove offscreen
            run["obstacles"] = [o for o in run["obstacles"] if not o.is_offscreen()]

            # Score: count pipes passed
            for o in run["obstacles"]:
                if not o.passed and o.x + PIPE_WIDTH < run["player"].x:
                    o.passed = True
                    run["score_passed"] += 1

            # Death conditions: hit ground/ceiling
            if run["player"].y - PLAYER_SIZE // 2 <= 0:
                run["death_reason"] = "ceiling"
                run["death_family"] = ""
                state = "GAME_OVER"
            elif run["player"].y + PLAYER_SIZE // 2 >= HEIGHT:
                run["death_reason"] = "ground"
                run["death_family"] = ""
                state = "GAME_OVER"
            else:
                # Collision with pipes
                player_rect = run["player"].rect
                for o in run["obstacles"]:
                    top, bottom = o.rects()
                    if player_rect.colliderect(top) or player_rect.colliderect(bottom):
                        run["death_reason"] = "obstacle_collision"
                        run["death_family"] = o.family
                        state = "GAME_OVER"
                        break

            # If just died, log immediately
            if state == "GAME_OVER":
                end_time = time.time()
                survival = end_time - run["start_time"]

                target = 8.0  # seconds
                reward = max(0.0, min(1.0, survival / target))

                if mode == "personalised":
                    skill_bin = skill.bin()
                    skill.update(survival)

                    # update difficulty once per run (not per frame)
                    delta = (reward - 0.6) * 0.05
                    delta = max(-0.03, min(0.03, delta))
                    difficulty = max(0.0, min(1.0, difficulty + delta))

                    family = run.get("death_family")
                    if run.get("death_reason") == "obstacle_collision" and family in FAMILIES:
                        bandit.update(skill_bin, family, reward)
                
                    save_state(skill, bandit)

                tap_count = len(run["tap_times"])
                mean_ms, sd_ms = safe_stats_intervals_ms(run["tap_times"])

                row = {
                    "timestamp_epoch": int(end_time),
                    "player_id": player_id,
                    "session_id": session_id,
                    "run_id": run_id,
                    "mode": mode,
                    "survival_time_s": round(survival, 3),
                    "score_passed_pipes": run["score_passed"],
                    "death_reason": run.get("death_reason", ""),
                    "obstacle_family": run.get("death_family", ""),
                    "tap_count": tap_count,
                    "tap_mean_interval_ms": mean_ms,
                    "tap_sd_interval_ms": sd_ms,
                }
                log_run(row)

        # ---- Draw
        screen.fill((18, 18, 24))
        mode_text = small_font.render(f"Mode: {mode}", True, (200, 200, 210))
        screen.blit(mode_text, (20, 120))

        if run.get("why_timer", 0) > 0:
            run["why_timer"] -= dt
            why_text = small_font.render(run.get("last_why", ""), True, (180, 180, 200))
            screen.blit(why_text, (20, 145))

        # Draw obstacles
        for o in run["obstacles"]:
            top, bottom = o.rects()

            if o.family == "precision_gap":
                color = (80, 200, 140)
            elif o.family == "timing_gate":
                color = (220, 170, 90)
            else:
                color = (160, 120, 255)  # rhythm_wave

            pygame.draw.rect(screen, color, top)
            pygame.draw.rect(screen, color, bottom)


        # Draw player
        pygame.draw.rect(screen, (240, 240, 245), run["player"].rect)

        # HUD
        now = time.time()
        survival_live = now - run["start_time"] if state == "RUNNING" else None

        score_text = font.render(f"Score: {run['score_passed']}", True, (240, 240, 245))
        screen.blit(score_text, (20, 20))

        if state == "RUNNING":
            t_text = small_font.render(f"Time: {survival_live:.2f}s", True, (200, 200, 210))
            screen.blit(t_text, (20, 60))
            hint = small_font.render("SPACE / Click = flap", True, (160, 160, 180))
            screen.blit(hint, (20, 90))
        else:
            over = font.render("GAME OVER", True, (255, 200, 200))
            screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 60))

            tip = small_font.render("Press SPACE or Click to restart", True, (220, 220, 230))
            screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT // 2 - 20))

            tip2 = small_font.render("ESC to quit", True, (160, 160, 180))
            screen.blit(tip2, (WIDTH // 2 - tip2.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

