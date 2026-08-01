var SymbolSearch = {
    symbols: [],
    selectedSymbol: null,
    selectedLotSize: 1,
    debounceTimer: null,
    isOpen: false,

    init: function() {
        this.bindEvents();
        this.loadSymbols();
    },

    bindEvents: function() {
        var self = this;
        var input = document.getElementById('tradeSymbol');
        var dropdown = document.getElementById('symbolDropdown');

        if (input) {
            input.addEventListener('input', function() {
                self.selectedSymbol = null;
                self.selectedLotSize = 1;
                self.updateLotInfo(1);
                clearTimeout(self.debounceTimer);
                self.debounceTimer = setTimeout(function() {
                    self.search(input.value);
                }, 200);
            });

            input.addEventListener('focus', function() {
                if (input.value.length === 0) {
                    self.showPopular();
                }
                self.isOpen = true;
                if (dropdown) dropdown.classList.add('active');
            });

            input.addEventListener('blur', function() {
                setTimeout(function() {
                    self.isOpen = false;
                    if (dropdown) dropdown.classList.remove('active');
                }, 200);
            });
        }

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.symbol-search-wrapper')) {
                self.isOpen = false;
                if (dropdown) dropdown.classList.remove('active');
            }
        });
    },

    loadSymbols: async function() {
        try {
            var res = await fetch('/api/symbols/all');
            this.symbols = await res.json();
        } catch (err) {
            console.error('Failed to load symbols:', err);
        }
    },

    search: async function(query) {
        var dropdown = document.getElementById('symbolDropdown');
        if (!dropdown) return;

        if (!query || query.length < 1) {
            this.showPopular();
            return;
        }

        try {
            var res = await fetch('/api/symbols/search?q=' + encodeURIComponent(query));
            var results = await res.json();
            this.renderResults(results);
        } catch (err) {
            console.error('Search failed:', err);
        }
    },

    showPopular: function() {
        var popular = [
            { symbol: 'NIFTY50', name: 'Nifty 50', type: 'index', lot_size: 65 },
            { symbol: 'SENSEX', name: 'BSE Sensex', type: 'index', lot_size: 10 },
            { symbol: 'BANKNIFTY', name: 'Bank Nifty', type: 'index', lot_size: 30 },
            { symbol: 'RELIANCE', name: 'Reliance Industries', type: 'stock', sector: 'Oil & Gas' },
            { symbol: 'TCS', name: 'Tata Consultancy Services', type: 'stock', sector: 'IT' },
            { symbol: 'HDFCBANK', name: 'HDFC Bank', type: 'stock', sector: 'Banking' },
            { symbol: 'INFY', name: 'Infosys', type: 'stock', sector: 'IT' },
            { symbol: 'SBIN', name: 'State Bank of India', type: 'stock', sector: 'Banking' },
        ];
        this.renderResults(popular, true);
    },

    renderResults: function(results, isPopular) {
        var dropdown = document.getElementById('symbolDropdown');
        if (!dropdown) return;

        if (results.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-empty">No symbols found</div>';
            dropdown.classList.add('active');
            return;
        }

        var html = '';
        if (isPopular) {
            html += '<div class="dropdown-header">Popular Symbols</div>';
        }

        var indices = results.filter(function(r) { return r.type === 'index'; });
        var stocks = results.filter(function(r) { return r.type === 'stock'; });

        if (indices.length > 0) {
            html += '<div class="dropdown-section">Indices</div>';
            indices.forEach(function(item) {
                html += '<div class="dropdown-item" data-symbol="' + item.symbol + '" data-type="index" data-name="' + item.name + '" data-lot="' + (item.lot_size || 50) + '">';
                html += '<span class="item-symbol">' + item.symbol + '</span>';
                html += '<span class="item-name">' + item.name + '</span>';
                html += '<span class="item-badge badge-index">' + (item.lot_size || 50) + ' Lot</span>';
                html += '</div>';
            });
        }

        if (stocks.length > 0) {
            html += '<div class="dropdown-section">Stocks</div>';
            stocks.forEach(function(item) {
                html += '<div class="dropdown-item" data-symbol="' + item.symbol + '" data-type="stock" data-name="' + item.name + '" data-lot="1">';
                html += '<span class="item-symbol">' + item.symbol + '</span>';
                html += '<span class="item-name">' + item.name + '</span>';
                if (item.sector) {
                    html += '<span class="item-sector">' + item.sector + '</span>';
                }
                html += '</div>';
            });
        }

        dropdown.innerHTML = html;
        dropdown.classList.add('active');

        var self = this;
        dropdown.querySelectorAll('.dropdown-item').forEach(function(item) {
            item.addEventListener('click', function() {
                self.selectSymbol({
                    symbol: item.dataset.symbol,
                    type: item.dataset.type,
                    name: item.dataset.name,
                    lot_size: parseInt(item.dataset.lot) || 1
                });
            });
        });
    },

    selectSymbol: function(symbolData) {
        this.selectedSymbol = symbolData;
        this.selectedLotSize = symbolData.lot_size || 1;

        var input = document.getElementById('tradeSymbol');
        var dropdown = document.getElementById('symbolDropdown');
        var typeSelect = document.getElementById('tradeType');
        var optionPanel = document.getElementById('optionChainPanel');
        var qtyInput = document.getElementById('tradeQty');

        if (input) {
            input.value = symbolData.symbol;
        }

        if (dropdown) {
            dropdown.classList.remove('active');
        }

        if (typeSelect) {
            if (symbolData.type === 'index') {
                typeSelect.value = 'option';
            }
        }

        if (qtyInput) {
            qtyInput.value = '1';
            qtyInput.setAttribute('data-lot-size', String(this.selectedLotSize));
            qtyInput.setAttribute('min', '1');
            qtyInput.setAttribute('step', '1');
        }

        this.updateLotInfo(this.selectedLotSize);

        if (optionPanel) {
            if (symbolData.type === 'index') {
                this.loadOptionChain(symbolData.symbol);
                optionPanel.classList.add('active');
            } else {
                optionPanel.classList.remove('active');
            }
        }

        FeeCalculator.scheduleCalculation();
    },

    updateLotInfo: function(lotSize) {
        var lotInfo = document.getElementById('lotInfo');
        var qtyInput = document.getElementById('tradeQty');
        if (lotInfo) {
            if (lotSize > 1) {
                lotInfo.textContent = '1 Lot = ' + lotSize + ' qty';
            } else {
                lotInfo.textContent = '';
            }
        }
        if (qtyInput) {
            qtyInput.setAttribute('data-lot-size', lotSize);
        }
    },

    loadOptionChain: async function(symbol) {
        var panel = document.getElementById('optionChainContent');
        if (!panel) return;

        panel.innerHTML = '<div class="loading">Loading option chain...</div>';

        try {
            var res = await fetch('/api/options/chain?symbol=' + encodeURIComponent(symbol));
            var chain = await res.json();

            if (chain.error) {
                panel.innerHTML = '<div class="error">' + chain.error + '</div>';
                return;
            }

            this.renderOptionChain(chain);
        } catch (err) {
            panel.innerHTML = '<div class="error">Failed to load option chain</div>';
        }
    },

    renderOptionChain: function(chain) {
        var panel = document.getElementById('optionChainContent');
        if (!panel) return;

        var html = '<div class="chain-header">';
        html += '<span class="chain-spot">Spot: ' + chain.current_price.toLocaleString() + '</span>';
        html += '<span class="chain-lot">Lot Size: ' + chain.lot_size + '</span>';
        html += '</div>';

        html += '<div class="chain-expiries">';
        html += '<label>Expiry:</label>';
        html += '<select id="optionExpiry">';
        chain.expiries.forEach(function(exp, i) {
            html += '<option value="' + exp + '"' + (i === 0 ? ' selected' : '') + '>' + exp + '</option>';
        });
        html += '</select>';
        html += '</div>';

        html += '<div class="chain-table-wrapper">';
        html += '<table class="chain-table">';
        html += '<thead><tr>';
        html += '<th>CE LTP</th><th>CE Chg</th><th>Strike</th><th>PE Chg</th><th>PE LTP</th>';
        html += '</tr></thead>';
        html += '<tbody>';

        var atm = chain.current_price;
        var options = chain.options[chain.expiries[0]] || [];

        options.forEach(function(opt) {
            var isAtm = Math.abs(opt.strike - atm) < 100;
            var rowClass = isAtm ? 'atm-row' : '';
            var changeClass = function(v) { return v >= 0 ? 'positive' : 'negative'; };

            html += '<tr class="' + rowClass + '">';
            html += '<td class="call-ltp" data-strike="' + opt.strike + '" data-type="call">' + opt.call_ltp.toFixed(2) + '</td>';
            html += '<td class="' + changeClass(opt.call_change) + '">' + opt.call_change.toFixed(2) + '</td>';
            html += '<td class="strike-cell">' + opt.strike.toLocaleString() + '</td>';
            html += '<td class="' + changeClass(opt.put_change) + '">' + opt.put_change.toFixed(2) + '</td>';
            html += '<td class="put-ltp" data-strike="' + opt.strike + '" data-type="put">' + opt.put_ltp.toFixed(2) + '</td>';
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        panel.innerHTML = html;

        var self = this;
        panel.querySelectorAll('.call-ltp, .put-ltp').forEach(function(cell) {
            cell.addEventListener('click', function() {
                var strike = cell.dataset.strike;
                var type = cell.dataset.type;
                var price = cell.textContent;
                self.selectOption(chain.symbol, strike, type, price, chain.lot_size);
            });
        });

        var expirySelect = document.getElementById('optionExpiry');
        if (expirySelect) {
            expirySelect.addEventListener('change', function() {
                self.renderOptionChain(chain);
            });
        }
    },

    selectOption: function(symbol, strike, type, price, lot_size) {
        var symbolInput = document.getElementById('tradeSymbol');
        var entryInput = document.getElementById('tradeEntry');
        var qtyInput = document.getElementById('tradeQty');
        var typeSelect = document.getElementById('tradeType');
        var sideSelect = document.getElementById('tradeSide');

        var optionSymbol = symbol + ' ' + strike + ' ' + type.toUpperCase();

        this.selectedLotSize = lot_size;

        if (symbolInput) symbolInput.value = optionSymbol;
        if (entryInput) entryInput.value = price;
        if (qtyInput) {
            qtyInput.value = '1';
            qtyInput.setAttribute('data-lot-size', String(lot_size));
            qtyInput.setAttribute('min', '1');
            qtyInput.setAttribute('step', '1');
        }
        if (typeSelect) typeSelect.value = 'option';
        if (sideSelect) sideSelect.value = 'long';

        this.updateLotInfo(lot_size);

        var optionPanel = document.getElementById('optionChainPanel');
        if (optionPanel) optionPanel.classList.remove('active');

        FeeCalculator.calculate();
    },

    getLotSize: function() {
        return this.selectedLotSize || 1;
    }
};
