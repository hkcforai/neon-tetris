#!/usr/bin/env python3
"""
炫彩俄羅斯方塊 - Neon Tetris
大量光子效果 + 粒子系統 + 動態發光
"""

import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
import sys

# ============== 初始化 ==============
pygame.init()

# 螢幕設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
BLOCK_SIZE = 28
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_OFFSET_X = 80
GRID_OFFSET_Y = 60

# 顏色配置 - 霓虹色系
NEON_COLORS = [
    (255, 0, 128),    # 霓虹粉
    (0, 255, 255),    # 青色
    (255, 255, 0),    # 黃色
    (128, 0, 255),    # 紫色
    (0, 255, 128),    # 綠色
    (255, 100, 0),    # 橙色
    (0, 128, 255),    # 藍色
    (255, 0, 64),     # 紅色
]

# 遊戲顏色
BG_COLOR = (10, 10, 20)
GRID_BG_COLOR = (20, 20, 40)
GRID_LINE_COLOR = (40, 40, 80)
TEXT_COLOR = (255, 255, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("✨ 炫彩俄羅斯方塊 ✨")
clock = pygame.time.Clock()

# 字體
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

# ============== 粒子系統 ==============
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: float

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
    
    def emit(self, x: int, y: int, color: Tuple[int, int, int], count: int = 20):
        """發射粒子"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 4)
            self.particles.append(Particle(
                x=x, y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed - 2,
                life=1.0,
                max_life=random.uniform(0.5, 1.5),
                color=color,
                size=random.uniform(2, 6)
            ))
    
    def emit_line_clear(self, y: int, color: Tuple[int, int, int]):
        """消除行時的粒子效果"""
        for x in range(GRID_OFFSET_X, GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE, BLOCK_SIZE):
            self.emit(x + BLOCK_SIZE//2, y + BLOCK_SIZE//2, color, 15)
    
    def update(self, dt: float):
        """更新粒子"""
        for p in self.particles[:]:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.1  # 重力
            p.life -= dt / p.max_life
            if p.life <= 0:
                self.particles.remove(p)
    
    def draw(self, surface: pygame.Surface):
        """繪製粒子"""
        for p in self.particles:
            alpha = int(p.life * 255)
            # 發光效果 - 多層繪製
            for glow in range(3, 0, -1):
                radius = p.size * glow
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color_with_alpha = (*p.color, alpha // glow)
                pygame.draw.circle(surf, color_with_alpha, (radius, radius), radius)
                surface.blit(surf, (p.x - radius, p.y - radius), special_flags=pygame.BLEND_ADD)

# ============== 光暈效果 ==============
def draw_glow_rect(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], intensity: float = 1.0):
    """繪製發光矩形"""
    # 多層光暈
    for i in range(8, 0, -2):
        alpha = int(30 * intensity / (i // 2 + 1))
        glow_rect = rect.inflate(i * 4, i * 4)
        s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=8)
        surface.blit(s, glow_rect.topleft, special_flags=pygame.BLEND_ADD)

def draw_glow_block(surface: pygame.Surface, x: int, y: int, color: Tuple[int, int, int], size: int = BLOCK_SIZE):
    """繪製發光方塊"""
    rect = pygame.Rect(x, y, size, size)
    
    # 外層光暈 - 調小
    for i in range(4, 0, -1):
        alpha = int(20 * (1 - i/5))
        glow_rect = rect.inflate(i, i)
        s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=4)
        surface.blit(s, glow_rect.topleft, special_flags=pygame.BLEND_ADD)
    
    # 主方塊
    pygame.draw.rect(surface, color, rect, border_radius=3)
    
    # 內部高光
    highlight = rect.inflate(-6, -6)
    highlight_color = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surface, highlight_color, highlight, border_radius=2)
    
    # 邊框
    pygame.draw.rect(surface, (*color, 180), rect, 1, border_radius=3)

# ============== 俄羅斯方塊形狀 ==============
SHAPES = [
    # I
    [[1, 1, 1, 1]],
    # O
    [[1, 1], [1, 1]],
    # T
    [[0, 1, 0], [1, 1, 1]],
    # S
    [[0, 1, 1], [1, 1, 0]],
    # Z
    [[1, 1, 0], [0, 1, 1]],
    # J
    [[1, 0, 0], [1, 1, 1]],
    # L
    [[0, 0, 1], [1, 1, 1]],
]

class Tetromino:
    def __init__(self, shape_idx: int):
        self.shape = [row[:] for row in SHAPES[shape_idx]]
        self.color = NEON_COLORS[shape_idx]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
    
    def rotate(self):
        """旋轉方塊"""
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[self.shape[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]
        return rotated
    
    def try_rotate(self, grid) -> bool:
        """嘗試旋轉"""
        rotated = self.rotate()
        original = self.shape
        self.shape = rotated
        if self.check_collision(grid):
            self.shape = original
            return False
        return True
    
    def check_collision(self, grid, offset_x: int = 0, offset_y: int = 0) -> bool:
        """檢查碰撞"""
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.x + x + offset_x
                    new_y = self.y + y + offset_y
                    if new_x < 0 or new_x >= GRID_WIDTH:
                        return True
                    if new_y >= GRID_HEIGHT:
                        return True
                    if new_y >= 0 and grid[new_y][new_x]:
                        return True
        return False

# ============== 遊戲類 ==============
class TetrisGame:
    def __init__(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.particles = ParticleSystem()
        self.drop_timer = 0
        self.drop_speed = 500  # 毫秒
        self.last_drop = pygame.time.get_ticks()
        
        # 動態背景
        self.bg_offset = 0
        self.glow_pulse = 0
        
        self.spawn_piece()
    
    def spawn_piece(self):
        """生成新方塊"""
        if self.next_piece is None:
            self.current_piece = Tetromino(random.randint(0, len(SHAPES) - 1))
        else:
            self.current_piece = self.next_piece
        self.next_piece = Tetromino(random.randint(0, len(SHAPES) - 1))
        
        # 檢查遊戲結束
        if self.current_piece.check_collision(self.grid):
            self.game_over = True
    
    def move(self, dx: int, dy: int) -> bool:
        """移動方塊"""
        if not self.current_piece.check_collision(self.grid, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False
    
    def rotate(self):
        """旋轉方塊"""
        if self.current_piece:
            self.current_piece.try_rotate(self.grid)
    
    def drop(self):
        """下落方塊"""
        if not self.move(0, 1):
            self.lock_piece()
            self.clear_lines()
            self.spawn_piece()
    
    def hard_drop(self):
        """硬下落"""
        drop_distance = 0
        while self.move(0, 1):
            drop_distance += 1
            self.score += drop_distance * 2
        self.particles.emit(
            self.current_piece.x * BLOCK_SIZE + GRID_OFFSET_X,
            self.current_piece.y * BLOCK_SIZE + GRID_OFFSET_Y,
            self.current_piece.color,
            30
        )
        self.lock_piece()
        self.clear_lines()
        self.spawn_piece()
    
    def lock_piece(self):
        """鎖定方塊到網格"""
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = self.current_piece.y + y
                    grid_x = self.current_piece.x + x
                    if 0 <= grid_y < GRID_HEIGHT and 0 <= grid_x < GRID_WIDTH:
                        self.grid[grid_y][grid_x] = self.current_piece.color
        
        # 鎖定粒子效果
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.particles.emit(
                        (self.current_piece.x + x) * BLOCK_SIZE + GRID_OFFSET_X + BLOCK_SIZE//2,
                        (self.current_piece.y + y) * BLOCK_SIZE + GRID_OFFSET_Y + BLOCK_SIZE//2,
                        self.current_piece.color,
                        8
                    )
    
    def clear_lines(self):
        """消除行"""
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(self.grid[y]):
                # 消除動畫 + 粒子
                self.particles.emit_line_clear(
                    y * BLOCK_SIZE + GRID_OFFSET_Y + BLOCK_SIZE//2,
                    (255, 255, 255)
                )
                
                del self.grid[y]
                self.grid.insert(0, [None for _ in range(GRID_WIDTH)])
                lines_cleared += 1
                continue
            y -= 1
        
        if lines_cleared > 0:
            # 計分
            points = [0, 100, 300, 500, 800]
            self.score += points[lines_cleared] * self.level
            self.lines += lines_cleared
            self.level = self.lines // 10 + 1
            self.drop_speed = max(100, 500 - self.level * 30)
    
    def update(self, dt: float):
        """更新遊戲"""
        self.particles.update(dt / 1000)
        self.glow_pulse += dt / 1000 * 2
        
        # 自動下落
        current_time = pygame.time.get_ticks()
        if current_time - self.last_drop > self.drop_speed:
            self.drop()
            self.last_drop = current_time
    
    def draw(self, surface: pygame.Surface):
        """繪製遊戲"""
        # 動態背景
        self.draw_dynamic_bg(surface)
        
        # 遊戲區域背景
        grid_rect = pygame.Rect(
            GRID_OFFSET_X - 5, GRID_OFFSET_Y - 5,
            GRID_WIDTH * BLOCK_SIZE + 10, GRID_HEIGHT * BLOCK_SIZE + 10
        )
        pygame.draw.rect(surface, GRID_BG_COLOR, grid_rect, border_radius=10)
        
        # 網格線
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(surface, GRID_LINE_COLOR,
                (GRID_OFFSET_X + x * BLOCK_SIZE, GRID_OFFSET_Y),
                (GRID_OFFSET_X + x * BLOCK_SIZE, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE))
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(surface, GRID_LINE_COLOR,
                (GRID_OFFSET_X, GRID_OFFSET_Y + y * BLOCK_SIZE),
                (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE, GRID_OFFSET_Y + y * BLOCK_SIZE))
        
        # 已鎖定的方塊
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    draw_glow_block(surface,
                        GRID_OFFSET_X + x * BLOCK_SIZE,
                        GRID_OFFSET_Y + y * BLOCK_SIZE,
                        self.grid[y][x])
        
        # 當前方塊
        if self.current_piece:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        draw_glow_block(surface,
                            GRID_OFFSET_X + (self.current_piece.x + x) * BLOCK_SIZE,
                            GRID_OFFSET_Y + (self.current_piece.y + y) * BLOCK_SIZE,
                            self.current_piece.color)
        
        # 粒子效果
        self.particles.draw(surface)
        
        # 下一個方塊預覽
        self.draw_next_piece(surface)
        
        # UI
        self.draw_ui(surface)
        
        # 遊戲結束 / 暫停
        if self.game_over:
            self.draw_game_over(surface)
        elif self.paused:
            self.draw_paused(surface)
    
    def draw_dynamic_bg(self, surface: pygame.Surface):
        """動態背景"""
        surface.fill(BG_COLOR)
        
        # 漸變網格背景
        self.bg_offset = (self.bg_offset + 0.5) % 40
        
        for i in range(-1, 25):
            y = i * 40 + self.bg_offset
            alpha = int(15 + 10 * math.sin(self.glow_pulse + i * 0.2))
            pygame.draw.line(surface, (30, 30, 60), (0, y), (SCREEN_WIDTH, y))
        
        for i in range(-1, 30):
            x = i * 40 + self.bg_offset
            alpha = int(15 + 10 * math.sin(self.glow_pulse + i * 0.2 + 1))
            pygame.draw.line(surface, (30, 30, 60), (x, 0), (x, SCREEN_HEIGHT))
        
        # 底部發光
        pulse = (math.sin(self.glow_pulse) + 1) / 2
        for i in range(50):
            y = SCREEN_HEIGHT - i * 3
            alpha = int(20 * pulse * (1 - i/50))
            pygame.draw.rect(surface, (*NEON_COLORS[1], alpha), 
                (0, y, SCREEN_WIDTH, 3))
    
    def draw_next_piece(self, surface: pygame.Surface):
        """下一個方塊預覽"""
        preview_x = GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 40
        preview_y = GRID_OFFSET_Y + 50
        
        # 背景
        preview_rect = pygame.Rect(preview_x - 20, preview_y - 20, 150, 120)
        s = pygame.Surface((preview_rect.width, preview_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 20, 40, 200), s.get_rect(), border_radius=10)
        surface.blit(s, preview_rect.topleft)
        
        # 標題
        text = font_small.render("NEXT", True, (150, 150, 150))
        surface.blit(text, (preview_x + 30, preview_y - 15))
        
        # 下一個方塊
        if self.next_piece:
            offset_x = preview_x + 60 - len(self.next_piece.shape[0]) * BLOCK_SIZE // 2
            offset_y = preview_y + 50
            for y, row in enumerate(self.next_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        draw_glow_block(surface,
                            offset_x + x * BLOCK_SIZE,
                            offset_y + y * BLOCK_SIZE,
                            self.next_piece.color,
                            BLOCK_SIZE - 4)
    
    def draw_ui(self, surface: pygame.Surface):
        """UI 顯示"""
        # 分數
        score_text = font_medium.render(f"SCORE", True, (150, 150, 150))
        surface.blit(score_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, 200))

        score_value = font_large.render(str(self.score), True, NEON_COLORS[1])
        surface.blit(score_value, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, 240))

        # 等級
        level_text = font_small.render(f"LEVEL {self.level}", True, NEON_COLORS[3])
        surface.blit(level_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, 350))

        # 行數
        lines_text = font_small.render(f"LINES {self.lines}", True, NEON_COLORS[4])
        surface.blit(lines_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, 390))
        
        # 標題
        title = font_medium.render("TETRIS", True, NEON_COLORS[0])
        glow_title = font_medium.render("TETRIS", True, (*NEON_COLORS[0], 100))
        for i in range(3, 0, -1):
            rect = title.get_rect(x=GRID_OFFSET_X - 10 - i*2, y=GRID_OFFSET_Y - 40 - i*2)
            surface.blit(glow_title, rect)
        surface.blit(title, (GRID_OFFSET_X - 5, GRID_OFFSET_Y - 35))
    
    def draw_game_over(self, surface: pygame.Surface):
        """遊戲結束畫面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        text = font_large.render("GAME OVER", True, NEON_COLORS[6])
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        
        # 發光
        for i in range(5, 0, -1):
            glow = font_large.render("GAME OVER", True, (*NEON_COLORS[6], 50*i))
            glow_rect = glow.get_rect(center=text_rect.center)
            surface.blit(glow, glow_rect)
        
        surface.blit(text, text_rect)
        
        restart = font_small.render("Press R to Restart", True, (200, 200, 200))
        surface.blit(restart, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 30))
    
    def draw_paused(self, surface: pygame.Surface):
        """暫停畫面"""
        text = font_large.render("PAUSED", True, NEON_COLORS[2])
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        for i in range(5, 0, -1):
            glow = font_large.render("PAUSED", True, (*NEON_COLORS[2], 50*i))
            glow_rect = glow.get_rect(center=text_rect.center)
            surface.blit(glow, glow_rect)
        
        surface.blit(text, text_rect)

# ============== 主程式 ==============
def main():
    game = TetrisGame()
    running = True
    
    while running:
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                if not game.game_over and not game.paused:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        game.drop()
                    elif event.key == pygame.K_UP or event.key == pygame.K_x:
                        game.rotate()
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()
                    elif event.key == pygame.K_p:
                        game.paused = not game.paused
                
                if game.game_over:
                    if event.key == pygame.K_r:
                        game = TetrisGame()
                
                if event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
        
        if not game.game_over and not game.paused:
            game.update(dt)
        
        game.draw(screen)
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
