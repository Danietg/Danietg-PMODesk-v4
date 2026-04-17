import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
from io import BytesIO
import json
from utils_backup import criar_backup_automatico, listar_backups, restaurar_backup

st.set_page_config(page_title="PMODesk v4.0", layout="wide", initial_sidebar_state="expanded")

API_URL = "http://127.0.0.1:8000"

# BACKUP AUTOMÁTICO AO INICIAR
criar_backup_automatico()

st.markdown("""
<style>
.header { color: #1f77b4; font-size: 2.2em; font-weight: bold; margin-bottom: 20px; }
.subheader { color: #1f77b4; font-size: 1.5em; font-weight: bold; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📊 PMODesk v4.0")
menu = st.sidebar.radio("Menu", 
    ["📊 Dashboard", "📁 Projetos", "✅ Tarefas", "📦 Macroentregas", "⚠️ Riscos", "🔄 Mudanças", "📅 Comunicações", "💾 Backup"],
    label_visibility="collapsed"
)

def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=3)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def api_post(endpoint, data):
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=5)
        return r.status_code in [200, 201], r.text if r.status_code not in [200, 201] else "OK"
    except Exception as e:
        return False, str(e)

def api_put(endpoint, data):
    try:
        r = requests.put(f"{API_URL}{endpoint}", json=data, timeout=5)
        return r.status_code == 200, r.text if r.status_code != 200 else "OK"
    except Exception as e:
        return False, str(e)

def api_delete(endpoint):
    try:
        r = requests.delete(f"{API_URL}{endpoint}", timeout=3)
        return r.status_code == 200
    except:
        return False

def exportar_para_excel(projetos_selecionados):
    """Exporta projetos selecionados para Excel com todas as informações"""
    try:
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Resumo dos projetos
            df_projetos = pd.DataFrame(projetos_selecionados)
            df_projetos.to_excel(writer, sheet_name='Projetos', index=False)
            
            # Sheets adicionais: Detalhes de cada projeto
            for projeto in projetos_selecionados:
                project_id = projeto.get('id')
                sheet_name = projeto.get('nome')[:31]  # Excel: max 31 chars
                
                # Dados do projeto
                projeto_info = {
                    'Campo': list(projeto.keys()),
                    'Valor': list(projeto.values())
                }
                df_info = pd.DataFrame(projeto_info)
                df_info.to_excel(writer, sheet_name=f'{sheet_name[:25]}_Info', index=False)
                
                # Tarefas do projeto
                tasks = api_get(f"/tasks/?project_id={project_id}")
                if tasks:
                    df_tasks = pd.DataFrame(tasks)
                    df_tasks.to_excel(writer, sheet_name=f'{sheet_name[:20]}_Tarefas', index=False)
                
                # Macroentregas
                macros = api_get(f"/macrodeliveries/?project_id={project_id}")
                if macros:
                    df_macros = pd.DataFrame(macros)
                    df_macros.to_excel(writer, sheet_name=f'{sheet_name[:15]}_Macros', index=False)
                
                # Riscos
                risks = api_get(f"/risks/?project_id={project_id}")
                if risks:
                    df_risks = pd.DataFrame(risks)
                    df_risks.to_excel(writer, sheet_name=f'{sheet_name[:18]}_Riscos', index=False)
                
                # Mudanças
                changes = api_get(f"/changes/?project_id={project_id}")
                if changes:
                    df_changes = pd.DataFrame(changes)
                    df_changes.to_excel(writer, sheet_name=f'{sheet_name[:17]}_Mudanças', index=False)
                
                # Comunicações
                comms = api_get(f"/communications/?project_id={project_id}")
                if comms:
                    df_comms = pd.DataFrame(comms)
                    df_comms.to_excel(writer, sheet_name=f'{sheet_name[:13]}_Comunicações', index=False)
        
        output.seek(0)
        return output
    except Exception as e:
        st.error(f"Erro ao exportar: {e}")
        return None

# ===== DASHBOARD =====
if menu == "📊 Dashboard":
    st.markdown('<p class="header">📊 Dashboard Executivo</p>', unsafe_allow_html=True)
    
    projects = api_get("/projects/")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📁 Projetos", len(projects))
    
    total_tasks = 0
    for p in projects:
        total_tasks += len(api_get(f"/tasks/?project_id={p.get('id')}"))
    col2.metric("✅ Tarefas", total_tasks)
    
    total_risks = sum([len(api_get(f"/risks/?project_id={p.get('id')}")) for p in projects])
    col3.metric("⚠️ Riscos", total_risks)
    
    total_changes = sum([len(api_get(f"/changes/?project_id={p.get('id')}")) for p in projects])
    col4.metric("🔄 Mudanças", total_changes)
    
    avg_progress = sum([p.get('progresso_realizado', 0) for p in projects]) // len(projects) if projects else 0
    col5.metric("📈 Progresso", f"{avg_progress}%")
    
    st.markdown("---")
    st.subheader("Projetos Ativos")
    if projects:
        df = pd.DataFrame(projects)
        st.dataframe(df[["nome", "status", "fase", "gp", "progresso_realizado"]].head(10), use_container_width=True)
    else:
        st.info("Nenhum projeto")

# ===== PROJETOS =====
elif menu == "📁 Projetos":
    st.markdown('<p class="header">📁 Gestão de Projetos PMBOK</p>', unsafe_allow_html=True)
    
    tab_criar, tab_listar, tab_exportar = st.tabs(["➕ Criar Novo", "📋 Listar Todos", "📊 Exportar para Excel"])
    
    with tab_criar:
        st.markdown('<p class="subheader">Novo Projeto</p>', unsafe_allow_html=True)
        
        with st.form("form_novo_projeto"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome do Projeto *")
            with col2:
                razao_social = st.text_input("Razão Social *")
            with col3:
                data_preenchimento = st.date_input("Data Preenchimento", value=date.today())
            
            col1, col2, col3 = st.columns(3)
            with col1:
                contratacao = st.text_input("Contratação")
            with col2:
                chamada = st.text_input("Chamada")
            with col3:
                vertical = st.text_input("Vertical")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                gp = st.text_input("GP (Gerente Projeto)")
            with col2:
                gf = st.text_input("GF (Gestor Financeiro)")
            with col3:
                gt = st.text_input("GT (Gestor Técnico)")
            
            col1, col2 = st.columns(2)
            with col1:
                fase = st.selectbox("Fase", ["Iniciação", "Planejamento", "Execução", "Monitoramento", "Encerramento"])
            with col2:
                status = st.selectbox("Status", ["Planejamento", "Em Execução", "Parado", "Concluído", "Cancelado"])
            
            st.markdown("**📅 Datas do Projeto**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                data_inicio_contrato = st.date_input("Início Contrato")
            with col2:
                data_final_contrato = st.date_input("Fim Contrato")
            with col3:
                data_inicio_execucao = st.date_input("Início Execução")
            with col4:
                data_final_execucao = st.date_input("Fim Execução")
            
            col1, col2 = st.columns(2)
            with col1:
                data_final_cronograma = st.date_input("Data Final Cronograma")
            with col2:
                pass
            
            st.markdown("**📊 Progresso**")
            col1, col2 = st.columns(2)
            with col1:
                progresso_planejado = st.slider("Progresso Planejado (%)", 0, 100, 0)
            with col2:
                progresso_realizado = st.slider("Progresso Realizado (%)", 0, 100, 0)
            
            pontos_criticos = st.text_area("Pontos Críticos", height=50)
            
            st.markdown("**⚙️ TSM (Termo de Suplementação)**")
            tsm_em_andamento = st.selectbox("TSM em Andamento?", ["Não", "Sim"])
            
            if tsm_em_andamento == "Sim":
                col1, col2 = st.columns(2)
                with col1:
                    tsm_status = st.selectbox("Status TSM", ["Aberto", "Em Análise", "Aprovado", "Rejeitado", "Fechado"])
                with col2:
                    tsm_vai_gerar_aditivo = st.selectbox("Vai gerar Aditivo?", ["Não", "Sim"])
                
                tsm_motivo = st.text_input("Motivo TSM")
                tsm_historico = st.text_area("Histórico TSM", height=50)
                
                if tsm_vai_gerar_aditivo == "Sim":
                    tsm_aditivo_desc = st.text_area("Descrição do Aditivo", height=50)
                else:
                    tsm_aditivo_desc = ""
            else:
                tsm_status = ""
                tsm_motivo = ""
                tsm_historico = ""
                tsm_vai_gerar_aditivo = ""
                tsm_aditivo_desc = ""
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ SALVAR PROJETO", use_container_width=True)
            with col2:
                st.form_submit_button("❌ CANCELAR", use_container_width=True)
            
            if submit:
                if not nome or not razao_social:
                    st.error("❌ Nome e Razão Social obrigatórios!")
                else:
                    data_projeto = {
                        "data_preenchimento": str(data_preenchimento),
                        "nome": nome,
                        "razao_social": razao_social,
                        "contratacao": contratacao or "",
                        "chamada": chamada or "",
                        "vertical": vertical or "",
                        "gp": gp or "",
                        "gf": gf or "",
                        "gt": gt or "",
                        "fase": fase,
                        "status": status,
                        "data_inicio_contrato": str(data_inicio_contrato),
                        "data_final_contrato": str(data_final_contrato),
                        "data_inicio_execucao": str(data_inicio_execucao),
                        "data_final_execucao": str(data_final_execucao),
                        "data_final_cronograma": str(data_final_cronograma),
                        "progresso_planejado": progresso_planejado,
                        "progresso_realizado": progresso_realizado,
                        "pontos_criticos": pontos_criticos or "",
                        "tsm_em_andamento": tsm_em_andamento,
                        "tsm_status": tsm_status or "",
                        "tsm_motivo": tsm_motivo or "",
                        "tsm_historico": tsm_historico or "",
                        "tsm_vai_gerar_aditivo": tsm_vai_gerar_aditivo or "",
                        "tsm_aditivo_desc": tsm_aditivo_desc or "",
                    }
                    
                    success, msg = api_post("/projects/", data_projeto)
                    if success:
                        st.success("✅ Projeto criado com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {msg}")
    
    with tab_listar:
        st.markdown('<p class="subheader">Lista de Projetos</p>', unsafe_allow_html=True)
        
        projects = api_get("/projects/")
        
        if projects:
            for project in projects:
                col1, col2, col3, col4 = st.columns([3, 0.8, 0.8, 0.8])
                
                with col1:
                    st.write(f"**📁 {project.get('nome')}**")
                    st.caption(f"RS: {project.get('razao_social')} | GP: {project.get('gp')} | Status: {project.get('status')}")
                
                with col2:
                    if st.button("📖 VER", key=f"view_{project.get('id')}", use_container_width=True):
                        st.session_state.selected_project_id = project.get('id')
                
                with col3:
                    if st.button("✏️ EDITAR", key=f"edit_{project.get('id')}", use_container_width=True):
                        st.session_state.edit_project_id = project.get('id')
                
                with col4:
                    if st.button("🗑️ DELETAR", key=f"del_{project.get('id')}", use_container_width=True):
                        if api_delete(f"/projects/{project.get('id')}"):
                            st.success("Deletado!")
                            st.rerun()
                
                # Editar projeto
                if st.session_state.get('edit_project_id') == project.get('id'):
                    st.markdown("---")
                    st.markdown("### ✏️ EDITAR PROJETO")
                    
                    with st.form(f"edit_form_{project.get('id')}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            nome_edit = st.text_input("Nome", value=project.get('nome'))
                        with col2:
                            razao_social_edit = st.text_input("Razão Social", value=project.get('razao_social', ''))
                        with col3:
                            data_preench_edit = st.date_input("Data Preenchimento", 
                                value=datetime.strptime(project.get('data_preenchimento', '2026-01-01'), '%Y-%m-%d').date() if project.get('data_preenchimento') else date.today())
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            contratacao_edit = st.text_input("Contratação", value=project.get('contratacao', ''))
                        with col2:
                            chamada_edit = st.text_input("Chamada", value=project.get('chamada', ''))
                        with col3:
                            vertical_edit = st.text_input("Vertical", value=project.get('vertical', ''))
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            gp_edit = st.text_input("GP", value=project.get('gp', ''))
                        with col2:
                            gf_edit = st.text_input("GF", value=project.get('gf', ''))
                        with col3:
                            gt_edit = st.text_input("GT", value=project.get('gt', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            fase_edit = st.selectbox("Fase", 
                                ["Iniciação", "Planejamento", "Execução", "Monitoramento", "Encerramento"],
                                index=["Iniciação", "Planejamento", "Execução", "Monitoramento", "Encerramento"].index(project.get('fase', 'Planejamento')))
                        with col2:
                            status_edit = st.selectbox("Status", 
                                ["Planejamento", "Em Execução", "Parado", "Concluído", "Cancelado"],
                                index=["Planejamento", "Em Execução", "Parado", "Concluído", "Cancelado"].index(project.get('status', 'Planejamento')))
                        
                        st.markdown("**📅 Datas**")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            data_ini_cont_edit = st.date_input("Início Contrato",
                                value=datetime.strptime(project.get('data_inicio_contrato', '2026-01-01'), '%Y-%m-%d').date() if project.get('data_inicio_contrato') else date.today())
                        with col2:
                            data_fim_cont_edit = st.date_input("Fim Contrato",
                                value=datetime.strptime(project.get('data_final_contrato', '2026-01-01'), '%Y-%m-%d').date() if project.get('data_final_contrato') else date.today())
                        with col3:
                            data_ini_exec_edit = st.date_input("Início Execução",
                                value=datetime.strptime(project.get('data_inicio_execucao', '2026-01-01'), '%Y-%m-%d').date() if project.get('data_inicio_execucao') else date.today())
                        with col4:
                            data_fim_exec_edit = st.date_input("Fim Execução",
                                value=datetime.strptime(project.get('data_final_execucao', '2026-01-01'), '%Y-%m-%d').date() if project.get('data_final_execucao') else date.today())
                        
                        col1 = st.columns(1)[0]
                        with col1:
                            data_fim_cron_edit = st.date_input("Data Final Cronograma",
                                value=datetime.strptime(project.get('data_final_cronograma', '2026-01-01'), '%Y-%m-%d').date() if project.get('data_final_cronograma') else date.today())
                        
                        st.markdown("**📊 Progresso**")
                        col1, col2 = st.columns(2)
                        with col1:
                            progresso_plan_edit = st.slider("Progresso Planejado (%)", 0, 100, project.get('progresso_planejado', 0), key=f"plan_{project.get('id')}")
                        with col2:
                            progresso_real_edit = st.slider("Progresso Realizado (%)", 0, 100, project.get('progresso_realizado', 0), key=f"real_{project.get('id')}")
                        
                        pontos_criticos_edit = st.text_area("Pontos Críticos", value=project.get('pontos_criticos', ''), height=50)
                        
                        st.markdown("**⚙️ TSM**")
                        tsm_anda_edit = st.selectbox("TSM em Andamento?", ["Não", "Sim"], 
                            index=0 if project.get('tsm_em_andamento', 'Não') == 'Não' else 1)
                        
                        if tsm_anda_edit == "Sim":
                            tsm_status_edit = st.selectbox("Status TSM", ["Aberto", "Em Análise", "Aprovado", "Rejeitado", "Fechado"], key=f"tsm_stat_{project.get('id')}")
                            tsm_motivo_edit = st.text_input("Motivo TSM", value=project.get('tsm_motivo', ''))
                            tsm_hist_edit = st.text_area("Histórico TSM", value=project.get('tsm_historico', ''), height=50)
                            tsm_aditivo_yn_edit = st.selectbox("Vai gerar Aditivo?", ["Não", "Sim"], key=f"adit_yn_{project.get('id')}")
                            if tsm_aditivo_yn_edit == "Sim":
                                tsm_aditivo_desc_edit = st.text_area("Descrição Aditivo", value=project.get('tsm_aditivo_desc', ''), height=50)
                            else:
                                tsm_aditivo_desc_edit = ""
                        else:
                            tsm_status_edit = ""
                            tsm_motivo_edit = ""
                            tsm_hist_edit = ""
                            tsm_aditivo_yn_edit = ""
                            tsm_aditivo_desc_edit = ""
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ ATUALIZAR"):
                                data_update = {
                                    "data_preenchimento": str(data_preench_edit),
                                    "nome": nome_edit,
                                    "razao_social": razao_social_edit,
                                    "contratacao": contratacao_edit,
                                    "chamada": chamada_edit,
                                    "vertical": vertical_edit,
                                    "gp": gp_edit,
                                    "gf": gf_edit,
                                    "gt": gt_edit,
                                    "fase": fase_edit,
                                    "status": status_edit,
                                    "data_inicio_contrato": str(data_ini_cont_edit),
                                    "data_final_contrato": str(data_fim_cont_edit),
                                    "data_inicio_execucao": str(data_ini_exec_edit),
                                    "data_final_execucao": str(data_fim_exec_edit),
                                    "data_final_cronograma": str(data_fim_cron_edit),
                                    "progresso_planejado": progresso_plan_edit,
                                    "progresso_realizado": progresso_real_edit,
                                    "pontos_criticos": pontos_criticos_edit,
                                    "tsm_em_andamento": tsm_anda_edit,
                                    "tsm_status": tsm_status_edit,
                                    "tsm_motivo": tsm_motivo_edit,
                                    "tsm_historico": tsm_hist_edit,
                                    "tsm_vai_gerar_aditivo": tsm_aditivo_yn_edit,
                                    "tsm_aditivo_desc": tsm_aditivo_desc_edit,
                                }
                                success, msg = api_put(f"/projects/{project.get('id')}", data_update)
                                if success:
                                    st.success("✅ Projeto atualizado!")
                                    st.session_state.edit_project_id = None
                                    st.rerun()
                        
                        with col2:
                            if st.form_submit_button("❌ CANCELAR"):
                                st.session_state.edit_project_id = None
                                st.rerun()
                
                st.divider()
        else:
            st.info("Nenhum projeto criado. Crie um novo!")
    
    with tab_exportar:
        st.markdown('<p class="subheader">Exportar para Excel</p>', unsafe_allow_html=True)
        
        projects = api_get("/projects/")
        
        if projects:
            st.write("**Selecione um ou mais projetos para exportar:**")
            
            projetos_selecionados = []
            
            for project in projects:
                if st.checkbox(f"📁 {project.get('nome')}", key=f"export_{project.get('id')}"):
                    projetos_selecionados.append(project)
            
            if st.button("📊 GERAR EXCEL COM OS PROJETOS SELECIONADOS", use_container_width=True):
                if projetos_selecionados:
                    excel_file = exportar_para_excel(projetos_selecionados)
                    
                    if excel_file:
                        st.download_button(
                            label="⬇️ Baixar Excel",
                            data=excel_file,
                            file_name=f"PMODesk_Projetos_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success(f"✅ Excel gerado com {len(projetos_selecionados)} projeto(s)!")
                else:
                    st.warning("⚠️ Selecione pelo menos um projeto!")
        else:
            st.info("Nenhum projeto disponível")

# ===== TAREFAS (SIMPLIFICADO) =====
elif menu == "✅ Tarefas":
    st.markdown('<p class="header">✅ Gestão de Tarefas</p>', unsafe_allow_html=True)
    
    projects = api_get("/projects/")
    
    if not projects:
        st.warning("Crie um projeto primeiro!")
    else:
        project_dict = {p["id"]: p["nome"] for p in projects}
        selected_proj = st.selectbox("Selecione o Projeto", list(project_dict.keys()), format_func=lambda x: project_dict[x])
        
        tab_criar, tab_listar = st.tabs(["➕ Nova Tarefa", "📋 Listar"])
        
        with tab_criar:
            with st.form("form_nova_tarefa"):
                nome = st.text_input("Nome da Tarefa *")
                descricao = st.text_area("Descrição", height=100)
                responsavel = st.text_input("Responsável")
                status = st.selectbox("Status", ["Pendente", "Em Progresso", "Concluído", "Bloqueado"])
                prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"])
                
                if st.form_submit_button("✅ CRIAR TAREFA"):
                    if not nome:
                        st.error("Nome obrigatório!")
                    else:
                        success, msg = api_post("/tasks/", {
                            "project_id": selected_proj,
                            "nome": nome,
                            "descricao": descricao or "",
                            "responsavel": responsavel or "",
                            "status": status,
                            "prioridade": prioridade
                        })
                        if success:
                            st.success("✅ Tarefa criada!")
                            st.rerun()
        
        with tab_listar:
            tasks = api_get(f"/tasks/?project_id={selected_proj}")
            if tasks:
                for task in tasks:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{task.get('nome')}** | {task.get('status')} | {task.get('prioridade')}")
                    with col2:
                        if st.button("✏️", key=f"edit_task_{task.get('id')}"):
                            st.session_state.edit_task_id = task.get('id')
                    with col3:
                        if st.button("🗑️", key=f"del_task_{task.get('id')}"):
                            if api_delete(f"/tasks/{task.get('id')}"):
                                st.rerun()
                    
                    if st.session_state.get('edit_task_id') == task.get('id'):
                        with st.form(f"edit_task_{task.get('id')}"):
                            nome_edit = st.text_input("Nome", value=task.get('nome'))
                            status_edit = st.selectbox("Status", ["Pendente", "Em Progresso", "Concluído", "Bloqueado"])
                            if st.form_submit_button("Atualizar"):
                                api_put(f"/tasks/{task.get('id')}", {"nome": nome_edit, "status": status_edit})
                                st.rerun()
            else:
                st.info("Nenhuma tarefa")

# ===== MACROENTREGAS (SIMPLIFICADO) =====
elif menu == "📦 Macroentregas":
    st.markdown('<p class="header">📦 Macroentregas</p>', unsafe_allow_html=True)
    
    projects = api_get("/projects/")
    
    if not projects:
        st.warning("Crie um projeto primeiro!")
    else:
        project_dict = {p["id"]: p["nome"] for p in projects}
        selected_proj = st.selectbox("Selecione o Projeto", list(project_dict.keys()), format_func=lambda x: project_dict[x], key="macro_proj")
        
        tab_criar, tab_listar = st.tabs(["➕ Nova", "📋 Listar"])
        
        with tab_criar:
            with st.form("form_nova_macro"):
                nome = st.text_input("Nome *")
                data_planejada = st.date_input("Data Planejada")
                data_real = st.date_input("Data Real (opcional)")
                progresso = st.slider("Progresso (%)", 0, 100, 0)
                owner = st.text_input("Owner/Responsável")
                
                if st.form_submit_button("✅ CRIAR"):
                    if not nome:
                        st.error("Nome obrigatório!")
                    else:
                        success, msg = api_post("/macrodeliveries/", {
                            "project_id": selected_proj,
                            "nome": nome,
                            "data_planejada": str(data_planejada),
                            "data_real": str(data_real) if data_real else None,
                            "progresso": progresso,
                            "owner": owner or "",
                            "status": "Planejada"
                        })
                        if success:
                            st.success("✅ Criada!")
                            st.rerun()
        
        with tab_listar:
            macros = api_get(f"/macrodeliveries/?project_id={selected_proj}")
            if macros:
                for macro in macros:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"📦 **{macro.get('nome')}** | {macro.get('progresso')}%")
                    with col2:
                        if st.button("🗑️", key=f"del_macro_{macro.get('id')}"):
                            if api_delete(f"/macrodeliveries/{macro.get('id')}"):
                                st.rerun()
            else:
                st.info("Nenhuma macroentrega")

# ===== RISCOS =====
elif menu == "⚠️ Riscos":
    st.markdown('<p class="header">⚠️ Riscos</p>', unsafe_allow_html=True)
    
    projects = api_get("/projects/")
    
    if not projects:
        st.warning("Crie um projeto primeiro!")
    else:
        project_dict = {p["id"]: p["nome"] for p in projects}
        selected_proj = st.selectbox("Selecione o Projeto", list(project_dict.keys()), format_func=lambda x: project_dict[x], key="risk_proj")
        
        tab_criar, tab_listar = st.tabs(["➕ Novo", "📋 Listar"])
        
        with tab_criar:
            with st.form("form_novo_risco"):
                descricao = st.text_input("Descrição *")
                probabilidade = st.selectbox("Probabilidade", ["Baixa", "Média", "Alta", "Muito Alta"])
                impacto = st.selectbox("Impacto", ["Baixo", "Médio", "Alto", "Crítico"])
                tipo_resposta = st.selectbox("Tipo Resposta", ["Mitigar", "Aceitar", "Evitar", "Transferir"])
                plano_resposta = st.text_area("Plano de Resposta", height=80)
                
                if st.form_submit_button("✅ CRIAR"):
                    if not descricao:
                        st.error("Descrição obrigatória!")
                    else:
                        success, msg = api_post("/risks/", {
                            "project_id": selected_proj,
                            "descricao": descricao,
                            "probabilidade": probabilidade,
                            "impacto": impacto,
                            "tipo_resposta": tipo_resposta,
                            "plano_resposta": plano_resposta or "",
                            "status": "Ativo"
                        })
                        if success:
                            st.success("✅ Risco criado!")
                            st.rerun()
        
        with tab_listar:
            risks = api_get(f"/risks/?project_id={selected_proj}")
            if risks:
                for risk in risks:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"⚠️ **{risk.get('descricao')}** | {risk.get('probabilidade')} / {risk.get('impacto')}")
                    with col2:
                        if st.button("🗑️", key=f"del_risk_{risk.get('id')}"):
                            if api_delete(f"/risks/{risk.get('id')}"):
                                st.rerun()
            else:
                st.info("Nenhum risco")

# ===== MUDANÇAS =====
elif menu == "🔄 Mudanças":
    st.markdown('<p class="header">🔄 Mudanças</p>', unsafe_allow_html=True)
    
    projects = api_get("/projects/")
    
    if not projects:
        st.warning("Crie um projeto primeiro!")
    else:
        project_dict = {p["id"]: p["nome"] for p in projects}
        selected_proj = st.selectbox("Selecione o Projeto", list(project_dict.keys()), format_func=lambda x: project_dict[x], key="change_proj")
        
        tab_criar, tab_listar = st.tabs(["➕ Nova", "📋 Listar"])
        
        with tab_criar:
            with st.form("form_nova_mudanca"):
                titulo = st.text_input("Título *")
                descricao = st.text_area("Descrição", height=100)
                motivo = st.text_input("Motivo")
                impacto_cronograma = st.number_input("Impacto no Cronograma (dias)", value=0)
                impacto_custo = st.number_input("Impacto no Custo (R$)", value=0.0)
                status = st.selectbox("Status", ["Aberta", "Aprovada", "Rejeitada", "Implementada"])
                
                if st.form_submit_button("✅ CRIAR"):
                    if not titulo:
                        st.error("Título obrigatório!")
                    else:
                        success, msg = api_post("/changes/", {
                            "project_id": selected_proj,
                            "titulo": titulo,
                            "descricao": descricao or "",
                            "motivo": motivo or "",
                            "impacto_cronograma": impacto_cronograma,
                            "impacto_custo": impacto_custo,
                            "status": status
                        })
                        if success:
                            st.success("✅ Mudança criada!")
                            st.rerun()
        
        with tab_listar:
            changes = api_get(f"/changes/?project_id={selected_proj}")
            if changes:
                for change in changes:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"🔄 **{change.get('titulo')}** | {change.get('status')}")
                    with col2:
                        if st.button("🗑️", key=f"del_change_{change.get('id')}"):
                            if api_delete(f"/changes/{change.get('id')}"):
                                st.rerun()
            else:
                st.info("Nenhuma mudança")

# ===== COMUNICAÇÕES =====
elif menu == "📅 Comunicações":
    st.markdown('<p class="header">📅 Comunicações</p>', unsafe_allow_html=True)
    
    projects = api_get("/projects/")
    
    if not projects:
        st.warning("Crie um projeto primeiro!")
    else:
        project_dict = {p["id"]: p["nome"] for p in projects}
        selected_proj = st.selectbox("Selecione o Projeto", list(project_dict.keys()), format_func=lambda x: project_dict[x], key="comm_proj")
        
        tab_criar, tab_listar = st.tabs(["➕ Nova", "📋 Listar"])
        
        with tab_criar:
            with st.form("form_nova_comm"):
                tipo = st.selectbox("Tipo", ["Reunião", "Email", "Status Report", "Logbook", "Comunicado"])
                titulo = st.text_input("Título *")
                descricao = st.text_area("Descrição", height=150)
                
                if st.form_submit_button("✅ CRIAR"):
                    if not titulo:
                        st.error("Título obrigatório!")
                    else:
                        success, msg = api_post("/communications/", {
                            "project_id": selected_proj,
                            "tipo": tipo,
                            "titulo": titulo,
                            "descricao": descricao or ""
                        })
                        if success:
                            st.success("✅ Comunicação criada!")
                            st.rerun()
        
        with tab_listar:
            comms = api_get(f"/communications/?project_id={selected_proj}")
            if comms:
                for comm in comms:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"📅 **{comm.get('tipo')}** - {comm.get('titulo')}")
                    with col2:
                        if st.button("🗑️", key=f"del_comm_{comm.get('id')}"):
                            if api_delete(f"/communications/{comm.get('id')}"):
                                st.rerun()
            else:
                st.info("Nenhuma comunicação")

# ===== BACKUP =====
elif menu == "💾 Backup":
    st.markdown('<p class="header">💾 Sistema de Backup</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Backups Disponíveis")
        backups = listar_backups()
        
        if backups:
            for backup in backups:
                st.write(f"✅ {backup}")
        else:
            st.info("Nenhum backup disponível")
    
    with col2:
        st.markdown("### 🔄 Ações")
        
        if st.button("💾 Fazer Backup Agora", use_container_width=True):
            if criar_backup_automatico():
                st.success("✅ Backup realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao fazer backup")

st.sidebar.markdown("---")
st.sidebar.markdown("**PMODesk v4.0** © 2026 | Gestão de Projetos PMBOK")
