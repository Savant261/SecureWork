const API_BASE = 'https://securework-api.onrender.com';

const AppUtils = {
    renderUI() {
        const role = localStorage.getItem('securework_role') || 'client';
        document.querySelectorAll('[data-role]').forEach(el => {
            if (el.getAttribute('data-role') !== role) {
                el.classList.add('hidden');
            } else {
                el.classList.remove('hidden');
            }
        });
    },

    async apiCall(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${AuthService.getToken()}`
        };
        
        const options = { method, headers };
        if (body) options.body = JSON.stringify(body);

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (response.status === 401) {
            AuthService.logout();
            return null;
        }

        const data = await response.json();

        if(!response.ok){
            throw new Error(data.error || 'Server Request Failed');
        }

        return data;
    }
};

// ==========================================
// 2. DASHBOARD LOGIC & NEW TOOLTIPS
// ==========================================

const DashboardApp = {
    financeChart: null,

    async init() {
        await this.loadUserInfo();
        await this.initFinanceChart();
        await this.loadContracts();
        await this.loadStats();
    },

    async loadUserInfo() {
        const user = AuthService.getUser();
        if (user) {
            const userNameEl = document.getElementById('userName');
            const userRoleEl = document.getElementById('userRole');
            const userAvatarEl = document.getElementById('userAvatar');

            if (userNameEl) userNameEl.textContent = user.name;
            if (userRoleEl) {
                userRoleEl.textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
            }
            if (userAvatarEl) {
                const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase();
                userAvatarEl.textContent = initials;
            }
        }
    },

    async initFinanceChart() {
        const ctx = document.getElementById('financeChart');
        if (!ctx) return;

        try {
            const response = await AppUtils.apiCall('/stats/', 'GET');
            const currentTotal = response ? response.totalValue : 0;

            const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const labels = [];
            const d = new Date();
            for (let i = 5; i >= 0; i--) {
                const pastDate = new Date(d.getFullYear(), d.getMonth() - i, 1);
                labels.push(monthNames[pastDate.getMonth()]);
            }

            let values = currentTotal > 0 ? [currentTotal * 0.15, currentTotal * 0.32, currentTotal * 0.45, currentTotal * 0.60, currentTotal * 0.85, currentTotal] : [0, 0, 0, 0, 0, 0];
            this.renderChart({ labels: labels, values: values });
        } catch (error) {
            this.renderChart({ labels: ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'], values: [0, 0, 0, 0, 0, 0] });
        }
    },

    renderChart(data) {
        const ctx = document.getElementById('financeChart');
        if (!ctx) return;

        if (this.financeChart) {
            this.financeChart.destroy();
        }

        const ctx2d = ctx.getContext('2d');
        const gradient = ctx2d.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)'); 
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)'); 

        this.financeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Contract Value',
                    data: data.values,
                    borderColor: '#34d399', 
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointBackgroundColor: '#064e3b', 
                    pointBorderColor: '#34d399', 
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#10b981',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    // NEW, UPGRADED TOOLTIPS HERE
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)', 
                        titleColor: '#34d399', // Emerald color for the month
                        bodyColor: '#f8fafc',
                        borderColor: 'rgba(51, 65, 85, 0.8)', 
                        borderWidth: 1,
                        padding: 14,
                        displayColors: false,
                        titleFont: { family: 'Space Grotesk', size: 14, weight: 'bold' },
                        bodyFont: { family: 'JetBrains Mono', size: 13 },
                        callbacks: {
                            title: function(tooltipItems) {
                                return 'Period: ' + tooltipItems[0].label;
                            },
                            label: function(context) { 
                                return 'Secured Capital: $' + context.parsed.y.toLocaleString('en-US', {minimumFractionDigits: 2}); 
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#64748b', 
                            callback: function(value) { return '$' + (value / 1000) + 'K'; },
                            font: { family: 'JetBrains Mono, monospace' }
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        border: { display: false }
                    },
                    x: {
                        ticks: { 
                            color: '#64748b',
                            font: { family: 'Inter' }
                        },
                        grid: { display: false },
                        border: { display: false }
                    }
                }
            }
        });
    },

    async loadContracts() {
        const tableBody = document.getElementById('contractsTable');
        if (!tableBody) return;

        try {
            const contracts = await AppUtils.apiCall('/contracts/', 'GET');
            if (contracts) {
                this.renderContracts(contracts);
            }
        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="7" class="px-6 py-4 text-center text-slate-500">Failed to load contracts.</td></tr>`;
        }
    },

    renderContracts(contracts) {
        const tableBody = document.getElementById('contractsTable');
        if (!tableBody) return;

        if (contracts.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" class="px-8 py-12 text-center text-slate-500 font-medium">No active infrastructure found.</td></tr>`;
            return;
        }

        tableBody.innerHTML = contracts.map(contract => {
            const numericHash = contract.id.replace(/\D/g, '');
            const shortId = numericHash ? numericHash.substring(0, 3).padStart(3, '0') : '000';

            const totalMilestones = contract.milestones ? contract.milestones.length : 0;
            const approvedMilestones = contract.milestones ? contract.milestones.filter(m => m.status === 'approved').length : 0;
            const progress = totalMilestones === 0 ? 0 : Math.round((approvedMilestones / totalMilestones) * 100);

            let statusClass = 'bg-slate-800 text-slate-400 border-slate-700'; 
            let statusText = contract.status.charAt(0).toUpperCase() + contract.status.slice(1);
            
            if (contract.status === 'completed') statusClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
            if (contract.status === 'active') statusClass = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
            if (contract.status === 'published') statusClass = 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';

            const budgetVal = parseFloat(contract.total_budget || 0);

            return `
                <tr class="hover:bg-slate-800/30 transition-colors border-b border-slate-800/50 last:border-0 group">
                    <td class="px-8 py-5">
                        <span class="font-mono text-sm font-semibold text-slate-500 group-hover:text-emerald-400 transition-colors">#SW-${shortId}</span>
                    </td>
                    <td class="px-8 py-5">
                        <span class="font-medium text-white">${contract.title}</span>
                    </td>
                    <td class="px-8 py-5">
                        <div class="flex items-center space-x-2">
                            <div class="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-400">
                                ${contract.counterpart_name.charAt(0).toUpperCase()}
                            </div>
                            <span class="text-slate-400 text-sm">${contract.counterpart_name}</span>
                        </div>
                    </td>
                    <td class="px-8 py-5">
                        <span class="font-mono font-bold text-white tracking-tight">$${budgetVal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </td>
                    <td class="px-8 py-5">
                        <div class="w-full bg-slate-800 rounded-full h-1.5 mb-2 overflow-hidden">
                            <div class="bg-gradient-to-r from-emerald-500 to-cyan-500 h-1.5 rounded-full relative" style="width: ${progress}%">
                                <div class="absolute inset-0 bg-white/20"></div>
                            </div>
                        </div>
                        <span class="text-xs text-slate-500 font-medium tracking-wide">${progress}% Resolved</span>
                    </td>
                    <td class="px-8 py-5">
                        <span class="px-3 py-1 text-xs font-bold rounded-full border ${statusClass} tracking-wide">
                            ${statusText}
                        </span>
                    </td>
                    <td class="px-8 py-5">
                        <a href="contract-detail.html?id=${contract.id}" class="inline-flex px-4 py-2 text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-lg font-bold text-sm transition-all border border-emerald-500/20 hover:border-emerald-500/40 hover:-translate-y-0.5 shadow-lg shadow-transparent hover:shadow-emerald-500/10">
                            Inspect
                        </a>
                    </td>
                </tr>
            `;
        }).join('');
    },

    async loadStats() {
        try {
            const stats = await AppUtils.apiCall('/stats/', 'GET');
            if (stats) {
                this.updateStats(stats);
            }
        } catch (error) {
            this.updateStats({ totalValue: 0, escrowBalance: 0, actionCount: 0 });
        }
    },

    updateStats(stats) {
        const totalValueEl = document.getElementById('totalValue');
        const escrowBalanceEl = document.getElementById('escrowBalance');
        const actionCountEl = document.getElementById('actionCount');

        if (totalValueEl) totalValueEl.textContent = `$${stats.totalValue.toLocaleString()}.00`;
        if (escrowBalanceEl) escrowBalanceEl.textContent = `$${stats.escrowBalance.toLocaleString()}.00`;
        if (actionCountEl) actionCountEl.textContent = stats.actionCount;
    }
};

// ==========================================
// 3. WALLET & FINANCIAL TRANSACTIONS
// ==========================================

const WalletApp = {
    async init() {
        await this.loadBalances();
        await this.loadTransactions();
    },

    async loadBalances() {
        try {
            const walletData = await AppUtils.apiCall('/wallet/', 'GET');
            if (walletData) {
                const availableEl = document.getElementById('availableBalanceAmount');
                const escrowEl = document.getElementById('escrowBalanceAmount');

                if (availableEl) availableEl.textContent = `$${parseFloat(walletData.balance).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                if (escrowEl) escrowEl.textContent = `$${parseFloat(walletData.escrow_balance).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
            }
        } catch (error) {
            console.error("Error loading wallet balances:", error);
        }
    },

    async loadTransactions() {
        const tableBody = document.getElementById('ledgerTable');
        if (!tableBody) return;

        try {
            const transactions = await AppUtils.apiCall('/wallet/transactions/', 'GET');
            
            if (transactions && transactions.length > 0) {
                this.renderTransactions(transactions);
            } else {
                tableBody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-slate-500 font-medium">No transactions found in ledger.</td></tr>`;
            }
        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="5" class="px-6 py-4 text-center text-red-500">Failed to load transactions.</td></tr>`;
        }
    },

    renderTransactions(transactions) {
        const tableBody = document.getElementById('ledgerTable');
        if (!tableBody) return;

        const rowsHtml = transactions.map(tx => {
            const amountVal = parseFloat(tx.amount);
            const isPositive = amountVal > 0;
            const isNegative = amountVal < 0;
            
            let amountClass = isPositive ? 'text-emerald-400' : isNegative ? 'text-rose-400' : 'text-slate-500';
            let amountSign = isPositive ? '+' : '';

            let typeBadgeClass = 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
            let typeName = tx.transaction_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

            if (tx.transaction_type === 'escrow_lock') typeBadgeClass = 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
            if (tx.transaction_type === 'escrow_release') typeBadgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
            if (tx.transaction_type === 'deposit') typeBadgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
            if (tx.transaction_type === 'withdraw') typeBadgeClass = 'bg-rose-500/10 text-rose-400 border border-rose-500/20';

            const txDate = new Date(tx.timestamp);
            const dateStr = txDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const timeStr = txDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });

            return `
                <tr class="hover:bg-slate-800/40 transition-colors border-b border-slate-800/50 last:border-0 group">
                    <td class="px-8 py-5">
                        <span class="font-mono text-sm font-semibold text-slate-500 group-hover:text-emerald-400 transition-colors">#${tx.id.substring(0,8)}</span>
                    </td>
                    <td class="px-8 py-5">
                        <div class="text-sm font-bold text-white mb-0.5">${dateStr}</div>
                        <div class="text-xs font-mono text-slate-500">${timeStr}</div>
                    </td>
                    <td class="px-8 py-5">
                        <span class="text-sm font-medium text-slate-300">${tx.description || typeName}</span>
                    </td>
                    <td class="px-8 py-5">
                        <span class="px-3 py-1 ${typeBadgeClass} rounded-full text-xs font-bold whitespace-nowrap tracking-wide">
                            ${typeName}
                        </span>
                    </td>
                    <td class="px-8 py-5 text-right">
                        <span class="text-lg font-mono font-bold ${amountClass} tracking-tight">
                            ${amountVal !== 0 ? `${amountSign}$${Math.abs(amountVal).toLocaleString('en-US', {minimumFractionDigits: 2})}` : '—'}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');

        tableBody.innerHTML = rowsHtml;
    }
};

const WalletActions = {
    depositFunds() { UIActions.toggleModal('depositModal'); },
    withdrawFunds() { UIActions.toggleModal('withdrawModal'); }
};

// ==========================================
// 4. PROPOSAL & WORKFLOW ACTIONS
// ==========================================

const ProposalActions = {
    async submitProposal(contractId, coverLetter, milestonesArray) {
        const payload = {
            contract: contractId,
            cover_letter: coverLetter,
            proposed_milestones: milestonesArray 
        };
        try {
            const result = await AppUtils.apiCall('/applications/', 'POST', payload);
            ToastService.show("Proposal transmitted to the network successfully.", "success");
            return result;
        } catch (err) {
            ToastService.show("Transmission failed. Verify proposal parameters.", "error");
            throw err;
        }
    },

    async acceptProposal(applicationId) {
        try {
            const result = await AppUtils.apiCall(`/applications/${applicationId}/accept/`, 'POST');
            if (result && result.id) {
                ToastService.show("Freelancer hired! Smart contract initialized.", "success");
                setTimeout(() => window.location.reload(), 1500); 
            }
        } catch (err) {
            ToastService.show("Hiring failed. Ensure your account is authorized.", "error");
        }
    },

    async fundMilestone(milestoneId) {
        return await AppUtils.apiCall(`/milestones/${milestoneId}/fund/`, 'POST');
    },

    async submitWork(milestoneId, submissionUrl) {
        return await AppUtils.apiCall(`/milestones/${milestoneId}/submit/`, 'POST', { submission_url: submissionUrl });
    }
};

// ==========================================
// 5. TOAST NOTIFICATION ENGINE
// ==========================================

const ToastService = {
    container: null,

    init() {
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed bottom-6 right-6 z-50 flex flex-col gap-4 items-end pointer-events-none';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    },

    show(message, type = 'success') {
        if (!this.container) this.init();

        let bgClass = 'bg-slate-900/90';
        let borderClass = 'border-slate-700/50';
        let iconHtml = '';
        let glowClass = '';

        if (type === 'success') {
            borderClass = 'border-emerald-500/50';
            glowClass = 'shadow-[0_0_20px_rgba(16,185,129,0.2)]';
            iconHtml = `<div class="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                        </div>`;
        } else if (type === 'error') {
            borderClass = 'border-rose-500/50';
            glowClass = 'shadow-[0_0_20px_rgba(244,63,94,0.2)]';
            iconHtml = `<div class="w-8 h-8 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                        </div>`;
        } else {
            borderClass = 'border-blue-500/50';
            glowClass = 'shadow-[0_0_20px_rgba(59,130,246,0.2)]';
            iconHtml = `<div class="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </div>`;
        }

        const toast = document.createElement('div');
        toast.className = `flex items-center p-4 rounded-2xl border backdrop-blur-xl ${bgClass} ${borderClass} ${glowClass} transform transition-all duration-300 translate-y-10 opacity-0 min-w-[300px] max-w-md`;
        
        toast.innerHTML = `
            ${iconHtml}
            <div class="ml-4 flex-1">
                <p class="text-sm font-bold text-white">${message}</p>
            </div>
        `;

        this.container.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('translate-y-10', 'opacity-0');
            toast.classList.add('translate-y-0', 'opacity-100');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('translate-y-0', 'opacity-100');
            toast.classList.add('translate-y-10', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
};

// ==========================================
// 6. INITIALIZATION & EVENT LISTENERS
// ==========================================

const UIActions = {
    initTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                tabBtns.forEach(b => b.classList.remove('border-emerald-500', 'text-emerald-400'));
                tabBtns.forEach(b => b.classList.add('border-transparent', 'text-slate-500'));
                tabContents.forEach(c => c.classList.add('hidden'));
                
                e.currentTarget.classList.remove('border-transparent', 'text-slate-500');
                e.currentTarget.classList.add('border-emerald-500', 'text-emerald-400');
                
                const targetId = e.currentTarget.getAttribute('data-target');
                document.getElementById(targetId).classList.remove('hidden');
            });
        });
    },
    toggleModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.toggle('hidden');
    }
};

window.addEventListener('DOMContentLoaded', () => {
    AppUtils.renderUI();
    UIActions.initTabs();
    ToastService.init();

    const currentPath = window.location.pathname;
    
    // ContractDetailApp has been removed entirely to fix the canvas collision!
    if (currentPath.includes('dashboard.html')) {
        DashboardApp.init();
    } else if (currentPath.includes('wallet.html')) {
        WalletApp.init();
    }

    // Modal Forms Initialization with CORRECT error Toast flags
    const depositForm = document.getElementById('depositForm');
    const withdrawForm = document.getElementById('withdrawForm');

    if (depositForm) {
        depositForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const amount = document.getElementById('depositAmount').value;
            
            try {
                await AppUtils.apiCall('/wallet/deposit/', 'POST', { amount: parseFloat(amount) });
                UIActions.toggleModal('depositModal');
                e.target.reset();
                ToastService.show(`$${parseFloat(amount).toLocaleString()} injected into liquid balance.`, "success");
                await WalletApp.init(); 
            } catch (err) {
                // Fixed: Added "error" parameter
                ToastService.show("Deposit failed. Please try again.", "error");
            }
        });
    }

    if (withdrawForm) {
        withdrawForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const amount = document.getElementById('withdrawAmount').value;
            
            try {
                const result = await AppUtils.apiCall('/wallet/withdraw/', 'POST', { amount: parseFloat(amount) });
                if (result) {
                    UIActions.toggleModal('withdrawModal');
                    e.target.reset();
                    ToastService.show(`$${parseFloat(amount).toLocaleString()} successfully withdrawn to bank.`, "success");
                    await WalletApp.init(); 
                }
            } catch (err) {
                // Fixed: Added "error" parameter
                ToastService.show("Withdrawal rejected. Check your available balance.", "error");
            }
        });
    }
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DashboardApp, WalletApp };

}
