import streamlit as st
import chess
import chess.svg
import base64

# Configuración de la página
st.set_page_config(page_title="IA de Ajedrez - Fórmula de Evaluación", layout="centered")
st.title("♟️ Evaluador de Movimientos de Ajedrez")
st.write("Esta IA resuelve la función de evaluación matemática para encontrar el mejor movimiento.")

# Inicializar el estado del tablero si no existe
if "board" not in st.session_state:
    st.session_state.board = chess.Board()

# --- FÓRMULA MATEMÁTICA DE EVALUACIÓN ---
# Valores estándar de las piezas (V_p)
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Matrices de posición simplificadas (P_p) para maximizar el control del centro
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

def evaluate_board(board):
    """Resuelve la ecuación E(T) para el estado actual del tablero."""
    if board.is_checkmate():
        if board.turn == chess.WHITE:
            return -99999
        else:
            return 99999
            
    score = 0
    # Sumatoria de Material (V_p) y Posición (P_p)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            # Obtener valor base de la pieza
            val = PIECE_VALUES[piece.piece_type]
            
            # Sumar bono por posición central
            pos_bonus = 0
            if piece.piece_type == chess.PAWN:
                pos_bonus = PAWN_TABLE[square if piece.color == chess.WHITE else chess.square_mirror(square)]
            elif piece.piece_type == chess.KNIGHT:
                pos_bonus = KNIGHT_TABLE[square if piece.color == chess.WHITE else chess.square_mirror(square)]
            
            # Sumar si son blancas, restar si son negras
            if piece.color == chess.WHITE:
                score += (val + pos_bonus)
            else:
                score -= (val + pos_bonus)
                
    # Movilidad (M_b): Añade un pequeño bono por cantidad de movimientos legales disponibles
    mobility = board.legal_moves.count()
    if board.turn == chess.WHITE:
        score += mobility * 10
    else:
        score -= mobility * 10
        
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """Algoritmo Minimax con podas Alfa-Beta para optimizar la búsqueda."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    best_move = None
    if maximizing_player:
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            evaluation, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_eval, best_move

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

# Renderizar el tablero en formato SVG compatible con Streamlit
def render_board(board):
    board_svg = chess.svg.board(board=board, size=400)
    b64 = base64.b64encode(board_svg.encode('utf-8')).decode('utf-8')
    return f'<div style="display: flex; justify-content: center;"><img src="data:image/svg+xml;base64,{b64}"/></div>'
# LÍNEA CORREGIDA:
st.markdown(render_board(st.session_state.board), unsafe_allow_html=True)

# Controles y lógica de cálculo
st.write("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🤖 Calcular Mejor Movimiento", use_container_width=True):
        if not st.session_state.board.is_game_over():
            # Determinar si la IA juega con Blancas (Maximizar) o Negras (Minimizar)
            is_white = st.session_state.board.turn == chess.WHITE
            
            with st.spinner("Resolviendo fórmulas matemáticas..."):
                # Profundidad 3 para un cálculo rápido pero inteligente
                score, best_move = minimax(st.session_state.board, depth=3, alpha=-float('inf'), beta=float('inf'), maximizing_player=is_white)
            
            if best_move:
                # Traducir el movimiento a datos legibles de pieza y casillas
                from_square = chess.square_name(best_move.from_square)
                to_square = chess.square_name(best_move.to_square)
                piece_moved = st.session_state.board.piece_at(best_move.from_square)
                piece_name = chess.piece_name(piece_moved.piece_type).upper()
                
                # Guardar el movimiento sugerido en el estado
                st.session_state.sug_move = best_move
                
                # Mostrar resultado directo al usuario
                st.success(f"🎯 **¡Movimiento Óptimo Encontrado!**")
                st.metric(label="Valor de Evaluación de la Posición", value=f"{score / 100.0} pts")
                st.info(f"🧩 **Pieza:** {piece_name}  \n📍 **Desde la casilla:** `{from_square}`  \n🏁 **Hacia la casilla:** `{to_square}`")
        else:
            st.error("El juego ha terminado.")

with col2:
    if st.button("🔄 Ejecutar Movimiento sugerido", use_container_width=True):
        if "sug_move" in st.session_state and st.session_state.sug_move in st.session_state.board.legal_moves:
            st.session_state.board.push(st.session_state.sug_move)
            del st.session_state.sug_move
            st.rerun()
        else:
            st.warning("Primero debes calcular un movimiento válido.")

if st.button("♻️ Reiniciar Tablero", type="secondary"):
    st.session_state.board = chess.Board()
    if "sug_move" in st.session_state:
        del st.session_state.sug_move
    st.rerun()
