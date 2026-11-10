"""
Gerador da Planilha Oficial de Entrada: Data/Input/Pedidos_Input.xlsx
Contém casos de sucesso, erros de negócio e casos de cancelamento (borda).
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "Data", "Input")
os.makedirs(INPUT_DIR, exist_ok=True)
FILE_PATH = os.path.join(INPUT_DIR, "Pedidos_Input.xlsx")

def criar_planilha_entrada():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pedidos_Diarios"

    # Cabeçalhos
    headers = [
        "ID_Pedido",
        "Nome_Cliente",
        "Produto",
        "Quantidade",
        "Valor_Unitario",
        "Status_Origem"
    ]
    ws.append(headers)

    # Dados de Teste (Casos Válidos e Casos de Exceção)
    dados = [
        ("PED-2001", "Metalúrgica Silva Ltda", "Cabo de Aço Galvanizado 10mm", 10, 150.50, "Aprovado"),
        ("PED-2002", "Construtora Horizonte SA", "Viga Metálica W200", 4, 1250.00, "Aberto"),
        ("PED-2003", "Auto Peças Brasil", "Filtro de Ar Industrial", 0, 85.00, "Aberto"),           # Qtd <= 0
        ("PED-2004", "Al", "Parafuso Sextavado M12", 50, 4.50, "Aberto"),                          # Cliente < 3 chars
        ("PED-2005", "Logística Express", "Palete de Madeira PBR", 15, 0.00, "Aprovado"),           # Valor <= 0
        ("PED-2006", "Indústria Mecânica Omega", "Chapa de Aço Inox 2mm", 8, 420.00, "Cancelado"),  # Ignorado (Cancelado)
        ("PED-2001", "Metalúrgica Silva Ltda", "Cabo de Aço Galvanizado 10mm", 5, 150.50, "Aprovado"), # ID Duplicado
        ("", "Distribuidora Norte", "Tubo PVC 100mm", 20, 32.00, "Aberto"),                         # ID Ausente
        ("PED-2007", "Tecnologia e Redes SA", "Cabo de Rede Cat6 305m", 3, 680.00, "Aprovado"),   # Sucesso
        ("PED-2008", "Comércio de Tintas Delta", "", 12, 110.00, "Aberto"),                         # Produto vazio
        ("PED-2009", "Eletrotécnica Volt Ltda", "Transformador Trifásico 15kVA", 2, 4500.00, "Aprovado"), # Sucesso
    ]

    for row in dados:
        ws.append(row)

    # Estilização Profissional
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    # Ajuste de largura das colunas e formatações
    larguras = {
        "A": 16, # ID_Pedido
        "B": 32, # Nome_Cliente
        "C": 36, # Produto
        "D": 15, # Quantidade
        "E": 18, # Valor_Unitario
        "F": 16  # Status_Origem
    }
    for col, width in larguras.items():
        ws.column_dimensions[col].width = width

    # Formatar números e bordas
    for row in ws.iter_rows(min_row=2, max_row=len(dados)+1, min_col=1, max_col=6):
        for cell in row:
            cell.border = thin_border
            if cell.column == 4: # Quantidade
                cell.alignment = Alignment(horizontal="right")
            elif cell.column == 5: # Valor_Unitario
                cell.number_format = 'R$ #,##0.00'
                cell.alignment = Alignment(horizontal="right")
            elif cell.column in (1, 6): # ID ou Status
                cell.alignment = Alignment(horizontal="center")

    wb.save(FILE_PATH)
    print(f"[OK] Planilha de entrada criada com sucesso: {FILE_PATH} ({len(dados)} pedidos)")

if __name__ == "__main__":
    criar_planilha_entrada()

