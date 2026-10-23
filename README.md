# 🎓 GATE Computer Science CBT Exam System

An interactive, high-performance Computer-Based Test (CBT) and practice platform built from **271 comprehensive test papers** (over **11,214 verified GATE questions**).

---

## 🌟 The Complete GATE 2027 Library Breakdown

The platform integrates four premier datasets:

### 🎯 1. 80 Full-Length All India Mock Tests (GATE 2027 Generated Mock Series)
- **80 Complete Papers (`GATE2027_Mock_01` to `GATE2027_Mock_80`)**
- **EXACTLY 65 Questions in EVERY Paper**:
  - **Section 1: General Aptitude (10 Questions = 15 Marks)**:
    - Q1 to Q5: 1 Mark each (penalty -0.33 for MCQ)
    - Q6 to Q10: 2 Marks each (penalty -0.67 for MCQ)
  - **Section 2: Technical (55 Questions = 85 Marks)**:
    - Q11 to Q35 (25 questions): 1 Mark each (penalty -0.33 for MCQ)
    - Q36 to Q65 (30 questions): 2 Marks each (penalty -0.67 for MCQ)
  - **Balanced Subject Coverage in Every Test**:
    - Algorithms (5 Qs)
    - Data Structures (4 Qs)
    - Programming in C (4 Qs)
    - Theory of Computation (5 Qs)
    - Compiler Design (4 Qs)
    - Operating Systems (5 Qs)
    - Databases / DBMS (5 Qs)
    - Computer Networks (5 Qs)
    - Computer Organization & Architecture (5 Qs)
    - Digital Logic Design (4 Qs)
    - Discrete Mathematics (6 Qs)
    - Engineering Mathematics (2 Qs)
    - Probability & Statistics (3 Qs)
    - General Aptitude (10 Qs)
- **Total Marks**: 100 Marks per test
- **Duration**: 180 Minutes (official GATE duration)

---

### 🎓 2. GO Classes Test Series (85 Tests & 2,331 Questions)
- **14 Full-Length Mock Tests** (AIMT 2–5, MT 1–14): 65 questions, 180 minutes, official GATE exam pattern.
- **19 Subject-Wise Tests**: 30 questions, 90 minutes across all GATE CS subjects.
- **48 Topic-Wise Tests**: 15 questions, 45 minutes for focused topic practice.
- **4 Mixed Subject Tests**: Multi-topic revision.

---

### 🏛️ 3. Official GATE PYQ Series (98 Tests across Volumes 1–3)
- **Volume 1 (956 Questions)**: Discrete Math (457 Qs), Engineering Math (166 Qs), Probability (114 Qs), General Aptitude (219 Qs).
- **Volume 2 (1,252 Questions)**: Algorithms (352 Qs), Data Structures (233 Qs), TOC (293 Qs), Compiler Design (242 Qs), C Programming (132 Qs).
- **Volume 3 (1,426 Questions)**: Operating Systems (343 Qs), DBMS (296 Qs), Computer Networks (225 Qs), COA (251 Qs), Digital Logic (311 Qs).

---

### 🔥 4. GATE 2027 Original Challenger Series (8 Tests)
- Deep conceptual predictor questions featuring tricky edge cases, non-polynomial recurrences, weak memory model concurrency, and full mathematical derivations.

---

## 🚀 How to Launch the Exam System

### Option 1: Double-Click (Quickest)
Double-click the **`run_exam_system.bat`** file located in this folder. It will launch the local server and automatically open your default web browser to:
```
http://localhost:8080/index.html
```

### Option 2: Terminal / Command Prompt
Open PowerShell or Command Prompt in this directory and run:
```powershell
python start_server.py
```

---

## ⚡ Real GATE CBT Exam Environment

1. **Countdown Timer**: Automatically synchronizes with official test duration (45m, 90m, or 180m).
2. **Official Status Palette**:
   - 🟢 **Green**: Answered
   - 🔴 **Red**: Not Answered
   - ⚪ **Gray**: Not Visited
   - 🟣 **Purple**: Marked for Review
   - 🟣🟢 **Purple with dot**: Answered & Marked for Review
3. **Section Switcher**: Seamlessly switch between General Aptitude and Technical sections.
4. **Full Question Type Support**:
   - **MCQ (Multiple Choice)**: Single-select radio buttons with standard GATE negative marking (-0.33 or -0.67).
   - **MSQ (Multiple Select)**: Checkboxes for multi-option questions (zero negative marks).
   - **NAT (Numerical Answer Type)**: Real GATE numeric input with on-screen virtual keypad (0-9, decimal, negative, backspace, clear) + keyboard input (zero negative marks).
5. **Series Switcher Tabs**: Filter in one click between:
   - `🌟 All Tests (271)`
   - `🎯 80 Full Mocks (65 Qs / 100M)`
   - `🎓 GO Classes Test Series (85)`
   - `🏛️ Official GATE PYQs (Vol 1–3) (98)`
   - `🔥 Challenger Series (8)`
6. **Built-in TCS iON Virtual Scientific Calculator**:
   - Replica of the official GATE virtual calculator.
   - Draggable window with trigonometry, logarithms, exponentials, roots, factorials, memory, and powers.
7. **Practice Mode**:
   - Instant "Check Answer" buttons with solution explanations and direct links to **GateOverflow discussion**.
8. **Automated Evaluation & Scorecard**:
   - Score breakdown: Positive Marks vs Penalty Marks.
   - Filter review by Correct, Incorrect, Unattempted, and Bookmarked.
   - **Bookmarks Vault**: Save tricky questions across any test for quick revision.
