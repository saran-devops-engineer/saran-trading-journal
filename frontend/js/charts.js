var Charts = {
    equityChart: null,
    dailyPnlChart: null,
    winLossChart: null,

    render: function() {
        var stats = Stats.data;
        if (!stats || !stats.trade_dates) return;

        this.renderEquityCurve(stats);
        this.renderDailyPnl(stats);
        this.renderWinLoss(stats);
    },

    renderEquityCurve: function(stats) {
        var ctx = document.getElementById('equityChart').getContext('2d');
        if (this.equityChart) this.equityChart.destroy();

        var labels = stats.trade_dates.map(function(d, i) { return 'Trade ' + (i + 1); });
        var data = stats.equity_curve;

        this.equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Equity',
                    data: data,
                    borderColor: '#00d4aa',
                    backgroundColor: 'rgba(0, 212, 170, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    pointBackgroundColor: '#00d4aa'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return '\u20B9' + ctx.parsed.y.toFixed(2); }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#8892b0' }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: {
                            color: '#8892b0',
                            callback: function(v) { return '\u20B9' + v; }
                        }
                    }
                }
            }
        });
    },

    renderDailyPnl: function(stats) {
        var ctx = document.getElementById('dailyPnlChart').getContext('2d');
        if (this.dailyPnlChart) this.dailyPnlChart.destroy();

        var labels = stats.trade_dates.map(function(d) {
            var date = new Date(d + 'T00:00:00');
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        var dailyPnl = stats.equity_curve.map(function(v, i) {
            return i === 0 ? v : v - stats.equity_curve[i - 1];
        });

        var colors = dailyPnl.map(function(v) {
            return v >= 0 ? '#00d4aa' : '#ff6b6b';
        });

        this.dailyPnlChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Daily P&L',
                    data: dailyPnl,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return '\u20B9' + ctx.parsed.y.toFixed(2); }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#8892b0' }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: {
                            color: '#8892b0',
                            callback: function(v) { return '\u20B9' + v; }
                        }
                    }
                }
            }
        });
    },

    renderWinLoss: function(stats) {
        var ctx = document.getElementById('winLossChart').getContext('2d');
        if (this.winLossChart) this.winLossChart.destroy();

        this.winLossChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Wins', 'Losses'],
                datasets: [{
                    data: [stats.winning_trades, stats.losing_trades],
                    backgroundColor: ['#00d4aa', '#ff6b6b'],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#8892b0', padding: 16 }
                    }
                }
            }
        });
    }
};
