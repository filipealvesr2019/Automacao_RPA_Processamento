// Portal Corporativo de Gestão de Pedidos - Lógica do Frontend
const STORAGE_KEY = 'NEXUS_ERP_PEDIDOS';

// Elementos da Interface
const form = document.getElementById('form-pedido');
const inputPedidoId = document.getElementById('input-pedido-id');
const inputClienteNome = document.getElementById('input-cliente-nome');
const inputProduto = document.getElementById('input-produto');
const inputQuantidade = document.getElementById('input-quantidade');
const inputValorUnitario = document.getElementById('input-valor-unitario');
const btnLimpar = document.getElementById('btn-limpar');
const btnResetar = document.getElementById('btn-resetar-banco');

// Elementos de Feedback
const feedbackSection = document.getElementById('feedback-section');
const feedbackIcon = document.getElementById('feedback-icon');
const feedbackTitle = document.getElementById('feedback-title');
const feedbackMessage = document.getElementById('feedback-message');
const protocoloWrapper = document.getElementById('protocolo-wrapper');
const numeroProtocolo = document.getElementById('numero-protocolo');
const btnCloseFeedback = document.getElementById('btn-close-feedback');

// Tabela de Consulta
const tabelaCorpo = document.getElementById('tabela-corpo');
const totalRegistros = document.getElementById('total-registros');

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
  carregarPedidos();
  configurarEventos();
});

function getPedidos() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : [];
}

function salvarPedidos(pedidos) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(pedidos));
  renderizarTabela();
}

function configurarEventos() {
  form.addEventListener('submit', handleCadastro);
  btnLimpar.addEventListener('click', limparFormulario);
  btnResetar.addEventListener('click', handleResetarBase);
  btnCloseFeedback.addEventListener('click', ocultarFeedback);
}

function handleCadastro(e) {
  e.preventDefault();

  const pedidoId = inputPedidoId.value.trim().toUpperCase();
  const clienteNome = inputClienteNome.value.trim();
  const produto = inputProduto.value.trim();
  const quantidade = parseInt(inputQuantidade.value, 10);
  const valorUnitario = parseFloat(inputValorUnitario.value);

  // Validação 1: Campos em branco
  if (!pedidoId || !clienteNome || !produto || isNaN(quantidade) || isNaN(valorUnitario)) {
    exibirFeedback('error', 'Campos Incompletos', 'Preencha todos os campos obrigatórios marcados com asterisco (*).');
    return;
  }

  // Validação 2: Quantidade
  if (quantidade <= 0) {
    exibirFeedback('error', 'Quantidade Inválida', 'A quantidade do pedido deve ser maior que zero.');
    inputQuantidade.focus();
    return;
  }

  // Validação 3: Valor Unitário
  if (valorUnitario <= 0) {
    exibirFeedback('error', 'Valor Unitário Inválido', 'O valor unitário deve ser maior que R$ 0,00.');
    inputValorUnitario.focus();
    return;
  }

  // Validação 4: Unicidade do ID do Pedido
  const pedidosExistentes = getPedidos();
  const jaExiste = pedidosExistentes.some(p => p.id === pedidoId);

  if (jaExiste) {
    exibirFeedback(
      'error',
      'ID de Pedido Duplicado',
      `O pedido '${pedidoId}' já foi cadastrado anteriormente no sistema. Operação rejeitada.`
    );
    inputPedidoId.focus();
    return;
  }

  // Gera protocolo de confirmação
  const ano = new Date().getFullYear();
  const randomSuffix = Math.floor(100000 + Math.random() * 900000);
  const protocolo = `PRT-${ano}-${randomSuffix}`;
  const dataHora = new Date().toLocaleString('pt-BR');
  const valorTotal = (quantidade * valorUnitario);

  const novoPedido = {
    id: pedidoId,
    cliente: clienteNome,
    produto: produto,
    quantidade: quantidade,
    valorUnitario: valorUnitario,
    valorTotal: valorTotal,
    protocolo: protocolo,
    dataHora: dataHora
  };

  pedidosExistentes.unshift(novoPedido);
  salvarPedidos(pedidosExistentes);

  // Feedback de Sucesso
  exibirFeedback(
    'success',
    'Pedido Cadastrado com Sucesso!',
    `O pedido '${pedidoId}' do cliente '${clienteNome}' foi registrado e faturado.`,
    protocolo
  );

  limparFormulario();
}

function exibirFeedback(tipo, titulo, mensagem, protocolo = null) {
  feedbackSection.className = `feedback-card ${tipo}`;
  feedbackTitle.textContent = titulo;
  feedbackMessage.textContent = mensagem;

  if (tipo === 'success') {
    feedbackIcon.textContent = '✓';
    if (protocolo) {
      numeroProtocolo.textContent = protocolo;
      protocoloWrapper.classList.remove('hidden');
    }
  } else {
    feedbackIcon.textContent = '!';
    protocoloWrapper.classList.add('hidden');
  }

  feedbackSection.classList.remove('hidden');
  feedbackSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function ocultarFeedback() {
  feedbackSection.classList.add('hidden');
}

function limparFormulario() {
  form.reset();
  inputPedidoId.focus();
}

function renderizarTabela() {
  const pedidos = getPedidos();
  totalRegistros.textContent = `${pedidos.length} ${pedidos.length === 1 ? 'pedido' : 'pedidos'}`;

  if (pedidos.length === 0) {
    tabelaCorpo.innerHTML = `
      <tr id="linha-vazia">
        <td colspan="8" class="text-center empty-state">Nenhum pedido registrado até o momento.</td>
      </tr>
    `;
    return;
  }

  tabelaCorpo.innerHTML = pedidos.map(p => `
    <tr>
      <td><strong>${escapeHtml(p.id)}</strong></td>
      <td>${escapeHtml(p.cliente)}</td>
      <td>${escapeHtml(p.produto)}</td>
      <td>${p.quantidade}</td>
      <td>R$ ${p.valorUnitario.toFixed(2).replace('.', ',')}</td>
      <td>R$ ${p.valorTotal.toFixed(2).replace('.', ',')}</td>
      <td><span class="protocolo-code" style="font-size:12px;">${escapeHtml(p.protocolo)}</span></td>
      <td style="color:#64748b; font-size:12px;">${p.dataHora}</td>
    </tr>
  `).join('');
}

function carregarPedidos() {
  renderizarTabela();
}

function handleResetarBase() {
  if (confirm('Tem certeza de que deseja limpar todos os pedidos cadastrados na base de testes?')) {
    localStorage.removeItem(STORAGE_KEY);
    renderizarTabela();
    exibirFeedback('success', 'Base Limpa', 'Todos os pedidos de teste foram removidos.');
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

