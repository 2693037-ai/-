import pygame
import random
import sys
import math
# 1. 게임 초기화 및 창 설정
pygame.init()
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 640
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter - 5 New Features Edition")
# 색상 정의 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 128, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
GREEN = (50, 255, 50)
ORANGE = (255, 128, 0)  
CYAN = (0, 255, 255)         # [신규] 지그재그 적용 색상
PURPLE = (147, 112, 219)     # [신규] 보스용 색상
HOT_PINK = (255, 105, 180)   # [신규] 체력 회복 아이템 색상
LIME = (180, 255, 60)        # [신규] 분열 적(대) 색상
LIME_DARK = (100, 200, 30)   # [신규] 분열 적(소) 색상
# FPS 조절을 위한 시계 설정
clock = pygame.time.Clock()
FPS = 60
# 게임 객체 속성 설정
player_width = 40
player_height = 40
player_x = (SCREEN_WIDTH // 2) - (player_width // 2)
player_y = SCREEN_HEIGHT - player_height - 20
player_speed = 5
# [신규] 플레이어 체력(HP) 시스템 변수
player_max_hp = 3
player_hp = player_max_hp
bullets = []
bullet_speed = 7
bullet_radius = 5
# [신규] 적 미사일 구조 수정: [x, y, dx, dy] 속도 벡터 포함
enemy_bullets = []
enemy_bullet_speed = 5
enemy_bullet_radius = 4

# [구조 변경] 적 리스트 내부 요소: [x, y, 적 종류, 현재 체력, 시작 X 좌표]
# - 적 종류(type):
#     0: 일반(빨간 네모)
#     1: 미사일(주황 네모)
#     2: 정예(노란 네모, 체력 3)
#     3: 지그재그 고속(민트 다이아몬드)
#     4: 분열 대형(라임 육각형, 처치 시 소형 2개로 분열)
#     5: 분열 소형(어두운 라임 삼각형, 처치 시 점수만 획득)
enemies = []  
enemy_width = 40
enemy_height = 40
enemy_speed = 3
enemy_spawn_counter = 0
items = []
item_width = 30
item_height = 30
item_speed = 4
item_spawn_counter = 0
# [신규] Pygame 내장 타이머 기반 버프 시스템 변수
triple_shot_active = False 
triple_shot_duration = 5000  # 5초 (밀리초 단위)
triple_shot_start_time = 0
# [신규] 파괴 시각 효과용 파티클 시스템 변수
particles = []
# [신규] 보스 레이드 관련 변수
boss_active = False
boss_hp = 0
boss_max_hp = 20
boss_x = 0
boss_y = 50
boss_width = 80
boss_height = 40
boss_speed = 2
boss_direction = 1
boss_shoot_counter = 0
boss_spawned_count = 0
# [신규] 맵 횡단 레이저 관련 변수
laser_state = 0  # 0: 대기, 1: 경고(지시선), 2: 발사(활성)
laser_state_timer = 0
laser_spawn_counter = 0
laser_x = 0
laser_y = 0
laser_height = 16
laser_damaged_player = False
# [신규] 패럴랙스 우주 배경 별 리스트
stars = []
for _ in range(50):
    size = random.choices([1, 1, 1, 2], weights=[5, 5, 5, 1])[0]
    speed = 0.3 if size == 1 else 0.7
    color_val = random.randint(40, 80) if size == 1 else random.randint(70, 120)
    color = (color_val, color_val, min(255, color_val + random.randint(0, 20)))
    stars.append([random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), size, speed, color])
# 게임 상태 변수
score = 0
game_over = False
# 폰트 설정
font = pygame.font.SysFont("arial", 30)
game_over_font = pygame.font.SysFont("arial", 50)
# [신규] 파티클 생성 함수
def spawn_particles(x, y, color, count=15):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        dx = speed * math.cos(angle)
        dy = speed * math.sin(angle)
        life = random.randint(10, 25)
        particles.append({
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'life': life,
            'max_life': life,
            'color': color
        })

# ──────────────────────────────────────────────
# [신규] 분열 적 소형 2마리를 생성하는 함수
# 대형 적이 파괴된 위치(cx, cy)에서 좌우로 퍼져나가며 스폰됨
# 소형 적 크기: 24x24 (대형의 60%)
# ──────────────────────────────────────────────
SPLIT_WIDTH  = 24
SPLIT_HEIGHT = 24

def spawn_split_enemies(cx, cy):
    """
    분열 대형 적(type 4) 처치 시 호출.
    cx, cy: 대형 적의 중심 좌표.
    소형 적(type 5) 2마리를 좌우 35° 방향으로 스폰한다.
    데이터 구조: [x, y, type, hp, start_x, dx, dy]
      - dx, dy: 소형 전용 속도 벡터 (일반 적과 달리 대각선으로 이동)
    """
    for side in (-1, 1):          # -1: 왼쪽, +1: 오른쪽
        angle = math.radians(35)  # 좌우 35도 분열각
        dx = side * enemy_speed * math.sin(angle)
        dy =       enemy_speed * math.cos(angle)
        spawn_x = cx - SPLIT_WIDTH  // 2
        spawn_y = cy - SPLIT_HEIGHT // 2
        # [x, y, type, hp, start_x, dx, dy]
        enemies.append([spawn_x, spawn_y, 5, 1, spawn_x, dx, dy])

# ──────────────────────────────────────────────
# [신규] 적 체력바 그리기 헬퍼 함수
# 적 몸체 바로 위에 체력바를 표시한다.
#   ex, ey      : 적의 좌상단 픽셀 좌표
#   w           : 적의 폭 (체력바 너비 기준)
#   hp, max_hp  : 현재/최대 체력
# 체력 비율에 따라 색상이 녹색→노란→빨간 순으로 변한다.
# 체력이 꽉 찬(hp == max_hp) 경우에는 표시하지 않는다.
# ──────────────────────────────────────────────
hp_font = pygame.font.SysFont("arial", 14, bold=True)

def draw_hp_number(surface, ex, ey, w, h, hp, max_hp):
    ratio = hp / max_hp
    if ratio > 0.6:
        color = WHITE
    elif ratio > 0.3:
        color = YELLOW
    else:
        color = RED
    text = hp_font.render(str(hp), True, color)
    outline = hp_font.render(str(hp), True, BLACK)
    tx = ex + w // 2 - text.get_width()  // 2
    ty = ey + h // 2 - text.get_height() // 2
    # 외곽선: 상하좌우 1px 오프셋으로 검은 텍스트 먼저 그리기
    for ox, oy in ((-1,0),(1,0),(0,-1),(0,1)):
        surface.blit(outline, (tx + ox, ty + oy))
    surface.blit(text, (tx, ty))

auto_fire_counter = 0   # 자동 연사 쿨다운 카운터
AUTO_FIRE_INTERVAL = 12  # 연사 간격 (프레임, 60fps 기준 약 0.2초)

# 메인 게임 루프
running = True
while running:
    clock.tick(FPS)
    # --- 이벤트 처리 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game_over:
                if event.key == pygame.K_r:
                    player_x = (SCREEN_WIDTH // 2) - (player_width // 2)
                    player_y = SCREEN_HEIGHT - player_height - 20
                    player_hp = player_max_hp
                    bullets.clear()
                    enemy_bullets.clear() 
                    enemies.clear()
                    items.clear()
                    particles.clear()

                    triple_shot_active = False
                    triple_shot_start_time = 0
                    auto_fire_counter = AUTO_FIRE_INTERVAL

                    boss_active = False
                    boss_hp = 0
                    boss_spawned_count = 0

                    laser_state = 0
                    laser_state_timer = 0
                    laser_spawn_counter = 0
                    laser_x = 0
                    laser_y = 0
                    laser_damaged_player = False

                    score = 0
                    game_over = False
            else:
                pass  # 발사는 아래 자동 연사 로직에서 처리

    # 우주 배경 별 이동 업데이트
    for star in stars:
        star[1] += star[3]
        if star[1] > SCREEN_HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, SCREEN_WIDTH)

    # --- 게임 로직 업데이트 ---
    if not game_over:
        # 점수에 따른 탄환 크기 및 속도 강화 시스템
        if score >= 3000:
            bullet_speed = 13
            bullet_radius = 8
            enemy_bullet_speed = 9.5
            enemy_bullet_radius = 7
        elif score >= 1500:
            bullet_speed = 11
            bullet_radius = 7
            enemy_bullet_speed = 8.0
            enemy_bullet_radius = 6
        elif score >= 500:
            bullet_speed = 9
            bullet_radius = 6
            enemy_bullet_speed = 6.5
            enemy_bullet_radius = 5
        else:
            bullet_speed = 7
            bullet_radius = 5
            enemy_bullet_speed = 5.0
            enemy_bullet_radius = 4

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH - player_width:
            player_x += player_speed
        if keys[pygame.K_UP] and player_y > 0:
            player_y -= player_speed
        if keys[pygame.K_DOWN] and player_y < SCREEN_HEIGHT - player_height:
            player_y += player_speed

        # ── 자동 연사: 스페이스바를 누르고 있으면 쿨다운마다 발사 ──────
        if keys[pygame.K_SPACE]:
            auto_fire_counter += 1
            if auto_fire_counter >= AUTO_FIRE_INTERVAL:
                auto_fire_counter = 0
                current_time = pygame.time.get_ticks()
                is_triple_active = triple_shot_active and (current_time < triple_shot_start_time + triple_shot_duration)
                if is_triple_active:
                    bullets.append([player_x + (player_width // 2), player_y, 0, -bullet_speed])
                    angle_rad = math.radians(30)
                    dx_diagonal = bullet_speed * math.sin(angle_rad)
                    dy_diagonal = -bullet_speed * math.cos(angle_rad)
                    bullets.append([player_x + (player_width // 2), player_y, -dx_diagonal, dy_diagonal])
                    bullets.append([player_x + (player_width // 2), player_y,  dx_diagonal, dy_diagonal])
                else:
                    bullets.append([player_x + (player_width // 2), player_y, 0, -bullet_speed])
        else:
            auto_fire_counter = AUTO_FIRE_INTERVAL  # 키를 떼면 즉시 발사 준비 상태로

        # 버프 타이머 업데이트
        current_time = pygame.time.get_ticks()
        if triple_shot_active and current_time >= triple_shot_start_time + triple_shot_duration:
            triple_shot_active = False

        # 파티클 업데이트
        for particle in particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                particles.remove(particle)

        # 맵 횡단 레이저 업데이트
        if laser_state == 0:
            laser_spawn_counter += 1
            if laser_spawn_counter >= 450:
                laser_state = 1
                laser_state_timer = 0
                laser_x = random.randint(50, SCREEN_WIDTH - 50)
                laser_y = random.randint(150, SCREEN_HEIGHT - 120)
                laser_damaged_player = False
                laser_spawn_counter = 0
        elif laser_state == 1:
            laser_state_timer += 1
            if laser_state_timer >= 90:
                laser_state = 2
                laser_state_timer = 0
        elif laser_state == 2:
            laser_state_timer += 1
            if not laser_damaged_player:
                player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
                laser_h_rect = pygame.Rect(0, laser_y - laser_height // 2, SCREEN_WIDTH, laser_height)
                laser_v_rect = pygame.Rect(laser_x - laser_height // 2, 0, laser_height, SCREEN_HEIGHT)
                if player_rect.colliderect(laser_h_rect) or player_rect.colliderect(laser_v_rect):
                    player_hp -= 1
                    laser_damaged_player = True
                    spawn_particles(player_x + player_width // 2, player_y + player_height // 2, RED, 20)
                    if player_hp <= 0:
                        game_over = True
            if random.random() < 0.4:
                spawn_particles(random.randint(0, SCREEN_WIDTH), laser_y, RED, 2)
                spawn_particles(laser_x, random.randint(0, SCREEN_HEIGHT), RED, 2)
            if laser_state_timer >= 30:
                laser_state = 0
                laser_state_timer = 0

        # 플레이어 미사일 위치 업데이트
        for bullet in bullets[:]:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            if bullet[1] < 0 or bullet[0] < 0 or bullet[0] > SCREEN_WIDTH:
                bullets.remove(bullet)

        # 적 미사일 위치 업데이트
        for e_bullet in enemy_bullets[:]:
            e_bullet[0] += e_bullet[2]
            e_bullet[1] += e_bullet[3]
            if e_bullet[1] > SCREEN_HEIGHT or e_bullet[0] < 0 or e_bullet[0] > SCREEN_WIDTH:
                enemy_bullets.remove(e_bullet)

        # 보스 출현 트리거 검사
        next_boss_score = 1000 * (boss_spawned_count + 1)
        if score >= next_boss_score and not boss_active:
            boss_active = True
            boss_spawned_count += 1
            boss_hp = boss_max_hp
            boss_x = (SCREEN_WIDTH // 2) - (boss_width // 2)
            boss_y = 50
            boss_direction = 1
            boss_shoot_counter = 0
            enemies.clear()
            enemy_bullets.clear()

        # 보스 로직 업데이트
        if boss_active:
            boss_x += boss_speed * boss_direction
            if boss_x <= 0:
                boss_x = 0
                boss_direction = 1
            elif boss_x >= SCREEN_WIDTH - boss_width:
                boss_x = SCREEN_WIDTH - boss_width
                boss_direction = -1

            boss_shoot_counter += 1
            if boss_shoot_counter >= 45:
                enemy_bullets.append([boss_x + (boss_width // 2), boss_y + boss_height, 0, enemy_bullet_speed])
                enemy_bullets.append([boss_x + 10, boss_y + boss_height, -0.3 * enemy_bullet_speed, enemy_bullet_speed])
                enemy_bullets.append([boss_x + boss_width - 10, boss_y + boss_height, 0.3 * enemy_bullet_speed, enemy_bullet_speed])
                boss_shoot_counter = 0

        # 적 생성 주기 관리 (보스 전투 중에는 일반 적 생성 일시 정지)
        if not boss_active:
            enemy_spawn_counter += 1
            if enemy_spawn_counter >= 30:
                enemy_x = random.randint(0, SCREEN_WIDTH - enemy_width)
                enemy_y = -enemy_height

                # ── 적 생성 로직 (type 4 분열 적 포함) ──────────────────
                # 데이터 구조: [x, y, 종류, 체력, 시작 X 좌표]
                # type 4(분열 대형)는 체력 2. 소형(type 5)은 spawn_split_enemies()에서 생성.
                if score >= 1250:
                    rand_val = random.random()
                    if rand_val < 0.20:    # 20% 미사일 적
                        enemies.append([enemy_x, enemy_y, 1, 1, enemy_x])
                    elif rand_val < 0.40:  # 20% 정예 노란색 적
                        enemies.append([enemy_x, enemy_y, 2, 3, enemy_x])
                    elif rand_val < 0.60:  # 20% 지그재그 고속 적
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    elif rand_val < 0.80:  # 20% 분열 대형 적
                        enemies.append([enemy_x, enemy_y, 4, 2, enemy_x])
                    else:                  # 20% 일반 적
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                elif score >= 750:
                    rand_val = random.random()
                    if rand_val < 0.25:
                        enemies.append([enemy_x, enemy_y, 1, 1, enemy_x])
                    elif rand_val < 0.45:
                        enemies.append([enemy_x, enemy_y, 2, 3, enemy_x])
                    elif rand_val < 0.65:
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    elif rand_val < 0.85:  # 20% 분열 대형 적
                        enemies.append([enemy_x, enemy_y, 4, 2, enemy_x])
                    else:
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                elif score >= 500:
                    rand_val = random.random()
                    if rand_val < 0.25:
                        enemies.append([enemy_x, enemy_y, 1, 1, enemy_x])
                    elif rand_val < 0.50:
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    elif rand_val < 0.75:  # 25% 분열 대형 적
                        enemies.append([enemy_x, enemy_y, 4, 2, enemy_x])
                    else:
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                elif score >= 300:
                    # 300점 이상부터 분열 적 첫 등장
                    rand_val = random.random()
                    if rand_val < 0.25:
                        enemies.append([enemy_x, enemy_y, 4, 2, enemy_x])
                    elif rand_val < 0.50:
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    else:
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                elif score >= 200:
                    if random.random() < 0.3:
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    else:
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                else:
                    enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])

                enemy_spawn_counter = 0

        # ── 적 위치 업데이트 및 미사일 발사 ──────────────────────────────
        for enemy in enemies[:]:
            if enemy[2] == 2:
                current_enemy_speed = 2
            elif enemy[2] == 3:
                current_enemy_speed = 5
            elif enemy[2] == 4:
                # 분열 대형: 묵직하게 천천히 내려옴 (체력 2)
                current_enemy_speed = 2
            elif enemy[2] == 5:
                # 소형 분열 적: dx/dy 벡터로 대각선 이동
                # (인덱스 5, 6에 dx/dy가 저장되어 있음)
                enemy[0] += enemy[5]
                enemy[1] += enemy[6]
                # 화면 밖으로 나가면 제거
                if (enemy[1] > SCREEN_HEIGHT or
                        enemy[0] < -SPLIT_WIDTH or
                        enemy[0] > SCREEN_WIDTH + SPLIT_WIDTH):
                    if enemy in enemies:
                        enemies.remove(enemy)
                continue  # 소형은 별도 이동 처리했으므로 아래 코드 스킵
            else:
                current_enemy_speed = enemy_speed

            enemy[1] += current_enemy_speed

            # 지그재그 적 사인파 비행
            if enemy[2] == 3:
                enemy[0] = enemy[4] + math.sin(enemy[1] * 0.05) * 60
                if enemy[0] < 0:
                    enemy[0] = 0
                elif enemy[0] > SCREEN_WIDTH - enemy_width:
                    enemy[0] = SCREEN_WIDTH - enemy_width

            # 미사일 쏘는 적(type 1) 공격 로직
            if enemy[2] == 1 and random.random() < 0.015:
                enemy_bullets.append([enemy[0] + (enemy_width // 2), enemy[1] + enemy_height, 0, enemy_bullet_speed])

            if enemy[1] > SCREEN_HEIGHT:
                enemies.remove(enemy)

        # 아이템 생성 주기 관리
        if not boss_active:
            item_spawn_counter += 1
            if item_spawn_counter >= 360: 
                item_x = random.randint(0, SCREEN_WIDTH - item_width)
                item_y = -item_height
                itype = 1 if random.random() < 0.3 else 0
                items.append([item_x, item_y, itype])
                item_spawn_counter = 0

        for item in items[:]:
            item[1] += item_speed
            if item[1] > SCREEN_HEIGHT:
                items.remove(item)

        # ── 충돌 검사 1: 플레이어 미사일 vs 적 ────────────────────────────
        for bullet in bullets[:]:
            bullet_rect = pygame.Rect(
                bullet[0] - bullet_radius, bullet[1] - bullet_radius,
                bullet_radius * 2, bullet_radius * 2
            )

            for enemy in enemies[:]:
                # 분열 소형(type 5)은 SPLIT 크기 사용
                if enemy[2] == 5:
                    e_rect = pygame.Rect(enemy[0], enemy[1], SPLIT_WIDTH, SPLIT_HEIGHT)
                else:
                    e_rect = pygame.Rect(enemy[0], enemy[1], enemy_width, enemy_height)

                if bullet_rect.colliderect(e_rect):
                    if bullet in bullets:
                        bullets.remove(bullet)

                    enemy[3] -= 1
                    spawn_particles(bullet[0], bullet[1], WHITE, 4)

                    if enemy[3] <= 0:
                        if enemy in enemies:
                            enemies.remove(enemy)

                        enemy_colors = {0: RED, 1: ORANGE, 2: YELLOW, 3: CYAN, 4: LIME, 5: LIME_DARK}
                        target_color = enemy_colors.get(enemy[2], RED)

                        # 중심 좌표 계산 (대형 vs 소형 크기 분기)
                        if enemy[2] == 5:
                            cx = enemy[0] + SPLIT_WIDTH  // 2
                            cy = enemy[1] + SPLIT_HEIGHT // 2
                        else:
                            cx = enemy[0] + enemy_width  // 2
                            cy = enemy[1] + enemy_height // 2

                        spawn_particles(cx, cy, target_color, 12)

                        # ── 분열 대형(type 4) 처치 → 소형 2마리 스폰 ──────
                        if enemy[2] == 4:
                            spawn_split_enemies(cx, cy)
                            score += 20   # 대형 자체 처치 점수 (소형 각 15점 추가)
                        elif enemy[2] == 5:
                            score += 15   # 분열 소형 처치 점수
                        elif enemy[2] == 2:
                            score += 50
                        elif enemy[2] == 1:
                            score += 20
                        elif enemy[2] == 3:
                            score += 30
                        else:
                            score += 10

                    break  # 한 탄환은 한 적만 맞춤

            # 보스와의 충돌 검사
            if boss_active:
                boss_rect = pygame.Rect(boss_x, boss_y, boss_width, boss_height)
                if bullet_rect.colliderect(boss_rect):
                    if bullet in bullets:
                        bullets.remove(bullet)
                    boss_hp -= 1
                    spawn_particles(bullet[0], bullet[1], WHITE, 4)
                    if boss_hp <= 0:
                        boss_active = False
                        score += 500
                        spawn_particles(boss_x + boss_width // 2, boss_y + boss_height // 2, PURPLE, 40)

        # ── 충돌 검사 2: 플레이어 vs 적 ───────────────────────────────────
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        for enemy in enemies[:]:
            if enemy[2] == 5:
                e_rect = pygame.Rect(enemy[0], enemy[1], SPLIT_WIDTH, SPLIT_HEIGHT)
            else:
                e_rect = pygame.Rect(enemy[0], enemy[1], enemy_width, enemy_height)

            if player_rect.colliderect(e_rect):
                enemies.remove(enemy)
                player_hp -= 1
                spawn_particles(enemy[0] + enemy_width // 2, enemy[1] + enemy_height // 2, RED, 20)
                if player_hp <= 0:
                    game_over = True

        # 플레이어 vs 적 미사일
        for e_bullet in enemy_bullets[:]:
            eb_rect = pygame.Rect(
                e_bullet[0] - enemy_bullet_radius, e_bullet[1] - enemy_bullet_radius,
                enemy_bullet_radius * 2, enemy_bullet_radius * 2
            )
            if player_rect.colliderect(eb_rect):
                enemy_bullets.remove(e_bullet)
                player_hp -= 1
                spawn_particles(player_x + player_width // 2, player_y + player_height // 2, ORANGE, 12)
                if player_hp <= 0:
                    game_over = True

        # 플레이어 vs 보스 본체
        if boss_active:
            boss_rect = pygame.Rect(boss_x, boss_y, boss_width, boss_height)
            if player_rect.colliderect(boss_rect):
                player_hp = 0
                spawn_particles(player_x + player_width // 2, player_y + player_height // 2, PURPLE, 30)
                game_over = True

        # 플레이어 vs 아이템
        for item in items[:]:
            item_rect = pygame.Rect(item[0], item[1], item_width, item_height)
            if player_rect.colliderect(item_rect):
                items.remove(item)
                item_type = item[2] if len(item) > 2 else 0
                if item_type == 1:
                    if player_hp < player_max_hp:
                        player_hp += 1
                    score += 15
                    spawn_particles(item[0] + item_width // 2, item[1] + item_height // 2, HOT_PINK, 15)
                else:
                    triple_shot_active = True
                    triple_shot_start_time = pygame.time.get_ticks()
                    score += 30
                    spawn_particles(item[0] + item_width // 2, item[1] + item_height // 2, GREEN, 15)

    # ── 화면 그리기 ──────────────────────────────────────────────────────
    screen.fill(BLACK)

    # 우주 배경 별
    for star in stars:
        pygame.draw.circle(screen, star[4], (star[0], int(star[1])), star[2])

    # 플레이어
    pygame.draw.rect(screen, BLUE, (player_x, player_y, player_width, player_height))

    # 플레이어 미사일
    for bullet in bullets:
        pygame.draw.circle(screen, YELLOW, (int(bullet[0]), int(bullet[1])), bullet_radius)

    # 적 미사일
    for e_bullet in enemy_bullets:
        pygame.draw.circle(screen, ORANGE, (int(e_bullet[0]), int(e_bullet[1])), enemy_bullet_radius)

    # ── 적 그리기 ────────────────────────────────────────────────────────
    for enemy in enemies:
        ex, ey = int(enemy[0]), int(enemy[1])

        if enemy[2] == 0:
            # 일반: 빨간 네모 (체력 1 → 풀피엔 바 숨김)
            pygame.draw.rect(screen, RED, (ex, ey, enemy_width, enemy_height))
            draw_hp_number(screen, ex, ey, enemy_width, enemy_height, enemy[3], 1)

        elif enemy[2] == 1:
            # 미사일: 주황 네모 (체력 1)
            pygame.draw.rect(screen, ORANGE, (ex, ey, enemy_width, enemy_height))
            draw_hp_number(screen, ex, ey, enemy_width, enemy_height, enemy[3], 1)

        elif enemy[2] == 2:
            # 정예: 노란 네모 (체력 3 → 피격마다 바 변화)
            pygame.draw.rect(screen, YELLOW, (ex, ey, enemy_width, enemy_height))
            draw_hp_number(screen, ex, ey, enemy_width, enemy_height, enemy[3], 3)

        elif enemy[2] == 3:
            # 지그재그: 민트 다이아몬드 (체력 1)
            pts = [
                (ex + enemy_width // 2, ey),
                (ex,                    ey + enemy_height // 2),
                (ex + enemy_width // 2, ey + enemy_height),
                (ex + enemy_width,      ey + enemy_height // 2),
            ]
            pygame.draw.polygon(screen, CYAN, pts)
            draw_hp_number(screen, ex, ey, enemy_width, enemy_height, enemy[3], 1)

        elif enemy[2] == 4:
            # ── 분열 대형: 라임색 육각형 (체력 2) ──────────────────────
            cx = ex + enemy_width  // 2
            cy = ey + enemy_height // 2
            rx, ry = enemy_width // 2, enemy_height // 2
            hex_pts = []
            for i in range(6):
                a = math.radians(60 * i - 30)
                hx = cx + int(rx * math.cos(a))
                hy = cy + int(ry * math.sin(a))
                hex_pts.append((hx, hy))
            pygame.draw.polygon(screen, LIME, hex_pts)
            pygame.draw.polygon(screen, WHITE, hex_pts, 2)
            # 분열 대형은 체력바를 머리 위에 표시
            draw_hp_number(screen, ex, ey, enemy_width, enemy_height, enemy[3], 2)

        elif enemy[2] == 5:
            # ── 분열 소형: 어두운 라임 삼각형 (체력 1) ─────────────────
            pts = [
                (ex + SPLIT_WIDTH // 2, ey + SPLIT_HEIGHT),
                (ex,                    ey),
                (ex + SPLIT_WIDTH,      ey),
            ]
            pygame.draw.polygon(screen, LIME_DARK, pts)
            pygame.draw.polygon(screen, LIME,      pts, 2)
            draw_hp_number(screen, ex, ey, SPLIT_WIDTH, SPLIT_HEIGHT, enemy[3], 1)

    # 보스 그리기
    if boss_active:
        pygame.draw.rect(screen, PURPLE, (boss_x, boss_y, boss_width, boss_height))
        pygame.draw.rect(screen, RED, (boss_x + 20, boss_y + 10, boss_width - 40, boss_height - 20))
        health_bar_width = boss_width
        pygame.draw.rect(screen, RED, (boss_x, boss_y - 12, health_bar_width, 6))
        current_health_bar_width = int((boss_hp / boss_max_hp) * health_bar_width)
        pygame.draw.rect(screen, GREEN, (boss_x, boss_y - 12, current_health_bar_width, 6))

    # 맵 횡단 레이저
    if laser_state == 1:
        if (pygame.time.get_ticks() // 100) % 2 == 0:
            pygame.draw.line(screen, RED, (0, laser_y), (SCREEN_WIDTH, laser_y), 2)
            pygame.draw.line(screen, RED, (laser_x, 0), (laser_x, SCREEN_HEIGHT), 2)
    elif laser_state == 2:
        pygame.draw.rect(screen, RED,   (0, laser_y - 8, SCREEN_WIDTH, 16))
        pygame.draw.rect(screen, WHITE, (0, laser_y - 3, SCREEN_WIDTH, 6))
        pygame.draw.rect(screen, RED,   (laser_x - 8, 0, 16, SCREEN_HEIGHT))
        pygame.draw.rect(screen, WHITE, (laser_x - 3, 0, 6, SCREEN_HEIGHT))

    # 파티클
    for particle in particles:
        radius = int(max(1, (particle['life'] / particle['max_life']) * 5))
        pygame.draw.circle(screen, particle['color'], (int(particle['x']), int(particle['y'])), radius)

    # 아이템
    for item in items:
        item_type = item[2] if len(item) > 2 else 0
        if item_type == 1:
            pygame.draw.rect(screen, HOT_PINK, (item[0] + item_width // 3, item[1], item_width // 3, item_height))
            pygame.draw.rect(screen, HOT_PINK, (item[0], item[1] + item_height // 3, item_width, item_height // 3))
        else:
            point1 = (item[0] + item_width // 2, item[1])
            point2 = (item[0], item[1] + item_height)
            point3 = (item[0] + item_width, item[1] + item_height)
            pygame.draw.polygon(screen, GREEN, [point1, point2, point3])

    # HUD
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    hp_label = font.render("HP: ", True, WHITE)
    screen.blit(hp_label, (SCREEN_WIDTH - 150, 10))
    for i in range(player_max_hp):
        rect_color = GREEN if i < player_hp else BLACK
        pygame.draw.rect(screen, rect_color, (SCREEN_WIDTH - 95 + i * 25, 16, 18, 18))
        pygame.draw.rect(screen, WHITE,      (SCREEN_WIDTH - 95 + i * 25, 16, 18, 18), 2)

    if triple_shot_active:
        remaining_time = max(0, (triple_shot_start_time + triple_shot_duration - current_time) / 1000.0)
        if remaining_time > 0:
            powerup_text = font.render(f"TRIPLE: {remaining_time:.1f}s", True, GREEN)
            screen.blit(powerup_text, (10, 45))

    if game_over:
        over_text    = game_over_font.render("GAME OVER", True, WHITE)
        restart_text = font.render("Press 'R' to Restart", True, WHITE)
        screen.blit(over_text,    (SCREEN_WIDTH // 2 - over_text.get_width()    // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    pygame.display.flip()

pygame.quit()
sys.exit()