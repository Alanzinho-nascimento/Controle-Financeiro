import streamlit as st
import pandas as pd
import altair as alt
import os
import uuid
from datetime import datetime
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Gestão Financeira", layout="wide")
st.markdown("""
    <style>
        .main {
            background-color: #e6f0ff;
        }
        .filtro-container {
            position: sticky;
            top: 0;
            background-color: #e6f0ff;
            z-index: 100;
            padding-top: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ccc;
        }
    </style>
""", unsafe_allow_html=True)

# Arquivo CSV
ARQUIVO = "dados.csv"

# Contas disponíveis
contas_disponiveis = ["Carteira", "Sicoob", "Itaú", "Nubank", "Mercado Pago", "Cartão Sicoob", "Cartão Itaú", "Cartão Nu Bank", "Cartão Mercado Pago"]

# Formatação de valores em reais
def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# Carregar dados
@st.cache_data(ttl=1)
def carregar_dados():
    if os.path.exists(ARQUIVO):
        return pd.read_csv(ARQUIVO, dtype={"Conta Origem": str, "Conta Destino": str})
    else:
        df_vazio = pd.DataFrame(columns=["ID", "Data", "Descrição", "Tipo", "Categoria", "Conta Origem", "Conta Destino", "Valor"])
        df_vazio.to_csv(ARQUIVO, index=False)
        return df_vazio

# Inicializa a variável de dados na sessão, se ainda não estiver
if "dados" not in st.session_state:
    st.session_state.dados = carregar_dados()
dados = st.session_state.dados

# Função para salvar os dados
def salvar_dados(novo_lancamento):
    dados_antigos = carregar_dados()
    df = pd.concat([dados_antigos, pd.DataFrame([novo_lancamento])], ignore_index=True)
    df.to_csv(ARQUIVO, index=False)

# Conversão de data e preenchimento de campos ausentes
dados["Data"] = pd.to_datetime(dados["Data"], errors="coerce")
dados["Conta Origem"] = dados["Conta Origem"].fillna("")
dados["Conta Destino"] = dados["Conta Destino"].fillna("")

# Adicionar contas únicas aos disponíveis
contas_unicas = pd.unique(dados[["Conta Origem", "Conta Destino"]].values.ravel("K"))
for conta in contas_unicas:
    if conta not in contas_disponiveis:
        contas_disponiveis.append(conta)

# Filtro por mês e ano (parte superior e sticky)
meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

from datetime import datetime

# Captura o mês e o ano atuais
ano_atual = datetime.today().year
mes_atual = datetime.today().month
meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

with st.container():
    st.markdown('<div class="filtro-container">', unsafe_allow_html=True)
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        anos_disponiveis = dados["Data"].dt.year.dropna().unique().tolist()
        ano_selecionado = st.selectbox("Ano", sorted(anos_disponiveis, reverse=True), index=anos_disponiveis.index(ano_atual) if ano_atual in anos_disponiveis else 0, key="filtro_ano")
    with col_f2:
        mes_selecionado = st.selectbox("Mês", list(meses.values()), index=list(meses.keys()).index(mes_atual) if mes_atual in meses.keys() else 0, key="filtro_mes")
    st.markdown('</div>', unsafe_allow_html=True)


numero_mes = list(meses.keys())[list(meses.values()).index(mes_selecionado)]
dados_filtrados = dados[(dados["Data"].dt.year == ano_selecionado) & (dados["Data"].dt.month == numero_mes)]

# Tabs

st.markdown("### Filtrar por Categoria")
categorias_disponiveis = ["Todas"] + sorted(dados_filtrados["Categoria"].dropna().unique().tolist())
categoria_selecionada = st.selectbox("Escolha uma categoria", categorias_disponiveis)

# Filtragem
if categoria_selecionada != "Todas":
    dados_filtrados = dados_filtrados[dados_filtrados["Categoria"] == categoria_selecionada]


aba_transacao, aba_graficos = st.tabs(["➕ Lançamentos", "📊 Gráficos"])


# Aplica o filtro à base de dados
if categoria_selecionada != "Todas":
    dados_filtrados = dados_filtrados[dados_filtrados["Categoria"] == categoria_selecionada]


# Saldo total
# Cálculo de saldo acumulado até o mês anterior
dados["Data"] = pd.to_datetime(dados["Data"], errors="coerce")
dados_anteriores = dados[(dados["Data"].dt.year < ano_selecionado) |
                         ((dados["Data"].dt.year == ano_selecionado) & (dados["Data"].dt.month < numero_mes))]

saldo_anterior = dados_anteriores.apply(
    lambda row: row['Valor'] if row['Tipo'] == 'Entrada' else -row['Valor'] if row['Tipo'] == 'Saída' else 0, axis=1
).sum()

# Saldo do mês atual
saldo_mes_atual = dados_filtrados.apply(
    lambda row: row['Valor'] if row['Tipo'] == 'Entrada' else -row['Valor'] if row['Tipo'] == 'Saída' else 0, axis=1
).sum()

# Saldo total acumulado até o mês atual
saldo_total = saldo_anterior + saldo_mes_atual
saldo_formatado = formatar_reais(saldo_total)


# ========================== ABA LANÇAMENTOS ============================
with aba_transacao:
    st.subheader("➕ Novo Lançamento")
    st.metric("💰 Saldo Atual", saldo_formatado)

    with st.form("form_lancamento"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data = st.date_input("Data", value=datetime.today())
        with col2:
            descricao = st.text_input("Descrição")
        with col3:
            tipo = st.selectbox("Tipo", ["Entrada", "Saída", "Transferência"])

        categoria = st.selectbox("Categoria", ["Salário", "Alimentação", "Transporte", "Lazer", "Investimento", "Transferência", "Cartão Sicoob", "Cartão Nu Bank", "Cartão Itaú", "Cartão Mercado Pago", "Outros"])
        conta_origem = st.selectbox("Conta de Origem", contas_disponiveis)

        conta_destino = ""
        if tipo == "Transferência" or categoria == "Transferência":
            conta_destino = st.selectbox("Conta de Destino", contas_disponiveis)

        valor = st.number_input("Valor", min_value=0.01, step=0.01, format="%.2f")
        enviar = st.form_submit_button("Adicionar")

        if enviar:
            nova = {
                "ID": str(uuid.uuid4()),
                "Data": data,
                "Descrição": descricao,
                "Tipo": tipo,
                "Categoria": categoria,
                "Conta Origem": conta_origem,
                "Conta Destino": conta_destino,
                "Valor": valor
            }
            dados = pd.concat([dados, pd.DataFrame([nova])], ignore_index=True)
            dados.to_csv(ARQUIVO, index=False)
            st.session_state.dados = dados  # Atualiza os dados na sessão
            st.success("Transação adicionada!")
            st.rerun()
 

    st.subheader("📋 Histórico de Lançamentos")
    for i, row in dados_filtrados.sort_values(by="Data", ascending=False).iterrows():
        with st.expander(f"{row['Data'].date()} - {row['Descrição']} - {formatar_reais(row['Valor'])}"):
            with st.form(f"editar_{row['ID']}"):
                nova_data = st.date_input("Data", row["Data"].date())
                nova_descricao = st.text_input("Descrição", row["Descrição"])
                novo_tipo = st.selectbox("Tipo", ["Entrada", "Saída", "Transferência"], index=["Entrada", "Saída", "Transferência"].index(row["Tipo"]))
                nova_categoria = st.selectbox("Categoria", ["Salário", "Alimentação", "Transporte", "Lazer", "Investimento", "Transferência", "Outros"], index=0)

                indice_origem = contas_disponiveis.index(row["Conta Origem"]) if row["Conta Origem"] in contas_disponiveis else 0
                nova_conta_origem = st.selectbox("Conta de Origem", contas_disponiveis, index=indice_origem)

                conta_dest = row["Conta Destino"] if "Conta Destino" in row else ""
                if row["Tipo"] == "Transferência" or row["Categoria"] == "Transferência":
                    indice_destino = contas_disponiveis.index(conta_dest) if conta_dest in contas_disponiveis else 0
                    nova_conta_destino = st.selectbox("Conta de Destino", contas_disponiveis, index=indice_destino)
                else:
                    nova_conta_destino = ""

                novo_valor = st.number_input("Valor", min_value=0.01, step=0.01, value=float(row["Valor"]))
                salvar = st.form_submit_button("Salvar Edição")

                if salvar:
                    dados.at[i, "Data"] = nova_data
                    dados.at[i, "Descrição"] = nova_descricao
                    dados.at[i, "Tipo"] = novo_tipo
                    dados.at[i, "Categoria"] = nova_categoria
                    dados.at[i, "Conta Origem"] = nova_conta_origem
                    dados.at[i, "Conta Destino"] = nova_conta_destino
                    dados.at[i, "Valor"] = novo_valor
                    dados.to_csv(ARQUIVO, index=False)
                    st.session_state.dados = dados  # Atualiza os dados na sessão
                    st.success("Transação atualizada!")
                    st.rerun()


            if st.button("Excluir", key=f"excluir_{row['ID']}"):
                dados = dados[dados["ID"] != row["ID"]]
                dados.to_csv(ARQUIVO, index=False)
                st.session_state.dados = dados  # Atualiza os dados na sessão
                st.warning("Transação excluída!")
                st.rerun()


# ========================== ABA GRÁFICOS ============================
with aba_graficos:
    st.subheader("📈 Visão Geral")
    st.metric("💰 Saldo Atual", saldo_formatado)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Entradas e Saídas")
        totais_tipo = dados_filtrados[dados_filtrados["Tipo"] != "Transferência"].groupby("Tipo")["Valor"].sum().reset_index()
        fig_tipo = px.bar(totais_tipo, x="Tipo", y="Valor", text="Valor", color="Tipo", title="Entradas e Saídas")
        fig_tipo.update_traces(texttemplate='%{text:.2f}')
        st.plotly_chart(fig_tipo, use_container_width=True)

with col2:
    st.markdown("#### Saídas por Categoria")
    saidas_categoria = dados_filtrados[
        dados_filtrados["Tipo"] == "Saída"
    ].groupby("Categoria")["Valor"].sum().reset_index()

    fig_pizza = px.pie(
        saidas_categoria,
        names="Categoria",
        values="Valor",
        title="Distribuição de Saídas por Categoria",
        hole=0.4
    )
    fig_pizza.update_traces(textinfo="percent+label+value")
    st.plotly_chart(fig_pizza, use_container_width=True)
    


