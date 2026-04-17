import shutil
import os
from datetime import datetime
from pathlib import Path

def criar_backup_automatico():
    """Cria backup automático do banco de dados"""
    try:
        # Detectar pasta raiz do projeto
        # Se estiver em Streamlit, usar diretório atual
        current_dir = Path.cwd()
        
        # Procurar por pmo.db
        db_path = current_dir / "data" / "pmo.db"
        
        # Se não encontrar, procurar em diretório pai
        if not db_path.exists():
            db_path = current_dir.parent / "data" / "pmo.db"
        
        # Se ainda não encontrar, procurar em PMO-App-v3
        if not db_path.exists():
            possible_paths = list(Path("C:/").glob("**/PMO-App-v3/data/pmo.db")) if os.name == 'nt' else list(Path.home().glob("**/PMO-App-v3/data/pmo.db"))
            if possible_paths:
                db_path = possible_paths[0]
        
        if not db_path.exists():
            print(f"❌ Banco não encontrado em: {db_path}")
            return False
        
        # Pasta de backup próximo ao banco
        backup_dir = db_path.parent.parent / "backups"
        backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Nome do backup com data/hora
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = backup_dir / f"pmo_backup_{timestamp}.db"
        
        # Copiar banco para backup
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ Backup criado: {backup_path}")
        
        # Limpar backups antigos (manter apenas últimos 7)
        backups = sorted(backup_dir.glob("pmo_backup_*.db"), reverse=True)
        for old_backup in backups[7:]:
            old_backup.unlink()
        
        return True
    except Exception as e:
        print(f"❌ Erro ao fazer backup: {e}")
        return False

def restaurar_backup(backup_filename):
    """Restaura um backup específico"""
    try:
        current_dir = Path.cwd()
        backup_dir = current_dir / "backups"
        
        if not backup_dir.exists():
            backup_dir = current_dir.parent / "backups"
        
        backup_path = backup_dir / backup_filename
        
        if not backup_path.exists():
            return False
        
        db_path = current_dir / "data" / "pmo.db"
        if not db_path.exists():
            db_path = current_dir.parent / "data" / "pmo.db"
        
        shutil.copy2(backup_path, db_path)
        
        return True
    except Exception as e:
        print(f"❌ Erro ao restaurar backup: {e}")
        return False

def listar_backups():
    """Lista todos os backups disponíveis"""
    try:
        current_dir = Path.cwd()
        backup_dir = current_dir / "backups"
        
        if not backup_dir.exists():
            backup_dir = current_dir.parent / "backups"
        
        if not backup_dir.exists():
            return []
        
        backups = sorted(backup_dir.glob("pmo_backup_*.db"), reverse=True)
        return [b.name for b in backups]
    except:
        return []
