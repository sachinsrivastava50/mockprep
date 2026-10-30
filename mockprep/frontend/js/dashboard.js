/**
 * MockPrep Dashboard & Progress Tracking Controller
 * Renders session history, Chart.js progress graphs, and session detail modals.
 */

const Dashboard = {
  chartInstance: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const refreshBtn = document.getElementById('refreshDashboardBtn');
    const startNewBtn = document.getElementById('dashStartNewBtn');
    const closeDetailBtn = document.getElementById('closeSessionDetailModal');

    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.loadStats());
    }
    if (startNewBtn) {
      startNewBtn.addEventListener('click', () => window.App.switchView('setup'));
    }
    if (closeDetailBtn) {
      closeDetailBtn.addEventListener('click', () => {
        document.getElementById('sessionDetailModal').classList.add('hidden');
      });
    }
  },

  async loadStats() {
    if (!API.getToken()) {
      return;
    }

    try {
      const stats = await API.getDashboardStats();
      this.renderKPIs(stats);
      this.renderChart(stats.score_trend);
      this.renderHistoryTable(stats.recent_sessions);
    } catch (err) {
      console.error('Failed to load dashboard statistics:', err);
    }
  },

  renderKPIs(stats) {
    document.getElementById('dashTotalInterviews').textContent = stats.total_interviews;
    document.getElementById('dashAvgScore').textContent = `${stats.average_score}/10`;
    document.getElementById('dashTotalQuestions').textContent = stats.total_questions_answered;
    document.getElementById('dashStrongestRole').textContent = stats.strongest_role;
  },

  renderChart(scoreTrend) {
    const ctx = document.getElementById('scoreTrendChart');
    if (!ctx) return;

    if (this.chartInstance) {
      this.chartInstance.destroy();
    }

    const labels = scoreTrend.map((_, idx) => `Session ${idx + 1}`);
    const data = scoreTrend.length ? scoreTrend : [0];

    this.chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels.length ? labels : ['No Data'],
        datasets: [{
          label: 'Score out of 10',
          data: data,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.15)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointBackgroundColor: '#8b5cf6',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            min: 0,
            max: 10,
            ticks: {
              color: '#94a3b8',
              stepSize: 2
            },
            grid: {
              color: 'rgba(148, 163, 184, 0.1)'
            }
          },
          x: {
            ticks: {
              color: '#94a3b8'
            },
            grid: {
              display: false
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1',
            borderColor: 'rgba(99, 102, 241, 0.4)',
            borderWidth: 1,
            padding: 10,
            displayColors: false,
            callbacks: {
              label: (context) => `Score: ${context.parsed.y} / 10`
            }
          }
        }
      }
    });
  },

  renderHistoryTable(sessions) {
    const tbody = document.getElementById('sessionHistoryTableBody');
    if (!tbody) return;

    if (!sessions || sessions.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-8 text-sm text-slate-400">
            No interview sessions recorded yet. Click "Start New Mock Interview" to begin your first practice session!
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = sessions.map(s => {
      const dateStr = new Date(s.started_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      let badgeColor = 'bg-slate-700 text-slate-300';
      if (s.average_score >= 8.0) badgeColor = 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
      else if (s.average_score >= 6.5) badgeColor = 'bg-blue-500/20 text-blue-300 border border-blue-500/30';
      else if (s.average_score > 0) badgeColor = 'bg-amber-500/20 text-amber-300 border border-amber-500/30';

      return `
        <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition">
          <td class="py-3 px-4 text-xs text-slate-400">${dateStr}</td>
          <td class="py-3 px-4 text-sm font-semibold text-white">${s.role}</td>
          <td class="py-3 px-4 text-xs text-slate-300">
            <span class="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700">${s.interview_type}</span>
          </td>
          <td class="py-3 px-4 text-xs">
            <span class="px-2 py-0.5 rounded-full ${s.difficulty === 'Hard' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : s.difficulty === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}">
              ${s.difficulty}
            </span>
          </td>
          <td class="py-3 px-4 text-sm font-bold">
            <span class="px-2.5 py-1 rounded-lg ${badgeColor}">
              ${s.average_score > 0 ? `${s.average_score}/10` : 'Incomplete'}
            </span>
          </td>
          <td class="py-3 px-4 text-right">
            <button onclick="window.Dashboard.viewSessionDetail(${s.id})" class="text-xs px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 font-medium transition">
              Inspect Review
            </button>
          </td>
        </tr>
      `;
    }).join('');
  },

  async viewSessionDetail(sessionId) {
    const modal = document.getElementById('sessionDetailModal');
    const content = document.getElementById('sessionDetailContent');
    modal.classList.remove('hidden');
    content.innerHTML = '<div class="text-center py-12 text-slate-400">Loading session history from PostgreSQL / Database...</div>';

    try {
      const data = await API.getSessionDetail(sessionId);
      const s = data.session;
      const questions = data.questions;

      content.innerHTML = `
        <div class="mb-6 p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap justify-between items-center gap-4">
          <div>
            <div class="text-xs text-indigo-400 font-semibold uppercase">${s.interview_type} • ${s.difficulty}</div>
            <h3 class="text-xl font-bold text-white">${s.role}</h3>
            <p class="text-xs text-slate-400 mt-0.5">Date: ${new Date(s.started_at).toLocaleString()}</p>
          </div>
          <div class="text-right">
            <div class="text-xs text-slate-400 uppercase font-semibold">Average Score</div>
            <div class="text-2xl font-black text-indigo-400">${s.average_score} <span class="text-sm text-slate-500">/ 10</span></div>
          </div>
        </div>

        <div class="space-y-6">
          ${questions.map((q, idx) => `
            <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <div class="flex justify-between items-start">
                <div>
                  <span class="text-xs px-2.5 py-1 rounded-md bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30 mr-2">Q${idx + 1}</span>
                  <span class="text-xs text-slate-400">${q.category || 'General'}</span>
                </div>
                <span class="text-xs px-2.5 py-1 rounded-md font-bold ${q.score >= 7.5 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}">
                  Score: ${q.score}/10
                </span>
              </div>

              <h4 class="text-base font-semibold text-white leading-snug">${q.question_text}</h4>

              <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <div class="text-[11px] font-semibold text-slate-400 uppercase mb-1">Your Typed Answer:</div>
                <p class="text-xs sm:text-sm text-slate-200 leading-relaxed">${q.user_answer}</p>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
                <div class="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                  <div class="text-[10px] text-slate-400 uppercase">Correctness</div>
                  <div class="font-bold text-indigo-300">${q.breakdown.correctness}/10</div>
                </div>
                <div class="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                  <div class="text-[10px] text-slate-400 uppercase">Clarity</div>
                  <div class="font-bold text-emerald-300">${q.breakdown.clarity}/10</div>
                </div>
                <div class="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                  <div class="text-[10px] text-slate-400 uppercase">Depth</div>
                  <div class="font-bold text-cyan-300">${q.breakdown.depth}/10</div>
                </div>
                <div class="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                  <div class="text-[10px] text-slate-400 uppercase">Relevance</div>
                  <div class="font-bold text-yellow-300">${q.breakdown.relevance}/10</div>
                </div>
                <div class="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                  <div class="text-[10px] text-slate-400 uppercase">Communication</div>
                  <div class="font-bold text-purple-300">${q.breakdown.communication}/10</div>
                </div>
              </div>

              <div class="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-900/30 text-xs sm:text-sm text-indigo-200">
                <span class="font-bold text-indigo-300">AI Feedback:</span> ${q.feedback_summary}
              </div>

              ${q.model_answer ? `
                <div class="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-900/30 text-xs sm:text-sm text-emerald-200">
                  <span class="font-bold text-emerald-300">Model Answer:</span> ${q.model_answer}
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      `;
    } catch (err) {
      content.innerHTML = `<div class="text-red-400 py-8 text-center">Failed to load session details: ${err.message}</div>`;
    }
  }
};

window.Dashboard = Dashboard;
