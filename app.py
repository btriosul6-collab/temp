import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="SCADA | Casa de Bombas",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

USERNAME = "admin"
PASSWORD = "admin"

BOMBAS_CONFIG = {
    "PISCINA / RAIA": {
        "bombas": ["Bomba 1", "Bomba 2", "Bomba 3"],
        "prefixo": ["PiscinaRaia_B1", "PiscinaRaia_B2", "PiscinaRaia_B3"],
        "tem_modo": True,
        "tem_temperatura": False,
    },
    "CALOR": {
        "bombas": ["Bomba 1", "Bomba 2"],
        "prefixo": ["Calor_B1", "Calor_B2"],
        "tem_modo": False,
        "tem_temperatura": True,
        "col_temperatura": "Calor_Temperatura",
    },
    "PISCINA / INFANTIL": {
        "bombas": ["Bomba 1", "Bomba 2"],
        "prefixo": ["PiscinaInfantil_B1", "PiscinaInfantil_B2"],
        "tem_modo": True,
        "tem_temperatura": False,
    },
    "CALOR2": {
        "bombas": ["Bomba 1", "Bomba 2"],
        "prefixo": ["Calor2_B1", "Calor2_B2"],
        "tem_modo": False,
        "tem_temperatura": True,
        "col_temperatura": "Calor2_Temperatura",
    },
}

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Q4JOXC5XP21B6sYy4TsZe50_OtL7ooKso7btXF0JfVk/edit?gid=0#gid=0"

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
    padding: 14px 16px;
    min-height: 160px;
    margin-bottom: 12px;
}
.bomba-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    color: #e0e6ed;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 12px;
}
.bomba-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid #1a1f2e;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 1px;
}
.bomba-row:last-child { border-bottom: none; }
.bomba-label { color: #6c7a89; text-transform: uppercase; }

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
.badge-ligada    { background: rgba(6,255,165,0.15);   color: #06ffa5; border: 1px solid #06ffa5; }
.badge-desligada { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }
.badge-falha     { background: rgba(255,56,96,0.15);   color: #ff3860; border: 1px solid #ff3860; }
.badge-semfalha  { background: rgba(6,255,165,0.10);   color: #06ffa5; border: 1px solid rgba(6,255,165,0.3); }
.badge-auto      { background: rgba(0,212,255,0.12);   color: #00d4ff; border: 1px solid #00d4ff; }
.badge-manual    { background: rgba(255,170,0,0.15);   color: #ffaa00; border: 1px solid #ffaa00; }
.badge-modo-off  { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }
.badge-ok        { background: rgba(6,255,165,0.15);   color: #06ffa5; border: 1px solid #06ffa5; }
.badge-naook     { background: rgba(255,56,96,0.15);   color: #ff3860; border: 1px solid #ff3860; }
.badge-ativo     { background: rgba(0,212,255,0.12);   color: #00d4ff; border: 1px solid #00d4ff; }
.badge-inativo   { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }
.badge-sim       { background: rgba(255,170,0,0.15);   color: #ffaa00; border: 1px solid #ffaa00; }
.badge-nao       { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }
.badge-quadro-ok { background: rgba(6,255,165,0.15);   color: #06ffa5; border: 1px solid #06ffa5; }
.badge-quadro-ac { background: rgba(255,56,96,0.15);   color: #ff3860; border: 1px solid #ff3860; }
.badge-nd        { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }

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

/* ── TEMPERATURA BADGE ──────────────────────────── */
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

[data-testid="stExpander"] {
    background: #131722 !important; border: 1px solid #2a3142 !important;
    border-radius: 4px !important;
}
[data-testid="stExpander"] summary {
    color: #e0e6ed !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important; text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
}
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
        st.caption("Sistema de Supervisão · Casa de Bombas")
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
# CONEXÃO
# =========================================================
conn = st.connection("gsheets", type=GSheetsConnection)


# =========================================================
# BADGES GENÉRICOS
# =========================================================
def badge_status(valor) -> str:
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("ligada", "ligado", "1", "true", "on", "sim"):
        return '<span class="badge badge-ligada">● Ligado</span>'
    if v in ("desligada", "desligado", "0", "false", "off", "nao", "não"):
        return '<span class="badge badge-desligada">○ Desligado</span>'
    return '<span class="badge badge-nd">-- N/D</span>'

def badge_falha(valor) -> str:
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("falha", "1", "true", "fault", "sim"):
        return '<span class="badge badge-falha">⚠ Falha</span>'
    if v in ("sem falha", "0", "false", "ok", "nao", "não", "normal"):
        return '<span class="badge badge-semfalha">✓ Sem Falha</span>'
    return '<span class="badge badge-nd">-- N/D</span>'

def badge_modo(valor) -> str:
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("auto", "automatico", "automático", "2"):
        return '<span class="badge badge-auto">Auto</span>'
    if v in ("manual", "man", "1"):
        return '<span class="badge badge-manual">Manual</span>'
    if v in ("desligada", "desligado", "off", "0"):
        return '<span class="badge badge-modo-off">Desligada</span>'
    return '<span class="badge badge-nd">-- N/D</span>'

def badge_ok_naook(valor) -> str:
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("ok", "1", "true", "sim", "atingida"):
        return '<span class="badge badge-ok">✓ Ok</span>'
    if v in ("nao ok", "não ok", "naook", "0", "false", "nao", "não"):
        return '<span class="badge badge-naook">✗ Não Ok</span>'
    return '<span class="badge badge-nd">-- N/D</span>'

def badge_ativo(valor) -> str:
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("ativo", "1", "true", "sim", "on"):
        return '<span class="badge badge-ativo">● Ativo</span>'
    if v in ("nao ativo", "não ativo", "inativo", "0", "false", "nao", "não", "off"):
        return '<span class="badge badge-inativo">○ Não Ativo</span>'
    return '<span class="badge badge-nd">-- N/D</span>'

def badge_sim_nao(valor) -> str:
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("sim", "1", "true", "on", "acionado"):
        return '<span class="badge badge-sim">● Sim</span>'
    if v in ("nao", "não", "0", "false", "off"):
        return '<span class="badge badge-nao">○ Não</span>'
    return '<span class="badge badge-nd">-- N/D</span>'

def badge_quadro(valor) -> str:
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("ok", "quadro ok", "0", "false", "normal"):
        return '<span class="badge badge-quadro-ok">✓ Quadro OK</span>'
    if v in ("acionado", "quadro acionado", "1", "true", "sim"):
        return '<span class="badge badge-quadro-ac">⚠ Quadro Acionado</span>'
    return '<span class="badge badge-nd">-- N/D</span>'

def badge_temp_valor(valor) -> str:
    try:
        n = float(str(valor).replace(",", "."))
        return f'<span class="badge badge-manual">{n:.1f} °C</span>'
    except Exception:
        return '<span class="badge badge-nd">-- °C</span>'


# =========================================================
# CARDS
# =========================================================
def card_bomba(nome: str, status, falha, modo=None) -> str:
    rows = f"""
    <div class="bomba-row"><span class="bomba-label">Status</span>{badge_status(status)}</div>
    <div class="bomba-row"><span class="bomba-label">Falha</span>{badge_falha(falha)}</div>
    """
    if modo is not None:
        rows += f'<div class="bomba-row"><span class="bomba-label">Modo</span>{badge_modo(modo)}</div>'
    return f'<div class="bomba-card"><div class="bomba-title">▸ {nome}</div>{rows}</div>'


def card_sauna(ultima_linha) -> str:
    status    = ultima_linha.get("Sauna_Status", None)
    temp_at   = ultima_linha.get("Sauna_TempAtingida", None)
    temp_val  = ultima_linha.get("Sauna_TempAtual", None)
    timer     = ultima_linha.get("Sauna_Temporizador", None)
    gerador   = ultima_linha.get("Sauna_Gerador", None)

    rows = f"""
    <div class="bomba-row"><span class="bomba-label">Status</span>{badge_status(status)}</div>
    <div class="bomba-row"><span class="bomba-label">Temp. Atingida</span>{badge_ok_naook(temp_at)}</div>
    <div class="bomba-row"><span class="bomba-label">Temp. Atual</span>{badge_temp_valor(temp_val)}</div>
    <div class="bomba-row"><span class="bomba-label">Temporizador</span>{badge_ativo(timer)}</div>
    <div class="bomba-row"><span class="bomba-label">Gerador Acionado</span>{badge_sim_nao(gerador)}</div>
    """
    return f'<div class="bomba-card"><div class="bomba-title">▸ SAUNA</div>{rows}</div>'


def card_spa(nome: str, prefixo: str, ultima_linha) -> str:
    status = ultima_linha.get(f"{prefixo}_Status", None)
    falha  = ultima_linha.get(f"{prefixo}_Falha", None)
    modo   = ultima_linha.get(f"{prefixo}_Modo", None)
    rows = f"""
    <div class="bomba-row"><span class="bomba-label">Status</span>{badge_status(status)}</div>
    <div class="bomba-row"><span class="bomba-label">Falha</span>{badge_falha(falha)}</div>
    <div class="bomba-row"><span class="bomba-label">Modo</span>{badge_modo(modo)}</div>
    """
    return f'<div class="bomba-card"><div class="bomba-title">▸ {nome}</div>{rows}</div>'


def card_quadro(ultima_linha) -> str:
    valor = ultima_linha.get("Quadro_Emergencia", None)
    rows = f'<div class="bomba-row"><span class="bomba-label">Estado</span>{badge_quadro(valor)}</div>'
    return f'<div class="bomba-card"><div class="bomba-title">▸ QUADRO EMERGÊNCIA</div>{rows}</div>'


# =========================================================
# LOGOUT BAR
# =========================================================
col_logo, _, col_sair = st.columns([1, 9, 1])
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
STALE_MIN = 5


@st.fragment(run_every="30s")
def painel_bombas():
    df_raw = conn.read(spreadsheet=URL_PLANILHA, ttl=20)

    if df_raw is None or len(df_raw) == 0:
        st.error("Falha ao carregar dados da planilha ou planilha vazia.")
        return

    df = pd.DataFrame(df_raw)
    df.columns = df.columns.str.strip()

    if "DataHora" in df.columns:
        df["DataHora"] = pd.to_datetime(
            df["DataHora"].astype(str).str.strip(), errors="coerce", dayfirst=True)
    elif "Data" in df.columns and "Hora" in df.columns:
        df["DataHora"] = pd.to_datetime(
            df["Data"].astype(str).str.strip() + " " + df["Hora"].astype(str).str.strip(),
            errors="coerce", dayfirst=True)
    else:
        st.error("Coluna DataHora ausente na planilha.")
        return

    df_valid = df.dropna(subset=["DataHora"]).sort_values("DataHora")
    if df_valid.empty:
        st.error("Sem registros válidos na planilha.")
        return

    ultima      = df_valid.iloc[-1]["DataHora"]
    agora       = pd.Timestamp.now(tz="America/Sao_Paulo").tz_localize(None)
    idade_min   = (agora - ultima).total_seconds() / 60.0
    ultima_linha = df_valid.iloc[-1]

    if idade_min <= STALE_MIN:
        status_cls, status_label, emoji_st = "status-online",  "ONLINE",  "🟢"
    elif idade_min <= STALE_MIN * 3:
        status_cls, status_label, emoji_st = "status-stale",   "STALE",   "🟡"
    else:
        status_cls, status_label, emoji_st = "status-offline", "OFFLINE", "🔴"

    # ── HEADER ───────────────────────────────────────────
    col_titulo, col_status = st.columns([3, 1])
    with col_titulo:
        st.markdown("### ◉ Temperatura · Casa de Bombas")
        st.caption("SCADA · UNIDADE RIO SUL")
    with col_status:
        st.markdown(f'<span class="{status_cls}">{emoji_st} {status_label}</span>', unsafe_allow_html=True)
        st.caption(f"Última leitura: {ultima.strftime('%d/%m/%Y %H:%M:%S')}")
        st.caption(f"Idade: {idade_min:.1f} min")
    st.divider()

    # ══════════════════════════════════════════════════════
    # LINHA 1 — PISCINA/RAIA + CALOR
    # ══════════════════════════════════════════════════════
    col_piscina, col_sep, col_calor = st.columns([5, 0.2, 4])

    with col_piscina:
        cfg = BOMBAS_CONFIG["PISCINA / RAIA"]
        st.markdown('<div class="grupo-header">PISCINA / RAIA</div>', unsafe_allow_html=True)
        cols_b = st.columns(len(cfg["bombas"]))
        for i, (nome_bomba, prefixo) in enumerate(zip(cfg["bombas"], cfg["prefixo"])):
            val_status = ultima_linha.get(f"{prefixo}_Status", None)
            val_falha  = ultima_linha.get(f"{prefixo}_Falha",  None)
            val_modo   = ultima_linha.get(f"{prefixo}_Modo",   None) if cfg["tem_modo"] else None
            with cols_b[i]:
                st.markdown(card_bomba(nome_bomba, val_status, val_falha, val_modo), unsafe_allow_html=True)

    with col_sep:
        st.markdown('<div style="border-left:1px solid #2a3142;height:100%;min-height:200px;"></div>', unsafe_allow_html=True)

    with col_calor:
        cfg = BOMBAS_CONFIG["CALOR"]
        col_temp_k = cfg.get("col_temperatura")
        temp_val = ultima_linha.get(col_temp_k, None) if col_temp_k else None
        try:
            temp_num = float(str(temp_val).replace(",", ".")) if temp_val and not pd.isna(temp_val) else None
            temp_txt = f"{temp_num:.1f} °C" if temp_num is not None else "-- °C"
        except Exception:
            temp_txt = "-- °C"
        st.markdown(
            f'<div class="grupo-header">CALOR <span class="temp-badge">Temperatura {temp_txt}</span></div>',
            unsafe_allow_html=True)
        cols_b = st.columns(len(cfg["bombas"]))
        for i, (nome_bomba, prefixo) in enumerate(zip(cfg["bombas"], cfg["prefixo"])):
            val_status = ultima_linha.get(f"{prefixo}_Status", None)
            val_falha  = ultima_linha.get(f"{prefixo}_Falha",  None)
            with cols_b[i]:
                st.markdown(card_bomba(nome_bomba, val_status, val_falha, modo=None), unsafe_allow_html=True)

    st.divider()

    # ══════════════════════════════════════════════════════
    # LINHA 2 — PISCINA/INFANTIL + CALOR2
    # ══════════════════════════════════════════════════════
    col_infantil, col_sep2, col_calor2 = st.columns([5, 0.2, 4])

    with col_infantil:
        cfg = BOMBAS_CONFIG["PISCINA / INFANTIL"]
        st.markdown('<div class="grupo-header">PISCINA / INFANTIL</div>', unsafe_allow_html=True)
        cols_b = st.columns(len(cfg["bombas"]))
        for i, (nome_bomba, prefixo) in enumerate(zip(cfg["bombas"], cfg["prefixo"])):
            val_status = ultima_linha.get(f"{prefixo}_Status", None)
            val_falha  = ultima_linha.get(f"{prefixo}_Falha",  None)
            val_modo   = ultima_linha.get(f"{prefixo}_Modo",   None) if cfg["tem_modo"] else None
            with cols_b[i]:
                st.markdown(card_bomba(nome_bomba, val_status, val_falha, val_modo), unsafe_allow_html=True)

    with col_sep2:
        st.markdown('<div style="border-left:1px solid #2a3142;height:100%;min-height:200px;"></div>', unsafe_allow_html=True)

    with col_calor2:
        cfg = BOMBAS_CONFIG["CALOR2"]
        col_temp_k = cfg.get("col_temperatura")
        temp_val = ultima_linha.get(col_temp_k, None) if col_temp_k else None
        try:
            temp_num = float(str(temp_val).replace(",", ".")) if temp_val and not pd.isna(temp_val) else None
            temp_txt = f"{temp_num:.1f} °C" if temp_num is not None else "-- °C"
        except Exception:
            temp_txt = "-- °C"
        st.markdown(
            f'<div class="grupo-header">CALOR <span class="temp-badge">Temperatura {temp_txt}</span></div>',
            unsafe_allow_html=True)
        cols_b = st.columns(len(cfg["bombas"]))
        for i, (nome_bomba, prefixo) in enumerate(zip(cfg["bombas"], cfg["prefixo"])):
            val_status = ultima_linha.get(f"{prefixo}_Status", None)
            val_falha  = ultima_linha.get(f"{prefixo}_Falha",  None)
            with cols_b[i]:
                st.markdown(card_bomba(nome_bomba, val_status, val_falha, modo=None), unsafe_allow_html=True)

    st.divider()

    # ══════════════════════════════════════════════════════
    # LINHA 3 — SAUNA + SPA HIDRO 01 + SPA HIDRO 02 + QUADRO EMERGÊNCIA
    # ══════════════════════════════════════════════════════
    col_sauna, col_spa1, col_spa2, col_quadro = st.columns([2.5, 2, 2, 2])

    with col_sauna:
        st.markdown('<div class="grupo-header">SAUNA</div>', unsafe_allow_html=True)
        st.markdown(card_sauna(ultima_linha), unsafe_allow_html=True)

    with col_spa1:
        st.markdown('<div class="grupo-header">SPA HIDRO 01</div>', unsafe_allow_html=True)
        st.markdown(card_spa("SPA HIDRO 01", "SpaHidro01", ultima_linha), unsafe_allow_html=True)

    with col_spa2:
        st.markdown('<div class="grupo-header">SPA HIDRO 02</div>', unsafe_allow_html=True)
        st.markdown(card_spa("SPA HIDRO 02", "SpaHidro02", ultima_linha), unsafe_allow_html=True)

    with col_quadro:
        st.markdown('<div class="grupo-header">QUADRO EMERGÊNCIA</div>', unsafe_allow_html=True)
        st.markdown(card_quadro(ultima_linha), unsafe_allow_html=True)

    st.divider()

    # ── TABELA ───────────────────────────────────────────
    # with st.expander("◉ Histórico bruto (últimas 50 leituras)"):
    #    st.dataframe(
     #       df_valid.sort_values("DataHora", ascending=False).head(50),
      #      use_container_width=True, height=300)

    # ── FOOTER ───────────────────────────────────────────
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.caption("SYS: SCADA-BOMBAS-01")
    c2.caption("MODE: AUTO · 30s")
    c3.caption(f"LEITURAS CARREGADAS: {len(df_valid)}")
    c4.caption("REFRESH: 30s")
    c5.caption(f"SERVER: {agora.strftime('%d/%m/%Y %H:%M:%S')}")


painel_bombas()
