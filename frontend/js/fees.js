var FeeCalculator = {
    currentFees: null,
    debounceTimer: null,
    isOpen: false,

    init: function() {
        this.bindEvents();
    },

    bindEvents: function() {
        var self = this;

        var entryInput = document.getElementById('tradeEntry');
        var exitInput = document.getElementById('tradeExit');
        var typeSelect = document.getElementById('tradeType');
        var sideSelect = document.getElementById('tradeSide');
        var qtyInput = document.getElementById('tradeQty');

        if (entryInput) {
            entryInput.addEventListener('input', function() { self.scheduleCalculation(); });
            entryInput.addEventListener('change', function() { self.scheduleCalculation(); });
        }
        if (exitInput) {
            exitInput.addEventListener('input', function() { self.scheduleCalculation(); });
            exitInput.addEventListener('change', function() { self.scheduleCalculation(); });
        }
        if (typeSelect) {
            typeSelect.addEventListener('change', function() { self.scheduleCalculation(); });
        }
        if (sideSelect) {
            sideSelect.addEventListener('change', function() { self.scheduleCalculation(); });
        }
        if (qtyInput) {
            qtyInput.addEventListener('input', function() { self.scheduleCalculation(); });
            qtyInput.addEventListener('change', function() { self.scheduleCalculation(); });
        }

        var toggleBtn = document.getElementById('toggleCharges');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() { self.toggleBreakdown(); });
        }
    },

    toggleBreakdown: function() {
        var panel = document.getElementById('chargesBreakdown');
        var btn = document.getElementById('toggleCharges');
        if (!panel || !btn) return;

        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            panel.classList.add('active');
            btn.textContent = 'Hide Breakdown';
        } else {
            panel.classList.remove('active');
            btn.textContent = 'View Breakdown';
        }
    },

    scheduleCalculation: function() {
        var self = this;
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(function() {
            self.calculate();
        }, 150);
    },

    calculate: async function() {
        var entryVal = document.getElementById('tradeEntry').value;
        var exitVal = document.getElementById('tradeExit').value;
        var lotsVal = document.getElementById('tradeQty').value;
        var type = document.getElementById('tradeType').value;
        var side = document.getElementById('tradeSide').value;

        var lotSize = 1;
        var qtyEl = document.getElementById('tradeQty');
        if (qtyEl) {
            lotSize = parseInt(qtyEl.getAttribute('data-lot-size')) || 1;
        }

        var lots = parseInt(lotsVal) || 0;
        var qty = lots * lotSize;

        if (!entryVal || lots <= 0 || parseFloat(entryVal) <= 0) {
            this.clearFees();
            return;
        }

        try {
            var res = await fetch('/api/fees/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    asset_type: type,
                    side: side,
                    entry_price: entryVal,
                    exit_price: exitVal || null,
                    quantity: qty,
                    exchange: 'NSE'
                })
            });

            var fees = await res.json();
            this.currentFees = fees;
            this.updateDisplay(fees);
        } catch (err) {
            console.error('Fee calculation failed:', err);
        }
    },

    updateDisplay: function(fees) {
        var chargesValue = document.getElementById('chargesValue');
        if (chargesValue) {
            chargesValue.textContent = '\u20B9' + fees.total_fees.toFixed(2);
        }

        var grid = document.getElementById('chargesGrid');
        var total = document.getElementById('chargesTotal');
        var pnl = document.getElementById('pnlSummary');

        if (grid) {
            grid.innerHTML =
                this.feeRow('Brokerage', fees.brokerage) +
                this.feeRow('STT', fees.stt) +
                this.feeRow('Exchange Charges', fees.exchange_charges) +
                this.feeRow('SEBI Charges', fees.sebi_charges) +
                this.feeRow('Stamp Duty', fees.stamp_duty) +
                this.feeRow('IPFT', fees.ipft) +
                this.feeRow('GST (18%)', fees.gst);
        }

        if (total) {
            total.innerHTML = '<span>Total Charges</span><span class="total-amount">\u20B9' + fees.total_fees.toFixed(2) + '</span>';
        }

        if (pnl && (fees.pnl_before_fees !== 0 || fees.pnl_after_fees !== 0)) {
            pnl.innerHTML =
                '<div class="pnl-row"><span>P&L (before fees)</span><span class="' + (fees.pnl_before_fees >= 0 ? 'positive' : 'negative') + '">\u20B9' + fees.pnl_before_fees.toFixed(2) + '</span></div>' +
                '<div class="pnl-row"><span>Net P&L (after fees)</span><span class="' + (fees.pnl_after_fees >= 0 ? 'positive' : 'negative') + '">\u20B9' + fees.pnl_after_fees.toFixed(2) + '</span></div>';
        }
    },

    feeRow: function(label, value) {
        return '<div class="fee-row"><span>' + label + '</span><span>\u20B9' + value.toFixed(2) + '</span></div>';
    },

    clearFees: function() {
        var chargesValue = document.getElementById('chargesValue');
        if (chargesValue) chargesValue.textContent = '\u20B90.00';

        var grid = document.getElementById('chargesGrid');
        var total = document.getElementById('chargesTotal');
        var pnl = document.getElementById('pnlSummary');

        if (grid) grid.innerHTML = '';
        if (total) total.innerHTML = '';
        if (pnl) pnl.innerHTML = '';

        this.currentFees = null;
    },

    getFees: function() {
        return this.currentFees;
    },

    getTotalFees: function() {
        return this.currentFees ? this.currentFees.total_fees : 0;
    }
};
