# Documento de Requisitos e Especificação do Projeto RPA

**Projeto:** Automação de Processamento de Pedidos e Cadastro Corporativo (ERP)  
**Ferramenta Principal:** UiPath Studio  
**Assistente de Desenvolvimento:** Antigravity  
**Metodologia:** Desenvolvimento Guiado por Evidências (Gate-Check em 7 Etapas)  
**Prazo:** 3 Dias  

---

## 1. Visão Geral e Princípios de Desenvolvimento

O objetivo deste projeto é construir uma automação RPA profissional, robusta e pronta para portfólio, demonstrando o fluxo completo de uma operação empresarial real:
- Leitura e auditoria de planilhas de entrada;
- Validação estrita de regras de negócio;
- Preenchimento e submissão automatizada em portal web corporativo (*Nexus ERP*);
- Captura de comprovante/protocolo gerado pelo sistema;
- Tratamento de exceções e geração de relatório final consolidado.

### 1.1. Regra de Ouro (Definition of Done)
> **Nenhuma etapa é considerada concluída com base apenas em declaração da IA ou execução teórica.**  
> Cada avanço exige comprovação prática:
> 1. Logs de execução claros e rastreáveis.
> 2. Validação visual ou em arquivo (Excel/Browser/UiPath).
> 3. Aprovação explícita antes de avançar para a próxima etapa.

---

## 2. Arquitetura da Solução

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Planilha Excel  │  ──>  │   Robô UiPath   │  ──>  │   Portal Web    │  ──>  │ Relatório Excel │
│ (Pedidos_Input) │       │ (Leitura/Regra) │       │   (Nexus ERP)   │       │ (Status/Logs)   │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **Entrada:** `Data/Input/Pedidos_Input.xlsx` contendo a fila de pedidos diários.
2. **Processamento:** Robô UiPath valida a integridade de cada registro.
3. **Destino:** Formulário web local (`http://localhost:8000`), cadastrando pedidos válidos e coletando o protocolo.
4. **Saída:** `Data/Output/Relatorio_Processamento.xlsx` com abas de sucesso, erros e ignorados.

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

### Dia 1 — Fundação, Ambiente e Dados
* **Etapa 1 — Definir o processo:**
  - Sistema alvo definido: *Nexus ERP Corporativo* rodando em servidor local (`http://localhost:8000`).
  - Documento de processo e regras aprovados.
  - *Entrega:* Portal web criado + Documento de requisitos atualizado.
* **Etapa 2 — Preparar o ambiente:**
  - Instalação e verificação do UiPath Studio.
  - Criação do projeto UiPath e estrutura de pastas.
  - *Entrega:* Projeto UiPath criado e validado.
* **Etapa 3 — Criar os dados de entrada:**
  - Criação de `Data/Input/Pedidos_Input.xlsx` contendo casos de sucesso e casos de borda/erro.
  - *Entrega:* Planilha criada e validada.

### Dia 2 — Lógica de Negócio e Automação Web
* **Etapa 4 — Desenvolver leitura e validação:**
  - Leitura da planilha em `DataTable`.
  - Classificação em Válidos, Inválidos e Cancelados (apenas em memória e logs, sem submissão).
  - *Entrega:* Output do UiPath comprovando a correta segregação.
* **Etapa 5 — Automatizar o cadastro web:**
  - Abertura de navegador e navegação até `http://localhost:8000`.
  - Preenchimento dos campos mapeados e envio.
  - Captura do protocolo retornado (`PRT-2026-XXXX`).
  - *Entrega:* Pedidos válidos inseridos e visíveis na tabela do portal.

### Dia 3 — Relatórios, Resiliência e Portfólio
* **Etapa 6 — Criar relatório e tratar erros:**
  - Estruturação do bloco `Try Catch` com captura de `BusinessRuleException` e `SystemException`.
  - Geração de `Relatorio_Processamento.xlsx` com timestamps e protocolos.
  - Captura de screenshot em falhas técnicas em `Data/Temp/`.
  - *Entrega:* Relatório final preenchido e logs de auditoria.
* **Etapa 7 — Testar e publicar:**
  - Testes de estresse com massa de dados anômala.
  - Confecção do `README.md` detalhado e estruturado para entrevistas.
  - Publicação do repositório no GitHub com evidências.
  - *Entrega:* Portfólio concluído e publicado.

---

## 5. Mapeamento Técnico dos Elementos Web (Nexus ERP)

| Elemento | Seletor / ID HTML | Tipo | Finalidade |
| :--- | :--- | :--- | :--- |
| Campo ID do Pedido | `#input-pedido-id` | Input Text | Inserir ID único |
| Campo Cliente | `#input-cliente-nome` | Input Text | Inserir nome do cliente |
| Campo Produto | `#input-produto` | Input Text | Inserir descrição do item |
| Campo Quantidade | `#input-quantidade` | Input Number | Inserir quantidade (>0) |
| Campo Valor Unitário | `#input-valor-unitario` | Input Number | Inserir valor unitário (R$) |
| Botão Cadastrar | `#btn-cadastrar` | Button | Submeter o formulário |
| Card de Feedback | `#feedback-section` | Container | Detectar classe `.success` ou `.error` |
| Protocolo Gerado | `#numero-protocolo` | Span Text | Capturar string `PRT-YYYY-XXXXXX` |
| Tabela de Histórico | `#tabela-pedidos` | Table | Conferência e auditoria |
