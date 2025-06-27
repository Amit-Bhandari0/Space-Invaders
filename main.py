import pygame
import random
import math
from pygame import mixer

# Initialize pygame and mixer
pygame.init()

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")
clock = pygame.time.Clock()
FPS = 35

# Colors
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
BG_COLOR = (10, 10, 30)

# Load sounds
mixer.music.load('assets/sounds/background.ogg')
mixer.music.set_volume(0.3)
mixer.music.play(-1)
laser_sound = mixer.Sound('assets/sounds/laser.ogg')
explosion_sound = mixer.Sound('assets/sounds/explosion.ogg')
gameover_sound = mixer.Sound('assets/sounds/gameover.wav')

# Load images
player_img = pygame.image.load('assets/images/spaceship.png')
enemy_img_1 = pygame.image.load('assets/images/alien_1.png')
enemy_img_2 = pygame.image.load('assets/images/alien_2.png')

# Fonts
font = pygame.font.SysFont("consolas", 28)
menu_font = pygame.font.SysFont("arial", 36)
over_font = pygame.font.SysFont("impact", 64)

# Game state flags
menu = True
game_over = False
game_over_played = False
running = True

# Player setup
player_x, player_y = 370, 500
player_speed = 8
player_x_change = 0
player_lives = 3

# Bullet setup
bullets = []
bullet_speed = 10
bullet_cooldown = 400  # ms between shots
last_bullet_time = pygame.time.get_ticks()

# Enemy setup
enemy_speed = 2.5
enemies = []
columns, rows = 10, 5
score = 0

ENEMY_WIDTH, ENEMY_HEIGHT = 32, 32
X_MARGIN, Y_MARGIN = 40, 40
X_SPACING, Y_SPACING = 48, 50

def create_enemies(clear_existing=False):
    if clear_existing:
        enemies.clear()
    for row in range(rows):
        for col in range(columns):
            x = X_MARGIN + col * X_SPACING
            y = Y_MARGIN + row * Y_SPACING
            img_type = enemy_img_1 if (row + col) % 2 == 0 else enemy_img_2
            enemies.append({
                'x': x, 'y': y, 'dx': enemy_speed, 'img': img_type,
                'dead': False, 'falling': False, 'fall_y': 0, 'line_hit': False
            })

def draw_text(text, font, color, x, y):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(x, y))
    screen.blit(surface, rect)

def draw_button(text, x, y, w, h):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    hovered = x < mouse[0] < x + w and y < mouse[1] < y + h
    pygame.draw.rect(screen, (70, 70, 120) if hovered else (40, 40, 90), (x, y, w, h), border_radius=8)
    draw_text(text, menu_font, WHITE, x + w // 2, y + h // 2)
    return hovered and click[0]

def fire_bullet(x, y):
    bullets.append({'x': x + 28, 'y': y + 10})

def is_collision(ex, ey, bx, by):
    return math.hypot(ex - bx, ey - by) < 27

def is_line_collision(px, py, lx, ly):
    return px <= lx <= px + 64 and py <= ly <= py + 64

def reset_game():
    global player_x, player_x_change, player_lives, bullets, score, game_over, game_over_played
    player_x = 370
    player_x_change = 0
    player_lives = 3
    bullets.clear()
    score = 0
    game_over = False
    game_over_played = False
    create_enemies(clear_existing=True)

create_enemies(clear_existing=True)

while running:
    screen.fill(BG_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if menu:
        draw_text("SPACE INVADERS", over_font, WHITE, SCREEN_WIDTH // 2, 150)
        if draw_button("Play", 300, 250, 200, 50):
            menu = False
            reset_game()
        elif draw_button("Quit", 300, 320, 200, 50):
            pygame.quit()
            exit()

    elif game_over:
        draw_text("GAME OVER", over_font, WHITE, SCREEN_WIDTH // 2, 150)
        draw_text(f"Score: {score}", font, WHITE, SCREEN_WIDTH // 2, 220)
        if draw_button("Play Again", 300, 270, 200, 50):
            reset_game()
        elif draw_button("Quit", 300, 340, 200, 50):
            pygame.quit()
            exit()

    else:
        keys = pygame.key.get_pressed()
        player_x_change = (-player_speed if keys[pygame.K_LEFT] else
                           player_speed if keys[pygame.K_RIGHT] else 0)

        current_time = pygame.time.get_ticks()
        if keys[pygame.K_SPACE] and current_time - last_bullet_time > bullet_cooldown:
            laser_sound.play()
            fire_bullet(player_x, player_y)
            last_bullet_time = current_time

        player_x = max(0, min(player_x + player_x_change, SCREEN_WIDTH - 64))
        screen.blit(player_img, (player_x, player_y))

        for enemy in enemies[:]:
            if not enemy['dead']:
                enemy['x'] += enemy['dx']
                if enemy['x'] <= 0 or enemy['x'] >= SCREEN_WIDTH - ENEMY_WIDTH:
                    for e in enemies:
                        if not e['dead']:
                            e['dx'] *= -1
                            e['x'] += e['dx']
                            e['y'] += 20
                screen.blit(enemy['img'], (enemy['x'], enemy['y']))
            elif enemy['falling']:
                lx = enemy['x'] + ENEMY_WIDTH // 2
                ly = enemy['fall_y']
                pygame.draw.line(screen, GRAY, (lx, ly), (lx, ly + 19), 2)  # thin fallen line
                enemy['fall_y'] += 5
                if not enemy['line_hit'] and is_line_collision(player_x, player_y, lx, ly):
                    player_lives -= 1
                    enemy['line_hit'] = True
                    enemy['falling'] = False
                if enemy['fall_y'] > SCREEN_HEIGHT:
                    enemies.remove(enemy)

        for bullet in bullets[:]:
            bullet['y'] -= bullet_speed
            if bullet['y'] < 0:
                bullets.remove(bullet)
            else:
                pygame.draw.rect(screen, YELLOW, (bullet['x'], bullet['y'], 5, 20))
                for enemy in enemies:
                    if not enemy['dead'] and is_collision(enemy['x'], enemy['y'], bullet['x'], bullet['y']):
                        explosion_sound.play()
                        enemy['dead'] = True
                        enemy['falling'] = True
                        enemy['fall_y'] = enemy['y']
                        score += 10
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break

        if player_lives <= 0:
            if not game_over:
                game_over = True
                if not game_over_played:
                    gameover_sound.play()
                    game_over_played = True

        alive_count = len([e for e in enemies if not e['dead']])
        if alive_count <= 10:
            create_enemies(clear_existing=True)

        draw_text(f"Score: {score}", font, WHITE, 80, 20)
        draw_text(f"Lives: {player_lives}", font, WHITE, SCREEN_WIDTH - 100, 20)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
