"""
Consolidador Oficial do Relatório RPA - Nexus ERP
Lê os resultados REAIS capturados e auditados pelo Robô UiPath
(Data/Temp/resultados_execucao_uipath.json) e gera a planilha final
formatada em Data/Output/Relatorio_Processamento.xlsx com 4 abas.
"""

import os
import sys
import json
import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_FILE = os.path.join(BASE_DIR, "Data", "Temp", "resultados_execucao_uipath.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "Data", "Output", "Relatorio_Processamento.xlsx")

def consolidar_relatorio():
    print("=" * 60)
    print("   CONSOLIDAÇÃO DO RELATÓRIO OFICIAL DA EXECUÇÃO UIPATH")
    print("=" * 60)

    if not os.path.exists(TEMP_FILE):
        print(f"[ERRO] Arquivo de resultados da execução UiPath não encontrado: {TEMP_FILE}")
        sys.exit(1)

    with open(TEMP_FILE, "r", encoding="utf-8") as f:
        registros = json.load(f)

    print(f"[1/2] Total de registros recebidos do Robô UiPath: {len(registros)}")

    todos_processados = []
    lista_sucessos = []
    lista_rejeitados = []
    lista_ignorados = []

    for reg in registros:
        todos_processados.append(reg)
        status = reg.get("status_final", "")
        if status == "Sucesso":
            lista_sucessos.append(reg)
        elif status == "Rejeitado":
            lista_rejeitados.append(reg)
        elif status == "Ignorado":
            lista_ignorados.append(reg)

    wb_out = openpyxl.Workbook()

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    def formatar_aba(ws, lista_dados, cor_header):
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

        for r in lista_dados:
            ws.append([
                r.get("pedido_id") or "-",
                r.get("cliente") or "-",
                r.get("produto") or "-",
                r.get("quantidade", 0),
                r.get("valor_unitario", 0.0),
                r.get("total", 0.0),
                r.get("status_origem") or "-",
                r.get("status_final") or "-",
                r.get("protocolo") or "-",
                r.get("motivo") or "-",
                r.get("data_proc") or "-"
            ])

        larguras = [14, 28, 30, 8, 16, 16, 15, 14, 20, 36, 18]
        for col_idx, width in enumerate(larguras, start=1):
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

        for row in ws.iter_rows(min_row=2, max_row=len(lista_dados) + 1, min_col=1, max_col=11):
            status = row[7].value
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
    formatar_aba(ws_cons, todos_processados, "1E3A8A")

    # Aba 2: Sucessos
    ws_suc = wb_out.create_sheet(title="Sucessos")
    formatar_aba(ws_suc, lista_sucessos, "059669")

    # Aba 3: Rejeitados
    ws_rej = wb_out.create_sheet(title="Rejeitados_Erros")
    formatar_aba(ws_rej, lista_rejeitados, "DC2626")

    # Aba 4: Ignorados
    ws_ign = wb_out.create_sheet(title="Ignorados_Cancelados")
    formatar_aba(ws_ign, lista_ignorados, "D97706")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    wb_out.save(OUTPUT_FILE)
    print(f"[2/2] Relatório gerado com sucesso em: {OUTPUT_FILE}")
    print(f"      • Sucessos: {len(lista_sucessos)} (com protocolos reais)")
    print(f"      • Rejeitados: {len(lista_rejeitados)}")
    print(f"      • Ignorados: {len(lista_ignorados)}")
    print("=" * 60)

if __name__ == "__main__":
    consolidar_relatorio()

