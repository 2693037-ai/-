import pygame
import random
import sys
import math

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

clock = pygame.time.Clock()
FPS   = 60

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

# ── 플레이어 기본값 (증강으로 변하는 값들은 별도 변수로 관리) ─────────────
player_width  = 40
player_height = 40

# 증강으로 변경 가능한 스탯 (초기값)
player_max_hp      = 3
player_hp          = player_max_hp
player_speed       = 5
bullet_speed       = 7
bullet_radius      = 5
AUTO_FIRE_INTERVAL = 12   # 연사 간격(프레임). 낮을수록 빠름
bullet_straight    = 1    # 직선 탄환 수 (최대 3)
bullet_spread      = 0    # 사선 탄환 쌍 수 (좌우 대칭, 최대 3)

player_x = (SCREEN_WIDTH  // 2) - (player_width  // 2)
player_y = (SCREEN_HEIGHT - player_height - 20)

bullets          = []
enemy_bullets    = []
enemy_bullet_speed  = 5
enemy_bullet_radius = 4

# ── 적 ────────────────────────────────────────────────────────────────────
# 구조: [x, y, type, hp, start_x]  /  type5 소형: [x, y, 5, hp, start_x, dx, dy]
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

# ── 레이저 ────────────────────────────────────────────────────────────────
laser_state        = 0
laser_state_timer  = 0
laser_spawn_counter= 0
laser_x = laser_y  = 0
laser_height       = 16
laser_damaged_player = False

# ── 배경 별 ───────────────────────────────────────────────────────────────
stars = []
for _ in range(50):
    sz  = random.choices([1,1,1,2], weights=[5,5,5,1])[0]
    spd = 0.3 if sz == 1 else 0.7
    cv  = random.randint(40,80) if sz==1 else random.randint(70,120)
    col = (cv, cv, min(255, cv + random.randint(0,20)))
    stars.append([random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), sz, spd, col])

# ── 자동 연사 ─────────────────────────────────────────────────────────────
auto_fire_counter = 0

# ── 게임 상태 ─────────────────────────────────────────────────────────────
score     = 0
game_over = False

# ════════════════════════════════════════════════════════════════════════════
#  웨이브 시스템
# ════════════════════════════════════════════════════════════════════════════
current_wave       = 1
wave_kill_goal     = 20        # 현재 웨이브 처치 목표
wave_kills         = 0         # 현재 웨이브 처치 수
wave_enemy_spawned = 0         # 이번 웨이브에 생성된 적 수
wave_spawn_total   = 25        # 이번 웨이브에 생성할 적 총 수 (kill_goal보다 약간 많게)
enemy_spawn_counter= 0
wave_spawn_interval= 30        # 적 생성 간격(프레임)

# 웨이브 간 상태:  'playing' | 'wave_clear' | 'augment' | 'boss'
wave_state      = 'playing'
wave_clear_timer= 0            # wave_clear 연출 표시 시간(프레임)
WAVE_CLEAR_SHOW = 120          # 2초

# 보스는 5웨이브마다 등장
BOSS_WAVE_INTERVAL = 5
boss_spawned_count = 0

# 증강은 4~5웨이브마다 제공 (boss 웨이브 직전 웨이브는 제외)
AUGMENT_EVERY = 4   # 매 4웨이브마다

# ════════════════════════════════════════════════════════════════════════════
#  증강(Augment) 시스템
# ════════════════════════════════════════════════════════════════════════════
# 6가지 업그레이드 후보 풀
AUGMENT_POOL = [
    {
        'id'   : 'max_hp',
        'name' : '최대 체력 +1',
        'desc' : '최대 HP가 1 증가하고\n현재 HP도 1 회복됩니다.',
        'color': HOT_PINK,
        'icon' : 'heart',
    },
    {
        'id'   : 'bullet_spd',
        'name' : '탄환 속도 +2',
        'desc' : '발사체가 더 빠르게\n날아갑니다.',
        'color': CYAN,
        'icon' : 'bullet',
    },
    {
        'id'   : 'bullet_straight',
        'name' : '직선 탄환 +1',
        'desc' : '정면으로 날아가는\n탄환이 1개 늘어납니다.\n(최대 3발)',
        'color': YELLOW,
        'icon' : 'straight',
    },
    {
        'id'   : 'bullet_spread',
        'name' : '사선 탄환 +1쌍',
        'desc' : '좌우 대각선으로\n탄환 1쌍이 추가됩니다.\n(최대 3쌍)',
        'color': LIME,
        'icon' : 'spread',
    },
    {
        'id'   : 'move_spd',
        'name' : '이동 속도 +1',
        'desc' : '플레이어가 더 빠르게\n이동합니다.',
        'color': GREEN,
        'icon' : 'arrow',
    },
    {
        'id'   : 'fire_rate',
        'name' : '연사 속도 +',
        'desc' : '탄환 발사 쿨다운이\n줄어듭니다.',
        'color': ORANGE,
        'icon' : 'rapid',
    },
]

augment_choices  = []   # 이번에 제시할 3가지 (AUGMENT_POOL에서 무작위 선택)
augment_hover    = -1   # 마우스 호버 중인 카드 인덱스

def pick_augment_choices():
    global augment_choices
    augment_choices = random.sample(AUGMENT_POOL, 3)

def apply_augment(aug_id):
    """선택한 증강을 플레이어 스탯에 즉시 적용."""
    global player_max_hp, player_hp, player_speed
    global bullet_speed, bullet_straight, bullet_spread, AUTO_FIRE_INTERVAL
    global bullet_radius

    if aug_id == 'max_hp':
        player_max_hp += 1
        player_hp = min(player_hp + 1, player_max_hp)
    elif aug_id == 'bullet_spd':
        bullet_speed    = min(bullet_speed  + 2, 20)
        bullet_radius   = min(bullet_radius + 1, 10)
    elif aug_id == 'bullet_straight':
        bullet_straight = min(bullet_straight + 1, 3)
    elif aug_id == 'bullet_spread':
        bullet_spread   = min(bullet_spread   + 1, 3)
    elif aug_id == 'move_spd':
        player_speed    = min(player_speed    + 1, 12)
    elif aug_id == 'fire_rate':
        AUTO_FIRE_INTERVAL = max(AUTO_FIRE_INTERVAL - 2, 4)

# 증강 카드 레이아웃 상수
CARD_W, CARD_H = 142, 215
CARD_GAP       = 7
CARDS_TOP      = 220
CARDS_TOTAL_W  = 3 * CARD_W + 2 * CARD_GAP
CARDS_LEFT     = (SCREEN_WIDTH - CARDS_TOTAL_W) // 2

def card_rect(i):
    x = CARDS_LEFT + i * (CARD_W + CARD_GAP)
    return pygame.Rect(x, CARDS_TOP, CARD_W, CARD_H)

# ════════════════════════════════════════════════════════════════════════════
#  헬퍼 함수
# ════════════════════════════════════════════════════════════════════════════
def spawn_particles(x, y, color, count=15):
    for _ in range(count):
        angle = random.uniform(0, 2*math.pi)
        spd   = random.uniform(1, 5)
        life  = random.randint(10, 25)
        particles.append({
            'x': x, 'y': y,
            'dx': spd*math.cos(angle), 'dy': spd*math.sin(angle),
            'life': life, 'max_life': life, 'color': color,
        })

def spawn_split_enemies(cx, cy):
    for side in (-1, 1):
        angle = math.radians(35)
        dx = side * enemy_speed * math.sin(angle)
        dy =        enemy_speed * math.cos(angle)
        sx = cx - SPLIT_WIDTH  // 2
        sy = cy - SPLIT_HEIGHT // 2
        enemies.append([sx, sy, 5, 1, sx, dx, dy])

def draw_hp_number(surface, ex, ey, w, h, hp, max_hp):
    ratio = hp / max_hp if max_hp else 0
    color = WHITE if ratio > 0.6 else (YELLOW if ratio > 0.3 else RED)
    text    = hp_font.render(str(hp), True, color)
    outline = hp_font.render(str(hp), True, BLACK)
    tx = ex + w//2 - text.get_width()//2
    ty = ey + h//2 - text.get_height()//2
    for ox, oy in ((-1,0),(1,0),(0,-1),(0,1)):
        surface.blit(outline, (tx+ox, ty+oy))
    surface.blit(text, (tx, ty))

def fire_bullets():
    """bullet_straight(직선) + bullet_spread(사선 쌍)에 맞춰 탄환을 발사."""
    cx = player_x + player_width // 2
    cy = player_y

    # ── 직선 탄환: 가운데 정렬, 10px 간격으로 옆으로 나열
    offset_step = 10
    total_w = (bullet_straight - 1) * offset_step
    for i in range(bullet_straight):
        ox = -total_w // 2 + i * offset_step
        bullets.append([cx + ox, cy, 0, -bullet_speed])

    # ── 사선 탄환: 15° 간격으로 좌우 대칭 쌍
    for pair in range(bullet_spread):
        angle = math.radians(15 + pair * 15)   # 15°, 30°, 45°
        dx = bullet_speed * math.sin(angle)
        dy = -bullet_speed * math.cos(angle)
        bullets.append([cx, cy,  dx, dy])   # 오른쪽
        bullets.append([cx, cy, -dx, dy])   # 왼쪽

def get_wave_enemy_table(wave):
    """웨이브 번호에 따른 적 타입 확률 테이블 반환 [(type, hp, weight), ...]"""
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
        base = [(0,1,15),(1,1,20),(3,1,20),(4,2,25),(2,3,20)]
        # 웨이브가 높을수록 정예·분열 비율 증가
        extra = min(w - 4, 6) * 2
        return [(0,1,max(5,15-extra)),(1,1,20),(3,1,20),(4,2,25+extra//2),(2,3,20+extra//2)]

def spawn_wave_enemy(wave):
    """현재 웨이브에 맞는 적 1마리 생성."""
    table   = get_wave_enemy_table(wave)
    types   = [t[0] for t in table]
    hps     = [t[1] for t in table]
    weights = [t[2] for t in table]
    idx     = random.choices(range(len(types)), weights=weights)[0]
    etype, ehp = types[idx], hps[idx]
    ex = random.randint(0, SCREEN_WIDTH - enemy_width)
    ey = -enemy_height
    enemies.append([ex, ey, etype, ehp, ex])

def start_wave(wave_num):
    """새 웨이브 시작 초기화."""
    global current_wave, wave_kills, wave_enemy_spawned
    global wave_spawn_total, wave_spawn_interval, enemy_spawn_counter
    global boss_active, boss_hp, boss_spawned_count, boss_max_hp
    global boss_x, boss_y, boss_direction, boss_shoot_counter
    global laser_state, laser_state_timer, laser_spawn_counter
    global laser_damaged_player, wave_state, wave_kill_goal

    current_wave        = wave_num
    wave_kills          = 0
    wave_enemy_spawned  = 0
    enemy_spawn_counter = 0
    enemies.clear()
    enemy_bullets.clear()
    items.clear()

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
        wave_spawn_total    = wave_kill_goal + 15   # 여유분 넉넉히
        wave_spawn_interval = max(15, 30 - wave_num)

    laser_state          = 0
    laser_state_timer    = 0
    laser_spawn_counter  = 0
    laser_damaged_player = False

def reset_game():
    """전체 게임 리셋."""
    global player_x, player_y, player_hp, player_max_hp
    global player_speed, bullet_speed, bullet_radius, bullet_straight, bullet_spread
    global AUTO_FIRE_INTERVAL, auto_fire_counter
    global score, game_over, wave_clear_timer, boss_spawned_count

    player_x          = SCREEN_WIDTH//2 - player_width//2
    player_y          = SCREEN_HEIGHT   - player_height - 20
    player_max_hp     = 3
    player_hp         = player_max_hp
    player_speed      = 5
    bullet_speed      = 7
    bullet_radius     = 5
    bullet_straight   = 1
    bullet_spread     = 0
    AUTO_FIRE_INTERVAL= 12
    auto_fire_counter = 0

    score              = 0
    game_over          = False
    wave_clear_timer   = 0
    boss_spawned_count = 0

    bullets.clear()
    particles.clear()
    start_wave(1)

# ── 최초 웨이브 시작 ─────────────────────────────────────────────────────
wave_kill_goal      = 20
wave_spawn_total    = 25
wave_spawn_interval = 30
start_wave(1)

# ════════════════════════════════════════════════════════════════════════════
#  메인 루프
# ════════════════════════════════════════════════════════════════════════════
running = True
while running:
    clock.tick(FPS)

    # ── 이벤트 ──────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                reset_game()

        # 증강 선택: 마우스 클릭
        if wave_state == 'augment' and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i in range(3):
                if card_rect(i).collidepoint(mx, my):
                    apply_augment(augment_choices[i]['id'])
                    start_wave(current_wave + 1)
                    break

        # 증강 선택: 마우스 호버
        if wave_state == 'augment' and event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            augment_hover = -1
            for i in range(3):
                if card_rect(i).collidepoint(mx, my):
                    augment_hover = i
                    break

    # ── 별 스크롤 (항상) ────────────────────────────────────────────────────
    for star in stars:
        star[1] += star[3]
        if star[1] > SCREEN_HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, SCREEN_WIDTH)

    # ════════════════════════════════════════════════════════════════════════
    #  게임 로직 (wave_state == 'playing' 또는 'boss')
    # ════════════════════════════════════════════════════════════════════════
    if not game_over and wave_state in ('playing', 'boss'):

        # 탄환 속도는 증강 적용값 그대로 사용 (점수 기반 자동 강화 제거)
        # 적 미사일은 웨이브에 따라 약간 강화
        enemy_bullet_speed  = 4 + current_wave * 0.3
        enemy_bullet_radius = 4

        # 플레이어 이동
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and player_x > 0:                        player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH-player_width: player_x += player_speed
        if keys[pygame.K_UP]    and player_y > 0:                        player_y -= player_speed
        if keys[pygame.K_DOWN]  and player_y < SCREEN_HEIGHT-player_height: player_y += player_speed

        # 자동 연사 (항상 발사)
        auto_fire_counter += 1
        if auto_fire_counter >= AUTO_FIRE_INTERVAL:
            auto_fire_counter = 0
            fire_bullets()

        # 파티클
        for p in particles[:]:
            p['x'] += p['dx']; p['y'] += p['dy']; p['life'] -= 1
            if p['life'] <= 0: particles.remove(p)

        # 레이저
        if laser_state == 0:
            laser_spawn_counter += 1
            if laser_spawn_counter >= 450:
                laser_state = 1; laser_state_timer = 0
                laser_x = random.randint(50, SCREEN_WIDTH-50)
                laser_y = random.randint(150, SCREEN_HEIGHT-120)
                laser_damaged_player = False; laser_spawn_counter = 0
        elif laser_state == 1:
            laser_state_timer += 1
            if laser_state_timer >= 90: laser_state = 2; laser_state_timer = 0
        elif laser_state == 2:
            laser_state_timer += 1
            if not laser_damaged_player:
                pr = pygame.Rect(player_x, player_y, player_width, player_height)
                lh = pygame.Rect(0, laser_y-laser_height//2, SCREEN_WIDTH, laser_height)
                lv = pygame.Rect(laser_x-laser_height//2, 0, laser_height, SCREEN_HEIGHT)
                if pr.colliderect(lh) or pr.colliderect(lv):
                    player_hp -= 1; laser_damaged_player = True
                    spawn_particles(player_x+player_width//2, player_y+player_height//2, RED, 20)
                    if player_hp <= 0: game_over = True
            if laser_state_timer >= 30: laser_state = 0; laser_state_timer = 0

        # 탄환 이동
        for b in bullets[:]:
            b[0] += b[2]; b[1] += b[3]
            if b[1] < 0 or b[0] < 0 or b[0] > SCREEN_WIDTH: bullets.remove(b)
        for eb in enemy_bullets[:]:
            eb[0] += eb[2]; eb[1] += eb[3]
            if eb[1] > SCREEN_HEIGHT or eb[0] < 0 or eb[0] > SCREEN_WIDTH: enemy_bullets.remove(eb)

        # ── 보스 웨이브 로직 ─────────────────────────────────────────────
        if wave_state == 'boss' and boss_active:
            boss_x += boss_speed * boss_direction
            if boss_x <= 0:                          boss_x = 0;                       boss_direction = 1
            elif boss_x >= SCREEN_WIDTH-boss_width:  boss_x = SCREEN_WIDTH-boss_width; boss_direction = -1
            boss_shoot_counter += 1
            if boss_shoot_counter >= 45:
                enemy_bullets.append([boss_x+boss_width//2, boss_y+boss_height, 0,                        enemy_bullet_speed])
                enemy_bullets.append([boss_x+10,            boss_y+boss_height, -0.3*enemy_bullet_speed,  enemy_bullet_speed])
                enemy_bullets.append([boss_x+boss_width-10, boss_y+boss_height,  0.3*enemy_bullet_speed,  enemy_bullet_speed])
                boss_shoot_counter = 0

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
            # 아이템 스폰 기준을 웨이브 시작 후 프레임이 아닌 카운터로 관리
            if not hasattr(start_wave, '_item_counter'):
                pass
        # 간단히 전역 카운터 사용
        if wave_state == 'playing':
            globals().setdefault('item_spawn_counter', 0)
            globals()['item_spawn_counter'] = globals().get('item_spawn_counter', 0) + 1
            if globals()['item_spawn_counter'] >= 360:
                ix = random.randint(0, SCREEN_WIDTH-item_width)
                items.append([ix, -item_height, 1])   # 항상 HP 회복 아이템
                globals()['item_spawn_counter'] = 0
        for item in items[:]:
            item[1] += item_speed
            if item[1] > SCREEN_HEIGHT: items.remove(item)

        # ── 충돌: 플레이어 탄환 vs 적 ───────────────────────────────────
        for b in bullets[:]:
            br = pygame.Rect(b[0]-bullet_radius, b[1]-bullet_radius, bullet_radius*2, bullet_radius*2)
            hit = False
            for enemy in enemies[:]:
                ew = SPLIT_WIDTH  if enemy[2]==5 else enemy_width
                eh = SPLIT_HEIGHT if enemy[2]==5 else enemy_height
                er = pygame.Rect(enemy[0], enemy[1], ew, eh)
                if br.colliderect(er):
                    if b in bullets: bullets.remove(b)
                    enemy[3] -= 1
                    spawn_particles(b[0], b[1], WHITE, 4)
                    if enemy[3] <= 0:
                        if enemy in enemies: enemies.remove(enemy)
                        cx = enemy[0] + ew//2
                        cy = enemy[1] + eh//2
                        ec = {0:RED,1:ORANGE,2:YELLOW,3:CYAN,4:LIME,5:LIME_DARK}
                        spawn_particles(cx, cy, ec.get(enemy[2], RED), 12)
                        if enemy[2] == 4:
                            spawn_split_enemies(cx, cy); score += 20
                        elif enemy[2] == 5: score += 15
                        elif enemy[2] == 2: score += 50
                        elif enemy[2] == 1: score += 20
                        elif enemy[2] == 3: score += 30
                        else:               score += 10
                        wave_kills += 1
                    hit = True; break

            # 보스 충돌
            if not hit and wave_state == 'boss' and boss_active:
                bossr = pygame.Rect(boss_x, boss_y, boss_width, boss_height)
                if br.colliderect(bossr):
                    if b in bullets: bullets.remove(b)
                    boss_hp -= 1
                    spawn_particles(b[0], b[1], WHITE, 4)
                    if boss_hp <= 0:
                        boss_active = False
                        score += 500 + current_wave * 50
                        spawn_particles(boss_x+boss_width//2, boss_y+boss_height//2, PURPLE, 40)
                        wave_kills += 1   # 보스 처치 = 1킬

        # ── 충돌: 플레이어 vs 적 ────────────────────────────────────────
        pr = pygame.Rect(player_x, player_y, player_width, player_height)
        for enemy in enemies[:]:
            ew = SPLIT_WIDTH  if enemy[2]==5 else enemy_width
            eh = SPLIT_HEIGHT if enemy[2]==5 else enemy_height
            if pr.colliderect(pygame.Rect(enemy[0], enemy[1], ew, eh)):
                enemies.remove(enemy)
                player_hp -= 1
                spawn_particles(enemy[0]+ew//2, enemy[1]+eh//2, RED, 20)
                if player_hp <= 0: game_over = True

        for eb in enemy_bullets[:]:
            ebr = pygame.Rect(eb[0]-enemy_bullet_radius, eb[1]-enemy_bullet_radius,
                              enemy_bullet_radius*2, enemy_bullet_radius*2)
            if pr.colliderect(ebr):
                enemy_bullets.remove(eb); player_hp -= 1
                spawn_particles(player_x+player_width//2, player_y+player_height//2, ORANGE, 12)
                if player_hp <= 0: game_over = True

        if wave_state == 'boss' and boss_active:
            if pr.colliderect(pygame.Rect(boss_x, boss_y, boss_width, boss_height)):
                player_hp = 0
                spawn_particles(player_x+player_width//2, player_y+player_height//2, PURPLE, 30)
                game_over = True

        # 아이템 획득
        for item in items[:]:
            if pr.colliderect(pygame.Rect(item[0], item[1], item_width, item_height)):
                items.remove(item)
                if player_hp < player_max_hp: player_hp += 1
                score += 15
                spawn_particles(item[0]+item_width//2, item[1]+item_height//2, HOT_PINK, 15)

        # ── 웨이브 클리어 판정 ───────────────────────────────────────────
        if not game_over and wave_kills >= wave_kill_goal and len(enemies) == 0 and wave_state in ('playing','boss'):
            wave_state       = 'wave_clear'
            wave_clear_timer = 0
            enemies.clear(); enemy_bullets.clear(); bullets.clear()

    # ── wave_clear 연출 ──────────────────────────────────────────────────
    elif not game_over and wave_state == 'wave_clear':
        for p in particles[:]:
            p['x'] += p['dx']; p['y'] += p['dy']; p['life'] -= 1
            if p['life'] <= 0: particles.remove(p)
        wave_clear_timer += 1
        if wave_clear_timer >= WAVE_CLEAR_SHOW:
            # 증강 타이밍 판단: 다음 웨이브가 (AUGMENT_EVERY)의 배수면 증강
            next_wave = current_wave + 1
            if next_wave % AUGMENT_EVERY == 0 and next_wave % BOSS_WAVE_INTERVAL != 0:
                wave_state = 'augment'
                pick_augment_choices()
            else:
                start_wave(next_wave)

    # ════════════════════════════════════════════════════════════════════════
    #  화면 그리기
    # ════════════════════════════════════════════════════════════════════════
    screen.fill(BLACK)

    # 별
    for star in stars:
        pygame.draw.circle(screen, star[4], (star[0], int(star[1])), star[2])

    # ── 게임 오브젝트 그리기 (플레이 / 보스 / wave_clear 중) ────────────
    if wave_state in ('playing','boss','wave_clear'):

        # 플레이어
        pygame.draw.rect(screen, BLUE, (player_x, player_y, player_width, player_height))

        # 플레이어 탄환
        for b in bullets:
            pygame.draw.circle(screen, YELLOW, (int(b[0]), int(b[1])), bullet_radius)

        # 적 탄환
        for eb in enemy_bullets:
            pygame.draw.circle(screen, ORANGE, (int(eb[0]), int(eb[1])), enemy_bullet_radius)

        # 적
        for enemy in enemies:
            ex, ey = int(enemy[0]), int(enemy[1])
            if enemy[2] == 0:
                pygame.draw.rect(screen, RED, (ex,ey,enemy_width,enemy_height))
                draw_hp_number(screen,ex,ey,enemy_width,enemy_height,enemy[3],1)
            elif enemy[2] == 1:
                pygame.draw.rect(screen, ORANGE, (ex,ey,enemy_width,enemy_height))
                draw_hp_number(screen,ex,ey,enemy_width,enemy_height,enemy[3],1)
            elif enemy[2] == 2:
                pygame.draw.rect(screen, YELLOW, (ex,ey,enemy_width,enemy_height))
                draw_hp_number(screen,ex,ey,enemy_width,enemy_height,enemy[3],3)
            elif enemy[2] == 3:
                pts = [(ex+enemy_width//2,ey),(ex,ey+enemy_height//2),
                       (ex+enemy_width//2,ey+enemy_height),(ex+enemy_width,ey+enemy_height//2)]
                pygame.draw.polygon(screen, CYAN, pts)
                draw_hp_number(screen,ex,ey,enemy_width,enemy_height,enemy[3],1)
            elif enemy[2] == 4:
                cx2=ex+enemy_width//2; cy2=ey+enemy_height//2
                rx=enemy_width//2; ry=enemy_height//2
                hpts=[(cx2+int(rx*math.cos(math.radians(60*i-30))),
                       cy2+int(ry*math.sin(math.radians(60*i-30)))) for i in range(6)]
                pygame.draw.polygon(screen, LIME, hpts)
                pygame.draw.polygon(screen, WHITE, hpts, 2)
                draw_hp_number(screen,ex,ey,enemy_width,enemy_height,enemy[3],2)
            elif enemy[2] == 5:
                pts=[(ex+SPLIT_WIDTH//2,ey+SPLIT_HEIGHT),(ex,ey),(ex+SPLIT_WIDTH,ey)]
                pygame.draw.polygon(screen, LIME_DARK, pts)
                pygame.draw.polygon(screen, LIME, pts, 2)
                draw_hp_number(screen,ex,ey,SPLIT_WIDTH,SPLIT_HEIGHT,enemy[3],1)

        # 보스
        if boss_active:
            pygame.draw.rect(screen, PURPLE, (boss_x,boss_y,boss_width,boss_height))
            pygame.draw.rect(screen, RED, (boss_x+20,boss_y+10,boss_width-40,boss_height-20))
            pygame.draw.rect(screen, RED,   (boss_x, boss_y-12, boss_width, 6))
            pygame.draw.rect(screen, GREEN, (boss_x, boss_y-12, int(boss_hp/boss_max_hp*boss_width), 6))

        # 레이저
        if laser_state == 1 and (pygame.time.get_ticks()//100)%2==0:
            pygame.draw.line(screen, RED, (0,laser_y),(SCREEN_WIDTH,laser_y), 2)
            pygame.draw.line(screen, RED, (laser_x,0),(laser_x,SCREEN_HEIGHT), 2)
        elif laser_state == 2:
            pygame.draw.rect(screen,RED,  (0,laser_y-8,SCREEN_WIDTH,16))
            pygame.draw.rect(screen,WHITE,(0,laser_y-3,SCREEN_WIDTH,6))
            pygame.draw.rect(screen,RED,  (laser_x-8,0,16,SCREEN_HEIGHT))
            pygame.draw.rect(screen,WHITE,(laser_x-3,0,6,SCREEN_HEIGHT))

        # 파티클
        for p in particles:
            r = int(max(1,(p['life']/p['max_life'])*5))
            pygame.draw.circle(screen,p['color'],(int(p['x']),int(p['y'])),r)

        # 아이템
        for item in items:
            if item[2]==1:
                pygame.draw.rect(screen,HOT_PINK,(item[0]+item_width//3,item[1],item_width//3,item_height))
                pygame.draw.rect(screen,HOT_PINK,(item[0],item[1]+item_height//3,item_width,item_height//3))
            else:
                pygame.draw.polygon(screen,GREEN,
                    [(item[0]+item_width//2,item[1]),(item[0],item[1]+item_height),(item[0]+item_width,item[1]+item_height)])

        # ── HUD ─────────────────────────────────────────────────────────
        # 점수
        screen.blit(font.render(f"Score: {score}", True, WHITE), (10,10))

        # 웨이브 번호 + 진행도
        wave_label = f"Wave {current_wave}"
        if wave_state == 'boss':
            wave_label += "  [BOSS]"
        screen.blit(font.render(wave_label, True, GOLD), (SCREEN_WIDTH//2 - 60, 10))

        # 처치 진행도 (보스 웨이브는 표시 안 함)
        if wave_state == 'playing':
            kill_text = small_font.render(f"{wave_kills}/{wave_kill_goal}", True, WHITE)
            screen.blit(kill_text, (SCREEN_WIDTH//2 - kill_text.get_width()//2, 42))

        # HP
        screen.blit(font.render("HP: ", True, WHITE), (SCREEN_WIDTH-150, 10))
        for i in range(player_max_hp):
            rc = GREEN if i < player_hp else BLACK
            pygame.draw.rect(screen, rc,    (SCREEN_WIDTH-95+i*25, 16, 18, 18))
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH-95+i*25, 16, 18, 18), 2)

        # ── Wave Clear 연출 ──────────────────────────────────────────────
        if wave_state == 'wave_clear':
            alpha = min(255, wave_clear_timer * 6)
            surf = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
            surf.fill((0,0,0,120))
            screen.blit(surf, (0, SCREEN_HEIGHT//2 - 50))
            t1 = big_font.render(f"WAVE {current_wave} CLEAR!", True, GOLD)
            screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, SCREEN_HEIGHT//2 - 40))

    # ── 증강 선택 화면 ───────────────────────────────────────────────────
    elif wave_state == 'augment':

        # 반투명 오버레이
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        screen.blit(overlay, (0,0))

        # 타이틀
        t = big_font.render("증강 선택", True, GOLD)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 140))
        sub = small_font.render("하나를 선택해 플레이어를 강화하세요", True, WHITE)
        screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 195))

        # 카드 3장
        for i, aug in enumerate(augment_choices):
            cr  = card_rect(i)
            hovered = (i == augment_hover)

            # 카드 배경
            bg_col = (50,50,70) if not hovered else (70,70,100)
            pygame.draw.rect(screen, bg_col, cr, border_radius=10)
            border_col = aug['color'] if hovered else (100,100,130)
            pygame.draw.rect(screen, border_col, cr, 2, border_radius=10)

            # 아이콘 영역 (상단 색상 띠)
            icon_rect = pygame.Rect(cr.x, cr.y, cr.w, 55)
            pygame.draw.rect(screen, aug['color'],
                             (cr.x+2, cr.y+2, cr.w-4, 53), border_radius=9)

            # 아이콘 심볼
            icx, icy = cr.centerx, cr.y + 28
            ic = aug['icon']
            if ic == 'heart':
                pygame.draw.circle(screen, WHITE, (icx-8,icy-4), 10)
                pygame.draw.circle(screen, WHITE, (icx+8,icy-4), 10)
                pygame.draw.polygon(screen, WHITE, [(icx-18,icy),(icx,icy+16),(icx+18,icy)])
            elif ic == 'bullet':
                pygame.draw.circle(screen, WHITE, (icx, icy-6), 7)
                pygame.draw.rect(screen, WHITE, (icx-5, icy-6, 10, 18))
            elif ic == 'straight':
                # 직선 탄환 아이콘: 3줄기가 위로 나란히
                for ox in (-8, 0, 8):
                    pygame.draw.line(screen, WHITE, (icx+ox, icy+10), (icx+ox, icy-12), 3)
                    pygame.draw.polygon(screen, WHITE,
                        [(icx+ox, icy-16),(icx+ox-4, icy-8),(icx+ox+4, icy-8)])
            elif ic == 'spread':
                # 사선 탄환 아이콘: 좌우 대각선 쌍
                for ang in (-35, 35):
                    a = math.radians(ang - 90)
                    pygame.draw.line(screen, WHITE, (icx,icy),
                                     (icx+int(20*math.cos(a)), icy+int(20*math.sin(a))), 3)
            elif ic == 'arrow':
                pygame.draw.polygon(screen, WHITE,
                    [(icx,icy-14),(icx-10,icy+4),(icx-4,icy+4),(icx-4,icy+14),
                     (icx+4,icy+14),(icx+4,icy+4),(icx+10,icy+4)])
            elif ic == 'rapid':
                for k in range(3):
                    pygame.draw.line(screen,WHITE,(icx-12+k*12,icy+8),(icx-8+k*12,icy-8),3)

            # 이름 (카드 너비를 넘으면 축소)
            nt = aug_title_font.render(aug['name'], True, WHITE)
            if nt.get_width() > CARD_W - 8:
                scale = (CARD_W - 8) / nt.get_width()
                nt = pygame.transform.smoothscale(nt,
                         (int(nt.get_width()*scale), int(nt.get_height()*scale)))
            screen.blit(nt, (cr.centerx - nt.get_width()//2, cr.y + 62))

            # 설명 (줄바꿈 처리, 카드 클리핑)
            prev_clip = screen.get_clip()
            screen.set_clip(pygame.Rect(cr.x+4, cr.y+82, CARD_W-8, CARD_H-120))
            for li, line in enumerate(aug['desc'].split('\n')):
                dt = aug_desc_font.render(line, True, (200,200,200))
                if dt.get_width() > CARD_W - 8:
                    scale = (CARD_W - 8) / dt.get_width()
                    dt = pygame.transform.smoothscale(dt,
                             (int(dt.get_width()*scale), int(dt.get_height()*scale)))
                screen.blit(dt, (cr.centerx - dt.get_width()//2, cr.y + 83 + li*19))
            screen.set_clip(prev_clip)

            # 호버 시 "선택" 버튼
            if hovered:
                btn = pygame.Rect(cr.x+15, cr.y+cr.h-35, cr.w-30, 25)
                pygame.draw.rect(screen, aug['color'], btn, border_radius=5)
                bt = small_font.render("선택", True, BLACK)
                screen.blit(bt, (btn.centerx - bt.get_width()//2, btn.centery - bt.get_height()//2))

    # ── 게임 오버 ────────────────────────────────────────────────────────
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,150))
        screen.blit(overlay,(0,0))
        ot = big_font.render("GAME OVER", True, WHITE)
        rt = font.render("Press 'R' to Restart", True, WHITE)
        st = font.render(f"Score: {score}  Wave: {current_wave}", True, GOLD)
        screen.blit(ot, (SCREEN_WIDTH//2 - ot.get_width()//2, SCREEN_HEIGHT//2 - 70))
        screen.blit(st, (SCREEN_WIDTH//2 - st.get_width()//2, SCREEN_HEIGHT//2))
        screen.blit(rt, (SCREEN_WIDTH//2 - rt.get_width()//2, SCREEN_HEIGHT//2 + 50))

    pygame.display.flip()

pygame.quit()
sys.exit()