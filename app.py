import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Dashboard de Temperatura")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(
    spreadsheet="https://docs.google.com/spreadsheets/d/13i86WpmQ62Bu9nF0LTeH_NgSpQeagO1VTY8ad2XUQL8/edit?gid=1592592023#gid=1592592023",
    ttl=30
    )
df = pd.DataFrame(df)

# Mostrar nomes das colunas lidas
st.write("Colunas encontradas na planilha:", list(df.columns))

# Ajuste dos nomes esperados
# Aqui estamos assumindo que sua planilha tem as colunas DataHora e Temperatura
if "Temperatura" in df.columns:
    df["Temperatura"] = pd.to_numeric(df["Temperatura"], errors="coerce")

if "DataHora" in df.columns:
    df["DataHora"] = pd.to_datetime(df["DataHora"], errors="coerce")

# Remover linhas inválidas
if "DataHora" in df.columns and "Temperatura" in df.columns:
    df = df.dropna(subset=["DataHora", "Temperatura"]).sort_values("DataHora")

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura média", f"{df['Temperatura'].mean():.2f} °C")
    col2.metric("Temperatura máxima", f"{df['Temperatura'].max():.2f} °C")
    col3.metric("Temperatura mínima", f"{df['Temperatura'].min():.2f} °C")

    # Gráfico de linha
    st.subheader("Evolução da Temperatura")
    st.line_chart(df.set_index("DataHora")["Temperatura"])

    # Gráfico de barras
    st.subheader("Temperatura por leitura")
    st.bar_chart(df.set_index("DataHora")["Temperatura"])

    # Mostrar tabela abaixo
    st.subheader("Tabela de dados")
    st.dataframe(df, use_container_width=True)

else:
    st.error("A planilha precisa ter as colunas 'DataHora' e 'Temperatura'.")