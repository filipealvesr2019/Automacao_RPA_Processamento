"""
Servidor Backend Nexus ERP & Orquestrador Local (RPA Target)
Tecnologia: Python HTTP Server + SQLite3
Porta: 8080
"""

import os
import sys
import json
import time
import sqlite3
import random
import datetime
import mimetypes
import threading
import subprocess
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Diretórios do Projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTAL_DIR = os.path.join(BASE_DIR, "PortalWeb")
DATA_DIR = os.path.join(BASE_DIR, "Data")
INPUT_DIR = os.path.join(DATA_DIR, "Input")
OUTPUT_DIR = os.path.join(DATA_DIR, "Output")
TEMP_DIR = os.path.join(DATA_DIR, "Temp")
DB_PATH = os.path.join(DATA_DIR, "nexus_erp.db")

# Garantir existência dos diretórios
for directory in [INPUT_DIR, OUTPUT_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Lock de concorrência para processamento
process_lock = threading.Lock()

# Estados possíveis:
# AGUARDANDO_PLANILHA, PRONTO_PARA_PROCESSAR, PROCESSANDO, CONCLUIDO, FALHOU
estado_automacao = {
    "estado": "AGUARDANDO_PLANILHA",
    "mensagem": "Aguardando envio da planilha Pedidos_Input.xlsx",
    "arquivo_atual": None,
    "total_pedidos": 0,
    "pedidos_processados": 0,
    "data_inicio": None,
    "data_fim": None,
    "relatorio_disponivel": False
}


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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
    conn.close()
    print(f"[DB] Banco de dados SQLite inicializado em: {DB_PATH}")


def gerar_protocolo():
    """Gera protocolo oficial único no formato PRT-YYYY-XXXXXX"""
    ano = datetime.datetime.now().year
    sufixo = random.randint(100000, 999999)
    return f"PRT-{ano}-{sufixo}"


class NexusERPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PORTAL_DIR, **kwargs)

    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_HEAD(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path.startswith("/api/"):
            self._set_headers(200)
        else:
            super().do_HEAD()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/status":
            self._handle_get_status()
        elif path == "/api/pedidos":
            self._handle_get_pedidos()
        elif path == "/api/relatorio/download":
            self._handle_download_relatorio()
        else:
            # Serve arquivos estáticos do frontend (PortalWeb)
            super().do_GET()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/pedidos":
            self._handle_post_pedido()
        elif path == "/api/upload":
            self._handle_upload_excel()
        elif path == "/api/processar":
            self._handle_iniciar_processamento()
        elif path == "/api/reset":
            self._handle_reset_banco()
        elif path == "/api/status/atualizar":
            self._handle_atualizar_status_interno()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"erro": "Endpoint não encontrado"}).encode("utf-8"))

    # ==========================
    # HANDLERS GET
    # ==========================
    def _handle_get_status(self):
        relatorio_path = os.path.join(OUTPUT_DIR, "Relatorio_Processamento.xlsx")
        estado_automacao["relatorio_disponivel"] = os.path.exists(relatorio_path)

        # Se a planilha já existe na pasta de entrada, avança automaticamente o estado para pronto
        caminho_input = os.path.join(INPUT_DIR, "Pedidos_Input.xlsx")
        if os.path.exists(caminho_input) and estado_automacao["estado"] == "AGUARDANDO_PLANILHA":
            estado_automacao["estado"] = "PRONTO_PARA_PROCESSAR"
            estado_automacao["arquivo_atual"] = "Pedidos_Input.xlsx"
            estado_automacao["mensagem"] = "Planilha padrão detectada em Data/Input/Pedidos_Input.xlsx. Pronto para processar."

        self._set_headers(200)
        self.wfile.write(json.dumps(estado_automacao, ensure_ascii=False).encode("utf-8"))

    def _handle_get_pedidos(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
            rows = cursor.fetchall()
            pedidos = [dict(row) for row in rows]
            conn.close()

            self._set_headers(200)
            self.wfile.write(json.dumps(pedidos, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"erro": f"Erro ao consultar pedidos: {str(e)}"}).encode("utf-8"))

    def _handle_download_relatorio(self):
        relatorio_path = os.path.join(OUTPUT_DIR, "Relatorio_Processamento.xlsx")
        if not os.path.exists(relatorio_path):
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"erro": "Relatório ainda não gerado ou indisponível."}).encode("utf-8"))
            return

        with open(relatorio_path, "rb") as f:
            conteudo = f.read()

        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition", 'attachment; filename="Relatorio_Processamento.xlsx"')
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    # ==========================
    # HANDLERS POST
    # ==========================
    def _handle_post_pedido(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            dados = json.loads(body_bytes.decode("utf-8"))

            pedido_id = str(dados.get("pedido_id", "")).strip()
            cliente = str(dados.get("cliente", "")).strip()
            produto = str(dados.get("produto", "")).strip()
            quantidade_raw = dados.get("quantidade")
            valor_raw = dados.get("valor_unitario")

            # Validações estritas de integridade (Defesa em Profundidade no Backend)
            erros = []
            if not pedido_id:
                erros.append("ID do Pedido é obrigatório.")
            if not cliente or len(cliente) < 3:
                erros.append("Nome do Cliente deve conter no mínimo 3 caracteres.")
            if not produto:
                erros.append("Produto é obrigatório.")

            try:
                quantidade = int(quantidade_raw)
                if quantidade <= 0:
                    erros.append("Quantidade deve ser maior que zero.")
            except (ValueError, TypeError):
                erros.append("Quantidade inválida.")

            try:
                valor_unitario = float(valor_raw)
                if valor_unitario <= 0:
                    erros.append("Valor unitário deve ser maior que zero.")
            except (ValueError, TypeError):
                erros.append("Valor unitário inválido.")

            if erros:
                self._set_headers(400)
                self.wfile.write(json.dumps({"erro": "; ".join(erros)}).encode("utf-8"))
                return

            total = round(quantidade * valor_unitario, 2)

            conn = get_db_connection()
            cursor = conn.cursor()

            # Verificar duplicidade de ID no SQLite
            cursor.execute("SELECT id FROM pedidos WHERE pedido_id = ?", (pedido_id,))
            if cursor.fetchone():
                conn.close()
                self._set_headers(409)
                self.wfile.write(json.dumps({"erro": f"ID de Pedido '{pedido_id}' já cadastrado no sistema."}).encode("utf-8"))
                return

            # Gerar protocolo único pelo backend
            protocolo = gerar_protocolo()
            data_hora = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

            cursor.execute("""
                INSERT INTO pedidos (pedido_id, cliente, produto, quantidade, valor_unitario, total, protocolo, data_hora)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pedido_id, cliente, produto, quantidade, valor_unitario, total, protocolo, data_hora))
            conn.commit()
            conn.close()

            self._set_headers(201)
            response_data = {
                "status": "sucesso",
                "protocolo": protocolo,
                "pedido_id": pedido_id,
                "cliente": cliente,
                "total": total,
                "data_hora": data_hora,
                "mensagem": "Pedido cadastrado e faturado com sucesso."
            }
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))

        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"erro": "JSON malformado"}).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"erro": f"Erro interno do servidor: {str(e)}"}).encode("utf-8"))

    def _handle_upload_excel(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            content_type = self.headers.get("Content-Type", "")

            # Processamento de multipart ou raw stream
            if "multipart/form-data" in content_type:
                boundary = content_type.split("boundary=")[1].encode("utf-8")
                raw_data = self.rfile.read(content_length)

                # Extrair o binário do arquivo dentro do payload multipart
                parts = raw_data.split(b"--" + boundary)
                file_bytes = None
                for part in parts:
                    if b'filename="' in part:
                        header_end = part.find(b"\r\n\r\n")
                        if header_end != -1:
                            file_bytes = part[header_end + 4 :].rstrip(b"\r\n")
                            break
            else:
                file_bytes = self.rfile.read(content_length)

            if not file_bytes:
                self._set_headers(400)
                self.wfile.write(json.dumps({"erro": "Nenhum arquivo enviado."}).encode("utf-8"))
                return

            caminho_destino = os.path.join(INPUT_DIR, "Pedidos_Input.xlsx")
            with open(caminho_destino, "wb") as f:
                f.write(file_bytes)

            # Contar linhas se openpyxl disponível
            total_linhas = 0
            try:
                import openpyxl
                wb = openpyxl.load_workbook(caminho_destino, data_only=True)
                ws = wb.active
                total_linhas = max(0, ws.max_row - 1)
            except Exception:
                total_linhas = "Indeterminado"

            # Atualizar estado
            estado_automacao["estado"] = "PRONTO_PARA_PROCESSAR"
            estado_automacao["mensagem"] = f"Planilha recebida com sucesso ({total_linhas} registros prontos)."
            estado_automacao["arquivo_atual"] = "Pedidos_Input.xlsx"
            estado_automacao["total_pedidos"] = total_linhas if isinstance(total_linhas, int) else 0

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "sucesso",
                "mensagem": "Arquivo salvo com sucesso em Data/Input/Pedidos_Input.xlsx",
                "total_registros": total_linhas
            }, ensure_ascii=False).encode("utf-8"))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"erro": f"Falha no upload do arquivo: {str(e)}"}).encode("utf-8"))

    def _handle_iniciar_processamento(self):
        # Controle de Concorrência Estrito
        if not process_lock.acquire(blocking=False):
            self._set_headers(409)
            self.wfile.write(json.dumps({"erro": "Um processamento já está em andamento. Aguarde a finalização."}).encode("utf-8"))
            return

        caminho_input = os.path.join(INPUT_DIR, "Pedidos_Input.xlsx")
        if not os.path.exists(caminho_input):
            process_lock.release()
            self._set_headers(400)
            self.wfile.write(json.dumps({"erro": "Nenhuma planilha encontrada em Data/Input/Pedidos_Input.xlsx."}).encode("utf-8"))
            return

        estado_automacao["estado"] = "PROCESSANDO"
        estado_automacao["mensagem"] = "Processando pedidos da planilha..."
        estado_automacao["data_inicio"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

        # Disparar thread de execução autônoma
        thread = threading.Thread(target=self._executar_robo_background)
        thread.daemon = True
        thread.start()

        self._set_headers(202)
        self.wfile.write(json.dumps({
            "status": "iniciado",
            "mensagem": "Orquestração iniciada. Robô executando sob demanda."
        }, ensure_ascii=False).encode("utf-8"))

    def _executar_robo_background(self):
        try:
            print("[ROBÔ] Disparo de execução autônoma iniciado...")
            time.sleep(1.5)
            # Chama o motor oficial de processamento de pedidos
            processador_script = os.path.join(BASE_DIR, "processar_pedidos.py")
            if os.path.exists(processador_script):
                subprocess.run([sys.executable, processador_script], check=True)

            time.sleep(1.0)
            estado_automacao["estado"] = "CONCLUIDO"
            estado_automacao["mensagem"] = "Processamento concluído com sucesso! Relatório disponível para download."
            estado_automacao["data_fim"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            estado_automacao["relatorio_disponivel"] = True
            print("[ROBÔ] Execução finalizada com sucesso.")
        except Exception as e:
            estado_automacao["estado"] = "FALHOU"
            estado_automacao["mensagem"] = f"Falha na execução: {str(e)}"
            print(f"[ROBÔ] Erro durante o processamento: {e}")
        finally:
            process_lock.release()

    def _handle_reset_banco(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pedidos")
            conn.commit()
            conn.close()

            estado_automacao["estado"] = "AGUARDANDO_PLANILHA"
            estado_automacao["mensagem"] = "Banco e estados resetados com sucesso."
            estado_automacao["arquivo_atual"] = None
            estado_automacao["total_pedidos"] = 0
            estado_automacao["pedidos_processados"] = 0
            estado_automacao["relatorio_disponivel"] = False

            # Limpar relatório de saída se existir
            relatorio_path = os.path.join(OUTPUT_DIR, "Relatorio_Processamento.xlsx")
            if os.path.exists(relatorio_path):
                os.remove(relatorio_path)

            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "sucesso", "mensagem": "Base de dados e histórico resetados."}).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"erro": f"Erro ao resetar banco: {str(e)}"}).encode("utf-8"))

    def _handle_atualizar_status_interno(self):
        # Permite ao UiPath ou worker atualizar o progresso
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            dados = json.loads(body_bytes.decode("utf-8"))
            for k, v in dados.items():
                if k in estado_automacao:
                    estado_automacao[k] = v
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"erro": str(e)}).encode("utf-8"))


def main():
    init_db()
    porta = 8080
    servidor = ThreadingHTTPServer(("0.0.0.0", porta), NexusERPRequestHandler)
    print(f"======================================================")
    print(f"   NEXUS ERP CORPORATIVO & API BACKEND (SQLITE)")
    print(f"   Servidor HTTP e API rodando na porta {porta}")
    print(f"   Acesse: http://localhost:{porta}")
    print(f"======================================================")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
        servidor.server_close()


if __name__ == "__main__":
    main()
