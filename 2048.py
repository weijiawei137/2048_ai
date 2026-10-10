import json
import os
import random
import sys

try:
    import pygame
except ImportError:
    print("Pygame is not installed. Please install it by running: pip install pygame")
    sys.exit()

# Constants
GRID_SIZE = 4
CELL_SIZE = 100
MARGIN = 20
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + (MARGIN * 2) + 100
WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + (MARGIN * 2) + 176
BACKGROUND_COLOR = (187, 173, 160)
CELL_COLORS = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 202),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 93, 59),
    128: (237, 207, 114),
    256: (237, 204, 94),
    512: (237, 200, 80),
    1024: (237, 188, 66),
    2048: (237, 174, 45),
}
TEXT_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT_SIZE = 40
SMALL_FONT_SIZE = 24
SCORE_FILE = "highest_score.json"
TILE_ANIMATION_DURATION = 160


def get_chinese_font_path():
    candidate_paths = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simkai.ttf",
        r"C:\Windows\Fonts\msjhl.ttc",
        r"C:\Windows\Fonts\wryh.ttf",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None


class Game2048:
    def __init__(self):
        pygame.display.init()
        pygame.font.init()

        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.highest_score = self.load_highest_score()
        self.highest_tile = self.load_highest_tile()
        self.game_over = False
        self.win = False

        font_path = get_chinese_font_path()
        self.font = pygame.font.Font(font_path, FONT_SIZE) if font_path else pygame.font.SysFont(None, FONT_SIZE)
        self.small_font = pygame.font.Font(font_path, SMALL_FONT_SIZE) if font_path else pygame.font.SysFont(None, SMALL_FONT_SIZE)

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("2048 Game")
        self.start_button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 25, 200, 60)
        self.mouse_down_pos = None
        self.tile_animation = None
        self.tile_animation_started = 0
        self.text_cache = {}
        self.tile_surface_cache = {}
        self.board_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.board_surface.fill(BACKGROUND_COLOR)
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                pygame.draw.rect(
                    self.board_surface,
                    CELL_COLORS[0],
                    self.tile_rect(row, col),
                    border_radius=5,
                )
        self.overlay_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.overlay_surface.fill((0, 0, 0, 128))
        self.menu_title = self.cached_text(self.font, "欢迎来到 2048", WHITE)
        self.start_button_text = self.cached_text(self.small_font, "开始游戏", WHITE)
        self.game_over_text = self.cached_text(self.font, "游戏结束！按 R 重新开始", WHITE)
        self.win_text = self.cached_text(self.font, "你赢了！按 R 重新开始", WHITE)
        self.instructions = [
            self.cached_text(self.small_font, "方向键 / 鼠标拖动：移动", WHITE),
            self.cached_text(self.small_font, "R：重新开始    Q：退出", WHITE),
        ]
        self.tile_rects = [
            [self.tile_rect(row, col) for col in range(GRID_SIZE)]
            for row in range(GRID_SIZE)
        ]
        self.reset_game()

    def load_highest_score(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("highest_score", 0)
            except (OSError, ValueError):
                return 0
        return 0

    def load_highest_tile(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("highest_tile", 0)
            except (OSError, ValueError):
                return 0
        return 0

    def save_highest_score(self):
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "highest_score": self.highest_score,
                    "highest_tile": self.highest_tile,
                },
                f,
            )

    def spawn_new_tile(self):
        empty_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if self.grid[r][c] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4
            self.highest_tile = max(self.highest_tile, self.grid[r][c])

    def move_left(self):
        new_grid = []
        score_gain = 0

        for row in self.grid:
            values = [value for value in row if value != 0]
            merged = []
            i = 0

            while i < len(values):
                if i + 1 < len(values) and values[i] == values[i + 1]:
                    merged_value = values[i] * 2
                    merged.append(merged_value)
                    score_gain += merged_value
                    i += 2
                else:
                    merged.append(values[i])
                    i += 1

            merged.extend([0] * (GRID_SIZE - len(merged)))
            new_grid.append(merged)

        if new_grid != self.grid:
            self.grid = new_grid
            self.score += score_gain

    def move_right(self):
        for row in self.grid:
            row.reverse()
        self.move_left()
        for row in self.grid:
            row.reverse()

    def move_up(self):
        self.grid = [list(row) for row in zip(*self.grid)]
        self.move_left()
        self.grid = [list(row) for row in zip(*self.grid)]

    def move_down(self):
        self.grid = [list(row) for row in zip(*self.grid)]
        self.grid = [list(reversed(row)) for row in self.grid]
        self.move_left()
        self.grid = [list(reversed(row)) for row in self.grid]
        self.grid = [list(row) for row in zip(*self.grid)]

    def is_game_over(self):
        if any(0 in row for row in self.grid):
            return False
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE - 1):
                if self.grid[row][col] == self.grid[row][col + 1]:
                    return False
        for row in range(GRID_SIZE - 1):
            for col in range(GRID_SIZE):
                if self.grid[row][col] == self.grid[row + 1][col]:
                    return False
        return True

    def check_win(self):
        return any(2048 in row for row in self.grid)

    def reset_game(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.win = False
        self.tile_animation = None
        self.spawn_new_tile()
        self.spawn_new_tile()

    def tile_rect(self, row, col):
        return pygame.Rect(
            col * CELL_SIZE + MARGIN,
            row * CELL_SIZE + MARGIN + 56,
            CELL_SIZE,
            CELL_SIZE,
        )

    def cached_text(self, font, text, color):
        key = (id(font), text, color)
        if key not in self.text_cache:
            if len(self.text_cache) >= 128:
                self.text_cache.pop(next(iter(self.text_cache)))
            self.text_cache[key] = font.render(text, True, color)
        return self.text_cache[key]

    def tile_surface(self, value):
        if value not in self.tile_surface_cache:
            tile = pygame.Surface((CELL_SIZE, CELL_SIZE))
            color = CELL_COLORS.get(value, (60, 50, 40))
            pygame.draw.rect(tile, color, tile.get_rect(), border_radius=5)
            text_color = BLACK if value < 8 else WHITE
            number_text = self.cached_text(self.font, str(value), text_color)
            tile.blit(number_text, number_text.get_rect(center=(CELL_SIZE // 2, CELL_SIZE // 2)))
            self.tile_surface_cache[value] = tile
        return self.tile_surface_cache[value]

    def render_tile(self, value, center, scale=1.0, alpha=255):
        size = max(1, round(CELL_SIZE * scale))
        tile = self.tile_surface(value)
        if size != CELL_SIZE:
            tile = pygame.transform.smoothscale(tile, (size, size))
        if alpha != 255:
            tile = tile.copy()
            tile.set_alpha(alpha)
        self.screen.blit(tile, tile.get_rect(center=center))

    def create_tile_animation(self, old_grid, direction):
        records = []
        destinations = set()

        for line_index in range(GRID_SIZE):
            if direction == pygame.K_LEFT:
                positions = [(line_index, col) for col in range(GRID_SIZE)]
            elif direction == pygame.K_RIGHT:
                positions = [(line_index, col) for col in range(GRID_SIZE - 1, -1, -1)]
            elif direction == pygame.K_UP:
                positions = [(row, line_index) for row in range(GRID_SIZE)]
            else:
                positions = [(row, line_index) for row in range(GRID_SIZE - 1, -1, -1)]

            tiles = [(old_grid[row][col], (row, col)) for row, col in positions if old_grid[row][col]]
            groups = []
            index = 0
            while index < len(tiles):
                value, source = tiles[index]
                if index + 1 < len(tiles) and tiles[index + 1][0] == value:
                    groups.append((value * 2, [source, tiles[index + 1][1]]))
                    index += 2
                else:
                    groups.append((value, [source]))
                    index += 1

            for index, (result_value, sources) in enumerate(groups):
                destination = positions[index]
                if len(sources) == 1 and sources[0] == destination:
                    continue
                destinations.add(destination)
                for source in sources:
                    records.append(
                        {
                            "value": old_grid[source[0]][source[1]],
                            "start": source,
                            "end": destination,
                            "merged_value": result_value if len(sources) == 2 else None,
                        }
                    )

        return records, destinations

    def perform_move(self, direction):
        if self.tile_animation is not None or self.game_over or self.win:
            return

        old_grid = [row[:] for row in self.grid]
        move = {
            pygame.K_LEFT: self.move_left,
            pygame.K_RIGHT: self.move_right,
            pygame.K_UP: self.move_up,
            pygame.K_DOWN: self.move_down,
        }.get(direction)
        if move is None:
            return

        move()
        if self.grid == old_grid:
            return
        self.highest_tile = max(self.highest_tile, max(max(row) for row in self.grid))

        records, destinations = self.create_tile_animation(old_grid, direction)
        moved_grid = [row[:] for row in self.grid]
        self.spawn_new_tile()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if moved_grid[row][col] == 0 and self.grid[row][col] != 0:
                    records.append(
                        {
                            "value": self.grid[row][col],
                            "start": (row, col),
                            "end": (row, col),
                            "merged_value": None,
                            "spawn": True,
                        }
                    )
                    destinations.add((row, col))
                    break
            else:
                continue
            break

        self.tile_animation = {"records": records, "destinations": destinations}
        self.tile_animation_started = pygame.time.get_ticks()
        self.check_state()

    def draw(self):
        self.screen.blit(self.board_surface, (0, 0))
        title_text = self.cached_text(self.small_font, "2048 游戏", WHITE)
        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 10))

        score_text = self.cached_text(self.small_font, f"分数: {self.score}", WHITE)
        self.screen.blit(score_text, (10, 10))

        high_score_text = self.cached_text(self.small_font, f"最高分: {self.highest_score}", WHITE)
        self.screen.blit(high_score_text, (WINDOW_WIDTH - high_score_text.get_width() - 10, 10))

        highest_tile_text = self.cached_text(self.small_font, f"历史最高方块: {self.highest_tile}", WHITE)
        self.screen.blit(highest_tile_text, (10, 36))

        for i, instruction_text in enumerate(self.instructions):
            self.screen.blit(instruction_text, (10, WINDOW_HEIGHT - 68 + i * 34))

        progress = None
        if self.tile_animation is not None:
            elapsed = pygame.time.get_ticks() - self.tile_animation_started
            progress = min(1.0, elapsed / TILE_ANIMATION_DURATION)
            if progress >= 1.0:
                self.tile_animation = None
                progress = None

        animated_destinations = self.tile_animation["destinations"] if progress is not None else set()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                value = self.grid[row][col]
                if value and (row, col) not in animated_destinations:
                    self.render_tile(value, self.tile_rects[row][col].center)

        if progress is not None:
            eased = 1 - (1 - progress) ** 3
            for record in self.tile_animation["records"]:
                start_row, start_col = record["start"]
                end_row, end_col = record["end"]
                start = self.tile_rects[start_row][start_col].center
                end = self.tile_rects[end_row][end_col].center

                if record.get("spawn"):
                    scale = 0.35 + 0.65 * eased
                    self.render_tile(record["value"], end, scale, round(255 * eased))
                elif record["merged_value"] is not None:
                    merge_progress = max(0.0, min(1.0, progress / 0.78))
                    x = round(start[0] + (end[0] - start[0]) * (1 - (1 - merge_progress) ** 3))
                    y = round(start[1] + (end[1] - start[1]) * (1 - (1 - merge_progress) ** 3))
                    scale = 1.0 - 0.35 * max(0.0, (progress - 0.55) / 0.45)
                    alpha = round(255 * max(0.0, 1.0 - (progress - 0.55) / 0.4))
                    self.render_tile(record["value"], (x, y), scale, alpha)
                else:
                    x = round(start[0] + (end[0] - start[0]) * eased)
                    y = round(start[1] + (end[1] - start[1]) * eased)
                    self.render_tile(record["value"], (x, y))

            for row, col in animated_destinations:
                value = self.grid[row][col]
                merge_records = [
                    record for record in self.tile_animation["records"]
                    if record["end"] == (row, col) and record["merged_value"] is not None
                ]
                if merge_records and progress >= 0.68:
                    pop_progress = min(1.0, (progress - 0.68) / 0.32)
                    scale = 0.65 + 0.35 * (1 - (1 - pop_progress) ** 3)
                    self.render_tile(value, self.tile_rects[row][col].center, scale)

        if self.game_over:
            self.screen.blit(self.overlay_surface, (0, 0))
            self.screen.blit(
                self.game_over_text,
                (WINDOW_WIDTH // 2 - self.game_over_text.get_width() // 2, WINDOW_HEIGHT // 2 - 20),
            )

        if self.win:
            self.screen.blit(self.overlay_surface, (0, 0))
            self.screen.blit(
                self.win_text,
                (WINDOW_WIDTH // 2 - self.win_text.get_width() // 2, WINDOW_HEIGHT // 2 - 20),
            )

    def handle_key(self, key):
        if self.game_over or self.win:
            if key == pygame.K_r:
                self.reset_game()
            elif key == pygame.K_q:
                self.save_highest_score()
                pygame.quit()
                sys.exit()
            return

        if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            self.perform_move(key)
        elif key == pygame.K_r:
            self.reset_game()
        elif key == pygame.K_q:
            self.save_highest_score()
            pygame.quit()
            sys.exit()

    def handle_mouse_swipe(self, start_pos, end_pos):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        if max(abs(dx), abs(dy)) < 30:
            return

        if abs(dx) > abs(dy):
            key = pygame.K_RIGHT if dx > 0 else pygame.K_LEFT
        else:
            key = pygame.K_DOWN if dy > 0 else pygame.K_UP
        self.handle_key(key)

    def check_state(self):
        if self.check_win():
            self.win = True
        if self.score > self.highest_score:
            self.highest_score = self.score
        if self.is_game_over():
            self.game_over = True

    def run(self):
        clock = pygame.time.Clock()
        running = True
        show_menu = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_highest_score()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if not show_menu:
                        self.handle_key(event.key)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if show_menu:
                        if self.start_button_rect.collidepoint(event.pos):
                            show_menu = False
                    else:
                        self.mouse_down_pos = event.pos
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not show_menu:
                    if self.mouse_down_pos is not None:
                        self.handle_mouse_swipe(self.mouse_down_pos, event.pos)
                    self.mouse_down_pos = None

            self.draw()
            if show_menu:
                self.screen.blit(self.overlay_surface, (0, 0))
                pygame.draw.rect(self.screen, (143, 122, 102), self.start_button_rect, border_radius=8)
                self.screen.blit(
                    self.menu_title,
                    (WINDOW_WIDTH // 2 - self.menu_title.get_width() // 2, WINDOW_HEIGHT // 2 - 75),
                )
                self.screen.blit(
                    self.start_button_text,
                    (
                        self.start_button_rect.centerx - self.start_button_text.get_width() // 2,
                        self.start_button_rect.centery - self.start_button_text.get_height() // 2,
                    ),
                )

            pygame.display.flip()
            clock.tick(60 if self.tile_animation is not None else 20)

        self.save_highest_score()
        pygame.quit()


if __name__ == "__main__":
    game = Game2048()
    game.run()
