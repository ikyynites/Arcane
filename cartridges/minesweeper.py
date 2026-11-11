from dataclasses import dataclass
from typing import NamedTuple, Final

from engine import Game, Screen, Colour, Ansi

class Vector2(NamedTuple):
    X: int
    Y: int

class Cell:
    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False):
        self.is_mine: bool = is_mine
        self.is_revealed: bool = is_revealed
        self.is_flagged: bool = is_flagged

    def __str__(self):
        if self.is_revealed:
            return "*" if self.is_mine else " "
        elif self.is_flagged:
            return "F"
        else:
            return "#"

class Board:
    DIMS: Final[Vector2] = Vector2(10, 10)

    def __init__(self):
        self.grid: list[list[Cell]] = [[Cell()] * self.DIMS.X for _ in range(self.DIMS.Y)]

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
        return True

    def render(self) -> None:
        self.screen.put(0, 0, f"{Ansi.UNDERLINE}{" " * (self.board.DIMS.X * 2 + 1)}")
        for y, row in enumerate(self.board.grid):
            for x, cell in enumerate(row):
                select: str = Ansi.FG.GREEN if x == self.cursor_x and y == self.cursor_y else ""
                self.screen.put(x * 2, y + 1, f"{Ansi.UNDERLINE}|{select}{cell}{Ansi.RESET}{Ansi.UNDERLINE}|")

    