var Trades = {
    trades: [],
    currentTradeId: null,

    load: async function() {
        try {
            var params = new URLSearchParams();
            var symbol = document.getElementById('filter-symbol') ? document.getElementById('filter-symbol').value : '';
            var type = document.getElementById('filter-type') ? document.getElementById('filter-type').value : '';
            var status = document.getElementById('filter-status') ? document.getElementById('filter-status').value : '';
            if (symbol) params.set('symbol', symbol);
            if (type) params.set('type', type);
            if (status) params.set('status', status);

            var res = await fetch('/api/trades?' + params.toString());
            this.trades = await res.json();
            this.renderTable();
        } catch (err) {
            console.error('Failed to load trades:', err);
        }
    },

    renderTable: function() {
        var tbody = document.getElementById('tradesTableBody');
        if (!this.trades.length) {
            tbody.innerHTML = '<tr><td colspan="10" class="no-data">No trades yet. Click "+ New Trade" to add one.</td></tr>';
            return;
        }

        var self = this;
        tbody.innerHTML = this.trades.map(function(t) {
            return '<tr>' +
                '<td>' + self.formatDate(t.date) + '</td>' +
                '<td><strong>' + t.symbol + '</strong></td>' +
                '<td>' + t.asset_type + '</td>' +
                '<td class="side-' + t.side + '">' + t.side.charAt(0).toUpperCase() + t.side.slice(1) + '</td>' +
                '<td>' + self.formatPrice(t.entry_price) + '</td>' +
                '<td>' + (t.exit_price ? self.formatPrice(t.exit_price) : '\u2014') + '</td>' +
                '<td>' + t.quantity + '</td>' +
                '<td class="' + self.pnlClass(t.pnl) + '">' + (t.pnl !== null ? Stats.formatMoney(t.pnl) : '\u2014') + '</td>' +
                '<td>' + (t.strategy || '\u2014') + '</td>' +
                '<td>' +
                    '<button class="action-btn" onclick="Trades.viewDetail(' + t.id + ')" title="View">\u{1F441}</button> ' +
                    '<button class="action-btn" onclick="Trades.edit(' + t.id + ')" title="Edit">\u{270F}</button> ' +
                    '<button class="action-btn" onclick="Trades.remove(' + t.id + ')" title="Delete">\u{1F5D1}</button>' +
                '</td>' +
            '</tr>';
        }).join('');
    },

    openModal: function(trade) {
        var modal = document.getElementById('tradeModal');
        var title = document.getElementById('modalTitle');
        var form = document.getElementById('tradeForm');

        this.clearMoodButtons();

        if (trade) {
            title.textContent = 'Edit Trade';
            document.getElementById('tradeId').value = trade.id;
            document.getElementById('tradeDate').value = trade.date;
            document.getElementById('tradeSymbol').value = trade.symbol;
            document.getElementById('tradeType').value = trade.asset_type;
            document.getElementById('tradeSide').value = trade.side;
            document.getElementById('tradeEntry').value = trade.entry_price;
            document.getElementById('tradeExit').value = trade.exit_price || '';
            document.getElementById('tradeQty').value = trade.quantity;
            document.getElementById('tradeStrategy').value = trade.strategy || '';
            document.getElementById('tradeTags').value = trade.tags || '';
            document.getElementById('tradeNotes').value = trade.notes || '';
            document.getElementById('tradeTakeaway').value = trade.takeaway || '';
            document.getElementById('tradeEntryTime').value = trade.entry_time || '';
            document.getElementById('tradeExitTime').value = trade.exit_time || '';

            if (trade.entry_mood) this.setMoodButton('entry', trade.entry_mood);
            if (trade.hold_mood) this.setMoodButton('hold', trade.hold_mood);

            var qtyInput = document.getElementById('tradeQty');
            if (qtyInput) {
                qtyInput.removeAttribute('data-lot-size');
            }

            setTimeout(function() { FeeCalculator.calculate(); }, 300);
        } else {
            title.textContent = 'Add New Trade';
            form.reset();
            document.getElementById('tradeId').value = '';
            document.getElementById('tradeDate').value = new Date().toISOString().split('T')[0];

            var qtyInput = document.getElementById('tradeQty');
            if (qtyInput) {
                qtyInput.removeAttribute('data-lot-size');
            }
        }

        modal.classList.add('active');
    },

    closeModal: function() {
        document.getElementById('tradeModal').classList.remove('active');
        document.getElementById('tradeForm').reset();
        document.getElementById('tradeId').value = '';
        FeeCalculator.clearFeesDisplay();
        this.clearMoodButtons();

        var optionPanel = document.getElementById('optionChainPanel');
        if (optionPanel) optionPanel.classList.remove('active');

        var qtyInput = document.getElementById('tradeQty');
        if (qtyInput) qtyInput.removeAttribute('data-lot-size');
    },

    save: async function(e) {
        e.preventDefault();
        var id = document.getElementById('tradeId').value;
        var calculatedFees = FeeCalculator.getTotalFees();
        var lots = parseInt(document.getElementById('tradeQty').value) || 1;
        var lotSize = parseInt(document.getElementById('tradeQty').getAttribute('data-lot-size')) || 1;
        var actualQty = lots * lotSize;
        var data = {
            date: document.getElementById('tradeDate').value,
            symbol: document.getElementById('tradeSymbol').value.toUpperCase(),
            asset_type: document.getElementById('tradeType').value,
            side: document.getElementById('tradeSide').value,
            entry_price: document.getElementById('tradeEntry').value,
            exit_price: document.getElementById('tradeExit').value || null,
            quantity: actualQty,
            fees: calculatedFees,
            strategy: document.getElementById('tradeStrategy').value,
            tags: document.getElementById('tradeTags').value,
            notes: document.getElementById('tradeNotes').value,
            entry_mood: this.getSelectedMood('entry'),
            hold_mood: this.getSelectedMood('hold'),
            takeaway: document.getElementById('tradeTakeaway').value,
            entry_time: document.getElementById('tradeEntryTime').value,
            exit_time: document.getElementById('tradeExitTime').value
        };

        try {
            var url = id ? '/api/trades/' + id : '/api/trades';
            var method = id ? 'PUT' : 'POST';
            var res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                Trades.closeModal();
                await Trades.load();
                await Stats.load();
                Charts.render();
            }
        } catch (err) {
            console.error('Failed to save trade:', err);
        }
    },

    edit: function(id) {
        var trade = this.trades.find(function(t) { return t.id === id; });
        if (trade) this.openModal(trade);
    },

    remove: async function(id) {
        if (!confirm('Delete this trade?')) return;
        try {
            await fetch('/api/trades/' + id, { method: 'DELETE' });
            await Trades.load();
            await Stats.load();
            Charts.render();
        } catch (err) {
            console.error('Failed to delete trade:', err);
        }
    },

    viewDetail: function(id) {
        var trade = this.trades.find(function(t) { return t.id === id; });
        if (!trade) return;

        this.currentTradeId = id;
        var content = document.getElementById('detailContent');
        content.innerHTML =
            '<div class="detail-row"><span class="detail-label">Date</span><span class="detail-value">' + this.formatDate(trade.date) + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Symbol</span><span class="detail-value">' + trade.symbol + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">' + trade.asset_type + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Side</span><span class="detail-value side-' + trade.side + '">' + trade.side + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Entry Price</span><span class="detail-value">' + this.formatPrice(trade.entry_price) + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Exit Price</span><span class="detail-value">' + (trade.exit_price ? this.formatPrice(trade.exit_price) : 'Open') + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Quantity</span><span class="detail-value">' + trade.quantity + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Fees</span><span class="detail-value">' + this.formatPrice(trade.fees) + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">P&amp;L</span><span class="detail-value ' + this.pnlClass(trade.pnl) + '">' + (trade.pnl !== null ? Stats.formatMoney(trade.pnl) : '\u2014') + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Strategy</span><span class="detail-value">' + (trade.strategy || '\u2014') + '</span></div>' +
            '<div class="detail-row"><span class="detail-label">Tags</span><span class="detail-value">' + (trade.tags || '\u2014') + '</span></div>' +
            (trade.entry_mood ? '<div class="detail-row"><span class="detail-label">Entry Mood</span><span class="detail-value"><span class="mood-badge mood-' + trade.entry_mood + '">' + trade.entry_mood + '</span></span></div>' : '') +
            (trade.hold_mood ? '<div class="detail-row"><span class="detail-label">Hold Mood</span><span class="detail-value"><span class="mood-badge mood-' + trade.hold_mood + '">' + trade.hold_mood + '</span></span></div>' : '') +
            (trade.notes ? '<div class="detail-notes"><strong>Notes:</strong> ' + trade.notes + '</div>' : '') +
            (trade.takeaway ? '<div class="detail-notes"><strong>Takeaway:</strong> ' + trade.takeaway + '</div>' : '');

        document.getElementById('detailModal').classList.add('active');
    },

    closeDetail: function() {
        document.getElementById('detailModal').classList.remove('active');
        this.currentTradeId = null;
    },

    exportCsv: function() {
        window.location.href = '/api/export/csv';
    },

    importCsvData: null,

    triggerImport: function() {
        document.getElementById('csvFileInput').click();
    },

    previewImport: async function(file) {
        var formData = new FormData();
        formData.append('file', file);

        try {
            var res = await fetch('/api/import/csv', { method: 'POST', body: formData });
            var data = await res.json();

            if (!res.ok) {
                alert(data.error || 'Failed to parse CSV');
                return;
            }

            this.importCsvData = data.preview;
            this.renderImportPreview(data);
        } catch (err) {
            alert('Failed to read CSV file');
            console.error('Import preview failed:', err);
        }
    },

    renderImportPreview: function(data) {
        var tbody = document.getElementById('importTableBody');
        var summary = document.getElementById('importSummary');
        var errors = document.getElementById('importErrors');

        summary.textContent = data.preview.length + ' trade' + (data.preview.length !== 1 ? 's' : '') + ' ready to import';

        if (data.errors.length > 0) {
            errors.innerHTML = '<div class="import-error-header">' + data.errors.length + ' row(s) skipped:</div>' +
                data.errors.map(function(e) { return '<div class="import-error-item">' + e + '</div>'; }).join('');
            errors.style.display = 'block';
        } else {
            errors.innerHTML = '';
            errors.style.display = 'none';
        }

        var self = this;
        tbody.innerHTML = data.preview.map(function(t) {
            return '<tr>' +
                '<td>' + t.date + '</td>' +
                '<td><strong>' + t.symbol + '</strong></td>' +
                '<td>' + t.asset_type + '</td>' +
                '<td class="side-' + t.side + '">' + t.side.charAt(0).toUpperCase() + t.side.slice(1) + '</td>' +
                '<td>' + self.formatPrice(t.entry_price) + '</td>' +
                '<td>' + (t.exit_price ? self.formatPrice(t.exit_price) : '\u2014') + '</td>' +
                '<td>' + t.quantity + '</td>' +
                '<td class="' + self.pnlClass(t.pnl) + '">' + (t.pnl !== null ? Stats.formatMoney(t.pnl) : '\u2014') + '</td>' +
                '<td>' + (t.strategy || '\u2014') + '</td>' +
            '</tr>';
        }).join('');

        document.getElementById('importModal').classList.add('active');
    },

    confirmImport: async function() {
        if (!this.importCsvData || this.importCsvData.length === 0) return;

        try {
            var res = await fetch('/api/import/confirm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trades: this.importCsvData })
            });
            var data = await res.json();

            this.closeImportModal();
            await this.load();
            await Stats.load();
            Charts.render();

            alert('Imported ' + data.imported + ' trade' + (data.imported !== 1 ? 's' : '') + ' successfully');
        } catch (err) {
            alert('Failed to import trades');
            console.error('Import confirm failed:', err);
        }
    },

    closeImportModal: function() {
        document.getElementById('importModal').classList.remove('active');
        this.importCsvData = null;
    },

    pnlClass: function(pnl) {
        if (pnl === null || pnl === undefined) return '';
        return pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
    },

    formatDate: function(dateStr) {
        var d = new Date(dateStr + 'T00:00:00');
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },

    formatPrice: function(val) {
        return val !== null && val !== undefined ? '\u20B9' + Number(val).toFixed(2) : '\u2014';
    },

    getSelectedMood: function(group) {
        var container = group === 'entry' ? document.getElementById('entryMoodButtons') : document.getElementById('holdMoodButtons');
        if (!container) return '';
        var active = container.querySelector('.mood-btn.active');
        return active ? active.dataset.mood : '';
    },

    setMoodButton: function(group, mood) {
        var container = group === 'entry' ? document.getElementById('entryMoodButtons') : document.getElementById('holdMoodButtons');
        if (!container) return;
        var btn = container.querySelector('[data-mood="' + mood + '"]');
        if (btn) btn.classList.add('active');
    },

    clearMoodButtons: function() {
        document.querySelectorAll('.mood-btn').forEach(function(btn) { btn.classList.remove('active'); });
        var takeaway = document.getElementById('tradeTakeaway');
        if (takeaway) takeaway.value = '';
    }
};
