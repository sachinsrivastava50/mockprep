/**
 * MockPrep REST API Client
 * Handles communication with the FastAPI backend, JWT Authorization,
 * and seamless local offline fallback if the Python server is not yet started.
 */

const API_BASE = window.location.origin.includes(':8000') 
  ? `${window.location.origin}/api` 
  : 'http://localhost:8000/api';

const API = {
  isOfflineMode: false,

  getToken() {
    return localStorage.getItem('mockprep_jwt_token');
  },

  setToken(token) {
    localStorage.setItem('mockprep_jwt_token', token);
  },

  clearToken() {
    localStorage.removeItem('mockprep_jwt_token');
    localStorage.removeItem('mockprep_user');
  },

  getUser() {
    const raw = localStorage.getItem('mockprep_user');
    return raw ? JSON.parse(raw) : null;
  },

  setUser(user) {
    localStorage.setItem('mockprep_user', JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401) {
          this.clearToken();
          window.dispatchEvent(new CustomEvent('auth:expired'));
        }
        throw new Error(data.detail || `Request failed with status ${response.status}`);
      }

      this.isOfflineMode = false;
      return data;
    } catch (err) {
      // If network connection failed (FastAPI backend not running), fallback seamlessly
      if (err.name === 'TypeError' || err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        console.warn(`[MockPrep Offline Mode] Backend unreachable at ${API_BASE}. Using local engine.`);
        this.isOfflineMode = true;
        return this.offlineFallback(endpoint, options);
      }
      throw err;
    }
  },

  // Offline Fallback Engine (Runs even if python run.py is not yet started!)
  offlineFallback(endpoint, options) {
    const body = options.body ? JSON.parse(options.body) : {};

    if (endpoint === '/auth/login' || endpoint === '/auth/register') {
      const mockUser = {
        id: 101,
        name: body.name || 'Demo Student (Group 05)',
        email: body.email || 'student@ietlucknow.ac.in',
        created_at: new Date().toISOString()
      };
      this.setToken('mock_jwt_token_' + Date.now());
      this.setUser(mockUser);
      return { access_token: this.getToken(), user: mockUser };
    }

    if (endpoint === '/interview/session') {
      const session = {
        id: Date.now(),
        user_id: 101,
        role: body.role || 'Software Engineer',
        interview_type: body.interview_type || 'Technical',
        difficulty: body.difficulty || 'Medium',
        status: 'IN_PROGRESS',
        average_score: 0.0,
        total_questions: 0,
        started_at: new Date().toISOString()
      };
      const all = JSON.parse(localStorage.getItem('mockprep_local_sessions') || '[]');
      all.unshift(session);
      localStorage.setItem('mockprep_local_sessions', JSON.stringify(all));
      return session;
    }

    if (endpoint === '/interview/generate-question') {
      const questionBank = [
        {
          question: `For a ${body.difficulty || 'Medium'} ${body.role || 'Software Engineer'}, how would you design a distributed caching layer using Redis to prevent cache stampedes and thundering herds?`,
          category: 'Distributed Systems & Caching',
          hint: 'Think about probabilistic early expiration (XFetch), mutex locks, and stale-while-revalidate patterns.'
        },
        {
          question: `Describe a situation where a major release you were responsible for experienced a production failure. How did you diagnose the root cause and lead the resolution?`,
          category: 'Behavioral & Incident Response',
          hint: 'Use the STAR method: Situation, Task, Action, and measurable Result. Highlight blameless post-mortem actions.'
        },
        {
          question: `Explain how indexing works in relational databases (B-Trees). In what scenarios can adding an index actually degrade database performance?`,
          category: 'Database Optimization',
          hint: 'Consider write penalties (INSERT/UPDATE/DELETE), index maintenance, index bloat, and low-cardinality columns.'
        }
      ];
      const selected = questionBank[Math.floor(Math.random() * questionBank.length)];
      return {
        question: selected.question,
        category: selected.category,
        hint: selected.hint,
        expected_key_points: ['Core architectural mechanics', 'Trade-offs and failure modes', 'Measurable outcomes']
      };
    }

    if (endpoint === '/interview/submit-answer') {
      const words = (body.user_answer || '').trim().split(/\s+/).length;
      let score = 7.5;
      if (words < 25) score = 4.8;
      else if (words > 60) score = 8.6;

      const correctness = Math.min(9.8, score + 0.3);
      const clarity = Math.min(9.5, score + 0.1);
      const depth = Math.min(9.6, score - 0.2);
      const relevance = Math.min(9.4, score + 0.2);
      const communication = Math.min(9.5, score);

      const result = {
        id: Date.now(),
        session_id: body.session_id,
        score: score,
        breakdown: {
          overall_score: score,
          correctness: correctness,
          clarity: clarity,
          depth: depth,
          relevance: relevance,
          communication: communication
        },
        strengths: [
          'Direct and clear engagement with the core question',
          'Good technical depth and awareness of architectural tradeoffs'
        ],
        improvements: [
          'Add quantifiable metrics (e.g. latency reduction %, throughput) to strengthen the conclusion',
          'Mention edge cases and failure recovery mechanisms'
        ],
        feedback_summary: `Solid answer! Your response demonstrated good foundational understanding, scoring ${score}/10 on the weighted rubric. Adding concrete production metrics will elevate this to an exceptional answer.`,
        model_answer: 'A top-performing answer should clearly establish the technical definitions, outline the end-to-end flow, compare tradeoffs, and finish with a quantifiable outcome or metric.'
      };

      // Update session in local storage
      const sessions = JSON.parse(localStorage.getItem('mockprep_local_sessions') || '[]');
      const curr = sessions.find(s => s.id === body.session_id);
      if (curr) {
        curr.total_questions = (curr.total_questions || 0) + 1;
        curr.average_score = score;
        localStorage.setItem('mockprep_local_sessions', JSON.stringify(sessions));
      }

      // Store in results
      const results = JSON.parse(localStorage.getItem('mockprep_local_results') || '[]');
      results.push({ ...result, ...body });
      localStorage.setItem('mockprep_local_results', JSON.stringify(results));

      return result;
    }

    if (endpoint === '/interview/session/' + (body.session_id || '') + '/complete') {
      return { status: 'COMPLETED' };
    }

    if (endpoint === '/dashboard/stats') {
      const sessions = JSON.parse(localStorage.getItem('mockprep_local_sessions') || '[]');
      const total = sessions.length;
      const avg = total ? (sessions.reduce((acc, s) => acc + (s.average_score || 0), 0) / total).toFixed(1) : 0;
      const questionsCount = sessions.reduce((acc, s) => acc + (s.total_questions || 0), 0);

      return {
        total_interviews: total,
        average_score: parseFloat(avg),
        total_questions_answered: questionsCount,
        strongest_role: total ? `${sessions[0].role} (${avg}/10)` : 'None yet',
        recent_sessions: sessions.slice(0, 10),
        score_trend: sessions.slice(0, 10).reverse().map(s => s.average_score || 7.0)
      };
    }

    if (endpoint.startsWith('/dashboard/session/')) {
      const sessionId = parseInt(endpoint.split('/')[3], 10);
      const sessions = JSON.parse(localStorage.getItem('mockprep_local_sessions') || '[]');
      const session = sessions.find(s => s.id === sessionId) || {
        id: sessionId,
        role: 'Software Engineer',
        interview_type: 'Technical',
        difficulty: 'Medium',
        average_score: 8.2,
        started_at: new Date().toISOString()
      };
      const results = JSON.parse(localStorage.getItem('mockprep_local_results') || '[]').filter(r => r.session_id === sessionId);

      return {
        session,
        questions: results.map(r => ({
          question_text: r.question_text || 'Technical Interview Question',
          category: r.category || 'Core Domain',
          user_answer: r.user_answer || 'Candidate answer',
          score: r.score || 8.0,
          breakdown: r.breakdown || { correctness: 8, clarity: 8, depth: 8, relevance: 8, communication: 8 },
          feedback_summary: r.feedback_summary || 'Good answer.',
          model_answer: r.model_answer || 'Benchmark reference answer.'
        }))
      };
    }

    return {};
  },

  // Auth Endpoints
  async register(name, email, password) {
    const res = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password })
    });
    this.setToken(res.access_token);
    this.setUser(res.user);
    return res;
  },

  async login(email, password) {
    const res = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    this.setToken(res.access_token);
    this.setUser(res.user);
    return res;
  },

  async getMe() {
    return this.request('/auth/me');
  },

  // Interview Endpoints
  async createSession(role, interview_type, difficulty) {
    return this.request('/interview/session', {
      method: 'POST',
      body: JSON.stringify({ role, interview_type, difficulty })
    });
  },

  async getSession(sessionId) {
    return this.request(`/interview/session/${sessionId}`);
  },

  async generateQuestion(sessionId, role, interview_type, difficulty, previous_questions = []) {
    return this.request('/interview/generate-question', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        role,
        interview_type,
        difficulty,
        previous_questions
      })
    });
  },

  async submitAnswer(sessionId, questionText, category, userAnswer, timeTakenSeconds = 0) {
    return this.request('/interview/submit-answer', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        question_text: questionText,
        category,
        user_answer: userAnswer,
        time_taken_seconds: timeTakenSeconds
      })
    });
  },

  async completeSession(sessionId) {
    return this.request(`/interview/session/${sessionId}/complete`, {
      method: 'POST'
    });
  },

  // Dashboard Endpoints
  async getDashboardStats() {
    return this.request('/dashboard/stats');
  },

  async getSessionDetail(sessionId) {
    return this.request(`/dashboard/session/${sessionId}/detail`);
  }
};

window.API = API;
