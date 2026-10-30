// ==========================================================================
// GATE Exam System - Core Application Logic
// ==========================================================================

class ExamApp {
  constructor() {
    this.manifest = [];
    this.currentTest = null;
    this.currentQIndex = 0;
    this.currentSection = null;
    this.isPracticeMode = false;
    this.timerInterval = null;
    this.timeRemaining = 0;
    this.timeElapsed = 0;

    // User responses: { [qIndex]: { value: any, status: string, timeSpent: number } }
    this.userResponses = {};

    // UI state
    this.currentView = 'dashboard';
    this.activeFilterSeries = 'All';
    this.activeFilterSubject = 'All';
    this.activeFilterType = 'All';
    this.searchQuery = '';
    this.sortBy = 'default';
    this.lastResultData = null;
    this.solutionFilter = 'all';

    // Auth & Access Protection
    this.currentUser = null;
    this.authTab = 'login';
    this.ADMIN_EMAIL = 'musicfusion123456@gmail.com';

    // ── Telemetry engine ──────────────────────────────────────────────────
    this._tel = {
      sessionId: 'sess_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      sessionStart: Date.now(),
      pagesVisited: [],
      seriesBrowsed: [],
      // Per-question tracking (reset on each exam start)
      qStartTime: {},      // { [idx]: timestamp }
      qTimeSpent: {},      // { [idx]: cumulative seconds }
      qChanges: {},        // { [idx]: number of answer changes }
      qMarkedReview: {},   // { [idx]: bool }
      qRevisited: {},      // { [idx]: bool }
      qVisited: {},        // { [idx]: bool } — first visit flag
      endSent: false,
    };
    // Send session-end on tab close / navigate away
    window.addEventListener('pagehide', () => this._telEndSession());
    // Track visibility (tab hide = student distracted?)
    document.addEventListener('visibilitychange', () => {
      this._telBehavior(document.hidden ? 'tab_hidden' : 'tab_visible');
    });

    this.init();
  }

  async init() {
    this.loadUserSession();
    this.loadHistory();
    this.loadBookmarks();
    this.setupEventListeners();
    await this.fetchManifest();
    this.renderDashboard();
    this.initTheme();
    // Log session start
    this._telSessionEvent('start');
  }

  // ==========================================================================
  // TELEMETRY ENGINE
  // ==========================================================================

  /** Device fingerprint for login/register payloads. */
  _deviceInfo() {
    return {
      userAgent:  navigator.userAgent || '',
      screenRes:  `${screen.width}x${screen.height}`,
      platform:   navigator.platform || navigator.userAgentData?.platform || '',
      language:   navigator.language || '',
      timezone:   Intl.DateTimeFormat().resolvedOptions().timeZone || '',
    };
  }

  /** Fire-and-forget POST to a telemetry endpoint. Never throws. */
  async _telPost(endpoint, payload, options = {}) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        ...options,
      });
      if (!response.ok) console.warn(`Telemetry request failed (${response.status}): ${endpoint}`);
      return response.ok;
    } catch (error) {
      console.warn(`Telemetry request could not reach the server: ${endpoint}`, error);
      return false;
    }
  }

  /** Log a session start or end event. */
  _telSessionEvent(type) {
    const duration = type === 'end'
      ? Math.round((Date.now() - this._tel.sessionStart) / 1000)
      : null;
    this._telPost('/api/telemetry/session', {
      email:           this.currentUser?.email || '',
      sessionId:       this._tel.sessionId,
      eventType:       type,
      durationSeconds: duration,
      pagesVisited:    [...this._tel.pagesVisited],
      seriesBrowsed:   [...this._tel.seriesBrowsed],
    });
  }

  _telEndSession() {
    if (this._tel.endSent) return;
    this._tel.endSent = true;
    const payload = {
      email: this.currentUser?.email || '',
      sessionId: this._tel.sessionId,
      eventType: 'end',
      durationSeconds: Math.round((Date.now() - this._tel.sessionStart) / 1000),
      pagesVisited: [...this._tel.pagesVisited],
      seriesBrowsed: [...this._tel.seriesBrowsed],
    };
    const body = new Blob([JSON.stringify(payload)], { type: 'application/json' });
    if (navigator.sendBeacon?.('/api/telemetry/session', body)) return;
    this._telPost('/api/telemetry/session', payload, { keepalive: true });
  }

  /** Log a single behavioral event. */
  _telBehavior(eventType, data = null) {
    this._telPost('/api/telemetry/event', {
      email:     this.currentUser?.email || '',
      sessionId: this._tel.sessionId,
      eventType,
      data,
    });
  }

  /** Called every time we navigate to a question — records visit & timing. */
  _telQuestionEnter(idx) {
    const now = Date.now();
    // If we were on a previous question, accumulate its time
    if (this._tel._currentQIdx !== undefined && this._tel._currentQIdx !== idx) {
      const prev = this._tel._currentQIdx;
      const spent = Math.round((now - (this._tel._qEnterTime || now)) / 1000);
      this._tel.qTimeSpent[prev] = (this._tel.qTimeSpent[prev] || 0) + spent;
    }
    if (!this._tel.qVisited[idx]) {
      this._tel.qVisited[idx] = true;
    } else {
      this._tel.qRevisited[idx] = true;
    }
    this._tel._currentQIdx = idx;
    this._tel._qEnterTime  = now;
  }

  /** Called on every answer change for a question. */
  _telAnswerChange(idx) {
    this._tel.qChanges[idx] = (this._tel.qChanges[idx] || 0) + 1;
  }

  /** Called when mark-for-review is toggled. */
  _telMarkReview(idx, isMarked) {
    if (isMarked) this._tel.qMarkedReview[idx] = true;
  }

  /** Reset per-question telemetry at the start of each exam. */
  _telResetExam() {
    this._tel.qStartTime    = {};
    this._tel.qTimeSpent    = {};
    this._tel.qChanges      = {};
    this._tel.qMarkedReview = {};
    this._tel.qRevisited    = {};
    this._tel.qVisited      = {};
    this._tel._currentQIdx  = undefined;
    this._tel._qEnterTime   = undefined;
  }

  /** Flush all question telemetry to server after exam submit. */
  _telFlushQuestions(resultRecord) {
    if (!resultRecord?.questions) return;
    // Finalize time for last question
    if (this._tel._currentQIdx !== undefined) {
      const idx = this._tel._currentQIdx;
      const spent = Math.round((Date.now() - (this._tel._qEnterTime || Date.now())) / 1000);
      this._tel.qTimeSpent[idx] = (this._tel.qTimeSpent[idx] || 0) + spent;
    }
    const rows = resultRecord.questions.map((q, idx) => ({
      testId:         resultRecord.testId,
      testTitle:      resultRecord.testTitle,
      questionIndex:  idx,
      subject:        q.section || resultRecord.subject || '',
      type:           q.type || 'MCQ',
      marks:          q.marks || 1,
      timeSpent:      this._tel.qTimeSpent[idx] || 0,
      answerChanges:  this._tel.qChanges[idx]   || 0,
      markedReview:   !!this._tel.qMarkedReview[idx],
      wasRevisited:   !!this._tel.qRevisited[idx],
      finalAnswer:    Array.isArray(q.userResponse) ? q.userResponse.join(',') : (q.userResponse ?? ''),
      isCorrect:      !!q.isCorrect,
      marksAwarded:   q.marksAwarded || 0,
      isAttempted:    !!q.isAttempted,
      testMode:       this.isPracticeMode ? 'practice' : 'exam',
    }));
    this._telPost('/api/telemetry/questions', {
      email: this.currentUser?.email || 'guest',
      rows,
    });
  }

  // --- User Session & Auth Management ---
  loadUserSession() {
    try {
      const saved = localStorage.getItem('gate_user_session');
      if (saved) {
        this.currentUser = JSON.parse(saved);
        if (this.currentUser.email && this.currentUser.email.toLowerCase().trim() === this.ADMIN_EMAIL) {
          this.currentUser.isAdmin = true;
          this.currentUser.hasFullAccess = true;
        }
      }
    } catch (e) {
      this.currentUser = null;
    }
    this.updateUserNavDisplay();
  }

  saveUserSession(user) {
    this.currentUser = user;
    if (user) {
      if (user.email && user.email.toLowerCase().trim() === this.ADMIN_EMAIL) {
        user.isAdmin = true;
        user.hasFullAccess = true;
      }
      localStorage.setItem('gate_user_session', JSON.stringify(user));
    } else {
      localStorage.removeItem('gate_user_session');
    }
    this.updateUserNavDisplay();
    this.renderTestsGrid();
  }

  updateUserNavDisplay() {
    const label = document.getElementById('user-display-name');
    const codeBtn = document.getElementById('btn-unlock-code');
    const adminBtn = document.getElementById('nav-admin');

    // Admin button is only visible to authenticated admin user
    if (adminBtn) {
      const isMasterAdmin = this.currentUser && (this.currentUser.isAdmin || (this.currentUser.email && this.currentUser.email.toLowerCase().trim() === this.ADMIN_EMAIL));
      adminBtn.style.display = isMasterAdmin ? 'inline-flex' : 'none';
    }

    if (this.currentUser) {
      const displayName = this.currentUser.name || this.currentUser.email.split('@')[0];
      const rolePrefix = this.currentUser.isAdmin ? '👑 Admin: ' : '👨‍🎓 ';
      if (label) label.textContent = `${rolePrefix}${displayName}`;
      
      if (codeBtn) {
        if (this.currentUser.hasFullAccess || this.currentUser.isAdmin) {
          codeBtn.innerHTML = '<span>🎉 Full Access</span>';
          codeBtn.style.color = '#6ee7b7';
        } else {
          codeBtn.innerHTML = '<span>🔑 Unlock Code</span>';
          codeBtn.style.color = '#fde68a';
        }
      }
    } else {
      if (label) label.textContent = '👤 Sign In';
      if (codeBtn) {
        codeBtn.innerHTML = '<span>🔑 Unlock Code</span>';
        codeBtn.style.color = '#fde68a';
      }
    }
  }

  canAccessTest(test) {
    // Official GATE PYQs are ALWAYS free for everyone!
    if (test.series === 'GATE PYQs') return true;
    
    // Admin always has access
    if (this.currentUser && this.currentUser.isAdmin) return true;
    
    // Logged-in user who unlocked with code or admin grant has access
    // Support both boolean true and numeric 1 from DB
    if (this.currentUser && (this.currentUser.hasFullAccess || this.currentUser.has_access_code == true || this.currentUser.has_access_code === 1)) return true;

    return false;
  }

  promptUnlock(testId) {
    if (!this.currentUser) {
      alert("Account required: Please Sign In or Create an Account first. Access codes are securely tied to your email account.");
      this.showAuthModal();
      return;
    }
    this.showUnlockModal();
  }

  // --- Auth Modals & REST calls ---
  showAuthModal() {
    if (this.currentUser) {
      const confirmLogout = confirm(`Signed in as: ${this.currentUser.email}\nDo you want to sign out?`);
      if (confirmLogout) {
        this.saveUserSession(null);
        alert('You have been signed out.');
        return;
      }
      return;
    }
    const modal = document.getElementById('modal-auth');
    if (modal) {
      this.clearAuthAlert();
      modal.classList.remove('hidden');
    }
  }

  hideAuthModal() {
    document.getElementById('modal-auth')?.classList.add('hidden');
  }

  setAuthTab(tab) {
    this.authTab = tab;
    this.clearAuthAlert();
    const loginTab = document.getElementById('auth-tab-login');
    const regTab = document.getElementById('auth-tab-register');
    const nameGroup = document.getElementById('auth-group-name');
    const submitBtn = document.getElementById('btn-auth-submit');

    if (tab === 'login') {
      loginTab?.classList.add('active');
      regTab?.classList.remove('active');
      if (nameGroup) nameGroup.style.display = 'none';
      if (submitBtn) submitBtn.textContent = 'Sign In';
    } else {
      regTab?.classList.add('active');
      loginTab?.classList.remove('active');
      if (nameGroup) nameGroup.style.display = 'flex';
      if (submitBtn) submitBtn.textContent = 'Create Student Account';
    }
  }

  showAuthAlert(message, type = 'error') {
    const el = document.getElementById('auth-alert');
    if (el) {
      el.textContent = message;
      el.className = `auth-alert ${type}`;
      el.style.display = 'block';
    }
  }

  clearAuthAlert() {
    const el = document.getElementById('auth-alert');
    if (el) {
      el.textContent = '';
      el.style.display = 'none';
    }
  }

  async handleAuthSubmit() {
    const email = document.getElementById('auth-input-email')?.value.trim();
    const password = document.getElementById('auth-input-password')?.value;
    const name = document.getElementById('auth-input-name')?.value.trim();

    if (!email || !password) {
      return this.showAuthAlert('Please enter both email and password.');
    }

    const endpoint = this.authTab === 'login' ? '/api/auth/login' : '/api/auth/register';
    const payload = { email, password, name, ...this._deviceInfo() };

    const submitBtn = document.getElementById('btn-auth-submit');
    if (submitBtn) { submitBtn.textContent = 'Signing in...'; submitBtn.disabled = true; }

    try {
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (!resp.ok) {
        // Show server error (wrong password, email not found, etc)
        if (submitBtn) { submitBtn.textContent = this.authTab === 'login' ? 'Sign In' : 'Create Student Account'; submitBtn.disabled = false; }
        return this.showAuthAlert(data.error || 'Authentication failed.');
      }

      // Normalize the user object from backend
      const user = data.user;
      user.adminToken = data.adminToken || null;
      user.hasFullAccess = user.has_access_code == true || user.has_access_code === 1 || user.role === 'admin';
      user.isAdmin = user.role === 'admin' || user.email.toLowerCase().trim() === this.ADMIN_EMAIL;

      this.saveUserSession(user);
      this.hideAuthModal();
      if (submitBtn) { submitBtn.textContent = this.authTab === 'login' ? 'Sign In' : 'Create Student Account'; submitBtn.disabled = false; }
      this.showToast(`Welcome, ${user.name || user.email}! 🎉`, 'success');
      this.renderTestsGrid();
    } catch (err) {
      // Server offline fallback — use local credentials
      console.warn('Backend API offline, using local session fallback:', err);
      if (submitBtn) { submitBtn.textContent = this.authTab === 'login' ? 'Sign In' : 'Create Student Account'; submitBtn.disabled = false; }
      const isMasterAdmin = email.toLowerCase().trim() === this.ADMIN_EMAIL;
      const locallyUnlocked = localStorage.getItem('gate_exam_unlocked') === 'true';
      const fallbackUser = {
        email: email.toLowerCase().trim(),
        name: name || email.split('@')[0],
        role: isMasterAdmin ? 'admin' : 'student',
        isAdmin: isMasterAdmin,
        hasFullAccess: isMasterAdmin || locallyUnlocked,
        has_access_code: isMasterAdmin || locallyUnlocked ? 1 : 0,
        joinedAt: new Date().toISOString()
      };
      this.saveUserSession(fallbackUser);
      this.hideAuthModal();
      this.showToast(`Welcome, ${fallbackUser.name}! (Offline mode)`, 'success');
      this.renderTestsGrid();
    }
  }

  // --- Code Unlock Modal & Action ---
  showUnlockModal() {
    if (!this.currentUser) {
      alert("Please Sign In or Create an Account first. Access codes are securely linked to your registered email account.");
      this.showAuthModal();
      return;
    }

    const modal = document.getElementById('modal-unlock');
    if (modal) {
      this.clearUnlockAlert();
      const userEmailEl = document.getElementById('unlock-user-email');
      if (userEmailEl) userEmailEl.textContent = this.currentUser.email;
      const codeInput = document.getElementById('unlock-code-input');
      if (codeInput) codeInput.value = '';
      modal.classList.remove('hidden');
    }
  }

  hideUnlockModal() {
    document.getElementById('modal-unlock')?.classList.add('hidden');
  }

  showUnlockAlert(message, type = 'error') {
    const el = document.getElementById('unlock-alert');
    if (el) {
      el.textContent = message;
      el.className = `auth-alert ${type}`;
      el.style.display = 'block';
    }
  }

  clearUnlockAlert() {
    const el = document.getElementById('unlock-alert');
    if (el) {
      el.textContent = '';
      el.style.display = 'none';
    }
  }

  async handleCodeUnlock() {
    if (!this.currentUser) {
      this.showUnlockAlert('Please sign in or create an account first.');
      return;
    }

    const code = document.getElementById('unlock-code-input')?.value.trim().toUpperCase();
    if (!code) {
      return this.showUnlockAlert('Please enter your 10-character access code.');
    }

    const email = this.currentUser.email;
    const VALID_CODE = '12G3A4T8WE';

    try {
      const resp = await fetch('/api/auth/unlock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code })
      });
      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.error || 'Invalid or expired access code. Please contact musicfusion123456@gmail.com');
      }

      // Success: update account state
      this.currentUser.hasFullAccess = true;
      this.currentUser.has_access_code = 1;
      this.saveUserSession(this.currentUser);
      localStorage.setItem('gate_exam_unlocked', 'true');

      this.showUnlockAlert('🎉 Success! Full series access unlocked for your account.', 'success');
      setTimeout(() => {
        this.hideUnlockModal();
        this.renderTestsGrid();
        this.updateUserNavDisplay();
      }, 1200);
    } catch (err) {
      // Server offline: check code locally
      if (code === VALID_CODE) {
        this.currentUser.hasFullAccess = true;
        this.currentUser.has_access_code = 1;
        this.saveUserSession(this.currentUser);
        localStorage.setItem('gate_exam_unlocked', 'true');
        this.showUnlockAlert('🎉 Access unlocked! Welcome to the full series.', 'success');
        setTimeout(() => {
          this.hideUnlockModal();
          this.renderTestsGrid();
          this.updateUserNavDisplay();
        }, 1200);
      } else {
        this.showUnlockAlert('❌ Invalid code. Contact musicfusion123456@gmail.com to obtain your access code.');
      }
    }
  }

  // --- Local Storage Management ---
  loadHistory() {
    try {
      this.history = JSON.parse(localStorage.getItem('gate_exam_history') || '[]');
    } catch (e) {
      this.history = [];
    }
  }

  saveHistory(record) {
    this.history.unshift(record);
    // Keep last 100 attempts
    if (this.history.length > 100) this.history.pop();
    localStorage.setItem('gate_exam_history', JSON.stringify(this.history));
  }

  loadBookmarks() {
    try {
      this.bookmarks = JSON.parse(localStorage.getItem('gate_exam_bookmarks') || '[]');
    } catch (e) {
      this.bookmarks = [];
    }
  }

  toggleBookmark(testId, qIndex, questionData) {
    const key = `${testId}_${qIndex}`;
    const idx = this.bookmarks.findIndex(b => b.key === key);
    if (idx >= 0) {
      this.bookmarks.splice(idx, 1);
    } else {
      this.bookmarks.push({
        key,
        testId,
        testTitle: this.currentTest ? this.currentTest.title : '',
        qIndex,
        question: questionData,
        savedAt: new Date().toISOString()
      });
    }
    localStorage.setItem('gate_exam_bookmarks', JSON.stringify(this.bookmarks));
    this.updateBookmarkButtonState(key);
  }

  isBookmarked(testId, qIndex) {
    const key = `${testId}_${qIndex}`;
    return this.bookmarks.some(b => b.key === key);
  }

  // --- Data Loading ---
  async fetchManifest() {
    try {
      const resp = await fetch('data/exam_manifest.json');
      if (!resp.ok) throw new Error('Failed to load test manifest');
      this.manifest = await resp.json();
    } catch (e) {
      console.error('Error fetching manifest:', e);
      this.manifest = [];
    }
  }

  // --- Toast Notifications ---
  showToast(message, type = 'info') {
    // Remove existing toast
    const existing = document.getElementById('app-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = `app-toast app-toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.add('visible');
    });

    // Auto-remove after 3.5 seconds
    setTimeout(() => {
      toast.classList.remove('visible');
      setTimeout(() => toast.remove(), 400);
    }, 3500);
  }


  async loadTest(testId) {
    try {
      const resp = await fetch(`data/tests/${testId}.json`);
      if (!resp.ok) throw new Error('Failed to load test file');
      return await resp.json();
    } catch (e) {
      console.error('Error loading test:', e);
      alert('Failed to load test data. Please try again.');
      return null;
    }
  }

  // --- Theme ---
  initTheme() {
    const saved = localStorage.getItem('gate_exam_theme');
    if (saved === 'light') {
      document.body.classList.add('light-theme');
      const icon = document.getElementById('theme-toggle-icon');
      if (icon) icon.textContent = '🌙';
    }
  }

  toggleTheme() {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem('gate_exam_theme', isLight ? 'light' : 'dark');
    const icon = document.getElementById('theme-toggle-icon');
    if (icon) icon.textContent = isLight ? '🌙' : '☀️';
  }

  // --- Event Listeners ---
  setupEventListeners() {
    // Header navigation
    document.getElementById('nav-dashboard')?.addEventListener('click', () => this.switchView('dashboard'));
    document.getElementById('nav-analytics')?.addEventListener('click', () => this.switchView('analytics'));
    document.getElementById('nav-history')?.addEventListener('click', () => this.switchView('history'));
    document.getElementById('nav-saved')?.addEventListener('click', () => this.switchView('saved'));
    document.getElementById('nav-admin')?.addEventListener('click', () => this.switchView('admin'));
    document.getElementById('btn-unlock-code')?.addEventListener('click', () => this.showUnlockModal());
    document.getElementById('btn-user-auth')?.addEventListener('click', () => this.showAuthModal());
    document.getElementById('theme-toggle-btn')?.addEventListener('click', () => this.toggleTheme());
    document.getElementById('brand-header')?.addEventListener('click', () => this.switchView('dashboard'));

    // Search and Sort
    document.getElementById('test-search-input')?.addEventListener('input', (e) => {
      this.searchQuery = e.target.value.toLowerCase().trim();
      this.renderTestsGrid();
    });

    document.getElementById('test-sort-select')?.addEventListener('change', (e) => {
      this.sortBy = e.target.value;
      this.renderTestsGrid();
    });

    // Series Switcher Tabs
    document.querySelectorAll('.series-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.activeFilterSeries = btn.dataset.series;
        document.querySelectorAll('.series-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeFilterSubject = 'All';
        this.renderSubjectPills();
        this.renderTestsGrid();
      });
    });

    // Exam Tools
    document.getElementById('btn-calculator')?.addEventListener('click', () => {
      this._telBehavior('calculator_open', { testId: this.currentTest?.id || null });
      if (window.gateCalculator) window.gateCalculator.toggle();
    });

    document.getElementById('btn-qpaper')?.addEventListener('click', () => this.showQuestionPaperModal());
    document.getElementById('modal-qpaper-close')?.addEventListener('click', () => this.hideQuestionPaperModal());

    // Exam Actions
    document.getElementById('btn-save-next')?.addEventListener('click', () => this.saveAndNext());
    document.getElementById('btn-mark-review')?.addEventListener('click', () => this.markForReview());
    document.getElementById('btn-clear-resp')?.addEventListener('click', () => this.clearResponse());
    document.getElementById('btn-prev-q')?.addEventListener('click', () => this.prevQuestion());
    document.getElementById('btn-submit-exam')?.addEventListener('click', () => this.showSubmitConfirmation());

    // Submit Modal
    document.getElementById('modal-submit-cancel')?.addEventListener('click', () => this.hideSubmitModal());
    document.getElementById('modal-submit-confirm')?.addEventListener('click', () => this.submitExam());

    // Keyboard shortcuts
    window.addEventListener('keydown', (e) => {
      if (this.currentView !== 'exam') return;
      if (e.target.tagName === 'INPUT') return;

      if (e.altKey && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        this.saveAndNext();
      } else if (e.altKey && e.key.toLowerCase() === 'p') {
        e.preventDefault();
        this.prevQuestion();
      } else if (e.altKey && e.key.toLowerCase() === 'c') {
        e.preventDefault();
        if (window.gateCalculator) window.gateCalculator.toggle();
      } else if (e.key === 'Escape') {
        this.hideSubmitModal();
        this.hideQuestionPaperModal();
        this.hideAuthModal();
        this.hideUnlockModal();
        if (window.gateCalculator) window.gateCalculator.hide();
      }
    });
  }

  // --- View Switcher ---
  switchView(viewName) {
    this.currentView = viewName;
    
    // Hide all views
    document.getElementById('view-dashboard')?.classList.add('hidden');
    document.getElementById('view-exam')?.classList.add('hidden');
    document.getElementById('view-results')?.classList.add('hidden');
    document.getElementById('view-history')?.classList.add('hidden');
    document.getElementById('view-saved')?.classList.add('hidden');
    document.getElementById('view-analytics')?.classList.add('hidden');
    document.getElementById('view-admin')?.classList.add('hidden');

    // Update active nav button
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    if (viewName === 'dashboard') document.getElementById('nav-dashboard')?.classList.add('active');
    if (viewName === 'analytics') document.getElementById('nav-analytics')?.classList.add('active');
    if (viewName === 'history') document.getElementById('nav-history')?.classList.add('active');
    if (viewName === 'saved') document.getElementById('nav-saved')?.classList.add('active');
    if (viewName === 'admin') document.getElementById('nav-admin')?.classList.add('active');

    // Show selected view
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.remove('hidden');

    if (viewName === 'dashboard') {
      this.renderDashboard();
    } else if (viewName === 'analytics') {
      this.renderAnalyticsView();
    } else if (viewName === 'history') {
      this.renderHistoryView();
    } else if (viewName === 'saved') {
      this.renderSavedView();
    } else if (viewName === 'admin') {
      this.renderAdminView();
    }
  }

  // ==========================================================================
  // DASHBOARD
  // ==========================================================================
  renderDashboard() {
    this.renderStatsBanner();
    this.renderSubjectPills();
    this.renderTestsGrid();
  }

  renderStatsBanner() {
    const totalTests = this.manifest.length;
    const totalQs = this.manifest.reduce((sum, t) => sum + (t.totalQuestions || 0), 0);
    const attemptedCount = this.history.length;
    const mock80Count = this.manifest.filter(t => t.series === 'GATE 2027 Generated Mock Series').length;
    const originalCount = this.manifest.filter(t => t.series === 'GATE 2027 Original').length;
    const goCount = this.manifest.filter(t => t.series === 'GO Test Series').length;
    const pyqCount = this.manifest.filter(t => t.series === 'GATE PYQs').length;
    
    // Calculate best score percentage
    let bestScore = 0;
    this.history.forEach(h => {
      const pct = (h.score / (h.totalMarks || 1)) * 100;
      if (pct > bestScore) bestScore = pct;
    });

    document.getElementById('dash-stat-tests').textContent = totalTests;
    document.getElementById('dash-stat-qs').textContent = totalQs.toLocaleString();
    document.getElementById('dash-stat-attempted').textContent = attemptedCount;
    document.getElementById('dash-stat-best').textContent = attemptedCount > 0 ? `${bestScore.toFixed(1)}%` : '--';

    // Update counts on series tabs
    const countAll = document.getElementById('count-series-all');
    if (countAll) countAll.textContent = totalTests;
    const countMock80 = document.getElementById('count-series-mock80');
    if (countMock80) countMock80.textContent = mock80Count;
    const countOrig = document.getElementById('count-series-original');
    if (countOrig) countOrig.textContent = originalCount;
    const countGo = document.getElementById('count-series-go');
    if (countGo) countGo.textContent = goCount;
    const countPyq = document.getElementById('count-series-pyq');
    if (countPyq) countPyq.textContent = pyqCount;

    // Brand tag
    const brandTag = document.getElementById('brand-tag-count');
    if (brandTag) brandTag.textContent = `${totalTests} Tests • ${totalQs.toLocaleString()}+ Qs`;
  }

  renderSubjectPills() {
    // Filter subjects by active series if a specific series is selected
    const pool = this.activeFilterSeries === 'All' 
      ? this.manifest 
      : this.manifest.filter(t => t.series === this.activeFilterSeries);

    const subjects = ['All', ...new Set(pool.map(t => t.subject))].sort();
    const container = document.getElementById('subject-pills-container');
    if (!container) return;

    // Reset to 'All' if current selected subject does not exist in the filtered series pool
    if (!subjects.includes(this.activeFilterSubject)) {
      this.activeFilterSubject = 'All';
    }

    container.innerHTML = subjects.map(s => `
      <button class="pill-btn ${this.activeFilterSubject === s ? 'active' : ''}" data-subject="${s}">
        ${s}
      </button>
    `).join('');

    container.querySelectorAll('.pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.activeFilterSubject = btn.dataset.subject;
        container.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.renderTestsGrid();
      });
    });
  }

  renderTestsGrid() {
    const container = document.getElementById('tests-grid-container');
    if (!container) return;

    let filtered = this.manifest.filter(test => {
      const matchSeries = this.activeFilterSeries === 'All' || test.series === this.activeFilterSeries;
      const matchSubject = this.activeFilterSubject === 'All' || test.subject === this.activeFilterSubject;
      const matchType = this.activeFilterType === 'All' || test.testType === this.activeFilterType;
      const matchSearch = !this.searchQuery || 
        test.title.toLowerCase().includes(this.searchQuery) ||
        test.subject.toLowerCase().includes(this.searchQuery) ||
        test.id.toLowerCase().includes(this.searchQuery);
      return matchSeries && matchSubject && matchType && matchSearch;
    });

    // Sort
    if (this.sortBy === 'questions-desc') {
      filtered.sort((a, b) => b.totalQuestions - a.totalQuestions);
    } else if (this.sortBy === 'duration-desc') {
      filtered.sort((a, b) => b.durationMinutes - a.durationMinutes);
    } else if (this.sortBy === 'name-asc') {
      filtered.sort((a, b) => a.title.localeCompare(b.title));
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);">
          <h3>No test papers found matching your filter</h3>
          <p>Try switching series tab, selecting a different subject, or clearing your search query.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(t => {
      // Find latest attempt for this test
      const latestAttempt = this.history.find(h => h.testId === t.id);
      const isMock80 = t.series === 'GATE 2027 Generated Mock Series';
      const isOriginal = t.series === 'GATE 2027 Original';
      const isPYQ = t.series === 'GATE PYQs';
      const canAccess = this.canAccessTest(t);

      let seriesBadgeClass = 'go';
      let seriesBadgeText = '🎓 GO Series';
      if (isMock80) {
        seriesBadgeClass = 'mock80';
        seriesBadgeText = '🎯 65Q Mock';
      } else if (isOriginal) {
        seriesBadgeClass = 'original';
        seriesBadgeText = '🔥 GATE 2027';
      } else if (isPYQ) {
        seriesBadgeClass = 'pyq';
        seriesBadgeText = '🏛️ GATE PYQ';
      }

      return `
        <div class="test-card ${canAccess ? '' : 'is-locked'}" data-testid="${t.id}">
          <div class="card-header-meta">
            <span class="subject-badge">${t.subject}</span>
            <div style="display: flex; gap: 0.35rem; align-items: center;">
              <span class="series-badge ${seriesBadgeClass}">
                ${seriesBadgeText}
              </span>
              ${isPYQ ? `
                <span class="brand-tag" style="background: rgba(16,185,129,0.2); color: #6ee7b7; border-color: rgba(16,185,129,0.4); font-size: 0.68rem; padding: 2px 6px;">🔓 Free</span>
              ` : (canAccess ? `
                <span class="brand-tag" style="background: rgba(99,102,241,0.2); color: #c7d2fe; border-color: rgba(99,102,241,0.4); font-size: 0.68rem; padding: 2px 6px;">🔓 Unlocked</span>
              ` : `
                <span class="lock-pill">🔒 Code Needed</span>
              `)}
            </div>
          </div>

          <div class="test-card-title">${t.title}</div>

          <div class="card-metrics">
            <div class="metric-item">
              <span>❓ ${t.totalQuestions}</span> Qs
            </div>
            <div class="metric-item">
              <span>⏱️ ${t.durationMinutes}</span> Mins
            </div>
            <div class="metric-item">
              <span>🎯 ${t.totalMarks}</span> Marks
            </div>
          </div>

          ${latestAttempt ? `
            <div class="past-score-badge">
              <span>Last Score: <b>${latestAttempt.score.toFixed(2)} / ${latestAttempt.totalMarks}</b> (${((latestAttempt.score/latestAttempt.totalMarks)*100).toFixed(1)}%)</span>
              <span>✅ ${latestAttempt.accuracy}% acc</span>
            </div>
          ` : ''}

          <div class="card-actions">
            ${canAccess ? `
              <button class="btn-start-test" onclick="app.startExam('${t.id}', false)">
                <span>🚀 Start CBT Test</span>
              </button>
              <button class="btn-practice" onclick="app.startExam('${t.id}', true)">
                <span>📖 Practice</span>
              </button>
            ` : `
              <button class="btn-start-test" onclick="app.promptUnlock('${t.id}')" title="Access code required. Contact musicfusion123456@gmail.com">
                <span>🔐 Enter Access Code</span>
              </button>
              <button class="btn-practice" onclick="app.promptUnlock('${t.id}')">
                <span>📧 Get Code</span>
              </button>
            `}
            ${!isPYQ ? `
              <a href="${t.fileName}" target="_blank" class="btn-practice" style="text-decoration:none; display:flex; align-items:center;" title="View original HTML test result">
                <span>📄</span>
              </a>
            ` : `
              <a href="data/tests/${t.id}.json" target="_blank" class="btn-practice" style="text-decoration:none; display:flex; align-items:center;" title="View test dataset">
                <span>💾</span>
              </a>
            `}
          </div>
        </div>
      `;
    }).join('');
  }

  // ==========================================================================
  // EXAM ENGINE
  // ==========================================================================
  async startExam(testId, isPracticeMode = false) {
    const testMeta = this.manifest.find(m => m.id === testId);
    if (testMeta && !this.canAccessTest(testMeta)) {
      this.promptUnlock(testId);
      return;
    }

    const testData = await this.loadTest(testId);
    if (!testData) return;

    this.currentTest = testData;
    this.isPracticeMode = isPracticeMode;
    this.currentQIndex = 0;
    this.currentSection = testData.sections && testData.sections.length > 0 ? testData.sections[0] : 'Technical';
    this.timeElapsed = 0;
    this.timeRemaining = (testData.durationMinutes || 45) * 60;

    // Initialize user responses
    this.userResponses = {};
    testData.questions.forEach((q, idx) => {
      this.userResponses[idx] = {
        value: q.type === 'MSQ' ? [] : '',
        status: 'not-visited',
        timeSpent: 0
      };
    });

    // Mark Q0 as not-answered (visited)
    if (this.userResponses[0]) {
      this.userResponses[0].status = 'not-answered';
    }

    // Switch view
    this.switchView('exam');

    // Setup Exam Header
    document.getElementById('exam-title-text').textContent = testData.title;
    document.getElementById('exam-mode-badge').textContent = isPracticeMode ? 'Practice Mode (Untimed)' : 'GATE CBT Exam Mode';
    document.getElementById('exam-mode-badge').style.background = isPracticeMode ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)';
    document.getElementById('exam-mode-badge').style.color = isPracticeMode ? '#6ee7b7' : '#c7d2fe';

    // Section switcher
    this.renderSectionTabs();

    // Palette profile
    document.getElementById('cand-test-id').textContent = testData.id;

    // Reset question telemetry counters for this exam
    this._telResetExam();

    // Start Timer
    if (this.timerInterval) clearInterval(this.timerInterval);
    if (!isPracticeMode) {
      document.getElementById('exam-timer-box').classList.remove('hidden');
      this.startTimer();
    } else {
      document.getElementById('exam-timer-box').classList.add('hidden');
    }

    // Log exam-start behavior event
    this._telBehavior(isPracticeMode ? 'practice_mode_start' : 'exam_mode_start', {
      testId: this.currentTest.id, testTitle: this.currentTest.title
    });

    // Render first question
    this.renderQuestion(0);
    this.renderPalette();
  }

  renderSectionTabs() {
    const container = document.getElementById('section-tabs-container');
    if (!container) return;

    const sections = this.currentTest.sections || ['Technical'];
    container.innerHTML = sections.map(sec => {
      const qCount = this.currentTest.questions.filter(q => q.section === sec).length;
      return `
        <button class="section-tab-btn ${this.currentSection === sec ? 'active' : ''}" data-sec="${sec}">
          ${sec} (${qCount})
        </button>
      `;
    }).join('');

    container.querySelectorAll('.section-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const sec = btn.dataset.sec;
        this.currentSection = sec;
        container.querySelectorAll('.section-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Find first question in this section
        const firstQ = this.currentTest.questions.findIndex(q => q.section === sec);
        if (firstQ >= 0) {
          this.navigateToQuestion(firstQ);
        }
      });
    });
  }

  startTimer() {
    const display = document.getElementById('timer-digits');
    this.updateTimerDisplay();

    this.timerInterval = setInterval(() => {
      this.timeRemaining--;
      this.timeElapsed++;

      // Track time on current question
      if (this.userResponses[this.currentQIndex]) {
        this.userResponses[this.currentQIndex].timeSpent += 1;
      }

      this.updateTimerDisplay();

      if (this.timeRemaining <= 0) {
        clearInterval(this.timerInterval);
        alert('Time is up! Submitting your test automatically.');
        this.submitExam();
      }
    }, 1000);
  }

  updateTimerDisplay() {
    const display = document.getElementById('timer-digits');
    if (!display) return;

    const hrs = Math.floor(this.timeRemaining / 3600);
    const mins = Math.floor((this.timeRemaining % 3600) / 60);
    const secs = this.timeRemaining % 60;

    const format = (n) => n.toString().padStart(2, '0');
    if (hrs > 0) {
      display.textContent = `${format(hrs)}:${format(mins)}:${format(secs)}`;
    } else {
      display.textContent = `${format(mins)}:${format(secs)}`;
    }

    if (this.timeRemaining <= 300) { // Under 5 minutes
      display.classList.add('warning');
    } else {
      display.classList.remove('warning');
    }
  }

  // --- Question Rendering ---
  getUsableChoiceOptions(question) {
    if (!Array.isArray(question?.options) || question.options.length < 2) return null;

    const options = question.options.map((option, index) => {
      const fallbackId = String.fromCharCode(65 + index);
      const id = typeof option === 'string'
        ? fallbackId
        : String(option?.id ?? fallbackId).trim();
      const textHtml = typeof option === 'string'
        ? option
        : (option?.textHtml ?? option?.html ?? option?.text ?? '');

      if (!id || typeof textHtml !== 'string' || !textHtml.trim()) return null;

      const plainText = textHtml
        .replace(/<[^>]*>/g, ' ')
        .replace(/&nbsp;|&#160;|&#xA0;/gi, ' ')
        .replace(/&amp;/gi, '&')
        .replace(/&#40;|&lpar;/gi, '(')
        .replace(/&#41;|&rpar;/gi, ')')
        .replace(/\s+/g, ' ')
        .trim();
      const isPlaceholder = /fallback-opt/i.test(textHtml) || /^option\s*\(?[a-z0-9]+\)?$/i.test(plainText);

      return { id, textHtml, isPlaceholder };
    });

    if (options.some(option => !option || option.isPlaceholder)) return null;
    return options.map(({ id, textHtml }) => ({ id, textHtml }));
  }

  renderUnavailableChoiceMessage(question, container) {
    const message = document.createElement('div');
    message.className = 'question-data-warning';
    message.textContent = 'Answer choices are unavailable for this question. It cannot be answered or graded until the source data is repaired.';
    container.appendChild(message);

    if (question.discussUrl) {
      const link = document.createElement('a');
      link.className = 'img-discuss-link';
      link.href = question.discussUrl;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'View the original discussion';
      message.appendChild(document.createTextNode(' '));
      message.appendChild(link);
    }
  }

  renderQuestion(index) {
    if (!this.currentTest || index < 0 || index >= this.currentTest.questions.length) return;

    // Telemetry: track time on previous question, record entering this one
    this._telQuestionEnter(index);

    this.currentQIndex = index;
    const q = this.currentTest.questions[index];
    const userResp = this.userResponses[index];

    // If was not-visited, mark as not-answered
    if (userResp.status === 'not-visited') {
      userResp.status = 'not-answered';
    }

    // Sync section tab
    if (q.section && q.section !== this.currentSection) {
      this.currentSection = q.section;
      document.querySelectorAll('.section-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.sec === q.section);
      });
    }

    // Question Number & Badges
    document.getElementById('q-number-display').textContent = `Question ${q.displayNum || (index + 1)}`;
    
    const typeBadge = document.getElementById('q-type-display');
    const questionType = String(q.type || '').toUpperCase();
    typeBadge.textContent = q.typeRaw || questionType || 'Question';
    typeBadge.className = `q-type-badge q-type-${questionType.toLowerCase()}`;

    document.getElementById('q-marks-display').textContent = `+${q.marks} / -${q.penalty || 0}`;

    // Question Text & Diagram
    const promptContainer = document.getElementById('q-prompt-container');
    
    // Inject question body with error fallback on images
    let promptHtml = typeof q.questionHtml === 'string' && q.questionHtml.trim()
      ? q.questionHtml
      : '<p>Question text is unavailable in the source data.</p>';
    // Replace img tags to attach an onerror handler
    promptHtml = promptHtml.replace(/<img\s+([^>]*?)src=["']([^"']+)["']([^>]*?)>/gi, (match, before, src, after) => {
      return `
        <img ${before} src="${src}" ${after} onerror="app.handleImageError(this, '${q.discussUrl}')">
      `;
    });

    promptContainer.innerHTML = promptHtml;

    // Render Options Area
    const optionsContainer = document.getElementById('q-options-container');
    optionsContainer.innerHTML = '';

    const choiceOptions = questionType === 'MCQ' || questionType === 'MSQ'
      ? this.getUsableChoiceOptions(q)
      : null;

    if (questionType === 'MCQ' || questionType === 'MSQ') {
      if (!choiceOptions) {
        this.renderUnavailableChoiceMessage(q, optionsContainer);
      } else if (questionType === 'MCQ') {
        this.renderMcqOptions(q, userResp, optionsContainer, index, choiceOptions);
      } else {
        this.renderMsqOptions(q, userResp, optionsContainer, index, choiceOptions);
      }
    } else if (questionType === 'NAT') {
      this.renderNatInput(q, userResp, optionsContainer);
    }

    // Practice Mode Feedback
    const feedbackBox = document.getElementById('practice-feedback-container');
    if (this.isPracticeMode) {
      feedbackBox.classList.remove('hidden');
      feedbackBox.innerHTML = `
        <div class="practice-feedback-box">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="feedback-title">📖 Practice Mode Tools</span>
            <button class="tool-btn" onclick="app.revealPracticeAnswer(${index})">👁️ Check Answer</button>
          </div>
          <div id="practice-ans-reveal-${index}" class="hidden" style="margin-top: 0.5rem; font-size: 0.9rem;">
            ${(questionType === 'MCQ' || questionType === 'MSQ') && !choiceOptions || !q.correctAnswer
              ? '<b>Answer unavailable:</b> the choices or answer key are missing from the source data.'
              : `<b>Correct Answer:</b> <span style="color: var(--gate-green); font-family: var(--font-mono); font-weight: 700;">${q.correctAnswer}</span>`}
            ${q.discussUrl ? `<div style="margin-top: 0.35rem;"><a href="${q.discussUrl}" target="_blank" class="img-discuss-link">💬 View GateOverflow Discussion</a></div>` : ''}
          </div>
        </div>
      `;
    } else {
      feedbackBox.classList.add('hidden');
    }

    // Update Palette active state
    this.renderPalette();

    // Trigger MathJax typesetting if available
    this.typesetMath();
  }

  handleImageError(imgEl, discussUrl) {
    const parent = imgEl.parentElement;
    const fallbackBox = document.createElement('div');
    fallbackBox.className = 'img-fallback-box';
    fallbackBox.innerHTML = `
      <div class="img-fallback-text">
        📊 <b>Diagram / Figure Question</b> (Refer to original discussion)
      </div>
      ${discussUrl ? `<a href="${discussUrl}" target="_blank" class="img-discuss-link">🔗 View Figure on GateOverflow</a>` : ''}
    `;
    parent.replaceChild(fallbackBox, imgEl);
  }

  typesetMath() {
    if (window.MathJax && window.MathJax.Hub) {
      window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub, 'q-prompt-container']);
      window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub, 'q-options-container']);
    }
  }

  revealPracticeAnswer(index) {
    const el = document.getElementById(`practice-ans-reveal-${index}`);
    if (el) el.classList.toggle('hidden');
  }

  // --- Option Renderers ---
  renderMcqOptions(q, userResp, container, index = this.currentQIndex, options = this.getUsableChoiceOptions(q)) {
    const list = document.createElement('div');
    list.className = 'options-workspace';

    options.forEach(opt => {
      const isSelected = userResp.value === opt.id;
      const row = document.createElement('div');
      row.className = `option-row ${isSelected ? 'selected' : ''}`;
      row.innerHTML = `
        <div class="option-marker">${opt.id}</div>
        <div class="option-text">${opt.textHtml}</div>
      `;

      row.addEventListener('click', () => {
        const wasAnswered = userResp.value !== undefined && userResp.value !== null;
        userResp.value = opt.id;
        list.querySelectorAll('.option-row').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');
        // Telemetry: count answer changes (only after first selection)
        if (wasAnswered) this._telAnswerChange(index);
      });

      list.appendChild(row);
    });

    container.appendChild(list);
  }

  renderMsqOptions(q, userResp, container, index = this.currentQIndex, options = this.getUsableChoiceOptions(q)) {
    const list = document.createElement('div');
    list.className = 'options-workspace';
    // MSQ hint
    const hint = document.createElement('div');
    hint.style.cssText = 'font-size:0.78rem; color: var(--text-muted); margin-bottom:0.5rem; padding: 0.4rem 0.6rem; background: rgba(99,102,241,0.08); border-radius:6px; border-left: 3px solid var(--accent-primary);';
    hint.textContent = 'Multiple Select Question (MSQ) — Select ALL correct options. No negative marking.';
    container.appendChild(hint);

    const selectedVals = Array.isArray(userResp.value) ? userResp.value : [];

    options.forEach(opt => {
      const isSelected = selectedVals.includes(opt.id);
      const row = document.createElement('div');
      row.className = `option-row msq-row ${isSelected ? 'selected' : ''}`;
      row.dataset.optId = opt.id;

      const marker = document.createElement('div');
      marker.className = 'option-marker msq-marker';
      marker.textContent = isSelected ? '✓' : opt.id;

      const text = document.createElement('div');
      text.className = 'option-text';
      text.innerHTML = opt.textHtml;

      row.appendChild(marker);
      row.appendChild(text);

      row.addEventListener('click', () => {
        let currentArr = Array.isArray(userResp.value) ? [...userResp.value] : [];
        if (currentArr.includes(opt.id)) {
          currentArr = currentArr.filter(x => x !== opt.id);
          row.classList.remove('selected');
          marker.textContent = opt.id;
        } else {
          currentArr.push(opt.id);
          currentArr.sort();
          row.classList.add('selected');
          marker.textContent = '✓';
        }
        userResp.value = currentArr;
        // Telemetry: every MSQ toggle counts as an answer change
        this._telAnswerChange(index);
        if (currentArr.length > 0) {
          this.renderPalette();
        }
      });

      list.appendChild(row);
    });

    container.appendChild(list);
  }

  renderNatInput(q, userResp, container) {
    const natBox = document.createElement('div');
    natBox.className = 'nat-input-area';
    natBox.innerHTML = `
      <div class="nat-display">
        <span class="nat-label">Numerical Answer:</span>
        <input type="text" id="nat-input-val" class="nat-input-field" placeholder="Enter value" value="${userResp.value || ''}">
      </div>

      <div class="virtual-keypad">
        <button class="keypad-btn" onclick="app.keypadInput('7')">7</button>
        <button class="keypad-btn" onclick="app.keypadInput('8')">8</button>
        <button class="keypad-btn" onclick="app.keypadInput('9')">9</button>
        <button class="keypad-btn backspace-btn" onclick="app.keypadBackspace()">⌫</button>

        <button class="keypad-btn" onclick="app.keypadInput('4')">4</button>
        <button class="keypad-btn" onclick="app.keypadInput('5')">5</button>
        <button class="keypad-btn" onclick="app.keypadInput('6')">6</button>
        <button class="keypad-btn action-btn" onclick="app.keypadClear()">C</button>

        <button class="keypad-btn" onclick="app.keypadInput('1')">1</button>
        <button class="keypad-btn" onclick="app.keypadInput('2')">2</button>
        <button class="keypad-btn" onclick="app.keypadInput('3')">3</button>
        <button class="keypad-btn" onclick="app.keypadInput('-')">±</button>

        <button class="keypad-btn" onclick="app.keypadInput('0')">0</button>
        <button class="keypad-btn" onclick="app.keypadInput('.')">.</button>
        <button class="keypad-btn" style="grid-column: span 2; background: var(--accent-primary); color: #fff;" onclick="app.saveAndNext()">Save & Next</button>
      </div>
    `;

    container.appendChild(natBox);

    // Sync input box changes
    const inputField = natBox.querySelector('#nat-input-val');
    inputField.addEventListener('input', (e) => {
      userResp.value = e.target.value.trim();
    });
  }

  // --- Keypad Helpers ---
  keypadInput(char) {
    const input = document.getElementById('nat-input-val');
    if (!input) return;

    if (char === '-') {
      if (input.value.startsWith('-')) input.value = input.value.slice(1);
      else input.value = '-' + input.value;
    } else {
      input.value += char;
    }

    if (this.userResponses[this.currentQIndex]) {
      this.userResponses[this.currentQIndex].value = input.value.trim();
    }
  }

  keypadBackspace() {
    const input = document.getElementById('nat-input-val');
    if (!input) return;
    input.value = input.value.slice(0, -1);
    if (this.userResponses[this.currentQIndex]) {
      this.userResponses[this.currentQIndex].value = input.value.trim();
    }
  }

  keypadClear() {
    const input = document.getElementById('nat-input-val');
    if (!input) return;
    input.value = '';
    if (this.userResponses[this.currentQIndex]) {
      this.userResponses[this.currentQIndex].value = '';
    }
  }

  // --- Response Actions ---
  hasAnswer(index) {
    const resp = this.userResponses[index];
    if (!resp) return false;
    if (Array.isArray(resp.value)) return resp.value.length > 0;
    return resp.value !== null && resp.value !== undefined && resp.value.toString().trim() !== '';
  }

  saveAndNext() {
    const userResp = this.userResponses[this.currentQIndex];
    if (this.hasAnswer(this.currentQIndex)) {
      userResp.status = 'answered';
    } else {
      userResp.status = 'not-answered';
    }

    if (this.currentQIndex < this.currentTest.questions.length - 1) {
      this.renderQuestion(this.currentQIndex + 1);
    } else {
      this.renderPalette();
    }
  }

  markForReview() {
    const userResp = this.userResponses[this.currentQIndex];
    if (this.hasAnswer(this.currentQIndex)) {
      userResp.status = 'marked-answered';
    } else {
      userResp.status = 'marked';
    }

    if (this.currentQIndex < this.currentTest.questions.length - 1) {
      this.renderQuestion(this.currentQIndex + 1);
    } else {
      this.renderPalette();
    }
  }

  clearResponse() {
    const userResp = this.userResponses[this.currentQIndex];
    const q = this.currentTest.questions[this.currentQIndex];
    userResp.value = q.type === 'MSQ' ? [] : '';
    userResp.status = 'not-answered';
    this.renderQuestion(this.currentQIndex);
  }

  prevQuestion() {
    if (this.currentQIndex > 0) {
      this.renderQuestion(this.currentQIndex - 1);
    }
  }

  navigateToQuestion(index) {
    if (index >= 0 && index < this.currentTest.questions.length) {
      this.renderQuestion(index);
    }
  }

  // --- Palette Rendering ---
  renderPalette() {
    const container = document.getElementById('palette-grid-container');
    if (!container || !this.currentTest) return;

    let answeredCount = 0;
    let notAnsweredCount = 0;
    let notVisitedCount = 0;
    let markedCount = 0;
    let markedAnsweredCount = 0;

    Object.values(this.userResponses).forEach(r => {
      if (r.status === 'answered') answeredCount++;
      else if (r.status === 'not-answered') notAnsweredCount++;
      else if (r.status === 'not-visited') notVisitedCount++;
      else if (r.status === 'marked') markedCount++;
      else if (r.status === 'marked-answered') markedAnsweredCount++;
    });

    // Update counts
    document.getElementById('legend-count-answered').textContent = answeredCount;
    document.getElementById('legend-count-not-answered').textContent = notAnsweredCount;
    document.getElementById('legend-count-not-visited').textContent = notVisitedCount;
    document.getElementById('legend-count-marked').textContent = markedCount;
    document.getElementById('legend-count-marked-answered').textContent = markedAnsweredCount;

    // Palette grid
    container.innerHTML = this.currentTest.questions.map((q, idx) => {
      const resp = this.userResponses[idx];
      const statusClass = `status-${resp.status}`;
      const isCurrent = idx === this.currentQIndex ? 'current' : '';

      return `
        <button class="palette-q-btn ${statusClass} ${isCurrent}" onclick="app.navigateToQuestion(${idx})">
          ${q.displayNum || (idx + 1)}
        </button>
      `;
    }).join('');
  }

  // --- Modals ---
  showQuestionPaperModal() {
    const modal = document.getElementById('modal-qpaper');
    const body = document.getElementById('qpaper-modal-body');
    if (!modal || !body || !this.currentTest) return;

    body.innerHTML = this.currentTest.questions.map((q, idx) => `
      <div style="border-bottom: 1px solid var(--border-subtle); padding: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-weight: 700;">
          <span>Q #${idx + 1} (${q.type} - ${q.marks} Marks)</span>
          <span style="color: var(--text-muted);">${q.section}</span>
        </div>
        <div>${q.questionHtml}</div>
      </div>
    `).join('');

    modal.classList.remove('hidden');
    this.typesetMath();
  }

  hideQuestionPaperModal() {
    document.getElementById('modal-qpaper')?.classList.add('hidden');
  }

  showSubmitConfirmation() {
    const modal = document.getElementById('modal-submit');
    if (!modal) return;

    let answered = 0, notAnswered = 0, marked = 0, notVisited = 0;
    Object.values(this.userResponses).forEach(r => {
      if (r.status === 'answered' || r.status === 'marked-answered') answered++;
      else if (r.status === 'not-answered') notAnswered++;
      else if (r.status === 'marked') marked++;
      else notVisited++;
    });

    document.getElementById('submit-stat-total').textContent = this.currentTest.questions.length;
    document.getElementById('submit-stat-answered').textContent = answered;
    document.getElementById('submit-stat-not-answered').textContent = notAnswered;
    document.getElementById('submit-stat-marked').textContent = marked;
    document.getElementById('submit-stat-not-visited').textContent = notVisited;

    modal.classList.remove('hidden');
  }

  hideSubmitModal() {
    document.getElementById('modal-submit')?.classList.add('hidden');
  }

  // ==========================================================================
  // EVALUATION & RESULTS
  // ==========================================================================
  submitExam() {
    this.hideSubmitModal();
    if (this.timerInterval) clearInterval(this.timerInterval);

    // Compute evaluation
    const questions = this.currentTest.questions;
    let score = 0;
    let maxMarks = this.currentTest.totalMarks || 0;
    let positiveMarks = 0;
    let penaltyMarks = 0;
    let correctCount = 0;
    let incorrectCount = 0;
    let unattemptedCount = 0;

    const evaluatedQuestions = questions.map((q, idx) => {
      const resp = this.userResponses[idx];
      const choiceDataUnavailable = ['MCQ', 'MSQ'].includes(String(q.type || '').toUpperCase())
        && !this.getUsableChoiceOptions(q);
      const hasAnswer = !choiceDataUnavailable && this.hasAnswer(idx);
      let isCorrect = false;
      let marksAwarded = 0;

      if (!hasAnswer) {
        unattemptedCount++;
      } else {
        // Evaluate
        if (q.type === 'MCQ') {
          const userVal = resp.value ? resp.value.toString().trim().toUpperCase() : '';
          const correctVal = q.correctAnswer ? q.correctAnswer.trim().toUpperCase() : '';
          isCorrect = userVal === correctVal;

          if (isCorrect) {
            marksAwarded = q.marks;
            positiveMarks += q.marks;
            correctCount++;
          } else {
            const pen = q.penalty || (q.marks / 3);
            marksAwarded = -pen;
            penaltyMarks += pen;
            incorrectCount++;
          }
        } else if (q.type === 'MSQ') {
          // Multiple select
          const userArr = Array.isArray(resp.value) ? [...resp.value].map(x => x.trim().toUpperCase()).sort() : [];
          // Correct answer can be 'A;B' or 'A, B' or 'A;B;C'
          const correctArr = (q.correctAnswer || '').split(/[;,]/).map(x => x.trim().toUpperCase()).filter(Boolean).sort();
          
          isCorrect = userArr.length === correctArr.length && userArr.every((v, i) => v === correctArr[i]);

          if (isCorrect) {
            marksAwarded = q.marks;
            positiveMarks += q.marks;
            correctCount++;
          } else {
            // In GATE, MSQ has NO negative marking!
            marksAwarded = 0;
            incorrectCount++;
          }
        } else if (q.type === 'NAT') {
          // Numerical Type
          const userNum = parseFloat(resp.value);
          const rawExpected = (q.correctAnswer || '').trim();
          
          if (!isNaN(userNum)) {
            // Check if expected is a range e.g. "74.01:75.01" or "74.01 to 75.01"
            if (rawExpected.includes(':') || rawExpected.toLowerCase().includes('to')) {
              const parts = rawExpected.includes(':') ? rawExpected.split(':') : rawExpected.toLowerCase().split('to');
              const minVal = parseFloat(parts[0]);
              const maxVal = parseFloat(parts[1]);
              if (!isNaN(minVal) && !isNaN(maxVal)) {
                isCorrect = userNum >= Math.min(minVal, maxVal) && userNum <= Math.max(minVal, maxVal);
              }
            } else {
              const expectedNum = parseFloat(rawExpected);
              if (!isNaN(expectedNum)) {
                // Tolerance 0.01
                isCorrect = Math.abs(userNum - expectedNum) <= 0.01;
              }
            }
          }

          if (isCorrect) {
            marksAwarded = q.marks;
            positiveMarks += q.marks;
            correctCount++;
          } else {
            // In GATE, NAT has NO negative marking!
            marksAwarded = 0;
            incorrectCount++;
          }
        }
      }

      score += marksAwarded;

      return {
        ...q,
        choiceDataUnavailable,
        correctAnswer: choiceDataUnavailable || !q.correctAnswer ? 'Unavailable' : q.correctAnswer,
        userResponse: resp.value,
        userStatus: resp.status,
        isCorrect,
        isAttempted: hasAnswer,
        marksAwarded: Number(marksAwarded.toFixed(2)),
        timeSpent: resp.timeSpent || 0
      };
    });

    score = Number(score.toFixed(2));
    if (score < 0) score = 0; // Net score floor

    const attemptedCount = correctCount + incorrectCount;
    const accuracy = attemptedCount > 0 ? Number(((correctCount / attemptedCount) * 100).toFixed(1)) : 0;

    const resultRecord = {
      testId: this.currentTest.id,
      testTitle: this.currentTest.title,
      subject: this.currentTest.subject,
      testType: this.currentTest.testType,
      date: new Date().toISOString(),
      score,
      totalMarks: maxMarks,
      positiveMarks: Number(positiveMarks.toFixed(2)),
      penaltyMarks: Number(penaltyMarks.toFixed(2)),
      totalQuestions: questions.length,
      attemptedCount,
      correctCount,
      incorrectCount,
      unattemptedCount,
      accuracy,
      timeElapsed: this.timeElapsed,
      questions: evaluatedQuestions
    };

    this.lastResultData = resultRecord;
    this.saveHistory(resultRecord);
    this.syncAttemptToDb(resultRecord);

    // Telemetry: flush per-question data and log submit event
    this._telFlushQuestions(resultRecord);
    this._telBehavior('exam_submit', {
      testId: this.currentTest.id,
      score: resultRecord.score,
      totalMarks: resultRecord.totalMarks,
      accuracy: resultRecord.accuracy,
      attemptedCount: resultRecord.attemptedCount,
      totalQuestions: resultRecord.totalQuestions
    });

    // Switch to Results View
    this.switchView('results');
    this.renderResultsView();
  }

  async syncAttemptToDb(record) {
    const email = this.currentUser ? this.currentUser.email : 'guest@example.com';
    try {
      await fetch('/api/attempts/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, attempt: record })
      });
    } catch (e) {
      console.warn('DB sync offline:', e);
    }
  }

  // --- Render Results View ---
  renderResultsView() {
    const data = this.lastResultData;
    if (!data) return;

    document.getElementById('res-test-title').textContent = data.testTitle;
    document.getElementById('res-test-date').textContent = new Date(data.date).toLocaleString();

    // Stats
    document.getElementById('res-score-display').textContent = `${data.score} / ${data.totalMarks}`;
    document.getElementById('res-accuracy-display').textContent = `${data.accuracy}%`;
    document.getElementById('res-attempted-display').textContent = `${data.attemptedCount} / ${data.totalQuestions}`;
    
    const mins = Math.floor(data.timeElapsed / 60);
    const secs = data.timeElapsed % 60;
    document.getElementById('res-time-display').textContent = `${mins}m ${secs}s`;

    document.getElementById('res-count-correct').textContent = data.correctCount;
    document.getElementById('res-count-incorrect').textContent = data.incorrectCount;
    document.getElementById('res-count-unattempted').textContent = data.unattemptedCount;

    // Setup filter tabs
    const filterTabs = document.querySelectorAll('.solution-filter-bar .filter-tab');
    filterTabs.forEach(tab => {
      tab.classList.toggle('active', tab.dataset.filter === this.solutionFilter);
      tab.onclick = () => {
        this.solutionFilter = tab.dataset.filter;
        filterTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.renderSolutionList();
      };
    });

    this.renderSolutionList();
  }

  renderSolutionList() {
    const container = document.getElementById('solution-list-container');
    if (!container || !this.lastResultData) return;

    const questions = this.lastResultData.questions.filter(q => {
      if (this.solutionFilter === 'correct') return q.isAttempted && q.isCorrect;
      if (this.solutionFilter === 'incorrect') return q.isAttempted && !q.isCorrect;
      if (this.solutionFilter === 'unattempted') return !q.isAttempted;
      if (this.solutionFilter === 'marked') return q.userStatus === 'marked' || q.userStatus === 'marked-answered';
      return true; // 'all'
    });

    if (questions.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-muted);">No questions match this filter.</div>`;
      return;
    }

    container.innerHTML = questions.map(q => {
      let statusClass = 'unattempted';
      let statusText = 'Unattempted';
      if (q.isAttempted) {
        if (q.isCorrect) {
          statusClass = 'correct';
          statusText = `Correct (+${q.marksAwarded})`;
        } else {
          statusClass = 'incorrect';
          statusText = `Incorrect (${q.marksAwarded})`;
        }
      }

      const isBookmarked = this.isBookmarked(this.lastResultData.testId, q.index);

      // Format user response
      let userAnsDisplay = 'None';
      if (q.isAttempted) {
        if (Array.isArray(q.userResponse)) {
          userAnsDisplay = q.userResponse.join(', ');
        } else {
          userAnsDisplay = q.userResponse;
        }
      }

      return `
        <div class="solution-card ${statusClass}">
          <div class="solution-meta">
            <div style="display:flex; align-items:center; gap:0.6rem;">
              <span style="font-weight: 800; font-size: 1.05rem;">Q #${q.displayNum || (q.index + 1)}</span>
              <span class="q-type-badge q-type-${q.type.toLowerCase()}">${q.type}</span>
              <span class="solution-status-badge ${statusClass}">${statusText}</span>
            </div>

            <div style="display:flex; align-items:center; gap: 0.5rem;">
              <button class="tool-btn" onclick="app.toggleBookmark('${this.lastResultData.testId}', ${q.index}, ${JSON.stringify(q).replace(/"/g, '&quot;')})">
                ${isBookmarked ? '⭐ Saved' : '☆ Bookmark'}
              </button>
              ${q.discussUrl ? `
                <a href="${q.discussUrl}" target="_blank" class="solution-discuss-btn">
                  💬 GateOverflow
                </a>
              ` : ''}
            </div>
          </div>

          <div class="question-prompt">
            ${q.questionHtml}
          </div>

          <div class="answer-comparison-box">
            <div class="ans-col">
              <span class="ans-title">Your Answer</span>
              <span class="ans-val ${q.isCorrect ? 'user-correct' : (q.isAttempted ? 'user-wrong' : '')}">
                ${userAnsDisplay}
              </span>
            </div>

            <div class="ans-col">
              <span class="ans-title">Correct Answer</span>
              <span class="ans-val correct-ans">
                ${q.correctAnswer}
              </span>
            </div>

            <div class="ans-col">
              <span class="ans-title">Marks</span>
              <span class="ans-val" style="color: ${q.marksAwarded > 0 ? 'var(--gate-green)' : (q.marksAwarded < 0 ? 'var(--gate-red)' : 'var(--text-muted)')};">
                ${q.marksAwarded > 0 ? `+${q.marksAwarded}` : q.marksAwarded}
              </span>
            </div>
          </div>
        </div>
      `;
    }).join('');

    this.typesetMath();
  }

  updateBookmarkButtonState(key) {
    // Re-render solution list or saved view if active
    if (this.currentView === 'results') {
      this.renderSolutionList();
    } else if (this.currentView === 'saved') {
      this.renderSavedView();
    }
  }

  // ==========================================================================
  // HISTORY VIEW
  // ==========================================================================
  renderHistoryView() {
    const container = document.getElementById('history-list-container');
    if (!container) return;

    if (this.history.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
          <h3>No test attempts yet</h3>
          <p>Start a test from the Dashboard to see your results and performance tracking here.</p>
          <button class="btn-start-test" style="max-width: 200px; margin: 1rem auto;" onclick="app.switchView('dashboard')">Browse Tests</button>
        </div>
      `;
      return;
    }

    container.innerHTML = this.history.map((h, idx) => `
      <div class="test-card" style="margin-bottom: 1rem;">
        <div class="card-header-meta">
          <span class="subject-badge">${h.subject}</span>
          <span style="color: var(--text-muted); font-size: 0.8rem;">${new Date(h.date).toLocaleDateString()}</span>
        </div>

        <div class="test-card-title">${h.testTitle}</div>

        <div class="card-metrics">
          <div class="metric-item">
            <span>Score:</span> <b>${h.score} / ${h.totalMarks}</b>
          </div>
          <div class="metric-item">
            <span>Accuracy:</span> <b>${h.accuracy}%</b>
          </div>
          <div class="metric-item">
            <span>Attempted:</span> <b>${h.attemptedCount} / ${h.totalQuestions}</b>
          </div>
        </div>

        <div class="card-actions">
          <button class="btn-start-test" onclick="app.reviewHistoryItem(${idx})">
            <span>🔍 Review Answers</span>
          </button>
          <button class="btn-practice" onclick="app.startExam('${h.testId}', false)">
            <span>🔄 Retake Test</span>
          </button>
        </div>
      </div>
    `).join('');
  }

  reviewHistoryItem(index) {
    if (this.history[index]) {
      this.lastResultData = this.history[index];
      this.switchView('results');
      this.renderResultsView();
    }
  }

  // ==========================================================================
  // SAVED / BOOKMARKS VIEW
  // ==========================================================================
  renderSavedView() {
    const container = document.getElementById('saved-list-container');
    if (!container) return;

    if (this.bookmarks.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
          <h3>No bookmarked questions</h3>
          <p>You can star / bookmark difficult questions during result review to revise them here.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.bookmarks.map(b => {
      const q = b.question;
      return `
        <div class="solution-card" style="margin-bottom: 1.5rem;">
          <div class="solution-meta">
            <div>
              <span class="subject-badge">${b.testTitle}</span>
              <span style="font-weight: 800; margin-left: 0.5rem;">Q #${(q.index + 1)}</span>
              <span class="q-type-badge q-type-${(q.type || 'mcq').toLowerCase()}">${q.type}</span>
            </div>

            <div style="display:flex; gap: 0.5rem;">
              <button class="tool-btn" onclick="app.toggleBookmark('${b.testId}', ${b.qIndex}, null)">
                🗑️ Remove
              </button>
              ${q.discussUrl ? `
                <a href="${q.discussUrl}" target="_blank" class="solution-discuss-btn">
                  💬 GateOverflow
                </a>
              ` : ''}
            </div>
          </div>

          <div class="question-prompt">
            ${q.questionHtml}
          </div>

          <div class="answer-comparison-box">
            <div class="ans-col">
              <span class="ans-title">Correct Answer</span>
              <span class="ans-val correct-ans">${q.correctAnswer}</span>
            </div>
          </div>
        </div>
      `;
    }).join('');

    this.typesetMath();
  }

  // ==========================================================================
  // PERFORMANCE ANALYZER & GRADING SYSTEM
  // ==========================================================================
  renderAnalyticsView() {
    // User header & greeting
    const userName = this.currentUser ? (this.currentUser.name || this.currentUser.email) : 'Guest Student';
    const userHeading = document.getElementById('analytics-user-heading');
    if (userHeading) userHeading.textContent = `Candidate Diagnostic: ${userName}`;

    const statusPill = document.getElementById('analytics-access-status-pill');
    if (statusPill) {
      const hasFull = this.currentUser && (this.currentUser.hasFullAccess || this.currentUser.isAdmin);
      if (hasFull) {
        statusPill.innerHTML = `
          <span class="brand-tag" style="background: rgba(16,185,129,0.2); color: #6ee7b7; border-color: rgba(16,185,129,0.4);">
            🔓 Full Access Granted (All 271 Tests)
          </span>
        `;
      } else {
        statusPill.innerHTML = `
          <button class="lock-pill" onclick="app.showUnlockModal()" style="cursor: pointer; padding: 6px 12px; font-size: 0.8rem;" title="Enter Code or Contact musicfusion123456@gmail.com">
            🔒 Code Required for Mocks (PYQs Free) • Click to Unlock
          </button>
        `;
      }
    }

    const attempts = this.history || [];
    const totalAttempts = attempts.length;

    // Calculate aggregated stats
    let totalScoreSum = 0;
    let totalMaxMarks = 0;
    let totalAccuracySum = 0;

    // Subject breakdown dictionary
    const subjectStats = {
      'Algorithms': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Data Structures': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Operating Systems': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Database Management Systems': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Computer Networks': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Theory of Computation': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Compiler Design': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Computer Organization': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Digital Logic': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Discrete Mathematics': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'Engineering Mathematics': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 },
      'General Aptitude': { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 }
    };

    attempts.forEach(att => {
      totalScoreSum += (att.score || 0);
      totalMaxMarks += (att.totalMarks || 100);
      totalAccuracySum += (att.accuracy || 0);

      // Analyze question by question if available
      if (att.questions && att.questions.length > 0) {
        att.questions.forEach(q => {
          let subj = q.subject || att.subject || 'Technical';
          // Normalize subject keys
          if (subj.includes('Algo')) subj = 'Algorithms';
          else if (subj.includes('Data Struct')) subj = 'Data Structures';
          else if (subj.includes('Operat')) subj = 'Operating Systems';
          else if (subj.includes('DBMS') || subj.includes('Database')) subj = 'Database Management Systems';
          else if (subj.includes('Network')) subj = 'Computer Networks';
          else if (subj.includes('TOC') || subj.includes('Computation') || subj.includes('Automata')) subj = 'Theory of Computation';
          else if (subj.includes('Compiler')) subj = 'Compiler Design';
          else if (subj.includes('COA') || subj.includes('Organization') || subj.includes('Architecture')) subj = 'Computer Organization';
          else if (subj.includes('Digital')) subj = 'Digital Logic';
          else if (subj.includes('Discrete')) subj = 'Discrete Mathematics';
          else if (subj.includes('Aptitude') || q.section === 'General Aptitude') subj = 'General Aptitude';
          else if (subj.includes('Math')) subj = 'Engineering Mathematics';
          else subj = 'Algorithms';

          if (!subjectStats[subj]) {
            subjectStats[subj] = { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 };
          }

          subjectStats[subj].totalQs++;
          subjectStats[subj].maxScore += (q.marks || 1);
          if (q.isCorrect) {
            subjectStats[subj].correct++;
            subjectStats[subj].score += (q.marks || 1);
          } else if (q.isAttempted) {
            subjectStats[subj].incorrect++;
            subjectStats[subj].score -= (q.marks ? q.marks / 3 : 0.33);
          }
        });
      } else {
        // Fallback by paper subject
        let subj = att.subject || 'Algorithms';
        if (!subjectStats[subj]) subjectStats[subj] = { totalQs: 0, correct: 0, incorrect: 0, score: 0, maxScore: 0 };
        subjectStats[subj].totalQs += (att.totalQuestions || 25);
        subjectStats[subj].correct += (att.correctCount || 0);
        subjectStats[subj].incorrect += (att.incorrectCount || 0);
        subjectStats[subj].score += (att.score || 0);
        subjectStats[subj].maxScore += (att.totalMarks || 100);
      }
    });

    const avgScorePct = totalMaxMarks > 0 ? ((totalScoreSum / totalMaxMarks) * 100).toFixed(1) : 0;
    const avgAccuracyPct = totalAttempts > 0 ? (totalAccuracySum / totalAttempts).toFixed(1) : 0;

    // Find best and worst subjects
    let bestSubject = '--';
    let bestAcc = -1;
    let worstSubject = '--';
    let worstAcc = 101;

    Object.entries(subjectStats).forEach(([subj, data]) => {
      const attempted = data.correct + data.incorrect;
      if (attempted >= 2) {
        const acc = (data.correct / attempted) * 100;
        if (acc > bestAcc) {
          bestAcc = acc;
          bestSubject = subj;
        }
        if (acc < worstAcc) {
          worstAcc = acc;
          worstSubject = subj;
        }
      }
    });

    if (bestSubject === '--' && totalAttempts > 0) bestSubject = 'Algorithms';
    if (worstSubject === '--' && totalAttempts > 0) worstSubject = 'Theory of Computation';

    // Populate top stat cards
    document.getElementById('ana-stat-tests').textContent = totalAttempts;
    document.getElementById('ana-stat-avg').textContent = `${avgScorePct}%`;
    document.getElementById('ana-stat-acc').textContent = `${avgAccuracyPct}%`;
    document.getElementById('ana-stat-strong').textContent = bestSubject;
    document.getElementById('ana-stat-weak').textContent = worstSubject;

    // Subject mastery matrix grid
    const subjectGrid = document.getElementById('analytics-subject-grid');
    if (subjectGrid) {
      subjectGrid.innerHTML = Object.entries(subjectStats).map(([subj, data]) => {
        const attempted = data.correct + data.incorrect;
        const accuracy = attempted > 0 ? Math.round((data.correct / attempted) * 100) : 0;
        
        let statusBadge = '<span class="status-badge-avg">Pending Evaluation</span>';
        let barColor = 'var(--text-muted)';
        if (attempted > 0) {
          if (accuracy >= 70) {
            statusBadge = '<span class="status-badge-strong">Mastered (High Yield)</span>';
            barColor = 'var(--gate-green)';
          } else if (accuracy >= 45) {
            statusBadge = '<span class="status-badge-avg">Moderate Accuracy</span>';
            barColor = '#f59e0b';
          } else {
            statusBadge = '<span class="status-badge-weak">Needs Revision</span>';
            barColor = 'var(--gate-red)';
          }
        }

        return `
          <div class="subject-mastery-card">
            <div class="subject-header-row">
              <span style="font-weight: 700; font-size: 0.95rem;">${subj}</span>
              ${statusBadge}
            </div>
            
            <div class="subject-mastery-progress">
              <div class="subject-mastery-bar" style="width: ${Math.max(accuracy, 4)}%; background: ${barColor};"></div>
            </div>

            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-secondary);">
              <span>Accuracy: <b>${accuracy}%</b> (${data.correct} / ${attempted})</span>
              <span>Questions Met: <b>${data.totalQs}</b></span>
            </div>
          </div>
        `;
      }).join('');
    }

    // AI Insight text
    const insightBox = document.getElementById('analytics-insight-text');
    if (insightBox) {
      if (totalAttempts === 0) {
        insightBox.innerHTML = `Start practicing from the <strong>80 Full-Length Mocks</strong> or <strong>Official GATE PYQs</strong> to generate your real-time accuracy matrix and personalized focus areas!`;
      } else {
        insightBox.innerHTML = `
          Diagnostic Report: Your strongest performance is in <strong>${bestSubject}</strong> (${bestAcc > 0 ? bestAcc.toFixed(1) + '%' : 'Strong'}).
          We recommend prioritizing revision and formula review for <strong>${worstSubject}</strong> to minimize negative marks.
          Practice numerical range accuracy (NAT) in your next full mock session.
        `;
      }
    }

    // Attempt history table
    const tbody = document.getElementById('analytics-attempts-tbody');
    if (tbody) {
      if (attempts.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
              No test attempts recorded yet. Launch a test from the library to build your performance profile!
            </td>
          </tr>
        `;
      } else {
        tbody.innerHTML = attempts.map((att, idx) => `
          <tr>
            <td style="font-weight: 700; color: var(--text-primary);">${att.testTitle}</td>
            <td><span class="subject-badge">${att.subject}</span></td>
            <td>${new Date(att.date).toLocaleDateString()}</td>
            <td style="font-family: var(--font-mono); font-weight: 700; color: #c7d2fe;">${att.score.toFixed(2)} / ${att.totalMarks}</td>
            <td style="font-weight: 700; color: ${att.accuracy >= 65 ? 'var(--gate-green)' : '#f59e0b'};">${att.accuracy}%</td>
            <td>${Math.floor(att.timeElapsed / 60)}m ${att.timeElapsed % 60}s</td>
            <td>
              <button class="btn-toggle-access grant" onclick="app.reviewHistoryItem(${idx})">
                🔍 Review
              </button>
            </td>
          </tr>
        `).join('');
      }
    }
  }

  // ==========================================================================
  // ADMIN PANEL
  // ==========================================================================
  async renderAdminView() {
    // Verify admin access
    const isAdmin = this.currentUser && (this.currentUser.isAdmin || (this.currentUser.email && this.currentUser.email.toLowerCase().trim() === this.ADMIN_EMAIL));
    
    const tbody = document.getElementById('admin-users-tbody');
    if (!tbody) return;

    if (!isAdmin) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-muted);">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">🔒</div>
            <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">Administrator Privileges Required</h3>
            <p style="margin-bottom: 1rem; max-width: 400px; margin-left: auto; margin-right: auto;">Only the master admin account <code style="color:#c7d2fe;">musicfusion123456@gmail.com</code> can manage student access, view user data, and grant/revoke permissions.</p>
            <button class="btn-cbt btn-primary" onclick="app.showAuthModal()">🔑 Sign in as Administrator</button>
          </td>
        </tr>
      `;
      return;
    }

    // Show loading state
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2rem; color: var(--text-muted);">⏳ Loading user data...</td></tr>`;
    await Promise.all([
      this.refreshAdminData(),
      this.refreshTelemetryDashboard()
    ]);
  }

  async refreshAdminData() {
    const adminEmail = this.currentUser ? this.currentUser.email : this.ADMIN_EMAIL;
    const tbody = document.getElementById('admin-users-tbody');

    try {
      const resp = await fetch('/api/admin/data', {
        headers: { 'Authorization': `Bearer ${this.currentUser?.adminToken || ''}` },
      });
      if (!resp.ok) {
        const error = new Error('Failed to load admin dataset');
        error.status = resp.status;
        throw error;
      }
      const data = await resp.json();

      document.getElementById('admin-stat-users').textContent = data.totalUsers || 1;
      document.getElementById('admin-stat-attempts').textContent = data.totalAttempts || 0;
      document.getElementById('admin-stat-unlocked').textContent = data.unlockedUsers || 1;

      if (!data.users || data.users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem;">No students registered yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.users.map(u => {
        const isMaster = u.email.toLowerCase().trim() === this.ADMIN_EMAIL;
        // API returns has_access (boolean from Python dict), tests_taken, avg_score, avg_accuracy, created_at, last_login
        const hasAccess = u.has_access === true || u.has_access == 1;
        const statusBadge = hasAccess
          ? `<span class="brand-tag" style="background: rgba(16,185,129,0.2); color: #6ee7b7; border-color: rgba(16,185,129,0.4);">🔓 Full Access</span>`
          : `<span class="lock-pill">🔒 Locked</span>`;
        
        const joinedStr = u.created_at ? new Date(u.created_at).toLocaleDateString() : 'Active';
        const lastLoginStr = (u.last_login && u.last_login !== 'Never') ? new Date(u.last_login).toLocaleDateString() : 'Never';
        const testsTaken = u.tests_taken || 0;
        const avgScore = (u.avg_score || 0).toFixed(1);
        const avgAcc = (u.avg_accuracy || 0).toFixed(1);

        return `
          <tr>
            <td>
              <div style="font-weight: 700; color: var(--text-primary);">${u.name || 'User'}</div>
              <div style="font-size: 0.75rem; font-family: var(--font-mono); color: var(--text-muted);">${u.email}</div>
              <div style="font-size: 0.7rem; color: var(--text-muted); margin-top:2px;">Last login: ${lastLoginStr}</div>
            </td>
            <td><span class="subject-badge" style="background: ${u.role === 'admin' ? 'rgba(99,102,241,0.25)' : 'var(--bg-secondary)'}; color: ${u.role === 'admin' ? '#c7d2fe' : 'var(--text-secondary)'}">${u.role.toUpperCase()}</span></td>
            <td style="color: var(--text-muted); font-size:0.82rem;">${joinedStr}</td>
            <td style="font-weight: 700; color: var(--text-primary); text-align:center;">${testsTaken}</td>
            <td style="font-weight: 700; color: #c7d2fe; text-align:center;">${avgScore}%<br><span style="font-size:0.7rem;color:var(--text-muted);">${avgAcc}% acc</span></td>
            <td>${statusBadge}</td>
            <td>
              ${isMaster ? `
                <span style="font-size: 0.78rem; color: var(--text-muted); font-weight: 600;">👑 Master Admin</span>
              ` : `
                <button class="btn-toggle-access ${hasAccess ? 'revoke' : 'grant'}" onclick="app.toggleUserAccess('${u.email}', ${!hasAccess})">
                  ${hasAccess ? '🔒 Revoke Access' : '🔓 Grant Access'}
                </button>
              `}
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      if (err.status === 401) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2rem; color:var(--text-muted);">Your administrator session expired. Please sign in again to load admin data.</td></tr>`;
        this.saveUserSession(null);
        this.showAuthModal();
        return;
      }
      console.warn('Admin API offline, showing local fallback:', err);
      document.getElementById('admin-stat-users').textContent = 1;
      document.getElementById('admin-stat-attempts').textContent = this.history.length;
      document.getElementById('admin-stat-unlocked').textContent = 1;

      tbody.innerHTML = `
        <tr>
          <td>
            <div style="font-weight: 700; color: var(--text-primary);">System Administrator</div>
            <div style="font-size: 0.75rem; font-family: var(--font-mono); color: var(--text-muted);">${this.ADMIN_EMAIL}</div>
          </td>
          <td><span class="subject-badge" style="background: rgba(99,102,241,0.2); color:#c7d2fe;">ADMIN</span></td>
          <td style="color:var(--text-muted);">Active</td>
          <td style="font-weight:700; text-align:center;">${this.history.length}</td>
          <td style="font-weight:700; color:#c7d2fe; text-align:center;">--</td>
          <td><span class="brand-tag" style="background: rgba(16,185,129,0.2); color: #6ee7b7;">🔓 Full Access</span></td>
          <td><span style="font-size: 0.78rem; color: var(--text-muted); font-weight:600;">👑 Master Admin</span></td>
        </tr>
        <tr>
          <td colspan="7" style="text-align:center; padding:0.75rem 1rem; color:var(--text-muted); font-size:0.8rem; background: rgba(245,158,11,0.05);">
            ⚠️ Admin service unavailable — check the server response and Render logs, then reload this page.
          </td>
        </tr>
      `;
    }
  }

  async toggleUserAccess(targetEmail, grant) {
    const adminEmail = this.currentUser ? this.currentUser.email : this.ADMIN_EMAIL;
    try {
      const resp = await fetch('/api/admin/toggle-access', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.currentUser?.adminToken || ''}`,
        },
        body: JSON.stringify({ targetEmail, grant })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Failed to update user access');
      alert(`Full access ${grant ? 'granted' : 'revoked'} for ${targetEmail}`);
      this.refreshAdminData();
    } catch (e) {
      alert(`Failed to update access: ${e.message}`);
    }
  }

  // ==========================================================================
  // ADMIN TELEMETRY DASHBOARD
  // ==========================================================================
  switchAdminTab(tabName) {
    const tabs = ['users', 'telemetry', 'audit'];
    tabs.forEach(t => {
      const btn = document.getElementById(`tab-btn-admin-${t}`);
      const sec = document.getElementById(`admin-sec-${t}`);
      if (btn) btn.classList.toggle('active', t === tabName);
      if (sec) sec.classList.toggle('hidden', t !== tabName);
    });

    if (tabName === 'telemetry' || tabName === 'audit') {
      this.refreshTelemetryDashboard();
    }
  }

  async refreshTelemetryDashboard() {
    const adminEmail = this.currentUser ? this.currentUser.email : this.ADMIN_EMAIL;

    try {
      const resp = await fetch('/api/admin/telemetry', {
        headers: { 'Authorization': `Bearer ${this.currentUser?.adminToken || ''}` },
      });
      if (!resp.ok) throw new Error('Telemetry request failed');
      const data = await resp.json();
      const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
      })[char]);

      // 1. KPI Counters
      document.getElementById('tel-stat-active-24h').textContent = data.activeUsers24h || 0;
      document.getElementById('tel-stat-active-7d').textContent = data.activeUsers7d || 0;
      document.getElementById('tel-stat-avg-session').textContent = `${data.avgSessionMins || 0}m`;
      document.getElementById('tel-stat-total-sessions').textContent = data.totalSessions || 0;

      // 2. High-Friction & Stuck Questions
      const hardestTbody = document.getElementById('tel-hardest-tbody');
      if (hardestTbody) {
        if (!data.hardestQuestions || data.hardestQuestions.length === 0) {
          hardestTbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">No question telemetry recorded yet. Students' per-question timings and stuck points will appear here automatically as tests are taken!</td></tr>`;
        } else {
          hardestTbody.innerHTML = data.hardestQuestions.map(q => {
            const isHighTime = (q.avg_sec || 0) >= 150;
            const isLowAcc = (q.acc_pct || 0) < 50;
            const isHighFlips = (q.total_changes || 0) >= 2;

            return `
              <tr>
                <td>
                  <div style="font-weight: 700; color: var(--text-primary);">${q.test_title || q.test_id}</div>
                  <div style="font-size: 0.8rem; font-family: var(--font-mono); color: var(--accent-primary);">Q #${(q.question_index || 0) + 1}</div>
                </td>
                <td>
                  <span class="subject-badge">${q.subject || 'Core'}</span>
                  <span class="q-type-badge q-type-${(q.question_type || 'MCQ').toLowerCase()}" style="margin-left: 4px;">${q.question_type || 'MCQ'}</span>
                </td>
                <td style="text-align: center; font-weight: 600;">${q.seen_by || 0} seen / ${q.attempted_n || 0} tried</td>
                <td style="text-align: center;">
                  <span style="font-weight: 800; font-family: var(--font-mono); color: ${isHighTime ? '#f87171' : '#c7d2fe'};">
                    ${q.avg_sec || 0}s
                  </span>
                  ${isHighTime ? '<br><span style="font-size: 0.68rem; color: #f87171;">⚠️ Slow / Stuck</span>' : ''}
                </td>
                <td style="text-align: center;">
                  <span style="font-weight: 700; color: ${isHighFlips ? '#fbbf24' : 'var(--text-secondary)'};">
                    ${q.total_changes || 0} flips
                  </span>
                  ${isHighFlips ? '<br><span style="font-size: 0.68rem; color: #fbbf24;">Confused</span>' : ''}
                </td>
                <td style="text-align: center; color: var(--text-muted); font-weight: 700;">
                  🔖 ${q.times_marked || 0}
                </td>
                <td style="text-align: center;">
                  <span style="font-weight: 800; color: ${isLowAcc ? '#f87171' : 'var(--gate-green)'};">
                    ${q.acc_pct || 0}%
                  </span>
                </td>
              </tr>
            `;
          }).join('');
        }
      }

      // 3. Student Struggle Radar
      const struggleTbody = document.getElementById('tel-struggle-tbody');
      if (struggleTbody) {
        if (!data.studentStruggle || data.studentStruggle.length === 0) {
          struggleTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 1.5rem; color: var(--text-muted);">No student attempt sessions yet.</td></tr>`;
        } else {
          struggleTbody.innerHTML = data.studentStruggle.map(s => `
            <tr>
              <td>
                <div style="font-weight: 700; color: var(--text-primary); font-size: 0.85rem;">${s.user_email}</div>
              </td>
              <td style="text-align: center; font-weight: 700;">${s.total_qs}</td>
              <td style="text-align: center; font-family: var(--font-mono); color: ${s.avg_sec_per_q > 120 ? '#f87171' : '#c7d2fe'}; font-weight: 700;">
                ${s.avg_sec_per_q}s
              </td>
              <td style="text-align: center; color: #fbbf24; font-weight: 700;">${s.total_changes || 0}</td>
              <td style="text-align: center; font-weight: 700; color: ${s.acc_pct >= 60 ? 'var(--gate-green)' : '#f87171'};">
                ${s.acc_pct}%
              </td>
            </tr>
          `).join('');
        }
      }

      // 4. Subject Difficulty Heatmap
      const subjectTbody = document.getElementById('tel-subject-tbody');
      if (subjectTbody) {
        if (!data.subjectDifficulty || data.subjectDifficulty.length === 0) {
          subjectTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 1.5rem; color: var(--text-muted);">No subject data yet.</td></tr>`;
        } else {
          subjectTbody.innerHTML = data.subjectDifficulty.map(sub => `
            <tr>
              <td><span class="subject-badge">${sub.subject}</span></td>
              <td style="text-align: center; font-weight: 700;">${sub.total_qs}</td>
              <td style="text-align: center; font-family: var(--font-mono); color: #c7d2fe; font-weight: 700;">${sub.avg_sec}s</td>
              <td style="text-align: center; color: var(--text-muted);">🔖 ${sub.times_marked || 0}</td>
              <td style="text-align: center; font-weight: 800; color: ${sub.acc_pct >= 60 ? 'var(--gate-green)' : (sub.acc_pct >= 40 ? '#fbbf24' : '#f87171')};">
                ${sub.acc_pct}%
              </td>
            </tr>
          `).join('');
        }
      }

      // 5. Audit & Login Activity
      const auditTbody = document.getElementById('tel-audit-tbody');
      if (auditTbody) {
        if (!data.recentLogins || data.recentLogins.length === 0) {
          auditTbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">No login or audit events recorded yet.</td></tr>`;
        } else {
          auditTbody.innerHTML = data.recentLogins.map(ev => {
            let evBadge = `<span class="brand-tag" style="background: rgba(99,102,241,0.2); color:#c7d2fe;">${escapeHtml(ev.event_type)}</span>`;
            if (ev.event_type === 'login') {
              evBadge = `<span class="brand-tag" style="background: rgba(16,185,129,0.2); color:#6ee7b7;">🔑 Login</span>`;
            } else if (ev.event_type === 'register') {
              evBadge = `<span class="brand-tag" style="background: rgba(59,130,246,0.2); color:#93c5fd;">✨ Register</span>`;
            } else if (ev.event_type === 'code_unlock') {
              evBadge = `<span class="brand-tag" style="background: rgba(245,158,11,0.2); color:#fde68a;">🔓 Code Unlock</span>`;
            }

            const cleanIp = escapeHtml(ev.ip_address || 'Unavailable');
            const cleanPlatform = escapeHtml(ev.platform || 'Unknown OS');
            const cleanRes = escapeHtml(ev.screen_res || 'Standard');
            const cleanUserAgent = escapeHtml(ev.user_agent || '');

            return `
              <tr>
                <td style="font-size: 0.8rem; color: var(--text-muted); font-family: var(--font-mono); white-space: nowrap;">
                  ${ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'Recent'}
                </td>
                <td>
                  <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem;">${escapeHtml(ev.user_email)}</div>
                </td>
                <td>${evBadge}</td>
                <td>
                  <code style="background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; color: #a5f3fc; font-size: 0.78rem;">${cleanIp}</code>
                </td>
                <td style="color: var(--text-secondary); font-size: 0.82rem;">${cleanPlatform}</td>
                <td style="color: var(--text-muted); font-size: 0.8rem; font-family: var(--font-mono);">${cleanRes}</td>
                <td style="color: var(--text-muted); font-size: 0.75rem; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${cleanUserAgent}">
                  ${escapeHtml(ev.timezone || '')} ${ev.user_agent ? '· ' + escapeHtml(ev.user_agent.split(' ')[0]) : ''}
                </td>
              </tr>
            `;
          }).join('');
        }
      }

      const accessTbody = document.getElementById('tel-site-access-tbody');
      if (accessTbody) {
        if (!data.recentSiteAccess?.length) {
          accessTbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 1.5rem; color: var(--text-muted);">No site accesses recorded yet.</td></tr>`;
        } else {
          accessTbody.innerHTML = data.recentSiteAccess.map(event => `
            <tr>
              <td style="white-space:nowrap; color:var(--text-muted);">${escapeHtml(event.timestamp ? new Date(event.timestamp).toLocaleString() : 'Unknown')}</td>
              <td><code>${escapeHtml(event.ip_address || 'Unavailable')}</code></td>
              <td>${escapeHtml(event.request_path || '')}</td>
              <td style="max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(event.user_agent || '')}">${escapeHtml(event.user_agent || 'Unknown')}</td>
            </tr>
          `).join('');
        }
      }

      // 6. Platform summary pills
      const platformCont = document.getElementById('tel-platforms-container');
      if (platformCont && data.platformBreakdown) {
        if (data.platformBreakdown.length === 0) {
          platformCont.innerHTML = `<span style="color: var(--text-muted); font-size: 0.85rem;">No platforms recorded yet.</span>`;
        } else {
          platformCont.innerHTML = data.platformBreakdown.map(p => `
            <span class="subject-badge" style="background: rgba(99,102,241,0.2); color: #c7d2fe; font-size: 0.8rem;">
              💻 ${p.platform}: <strong>${p.cnt}</strong>
            </span>
          `).join('');
        }
      }

      // 7. Behavior events summary pills
      const behavCont = document.getElementById('tel-behaviors-container');
      if (behavCont && data.behaviorSummary) {
        if (data.behaviorSummary.length === 0) {
          behavCont.innerHTML = `<span style="color: var(--text-muted); font-size: 0.85rem;">No behavioral events recorded yet.</span>`;
        } else {
          behavCont.innerHTML = data.behaviorSummary.map(b => `
            <span class="brand-tag" style="background: rgba(16,185,129,0.15); color: #6ee7b7; font-size: 0.78rem;">
              ⚡ ${b.event_type}: <strong>${b.cnt}</strong>
            </span>
          `).join('');
        }
      }

    } catch (e) {
      console.warn('Telemetry dashboard fetch error:', e);
    }
  }
}

// Global App Instance
window.app = new ExamApp();
