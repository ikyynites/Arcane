from ctypes import byref, create_unicode_buffer, windll, wintypes
from importlib import import_module
from msvcrt import getwch, kbhit
from os import get_terminal_size
from pathlib import Path
from re import compile
from sys import stdout
from threading import Event, Thread
from time import perf_counter, sleep
from typing import Final, Iterator

type Buffer = list[list[str]]

kernel32 = windll.LoadLibrary("kernel32.dll")
user32 = windll.LoadLibrary("user32.dll")
winmm = windll.LoadLibrary("winmm.dll")

AUDIO_ROOT: Final[Path] = Path(__file__).resolve().parent / "assets" / "audio"
CARTRIDGES_ROOT: Final[Path] = Path(__file__).resolve().parent / "cartridges"
ICON: Final[Path] = Path(__file__).resolve().parent / "assets" / "ico" / "ico.ico"

MCI_TYPES: Final[dict[str, str]] = {".wav": "waveaudio"}

ARCANE_ART: Final[list[str]] = [
    " █████╗ ██████╗  ██████╗ █████╗ ███╗   ██╗███████╗",
    "██╔══██╗██╔══██╗██╔════╝██╔══██╗████╗  ██║██╔════╝",
    "███████║██████╔╝██║     ███████║██╔██╗ ██║█████╗  ",
    "██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗██║██╔══╝  ",
    "██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████║███████╗",
    "╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝",
]

class Audio:
    def __init__(self, root: Path, sfx_channels: int = 4) -> None:
        self.root: Path = root
        
        self.bgm: Channel = Channel("arcane_bgm")
        self.sfx: list[Channel] = [Channel(f"arcane_sfx{i}") for i in range(sfx_channels)]
        
        self._bgm_path: Path | None = None
    
    def play_bgm(self, name: str | Path, loop: bool = True) -> None:
        p = self._check(name)
        if p == self._bgm_path and self.bgm.busy:
            return
        self._bgm_path = p
        self.bgm.play(p, loop)
    
    def stop_bgm(self) -> None:
        self._bgm_path = None
        self.bgm.stop()
    
    def play_sfx(self, name: str | Path) -> bool:
        p = self._check(name)
        for channel in self.sfx:
            if not channel.busy:
                channel.play(p, False)
                return True
        return False

    def close(self) -> None:
        self.bgm.stop()
        for channel in self.sfx:
            channel.stop()
    
    def _check(self, name: str | Path) -> Path:
        p = self.root / name
        if not p.is_file():
            raise FileNotFoundError(p)
        if p.suffix.lower() not in MCI_TYPES:
            raise ValueError(f"unsupported audio type: {p.suffix}")
        return p
    
    @staticmethod
    def MCI(command: str) -> int:
        return winmm.mciSendStringW(command, None, 0, None)
    
    @staticmethod
    def MCI_STR(command: str) -> str:
        buf = create_unicode_buffer(64)
        winmm.mciSendStringW(command, buf, len(buf), None)
        return buf.value

class Channel:
    def __init__(self, alias: str) -> None:
        self.alias: str = alias
        self._stop: Event = Event()
        self._thread: Thread | None = None
    
    @property
    def busy(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
    
    def play(self, path: Path, loop: bool) -> None:
        self.stop()
        self._stop.clear()
        self._thread = Thread(target=self._run, args=(path, loop), daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
    
    def _run(self, path: Path, loop: bool) -> None:
        mci_type: str = MCI_TYPES[path.suffix.lower()]
        
        if Audio.MCI(f'open "{path}" type {mci_type} alias {self.alias}'):
            return
        
        try:
            while not self._stop.is_set():
                if Audio.MCI(f"play {self.alias} from 0"):
                    break
                
                while not self._stop.wait(0.02):
                    if Audio.MCI_STR(f"status {self.alias} mode") != "playing":
                        break
                
                if not loop:
                    break
        finally:
            Audio.MCI(f"stop {self.alias}")
            Audio.MCI(f"close {self.alias}")

class Colour:
    def __init__(self, R: int = 0, G: int = 0, B: int = 0, bg: bool = False) -> None:
        self.R: int = R
        self.G: int = G
        self.B: int = B
        self.bg: bool = bg
    
    def __str__(self) -> str:
        return Ansi.RGB(self.R, self.G, self.B, bg=self.bg)
    
    @staticmethod
    def lerp(top: Colour, bottom: Colour, a: float, bg: bool = False) -> Colour:
        r_top, g_top, b_top = top.R, top.G, top.B
        r_bottom, g_bottom, b_bottom = bottom.R, bottom.G, bottom.B

        r = int(((a * r_top) + ((255 - a) * r_bottom)) // 255)
        g = int(((a * g_top) + ((255 - a) * g_bottom)) // 255)
        b = int(((a * b_top) + ((255 - a) * b_bottom)) // 255)

        return Colour(r, g, b, bg=bg)

class Ansi:
    CSI: Final[str] = "\x1b["
    
    CLEAR_SCREEN: Final[str] = CSI + "2J"
    CURSOR_HOME: Final[str] = CSI + "H"
    HIDE_CURSOR: Final[str] = CSI + "?25l"
    SHOW_CURSOR: Final[str] = CSI + "?25h"

    RESET: Final[str] = CSI + "0m"
    BOLD: Final[str] = CSI + "1m"
    NOBOLD: Final[str] = CSI + "22m"
    ITALIC: Final[str] = CSI + "3m"
    NOITALIC: Final[str] = CSI + "23m"
    UNDERLINE: Final[str] = CSI + "4m"
    NOUNDERLINE: Final[str] = CSI + "24m"
    
    class FG:
        _CSI: Final[str] = "\x1b["
        
        BLACK: Final[str] = _CSI + "30m"
        GREY: Final[str] = _CSI + "90m"
        RED: Final[str] = _CSI + "91m"
        GREEN: Final[str] = _CSI + "92m"
        YELLOW: Final[str] = _CSI + "93m"
        BLUE: Final[str] = _CSI + "94m"
        MAGENTA: Final[str] = _CSI + "95m"
        CYAN: Final[str] = _CSI + "96m"
        WHITE: Final[str] = _CSI + "97m"
    
    class BG:
        _CSI: Final[str] = "\x1b["
        
        BLACK: Final[str] = _CSI + "40m"     
        GREY: Final[str] = _CSI + "100m"
        RED: Final[str] = _CSI + "101m"
        GREEN: Final[str] = _CSI + "102m"
        YELLOW: Final[str] = _CSI + "103m"
        BLUE: Final[str] = _CSI + "104m"
        MAGENTA: Final[str] = _CSI + "105m"
        CYAN: Final[str] = _CSI + "106m"
        WHITE: Final[str] = _CSI + "107m"
    
    _PATTERN = compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    _SPLIT = compile(r"(\x1b\[[0-?]*[ -/]*[@-~])")
    
    @staticmethod
    def RGB(r: int, g: int, b: int, bg: bool = False) -> str:
        return f"{Ansi.CSI}{"4" if bg else "3"}8;2;{r};{g};{b}m"
    
    @staticmethod
    def find(text: str) -> Iterator[str]:
        for match in Ansi._PATTERN.finditer(text):
            yield match.group()
    
    @staticmethod
    def split(text: str) -> list[str]:
        cells: list[str] = []
        style: str = ""
        
        for i, part in enumerate(Ansi._SPLIT.split(text)):
            if i % 2: # filter out styles
                style = "" if part in (Ansi.RESET, "\x1b[m") else style + part
            else:
                for ch in part: # set style for each individual cell
                    cells.append(style + ch + Ansi.RESET if style else ch)
        
        return cells
    
    @staticmethod
    def strip(text: str) -> str:
        return Ansi._PATTERN.sub("", text)

class Screen:
    HWND: Final = kernel32.GetConsoleWindow()
    
    def __init__(self, w: int, h: int, title: str | None = "") -> None:
        if title is not None:
            self.set_title(title)
        self.set_icon(ICON)
        
        self.audio: Audio = Audio(AUDIO_ROOT)
        
        self.w: int = w
        self.h: int = h
        
        self.front: Buffer = [[" "] * w for _ in range(h)]
        self.back: Buffer = [[" "] * w for _ in range(h)]
    
    def __enter__(self) -> Screen:
        # get stdio handles
        self.h_stdout = kernel32.GetStdHandle(-11)
        self.h_stdin = kernel32.GetStdHandle(-10)
        
        buf = create_unicode_buffer(260)
        kernel32.GetConsoleTitleW(buf, len(buf))
        self.original_title: str = buf.value
        
        # initialise console modes
        self.mode_out = wintypes.DWORD()
        self.mode_in = wintypes.DWORD()
        kernel32.GetConsoleMode(self.h_stdout, byref(self.mode_out))
        kernel32.GetConsoleMode(self.h_stdin, byref(self.mode_in))
        
        # win32 api console mode flags
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
        ENABLE_QUICK_EDIT_MODE = 0x0040
        ENABLE_EXTENDED_FLAGS = 0x0080
        
        # arcane stdout mode
        self.a_mode_out: int = self.mode_out.value
        self.a_mode_out |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
        self.a_mode_out &= ~ENABLE_WRAP_AT_EOL_OUTPUT
        
        # arcane stdin mode
        self.a_mode_in: int = self.mode_in.value
        self.a_mode_in |= ENABLE_EXTENDED_FLAGS
        self.a_mode_in &= ~ENABLE_QUICK_EDIT_MODE
        
        # apply custom arcane console modes
        kernel32.SetConsoleMode(self.h_stdout, self.a_mode_out)
        kernel32.SetConsoleMode(self.h_stdin, self.a_mode_in)
        
        stdout.write(f"{Ansi.HIDE_CURSOR}{Ansi.CLEAR_SCREEN}{Ansi.CURSOR_HOME}")
        stdout.flush()

        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        # reset terminal to original console mode
        stdout.write(f"{Ansi.SHOW_CURSOR}{Ansi.CLEAR_SCREEN}{Ansi.CURSOR_HOME}")
        stdout.flush()
        
        kernel32.SetConsoleMode(self.h_stdout, self.mode_out.value)
        kernel32.SetConsoleMode(self.h_stdin, self.mode_in.value)
        
        self.set_title(self.original_title)
        
        self.audio.close()
    
    def put(self, x: int, y: int, text: str) -> None:
        if not 0 <= y < self.h:
            return
        for i, cell in enumerate(Ansi.split(text)):
            if 0 <= x + i < self.w:
                self.back[y][x + i] = cell
    
    def present(self):
        # footer = f"{Ansi.BG.GREY}{" " * screen.w}{Ansi.RESET}"
        # self.put(0, self.h - 1, footer)
        # TODO: footer code?
        
        out = [f"\x1b[{y+1};1H{"".join(row)}"
               for y, row in enumerate(self.back) if row != self.front[y]]
        
        stdout.write("".join(out))
        stdout.flush()
        
        self.front, self.back = self.back, [[" "] * self.w for _ in range(self.h)]
    
    def overlay(self):
        out = [f"\x1b[{y+1};1H{"".join(row)}"
               for y, row in enumerate(self.back) if not all(cell == " " for cell in row)]
        
        stdout.write("".join(out))
        stdout.flush()
        
        self.front, self.back = [self.back[i] if not all(cell == " " for cell in self.back[i]) > 0 else self.front[i] for i in range(len(self.front))], [[" "] * self.w for _ in range(self.h)]
        
    
    def check_resize(self) -> None:
        w, h = get_terminal_size()
        
        if (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            
            self.front = [[" "] * w for _ in range(h)]
            self.back = [[" "] * w for _ in range(h)]
            
            stdout.write(Ansi.CLEAR_SCREEN)
            stdout.flush()
    
    @staticmethod
    def set_title(text: str) -> None:
        kernel32.SetConsoleTitleW(text)
    
    @staticmethod
    def set_icon(path: Path) -> None:
        if not Screen.HWND:
            return
        
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        
        small = user32.LoadImageW(None, str(path.absolute()), IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        big = user32.LoadImageW(None, str(path.absolute()), IMAGE_ICON, 24, 24, LR_LOADFROMFILE)
        
        user32.SendMessageW(Screen.HWND, WM_SETICON, ICON_SMALL, small)
        user32.SendMessageW(Screen.HWND, WM_SETICON, ICON_BIG, big)

    @staticmethod
    def get_key() -> str | None:
        if not kbhit():
            return None
        ch: str = getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}.get(getwch())
        return ch
    
    @staticmethod
    def has_focus() -> bool:
        return Screen.HWND == user32.GetForegroundWindow()
    
    @staticmethod
    def is_down(vk: int) -> bool:
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)

class Modifiers:
    KEYS = {"lshift": 0xA0, "rshift": 0xA1, "lctrl": 0xA2, "rctrl": 0xA3,
            **{f"f{i+1}": 0x70 + i for i in range(12)} # f1-f12
            }

    def __init__(self) -> None:
        self.prev: dict[str, bool] = {name: False for name in self.KEYS}
        self.now: dict[str, bool] = dict(self.prev)

    def poll(self) -> None:
        focused: bool = Screen.has_focus()
        self.prev = self.now
        self.now = {name: focused and Screen.is_down(vk) for name, vk in self.KEYS.items()}

    def pressed(self, name: str) -> bool:
        return self.now[name] and not self.prev[name]

    def held(self, name: str) -> bool:
        return self.now[name]

class Game:
    TITLE: str = "untitled"
    FPS: int = 60
    
    def __init__(self, screen: Screen) -> None:
        self.screen: Screen = screen
        self.modifiers: Modifiers = Modifiers()
    
    def start(self) -> None:
        Screen.set_title(f"{self.TITLE} | arcane - ikyyn's arcade")
        self.on_enter()
        
        self.modifiers.poll()
        self.modifiers.poll()
        
        frame_time: float = 1 / self.FPS
        max_dt: float = 10 * frame_time
        
        last: float = perf_counter()
        
        try:
            while True:
                t0: float = perf_counter()
                
                dt: float = min(t0 - last, max_dt)
                last = t0

                self.screen.check_resize()
                self.modifiers.poll()
                key: str | None = Screen.get_key()

                if key in ("q", "Q"):
                    break
                if not self.update(key, dt):
                    break
                
                self.render()
                self.screen.present()

                sleep(max(0.0, frame_time - (perf_counter() - t0)))
        finally:
            self.on_exit()
    
    def on_enter(self) -> None:
        pass
    
    def on_exit(self) -> None:
        pass
    
    def update(self, key: str | None, dt: float) -> bool:
        raise NotImplementedError

    def render(self) -> None:
        raise NotImplementedError

class Menu(Game):
    TITLE: str = "menu"
    
    def __init__(self, screen: Screen) -> None:
        super().__init__(screen)
        self.games: list[type[Game]] = self.load_cartridges()
        self.index: int = 0
        self.selected: type[Game] | None = None
    
    def update(self, key: str | None, dt: float) -> bool:
        if not self.games:
            return True
        
        if key == "UP" and len(self.games) > 1:
            self.index = (self.index - 1) % len(self.games)
            self.screen.audio.play_sfx("beep.wav")
        elif key == "DOWN" and len(self.games) > 1:
            self.index = (self.index + 1) % len(self.games)
            self.screen.audio.play_sfx("beep.wav")
        elif key == "\r":
            self.selected = self.games[self.index]
            self.screen.audio.play_sfx("select.wav")
            
            sleep(0.5)
            
            return False
        return True
    
    def render(self) -> None:
        print_x: int = (self.screen.w - max(len(line) for line in ARCANE_ART)) // 2
        print_y: int = 1
        
        for i, line in enumerate(ARCANE_ART):
            self.screen.put(print_x, print_y + i, f"{Ansi.FG.YELLOW}{line}{Ansi.RESET}")
        top: int = print_y + len(ARCANE_ART) + 2
        
        if not self.games:
            empty: str = f"{Ansi.FG.GREY}no cartridges found :({Ansi.RESET}"
            self.screen.put((self.screen.w - len(Ansi.strip(empty))) // 2, top, empty)
            return

        width: int = max(len(g.TITLE) for g in self.games) + 6
        x: int = (self.screen.w - width) // 2
        
        for i, game in enumerate(self.games):
            style = f"> {Ansi.BG.WHITE}{Ansi.FG.BLACK}" if i == self.index else Ansi.FG.GREY
            self.screen.put(x - (2 if i == self.index else 0), top + i, f"{style}{game.TITLE.center(width)}{Ansi.RESET}")
        return
    
    def load_cartridges(self) -> list[type[Game]]:
        for file in sorted(CARTRIDGES_ROOT.glob("*.py")):
            import_module(f"cartridges.{file.stem}")

        return [g for g in Game.__subclasses__() if g is not Menu]
        