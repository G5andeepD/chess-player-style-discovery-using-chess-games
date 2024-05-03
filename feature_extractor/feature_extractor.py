import chess
import chess.pgn
import pandas as pd
import random

def extract_features(game, game_id, player_id_white, player_id_black):
    board = game.board()

    features = {
        'white': initialize_features(),
        'black': initialize_features(),
        'game_id': game_id,
        'player_id_white': player_id_white,
        'player_id_black': player_id_black
    }

    for move in game.mainline_moves():
        board.push(move)
        
        if board.turn != chess.WHITE:
            features['white'] = update_features(features['white'], board, "white")
        else:
            features['black'] = update_features(features['black'], board, 'black')

    features['white']['game_id'] = game_id
    features['white']['player_id'] = player_id_white
    features['black']['game_id'] = game_id
    features['black']['player_id'] = player_id_black

    return features['white'], features['black']

# Additional function implementations...



def initialize_features():
    # Initialize all feature scores to zero
    return {
        'center_control_score': 0,
        'piece_activity_score': 0,
        'king_safety_score': 0,
        'attacking_moves_score': 0,
        'captures_score': 0,
        'pawn_structure_score': 0
    }

def update_features(feature_dict, board,color):
    # Update each feature score based on the current board state
    feature_dict['center_control_score'] += calculate_center_control(board,color)
    feature_dict['piece_activity_score'] += calculate_piece_activity(board,color)
    feature_dict['king_safety_score'] += calculate_king_safety(board,color)
    feature_dict['attacking_moves_score'] += calculate_attacking_moves(board,color)
    feature_dict['captures_score'] += calculate_captures(board,color)
    feature_dict['pawn_structure_score'] += calculate_pawn_structure(board,color)
    return feature_dict
    

def calculate_center_control(board,color):
    # Define central squares
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    center_control = 0

    # Iterate over each central square
    for square in center_squares:
        # Check for pieces on the square and count them
        if board.piece_at(square):
            center_control += 1
        
        # Count attackers to each central square
        # For White
        if color == 'white':
            white_attackers = board.attackers(chess.WHITE, square)
            center_control += len(white_attackers)
        else:
            black_attackers = board.attackers(chess.BLACK, square)
            center_control += len(black_attackers)
        

    return center_control

def calculate_piece_activity(board, color):
    activity_score = 0
    chess_color = chess.WHITE if color == 'white' else chess.BLACK

    # Using items() to retrieve both the square and the piece
    for square, piece in board.piece_map().items():
        if piece.color == chess_color:
            # Calculate the number of attacked squares from this square
            activity_score += len(board.attacks(square))
    return activity_score

def calculate_king_safety(board, color):
    king_safety_score = 0
    chess_color = chess.WHITE if color == 'white' else chess.BLACK
    enemy_color = not chess_color
    king_square = board.king(chess_color)

    # Count guards
    own_guardians = board.attackers(chess_color, king_square)
    king_safety_score += len(own_guardians)

    # Count attacking enemy pieces
    enemy_attackers = board.attackers(enemy_color, king_square)
    king_safety_score -= len(enemy_attackers)

    # Consider pawn structure
    for pawn_square in board.pieces(chess.PAWN, chess_color):
        if board.is_attacked_by(chess_color, pawn_square):
            king_safety_score += 1

    return king_safety_score

def calculate_attacking_moves(board, color):
    attacking_moves_score = 0
    chess_color = chess.WHITE if color == 'white' else chess.BLACK
    #last_move = board.peek()  # Get the last move made
    if board.move_stack:
        last_move = board.peek()
        #print(last_move)
        if last_move:
            # Determine the square from which the piece moved and where it moved to
            moved_piece = board.piece_at(last_move.to_square)
            if moved_piece and moved_piece.color == chess_color:
                # Get the squares attacked by this piece from its new position
                attacked_squares = board.attacks(last_move.to_square)
                for square in attacked_squares:
                    #print(square)
                    rank = chess.square_rank(square)+1
                    file = chess.square_file(square)+1

                    #print('Rank:', rank)
                    #print('File:', file)


                    # Score based on depth of attack
                    if chess_color == chess.WHITE:
                        # Attacking towards rank 8
                        rank_score = max(0, rank - 4)
                    else:
                        # Attacking towards rank 1
                        rank_score = max(0, 7 - rank - 4)
                    #print('Rank Score:', rank_score)
                    # Increment score if attacking enemy territory
                    if board.color_at(square) != chess_color:

                        piece_at_target = board.piece_at(square)
                        if piece_at_target:
                            # Basic value of the piece, for simplicity using piece type value
                            piece_value = 1 + (piece_at_target.piece_type - 1) * 2  # Simplified scoring
                            # Check if the square is defended
                            defenders = board.attackers(chess_color, square)
                            if len(defenders) == 0:
                                # No defenders, add full piece value
                                attacking_moves_score += piece_value
                            else:
                                # Reduce value based on number of defenders
                                attacking_moves_score += piece_value - len(defenders)
                        attacking_moves_score += (rank_score * 2)  # Adjust depth score

                    # Special scoring for check
                    if board.is_check():
                        attacking_moves_score += 10  # Arbitrary score for delivering check

    
    return attacking_moves_score

def calculate_pawn_structure(board, color):
    pawn_structure_score = 0
    chess_color = chess.WHITE if color == 'white' else chess.BLACK
    pawns = board.pieces(chess.PAWN, chess_color)
    file_dict = {}

    for pawn in pawns:
        file = chess.square_file(pawn)
        if file in file_dict:
            file_dict[file] += 1
        else:
            file_dict[file] = 1

    # Penalize doubled pawns
    for count in file_dict.values():
        if count > 1:
            pawn_structure_score -= count - 1

    # Check for isolated pawns
    for file, count in file_dict.items():
        if count > 0:
            if (file == 0 or file_dict.get(file - 1, 0) == 0) and (file == 7 or file_dict.get(file + 1, 0) == 0):
                pawn_structure_score -= count

    return pawn_structure_score

def calculate_captures(board, color):
    captures = 0
    for move in board.legal_moves:
        if board.is_capture(move):
            captures += 1
    return captures


def get_player_details(game, color):
    # Placeholder function to extract player details
    return {
        "player_id": game.headers[f"{color}Id"] if f"{color}Id" in game.headers else "unknown",
        "name": game.headers[color],
        "result": game.headers['Result'],
        "color": color
    }

# Initialize DataFrames
columns = ['center_control_score', 'piece_activity_score', 'king_safety_score',
           'attacking_moves_score', 'captures_score', 'pawn_structure_score', 'game_id', 'player_id']
data = pd.DataFrame(columns=columns)
player_games_list = []
players_list = []

# Loop to process each game
pgn = open('wchcand24.pgn')
game = chess.pgn.read_game(pgn)
game_id = 0

while game:
    game_id += 1  # Increment game ID for each new game
    for color in ['white', 'black']:
        player_info = get_player_details(game, color)
        player_games_list.append({**player_info, "game_id": game_id})
        
        if not any(player['player_id'] == player_info['player_id'] for player in players_list):
            players_list.append({
                "player_id": player_info['player_id'],
                "name": player_info['name'],
                # Additional details like country, rating can be added here
            })

        # Extract and save game features
        features = extract_features(game, game_id, player_info['player_id'],color)
        data = pd.concat([data, pd.DataFrame([features])], ignore_index=True)

    # Prepare for the next game
    game = chess.pgn.read_game(pgn)

# Convert lists to DataFrames
player_games = pd.DataFrame(player_games_list)
players = pd.DataFrame(players_list)

# Save all to CSV
data.to_csv('chess_features.csv', index=False)
player_games.to_csv('player_games.csv', index=False)
players.to_csv('player.csv', index=False)

