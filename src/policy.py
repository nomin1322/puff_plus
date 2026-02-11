import json
import os
import random

STATE_PATH = os.path.join("data", "policy_state.json")

FAMILIES = ["precision_gap", "timing_gate", "rhythm_wave"]

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

class SkillTracker:
    """
    Simple skill estimate using exponential moving average of survival time.
    """
    def __init__(self, ema_survival=3.0, alpha=0.15):
        self.ema_survival = float(ema_survival)
        self.alpha = float(alpha)

    def update(self, survival_time_s: float):
        if survival_time_s is None:
            return
        self.ema_survival = (1 - self.alpha) * self.ema_survival + self.alpha * float(survival_time_s)

    def bin(self):
        """
        Discretise skill to make a tiny contextual bandit.
        """
        s = self.ema_survival
        if s < 3.0:
            return "low"
        if s < 8.0:
            return "mid"
        return "high"

class ThompsonBandit:
    """
    Contextual (binned) Thompson sampling with Beta distributions.
    Reward is treated as probability-like in [0, 1].
    """
    def __init__(self):
        # params[skill_bin][family] = [a, b]
        self.params = {b: {f: [1.0, 1.0] for f in FAMILIES} for b in ["low", "mid", "high"]}
        self.last_choice = None

    def sample_beta(self, a, b):
        # random.betavariate exists in Python stdlib
        return random.betavariate(a, b)

    def choose_family(self, skill_bin: str, recent_families: list[str]):
        """
        Choose by Thompson sampling, with a light anti-repeat guard.
        """
        scores = {}
        for f in FAMILIES:
            a, b = self.params[skill_bin][f]
            scores[f] = self.sample_beta(a, b)

        # tiny variety nudge: if last 2 spawns were same family, downweight it
        if len(recent_families) >= 2 and recent_families[-1] == recent_families[-2]:
            repeat = recent_families[-1]
            scores[repeat] *= 0.6

        choice = max(scores, key=scores.get)
        self.last_choice = choice
        return choice, scores

    def update(self, skill_bin: str, family: str, reward: float):
        reward = clamp(float(reward), 0.0, 1.0)
        a, b = self.params[skill_bin][family]
        # Interpret reward as success probability
        self.params[skill_bin][family] = [a + reward, b + (1.0 - reward)]

def load_state():
    if not os.path.exists(STATE_PATH):
        return SkillTracker(), ThompsonBandit()

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    st = SkillTracker(raw.get("ema_survival", 3.0), raw.get("alpha", 0.15))
    tb = ThompsonBandit()
    tb.params = raw.get("bandit_params", tb.params)
    return st, tb

def save_state(skill: SkillTracker, bandit: ThompsonBandit):
    os.makedirs("data", exist_ok=True)
    raw = {
        "ema_survival": skill.ema_survival,
        "alpha": skill.alpha,
        "bandit_params": bandit.params,
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)
