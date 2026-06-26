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

# Mapeamento de colunas esperadas na planilha:
# Cada bomba tem 3 colunas: Ligada/Desligada, Falha/Sem Falha, Auto/Manual/Desligada
# Exemplo de cabeçalho esperado na aba:
#   PiscinaRaia_B1_Status | PiscinaRaia_B1_Falha | PiscinaRaia_B1_Modo
#   PiscinaRaia_B2_Status | PiscinaRaia_B2_Falha | PiscinaRaia_B2_Modo
#   PiscinaRaia_B3_Status | PiscinaRaia_B3_Falha | PiscinaRaia_B3_Modo
#   Calor_B1_Status       | Calor_B1_Falha       | Calor_B1_Modo
#   Calor_B2_Status       | Calor_B2_Falha       | Calor_B2_Modo
#   Calor_Temperatura     (valor numérico da temperatura, ex: 44.0)

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
}

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Q4JOXC5XP21B6sYy4TsZe50_OtL7ooKso7btXF0JfVk/edit?gid=0#gid=0"

# =========================================================
# CSS — mesma identidade visual do SCADA de temperatura
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

/* ── CARDS DE BOMBA ────────────────────────────── */
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
.badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 2px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.badge-ligada    { background: rgba(6,255,165,0.15);  color: #06ffa5; border: 1px solid #06ffa5; }
.badge-desligada { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }
.badge-falha     { background: rgba(255,56,96,0.15);  color: #ff3860; border: 1px solid #ff3860; }
.badge-semfalha  { background: rgba(6,255,165,0.10);  color: #06ffa5; border: 1px solid rgba(6,255,165,0.3); }
.badge-auto      { background: rgba(0,212,255,0.12);  color: #00d4ff; border: 1px solid #00d4ff; }
.badge-manual    { background: rgba(255,170,0,0.15);  color: #ffaa00; border: 1px solid #ffaa00; }
.badge-modo-off  { background: rgba(108,122,137,0.12); color: #6c7a89; border: 1px solid #3a4256; }

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
}

/* ── TEMPERATURA BADGE ──────────────────────────── */
.temp-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    color: #ffaa00;
    background: rgba(255,170,0,0.1);
    border: 1px solid #ffaa00;
    border-radius: 4px;
    padding: 4px 14px;
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
# CONEXÃO GSHEETS
# =========================================================
conn = st.connection("gsheets", type=GSheetsConnection)


# =========================================================
# HELPERS — RENDERIZAÇÃO DOS BADGES
# =========================================================
def badge_status(valor: str) -> str:
    """Ligada / Desligada"""
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("ligada", "1", "true", "on", "sim"):
        return '<span class="badge badge-ligada">● Ligada</span>'
    elif v in ("desligada", "0", "false", "off", "nao", "não"):
        return '<span class="badge badge-desligada">○ Desligada</span>'
    return '<span class="badge badge-desligada">-- Offline</span>'


def badge_falha(valor: str) -> str:
    """Falha / Sem Falha"""
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("falha", "1", "true", "fault", "sim"):
        return '<span class="badge badge-falha">⚠ Falha</span>'
    elif v in ("sem falha", "0", "false", "ok", "nao", "não", "normal"):
        return '<span class="badge badge-semfalha">✓ Sem Falha</span>'
    return '<span class="badge badge-modo-off">-- N/D</span>'


def badge_modo(valor: str) -> str:
    """Auto / Manual / Desligada"""
    v = str(valor).strip().lower() if valor and not pd.isna(valor) else ""
    if v in ("auto", "automatico", "automático", "2"):
        return '<span class="badge badge-auto">Auto</span>'
    elif v in ("manual", "man", "1"):
        return '<span class="badge badge-manual">Manual</span>'
    elif v in ("desligada", "desligado", "off", "0"):
        return '<span class="badge badge-modo-off">Desligada</span>'
    return '<span class="badge badge-modo-off">-- N/D</span>'


def card_bomba(nome: str, status: str, falha: str, modo: str | None = None) -> str:
    rows = f"""
    <div class="bomba-row">
        <span class="bomba-label">Status</span>
        {badge_status(status)}
    </div>
    <div class="bomba-row">
        <span class="bomba-label">Falha</span>
        {badge_falha(falha)}
    </div>
    """
    if modo is not None:
        rows += f"""
    <div class="bomba-row">
        <span class="bomba-label">Modo</span>
        {badge_modo(modo)}
    </div>
    """
    return f"""
    <div class="bomba-card">
        <div class="bomba-title">▸ {nome}</div>
        {rows}
    </div>
    """


# =========================================================
# LOGOUT BAR
# =========================================================
col_logo, _, col_sair = st.columns([1, 9, 1])
with col_logo:
    # st.image("logonome.png", width=350)  # descomente com o arquivo disponível
    st.markdown("**◉ bt | bodytech**")
with col_sair:
    if st.button("Sair", use_container_width=True):
        logout()


# =========================================================
# PAINEL PRINCIPAL
# =========================================================
STALE_MIN = 5


@st.fragment(run_every="30s")
def painel_bombas():
    df_raw = conn.read(
        spreadsheet=URL_PLANILHA,
        ttl=20,
    )

    if df_raw is None or len(df_raw) == 0:
        st.error("Falha ao carregar dados da planilha ou planilha vazia.")
        return

    df = pd.DataFrame(df_raw)
    df.columns = df.columns.str.strip()

    # Identifica a última linha com DataHora
    if "DataHora" in df.columns:
        df["DataHora"] = pd.to_datetime(
            df["DataHora"].astype(str).str.strip(), errors="coerce", dayfirst=True
        )
    elif "Data" in df.columns and "Hora" in df.columns:
        df["DataHora"] = pd.to_datetime(
            df["Data"].astype(str).str.strip() + " " + df["Hora"].astype(str).str.strip(),
            errors="coerce", dayfirst=True,
        )
    else:
        st.error("Coluna DataHora ausente na planilha.")
        return

    df_valid = df.dropna(subset=["DataHora"]).sort_values("DataHora")
    if df_valid.empty:
        st.error("Sem registros válidos na planilha.")
        return

    ultima = df_valid.iloc[-1]["DataHora"]
    agora  = pd.Timestamp.now(tz="America/Sao_Paulo").tz_localize(None)
    idade_min = (agora - ultima).total_seconds() / 60.0

    if idade_min <= STALE_MIN:
        status_cls, status_label, emoji_st = "status-online",  "ONLINE",  "🟢"
    elif idade_min <= STALE_MIN * 3:
        status_cls, status_label, emoji_st = "status-stale",   "STALE",   "🟡"
    else:
        status_cls, status_label, emoji_st = "status-offline", "OFFLINE", "🔴"

    ultima_linha = df_valid.iloc[-1]

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

    # ── GRUPOS ───────────────────────────────────────────
    col_piscina, col_sep, col_calor = st.columns([5, 0.2, 4])

    # -------- PISCINA / RAIA --------
    with col_piscina:
        cfg = BOMBAS_CONFIG["PISCINA / RAIA"]
        st.markdown('<div class="grupo-header">PISCINA / RAIA</div>', unsafe_allow_html=True)
        cols_b = st.columns(len(cfg["bombas"]))
        for i, (nome_bomba, prefixo) in enumerate(zip(cfg["bombas"], cfg["prefixo"])):
            col_status_k = f"{prefixo}_Status"
            col_falha_k  = f"{prefixo}_Falha"
            col_modo_k   = f"{prefixo}_Modo"

            val_status = ultima_linha.get(col_status_k, None)
            val_falha  = ultima_linha.get(col_falha_k,  None)
            val_modo   = ultima_linha.get(col_modo_k,   None) if cfg["tem_modo"] else None

            with cols_b[i]:
                st.markdown(
                    card_bomba(nome_bomba, val_status, val_falha, val_modo),
                    unsafe_allow_html=True,
                )

    # -------- SEPARADOR VERTICAL (simulado) --------
    with col_sep:
        st.markdown(
            '<div style="border-left:1px solid #2a3142; height:100%; min-height:200px;"></div>',
            unsafe_allow_html=True,
        )

    # -------- CALOR --------
    with col_calor:
        cfg = BOMBAS_CONFIG["CALOR"]
        col_temp_header, col_temp_val = st.columns([1, 1])
        with col_temp_header:
            st.markdown('<div class="grupo-header">CALOR</div>', unsafe_allow_html=True)
        with col_temp_val:
            col_temp_k = cfg.get("col_temperatura")
            temp_val = ultima_linha.get(col_temp_k, None) if col_temp_k else None
            try:
                temp_num = float(str(temp_val).replace(",", ".")) if temp_val and not pd.isna(temp_val) else None
                temp_txt = f"{temp_num:.1f} °C" if temp_num is not None else "-- °C"
            except Exception:
                temp_txt = "-- °C"
            st.markdown(
                f'<div style="margin-top:2px;"><span class="temp-badge">Temperatura {temp_txt}</span></div>',
                unsafe_allow_html=True,
            )

        st.write("")
        cols_b = st.columns(len(cfg["bombas"]))
        for i, (nome_bomba, prefixo) in enumerate(zip(cfg["bombas"], cfg["prefixo"])):
            col_status_k = f"{prefixo}_Status"
            col_falha_k  = f"{prefixo}_Falha"

            val_status = ultima_linha.get(col_status_k, None)
            val_falha  = ultima_linha.get(col_falha_k,  None)

            with cols_b[i]:
                st.markdown(
                    card_bomba(nome_bomba, val_status, val_falha, modo=None),
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── TABELA HISTÓRICO ─────────────────────────────────
    with st.expander("◉ Histórico bruto (últimas 50 leituras)"):
        st.dataframe(
            df_valid.sort_values("DataHora", ascending=False).head(50),
            use_container_width=True,
            height=300,
        )

    # ── FOOTER ───────────────────────────────────────────
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.caption("SYS: SCADA-BOMBAS-01")
    c2.caption("MODE: AUTO · 30s")
    c3.caption(f"LEITURAS CARREGADAS: {len(df_valid)}")
    c4.caption("REFRESH: 30s")
    c5.caption(f"SERVER: {agora.strftime('%d/%m/%Y %H:%M:%S')}")


painel_bombas()
