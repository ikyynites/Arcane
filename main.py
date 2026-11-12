from msvcrt import kbhit, getwch
from os import get_terminal_size
from platform import system
from time import sleep

# prevent __pycache__ folders from generating
import sys
sys.dont_write_bytecode = True

from engine import *

SKIP_BOOT_DBG: bool = True

if __name__ == "__main__":
    if system().lower() != "windows":
        # TODO: implement cross-platform keyboard input
        raise OSError("arcane is only supported on windows due to use of the \"msvcrt\" module for keyboard input.")
    
    with Screen(*get_terminal_size(), title="arcane - ikyyn's arcade") as screen:
        # TODO: games planned:
        # 1. tetris
        # 2. pacman
        # 3. snake
        # 4. minesweeper
        # 5. asteroids (research)
        # 6. space invaders
        # 7. breakout
        
        # HARDCODED BOOTUP SEQUENCE
        if not SKIP_BOOT_DBG:
            x: int = (screen.w - max(len(line) for line in ARCANE_ART)) // 2
            y: int = (screen.h - len(ARCANE_ART)) // 3 # put title 1/3 down
            
            tag: str = f"{Ansi.FG.BLUE}{Ansi.ITALIC}~ powered by ikyyn ~{Ansi.RESET}"
            play: str = f"{Ansi.FG.GREY}{Ansi.ITALIC}press any key to start ...{Ansi.RESET}"
            
            screen.audio.play_sfx("coin-drop.wav")
            sleep(1.58)
            
            screen.audio.play_sfx("start.wav")
            
            # first render block - startup sound
            for beep in range(3): # 3x 2-line chunks
                for i, line in enumerate(ARCANE_ART[:2*(beep + 1)]): # write title in 2-line chunks
                    screen.put(x, y + i, f"{Ansi.FG.YELLOW}{line}{Ansi.RESET}")
                screen.present()
                sleep(0.28)
            
            # second render block - full title
            for i, line in enumerate(ARCANE_ART): # write whole title
                screen.put(x, y + i, f"{Ansi.FG.YELLOW}{line}{Ansi.RESET}")
            screen.put((screen.w - len(Ansi.strip(tag))) // 2, y + len(ARCANE_ART) + 1, tag) # put tag 1 below title
            
            screen.present()
            
            # last render block - press to play
            for i, line in enumerate(ARCANE_ART): # write whole title
                screen.put(x, y + i, f"{Ansi.FG.YELLOW}{line}{Ansi.RESET}")
            screen.put((screen.w - len(Ansi.strip(tag))) // 2, y + len(ARCANE_ART) + 1, tag) # put tag 1 below title
            screen.put((screen.w - len(Ansi.strip(play))) // 2, (screen.h * 3) // 4, play) # put play 3/4 down
            
            sleep(1.0)
            screen.audio.play_sfx("beep.wav")
            screen.present()
            
            # clear stdin
            while kbhit():
                getwch()
            
            getwch()
        
        menu: Menu = Menu(screen)
        
        while True:
            menu.selected = None
            menu.start()
            
            if menu.selected is None:
                break
            
            menu.selected(screen).start()
        