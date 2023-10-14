# MIT License
# Copyright (c) 2023 Leos
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import json
import requests

#RPC
RPC_USER = 'your_rpc_username'
RPC_PASSWORD = 'your_rpc_password'
RPC_URL = 'http://127.0.0.1:15419/'

#RPCCALL
def rpc_call(method, params=None):
    payload = {
        'method': method,
        'jsonrpc': '2.0',
        'id': 1,
    }

    if params is not None:
        payload['params'] = params

    response = requests.post(RPC_URL, json=payload, auth=(RPC_USER, RPC_PASSWORD))

    if response.status_code != 200:
        raise Exception(f"RPC call failed with status code {response.status_code}: {response.text}")

    result = response.json().get('result')
    if result is None:
        raise Exception(f"RPC call failed: {response.json().get('error')}")

    return result

#GAMEID
def create_new_game():
    game_id = 'NEOXA'
    initial_board = [[' ']*3 for _ in range(3)]
    return game_id, initial_board

#MAKEMOVES
def make_move(board, player, row, col):
    if board[row][col] == ' ':
        board[row][col] = player
        return True
    return False

#WINNERS
def check_winner(board, player):
    #Check for a win
    for i in range(3):
        if all(board[i][j] == player for j in range(3)) or all(board[j][i] == player for j in range(3)):
            return True
    if all(board[i][i] == player for i in range(3)) or all(board[i][2-i] == player for i in range(3)):
        return True
    return False

#BOARD->METADATA
def board_to_metadata(board):
    flat_board = [cell for row in board for cell in row]
    metadata = ''.join(flat_board)
    return metadata

def submit_game_result(game_id, board, winner):
    metadata = board_to_metadata(board)
    hex_payload = metadata.encode().hex()

    # UTXO->TX
    unspent_outputs = rpc_call('listunspent')
    inputs = [{'txid': utxo['txid'], 'vout': utxo['vout']} for utxo in unspent_outputs]

    # Create the outputs object with the OP_RETURN data and an address for the transaction fee
    outputs = {
        'data': hex_payload,  # OP_RETURN data
        'GLXZRqjavBKAkjoQgDsKNnPAvdDBpTyEb4': 10  
        # Transaction fee amount in coins
        # Current Change works as e.g. balance used in address
        # as a whole ""utxo 100 , tx fee 10 , tx fee = 90 , change = 10
        #refactoring needed for this in reverse         
    }

    # Create
    raw_tx = rpc_call('createrawtransaction', [inputs, outputs])

    # Sign
    signed_tx = rpc_call('signrawtransaction', [raw_tx])

    # Send
    txid = rpc_call('sendrawtransaction', [signed_tx['hex']])

    return txid


# Main game loop
def main():
    game_id, board = create_new_game()
    player = 'X'
    winner = None

    while True:
        # Display the board
        for row in board:
            print(' '.join(row))
        print()

        # Get player's move
        row, col = map(int, input(f"Player {player}, enter row (0-2) and column (0-2) (e.g., '0 0'): ").split())

        # Make the move
        if make_move(board, player, row, col):
            # Check if there is a winner
            if check_winner(board, player):
                winner = player
                break

            # Switch to the other player
            player = 'X' if player == 'O' else 'O'

    # Display the final board
    for row in board:
        print(' '.join(row))
    print()

    # Submit the game result to the blockchain
    txid = submit_game_result(game_id, board, winner)
    print(f"Game ID: {game_id}")
    print(f"Winner: {winner}")
    print(f"Transaction ID: {txid}")

if __name__ == '__main__':
    main()
