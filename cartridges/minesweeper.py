from enum import Enum
from random import sample
from typing import Callable, Final, NamedTuple

from engine import Ansi, Colour, Game, MouseButton, Screen


class State(Enum):
    PLAYING = 0
    GAME_OVER = 1
    WON = 2

class Difficulty(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2

class Actions(Enum):
    RESET = 0
    REVEAL = 1
    FLAG = 2
    DIFFICULTY_UP = 3
    DIFFICULTY_DOWN = 4

class Vector2(NamedTuple):
    X: int
    Y: int

class Colours(NamedTuple):
    FG: Colour = Colour()
    BG: Colour = Colour()
    UL: Colour = Colour()

class Layout(NamedTuple):
    left: int
    top: int
    frame_w: int
    board_left: int
    board_top: int
    board_w: int

KEYBINDS: Final[dict[str, Actions]] = {
    "r": Actions.RESET,
    " ": Actions.REVEAL,
    "f": Actions.FLAG,
    "+": Actions.DIFFICULTY_UP,
    "-": Actions.DIFFICULTY_DOWN
}
CHARSET: Final[dict[str, str]] = {
    "FLAG": "#",
    "MINE": "*",
    "OPEN": " ",
    "HIDDEN": "o",
}
COLOURSET: Final[dict[str, Colours]] = {
    "CELL":   Colours(FG=Colour(128, 128, 128), BG=Colour(192, 192, 192, bg=True), UL=Colour(128, 128, 128, ul=True)),
    "SMILEY": Colours(FG=Colour(0, 0, 0), BG=Colour(255, 255, 0, bg=True)),
    "7-SEG":  Colours(FG=Colour(255, 0, 0), BG=Colour(0, 0, 0, bg=True)),
    "FAIL-MINE": Colours(FG=Colour(0, 0, 0), BG=Colour(255, 0, 0, bg=True)),
    
    CHARSET["FLAG"]:   Colours(FG=Colour(255, 0, 255)),
    CHARSET["MINE"]:   Colours(FG=Colour(0, 0, 0)),
    CHARSET["HIDDEN"]: Colours(FG=Colour(164, 164, 164)),
    
    "1": Colours(FG=Colour(0, 0, 255)),
    "2": Colours(FG=Colour(0, 128, 0)),
    "3": Colours(FG=Colour(255, 0, 0)),
    "4": Colours(FG=Colour(0, 0, 128)),
    "5": Colours(FG=Colour(128, 0, 0)),
    "6": Colours(FG=Colour(0, 128, 128)),
    "7": Colours(FG=Colour(0, 0, 0)),
    "8": Colours(FG=Colour(128, 128, 128)),
}
DIGITSET: Final[dict[str, list[str]]] = {
    "0": ["╻━━╻",
          "┃  ┃",
          "╹━━╹"],
    "1": ["   ╻",
          "   ┃",
          "   ╹"],
    "2": [" ━━╻",
          "╻━━╹",
          "╹━━ "],
    "3": [" ━━╻",
          " ━━┃",
          " ━━╹"],
    "4": ["╻  ╻",
          "╹━━┃",
          "   ╹"],
    "5": ["╻━━ ",
          "╹━━╻",
          " ━━╹"],
    "6": ["╻━━ ",
          "┃━━╻",
          "╹━━╹"],
    "7": [" ━━╻",
          "   ┃",
          "   ╹"],
    "8": ["╻━━╻",
          "┃━━┃",
          "╹━━╹"],
    "9": ["╻━━╻",
          "╹━━┃",
          " ━━╹"],
}

DIFFICULTY_SETTINGS: Final[dict[Difficulty, tuple[Vector2, int]]] = {
    Difficulty.EASY:   (Vector2(9, 9),   10),
    Difficulty.MEDIUM: (Vector2(16, 16), 40),
    Difficulty.HARD:   (Vector2(30, 16), 99),
}

# 1 border + 14 bomb rem. + 9 difficulty + 11 title + 9 opposite difficulty + 14 timer + 1 border = 59
MIN_WIDTH: int = 59
TITLE_HEIGHT: Final[int] = 5

class Cell:
    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False):
        self.is_mine: bool = is_mine
        self.is_revealed: bool = is_revealed
        self.is_flagged: bool = is_flagged
        self.surrounding_mines: int = 0
        
        self.marked: bool = False

    def __str__(self):
        if self.is_revealed:
            return CHARSET["MINE"] if self.is_mine else CHARSET["OPEN"] if self.surrounding_mines == 0 else str(self.surrounding_mines)
        elif self.is_flagged:
            return CHARSET["FLAG"]
        else:
            return CHARSET["HIDDEN"]

    def reveal(self) -> None:
        if self.is_flagged:
            return
        
        self.is_revealed = True
        return
    
    def toggle_flag(self) -> bool:
        if not self.is_revealed:
            self.is_flagged = not self.is_flagged
            return True
        return False

    def is_empty(self) -> bool:
        return not self.is_mine and self.surrounding_mines == 0

class Board:
    DIMS: Vector2
    MINES: int

    def __init__(self, difficulty: Difficulty = Difficulty.EASY):
        self.DIMS, self.MINES = DIFFICULTY_SETTINGS[difficulty][0], DIFFICULTY_SETTINGS[difficulty][1]

        self.grid: list[list[Cell]] = [[Cell() for _ in range(self.DIMS.X)] for _ in range(self.DIMS.Y)]
        
        for idx in sample(range(self.DIMS.X * self.DIMS.Y), self.MINES):
            y, x = divmod(idx, self.DIMS.X)
            self.grid[y][x].is_mine = True
        
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if not cell.is_mine:
                    cell.surrounding_mines = self.surrounding_mines(x, y)
    
    def surrounding_mines(self, x: int, y: int) -> int:
        return sum(
            self.grid[ny][nx].is_mine
            for ny in range(max(0, y - 1), min(self.DIMS.Y, y + 2))
            for nx in range(max(0, x - 1), min(self.DIMS.X, x + 2))
            if (ny, nx) != (y, x)
        )
    
    def surrounding_flags(self, x: int, y: int) -> int:
        return sum(
            self.grid[ny][nx].is_flagged
            for ny in range(max(0, y - 1), min(self.DIMS.Y, y + 2))
            for nx in range(max(0, x - 1), min(self.DIMS.X, x + 2))
            if (ny, nx) != (y, x)
        )
    
    def reveal(self, x: int, y: int, by_player: bool = True) -> bool:
        if not (0 <= x < self.DIMS.X and 0 <= y < self.DIMS.Y):
            return True
        
        cell: Cell = self.grid[y][x]
        
        # skip if flagged
        if cell.is_flagged:
            return True
        
        # if bomb, reveal and return game over
        if cell.is_mine:
            cell.reveal()
            cell.marked = True
            return False
        
        # skip if already revealed
        if cell.is_revealed:
            # chording
            if by_player and self.surrounding_flags(x, y) == cell.surrounding_mines:
                hit_bomb: bool = False
                
                for ny in range(max(0, y - 1), min(self.DIMS.Y, y + 2)):
                    for nx in range(max(0, x - 1), min(self.DIMS.X, x + 2)):
                        if (ny, nx) == (y, x):
                            continue
                        
                        if not self.reveal(nx, ny, by_player=False):
                            hit_bomb = True
                
                return not hit_bomb
        
        cell.reveal()
        
        # if the cell is empty, recursively reveal surrounding cells
        if cell.is_empty():
            for ny in range(max(0, y - 1), min(self.DIMS.Y, y + 2)):
                for nx in range(max(0, x - 1), min(self.DIMS.X, x + 2)):
                    if (ny, nx) == (y, x):
                        continue
                    
                    empty_cell: Cell = self.grid[ny][nx]

                    if empty_cell.is_empty():
                        self.reveal(nx, ny, by_player=False)
                    else:
                        empty_cell.reveal()
            return True
        
        return True
    
    def is_cleared(self) -> bool:
        return all(cell.is_revealed or cell.is_mine for row in self.grid for cell in row)
    
    def flagged_cells(self) -> int:
        return sum(cell.is_flagged for row in self.grid for cell in row)
    
    def bombs_remaining(self) -> int:
        return max(0, self.MINES - self.flagged_cells())

class Minesweeper(Game):
    TITLE: str = "minesweeper"

    def __init__(self, screen: Screen):
        super().__init__(screen)

        self.difficulty: Difficulty = Difficulty.EASY
        self.reset()

    def reset(self, difficulty: Difficulty | None = None):
        if difficulty is not None:
            self.difficulty = difficulty
        self.board: Board = Board(difficulty=self.difficulty)
        self.state: State = State.PLAYING

        self.cursor_x: int = 0
        self.cursor_y: int = 0

        self.game_over: bool = False
        self.win: bool = False
        
        self.play_timer: float = 0.0

    def on_enter(self):
        return super().on_enter()

    def on_exit(self):
        return super().on_exit()

    def update(self, key: str | None, dt: float) -> bool:
        if self.state is State.PLAYING:
            self.play_timer += dt
        
        if self.board.is_cleared() and self.state is State.PLAYING:
            self.state = State.WON
        
        for m in self.screen.input.mouse:
            if not m.pressed:
                continue
            if self.hits_smiley(m.x, m.y):
                self.reset()
                continue
            if self.state is not State.PLAYING:
                continue
            
            cell: tuple[int, int] | None = self.cell_at(m.x, m.y)
            if cell is None:
                continue
            
            if m.button == MouseButton.LEFT:
                self.screen.audio.play_sfx("minesweeper/reveal.wav")
                if not self.board.reveal(cell[0], cell[1]):
                    self.state = State.GAME_OVER
                    self.screen.audio.play_sfx("minesweeper/explosion.wav")
            elif m.button == MouseButton.RIGHT:
                if self.board.grid[cell[1]][cell[0]].toggle_flag():
                    self.screen.audio.play_sfx("minesweeper/flag.wav")
        
        if key == "r":
            self.reset()
        if key == "+":
            if self.difficulty is not Difficulty.HARD:
                self.reset(Difficulty(self.difficulty.value + 1))
        if key == "-":
            if self.difficulty is not Difficulty.EASY:
                self.reset(Difficulty(self.difficulty.value - 1))
        
        return True

    def layout(self) -> Layout:
        board_w: int = self.board.DIMS.X * 2 + 1
        frame_w: int = max(MIN_WIDTH, board_w)
        h: int = self.board.DIMS.Y + 2 + TITLE_HEIGHT
        left: int = (self.screen.w - frame_w) // 2
        top: int = (self.screen.h - h) // 2
        return Layout(left, top, frame_w,
                  left + (frame_w - board_w) // 2,
                  top + TITLE_HEIGHT,
                  board_w)
    
    def cell_at(self, cx: int, cy: int) -> Vector2 | None:
        lay = self.layout()
        x: int = (cx - lay.board_left) // 2
        y: int = cy - lay.board_top
        if 0 <= x < self.board.DIMS.X and 0 <= y < self.board.DIMS.Y:
            return Vector2(x, y)
        return None
    
    def hits_smiley(self, cx: int, cy: int) -> bool:
        lay = self.layout()
        sx: int = lay.left + (lay.frame_w - 2) // 2
        return cy == lay.top + 3 and sx <= cx < sx + 2
    
    def render_7_seg(self, x: int, y: int, num: int) -> None:
        num = max(0, min(num, 999))
        num_str = str(num).rjust(3, "0")
        
        for digit in num_str:
            digit_lines = DIGITSET[digit]
            for i, line in enumerate(digit_lines):
                self.screen.put(x, y + i, f"{COLOURSET["7-SEG"].FG}{COLOURSET["7-SEG"].BG}{line}{Ansi.RESET}")
            x += 4
    
    def render(self) -> None:
        board_w: int = self.board.DIMS.X * 2 + 1
        frame_w: int = max(MIN_WIDTH, board_w)      # header + padded board width
        pad_l: int = (frame_w - board_w) // 2       # blank cells left of the board

        h: int = self.board.DIMS.Y + 2 + TITLE_HEIGHT
        left: int = (self.screen.w - frame_w) // 2  # frame left edge (centred on frame, not board)
        top: int = (self.screen.h - h) // 2
        board_left: int = left + pad_l              # board"s own left edge, inside the frame

        cell: Colours = COLOURSET["CELL"]
        box: str = f"{cell.FG}{cell.BG}"
        inner: int = frame_w - 2

        # header border
        self.screen.put(left, top, f"{box}╔{"═" * inner}╗{Ansi.RESET}")
        for row in (1, 2, 3):
            self.screen.put(left, top + row, f"{box}║{" " * inner}║{Ansi.RESET}")
        self.screen.put(left, top + 4, f"{Ansi.UNDERLINE}{box}╚{"═" * inner}╝{Ansi.RESETUNDERLINE}")

        # title
        title: str = f"{Ansi.UNDERLINE}{Ansi.FG.BLACK}{cell.BG}MINESWEEPER{Ansi.RESETUNDERLINE}"
        self.screen.put(left + (frame_w - len(Ansi.strip(title))) // 2, top + 1, title)

        # smiley
        face: str = ":)" if self.state is State.PLAYING else "X(" if self.state is State.GAME_OVER else ":D"
        status: str = f"{COLOURSET["SMILEY"].FG}{COLOURSET["SMILEY"].BG}{face}{Ansi.RESET}"
        self.screen.put(left + (frame_w - len(Ansi.strip(status))) // 2, top + 3, status)

        # counters: anchored to the FRAME edges, so they never depend on board width
        self.render_7_seg(left + 2, top + 1, self.board.bombs_remaining())
        self.render_7_seg(left + frame_w - 14, top + 1, int(self.play_timer))
        
        # difficulty indicator: anchored to the COUNTER edges, so they never depend on board
        diff: Callable[[Difficulty], str] = lambda d: "EASY" if d is Difficulty.EASY else "MED." if d is Difficulty.MEDIUM else "HARD"
        indicator: Callable[[Difficulty], str] = lambda d: " ┿" if d is self.difficulty else " │"
        
        for i, d in enumerate(Difficulty):
            self.screen.put(left + 16, top + 1 + i, f"{COLOURSET[CHARSET["HIDDEN"]].FG}{cell.BG}{diff(d)}{Ansi.FG.BLACK}{indicator(d)}{Ansi.RESET}")

        # board
        fill: str = f"{cell.BG}{" " * frame_w}{Ansi.RESET}"
        cell_style: str = f"{Ansi.UNDERLINE}{box}{cell.UL}"

        # top edge row: fill frame, then underline just the board span
        self.screen.put(left, top + TITLE_HEIGHT, fill)
        self.screen.put(board_left, top + TITLE_HEIGHT,
                        f"{Ansi.UNDERLINE}{cell.UL}{" " * board_w}{Ansi.RESETUNDERLINE}")

        for y, row in enumerate(self.board.grid):
            row_y: int = top + TITLE_HEIGHT + y

            if frame_w > board_w:
                self.screen.put(left, row_y, fill)  # blank bg first; cells draw over it

            for x, c in enumerate(row):
                cc: Colours = COLOURSET.get(str(c), Colours())
                
                if c.marked:
                    cc = COLOURSET["FAIL-MINE"]
                
                self.screen.put(board_left + x * 2, row_y,
                                f"{cell_style}|{cc.FG}{"" if not c.marked else cc.BG}{c}{cell.FG}|{Ansi.RESETUNDERLINE}")