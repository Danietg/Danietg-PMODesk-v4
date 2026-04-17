# PMODesk v4.0

Sistema Profissional de Gestao de Projetos PMBOK

Deploy: https://pmoapp-v4.streamlit.app

---

## O que eh PMODesk?

PMODesk e um sistema desktop/web para gerenciar projetos com metodologia PMBOK.

### Funcionalidades

- **Projetos**: 25 campos PMBOK completos
- **Tarefas**: Gestao de tarefas com status e prioridade
- **Riscos**: Identificacao e monitoramento de riscos
- **Mudancas**: Controle de mudancas
- **Macroentregas**: Organizacao de entregas
- **Comunicacoes**: Registro de reunioes e decisoes
- **Dashboard**: KPIs em tempo real
- **Backup**: Automatico e manual
- **Exportacao**: Para Excel com todas as informacoes

---

## Instalacao Local

### Prerequisitos
- Python 3.8+
- pip

### Passos

1. Clone ou baixe este repositorio
2. Instale dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o app:
   ```bash
   python -m streamlit run app.py
   ```

4. Navegador abre em: http://localhost:8501

---

## Deploy no Streamlit Cloud

Este app esta configurado para deploy automatico no Streamlit Cloud.

1. Conecte seu GitHub ao Streamlit Cloud
2. Selecione este repositorio
3. Arquivo principal: `app.py`
4. Deploy automatico!

---

## Estrutura

```
PMODesk-v4/
├── app.py                    # Frontend Streamlit
├── utils_backup.py           # Sistema de backup
├── requirements.txt          # Dependencias
├── .streamlit/
│   └── config.toml          # Configuracoes Streamlit
├── backend/
│   ├── main.py              # API FastAPI
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── routes.py
│   └── requirements.txt
├── data/
│   └── pmo.db               # Banco SQLite
└── README.md
```

---

## Uso

### Instalacao (3 passos)
1. Extrair ZIP
2. Duplo-clique em `installer.bat`
3. Duplo-clique em `run_app.bat`

### Funcionalidades

**Criar Projeto**
1. Va para: PROJETOS
2. Clique em: CRIAR NOVO
3. Preencha 25 campos PMBOK
4. Clique: SALVAR

**Exportar para Excel**
1. Va para: PROJETOS
2. Clique em: EXPORTAR PARA EXCEL
3. Selecione projetos
4. Clique: GERAR EXCEL

**Fazer Backup**
1. Va para: BACKUP
2. Clique em: Fazer Backup Agora
3. Pronto!

---

## Troubleshooting

### Porta ja em uso
Reinicie o computador ou feche outras aplicacoes

### Python nao instalado
Abra chamado na Central de TI para instalar

### Banco corrompido
Delete: `data/pmo.db`
Abra novamente (banco e recriado)

---

## Versao

**PMODesk v4.0**
- Dashboard com KPIs
- 25 campos PMBOK
- Exportacao para Excel
- Backup automatico
- Interface intuitiva

---

## Licenca

Proprietary © 2026

---

*PMODesk v4.0 - Sistema de Gestao de Projetos PMBOK*
