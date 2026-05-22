import pygame
import sys

# 初始化 pygame
pygame.init()

# 屏幕尺寸
BOARD_SIZE = 15          # 15x15 棋盘
CELL_SIZE = 40           # 格子大小（像素）
MARGIN = 40              # 边缘留白
WINDOW_WIDTH = 2 * MARGIN + (BOARD_SIZE - 1) * CELL_SIZE
WINDOW_HEIGHT = 2 * MARGIN + (BOARD_SIZE - 1) * CELL_SIZE + 60

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (120, 120, 120)
BOARD_COLOR = (210, 180, 140)
TEXT_COLOR = (50, 50, 50)

# 棋子类型
EMPTY = 0
BLACK_STONE = 1    # 黑棋（玩家）
WHITE_STONE = 2    # 白棋（AI）

WIN_COUNT = 5

# 初始化屏幕
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("五子棋 AI - 人机对战")

# -------- 修复中文显示问题 --------
# 尝试多个常见中文字体，第一个可用的会被使用
font_names = ['simhei', 'microsoftyahei', 'notosanscjksc', 'fangsong', 'SimHei']
font = None
for name in font_names:
    try:
        font = pygame.font.SysFont(name, 36)
        # 测试一下能否渲染中文
        test_surf = font.render("测", True, (0,0,0))
        if test_surf.get_width() > 0:
            break
    except:
        continue
if font is None:
    # 如果都不行，回退到默认字体（可能还是框，但至少不会崩溃）
    font = pygame.font.Font(None, 36)

small_font = pygame.font.SysFont('simhei', 24) if font else pygame.font.Font(None, 24)

# -----------------------------------------------------------------

class Gomoku:
    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK_STONE
        self.game_over = False
        self.winner = None
        self.last_move = None

    def reset(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK_STONE
        self.game_over = False
        self.winner = None
        self.last_move = None

    def place_stone(self, row, col):
        if not self.game_over and self.board[row][col] == EMPTY and self.current_player is not None:
            self.board[row][col] = self.current_player
            self.last_move = (row, col)
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
            self.current_player = BLACK_STONE if self.current_player == WHITE_STONE else WHITE_STONE
            return True
        return False

    def check_win(self, row, col, player):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            for step in range(1, WIN_COUNT):
                r, c = row + dx * step, col + dy * step
                if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                    break
                if self.board[r][c] == player:
                    count += 1
                else:
                    break
            for step in range(1, WIN_COUNT):
                r, c = row - dx * step, col - dy * step
                if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                    break
                if self.board[r][c] == player:
                    count += 1
                else:
                    break
            if count >= WIN_COUNT:
                return True
        return False

    def is_full(self):
        for row in self.board:
            if EMPTY in row:
                return False
        return True

    PATTERNS = {
        "WIN5": 100000000,
        "ALIVE4": 100000,
        "SLEEP4": 10000,
        "ALIVE3": 5000,
        "SLEEP3": 800,
        "ALIVE2": 200,
        "SLEEP2": 30,
        "OTHER": 1
    }

    @staticmethod
    def get_pattern_score(count, left_blocked, right_blocked):
        if count >= WIN_COUNT:
            return Gomoku.PATTERNS["WIN5"]
        if count == 4 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE4"]
        if count == 4 and (left_blocked or right_blocked):
            return Gomoku.PATTERNS["SLEEP4"]
        if count == 3 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE3"]
        if count == 3 and (left_blocked or right_blocked):
            return Gomoku.PATTERNS["SLEEP3"]
        if count == 2 and not left_blocked and not right_blocked:
            return Gomoku.PATTERNS["ALIVE2"]
        if count == 2 and (left_blocked or right_blocked):
            return Gomoku.PATTERNS["SLEEP2"]
        return 1

    @staticmethod
    def _count_consecutive(board, row, col, dx, dy, player):
        count = 1
        right_blocked = False
        for step in range(1, WIN_COUNT+2):
            r, c = row + dx*step, col + dy*step
            if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                right_blocked = True
                break
            if board[r][c] == player:
                count += 1
            else:
                if board[r][c] != EMPTY:
                    right_blocked = True
                break
        left_blocked = False
        for step in range(1, WIN_COUNT+2):
            r, c = row - dx*step, col - dy*step
            if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                left_blocked = True
                break
            if board[r][c] == player:
                count += 1
            else:
                if board[r][c] != EMPTY:
                    left_blocked = True
                break
        return count, left_blocked, right_blocked

    def evaluate_position(self, row, col, player):
        if self.board[row][col] != EMPTY:
            return 0
        total_score = 0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count, left_blocked, right_blocked = self._count_consecutive(
                self.board, row, col, dx, dy, player
            )
            score = self.get_pattern_score(count, left_blocked, right_blocked)
            total_score += score
        return total_score

    def ai_move(self):
        if self.game_over or self.current_player != WHITE_STONE:
            return
        best_score = -1
        best_move = None
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] == EMPTY:
                    attack = self.evaluate_position(i, j, WHITE_STONE)
                    defense = self.evaluate_position(i, j, BLACK_STONE)
                    total = attack + defense * 0.9
                    if total > best_score:
                        best_score = total
                        best_move = (i, j)
        if best_move:
            self.place_stone(best_move[0], best_move[1])

    def draw_board(self, screen):
        screen.fill(BOARD_COLOR)
        for i in range(BOARD_SIZE):
            start_pos = (MARGIN, MARGIN + i * CELL_SIZE)
            end_pos = (MARGIN + (BOARD_SIZE-1) * CELL_SIZE, MARGIN + i * CELL_SIZE)
            pygame.draw.line(screen, BLACK, start_pos, end_pos, 2)
            start_pos = (MARGIN + i * CELL_SIZE, MARGIN)
            end_pos = (MARGIN + i * CELL_SIZE, MARGIN + (BOARD_SIZE-1) * CELL_SIZE)
            pygame.draw.line(screen, BLACK, start_pos, end_pos, 2)
        star_points = [(3,3), (11,3), (7,7), (3,11), (11,11)] if BOARD_SIZE == 15 else [(7,7)]
        for (x,y) in star_points:
            cx = MARGIN + x * CELL_SIZE
            cy = MARGIN + y * CELL_SIZE
            pygame.draw.circle(screen, BLACK, (cx, cy), 5, 0)

    def draw_stones(self, screen):
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                stone = self.board[i][j]
                if stone != EMPTY:
                    x = MARGIN + j * CELL_SIZE
                    y = MARGIN + i * CELL_SIZE
                    color = BLACK if stone == BLACK_STONE else WHITE
                    pygame.draw.circle(screen, color, (x, y), CELL_SIZE//2 - 2)
                    if color == BLACK:
                        pygame.draw.circle(screen, WHITE, (x, y), CELL_SIZE//2 - 2, 1)
        if self.last_move:
            r, c = self.last_move
            x = MARGIN + c * CELL_SIZE
            y = MARGIN + r * CELL_SIZE
            pygame.draw.circle(screen, (255, 0, 0), (x, y), 6, 2)

    def draw_info(self, screen):
        if self.game_over:
            if self.winner == BLACK_STONE:
                text = "恭喜！你赢了！"
            elif self.winner == WHITE_STONE:
                text = "AI赢了，再来一局？"
            else:
                text = "平局！"
        else:
            text = "你的回合" if self.current_player == BLACK_STONE else "AI 思考中 ..."
        # 使用已经设置好的中文字体
        rendered = font.render(text, True, TEXT_COLOR)
        screen.blit(rendered, (MARGIN, WINDOW_HEIGHT - 52))

        restart_text = small_font.render("按 R 键重新开始", True, DARK_GRAY)
        screen.blit(restart_text, (WINDOW_WIDTH - 225, WINDOW_HEIGHT - 48))

    def run(self):
        clock = pygame.time.Clock()
        self.reset()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and self.current_player == BLACK_STONE:
                    x, y = pygame.mouse.get_pos()
                    col = round((x - MARGIN) / CELL_SIZE)
                    row = round((y - MARGIN) / CELL_SIZE)
                    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                        self.place_stone(row, col)
            if not self.game_over and self.current_player == WHITE_STONE:
                self.ai_move()
            self.draw_board(screen)
            self.draw_stones(screen)
            self.draw_info(screen)
            pygame.display.flip()
            clock.tick(30)


if __name__ == "__main__":
    game = Gomoku()
    game.run()
    