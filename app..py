import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Dashboard Google Sheets",
    layout="wide"
)

st.title("Dashboard conectado ao Google Sheets")

# Conexão com a planilha
conn = st.connection("gsheets", type=GSheetsConnection)

# Leitura com cache para evitar excesso de requisições
df = conn.read(ttl=30)

# Garantir DataFrame
df = pd.DataFrame(df)

# Mostrar dados brutos
st.subheader("Dados da planilha")
st.dataframe(df, use_container_width=True)

# Exemplo de tratamento de dados
if "Temperatura" in df.columns:
    df["Temperatura"] = pd.to_numeric(df["Temperatura"], errors="coerce")

if "DataHora" in df.columns:
    df["DataHora"] = pd.to_datetime(df["DataHora"], errors="coerce")

# KPIs
col1, col2, col3 = st.columns(3)

if "Temperatura" in df.columns and not df["Temperatura"].dropna().empty:
    col1.metric("Temperatura média", f"{df['Temperatura'].mean():.2f} °C")
    col2.metric("Temperatura máxima", f"{df['Temperatura'].max():.2f} °C")
    col3.metric("Temperatura mínima", f"{df['Temperatura'].min():.2f} °C")

# Gráfico
if "DataHora" in df.columns and "Temperatura" in df.columns:
    df_plot = df.dropna(subset=["DataHora", "Temperatura"]).sort_values("DataHora")
    st.subheader("Temperatura ao longo do tempo")
    st.line_chart(df_plot.set_index("DataHora")["Temperatura"])