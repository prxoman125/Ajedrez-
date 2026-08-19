import streamlit as st
import chess
import chess.svg
import base64

st.set_page_config(page_title="IA Ajedrez Personalizado", layout="centered")
st.title("♟️ Analizador de Ajedrez Matemático")
st.write("Configura tu bando. Mueve las piezas del rival mediante texto y la IA resolverá la fórmula para ti.")

# 1. Configurar bando
user_color_str = st.radio("Selecciona tu bando:", ("Blancas", "Negras"), horizontal=True)
user_is_white = (user_color_str == "Blancas")

# 2. Inicializar Tablero
if "board" not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

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

# --- RENDERIZADO DEL TABLERO ---
def render_board(b, flipped):
    board_svg = chess.svg.board(board=b, size=420, flipped=flipped)
    b64 = base64.b64encode(board_svg.encode('utf-8')).decode('utf-8')
    return f'<div style="display: flex; justify-content: center;"><img src="data:image/svg+xml;base64,{b64}"/></div>'

# Se voltea el tablero según la perspectiva elegida para comodidad visual
st.markdown(render_board(board, flipped=not user_is_white), unsafe_allow_html=True)

st.write(f"**Turno actual en la partida:** {'Blancas' if board.turn == chess.WHITE else 'Negras'}")
st.write("---")

# Determinar si es el turno del usuario o del oponente
is_user_turn = (board.turn == chess.WHITE and user_is_white) or (board.turn == chess.BLACK and not user_is_white)

if is_user_turn:
    st.info("💡 **Es tu turno.** Deja que la IA analice la posición actual resolviendo la ecuación de evaluación.")
    if st.button("🧮 Calcular mi mejor jugada", use_container_width=True):
        with st.spinner("Procesando árboles de decisión Minimax..."):
            score, best_move = minimax(board, depth=3, alpha=-float('inf'), beta=float('inf'), maximizing_player=user_is_white)
        
        if best_move:
            from_sq = chess.square_name(best_move.from_square).upper()
            to_sq = chess.square_name(best_move.to_square).upper()
            piece = board.piece_at(best_move.from_square)
            p_name = chess.piece_name(piece.piece_type).upper() if piece else "PIEZA"
            
            st.success("🎯 **¡Movimiento Óptimo Encontrado!**")
            st.markdown(f"* 🧩 **Pieza:** {p_name}")
            st.markdown(f"* 📍 **De la casilla:** `{from_sq}`")
            st.markdown(f"* 🏁 **Hacia la casilla:** `{to_sq}`")
            st.caption(f"Valor numérico posicional: {score / 100.0} pts.")
            
            st.session_state.ai_move = best_move

    if "ai_move" in st.session_state:
        if st.button("🤖 Aplicar movimiento sugerido por la IA", type="primary", use_container_width=True):
            board.push(st.session_state.ai_move)
            del st.session_state.ai_move
            st.rerun()
else:
    st.warning("⏳ **Turno del Rival.** Ingresa la jugada que hizo tu oponente abajo para actualizar el tablero.")
    
    # Campo de entrada de texto interactivo para simular jugadas rivales
    rival_input = st.text_input("Ingresa el movimiento rival (Ejemplo: e2e4, g1f3):", key="rival_move_input")
    
    if st.button("🔄 Registrar jugada rival", use_container_width=True):
        if rival_input:
            try:
                move = chess.Move.from_uci(rival_input.lower())
                if move in board.legal_moves:
                    board.push(move)
                    st.rerun()
                else:
                    st.error("❌ Ese movimiento no es legal en la posición actual. Intenta con otro.")
            except ValueError:
                st.error("❌ Formato inválido. Usa el estándar de 4 caracteres (ejemplo: `e7e5`).")

# Botón para resetear todo
if st.button("♻️ Reiniciar Partida por completo", type="secondary"):
    st.session_state.board = chess.Board()
    if "ai_move" in st.session_state:
        del st.session_state.ai_move
    st.rerun()
