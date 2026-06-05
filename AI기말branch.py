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
# - 적 종류(type): 0(일반), 1(미사일), 2(750점 정예 노란네모), 3(지그재그 고속 민트다이아몬드)
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
    # 크기에 따른 속도 설정 (아주 느리게 흘러가도록)
    speed = 0.3 if size == 1 else 0.7
    # 깊이감에 따른 별의 밝기(색상) 설정 (어둡고 은은하게)
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
                    player_hp = player_max_hp # HP 리셋
                    bullets.clear()
                    enemy_bullets.clear() 
                    enemies.clear()
                    items.clear()
                    particles.clear() # 파티클 초기화
                    
                    triple_shot_active = False
                    triple_shot_start_time = 0
                    
                    boss_active = False
                    boss_hp = 0
                    boss_spawned_count = 0 # 보스 카운트 리셋
                    
                    # 레이저 상태 리셋
                    laser_state = 0
                    laser_state_timer = 0
                    laser_spawn_counter = 0
                    laser_x = 0
                    laser_y = 0
                    laser_damaged_player = False
                    
                    score = 0
                    game_over = False
            else:
                if event.key == pygame.K_SPACE:
                    current_time = pygame.time.get_ticks()
                    # Pygame 내장 타이머를 사용한 버프 시간 활성 여부 체크
                    is_triple_active = triple_shot_active and (current_time < triple_shot_start_time + triple_shot_duration)
                    
                    if is_triple_active:
                        bullets.append([player_x + (player_width // 2), player_y, 0, -bullet_speed])
                        angle_rad = math.radians(30)
                        dx_diagonal = bullet_speed * math.sin(angle_rad)
                        dy_diagonal = -bullet_speed * math.cos(angle_rad)
                        bullets.append([player_x + (player_width // 2), player_y, -dx_diagonal, dy_diagonal])
                        bullets.append([player_x + (player_width // 2), player_y, dx_diagonal, dy_diagonal])
                    else:
                        bullets.append([player_x + (player_width // 2), player_y, 0, -bullet_speed])
    # [신규] 우주 배경 별 이동 업데이트 (게임오버 상태에서도 스크롤링 유지)
    for star in stars:
        star[1] += star[3]
        if star[1] > SCREEN_HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, SCREEN_WIDTH)
    # --- 게임 로직 업데이트 ---
    if not game_over:
        # [신규] 점수에 따른 탄환 크기 및 속도 강화 시스템
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
        # [신규] 버프 타이머 업데이트
        current_time = pygame.time.get_ticks()
        if triple_shot_active and current_time >= triple_shot_start_time + triple_shot_duration:
            triple_shot_active = False
            print("Power-up Deactivated!")
        # [신규] 파티클 업데이트
        for particle in particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                particles.remove(particle)
        # [신규] 맵 횡단 레이저 업데이트
        if laser_state == 0:
            laser_spawn_counter += 1
            if laser_spawn_counter >= 450:  # 7.5초 간격으로 출현
                laser_state = 1
                laser_state_timer = 0
                laser_x = random.randint(50, SCREEN_WIDTH - 50)
                laser_y = random.randint(150, SCREEN_HEIGHT - 120)
                laser_damaged_player = False
                laser_spawn_counter = 0
        elif laser_state == 1:
            laser_state_timer += 1
            if laser_state_timer >= 90:  # 1.5초간 경고선 표시
                laser_state = 2
                laser_state_timer = 0
        elif laser_state == 2:
            laser_state_timer += 1
            # 충돌 판정 (플레이어가 피해를 입지 않았을 때 한정)
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
            # 레이저 선상에 빨간 파티클 스파크 가끔 생성
            if random.random() < 0.4:
                spawn_particles(random.randint(0, SCREEN_WIDTH), laser_y, RED, 2)
                spawn_particles(laser_x, random.randint(0, SCREEN_HEIGHT), RED, 2)
            
            if laser_state_timer >= 30:  # 0.5초간 레이저 발사
                laser_state = 0
                laser_state_timer = 0
        # 플레이어 미사일 위치 업데이트
        for bullet in bullets[:]:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]
            if bullet[1] < 0 or bullet[0] < 0 or bullet[0] > SCREEN_WIDTH:
                bullets.remove(bullet)
        # 적 미사일 위치 업데이트 (구조 변경 반영)
        for e_bullet in enemy_bullets[:]:
            e_bullet[0] += e_bullet[2]
            e_bullet[1] += e_bullet[3]
            if e_bullet[1] > SCREEN_HEIGHT or e_bullet[0] < 0 or e_bullet[0] > SCREEN_WIDTH:
                enemy_bullets.remove(e_bullet)
        # [신규] 보스 출현 트리거 검사 (1000점 단위로 등장)
        next_boss_score = 1000 * (boss_spawned_count + 1)
        if score >= next_boss_score and not boss_active:
            boss_active = True
            boss_spawned_count += 1
            boss_hp = boss_max_hp
            boss_x = (SCREEN_WIDTH // 2) - (boss_width // 2)
            boss_y = 50
            boss_direction = 1
            boss_shoot_counter = 0
            # 기존 일반 적과 미사일 제거하여 보스전에 집중
            enemies.clear()
            enemy_bullets.clear()
            print("Boss Spawned!")
        # [신규] 보스 로직 업데이트
        if boss_active:
            boss_x += boss_speed * boss_direction
            if boss_x <= 0:
                boss_x = 0
                boss_direction = 1
            elif boss_x >= SCREEN_WIDTH - boss_width:
                boss_x = SCREEN_WIDTH - boss_width
                boss_direction = -1
            
            # 보스 미사일 발사 (3방향 부채꼴 발사)
            boss_shoot_counter += 1
            if boss_shoot_counter >= 45:  # 약 0.75초 간격
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
                
                # [변경] 지그재그 적(Type 3) 추가된 적 생성 로직
                # 데이터 구조: [x, y, 종류, 체력, 시작 X 좌표]
                if score >= 1250:
                    rand_val = random.random()
                    if rand_val < 0.3:     # 30% 확률 미사일 적
                        enemies.append([enemy_x, enemy_y, 1, 1, enemy_x])
                    elif rand_val < 0.6:   # 30% 확률 정예 노란색 적 (체력 3)
                        enemies.append([enemy_x, enemy_y, 2, 3, enemy_x])
                    elif rand_val < 0.85:  # 25% 확률 지그재그 고속 적
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    else:                  # 15% 확률 일반 적
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                elif score >= 750:
                    rand_val = random.random()
                    if rand_val < 0.3:
                        enemies.append([enemy_x, enemy_y, 1, 1, enemy_x])
                    elif rand_val < 0.55:
                        enemies.append([enemy_x, enemy_y, 2, 3, enemy_x])
                    elif rand_val < 0.8:
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    else:
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                elif score >= 500:
                    rand_val = random.random()
                    if rand_val < 0.35:
                        enemies.append([enemy_x, enemy_y, 1, 1, enemy_x])
                    elif rand_val < 0.65:
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    else:
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                elif score >= 200:
                    # 200점 이상부터 지그재그 고속 적 출현
                    if random.random() < 0.3:
                        enemies.append([enemy_x, enemy_y, 3, 1, enemy_x])
                    else:
                        enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                else:
                    # 200점 미만: 일반 적만 생성
                    enemies.append([enemy_x, enemy_y, 0, 1, enemy_x])
                    
                enemy_spawn_counter = 0
        # 적 위치 업데이트 및 미사일 발사
        for enemy in enemies[:]:
            # 노란색 정예 적(type 2)은 묵직하게 이동 속도를 조금 느리게(2) 해줍니다.
            # 지그재그 고속 적(type 3)은 매우 빠르게(5) 하강합니다.
            if enemy[2] == 2:
                current_enemy_speed = 2
            elif enemy[2] == 3:
                current_enemy_speed = 5
            else:
                current_enemy_speed = enemy_speed
            
            enemy[1] += current_enemy_speed
            
            # [신규] 지그재그 적(Type 3)의 좌우 사인파 비행 패턴
            if enemy[2] == 3:
                enemy[0] = enemy[4] + math.sin(enemy[1] * 0.05) * 60
                # 화면 경계 이탈 방지
                if enemy[0] < 0:
                    enemy[0] = 0
                elif enemy[0] > SCREEN_WIDTH - enemy_width:
                    enemy[0] = SCREEN_WIDTH - enemy_width
            
            # 미사일 쏘는 적(type 1) 공격 로직
            if enemy[2] == 1 and random.random() < 0.015:
                enemy_bullets.append([enemy[0] + (enemy_width // 2), enemy[1] + enemy_height, 0, enemy_bullet_speed])
            if enemy[1] > SCREEN_HEIGHT:
                enemies.remove(enemy)
        # 아이템 생성 주기 관리 (보스 전투 중에는 아이템이 생성되지 않음)
        if not boss_active:
            item_spawn_counter += 1
            if item_spawn_counter >= 360: 
                item_x = random.randint(0, SCREEN_WIDTH - item_width)
                item_y = -item_height
                # 70% 확률로 트리플 샷 (0), 30% 확률로 체력 회복 (1) 아이템 스폰
                itype = 1 if random.random() < 0.3 else 0
                items.append([item_x, item_y, itype])
                item_spawn_counter = 0
        for item in items[:]:
            item[1] += item_speed
            if item[1] > SCREEN_HEIGHT:
                items.remove(item)
        # [중요 변경] 충돌 검사 1: 플레이어 미사일과 적의 충돌 (체력 깎기 및 파티클)
        for bullet in bullets[:]:
            bullet_rect = pygame.Rect(bullet[0] - bullet_radius, bullet[1] - bullet_radius, bullet_radius * 2, bullet_radius * 2)
            
            # 일반 적들과의 충돌 검사
            for enemy in enemies[:]:
                enemy_rect = pygame.Rect(enemy[0], enemy[1], enemy_width, enemy_height)
                if bullet_rect.colliderect(enemy_rect):
                    if bullet in bullets: 
                        bullets.remove(bullet)
                    
                    # 적 체력 1 감소
                    enemy[3] -= 1
                    
                    # 피격 스파크 파티클 생성
                    spawn_particles(bullet[0], bullet[1], WHITE, 4)
                    
                    # 체력이 0 이하가 되면 적을 처치하고 점수 획득
                    if enemy[3] <= 0:
                        if enemy in enemies: 
                            enemies.remove(enemy)
                        
                        # [신규] 적 타입별 폭발 파티클 색상 분기
                        enemy_colors = {0: RED, 1: ORANGE, 2: YELLOW, 3: CYAN}
                        target_color = enemy_colors.get(enemy[2], RED)
                        spawn_particles(enemy[0] + enemy_width // 2, enemy[1] + enemy_height // 2, target_color, 12)
                        
                        # 적 종류별 점수 배정
                        if enemy[2] == 2:
                            score += 50   # 튼튼한 노란 네모는 50점!
                        elif enemy[2] == 1:
                            score += 20   # 미사일 적 20점
                        elif enemy[2] == 3:
                            score += 30   # 지그재그 고속 적 30점
                        else:
                            score += 10   # 일반 적 10점
            # [신규] 보스와의 충돌 검사
            if boss_active:
                boss_rect = pygame.Rect(boss_x, boss_y, boss_width, boss_height)
                if bullet_rect.colliderect(boss_rect):
                    if bullet in bullets:
                        bullets.remove(bullet)
                    
                    boss_hp -= 1
                    # 피격 스파크
                    spawn_particles(bullet[0], bullet[1], WHITE, 4)
                    
                    # 보스 처치
                    if boss_hp <= 0:
                        boss_active = False
                        score += 500
                        # 대규모 폭발 이펙트
                        spawn_particles(boss_x + boss_width // 2, boss_y + boss_height // 2, PURPLE, 40)
                        print("Boss Defeated!")
        # [중요 변경] 충돌 검사 2: 플레이어와 적의 충돌 (체력 깎임 및 파티클)
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        for enemy in enemies[:]:
            enemy_rect = pygame.Rect(enemy[0], enemy[1], enemy_width, enemy_height)
            if player_rect.colliderect(enemy_rect):
                enemies.remove(enemy)
                player_hp -= 1
                spawn_particles(enemy[0] + enemy_width // 2, enemy[1] + enemy_height // 2, RED, 20)
                if player_hp <= 0:
                    game_over = True
        # [중요 변경] 충돌 검사 2-2: 플레이어와 적 미사일의 충돌 (체력 깎임)
        for e_bullet in enemy_bullets[:]:
            eb_rect = pygame.Rect(e_bullet[0] - enemy_bullet_radius, e_bullet[1] - enemy_bullet_radius, enemy_bullet_radius * 2, enemy_bullet_radius * 2)
            if player_rect.colliderect(eb_rect):
                enemy_bullets.remove(e_bullet)
                player_hp -= 1
                spawn_particles(player_x + player_width // 2, player_y + player_height // 2, ORANGE, 12)
                if player_hp <= 0:
                    game_over = True
        # [신규] 충돌 검사 2-3: 플레이어와 보스 본체의 직접 충돌
        if boss_active:
            boss_rect = pygame.Rect(boss_x, boss_y, boss_width, boss_height)
            if player_rect.colliderect(boss_rect):
                player_hp = 0
                spawn_particles(player_x + player_width // 2, player_y + player_height // 2, PURPLE, 30)
                game_over = True
        # 충돌 검사 3: 플레이어와 아이템의 충돌
        for item in items[:]:
            item_rect = pygame.Rect(item[0], item[1], item_width, item_height)
            if player_rect.colliderect(item_rect):
                items.remove(item)
                
                item_type = item[2] if len(item) > 2 else 0
                
                if item_type == 1:
                    # 체력 회복 아이템
                    if player_hp < player_max_hp:
                        player_hp += 1
                        print("Power-up: HP Recovered!")
                    score += 15
                    # 획득 이펙트 (핫핑크)
                    spawn_particles(item[0] + item_width // 2, item[1] + item_height // 2, HOT_PINK, 15)
                else:
                    # 트리플 샷 아이템
                    triple_shot_active = True
                    triple_shot_start_time = pygame.time.get_ticks() # 파워업 시작 시간 기록
                    score += 30
                    # 획득 이펙트 (초록색)
                    spawn_particles(item[0] + item_width // 2, item[1] + item_height // 2, GREEN, 15)
                    print("Power-up Activated: Triple Shot!")
    # --- 화면 그리기 ---
    screen.fill(BLACK)
    
    # [신규] 우주 배경 별 그리기
    for star in stars:
        pygame.draw.circle(screen, star[4], (star[0], int(star[1])), star[2])
    
    # 플레이어
    pygame.draw.rect(screen, BLUE, (player_x, player_y, player_width, player_height))
    # 플레이어 미사일 (노란색)
    for bullet in bullets:
        pygame.draw.circle(screen, YELLOW, (int(bullet[0]), int(bullet[1])), bullet_radius)
    # 적 미사일 그리기 (주황색 원)
    for e_bullet in enemy_bullets:
        pygame.draw.circle(screen, ORANGE, (int(e_bullet[0]), int(e_bullet[1])), enemy_bullet_radius)
    # 적 그리기
    for enemy in enemies:
        # enemy[2] 종류에 따라 색상 분기
        if enemy[2] == 2:
            # 정예 적: 노란색 네모
            pygame.draw.rect(screen, YELLOW, (enemy[0], enemy[1], enemy_width, enemy_height))
        elif enemy[2] == 1:
            # 미사일 적: 주황색 네모
            pygame.draw.rect(screen, ORANGE, (enemy[0], enemy[1], enemy_width, enemy_height))
        elif enemy[2] == 3:
            # [신규] 지그재그 고속 적: 민트색(CYAN) 다이아몬드형
            point1 = (enemy[0] + enemy_width // 2, enemy[1])
            point2 = (enemy[0], enemy[1] + enemy_height // 2)
            point3 = (enemy[0] + enemy_width // 2, enemy[1] + enemy_height)
            point4 = (enemy[0] + enemy_width, enemy[1] + enemy_height // 2)
            pygame.draw.polygon(screen, CYAN, [point1, point2, point3, point4])
        else:
            # 일반 적: 빨간색 네모
            pygame.draw.rect(screen, RED, (enemy[0], enemy[1], enemy_width, enemy_height))
    # [신규] 보스 그리기
    if boss_active:
        pygame.draw.rect(screen, PURPLE, (boss_x, boss_y, boss_width, boss_height))
        pygame.draw.rect(screen, RED, (boss_x + 20, boss_y + 10, boss_width - 40, boss_height - 20)) # 코어
        
        # 보스 체력바
        health_bar_width = boss_width
        pygame.draw.rect(screen, RED, (boss_x, boss_y - 12, health_bar_width, 6))
        current_health_bar_width = int((boss_hp / boss_max_hp) * health_bar_width)
        pygame.draw.rect(screen, GREEN, (boss_x, boss_y - 12, current_health_bar_width, 6))
    # [신규] 맵 횡단 레이저 그리기
    if laser_state == 1:
        # 경고선: 점멸하는 얇은 빨간 선 (수평 & 수직)
        if (pygame.time.get_ticks() // 100) % 2 == 0:
            pygame.draw.line(screen, RED, (0, laser_y), (SCREEN_WIDTH, laser_y), 2)
            pygame.draw.line(screen, RED, (laser_x, 0), (laser_x, SCREEN_HEIGHT), 2)
    elif laser_state == 2:
        # 활성 레이저: 겉은 빨간색 글로우, 속은 흰색 광선 (수평 & 수직)
        # 1. 수평 레이저
        pygame.draw.rect(screen, RED, (0, laser_y - 8, SCREEN_WIDTH, 16))
        pygame.draw.rect(screen, WHITE, (0, laser_y - 3, SCREEN_WIDTH, 6))
        # 2. 수직 레이저
        pygame.draw.rect(screen, RED, (laser_x - 8, 0, 16, SCREEN_HEIGHT))
        pygame.draw.rect(screen, WHITE, (laser_x - 3, 0, 6, SCREEN_HEIGHT))
    # [신규] 파티클 그리기
    for particle in particles:
        # 시간이 지날수록 크기가 작아지며 서서히 사라지는 연출
        radius = int(max(1, (particle['life'] / particle['max_life']) * 5))
        pygame.draw.circle(screen, particle['color'], (int(particle['x']), int(particle['y'])), radius)
    # 아이템 그리기 (트리플 샷: 초록 삼각형, 체력 회복: 빨간 십자가)
    for item in items:
        item_type = item[2] if len(item) > 2 else 0
        if item_type == 1:
            # 체력 회복: 핫핑크 십자가 (+) 모양
            pygame.draw.rect(screen, HOT_PINK, (item[0] + item_width // 3, item[1], item_width // 3, item_height))
            pygame.draw.rect(screen, HOT_PINK, (item[0], item[1] + item_height // 3, item_width, item_height // 3))
        else:
            # 트리플 샷: 초록 삼각형
            point1 = (item[0] + item_width // 2, item[1])
            point2 = (item[0], item[1] + item_height)
            point3 = (item[0] + item_width, item[1] + item_height)
            pygame.draw.polygon(screen, GREEN, [point1, point2, point3])
    # HUD 정보 표시
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    # [신규] 플레이어 체력(HP) 하트 UI 그리기
    hp_label = font.render("HP: ", True, WHITE)
    screen.blit(hp_label, (SCREEN_WIDTH - 150, 10))
    for i in range(player_max_hp):
        rect_color = GREEN if i < player_hp else BLACK
        pygame.draw.rect(screen, rect_color, (SCREEN_WIDTH - 95 + i * 25, 16, 18, 18))
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 95 + i * 25, 16, 18, 18), 2)
    # [신규] 트리플 샷 파워업 상태 남은 시간 표시
    if triple_shot_active:
        remaining_time = max(0, (triple_shot_start_time + triple_shot_duration - current_time) / 1000.0)
        if remaining_time > 0:
            powerup_text = font.render(f"TRIPLE: {remaining_time:.1f}s", True, GREEN)
            screen.blit(powerup_text, (10, 45))
    if game_over:
        over_text = game_over_font.render("GAME OVER", True, WHITE)
        restart_text = font.render("Press 'R' to Restart", True, WHITE)
        screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
    pygame.display.flip()
pygame.quit()
sys.exit()