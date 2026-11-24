#!/usr/bin/env python3
# agent_template.py — minimal agent (replace with your solver).
"""
How the agent talks to the game (run everything with: python controller.py)

The game sends JSON lines on stdin. After every move you get one "state":

  {"type": "state", "rows": 9, "cols": 9, "status": "playing",
   "mines": 10, "flags": 0, "elapsed": 12,
   "cells": [{"r": 0, "c": 0, "revealed": true, "flagged": false,
              "adjacent": 1, "mine": null}, ...]}

  status    "ready" (no clicks yet) | "playing" | "won" | "lost"
  adjacent  number of neighboring mines if revealed, else null
  mine      null until the game ends
  rows and columns are numbered from 0

You may also get events, which you can usually ignore, e.g.
  {"type": "event", "event": "error", "message": "(3, 4) is already revealed"}
An invalid move gets an error event followed by the unchanged state.

Reply by printing ONE command per state (always flush=True):
  left r c     reveal cell (r, c)        first click is always safe
  right r c    flag / unflag cell (r, c)
  reset        start a new game
  setdiff i    0 = Beginner, 1 = Intermediate, 2 = Expert (starts a new game)
  dump         ask for the current state again

Anything printed to stdout goes to the game. Use debug(...) for your own output;
it shows up in the controller's console as "[agent stderr] ...".
"""
import sys, json, random, time

MOVE_DELAY = 3       # seconds between moves (lower it while testing)
WIN_PAUSE = 1        # seconds to leave a won board on screen before resetting
LOSS_PAUSE = 200        # seconds to leave a lost board on screen before resetting
STOP_AFTER_WIN = False  # True: stay on the winning board instead of starting a new game

def debug(*args):
    print(*args, file=sys.stderr, flush=True)

def neighbors(r, c, rows, cols):
    """Yield the (row, col) of each of the up-to-8 cells around (r, c)."""
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0: continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc

def make_grid(state):
    """grid[r][c] -> that cell's dict from the state message."""
    grid = [[None] * state["cols"] for _ in range(state["rows"])]
    for cell in state["cells"]:
        grid[cell["r"]][cell["c"]] = cell
    return grid

class AgentMemory:
    def __init__(self):
        self.known_mines = set() # List of all mines known to the agent, will be used to flag multiple cells in sequential moves
        self.known_safe = set() # List of all cells known to be safe, will be used to reveal new cells in sequence
        self.completed_numbers = set() # List of number cells that have all their mines found/flagged
        self.first_turn = True
    def reset_memory(self):
        self.known_mines.clear()
        self.known_safe.clear()
        self.completed_numbers.clear()
        self.first_turn = True
    


    def check_memory(self):
        if not self.known_mines and not self.known_safe and not self.completed_numbers:
            return False
        else:
            return True



def choose_move(state, mem : AgentMemory):
    # Replace this with your solver: use make_grid() and neighbors() to reason
    # about which hidden cells are safe ("left") or must be mines ("right").
    need_help = False
    given_up = False
    previous_knowledge = mem.check_memory()
    first_turn = mem.first_turn
    cells = state["cells"]
    grid = make_grid(state)
    hidden = [(c["r"], c["c"]) for c in cells if not c["revealed"] and not c["flagged"]]      
    if(first_turn):
        debug("FIRST TURN : RAND")
        mem.first_turn = False
        r, c = random.choice(hidden)
        return f"left {r} {c}"
    numbers = [(c) for c in cells if c["revealed"] and c["adjacent"] > 0]
    cols = state["cols"]
    rows = state["rows"]
    known_mines = mem.known_mines ### references known_mines set in AgentMemory object
    known_safe = mem.known_safe ### references known_safe set in AgentMemory object
    completed_numbers = mem.completed_numbers ### you get it at this point
    if((len(known_mines) == 0 and len(known_safe) == 0) or (not known_mines and not known_safe)):
        debug("NONE LEFT TO EXPLORE, NEXT LAYER")
        for n in numbers:
            n_row = n["r"]
            n_col = n["c"]

            try:
                if (n_row, n_col) in completed_numbers:
                    continue
            except ValueError:
                pass
            n_num = n["adjacent"]
            hidden_list = []
            flag_list = []
            for adj_r, adj_c in neighbors(n_row, n_col, rows, cols):
                adj = grid[adj_r][adj_c]
                if not adj["revealed"] and not adj["flagged"]:
                    hidden_list.append((adj_r, adj_c))
                elif not adj["revealed"] and adj["flagged"]:
                    flag_list.append((adj_r, adj_c))
            num_hide = len(hidden_list)
            num_flag = len(flag_list)
            if num_flag == n_num and num_hide == 0:
                completed_numbers.add((n_row, n_col))
            elif num_flag == n_num and num_hide > 0:
                for h in hidden_list:
                    known_safe.add(h)
            elif num_hide > 0 and num_flag < n_num and num_hide + num_flag == n_num:
                for h in hidden_list:
                    known_mines.add(h)
    if(len(known_safe) == 0 and len(known_mines) == 0):
        need_help = True
     
    debug("FINISHING LAYER")
    debug(known_mines)
    debug(known_safe)
    while(len(known_mines) > 0):
        mine = known_mines.pop()
        if(grid[mine[0]][mine[1]]["flagged"]):
            continue
        else:
            return f"right {mine[0]} {mine[1]}"
    while(len(known_safe) > 0):
        safe = known_safe.pop()
        if grid[safe[0]][safe[1]]["revealed"]:
            continue
        else:
            return f"left {safe[0]} {safe[1]}"


    if(not known_safe and not known_mines and need_help):
        incomplete_nums = {}
        incomplete_keys = set()
        for n in numbers:
            r = n["r"]
            c = n["c"]
            if((r,c) in completed_numbers):
                continue
            else:
                incomplete_keys.add((r,c))
                hidden_set = set()
                set_value = n["adjacent"]
                adj_keys = []
                for adj_r, adj_c in neighbors(r,c, rows, cols):
                    adj = grid[adj_r][adj_c]
                    if not adj["revealed"] and not adj["flagged"]:
                        hidden_set.add((adj_r, adj_c))
                    elif not adj["revealed"] and adj["flagged"]:
                        set_value -= 1
                    elif adj["revealed"] and adj["adjacent"] > 0 and not (adj["r"], adj["c"]) in completed_numbers:
                        adj_keys.append((adj_r, adj_c))
                incomplete_nums[(r,c)] = (hidden_set, set_value, adj_keys)
                ### WHAT ABOUT COMPLETED NEIGHBORS??? WHO KNOWS
        ### starting from the edges
        for key in incomplete_keys:
            debug(f"key {key} : {incomplete_nums[key]}")
            num_a = incomplete_nums[key]
            for neighbor_key in num_a[2]:
                num_b = incomplete_nums[neighbor_key]
                # case 1: a is a subset of b, b - a = num bombs(b) - num bombs(a)
                if num_a[0].issubset(num_b[0]):
                    set_diff = num_b[0] - num_a[0]
                    diff_value = num_b[1] - num_a[1]
                    #case 1.1 |set diff| > 0, diff value == 0 -> all members of set diff are safe
                    if(len(set_diff) > 0 and diff_value == 0):
                        while(len(set_diff) > 0):
                            safe = set_diff.pop()
                            known_safe.add(safe)
                    # case 1.2 |set diff| > 0, diff value == |set diff| -> all members of set diff are mines
                    elif(len(set_diff) > 0 and len(set_diff) == diff_value):
                        while(len(set_diff) > 0):
                            mine = set_diff.pop()
                            known_mines.add(mine)
                    # case 1.3 |set diff| == 0 OR |set diff| > 0 and 0 < diff value < |set diff| -> no information acquired
                    else:
                        continue
                # case 2: set values differ between a and b
                elif num_a[1] != num_b[1]:
                    if(num_a[1] < num_b[1]):
                        set_diff = num_b[0] - num_a[0]
                        diff_value = num_b[1] - num_a[1]
                        # case 2.1: |set diff| > 0 and diff value == 0 -> all members of set diff are safe
                        if(len(set_diff) > 0 and diff_value == 0):
                            while(len(set_diff) > 0):
                                safe = set_diff.pop()
                                known_safe.add(safe)
                        # case 2.2: |set diff| > 0 and diff value == |set diff| -> all members of set diff are mines
                        if(len(set_diff) > 0 and diff_value == len(set_diff)):
                            while(len(set_diff) > 0):
                                mine = set_diff.pop()
                                known_mines.add(mine)

        
        
        if len(known_mines) == 0 and len(known_safe) == 0:
            given_up = True
        else:
                debug("ACTING ON SET ANALYSIS")
                debug(known_mines)
                debug(known_safe)
                while(len(known_mines) > 0):
                    mine = known_mines.pop()
                    if(grid[mine[0]][mine[1]]["flagged"]):
                        continue
                    else:
                        return f"right {mine[0]} {mine[1]}"
                while(len(known_safe) > 0):
                    safe = known_safe.pop()
                    if grid[safe[0]][safe[1]]["revealed"]:
                        continue
                    else:
                        return f"left {safe[0]} {safe[1]}"

        
    debug("nothing found, random choice...")
    if not hidden:
        return None
    elif (need_help and given_up):
        r, c = random.choice(hidden)
        return f"left {r} {c}"

def main():
    stopped = False
    memory = AgentMemory()
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("type") == "event" and msg.get("event") == "error":
            debug("game rejected a command:", msg.get("message"))
            continue
        if msg.get("type") != "state":
            continue
        status = msg.get("status")
        if stopped:
            if status != "ready":
                continue  # sitting on the winning board until someone presses Reset
            stopped = False
        if status == "won":
            debug("WON!")
            if STOP_AFTER_WIN:
                stopped = True
                continue
            time.sleep(WIN_PAUSE)
            memory.reset_memory()
            print("reset", flush=True)
            continue
        if status == "lost":
            time.sleep(LOSS_PAUSE)
            memory.reset_memory()
            print("reset", flush=True)
            continue
        move = choose_move(msg, memory)
        time.sleep(MOVE_DELAY)
        print(move if move else "dump", flush=True)

if __name__ == "__main__":
    main()
