/**
 * MockPrep Main Application Entrypoint
 * Coordinates view transitions and component initializations.
 */

const App = {
  activeView: 'landing',

  init() {
    this.bindNavigation();
    window.Auth.init();
    window.Interview.init();
    window.Dashboard.init();

    // Auto-detect login status
    if (API.getToken()) {
      this.switchView('dashboard');
    } else {
      this.switchView('landing');
    }
  },

  bindNavigation() {
    const navHome = document.getElementById('navHome');
    const navPractice = document.getElementById('navPractice');
    const navDashboard = document.getElementById('navDashboard');
    const heroPracticeBtn = document.getElementById('heroPracticeBtn');

    if (navHome) navHome.addEventListener('click', () => this.switchView('landing'));
    if (navPractice) navPractice.addEventListener('click', () => this.switchView('setup'));
    if (navDashboard) navDashboard.addEventListener('click', () => this.switchView('dashboard'));
    if (heroPracticeBtn) heroPracticeBtn.addEventListener('click', () => this.switchView('setup'));
  },

  switchView(viewName) {
    this.activeView = viewName;

    // View Containers
    const views = {
      landing: document.getElementById('landingSection'),
      setup: document.getElementById('setupSection'),
      interview: document.getElementById('interviewSection'),
      dashboard: document.getElementById('dashboardSection')
    };

    // Hide all views
    Object.values(views).forEach(el => {
      if (el) el.classList.add('hidden');
    });

    // Show target view
    if (views[viewName]) {
      views[viewName].classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // View specific actions
    if (viewName === 'dashboard') {
      window.Dashboard.loadStats();
    }

    // Update active nav link highlighting
    const navLinks = {
      landing: document.getElementById('navHome'),
      setup: document.getElementById('navPractice'),
      dashboard: document.getElementById('navDashboard')
    };

    Object.entries(navLinks).forEach(([key, link]) => {
      if (!link) return;
      if (key === viewName) {
        link.classList.add('text-indigo-400', 'font-semibold');
        link.classList.remove('text-slate-300');
      } else {
        link.classList.remove('text-indigo-400', 'font-semibold');
        link.classList.add('text-slate-300');
      }
    });
  }
};

window.App = App;

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
