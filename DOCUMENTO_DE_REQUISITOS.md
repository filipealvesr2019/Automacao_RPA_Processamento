# Documento de Requisitos e Especificação do Projeto RPA

**Projeto:** Automação de Processamento de Pedidos e Cadastro Corporativo (ERP)  
**Ferramenta Principal:** UiPath Studio  
**Assistente de Desenvolvimento:** Antigravity  
**Metodologia:** Desenvolvimento Guiado por Evidências (Gate-Check em 7 Etapas)  
**Modalidade:** Automação Sob Demanda (*Attended Trigger* com Execução Autônoma)  
**Prazo:** 3 Dias  

---

## 1. Visão Geral e Princípios de Desenvolvimento

O objetivo deste projeto é construir uma automação RPA profissional, robusta e pronta para portfólio, demonstrando o fluxo completo de uma operação empresarial moderna em camadas:
- Interface corporativa (*Nexus ERP*) com área de **Upload de Planilha de Pedidos** e painel de controle;
- Disparo sob demanda do robô UiPath através do botão **"Processar Pedidos"**;
- Execução 100% autônoma pelo UiPath (leitura, auditoria de regras de negócio, preenchimento web e captura de comprovantes);
- Backend em **Python** com dupla validação de integridade e persistência transacional em banco **SQLite** (`nexus_erp.db`);
- Emissão oficial do protocolo pelo backend;
- Monitoramento de ciclo de vida e disponibilização de download do **Relatório Consolidado de Auditoria** (`Relatorio_Processamento.xlsx`) no próprio portal.

### 1.1. Regra de Ouro (Definition of Done)
> **Nenhuma etapa é considerada concluída com base apenas em declaração da IA ou execução teórica.**  
> Cada avanço exige comprovação prática:
> 1. Logs de execução claros e rastreáveis.
> 2. Validação visual ou em arquivo (Excel/Browser/UiPath/Banco SQLite).
> 3. Aprovação explícita antes de avançar para a próxima etapa.

---

## 2. Arquitetura da Solução e Fluxo Sob Demanda

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

### 2.1. O Ciclo de Vida em 5 Passos (Fluxo Definitivo)

1. **Upload da Planilha:** O usuário acessa o Nexus ERP, seleciona `Pedidos_Input.xlsx` e faz o envio. O backend confirma o recebimento e armazena o arquivo em `Data/Input/Pedidos_Input.xlsx`.
2. **Confirmação e Habilitação:** O portal atualiza o status para `Pronto para Processar` e habilita a ação de início.
3. **Disparo Sob Demanda:** O usuário clica em **"Processar Pedidos"**. A API registra o início e aciona o robô UiPath.
4. **Execução Autônoma do UiPath:** O robô trabalha sozinho (sem intervenção humana):
   - Lê a planilha;
   - Aplica as regras de negócio em memória;
   - Preenche o formulário do ERP para os pedidos válidos;
   - Recebe o protocolo gerado pelo backend;
   - Consolida os resultados e salva `Data/Output/Relatorio_Processamento.xlsx`.
5. **Relatório Disponível:** O UiPath sinaliza a conclusão. O portal muda o estado para `Concluído` e libera o botão para download do relatório de auditoria final.

### 2.2. Diretrizes Críticas de Arquitetura

1. **O Botão Solicita o Processamento (Não Gera o Relatório Diretamente):**  
   O botão do portal apenas inicia a orquestração do robô UiPath. O relatório só passa a existir quando o robô concluir toda a fila de pedidos.
2. **Controle Estrito de Concorrência (Lock de Execução):**  
   O backend não permite disparar dois processamentos simultâneos. Se o robô já estiver executando, novas tentativas de disparo são bloqueadas.
3. **Máquina de Estados Visível no Portal:**  
   O usuário acompanha claramente as 4 etapas no painel:
   - `Aguardando Planilha` ➔ `Pronto para Processar` ➔ `Processando...` (com bloqueio de tela/botão) ➔ `Concluído` (ou `Falhou`).
4. **Liberação Condicional de Download:**  
   O link/botão para download do relatório só fica visível e ativo após a transição para o estado `Concluído`.
5. **Origem do Protocolo no Backend:**  
   O protocolo (`PRT-2026-XXXXXX`) é gerado pela API Python no momento do `INSERT` no SQLite, nunca pelo JavaScript.
6. **Dupla Validação (Defesa em Profundidade):**  
   A API Python rejeita qualquer requisição com campos nulos, valores $\le 0$ ou duplicidade de `ID_Pedido`.
7. **Tratamento de Exceções no Frontend:**  
   Falhas de rede, erros HTTP (`400`, `409`, `500`) ou travamentos são tratados com alertas visuais explícitos de erro.

---

### 2.3. Matriz de Responsabilidades

| Componente | Tecnologia | Responsabilidade Principal |
| :--- | :--- | :--- |
| **Interface ERP** | `HTML / CSS / JS` | Upload de arquivos, exibição dos estados (`Aguardando`, `Processando`, `Concluído`), disparo do fluxo e formulário de cadastro. |
| **API Local** | `Python (REST)` | Receber upload do Excel, gerenciar o estado da execução (evitar concorrência), disparar o robô, validar regras e persistir dados. |
| **Banco de Dados** | `SQLite (nexus_erp.db)`| Armazenamento estruturado e persistente de todos os pedidos e protocolos gerados. |
| **Robô RPA** | `UiPath Studio` | Leitura da planilha, auditoria em memória, preenchimento automatizado na interface web e gravação do relatório final. |
| **Arquivos Excel** | `.xlsx` | Entrada (`Data/Input/`) com os dados brutos e Saída (`Data/Output/`) com auditoria consolidada para download. |

---

## 3. Regras de Negócio e Dicionário de Dados

| Campo | Tipo | Obrigatoriedade | Regra de Negócio | Ação do Robô em caso de Falha |
| :--- | :--- | :--- | :--- | :--- |
| `ID_Pedido` | Alfanumérico | Sim | Preenchido e **único** no lote | Rejeitar: "ID ausente ou duplicado" |
| `Nome_Cliente` | Texto | Sim | Preenchido (mín. 3 caracteres) | Rejeitar: "Nome do cliente inválido" |
| `Produto` | Texto | Sim | Preenchido | Rejeitar: "Produto não informado" |
| `Quantidade` | Inteiro | Sim | Numérico e > 0 | Rejeitar: "Quantidade menor ou igual a zero" |
| `Valor_Unitario`| Decimal | Sim | Numérico e > 0.00 | Rejeitar: "Valor unitário inválido" |
| `Status_Origem` | Texto | Sim | `Aberto`, `Aprovado` ou `Cancelado` | Se `Cancelado`: Não cadastrar (Ignorado) |

---

## 4. Plano Passo a Passo (7 Etapas em 3 Dias)

### Dia 1 — Fundação, Ambiente, Backend e Dados
* **Etapa 1 — Definir e Construir o Backend / Portal Alvo:**
  - **1.1 (API + SQLite):** Criação da API Python com endpoints de cadastro, persistência SQLite e controle de estado (`/api/pedidos`, `/api/upload`, `/api/processar`, `/api/status`, `/api/relatorio`).
  - **1.2 (Interface Completa):** Atualização do Nexus ERP com área de Upload, Máquina de Estados (Aguardando / Processando / Concluído), botão "Processar Pedidos" e formulário conectado.
  - **1.3 (Testes de Integração):** Validação de persistência, bloqueio de concorrência e respostas HTTP.
  - *Entrega:* Portal web e API funcionando com persistência real em SQLite e controle de ciclo de vida.
* **Etapa 2 — Preparar o ambiente UiPath:**
  - Verificação/instalação do UiPath Studio.
  - Criação do projeto UiPath e estrutura de pastas padronizada.
  - *Entrega:* Projeto UiPath configurado e validado.
* **Etapa 3 — Criar os dados de entrada:**
  - Criação de `Data/Input/Pedidos_Input.xlsx` contendo casos de sucesso e casos de borda/erro.
  - *Entrega:* Planilha criada e validada.

### Dia 2 — Lógica de Negócio e Automação Web
* **Etapa 4 — Desenvolver leitura e validação:**
  - Leitura da planilha em `DataTable`.
  - Classificação em Válidos, Inválidos e Cancelados (apenas em memória e logs, sem submissão).
  - *Entrega:* Output do UiPath comprovando a correta segregação.
* **Etapa 5 — Automatizar o cadastro web:**
  - Abertura de navegador e navegação até `http://localhost:8080`.
  - Preenchimento dos campos mapeados e envio.
  - Captura do protocolo retornado pela API via interface (`PRT-2026-XXXX`).
  - *Entrega:* Pedidos válidos inseridos e gravados no banco SQLite.

### Dia 3 — Relatórios, Resiliência e Portfólio
* **Etapa 6 — Criar relatório e tratar erros:**
  - Estruturação do bloco `Try Catch` com captura de `BusinessRuleException` e `SystemException`.
  - Geração de `Relatorio_Processamento.xlsx` com timestamps e protocolos.
  - Captura de screenshot em falhas técnicas em `Data/Temp/`.
  - *Entrega:* Relatório final preenchido, disponível para download no portal e logs de auditoria.
* **Etapa 7 — Testar e publicar:**
  - Testes de estresse com massa de dados anômala.
  - Confecção do `README.md` detalhado e estruturado para entrevistas.
  - Publicação do repositório no GitHub com evidências.
  - *Entrega:* Portfólio concluído e publicado.

---

## 5. Mapeamento Técnico dos Elementos Web (Nexus ERP)

| Seção | Elemento | Seletor / ID HTML | Tipo | Finalidade |
| :--- | :--- | :--- | :--- | :--- |
| **Painel de Controle** | Input Arquivo Excel | `#input-upload-excel` | Input File | Selecionar `Pedidos_Input.xlsx` |
| **Painel de Controle** | Botão Upload | `#btn-upload` | Button | Enviar planilha para o backend |
| **Painel de Controle** | Indicador de Estado | `#badge-status-automacao` | Badge | Exibir `Aguardando`, `Processando` ou `Concluído` |
| **Painel de Controle** | Botão Processar | `#btn-processar-pedidos` | Button | Solicitar início da execução do UiPath |
| **Painel de Controle** | Botão Baixar Relatório | `#btn-download-relatorio` | Link/Button | Baixar `Relatorio_Processamento.xlsx` gerado |
| **Cadastro de Pedido** | Campo ID do Pedido | `#input-pedido-id` | Input Text | Inserir ID único |
| **Cadastro de Pedido** | Campo Cliente | `#input-cliente-nome` | Input Text | Inserir nome do cliente |
| **Cadastro de Pedido** | Campo Produto | `#input-produto` | Input Text | Inserir descrição do item |
| **Cadastro de Pedido** | Campo Quantidade | `#input-quantidade` | Input Number | Inserir quantidade (>0) |
| **Cadastro de Pedido** | Campo Valor Unitário | `#input-valor-unitario` | Input Number | Inserir valor unitário (R$) |
| **Cadastro de Pedido** | Botão Cadastrar | `#btn-cadastrar` | Button | Submeter o formulário |
| **Feedback** | Card de Feedback | `#feedback-section` | Container | Exibir sucesso ou erro |
| **Feedback** | Protocolo Gerado | `#numero-protocolo` | Span Text | Capturar string `PRT-YYYY-XXXXXX` |
| **Histórico** | Tabela de Histórico | `#tabela-pedidos` | Table | Auditoria em tempo real do SQLite |
