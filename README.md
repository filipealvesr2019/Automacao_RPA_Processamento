# 🤖 Automação RPA: Processamento de Pedidos e Cadastro Corporativo (Nexus ERP)

> **Solução corporativa completa de automação robótica de processos (RPA)** integrada a um portal web corporativo (*Nexus ERP*), com backend REST em Python, persistência transacional em SQLite e geração automatizada de relatórios gerenciais em Excel.

---

## 🏛️ 1. Arquitetura da Solução & Separação de Responsabilidades

O projeto implementa uma arquitetura em camadas orientada a eventos sob demanda (*Attended On-Demand Trigger* com execução 100% autônoma):

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PORTAL WEB (NEXUS ERP)                                    │
│  [ Upload do Excel ] ──> [ Botão: Processar Pedidos ] ──> [ Status ] ──> [ Baixar Relatório ]│
└────────────┬─────────────────────────────┬─────────────────────────────────────▲───────┘
             │ Envia .xlsx                 │ Dispara Execução                     │ Download
             ▼                             ▼                                     │
┌─────────────────────────┐   ┌─────────────────────────┐               ┌────────┴───────┐
│       API PYTHON        │   │       ROBÔ UIPATH       │               │ RELATÓRIO EXCEL│
│ • Salva em Data/Input/  │   │ • Lê e audita linhas    │               │ (Data/Output/) │
│ • Controla Concorrência │   │ • Preenche o formulário │ ────────────> │                │
│ • Gerencia Estados      │   │ • Captura protocolos    │               └────────────────┘
└────────────┬────────────┘   └────────────┬────────────┘
             │                             │
             │ INSERT / Validação          │ POST /api/pedidos
             ▼                             ▼
┌───────────────────────────────────────────────────────┐
│               BANCO DE DADOS SQLITE                   │
│                    (nexus_erp.db)                     │
└───────────────────────────────────────────────────────┘
```

### Matriz de Responsabilidades

| Componente | Tecnologia | Responsabilidade Principal |
| :--- | :--- | :--- |
| **Interface ERP** | `HTML5 / CSS3 / JavaScript` | Portal corporativo responsivo, área de upload, máquina de estados visual, botão de disparo sob demanda e grid de consulta. |
| **API Local** | `Python (ThreadingHTTPServer)` | Endpoints REST (`/api/pedidos`, `/api/upload`, `/api/processar`, `/api/status`, `/api/reset`, `/api/relatorio`), controle de concorrência e geração oficial de protocolos. |
| **Banco de Dados** | `SQLite (nexus_erp.db)` | Persistência relacional definitiva dos pedidos faturados. |
| **Robô RPA** | `UiPath Studio (.NET/XAML)` | Leitura de planilha, auditoria estrita de regras de negócio em memória, automação da interface gráfica e emissão do relatório final. |
| **Excel Entrada** | `Data/Input/Pedidos_Input.xlsx` | Lote diário com registros válidos e casos de teste (erros de borda). |
| **Excel Saída** | `Data/Output/Relatorio_Processamento.xlsx`| Relatório consolidado multi-abas (Consolidado, Sucessos, Rejeitados, Ignorados). |

---

## 📋 2. Regras de Negócio e Validações

O robô e a API aplicam **dupla validação (Defesa em Profundidade)**:

| Campo | Validação | Ação em caso de Inconsistência |
| :--- | :--- | :--- |
| `ID_Pedido` | Obrigatório e único no lote e no banco | **Rejeitado:** *"ID ausente ou duplicado"* |
| `Nome_Cliente` | Obrigatório (mínimo de 3 caracteres) | **Rejeitado:** *"Nome do cliente inválido"* |
| `Produto` | Obrigatório e preenchido | **Rejeitado:** *"Produto não informado"* |
| `Quantidade` | Numérico e estritamente $> 0$ | **Rejeitado:** *"Quantidade menor ou igual a zero"* |
| `Valor_Unitario`| Numérico e estritamente $> 0.00$ | **Rejeitado:** *"Valor unitário menor ou igual a zero"* |
| `Status_Origem` | Se for `Cancelado` | **Ignorado:** *"Pedido cancelado na origem"* (não vai ao ERP) |

---

## 🚀 3. Como Executar o Projeto

### Pré-requisitos
- **Python 3.10+** instalado no PATH
- **Navegador Web** (Google Chrome, Edge ou Firefox)
- **UiPath Studio** (para edição/execução dos workflows `.xaml`)

### Passo 1: Iniciar o Portal Web e API Backend
Dê um duplo clique no arquivo:
```cmd
iniciar_portal.bat
```
Ou execute via terminal:
```bash
python server.py
```
O servidor inicializará na porta **`8080`** e abrirá automaticamente o navegador em:  
👉 **`http://localhost:8080`**

### Passo 2: Executar o Processamento
Existem duas maneiras:
1. **Via Portal Web (Recomendado):**
   - Acesse o portal web;
   - Clique em **"Enviar Planilha"** (já vem carregado com o arquivo oficial);
   - Clique em **"⚙️ Processar Pedidos"**;
   - Acompanhe a tabela do SQLite atualizando em tempo real com os protocolos gerados;
   - Ao concluir, clique em **"📊 Baixar Relatório Final (.xlsx)"**.
2. **Via Linha de Comando / UiPath:**
   - Execute o motor de processamento direto no terminal:
   ```bash
   python processar_pedidos.py
   ```
   - Ou abra o projeto no **UiPath Studio** abrindo o arquivo `project.json` e executando `Main.xaml`.

---

## 📊 4. Evidências de Execução e Relatório Gerado

O relatório final em `Data/Output/Relatorio_Processamento.xlsx` contém 4 abas estruturadas e coloridas:
1. **Consolidado Geral:** Visão 360° de todos os pedidos auditados com timestamp e detalhes.
2. **Sucessos:** Somente os pedidos faturados com seu respectivo protocolo oficial `PRT-2026-XXXXXX`.
3. **Rejeitados_Erros:** Pedidos descartados por falha nas regras de negócio (duplicidade, valores negativos, etc.).
4. **Ignorados_Cancelados:** Pedidos previamente cancelados na origem.

---

## 📁 5. Estrutura de Pastas do Repositório

```text
Automacao_RPA_Processamento/
│
├── Data/
│   ├── Input/
│   │   └── Pedidos_Input.xlsx          # Planilha de entrada com massa de testes
│   ├── Output/
│   │   └── Relatorio_Processamento.xlsx # Relatório de auditoria gerado
│   ├── Temp/                           # Screenshots e evidências temporárias
│   └── nexus_erp.db                    # Banco de dados relacional SQLite
│
├── PortalWeb/
│   ├── index.html                      # Interface visual do ERP (com painel RPA)
│   ├── styles.css                      # Folhas de estilo corporativas
│   └── app.js                          # Integração frontend com API REST
│
├── Workflows/
│   └── ProcessarFilaPedidos.xaml       # Subfluxo de leitura e processamento
│
├── DOCUMENTO_DE_REQUISITOS.md           # Especificação funcional e técnica
├── README.md                           # Documentação executiva do repositório
├── iniciar_portal.bat                  # Script de inicialização em 1 clique
├── server.py                           # Backend REST HTTP + SQLite em Python
├── processar_pedidos.py                # Motor de regras de negócio e relatórios
├── criar_planilha_input.py             # Gerador da planilha de teste oficial
├── project.json                        # Definição do projeto UiPath Studio
└── Main.xaml                           # Workflow principal do UiPath Studio
```

