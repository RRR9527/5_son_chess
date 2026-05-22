import pygame
import sys
import math

# 初始化 pygame 所有模块
pygame.init()

# ---------------------- 全局辅助函数 ----------------------
# 尝试加载中文字体，避免显示方框
FONT_NAMES = ['simhei', 'microsoftyahei', 'notosanscjksc', 'fangsong', 'SimHei']
def load_font(size):
    """加载指定大小的中文字体，若失败则返回默认字体（英文）"""
    for name in FONT_NAMES:
        try:
            font = pygame.font.SysFont(name, size)
            # 渲染一个中文字符，检查宽度 >0 表示支持中文
            test = font.render("测", True, (0,0,0))
            if test.get_width() > 0:
                return font
        except:
            continue
    return pygame.font.Font(None, size)          # 回退到默认字体


# ---------------------- 菜单界面（开局设置） ----------------------
class Menu:
    """游戏开始前的设置菜单，选择棋子颜色和棋盘大小"""
    def __init__(self, screen):
        self.screen = screen
        # 颜色选项：(显示文字, 棋子类型常量)  1=黑棋, 2=白棋
        self.colors = [("执黑 (先手)", 1), ("执白 (后手)", 2)]
        # 棋盘大小选项：(显示文字, 尺寸)
        self.sizes = [("9路   (9×9)", 9), ("13路 (13×13)", 13), ("15路 (15×15)", 15)]
        self.selected_color_idx = 0          # 默认选中第一项（执黑）
        self.selected_size_idx = 2           # 默认选中第三项（15路）
        self.clock = pygame.time.Clock()
        self.font = load_font(36)
        self.small = load_font(24)

    def run(self):
        """显示菜单并处理用户输入，返回 (棋盘大小, 玩家棋子颜色)"""
        while True:
            self.screen.fill((210, 180, 140))   # 木色背景
            # 标题
            title = self.font.render("五子棋 - 游戏设置", True, (50,50,50))
            self.screen.blit(title, (40, 60))

            # 颜色选择区域
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

            # 棋盘大小选择区域
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

            # 开始按钮
            info = self.small.render("点击选项切换，按 ENTER 或点击下方按钮开始", True, (120,120,120))
            self.screen.blit(info, (40, 440))
            start_rect = pygame.Rect(40, 490, 300, 50)
            pygame.draw.rect(self.screen, (0,150,0), start_rect, border_radius=5)
            start_text = self.font.render("开始游戏", True, (255,255,255))
            self.screen.blit(start_text, (start_rect.x+50, start_rect.y+5))

            pygame.display.flip()
            self.clock.tick(30)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        return self.sizes[self.selected_size_idx][1], self.colors[self.selected_color_idx][1]
                    # 方向键切换选项
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.selected_color_idx = (self.selected_color_idx + 1) % 2
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        self.selected_size_idx = (self.selected_size_idx + 1) % 3
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    # 检查颜色选项点击
                    for i in range(len(self.colors)):
                        if pygame.Rect(40 + i*200, 200, 160, 50).collidepoint(mx, my):
                            self.selected_color_idx = i
                    # 检查大小选项点击
                    for i in range(len(self.sizes)):
                        if pygame.Rect(40 + i*180, 340, 160, 50).collidepoint(mx, my):
                            self.selected_size_idx = i
                    # 点击开始按钮
                    if start_rect.collidepoint(mx, my):
                        return self.sizes[self.selected_size_idx][1], self.colors[self.selected_color_idx][1]


# ---------------------- 游戏核心类 ----------------------
class Gomoku:
    def __init__(self, screen, board_size, player_stone):
        """
        screen       : pygame 窗口 surface (内部重新创建窗口，故可传 None)
        board_size   : 棋盘大小 (9, 13, 15)
        player_stone : 玩家棋子颜色 (1: 黑, 2: 白)
        """
        self.board_size = board_size
        self.player_stone = player_stone          # 玩家棋子
        self.ai_stone = 2 if player_stone == 1 else 1  # AI 棋子

        # 重新计算窗口尺寸以适应所选棋盘
        self.cell_size = 40
        self.margin = 40
        self.window_width = 2 * self.margin + (self.board_size - 1) * self.cell_size
        self.window_height = 2 * self.margin + (self.board_size - 1) * self.cell_size + 60
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"五子棋 AI - {self.board_size}×{self.board_size}")

        # 加载字体
        self.font = load_font(36)
        self.small_font = load_font(24)

        # 游戏状态
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None
        self.current_player = 1           # 黑棋永远先手
        self.last_move = None
        self.move_history = []            # 记录每一步 (row, col, player)
        self.paused = False               # 是否处于暂停状态

        # ---------- 新增：提示系统变量 ----------
        self.player_turn_start_time = 0   # 当前玩家回合开始的时刻 (pygame ticks)
        self.show_hint = False            # 是否显示提示
        self.hint_pos = None              # 推荐落子位置 (row, col)

        # 如果玩家执白，AI需立即走第一步（黑棋）
        if self.player_stone == 2:
            self._ai_first_move()

    def _ai_first_move(self):
        """AI 执黑先手时自动落子（天元或附近）"""
        c = self.board_size // 2
        # 优先天元，若已被占（不可能）则向右下
        if self.board[c][c] == 0:
            self._do_place(c, c)
        else:
            self._do_place(c, c+1)

    def reset(self):
        """重置棋盘到初始状态，保留颜色和尺寸设置"""
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None
        self.current_player = 1
        self.last_move = None
        self.move_history.clear()
        self.paused = False
        # 重置提示相关变量
        self.player_turn_start_time = 0
        self.show_hint = False
        self.hint_pos = None
        # 若AI执黑则再走第一步
        if self.player_stone == 2:
            self._ai_first_move()

    # ---------- 落子与胜负逻辑 ----------
    def _do_place(self, row, col):
        """内部落子方法，不检查合法性，用于AI先手或历史恢复"""
        self.board[row][col] = self.current_player
        self.move_history.append((row, col, self.current_player))
        self.last_move = (row, col)

    def place_stone(self, row, col):
        """尝试落子，返回是否成功，并更新游戏状态（切换玩家）"""
        if self.game_over or self.paused:
            return False
        if self.board[row][col] != 0 or self.current_player is None:
            return False

        # 执行落子
        self.board[row][col] = self.current_player
        self.move_history.append((row, col, self.current_player))
        self.last_move = (row, col)

        # 玩家落子后立即隐藏提示，并重置计时器（下次轮到玩家会重新计时）
        self.show_hint = False
        self.player_turn_start_time = 0

        # 检查胜利
        if self.check_win(row, col, self.current_player):
            self.game_over = True
            self.winner = self.current_player
            self.current_player = None
            return True
        # 检查平局
        if self.is_full():
            self.game_over = True
            self.winner = None
            self.current_player = None
            return True
        # 切换玩家
        self.current_player = 2 if self.current_player == 1 else 1
        return True

    def check_win(self, row, col, player):
        """检查 player 在 (row,col) 落子后是否达成五连"""
        dirs = [(1,0), (0,1), (1,1), (1,-1)]
        size = self.board_size
        for dx, dy in dirs:
            cnt = 1
            # 正方向
            for step in range(1, 5):
                r, c = row + dx*step, col + dy*step
                if 0 <= r < size and 0 <= c < size and self.board[r][c] == player:
                    cnt += 1
                else:
                    break
            # 负方向
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
        """判断棋盘是否已被占满"""
        for row in self.board:
            if 0 in row:
                return False
        return True

    # ---------- AI 评估系统 (优化版，已防止边角冲四) ----------
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
        """根据连子数与两端封堵情况返回分数，死型直接返回0"""
        if count >= 5:
            return Gomoku.PATTERNS["WIN5"]
        if left_blocked and right_blocked:          # 两端全堵死，无发展空间
            return 0
        # 活型
        if count == 4 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE4"]
        if count == 3 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE3"]
        if count == 2 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE2"]
        # 眠型
        if count == 4:
            return Gomoku.PATTERNS["SLEEP4"]
        if count == 3:
            return Gomoku.PATTERNS["SLEEP3"]
        if count == 2:
            return Gomoku.PATTERNS["SLEEP2"]
        return 1

    def _count_consecutive(self, row, col, dx, dy, player):
        """模拟在 (row,col) 放置 player 棋子后，沿 (dx,dy) 方向的连子数与封堵情况"""
        count = 1
        right_blocked = False
        size = self.board_size
        # 正方向探查（多探两步以便准确判断封堵）
        for step in range(1, 7):
            r, c = row + dx*step, col + dy*step
            if r < 0 or r >= size or c < 0 or c >= size:
                right_blocked = True
                break
            if self.board[r][c] == player:
                count += 1
            else:
                if self.board[r][c] != 0:   # 对方棋子
                    right_blocked = True
                break
        left_blocked = False
        # 负方向探查
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
        """
        评估 player 在 (row,col) 落子的价值 = 四方向棋型分总和 × 位置衰减系数。
        位置衰减：离中心越远，分数越低，避免边角无意义冲棋。
        """
        if self.board[row][col] != 0:
            return 0
        total = 0
        dirs = [(1,0), (0,1), (1,1), (1,-1)]
        for dx, dy in dirs:
            cnt, lb, rb = self._count_consecutive(row, col, dx, dy, player)
            total += self.get_pattern_score(cnt, lb, rb)
        # 位置衰减系数
        center = self.board_size // 2
        dist = max(abs(row - center), abs(col - center))
        penalty = 1.0 - 0.09 * dist
        if penalty < 0.1:
            penalty = 0.1
        return total * penalty

    def ai_move(self):
        """AI 执行一步棋（在轮到 AI 且未暂停/结束时调用）"""
        if self.game_over or self.paused or self.current_player != self.ai_stone:
            return
        best_score = -1
        best_move = None
        # 遍历所有空位
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

    # ---------- 新增：推荐落子位置 (提示系统) ----------
    def find_hint(self):
        """为玩家寻找当前局面的最佳落子位置（基于 ai 评估玩家棋子的得分）"""
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

    # ---------- 悔棋功能 ----------
    def undo_last_move(self):
        """撤销最后一步落子，更新棋盘状态和历史记录"""
        if not self.move_history:
            return
        row, col, player = self.move_history.pop()
        self.board[row][col] = 0                       # 清除棋子
        # 如果之前游戏结束，撤销后应恢复游戏
        if self.game_over:
            self.game_over = False
            self.winner = None
        # 当前玩家恢复为被撤销棋子的颜色
        self.current_player = player
        # 更新最后一步标记
        if self.move_history:
            self.last_move = (self.move_history[-1][0], self.move_history[-1][1])
        else:
            self.last_move = None
        # 撤销后重置提示计时器（避免错误显示）
        self.player_turn_start_time = 0
        self.show_hint = False

    def undo_two_moves(self):
        """
        悔棋至玩家回合：连续撤销两步（若历史足够），保证轮到玩家行棋。
        若历史不足两步，则尽可能撤销。
        """
        self.undo_last_move()
        if self.move_history:
            self.undo_last_move()

    # ---------- 绘制功能 ----------
    def get_star_points(self):
        """根据棋盘大小返回星位坐标列表 (row, col)"""
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
        """绘制棋盘网格与星位"""
        self.screen.fill((210, 180, 140))
        # 画横线
        for i in range(self.board_size):
            start = (self.margin, self.margin + i * self.cell_size)
            end = (self.margin + (self.board_size - 1) * self.cell_size, self.margin + i * self.cell_size)
            pygame.draw.line(self.screen, (0,0,0), start, end, 2)
        # 画竖线
        for i in range(self.board_size):
            start = (self.margin + i * self.cell_size, self.margin)
            end = (self.margin + i * self.cell_size, self.margin + (self.board_size - 1) * self.cell_size)
            pygame.draw.line(self.screen, (0,0,0), start, end, 2)
        # 星位
        for (r, c) in self.get_star_points():
            cx = self.margin + c * self.cell_size
            cy = self.margin + r * self.cell_size
            pygame.draw.circle(self.screen, (0,0,0), (cx, cy), 5)

    def draw_stones(self):
        """绘制所有棋子，并用红圈标记最后一步"""
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.board[i][j]
                if stone != 0:
                    x = self.margin + j * self.cell_size
                    y = self.margin + i * self.cell_size
                    color = (0,0,0) if stone == 1 else (255,255,255)
                    pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 2 - 2)
                    # 黑子外围加白圈增加立体感
                    if stone == 1:
                        pygame.draw.circle(self.screen, (255,255,255), (x, y), self.cell_size//2-2, 1)
        # 红色标记最后一步
        if self.last_move:
            r, c = self.last_move
            x = self.margin + c * self.cell_size
            y = self.margin + r * self.cell_size
            pygame.draw.circle(self.screen, (255,0,0), (x, y), 6, 2)

    def draw_hint(self):
        """
        绘制闪烁的半透明淡绿色推荐光标。
        每 500 毫秒闪烁一次（可见/不可见交替）。
        """
        if not self.show_hint or self.hint_pos is None:
            return
        r, c = self.hint_pos
        x = self.margin + c * self.cell_size
        y = self.margin + r * self.cell_size
        # 闪烁控制：时间除以500，偶数秒可见，奇数秒不可见
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            # 创建带透明通道的小表面，绘制半透明绿色圆
            hint_surf = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
            pygame.draw.circle(hint_surf, (0, 255, 0, 120),       # 淡绿色，alpha=120
                               (self.cell_size // 2, self.cell_size // 2), self.cell_size // 2 - 4)
            self.screen.blit(hint_surf, (x - self.cell_size // 2, y - self.cell_size // 2))

    def draw_ui(self):
        """绘制底部状态栏和暂停按钮"""
        # 状态信息文字
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
        self.screen.blit(info_surf, (self.margin, self.window_height - 50))

        # 暂停按钮（右上角）
        btn_text = "暂停" if not self.paused else "继续"
        btn_surf = self.small_font.render(btn_text, True, (50,50,50))
        btn_w = btn_surf.get_width() + 10
        btn_h = btn_surf.get_height() + 6
        btn_x = self.window_width - self.margin - btn_w - 10
        btn_y = self.window_height - 50
        self.pause_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        # 绘制按钮背景与边框
        pygame.draw.rect(self.screen, (200,200,200), self.pause_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0,0,0), self.pause_rect, 2, border_radius=5)
        self.screen.blit(btn_surf, (btn_x + 5, btn_y + 3))

    def draw_pause_menu(self):
        """绘制暂停时的半透明遮罩及选项菜单"""
        # 半透明遮罩
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # 菜单框
        menu_w, menu_h = 300, 200
        menu_x = (self.window_width - menu_w) // 2
        menu_y = (self.window_height - menu_h) // 2
        menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        pygame.draw.rect(self.screen, (230,230,230), menu_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0,0,0), menu_rect, 3, border_radius=12)

        # 选项按钮：悔棋、重新开始、继续游戏
        options = [
            ("悔棋", self.undo_two_moves),
            ("重新开始", self.reset),
            ("继续游戏", self._toggle_pause)
        ]
        for i, (label, action) in enumerate(options):
            opt_x = menu_x + 50
            opt_y = menu_y + 20 + i * 40
            opt_rect = pygame.Rect(opt_x, opt_y, 200, 35)
            pygame.draw.rect(self.screen, (180,180,180), opt_rect, border_radius=5)
            opt_surf = self.small_font.render(label, True, (0,0,0))
            self.screen.blit(opt_surf, (opt_x + 5, opt_y + 5))
            # 记录按钮位置供点击检测
            setattr(self, f"opt{i}_rect", opt_rect)

    def _toggle_pause(self):
        """切换暂停状态"""
        self.paused = not self.paused

    # ---------- 主循环 ----------
    def run(self):
        clock = pygame.time.Clock()
        while True:
            # ================= 事件处理 =================
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    # ESC 键可作为暂停快捷键
                    if event.key == pygame.K_ESCAPE:
                        self._toggle_pause()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    # 暂停按钮 （任何状态都可点击）
                    if hasattr(self, 'pause_rect') and self.pause_rect.collidepoint(mx, my):
                        self._toggle_pause()
                    # 暂停菜单按钮点击
                    elif self.paused:
                        for i, (label, action) in enumerate([("悔棋", self.undo_two_moves),
                                                              ("重新开始", self.reset),
                                                              ("继续游戏", self._toggle_pause)]):
                            opt_attr = f"opt{i}_rect"
                            if hasattr(self, opt_attr) and getattr(self, opt_attr).collidepoint(mx, my):
                                action()
                                break
                    # 正常落子 (仅玩家回合且未暂停未结束)
                    elif not self.game_over and not self.paused and self.current_player == self.player_stone:
                        col = round((mx - self.margin) / self.cell_size)
                        row = round((my - self.margin) / self.cell_size)
                        if 0 <= row < self.board_size and 0 <= col < self.board_size:
                            self.place_stone(row, col)

            # ================= 提示计时器更新 =================
            if not self.paused and not self.game_over:
                if self.current_player == self.player_stone:
                    # 玩家回合：若首次进入，记录开始时间
                    if self.player_turn_start_time == 0:
                        self.player_turn_start_time = pygame.time.get_ticks()
                    # 超过 10 秒未落子，则计算推荐点位并显示
                    elif pygame.time.get_ticks() - self.player_turn_start_time > 10000:
                        if not self.show_hint:
                            self.show_hint = True
                        # 定期更新推荐点（例如每 2 秒刷新一次，避免性能浪费）
                        if self.hint_pos is None or (pygame.time.get_ticks() - self.player_turn_start_time) % 2000 < 50:
                            new_hint = self.find_hint()
                            if new_hint:
                                self.hint_pos = new_hint
                else:
                    # 非玩家回合（AI回合或游戏结束）：重置提示状态
                    self.player_turn_start_time = 0
                    self.show_hint = False
                    self.hint_pos = None

            # ================= AI 回合 =================
            if not self.game_over and not self.paused and self.current_player == self.ai_stone:
                self.ai_move()

            # ================= 画面绘制 =================
            self.draw_board()
            self.draw_stones()
            self.draw_hint()            # 绘制闪烁的提示光标
            self.draw_ui()
            if self.paused:
                self.draw_pause_menu()
            pygame.display.flip()
            clock.tick(30)


# ---------------------- 程序入口 ----------------------
if __name__ == "__main__":
    # 创建临时窗口供菜单使用（默认15路尺寸）
    temp_screen = pygame.display.set_mode((40*2 + 14*40, 40*2 + 14*40 + 60))
    menu = Menu(temp_screen)
    board_size, player_color = menu.run()      # 获取设置

    # 创建游戏实例并运行（窗口尺寸在 __init__ 中重新调整）
    game = Gomoku(None, board_size, player_color)
    game.run()