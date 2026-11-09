"""
Script de Teste e Validação da Micro-etapa 2.1 (Banco de Dados SQLite)
Executa os 6 testes obrigatórios de integridade, constraints e rollback.
"""

import os
import sys
import sqlite3
from datetime import datetime
import database

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_nexus_erp.db")

def run_tests():
    print("=" * 65)
    print(" BATERIA DE TESTES DE INTEGRIDADE: database.py (MICRO-ETAPA 2.1)")
    print("=" * 65)

    # Limpeza prévia para isolar os testes
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    ano_atual = datetime.now().year

    # -------------------------------------------------------------
    # Teste 1: Inicializar o banco
    # -------------------------------------------------------------
    print("\n[TESTE 1] Inicialização do Banco de Dados e Criação de Tabelas...")
    database.init_db(TEST_DB)
    assert os.path.exists(TEST_DB), "Falha: Arquivo do banco de dados não foi criado."
    
    conn = database.get_connection(TEST_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        assert "pedidos" in tables, "Falha: Tabela 'pedidos' não encontrada."
        assert "execucoes" in tables, "Falha: Tabela 'execucoes' não encontrada."
    finally:
        conn.close()
    print(" -> PASSOU: Tabelas 'pedidos' e 'execucoes' criadas com sucesso.")

    # -------------------------------------------------------------
    # Teste 2: Inserir um pedido válido
    # -------------------------------------------------------------
    print("\n[TESTE 2] Inserção de Pedido Válido...")
    pedido = database.inserir_pedido(
        pedido_id="PED-1001",
        cliente_nome="Indústria Metalúrgica Alfa",
        produto="Parafuso Sextavado 8mm",
        quantidade=50,
        valor_unitario=2.50,
        db_path=TEST_DB
    )
    assert pedido is not None, "Falha: Pedido não foi retornado."
    assert pedido["pedido_id"] == "PED-1001", "Falha: ID divergente."
    assert pedido["valor_total"] == 125.00, f"Falha: Total incorreto. Esperado: 125.0, Obtido: {pedido['valor_total']}"
    print(f" -> PASSOU: Pedido inserido: ID={pedido['pedido_id']} | Total=R$ {pedido['valor_total']} | Protocolo={pedido['protocolo']}")

    # -------------------------------------------------------------
    # Teste 3: Consultar o pedido e conferir o protocolo dinâmico
    # -------------------------------------------------------------
    print("\n[TESTE 3] Consulta e Validação do Protocolo Dinâmico (PRT-AAAA-XXXXXX)...")
    consultado = database.buscar_pedido_por_id("PED-1001", db_path=TEST_DB)
    assert consultado is not None, "Falha: Pedido não encontrado na consulta."
    protocolo = consultado["protocolo"]
    partes = protocolo.split("-")
    assert len(partes) == 3, f"Falha: Formato inválido de protocolo: {protocolo}"
    assert partes[0] == "PRT", f"Falha: Prefixo divergente: {partes[0]}"
    assert partes[1] == str(ano_atual), f"Falha: Ano não é dinâmico. Esperado: {ano_atual}, Obtido: {partes[1]}"
    assert len(partes[2]) == 6 and partes[2].isdigit(), f"Falha: Sufixo numérico inválido: {partes[2]}"
    print(f" -> PASSOU: Protocolo verificado: {protocolo} (Ano atual dinâmico: {partes[1]})")

    # -------------------------------------------------------------
    # Teste 4: Tentar inserir o mesmo ID_Pedido (Constraint de Unicidade)
    # -------------------------------------------------------------
    print("\n[TESTE 4] Bloqueio de Duplicidade de ID_Pedido (SQLite UNIQUE Constraint)...")
    bloqueado_duplicidade = False
    try:
        database.inserir_pedido(
            pedido_id="PED-1001",
            cliente_nome="Outro Cliente",
            produto="Outro Produto",
            quantidade=10,
            valor_unitario=5.00,
            db_path=TEST_DB
        )
    except sqlite3.IntegrityError as e:
        bloqueado_duplicidade = True
        print(f" -> PASSOU: Bloqueio confirmado pelo SQLite: {e}")
    assert bloqueado_duplicidade, "Falha: SQLite permitiu cadastrar ID_Pedido duplicado."

    # -------------------------------------------------------------
    # Teste 5: Tentar inserir quantidade ou valor unitário inválido (<= 0)
    # -------------------------------------------------------------
    print("\n[TESTE 5] Bloqueio de Valores Inválidos (SQLite CHECK Constraints)...")
    # Caso 5.1: Quantidade Zero
    bloqueado_qtd_zero = False
    try:
        database.inserir_pedido("PED-1002", "Cliente Teste", "Produto", quantidade=0, valor_unitario=10.0, db_path=TEST_DB)
    except sqlite3.IntegrityError as e:
        bloqueado_qtd_zero = True
        print(f" -> PASSOU: Quantidade 0 rejeitada pela CHECK constraint: {e}")
    assert bloqueado_qtd_zero, "Falha: SQLite permitiu quantidade 0."

    # Caso 5.2: Quantidade Negativa
    bloqueado_qtd_neg = False
    try:
        database.inserir_pedido("PED-1003", "Cliente Teste", "Produto", quantidade=-5, valor_unitario=10.0, db_path=TEST_DB)
    except sqlite3.IntegrityError as e:
        bloqueado_qtd_neg = True
        print(f" -> PASSOU: Quantidade negativa rejeitada pela CHECK constraint: {e}")
    assert bloqueado_qtd_neg, "Falha: SQLite permitiu quantidade negativa."

    # Caso 5.3: Valor Unitário Zero
    bloqueado_val_zero = False
    try:
        database.inserir_pedido("PED-1004", "Cliente Teste", "Produto", quantidade=10, valor_unitario=0.0, db_path=TEST_DB)
    except sqlite3.IntegrityError as e:
        bloqueado_val_zero = True
        print(f" -> PASSOU: Valor unitário 0.0 rejeitado pela CHECK constraint: {e}")
    assert bloqueado_val_zero, "Falha: SQLite permitiu valor unitário 0."

    # -------------------------------------------------------------
    # Teste 6: Provocar falha transacional e validar ROLLBACK estrito
    # -------------------------------------------------------------
    print("\n[TESTE 6] Validação de Transação e Rollback (ACID)...")
    total_antes = database.total_pedidos_cadastrados(db_path=TEST_DB)
    print(f" Total de pedidos antes do lote: {total_antes}")

    lote_com_erro = [
        {"pedido_id": "PED-2001", "cliente_nome": "Cliente Bom 1", "produto": "Item A", "quantidade": 5, "valor_unitario": 20.0},
        {"pedido_id": "PED-2002", "cliente_nome": "Cliente Bom 2", "produto": "Item B", "quantidade": 8, "valor_unitario": 15.0},
        # Este registro causará falha por colidir com PED-1001 já existente:
        {"pedido_id": "PED-1001", "cliente_nome": "Cliente Conflito", "produto": "Item C", "quantidade": 2, "valor_unitario": 50.0},
    ]

    rollback_confirmado = False
    try:
        database.inserir_lote_pedidos_transacional(lote_com_erro, db_path=TEST_DB)
    except sqlite3.IntegrityError as e:
        rollback_confirmado = True
        print(f" Exceção esperada disparada no 3º item: {e}")

    assert rollback_confirmado, "Falha: O lote não disparou exceção."

    total_depois = database.total_pedidos_cadastrados(db_path=TEST_DB)
    print(f" Total de pedidos após falha do lote: {total_depois}")
    assert total_depois == total_antes, (
        f"Falha de Rollback: Registros parciais foram commitados! Antes: {total_antes}, Depois: {total_depois}"
    )

    # Verificar que PED-2001 não ficou órfão no banco
    assert database.buscar_pedido_por_id("PED-2001", db_path=TEST_DB) is None, "Falha: PED-2001 foi persistido apesar do rollback!"
    print(" -> PASSOU: Rollback confirmado com sucesso. Zero registros parciais gravados.")

    # -------------------------------------------------------------
    # Inicialização oficial do banco de produção (nexus_erp.db)
    # -------------------------------------------------------------
    print("\n[FINALIZAÇÃO] Inicializando banco oficial de produção (nexus_erp.db)...")
    database.init_db(database.DB_PATH)
    assert os.path.exists(database.DB_PATH), "Falha: nexus_erp.db não foi criado."
    print(f" -> PASSOU: Banco oficial pronto em: {database.DB_PATH}")

    # Limpeza do arquivo temporário de teste
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    print("\n" + "=" * 65)
    print(" TODOS OS 6 TESTES DA MICRO-ETAPA 2.1 PASSARAM COM SUCESSO!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
