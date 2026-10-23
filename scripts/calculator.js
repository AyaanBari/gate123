// TCS iON Style GATE Virtual Scientific Calculator
class GateCalculator {
  constructor() {
    this.currentVal = '0';
    this.memory = 0;
    this.isDeg = true; // Degrees by default
    this.expression = '';
    this.isNewInput = true;
    this.isOpen = false;
    this.init();
  }

  init() {
    this.modal = document.getElementById('gate-calc-modal');
    this.displayExp = document.getElementById('calc-display-exp');
    this.displayVal = document.getElementById('calc-display-val');
    this.radDegBtn = document.getElementById('calc-rad-deg-btn');
    this.setupDrag();
  }

  toggle() {
    if (!this.modal) this.init();
    if (!this.modal) return;
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      this.modal.classList.remove('hidden');
      this.modal.style.display = 'block';
      this.reset();
    } else {
      this.modal.classList.add('hidden');
      this.modal.style.display = 'none';
    }
  }

  show() {
    if (!this.modal) this.init();
    if (this.modal) {
      this.isOpen = true;
      this.modal.classList.remove('hidden');
      this.modal.style.display = 'block';
    }
  }

  hide() {
    if (this.modal) {
      this.isOpen = false;
      this.modal.classList.add('hidden');
      this.modal.style.display = 'none';
    }
  }

  reset() {
    this.currentVal = '0';
    this.expression = '';
    this.isNewInput = true;
    this.updateDisplay();
  }

  updateDisplay() {
    if (this.displayVal) this.displayVal.textContent = this.currentVal;
    if (this.displayExp) this.displayExp.textContent = this.expression;
    if (this.radDegBtn) this.radDegBtn.textContent = this.isDeg ? 'Deg' : 'Rad';
  }

  toggleAngle() {
    this.isDeg = !this.isDeg;
    this.updateDisplay();
  }

  inputDigit(d) {
    if (this.isNewInput) {
      this.currentVal = d.toString();
      this.isNewInput = false;
    } else {
      if (this.currentVal === '0') {
        this.currentVal = d.toString();
      } else {
        this.currentVal += d.toString();
      }
    }
    this.updateDisplay();
  }

  inputDot() {
    if (this.isNewInput) {
      this.currentVal = '0.';
      this.isNewInput = false;
    } else if (!this.currentVal.includes('.')) {
      this.currentVal += '.';
    }
    this.updateDisplay();
  }

  backspace() {
    if (this.isNewInput) return;
    if (this.currentVal.length > 1) {
      this.currentVal = this.currentVal.slice(0, -1);
    } else {
      this.currentVal = '0';
      this.isNewInput = true;
    }
    this.updateDisplay();
  }

  clearEntry() {
    this.currentVal = '0';
    this.isNewInput = true;
    this.updateDisplay();
  }

  clearAll() {
    this.currentVal = '0';
    this.expression = '';
    this.isNewInput = true;
    this.updateDisplay();
  }

  toggleSign() {
    let num = parseFloat(this.currentVal);
    if (!isNaN(num)) {
      this.currentVal = (-num).toString();
      this.updateDisplay();
    }
  }

  applyConstant(name) {
    if (name === 'pi') {
      this.currentVal = Math.PI.toString();
    } else if (name === 'e') {
      this.currentVal = Math.E.toString();
    }
    this.isNewInput = true;
    this.updateDisplay();
  }

  applyUnary(fn) {
    let x = parseFloat(this.currentVal);
    if (isNaN(x)) return;

    let toAngle = (rad) => this.isDeg ? rad * (180 / Math.PI) : rad;
    let fromAngle = (val) => this.isDeg ? val * (Math.PI / 180) : val;

    let res = 0;
    try {
      switch (fn) {
        case 'sin': res = Math.sin(fromAngle(x)); break;
        case 'cos': res = Math.cos(fromAngle(x)); break;
        case 'tan': res = Math.tan(fromAngle(x)); break;
        case 'asin': res = toAngle(Math.asin(x)); break;
        case 'acos': res = toAngle(Math.acos(x)); break;
        case 'atan': res = toAngle(Math.atan(x)); break;
        case 'sinh': res = Math.sinh(x); break;
        case 'cosh': res = Math.cosh(x); break;
        case 'tanh': res = Math.tanh(x); break;
        case 'sqrt': res = Math.sqrt(x); break;
        case 'cbrt': res = Math.cbrt(x); break;
        case 'sqr': res = x * x; break;
        case 'cube': res = x * x * x; break;
        case 'inv': res = 1 / x; break;
        case 'ln': res = Math.log(x); break;
        case 'log10': res = Math.log10(x); break;
        case 'log2': res = Math.log2(x); break;
        case 'exp': res = Math.exp(x); break;
        case 'pow10': res = Math.pow(10, x); break;
        case 'fact': res = this.factorial(x); break;
        case 'abs': res = Math.abs(x); break;
        default: res = x;
      }

      if (isNaN(res) || !isFinite(res)) {
        this.currentVal = 'Error';
      } else {
        // Round to reasonable precision
        this.currentVal = parseFloat(res.toPrecision(12)).toString();
      }
    } catch (e) {
      this.currentVal = 'Error';
    }

    this.isNewInput = true;
    this.updateDisplay();
  }

  factorial(n) {
    if (n < 0 || Math.floor(n) !== n) return NaN;
    if (n > 170) return Infinity; // JS max float limit
    let r = 1;
    for (let i = 2; i <= n; i++) r *= i;
    return r;
  }

  applyOp(op) {
    let sym = op;
    if (op === '*') sym = '×';
    if (op === '/') sym = '÷';
    if (op === '^') sym = '^';

    this.expression += ` ${this.currentVal} ${sym}`;
    this.isNewInput = true;
    this.updateDisplay();
  }

  applyParen(p) {
    if (p === '(') {
      this.expression += ' ( ';
    } else {
      this.expression += ` ${this.currentVal} ) `;
    }
    this.isNewInput = true;
    this.updateDisplay();
  }

  calculate() {
    let fullExp = `${this.expression} ${this.currentVal}`;
    // Replace visual symbols with js symbols
    let sanitized = fullExp
      .replace(/×/g, '*')
      .replace(/÷/g, '/')
      .replace(/\^/g, '**');

    try {
      // Safe math evaluator using Function with sanitized input
      if (!/^[0-9\+\-\*\/\%\.\(\)\s\*\*]+$/.test(sanitized)) {
        throw new Error('Invalid input');
      }
      let result = Function(`'use strict'; return (${sanitized})`)();
      if (isNaN(result) || !isFinite(result)) {
        this.currentVal = 'Error';
      } else {
        this.currentVal = parseFloat(result.toPrecision(12)).toString();
      }
      this.expression = '';
    } catch (e) {
      this.currentVal = 'Error';
    }
    this.isNewInput = true;
    this.updateDisplay();
  }

  memClear() { this.memory = 0; }
  memRecall() { this.currentVal = this.memory.toString(); this.isNewInput = true; this.updateDisplay(); }
  memStore() { this.memory = parseFloat(this.currentVal) || 0; }
  memAdd() { this.memory += (parseFloat(this.currentVal) || 0); }
  memSub() { this.memory -= (parseFloat(this.currentVal) || 0); }

  setupDrag() {
    if (!this.modal) return;
    const header = this.modal.querySelector('.calc-header');
    if (!header) return;

    let isDragging = false;
    let startX = 0, startY = 0;
    let initialX = 0, initialY = 0;

    header.addEventListener('mousedown', (e) => {
      if (e.target.closest('.calc-close-btn')) return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = this.modal.getBoundingClientRect();
      initialX = rect.left;
      initialY = rect.top;
      this.modal.style.position = 'fixed';
      this.modal.style.margin = '0';
      this.modal.style.transform = 'none';
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });

    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      let newX = Math.max(10, Math.min(window.innerWidth - 380, initialX + dx));
      let newY = Math.max(10, Math.min(window.innerHeight - 300, initialY + dy));
      this.modal.style.left = `${newX}px`;
      this.modal.style.top = `${newY}px`;
    };

    const onMouseUp = () => {
      isDragging = false;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
  }
}

// Global instance
window.gateCalculator = new GateCalculator();
