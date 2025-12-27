// Dashboard Features JavaScript
// New features: Cumulative P&L, Daily Stats, Calendar Heatmap, etc.

let cumulativePnlChart = null;
let pnlCalendarData = {};
let dailyStatsData = {};

// Initialize all dashboard features
function initializeDashboardFeatures() {
    loadCumulativePnl();
    loadDailyStats();
    loadTradeHistory();
    loadPnlCalendar();
    loadUserInfo();
    
    // Set up auto-refresh
    setInterval(loadCumulativePnl, 60000); // Every minute
    setInterval(loadDailyStats, 30000); // Every 30 seconds
    setInterval(loadTradeHistory, 60000); // Every minute
    setInterval(loadUserInfo, 30000); // Every 30 seconds
}

// Load Cumulative P&L data and render chart
async function loadCumulativePnl() {
    try {
        const response = await fetch('/api/dashboard/cumulative-pnl');
        const data = await response.json();
        
        if (data.status === 'success' && data.cumulativePnl) {
            updateCumulativePnlDisplay(data.cumulativePnl);
            renderCumulativePnlChart(data.cumulativePnl);
        }
    } catch (error) {
        console.error('Error loading cumulative P&L:', error);
    }
}

// Update Cumulative P&L display
function updateCumulativePnlDisplay(pnlData) {
    const elements = {
        'allTime': document.getElementById('value-all-time'),
        'year': document.getElementById('value-year'),
        'month': document.getElementById('value-month'),
        'week': document.getElementById('value-week'),
        'day': document.getElementById('value-day')
    };
    
    const percentages = {
        'allTime': document.getElementById('percentage-all-time'),
        'year': document.getElementById('percentage-year'),
        'month': document.getElementById('percentage-month'),
        'week': document.getElementById('percentage-week'),
        'day': document.getElementById('percentage-day')
    };
    
    for (const [key, element] of Object.entries(elements)) {
        if (element) {
            const value = pnlData[key] || 0;
            element.textContent = formatCurrency(value);
            element.className = 'metric-value ' + (value >= 0 ? 'positive' : 'negative');
        }
    }
    
    // Update percentages (year percentage shows contribution to all-time)
    if (percentages.year && pnlData.allTime !== 0) {
        const yearPct = (pnlData.year / pnlData.allTime * 100).toFixed(1);
        percentages.year.textContent = `(${yearPct}%)`;
    }
}

// Render Cumulative P&L Radial Chart
function renderCumulativePnlChart(pnlData) {
    const canvas = document.getElementById('cumulativePnlChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (cumulativePnlChart) {
        cumulativePnlChart.destroy();
    }
    
    // Prepare data for radial chart
    const labels = ['All Time', 'Year', 'Month', 'Week', 'Day'];
    const values = [
        pnlData.allTime || 0,
        pnlData.year || 0,
        pnlData.month || 0,
        pnlData.week || 0,
        pnlData.day || 0
    ];
    
    // Normalize values for chart (use max value as 100%)
    const maxValue = Math.max(...values.map(Math.abs), 1);
    const normalizedValues = values.map(v => (v / maxValue) * 100);
    
    cumulativePnlChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: normalizedValues,
                backgroundColor: [
                    '#22c55e', // All time - green
                    '#3b82f6', // Year - blue
                    '#a855f7', // Month - purple
                    '#14b8a6', // Week - teal
                    '#f97316'  // Day - orange
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            return `${labels[index]}: ${formatCurrency(values[index])}`;
                        }
                    }
                }
            }
        }
    });
}

// Load Daily Stats
async function loadDailyStats() {
    try {
        const response = await fetch('/api/dashboard/daily-stats');
        const data = await response.json();
        
        if (data.status === 'success' && data.dailyStats) {
            updateDailyStatsDisplay(data.dailyStats);
            dailyStatsData = data.dailyStats;
        }
    } catch (error) {
        console.error('Error loading daily stats:', error);
    }
}

// Update Daily Stats Display
function updateDailyStatsDisplay(stats) {
    const lossUsedEl = document.getElementById('dailyLossUsed');
    const lossLimitEl = document.getElementById('lossLimit');
    const lossUsedValueEl = document.getElementById('lossUsed');
    const progressEl = document.getElementById('lossProgress');
    
    if (lossUsedEl) {
        lossUsedEl.textContent = formatCurrency(stats.lossUsed || 0);
    }
    
    if (lossLimitEl) {
        lossLimitEl.textContent = formatCurrency(stats.lossLimit || 5000);
    }
    
    if (lossUsedValueEl) {
        lossUsedValueEl.textContent = formatCurrency(stats.lossUsed || 0);
    }
    
    if (progressEl) {
        const percentage = stats.lossPercentage || 0;
        progressEl.style.width = `${Math.min(percentage, 100)}%`;
        
        // Update color based on percentage
        if (percentage >= 80) {
            progressEl.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
        } else if (percentage >= 50) {
            progressEl.style.background = 'linear-gradient(90deg, #f59e0b, #ef4444)';
        } else {
            progressEl.style.background = 'linear-gradient(90deg, #f59e0b, #f59e0b)';
        }
    }
}

// Load Trade History with enhanced features
async function loadTradeHistory() {
    try {
        const showAll = document.getElementById('showAllTrades')?.checked || false;
        const dateFilter = document.getElementById('tradeDateFilter')?.value || '';
        
        let url = '/api/dashboard/trade-history?';
        if (showAll) {
            url += 'showAll=true';
        } else if (dateFilter) {
            url += `date=${dateFilter}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            updateTradeHistoryTable(data.trades || []);
            updateTradeSummary(data.summary || {});
        }
    } catch (error) {
        console.error('Error loading trade history:', error);
    }
}

// Update Trade History Table
function updateTradeHistoryTable(trades) {
    const tbody = document.getElementById('tradesBody');
    if (!tbody) return;
    
    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No trades found</td></tr>';
        return;
    }
    
    tbody.innerHTML = trades.map(trade => `
        <tr>
            <td>${trade.symbol || 'N/A'}</td>
            <td>${formatDateTime(trade.entryTime)}</td>
            <td>${formatDateTime(trade.exitTime)}</td>
            <td>₹${(trade.entryPrice || 0).toFixed(2)}</td>
            <td>₹${(trade.exitPrice || 0).toFixed(2)}</td>
            <td>${trade.quantity || 0}</td>
            <td class="${trade.pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(trade.pnl || 0)}</td>
            <td>${trade.type || 'SELL'}</td>
        </tr>
    `).join('');
}

// Update Trade Summary
function updateTradeSummary(summary) {
    const elements = {
        'totalTrades': document.getElementById('totalTrades'),
        'totalProfit': document.getElementById('totalProfit'),
        'totalLoss': document.getElementById('totalLoss'),
        'netPnl': document.getElementById('netPnl'),
        'winRate': document.getElementById('winRate')
    };
    
    if (elements.totalTrades) {
        elements.totalTrades.textContent = summary.totalTrades || 0;
    }
    
    if (elements.totalProfit) {
        elements.totalProfit.textContent = formatCurrency(summary.totalProfit || 0);
    }
    
    if (elements.totalLoss) {
        elements.totalLoss.textContent = formatCurrency(summary.totalLoss || 0);
    }
    
    if (elements.netPnl) {
        const netPnl = summary.netPnl || 0;
        elements.netPnl.textContent = formatCurrency(netPnl);
        elements.netPnl.className = netPnl >= 0 ? 'positive' : 'negative';
    }
    
    if (elements.winRate) {
        elements.winRate.textContent = `${(summary.winRate || 0).toFixed(1)}%`;
    }
}

// Load P&L Calendar Data
async function loadPnlCalendar() {
    try {
        const startDate = document.getElementById('pnlDateRange')?.value?.split(' - ')[0];
        const endDate = document.getElementById('pnlDateRange')?.value?.split(' - ')[1];
        
        let url = '/api/dashboard/pnl-calendar?';
        if (startDate) url += `start_date=${startDate}&`;
        if (endDate) url += `end_date=${endDate}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            pnlCalendarData = data.pnlByDate || {};
            renderPnlCalendar(pnlCalendarData);
            updatePnlSummary(data.summary || {});
        }
    } catch (error) {
        console.error('Error loading P&L calendar:', error);
    }
}

// Render P&L Calendar Heatmap
function renderPnlCalendar(pnlByDate) {
    const container = document.getElementById('pnlCalendarHeatmap');
    if (!container) return;
    
    // Group dates by month
    const months = {};
    for (const [dateStr, pnl] of Object.entries(pnlByDate)) {
        const date = new Date(dateStr);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        
        if (!months[monthKey]) {
            months[monthKey] = [];
        }
        
        months[monthKey].push({ date, pnl });
    }
    
    // Generate calendar HTML
    let html = '';
    for (const [monthKey, days] of Object.entries(months)) {
        const [year, month] = monthKey.split('-');
        const monthName = new Date(year, month - 1).toLocaleString('default', { month: 'short' });
        
        html += `
            <div class="pnl-month-column">
                <div class="pnl-month-header">${monthName} ${year}</div>
                <div class="pnl-week-row">
        `;
        
        // Generate days for the month
        const firstDay = new Date(year, month - 1, 1);
        const lastDay = new Date(year, month, 0);
        const startWeekday = firstDay.getDay();
        
        // Add empty cells for days before month start
        for (let i = 0; i < startWeekday; i++) {
            html += '<div class="pnl-day-cell no-data"></div>';
        }
        
        // Add days of the month
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const dateStr = `${year}-${month}-${String(day).padStart(2, '0')}`;
            const pnl = pnlByDate[dateStr] || null;
            const cellClass = getPnlCellClass(pnl);
            const tooltip = pnl !== null ? `P&L: ${formatCurrency(pnl)}` : 'No data';
            
            html += `<div class="pnl-day-cell ${cellClass}" title="${tooltip}"></div>`;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Get CSS class for P&L cell based on value
function getPnlCellClass(pnl) {
    if (pnl === null || pnl === undefined) return 'no-data';
    
    if (pnl > 0) {
        if (pnl >= 1000) return 'profit-large';
        if (pnl >= 500) return 'profit-medium';
        return 'profit-small';
    } else {
        if (pnl <= -1000) return 'loss-large';
        if (pnl <= -500) return 'loss-medium';
        return 'loss-small';
    }
}

// Update P&L Summary
function updatePnlSummary(summary) {
    const elements = {
        'realisedPnlValue': document.getElementById('realisedPnlValue'),
        'paperPnlValue': document.getElementById('paperPnlValue'),
        'livePnlValue': document.getElementById('livePnlValue'),
        'totalTradesCount': document.getElementById('totalTradesCount')
    };
    
    if (elements.realisedPnlValue) {
        elements.realisedPnlValue.textContent = formatCurrency(summary.realisedPnl || 0);
    }
    
    if (elements.paperPnlValue) {
        elements.paperPnlValue.textContent = formatCurrency(summary.paperPnl || 0);
    }
    
    if (elements.livePnlValue) {
        elements.livePnlValue.textContent = formatCurrency(summary.livePnl || 0);
    }
    
    if (elements.totalTradesCount) {
        elements.totalTradesCount.textContent = summary.totalTrades || 0;
    }
}

// Helper Functions
function formatCurrency(value) {
    const num = parseFloat(value) || 0;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('en-IN', { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateStr;
    }
}

// Sync Orders from Zerodha
async function syncOrdersFromZerodha() {
    try {
        const btn = document.getElementById('syncOrdersBtn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = '🔄 Syncing...';
        }
        
        const response = await fetch('/api/dashboard/sync-orders', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Orders synced successfully!', 'success');
            loadTradeHistory();
        } else {
            showNotification('Error syncing orders: ' + (data.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Error syncing orders: ' + error.message, 'error');
    } finally {
        const btn = document.getElementById('syncOrdersBtn');
        if (btn) {
            btn.disabled = false;
            btn.textContent = '🔄 Sync Orders from Zerodha';
        }
    }
}

// Toggle Trade Filter
function toggleTradeFilter() {
    loadTradeHistory();
}

// Show Help Modal
function showHelp(topic) {
    const helpContent = {
        'daily-loss': {
            title: 'Daily Loss Used',
            body: `
                <h3>What is Daily Loss Used?</h3>
                <p>The Daily Loss Used shows how much of your daily loss limit has been consumed today.</p>
                <h3>How it works:</h3>
                <ul>
                    <li><strong>Loss Limit:</strong> The maximum amount you're willing to lose in a single day (default: ₹5,000)</li>
                    <li><strong>Loss Used:</strong> The cumulative loss from all losing trades today</li>
                    <li><strong>Progress Bar:</strong> Visual indicator showing percentage of limit used</li>
                </ul>
                <div class="help-note">
                    <strong>Note:</strong> When the daily loss limit is reached, trading may be automatically blocked to protect your capital.
                </div>
            `
        },
        'cumulative-pnl': {
            title: 'Cumulative Profit & Loss',
            body: `
                <h3>What is Cumulative P&L?</h3>
                <p>Cumulative P&L shows your total profit or loss across different time periods.</p>
                <h3>Time Periods:</h3>
                <ul>
                    <li><strong>All Time:</strong> Total P&L since you started trading</li>
                    <li><strong>Year:</strong> P&L for the current calendar year</li>
                    <li><strong>Month:</strong> P&L for the current month</li>
                    <li><strong>Week:</strong> P&L for the current week (Monday to today)</li>
                    <li><strong>Day:</strong> P&L for today</li>
                </ul>
                <h3>Chart:</h3>
                <p>The radial chart visualizes the relative contribution of each time period to your overall performance.</p>
            `
        },
        'trade-history': {
            title: 'Trade History',
            body: `
                <h3>Trade History Table</h3>
                <p>This table shows all your completed trades with detailed information.</p>
                <h3>Columns:</h3>
                <ul>
                    <li><strong>Symbol:</strong> Trading symbol of the instrument</li>
                    <li><strong>Entry Time:</strong> When the position was opened</li>
                    <li><strong>Exit Time:</strong> When the position was closed</li>
                    <li><strong>Entry Price:</strong> Average entry price</li>
                    <li><strong>Exit Price:</strong> Average exit price</li>
                    <li><strong>Quantity:</strong> Number of contracts/shares</li>
                    <li><strong>P&L:</strong> Realized profit or loss</li>
                    <li><strong>Type:</strong> BUY or SELL transaction</li>
                </ul>
                <h3>Filters:</h3>
                <ul>
                    <li><strong>Show All Trades:</strong> Display all historical trades</li>
                    <li><strong>Date Filter:</strong> Filter trades by specific date</li>
                </ul>
            `
        },
        'pnl-chart': {
            title: 'P&L Calendar Heatmap',
            body: `
                <h3>P&L Calendar Heatmap</h3>
                <p>This calendar visualization shows your daily P&L over time, similar to GitHub's contribution graph.</p>
                <h3>Color Coding:</h3>
                <ul>
                    <li><strong>Green shades:</strong> Profitable days (darker = larger profit)</li>
                    <li><strong>Pink/Red shades:</strong> Losing days (darker = larger loss)</li>
                    <li><strong>Gray:</strong> No trading activity</li>
                </ul>
                <h3>Filters:</h3>
                <ul>
                    <li><strong>Segment:</strong> Filter by market segment (NIFTY, BANKNIFTY, etc.)</li>
                    <li><strong>P&L Type:</strong> Combined, Paper, or Live trading</li>
                    <li><strong>Symbol:</strong> Filter by specific symbol</li>
                    <li><strong>Date Range:</strong> Select custom date range</li>
                </ul>
            `
        }
    };
    
    const content = helpContent[topic];
    if (!content) return;
    
    const modal = document.getElementById('helpModal');
    const titleEl = document.getElementById('helpModalTitle');
    const bodyEl = document.getElementById('helpModalBody');
    
    if (modal && titleEl && bodyEl) {
        titleEl.textContent = content.title;
        bodyEl.innerHTML = content.body;
        modal.style.display = 'flex';
    }
}

// Close Help Modal
function closeHelp() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Show Notification
function showNotification(message, type = 'info') {
    // Implementation depends on your notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
    // You can integrate with your existing notification system here
    if (typeof addNotification === 'function') {
        addNotification(message, type);
    }
}

// Load and Update User Info
async function loadUserInfo() {
    try {
        const response = await fetch('/api/auth/details');
        const data = await response.json();
        
        if (data.success && data.details) {
            const userNameEl = document.getElementById('userName');
            const userIdEl = document.getElementById('userId');
            const userInfoEl = document.getElementById('userInfo');
            
            if (userNameEl && userIdEl && userInfoEl) {
                const userName = data.details.account_name || data.details.user_id || '-';
                const userId = data.details.user_id || '-';
                
                userNameEl.textContent = userName;
                userIdEl.textContent = `ID: ${userId}`;
                userInfoEl.style.display = 'flex';
            }
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboardFeatures);
} else {
    initializeDashboardFeatures();
}

// Load user info on initialization
loadUserInfo();
setInterval(loadUserInfo, 30000); // Update every 30 seconds

