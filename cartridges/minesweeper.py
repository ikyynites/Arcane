from dataclasses import dataclass
from random import sample
from typing import NamedTuple, Final

from engine import Game, Screen, Colour, Ansi

class Vector2(NamedTuple):
    X: int
    Y: int

class Colours(NamedTuple):
    FG: Colour = Colour()
    BG: Colour = Colour()
    UL: Colour = Colour()

COLOURSET: Final[dict[str, Colours]] = {
    "CELL": Colours(FG=Colour(128, 128, 128), BG=Colour(192, 192, 192, bg=True), UL=Colour(128, 128, 128, ul=True)),
    
    "o": Colours(FG=Colour(164, 164, 164)),
    "*": Colours(FG=Colour(0, 0, 0)),
    "1": Colours(FG=Colour(0, 0, 255)),
    "2": Colours(FG=Colour(0, 128, 0)),
    "3": Colours(FG=Colour(255, 0, 0)),
    "4": Colours(FG=Colour(0, 0, 128)),
    "5": Colours(FG=Colour(128, 0, 0)),
    "6": Colours(FG=Colour(0, 128, 128)),
    "7": Colours(FG=Colour(0, 0, 0)),
    "8": Colours(FG=Colour(128, 128, 128)),
    "#": Colours(FG=Colour(255, 0, 255)),
}

class Cell:
    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False):
        self.is_mine: bool = is_mine
        self.is_revealed: bool = is_revealed
        self.is_flagged: bool = is_flagged
        self.surrounding: int = 0

    def __str__(self):
        if self.is_revealed:
            return "*" if self.is_mine else " " if self.surrounding == 0 else str(self.surrounding)
        elif self.is_flagged:
            return "#"
        else:
            return "o"

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
        
        self.grid[0][0].is_revealed = False
        self.grid[0][0].is_flagged = True
        
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if x > self.DIMS.X // 2:
                    continue
                cell.is_revealed = False

class Minesweeper(Game):
    TITLE: str = "minesweeper"

    def __init__(self, screen: Screen):
        super().__init__(screen)

        self.reset()

    def reset(self):
        self.board: Board = Board()

        self.cursor_x: int = 0
        self.cursor_y: int = 0

        self.game_over: bool = False
        self.win: bool = False

    def on_enter(self):
        return super().on_enter()

    def on_exit(self):
        return super().on_exit()

    def update(self, key: str | None, dt: float) -> bool:
        if key == "r":
            self.reset()
        
        return True

    def render(self) -> None:
        left: int = (self.screen.w - (self.board.DIMS.X * 2 + 1)) // 2
        top: int = (self.screen.h - (self.board.DIMS.Y + 2)) // 2
        
        self.screen.put(left, top, f"{Ansi.UNDERLINE}{COLOURSET["CELL"].UL}{" " * (self.board.DIMS.X * 2 + 1)}{Ansi.RESETUNDERLINE}")
        for y, row in enumerate(self.board.grid):
            for x, cell in enumerate(row):
                # select: str = Ansi.FG.GREEN if x == self.cursor_x and y == self.cursor_y else ""
                cell_colour: Colours = COLOURSET.get(str(cell), Colours())
                
                self.screen.put(x * 2 + left, y + 1 + top, f"{Ansi.UNDERLINE}{COLOURSET["CELL"].FG}{COLOURSET["CELL"].BG}{COLOURSET["CELL"].UL}|{cell_colour.FG}{cell}{COLOURSET["CELL"].FG}|{Ansi.RESETUNDERLINE}")

    