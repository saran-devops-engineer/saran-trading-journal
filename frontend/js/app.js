var App = {
    currentView: 'dashboard',
    deferredPrompt: null,

    init: function() {
        this.bindEvents();
        this.loadView('dashboard');
        this.registerSW();
        this.checkInstallPrompt();
        SymbolSearch.init();
        FeeCalculator.init();
    },

    bindEvents: function() {
        var self = this;

        document.querySelectorAll('.nav-link').forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                self.loadView(link.dataset.view);
            });
        });

        document.getElementById('addTradeBtn').addEventListener('click', function() { Trades.openModal(); });
        document.getElementById('tradeForm').addEventListener('submit', function(e) { Trades.save(e); });
        document.getElementById('modalClose').addEventListener('click', function() { Trades.closeModal(); });
        document.getElementById('modalCancel').addEventListener('click', function() { Trades.closeModal(); });
        document.getElementById('tradeModal').addEventListener('click', function(e) {
            if (e.target === e.currentTarget) Trades.closeModal();
        });

        document.querySelectorAll('.mood-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var group = btn.dataset.group;
                var container = group === 'entry' ? document.getElementById('entryMoodButtons') : document.getElementById('holdMoodButtons');
                container.querySelectorAll('.mood-btn').forEach(function(b) { b.classList.remove('active'); });
                btn.classList.add('active');
            });
        });

        document.getElementById('detailClose').addEventListener('click', function() { Trades.closeDetail(); });
        document.getElementById('detailModal').addEventListener('click', function(e) {
            if (e.target === e.currentTarget) Trades.closeDetail();
        });
        document.getElementById('detailEdit').addEventListener('click', function() {
            Trades.closeDetail();
            Trades.edit(Trades.currentTradeId);
        });
        document.getElementById('detailDelete').addEventListener('click', function() {
            Trades.closeDetail();
            Trades.remove(Trades.currentTradeId);
        });

        document.getElementById('exportCsvBtn').addEventListener('click', function() { Trades.exportCsv(); });

        document.getElementById('importCsvBtn').addEventListener('click', function() { Trades.triggerImport(); });
        document.getElementById('csvFileInput').addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                Trades.previewImport(e.target.files[0]);
                e.target.value = '';
            }
        });
        document.getElementById('importConfirm').addEventListener('click', function() { Trades.confirmImport(); });
        document.getElementById('importCancel').addEventListener('click', function() { Trades.closeImportModal(); });
        document.getElementById('importModalClose').addEventListener('click', function() { Trades.closeImportModal(); });
        document.getElementById('importModal').addEventListener('click', function(e) {
            if (e.target === e.currentTarget) Trades.closeImportModal();
        });

        document.getElementById('filter-symbol').addEventListener('input', function() { Trades.load(); });
        document.getElementById('filter-type').addEventListener('change', function() { Trades.load(); });
        document.getElementById('filter-status').addEventListener('change', function() { Trades.load(); });

        document.getElementById('logoutBtn').addEventListener('click', function() { Auth.logout(); });
        document.getElementById('saveDhanSettings').addEventListener('click', function() { App.saveDhanSettings(); });
        document.getElementById('testDhanConnection').addEventListener('click', function() { App.testDhanConnection(); });
        document.getElementById('renewDhanNow').addEventListener('click', function() { App.renewDhanNow(); });

        document.getElementById('mobileMenuBtn').addEventListener('click', function() {
            document.querySelector('.nav-links').classList.toggle('active');
        });

        var installBtn = document.getElementById('installBtn');
        var installDismiss = document.getElementById('installDismiss');
        if (installBtn) installBtn.addEventListener('click', function() { self.installApp(); });
        if (installDismiss) installDismiss.addEventListener('click', function() { self.dismissInstall(); });

        var closeOptionPanel = document.getElementById('closeOptionPanel');
        if (closeOptionPanel) {
            closeOptionPanel.addEventListener('click', function() {
                document.getElementById('optionChainPanel').classList.remove('active');
            });
        }
    },

    loadView: async function(view) {
        this.currentView = view;

        document.querySelectorAll('.view').forEach(function(v) { v.classList.remove('active'); });
        document.getElementById(view + '-view').classList.add('active');

        document.querySelectorAll('.nav-link').forEach(function(l) {
            l.classList.toggle('active', l.dataset.view === view);
        });

        var navLinks = document.querySelector('.nav-links');
        if (navLinks) navLinks.classList.remove('active');

        if (view === 'dashboard') {
            await Stats.load();
            Charts.render();
        } else if (view === 'trades') {
            await Trades.load();
        } else if (view === 'analytics') {
            await Stats.load();
            await Analytics.load();
        } else if (view === 'settings') {
            App.loadSettings();
        }
    },

    registerSW: async function() {
        if ('serviceWorker' in navigator) {
            try {
                await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered');
            } catch (err) {
                console.log('SW registration failed:', err);
            }
        }
    },

    checkInstallPrompt: function() {
        var self = this;
        window.addEventListener('beforeinstallprompt', function(e) {
            e.preventDefault();
            self.deferredPrompt = e;
            var banner = document.getElementById('installBanner');
            if (banner) banner.classList.remove('hidden');
        });
    },

    installApp: async function() {
        if (!this.deferredPrompt) return;
        this.deferredPrompt.prompt();
        await this.deferredPrompt.userChoice;
        this.deferredPrompt = null;
        var banner = document.getElementById('installBanner');
        if (banner) banner.classList.add('hidden');
    },

    dismissInstall: function() {
        var banner = document.getElementById('installBanner');
        if (banner) banner.classList.add('hidden');
    },

    loadSettings: async function() {
        try {
            var res = await fetch('/api/settings', { credentials: 'include' });
            if (res.status === 401) {
                Auth.showLogin();
                return;
            }
            var data = await res.json();
            document.getElementById('dhanClientId').value = data.dhan_client_id || '';
            var statusEl = document.getElementById('dhanTokenStatus');
            var renewInfo = document.getElementById('dhanRenewInfo');
            if (data.has_dhan_token) {
                statusEl.textContent = 'Token configured';
                statusEl.className = 'token-status valid';
            } else {
                statusEl.textContent = 'No token configured';
                statusEl.className = 'token-status invalid';
            }
            if (data.dhan_token_renewed_at) {
                var d = new Date(data.dhan_token_renewed_at);
                var hoursAgo = Math.round((Date.now() - d.getTime()) / 3600000);
                renewInfo.textContent = 'Last renewed: ' + d.toLocaleString() + ' (' + hoursAgo + 'h ago)';
                if (hoursAgo >= 24) {
                    renewInfo.textContent += ' - Token may be expired, click Test Connection to check';
                    renewInfo.style.color = '#f87171';
                } else {
                    renewInfo.style.color = '#888';
                }
            } else {
                renewInfo.textContent = 'Auto-renewal runs every 23 hours';
                renewInfo.style.color = '#888';
            }
        } catch (err) {
            console.error('Failed to load settings');
        }
    },

    saveDhanSettings: async function() {
        var clientId = document.getElementById('dhanClientId').value.trim();
        var token = document.getElementById('dhanToken').value.trim();
        var data = {};
        if (clientId) data.dhan_client_id = clientId;
        if (token) data.dhan_access_token = token;

        if (Object.keys(data).length === 0) {
            alert('Enter Client ID or Access Token first');
            return;
        }

        try {
            var res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(data)
            });
            var result = await res.json();
            if (res.ok) {
                document.getElementById('dhanToken').value = '';
                App.loadSettings();
                alert('Settings saved');
            } else if (res.status === 401) {
                Auth.showLogin();
            } else {
                alert(result.error || 'Failed to save settings');
            }
        } catch (err) {
            alert('Failed to save settings - is the server running?');
        }
    },

    testDhanConnection: async function() {
        var resultEl = document.getElementById('dhanTestResult');
        resultEl.textContent = 'Testing...';
        resultEl.style.color = '#aaa';
        try {
            var res = await fetch('/api/settings/test-dhan', {
                method: 'POST',
                credentials: 'include'
            });
            var data = await res.json();
            if (data.ok) {
                resultEl.textContent = 'Connected';
                resultEl.style.color = '#4ade80';
            } else {
                var msg = data.error || 'Connection failed';
                if (msg.indexOf('expired') !== -1 || msg.indexOf('Invalid') !== -1) {
                    msg += ' - Generate new token from Dhan website and save it here';
                }
                resultEl.textContent = msg;
                resultEl.style.color = '#f87171';
            }
        } catch (err) {
            resultEl.textContent = 'Server unreachable';
            resultEl.style.color = '#f87171';
        }
    },

    renewDhanNow: async function() {
        var resultEl = document.getElementById('dhanTestResult');
        resultEl.textContent = 'Renewing token...';
        resultEl.style.color = '#aaa';
        try {
            var res = await fetch('/api/settings/renew-dhan', {
                method: 'POST',
                credentials: 'include'
            });
            var data = await res.json();
            if (data.ok) {
                resultEl.textContent = 'Token renewed successfully';
                resultEl.style.color = '#4ade80';
                App.loadSettings();
            } else {
                resultEl.textContent = data.error || 'Renewal failed';
                resultEl.style.color = '#f87171';
            }
        } catch (err) {
            resultEl.textContent = 'Server unreachable';
            resultEl.style.color = '#f87171';
        }
    }
};

document.addEventListener('DOMContentLoaded', function() { App.init(); });
