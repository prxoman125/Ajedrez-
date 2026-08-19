import streamlit as st
import chess
# CAMBIO AQUÍ: Usamos la librería correcta 'stchess'
from stchess import board as st_chess

st.set_page_config(page_title="IA Ajedrez Personalizado", layout="centered")
st.title("♟️ Analizador de Ajedrez con Tu Color")
st.write("Elige tu bando. Mueve las piezas del rival manualmente y la IA resolverá la fórmula para tu bando.")

# 1. Selección de Color del Usuario
user_color_str = st.radio("Selecciona tu bando:", ("Blancas", "Negras"), horizontal=True)
user_is_white = (user_color_str == "Blancas")

# 2. Inicializar el Tablero en el Estado de la Sesión
if "board_fen" not in st.session_state:
    st.session_state.board_fen = chess.STARTING_FEN

board = chess.Board(st.session_state.board_fen)

# --- FÓRMULA MATEMÁTICA DE EVALUACIÓN ---
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10,-20,-20, 10, 10,  5,
    5, -5,-10,  0,  0,-10, -5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

def evaluate_board(b):
    if b.is_checkmate():
        return -99999 if b.turn == chess.WHITE else 99999
    score = 0
    for square in chess.SQUARES:
        piece = b.piece_at(square)
        if piece is not None:
            val = PIECE_VALUES[piece.piece_type]
            pos_bonus = 0
            if piece.piece_type == chess.PAWN:
                pos_bonus = PAWN_TABLE[square if piece.color == chess.WHITE else chess.square_mirror(square)]
            elif piece.piece_type == chess.KNIGHT:
                pos_bonus = KNIGHT_TABLE[square if piece.color == chess.WHITE else chess.square_mirror(square)]
            
            if piece.color == chess.WHITE:
                score += (val + pos_bonus)
            else:
                score -= (val + pos_bonus)
    mobility = b.legal_moves.count()
    score += (mobility * 10) if b.turn == chess.WHITE else -(mobility * 10)
    return score

def minimax(b, depth, alpha, beta, maximizing_player):
    if depth == 0 or b.is_game_over():
        return evaluate_board(b), None
    best_move = None
    if maximizing_player:
        max_eval = -float('inf')
        for move in b.legal_moves:
            b.push(move)
            evaluation, _ = minimax(b, depth - 1, alpha, beta, False)
            b.pop()
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha: break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in b.legal_moves:
            b.push(move)
            evaluation, _ = minimax(b, depth - 1, alpha, beta, True)
            b.pop()
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha: break
        return min_eval, best_move

# --- INTERFAZ VISUAL DEL TABLERO ---
st.write(f"**Turno actual del juego:** {'Blancas' if board.turn == chess.WHITE else 'Negras'}")

# Renderizar tablero interactivo que permite arrastrar piezas
# 'orientation' voltea el tablero para comodidad del usuario
board_orientation = "white" if user_is_white else "black"
chess_move = st_chess(fen=st.session_state.board_fen, orientation=board_orientation, key="chess_board")

# Detectar si el usuario movió una pieza en la pantalla
if chess_move and chess_move.get("fen") and chess_move["fen"] != st.session_state.board_fen:
    st.session_state.board_fen = chess_move["fen"]
    st.rerun()

# --- LÓGICA DE ANÁLISIS ---
st.write("---")

# Comprobar si es el turno del bando del usuario
is_user_turn = (board.turn == chess.WHITE and user_is_white) or (board.turn == chess.BLACK and not user_is_white)

if is_user_turn:
    st.info("💡 **Es tu turno.** Presiona el botón para que la fórmula matemática calcule tu mejor opción estratégica.")
    if st.button("🧮 Calcular mi mejor jugada", use_container_width=True):
        with st.spinner("Resolviendo ecuaciones de posición..."):
            # Profundidad 3 para balancear velocidad y precisión
            score, best_move = minimax(board, depth=3, alpha=-float('inf'), beta=float('inf'), maximizing_player=user_is_white)
        
        if best_move:
            from_sq = chess.square_name(best_move.from_square)
            to_sq = chess.square_name(best_move.to_square)
            piece_moved = board.piece_at(best_move.from_square)
            piece_name = chess.piece_name(piece_moved.piece_type).upper() if piece_moved else "PIEZA"
            
            st.success("🎯 **¡Movimiento matemático óptimo encontrado!**")
            st.markdown(f"* **Pieza a mover:** {piece_name}")
            st.markdown(f"* **Desde la casilla:** `{from_sq.upper()}`")
            st.markdown(f"* **Hacia la casilla:** `{to_sq.upper()}`")
            st.caption(f"Valor matemático neto de la posición: {score / 100.0} puntos.")
            
            # Guardamos la sugerencia para poder ejecutarla automáticamente si el usuario quiere
            st.session_state.ai_suggested_move = best_move
else:
    st.warning("⏳ **Turno del Rival.** Mueve directamente las piezas del oponente en el tablero de arriba para simular su jugada.")

# Botón opcional para aplicar la jugada de la IA directamente
if "ai_suggested_move" in st.session_state and is_user_turn:
    if st.button("🤖 Aplicar movimiento sugerido por la IA", type="primary", use_container_width=True):
        board.push(st.session_state.ai_suggested_move)
        st.session_state.board_fen = board.fen()
        del st.session_state.ai_suggested_move
        st.rerun()

# Botón para resetear la partida
if st.button("♻️ Reiniciar Partida", type="secondary"):
    st.session_state.board_fen = chess.STARTING_FEN
    if "ai_suggested_move" in st.session_state:
        del st.session_state.ai_suggested_move
    st.rerun()
 
