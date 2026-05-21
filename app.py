import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da Página
st.set_page_config(page_title="Planejador de Ambientes", page_icon="🏠", layout="wide")

st.title("📋 Planejador Compartilhado: Balanço de Bens & Compras Futuras")
st.write("Sincronizado em tempo real com o Google Sheets. Funciona em Smartphone, Tablet e PC!")

# ================= CONEXÃO COM O GOOGLE SHEETS =================
# Cole aqui a URL de compartilhamento da sua planilha (aquela que configuramos como EDITOR)
URL_PLANILHA = https://docs.google.com/spreadsheets/d/1aDOYJWNtb5lE183WoCJGMZae_OMyttRf7yK9WCa3ibQ/edit?gid=0#gid=0


# Inicializa a conexão oficial do Streamlit com o Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para buscar dados atualizados da nuvem
def carregar_dados_sheets():
    try:
        # Lê os dados da planilha pública usando a URL fornecida
        return conn.read(spreadsheet=URL_PLANILHA, ttl="0d")
    except Exception as e:
        # Se a planilha estiver vazia ou der erro, retorna a estrutura padrão
        return pd.DataFrame(columns=["Item", "Categoria", "Status", "Prioridade", "Valor (R$)"])

# Carrega os dados para a sessão atual
if "meus_itens" not in st.session_state or st.sidebar.button("🔄 Forçar Sincronização"):
    st.session_state.meus_itens = carregar_dados_sheets()

df = st.session_state.meus_itens

# Garantir que as colunas estejam com os tipos corretos
if not df.empty:
    df["Valor (R$)"] = pd.to_numeric(df["Valor (R$)"], errors='coerce').fillna(0.0)
# ===============================================================

# 2. Barra Lateral para Cadastro de Novos Itens
st.sidebar.header("➕ Cadastrar Novo Item")
with st.sidebar.form(key="form_cadastro", clear_on_submit=True):
    nome_item = st.text_input("Nome do Item:", placeholder="Ex: Sofá, Geladeira...")
    categoria = st.selectbox("Cômodo / Categoria:", ["Sala", "Cozinha", "Banheiro", "Quarto", "Geral"])
    status = st.radio("Status Atual:", ["Já Possuo", "Desejo Futuro"])
    prioridade = st.selectbox("Prioridade (para compras futuras):", ["Alta", "Média", "Baixa"])
    valor = st.number_input("Valor Estimado (R$):", min_value=0.0, step=50.0, value=0.0)
    
    botao_salvar = st.form_submit_button("Salvar Item")

if botao_salvar and nome_item:
    novo_item = pd.DataFrame([{
        "Item": nome_item,
        "Categoria": categoria,
        "Status": status,
        "Prioridade": prioridade if status == "Desejo Futuro" else "N/A",
        "Valor (R$)": valor
    }])
    
    # Junta o novo item ao banco de dados existente
    df_atualizado = pd.concat([df, novo_item], ignore_index=True)
    
    try:
        # GRAVA DE FATO NA PLANILHA DO GOOGLE
        conn.update(spreadsheet=URL_PLANILHA, data=df_atualizado)
        st.session_state.meus_itens = df_atualizado
        st.sidebar.success(f"'{nome_item}' gravado no Google Sheets!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar: {e}. Verifique se a planilha está configurada como 'Editor' para qualquer pessoa com o link.")

# 3. Cálculos e Painel de Indicadores (Dashboard)
if not df.empty:
    total_possuo = df[df["Status"] == "Já Possuo"]["Valor (R$)"].sum()
    total_desejo = df[df["Status"] == "Desejo Futuro"]["Valor (R$)"].sum()
    total_geral = df["Valor (R$)"].sum()
    
    qtd_possuo = len(df[df["Status"] == "Já Possuo"])
    qtd_total = len(df)
    porcentagem_concluida = (qtd_possuo / qtd_total) if qtd_total > 0 else 0

    st.markdown(f"### 📊 Investimento Total do Projeto: **R$ {total_geral:,.2f}**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="💰 Já Investido (Bens Atuais)", value=f"R$ {total_possuo:,.2f}")
    col2.metric(label="🎯 Orçamento Necessário (Desejos)", value=f"R$ {total_desejo:,.2f}")
    col3.metric(label="📦 Progresso do Projeto", value=f"{qtd_possuo} de {qtd_total} itens", delta=f"{porcentagem_concluida:.1%}")
    
    st.progress(porcentagem_concluida)
    st.divider()

    # Gráficos Dinâmicos
    with st.expander("📊 Clique aqui para abrir os Gráficos do Projeto", expanded=False):
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("**Valores Totais por Cômodo (R$)**")
            df_gasto_comodo = df.groupby("Categoria")["Valor (R$)"].sum()
            st.bar_chart(df_gasto_comodo, color="#2E8B57")
        with col_graf2:
            st.markdown("**Resumo de Itens por Status**")
            df_status_qtd = df.groupby("Status").size().reset_index(name="Quantidade")
            st.dataframe(df_status_qtd, use_container_width=True, hide_index=True)

    st.divider()

    # Planilha de Edição e Exclusão Simultânea
    st.markdown("### ✏️ Visualizar e Editar Lista")
    st.caption("Qualquer alteração feita abaixo ou linhas deletadas serão sincronizadas na planilha ao clicar fora da tabela.")
    
    config_colunas = {
        "Categoria": st.column_config.SelectboxColumn("Cômodo", options=["Sala", "Cozinha", "Banheiro", "Quarto", "Geral"], required=True),
        "Status": st.column_config.SelectboxColumn("Status", options=["Já Possuo", "Desejo Futuro"], required=True),
        "Prioridade": st.column_config.SelectboxColumn("Prioridade", options=["Alta", "Média", "Baixa", "N/A"]),
        "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", min_value=0, format="R$ %.2f")
    }

    df_editado = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config=config_colunas,
        key="editor_bens_desejos"
    )

    # Se você alterar algo na tabela da tela, envia a alteração de volta pro Google Sheets
    if not df_editado.equals(df):
        try:
            conn.update(spreadsheet=URL_PLANILHA, data=df_editado)
            st.session_state.meus_itens = df_editado
            st.success("Planilha Google Sheets atualizada com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar edição: {e}")
else:
    st.info("👋 Use a barra lateral esquerda para cadastrar seus primeiros itens!")
