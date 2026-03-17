"""
🐍 終極貪吃蛇遊戲 - Ultimate Snake Game
功能：
- 經典貪吃蛇玩法
- 道具系統（加速、減速、無敵、穿牆）
- 障礙物
- 粒子特效
- AI Bot 模式
- 分数排行榜
"""

import pygame
import random
import sys
import math
import json
import os
from datetime import datetime
from enum import Enum

# ============== 配置 ==============
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# 顏色 - 炫彩主題
COLORS = {
    'background': (10, 10, 25),
    'background_grad1': (20, 10, 40),
    'background_grad2': (10, 25, 40),
    'grid': (40, 40, 60),
    'grid_bright': (60, 60, 90),
    'snake_head': (0, 255, 200),
    'snake_body': (0, 220, 150),
    'snake_body_alt': (50, 255, 180),
    'snake_glow': (0, 255, 255),
    'food': (255, 60, 80),
    'food_glow': (255, 255, 100),
    'food_golden': (255, 220, 0),
    'food_speed': (60, 180, 255),
    'food_slow': (255, 160, 60),
    'food_ghost': (220, 120, 255),
    'obstacle': (80, 80, 110),
    'obstacle_glow': (100, 100, 150),
    'text': (255, 255, 255),
    'text_dim': (120, 140, 180),
    'ui_panel': (30, 30, 50),
    'accent': (0, 255, 200),
    'accent_glow': (0, 200, 255),
    'particle1': (0, 255, 200),
    'particle2': (255, 100, 150),
    'particle3': (100, 150, 255),
}

# 方向
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# 食物類型
class FoodType(Enum):
    NORMAL = {'color': COLORS['food'], 'points': 10, 'duration': 0}
    GOLDEN = {'color': COLORS['food_golden'], 'points': 50, 'duration': 0}
    SPEED = {'color': COLORS['food_speed'], 'points': 5, 'duration': 300}
    SLOW = {'color': COLORS['food_slow'], 'points': 5, 'duration': 300}
    GHOST = {'color': COLORS['food_ghost'], 'points': 20, 'duration': 500}

# 粒子系統
class Particle:
    def __init__(self, x, y, color, velocity=None, particle_type='normal'):
        self.x = x
        self.y = y
        self.color = color
        self.life = 30
        self.max_life = 30
        self.particle_type = particle_type
        
        if velocity:
            self.vx, self.vy = velocity
        else:
            if particle_type == 'sparkle':
                self.vx = random.uniform(-1, 1)
                self.vy = random.uniform(-3, -1)  # 向上飄
            elif particle_type == 'trail':
                self.vx = random.uniform(-0.5, 0.5)
                self.vy = random.uniform(-0.5, 0.5)
            else:
                self.vx = random.uniform(-2, 2)
                self.vy = random.uniform(-2, 2)
        
        if particle_type == 'trail':
            self.size = random.randint(4, 8)
        else:
            self.size = random.randint(2, 6)
    
    def update(self):
        if self.particle_type == 'sparkle':
            self.vy -= 0.02  # 逐漸加速向上
        
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(0.5, self.size - 0.15)
    
    def draw(self, surface):
        if self.life > 0:
            ratio = self.life / self.max_life
            
            if self.particle_type == 'trail':
                # 拖尾效果 - 矩形
                alpha = int(180 * ratio)
                s = pygame.Surface((int(self.size), int(self.size)), pygame.SRCALPHA)
                pygame.draw.rect(s, (*self.color, alpha), s.get_rect())
                surface.blit(s, (int(self.x), int(self.y)))
            else:
                # 正常粒子 - 圓形帶發光
                # 外圈發光
                glow_size = int(self.size * 2)
                if glow_size > 0:
                    glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                    alpha = int(50 * ratio)
                    pygame.draw.circle(glow_surf, (*self.color, alpha), (glow_size, glow_size), glow_size)
                    surface.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))
                
                # 核心
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), max(1, int(self.size)))

# 背景星星粒子
class StarParticle:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.uniform(0.5, 2)
        self.speed = random.uniform(0.2, 0.8)
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.twinkle_offset = random.uniform(0, math.pi * 2)
    
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, surface, time_ms):
        # 閃爍效果
        twinkle = math.sin(time_ms * self.twinkle_speed + self.twinkle_offset) * 0.3 + 0.7
        brightness = int(self.brightness * twinkle)
        color = (brightness, brightness, min(brightness + 50, 255))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

# 蛇
class Snake:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.length = 3
        self.score = 0
        self.alive = True
        self.ghost_mode = False
        self.ghost_timer = 0
        self.effect_timer = 0
        self.base_speed = 8  # 每秒移動次數
    
    @property
    def speed(self):
        if self.effect_timer > 0:
            if self.effect_type == 'speed':
                return self.base_speed * 2
            elif self.effect_type == 'slow':
                return self.base_speed // 2
        return self.base_speed
    
    @property
    def effect_type(self):
        return getattr(self, '_effect_type', None)
    
    @effect_type.setter
    def effect_type(self, value):
        self._effect_type = value
    
    def set_direction(self, direction):
        # 防止直接掉頭
        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        if direction != opposite.get(self.direction):
            self.next_direction = direction
    
    def move(self):
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        
        # 穿牆模式
        if self.ghost_mode:
            new_head = (
                new_head[0] % GRID_WIDTH,
                new_head[1] % GRID_HEIGHT
            )
        else:
            # 普通模式邊界檢查
            if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or \
               new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
                self.alive = False
                return
        
        # 撞到自己
        if new_head in self.body[:-1] and not self.ghost_mode:
            self.alive = False
            return
        
        self.body.insert(0, new_head)
        
        # 更新效果計時
        if self.effect_timer > 0:
            self.effect_timer -= 1
            if self.effect_timer <= 0:
                self.effect_type = None
                self.ghost_mode = False
        
        if self.ghost_timer > 0:
            self.ghost_timer -= 1
            if self.ghost_timer <= 0:
                self.ghost_mode = False
        
        # 保持長度
        while len(self.body) > self.length:
            self.body.pop()
    
    def grow(self, amount=1):
        self.length += amount
        self.score += amount * 5
    
    def apply_effect(self, food_type):
        effect_data = food_type.value
        self.effect_type = None
        self.effect_timer = 0
        
        if effect_data['duration'] > 0:
            if food_type == FoodType.SPEED:
                self.effect_type = 'speed'
                self.effect_timer = effect_data['duration']
            elif food_type == FoodType.SLOW:
                self.effect_type = 'slow'
                self.effect_timer = effect_data['duration']
            elif food_type == FoodType.GHOST:
                self.ghost_mode = True
                self.ghost_timer = effect_data['duration']
    
    def draw(self, surface):
        # 蛇身發光效果
        for i, segment in enumerate(self.body):
            x, y = segment
            px, py = x * GRID_SIZE, y * GRID_SIZE
            
            # 漸變顏色
            ratio = i / max(len(self.body), 1)
            if i % 2 == 0:
                color = COLORS['snake_body']
            else:
                color = COLORS['snake_body_alt']
            
            # 頭部特別處理
            if i == 0:
                color = COLORS['snake_head']
                # 無敵/穿牆效果
                if self.ghost_mode:
                    color = COLORS['food_ghost']
                
                # 頭部發光
                glow = pygame.Surface((GRID_SIZE + 12, GRID_SIZE + 12), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*COLORS['snake_glow'], 50), glow.get_rect(), border_radius=8)
                surface.blit(glow, (px - 6, py - 6))
            
            # 身體發光（較弱）
            if i > 0 and i < 5:
                glow = pygame.Surface((GRID_SIZE + 6, GRID_SIZE + 6), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 30), glow.get_rect(), border_radius=6)
                surface.blit(glow, (px - 3, py - 3))
            
            pygame.draw.rect(surface, color, (px + 1, py + 1, GRID_SIZE - 2, GRID_SIZE - 2),
                           border_radius=4)
            
            # 眼睛
            if i == 0:
                eye_size = 4
                dx, dy = self.direction.value
                if dx == 1:  # RIGHT
                    eyes = [(px + 14, py + 6), (px + 14, py + 14)]
                elif dx == -1:  # LEFT
                    eyes = [(px + 6, py + 6), (px + 6, py + 14)]
                elif dy == 1:  # DOWN
                    eyes = [(px + 6, py + 14), (px + 14, py + 14)]
                else:  # UP
                    eyes = [(px + 6, py + 6), (px + 14, py + 6)]
                
                for ex, ey in eyes:
                    pygame.draw.circle(surface, (0, 0, 0), (ex, ey), eye_size)

# 食物
class Food:
    def __init__(self):
        self.position = (0, 0)
        self.type = FoodType.NORMAL
        self.respawn()
    
    def respawn(self):
        self.position = (random.randint(0, GRID_WIDTH - 1),
                        random.randint(0, GRID_HEIGHT - 1))
        
        # 隨機選擇食物類型
        rand = random.random()
        if rand < 0.6:
            self.type = FoodType.NORMAL
        elif rand < 0.75:
            self.type = FoodType.GOLDEN
        elif rand < 0.85:
            self.type = FoodType.SPEED
        elif rand < 0.95:
            self.type = FoodType.SLOW
        else:
            self.type = FoodType.GHOST
    
    def draw(self, surface):
        x, y = self.position
        px, py = x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2
        color = self.type.value['color']
        
        # 閃爍效果
        pulse = math.sin(pygame.time.get_ticks() * 0.01) * 0.2 + 0.8
        
        if self.type == FoodType.GOLDEN:
            # 金色食物發光
            pygame.draw.circle(surface, color, (px, py), int(GRID_SIZE // 2 * pulse))
            pygame.draw.circle(surface, (255, 255, 200), (px, py), int(GRID_SIZE // 3 * pulse))
        elif self.type == FoodType.GHOST:
            # 幽靈效果
            pygame.draw.circle(surface, color, (px, py), int(GRID_SIZE // 2))
            # 半透明效果
            s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, 100), (GRID_SIZE//2, GRID_SIZE//2), GRID_SIZE//2)
            surface.blit(s, (px - GRID_SIZE//2, py - GRID_SIZE//2))
        else:
            pygame.draw.circle(surface, color, (px, py), int(GRID_SIZE // 2 * pulse))

# 障礙物
class Obstacle:
    def __init__(self, count=10, avoid_positions=None):
        self.positions = []
        self.respawn(count, avoid_positions)
    
    def respawn(self, count, avoid_positions=None):
        self.positions = []
        if avoid_positions is None:
            avoid_positions = []
        
        for _ in range(count):
            pos = (random.randint(0, GRID_WIDTH - 1),
                  random.randint(0, GRID_HEIGHT - 1))
            if pos not in avoid_positions and pos not in self.positions:
                self.positions.append(pos)
    
    def check_collision(self, pos):
        return pos in self.positions
    
    def draw(self, surface):
        for x, y in self.positions:
            px, py = x * GRID_SIZE, y * GRID_SIZE
            pygame.draw.rect(surface, COLORS['obstacle'], 
                           (px + 2, py + 2, GRID_SIZE - 4, GRID_SIZE - 4),
                           border_radius=3)

# AI Bot
class AIBot:
    def __init__(self, snake, food, obstacles):
        self.snake = snake
        self.food = food
        self.obstacles = obstacles
    
    def get_best_direction(self):
        head = self.snake.body[0]
        food_pos = self.food.position
        
        # BFS 找最短路徑
        from collections import deque
        
        directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        best_dir = self.snake.direction
        min_distance = float('inf')
        
        for direction in directions:
            dx, dy = direction.value
            next_pos = (head[0] + dx, head[1] + dy)
            
            # 檢查是否有效
            if not self.is_valid_move(next_pos):
                continue
            
            # 計算距離
            dist = abs(next_pos[0] - food_pos[0]) + abs(next_pos[1] - food_pos[1])
            
            if dist < min_distance:
                min_distance = dist
                best_dir = direction
        
        return best_dir
    
    def is_valid_move(self, pos):
        x, y = pos
        
        # 邊界
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            return False
        
        # 障礙物
        if self.obstacles.check_collision(pos):
            return False
        
        # 蛇身（幽靈模式除外）
        if pos in self.snake.body and not self.snake.ghost_mode:
            return False
        
        return True

# 分數排行
class Leaderboard:
    def __init__(self, file_path='snake_leaderboard.json'):
        self.file_path = file_path
        self.scores = self.load()
    
    def load(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.scores, f, indent=2)
    
    def add_score(self, name, score):
        self.scores.append({'name': name, 'score': score, 'date': datetime.now().strftime('%Y-%m-%d %H:%M')})
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        self.scores = self.scores[:10]  # 保留前10
        self.save()
    
    def get_top(self, n=5):
        return self.scores[:n]

# 主遊戲類
class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('🐍 終極貪吃蛇')
        
        # 初始化字体 - 根据操作系统选择合适的字体
        pygame.font.init()
        
        import platform
        system = platform.system()
        
        font_loaded = False
        
        if system == 'Darwin':  # macOS
            font_path = '/System/Library/Fonts/STHeiti Light.ttc'
            if os.path.exists(font_path):
                try:
                    self.font = pygame.font.Font(font_path, 24)
                    self.font_large = pygame.font.Font(font_path, 48)
                    self.font_small = pygame.font.Font(font_path, 18)
                    font_loaded = True
                except:
                    pass
        
        if not font_loaded:
            # Windows 或其他系统 - 尝试多种中文字体
            windows_fonts = ['microsoftyahei', 'simhei', 'simsun', 'pingfang', 'notosanscjk']
            mac_fonts = ['songti', 'applesdgothicneo', 'hiraginosansgb', 'pingfang']
            
            if system == 'Windows':
                font_list = windows_fonts
            else:
                font_list = mac_fonts + windows_fonts
            
            for font_name in font_list:
                try:
                    self.font = pygame.font.SysFont(font_name, 24)
                    self.font_large = pygame.font.SysFont(font_name, 48)
                    self.font_small = pygame.font.SysFont(font_name, 18)
                    # 测试是否能渲染中文
                    test_surf = self.font.render('測試', True, (255, 255, 255))
                    if test_surf.get_buffer().length > 0:
                        font_loaded = True
                        break
                except:
                    continue
        
        if not font_loaded:
            # 最后回退到默认字体
            self.font = pygame.font.Font(None, 24)
            self.font_large = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 18)
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        self.snake = Snake()
        self.food = Food()
        self.obstacles = Obstacle(15)
        self.particles = []
        self.stars = [StarParticle() for _ in range(50)]  # 背景星星
        self.leaderboard = Leaderboard()
        
        self.game_mode = 'menu'  # menu, play, ai, gameover
        self.menu_index = 0  # 菜單當前選中項
        self.ai_bot = AIBot(self.snake, self.food, self.obstacles)
        
        self.player_name = "Player"
        self.move_timer = 0
        self.last_move_time = 0
        
        self.running = True
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if self.game_mode == 'menu':
                    menu_options = ['play', 'ai', 'leaderboard', 'quit']
                    
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.menu_index = (self.menu_index - 1) % 4
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.menu_index = (self.menu_index + 1) % 4
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        selected = menu_options[self.menu_index]
                        if selected == 'play':
                            self.game_mode = 'play'
                            self.reset_game()
                        elif selected == 'ai':
                            self.game_mode = 'ai'
                            self.reset_game()
                        elif selected == 'leaderboard':
                            self.show_leaderboard()
                        elif selected == 'quit':
                            self.running = False
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                
                elif self.game_mode == 'play':
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.snake.set_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.snake.set_direction(Direction.DOWN)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.snake.set_direction(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.snake.set_direction(Direction.RIGHT)
                    elif event.key == pygame.K_ESCAPE:
                        self.game_mode = 'menu'
                    elif event.key == pygame.K_r:
                        self.reset_game()
                
                elif self.game_mode == 'ai':
                    if event.key == pygame.K_ESCAPE:
                        self.game_mode = 'menu'
                    elif event.key == pygame.K_r:
                        self.reset_game()
                
                elif self.game_mode == 'gameover':
                    if event.key == pygame.K_r:
                        if self.game_mode == 'gameover':
                            self.game_mode = 'play'
                            self.reset_game()
                    elif event.key == pygame.K_m:
                        self.game_mode = 'menu'
                    elif event.key == pygame.K_ESCAPE:
                        self.game_mode = 'menu'
    
    def reset_game(self):
        self.snake.reset()
        # 避免障礙物生成在蛇周圍
        avoid = set(self.snake.body)
        for _ in range(5):
            avoid.add(self.food.position)
        self.obstacles.respawn(15, list(avoid))
        self.food.respawn()
        self.particles = []
        self.move_timer = 0
    
    def update(self):
        current_time = pygame.time.get_ticks()
        
        if self.game_mode == 'play' or self.game_mode == 'ai':
            # AI 控制
            if self.game_mode == 'ai':
                best_dir = self.ai_bot.get_best_direction()
                self.snake.set_direction(best_dir)
            
            # 移動計時
            move_interval = 1000 // self.snake.speed
            
            if current_time - self.last_move_time > move_interval:
                self.last_move_time = current_time
                self.snake.move()
                
                # 檢查死亡
                if not self.snake.alive:
                    if self.game_mode == 'play':
                        self.leaderboard.add_score(self.player_name, self.snake.score)
                    self.game_mode = 'gameover'
                    return
                
                # 檢查食物
                if self.snake.body[0] == self.food.position:
                    self.snake.score += self.food.type.value['points']
                    self.snake.grow()
                    self.snake.apply_effect(self.food.type)
                    
                    # 生成粒子效果
                    fx, fy = self.food.position
                    for _ in range(10):
                        self.particles.append(Particle(
                            fx * GRID_SIZE + GRID_SIZE // 2,
                            fy * GRID_SIZE + GRID_SIZE // 2,
                            self.food.type.value['color']
                        ))
                    
                    self.food.respawn()
                
                # 檢查障礙物碰撞（非幽靈模式）
                if not self.snake.ghost_mode and self.obstacles.check_collision(self.snake.body[0]):
                    self.snake.alive = False
                    if self.game_mode == 'play':
                        self.leaderboard.add_score(self.player_name, self.snake.score)
                    self.game_mode = 'gameover'
        
        # 更新粒子
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)
        
        # 更新星星
        for star in self.stars:
            star.update()
    
    def draw_background(self):
        # 漸變背景
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(COLORS['background_grad1'][0] * (1 - ratio) + COLORS['background_grad2'][0] * ratio)
            g = int(COLORS['background_grad1'][1] * (1 - ratio) + COLORS['background_grad2'][1] * ratio)
            b = int(COLORS['background_grad1'][2] * (1 - ratio) + COLORS['background_grad2'][2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 繪製星星
        time_ms = pygame.time.get_ticks()
        for star in self.stars:
            star.draw(self.screen, time_ms)
    
    def draw_grid(self):
        # 漸變效果的網格
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            alpha = 30 + int(20 * math.sin(x * 0.01))
            color = (*COLORS['grid'], alpha) if isinstance(COLORS['grid'], tuple) else (40, 40, 60)
            pygame.draw.line(self.screen, COLORS['grid'], (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, COLORS['grid'], (0, y), (SCREEN_WIDTH, y))
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, COLORS['grid'], (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, COLORS['grid'], (0, y), (SCREEN_WIDTH, y))
    
    def draw_menu(self):
        self.draw_background()
        
        # 標題發光效果
        title = self.font_large.render('貪吃蛇', True, COLORS['accent'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        
        # 發光
        glow_surf = pygame.Surface((title.get_width() + 20, title.get_height() + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*COLORS['accent_glow'], 30), glow_surf.get_rect(), border_radius=10)
        self.screen.blit(glow_surf, (title_rect.x - 10, title_rect.y - 10))
        
        self.screen.blit(title, title_rect)
        
        menu_items = [
            ('單人模式', 'play'),
            ('AI 模式', 'ai'),
            ('排行榜', 'leaderboard'),
            ('退出', 'quit')
        ]
        
        for i, (text, _) in enumerate(menu_items):
            # 選中的項目用不同顏色和箭頭標記
            if i == self.menu_index:
                color = COLORS['accent']
                arrow = '> '
            else:
                color = COLORS['text']
                arrow = '  '
            
            item = self.font.render(arrow + text, True, color)
            rect = item.get_rect(center=(SCREEN_WIDTH // 2, 280 + i * 60))
            self.screen.blit(item, rect)
        
        # 底部提示
        hint = self.font_small.render('使用 ↑↓ 選擇，ENTER 確認', True, COLORS['text_dim'])
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)
    
    def draw_game(self):
        self.draw_background()
        self.draw_grid()
        
        # 繪製障礙物（帶發光）
        for obs in self.obstacles.positions:
            x, y = obs
            px, py = x * GRID_SIZE, y * GRID_SIZE
            # 發光
            glow = pygame.Surface((GRID_SIZE + 8, GRID_SIZE + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*COLORS['obstacle_glow'], 40), glow.get_rect(), border_radius=5)
            self.screen.blit(glow, (px - 4, py - 4))
            pygame.draw.rect(self.screen, COLORS['obstacle'], 
                           (px + 2, py + 2, GRID_SIZE - 4, GRID_SIZE - 4),
                           border_radius=3)
        
        # 繪製食物（帶發光）
        fx, fy = self.food.position
        px, py = fx * GRID_SIZE + GRID_SIZE // 2, fy * GRID_SIZE + GRID_SIZE // 2
        
        # 食物發光
        glow_size = 25
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.food.type.value['color'], 60), (glow_size, glow_size), glow_size)
        self.screen.blit(glow_surf, (px - glow_size, py - glow_size))
        
        self.food.draw(self.screen)
        
        # 繪製蛇（帶發光）
        self.snake.draw(self.screen)
        
        # 繪製粒子
        for particle in self.particles:
            particle.draw(self.screen)
        
        # UI 面板
        ui_y = 10
        
        # 分數
        score_text = self.font.render(f'分數: {self.snake.score}', True, COLORS['text'])
        self.screen.blit(score_text, (20, ui_y))
        
        # 長度
        length_text = self.font.render(f'長度: {self.snake.length}', True, COLORS['text'])
        self.screen.blit(length_text, (20, ui_y + 35))
        
        # 模式指示
        mode_text = 'AI 模式' if self.game_mode == 'ai' else '單人'
        mode = self.font.render(mode_text, True, COLORS['text_dim'])
        self.screen.blit(mode, (SCREEN_WIDTH - 120, ui_y))
        
        # 效果指示
        if self.snake.ghost_mode:
            effect = self.font.render('穿牆', True, COLORS['food_ghost'])
            self.screen.blit(effect, (SCREEN_WIDTH - 120, ui_y + 35))
        elif self.snake.effect_type == 'speed':
            effect = self.font.render('加速', True, COLORS['food_speed'])
            self.screen.blit(effect, (SCREEN_WIDTH - 120, ui_y + 35))
        elif self.snake.effect_type == 'slow':
            effect = self.font.render('減速', True, COLORS['food_slow'])
            self.screen.blit(effect, (SCREEN_WIDTH - 120, ui_y + 35))
        
        # 暫停提示
        pause_text = self.font_small.render('按 ESC 返回菜單 | R 重新開始', True, COLORS['text_dim'])
        self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT - 30))
    
    def draw_gameover(self):
        # 炫彩背景
        self.draw_background()
        
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 遊戲結束 - 白色文字
        gameover = self.font_large.render('遊戲結束', True, (255, 255, 255))
        rect = gameover.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(gameover, rect)
        
        # 分數
        final_score = self.font.render(f'分數: {self.snake.score}', True, COLORS['accent'])
        rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, 260))
        self.screen.blit(final_score, rect)
        
        # 排行榜
        top_scores = self.leaderboard.get_top(5)
        if top_scores:
            leader_title = self.font.render('排行榜', True, COLORS['accent'])
            self.screen.blit(leader_title, (SCREEN_WIDTH // 2 - 40, 320))
            
            for i, entry in enumerate(top_scores):
                text = self.font_small.render(f'{i+1}. {entry["name"]}: {entry["score"]}', True, COLORS['text'])
                self.screen.blit(text, (SCREEN_WIDTH // 2 - 80, 360 + i * 25))
        
        # 提示
        hint = self.font.render('按 R 重新開始  |  M 返回菜單', True, COLORS['text_dim'])
        rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(hint, rect)
    
    def show_leaderboard(self):
        self.draw_background()
        
        # 排行榜發光標題
        title = self.font_large.render('排行榜', True, COLORS['accent'])
        rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        
        # 發光效果
        glow = pygame.Surface((title.get_width() + 20, title.get_height() + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*COLORS['accent_glow'], 40), glow.get_rect(), border_radius=10)
        self.screen.blit(glow, (rect.x - 10, rect.y - 10))
        
        self.screen.blit(title, rect)
        
        top_scores = self.leaderboard.get_top(10)
        if not top_scores:
            no_data = self.font.render('暫無記錄', True, COLORS['text_dim'])
            rect = no_data.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(no_data, rect)
        else:
            for i, entry in enumerate(top_scores):
                color = COLORS['accent'] if i == 0 else COLORS['text']
                text = self.font.render(f'{i+1}. {entry["name"]}: {entry["score"]} ({entry["date"]})', True, color)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, 160 + i * 40))
                self.screen.blit(text, rect)
        
        hint = self.font_small.render('按 ESC 返回', True, COLORS['text_dim'])
        rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint, rect)
        
        pygame.display.flip()
        
        # 等待返回
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        waiting = False
    
    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            
            if self.game_mode == 'menu':
                self.draw_menu()
            elif self.game_mode == 'play' or self.game_mode == 'ai':
                self.draw_game()
            elif self.game_mode == 'gameover':
                self.draw_game()
                self.draw_gameover()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# 啟動遊戲
if __name__ == '__main__':
    game = SnakeGame()
    game.run()
