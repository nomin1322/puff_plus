import os
import csv
import time
import random
import pygame

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
        margin = 80
        gap_y = random.randint(margin + GAP_SIZE // 2, HEIGHT - margin - GAP_SIZE // 2)
        self.x = x
        self.gap_y = gap_y
        self.passed = False

    def update(self, dt):
        self.x -= PIPE_SPEED * dt

    def is_offscreen(self):
        return self.x + PIPE_WIDTH < 0

    def rects(self):
        top_height = self.gap_y - GAP_SIZE // 2
        bot_y = self.gap_y + GAP_SIZE // 2
        bot_height = HEIGHT - bot_y

        top = pygame.Rect(int(self.x), 0, PIPE_WIDTH, int(top_height))
        bottom = pygame.Rect(int(self.x), int(bot_y), PIPE_WIDTH, int(bot_height))
        return top, bottom

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PUFF+ Day 1 Baseline Slice")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)

    # Session + identity
    player_id = "farrah"  # keep simple for now
    session_id = str(int(time.time()))

    run_id = 0
    mode = "baseline"
    obstacle_family = "precision_gap"

    def reset_run():
        nonlocal run_id
        run_id += 1
        return {
            "player": Player(),
            "pipes": [],
            "spawn_timer": 0.0,
            "start_time": time.time(),
            "alive": True,
            "death_reason": "",
            "score_passed": 0,
            "tap_times": [],
        }

    state = "RUNNING"  # RUNNING | GAME_OVER
    run = reset_run()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ---- Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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

            # Spawn pipes
            run["spawn_timer"] += dt
            if run["spawn_timer"] >= SPAWN_EVERY_S:
                run["spawn_timer"] = 0.0
                run["pipes"].append(PipePair(WIDTH + 10))

            # Update pipes
            for p in run["pipes"]:
                p.update(dt)

            # Remove offscreen
            run["pipes"] = [p for p in run["pipes"] if not p.is_offscreen()]

            # Score: count pipes passed
            for p in run["pipes"]:
                if not p.passed and p.x + PIPE_WIDTH < run["player"].x:
                    p.passed = True
                    run["score_passed"] += 1

            # Death conditions: hit ground/ceiling
            if run["player"].y - PLAYER_SIZE // 2 <= 0:
                run["death_reason"] = "ceiling"
                state = "GAME_OVER"
            elif run["player"].y + PLAYER_SIZE // 2 >= HEIGHT:
                run["death_reason"] = "ground"
                state = "GAME_OVER"
            else:
                # Collision with pipes
                player_rect = run["player"].rect
                for p in run["pipes"]:
                    top, bottom = p.rects()
                    if player_rect.colliderect(top) or player_rect.colliderect(bottom):
                        run["death_reason"] = "pipe_collision"
                        state = "GAME_OVER"
                        break

            # If just died, log immediately
            if state == "GAME_OVER":
                end_time = time.time()
                survival = end_time - run["start_time"]
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
                    "death_reason": run["death_reason"],
                    "obstacle_family": obstacle_family,
                    "tap_count": tap_count,
                    "tap_mean_interval_ms": mean_ms,
                    "tap_sd_interval_ms": sd_ms,
                }
                log_run(row)

        # ---- Draw
        screen.fill((18, 18, 24))

        # Draw pipes
        for p in run["pipes"]:
            top, bottom = p.rects()
            pygame.draw.rect(screen, (80, 200, 140), top)
            pygame.draw.rect(screen, (80, 200, 140), bottom)

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
