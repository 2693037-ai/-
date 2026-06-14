import pygame
import random
import sys

# ── 초기화 ──────────────────────────────────────────────────────────────
pygame.init()

# ── 화면 설정 ────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 480, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sky Shooter")
clock = pygame.time.Clock()
FPS = 60
[]
# ── 색상 ─────────────────────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
DARK_BLUE  = (10,  10,  40)
BLUE       = (30,  80,  180)
CYAN       = (0,   200, 220)
GREEN      = (50,  220, 100)
RED        = (220, 50,  50)
ORANGE     = (255, 140, 0)
YELLOW     = (255, 230, 0)
GRAY       = (160, 160, 160)
LIGHT_GRAY = (200, 200, 200)
PURPLE     = (140, 60,  200)

# ── 폰트 ─────────────────────────────────────────────────────────────────
font_large  = pygame.font.SysFont("consolas", 48, bold=True)
font_medium = pygame.font.SysFont("consolas", 28, bold=True)
font_small  = pygame.font.SysFont("consolas", 20)

# ── 별(배경) 생성 ────────────────────────────────────────────────────────
NUM_STARS = 80
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
          random.choice([1, 1, 1, 2, 2, 3])) for _ in range(NUM_STARS)]

# ── 도형으로 비행기 그리기 헬퍼 ─────────────────────────────────────────

def draw_player(surface, x, y):
    """플레이어 비행기 (파란색/청록색 계열)"""
    cx = int(x)
    cy = int(y)
    # 동체
    pygame.draw.polygon(surface, CYAN, [
        (cx,      cy - 28),
        (cx - 14, cy + 18),
        (cx,      cy + 10),
        (cx + 14, cy + 18),
    ])
    # 날개
    pygame.draw.polygon(surface, BLUE, [
        (cx - 14, cy + 4),
        (cx - 30, cy + 22),
        (cx - 6,  cy + 14),
    ])
    pygame.draw.polygon(surface, BLUE, [
        (cx + 14, cy + 4),
        (cx + 30, cy + 22),
        (cx + 6,  cy + 14),
    ])
    # 꼬리
    pygame.draw.polygon(surface, BLUE, [
        (cx - 6,  cy + 10),
        (cx + 6,  cy + 10),
        (cx + 4,  cy + 20),
        (cx - 4,  cy + 20),
    ])
    # 조종석 (원)
    pygame.draw.circle(surface, WHITE, (cx, cy - 10), 5)
    # 엔진 불꽃
    pygame.draw.polygon(surface, ORANGE, [
        (cx - 4, cy + 20),
        (cx + 4, cy + 20),
        (cx,     cy + 32),
    ])
    pygame.draw.polygon(surface, YELLOW, [
        (cx - 2, cy + 20),
        (cx + 2, cy + 20),
        (cx,     cy + 26),
    ])


def draw_enemy(surface, x, y, variant=0):
    """적 비행기 (빨강/주황 계열). variant=0,1,2"""
    cx = int(x)
    cy = int(y)
    color_body = [RED, ORANGE, PURPLE][variant % 3]
    color_wing = [(160, 30, 30), (180, 90, 0), (90, 30, 160)][variant % 3]
    # 동체 (아래를 향해 뾰족)
    pygame.draw.polygon(surface, color_body, [
        (cx,      cy + 24),
        (cx - 12, cy - 14),
        (cx,      cy - 6),
        (cx + 12, cy - 14),
    ])
    # 날개
    pygame.draw.polygon(surface, color_wing, [
        (cx - 12, cy - 2),
        (cx - 28, cy + 14),
        (cx - 5,  cy + 6),
    ])
    pygame.draw.polygon(surface, color_wing, [
        (cx + 12, cy - 2),
        (cx + 28, cy + 14),
        (cx + 5,  cy + 6),
    ])
    # 조종석
    pygame.draw.circle(surface, LIGHT_GRAY, (cx, cy + 8), 4)


def draw_bullet_player(surface, x, y):
    pygame.draw.rect(surface, YELLOW, (int(x) - 2, int(y) - 8, 4, 14))
    pygame.draw.circle(surface, WHITE, (int(x), int(y) - 8), 3)


def draw_bullet_enemy(surface, x, y):
    pygame.draw.rect(surface, RED, (int(x) - 2, int(y) - 6, 4, 12))
    pygame.draw.circle(surface, ORANGE, (int(x), int(y) + 6), 3)


# ── 파티클 폭발 ──────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 6.28)
        speed = random.uniform(1.5, 5.0)
        self.vx = speed * __import__('math').cos(angle)
        self.vy = speed * __import__('math').sin(angle)
        self.life = random.randint(18, 36)
        self.max_life = self.life
        self.radius = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12   # 중력
        self.life -= 1

    def draw(self, surface):
        alpha_ratio = self.life / self.max_life
        r = max(0, min(255, int(self.color[0] * alpha_ratio)))
        g = max(0, min(255, int(self.color[1] * alpha_ratio)))
        b = max(0, min(255, int(self.color[2] * alpha_ratio)))
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), self.radius)

    @property
    def alive(self):
        return self.life > 0


def spawn_explosion(particles, x, y, colors=None):
    if colors is None:
        colors = [ORANGE, YELLOW, RED, WHITE]
    for _ in range(30):
        particles.append(Particle(x, y, random.choice(colors)))


# ── 게임 클래스 ──────────────────────────────────────────────────────────
class Game:
    PLAYER_SPEED   = 5
    BULLET_SPEED   = 10
    ENEMY_BULLET_SPEED = 4
    ENEMY_SHOOT_CHANCE = 0.004   # 프레임당 적 1기가 발사할 확률

    def __init__(self):
        self.reset()

    def reset(self):
        # 플레이어
        self.px = WIDTH / 2
        self.py = HEIGHT - 80
        self.player_alive = True
        self.invincible_timer = 0   # 데미지 후 무적 프레임

        # 총알
        self.p_bullets  = []   # (x, y)
        self.e_bullets  = []   # (x, y)

        # 적
        self.enemies = []      # (x, y, variant)
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 90  # 프레임 (난이도에 따라 감소)

        # 파티클
        self.particles = []

        # 게임 상태
        self.score = 0
        self.high_score = getattr(self, '_hs', 0)
        self._hs = self.high_score

        # 발사 쿨다운
        self.shoot_cooldown = 0

        # 배경 별 스크롤
        self.star_offset = 0

        # 게임 오버 연출
        self.gameover_timer = 0   # 0 = 살아있음, >0 = 연출 중
        self.state = "playing"    # "playing" | "gameover"

    # ── 업데이트 ─────────────────────────────────────────────────────────
    def update(self, keys):
        if self.state == "gameover":
            self.gameover_timer -= 1
            self.particles = [p for p in self.particles if p.alive]
            for p in self.particles:
                p.update()
            return

        # 별 스크롤
        self.star_offset = (self.star_offset + 1) % HEIGHT

        # 플레이어 이동
        if keys[pygame.K_LEFT]  and self.px > 24:  self.px -= self.PLAYER_SPEED
        if keys[pygame.K_RIGHT] and self.px < WIDTH - 24: self.px += self.PLAYER_SPEED
        if keys[pygame.K_UP]    and self.py > HEIGHT // 2: self.py -= self.PLAYER_SPEED
        if keys[pygame.K_DOWN]  and self.py < HEIGHT - 40: self.py += self.PLAYER_SPEED

        # 발사
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
        if keys[pygame.K_SPACE] and self.shoot_cooldown == 0:
            self.p_bullets.append([self.px, self.py - 28])
            self.shoot_cooldown = 12

        # 플레이어 총알 이동
        self.p_bullets = [[bx, by - self.BULLET_SPEED]
                          for bx, by in self.p_bullets if by > -10]

        # 적 스폰 (난이도: 점수 오를수록 빨라짐)
        self.enemy_spawn_interval = max(35, 90 - self.score // 3)
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            ex = random.randint(30, WIDTH - 30)
            variant = random.randint(0, 2)
            self.enemies.append([ex, -30, variant])

        # 적 이동 + 발사
        new_enemies = []
        for e in self.enemies:
            speed = 1.8 + self.score * 0.03
            e[1] += min(speed, 5.5)
            # 적 발사
            if random.random() < self.ENEMY_SHOOT_CHANCE + self.score * 0.00008:
                self.e_bullets.append([e[0], e[1] + 24])
            if e[1] < HEIGHT + 40:
                new_enemies.append(e)
        self.enemies = new_enemies

        # 적 총알 이동
        self.e_bullets = [[bx, by + self.ENEMY_BULLET_SPEED]
                          for bx, by in self.e_bullets if by < HEIGHT + 10]

        # 충돌: 플레이어 총알 vs 적
        surviving_enemies = []
        hit_bullets = set()
        for e in self.enemies:
            ex, ey, ev = e
            killed = False
            for i, (bx, by) in enumerate(self.p_bullets):
                if abs(bx - ex) < 20 and abs(by - ey) < 24:
                    killed = True
                    hit_bullets.add(i)
                    break
            if killed:
                self.score += 10
                spawn_explosion(self.particles, ex, ey, [ORANGE, YELLOW, RED, WHITE])
            else:
                surviving_enemies.append(e)
        self.enemies = surviving_enemies
        self.p_bullets = [b for i, b in enumerate(self.p_bullets) if i not in hit_bullets]

        # 충돌: 적 총알 or 적 vs 플레이어
        if self.player_alive and self.invincible_timer == 0:
            px, py = self.px, self.py
            # 적 총알
            for bx, by in self.e_bullets:
                if abs(bx - px) < 16 and abs(by - py) < 16:
                    self._player_die()
                    return
            # 적 기체 충돌
            for ex, ey, _ in self.enemies:
                if abs(ex - px) < 26 and abs(ey - py) < 26:
                    self._player_die()
                    return

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # 파티클 업데이트
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

    def _player_die(self):
        self.player_alive = False
        spawn_explosion(self.particles, self.px, self.py, [CYAN, WHITE, YELLOW, ORANGE])
        self._hs = max(self._hs, self.score)
        self.gameover_timer = 180   # 3초 연출
        self.state = "gameover"

    # ── 그리기 ───────────────────────────────────────────────────────────
    def draw(self, surface):
        # 배경
        surface.fill(DARK_BLUE)

        # 별
        for sx, sy, sr in stars:
            draw_y = (sy + self.star_offset) % HEIGHT
            brightness = 120 + sr * 30
            pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, draw_y), sr)

        # 플레이어 (무적 중 깜빡임)
        if self.player_alive:
            if self.invincible_timer == 0 or (self.invincible_timer // 4) % 2 == 0:
                draw_player(surface, self.px, self.py)

        # 플레이어 총알
        for bx, by in self.p_bullets:
            draw_bullet_player(surface, bx, by)

        # 적 기체
        for ex, ey, ev in self.enemies:
            draw_enemy(surface, ex, ey, ev)

        # 적 총알
        for bx, by in self.e_bullets:
            draw_bullet_enemy(surface, bx, by)

        # 파티클
        for p in self.particles:
            p.draw(surface)

        # HUD
        score_surf = font_medium.render(f"SCORE  {self.score:05d}", True, WHITE)
        surface.blit(score_surf, (12, 10))

        hs_surf = font_small.render(f"BEST {self._hs:05d}", True, GRAY)
        surface.blit(hs_surf, (WIDTH - hs_surf.get_width() - 12, 14))

        # 조작 안내 (플레이 중)
        if self.state == "playing":
            guide = font_small.render("← → ↑ ↓  MOVE    SPACE  FIRE", True, GRAY)
            surface.blit(guide, (WIDTH // 2 - guide.get_width() // 2, HEIGHT - 22))

        # 게임 오버 오버레이
        if self.state == "gameover":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = min(160, int(160 * (1 - self.gameover_timer / 180)))
            overlay.fill((0, 0, 0, alpha))
            surface.blit(overlay, (0, 0))

            go_surf = font_large.render("GAME OVER", True, RED)
            surface.blit(go_surf, (WIDTH // 2 - go_surf.get_width() // 2, HEIGHT // 2 - 80))

            sc_surf = font_medium.render(f"SCORE  {self.score:05d}", True, WHITE)
            surface.blit(sc_surf, (WIDTH // 2 - sc_surf.get_width() // 2, HEIGHT // 2 - 10))

            hs2_surf = font_medium.render(f"BEST   {self._hs:05d}", True, YELLOW)
            surface.blit(hs2_surf, (WIDTH // 2 - hs2_surf.get_width() // 2, HEIGHT // 2 + 30))

            if self.gameover_timer <= 0:
                retry_surf = font_small.render("Press  R  to RETRY   /   ESC  to QUIT", True, LIGHT_GRAY)
                surface.blit(retry_surf, (WIDTH // 2 - retry_surf.get_width() // 2, HEIGHT // 2 + 90))


# ── 메인 루프 ────────────────────────────────────────────────────────────
def main():
    game = Game()

    while True:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                # 게임 오버 후 재시작
                if event.key == pygame.K_r and game.state == "gameover" and game.gameover_timer <= 0:
                    game.reset()

        game.update(keys)
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()