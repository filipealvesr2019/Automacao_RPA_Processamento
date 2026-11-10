// Portal Corporativo de Gestão de Pedidos - Nexus ERP
// Frontend Conectado à API Python + SQLite

// Elementos do Formulário de Cadastro
const form = document.getElementById('form-pedido');
const inputPedidoId = document.getElementById('input-pedido-id');
const inputClienteNome = document.getElementById('input-cliente-nome');
const inputProduto = document.getElementById('input-produto');
const inputQuantidade = document.getElementById('input-quantidade');
const inputValorUnitario = document.getElementById('input-valor-unitario');
const btnLimpar = document.getElementById('btn-limpar');
const btnCadastrar = document.getElementById('btn-cadastrar');
const btnResetar = document.getElementById('btn-resetar-banco');

// Elementos de Feedback
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

// Painel de Controle e Orquestração RPA
const inputUploadExcel = document.getElementById('input-upload-excel');
const btnUpload = document.getElementById('btn-upload');
const uploadFeedback = document.getElementById('upload-feedback');
const btnProcessarPedidos = document.getElementById('btn-processar-pedidos');
const processarFeedback = document.getElementById('processar-feedback');
const badgeStatusAutomacao = document.getElementById('badge-status-automacao');
const btnDownloadRelatorio = document.getElementById('btn-download-relatorio');
const relatorioFeedback = document.getElementById('relatorio-feedback');

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
  carregarPedidos();
  consultarStatusAutomacao();
  configurarEventos();

  // Polling para monitorar o status do robô caso esteja processando
  setInterval(consultarStatusAutomacao, 3000);
});

function configurarEventos() {
  form.addEventListener('submit', handleCadastro);
  btnLimpar.addEventListener('click', limparFormulario);
  btnResetar.addEventListener('click', handleResetarBase);
  btnCloseFeedback.addEventListener('click', ocultarFeedback);

  btnUpload.addEventListener('click', handleUploadExcel);
  btnProcessarPedidos.addEventListener('click', handleProcessarPedidos);
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
      // Tratamento estrito de erros do backend (duplicidade, validação ou servidor)
      exibirFeedback('error', 'Rejeição no Cadastro', data.erro || 'Falha ao processar pedido na API.');
      return;
    }

    // Sucesso: Protocolo gerado exclusivamente pelo backend (SQLite)
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
// 3. ORQUESTRAÇÃO RPA: UPLOAD, STATUS E DISPARO
// ==========================================
async function handleUploadExcel() {
  const file = inputUploadExcel.files[0];
  if (!file) {
    uploadFeedback.textContent = 'Por favor, selecione um arquivo Excel primeiro.';
    uploadFeedback.style.color = '#dc2626';
    return;
  }

  btnUpload.disabled = true;
  btnUpload.textContent = 'Enviando...';
  uploadFeedback.textContent = 'Enviando arquivo ao servidor...';
  uploadFeedback.style.color = '#64748b';

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream' },
      body: file
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.erro || 'Erro ao enviar arquivo.');
    }

    uploadFeedback.textContent = `✓ Arquivo recebido: ${file.name} (${data.total_registros} registros)`;
    uploadFeedback.style.color = '#059669';

    consultarStatusAutomacao();
  } catch (err) {
    uploadFeedback.textContent = `Erro: ${err.message}`;
    uploadFeedback.style.color = '#dc2626';
  } finally {
    btnUpload.disabled = false;
    btnUpload.textContent = 'Enviar Planilha';
  }
}

async function handleProcessarPedidos() {
  btnProcessarPedidos.disabled = true;
  btnProcessarPedidos.textContent = '⏳ Robô Executando...';
  processarFeedback.textContent = 'Robô em execução: validando regras de negócio e persistindo pedidos...';
  atualizarBadgeStatus('PROCESSANDO', 'Processando pedidos...');

  try {
    const res = await fetch('/api/processar', { method: 'POST' });
    const data = await res.json();

    if (!res.ok) {
      alert(data.erro || 'Não foi possível iniciar o processamento.');
      consultarStatusAutomacao();
      return;
    }

    // Polling imediato acelerado durante o processamento
    const intervalId = setInterval(async () => {
      const statusRes = await fetch('/api/status');
      if (statusRes.ok) {
        const info = await statusRes.json();
        consultarStatusAutomacao();
        if (info.estado === 'CONCLUIDO' || info.estado === 'FALHOU') {
          clearInterval(intervalId);
          carregarPedidos();
        }
      }
    }, 1000);

  } catch (err) {
    alert('Erro de conexão ao solicitar início da automação.');
    consultarStatusAutomacao();
  }
}

async function consultarStatusAutomacao() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const info = await res.json();

    atualizarBadgeStatus(info.estado, info.mensagem);

    if (info.estado === 'AGUARDANDO_PLANILHA') {
      btnProcessarPedidos.disabled = false;
      btnProcessarPedidos.textContent = '⚙️ Processar Pedidos';
      processarFeedback.textContent = 'Dica: Selecione a planilha ao lado ou clique para usar o arquivo padrão.';
      btnDownloadRelatorio.classList.add('hidden');
      relatorioFeedback.textContent = 'Disponível após conclusão do robô.';
    } else if (info.estado === 'PRONTO_PARA_PROCESSAR') {
      btnProcessarPedidos.disabled = false;
      btnProcessarPedidos.textContent = '⚙️ Processar Pedidos';
      processarFeedback.textContent = 'Planilha carregada. Clique para iniciar o processamento!';
      uploadFeedback.textContent = `✓ Planilha pronta: ${info.arquivo_atual || 'Pedidos_Input.xlsx'}`;
      uploadFeedback.style.color = '#059669';
      btnDownloadRelatorio.classList.add('hidden');
    } else if (info.estado === 'PROCESSANDO') {
      btnProcessarPedidos.disabled = true;
      btnProcessarPedidos.textContent = '⏳ Robô Executando...';
      processarFeedback.textContent = 'Aguarde: o robô está validando e cadastrando pedidos.';
      btnDownloadRelatorio.classList.add('hidden');
      relatorioFeedback.textContent = 'Gerando relatório...';
      carregarPedidos();
    } else if (info.estado === 'CONCLUIDO') {
      btnProcessarPedidos.disabled = false;
      btnProcessarPedidos.textContent = '⚙️ Processar Novamente';
      processarFeedback.textContent = 'Última execução finalizada com sucesso!';
      btnDownloadRelatorio.classList.remove('hidden');
      relatorioFeedback.textContent = '✓ Relatório pronto para download.';
      carregarPedidos();
    } else if (info.estado === 'FALHOU') {
      btnProcessarPedidos.disabled = false;
      btnProcessarPedidos.textContent = '⚙️ Tentar Novamente';
      processarFeedback.textContent = `Atenção: ${info.mensagem}`;
      btnDownloadRelatorio.classList.add('hidden');
    }
  } catch (err) {
    console.warn('Erro ao consultar status da automação:', err);
  }
}

function atualizarBadgeStatus(estado, mensagem) {
  badgeStatusAutomacao.className = 'badge-status';

  const map = {
    'AGUARDANDO_PLANILHA': { label: 'Aguardando Planilha', cls: 'badge-waiting' },
    'PRONTO_PARA_PROCESSAR': { label: 'Pronto para Processar', cls: 'badge-ready' },
    'PROCESSANDO': { label: 'Processando...', cls: 'badge-processing' },
    'CONCLUIDO': { label: 'Concluído', cls: 'badge-completed' },
    'FALHOU': { label: 'Falhou', cls: 'badge-failed' }
  };

  const current = map[estado] || { label: estado, cls: 'badge-waiting' };
  badgeStatusAutomacao.textContent = current.label;
  badgeStatusAutomacao.classList.add(current.cls);
  badgeStatusAutomacao.title = mensagem || '';
}

// ==========================================
// 4. RESET DA BASE E CONTROLES DE INTERFACE
// ==========================================
async function handleResetarBase() {
  const confirmou = confirm('Atenção: Isso irá apagar todos os pedidos do banco SQLite e resetar o histórico. Deseja continuar?');
  if (!confirmou) return;

  try {
    const res = await fetch('/api/reset', { method: 'POST' });
    const data = await res.json();
    exibirFeedback('success', 'Base Resetada', 'Todos os pedidos do SQLite foram apagados com sucesso.');
    carregarPedidos();
    consultarStatusAutomacao();
    uploadFeedback.textContent = 'Nenhum arquivo enviado.';
    uploadFeedback.style.color = '#64748b';
    inputUploadExcel.value = '';
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
