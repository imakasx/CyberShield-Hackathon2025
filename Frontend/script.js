let pie, bar;

const csvData = [
    "Scanned Post: 'New Job Openings' → Classified as Safe",
    "Suspicious Link detected in Post: 'Free Crypto Giveaway'",
    "Post: 'Product Review' → Neutral sentiment",
    "Verified News Article classified as Safe",
    "Phishing attempt flagged in Post: 'Login to claim reward'",
    "Post: 'Weather Update' → Neutral",
    "Positive engagement on Post: 'Community Event'",
    "Post: 'Breaking News' → Safe",
    "Spam keywords detected in Post: 'Win iPhone Free'",
    "Community Post reviewed → Neutral",
    "Facebook	भारत के वैज्ञानिकों पर गर्व है। Safe",
    "Misleading claims about Indian policies, Suspicious",
    "Twitter/X	Misleading claims about Indian policie Neutral",
    "Facebook	India’s startups are growing fast. Safe",
    "LinkedIn	Unverified allegations used to criticise India., Suspicious",
    "Koo	भारत के वैज्ञानिकों पर गर्व है। Neutral",
    "Jay hind, Safe",
    "kashmir pandit, Suspicious",
    "mera desh maahan, Neutral",
    "GoIndia, Safe"
];

const logBox = document.getElementById("logBox");
let index = 0;

// Dummy CSV analysis data (backend se aayega)
function getCSVAnalysis() {
    return {
        positive: 25,
        negative: 15,
        neutral: 10,
        platforms: {
            Twitter: 20,
            Facebook: 15,
            Instagram: 10,
            Reddit: 5,
            LinkedIn: 12,
            YouTube: 18
        }
    };
}

// Logs updater (fast 1.5s)
function updateLogs() {
    const line = csvData[index % csvData.length];
    const div = document.createElement("div");
    div.textContent = line;
    logBox.appendChild(div);

    if (logBox.children.length > csvData.length) {
        logBox.removeChild(logBox.children[0]);
    }
    logBox.scrollTop = logBox.scrollHeight;
    index++;
}

// Pie chart & counts (static)
function updatePieAndCounts() {
    const data = getCSVAnalysis();
    const total = data.positive + data.negative + data.neutral;

    document.getElementById("safeCount").textContent =
        `${data.positive} (${Math.round((data.positive / total) * 100)}%)`;

    document.getElementById("suspiciousCount").textContent =
        `${data.negative} (${Math.round((data.negative / total) * 100)}%)`;

    document.getElementById("neutralCount").textContent =
        `${data.neutral} (${Math.round((data.neutral / total) * 100)}%)`;

    // Pie Chart (no animation)
    const pieCtx = document.getElementById('pieChart').getContext('2d');
    if (pie) pie.destroy();
    pie = new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [data.positive, data.negative, data.neutral],
                backgroundColor: ['#00ff99', '#ff4c4c', '#ffc107'],
                borderColor: '#1b1b1b',
                borderWidth: 2
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            animation: false
        }
    });
}

// Bar chart updater (independent animation 2s)
function updateBarChart() {
    const data = getCSVAnalysis();

    const barCtx = document.getElementById('barChart').getContext('2d');
    if (bar) bar.destroy();
    bar = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(data.platforms),
            datasets: [{
                label: 'Platform %',
                data: Object.values(data.platforms),
                backgroundColor: '#00bfff'
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            animation: {
                duration: 1500, // 2s animation
                easing: 'easeInOutCubic'
            },
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, max: 100, ticks: { color: '#ffffff' } },
                x: { ticks: { color: '#ffffff' } }
            }
        }
    });

    // Platform counts (right side text)
    const platformCountsBox = document.getElementById("platformCounts");
    platformCountsBox.innerHTML = "";
    for (let [platform, value] of Object.entries(data.platforms)) {
        const div = document.createElement("div");
        div.textContent = `${platform}: ${value}%`;
        platformCountsBox.appendChild(div);
    }
}

// Initial load
updatePieAndCounts();
updateLogs();
updateBarChart();

// Different intervals
setInterval(updateLogs, 700);    // Logs faster scroll
setInterval(updateBarChart, 7000); // Bar chart update every 3s
