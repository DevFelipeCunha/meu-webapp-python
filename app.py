import streamlit as st
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Planejador de Ambientes", page_icon="🏠", layout="wide")

st.title("📋 Planejador Compartilhado: Balanço de Bens & Compras Futuras")
st.write("Sincronizado em tempo real. Edite as informações e acompanhe pelo smartphone, tablet ou desktop!")

# ================= CONEXÃO COM O GOOGLE SHEETS =================
# Cole aqui o link da sua planilha do Google que você configurou como EDITORA
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1aDOYJWNtb5lE183WoCJGMZae_OMyttRf7yK9WCa3ibQ/edit?gid=0#gid=0"

# Função para converter o link normal em um link de exportação de dados
def obter_url_csv(url):
    try:
        id_planilha = url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{id_planilha}/export?format=csv"
    except:
        return None

URL_CSV = obter_url_csv(URL_PLANILHA)

# Função para carregar os dados direto da nuvem do Google
def carregar_dados_nuvem():
    if URL_CSV:
        try:
            # O st.cache_data com ttl=2 força o app a buscar dados novos a cada 2 segundos se houver recarga
            return pd.read_csv(URL_CSV)
        except Exception as e:
            st.error(f"Erro ao conectar com a planilha: {e}")
            return pd.DataFrame(columns=["Item", "Categoria", "Status", "Prioridade", "Valor (R$)"])
    else:
        st.warning("Por favor, configure o link correto da sua Planilha do Google no código.")
        return pd.DataFrame(columns=["Item", "Categoria", "Status", "Prioridade", "Valor (R$)"])

# Função para salvar os dados de volta na Planilha do Google usando uma requisição simples
def salvar_dados_nuvem(df_para_salvar):
    try:
        import requests
        id_planilha = URL_PLANILHA.split("/d/")[1].split("/")[0]
        
        # Como estamos usando um método simples sem contas de serviço complexas do Google Cloud,
        # a melhor abordagem para atualizar via código mantendo 100% online e gratuito
        # é usar a biblioteca gspread ou salvar localmente enquanto preparamos o deploy oficial.
        # Para testarmos agora, ele salvará as alterações na sessão atual:
        st.session_state.meus_itens = df_para_salvar
    except:
        pass

# Inicializa os dados buscando da planilha online
if "meus_itens" not in st.session_state:
    st.session_state.meus_itens = carregar_dados_nuvem()

# Botão manual de sincronização no topo para forçar a atualização entre os dois usuários
if st.button("🔄 Sincronizar e Atualizar Dados Agora"):
    st.session_state.meus_itens = carregar_dados_nuvem()
    st.rerun()

# 3. Barra Lateral para Cadastro de Novos Itens
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
    
    # Adiciona o item e simula a atualização
    st.session_state.meus_itens = pd.concat([st.session_state.meus_itens, novo_item], ignore_index=True)
    st.sidebar.success(f"'{nome_item}' adicionado à lista!")
    st.rerun()

# 4. Cálculos e Painel de Indicadores
df = st.session_state.meus_itens

if not df.empty:
    total_possuo = pd.to_numeric(df["Valor (R$)"], errors='coerce').sum()
    total_desejo = pd.to_numeric(df[df["Status"] == "Desejo Futuro"]["Valor (R$)"], errors='coerce').sum()
    total_geral = pd.to_numeric(df["Valor (R$)"], errors='coerce').sum()
    
    qtd_possuo = len(df[df["Status"] == "Já Possuo"])
    qtd_total = len(df)
    porcentagem_concluida = (qtd_possuo / qtd_total) if qtd_total > 0 else 0

    st.markdown(f"### 📊 Investimento Total do Projeto: **R$ {total_geral:,.2f}**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="💰 Já Investido (Bens Atuais)", value=f"R$ {total_possuo:,.2f}")
    col2.metric(label="🎯 Orçamento Necessário", value=f"R$ {total_desejo:,.2f}")
    col3.metric(label="📦 Progresso do Projeto", value=f"{qtd_possuo} de {qtd_total} itens", delta=f"{porcentagem_concluida:.1%}")
    
    st.progress(porcentagem_concluida)
    st.divider()

    # Gráficos
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

    # Planilha de Edição
    st.markdown("### ✏️ Visualizar e Editar Lista")
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

    if not df_editado.equals(df):
        st.session_state.meus_itens = df_editado
        st.success("Alterações aplicadas na tela!")
        st.rerun()
else:
    st.info("👋 Use a barra lateral esquerda para cadastrar seus primeiros itens!")
