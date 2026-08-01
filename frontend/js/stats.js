const Stats = {
    data: null,

    async load() {
        try {
            const res = await fetch('/api/stats');
            this.data = await res.json();
            this.render();
            return this.data;
        } catch (err) {
            console.error('Failed to load stats:', err);
        }
    },

    render() {
        const s = this.data;
        if (!s) return;

        document.getElementById('stat-total-pnl').textContent = this.formatMoney(s.total_pnl);
        document.getElementById('stat-total-pnl').className = 'stat-value ' + (s.total_pnl >= 0 ? 'profit' : 'loss');

        document.getElementById('stat-win-rate').textContent = s.win_rate + '%';
        document.getElementById('stat-win-rate').className = 'stat-value ' + (s.win_rate >= 50 ? 'profit' : 'loss');

        document.getElementById('stat-profit-factor').textContent = s.profit_factor >= 9999.99 ? '∞' : s.profit_factor.toFixed(2);
        document.getElementById('stat-profit-factor').className = 'stat-value ' + (s.profit_factor >= 1 ? 'profit' : 'loss');

        document.getElementById('stat-total-trades').textContent = s.total_trades;
        document.getElementById('stat-avg-win').textContent = this.formatMoney(s.avg_win);
        document.getElementById('stat-avg-loss').textContent = this.formatMoney(s.avg_loss);
        document.getElementById('stat-max-dd').textContent = this.formatMoney(s.max_drawdown);
        document.getElementById('stat-largest-win').textContent = this.formatMoney(s.largest_win);

        document.getElementById('stat-risk-reward').textContent = s.risk_reward >= 9999.99 ? '∞' : s.risk_reward.toFixed(2);
        document.getElementById('stat-risk-reward').className = 'stat-value ' + (s.risk_reward >= 1 ? 'profit' : 'loss');
    },

    formatMoney(val) {
        if (val === undefined || val === null) return '\u20B90.00';
        var sign = val >= 0 ? '+' : '';
        return sign + '\u20B9' + Math.abs(val).toFixed(2);
    },

    formatMoneyPlain(val) {
        if (val === undefined || val === null) return '\u20B90.00';
        return '\u20B9' + Number(val).toFixed(2);
    }
};
