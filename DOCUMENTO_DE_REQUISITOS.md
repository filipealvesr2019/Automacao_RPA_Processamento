# Documento de Requisitos e Especificação do Projeto RPA

**Projeto:** Automação de Processamento de Pedidos e Cadastro Corporativo (ERP)  
**Ferramenta Principal:** UiPath Studio & UiPath Orchestrator Cloud  
**Assistente de Desenvolvimento:** Antigravity  
**Metodologia:** Desenvolvimento Guiado por Evidências (Gate-Check em 7 Etapas)  
**Modalidade:** Automação sob demanda via Portal Web, com execução Unattended gerenciada pelo UiPath Orchestrator  
**Prazo:** 3 Dias (Meta MVP, priorizando validações de arquitetura)  

---

## 1. Visão Geral e Princípios de Desenvolvimento

O objetivo deste projeto é construir uma automação RPA de padrão corporativo para portfólio de **RPA Júnior**, demonstrando não apenas automação de interface no Studio, mas domínio de arquitetura integrada em camadas:
- Interface corporativa (*Nexus ERP*) com upload de planilha e acompanhamento de status em tempo real;
- Backend em **Python** para controle de execução, concorrência e integração com o Orchestrator;
- Orquestração centralizada via **UiPath Orchestrator Cloud** acionado por **API Trigger** (OAuth 2.0);
- Execução autônoma pelo **UiPath Robot** na máquina Windows;
- Persistência transacional com banco **SQLite** (`nexus_erp.db`) e emissão de protocolos pelo backend;
- Disponibilização do **Relatório Consolidado de Auditoria** (`Relatorio_Processamento.xlsx`) para download no próprio portal.

### 1.1. Regra de Ouro (Definition of Done)
> **Nenhuma etapa é considerada concluída com base apenas em declaração da IA ou execução teórica.**  
> Cada avanço exige comprovação prática:
> 1. Logs de execução claros e rastreáveis.
> 2. Validação visual ou em arquivo (Excel/Browser/UiPath/Banco SQLite/Orchestrator).
> 3. Aprovação explícita em Gate-Check antes de avançar para a próxima etapa.

### 1.2. Critérios de Aceitação Obrigatórios (Os 5 Pilares)
1. **Concorrência:** O backend deve implementar lock de execução ativo. Se um processamento já estiver em andamento ou na fila, qualquer nova solicitação é bloqueada (`HTTP 409 Conflict`).
2. **Integridade Transacional (ACID):** Persistência no SQLite gerenciada por transações estritas com *rollback* em caso de falha, impedindo pedidos parcialmente cadastrados.
3. **Validação de Entrada:** Arquivos fora do padrão `.xlsx`, corrompidos ou com colunas divergentes são rejeitados imediatamente no upload com log do motivo.
4. **Rastreabilidade Completa:** Cada ciclo possui um `ID_Execucao` único, e cada pedido recebe protocolo imutável gerado pelo backend (`PRT-2026-XXXXXX`), com data/hora e status.
5. **Evidências Comprováveis:** Logs detalhados, screenshots de falhas sistêmicas (`Data/Temp/`), histórico de Jobs no Orchestrator e relatório final consolidado (`Data/Output/Relatorio_Processamento.xlsx`).

---

## 2. Nova Arquitetura da Solução e Fluxo Orchestrator

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PORTAL WEB (NEXUS ERP)                                    │
│  [ Upload do Excel ] ──> [ Botão: Processar Pedidos ] ──> [ Status ] ──> [ Baixar Relatório ]│
└────────────┬─────────────────────────────┬─────────────────────────────────────▲───────┘
             │ Envia .xlsx                 │ Dispara Execução                     │ Download
             ▼                             ▼                                     │
┌─────────────────────────┐   ┌─────────────────────────┐                        │
│       API PYTHON        │   │   UiPath Orchestrator   │                        │
│ • Salva em Data/Input/  │──>│ • Autentica via OAuth   │                        │
│ • Cria ID_Execucao      │   │ • API Trigger (StartJob)│                        │
│ • Monitora Job (Poll)   │   │ • Gerencia fila/robôs   │                        │
└────────────┬────────────┘   └────────────┬────────────┘                        │
             │                             │ Dispara Job                         │
             │ POST /api/pedidos           ▼                                     │
             │ (Valida & Salva)     ┌─────────────────────────┐                  │
             │                      │       UiPath ROBOT      │                  │
             │                      │ • Lê planilha local     │                  │
             │                      │ • Aplica regras negócio │ ─────────────────┤
             │                      │ • Preenche Nexus ERP    │                  │
             ▼                      │ • Gera Relatório Excel  │ ─────────────────┘
┌─────────────────────────┐         └─────────────────────────┘
│  BANCO SQLITE (ERP)     │
│  (nexus_erp.db)         │
└─────────────────────────┘
```

### 2.1. O Ciclo de Vida em 6 Passos
1. **Upload da Planilha:** O usuário envia `Pedidos_Input.xlsx` pelo Nexus ERP. O backend gera um `ID_Execucao` único (ex: `EXEC-2026-001`) e armazena o arquivo em `Data/Input/`.
2. **Habilitação de Disparo:** O portal atualiza o status para `Pronto para processar` e libera o botão de processamento.
3. **Disparo via API Trigger:** Ao clicar em "Processar Pedidos", o Python obtém token OAuth 2.0 da UiPath e chama o endpoint de Start Job no Orchestrator, passando o `ID_Execucao` e caminho do arquivo como argumentos.
4. **Execução pelo Robot:** O Orchestrator despacha o Job para o UiPath Robot na máquina Windows. O robô lê a planilha, valida regras, preenche o portal web e captura os protocolos.
5. **Monitoramento de Estado:** A API Python acompanha o estado do Job no Orchestrator e atualiza o portal em tempo real (*Aguardando* ➔ *Na fila* ➔ *Processando* ➔ *Concluído*).
6. **Relatório e Download:** Ao finalizar com sucesso, o robô salva `Data/Output/Relatorio_Processamento.xlsx` e o portal libera o botão para download.

### 2.2. Requisitos Técnicos Específicos
* **A. Identificação da Execução:** Cada lote recebe um `ID_Execucao` único para segregar arquivos, logs e relatórios.
* **B. Comunicação de Estados no Portal:**
  `Aguardando planilha` ➔ `Pronto para processar` ➔ `Enviando solicitação ao Orchestrator` ➔ `Na fila` ➔ `Processando` ➔ `Concluído` (ou `Falhou`).
* **C. Localização e Argumentos:** O Robot acessa o arquivo no caminho local da máquina. O Python passa os argumentos `in_ExecutionId` e `in_FilePath` ao iniciar o Job no Orchestrator.
* **D. Segurança:** `Client ID`, `Client Secret`, `User Key` e tokens OAuth são mantidos exclusivamente no backend Python (`.env` protegido), nunca expostos no front-end.

---

## 3. Matriz de Responsabilidades

| Componente | Tecnologia | Responsabilidade Principal |
| :--- | :--- | :--- |
| **Nexus ERP** | `HTML / CSS / JS` | Upload de planilha, solicitação de processamento, exibição dos estados e download do relatório. |
| **Python REST API** | `Python (Flask/FastAPI)` | Gerenciamento de arquivos e IDs de execução, autenticação OAuth, chamada de API Trigger no Orchestrator e controle de concorrência. |
| **UiPath Orchestrator**| `Cloud Orchestrator` | Autenticação central, agendamento/disparo de Jobs, governança e monitoramento do status da execução. |
| **UiPath Robot** | `UiPath Studio / Robot`| Execução do workflow na máquina Windows, validação de regras de negócio, automação da interface web e geração do relatório final. |
| **Banco SQLite** | `SQLite (nexus_erp.db)`| Persistência estruturada dos pedidos validados, protocolos oficiais emitidos e histórico. |
| **Arquivos Excel** | `.xlsx` | Planilha de entrada (`Data/Input/`) e Relatório Consolidado de Auditoria (`Data/Output/`). |

---

## 4. Regras de Negócio e Dicionário de Dados

| Campo | Tipo | Obrigatoriedade | Regra de Negócio | Ação do Robô em caso de Falha |
| :--- | :--- | :--- | :--- | :--- |
| `ID_Pedido` | Alfanumérico | Sim | Preenchido e **único** no lote | Rejeitar: "ID ausente ou duplicado" |
| `Nome_Cliente` | Texto | Sim | Preenchido (mín. 3 caracteres) | Rejeitar: "Nome do cliente inválido" |
| `Produto` | Texto | Sim | Preenchido | Rejeitar: "Produto não informado" |
| `Quantidade` | Inteiro | Sim | Numérico e > 0 | Rejeitar: "Quantidade menor ou igual a zero" |
| `Valor_Unitario`| Decimal | Sim | Numérico e > 0.00 | Rejeitar: "Valor unitário inválido" |
| `Status_Origem` | Texto | Sim | `Aberto`, `Aprovado` ou `Cancelado` | Se `Cancelado`: Não cadastrar (Ignorado) |

---

## 5. Plano de 7 Etapas Reorganizado

| Etapa | Foco Principal | Entregável e Gate-Check |
| :--- | :--- | :--- |
| **1. Ambiente UiPath** | Configuração do Automation Cloud, licenças Community, Studio, Robot local conectado e permissão de External Application (OAuth). | **Gate-Check 1:** Publicar um processo simples "Hello World" e dispará-lo com sucesso pelo Orchestrator na máquina local. |
| **2. Backend + SQLite** | Criação da API REST em Python, estrutura do banco `nexus_erp.db`, endpoints de upload com geração de `ID_Execucao` e controle de lock. | **Gate-Check 2:** Upload de planilha via API testado, arquivo salvo em `Data/Input/` e banco inicializado. |
| **3. Integração Orchestrator** | Implementação do cliente OAuth no Python, chamada da API de Start Job e polling de status do Job no Orchestrator. | **Gate-Check 3:** Script Python dispara com sucesso um Job no Orchestrator via API e captura seu status até a conclusão. |
| **4. Portal Nexus ERP** | Interface web com área de upload, indicador dos 6 estados do ciclo de vida, botão de disparo e link condicional de download. | **Gate-Check 4:** Interface integrada à API funcionando no navegador e refletindo os estados em tempo real. |
| **5. Dados e Validação** | Criação da planilha de testes `Pedidos_Input.xlsx` e workflow UiPath para leitura e validação estrita das regras de negócio em memória. | **Gate-Check 5:** Execução local do workflow classificando registros válidos, inválidos e cancelados nos logs de saída. |
| **6. Automação Web e Relatório**| Workflow UiPath preenchendo o Nexus ERP para os pedidos válidos, capturando protocolos gerados e gravando `Relatorio_Processamento.xlsx`. | **Gate-Check 6:** Execução completa gerando o arquivo final com comprovantes e pedidos salvos no SQLite. |
| **7. Testes e Portfólio** | Testes de concorrência, simulação de falhas, tratamento de erros no UiPath, confecção do `README.md` arquitetural e publicação no GitHub. | **Gate-Check 7:** Repositório público no GitHub com documentação, diagramas e evidências gravadas. |

---

## 6. Mapeamento Técnico dos Elementos Web (Nexus ERP)

| Seção | Elemento | Seletor / ID HTML | Tipo | Finalidade |
| :--- | :--- | :--- | :--- | :--- |
| **Painel de Controle** | Input Arquivo Excel | `#input-upload-excel` | Input File | Selecionar `Pedidos_Input.xlsx` |
| **Painel de Controle** | Botão Upload | `#btn-upload` | Button | Enviar planilha para a API Python |
| **Painel de Controle** | Indicador de Estado | `#badge-status-automacao` | Badge | Exibir os 6 estados do ciclo de vida |
| **Painel de Controle** | Botão Processar | `#btn-processar-pedidos` | Button | Solicitar disparo do Job ao Orchestrator |
| **Painel de Controle** | Botão Baixar Relatório | `#btn-download-relatorio` | Link/Button | Baixar `Relatorio_Processamento.xlsx` |
| **Cadastro de Pedido** | Campo ID do Pedido | `#input-pedido-id` | Input Text | Inserir ID único |
| **Cadastro de Pedido** | Campo Cliente | `#input-cliente-nome` | Input Text | Inserir nome do cliente |
| **Cadastro de Pedido** | Campo Produto | `#input-produto` | Input Text | Inserir descrição do item |
| **Cadastro de Pedido** | Campo Quantidade | `#input-quantidade` | Input Number | Inserir quantidade (>0) |
| **Cadastro de Pedido** | Campo Valor Unitário | `#input-valor-unitario` | Input Number | Inserir valor unitário (R$) |
| **Cadastro de Pedido** | Botão Cadastrar | `#btn-cadastrar` | Button | Submeter o formulário |
| **Feedback** | Card de Feedback | `#feedback-section` | Container | Exibir sucesso ou erro |
| **Feedback** | Protocolo Gerado | `#numero-protocolo` | Span Text | Capturar string `PRT-YYYY-XXXXXX` |
| **Histórico** | Tabela de Histórico | `#tabela-pedidos` | Table | Auditoria em tempo real do SQLite |
