"""
Play GROT game.
"""

import http.client
import json
import math
import random
import time

BOARD_SIZE = 5


def get_flattened_augmented_board(data):
    cells = [cell for row in data['board'] for cell in row]
    for cell in cells:
        score, length = get_score_and_cleared_from_move(data, cell['x'], cell['y'])
        cell['total_points'] = score
        cell['cleared'] = length
    return cells

def get_move_with_most_cell_points(data):
    cells = get_flattened_augmented_board(data)
    cell = sorted(cells, key=lambda cell: cell['points'], reverse=True)[0]
    return cell

def get_move_with_most_total_points(data):
    cells = get_flattened_augmented_board(data)
    cell = sorted(cells, key=lambda cell: cell['total_points'], reverse=True)[0]
    return cell

def get_move_with_most_length(data):
    cells = get_flattened_augmented_board(data)
    cell = sorted(cells, key=lambda cell: cell['cleared'], reverse=True)[0]
    return cell

def get_move_with_most_length_points(data):
    cells = get_flattened_augmented_board(data)
    cells = sorted(cells, key=lambda cell: cell['total_points'], reverse=True)
    cells = sorted(cells, key=lambda cell: cell['cleared'], reverse=True)
    return cells[0]

def get_move_with_most_length_unless_no_bonus(data):
    cells = get_flattened_augmented_board(data)
    for cell in cells:
        _, length = get_score_and_cleared_from_move(data, cell['x'], cell['y'])
        cell['cleared'] = length
    cell = sorted(cells, key=lambda cell: cell['cleared'], reverse=True)[0]

    threshold = math.floor(data['score'] / (5 * BOARD_SIZE * BOARD_SIZE)) + BOARD_SIZE - 1
    if cell['cleared'] <= threshold:
        return get_move_with_most_total_points(data)

    return cell

def get_move_with_most_length_points_unless_no_bonus(data):
    cells = get_flattened_augmented_board(data)
    cells = sorted(cells, key=lambda cell: cell['total_points'], reverse=True)
    cells = sorted(cells, key=lambda cell: cell['cleared'], reverse=True)
    cell = cells[0]

    threshold = math.floor(data['score'] / (5 * BOARD_SIZE * BOARD_SIZE)) + BOARD_SIZE - 1
    if cell['cleared'] <= threshold:
        return get_move_with_most_total_points(data)

    return cell

get_move = get_move_with_most_length_points_unless_no_bonus


def get_score_and_cleared_from_move(data, x, y):
    board = [row[:] for row in data['board']]  # Deep copy board so we can edit

    # Create a flag to indicate whether the cell is still present on the board
    for row in board:
        for cell in row:
            cell['present'] = True

    score = 0
    cleared_cells = 0

    # Walk around following the arrows
    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
        cell = board[y][x]

        # Skip over cells no longer present
        if cell['present']:
            score = score + cell['points']
            cleared_cells = cleared_cells + 1

            if cell['direction'] == 'up':
                dx, dy = 0, -1
            elif cell['direction'] == 'down':
                dx, dy = 0, 1
            elif cell['direction'] == 'left':
                dx, dy = -1, 0
            elif cell['direction'] == 'right':
                dx, dy = 1, 0

            cell['present'] = False

        x = x + dx
        y = y + dy

    # Add bonus points for cleared rows
    for y in range(BOARD_SIZE):
        cleared = True
        for x in range(BOARD_SIZE):
            if board[y][x]['present']:
                cleared=False
                break
        if cleared:
            score = score + 10 * BOARD_SIZE

    # Add bonus points for cleared columns
    for x in range(BOARD_SIZE):
        cleared = True
        for y in range(BOARD_SIZE):
            if board[y][x]['present']:
                cleared=False
                break
        if cleared:
            score = score + 10 * BOARD_SIZE

    return score, cleared_cells

def play(room_id, token, server, debug=False, alias=''):
    """
    Connect to game server and play rounds in the loop until end of game.
    """
    # connect to the game server
    client = http.client.HTTPConnection(server)
    client.connect()
    game_url = '/games/{}/board?token={}'.format(room_id, token)
    if alias:
        game_url += '&alias={}'.format(alias)

    # wait until the game starts
    client.request('GET', game_url)

    response = client.getresponse()

    while response.status == 200:
        data = json.loads(response.read().decode())
        if debug:
            print(data)
            # sleep 3 seconds so, you will be able to read printed data
            time.sleep(3)

        # make your move and wait for a new round
        client.request('POST', game_url, json.dumps(get_move(data)))

        response = client.getresponse()
