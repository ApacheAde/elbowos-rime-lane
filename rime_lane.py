#!/usr/bin/env python3
"""RIME LANE — neon curling arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/RIME_LANE_ElbowOS.mp4")
TITLE, HANDLE = "RIME LANE", "x.com/ElbowOS"

NAVY = (6, 18, 48)
ICE = (18, 56, 98)
TEAL = (40, 230, 220)
CYAN = (120, 255, 255)
GOLD = (255, 210, 70)
CORAL = (255, 78, 118)
MAG = (255, 70, 200)
VIO = (150, 110, 255)
WHITE = (240, 250, 255)
LIME = (160, 255, 110)
INK = (8, 28, 68)

HOUSE_Y, HOUSE_R = 340, 210
LANE_L, LANE_R = 150, 930
LAUNCH_Y = 1680
STONE_R = 42


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 58, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 38, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 26)
        self.clock = pygame.time.Clock()
        self.score = self.best = self.t = 0
        self.flash = self.banner = 0
        self.aim = 0.0
        self.power = 0.55
        self.charging = False
        self.stones = []
        self.sparks, self.rings = [], []
        self.guards = [(340, 980, 34), (740, 1080, 34), (540, 860, 28)]
        self.snow = [[random.randint(LANE_L, LANE_R), random.randint(180, H - 80),
                      random.uniform(0.4, 1.6)] for _ in range(55)]
        self.next_shot = 12
        self.team = 0
        self.banner_txt = ""

    def burst(self, x, y, col, n=14):
        for _ in range(n):
            a = random.uniform(0, 6.2832)
            sp = random.uniform(2, 11)
            self.sparks.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 18, col])

    def launch(self, aim=None, power=None):
        a = self.aim if aim is None else aim
        p = self.power if power is None else power
        col = CORAL if self.team % 2 == 0 else TEAL
        self.stones.append({
            "x": W / 2 + a * 210, "y": LAUNCH_Y, "vx": a * 7.2,
            "vy": -(16.5 + p * 17.5), "r": STONE_R, "col": col,
            "spin": a * 0.08, "a": 0.0, "live": True, "team": self.team % 2,
        })
        self.team += 1
        self.burst(W / 2 + a * 210, LAUNCH_Y, col, 10)

    def autoplay(self):
        if self.next_shot <= 0 and len([s for s in self.stones if s["live"]]) < 7:
            target = random.uniform(-0.42, 0.42)
            self.aim += (target - self.aim) * 0.35
            self.power = random.uniform(0.42, 0.95)
            self.launch()
            self.next_shot = random.randint(38, 58)
        else:
            self.aim += math.sin(self.t * 0.11) * 0.012
            self.aim = max(-0.85, min(0.85, self.aim))

    def score_house(self):
        pts = 0
        for s in self.stones:
            d = math.hypot(s["x"] - W / 2, s["y"] - HOUSE_Y)
            if d < HOUSE_R * 0.28:
                pts += 8
            elif d < HOUSE_R * 0.55:
                pts += 5
            elif d < HOUSE_R * 0.82:
                pts += 3
            elif d < HOUSE_R:
                pts += 1
        return pts

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.banner = max(0, self.banner - 1)
        self.next_shot = max(0, self.next_shot - 1)
        if self.charging:
            self.power = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(self.t * 0.18))
        for s in self.stones:
            if not s["live"]:
                continue
            s["vy"] += 0.12
            s["vx"] *= 0.992
            s["vy"] *= 0.988
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["a"] += s["spin"] + s["vx"] * 0.01
            if s["x"] < LANE_L + s["r"]:
                s["x"] = LANE_L + s["r"]
                s["vx"] *= -0.62
                self.burst(s["x"], s["y"], CYAN, 6)
            if s["x"] > LANE_R - s["r"]:
                s["x"] = LANE_R - s["r"]
                s["vx"] *= -0.62
                self.burst(s["x"], s["y"], CYAN, 6)
            if s["y"] < 190 + s["r"]:
                s["y"] = 190 + s["r"]
                s["vy"] *= -0.35
                s["vx"] *= 0.8
            if s["y"] > LAUNCH_Y + 40:
                s["live"] = False
            for gx, gy, gr in self.guards:
                d = math.hypot(s["x"] - gx, s["y"] - gy) or 1
                if d < s["r"] + gr:
                    nx, ny = (s["x"] - gx) / d, (s["y"] - gy) / d
                    overlap = s["r"] + gr - d
                    s["x"] += nx * overlap
                    s["y"] += ny * overlap
                    dot = s["vx"] * nx + s["vy"] * ny
                    s["vx"] -= 1.7 * dot * nx
                    s["vy"] -= 1.7 * dot * ny
                    self.burst(s["x"], s["y"], GOLD, 8)
            if abs(s["vx"]) < 0.18 and abs(s["vy"]) < 0.18 and s["y"] < 1500:
                s["vx"] = s["vy"] = 0
        n = len(self.stones)
        for i in range(n):
            a = self.stones[i]
            if not a["live"]:
                continue
            for j in range(i + 1, n):
                b = self.stones[j]
                if not b["live"]:
                    continue
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                d = math.hypot(dx, dy) or 1
                if d < a["r"] + b["r"]:
                    nx, ny = dx / d, dy / d
                    overlap = a["r"] + b["r"] - d
                    a["x"] -= nx * overlap * 0.5
                    a["y"] -= ny * overlap * 0.5
                    b["x"] += nx * overlap * 0.5
                    b["y"] += ny * overlap * 0.5
                    av = a["vx"] * nx + a["vy"] * ny
                    bv = b["vx"] * nx + b["vy"] * ny
                    a["vx"] += (bv - av) * nx
                    a["vy"] += (bv - av) * ny
                    b["vx"] += (av - bv) * nx
                    b["vy"] += (av - bv) * ny
                    self.burst((a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2, WHITE, 10)
                    self.flash = 3
        house = self.score_house()
        if house > self.score:
            self.banner = 10
            self.banner_txt = "SHEET"
            self.rings.append([W / 2, HOUSE_Y, 12, GOLD])
        self.score = house
        self.best = max(self.best, self.score)
        for sp in self.sparks:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[4] -= 1
        self.sparks = [sp for sp in self.sparks if sp[4] > 0]
        for r in self.rings:
            r[2] += 8
        self.rings = [r for r in self.rings if r[2] < 220]
        for e in self.snow:
            e[1] += e[2]
            e[0] += math.sin(self.t * 0.05 + e[1] * 0.01) * 0.4
            if e[1] > H - 40:
                e[1] = 200
                e[0] = random.randint(LANE_L, LANE_R)

    def draw(self, surf):
        surf.fill(NAVY)
        pygame.draw.rect(surf, ICE, (LANE_L - 24, 170, LANE_R - LANE_L + 48, 1580), border_radius=40)
        pygame.draw.rect(surf, (28, 78, 128), (LANE_L, 190, LANE_R - LANE_L, 1540), border_radius=28)
        for i, y in enumerate(range(260, 1640, 70)):
            shade = 40 + (i % 2) * 10
            pygame.draw.line(surf, (shade, 110, 160), (LANE_L + 10, y), (LANE_R - 10, y), 1)
        pygame.draw.circle(surf, (30, 90, 160), (W // 2, HOUSE_Y), HOUSE_R)
        pygame.draw.circle(surf, (70, 40, 90), (W // 2, HOUSE_Y), int(HOUSE_R * 0.82))
        pygame.draw.circle(surf, (20, 130, 150), (W // 2, HOUSE_Y), int(HOUSE_R * 0.55))
        pygame.draw.circle(surf, CORAL, (W // 2, HOUSE_Y), int(HOUSE_R * 0.28))
        pygame.draw.circle(surf, GOLD, (W // 2, HOUSE_Y), HOUSE_R, 4)
        pygame.draw.circle(surf, WHITE, (W // 2, HOUSE_Y), int(HOUSE_R * 0.55), 3)
        pygame.draw.line(surf, CYAN, (LANE_L, HOUSE_Y), (LANE_R, HOUSE_Y), 2)
        pygame.draw.line(surf, CYAN, (W // 2, 190), (W // 2, 1640), 2)
        for gx, gy, gr in self.guards:
            pygame.draw.circle(surf, VIO, (gx, gy), gr + 6)
            pygame.draw.circle(surf, GOLD, (gx, gy), gr)
            pygame.draw.circle(surf, WHITE, (gx - 8, gy - 8), 7)
        for e in self.snow:
            pygame.draw.circle(surf, (180, 220, 255), (int(e[0]), int(e[1])), 2)
        for s in self.stones:
            if not s["live"] and s["y"] > 1600:
                continue
            pygame.draw.circle(surf, (10, 20, 40), (int(s["x"] + 6), int(s["y"] + 8)), s["r"])
            pygame.draw.circle(surf, s["col"], (int(s["x"]), int(s["y"])), s["r"])
            pygame.draw.circle(surf, WHITE, (int(s["x"] - 10), int(s["y"] - 12)), 12)
            pygame.draw.circle(surf, GOLD, (int(s["x"]), int(s["y"])), s["r"], 3)
            hx = s["x"] + math.cos(s["a"]) * 16
            hy = s["y"] + math.sin(s["a"]) * 16
            pygame.draw.circle(surf, WHITE, (int(hx), int(hy)), 6)
        for r in self.rings:
            pygame.draw.circle(surf, r[3], (int(r[0]), int(r[1])), int(r[2]), 3)
        for sp in self.sparks:
            pygame.draw.circle(surf, sp[5], (int(sp[0]), int(sp[1])), max(2, sp[4] // 4))
        ax = W / 2 + self.aim * 210
        pygame.draw.circle(surf, GOLD, (int(ax), LAUNCH_Y), 18, 3)
        pygame.draw.line(surf, LIME, (int(ax), LAUNCH_Y),
                         (int(ax + self.aim * 90), LAUNCH_Y - int(80 + self.power * 140)), 4)
        bar_w = int(320 * self.power)
        pygame.draw.rect(surf, INK, (W // 2 - 170, 1768, 340, 22), border_radius=8)
        pygame.draw.rect(surf, LIME if self.power < 0.8 else CORAL,
                         (W // 2 - 166, 1772, bar_w, 14), border_radius=6)
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 210, 70, 24))
            surf.blit(ov, (0, 0))
        if self.banner:
            lab = self.font.render(self.banner_txt or "SHEET", True, GOLD)
            surf.blit(lab, lab.get_rect(center=(W // 2, 210)))
        title = self.font_lg.render(TITLE, True, CYAN)
        surf.blit(title, title.get_rect(center=(W // 2, 72)))
        sub = self.font_sm.render(HANDLE, True, MAG)
        surf.blit(sub, sub.get_rect(center=(W // 2, 128)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        cb = self.font_sm.render(f"HOUSE  {self.score}   BEST  {self.best}", True, GOLD)
        hint = self.font_sm.render("A/D aim   SPACE launch   hold to charge", True, TEAL)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 118)))
        surf.blit(cb, cb.get_rect(center=(W // 2, H - 72)))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 32)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_w):
                    self.charging = True
                if ev.type == pygame.KEYUP and ev.key in (pygame.K_SPACE, pygame.K_w):
                    self.charging = False
                    self.launch()
                    self.power = 0.55
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.aim = max(-0.85, self.aim - 0.03)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.aim = min(0.85, self.aim + 0.03)
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
