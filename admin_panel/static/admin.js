// API Base URL
const API_URL = window.location.origin;

// Armazenar token JWT
let authToken = localStorage.getItem('admin_token');

// Função para fazer requisições autenticadas
async function apiRequest(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const options = {
        method: method,
        headers: headers
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        
        if (response.status === 401) {
            // Token expirado ou inválido
            localStorage.removeItem('admin_token');
            window.location.href = '/admin/login';
            return null;
        }
        
        const result = await response.json();
        return { status: response.status, data: result };
    } catch (error) {
        console.error('API Error:', error);
        showAlert('Erro de conexão com o servidor', 'error');
        return null;
    }
}

// Função para mostrar alertas
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = message;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.maxWidth = '300px';
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// Função para mostrar loading
function showLoading(show) {
    const loadingDiv = document.getElementById('loading-overlay') || createLoadingOverlay();
    loadingDiv.style.display = show ? 'flex' : 'none';
}

function createLoadingOverlay() {
    const div = document.createElement('div');
    div.id = 'loading-overlay';
    div.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    div.innerHTML = '<div class="spinner"></div><p style="margin-top: 10px;">Carregando...</p>';
    document.body.appendChild(div);
    return div;
}

// ==================== DASHBOARD ====================

async function loadDashboard() {
    showLoading(true);
    const result = await apiRequest('/api/admin/dashboard/stats');
    showLoading(false);
    
    if (result && result.status === 200) {
        document.getElementById('total-users').textContent = result.data.total_users || 0;
        document.getElementById('total-licenses').textContent = result.data.total_licenses || 0;
        document.getElementById('active-licenses').textContent = result.data.active_licenses || 0;
        document.getElementById('expired-licenses').textContent = result.data.expired_licenses || 0;
        document.getElementById('blocked-licenses').textContent = result.data.blocked_licenses || 0;
        document.getElementById('revenue').textContent = `R$ ${(result.data.revenue_last_30_days || 0).toFixed(2)}`;
        
        // Carregar atividade recente
        const activityList = document.getElementById('recent-activity');
        if (activityList && result.data.recent_activity) {
            activityList.innerHTML = result.data.recent_activity.map(activity => `
                <tr>
                    <td>${new Date(activity.created_at).toLocaleString()}</td>
                    <td>${activity.action}</td>
                    <td>${activity.details || '-'}</td>
                    <td>${activity.user || 'Sistema'}</td>
                </tr>
            `).join('');
        }
    }
}

// ==================== LICENÇAS ====================

let currentLicensePage = 0;
const licensePageSize = 50;

async function loadLicenses() {
    showLoading(true);
    const result = await apiRequest(`/api/admin/licenses?skip=${currentLicensePage * licensePageSize}&limit=${licensePageSize}`);
    showLoading(false);
    
    if (result && result.status === 200) {
        const tbody = document.getElementById('licenses-table-body');
        if (tbody) {
            tbody.innerHTML = result.data.licenses.map(license => `
                <tr>
                    <td><code>${license.key}</code></td>
                    <td>${license.user || '-'}</td>
                    <td>${license.plan || '-'}</td>
                    <td><span class="status-badge status-${license.status.toLowerCase()}">${license.status}</span></td>
                    <td>${license.machine_id ? license.machine_id.substring(0, 20) + '...' : '-'}</td>
                    <td>${new Date(license.created_at).toLocaleDateString()}</td>
                    <td>${license.expires_at ? new Date(license.expires_at).toLocaleDateString() : 'Lifetime'}</td>
                    <td>${license.remaining_days || '-'}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="blockLicense('${license.key}')">Bloquear</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteLicense('${license.key}')">Excluir</button>
                    </td>
                </tr>
            `).join('');
        }
        
        // Atualizar paginação
        const pageInfo = document.getElementById('license-page-info');
        if (pageInfo) {
            pageInfo.textContent = `Mostrando ${result.data.licenses.length} de ${result.data.total} licenças`;
        }
    }
}

async function createLicense() {
    const userId = prompt('Digite o ID do usuário:');
    if (!userId) return;
    
    const planType = prompt('Digite o tipo do plano (FREE, THIRTY_DAYS, NINETY_DAYS, ONE_EIGHTY_DAYS, THREE_SIXTY_FIVE_DAYS, LIFETIME):');
    if (!planType) return;
    
    showLoading(true);
    const result = await apiRequest('/api/admin/licenses', 'POST', {
        user_id: parseInt(userId),
        plan_type: planType.toUpperCase()
    });
    showLoading(false);
    
    if (result && result.status === 200) {
        showAlert(`Licença criada com sucesso! Chave: ${result.data.license.key}`, 'success');
        loadLicenses();
    } else {
        showAlert(`Erro ao criar licença: ${result?.data?.detail || 'Erro desconhecido'}`, 'error');
    }
}

async function blockLicense(licenseKey) {
    if (!confirm(`Tem certeza que deseja bloquear a licença ${licenseKey}?`)) return;
    
    showLoading(true);
    const result = await apiRequest(`/api/admin/licenses/${licenseKey}/block`, 'PUT');
    showLoading(false);
    
    if (result && result.status === 200) {
        showAlert('Licença bloqueada com sucesso!', 'success');
        loadLicenses();
    } else {
        showAlert('Erro ao bloquear licença', 'error');
    }
}

async function unblockLicense(licenseKey) {
    if (!confirm(`Tem certeza que deseja desbloquear a licença ${licenseKey}?`)) return;
    
    showLoading(true);
    const result = await apiRequest(`/api/admin/licenses/${licenseKey}/unblock`, 'PUT');
    showLoading(false);
    
    if (result && result.status === 200) {
        showAlert('Licença desbloqueada com sucesso!', 'success');
        loadLicenses();
    } else {
        showAlert('Erro ao desbloquear licença', 'error');
    }
}

async function deleteLicense(licenseKey) {
    if (!confirm(`Tem certeza que deseja EXCLUIR a licença ${licenseKey}? Esta ação não pode ser desfeita.`)) return;
    
    showLoading(true);
    const result = await apiRequest(`/api/admin/licenses/${licenseKey}`, 'DELETE');
    showLoading(false);
    
    if (result && result.status === 200) {
        showAlert('Licença excluída com sucesso!', 'success');
        loadLicenses();
    } else {
        showAlert('Erro ao excluir licença', 'error');
    }
}

// ==================== PLANOS (COM STRIPE) ====================

async function loadPlans() {
    showLoading(true);
    const result = await apiRequest('/api/admin/plans');
    showLoading(false);
    
    if (result && result.status === 200) {
        const tbody = document.getElementById('plans-table-body');
        if (tbody) {
            tbody.innerHTML = result.data.map(plan => `
                <tr>
                    <td>${plan.name}</td>
                    <td>${plan.type}</td>
                    <td>${plan.validity_days ? plan.validity_days + ' dias' : 'Ilimitado'}</td>
                    <td>R$ ${plan.price.toFixed(2)}</td>
                    <td><code style="font-size: 11px;">${plan.stripe_price_id || '-'}</code></td>
                    <td><code style="font-size: 11px;">${plan.stripe_product_id || '-'}</code></td>
                    <td>${plan.is_active ? '✅ Ativo' : '❌ Inativo'}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="editPlan(${plan.id})">Editar</button>
                        <button class="btn btn-danger btn-sm" onclick="deletePlan(${plan.id})">Excluir</button>
                    </td>
                </tr>
            `).join('');
        }
    }
}

function showCreatePlanModal() {
    document.getElementById('plan-modal-title').textContent = 'Criar Novo Plano';
    document.getElementById('plan-id').value = '';
    document.getElementById('plan-name').value = '';
    document.getElementById('plan-type').value = '';
    document.getElementById('plan-validity-days').value = '';
    document.getElementById('plan-price').value = '';
    document.getElementById('plan-stripe-price-id').value = '';
    document.getElementById('plan-stripe-product-id').value = '';
    document.getElementById('plan-modal').style.display = 'flex';
}

async function editPlan(planId) {
    showLoading(true);
    const result = await apiRequest('/api/admin/plans');
    showLoading(false);
    
    if (result && result.status === 200) {
        const plan = result.data.find(p => p.id === planId);
        if (plan) {
            document.getElementById('plan-modal-title').textContent = 'Editar Plano';
            document.getElementById('plan-id').value = plan.id;
            document.getElementById('plan-name').value = plan.name;
            document.getElementById('plan-type').value = plan.type;
            document.getElementById('plan-validity-days').value = plan.validity_days || '';
            document.getElementById('plan-price').value = plan.price;
            document.getElementById('plan-stripe-price-id').value = plan.stripe_price_id || '';
            document.getElementById('plan-stripe-product-id').value = plan.stripe_product_id || '';
            document.getElementById('plan-modal').style.display = 'flex';
        }
    }
}

async function savePlan() {
    const planId = document.getElementById('plan-id').value;
    const data = {
        name: document.getElementById('plan-name').value,
        type: document.getElementById('plan-type').value,
        validity_days: document.getElementById('plan-validity-days').value ? parseInt(document.getElementById('plan-validity-days').value) : null,
        price: parseFloat(document.getElementById('plan-price').value),
        stripe_price_id: document.getElementById('plan-stripe-price-id').value || null,
        stripe_product_id: document.getElementById('plan-stripe-product-id').value || null
    };
    
    // Validação básica
    if (!data.name || !data.type || isNaN(data.price)) {
        showAlert('Preencha todos os campos obrigatórios', 'error');
        return;
    }
    
    showLoading(true);
    let result;
    if (planId) {
        result = await apiRequest(`/api/admin/plans/${planId}`, 'PUT', data);
    } else {
        result = await apiRequest('/api/admin/plans', 'POST', data);
    }
    showLoading(false);
    
    if (result && (result.status === 200 || result.status === 201)) {
        showAlert(`Plano ${planId ? 'atualizado' : 'criado'} com sucesso!`, 'success');
        closePlanModal();
        loadPlans();
    } else {
        showAlert(`Erro ao salvar plano: ${result?.data?.detail || 'Erro desconhecido'}`, 'error');
    }
}

async function deletePlan(planId) {
    if (!confirm('Tem certeza que deseja excluir este plano?')) return;
    
    showLoading(true);
    const result = await apiRequest(`/api/admin/plans/${planId}`, 'DELETE');
    showLoading(false);
    
    if (result && result.status === 200) {
        showAlert('Plano excluído com sucesso!', 'success');
        loadPlans();
    } else {
        showAlert('Erro ao excluir plano', 'error');
    }
}

function closePlanModal() {
    document.getElementById('plan-modal').style.display = 'none';
}

// ==================== LOGIN ====================

async function adminLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_URL}/api/admin/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        showLoading(false);
        
        if (response.status === 200 && data.access_token) {
            authToken = data.access_token;
            localStorage.setItem('admin_token', authToken);
            showAlert('Login realizado com sucesso!', 'success');
            window.location.href = '/admin/dashboard';
        } else {
            showAlert('Usuário ou senha incorretos', 'error');
        }
    } catch (error) {
        showLoading(false);
        showAlert('Erro de conexão com o servidor', 'error');
    }
}

function adminLogout() {
    localStorage.removeItem('admin_token');
    window.location.href = '/admin/login';
}

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    if (path.includes('/admin/dashboard')) {
        loadDashboard();
    } else if (path.includes('/admin/licenses')) {
        loadLicenses();
    } else if (path.includes('/admin/plans')) {
        loadPlans();
    }
    
    // Configurar modais
    const modal = document.getElementById('plan-modal');
    if (modal) {
        window.onclick = function(event) {
            if (event.target === modal) {
                closePlanModal();
            }
        };
    }
});