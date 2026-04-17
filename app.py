import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="PMODesk v4.0", layout="wide")

FIREBASE_URL = "https://pmodesk-18f54-default-rtdb.firebaseio.com"

# ====== FIREBASE REST ======
def salvar_projeto(projeto):
    try:
        response = requests.post(f"{FIREBASE_URL}/projetos.json", json=projeto, timeout=10)
        return True
    except:
        st.error("Erro ao salvar!")
        return False

def listar_projetos():
    try:
        response = requests.get(f"{FIREBASE_URL}/projetos.json", timeout=10)
        data = response.json()
        return data if data else {}
    except:
        return {}

def deletar_projeto(proj_id):
    try:
        requests.delete(f"{FIREBASE_URL}/projetos/{proj_id}.json", timeout=10)
        return True
    except:
        return False

def salvar_tarefa(proj_id, tarefa):
    try:
        requests.post(f"{FIREBASE_URL}/tarefas/{proj_id}.json", json=tarefa, timeout=10)
        return True
    except:
        return False

def listar_tarefas(proj_id):
    try:
        response = requests.get(f"{FIREBASE_URL}/tarefas/{proj_id}.json", timeout=10)
        data = response.json()
        return data if data else {}
    except:
        return {}

def deletar_tarefa(proj_id, tar_id):
    try:
        requests.delete(f"{FIREBASE_URL}/tarefas/{proj_id}/{tar_id}.json", timeout=10)
        return True
    except:
        return False

def salvar_risco(proj_id, risco):
    try:
        requests.post(f"{FIREBASE_URL}/riscos/{proj_id}.json", json=risco, timeout=10)
        return True
    except:
        return False

def listar_riscos(proj_id):
    try:
        response = requests.get(f"{FIREBASE_URL}/riscos/{proj_id}.json", timeout=10)
        data = response.json()
        return data if data else {}
    except:
        return {}

def deletar_risco(proj_id, ris_id):
    try:
        requests.delete(f"{FIREBASE_URL}/riscos/{proj_id}/{ris_id}.json", timeout=10)
        return True
    except:
        return False

# ====== SIDEBAR ======
st.sidebar.title("📊 PMODesk v4.0")
pagina = st.sidebar.radio("Menu", [
    "📊 Dashboard",
    "📁 Projetos",
    "✅ Tarefas",
    "⚠️ Riscos"
])

# ====== DASHBOARD ======
if pagina == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    projetos = listar_projetos()
    total = len(projetos)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Projetos", total)
    with col2:
        ativo = len([p for p in projetos.values() if p.get('status') == 'Ativo'])
        st.metric("🚀 Ativos", ativo)
    with col3:
        st.metric("⏳ Hoje", total)
    
    st.subheader("Últimos Projetos")
    if projetos:
        for p in list(projetos.values())[:3]:
            st.write(f"**{p.get('nome')}** - {p.get('status')} ({p.get('progresso_realizado')}%)")
    else:
        st.info("Nenhum projeto ainda")

# ====== PROJETOS ======
elif pagina == "📁 Projetos":
    st.title("📁 Projetos")
    
    tab1, tab2 = st.tabs(["Listar", "Criar"])
    
    with tab1:
        projetos = listar_projetos()
        if projetos:
            for proj_id, p in projetos.items():
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    st.write(f"**{p.get('nome')}** ({p.get('status')})")
                    st.write(f"GP: {p.get('gp')} | {p.get('progresso_realizado')}%")
                with col2:
                    if st.button("🗑️", key=f"d{proj_id[:5]}"):
                        if deletar_projeto(proj_id):
                            st.rerun()
        else:
            st.info("Nenhum projeto")
    
    with tab2:
        st.subheader("Novo Projeto")
        with st.form("proj"):
            nome = st.text_input("Nome *")
            razao_social = st.text_input("Razão Social")
            status = st.selectbox("Status", ["Ativo", "Planejamento", "Encerrado"])
            gp = st.text_input("Gerente")
            progresso = st.slider("Progresso %", 0, 100)
            
            if st.form_submit_button("Salvar"):
                if nome:
                    if salvar_projeto({
                        'nome': nome,
                        'razao_social': razao_social,
                        'status': status,
                        'gp': gp,
                        'progresso_realizado': progresso
                    }):
                        st.success("✅ Criado!")
                        st.rerun()
                else:
                    st.error("Nome obrigatório")

# ====== TAREFAS ======
elif pagina == "✅ Tarefas":
    st.title("✅ Tarefas")
    
    projetos = listar_projetos()
    if not projetos:
        st.warning("Crie um projeto!")
    else:
        proj_id = st.selectbox("Projeto", list(projetos.keys()), 
                               format_func=lambda x: projetos[x].get('nome'))
        
        tab1, tab2 = st.tabs(["Listar", "Criar"])
        
        with tab1:
            tarefas = listar_tarefas(proj_id)
            if tarefas:
                for tar_id, t in tarefas.items():
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        st.write(f"**{t.get('nome')}** ({t.get('status')})")
                    with col2:
                        if st.button("🗑️", key=f"t{tar_id[:5]}"):
                            if deletar_tarefa(proj_id, tar_id):
                                st.rerun()
            else:
                st.info("Nenhuma tarefa")
        
        with tab2:
            with st.form("tar"):
                nome = st.text_input("Nome *")
                responsavel = st.text_input("Responsável")
                status = st.selectbox("Status", ["Pendente", "Progresso", "Concluído"])
                
                if st.form_submit_button("Salvar"):
                    if nome:
                        if salvar_tarefa(proj_id, {
                            'nome': nome,
                            'responsavel': responsavel,
                            'status': status
                        }):
                            st.success("✅ Criado!")
                            st.rerun()
                    else:
                        st.error("Nome obrigatório")

# ====== RISCOS ======
elif pagina == "⚠️ Riscos":
    st.title("⚠️ Riscos")
    
    projetos = listar_projetos()
    if not projetos:
        st.warning("Crie um projeto!")
    else:
        proj_id = st.selectbox("Projeto", list(projetos.keys()), 
                               format_func=lambda x: projetos[x].get('nome'),
                               key="proj_risco")
        
        tab1, tab2 = st.tabs(["Listar", "Criar"])
        
        with tab1:
            riscos = listar_riscos(proj_id)
            if riscos:
                for ris_id, r in riscos.items():
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        st.write(f"**{r.get('descricao')}**")
                        st.write(f"Prob: {r.get('probabilidade')} | Impacto: {r.get('impacto')}")
                    with col2:
                        if st.button("🗑️", key=f"r{ris_id[:5]}"):
                            if deletar_risco(proj_id, ris_id):
                                st.rerun()
            else:
                st.info("Nenhum risco")
        
        with tab2:
            with st.form("ris"):
                descricao = st.text_area("Descrição *")
                probabilidade = st.selectbox("Probabilidade", ["Baixa", "Média", "Alta"])
                impacto = st.selectbox("Impacto", ["Baixo", "Médio", "Alto"])
                resposta = st.selectbox("Resposta", ["Mitigar", "Aceitar", "Evitar"])
                
                if st.form_submit_button("Salvar"):
                    if descricao:
                        if salvar_risco(proj_id, {
                            'descricao': descricao,
                            'probabilidade': probabilidade,
                            'impacto': impacto,
                            'tipo_resposta': resposta
                        }):
                            st.success("✅ Criado!")
                            st.rerun()
                    else:
                        st.error("Descrição obrigatória")

st.sidebar.markdown("---")
st.sidebar.write("**PMODesk v4.0**")
st.sidebar.write("Com Firebase ☁️")
