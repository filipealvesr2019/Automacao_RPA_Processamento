"""
Motor de Processamento RPA - Validação de Regras de Negócio,
Persistência no SQLite e Geração do Relatório Final de Auditoria.
"""

import os
import sys
import sqlite3
import datetime
import random
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
INPUT_FILE = os.path.join(DATA_DIR, "Input", "Pedidos_Input.xlsx")
OUTPUT_FILE = os.path.join(DATA_DIR, "Output", "Relatorio_Processamento.xlsx")
DB_PATH = os.path.join(DATA_DIR, "nexus_erp.db")


def gerar_protocolo():
    ano = datetime.datetime.now().year
    sufixo = random.randint(100000, 999999)
    return f"PRT-{ano}-{sufixo}"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def processar():
    print("=" * 60)
    print("   MOTOR RPA - PROCESSAMENTO DE PEDIDOS E AUDITORIA")
    print("=" * 60)

    if not os.path.exists(INPUT_FILE):
        print(f"[ERRO] Arquivo de entrada não encontrado: {INPUT_FILE}")
        sys.exit(1)

    print(f"[1/4] Lendo planilha de entrada: {INPUT_FILE}")
    wb_in = openpyxl.load_workbook(INPUT_FILE, data_only=True)
    ws_in = wb_in.active

    # Carregar dados em memória
    linhas = list(ws_in.iter_rows(values_only=True))
    if len(linhas) <= 1:
        print("[AVISO] Planilha vazia ou sem linhas de dados.")
        sys.exit(0)

    cabecalho = linhas[0]
    dados = linhas[1:]
    print(f"      Total de registros identificados: {len(dados)}")

    # Conectar ao banco SQLite
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id TEXT UNIQUE NOT NULL,
            cliente TEXT NOT NULL,
            produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            total REAL NOT NULL,
            protocolo TEXT UNIQUE NOT NULL,
            data_hora TEXT NOT NULL
        )
    """)
    conn.commit()

    # IDs já cadastrados no banco para evitar duplicidade externa
    cursor.execute("SELECT pedido_id FROM pedidos")
    ids_banco = set(row["pedido_id"] for row in cursor.fetchall())

    # Estruturas para segregação e relatório
    todos_processados = []
    lista_sucessos = []
    lista_rejeitados = []
    lista_ignorados = []

    ids_lote = set()
    timestamp_processamento = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("[2/4] Aplicando regras de negócio e validações...")

    for idx, row in enumerate(dados, start=2):
        pedido_id_raw = row[0]
        cliente_raw = row[1]
        produto_raw = row[2]
        qtd_raw = row[3]
        valor_raw = row[4]
        status_origem_raw = row[5]

        pedido_id = str(pedido_id_raw).strip().upper() if pedido_id_raw else ""
        cliente = str(cliente_raw).strip() if cliente_raw else ""
        produto = str(produto_raw).strip() if produto_raw else ""
        status_origem = str(status_origem_raw).strip().capitalize() if status_origem_raw else "Aberto"

        try:
            quantidade = int(qtd_raw) if qtd_raw is not None else 0
        except (ValueError, TypeError):
            quantidade = 0

        try:
            valor_unitario = float(valor_raw) if valor_raw is not None else 0.0
        except (ValueError, TypeError):
            valor_unitario = 0.0

        total = round(quantidade * valor_unitario, 2)

        registro_base = {
            "linha_excel": idx,
            "pedido_id": pedido_id,
            "cliente": cliente,
            "produto": produto,
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "total": total,
            "status_origem": status_origem,
            "data_proc": timestamp_processamento
        }

        # REGRA 1: Status Origem = Cancelado (Ignorado)
        if status_origem == "Cancelado":
            registro_base["status_final"] = "Ignorado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "Pedido cancelado na origem"
            lista_ignorados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] IGNORADO: {pedido_id or 'Sem ID'} - Pedido cancelado na origem.")
            continue

        # REGRA 2: ID ausente ou duplicado no lote ou no banco
        if not pedido_id:
            registro_base["status_final"] = "Rejeitado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "ID do pedido ausente"
            lista_rejeitados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] REJEITADO: ID ausente.")
            continue

        if pedido_id in ids_lote:
            registro_base["status_final"] = "Rejeitado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "ID do pedido duplicado no lote"
            lista_rejeitados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] REJEITADO: {pedido_id} - Duplicado no lote.")
            continue

        if pedido_id in ids_banco:
            registro_base["status_final"] = "Rejeitado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "ID do pedido já faturado no sistema anteriormente"
            lista_rejeitados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] REJEITADO: {pedido_id} - Já existe no banco SQLite.")
            continue

        # REGRA 3: Nome do cliente inválido (< 3 caracteres)
        if len(cliente) < 3:
            registro_base["status_final"] = "Rejeitado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "Nome do cliente inválido (mínimo 3 caracteres)"
            lista_rejeitados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] REJEITADO: {pedido_id} - Cliente inválido ('{cliente}').")
            continue

        # REGRA 4: Produto não informado
        if not produto:
            registro_base["status_final"] = "Rejeitado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "Produto não informado"
            lista_rejeitados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] REJEITADO: {pedido_id} - Produto vazio.")
            continue

        # REGRA 5: Quantidade <= 0
        if quantidade <= 0:
            registro_base["status_final"] = "Rejeitado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "Quantidade menor ou igual a zero"
            lista_rejeitados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] REJEITADO: {pedido_id} - Quantidade inválida ({quantidade}).")
            continue

        # REGRA 6: Valor Unitário <= 0
        if valor_unitario <= 0.0:
            registro_base["status_final"] = "Rejeitado"
            registro_base["protocolo"] = "-"
            registro_base["motivo"] = "Valor unitário menor ou igual a zero"
            lista_rejeitados.append(registro_base)
            todos_processados.append(registro_base)
            print(f"   [Linha {idx}] REJEITADO: {pedido_id} - Valor unitário inválido (R$ {valor_unitario}).")
            continue

        # CASO DE SUCESSO: Cadastro e Persistência no SQLite
        ids_lote.add(pedido_id)
        ids_banco.add(pedido_id)
        protocolo = gerar_protocolo()

        cursor.execute("""
            INSERT INTO pedidos (pedido_id, cliente, produto, quantidade, valor_unitario, total, protocolo, data_hora)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pedido_id, cliente, produto, quantidade, valor_unitario, total, protocolo, timestamp_processamento))
        conn.commit()

        registro_base["status_final"] = "Sucesso"
        registro_base["protocolo"] = protocolo
        registro_base["motivo"] = "Cadastrado e faturado com sucesso no Nexus ERP"
        lista_sucessos.append(registro_base)
        todos_processados.append(registro_base)
        print(f"   [Linha {idx}] SUCESSO: {pedido_id} faturado com protocolo {protocolo}.")

    conn.close()

    print("[3/4] Gerando Relatório Consolidado de Auditoria...")
    wb_out = openpyxl.Workbook()

    # Estilos de formatação
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    def formatar_aba(ws, registros, cor_header):
        fill_header = PatternFill(start_color=cor_header, end_color=cor_header, fill_type="solid")
        headers = [
            "ID Pedido", "Cliente", "Produto", "Qtd", "Valor Unitário",
            "Total", "Status Origem", "Status Final", "Protocolo ERP", "Motivo / Detalhe", "Data/Hora"
        ]
        ws.append(headers)

        for cell in ws[1]:
            cell.fill = fill_header
            cell.font = font_header
            cell.alignment = align_center

        for reg in registros:
            ws.append([
                reg["pedido_id"] or "-",
                reg["cliente"] or "-",
                reg["produto"] or "-",
                reg["quantidade"],
                reg["valor_unitario"],
                reg["total"],
                reg["status_origem"],
                reg["status_final"],
                reg["protocolo"],
                reg["motivo"],
                reg["data_proc"]
            ])

        # Formatação de larguras e células
        larguras = [14, 28, 30, 8, 16, 16, 15, 14, 20, 36, 18]
        for col_idx, width in enumerate(larguras, start=1):
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

        for row in ws.iter_rows(min_row=2, max_row=len(registros)+1, min_col=1, max_col=11):
            status = row[7].value # Status Final
            for cell in row:
                cell.border = thin_border
                if cell.column in (1, 7, 8, 9, 11):
                    cell.alignment = align_center
                elif cell.column in (2, 3, 10):
                    cell.alignment = align_left
                elif cell.column == 4:
                    cell.alignment = align_right
                elif cell.column in (5, 6):
                    cell.number_format = 'R$ #,##0.00'
                    cell.alignment = align_right

            # Cores de destaque no Status Final
            cell_status = row[7]
            if status == "Sucesso":
                cell_status.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
                cell_status.font = Font(name="Calibri", size=10, bold=True, color="065F46")
            elif status == "Rejeitado":
                cell_status.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                cell_status.font = Font(name="Calibri", size=10, bold=True, color="991B1B")
            elif status == "Ignorado":
                cell_status.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                cell_status.font = Font(name="Calibri", size=10, bold=True, color="92400E")

    # Aba 1: Consolidado Geral
    ws_cons = wb_out.active
    ws_cons.title = "Consolidado Geral"
    formatar_aba(ws_cons, todos_processados, "1E3A8A") # Azul Corporativo

    # Aba 2: Sucessos
    ws_suc = wb_out.create_sheet(title="Sucessos")
    formatar_aba(ws_suc, lista_sucessos, "059669") # Verde

    # Aba 3: Rejeitados (Erros de Negócio)
    ws_rej = wb_out.create_sheet(title="Rejeitados_Erros")
    formatar_aba(ws_rej, lista_rejeitados, "DC2626") # Vermelho

    # Aba 4: Ignorados (Cancelados)
    ws_ign = wb_out.create_sheet(title="Ignorados_Cancelados")
    formatar_aba(ws_ign, lista_ignorados, "D97706") # Âmbar

    wb_out.save(OUTPUT_FILE)
    print(f"[4/4] Relatório salvo com sucesso: {OUTPUT_FILE}")
    print("=" * 60)
    print(f"   RESUMO FINAL DO PROCESSAMENTO:")
    print(f"   • Total Processado : {len(todos_processados)}")
    print(f"   • Sucesso          : {len(lista_sucessos)}")
    print(f"   • Rejeitados       : {len(lista_rejeitados)}")
    print(f"   • Ignorados        : {len(lista_ignorados)}")
    print("=" * 60)


if __name__ == "__main__":
    processar()

