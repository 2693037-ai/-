import pygame
import random
import sys
import math
from sounds import init_sounds

# ── 초기화 ────────────────────────────────────────────────────────────────
pygame.init()
SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 640
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter")

# ── 색상 ──────────────────────────────────────────────────────────────────
BLACK    = (0,   0,   0)
WHITE    = (255, 255, 255)
BLUE     = (0,   128, 255)
RED      = (255, 50,  50)
YELLOW   = (255, 255, 0)
GREEN    = (50,  255, 50)
ORANGE   = (255, 128, 0)
CYAN     = (0,   255, 255)
PURPLE   = (147, 112, 219)
HOT_PINK = (255, 105, 180)
LIME     = (180, 255, 60)
LIME_DARK= (100, 200, 30)
DARK_GRAY= (30,  30,  40)
GOLD     = (255, 215, 0)

# ── 추가 팔레트 (space_shooter.py) ───────────────────────────────────────
DEEP_SPACE    = (6,   8,  20)
NEBULA_BLUE   = (10,  20, 50)
NEBULA_PURPLE = (25,  10, 45)
PLAYER_CORE   = (80, 180, 255)
PLAYER_BODY   = (30,  90, 180)
PLAYER_ENGINE = (0,  220, 255)
THRUSTER_HOT  = (255, 200, 80)
THRUSTER_MID  = (255, 100, 20)
THRUSTER_COLD = (180, 30,  80)
BULLET_CORE   = (255, 255, 180)
BULLET_GLOW   = (255, 255, 80)
HUD_BG        = (8,  12,  30, 200)
HUD_BORDER    = (40, 80, 160)
HP_FULL       = (0,  220, 120)
HP_MID        = (255, 200, 0)
HP_LOW        = (255, 50,  50)
WAVE_GOLD     = (255, 210, 60)
SCORE_COL     = (200, 230, 255)

clock = pygame.time.Clock()
FPS   = 60

# ── 베스트 스코어 영속 저장 ──────────────────────────────────────────────
_BEST_SCORE_FILE = 'best_score.txt'

def _load_best_score():
    try:
        with open(_BEST_SCORE_FILE, 'r') as f:
            return max(0, int(f.read().strip()))
    except Exception:
        return 0

def _save_best_score(s):
    try:
        with open(_BEST_SCORE_FILE, 'w') as f:
            f.write(str(s))
    except Exception:
        pass

best_score = _load_best_score()

# ════════════════════════════════════════════════════════════════════════════
#  스프라이트 생성 함수 (space_shooter.py)
# ════════════════════════════════════════════════════════════════════════════

def make_player_sprite(w=40, h=40):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body_pts = [
        (w//2, 0), (w//2-6, h//3), (w//2-12, h*2//3),
        (w//2-16, h), (w//2, h*5//6), (w//2+16, h),
        (w//2+12, h*2//3), (w//2+6, h//3),
    ]
    pygame.draw.polygon(surf, PLAYER_BODY, body_pts)
    pygame.draw.polygon(surf, PLAYER_CORE, [(w//2, 2), (w//2-4, h//3+2), (w//2+4, h//3+2)])
    pygame.draw.line(surf, PLAYER_CORE, (w//2, 2), (w//2, h*5//6), 2)
    pygame.draw.polygon(surf, (20, 60, 140), [(w//2-6, h//3), (0, h*3//4), (w//2-14, h*3//4)])
    pygame.draw.polygon(surf, (20, 60, 140), [(w//2+6, h//3), (w, h*3//4), (w//2+14, h*3//4)])
    pygame.draw.line(surf, PLAYER_CORE, (w//2-6, h//3), (2, h*3//4-4), 1)
    pygame.draw.line(surf, PLAYER_CORE, (w//2+6, h//3), (w-2, h*3//4-4), 1)
    pygame.draw.ellipse(surf, (100, 200, 255, 200), (w//2-5, h//8, 10, 12))
    pygame.draw.ellipse(surf, (200, 240, 255, 100), (w//2-3, h//8+1, 5, 6))
    pygame.draw.rect(surf, (20, 50, 100), (w//2-5, h-8, 10, 8))
    pygame.draw.rect(surf, PLAYER_ENGINE, (w//2-3, h-6, 6, 4))
    return surf

def make_thruster_flame(frame):
    w, h = 14, 18
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    flicker = math.sin(frame * 0.8) * 0.3 + 0.7
    fh = int(h * flicker)
    for i in range(fh):
        ratio = i / fh
        if ratio < 0.3:
            c = THRUSTER_HOT
        elif ratio < 0.6:
            r = int(THRUSTER_HOT[0] + (THRUSTER_MID[0]-THRUSTER_HOT[0])*(ratio-0.3)/0.3)
            g = int(THRUSTER_HOT[1] + (THRUSTER_MID[1]-THRUSTER_HOT[1])*(ratio-0.3)/0.3)
            b = int(THRUSTER_HOT[2] + (THRUSTER_MID[2]-THRUSTER_HOT[2])*(ratio-0.3)/0.3)
            c = (r, g, b)
        else:
            r = int(THRUSTER_MID[0] + (THRUSTER_COLD[0]-THRUSTER_MID[0])*(ratio-0.6)/0.4)
            g = int(THRUSTER_MID[1] + (THRUSTER_COLD[1]-THRUSTER_MID[1])*(ratio-0.6)/0.4)
            b = int(THRUSTER_MID[2] + (THRUSTER_COLD[2]-THRUSTER_MID[2])*(ratio-0.6)/0.4)
            c = (r, g, b)
        alpha = int(220 * (1 - ratio))
        width = int((w//2) * (1 - ratio * 0.5) * flicker)
        if width > 0:
            pygame.draw.line(surf, c + (alpha,), (w//2 - width, i), (w//2 + width, i), 1)
    return surf

def make_enemy_sprite(etype, w=40, h=40):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if etype == 0:
        # 황토색 찌그러진 삼각형 동체 (작고 볼품없음)
        body = [(w//2+2, 10), (w-8, h-5), (6, h-5)]
        pygame.draw.polygon(surf, (160, 120, 40), body)
        pygame.draw.polygon(surf, (190, 150, 60), body, 1)
        # 긁힌 듯한 균열선
        pygame.draw.line(surf, (100, 75, 20), (w//2, 14), (w//2-3, h-8), 1)
        pygame.draw.line(surf, (100, 75, 20), (w//2+3, 18), (w//2+5, h-9), 1)
        # 엔진 흔적 (작고 희미한 사각형 2개)
        pygame.draw.rect(surf, (120, 90, 25), (w//2-7, h-7, 5, 4))
        pygame.draw.rect(surf, (120, 90, 25), (w//2+2, h-7, 5, 4))
    elif etype == 1:
        pygame.draw.circle(surf, (180, 80, 20), (w//2, h//2), w//2-3)
        pygame.draw.circle(surf, (255, 130, 40), (w//2, h//2), w//2-3, 2)
        pygame.draw.rect(surf, (255, 160, 60), (w//2-10, h-6, 5, 8))
        pygame.draw.rect(surf, (255, 160, 60), (w//2+5, h-6, 5, 8))
        pygame.draw.circle(surf, (255, 200, 120), (w//2, h//2), 6)
    elif etype == 2:
        pts = [(w//2+int((w//2-4)*math.cos(math.radians(60*i-90))),
                h//2+int((h//2-4)*math.sin(math.radians(60*i-90)))) for i in range(6)]
        pygame.draw.polygon(surf, (160, 140, 0), pts)
        pygame.draw.polygon(surf, (255, 220, 0), pts, 2)
        pygame.draw.circle(surf, (255, 240, 80), (w//2, h//2), 8)
        pygame.draw.circle(surf, (255, 255, 180), (w//2, h//2), 4)
    elif etype == 3:
        body = [(w//2, 2), (w-4, h//2), (w//2, h-2), (4, h//2)]
        pygame.draw.polygon(surf, (0, 140, 160), body)
        pygame.draw.polygon(surf, (0, 240, 255), body, 2)
        pygame.draw.line(surf, (100, 255, 255), (w//2, 8), (w//2, h-8), 1)
        pygame.draw.line(surf, (100, 255, 255), (8, h//2), (w-8, h//2), 1)
    elif etype == 4:
        pts = [(w//2+int((w//2-4)*math.cos(math.radians(60*i-30))),
                h//2+int((h//2-4)*math.sin(math.radians(60*i-30)))) for i in range(6)]
        pygame.draw.polygon(surf, (80, 160, 20), pts)
        pygame.draw.polygon(surf, (180, 255, 60), pts, 2)
        pygame.draw.line(surf, (220, 255, 100), (w//4, h//4), (w*3//4, h*3//4), 2)
        pygame.draw.line(surf, (220, 255, 100), (w*3//4, h//4), (w//4, h*3//4), 2)
    elif etype == 5:
        sw, sh = 24, 24
        pts = [(sw//2, sh-2), (0, 2), (sw, 2)]
        pygame.draw.polygon(surf, (60, 150, 20), pts)
        pygame.draw.polygon(surf, (140, 255, 60), pts, 1)
    elif etype == 6:
        # ── 빨간 전투기 (미니보스) ──────────────────────────────────────
        # 동체
        body = [(w//2,2),(w-5,h*2//3),(w//2+7,h-3),(w//2,h-8),(w//2-7,h-3),(5,h*2//3)]
        pygame.draw.polygon(surf, (180, 15, 15), body)
        pygame.draw.polygon(surf, (255, 60, 60), body, 2)
        # 좌우 날개
        pygame.draw.polygon(surf, (130, 8, 8),
                            [(5,h*2//3),(0,h-3),(w//2-5,h//2)])
        pygame.draw.polygon(surf, (130, 8, 8),
                            [(w-5,h*2//3),(w,h-3),(w//2+5,h//2)])
        # 날개 테두리
        pygame.draw.polygon(surf, (220, 50, 50),
                            [(5,h*2//3),(0,h-3),(w//2-5,h//2)], 1)
        pygame.draw.polygon(surf, (220, 50, 50),
                            [(w-5,h*2//3),(w,h-3),(w//2+5,h//2)], 1)
        # 캐노피
        pygame.draw.ellipse(surf, (255, 110, 110), (w//2-5, h//8, 10, 14))
        pygame.draw.ellipse(surf, (255, 210, 210), (w//2-3, h//8+2, 5, 6))
        # 엔진 노즐
        pygame.draw.rect(surf, (90, 5, 5),    (w//2-4, h-7, 8, 7))
        pygame.draw.rect(surf, (255, 80, 0),  (w//2-2, h-5, 4, 5))
        # 중심선
        pygame.draw.line(surf, (255, 80, 80), (w//2, 4), (w//2, h-9), 1)
    return surf

def make_boss_sprite(w=80, h=48):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body = [
        (w//2, 2), (w-8, 10), (w-4, h-4),
        (w//2+6, h-10), (w//2, h-4),
        (w//2-6, h-10), (4, h-4), (8, 10)
    ]
    pygame.draw.polygon(surf, (80, 30, 130), body)
    pygame.draw.polygon(surf, (180, 80, 255), body, 2)
    pygame.draw.polygon(surf, (60, 20, 100), [(8, 10), (0, h//2), (12, h*3//4)])
    pygame.draw.polygon(surf, (60, 20, 100), [(w-8, 10), (w, h//2), (w-12, h*3//4)])
    pygame.draw.circle(surf, (220, 100, 255), (w//2, h//2), 12)
    pygame.draw.circle(surf, (255, 200, 255), (w//2, h//2), 7)
    pygame.draw.circle(surf, (255, 255, 255), (w//2, h//2), 3)
    for px in [w//2, w//4, w*3//4]:
        pygame.draw.rect(surf, (200, 60, 255), (px-3, h-6, 6, 8))
    pygame.draw.line(surf, (140, 60, 200), (w//4, h//4), (w*3//4, h//4), 1)
    pygame.draw.line(surf, (140, 60, 200), (w//5, h//2), (w*4//5, h//2), 1)
    return surf

def make_item_sprite(itype, w=30, h=30):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if itype == 1:
        pygame.draw.circle(surf, HOT_PINK, (w//2-7, h//3), 8)
        pygame.draw.circle(surf, HOT_PINK, (w//2+7, h//3), 8)
        pygame.draw.polygon(surf, HOT_PINK, [(w//2-14, h//3+2), (w//2, h-4), (w//2+14, h//3+2)])
        pygame.draw.circle(surf, (255, 180, 220), (w//2-5, h//3-2), 3)
    return surf

def make_bullet_surface(radius):
    sz = (radius + 6) * 2
    surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz // 2, sz // 2
    for r in range(radius + 5, radius - 1, -1):
        alpha = int(80 * (1 - (r - radius) / 5)) if r > radius else 200
        pygame.draw.circle(surf, (BULLET_GLOW[0], BULLET_GLOW[1], BULLET_GLOW[2], alpha), (cx, cy), r)
    pygame.draw.circle(surf, BULLET_CORE, (cx, cy), radius)
    return surf

def make_enemy_bullet_surface(radius):
    sz = (radius + 5) * 2
    surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz // 2, sz // 2
    pygame.draw.circle(surf, (255, 80, 0, 60), (cx, cy), radius + 4)
    pygame.draw.circle(surf, (255, 140, 30, 130), (cx, cy), radius + 2)
    pygame.draw.circle(surf, (255, 200, 80), (cx, cy), radius)
    return surf

def make_missile_surface():
    """유도 미사일 – 위쪽(음의 y)이 탄두 방향인 기저 서피스."""
    w, h = 8, 22
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # 탄두 (삼각형, 위쪽)
    pygame.draw.polygon(surf, (255, 90, 90), [(w//2, 0), (1, 6), (w-1, 6)])
    # 동체
    pygame.draw.rect(surf, (200, 30, 30), (2, 5, 4, 13))
    # 동체 하이라이트
    pygame.draw.line(surf, (255, 150, 150), (w//2, 2), (w//2, h-8), 1)
    # 꼬리 날개 (fin)
    pygame.draw.polygon(surf, (150, 10, 10), [(0, h-1), (3, h-8), (3, h)])
    pygame.draw.polygon(surf, (150, 10, 10), [(w, h-1), (w-3, h-8), (w-3, h)])
    return surf

# ── 폰트 ──────────────────────────────────────────────────────────────────
def load_korean_font(size, bold=False):
    for name in ("malgun gothic", "맑은 고딕", "gulim", "dotum", "batang"):
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f.render("가", True, (255,255,255)).get_width() > 1:
                return f
        except Exception:
            pass
    return pygame.font.SysFont(None, size, bold=bold)

font           = load_korean_font(30)
small_font     = load_korean_font(20)
big_font       = load_korean_font(48, bold=True)
hp_font        = load_korean_font(14, bold=True)
aug_title_font = load_korean_font(18, bold=True)
aug_desc_font  = load_korean_font(14)

# ── 스프라이트 캐시 ───────────────────────────────────────────────────────
PLAYER_SPRITE = make_player_sprite()
ENEMY_SPRITES = {i: make_enemy_sprite(i) for i in range(7)}
BOSS_SPRITE   = make_boss_sprite()
ITEM_SPRITES  = {1: make_item_sprite(1)}

_bullet_surf_cache = {}
def get_bullet_surf(radius):
    if radius not in _bullet_surf_cache:
        _bullet_surf_cache[radius] = make_bullet_surface(radius)
    return _bullet_surf_cache[radius]

ENEMY_BULLET_SURF  = make_enemy_bullet_surface(4)
MISSILE_RADIUS = 6
MISSILE_SURF   = make_missile_surface()
THRUSTER_FRAMES = [make_thruster_flame(i) for i in range(8)]
thruster_frame = 0

# ── 플레이어 기본값 ────────────────────────────────────────────────────────
player_width  = 40
player_height = 40

player_max_hp      = 3
player_hp          = player_max_hp
player_speed       = 5
bullet_speed       = 7
bullet_radius      = 5
AUTO_FIRE_INTERVAL = 24   # AI기말branch.py 기준 (느린 초기 연사)
bullet_straight    = 1
bullet_spread      = 0
bullet_damage      = 1    # AI기말branch.py 추가: 탄환 대미지

player_x = (SCREEN_WIDTH  // 2) - (player_width  // 2)
player_y = (SCREEN_HEIGHT - player_height - 20)

bullets          = []
enemy_bullets    = []
enemy_bullet_speed  = 5
enemy_bullet_radius = 4

# ── 적 ────────────────────────────────────────────────────────────────────
enemies      = []
enemy_width  = 40
enemy_height = 40
enemy_speed  = 3

SPLIT_WIDTH  = 24
SPLIT_HEIGHT = 24

# ── 아이템 ────────────────────────────────────────────────────────────────
items       = []
item_width  = 30
item_height = 30
item_speed  = 4

# ── 파티클 ────────────────────────────────────────────────────────────────
particles = []

# ── 미사일 / 스폰 링 이펙트 ──────────────────────────────────────────────
clown_balls    = []   # 유도 미사일: [x, y, dx, dy]
number_effects = []   # (미사용, 호환성 유지)
spawn_rings    = []   # 미니보스 등장 링: {x, y, max_r, life, max_life}

# ── 보스 ──────────────────────────────────────────────────────────────────
boss_active       = False
boss_hp           = 0
boss_max_hp       = 20
boss_x            = 0
boss_y            = 50
boss_width        = 80
boss_height       = 40
boss_speed        = 2
boss_direction    = 1
boss_shoot_counter= 0
boss_anim_timer   = 0

# ── 레이저 ────────────────────────────────────────────────────────────────
laser_state        = 0
laser_state_timer  = 0
laser_spawn_counter= 0
laser_x = laser_y  = 0
laser_height       = 16
laser_damaged_player = False

# ── 보스 수직 레이저 (AI기말branch.py, 웨이브 10+) ───────────────────────
boss_laser_state          = 0
boss_laser_timer          = 0
boss_laser_counter        = 0
boss_laser_xs             = []
boss_laser_damaged_player = False
BOSS_LASER_INTERVAL       = 450

# ── 아이템 스폰 카운터 ───────────────────────────────────────────────────
item_spawn_counter = 0

# ── 피격 플래시 / 무적 (space_shooter.py) ────────────────────────────────
damage_flash_timer = 0
invincible_timer   = 0

# ── 팝업 텍스트 (space_shooter.py) ───────────────────────────────────────
popups = []

# ── 배경 시스템 (space_shooter.py) ───────────────────────────────────────
stars = []
for _ in range(80):
    layer = random.choices([0, 1, 2], weights=[50, 30, 20])[0]
    sz    = [1, 1, 2][layer]
    spd   = [0.2, 0.5, 1.0][layer]
    base  = random.randint(30, 60) + layer * 30
    col   = (base, base, min(255, base + random.randint(0, 30)))
    stars.append([random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), sz, spd, col, layer])

def make_nebula():
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT * 2), pygame.SRCALPHA)
    for _ in range(6):
        cx = random.randint(40, SCREEN_WIDTH - 40)
        cy = random.randint(40, SCREEN_HEIGHT * 2 - 40)
        rx = random.randint(60, 160)
        ry = random.randint(40, 120)
        for scale in range(5, 0, -1):
            alpha = random.randint(4, 12)
            base_col = random.choice([NEBULA_BLUE, NEBULA_PURPLE, (15, 5, 35)])
            nebula_s = pygame.Surface((rx * scale // 2 * 2, ry * scale // 2 * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(nebula_s, base_col + (alpha,),
                                (0, 0, rx * scale // 2 * 2, ry * scale // 2 * 2))
            s.blit(nebula_s, (cx - rx * scale // 4, cy - ry * scale // 4))
    return s

_nebula_surf   = make_nebula()
_nebula_y_offset = 0.0

def _make_bg_base():
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        ratio = y / SCREEN_HEIGHT
        r = int(DEEP_SPACE[0] + (NEBULA_BLUE[0] - DEEP_SPACE[0]) * ratio * 0.3)
        g = int(DEEP_SPACE[1] + (NEBULA_BLUE[1] - DEEP_SPACE[1]) * ratio * 0.3)
        b = int(DEEP_SPACE[2] + (NEBULA_BLUE[2] - DEEP_SPACE[2]) * ratio * 0.5)
        pygame.draw.line(s, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    return s

_bg_base = _make_bg_base()

# ── 자동 연사 ─────────────────────────────────────────────────────────────
auto_fire_counter = 0

# ── 게임 상태 ─────────────────────────────────────────────────────────────
score     = 0
game_over = False

# ════════════════════════════════════════════════════════════════════════════
#  웨이브 시스템
# ════════════════════════════════════════════════════════════════════════════
current_wave       = 1
wave_kill_goal     = 20
wave_kills         = 0
wave_enemy_spawned = 0
wave_spawn_total   = 25
enemy_spawn_counter= 0
wave_spawn_interval= 30

wave_state      = 'playing'
wave_clear_timer= 0
WAVE_CLEAR_SHOW = 120

BOSS_WAVE_INTERVAL = 5
boss_spawned_count = 0
AUGMENT_EVERY = 4

# ════════════════════════════════════════════════════════════════════════════
#  증강 시스템
# ════════════════════════════════════════════════════════════════════════════
AUGMENT_POOL = [
    {'id':'max_hp',          'name':'최대 체력 +1',    'desc':'최대 HP가 1 증가하고\n현재 HP도 1 회복됩니다.',      'color':HOT_PINK, 'icon':'heart'},
    {'id':'bullet_spd',      'name':'탄환 속도 +2',    'desc':'발사체가 더 빠르게\n날아갑니다.',                   'color':CYAN,     'icon':'bullet'},
    {'id':'bullet_straight', 'name':'직선 탄환 +1',    'desc':'정면으로 날아가는\n탄환이 1개 늘어납니다.\n(최대 3발)', 'color':YELLOW, 'icon':'straight'},
    {'id':'bullet_spread',   'name':'사선 탄환 +1쌍',  'desc':'좌우 대각선으로\n탄환 1쌍이 추가됩니다.\n(최대 3쌍)', 'color':LIME,   'icon':'spread'},
    {'id':'move_spd',        'name':'이동 속도 +1',    'desc':'플레이어가 더 빠르게\n이동합니다.',                  'color':GREEN,    'icon':'arrow'},
    {'id':'fire_rate',       'name':'연사 속도 +',     'desc':'탄환 발사 쿨다운이\n줄어듭니다.',                   'color':ORANGE,   'icon':'rapid'},
    {'id':'bullet_dmg',      'name':'탄환 대미지 +1',  'desc':'탄환 1발의 대미지가\n1 증가합니다.',                 'color':RED,      'icon':'damage'},
]

augment_choices     = []
augment_hover       = -1


def pick_augment_choices():
    global augment_choices
    augment_choices = random.sample(AUGMENT_POOL, 3)

def apply_augment(aug_id):
    global player_max_hp, player_hp, player_speed
    global bullet_speed, bullet_straight, bullet_spread, AUTO_FIRE_INTERVAL
    global bullet_radius, bullet_damage
    if aug_id == 'max_hp':
        player_max_hp += 1
        player_hp = min(player_hp + 1, player_max_hp)
    elif aug_id == 'bullet_spd':
        bullet_speed    = min(bullet_speed  + 2, 20)
        bullet_radius   = min(bullet_radius + 1, 10)
        _bullet_surf_cache.clear()
    elif aug_id == 'bullet_straight':
        bullet_straight = min(bullet_straight + 1, 3)
    elif aug_id == 'bullet_spread':
        bullet_spread   = min(bullet_spread   + 1, 3)
    elif aug_id == 'move_spd':
        player_speed    = min(player_speed    + 1, 12)
    elif aug_id == 'fire_rate':
        AUTO_FIRE_INTERVAL = max(AUTO_FIRE_INTERVAL - 2, 4)
    elif aug_id == 'bullet_dmg':
        bullet_damage += 1

def _finish_augment(aug_id):
    global wave_state
    apply_augment(aug_id)
    start_wave(current_wave + 1)

CARD_W, CARD_H = 142, 215
CARD_GAP       = 7
CARDS_TOP      = 220
CARDS_TOTAL_W  = 3 * CARD_W + 2 * CARD_GAP
CARDS_LEFT     = (SCREEN_WIDTH - CARDS_TOTAL_W) // 2

def card_rect(i):
    x = CARDS_LEFT + i * (CARD_W + CARD_GAP)
    return pygame.Rect(x, CARDS_TOP, CARD_W, CARD_H)

# ════════════════════════════════════════════════════════════════════════════
#  그리기 헬퍼
# ════════════════════════════════════════════════════════════════════════════

def draw_text_outlined(surface, text, font_, color, x, y, outline_col=(0,0,0)):
    s = font_.render(text, True, outline_col)
    for ox, oy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
        surface.blit(s, (x+ox, y+oy))
    s = font_.render(text, True, color)
    surface.blit(s, (x, y))

def draw_glow_circle(surface, color, pos, radius, glow_radius=8, alpha=60):
    glow_surf = pygame.Surface((glow_radius*2+radius*2, glow_radius*2+radius*2), pygame.SRCALPHA)
    for r in range(glow_radius, 0, -1):
        a = int(alpha * (1 - r / glow_radius))
        pygame.draw.circle(glow_surf, color+(a,), (glow_radius+radius, glow_radius+radius), radius+r)
    surface.blit(glow_surf, (pos[0]-glow_radius-radius, pos[1]-glow_radius-radius))
    pygame.draw.circle(surface, color, pos, radius)

def draw_hp_bar(surface, x, y, w, hp, max_hp):
    bh = 5
    ratio = hp / max_hp if max_hp else 0
    pygame.draw.rect(surface, (30, 30, 30), (x, y, w, bh), border_radius=2)
    if ratio > 0:
        fill_w = max(2, int(w * ratio))
        col = HP_FULL if ratio > 0.6 else (HP_MID if ratio > 0.3 else HP_LOW)
        pygame.draw.rect(surface, col, (x, y, fill_w, bh), border_radius=2)
    pygame.draw.rect(surface, (80, 80, 80), (x, y, w, bh), 1, border_radius=2)

def spawn_particles(x, y, color, count=15, speed_range=(1, 5), life_range=(10, 25)):
    for _ in range(count):
        angle = random.uniform(0, 2*math.pi)
        spd   = random.uniform(*speed_range)
        life  = random.randint(*life_range)
        particles.append({
            'x': x, 'y': y,
            'dx': spd*math.cos(angle), 'dy': spd*math.sin(angle),
            'life': life, 'max_life': life, 'color': color,
            'size': random.uniform(1.5, 4.0),
        })

def spawn_explosion(x, y, color, count=25):
    spawn_particles(x, y, color, count // 2, (2, 6), (15, 30))
    spawn_particles(x, y, WHITE, count // 3, (1, 4), (8, 18))
    for _ in range(count // 5):
        angle = random.uniform(0, 2*math.pi)
        spd   = random.uniform(0.5, 2.5)
        life  = random.randint(20, 40)
        particles.append({
            'x': x, 'y': y,
            'dx': spd*math.cos(angle), 'dy': spd*math.sin(angle),
            'life': life, 'max_life': life, 'color': color,
            'size': random.uniform(3.0, 7.0),
        })

def spawn_popup(text, x, y, color=GOLD):
    popups.append({'text': text, 'x': x, 'y': y, 'life': 60, 'max_life': 60, 'color': color})

def spawn_split_enemies(cx, cy):
    for side in (-1, 1):
        angle = math.radians(35)
        dx = side * enemy_speed * math.sin(angle)
        dy =        enemy_speed * math.cos(angle)
        sx = cx - SPLIT_WIDTH  // 2
        sy = cy - SPLIT_HEIGHT // 2
        enemies.append([sx, sy, 5, 1, sx, dx, dy])

def fire_bullets():
    cx = player_x + player_width // 2
    cy = player_y
    offset_step = 10
    total_w = (bullet_straight - 1) * offset_step
    for i in range(bullet_straight):
        ox = -total_w // 2 + i * offset_step
        bullets.append([cx + ox, cy, 0, -bullet_speed])
    for pair in range(bullet_spread):
        angle = math.radians(15 + pair * 15)
        dx = bullet_speed * math.sin(angle)
        dy = -bullet_speed * math.cos(angle)
        bullets.append([cx, cy,  dx, dy])
        bullets.append([cx, cy, -dx, dy])

def get_wave_enemy_table(wave):
    if wave <= 1:
        return [(0,1,100)]
    elif wave == 2:
        return [(0,1,60),(3,1,40)]
    elif wave == 3:
        return [(0,1,40),(1,1,30),(3,1,30)]
    elif wave == 4:
        return [(0,1,25),(1,1,25),(3,1,25),(4,2,25)]
    else:
        w = min(wave, 10)
        extra = min(w - 4, 6) * 2
        return [(0,1,max(5,15-extra)),(1,1,20),(3,1,20),(4,2,25+extra//2),(2,3,20+extra//2)]

def hp_multiplier(wave):
    """웨이브에 따른 적 HP 배율. 5웨이브마다 1씩 증가 (AI기말branch.py)."""
    return 1 + (wave - 1) // 5

def spawn_wave_enemy(wave):
    table   = get_wave_enemy_table(wave)
    types   = [t[0] for t in table]
    hps     = [t[1] for t in table]
    weights = [t[2] for t in table]
    idx     = random.choices(range(len(types)), weights=weights)[0]
    etype, ehp = types[idx], hps[idx]
    ehp = ehp * hp_multiplier(wave)   # AI기말branch.py: 웨이브 배율 적용
    ex = random.randint(0, SCREEN_WIDTH - enemy_width)
    ey = -enemy_height
    enemies.append([ex, ey, etype, ehp, ex])

def start_wave(wave_num):
    global current_wave, wave_kills, wave_enemy_spawned
    global wave_spawn_total, wave_spawn_interval, enemy_spawn_counter
    global boss_active, boss_hp, boss_spawned_count, boss_max_hp
    global boss_x, boss_y, boss_direction, boss_shoot_counter
    global laser_state, laser_state_timer, laser_spawn_counter
    global laser_damaged_player, wave_state, wave_kill_goal
    global boss_laser_state, boss_laser_timer, boss_laser_counter
    global boss_laser_xs, boss_laser_damaged_player, item_spawn_counter

    current_wave        = wave_num
    wave_kills          = 0
    wave_enemy_spawned  = 0
    enemy_spawn_counter = 0
    item_spawn_counter  = 0
    enemies.clear()
    enemy_bullets.clear()
    items.clear()
    clown_balls.clear()
    spawn_rings.clear()

    if wave_num % BOSS_WAVE_INTERVAL == 0:
        wave_state         = 'boss'
        boss_active        = True
        boss_spawned_count += 1
        boss_max_hp        = 20 + (wave_num // BOSS_WAVE_INTERVAL - 1) * 10
        boss_hp            = boss_max_hp
        boss_x             = SCREEN_WIDTH//2 - boss_width//2
        boss_y             = 50
        boss_direction     = 1
        boss_shoot_counter = 0
        wave_kill_goal     = 1
        wave_spawn_total   = 0
    else:
        wave_state          = 'playing'
        boss_active         = False
        wave_kill_goal      = 15 + wave_num * 5
        wave_spawn_total    = wave_kill_goal + 15
        wave_spawn_interval = max(15, 30 - wave_num)

        # ── 보스 직전 웨이브: 적 전투기만 출현, 일반 적 스폰 없음 ──────────
        if wave_num % BOSS_WAVE_INTERVAL == BOSS_WAVE_INTERVAL - 1:
            n_jets = wave_num // BOSS_WAVE_INTERVAL + 1
            for j in range(n_jets):
                spacing = SCREEN_WIDTH // (n_jets + 1)
                jx = float(spacing * (j + 1) - enemy_width // 2)
                jy = 68.0
                phase = j * (2 * math.pi / max(n_jets, 1))
                ehp_j = 6 * hp_multiplier(wave_num)
                enemies.append([jx, jy, 6, ehp_j, phase, random.randint(60, 240)])
                spawn_rings.append({'x': jx + enemy_width//2, 'y': jy + enemy_height//2,
                                    'max_r': 60, 'life': 50, 'max_life': 50})
            wave_kill_goal   = n_jets
            wave_spawn_total = 0   # 일반 적 스폰 차단

    laser_state               = 0
    laser_state_timer         = 0
    laser_spawn_counter       = 0
    laser_damaged_player      = False
    boss_laser_state          = 0
    boss_laser_timer          = 0
    boss_laser_counter        = 0
    boss_laser_xs             = []
    boss_laser_damaged_player = False

def reset_game():
    global player_x, player_y, player_hp, player_max_hp
    global player_speed, bullet_speed, bullet_radius, bullet_straight, bullet_spread
    global AUTO_FIRE_INTERVAL, auto_fire_counter, bullet_damage
    global score, game_over, wave_clear_timer, boss_spawned_count
    global damage_flash_timer, invincible_timer, item_spawn_counter
    global _go_sound_played, _bgm_duck_timer

    player_x          = SCREEN_WIDTH//2 - player_width//2
    player_y          = SCREEN_HEIGHT   - player_height - 20
    player_max_hp     = 3
    player_hp         = player_max_hp
    player_speed      = 5
    bullet_speed      = 7
    bullet_radius     = 5
    bullet_straight   = 1
    bullet_spread     = 0
    bullet_damage     = 1
    AUTO_FIRE_INTERVAL= 24
    auto_fire_counter = 0

    score              = 0
    game_over          = False
    wave_clear_timer   = 0
    boss_spawned_count = 0
    damage_flash_timer = 0
    invincible_timer   = 0
    item_spawn_counter = 0

    bullets.clear()
    particles.clear()
    popups.clear()
    clown_balls.clear()
    spawn_rings.clear()
    _bullet_surf_cache.clear()

    _go_sound_played        = False
    _bgm_duck_timer         = 0

    # 게임 시작 전 증강 선택 (AI기말branch.py)
    global current_wave, wave_state
    current_wave = 0
    wave_state   = 'augment'
    pick_augment_choices()
    sounds['bgm'].set_volume(BGM_FULL_VOL)
    sounds['bgm'].play(-1)

# ── 최초 웨이브: 증강 선택부터 시작 (AI기말branch.py) ──────────────────
wave_kill_goal      = 20
wave_spawn_total    = 25
wave_spawn_interval = 30
current_wave = 0
wave_state   = 'augment'
pick_augment_choices()

# ── 사운드 (game.py) ──────────────────────────────────────────────────────
sounds = init_sounds()
sounds['bgm'].play(-1)
_go_sound_played  = False
BGM_FULL_VOL      = 0.35
_bgm_duck_timer   = 0

# ════════════════════════════════════════════════════════════════════════════
#  배경 그리기 (space_shooter.py)
# ════════════════════════════════════════════════════════════════════════════

def draw_background():
    global _nebula_y_offset
    screen.blit(_bg_base, (0, 0))
    _nebula_y_offset += 0.08
    if _nebula_y_offset >= SCREEN_HEIGHT:
        _nebula_y_offset -= SCREEN_HEIGHT
    oy = int(_nebula_y_offset)
    screen.blit(_nebula_surf, (0, -SCREEN_HEIGHT + oy))
    if oy < SCREEN_HEIGHT:
        screen.blit(_nebula_surf, (0, oy))
    for star in stars:
        star[1] += star[3]
        if star[1] > SCREEN_HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, SCREEN_WIDTH)
        brightness = int(180 + 60 * math.sin(pygame.time.get_ticks() * 0.001 + star[0]))
        base = star[4]
        col = (min(255, base[0] + brightness // 6),
               min(255, base[1] + brightness // 6),
               min(255, base[2] + brightness // 4))
        pygame.draw.circle(screen, col, (star[0], int(star[1])), star[2])

# ════════════════════════════════════════════════════════════════════════════
#  HUD (space_shooter.py)
# ════════════════════════════════════════════════════════════════════════════

def draw_hud():
    hud_height = 70
    hud_surf = pygame.Surface((SCREEN_WIDTH, hud_height), pygame.SRCALPHA)
    hud_surf.fill((5, 8, 25, 210))
    screen.blit(hud_surf, (0, 0))
    pygame.draw.line(screen, HUD_BORDER, (0, hud_height), (SCREEN_WIDTH, hud_height), 1)

    # BEST SCORE (상단 작은 행)
    best_label = hp_font.render("BEST", True, (80, 110, 160))
    best_val   = hp_font.render(f"{best_score:,}", True, (150, 175, 215))
    screen.blit(best_label, (12, 4))
    screen.blit(best_val,   (12 + best_label.get_width() + 5, 4))

    # 구분선
    pygame.draw.line(screen, (25, 35, 70), (12, 19), (120, 19), 1)

    # SCORE (하단 큰 행)
    score_label = small_font.render("SCORE", True, (120, 150, 200))
    score_val   = font.render(f"{score:,}", True, SCORE_COL)
    screen.blit(score_label, (12, 22))
    screen.blit(score_val,   (12, 38))

    # WAVE (중앙)
    wave_label_text = f"WAVE  {current_wave}"
    if wave_state == 'boss':
        wave_label_text = f"WAVE  {current_wave}  ★BOSS★"
    wt = font.render(wave_label_text, True, WAVE_GOLD)
    screen.blit(wt, (SCREEN_WIDTH//2 - wt.get_width()//2, 10))
    if wave_state == 'playing':
        bar_w = 90
        bar_x = SCREEN_WIDTH//2 - bar_w//2
        bar_y = 50
        ratio  = min(1.0, wave_kills / wave_kill_goal) if wave_kill_goal else 0
        pygame.draw.rect(screen, (30, 30, 50), (bar_x, bar_y, bar_w, 7), border_radius=3)
        if ratio > 0:
            fill_col = (80 + int(175 * ratio), 200 - int(100 * ratio), 80)
            pygame.draw.rect(screen, fill_col, (bar_x, bar_y, int(bar_w * ratio), 7), border_radius=3)
        pygame.draw.rect(screen, (80, 80, 120), (bar_x, bar_y, bar_w, 7), 1, border_radius=3)
        kill_t = hp_font.render(f"{wave_kills}/{wave_kill_goal}", True, (180, 180, 220))
        screen.blit(kill_t, (bar_x + bar_w + 5, bar_y))

    # HP (우측)
    hp_label = small_font.render("HP", True, (120, 150, 200))
    screen.blit(hp_label, (SCREEN_WIDTH - 105, 4))
    for i in range(player_max_hp):
        bx = SCREEN_WIDTH - 100 + i * 28
        by = 22
        bw, bh = 22, 16
        col = HP_FULL if i < player_hp else (30, 40, 30)
        pygame.draw.rect(screen, (20, 30, 20), (bx, by, bw, bh), border_radius=3)
        if i < player_hp:
            pygame.draw.rect(screen, col, (bx+1, by+1, bw-2, bh-2), border_radius=2)
        pygame.draw.rect(screen, (60, 100, 60) if i < player_hp else (50, 60, 50),
                         (bx, by, bw, bh), 1, border_radius=3)

    if wave_state == 'boss' and boss_active:
        bbar_w = 300
        bbar_h = 16
        bbar_x = SCREEN_WIDTH//2 - bbar_w//2
        bbar_y = SCREEN_HEIGHT - 50
        ratio   = boss_hp / boss_max_hp if boss_max_hp else 0
        panel = pygame.Surface((bbar_w + 30, 40), pygame.SRCALPHA)
        panel.fill((10, 5, 20, 200))
        screen.blit(panel, (bbar_x - 15, bbar_y - 14))
        bl = small_font.render("BOSS", True, (200, 100, 255))
        screen.blit(bl, (bbar_x, bbar_y - 14))
        pygame.draw.rect(screen, (30, 10, 50), (bbar_x, bbar_y, bbar_w, bbar_h), border_radius=4)
        if ratio > 0:
            fill_w = max(2, int(bbar_w * ratio))
            r = int(180 + 75 * (1 - ratio))
            g = int(50 * ratio)
            b = int(200 * ratio + 100 * (1 - ratio))
            pygame.draw.rect(screen, (r, g, b), (bbar_x, bbar_y, fill_w, bbar_h), border_radius=4)
        pygame.draw.rect(screen, (150, 50, 200), (bbar_x, bbar_y, bbar_w, bbar_h), 1, border_radius=4)
        hp_txt = small_font.render(f"{boss_hp} / {boss_max_hp}", True, (220, 180, 255))
        screen.blit(hp_txt, (bbar_x + bbar_w//2 - hp_txt.get_width()//2, bbar_y + 18))

# ════════════════════════════════════════════════════════════════════════════
#  메인 메뉴 (space_shooter.py)
# ════════════════════════════════════════════════════════════════════════════

def draw_main_menu(tick):
    draw_background()
    pulse = 0.5 + 0.5 * math.sin(tick * 0.04)
    title_big  = big_font.render("SPACE",   True, PLAYER_CORE)
    title_big2 = big_font.render("SHOOTER", True, WAVE_GOLD)
    draw_text_outlined(screen, "SPACE",   big_font, PLAYER_CORE,
                       SCREEN_WIDTH//2 - title_big.get_width()//2,  SCREEN_HEIGHT//2 - 200, (0,20,80))
    draw_text_outlined(screen, "SHOOTER", big_font, WAVE_GOLD,
                       SCREEN_WIDTH//2 - title_big2.get_width()//2, SCREEN_HEIGHT//2 - 155, (60,40,0))
    pygame.draw.line(screen, PLAYER_CORE,
                     (SCREEN_WIDTH//4, SCREEN_HEIGHT//2 - 110),
                     (SCREEN_WIDTH*3//4, SCREEN_HEIGHT//2 - 110), 1)
    scaled = pygame.transform.scale(PLAYER_SPRITE, (60, 60))
    screen.blit(scaled, (SCREEN_WIDTH//2 - 30, SCREEN_HEIGHT//2 - 95))
    controls = [("← → ↑ ↓", "이동"), ("자동 발사", "연속 사격"), ("R", "재시작")]
    cy = SCREEN_HEIGHT//2 - 20
    for key, desc in controls:
        key_s  = small_font.render(key, True, YELLOW)
        desc_s = small_font.render(f"  {desc}", True, (180, 190, 210))
        total_w = key_s.get_width() + desc_s.get_width()
        screen.blit(key_s,  (SCREEN_WIDTH//2 - total_w//2, cy))
        screen.blit(desc_s, (SCREEN_WIDTH//2 - total_w//2 + key_s.get_width(), cy))
        cy += 26
    if (tick // 35) % 2 == 0:
        pt = font.render("PRESS ANY KEY", True, WHITE)
        screen.blit(pt, (SCREEN_WIDTH//2 - pt.get_width()//2, SCREEN_HEIGHT//2 + 100))
    ver = small_font.render("v3.0  Final Edition", True, (60, 70, 90))
    screen.blit(ver, (SCREEN_WIDTH//2 - ver.get_width()//2, SCREEN_HEIGHT - 30))

# ════════════════════════════════════════════════════════════════════════════
#  게임오버 화면 (space_shooter.py)
# ════════════════════════════════════════════════════════════════════════════

def draw_game_over(tick):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))
    shake = int(3 * math.sin(tick * 0.15)) if tick < 60 else 0
    draw_text_outlined(screen, "GAME OVER", big_font, (255, 60, 60),
                       SCREEN_WIDTH//2 - big_font.size("GAME OVER")[0]//2 + shake,
                       SCREEN_HEIGHT//2 - 100, (80, 0, 0))
    pygame.draw.line(screen, (180, 40, 40),
                     (SCREEN_WIDTH//5, SCREEN_HEIGHT//2 - 40),
                     (SCREEN_WIDTH*4//5, SCREEN_HEIGHT//2 - 40), 1)
    panel = pygame.Surface((260, 90), pygame.SRCALPHA)
    panel.fill((10, 5, 20, 200))
    screen.blit(panel, (SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 - 30))
    pygame.draw.rect(screen, (60, 20, 80),
                     (SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 - 30, 260, 90), 1, border_radius=4)
    is_new_best = (score >= best_score and score > 0)
    st  = font.render(f"SCORE  {score:,}", True, WAVE_GOLD)
    wt2 = font.render(f"WAVE   {current_wave}", True, SCORE_COL)
    bst = small_font.render(
        f"BEST  {best_score:,}{'  ★NEW BEST!★' if is_new_best else ''}",
        True, (255, 215, 0) if is_new_best else (130, 155, 195))
    screen.blit(st,  (SCREEN_WIDTH//2 - st.get_width()//2,  SCREEN_HEIGHT//2 - 28))
    screen.blit(wt2, (SCREEN_WIDTH//2 - wt2.get_width()//2, SCREEN_HEIGHT//2 + 7))
    screen.blit(bst, (SCREEN_WIDTH//2 - bst.get_width()//2, SCREEN_HEIGHT//2 + 42))
    if (tick // 30) % 2 == 0:
        rt = font.render("[ R ]  RESTART", True, WHITE)
        screen.blit(rt, (SCREEN_WIDTH//2 - rt.get_width()//2, SCREEN_HEIGHT//2 + 75))

# ════════════════════════════════════════════════════════════════════════════
#  증강 선택 화면 (space_shooter.py 디자인 + AI기말branch.py 키보드 단축키)
# ════════════════════════════════════════════════════════════════════════════

def draw_augment_screen(tick):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))
    banner = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
    banner.fill((10, 15, 50, 220))
    screen.blit(banner, (0, 110))
    pygame.draw.line(screen, HUD_BORDER, (0, 110), (SCREEN_WIDTH, 110), 1)
    pygame.draw.line(screen, HUD_BORDER, (0, 190), (SCREEN_WIDTH, 190), 1)
    pulse = 0.5 + 0.5 * math.sin(tick * 0.05)
    gold_pulse = (int(220 + 35*pulse), int(190 + 25*pulse), int(50 + 10*pulse))
    draw_text_outlined(screen, "증강 선택", big_font, gold_pulse,
                       SCREEN_WIDTH//2 - big_font.size("증강 선택")[0]//2, 120, (60, 40, 0))
    sub_text = "하나를 선택해 플레이어를 강화하세요"
    sub = small_font.render(sub_text, True, (160, 180, 220))
    screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 168))

    for i, aug in enumerate(augment_choices):
        cr      = card_rect(i)
        hovered = (i == augment_hover)
        cy_offset = -5 if hovered else 0
        cr_draw = cr.move(0, cy_offset)

        bg_col = (55, 55, 80) if hovered else (35, 35, 55)
        pygame.draw.rect(screen, bg_col, cr_draw, border_radius=10)
        if hovered:
            for bw in range(4, 0, -1):
                a = int(60 * (1 - bw / 4))
                bc = aug['color']
                bs = pygame.Surface((CARD_W + bw*2, CARD_H + bw*2), pygame.SRCALPHA)
                pygame.draw.rect(bs, bc+(a,), (0, 0, CARD_W+bw*2, CARD_H+bw*2), border_radius=12+bw, width=1)
                screen.blit(bs, (cr_draw.x - bw, cr_draw.y - bw))
        border_w = 3 if hovered else 2
        pygame.draw.rect(screen, aug['color'], cr_draw, border_w, border_radius=10)

        icon_h = 55
        for row in range(icon_h):
            bc = aug['color']
            r = min(255, int(bc[0] * (1 - row/icon_h*0.4)))
            g = min(255, int(bc[1] * (1 - row/icon_h*0.4)))
            b = min(255, int(bc[2] * (1 - row/icon_h*0.4)))
            pygame.draw.line(screen, (r,g,b),
                             (cr_draw.x+2, cr_draw.y+2+row),
                             (cr_draw.x+CARD_W-2, cr_draw.y+2+row))

        icx, icy = cr_draw.centerx, cr_draw.y + 28
        ic = aug['icon']
        if ic == 'heart':
            pygame.draw.circle(screen, WHITE, (icx-8, icy-4), 10)
            pygame.draw.circle(screen, WHITE, (icx+8, icy-4), 10)
            pygame.draw.polygon(screen, WHITE, [(icx-18, icy), (icx, icy+16), (icx+18, icy)])
        elif ic == 'bullet':
            pygame.draw.circle(screen, WHITE, (icx, icy-6), 7)
            pygame.draw.rect(screen, WHITE, (icx-5, icy-6, 10, 18))
        elif ic == 'straight':
            for ox in (-8, 0, 8):
                pygame.draw.line(screen, WHITE, (icx+ox, icy+10), (icx+ox, icy-12), 3)
                pygame.draw.polygon(screen, WHITE, [(icx+ox, icy-16),(icx+ox-4, icy-8),(icx+ox+4, icy-8)])
        elif ic == 'spread':
            for ang in (-35, 35):
                a = math.radians(ang - 90)
                pygame.draw.line(screen, WHITE, (icx, icy),
                                 (icx+int(20*math.cos(a)), icy+int(20*math.sin(a))), 3)
        elif ic == 'arrow':
            pygame.draw.polygon(screen, WHITE,
                [(icx,icy-14),(icx-10,icy+4),(icx-4,icy+4),(icx-4,icy+14),
                 (icx+4,icy+14),(icx+4,icy+4),(icx+10,icy+4)])
        elif ic == 'rapid':
            for k in range(3):
                pygame.draw.line(screen, WHITE, (icx-12+k*12, icy+8), (icx-8+k*12, icy-8), 3)
        elif ic == 'damage':
            for k in range(5):
                a_out = math.radians(k*72 - 90)
                a_in  = math.radians(k*72 - 90 + 36)
                ox2 = icx + int(14*math.cos(a_out))
                oy2 = icy + int(14*math.sin(a_out))
                ix2 = icx + int(6*math.cos(a_in))
                iy2 = icy + int(6*math.sin(a_in))
                pygame.draw.line(screen, WHITE, (ox2,oy2), (ix2,iy2), 2)
                next_a = math.radians((k+1)*72 - 90)
                nx = icx + int(14*math.cos(next_a))
                ny = icy + int(14*math.sin(next_a))
                pygame.draw.line(screen, WHITE, (ix2,iy2), (nx,ny), 2)

        nt = aug_title_font.render(aug['name'], True, WHITE)
        if nt.get_width() > CARD_W - 8:
            scale = (CARD_W - 8) / nt.get_width()
            nt = pygame.transform.smoothscale(nt, (int(nt.get_width()*scale), int(nt.get_height()*scale)))
        screen.blit(nt, (cr_draw.centerx - nt.get_width()//2, cr_draw.y + 62))

        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(cr_draw.x+4, cr_draw.y+82, CARD_W-8, CARD_H-120))
        for li, line in enumerate(aug['desc'].split('\n')):
            dt = aug_desc_font.render(line, True, (190, 195, 215))
            if dt.get_width() > CARD_W - 8:
                scale = (CARD_W - 8) / dt.get_width()
                dt = pygame.transform.smoothscale(dt, (int(dt.get_width()*scale), int(dt.get_height()*scale)))
            screen.blit(dt, (cr_draw.centerx - dt.get_width()//2, cr_draw.y + 83 + li*19))
        screen.set_clip(prev_clip)

        btn = pygame.Rect(cr_draw.x+15, cr_draw.y+cr_draw.h-35, CARD_W-30, 25)
        if hovered:
            pygame.draw.rect(screen, aug['color'], btn, border_radius=5)
            bt = small_font.render("선택 ▶", True, BLACK)
        else:
            pygame.draw.rect(screen, (60, 60, 80), btn, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 130), btn, 1, border_radius=5)
            bt = small_font.render(f"[{i+1}] 선택", True, (160, 160, 180))
        screen.blit(bt, (btn.centerx - bt.get_width()//2, btn.centery - bt.get_height()//2))

# ════════════════════════════════════════════════════════════════════════════
#  Wave Clear 연출 (space_shooter.py)
# ════════════════════════════════════════════════════════════════════════════

def draw_wave_clear(timer, wave_num):
    banner = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
    banner.fill((0, 0, 0, min(200, timer * 4)))
    screen.blit(banner, (0, SCREEN_HEIGHT//2 - 55))
    pulse = 0.5 + 0.5 * math.sin(timer * 0.15)
    gold_p = (int(240 + 15*pulse), int(200 + 15*pulse), int(50 + 10*pulse))
    draw_text_outlined(screen, f"WAVE  {wave_num}  CLEAR!", big_font, gold_p,
                       SCREEN_WIDTH//2 - big_font.size(f"WAVE  {wave_num}  CLEAR!")[0]//2,
                       SCREEN_HEIGHT//2 - 45, (60, 40, 0))
    if timer % 8 == 0 and timer < 80:
        for _ in range(3):
            cx2 = random.randint(SCREEN_WIDTH//5, SCREEN_WIDTH*4//5)
            cy2 = random.randint(SCREEN_HEIGHT//4, SCREEN_HEIGHT*3//4)
            col = random.choice([WAVE_GOLD, PLAYER_CORE, HOT_PINK, GREEN])
            spawn_explosion(cx2, cy2, col, 12)

# ════════════════════════════════════════════════════════════════════════════
#  메인 루프
# ════════════════════════════════════════════════════════════════════════════
main_menu      = True
main_menu_tick = 0
game_over_tick = 0
running        = True
global_tick    = 0

while running:
    clock.tick(FPS)
    global_tick += 1

    # ── 이벤트 ──────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if main_menu:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                main_menu = False
                reset_game()
                break
            continue

        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                reset_game()
                game_over_tick = 0
            if not game_over and event.key == pygame.K_n and wave_state in ('playing', 'boss'):
                enemies.clear()
                clown_balls.clear()
                wave_kills = wave_kill_goal
                wave_state = 'wave_clear'
            # 증강 선택 키보드 단축키 (AI기말branch.py)
            if wave_state == 'augment':
                if event.key == pygame.K_1 and len(augment_choices) > 0:
                    _finish_augment(augment_choices[0]['id'])
                elif event.key == pygame.K_2 and len(augment_choices) > 1:
                    _finish_augment(augment_choices[1]['id'])
                elif event.key == pygame.K_3 and len(augment_choices) > 2:
                    _finish_augment(augment_choices[2]['id'])

        if wave_state == 'augment' and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i in range(3):
                if card_rect(i).collidepoint(mx, my):
                    _finish_augment(augment_choices[i]['id'])
                    break

        if wave_state == 'augment' and event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            augment_hover = -1
            for i in range(3):
                cr = card_rect(i)
                hover_cr = cr.move(0, -5)
                if hover_cr.collidepoint(mx, my) or cr.collidepoint(mx, my):
                    augment_hover = i
                    break

    if not running:
        break

    # ── 메인 메뉴 ────────────────────────────────────────────────────────────
    if main_menu:
        main_menu_tick += 1
        draw_main_menu(main_menu_tick)
        pygame.display.flip()
        continue

    # ── 엔진 불꽃 / 게임오버 카운터 ──────────────────────────────────────
    thruster_frame = (global_tick // 4) % 8
    if game_over:
        game_over_tick += 1

    # ── 베스트 스코어 갱신 ───────────────────────────────────────────────
    if score > best_score:
        best_score = score
        _save_best_score(best_score)

    # ── BGM 덕킹 복구 ─────────────────────────────────────────────────────
    if _bgm_duck_timer > 0:
        _bgm_duck_timer -= 1
        if _bgm_duck_timer == 0:
            sounds['bgm'].set_volume(BGM_FULL_VOL)

    # ════════════════════════════════════════════════════════════════════════
    #  게임 로직
    # ════════════════════════════════════════════════════════════════════════
    if not game_over and wave_state in ('playing', 'boss'):

        enemy_bullet_speed  = 4 + current_wave * 0.3
        enemy_bullet_radius = 4

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and player_x > 0:                         player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH-player_width:  player_x += player_speed
        if keys[pygame.K_UP]    and player_y > 0:                          player_y -= player_speed
        if keys[pygame.K_DOWN]  and player_y < SCREEN_HEIGHT-player_height: player_y += player_speed

        auto_fire_counter += 1
        if auto_fire_counter >= AUTO_FIRE_INTERVAL:
            auto_fire_counter = 0
            fire_bullets()
            sounds['shoot'].play()

        if invincible_timer > 0:
            invincible_timer -= 1
        if damage_flash_timer > 0:
            damage_flash_timer -= 1

        for p in particles[:]:
            p['x'] += p['dx']; p['y'] += p['dy']; p['life'] -= 1
            if p['life'] <= 0: particles.remove(p)

        for pop in popups[:]:
            pop['y']   -= 0.8
            pop['life'] -= 1
            if pop['life'] <= 0: popups.remove(pop)

        # ── 레이저 ──────────────────────────────────────────────────────
        if laser_state == 0:
            laser_spawn_counter += 1
            if laser_spawn_counter >= 450:
                laser_state = 1; laser_state_timer = 0
                laser_x = random.randint(50, SCREEN_WIDTH-50)
                laser_y = random.randint(150, SCREEN_HEIGHT-120)
                laser_damaged_player = False; laser_spawn_counter = 0
                sounds['laser_warning'].play()
        elif laser_state == 1:
            laser_state_timer += 1
            if laser_state_timer >= 90:
                laser_state = 2; laser_state_timer = 0
                sounds['laser_warning'].stop()
                sounds['laser_fire'].play()
        elif laser_state == 2:
            laser_state_timer += 1
            if not laser_damaged_player and invincible_timer == 0:
                pr = pygame.Rect(player_x, player_y, player_width, player_height)
                lh = pygame.Rect(0, laser_y-laser_height//2, SCREEN_WIDTH, laser_height)
                lv = pygame.Rect(laser_x-laser_height//2, 0, laser_height, SCREEN_HEIGHT)
                if pr.colliderect(lh) or pr.colliderect(lv):
                    player_hp -= 1; laser_damaged_player = True
                    damage_flash_timer = 20; invincible_timer = 60
                    spawn_explosion(player_x+player_width//2, player_y+player_height//2, RED, 20)
                    sounds['player_hit'].play()
                    if player_hp <= 0:
                        game_over = True
                        if not _go_sound_played:
                            _go_sound_played = True
                            sounds['bgm'].fadeout(600)
                            sounds['game_over'].play()
            if laser_state_timer >= 30: laser_state = 0; laser_state_timer = 0

        # ── 탄환 이동 ────────────────────────────────────────────────────
        for b in bullets[:]:
            b[0] += b[2]; b[1] += b[3]
            if b[1] < 0 or b[0] < 0 or b[0] > SCREEN_WIDTH: bullets.remove(b)
        for eb in enemy_bullets[:]:
            eb[0] += eb[2]; eb[1] += eb[3]
            if eb[1] > SCREEN_HEIGHT or eb[0] < 0 or eb[0] > SCREEN_WIDTH: enemy_bullets.remove(eb)

        # ── 유도 미사일 이동 + 매연 ──────────────────────────────────────
        TURN_RATE = 0.04
        tx = player_x + player_width  // 2
        ty = player_y + player_height // 2
        for missile in clown_balls[:]:
            dpx = tx - missile[0]; dpy = ty - missile[1]
            dist_p = math.sqrt(dpx*dpx + dpy*dpy)
            if dist_p > 0:
                nx, ny = dpx/dist_p, dpy/dist_p
                spd = math.sqrt(missile[2]**2 + missile[3]**2)
                missile[2] += nx * TURN_RATE * spd
                missile[3] += ny * TURN_RATE * spd
                new_spd = math.sqrt(missile[2]**2 + missile[3]**2)
                if new_spd > 0:
                    missile[2] = missile[2] / new_spd * spd
                    missile[3] = missile[3] / new_spd * spd
            missile[0] += missile[2]; missile[1] += missile[3]
            spd2 = math.sqrt(missile[2]**2 + missile[3]**2)
            if spd2 > 0:
                ex2 = missile[0] - missile[2]/spd2 * 9
                ey2 = missile[1] - missile[3]/spd2 * 9
                ecol = random.choice([(255,120,0),(255,200,50),(210,210,210)])
                particles.append({'x':ex2+random.uniform(-2,2),'y':ey2+random.uniform(-2,2),
                                   'dx':-missile[2]/spd2*0.6+random.uniform(-0.6,0.6),
                                   'dy':-missile[3]/spd2*0.6+random.uniform(-0.6,0.6),
                                   'life':10,'max_life':10,'color':ecol,'size':random.uniform(1.5,3.0)})
            if (missile[0] < -30 or missile[0] > SCREEN_WIDTH+30 or
                    missile[1] < -30 or missile[1] > SCREEN_HEIGHT+30):
                if missile in clown_balls: clown_balls.remove(missile)

        # ── 스폰 링 이펙트 업데이트 ──────────────────────────────────────
        for ring in spawn_rings[:]:
            ring['life'] -= 1
            if ring['life'] <= 0: spawn_rings.remove(ring)

        # ── 보스 웨이브 ──────────────────────────────────────────────────
        if wave_state == 'boss' and boss_active:
            boss_anim_timer += 1
            boss_x += boss_speed * boss_direction
            if boss_x <= 0:                          boss_x = 0;                       boss_direction = 1
            elif boss_x >= SCREEN_WIDTH-boss_width:  boss_x = SCREEN_WIDTH-boss_width; boss_direction = -1
            boss_shoot_counter += 1
            if boss_shoot_counter >= 45:
                enemy_bullets.append([boss_x+boss_width//2, boss_y+boss_height, 0,                       enemy_bullet_speed])
                enemy_bullets.append([boss_x+10,            boss_y+boss_height, -0.3*enemy_bullet_speed, enemy_bullet_speed])
                enemy_bullets.append([boss_x+boss_width-10, boss_y+boss_height,  0.3*enemy_bullet_speed, enemy_bullet_speed])
                boss_shoot_counter = 0

            # ── 보스 수직 레이저 (AI기말branch.py, tier≥2) ───────────────
            boss_tier = current_wave // BOSS_WAVE_INTERVAL
            if boss_tier >= 2:
                if boss_laser_state == 0:
                    boss_laser_counter += 1
                    if boss_laser_counter >= BOSS_LASER_INTERVAL:
                        boss_laser_counter        = 0
                        boss_laser_state          = 1
                        boss_laser_timer          = 0
                        boss_laser_damaged_player = False
                        bcx = boss_x + boss_width // 2
                        boss_laser_xs = [max(8, bcx-120), min(SCREEN_WIDTH-8, bcx+120)]
                elif boss_laser_state == 1:
                    boss_laser_timer += 1
                    if boss_laser_timer >= 90:
                        boss_laser_state = 2; boss_laser_timer = 0
                elif boss_laser_state == 2:
                    boss_laser_timer += 1
                    if not boss_laser_damaged_player and invincible_timer == 0:
                        pr2 = pygame.Rect(player_x, player_y, player_width, player_height)
                        lw  = 16
                        for lx in boss_laser_xs:
                            if pr2.colliderect(pygame.Rect(lx - lw//2, 0, lw, SCREEN_HEIGHT)):
                                player_hp -= 1
                                boss_laser_damaged_player = True
                                damage_flash_timer = 20; invincible_timer = 60
                                spawn_explosion(player_x+player_width//2,
                                                player_y+player_height//2, PURPLE, 20)
                                sounds['player_hit'].play()
                                if player_hp <= 0:
                                    game_over = True
                                    if not _go_sound_played:
                                        _go_sound_played = True
                                        sounds['bgm'].fadeout(600)
                                        sounds['game_over'].play()
                                break
                    if boss_laser_timer >= 30:
                        boss_laser_state = 0; boss_laser_timer = 0

        # ── 일반 웨이브: 적 생성 ─────────────────────────────────────────
        if wave_state == 'playing' and not boss_active:
            enemy_spawn_counter += 1
            if enemy_spawn_counter >= wave_spawn_interval and wave_kills < wave_kill_goal:
                spawn_wave_enemy(current_wave)
                wave_enemy_spawned += 1
                enemy_spawn_counter = 0

        # ── 적 이동 ──────────────────────────────────────────────────────
        for enemy in enemies[:]:
            if enemy[2] == 2:   spd = 2
            elif enemy[2] == 3: spd = 5
            elif enemy[2] == 4: spd = 2
            elif enemy[2] == 6:
                # 사인파 수평 이동 (상단 고정)
                enemy[4] += 0.022   # phase (index 4 재활용)
                amplitude = (SCREEN_WIDTH // 2 - enemy_width - 12)
                enemy[0] = SCREEN_WIDTH // 2 + math.sin(enemy[4]) * amplitude
                enemy[0] = max(0.0, min(enemy[0], float(SCREEN_WIDTH - enemy_width)))
                enemy[1] = 68.0
                # 발사 카운터 (index 5)
                enemy[5] += 1
                if enemy[5] >= 300:
                    enemy[5] = 0
                    cx6 = enemy[0] + enemy_width  // 2
                    cy6 = enemy[1] + enemy_height // 2
                    mspd = enemy_bullet_speed * 1.5
                    # 초기 방향: 플레이어 쪽
                    ddx = (player_x + player_width //2) - cx6
                    ddy = (player_y + player_height//2) - cy6
                    dlen = math.sqrt(ddx*ddx + ddy*ddy) or 1
                    clown_balls.append([cx6, cy6,
                                        ddx/dlen*mspd, ddy/dlen*mspd])
                continue
            elif enemy[2] == 5:
                enemy[0] += enemy[5]; enemy[1] += enemy[6]
                if enemy[1] > SCREEN_HEIGHT or enemy[0] < -SPLIT_WIDTH or enemy[0] > SCREEN_WIDTH+SPLIT_WIDTH:
                    if enemy in enemies: enemies.remove(enemy)
                continue
            else: spd = enemy_speed
            enemy[1] += spd
            if enemy[2] == 3:
                enemy[0] = enemy[4] + math.sin(enemy[1]*0.05)*60
                enemy[0] = max(0, min(enemy[0], SCREEN_WIDTH-enemy_width))
            if enemy[2] == 1 and random.random() < 0.015:
                enemy_bullets.append([enemy[0]+enemy_width//2, enemy[1]+enemy_height, 0, enemy_bullet_speed])
            if enemy[1] > SCREEN_HEIGHT:
                enemies.remove(enemy)

        # ── 아이템 ───────────────────────────────────────────────────────
        if wave_state == 'playing':
            item_spawn_counter += 1
            if item_spawn_counter >= 360:
                ix = random.randint(0, SCREEN_WIDTH-item_width)
                items.append([ix, -item_height, 1])
                item_spawn_counter = 0
        for item in items[:]:
            item[1] += item_speed
            if item[1] > SCREEN_HEIGHT: items.remove(item)

        # ── 충돌: 플레이어 탄환 vs 적 ───────────────────────────────────
        for b in bullets[:]:
            br  = pygame.Rect(b[0]-bullet_radius, b[1]-bullet_radius, bullet_radius*2, bullet_radius*2)
            hit = False
            for enemy in enemies[:]:
                ew = SPLIT_WIDTH  if enemy[2]==5 else enemy_width
                eh = SPLIT_HEIGHT if enemy[2]==5 else enemy_height
                er = pygame.Rect(enemy[0], enemy[1], ew, eh)
                if br.colliderect(er):
                    if b in bullets: bullets.remove(b)
                    enemy[3] -= bullet_damage   # AI기말branch.py: bullet_damage 적용
                    spawn_particles(b[0], b[1], WHITE, 4, (1, 3), (6, 12))
                    if enemy[3] <= 0:
                        if enemy in enemies: enemies.remove(enemy)
                        cx2 = enemy[0] + ew//2
                        cy2 = enemy[1] + eh//2
                        ec  = {0:(160,120,40),1:ORANGE,2:YELLOW,3:CYAN,4:LIME,5:LIME_DARK,6:HOT_PINK}
                        spawn_explosion(cx2, cy2, ec.get(enemy[2], RED), 20)
                        sounds['explode'].play()
                        if enemy[2] == 4:
                            spawn_split_enemies(cx2, cy2); pts = 20
                        elif enemy[2] == 5: pts = 15
                        elif enemy[2] == 2: pts = 50
                        elif enemy[2] == 1: pts = 20
                        elif enemy[2] == 3: pts = 30
                        else:               pts = 10
                        score      += pts
                        wave_kills += 1
                        spawn_popup(f"+{pts}", cx2, cy2, ec.get(enemy[2], WHITE))
                    else:
                        sounds['hit'].play()
                    hit = True; break

            if not hit and wave_state == 'boss' and boss_active:
                bossr = pygame.Rect(boss_x, boss_y, boss_width, boss_height)
                if br.colliderect(bossr):
                    if b in bullets: bullets.remove(b)
                    boss_hp -= 1
                    spawn_particles(b[0], b[1], WHITE, 4, (1, 3), (6, 12))
                    if boss_hp <= 0:
                        boss_active = False
                        pts = 500 + current_wave * 50
                        score += pts
                        spawn_explosion(boss_x+boss_width//2, boss_y+boss_height//2, PURPLE, 50)
                        spawn_explosion(boss_x+boss_width//2, boss_y+boss_height//2, WHITE, 30)
                        spawn_popup(f"+{pts} BOSS!", boss_x+boss_width//2, boss_y, PURPLE)
                        sounds['bgm'].fadeout(800)
                        sounds['boss_explode'].play()
                        wave_kills += 1
                    else:
                        sounds['boss_hit'].play()

        # ── 충돌: 플레이어 vs 적/탄환 ───────────────────────────────────
        pr = pygame.Rect(player_x, player_y, player_width, player_height)
        if invincible_timer == 0:
            for enemy in enemies[:]:
                ew = SPLIT_WIDTH  if enemy[2]==5 else enemy_width
                eh = SPLIT_HEIGHT if enemy[2]==5 else enemy_height
                if pr.colliderect(pygame.Rect(enemy[0], enemy[1], ew, eh)):
                    enemies.remove(enemy)
                    player_hp -= 1
                    damage_flash_timer = 20; invincible_timer = 90
                    spawn_explosion(enemy[0]+ew//2, enemy[1]+eh//2, RED, 20)
                    sounds['player_hit'].play()
                    if player_hp <= 0:
                        game_over = True
                        if not _go_sound_played:
                            _go_sound_played = True
                            sounds['bgm'].fadeout(600)
                            sounds['game_over'].play()

            for eb in enemy_bullets[:]:
                ebr = pygame.Rect(eb[0]-enemy_bullet_radius, eb[1]-enemy_bullet_radius,
                                  enemy_bullet_radius*2, enemy_bullet_radius*2)
                if pr.colliderect(ebr):
                    enemy_bullets.remove(eb); player_hp -= 1
                    damage_flash_timer = 15; invincible_timer = 60
                    spawn_explosion(player_x+player_width//2, player_y+player_height//2, ORANGE, 12)
                    sounds['player_hit'].play()
                    if player_hp <= 0:
                        game_over = True
                        if not _go_sound_played:
                            _go_sound_played = True
                            sounds['bgm'].fadeout(600)
                            sounds['game_over'].play()

            for ball in clown_balls[:]:
                mr = MISSILE_RADIUS
                br2 = pygame.Rect(int(ball[0])-mr, int(ball[1])-mr, mr*2, mr*2)
                if pr.colliderect(br2):
                    if ball in clown_balls: clown_balls.remove(ball)
                    player_hp -= 1
                    damage_flash_timer = 20; invincible_timer = 90
                    spawn_explosion(int(ball[0]), int(ball[1]), HOT_PINK, 20)
                    sounds['player_hit'].play()
                    if player_hp <= 0:
                        game_over = True
                        if not _go_sound_played:
                            _go_sound_played = True
                            sounds['bgm'].fadeout(600)
                            sounds['game_over'].play()
                    break

            if wave_state == 'boss' and boss_active:
                if pr.colliderect(pygame.Rect(boss_x, boss_y, boss_width, boss_height)):
                    player_hp = 0
                    spawn_explosion(player_x+player_width//2, player_y+player_height//2, PURPLE, 30)
                    sounds['player_hit'].play()
                    game_over = True
                    if not _go_sound_played:
                        _go_sound_played = True
                        sounds['bgm'].fadeout(600)
                        sounds['game_over'].play()

        # ── 아이템 획득 ──────────────────────────────────────────────────
        for item in items[:]:
            if pr.colliderect(pygame.Rect(item[0], item[1], item_width, item_height)):
                items.remove(item)
                if player_hp < player_max_hp:
                    player_hp += 1
                    spawn_popup("HP +1", item[0]+item_width//2, item[1], HOT_PINK)
                score += 15
                spawn_explosion(item[0]+item_width//2, item[1]+item_height//2, HOT_PINK, 15)
                sounds['item'].play()

        # ── 웨이브 클리어 판정 ───────────────────────────────────────────
        if not game_over and wave_kills >= wave_kill_goal and len(enemies) == 0 and wave_state in ('playing','boss'):
            wave_state       = 'wave_clear'
            wave_clear_timer = 0
            enemies.clear(); enemy_bullets.clear(); bullets.clear()
            clown_balls.clear(); spawn_rings.clear()
            sounds['bgm'].set_volume(0.08)
            sounds['wave_clear'].play()
            _bgm_duck_timer = 90

    # ── wave_clear 연출 ──────────────────────────────────────────────────
    elif not game_over and wave_state == 'wave_clear':
        for p in particles[:]:
            p['x'] += p['dx']; p['y'] += p['dy']; p['life'] -= 1
            if p['life'] <= 0: particles.remove(p)
        for eff in number_effects[:]:
            eff['life'] -= 1
            if eff['life'] <= 0: number_effects.remove(eff)
        wave_clear_timer += 1
        if wave_clear_timer >= WAVE_CLEAR_SHOW:
            sounds['bgm'].set_volume(BGM_FULL_VOL)
            next_wave = current_wave + 1
            if next_wave % AUGMENT_EVERY == 0 and next_wave % BOSS_WAVE_INTERVAL != 0:
                wave_state = 'augment'
                pick_augment_choices()
            else:
                start_wave(next_wave)

    # ════════════════════════════════════════════════════════════════════════
    #  렌더링
    # ════════════════════════════════════════════════════════════════════════
    draw_background()

    if wave_state in ('playing', 'boss', 'wave_clear'):

        # 플레이어 (무적 중 깜빡임)
        draw_player = (invincible_timer == 0) or (invincible_timer // 4) % 2 == 0
        if draw_player:
            flame = THRUSTER_FRAMES[thruster_frame]
            screen.blit(flame, (player_x + player_width//2 - flame.get_width()//2,
                                 player_y + player_height - 4))
            screen.blit(PLAYER_SPRITE, (player_x, player_y))
            draw_glow_circle(screen, PLAYER_ENGINE,
                             (player_x + player_width//2, player_y + player_height + 2),
                             3, glow_radius=8, alpha=50)

        # 플레이어 탄환
        b_surf = get_bullet_surf(bullet_radius)
        for b in bullets:
            screen.blit(b_surf, (int(b[0]) - b_surf.get_width()//2,
                                  int(b[1]) - b_surf.get_height()//2))

        # 적 탄환
        for eb in enemy_bullets:
            screen.blit(ENEMY_BULLET_SURF,
                        (int(eb[0]) - ENEMY_BULLET_SURF.get_width()//2,
                         int(eb[1]) - ENEMY_BULLET_SURF.get_height()//2))

        # 적
        for enemy in enemies:
            ex, ey = int(enemy[0]), int(enemy[1])
            etype  = enemy[2]
            ew, eh = (SPLIT_WIDTH, SPLIT_HEIGHT) if etype == 5 else (enemy_width, enemy_height)
            spr = ENEMY_SPRITES.get(etype)
            if spr:
                screen.blit(spr, (ex, ey))
            max_hp_map = {0:1,1:1,2:3,3:1,4:2,5:1,6:6}
            ehp_max = max_hp_map.get(etype, 1) * hp_multiplier(current_wave)
            if enemy[3] < ehp_max or ehp_max > 1:
                draw_hp_bar(screen, ex, ey - 8, ew, enemy[3], ehp_max)

        # 보스
        if boss_active:
            pulse_offset = int(3 * math.sin(boss_anim_timer * 0.1))
            screen.blit(BOSS_SPRITE, (int(boss_x), boss_y + pulse_offset))
            pulse_a = int(40 + 40 * math.sin(boss_anim_timer * 0.15))
            draw_glow_circle(screen, (200, 80, 255),
                             (int(boss_x + boss_width//2), boss_y + boss_height//2 + pulse_offset),
                             14, glow_radius=14, alpha=pulse_a)

        # 레이저
        if laser_state == 1:
            tick_ms = pygame.time.get_ticks()
            if (tick_ms // 100) % 2 == 0:
                pygame.draw.line(screen, (255, 50, 50), (0, laser_y), (SCREEN_WIDTH, laser_y), 2)
                pygame.draw.line(screen, (255, 50, 50), (laser_x, 0), (laser_x, SCREEN_HEIGHT), 2)
        elif laser_state == 2:
            for thickness, color, alpha in [(16,(255,30,30),60),(8,(255,100,80),120),(4,(255,200,200),220)]:
                ls = pygame.Surface((SCREEN_WIDTH, thickness), pygame.SRCALPHA)
                ls.fill(color + (alpha,))
                screen.blit(ls, (0, laser_y - thickness//2))
                ls2 = pygame.Surface((thickness, SCREEN_HEIGHT), pygame.SRCALPHA)
                ls2.fill(color + (alpha,))
                screen.blit(ls2, (laser_x - thickness//2, 0))

        # 보스 수직 레이저 (AI기말branch.py)
        if wave_state == 'boss' and boss_laser_xs:
            if boss_laser_state == 1 and (pygame.time.get_ticks()//100)%2==0:
                for blx in boss_laser_xs:
                    pygame.draw.line(screen, PURPLE, (blx, 0), (blx, SCREEN_HEIGHT), 2)
            elif boss_laser_state == 2:
                for blx in boss_laser_xs:
                    pygame.draw.rect(screen, PURPLE, (blx-8, 0, 16, SCREEN_HEIGHT))
                    pygame.draw.rect(screen, WHITE,  (blx-3, 0,  6, SCREEN_HEIGHT))

        # 파티클
        for p in particles:
            ratio = p['life'] / p['max_life']
            r = max(1, int(p['size'] * ratio))
            col = p['color']
            if r >= 1:
                ps = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                a  = int(220 * ratio)
                pygame.draw.circle(ps, col + (a,), (r, r), r)
                screen.blit(ps, (int(p['x'])-r, int(p['y'])-r))

        # 미니보스 등장 링 이펙트
        for ring in spawn_rings:
            ratio = ring['life'] / ring['max_life']  # 1→0
            r = int(ring['max_r'] * (1 - ratio))
            alpha = int(35 * ratio)
            if r > 1 and alpha > 0:
                rs = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(rs, (255,255,255,alpha), (r+2,r+2), r, 2)
                screen.blit(rs, (int(ring['x'])-r-2, int(ring['y'])-r-2))

        # 유도 미사일 (방향에 따라 회전)
        for missile in clown_balls:
            spd_m = math.sqrt(missile[2]**2 + missile[3]**2)
            if spd_m > 0:
                ang = -math.degrees(math.atan2(missile[2], -missile[3]))
                rot_surf = pygame.transform.rotate(MISSILE_SURF, ang)
                screen.blit(rot_surf, (int(missile[0]) - rot_surf.get_width()//2,
                                       int(missile[1]) - rot_surf.get_height()//2))

        # 아이템
        for item in items:
            float_offset = int(3 * math.sin(global_tick * 0.1 + item[0]))
            spr = ITEM_SPRITES.get(item[2])
            if spr:
                screen.blit(spr, (item[0], item[1] + float_offset))
            draw_glow_circle(screen, HOT_PINK,
                             (item[0]+item_width//2, item[1]+item_height//2+float_offset),
                             5, glow_radius=10, alpha=30)

        # 팝업 텍스트
        for pop in popups:
            ratio = pop['life'] / pop['max_life']
            a = int(255 * min(1.0, ratio * 3))
            ps = small_font.render(pop['text'], True, pop['color'])
            ps.set_alpha(a)
            screen.blit(ps, (int(pop['x']) - ps.get_width()//2, int(pop['y'])))

        draw_hud()

        if wave_state == 'wave_clear':
            draw_wave_clear(wave_clear_timer, current_wave)

        # 피격 플래시
        if damage_flash_timer > 0:
            flash_a = int(120 * (damage_flash_timer / 20))
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 0, 0, flash_a))
            screen.blit(flash_surf, (0, 0))

    elif wave_state == 'augment':
        draw_augment_screen(global_tick)

    # 숫자 이펙트 (삐에로 공 6번/7번 튕김) – 화면 전체 오버레이
    if number_effects:
        for eff in number_effects:
            ratio   = 1 - eff['life'] / eff['max_life']   # 0→1
            alpha   = int(200 * (1 - ratio))
            scale_f = 3.0 + ratio * 7.0                   # 3x→10x
            if alpha <= 0:
                continue
            outline_col = (255, 80,  160)
            fill_col    = (255, 190, 220)
            base  = big_font.render(eff['num'], True, fill_col)
            bw, bh = base.get_size()
            sw, sh = max(1, int(bw * scale_f)), max(1, int(bh * scale_f))
            out_s  = big_font.render(eff['num'], True, outline_col)
            out_sc = pygame.transform.scale(out_s, (sw, sh))
            out_sc.set_alpha(alpha)
            cx_n = SCREEN_WIDTH//2 - sw//2
            cy_n = SCREEN_HEIGHT//2 - sh//2
            for ox, oy in [(-5,0),(5,0),(0,-5),(0,5)]:
                screen.blit(out_sc, (cx_n+ox, cy_n+oy))
            fill_sc = pygame.transform.scale(base, (sw, sh))
            fill_sc.set_alpha(alpha)
            screen.blit(fill_sc, (cx_n, cy_n))

    if game_over:
        draw_game_over(game_over_tick)

    pygame.display.flip()

pygame.quit()
sys.exit()
