var Analytics = {
    data: null,
    benchmarkData: null,
    dayOfWeekChart: null,
    winRateDayChart: null,
    benchmarkChart: null,

    load: async function() {
        try {
            var res = await fetch('/api/analytics');
            this.data = await res.json();
            var benchRes = await fetch('/api/benchmark');
            this.benchmarkData = await benchRes.json();
            this.render();
        } catch (err) {
            console.error('Failed to load analytics:', err);
        }
    },

    render: function() {
        if (!this.data) return;
        this.renderExpectancy();
        this.renderBehavioral();
        this.renderHoldTime();
        this.renderStrategyTable();
        this.renderDayOfWeekCharts();
        this.renderMoodTable();
        this.renderBenchmark();
    },

    renderExpectancy: function() {
        var val = this.data.expectancy;
        var el = document.getElementById('expectancy-value');
        var formula = document.getElementById('expectancy-formula');
        if (el) {
            el.textContent = Stats.formatMoney(val);
            el.className = 'expectancy-value ' + (val >= 0 ? 'profit' : 'loss');
        }
        if (formula) {
            formula.textContent = 'Per trade: (Win% × Avg Win) - (Loss% × Avg Loss)';
        }
    },

    renderBehavioral: function() {
        var b = this.data.behavioral;
        if (!b) return;
        var setVal = function(id, val) { var el = document.getElementById(id); if (el) el.textContent = val; };
        setVal('max-consec-losses', b.max_consecutive_losses);
        setVal('revenge-trades', b.revenge_trades);
        setVal('overtrade-days', b.overtrade_days);
        setVal('avg-trades-day', b.avg_trades_per_day);
    },

    renderHoldTime: function() {
        var h = this.data.hold_time;
        if (!h) return;
        var formatHours = function(h) {
            if (h === 0) return 'N/A';
            if (h < 1) return Math.round(h * 60) + 'm';
            return h.toFixed(1) + 'h';
        };
        var winners = document.getElementById('hold-winners');
        var losers = document.getElementById('hold-losers');
        if (winners) winners.textContent = formatHours(h.avg_winner_hold_hours);
        if (losers) losers.textContent = formatHours(h.avg_loser_hold_hours);
    },

    renderStrategyTable: function() {
        var tbody = document.getElementById('strategyTableBody');
        if (!tbody) return;
        var strats = this.data.strategy;
        if (!strats || Object.keys(strats).length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No strategy data yet. Add strategies to your trades.</td></tr>';
            return;
        }

        var rows = Object.keys(strats).map(function(name) {
            var s = strats[name];
            return '<tr>' +
                '<td><strong>' + name + '</strong></td>' +
                '<td>' + s.total + '</td>' +
                '<td class="' + (s.win_rate >= 50 ? 'profit' : 'loss') + '">' + s.win_rate + '%</td>' +
                '<td class="' + (s.total_pnl >= 0 ? 'pnl-positive' : 'pnl-negative') + '">' + Stats.formatMoney(s.total_pnl) + '</td>' +
                '<td>' + Stats.formatMoney(s.avg_pnl) + '</td>' +
                '<td>' + (s.profit_factor >= 9999.99 ? '∞' : s.profit_factor.toFixed(2)) + '</td>' +
                '<td>' + (s.risk_reward >= 9999.99 ? '∞' : s.risk_reward.toFixed(2)) + '</td>' +
            '</tr>';
        });
        tbody.innerHTML = rows.join('');
    },

    renderDayOfWeekCharts: function() {
        var td = this.data.time_day;
        if (!td || !td.by_day) return;

        var days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        var dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        var pnlData = days.map(function(d) { return td.by_day[d] ? td.by_day[d].total_pnl : 0; });
        var winData = days.map(function(d) { return td.by_day[d] ? td.by_day[d].win_rate : 0; });
        var colors = pnlData.map(function(v) { return v >= 0 ? '#00d4aa' : '#ff6b6b'; });

        if (this.dayOfWeekChart) this.dayOfWeekChart.destroy();
        var ctx1 = document.getElementById('dayOfWeekChart');
        if (ctx1) {
            this.dayOfWeekChart = new Chart(ctx1.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: dayLabels,
                    datasets: [{
                        label: 'Total P&L',
                        data: pnlData,
                        backgroundColor: colors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#8892b0' } },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#8892b0', callback: function(v) { return '₹' + v; } }
                        }
                    }
                }
            });
        }

        if (this.winRateDayChart) this.winRateDayChart.destroy();
        var ctx2 = document.getElementById('winRateDayChart');
        if (ctx2) {
            this.winRateDayChart = new Chart(ctx2.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: dayLabels,
                    datasets: [{
                        label: 'Win Rate %',
                        data: winData,
                        backgroundColor: '#3498db',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#8892b0' } },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#8892b0', callback: function(v) { return v + '%'; } },
                            max: 100
                        }
                    }
                }
            });
        }
    },

    renderMoodTable: function() {
        var tbody = document.getElementById('moodTableBody');
        if (!tbody) return;

        var moodStats = Stats.data ? Stats.data.mood_stats : null;
        if (!moodStats || Object.keys(moodStats).length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="no-data">No mood data yet. Start logging your mood with trades.</td></tr>';
            return;
        }

        var moodLabels = {
            confident: 'Confident', neutral: 'Neutral', nervous: 'Nervous',
            revenge: 'Revenge', fomo: 'FOMO', greed: 'Greed',
            calm: 'Calm', anxious: 'Anxious', hoping: 'Hoping', panicking: 'Panicking'
        };

        var rows = Object.keys(moodStats).map(function(mood) {
            var m = moodStats[mood];
            return '<tr>' +
                '<td><span class="mood-badge mood-' + mood + '">' + (moodLabels[mood] || mood) + '</span></td>' +
                '<td>' + m.total + '</td>' +
                '<td class="' + (m.win_rate >= 50 ? 'profit' : 'loss') + '">' + m.win_rate + '%</td>' +
                '<td class="' + (m.avg_pnl >= 0 ? 'pnl-positive' : 'pnl-negative') + '">' + Stats.formatMoney(m.avg_pnl) + '</td>' +
            '</tr>';
        });
        tbody.innerHTML = rows.join('');
    },

    renderBenchmark: function() {
        var b = this.benchmarkData;
        if (!b || !b.dates || b.dates.length === 0) return;

        var statsEl = document.getElementById('benchmarkStats');
        if (statsEl) {
            var alphaClass = b.alpha >= 0 ? 'profit' : 'loss';
            statsEl.innerHTML =
                '<div class="benchmark-stat">' +
                    '<span class="benchmark-stat-label">Your Return</span>' +
                    '<span class="benchmark-stat-value ' + (b.your_total >= 0 ? 'profit' : 'loss') + '">' + b.your_total.toFixed(2) + '%</span>' +
                '</div>' +
                '<div class="benchmark-stat">' +
                    '<span class="benchmark-stat-label">Market Return</span>' +
                    '<span class="benchmark-stat-value">' + b.benchmark_total.toFixed(2) + '%</span>' +
                '</div>' +
                '<div class="benchmark-stat">' +
                    '<span class="benchmark-stat-label">Alpha</span>' +
                    '<span class="benchmark-stat-value ' + alphaClass + '">' + (b.alpha >= 0 ? '+' : '') + b.alpha.toFixed(2) + '%</span>' +
                '</div>';
        }

        if (this.benchmarkChart) this.benchmarkChart.destroy();
        var ctx = document.getElementById('benchmarkChart');
        if (!ctx) return;

        var labels = b.dates.map(function(d, i) { return 'Trade ' + (i + 1); });
        this.benchmarkChart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Your Returns',
                        data: b.your_returns,
                        borderColor: '#00d4aa',
                        backgroundColor: 'rgba(0, 212, 170, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3
                    },
                    {
                        label: 'Market (NIFTY50)',
                        data: b.benchmark_returns,
                        borderColor: '#8892b0',
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.3,
                        pointRadius: 2
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#8892b0', padding: 16 }
                    }
                },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8892b0' } },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#8892b0', callback: function(v) { return v + '%'; } }
                    }
                }
            }
        });
    }
};
