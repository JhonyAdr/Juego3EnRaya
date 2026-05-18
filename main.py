import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import math

# ─────────────────────────────────────────────
#  JUEGO  —  métodos Player, Actions, Result,
#            Terminal, Utility + Minimax
# ─────────────────────────────────────────────

X = "X"
O = "O"
EMPTY = None

def initial_state():
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]

def player(board):
    """Devuelve el jugador al que le toca mover."""
    x_count = sum(row.count(X) for row in board)
    o_count = sum(row.count(O) for row in board)
    return X if x_count == o_count else O

def actions(board):
    """Devuelve el conjunto de acciones (i, j) disponibles."""
    return {(i, j)
            for i in range(3)
            for j in range(3)
            if board[i][j] is EMPTY}

def result(board, action):
    """Devuelve el tablero resultante de aplicar action."""
    i, j = action
    if board[i][j] is not EMPTY:
        raise ValueError("Acción inválida: casilla ocupada.")
    new_board = [row[:] for row in board]
    new_board[i][j] = player(board)
    return new_board

def winner(board):
    """Devuelve X, O o None según quién ganó."""
    lines = []
    # Filas y columnas
    for i in range(3):
        lines.append([board[i][j] for j in range(3)])
        lines.append([board[j][i] for j in range(3)])
    # Diagonales
    lines.append([board[i][i]     for i in range(3)])
    lines.append([board[i][2 - i] for i in range(3)])

    for line in lines:
        if line[0] is not None and line[0] == line[1] == line[2]:
            return line[0]
    return None

def terminal(board):
    """Devuelve True si el juego terminó."""
    if winner(board) is not None:
        return True
    return all(board[i][j] is not EMPTY for i in range(3) for j in range(3))

def utility(board):
    """Devuelve +1 (X gana), -1 (O gana), 0 (empate)."""
    w = winner(board)
    if w == X: return  1
    if w == O: return -1
    return 0


# ─────────────────────────────────────────────
#  MINIMAX  con poda alfa-beta
# ─────────────────────────────────────────────

def minimax(board, alpha=-math.inf, beta=math.inf):
    """Devuelve (mejor_valor, mejor_acción) para el jugador actual."""
    if terminal(board):
        return utility(board), None

    current = player(board)

    if current == X:                          # maximizador
        best_val  = -math.inf
        best_act  = None
        for act in actions(board):
            val, _ = minimax(result(board, act), alpha, beta)
            if val > best_val:
                best_val, best_act = val, act
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        return best_val, best_act
    else:                                     # minimizador
        best_val  =  math.inf
        best_act  = None
        for act in actions(board):
            val, _ = minimax(result(board, act), alpha, beta)
            if val < best_val:
                best_val, best_act = val, act
            beta = min(beta, best_val)
            if beta <= alpha:
                break
        return best_val, best_act


# ─────────────────────────────────────────────
#  PALETA
# ─────────────────────────────────────────────
BG       = "#080818"
DARK     = "#0c0c20"
PANEL    = "#10102a"
PANEL2   = "#14143a"
ACCENT   = "#5448ee"
ACCENT2  = "#ee4870"
GOLD     = "#f0c030"
SILVER   = "#9090c0"
TEXT_CLR = "#dde0ff"
MUTED    = "#606090"
GREEN    = "#30d080"
EMPTY_BG = "#0a0a22"

# Colores de X y O
COLOR_X      = "#5448ee"   # azul-violeta (ACCENT)
COLOR_O      = "#ee4870"   # rojo-rosa   (ACCENT2)
COLOR_X_LIT  = "#7a70ff"
COLOR_O_LIT  = "#ff6a90"
COLOR_WIN    = "#f0c030"   # GOLD para la línea ganadora

def _lighten(h, a=28):
    try:
        h = h.lstrip('#')
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{min(255,r+a):02x}{min(255,g+a):02x}{min(255,b+a):02x}"
    except:
        return h

def _darken(h, a=20):
    try:
        h = h.lstrip('#')
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{max(0,r-a):02x}{max(0,g-a):02x}{max(0,b-a):02x}"
    except:
        return h


# ─────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────
class TicTacToeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("❌  Tres en Raya  ×  Minimax")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(680, 480)

        self.board         = initial_state()
        self.moves         = 0
        self.time0         = None
        self.timer_running = False
        self.ai_thinking   = False
        self.ai_after      = None
        self.game_over     = False

        # quién es humano: X siempre empieza
        self.human_side   = X      # puede cambiar desde el panel
        self.ai_side      = O

        self._build_ui()
        self._render()
        self._tick()
        self._maybe_ai_move()     # si la IA empieza primero

    # ══════════════════════════════════════════
    #  UI PRINCIPAL
    # ══════════════════════════════════════════
    def _build_ui(self):
        # ── Header ─────────────────────────────
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 0))

        tk.Label(hdr, text="❌", font=("Segoe UI Emoji", 26),
                 bg=BG, fg=COLOR_X).pack(side="left")
        tk.Label(hdr, text="  TRES EN RAYA",
                 font=("Courier New", 19, "bold"),
                 bg=BG, fg=TEXT_CLR).pack(side="left")
        tk.Label(hdr, text="Minimax  ×  Poda Alfa-Beta",
                 font=("Courier New", 9), bg=BG, fg=MUTED).pack(side="right", pady=6)

        tk.Frame(self.root, bg=ACCENT, height=2).pack(fill="x", padx=16, pady=(4, 8))

        # ── Layout ─────────────────────────────
        self.main_fr = tk.Frame(self.root, bg=BG)
        self.main_fr.pack(fill="both", expand=True, padx=8, pady=4)

        self.board_wrap = tk.Frame(self.main_fr, bg=BG)
        self.board_wrap.pack(side="left", fill="both", expand=True)

        self.ctrl_fr = tk.Frame(self.main_fr, bg=PANEL, width=258, bd=0)
        self.ctrl_fr.pack(side="right", fill="y", padx=(6, 4), pady=2)
        self.ctrl_fr.pack_propagate(False)

        self._build_board_canvas()
        self._build_controls(self.ctrl_fr)

    # ── Canvas del tablero ─────────────────────
    def _build_board_canvas(self):
        for w in self.board_wrap.winfo_children():
            w.destroy()

        CELL = 118
        GRID = CELL * 3 + 12     # 3 celdas + 2 gaps de 3px + 2 bordes de 3px

        outer = tk.Frame(self.board_wrap, bg=DARK, bd=3, relief="flat")
        outer.pack(expand=True, pady=20, padx=20)

        self.cell_frames = {}
        self.cell_labels = {}

        for r in range(3):
            for c in range(3):
                fr = tk.Frame(outer, width=CELL, height=CELL,
                              bg=EMPTY_BG, bd=0)
                fr.grid(row=r, column=c, padx=3, pady=3)
                fr.pack_propagate(False)
                fr.grid_propagate(False)

                lbl = tk.Label(fr, text="",
                               font=("Courier New", 44, "bold"),
                               bg=EMPTY_BG, fg=TEXT_CLR)
                lbl.pack(expand=True)

                for w in (fr, lbl):
                    w.bind("<Button-1>",
                           lambda e, rr=r, cc=c: self._cell_click(rr, cc))
                    w.bind("<Enter>",
                           lambda e, ff=fr, ll=lbl, rr=r, cc=c:
                               self._hover_on(ff, ll, rr, cc))
                    w.bind("<Leave>",
                           lambda e, ff=fr, ll=lbl, rr=r, cc=c:
                               self._hover_off(ff, ll, rr, cc))

                self.cell_frames[(r, c)] = fr
                self.cell_labels[(r, c)] = lbl

    def _hover_on(self, fr, lbl, r, c):
        if self.game_over or self.ai_thinking:
            return
        if self.board[r][c] is not EMPTY:
            return
        if player(self.board) != self.human_side:
            return
        fr.config(bg=_lighten(EMPTY_BG, 18), cursor="hand2")
        lbl.config(bg=_lighten(EMPTY_BG, 18),
                   text=self.human_side,
                   fg=COLOR_X_LIT if self.human_side == X else COLOR_O_LIT)

    def _hover_off(self, fr, lbl, r, c):
        if self.board[r][c] is not EMPTY:
            return
        fr.config(bg=EMPTY_BG, cursor="")
        lbl.config(bg=EMPTY_BG, text="")

    # ── Panel de controles ─────────────────────
    def _sec(self, p, txt):
        tk.Frame(p, bg=ACCENT, height=1).pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(p, text=txt, font=("Courier New", 8, "bold"),
                 bg=PANEL, fg=ACCENT).pack(anchor="w", padx=12, pady=(3, 1))

    def _build_controls(self, p):
        # ── Estadísticas ───────────────────────
        self._sec(p, "ESTADÍSTICAS EN VIVO")
        sf = tk.Frame(p, bg=PANEL)
        sf.pack(fill="x", padx=12, pady=4)
        sf.columnconfigure(1, weight=1)

        def srow(row, label, color=TEXT_CLR, big=False):
            fnt_l = ("Courier New", 8)
            fnt_v = ("Courier New", 13, "bold") if big else ("Courier New", 10, "bold")
            tk.Label(sf, text=label, bg=PANEL, fg=MUTED,
                     font=fnt_l, anchor="w").grid(
                row=row, column=0, sticky="w", pady=2, padx=2)
            v = tk.StringVar(value="—")
            tk.Label(sf, textvariable=v, bg=PANEL, fg=color,
                     font=fnt_v, anchor="e").grid(
                row=row, column=1, sticky="e", padx=2)
            return v

        self.sv_moves   = srow(0, "Movimientos:", GOLD,   big=True)
        self.sv_time    = srow(1, "Tiempo:",       GOLD,   big=True)
        self.sv_turn    = srow(2, "Turno actual:", SILVER)
        self.sv_status  = srow(3, "Estado:",       GREEN)
        self.sv_score   = srow(4, "Marcador X-O:", TEXT_CLR)

        self.score = {X: 0, O: 0, "empate": 0}
        self._update_score_label()

        # ── Elegir lado ────────────────────────
        self._sec(p, "JUGAR COMO")
        self.side_var = tk.StringVar(value=X)
        for val, icon, txt, col in (
            (X, "❌", "X  (primer turno)", COLOR_X),
            (O, "⭕", "O  (segundo turno)", COLOR_O),
        ):
            rb = tk.Radiobutton(
                p, text=f"{icon}  {txt}",
                variable=self.side_var, value=val,
                command=self._on_side_change,
                bg=PANEL, fg=TEXT_CLR, selectcolor=DARK,
                activebackground=PANEL, activeforeground=col,
                font=("Courier New", 9), indicatoron=False,
                relief="flat", bd=0, padx=8, pady=5,
                justify="left", cursor="hand2"
            )
            rb.pack(fill="x", padx=10, pady=2)

        # ── Velocidad IA ───────────────────────
        self._sec(p, "VELOCIDAD DE LA IA")
        spd = tk.Frame(p, bg=PANEL)
        spd.pack(fill="x", padx=12, pady=3)
        tk.Label(spd, text="Lento", bg=PANEL, fg=MUTED,
                 font=("Courier New", 7)).pack(side="left")
        self.speed_var = tk.IntVar(value=350)
        ttk.Scale(spd, from_=80, to=900,
                  variable=self.speed_var,
                  orient="horizontal").pack(side="left", fill="x",
                                            expand=True, padx=4)
        tk.Label(spd, text="Rápido", bg=PANEL, fg=MUTED,
                 font=("Courier New", 7)).pack(side="left")

        # ── Botones ────────────────────────────
        self._sec(p, "CONTROLES")
        bcfg = dict(font=("Courier New", 10, "bold"), bd=0,
                    relief="flat", cursor="hand2", pady=8)

        tk.Button(p, text="🔄  NUEVA PARTIDA", bg=ACCENT, fg="white",
                  command=self.new_game, **bcfg).pack(
                      fill="x", padx=10, pady=(6, 3))

        tk.Button(p, text="🏳  REINICIAR TODO", bg=PANEL2, fg=TEXT_CLR,
                  command=self.reset_all, **bcfg).pack(
                      fill="x", padx=10, pady=3)

        self.sv_ai_label = tk.StringVar(value="🤖  IA pensando…")
        self.lbl_thinking = tk.Label(p, textvariable=self.sv_ai_label,
                                     bg=PANEL, fg=MUTED,
                                     font=("Courier New", 8, "italic"))
        self.lbl_thinking.pack(fill="x", padx=12, pady=2)
        self.lbl_thinking.pack_forget()   # oculto hasta que la IA piense

        # ── Instrucciones ──────────────────────
        self._sec(p, "INSTRUCCIONES")
        instruc = (
            "• Clic en una casilla para colocar\n"
            "  tu ficha\n"
            "• La IA usa Minimax con poda\n"
            "  Alfa-Beta: ¡juega perfecto!\n"
            "• Cambia de lado y vuelve\n"
            "  a intentarlo"
        )
        tk.Label(p, text=instruc, bg=PANEL, fg=MUTED,
                 font=("Courier New", 8), justify="left",
                 wraplength=230).pack(padx=12, pady=4, anchor="w")

        # ── Leyenda ────────────────────────────
        self._sec(p, "LEYENDA")
        leg = tk.Frame(p, bg=PANEL)
        leg.pack(fill="x", padx=12, pady=4)
        for sym, col, lbl in ((X, COLOR_X, "Humano / IA"),
                               (O, COLOR_O, "Humano / IA")):
            rf = tk.Frame(leg, bg=PANEL)
            rf.pack(side="left", padx=4)
            tk.Frame(rf, bg=col, width=14, height=14).pack(side="left", padx=1)
            tk.Label(rf, text=f"{sym}", bg=PANEL, fg=col,
                     font=("Courier New", 8, "bold")).pack(side="left")

    # ══════════════════════════════════════════
    #  RENDER
    # ══════════════════════════════════════════
    def _render(self, winning_cells=None):
        winning_cells = winning_cells or set()
        for r in range(3):
            for c in range(3):
                val = self.board[r][c]
                fr  = self.cell_frames[(r, c)]
                lbl = self.cell_labels[(r, c)]

                if (r, c) in winning_cells:
                    bg_col  = _darken(COLOR_WIN, 50)
                    fg_col  = COLOR_WIN
                elif val == X:
                    bg_col  = _darken(COLOR_X, 30)
                    fg_col  = COLOR_X_LIT
                elif val == O:
                    bg_col  = _darken(COLOR_O, 30)
                    fg_col  = COLOR_O_LIT
                else:
                    bg_col  = EMPTY_BG
                    fg_col  = TEXT_CLR

                fr.config(bg=bg_col)
                lbl.config(bg=bg_col, fg=fg_col,
                            text=val if val else "")

        self.sv_moves.set(str(self.moves))
        if not self.game_over:
            cur = player(self.board) if not terminal(self.board) else "—"
            self.sv_turn.set(f"{cur}  {'(tú)' if cur == self.human_side else '(IA)'}")

    def _update_score_label(self):
        self.sv_score.set(f"{self.score[X]} — {self.score[O]}  ({self.score['empate']} ∅)")

    def _tick(self):
        if self.timer_running and self.time0:
            elapsed = time.perf_counter() - self.time0
            self.sv_time.set(f"{elapsed:.1f}s")
        self.root.after(100, self._tick)

    # ══════════════════════════════════════════
    #  LÓGICA DE JUEGO
    # ══════════════════════════════════════════
    def _cell_click(self, r, c):
        if self.game_over or self.ai_thinking:
            return
        if player(self.board) != self.human_side:
            return
        if self.board[r][c] is not EMPTY:
            return

        self.board = result(self.board, (r, c))
        self.moves += 1
        self._render()
        self._check_end()
        if not self.game_over:
            self._maybe_ai_move()

    def _maybe_ai_move(self):
        if self.game_over:
            return
        if terminal(self.board):
            return
        if player(self.board) != self.ai_side:
            return

        # Mostrar indicador de "pensando"
        self.ai_thinking = True
        self.lbl_thinking.pack(fill="x", padx=12, pady=2)
        self.sv_ai_label.set("🤖  IA pensando…")
        self.sv_status.set("IA calculando…")

        def think():
            _, best_act = minimax(self.board)
            # Delay artificial para simular "pensamiento" según slider
            delay_ms = max(80, 1000 - int(self.speed_var.get()))
            self.root.after(delay_ms, lambda: self._apply_ai_move(best_act))

        threading.Thread(target=think, daemon=True).start()

    def _apply_ai_move(self, act):
        self.ai_thinking = False
        self.lbl_thinking.pack_forget()
        if self.game_over:
            return
        if act is None:
            return
        self.board = result(self.board, act)
        self.moves += 1
        self._render()
        self._check_end()

    def _check_end(self):
        w = winner(self.board)
        wcells = self._winner_cells()

        if w is not None:
            self.game_over     = True
            self.timer_running = False
            elapsed = time.perf_counter() - self.time0 if self.time0 else 0
            self.score[w] += 1
            self._update_score_label()
            self._render(winning_cells=wcells)

            if w == self.human_side:
                msg = f"🎉 ¡GANASTE!\n\nMovimientos: {self.moves}\nTiempo: {elapsed:.1f}s"
                status = "¡Ganaste! 🎉"
            else:
                msg = f"🤖 La IA ganó.\n\nMovimientos: {self.moves}\nTiempo: {elapsed:.1f}s"
                status = "IA ganó 🤖"

            self.sv_status.set(status)
            self.sv_turn.set("—")
            self.root.after(400, lambda: messagebox.showinfo("Fin del juego", msg))

        elif terminal(self.board):
            self.game_over     = True
            self.timer_running = False
            elapsed = time.perf_counter() - self.time0 if self.time0 else 0
            self.score["empate"] += 1
            self._update_score_label()
            self.sv_status.set("Empate 🤝")
            self.sv_turn.set("—")
            self.root.after(400, lambda: messagebox.showinfo(
                "Empate", f"🤝 ¡Empate!\n\nMovimientos: {self.moves}\nTiempo: {elapsed:.1f}s"))
        else:
            self.sv_status.set("En juego…")

    def _winner_cells(self):
        """Devuelve las celdas de la línea ganadora (set de tuplas)."""
        lines = [
            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],
        ]
        for line in lines:
            vals = [self.board[r][c] for r, c in line]
            if vals[0] is not None and vals[0] == vals[1] == vals[2]:
                return set(line)
        return set()

    # ══════════════════════════════════════════
    #  CONTROLES
    # ══════════════════════════════════════════
    def _on_side_change(self):
        self.human_side = self.side_var.get()
        self.ai_side    = O if self.human_side == X else X
        self.new_game()

    def new_game(self):
        if self.ai_after:
            self.root.after_cancel(self.ai_after)
            self.ai_after = None
        self.ai_thinking   = False
        self.lbl_thinking.pack_forget()
        self.board         = initial_state()
        self.moves         = 0
        self.game_over     = False
        self.time0         = time.perf_counter()
        self.timer_running = True
        self.sv_status.set("En juego…")
        self.sv_time.set("0.0s")
        self._render()
        self._maybe_ai_move()

    def reset_all(self):
        self.score = {X: 0, O: 0, "empate": 0}
        self._update_score_label()
        self.new_game()


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("780x560")
    root.minsize(680, 480)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Horizontal.TScale",
                    background=PANEL, troughcolor=DARK,
                    sliderthickness=13, sliderrelief="flat")

    app = TicTacToeApp(root)
    root.mainloop()
