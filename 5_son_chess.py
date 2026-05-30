import pygame
import sys
import math

BLACK_STONE = 1
WHITE_STONE = 2

pygame.init()

# ---------------------- 全局辅助函数 ----------------------
FONT_NAMES = ['simhei', 'microsoftyahei', 'notosanscjksc', 'fangsong', 'SimHei']
def load_font(size):
    for name in FONT_NAMES:
        try:
            font = pygame.font.SysFont(name, size)
            test = font.render("测", True, (0,0,0))
            if test.get_width() > 0:
                return font
        except:
            continue
    return pygame.font.Font(None, size)

MENU_WINDOW_WIDTH = 2 * 40 + (15 - 1) * 40
MENU_WINDOW_HEIGHT = 2 * 40 + (15 - 1) * 40 + 60


# ---------------------- 菜单界面 ----------------------
class Menu:
    def __init__(self):
        self.screen = pygame.display.set_mode((MENU_WINDOW_WIDTH, MENU_WINDOW_HEIGHT))
        pygame.display.set_caption("五子棋 - 游戏设置")
        self.colors = [("执黑 (先手)", 1), ("执白 (后手)", 2)]
        self.sizes = [("9路   (9×9)", 9), ("13路 (13×13)", 13), ("15路 (15×15)", 15)]
        self.selected_color_idx = 0
        self.selected_size_idx = 2
        self.clock = pygame.time.Clock()
        self.font = load_font(36)
        self.small = load_font(24)

    def run(self):
        while True:
            self.screen.fill((210, 180, 140))
            title = self.font.render("五子棋 - 游戏设置", True, (50,50,50))
            self.screen.blit(title, (40, 60))

            prompt1 = self.small.render("选择你的棋子颜色：", True, (120,120,120))
            self.screen.blit(prompt1, (40, 150))
            for i, (txt, _) in enumerate(self.colors):
                x = 40 + i * 200
                y = 200
                rect = pygame.Rect(x, y, 160, 50)
                bg = (0,100,255) if i == self.selected_color_idx else (200,200,200)
                pygame.draw.rect(self.screen, bg, rect, border_radius=5)
                text = self.small.render(txt, True, (255,255,255) if i == self.selected_color_idx else (0,0,0))
                self.screen.blit(text, (x+10, y+10))

            prompt2 = self.small.render("选择棋盘大小：", True, (120,120,120))
            self.screen.blit(prompt2, (40, 290))
            for i, (txt, _) in enumerate(self.sizes):
                x = 40 + i * 180
                y = 340
                rect = pygame.Rect(x, y, 160, 50)
                bg = (0,100,255) if i == self.selected_size_idx else (200,200,200)
                pygame.draw.rect(self.screen, bg, rect, border_radius=5)
                text = self.small.render(txt, True, (255,255,255) if i == self.selected_size_idx else (0,0,0))
                self.screen.blit(text, (x+10, y+10))

            info = self.small.render("点击选项切换，按 ENTER 或点击下方按钮开始", True, (120,120,120))
            self.screen.blit(info, (40, 440))
            start_rect = pygame.Rect(40, 490, 300, 50)
            pygame.draw.rect(self.screen, (0,150,0), start_rect, border_radius=5)
            start_text = self.font.render("开始游戏", True, (255,255,255))
            self.screen.blit(start_text, (start_rect.x+50, start_rect.y+5))

            pygame.display.flip()
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return self.sizes[self.selected_size_idx][1], self.colors[self.selected_color_idx][1]
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.selected_color_idx = (self.selected_color_idx + 1) % 2
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        self.selected_size_idx = (self.selected_size_idx + 1) % 3
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    for i in range(len(self.colors)):
                        if pygame.Rect(40 + i*200, 200, 160, 50).collidepoint(mx, my):
                            self.selected_color_idx = i
                    for i in range(len(self.sizes)):
                        if pygame.Rect(40 + i*180, 340, 160, 50).collidepoint(mx, my):
                            self.selected_size_idx = i
                    if start_rect.collidepoint(mx, my):
                        return self.sizes[self.selected_size_idx][1], self.colors[self.selected_color_idx][1]


# ---------------------- 游戏核心类 ----------------------
class Gomoku:
    def __init__(self, board_size, player_stone):
        self.board_size = board_size
        self.player_stone = player_stone
        self.ai_stone = WHITE_STONE if player_stone == BLACK_STONE else BLACK_STONE

        self.cell_size = 40
        self.margin = 40
        self.window_width = 2 * self.margin + (self.board_size - 1) * self.cell_size
        self.window_height = 2 * self.margin + (self.board_size - 1) * self.cell_size + 60
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"五子棋 AI - {self.board_size}×{self.board_size}")

        self.font = load_font(36)
        self.small_font = load_font(24)

        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None
        self.current_player = BLACK_STONE
        self.last_move = None
        self.move_history = []
        self.paused = False
        self.back_to_menu_flag = False

        self.player_turn_start_time = 0
        self.show_hint = False
        self.hint_pos = None

        self.pause_buttons = []

        # 底部 UI 元素的 Y 坐标（整体上移 10 像素）
        self.ui_y_baseline = self.window_height - 75   # 状态文字和暂停按钮
        self.hint_y = self.window_height - 25          # 快捷键提示

    def reset(self):
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None
        self.current_player = BLACK_STONE
        self.last_move = None
        self.move_history.clear()
        self.paused = False
        self.back_to_menu_flag = False
        self.player_turn_start_time = 0
        self.show_hint = False
        self.hint_pos = None

    def _do_place(self, row, col):
        self.board[row][col] = self.current_player
        self.move_history.append((row, col, self.current_player))
        self.last_move = (row, col)

    def place_stone(self, row, col):
        if self.game_over or self.paused:
            return False
        if self.board[row][col] != 0 or self.current_player is None:
            return False

        self.board[row][col] = self.current_player
        self.move_history.append((row, col, self.current_player))
        self.last_move = (row, col)
        self.show_hint = False
        self.player_turn_start_time = 0

        if self.check_win(row, col, self.current_player):
            self.game_over = True
            self.winner = self.current_player
            self.current_player = None
            return True
        if self.is_full():
            self.game_over = True
            self.winner = None
            self.current_player = None
            return True
        self.current_player = WHITE_STONE if self.current_player == BLACK_STONE else BLACK_STONE
        return True

    def check_win(self, row, col, player):
        dirs = [(1,0), (0,1), (1,1), (1,-1)]
        size = self.board_size
        for dx, dy in dirs:
            cnt = 1
            for step in range(1, 5):
                r, c = row + dx*step, col + dy*step
                if 0 <= r < size and 0 <= c < size and self.board[r][c] == player:
                    cnt += 1
                else:
                    break
            for step in range(1, 5):
                r, c = row - dx*step, col - dy*step
                if 0 <= r < size and 0 <= c < size and self.board[r][c] == player:
                    cnt += 1
                else:
                    break
            if cnt >= 5:
                return True
        return False

    def is_full(self):
        for row in self.board:
            if 0 in row:
                return False
        return True

    def back_to_menu(self):
        self.back_to_menu_flag = True
        self.paused = False

    # ---------- AI 评估系统 ----------
    PATTERNS = {
        "WIN5": 100000000,
        "ALIVE4": 100000,
        "SLEEP4": 10000,
        "ALIVE3": 5000,
        "SLEEP3": 800,
        "ALIVE2": 200,
        "SLEEP2": 30,
    }

    @staticmethod
    def get_pattern_score(count, left_blocked, right_blocked):
        if count >= 5:
            return Gomoku.PATTERNS["WIN5"]
        if left_blocked and right_blocked:
            return 0
        if count == 4 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE4"]
        if count == 3 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE3"]
        if count == 2 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE2"]
        if count == 4:
            return Gomoku.PATTERNS["SLEEP4"]
        if count == 3:
            return Gomoku.PATTERNS["SLEEP3"]
        if count == 2:
            return Gomoku.PATTERNS["SLEEP2"]
        return 1

    def _count_consecutive(self, row, col, dx, dy, player):
        count = 1
        right_blocked = False
        size = self.board_size
        for step in range(1, 7):
            r, c = row + dx*step, col + dy*step
            if r < 0 or r >= size or c < 0 or c >= size:
                right_blocked = True
                break
            if self.board[r][c] == player:
                count += 1
            else:
                if self.board[r][c] != 0:
                    right_blocked = True
                break
        left_blocked = False
        for step in range(1, 7):
            r, c = row - dx*step, col - dy*step
            if r < 0 or r >= size or c < 0 or c >= size:
                left_blocked = True
                break
            if self.board[r][c] == player:
                count += 1
            else:
                if self.board[r][c] != 0:
                    left_blocked = True
                break
        return count, left_blocked, right_blocked

    def evaluate_position(self, row, col, player):
        if self.board[row][col] != 0:
            return 0
        total = 0
        dirs = [(1,0), (0,1), (1,1), (1,-1)]
        for dx, dy in dirs:
            cnt, lb, rb = self._count_consecutive(row, col, dx, dy, player)
            total += self.get_pattern_score(cnt, lb, rb)
        center = self.board_size // 2
        dist = max(abs(row - center), abs(col - center))
        penalty = 1.0 - 0.09 * dist
        if penalty < 0.1:
            penalty = 0.1
        return total * penalty

    def ai_move(self):
        if self.game_over or self.paused or self.current_player != self.ai_stone:
            return
        best_score = -1
        best_move = None
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board[r][c] == 0:
                    attack = self.evaluate_position(r, c, self.ai_stone)
                    defense = self.evaluate_position(r, c, self.player_stone)
                    total = attack + defense * 0.9
                    if total > best_score:
                        best_score = total
                        best_move = (r, c)
        if best_move:
            self.place_stone(best_move[0], best_move[1])

    # ---------- 提示系统 ----------
    def find_hint(self):
        best_score = -1
        best_move = None
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board[r][c] == 0:
                    score = self.evaluate_position(r, c, self.player_stone)
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
        return best_move

    def ai_play_for_player(self):
        if self.game_over or self.paused or self.current_player != self.player_stone:
            return
        best_move = self.find_hint()
        if best_move:
            self.place_stone(best_move[0], best_move[1])

    # ---------- 悔棋 ----------
    def undo_last_move(self):
        if not self.move_history:
            return
        row, col, player = self.move_history.pop()
        self.board[row][col] = 0
        if self.game_over:
            self.game_over = False
            self.winner = None
        self.current_player = player
        if self.move_history:
            self.last_move = (self.move_history[-1][0], self.move_history[-1][1])
        else:
            self.last_move = None
        self.player_turn_start_time = 0
        self.show_hint = False

    def undo_two_moves(self):
        self.undo_last_move()
        if self.move_history:
            self.undo_last_move()
        self.paused = False

    # ---------- 绘制 ----------
    def get_star_points(self):
        s = self.board_size
        if s == 9:
            return [(4,4)]
        elif s == 13:
            return [(3,3), (9,3), (6,6), (3,9), (9,9)]
        elif s == 15:
            return [(3,3), (11,3), (7,7), (3,11), (11,11)]
        else:
            return [(s//2, s//2)]

    def draw_board(self):
        self.screen.fill((210, 180, 140))
        for i in range(self.board_size):
            start = (self.margin, self.margin + i * self.cell_size)
            end = (self.margin + (self.board_size - 1) * self.cell_size, self.margin + i * self.cell_size)
            pygame.draw.line(self.screen, (0,0,0), start, end, 2)
            start = (self.margin + i * self.cell_size, self.margin)
            end = (self.margin + i * self.cell_size, self.margin + (self.board_size - 1) * self.cell_size)
            pygame.draw.line(self.screen, (0,0,0), start, end, 2)
        for (r, c) in self.get_star_points():
            cx = self.margin + c * self.cell_size
            cy = self.margin + r * self.cell_size
            pygame.draw.circle(self.screen, (0,0,0), (cx, cy), 5)

    def draw_stones(self):
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.board[i][j]
                if stone != 0:
                    x = self.margin + j * self.cell_size
                    y = self.margin + i * self.cell_size
                    color = (0,0,0) if stone == 1 else (255,255,255)
                    pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 2 - 2)
                    if stone == 1:
                        pygame.draw.circle(self.screen, (255,255,255), (x, y), self.cell_size//2-2, 1)
        if self.last_move:
            r, c = self.last_move
            x = self.margin + c * self.cell_size
            y = self.margin + r * self.cell_size
            pygame.draw.circle(self.screen, (255,0,0), (x, y), 6, 2)

    def draw_hint(self):
        if not self.show_hint or self.hint_pos is None:
            return
        r, c = self.hint_pos
        x = self.margin + c * self.cell_size
        y = self.margin + r * self.cell_size
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            hint_surf = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
            pygame.draw.circle(hint_surf, (0, 255, 0, 120),
                               (self.cell_size // 2, self.cell_size // 2), self.cell_size // 2 - 4)
            self.screen.blit(hint_surf, (x - self.cell_size // 2, y - self.cell_size // 2))

    def draw_ui(self):
        # 状态文字（上移后使用 self.ui_y_baseline）
        if self.game_over:
            if self.winner == self.player_stone:
                text = "恭喜！你赢了！"
            elif self.winner == self.ai_stone:
                text = "AI赢了，再来一局？"
            else:
                text = "平局！"
        else:
            text = "你的回合" if self.current_player == self.player_stone else "AI 思考中 ..."
        info_surf = self.font.render(text, True, (50,50,50))
        self.screen.blit(info_surf, (self.margin, self.ui_y_baseline))

        # 快捷键提示（上移后使用 self.hint_y）
        hint_txt = "Q悔棋 | R重开 | A代走 | ESC暂停"
        hint_surf = self.small_font.render(hint_txt, True, (80,80,80))
        self.screen.blit(hint_surf, (self.margin, self.hint_y - 10))

        # 暂停按钮（上移后使用 self.ui_y_baseline）
        btn_text = "暂停" if not self.paused else "继续"
        btn_surf = self.small_font.render(btn_text, True, (50,50,50))
        btn_w = btn_surf.get_width() + 10
        btn_h = btn_surf.get_height() + 6
        btn_x = self.window_width - self.margin - btn_w - 10
        btn_y = self.ui_y_baseline
        self.pause_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (200,200,200), self.pause_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0,0,0), self.pause_rect, 2, border_radius=5)
        self.screen.blit(btn_surf, (btn_x + 5, btn_y + 3))

    def draw_pause_menu(self):
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        menu_w, menu_h = 300, 240
        menu_x = (self.window_width - menu_w) // 2
        menu_y = (self.window_height - menu_h) // 2
        menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        pygame.draw.rect(self.screen, (230,230,230), menu_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0,0,0), menu_rect, 3, border_radius=12)

        self.pause_buttons = [
            ("继续游戏", self._toggle_pause),
            ("悔棋", self.undo_two_moves),
            ("重新开始", self.reset),
            ("返回菜单", self.back_to_menu)
        ]
        for i, (label, action) in enumerate(self.pause_buttons):
            opt_x = menu_x + 50
            opt_y = menu_y + 20 + i * 45
            opt_rect = pygame.Rect(opt_x, opt_y, 200, 35)
            pygame.draw.rect(self.screen, (180,180,180), opt_rect, border_radius=5)
            opt_surf = self.small_font.render(label, True, (0,0,0))
            self.screen.blit(opt_surf, (opt_x + 5, opt_y + 5))
            self.pause_buttons[i] = (opt_rect, action)

    def _toggle_pause(self):
        self.paused = not self.paused

    # ---------- 主循环 ----------
    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._toggle_pause()
                    elif event.key == pygame.K_q:
                        self.undo_two_moves()
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_a:
                        self.ai_play_for_player()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if hasattr(self, 'pause_rect') and self.pause_rect.collidepoint(mx, my):
                        self._toggle_pause()
                    elif self.paused and hasattr(self, 'pause_buttons'):
                        for rect, action in self.pause_buttons:
                            if rect.collidepoint(mx, my):
                                action()
                                break
                    elif not self.game_over and not self.paused and self.current_player == self.player_stone:
                        col = round((mx - self.margin) / self.cell_size)
                        row = round((my - self.margin) / self.cell_size)
                        if 0 <= row < self.board_size and 0 <= col < self.board_size:
                            self.place_stone(row, col)

            if self.back_to_menu_flag:
                return

            if not self.paused and not self.game_over:
                if self.current_player == self.player_stone:
                    if self.player_turn_start_time == 0:
                        self.player_turn_start_time = pygame.time.get_ticks()
                    elif pygame.time.get_ticks() - self.player_turn_start_time > 10000:
                        self.show_hint = True
                        if self.hint_pos is None or (pygame.time.get_ticks() - self.player_turn_start_time) % 2000 < 50:
                            new_hint = self.find_hint()
                            if new_hint:
                                self.hint_pos = new_hint
                else:
                    self.player_turn_start_time = 0
                    self.show_hint = False
                    self.hint_pos = None

            if not self.game_over and not self.paused and self.current_player == self.ai_stone:
                self.ai_move()

            self.draw_board()
            self.draw_stones()
            self.draw_hint()
            self.draw_ui()
            if self.paused:
                self.draw_pause_menu()
            pygame.display.flip()
            clock.tick(30)


# ---------------------- 程序入口 ----------------------
if __name__ == "__main__":
    pygame.display.set_mode((MENU_WINDOW_WIDTH, MENU_WINDOW_HEIGHT))
    while True:
        menu = Menu()
        board_size, player_color = menu.run()
        game = Gomoku(board_size, player_color)
        game.run()
        pygame.display.set_mode((MENU_WINDOW_WIDTH, MENU_WINDOW_HEIGHT))