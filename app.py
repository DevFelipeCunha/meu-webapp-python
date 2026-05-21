import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando)
st.set_page_config(page_title="Planejador de Ambientes", page_icon="🏠", layout="wide")

st.title("📋 Planejador Compartilhado: Balanço de Bens & Compras Futuras")
st.write("Sincronizado em tempo real. Edite pelo smartphone, tablet ou desktop!")

# ==================== CONEXÃO COM O GOOGLE SHEETS ====================
# IMPORTANTE: Cole aqui a URL de compartilhamento da sua planilha (Configurada como EDITOR)
URL_PLANILHA = "COLE_O_LINK_DA_SUA_PLANILHA_AQUI"

def carregar_dados_sheets():
    try:
        # Extrai o ID único da planilha contido na URL do Google
        id_planilha = URL_PLANILHA.split("/d/")[1].split("/")[0]
        url_csv = f"https://docs.google.com/spreadsheets/d/{id_planilha}/export?format=csv"
        
        # Lê os dados limpos direto da nuvem usando apenas o pandas nativo
        dados = pd.read_csv(url_csv)
        
        if dados.empty:
            return pd.DataFrame(columns=["Item", "Categoria", "Status", "Prioridade", "Valor (R$)"])
        return dados
    except Exception as e:
        st.error(f"Aguardando conexão válida com a planilha: {e}")
        return pd.DataFrame(columns=["Item", "Categoria", "Status", "Prioridade", "Valor (R$)"])

# Gerencia o estado dos dados na sessão
if "meus_itens" not in st.session_state or st.sidebar.button("🔄 Forçar Sincronização"):
    st.session_state.meus_itens = carregar_dados_sheets()

df = st.session_state.meus_itens

if not df.empty and "Valor (R$)" in df.columns:
    df["Valor (R$)"] = pd.to_numeric(df["Valor (R$)"], errors='coerce').fillna(0.0)
# =====================================================================

# 2. BARRA LATERAL: CADASTRO DE NOVOS ITENS
st.sidebar.header("➕ Cadastrar Novo Item")
with st.sidebar.form(key="form_cadastro", clear_on_submit=True):
    nome_item = st.text_input("Nome do Item:", placeholder="Ex: Sofá, Geladeira...")
    categoria = st.selectbox("Cômodo / Categoria:", ["Sala", "Cozinha", "Banheiro", "Quarto", "Geral"])
    status = st.radio("Status Atual:", ["Já Possuo", "Desejo Futuro"])
    prioridade = st.selectbox("Prioridade:", ["Alta", "Média", "Baixa"])
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
    st.session_state.meus_itens = pd.concat([df, novo_item], ignore_index=True)
    st.sidebar.success(f"'{nome_item}' adicionado à visualização!")
    st.rerun()

# 3. PAINEL DE INDICADORES (DASHBOARD)
if not df.empty:
    total_possuo = df[df["Status"] == "Já Possuo"]["Valor (R$)"].sum()
    total_desejo = df[df["Status"] == "Desejo Futuro"]["Valor (R$)"].sum()
    total_geral = df["Valor (R$)"].sum()
    
    qtd_possuo = len(df[df["Status"] == "Já Possuo"])
    qtd_total = len(df)
    porcentagem_concluida = (qtd_possuo / qtd_total) if qtd_total > 0 else 0

    st.markdown(f"### 📊 Investimento Total do Projeto: **R$ {total_geral:,.2f}**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="💰 Já Investido", value=f"R$ {total_possuo:,.2f}")
    col2.metric(label="🎯 Orçamento Necessário", value=f"R$ {total_desejo:,.2f}")
    col3.metric(label="📦 Progresso Total", value=f"{qtd_possuo} de {qtd_total} itens", delta=f"{porcentagem_concluida:.1%}")
    
    st.progress(porcentagem_concluida)
    st.divider()

    # 4. GERENCIADOR ESTILO EXCEL
    st.markdown("### ✏️ Visualizar e Modificar Lista Geral")
    
    config_colunas = {
        "Categoria": st.column_config.SelectboxColumn("Cômodo", options=["Sala", "Cozinha", "Banheiro", "Quarto", "Geral"], required=True),
        "Status": st.column_config.SelectboxColumn("Status", options=["Já Possuo", "Desejo Futuro"], required=True),
        "Prioridade": st.column_config.SelectboxColumn("Prioridade", options=["Alta", "Média", "Baixa", "N/A"]),
        "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", min_value=0, format="R$ %.2f")
    }

    df_editado = st.data_editor(df, use_container_width=True, num_rows="dynamic", column_config=config_colunas, key="editor_bens")

    if not df_editado.equals(df):
        st.session_state.meus_itens = df_editado
        st.success("Alterações aplicadas com sucesso no painel!")
        st.rerun()

    st.divider()
    
    csv_download = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Baixar Backup da Lista (CSV)", data=csv_download, file_name="planejamento.csv", mime="text/csv")
else:
    st.info("👋 Use o formulário na lateral para cadastrar os primeiros itens!")
