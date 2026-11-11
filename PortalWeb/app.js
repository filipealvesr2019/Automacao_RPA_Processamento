// Portal Corporativo de Gestão de Pedidos - Nexus ERP
// Frontend Conectado à API Python + SQLite

// Elementos do Formulário de Cadastro Manual
const form = document.getElementById('form-pedido');
const inputPedidoId = document.getElementById('input-pedido-id');
const inputClienteNome = document.getElementById('input-cliente-nome');
const inputProduto = document.getElementById('input-produto');
const inputQuantidade = document.getElementById('input-quantidade');
const inputValorUnitario = document.getElementById('input-valor-unitario');
const btnLimpar = document.getElementById('btn-limpar');
const btnCadastrar = document.getElementById('btn-cadastrar');
const btnResetar = document.getElementById('btn-resetar-banco');

// Elementos de Feedback e Protocolo
const feedbackSection = document.getElementById('feedback-section');
const feedbackIcon = document.getElementById('feedback-icon');
const feedbackTitle = document.getElementById('feedback-title');
const feedbackMessage = document.getElementById('feedback-message');
const protocoloWrapper = document.getElementById('protocolo-wrapper');
const numeroProtocolo = document.getElementById('numero-protocolo');
const btnCloseFeedback = document.getElementById('btn-close-feedback');

// Tabela de Consulta do SQLite
const tabelaCorpo = document.getElementById('tabela-corpo');
const totalRegistros = document.getElementById('total-registros');

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
  carregarPedidos();
  configurarEventos();
});

function configurarEventos() {
  form.addEventListener('submit', handleCadastro);
  btnLimpar.addEventListener('click', limparFormulario);
  btnResetar.addEventListener('click', handleResetarBase);
  btnCloseFeedback.addEventListener('click', ocultarFeedback);
}

// ==========================================
// 1. CARREGAMENTO E ATUALIZAÇÃO DA TABELA (SQLITE)
// ==========================================
async function carregarPedidos() {
  try {
    const res = await fetch('/api/pedidos');
    if (!res.ok) throw new Error('Falha ao consultar banco SQLite.');
    const pedidos = await res.json();
    renderizarTabela(pedidos);
  } catch (err) {
    console.error('Erro ao carregar pedidos:', err);
    totalRegistros.textContent = 'Erro ao carregar';
  }
}

function renderizarTabela(pedidos) {
  tabelaCorpo.innerHTML = '';
  totalRegistros.textContent = `${pedidos.length} ${pedidos.length === 1 ? 'pedido' : 'pedidos'}`;

  if (!pedidos || pedidos.length === 0) {
    tabelaCorpo.innerHTML = `
      <tr id="linha-vazia">
        <td colspan="8" class="text-center empty-state">Nenhum pedido registrado até o momento.</td>
      </tr>
    `;
    return;
  }

  pedidos.forEach(pedido => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${escapeHtml(pedido.pedido_id)}</strong></td>
      <td>${escapeHtml(pedido.cliente)}</td>
      <td>${escapeHtml(pedido.produto)}</td>
      <td>${pedido.quantidade}</td>
      <td>R$ ${parseFloat(pedido.valor_unitario).toFixed(2).replace('.', ',')}</td>
      <td><strong>R$ ${parseFloat(pedido.total).toFixed(2).replace('.', ',')}</strong></td>
      <td><span class="protocolo-code">${escapeHtml(pedido.protocolo)}</span></td>
      <td><small class="text-muted">${escapeHtml(pedido.data_hora)}</small></td>
    `;
    tabelaCorpo.appendChild(tr);
  });
}

// ==========================================
// 2. CADASTRO DE PEDIDO (ALVO DO ROBÔ UIPATH)
// ==========================================
async function handleCadastro(e) {
  e.preventDefault();

  const pedidoId = inputPedidoId.value.trim().toUpperCase();
  const clienteNome = inputClienteNome.value.trim();
  const produto = inputProduto.value.trim();
  const quantidade = parseInt(inputQuantidade.value, 10);
  const valorUnitario = parseFloat(inputValorUnitario.value);

  // Pré-validação de campos obrigatórios no frontend
  if (!pedidoId || !clienteNome || !produto || isNaN(quantidade) || isNaN(valorUnitario)) {
    exibirFeedback('error', 'Campos Incompletos', 'Preencha todos os campos obrigatórios marcados com asterisco (*).');
    return;
  }

  if (quantidade <= 0) {
    exibirFeedback('error', 'Quantidade Inválida', 'A quantidade do pedido deve ser maior que zero.');
    inputQuantidade.focus();
    return;
  }

  if (valorUnitario <= 0) {
    exibirFeedback('error', 'Valor Unitário Inválido', 'O valor unitário deve ser maior que R$ 0,00.');
    inputValorUnitario.focus();
    return;
  }

  btnCadastrar.disabled = true;
  btnCadastrar.textContent = 'Enviando ao ERP...';

  try {
    const payload = {
      pedido_id: pedidoId,
      cliente: clienteNome,
      produto: produto,
      quantidade: quantidade,
      valor_unitario: valorUnitario
    };

    const res = await fetch('/api/pedidos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      // Retorno de erro do backend (ex: ID duplicado ou erro de banco)
      exibirFeedback('error', 'Rejeição no Cadastro', data.erro || 'Falha ao processar pedido na API.');
      return;
    }

    // Sucesso: Protocolo oficial gerado exclusivamente pelo backend (SQLite)
    exibirFeedback(
      'success',
      'Pedido Cadastrado com Sucesso!',
      `O pedido '${data.pedido_id}' do cliente '${data.cliente}' foi persistido no banco e faturado.`,
      data.protocolo
    );

    limparFormulario();
    carregarPedidos();

  } catch (err) {
    exibirFeedback('error', 'Erro de Conexão', 'Não foi possível conectar ao servidor backend (API indisponível).');
  } finally {
    btnCadastrar.disabled = false;
    btnCadastrar.textContent = 'Cadastrar Pedido';
  }
}

// ==========================================
// 3. RESET DA BASE E CONTROLES DE INTERFACE
// ==========================================
async function handleResetarBase() {
  const confirmou = confirm('Atenção: Isso irá apagar todos os pedidos do banco SQLite e resetar o histórico. Deseja continuar?');
  if (!confirmou) return;

  try {
    const res = await fetch('/api/reset', { method: 'POST' });
    const data = await res.json();
    exibirFeedback('success', 'Base Resetada', 'Todos os pedidos do SQLite foram apagados com sucesso.');
    carregarPedidos();
  } catch (err) {
    exibirFeedback('error', 'Falha ao Resetar', 'Não foi possível resetar o banco de dados.');
  }
}

function exibirFeedback(tipo, titulo, mensagem, protocolo = null) {
  feedbackSection.classList.remove('hidden', 'feedback-success', 'feedback-error');

  if (tipo === 'success') {
    feedbackSection.classList.add('feedback-success');
    feedbackIcon.textContent = '✓';
    feedbackTitle.textContent = titulo;
    feedbackMessage.textContent = mensagem;

    if (protocolo) {
      protocoloWrapper.classList.remove('hidden');
      numeroProtocolo.textContent = protocolo;
    } else {
      protocoloWrapper.classList.add('hidden');
    }
  } else {
    feedbackSection.classList.add('feedback-error');
    feedbackIcon.textContent = '✕';
    feedbackTitle.textContent = titulo;
    feedbackMessage.textContent = mensagem;
    protocoloWrapper.classList.add('hidden');
  }

  feedbackSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function ocultarFeedback() {
  feedbackSection.classList.add('hidden');
}

function limparFormulario() {
  form.reset();
  inputPedidoId.focus();
}

function escapeHtml(texto) {
  if (texto === null || texto === undefined) return '';
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
