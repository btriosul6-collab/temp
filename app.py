import streamlit as st
import pandas as pd
from urllib.error import HTTPError
from urllib.parse import quote

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="SCADA | Temperaturas",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

USERNAME = "admin"
PASSWORD = "admin"

SHEET_ID = "1si78r9HgpgbFTUNbeaxZI9lZBozciHYyTl99U5QpOrs"

# Aba a ler: nome (ex.: "Leituras") ou gid numérico (ex.: "123456789").
WORKSHEET = "Leituras"

TZ = "America/Sao_Paulo"
STALE_MIN = 5

# Colunas C..L (posição 2..11, base 0) -> nome exibido
SENSORES = [
    "Sala Hall",             # C
    "Sala Mind",             # D
    "Indor Cycle",           # E
    "Sala 2",                # F
    "Musculação 1",          # G
    "Musculação 2",          # H
    "Retorno Musculação",    # I
    "Sala 1",                # J
    "Flag 1",                # K
    "Flag 2",                # L
]
COL_INI = 2                  # C
COL_FIM = COL_INI + len(SENSORES)

# Escala do gauge e limites de alarme
G_MIN, G_MAX = 10.0, 40.0
LIM_BAIXO, LIM_ALTO = 10.0, 40.0   # fora disso => alarme (vermelho)
# Leituras fora desta faixa são tratadas como FALHA DE SENSOR (ex.: 127,9 = entrada saturada/sem sensor; 0 = sem dado)
V_MIN_VALIDO, V_MAX_VALIDO = 1.0, 100.0

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

.stApp {
    background: radial-gradient(ellipse at top, #0f1419 0%, #0a0e1a 60%, #060912 100%);
    color: #e0e6ed;
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: transparent; height: 0; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"]    { visibility: hidden !important; }
[data-testid="stDecoration"] { visibility: hidden !important; }
[data-testid="stStatusWidget"] { visibility: hidden !important; }
.block-container { padding: 1rem 1.5rem 2rem 1.5rem; max-width: 100%; }

h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    color: #ffffff !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
h3 { font-size: 1.1rem !important; font-weight: 700 !important; }
p, .stMarkdown p { color: #e0e6ed !important; font-family: 'Inter', sans-serif; }

.stCaption, [data-testid="stCaptionContainer"] p {
    color: #6c7a89 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

hr { border-color: #2a3142 !important; margin: 10px 0 !important; }

.stButton > button {
    background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%) !important;
    color: #0a0e1a !important; border: none !important;
    font-weight: 700 !important; text-transform: uppercase !important;
    letter-spacing: 1.5px !important; font-size: 0.78rem !important;
    border-radius: 2px !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00ffff 0%, #00d4ff 100%) !important;
    box-shadow: 0 0 16px rgba(0,212,255,0.45) !important;
}

.stTextInput input, .stPasswordInput input {
    background: #0a0e1a !important; border: 1px solid #2a3142 !important;
    color: #e0e6ed !important; font-family: 'JetBrains Mono', monospace !important;
    border-radius: 2px !important;
}
.stTextInput input:focus, .stPasswordInput input:focus {
    border-color: #00d4ff !important; box-shadow: 0 0 0 1px #00d4ff !important;
}
.stTextInput label, .stPasswordInput label {
    color: #6c7a89 !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important; text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
}

/* ── CARDS ─────────────────────────────────────────── */
.bomba-card {
    background: linear-gradient(135deg, #131722, #1a1f2e);
    border: 1px solid #2a3142;
    border-top: 3px solid #00d4ff;
    border-radius: 4px;
    padding: 14px 16px 10px 16px;
    margin-bottom: 12px;
}
.bomba-card.alarme { border-top-color: #ff3860; }
.bomba-card.nd     { border-top-color: #3a4256; }
.bomba-card.falha  { border-top-color: #ffaa00; }
.bomba-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    color: #e0e6ed;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 4px;
}
.bomba-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 0;
    border-top: 1px solid #1a1f2e;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 1px;
}
.bomba-label { color: #6c7a89; text-transform: uppercase; }

/* ── GAUGE ─────────────────────────────────────────── */
.tp-gauge { width: 100%; display: block; }
.tp-trk, .tp-fill { fill: none; stroke-width: 14; }
.tp-trk  { stroke: #2a3142; }
.tp-fill { stroke: #06ffa5; }
.tp-gv  { font-family: 'JetBrains Mono', monospace; font-size: 30px; font-weight: 700; fill: #e0e6ed; }
.tp-gu  { font-family: 'JetBrains Mono', monospace; font-size: 11px; fill: #6c7a89; }
.tp-lim { font-family: 'JetBrains Mono', monospace; font-size: 9px;  fill: #6c7a89; }
.bomba-card.alarme .tp-fill { stroke: #ff3860; }
.bomba-card.alarme .tp-gv   { fill: #ff3860; }
.bomba-card.nd .tp-gv       { fill: #6c7a89; }
.bomba-card.falha .tp-gv    { fill: #ffaa00; }

/* ── BADGES ─────────────────────────────────────────── */
.badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 2px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.badge-ok     { background: rgba(6,255,165,0.15);   color: #06ffa5; border: 1px solid #06ffa5; }
.badge-alto   { background: rgba(255,56,96,0.15);   color: #ff3860; border: 1px solid #ff3860; }
.badge-baixo  { background: rgba(0,212,255,0.12);   color: #00d4ff; border: 1px solid #00d4ff; }
.badge-falha  { background: rgba(255,170,0,0.15);   color: #ffaa00; border: 1px solid #ffaa00; }
.badge-nd     { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }

/* ── GRUPO HEADER ───────────────────────────────── */
.grupo-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
    color: #00d4ff;
    text-transform: uppercase;
    letter-spacing: 3px;
    border-left: 3px solid #00d4ff;
    padding-left: 10px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.temp-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    color: #ffaa00;
    background: rgba(255,170,0,0.1);
    border: 1px solid #ffaa00;
    border-radius: 4px;
    padding: 2px 8px;
    display: inline-block;
    letter-spacing: 2px;
}

/* ── STATUS GERAL ───────────────────────────────── */
.status-online  { color: #06ffa5; font-weight: 700; }
.status-offline { color: #ff3860; font-weight: 700; }
.status-stale   { color: #ffaa00; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# =========================================================
# LOGIN
# =========================================================
def login():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.image("logo.png", width=160)
        st.markdown("### ◉ BODYTECH")
        st.caption("Sistema de Supervisão · Temperaturas")
        st.divider()
        with st.form("login_form"):
            username  = st.text_input("Usuário")
            password  = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Autenticar", use_container_width=True)
            if submitted:
                if username == USERNAME and password == PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")


def logout():
    st.session_state.logged_in = False
    st.rerun()


if not st.session_state.logged_in:
    login()
    st.stop()

# =========================================================
# LEITURA (CSV público via gviz — não depende de credenciais)
# =========================================================
def url_planilha() -> str:
    base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
    ws = str(WORKSHEET).strip()
    return f"{base}&gid={ws}" if ws.isdigit() else f"{base}&sheet={quote(ws)}"


@st.cache_data(ttl=20, show_spinner=False)
def ler_planilha(url: str) -> pd.DataFrame:
    # dtype=str: preserva "23,5" (vírgula decimal da planilha pt-BR); a conversão é feita em para_float()
    return pd.read_csv(url, dtype=str, keep_default_na=False, na_values=[""])


# =========================================================
# PARSE
# =========================================================
def _parse_dt(s: pd.Series) -> pd.Series:
    """Texto ISO/BR ou epoch (s/ms) -> datetime naive no fuso de São Paulo."""
    s = s.astype(str).str.strip()
    num = pd.to_numeric(s, errors="coerce")
    if num.notna().mean() > 0.9:
        unit = "ms" if num.median() > 1e11 else "s"
        dt = pd.to_datetime(num, unit=unit, utc=True, errors="coerce")
        return dt.dt.tz_convert(TZ).dt.tz_localize(None)
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if getattr(dt.dt, "tz", None) is not None:
        dt = dt.dt.tz_convert(TZ).dt.tz_localize(None)
    return dt


def montar_datahora(df: pd.DataFrame) -> pd.Series:
    cols = {c.lower(): c for c in df.columns}
    for nome in ("datahora", "timestamp", "ts"):
        if nome in cols:
            return _parse_dt(df[cols[nome]])
    if "data" in cols and "hora" in cols:
        return _parse_dt(df[cols["data"]].astype(str) + " " + df[cols["hora"]].astype(str))
    # fallback posicional: A; se não parsear, A + B (data + hora)
    dt = _parse_dt(df.iloc[:, 0])
    if dt.notna().mean() < 0.5 and df.shape[1] > 1:
        dt = _parse_dt(df.iloc[:, 0].astype(str) + " " + df.iloc[:, 1].astype(str))
    return dt


def para_float(v):
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    try:
        n = float(str(v).strip().replace(",", "."))
    except ValueError:
        return None
    return n if n == n and abs(n) != float("inf") else None


# =========================================================
# CARD
# =========================================================
def invalido(valor) -> bool:
    return valor is not None and not (V_MIN_VALIDO <= valor <= V_MAX_VALIDO)


def classifica(valor):
    if valor is None:
        return "nd"
    if invalido(valor):
        return "falha"
    if valor < LIM_BAIXO or valor > LIM_ALTO:
        return "alarme"
    return "ok"


def badge_estado(valor) -> str:
    if valor is None:
        return '<span class="badge badge-nd">-- N/D</span>'
    if invalido(valor):
        return '<span class="badge badge-falha">⚠ Falha sensor</span>'
    if valor > LIM_ALTO:
        return '<span class="badge badge-alto">⚠ Alta</span>'
    if valor < LIM_BAIXO:
        return '<span class="badge badge-baixo">⚠ Baixa</span>'
    return '<span class="badge badge-ok">✓ Normal</span>'


def gauge_svg(valor) -> str:
    if valor is None:
        frac = 0.0
        txt = "--"
    elif invalido(valor):
        frac = 0.0
        txt = "ERR"
    else:
        frac = min(1.0, max(0.0, (valor - G_MIN) / (G_MAX - G_MIN)))
        txt = f"{valor:.1f}"
    arco = "M 20 100 A 80 80 0 0 1 180 100"
    return (
        '<svg class="tp-gauge" viewBox="0 0 200 125">'
        f'<path class="tp-trk" d="{arco}" pathLength="100"/>'
        f'<path class="tp-fill" d="{arco}" pathLength="100" stroke-dasharray="{frac * 100:.2f} 100"/>'
        f'<text class="tp-lim" x="20" y="118" text-anchor="middle">{G_MIN:.0f}</text>'
        f'<text class="tp-lim" x="180" y="118" text-anchor="middle">{G_MAX:.0f}</text>'
        f'<text class="tp-gv" x="100" y="88" text-anchor="middle">{txt}</text>'
        '<text class="tp-gu" x="100" y="106" text-anchor="middle">°C</text>'
        '</svg>'
    )


def card_temp(nome: str, valor) -> str:
    cls = classifica(valor)
    cls_css = "" if cls == "ok" else f" {cls}"
    return (
        f'<div class="bomba-card{cls_css}">'
        f'<div class="bomba-title">▸ {nome}</div>'
        f'{gauge_svg(valor)}'
        f'<div class="bomba-row"><span class="bomba-label">Estado</span>{badge_estado(valor)}</div>'
        '</div>'
    )


# =========================================================
# LOGOUT BAR
# =========================================================
col_logo, _, col_voltnadi, col_sair = st.columns([2, 7, 1, 1])
with col_logo:
    st.image("logonome.png", width=350)
with col_voltnadi:
    st.image("logovoltnadi.png", width=120)
with col_sair:
    if st.button("Sair", use_container_width=True):
        logout()


# =========================================================
# PAINEL
# =========================================================
@st.fragment(run_every="30s")
def painel_temperaturas():
    try:
        df_raw = ler_planilha(url_planilha())
    except pd.errors.EmptyDataError:
        st.warning(f"A aba '{WORKSHEET}' está vazia (sem cabeçalho nem linhas).")
        return
    except HTTPError as e:
        st.error(f"O Google respondeu HTTP {e.code} ao ler a aba '{WORKSHEET}'. "
                 "Confira o nome da aba e o compartilhamento (qualquer pessoa com o link: leitor).")
        return
    except Exception as e:
        st.error(f"Não foi possível ler a planilha ({type(e).__name__}: {e}).")
        return

    if df_raw is None or len(df_raw) == 0:
        st.error("Falha ao carregar dados da planilha ou planilha vazia.")
        return

    df = pd.DataFrame(df_raw)
    df.columns = df.columns.astype(str).str.strip()

    if df.shape[1] < COL_FIM:
        st.error(f"A planilha tem {df.shape[1]} colunas; esperado ao menos {COL_FIM} (A..L).")
        return

    df["_DataHora"] = montar_datahora(df)
    df_valid = df.dropna(subset=["_DataHora"]).sort_values("_DataHora")
    if df_valid.empty:
        st.error("Sem registros válidos na planilha (coluna de data/hora não reconhecida).")
        return

    ultima_linha = df_valid.iloc[-1]
    ultima       = ultima_linha["_DataHora"]
    agora        = pd.Timestamp.now(tz=TZ).tz_localize(None)
    idade_min    = (agora - ultima).total_seconds() / 60.0

    valores = [para_float(ultima_linha.iloc[COL_INI + i]) for i in range(len(SENSORES))]
    validos = [v for v in valores if v is not None and not invalido(v)]

    # coluna clp_online (B): 1 = CLP respondendo, 0 = CLP fora
    col_clp = next((c for c in df.columns if c.lower() == "clp_online"), df.columns[1])
    clp_on  = para_float(ultima_linha[col_clp])

    if idade_min <= STALE_MIN:
        if clp_on == 0:
            status_cls, status_label, emoji_st = "status-offline", "CLP OFFLINE", "🔴"
        else:
            status_cls, status_label, emoji_st = "status-online",  "ONLINE",  "🟢"
    elif idade_min <= STALE_MIN * 3:
        status_cls, status_label, emoji_st = "status-stale",   "STALE",   "🟡"
    else:
        status_cls, status_label, emoji_st = "status-offline", "OFFLINE", "🔴"

    # ── HEADER ───────────────────────────────────────────
    col_titulo, col_status = st.columns([3, 1])
    with col_titulo:
        st.markdown("### ◉ Temperaturas")
        st.caption("SCADA · UNIDADE RIO SUL")
    with col_status:
        st.markdown(f'<span class="{status_cls}">{emoji_st} {status_label}</span>', unsafe_allow_html=True)
        st.caption(f"Última leitura: {ultima.strftime('%d/%m/%Y %H:%M:%S')}")
        st.caption(f"Idade: {idade_min:.1f} min")
    st.divider()

    # ── RESUMO ───────────────────────────────────────────
    if validos:
        resumo = (
            f"MÍN {min(validos):.1f} °C  ·  MÉD {sum(validos)/len(validos):.1f} °C  ·  "
            f"MÁX {max(validos):.1f} °C"
        )
    else:
        resumo = "SEM LEITURAS VÁLIDAS"
    n_alarme = sum(1 for v in valores if classifica(v) == "alarme")
    n_nd     = sum(1 for v in valores if v is None)
    n_falha  = sum(1 for v in valores if classifica(v) == "falha")
    st.markdown(
        f'<div class="grupo-header">AMBIENTES <span class="temp-badge">{resumo}</span></div>',
        unsafe_allow_html=True)
    if n_alarme or n_nd or n_falha:
        st.caption(f"Alarmes: {n_alarme}  ·  Falha de sensor: {n_falha}  ·  Sem leitura: {n_nd}  ·  "
                   f"Faixa normal: {LIM_BAIXO:.0f}–{LIM_ALTO:.0f} °C")

    # ── CARDS (2 linhas x 5) ─────────────────────────────
    por_linha = 5
    for ini in range(0, len(SENSORES), por_linha):
        cols = st.columns(por_linha)
        for j in range(por_linha):
            i = ini + j
            if i >= len(SENSORES):
                break
            with cols[j]:
                st.markdown(card_temp(SENSORES[i], valores[i]), unsafe_allow_html=True)

    # ── FOOTER ───────────────────────────────────────────
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.caption("SYS: SCADA-TEMP-01")
    c2.caption("MODE: AUTO · 30s")
    c3.caption(f"LEITURAS CARREGADAS: {len(df_valid)}")
    c4.caption("REFRESH: 30s")
    c5.caption(f"SERVER: {agora.strftime('%d/%m/%Y %H:%M:%S')}")


painel_temperaturas()
