import streamlit as st
import pandas as pd
import requests
import json

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit)
st.set_page_config(page_title="Centro de Custo", page_icon="🏠", layout="wide")

st.title("📋 Nosso Planejamento Fe+Tha")
st.write("Foco no Foco")

# ==================== CONFIGURAÇÃO DAS URLs ====================
# Cole o link normal da sua planilha do Google (onde você visualiza os dados)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1aDOYJWNtb5lE183WoCJGMZae_OMyttRf7yK9WCa3ibQ/edit?gid=0#gid=0"

# Cole o link do App da Web que você copiou lá do Google Apps Script
URL_API_GOOGLE = "https://script.google.com/macros/s/AKfycbwphg1nMavGitbVu3eRQnFsXm9LsCLbr0xTR1qAPjF7p1MwkN58NyfeorckbEtPkgIZwQ/exec"
# ===============================================================

# Função para buscar dados do Sheets via exportação CSV (Leitura rápida)
def carregar_dados_sheets():
    try:
        id_planilha = URL_PLANILHA.split("/d/")[1].split("/")[0]
        url_csv = f"https://docs.google.com/spreadsheets/d/{id_planilha}/export?format=csv"
        dados = pd.read_csv(url_csv)
        if dados.empty:
            return pd.DataFrame(columns=["Item", "Categoria", "Status", "Prioridade", "Valor (R$)"])
        return dados
    except Exception as e:
        return pd.DataFrame(columns=["Item", "Categoria", "Status", "Prioridade", "Valor (R$)"])

# Função para enviar a tabela inteira atualizada para o Google Sheets (Gravação rápida)
def salvar_dados_sheets(dataframe_atual):
    if URL_API_GOOGLE and "COLE_A_URL" not in URL_API_GOOGLE:
        try:
            dados_json = dataframe_atual.to_dict(orient="records")
            resposta = requests.post(URL_API_GOOGLE, data=json.dumps(dados_json), headers={"Content-Type": "application/json"})
            if resposta.status_code == 200:
                return True
        except:
            pass
    return False

# Inicializa ou sincroniza os dados na sessão
if "meus_itens" not in st.session_state or st.sidebar.button("🔄 Sincronizar Dados"):
    st.session_state.meus_itens = carregar_dados_sheets()

df = st.session_state.meus_itens

if not df.empty and "Valor (R$)" in df.columns:
    df["Valor (R$)"] = pd.to_numeric(df["Valor (R$)"], errors='coerce').fillna(0.0)

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
    df_novo = pd.concat([df, novo_item], ignore_index=True)
    
    with st.spinner("Gravando no Google Sheets..."):
        if salvar_dados_sheets(df_novo):
            st.session_state.meus_itens = df_novo
            st.sidebar.success(f"'{nome_item}' salvo no Google!")
            st.rerun()
        else:
            st.sidebar.error("Erro ao salvar na nuvem. Verifique a URL do Script.")

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

    # ==================== SEÇÃO DE GRÁFICOS (RETORNADA) ====================
    with st.expander("📊 Clique aqui para abrir os Gráficos do Projeto", expanded=False):
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("**Valores Totais Acumulados por Cômodo (R$)**")
            df_gasto_comodo = df.groupby("Categoria")["Valor (R$)"].sum()
            st.bar_chart(df_gasto_comodo, color="#2E8B57")
            
        with col_graf2:
            st.markdown("**Resumo de Itens Cadastrados**")
            df_status_qtd = df.groupby("Status").size().reset_index(name="Quantidade")
            st.dataframe(df_status_qtd, use_container_width=True, hide_index=True)
            
            valor_medio = df["Valor (R$)"].mean()
            st.info(f"💡 Custo médio estimado por item na sua lista: **R$ {valor_medio:,.2f}**")

    st.divider()
    # =======================================================================

    # 4. GERENCIADOR ESTILO EXCEL COM AUTO-SALVAMENTO
    st.markdown("### ✏️ Visualizar e Modificar Lista Geral")
    st.caption("Qualquer alteração feita nas células abaixo será salva na planilha do Google assim que você clicar fora da tabela.")
    
    config_colunas = {
        "Categoria": st.column_config.SelectboxColumn("Cômodo", options=["Sala", "Cozinha", "Banheiro", "Quarto", "Geral"], required=True),
        "Status": st.column_config.SelectboxColumn("Status", options=["Já Possuo", "Desejo Futuro"], required=True),
        "Prioridade": st.column_config.SelectboxColumn("Prioridade", options=["Alta", "Média", "Baixa", "N/A"]),
        "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", min_value=0, format="R$ %.2f")
    }

    df_editado = st.data_editor(df, use_container_width=True, num_rows="dynamic", column_config=config_colunas, key="editor_bens")

    # Se houver edição direta na tabela na tela, dispara o salvamento automático no Google
    if not df_editado.equals(df):
        with st.spinner("Sincronizando alterações com o Google..."):
            if salvar_dados_sheets(df_editado):
                st.session_state.meus_itens = df_editado
                st.toast("Planilha Google updated!", icon="☁️")
                st.rerun()
            else:
                st.error("Falha ao sincronizar edições automáticas.")

    st.divider()
    
    csv_download = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Baixar Backup da Lista (CSV)", data=csv_download, file_name="planejamento.csv", mime="text/csv")
else:
    st.info("👋 Use o formulário na lateral para cadastrar os primeiros itens!")
