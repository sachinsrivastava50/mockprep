/**
 * MockPrep Interview Flow Controller
 * Manages question generation, answering, weighted scoring rubric, and results.
 */

const Interview = {
  currentSession: null,
  currentQuestion: null,
  previousQuestions: [],
  questionIndex: 0,
  targetQuestions: 3,
  timerInterval: null,
  secondsElapsed: 0,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const startBtn = document.getElementById('startSessionBtn');
    const submitAnswerBtn = document.getElementById('submitAnswerBtn');
    const nextQuestionBtn = document.getElementById('nextQuestionBtn');
    const finishSessionBtn = document.getElementById('finishSessionBtn');
    const toggleHintBtn = document.getElementById('toggleHintBtn');
    const roleSelect = document.getElementById('interviewRoleSelect');
    const customRoleWrapper = document.getElementById('customRoleWrapper');

    if (roleSelect && customRoleWrapper) {
      roleSelect.addEventListener('change', () => {
        if (roleSelect.value === 'Custom') {
          customRoleWrapper.classList.remove('hidden');
        } else {
          customRoleWrapper.classList.add('hidden');
        }
      });
    }

    if (startBtn) {
      startBtn.addEventListener('click', () => this.startSession());
    }

    if (submitAnswerBtn) {
      submitAnswerBtn.addEventListener('click', () => this.submitAnswer());
    }

    if (nextQuestionBtn) {
      nextQuestionBtn.addEventListener('click', () => this.loadNextQuestion());
    }

    if (finishSessionBtn) {
      finishSessionBtn.addEventListener('click', () => this.finishSession());
    }

    if (toggleHintBtn) {
      toggleHintBtn.addEventListener('click', () => {
        const hintBox = document.getElementById('questionHintBox');
        if (hintBox) hintBox.classList.toggle('hidden');
      });
    }

    // Ctrl+Enter shortcut to submit answer
    const answerTextarea = document.getElementById('userAnswerInput');
    if (answerTextarea) {
      answerTextarea.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
          e.preventDefault();
          this.submitAnswer();
        }
      });
    }
  },

  async startSession() {
    if (!API.getToken()) {
      alert('Please log in or click Guest Demo to start practicing!');
      window.Auth.showModal('login');
      return;
    }

    const roleSelect = document.getElementById('interviewRoleSelect').value;
    const customRoleInput = document.getElementById('customRoleInput').value.trim();
    const role = (roleSelect === 'Custom' && customRoleInput) ? customRoleInput : roleSelect;

    const interviewType = document.getElementById('interviewTypeSelect').value;
    const difficulty = document.getElementById('interviewDifficultySelect').value;
    const countSelect = document.getElementById('questionCountSelect').value;

    this.targetQuestions = parseInt(countSelect, 10) || 3;
    this.questionIndex = 0;
    this.previousQuestions = [];

    const startBtn = document.getElementById('startSessionBtn');
    startBtn.disabled = true;
    startBtn.textContent = 'Initializing AI Session...';

    try {
      this.currentSession = await API.createSession(role, interviewType, difficulty);
      window.App.switchView('interview');
      await this.loadNextQuestion();
    } catch (err) {
      alert('Could not start session: ' + err.message);
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = 'Begin Mock Interview';
    }
  },

  async loadNextQuestion() {
    this.questionIndex++;

    // Hide feedback panel, show active question panel
    document.getElementById('evaluationFeedbackPanel').classList.add('hidden');
    document.getElementById('activeQuestionPanel').classList.remove('hidden');

    // Reset answer input & hints
    document.getElementById('userAnswerInput').value = '';
    const hintBox = document.getElementById('questionHintBox');
    if (hintBox) hintBox.classList.add('hidden');

    // Update Progress Header
    document.getElementById('interviewProgressLabel').textContent = 
      `Question ${this.questionIndex} of ${this.targetQuestions}`;
    const percent = (this.questionIndex / this.targetQuestions) * 100;
    document.getElementById('interviewProgressBar').style.width = `${percent}%`;

    // Metadata badges
    document.getElementById('activeRoleBadge').textContent = this.currentSession.role;
    document.getElementById('activeTypeBadge').textContent = this.currentSession.interview_type;
    document.getElementById('activeDifficultyBadge').textContent = this.currentSession.difficulty;

    // Loading state for question
    document.getElementById('activeQuestionText').textContent = 'Generating role-specific interview question using AI model...';
    document.getElementById('submitAnswerBtn').disabled = true;

    try {
      const qData = await API.generateQuestion(
        this.currentSession.id,
        this.currentSession.role,
        this.currentSession.interview_type,
        this.currentSession.difficulty,
        this.previousQuestions
      );

      this.currentQuestion = qData;
      this.previousQuestions.push(qData.question);

      document.getElementById('activeQuestionText').textContent = qData.question;
      document.getElementById('activeCategoryBadge').textContent = qData.category || 'Core Competency';
      document.getElementById('questionHintText').textContent = qData.hint || 'Focus on clarity, depth, and structured reasoning.';
      document.getElementById('submitAnswerBtn').disabled = false;

      // Start Question Stopwatch
      this.startTimer();
    } catch (err) {
      document.getElementById('activeQuestionText').textContent = 'Error loading question. Please try again.';
      alert('Failed to generate question: ' + err.message);
    }
  },

  startTimer() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    this.secondsElapsed = 0;
    const timerDisplay = document.getElementById('interviewTimerDisplay');
    
    this.timerInterval = setInterval(() => {
      this.secondsElapsed++;
      const mins = String(Math.floor(this.secondsElapsed / 60)).padStart(2, '0');
      const secs = String(this.secondsElapsed % 60).padStart(2, '0');
      if (timerDisplay) timerDisplay.textContent = `${mins}:${secs}`;
    }, 1000);
  },

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  },

  async submitAnswer() {
    const answer = document.getElementById('userAnswerInput').value.trim();
    if (!answer) {
      alert('Please type an answer before submitting for evaluation.');
      document.getElementById('userAnswerInput').focus();
      return;
    }

    this.stopTimer();
    const submitBtn = document.getElementById('submitAnswerBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Evaluating with AI Model...';

    try {
      const evalResult = await API.submitAnswer(
        this.currentSession.id,
        this.currentQuestion.question,
        this.currentQuestion.category,
        answer,
        this.secondsElapsed
      );

      this.renderEvaluation(evalResult);
    } catch (err) {
      alert('Evaluation error: ' + err.message);
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Answer for AI Evaluation';
    }
  },

  renderEvaluation(result) {
    // Hide active question input panel, show evaluation panel
    document.getElementById('activeQuestionPanel').classList.add('hidden');
    const feedbackPanel = document.getElementById('evaluationFeedbackPanel');
    feedbackPanel.classList.remove('hidden');

    // Overall Score out of 10.0
    const scoreVal = result.score;
    document.getElementById('evalScoreValue').textContent = `${scoreVal}/10`;

    // Radial Circle Stroke
    const circle = document.getElementById('evalCircleProgress');
    if (circle) {
      const radius = 45;
      const circumference = 2 * Math.PI * radius;
      const offset = circumference - (scoreVal / 10) * circumference;
      circle.style.strokeDasharray = `${circumference}`;
      circle.style.strokeDashoffset = `${offset}`;
    }

    // Verdict Badge
    const verdictEl = document.getElementById('evalVerdictBadge');
    if (scoreVal >= 8.5) {
      verdictEl.textContent = 'Exceptional Response';
      verdictEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
    } else if (scoreVal >= 7.0) {
      verdictEl.textContent = 'Strong Performance';
      verdictEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40';
    } else if (scoreVal >= 5.5) {
      verdictEl.textContent = 'Good Effort • Needs Refinement';
      verdictEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40';
    } else {
      verdictEl.textContent = 'Needs Practice';
      verdictEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/40';
    }

    // Weighted Sub-scores Breakdown
    const bd = result.breakdown;
    document.getElementById('subCorrectnessVal').textContent = `${bd.correctness}/10`;
    document.getElementById('subCorrectnessBar').style.width = `${(bd.correctness / 10) * 100}%`;

    document.getElementById('subClarityVal').textContent = `${bd.clarity}/10`;
    document.getElementById('subClarityBar').style.width = `${(bd.clarity / 10) * 100}%`;

    document.getElementById('subDepthVal').textContent = `${bd.depth}/10`;
    document.getElementById('subDepthBar').style.width = `${(bd.depth / 10) * 100}%`;

    document.getElementById('subRelevanceVal').textContent = `${bd.relevance}/10`;
    document.getElementById('subRelevanceBar').style.width = `${(bd.relevance / 10) * 100}%`;

    document.getElementById('subCommunicationVal').textContent = `${bd.communication}/10`;
    document.getElementById('subCommunicationBar').style.width = `${(bd.communication / 10) * 100}%`;

    // Feedback summary
    document.getElementById('evalFeedbackSummary').textContent = result.feedback_summary;

    // Strengths list
    const strengthsUl = document.getElementById('evalStrengthsList');
    strengthsUl.innerHTML = (result.strengths || []).map(s => `
      <li class="flex items-start text-xs sm:text-sm text-slate-300">
        <svg class="w-4 h-4 text-emerald-400 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        <span>${s}</span>
      </li>
    `).join('');

    // Improvements list
    const improvementsUl = document.getElementById('evalImprovementsList');
    improvementsUl.innerHTML = (result.improvements || []).map(i => `
      <li class="flex items-start text-xs sm:text-sm text-slate-300">
        <svg class="w-4 h-4 text-amber-400 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
        <span>${i}</span>
      </li>
    `).join('');

    // Model Answer
    document.getElementById('evalModelAnswerText').textContent = result.model_answer;

    // Toggle Next vs Finish button
    const nextBtn = document.getElementById('nextQuestionBtn');
    const finishBtn = document.getElementById('finishSessionBtn');

    if (this.questionIndex < this.targetQuestions) {
      nextBtn.classList.remove('hidden');
      finishBtn.classList.add('hidden');
    } else {
      nextBtn.classList.add('hidden');
      finishBtn.classList.remove('hidden');
    }

    feedbackPanel.scrollIntoView({ behavior: 'smooth' });
  },

  async finishSession() {
    if (this.currentSession) {
      try {
        await API.completeSession(this.currentSession.id);
      } catch (err) {
        console.warn('Complete session warning:', err);
      }
    }
    // Switch to Dashboard to view progress and scores!
    window.App.switchView('dashboard');
  }
};

window.Interview = Interview;
