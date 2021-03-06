import sys
import os
import json
from enum import Enum
from dataclasses import dataclass
import svgwrite
import itertools
import copy
import time


class CellState(Enum):
    UNTOUCHED = 0
    EMPTY = 1
    FILLED = 2


@dataclass
class Cell():
    value: int
    state: CellState


def read_puzzle(path):
    with open(path) as file:
        content = file.read()
        content = content.replace("\n", "")
        puzzle = json.loads(content)
        return puzzle


def make_cell(c):
    if c == '.':
        return Cell(None, CellState.UNTOUCHED)
    else:
        return Cell(ord(c) - 0x30, CellState.UNTOUCHED)


def convert_puzzle_to_board(puzzle):
    parsed = [[make_cell(c) for c in row] for row in puzzle]
    return list(map(list, zip(*parsed)))


def print_board(board):
    height = len(board[0])
    width = len(board)

    for y in range(height):
        s = ""
        for x in range(width):
            if board[x][y].state == CellState.UNTOUCHED:
                if board[x][y].value == None:
                    s += "."
                else:
                    s += str(board[x][y].value)
            elif board[x][y].state == CellState.EMPTY:
                s += "O"
            elif board[x][y].state == CellState.FILLED:
                s += "X"
        print(s)


def draw_board(board, name):
    height = len(board[0])
    width = len(board)
    size = 30
    dwg = svgwrite.Drawing("out/" + name + ".svg",
                           size=(width*size, height*size))

    for y in range(height):
        for x in range(width):
            group = dwg.g()
            text_inset = (x*size + size/3, y*size + size - size/3)
            if board[x][y].state == CellState.EMPTY:
                group.add(dwg.rect((size*x, size*y), (size, size),
                                   stroke="black", fill="gray"))
                if board[x][y].value != None:
                    group.add(
                        dwg.text(str(board[x][y].value), text_inset, fill="black"))
            elif board[x][y].state == CellState.FILLED:
                group.add(dwg.rect((size*x, size*y), (size, size),
                                   stroke="black", fill="black"))
                if board[x][y].value != None:
                    group.add(
                        dwg.text(str(board[x][y].value), text_inset, fill="white"))
            else:
                group.add(dwg.rect((size*x, size*y), (size, size),
                                   stroke="black", fill="white"))
                if board[x][y].value != None:
                    group.add(
                        dwg.text(str(board[x][y].value), text_inset, fill="black"))
            dwg.add(group)
    dwg.save()


def fill_board(board, center, value):
    x = center[0]
    y = center[1]
    height = len(board[0])
    width = len(board)

    for sx in [x-1, x, x+1]:
        for sy in [y-1, y, y+1]:
            if sx < 0 or sx >= width or sy < 0 or sy >= height:
                pass
            else:
                if board[sx][sy].state == CellState.UNTOUCHED:
                    board[sx][sy].state = value


def fill_cells(board, coords, value):
    height = len(board[0])
    width = len(board)

    changed = False
    for coord in coords:
        x, y = coord
        if x < 0 or x >= width or y < 0 or y >= height:
            pass
        else:
            if board[x][y].state == CellState.UNTOUCHED:
                board[x][y].state = value
                changed = True
    return changed


def get_cell(board, x, y):
    height = len(board[0])
    width = len(board)

    if x < 0 or x >= width or y < 0 or y >= height:
        return None
    return board[x][y]


def solve_puzzle(board):
    height = len(board[0])
    width = len(board)

    nice_cells = []
    for y in range(height):
        for x in range(width):
            if board[x][y].value != None:
                nice_cells.append((x, y, board[x][y].value))

    return solver(board, nice_cells, 0)


# returns (board, solved, iter_cnt)
def solver(board, nice_cells, iter_cnt):
    height = len(board[0])
    width = len(board)

    updated = True
    while updated:
        #print("\niteration " + str(iter_cnt))
        iter_cnt += 1

        updated = False
        new_nice_cells = []
        for c in nice_cells:
            x = c[0]
            y = c[1]
            cell = board[x][y]

            empty = 0
            filled = 0
            neighbor_cells = 9
            for sx in [x-1, x, x+1]:
                for sy in [y-1, y, y+1]:
                    if sx < 0 or sx >= width or sy < 0 or sy >= height:
                        neighbor_cells -= 1
                    else:
                        if board[sx][sy].state == CellState.EMPTY:
                            empty += 1
                        elif board[sx][sy].state == CellState.FILLED:
                            filled += 1

            if cell.value < filled or 9 - cell.value < empty:
                #print("cell is invalid, returning: " + str((x, y)))
                return (board, False, iter_cnt)

            # fill all nighbor (4 in corner; 6 on edge; 9)
            if neighbor_cells == cell.value:
                fill_board(board, (x, y), CellState.FILLED)
                #print("filled cell (corner case): "+ str((x, y)))
                updated = True
            # empty all neighbor (0)
            elif cell.value == 0:
                fill_board(board, (x, y), CellState.EMPTY)
                updated = True
                #print("emptied cell (value 0): "+ str((x, y)))
            # if enough empty: fill rest
            elif empty == neighbor_cells - cell.value:
                fill_board(board, (x, y), CellState.FILLED)
                updated = True
                #print("filled cell (known all empty): " + str((x, y)))
            # if enough filled: empty rest
            elif filled == cell.value:
                fill_board(board, (x, y), CellState.EMPTY)
                #print("emptied cell (known all filled): " + str((x, y)))
                updated = True
            else:
                # check if any known solution met (pairs )
                left_cell = get_cell(board, x-1, y)
                right_cell = get_cell(board, x+1, y)
                up_cell = get_cell(board, x, y-1)
                down_cell = get_cell(board, x, y+1)

                if left_cell != None and left_cell.value != None and cell.value - left_cell.value >= 3:
                    filled = fill_cells(
                        board, [(x+1, y-1), (x+1, y),  (x+1, y+1)], CellState.FILLED)
                    # if filled:
                    #print("filled right column: " + str((x, y)))
                    updated = updated or filled

                if right_cell != None and right_cell.value != None and cell.value - right_cell.value >= 3:
                    filled = fill_cells(
                        board, [(x-1, y-1), (x-1, y),  (x-1, y+1)], CellState.FILLED)
                    # if filled:
                    #print("filled left column: " + str((x, y)))
                    updated = updated or filled

                if up_cell != None and up_cell.value != None and cell.value - up_cell.value >= 3:
                    filled = fill_cells(
                        board, [(x-1, y+1), (x, y+1),  (x+1, y+1)], CellState.FILLED)
                    # if filled:
                    #print("filled down row: " + str((x, y)))
                    updated = updated or filled

                if down_cell != None and down_cell.value != None and cell.value - down_cell.value >= 3:
                    filled = fill_cells(
                        board, [(x-1, y-1), (x, y-1),  (x+1, y-1)], CellState.FILLED)
                    # if filled:
                    #print("filled upper row: " + str((x, y)))
                    updated = updated or filled

                # TODO: add corner cases

                # todo: add same numbers on edge cases
                if y == 1 and up_cell != None and up_cell.value != None and cell.value == up_cell.value:
                    filled = fill_cells(
                        board, [(x-1, y+1), (x, y+1),  (x+1, y+1)], CellState.EMPTY)
                    #print("emptied upper row: " + str((x, y)))
                    updated = updated or filled

                if y == height-2 and down_cell != None and down_cell.value != None and cell.value == down_cell.value:
                    filled = fill_cells(
                        board, [(x-1, y-1), (x, y-1),  (x+1, y-1)], CellState.EMPTY)
                    # if filled:
                    #print("emptied lower row: " + str((x, y)))
                    updated = updated or filled

                if x == 1 and left_cell != None and left_cell.value != None and cell.value == left_cell.value:
                    filled = fill_cells(
                        board, [(x+1, y-1), (x+1, y),  (x+1, y+1)], CellState.EMPTY)
                    # if filled:
                    #print("emptied right column: " + str((x, y)))
                    updated = updated or filled

                if x == width-2 and right_cell != None and right_cell.value != None and cell.value == right_cell.value:
                    filled = fill_cells(
                        board, [(x-1, y-1), (x-1, y),  (x-1, y+1)], CellState.EMPTY)
                    # if filled:
                    #print("emptied left column: " + str((x, y)))
                    updated = updated or filled

                new_nice_cells.append(c)
        nice_cells = new_nice_cells
        # print_board(board)
        #draw_board(board, "iter_"+str(iter_cnt))

    if len(nice_cells) == 0:
        return (board, True, iter_cnt)

        # branch: generate all boards for nice cell
    c = nice_cells[0]
    x = c[0]
    y = c[1]
    cell = board[x][y]
    #print("branching at: " + str((x, y)))
    result_board = None
    empty = []
    filled = []
    untouched = []
    for sx in [x-1, x, x+1]:
        for sy in [y-1, y, y+1]:
            if sx < 0 or sx >= width or sy < 0 or sy >= height:
                pass
            else:
                if board[sx][sy].state == CellState.EMPTY:
                    empty.append((sx, sy))
                elif board[sx][sy].state == CellState.FILLED:
                    filled.append((sx, sy))
                elif board[sx][sy].state == CellState.UNTOUCHED:
                    untouched.append((sx, sy))

    available = cell.value - len(filled)
    for comb in itertools.combinations(untouched, available):
        new_board = copy.deepcopy(board)
        for cords in comb:
            new_board[cords[0]][cords[1]].state = CellState.FILLED
        # print("\nbranch")
        # print_board(new_board)
        #draw_board(new_board, "iter_"+str(iter_cnt)+"_branch")
        sorted_cells = sorted(nice_cells, key=lambda p: (
            p[0] - x)**2 + (p[1] - y)**2)
        result_board, solved, iter_cnt = solver(
            new_board, sorted_cells, iter_cnt)
        if solved:
            return (result_board, True, iter_cnt)

    return (result_board, False, iter_cnt)
    # possible cut for repeated branches


def main():
    puzzle_path = sys.argv[1]
    puzzle = read_puzzle(puzzle_path)
    board = convert_puzzle_to_board(puzzle)

    start_time = time.time()

    draw_board(board, "input")
    result_board, solved, iterations = solve_puzzle(board)

    elapsed_time = time.time() - start_time
    print('Execution time max: ' + str((elapsed_time)))

    print("\nresult")
    print_board(result_board)
    draw_board(result_board, "final")
    print(solved)
    print(iterations)


if __name__ == "__main__":
    main()

# Optimizations
# next to wall if difference between two neighbor cell values is 2 then shared space determines one row
# if difference between two neighbor cell values is 3 then shared space determines one row
