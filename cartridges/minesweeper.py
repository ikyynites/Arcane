from enum import Enum
from random import sample
from typing import NamedTuple, Final

from engine import Game, Screen, Colour, Ansi

class State(Enum):
    PLAYING = 0
    GAME_OVER = 1
    WON = 2

class Vector2(NamedTuple):
    X: int
    Y: int

class Colours(NamedTuple):
    FG: Colour = Colour()
    BG: Colour = Colour()
    UL: Colour = Colour()

class CHARSET(Enum):
    FLAG = "#"
    MINE = "*"
    OPEN = " "
    HIDDEN = "o"

COLOURSET: Final[dict[str, Colours]] = {
    "CELL":   Colours(FG=Colour(128, 128, 128), BG=Colour(192, 192, 192, bg=True), UL=Colour(128, 128, 128, ul=True)),
    "SMILEY": Colours(FG=Colour(0, 0, 0), BG=Colour(255, 255, 0, bg=True)),
    "7-SEG":  Colours(FG=Colour(255, 0, 0), BG=Colour(0, 0, 0, bg=True)),
    
    CHARSET.FLAG.value:   Colours(FG=Colour(255, 0, 255)),
    CHARSET.MINE.value:   Colours(FG=Colour(0, 0, 0)),
    CHARSET.HIDDEN.value: Colours(FG=Colour(164, 164, 164)),
    
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
    "0": ["┏━━┓",
          "┃  ┃",
          "┗━━┛"],
    "1": ["   ╻",
          "   ┃",
          "   ╹"],
    "2": [" ━━┓",
          "┏━━┛",
          "┗━━ "],
    "3": [" ━━┓",
          " ━━┫",
          " ━━┛"],
    "4": ["╻  ╻",
          "┗━━┫",
          "   ╹"],
    "5": ["┏━━ ",
          "┗━━┓",
          " ━━┛"],
    "6": ["┏━━ ",
          "┣━━┓",
          "┗━━┛"],
    "7": [" ━━┓",
          "   ┃",
          "   ╹"],
    "8": ["┏━━┓",
          "┣━━┫",
          "┗━━┛"],
    "9": ["┏━━┓",
          "┗━━┫",
          " ━━┛"],
}

TITLE_HEIGHT: Final[int] = 5

class Cell:
    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False):
        self.is_mine: bool = is_mine
        self.is_revealed: bool = is_revealed
        self.is_flagged: bool = is_flagged
        self.surrounding: int = 0

    def __str__(self):
        if self.is_revealed:
            return CHARSET.MINE.value if self.is_mine else CHARSET.OPEN.value if self.surrounding == 0 else str(self.surrounding)
        elif self.is_flagged:
            return CHARSET.FLAG.value
        else:
            return CHARSET.HIDDEN.value
    
    def reveal(self) -> bool:
        if not self.is_flagged:
            self.is_revealed = True
            return self.is_mine
        return False
    
    def toggle_flag(self):
        if not self.is_revealed:
            self.is_flagged = not self.is_flagged
    
    def is_empty(self) -> bool:
        return not self.is_mine and self.surrounding == 0

class Board:
    DIMS: Final[Vector2] = Vector2(30, 16)
    MINES: Final[int] = 99

    def __init__(self):
        self.grid: list[list[Cell]] = [[Cell(is_revealed=True) for _ in range(self.DIMS.X)] for _ in range(self.DIMS.Y)]
        
        for idx in sample(range(self.DIMS.X * self.DIMS.Y), self.MINES):
            y, x = divmod(idx, self.DIMS.X)
            self.grid[y][x].is_mine = True
        
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if not cell.is_mine:
                    cell.surrounding = sum(
                        self.grid[ny][nx].is_mine
                        for ny in range(max(0, y - 1), min(self.DIMS.Y, y + 2))
                        for nx in range(max(0, x - 1), min(self.DIMS.X, x + 2))
                        if (ny, nx) != (y, x)
                    )
        
        # temp testing for flag
        self.grid[0][0].is_revealed = False
        self.grid[0][0].is_flagged = True
        
        # temp testing for hidden and open
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if x > self.DIMS.X // 2:
                    continue
                cell.is_revealed = False
    
    def flagged_cells(self) -> int:
        return sum(cell.is_flagged for row in self.grid for cell in row)
    
    def bombs_remaining(self) -> int:
        return max(0, self.MINES - self.flagged_cells())

class Minesweeper(Game):
    TITLE: str = "minesweeper"

    def __init__(self, screen: Screen):
        super().__init__(screen)

        self.reset()

    def reset(self):
        self.board: Board = Board()
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
        self.play_timer += dt
        
        if key == "r":
            self.reset()
        
        return True

    def render_7_seg(self, x: int, y: int, num: int) -> None:
        num = max(0, min(num, 999))
        num_str = str(num).rjust(3, "0")
        
        for digit in num_str:
            digit_lines = DIGITSET[digit]
            for i, line in enumerate(digit_lines):
                self.screen.put(x, y + i, f"{COLOURSET["7-SEG"].FG}{COLOURSET["7-SEG"].BG}{line}{Ansi.RESET}")
            x += 4
    
    def render(self) -> None:
        w: int = self.board.DIMS.X * 2 + 1
        h: int = self.board.DIMS.Y + 2 + TITLE_HEIGHT
        
        left: int = (self.screen.w - w) // 2
        top: int = (self.screen.h - h) // 2
        
        # render border
        self.screen.put(left, top, f"{COLOURSET["CELL"].FG}{COLOURSET["CELL"].BG}╔{"═" * (w - 2)}╗")
        self.screen.put(left, top + 1, f"{COLOURSET["CELL"].FG}{COLOURSET["CELL"].BG}║{" " * (w - 2)}║")
        self.screen.put(left, top + 2, f"{COLOURSET["CELL"].FG}{COLOURSET["CELL"].BG}║{" " * (w - 2)}║")
        self.screen.put(left, top + 3, f"{COLOURSET["CELL"].FG}{COLOURSET["CELL"].BG}║{" " * (w - 2)}║")
        self.screen.put(left, top + 4, f"{Ansi.UNDERLINE}{COLOURSET["CELL"].FG}{COLOURSET["CELL"].BG}╚{"═" * (w - 2)}╝{Ansi.RESETUNDERLINE}")
        
        # render title
        title: str = f"{Ansi.UNDERLINE}{Ansi.FG.BLACK}{COLOURSET["CELL"].BG}MINESWEEPER{Ansi.RESETUNDERLINE}"
        self.screen.put(left + (w - len(Ansi.strip(title))) // 2, top + 1, title)
        
        # render smiley face based on game state
        status: str = f"{COLOURSET["SMILEY"].FG}{COLOURSET["SMILEY"].BG}{":)" if self.state is State.PLAYING else "X(" if self.state is State.GAME_OVER else ":D"}{Ansi.RESET}"
        self.screen.put(left + (w - len(Ansi.strip(status))) // 2, top + 3, status)
        
        # render bombs remaining and timer
        #                            ┌> (4 cells * 3 digits) + 1 padding + 1 border
        self.render_7_seg(left + w - 14, top + 1, int(self.play_timer))
        self.render_7_seg(left + 2, top + 1, self.board.bombs_remaining())
        #                        └> 1 padding + 1 border
        
        # render board
        self.screen.put(left, top + TITLE_HEIGHT, f"{Ansi.UNDERLINE}{COLOURSET["CELL"].UL}{" " * (self.board.DIMS.X * 2 + 1)}{Ansi.RESETUNDERLINE}")
        for y, row in enumerate(self.board.grid):
            for x, cell in enumerate(row):
                # select: str = Ansi.FG.GREEN if x == self.cursor_x and y == self.cursor_y else ""
                cell_colour: Colours = COLOURSET.get(str(cell), Colours())
                
                self.screen.put(x * 2 + left, y + top + TITLE_HEIGHT, f"{Ansi.UNDERLINE}{COLOURSET["CELL"].FG}{COLOURSET["CELL"].BG}{COLOURSET["CELL"].UL}|{cell_colour.FG}{cell}{COLOURSET["CELL"].FG}|{Ansi.RESETUNDERLINE}")

    