from dataclasses import dataclass
from enum import Enum
from random import shuffle
from typing import Callable, Final, NamedTuple

from engine import Game, Screen, Colour, Ansi

type Shape = list[list[int]]
type Shapes = list[Shape]

class State(Enum):
    PLAYING = 0
    GAME_OVER = 1
    PAUSED = 2
    CLEARING = 3

class Actions(Enum):
    MOVE_LEFT = 1
    MOVE_RIGHT = 2
    MOVE_DOWN = 3
    ROTATE_CW = 4
    ROTATE_CCW = 5
    HARD_DROP = 6
    SOFT_DROP = 7
    HOLD = 8
    PAUSE = 9
    CONFIRM = 10

class TType(Enum):
    O = 1
    I = 2
    T = 3
    L = 4
    J = 5
    S = 6
    Z = 7

class Vector2(NamedTuple):
    X: int
    Y: int

class Colours(NamedTuple):
    FG: Colour = Colour() # FOREGROUND
    BG: Colour = Colour() # BACKGROUND
    HI: Colour = Colour() # HIGHLIGHT
    SH: Colour = Colour() # SHADOW

KEYBINDS: Final[dict[str, Actions]] = {
    "left":  Actions.MOVE_LEFT,
    "right": Actions.MOVE_RIGHT,
    "up":    Actions.ROTATE_CW,
    "down":  Actions.SOFT_DROP,
    
    " ": Actions.HARD_DROP,
    "z": Actions.ROTATE_CCW,
    "x": Actions.ROTATE_CW,
    "c": Actions.HOLD,
    
    "lshift": Actions.HOLD,
    "rshift": Actions.HOLD,
    "lctrl":  Actions.ROTATE_CCW,
    "rctrl":  Actions.ROTATE_CW,
    
    "\x1b": Actions.PAUSE,
    "f1": Actions.PAUSE,
    
    "\r": Actions.CONFIRM
}
VK_DOWN_ARROW: int = 0x28
COLOURSET: Final[dict[str, Colours]] = {
    "BORDER":    Colours(FG=Colour(244, 244, 244), BG=Colour(224, 224, 224, bg=True)),
    "FLASHING":  Colours(FG=Colour(211, 211, 211), BG=Colour(255, 255, 255, bg=True)),
    "EMPTY":     Colours(FG=Colour(11, 11, 11),    BG=Colour(21, 21, 21, bg=True)),
    "EMPTY_ALT": Colours(FG=Colour(21, 21, 21),    BG=Colour(31, 31, 31, bg=True))
}

LINES_PER_LEVEL: Final[int] = 5
LOCK_DELAY: Final[float] = 0.5
MAX_RESETS: Final[float] = 15
FLASH_STEP: Final[float] = 0.07
CLEAR_TIME: Final[float] = FLASH_STEP * 8
LINE_POINTS: Final[dict[int, int]] = {1: 100, 2: 300, 3: 500, 4: 800}

class Chars:
    _OPACITY: int = 50
    
    BORDER: str =    f"{COLOURSET["BORDER"].BG}{COLOURSET["BORDER"].FG}[]{Ansi.RESET}"
    FLASHING: str =  f"{COLOURSET["FLASHING"].BG}{COLOURSET["FLASHING"].FG}[]{Ansi.RESET}"
    EMPTY: str =     f"{COLOURSET["EMPTY"].BG}{COLOURSET["EMPTY"].FG}[]{Ansi.RESET}"
    EMPTY_ALT: str = f"{COLOURSET["EMPTY_ALT"].BG}{COLOURSET["EMPTY_ALT"].FG}[]{Ansi.RESET}"
    
    # t(etrimino), (e)mpty
    TETRIMINO: Callable[[int], str] =      lambda t: f"{T_COLOURS[TType(t)].BG}{T_COLOURS[TType(t)].HI}[{T_COLOURS[TType(t)].SH}]{Ansi.RESET}"
    GHOST_TET: Callable[[int, str], str] = lambda t, e: f"{Colour.lerp(T_COLOURS[TType(t)].BG, COLOURSET[e].BG, Chars._OPACITY, bg=True)}{Colour.lerp(T_COLOURS[TType(t)].HI, COLOURSET[e].FG, Chars._OPACITY)}[{Colour.lerp(T_COLOURS[TType(t)].SH, COLOURSET[e].FG, Chars._OPACITY)}]{Ansi.RESET}"   

T_COLOURS: Final[dict[TType, Colours]] = {
    TType.O: Colours(Colour(190, 190, 0), Colour(190, 190, 0, bg=True), Colour(229, 229, 153), Colour(95, 95, 0)),
    TType.I: Colours(Colour(0, 240, 240), Colour(0, 240, 240, bg=True), Colour(141, 248, 248), Colour(0, 120, 120)),
    TType.T: Colours(Colour(160, 0, 240), Colour(160, 0, 240, bg=True), Colour(212, 140, 248), Colour(80, 0, 120)),
    TType.L: Colours(Colour(240, 160, 0), Colour(240, 160, 0, bg=True), Colour(248, 212, 140), Colour(120, 80, 0)),
    TType.J: Colours(Colour(0, 0, 240),   Colour(0, 0, 240, bg=True),   Colour(140, 140, 248), Colour(0, 0, 120)),
    TType.S: Colours(Colour(0, 240, 0),   Colour(0, 240, 0, bg=True),   Colour(141, 248, 140), Colour(0, 120, 0)),
    TType.Z: Colours(Colour(240, 0, 0),   Colour(240, 0, 0, bg=True),   Colour(248, 140, 140), Colour(120, 0, 0)),
}
T_SHAPES: Final[dict[TType, Shapes]] = {
    TType.O: [
        [[0, 1, 1],
         [0, 1, 1],
         [0, 0, 0]],
    ],
    TType.I: [
        [[0, 0, 0, 0],
         [2, 2, 2, 2],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 2, 0, 0],
         [0, 2, 0, 0],
         [0, 2, 0, 0],
         [0, 2, 0, 0]],
    ],
    TType.T: [
        [[0, 3, 0],
         [3, 3, 3],
         [0, 0, 0]],
        [[0, 3, 0],
         [0, 3, 3],
         [0, 3, 0]],
        [[0, 0, 0],
         [3, 3, 3],
         [0, 3, 0]],
        [[0, 3, 0],
         [3, 3, 0],
         [0, 3, 0]],
    ],
    TType.L: [
        [[0, 0, 4],
         [4, 4, 4],
         [0, 0, 0]],
        [[0, 4, 0],
         [0, 4, 0],
         [0, 4, 4]],
        [[0, 0, 0],
         [4, 4, 4],
         [4, 0, 0]],
        [[4, 4, 0],
         [0, 4, 0],
         [0, 4, 0]],
    ],
    TType.J: [
        [[5, 0, 0],
         [5, 5, 5],
         [0, 0, 0]],
        [[0, 5, 5],
         [0, 5, 0],
         [0, 5, 0]],
        [[0, 0, 0],
         [5, 5, 5],
         [0, 0, 5]],
        [[0, 5, 0],
         [0, 5, 0],
         [5, 5, 0]],
    ],
    TType.S: [
        [[0, 6, 6],
         [6, 6, 0],
         [0, 0, 0]],
        [[0, 6, 0],
         [0, 6, 6],
         [0, 0, 6]],
        [[0, 0, 0],
         [0, 6, 6],
         [6, 6, 0]],
        [[6, 0, 0],
         [6, 6, 0],
         [0, 6, 0]],
    ],
    TType.Z: [
        [[7, 7, 0],
         [0, 7, 7],
         [0, 0, 0]],
        [[0, 0, 7],
         [0, 7, 7],
         [0, 7, 0]],
        [[0, 0, 0],
         [7, 7, 0],
         [0, 7, 7]],
        [[0, 7, 0],
         [7, 7, 0],
         [7, 0, 0]],
    ],
}
T_SPAWNS: Final[dict[TType, Vector2]] = {
    TType.O: Vector2(3, 0),
    TType.I: Vector2(3, -1),
    TType.T: Vector2(3, 0),
    TType.L: Vector2(3, 0),
    TType.J: Vector2(3, 0),
    TType.S: Vector2(3, 0),
    TType.Z: Vector2(3, 0),
}
T_ICONS: Final[dict[TType, str]] = {
    TType.O: " ██ ",
    TType.I: "▄▄▄▄",
    TType.T: "▄█▄ ",
    TType.L: "▄▄█ ",
    TType.J: "█▄▄ ",
    TType.S: "▄█▀ ",
    TType.Z: "▀█▄ ",
}

@dataclass(frozen=True)
class Tetrimino:
    ttype: TType
    x: int
    y: int
    rotation: int
    
    @classmethod
    def spawn(cls, ttype: TType) -> Tetrimino:
        return cls(ttype, *T_SPAWNS[ttype], 0)
    
    def moved(self, dx: int, dy: int) -> Tetrimino:
        return self.__replace__(x=self.x + dx, y=self.y + dy)
    
    def rotated(self, dr: int) -> Tetrimino:
        return self.__replace__(rotation=(self.rotation + dr) % len(T_SHAPES[self.ttype]))
    
    def cells(self) -> list[tuple[int, int]]:
        return [(self.x + dx, self.y + dy)
                for dy, row in enumerate(T_SHAPES[self.ttype][self.rotation])
                for dx, cell in enumerate(row) if cell]
    
    def bottom(self) -> int:
        return max(y for _, y in self.cells())

class Board:
    DIMS: Final[Vector2] = Vector2(10, 20)
    
    def __init__(self) -> None:
        self.grid: list[list[int]] = [[0] * self.DIMS.X for _ in range(self.DIMS.Y)]
    
    def fits(self, piece: Tetrimino) -> bool:
        return all(0 <= x < self.DIMS.X and 0 <= y < self.DIMS.Y and not self.grid[y][x]
                   for x, y in piece.cells())
    
    def lock(self, piece: Tetrimino) -> None:
        for x, y in piece.cells():
            self.grid[y][x] = piece.ttype.value
    
    def full_rows(self) -> list[int]:
        return [i for i, row in enumerate(self.grid) if all(row)]

    def clear(self, rows: list[int]) -> None:
        keep_rows: list[list[int]] = [r for i, r in enumerate(self.grid) if i not in rows]
        self.grid = [[0] * 10 for _ in rows] + keep_rows

class Tetris(Game):
    TITLE: str = "tetris"
    
    def __init__(self, screen: Screen) -> None:
        super().__init__(screen)
        
        self.reset()
    
    # game lifecycle
    def reset(self) -> None:
        self.board: Board = Board()
        self.state = State.PLAYING
        
        self.bag: list[TType] = []
        self.refill()
        
        self.active_piece: Tetrimino = Tetrimino.spawn(self.draw())
        self.lowest_y: int = self.active_piece.bottom()
        
        self.held_piece: TType | None = None
        self.can_hold: bool = True
        
        self.score: int = 0
        self.lines_cleared: int = 0
        self.b2b: bool = False
        
        self.clearing_rows: list[int] = []
        self.clear_timer: float = 0.0
        
        self.anim_timer: float = 0.0
        self.gravity_timer: float = 0.0
        self.lock_timer: float = 0.0
        self.lock_resets: int = 0
        
        self.screen.audio.play_bgm("tetris-bgm.wav")
    
    def on_enter(self) -> None:
        return super().on_enter()
    
    def on_exit(self) -> None:
        self.screen.audio.stop_bgm()
        
        return super().on_exit()
    
    # derived values
    @property
    def level(self) -> int:
        return self.lines_cleared // LINES_PER_LEVEL + 1
    
    @property
    def fall_time(self) -> float:
        return max((0.8 - (self.level - 1) * 0.007) ** (self.level - 1), 1e-4)
    
    @property
    def queue(self) -> list[TType]:
        return self.bag[::-1]

    def grounded(self) -> bool:
        return not self.board.fits(self.active_piece.moved(0, 1))
    
    # bag and spawn
    def refill(self) -> None:
        self.bag = list(TType)
        shuffle(self.bag)
    
    def draw(self) -> TType:
        ttype: TType = self.bag.pop()
        
        if not self.bag:
            self.refill()
        
        return ttype
    
    def spawn(self, ttype: TType) -> None:
        self.active_piece = Tetrimino.spawn(ttype)
        
        self.gravity_timer = 0.0
        self.lock_timer = 0.0
        self.lock_resets = 0
        
        self.lowest_y = self.active_piece.bottom()
        
        if not self.board.fits(self.active_piece):
            self.state = State.GAME_OVER
            self.screen.audio.stop_bgm()
            self.screen.audio.play_sfx("tetris-game-over.wav")

    # piece actions
    def commit(self, piece: Tetrimino, by_player: bool) -> None:
        self.active_piece = piece
        if piece.bottom() > self.lowest_y:
            self.lowest_y = piece.bottom()
            self.lock_resets = 0
        if by_player and self.grounded() and self.lock_resets < MAX_RESETS:
            self.lock_timer = 0.0
            self.lock_resets += 1
 
    def try_move(self, dx: int) -> None:
        moved = self.active_piece.moved(dx, 0)
        if self.board.fits(moved):
            self.commit(moved, by_player=True)
            self.screen.audio.play_sfx("tetris-move.wav")
 
    def try_rotate(self, dr: int) -> None:
        rotated = self.active_piece.rotated(dr)
        if rotated != self.active_piece and self.board.fits(rotated):
            self.commit(rotated, by_player=True)
            self.screen.audio.play_sfx("tetris-rotate.wav")

    def hard_drop(self) -> None:
        while self.board.fits((moved := self.active_piece.moved(0, 1))):
            self.active_piece = moved
            self.score += 2
        self.lock()
    
    def hold(self) -> None:
        if not self.can_hold:
            return
        
        self.can_hold = False
        
        if self.held_piece is None:
            self.held_piece = self.active_piece.ttype
            self.spawn(self.draw())
        else:
            self.held_piece, ttype = self.active_piece.ttype, self.held_piece
            self.spawn(ttype)

    def lock(self) -> None:
        self.board.lock(self.active_piece)
        
        self.can_hold = True
        full_rows = self.board.full_rows()
        
        if full_rows:
            self.award(len(full_rows))
            self.clearing_rows = full_rows
            self.clear_timer = 0.0
            self.state = State.CLEARING
            self.screen.audio.play_sfx("tetris-landed-with-clear.wav")
        else:
            self.spawn(self.draw())
            self.screen.audio.play_sfx("tetris-landed.wav")

    def award(self, cleared: int) -> None:
        points: int = LINE_POINTS[cleared] * self.level
        
        if cleared > 0:
            if self.b2b:
                points *= 2
            self.b2b = True
            
            if cleared == 4:
                self.screen.audio.play_sfx("tetris-4-line-clear.wav")
            else:
                self.screen.audio.play_sfx("tetris-line-clear.wav")
        else:
            self.b2b = False
        
        current_level: int = self.level
        
        self.score += points
        self.lines_cleared += cleared
        
        if self.level > current_level:
            self.screen.audio.play_sfx("tetris-level-up.wav")
    
    # input handling
    def get_actions(self, key: str | None) -> set[Actions]:
        names: set[str] = {m for m in ("lctrl", "rctrl", "lshift", "rshift") if self.modifiers.pressed(m)}
        if key is not None:
            names.add(key.lower())
        return {KEYBINDS[n] for n in names if n in KEYBINDS}
    
    def handle_input(self, actions: set[Actions]) -> None:
        if Actions.MOVE_LEFT in actions:
            self.try_move(-1)
        if Actions.MOVE_RIGHT in actions:
            self.try_move(1)
        if Actions.ROTATE_CW in actions:
            self.try_rotate(1)
        if Actions.ROTATE_CCW in actions:
            self.try_rotate(-1)
        if Actions.HARD_DROP in actions:
            self.hard_drop()
            return
        
        if Actions.HOLD in actions:
            self.hold()
    
    # time functions
    def apply_gravity(self, dt: float) -> None:
        soft_drop: bool = Screen.is_down(VK_DOWN_ARROW)
        drop_time: float = max(self.fall_time / (20 if soft_drop else 1), 1e-4)
        
        if self.grounded():
            self.gravity_timer = 0.0
            self.lock_timer += dt
            if self.lock_timer >= LOCK_DELAY:
                self.lock()
            return
        
        self.lock_timer = 0.0
        self.gravity_timer += dt / drop_time
        
        while self.gravity_timer >= 1.0 and not self.grounded():
            self.gravity_timer -= 1.0
            self.commit(self.active_piece.moved(0, 1), by_player=False)
            
            if soft_drop:
                self.score += 1
    
    def update(self, key: str | None, dt: float) -> bool:
        self.anim_timer += dt
        actions: set[Actions] = self.get_actions(key)
        
        if self.state is State.GAME_OVER:
            if Actions.CONFIRM in actions:
                self.reset()
            return True
        
        elif self.state is State.PAUSED:
            if Actions.PAUSE in actions:
                self.state = State.PLAYING
            return True
        
        elif self.state is State.CLEARING:
            self.clear_timer += dt
            
            if self.clear_timer >= CLEAR_TIME:
                self.board.clear(self.clearing_rows)
                self.clearing_rows = []
                self.state = State.PLAYING
                self.spawn(self.draw())
    
            return True
        
        if Actions.PAUSE in actions:
            self.state = State.PAUSED
        
        self.handle_input(actions)
        if self.state is State.PLAYING:
            self.apply_gravity(dt)
        
        return True
    
    # rendering code
    def overlay_active(self) -> dict[tuple[int, int], str]:
        if self.state not in (State.PLAYING, State.PAUSED):
            return {}
        
        ghost: Tetrimino = self.active_piece
        while self.board.fits((below := ghost.moved(0, 1))):
            ghost = below
            
        cell: int = self.active_piece.ttype.value
        
        layer = {(x, y): Chars.GHOST_TET(cell, "EMPTY" if x % 2 == 0 else "EMPTY_ALT")
                 for x, y in ghost.cells()}
        layer |= {(x, y): Chars.TETRIMINO(cell) for x, y in self.active_piece.cells()}
        
        return layer
    
    def tag(self) -> str:
        if self.state is State.GAME_OVER:
            text = f"{Ansi.FG.RED}game over! {Ansi.FG.GREY}press enter to restart{Ansi.RESET}"
            return text
        
        if self.state is State.PAUSED:
            dots = "." * (int(self.anim_timer / 0.5) % 4)
            return f"{Ansi.FG.GREY}paused{dots.ljust(3)}{Ansi.RESET}"
        
        return ""
    
    def render(self) -> None:
        w, h = Board.DIMS
        
        left = (self.screen.w - (w * 2 + 4)) // 2
        top = (self.screen.h - (h + 2)) // 2
        
        active = self.overlay_active()
        flash: bool = self.state is State.CLEARING and int(self.clear_timer / FLASH_STEP) % 2 == 0
        
        title: str = f"{COLOURSET["BORDER"].BG}{Ansi.FG.BLACK}TETRIS{Ansi.RESET}"
        
        self.screen.put(left, top, Chars.BORDER * (w + 2))
        self.screen.put((self.screen.w - len(Ansi.strip(title))) // 2, top, title)
        
        for y, row in enumerate(self.board.grid):
            cells = [Chars.BORDER]
            
            for x, cell in enumerate(row):
                if (x, y) in active:
                    cells.append(active[(x, y)])
                elif flash and y in self.clearing_rows:
                    cells.append(Chars.FLASHING)
                elif cell:
                    cells.append(Chars.TETRIMINO(cell))
                else:
                    cells.append(Chars.EMPTY if x % 2 == 0 else Chars.EMPTY_ALT)
            
            cells.append(Chars.BORDER)
            
            self.screen.put(left, top + 1 + y, "".join(cells))
        self.screen.put(left, top + 1 + h, Chars.BORDER * (w + 2))
        
        text = self.tag()
        if text:
            self.screen.put((self.screen.w - len(Ansi.strip(text))) // 2, top + h + 3, text)
        
        return