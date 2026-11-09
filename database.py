"""
Módulo de Banco de Dados - Nexus ERP (SQLite)
Gerencia a persistência transacional de pedidos e o ciclo de vida das execuções RPA.
"""

import sqlite3
import os
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus_erp.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Cria e retorna uma conexão com o banco SQLite com suporte a tipos e chaves estrangeiras."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Inicializa as tabelas do banco de dados com constraints estritas de integridade."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()

            # Tabela de Execuções (Ciclo de Vida da Automação)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execucoes (
                    id_execucao TEXT PRIMARY KEY,
                    status TEXT NOT NULL CHECK(status IN (
                        'Aguardando planilha',
                        'Pronto para processar',
                        'Enviando solicitação ao Orchestrator',
                        'Na fila',
                        'Processando',
                        'Concluído',
                        'Falhou'
                    )),
                    arquivo_origem TEXT,
                    total_pedidos INTEGER DEFAULT 0,
                    pedidos_sucesso INTEGER DEFAULT 0,
                    pedidos_erro INTEGER DEFAULT 0,
                    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_fim TIMESTAMP,
                    mensagem_erro TEXT
                );
            """)

            # Tabela de Pedidos Corporativos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id TEXT NOT NULL UNIQUE,
                    cliente_nome TEXT NOT NULL,
                    produto TEXT NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    valor_unitario REAL NOT NULL CHECK (valor_unitario > 0.0),
                    valor_total REAL NOT NULL CHECK (valor_total > 0.0),
                    protocolo TEXT NOT NULL UNIQUE,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    id_execucao TEXT,
                    FOREIGN KEY (id_execucao) REFERENCES execucoes (id_execucao) ON DELETE SET NULL
                );
            """)

            # Índices para performance e consultas rápidas
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_pedido_id ON pedidos (pedido_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_protocolo ON pedidos (protocolo);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_execucao ON pedidos (id_execucao);")
    finally:
        conn.close()


def gerar_protocolo_unico(cursor: sqlite3.Cursor) -> str:
    """Gera um protocolo único no formato PRT-AAAA-XXXXXX usando o ano atual dinamicamente."""
    ano_atual = datetime.now().year
    while True:
        sufixo = f"{random.randint(100000, 999999)}"
        protocolo = f"PRT-{ano_atual}-{sufixo}"
        cursor.execute("SELECT 1 FROM pedidos WHERE protocolo = ?", (protocolo,))
        if not cursor.fetchone():
            return protocolo


def inserir_pedido(
    pedido_id: str,
    cliente_nome: str,
    produto: str,
    quantidade: int,
    valor_unitario: float,
    id_execucao: Optional[str] = None,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """
    Insere um pedido de forma atômica e transacional.
    Calcula o valor total e gera o protocolo oficial dinâmico.
    Dispara sqlite3.IntegrityError caso viole constraints do banco.
    """
    pedido_id = str(pedido_id).strip().upper()
    cliente_nome = str(cliente_nome).strip()
    produto = str(produto).strip()
    quantidade = int(quantidade)
    valor_unitario = round(float(valor_unitario), 2)
    valor_total = round(quantidade * valor_unitario, 2)

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            protocolo = gerar_protocolo_unico(cursor)

            cursor.execute("""
                INSERT INTO pedidos (
                    pedido_id, cliente_nome, produto, quantidade,
                    valor_unitario, valor_total, protocolo, id_execucao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                pedido_id, cliente_nome, produto, quantidade,
                valor_unitario, valor_total, protocolo, id_execucao
            ))

            novo_id = cursor.lastrowid
            cursor.execute("SELECT * FROM pedidos WHERE id = ?", (novo_id,))
            row = cursor.fetchone()
            return dict(row)
    finally:
        conn.close()


def inserir_lote_pedidos_transacional(
    lista_pedidos: List[Dict[str, Any]],
    id_execucao: Optional[str] = None,
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """
    Insere múltiplos pedidos em uma transação única (tudo ou nada).
    Se qualquer pedido falhar, ocorre ROLLBACK completo de todo o lote.
    """
    conn = get_connection(db_path)
    pedidos_inseridos = []
    try:
        with conn:
            cursor = conn.cursor()
            for p in lista_pedidos:
                pedido_id = str(p['pedido_id']).strip().upper()
                cliente_nome = str(p['cliente_nome']).strip()
                produto = str(p['produto']).strip()
                quantidade = int(p['quantidade'])
                valor_unitario = round(float(p['valor_unitario']), 2)
                valor_total = round(quantidade * valor_unitario, 2)
                protocolo = gerar_protocolo_unico(cursor)

                cursor.execute("""
                    INSERT INTO pedidos (
                        pedido_id, cliente_nome, produto, quantidade,
                        valor_unitario, valor_total, protocolo, id_execucao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    pedido_id, cliente_nome, produto, quantidade,
                    valor_unitario, valor_total, protocolo, id_execucao
                ))
                p_copy = dict(p)
                p_copy['protocolo'] = protocolo
                p_copy['valor_total'] = valor_total
                pedidos_inseridos.append(p_copy)
        return pedidos_inseridos
    except Exception as e:
        # with conn faz rollback automático ao capturar exceção
        raise e
    finally:
        conn.close()


def buscar_pedido_por_id(pedido_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Busca um pedido pelo seu ID de negócio (ex: PED-1001)."""
    pedido_id = str(pedido_id).strip().upper()
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos WHERE pedido_id = ?", (pedido_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def listar_pedidos(limite: int = 100, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retorna os pedidos mais recentes cadastrados no sistema."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos ORDER BY id DESC LIMIT ?", (limite,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def total_pedidos_cadastrados(db_path: str = DB_PATH) -> int:
    """Retorna a contagem total de pedidos persistidos."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def registrar_execucao(
    id_execucao: str,
    status: str,
    arquivo_origem: Optional[str] = None,
    db_path: str = DB_PATH
) -> None:
    """Registra uma nova execução ou atualiza status no banco."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO execucoes (id_execucao, status, arquivo_origem)
                VALUES (?, ?, ?)
                ON CONFLICT(id_execucao) DO UPDATE SET
                    status = excluded.status,
                    arquivo_origem = COALESCE(excluded.arquivo_origem, execucoes.arquivo_origem);
            """, (id_execucao, status, arquivo_origem))
    finally:
        conn.close()


def atualizar_status_execucao(
    id_execucao: str,
    status: str,
    sucessos: int = 0,
    erros: int = 0,
    mensagem_erro: Optional[str] = None,
    db_path: str = DB_PATH
) -> None:
    """Atualiza o ciclo de vida e contadores da execução."""
    data_fim = datetime.now().isoformat() if status in ('Concluído', 'Falhou') else None
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE execucoes SET
                    status = ?,
                    pedidos_sucesso = ?,
                    pedidos_erro = ?,
                    data_fim = COALESCE(?, data_fim),
                    mensagem_erro = ?
                WHERE id_execucao = ?;
            """, (status, sucessos, erros, data_fim, mensagem_erro, id_execucao))
    finally:
        conn.close()
