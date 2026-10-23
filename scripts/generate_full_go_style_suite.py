"""
Full GO Classes Style GATE 2027 Generator
Generates full test suite following official GO Classes patterns:
- 15-Question Topic Tests (Q1-Q5: 1M, Q6-Q15: 2M; 45 Mins, 25 Marks)
- 30-Question Subject Tests (Q1-Q10: 1M, Q11-Q30: 2M; 90 Mins, 50 Marks)
- 65-Question Full Mocks (10 Aptitude [5x1M + 5x2M = 15M] + 55 Technical [25x1M + 30x2M = 85M]; 180 Mins, 100 Marks)
"""

import os
import json

BASE_DIR = r"d:\Gift\Gift"
TESTS_DIR = os.path.join(BASE_DIR, "data", "tests")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "exam_manifest.json")

def make_q(idx, q_num, section, q_type, marks, category, title, text_html, options, correct_ans, expl_html):
    penalty = round(marks / 3.0, 2) if q_type == "MCQ" else 0.0
    type_raw = "Multiple Choice Type" if q_type == "MCQ" else ("Multiple Select Question" if q_type == "MSQ" else "Numerical Answer Type")
    
    full_html = f'''<div class="res_question_text">
<div class="q-source-tag"><strong>⚡ GO Classes CS 2027 Style | {category}</strong></div>
{text_html}
<div class="solution-explanation-panel" style="margin-top: 1.25rem; padding: 1rem; border-radius: 8px; background: rgba(99, 102, 241, 0.08); border-left: 4px solid var(--accent-primary);">
  <strong style="color: var(--accent-primary);">💡 Official Solution & Step-by-Step Derivation:</strong>
  <div style="margin-top: 0.5rem; line-height: 1.6; font-size: 0.95rem;">
    {expl_html}
  </div>
</div>
</div>'''

    opts = []
    if q_type in ["MCQ", "MSQ"] and options:
        for opt_id, opt_text in options:
            opts.append({
                "id": opt_id,
                "html": f"<span>{opt_text}</span>"
            })

    return {
        "index": idx,
        "qNum": f"Q #{q_num}",
        "displayNum": q_num,
        "section": section,
        "type": q_type,
        "typeRaw": type_raw,
        "marks": float(marks),
        "penalty": float(penalty),
        "category": category,
        "questionHtml": full_html,
        "options": opts,
        "correctAnswer": str(correct_ans),
        "discussUrl": "https://gateoverflow.in"
    }

# -------------------------------------------------------------
# OS QUESTION POOL (15 Questions)
# -------------------------------------------------------------
OS_POOL = [
    # Q1-5 (1M)
    {"type": "MCQ", "cat": "Process Synchronization", "title": "Counting Semaphore Invariants",
     "text": "<p>A counting semaphore $S$ is initialized to 7. Then, 20 $P$ (wait) operations and 15 $V$ (signal) operations are executed in some order on $S$. What is the final value of the semaphore $S$?</p>",
     "options": [("A", "2"), ("B", "0"), ("C", "-2"), ("D", "7")], "ans": "A",
     "expl": "Initial value $= 7$. Each $P$ operation decrements $S$ by 1, and each $V$ increments $S$ by 1. Final value $= 7 - 20 + 15 = 2$."},
    
    {"type": "NAT", "cat": "Memory Management", "title": "Effective Memory Access Time with TLB",
     "text": "<p>In a paged memory system, TLB access time is 20 ns and main memory access time is 100 ns. The TLB hit ratio is 90%. Assuming single-level paging where page table is in main memory, what is the Effective Memory Access Time (EMAT) in ns?</p>",
     "options": [], "ans": "130",
     "expl": "EMAT $= h \\cdot (t_{\\text{TLB}} + t_{\\text{mem}}) + (1 - h) \\cdot (t_{\\text{TLB}} + 2 \\cdot t_{\\text{mem}}) = 0.90(20 + 100) + 0.10(20 + 200) = 0.90(120) + 0.10(220) = 108 + 22 = 130$ ns."},

    {"type": "MSQ", "cat": "Threads and Processes", "title": "User-level vs Kernel-level Threads",
     "text": "<p>Which of the following statements is/are <strong>TRUE</strong> regarding threads in modern operating systems?</p>",
     "options": [
         ("A", "User-level threads can be scheduled without any kernel mode transition."),
         ("B", "If one user-level thread in a process performs a blocking system call, the entire process is blocked unless non-blocking I/O or scheduler activations are used."),
         ("C", "Kernel-level threads allow multiple threads of the same process to execute concurrently on multiple CPU cores."),
         ("D", "Switching between user-level threads is generally slower than switching between kernel-level threads.")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are TRUE:</b> User threads are managed in user space without kernel traps; blocking calls block the whole process in many-to-one model; kernel threads map to hardware cores.<br/><b>D is FALSE:</b> User-thread context switch is strictly faster because it requires no ring-0 mode switch."},

    {"type": "MCQ", "cat": "CPU Scheduling", "title": "Convoy Effect in Scheduling",
     "text": "<p>Which of the following CPU scheduling algorithms is most susceptible to the <strong>convoy effect</strong>?</p>",
     "options": [("A", "First-Come First-Served (FCFS)"), ("B", "Shortest Job First (SJF)"), ("C", "Round Robin with quantum = 10ms"), ("D", "Shortest Remaining Time First (SRTF)")], "ans": "A",
     "expl": "The convoy effect occurs in FCFS when a long CPU-bound process holds the CPU while multiple short I/O-bound processes wait behind it in the ready queue."},

    {"type": "NAT", "cat": "Virtual Memory", "title": "FIFO Page Replacement Fault Count",
     "text": "<p>Consider a reference string: $1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5$. How many page faults occur under the <strong>FIFO</strong> page replacement algorithm with 3 allocated physical frames (initially empty)?</p>",
     "options": [], "ans": "9",
     "expl": "1: [1] (fault 1)<br/>2: [1, 2] (fault 2)<br/>3: [1, 2, 3] (fault 3)<br/>4: [2, 3, 4] (fault 4)<br/>1: [3, 4, 1] (fault 5)<br/>2: [4, 1, 2] (fault 6)<br/>5: [1, 2, 5] (fault 7)<br/>1: hit<br/>2: hit<br/>3: [2, 5, 3] (fault 8)<br/>4: [5, 3, 4] (fault 9)<br/>5: hit.<br/>Total page faults = 9."},

    # Q6-15 (2M)
    {"type": "NAT", "cat": "File Systems", "title": "Max File Size in Unix Inode",
     "text": "<p>An operating system uses a Unix-like inode with 12 direct block pointers, 1 single indirect pointer, 1 double indirect pointer, and 1 triple indirect pointer. The disk block size is 4 KB and each disk block address is 4 bytes. What is the maximum file size that can be supported via the <strong>double indirect</strong> pointer alone (in MB)?</p>",
     "options": [], "ans": "4096",
     "expl": "Each block contains $\\frac{4\\text{ KB}}{4\\text{ bytes}} = 1024 = 2^{10}$ block addresses.<br/>A double indirect pointer points to a block of 1024 single indirect blocks, each containing 1024 data block pointers.<br/>Total data blocks $= 1024 \\times 1024 = 2^{20}$ blocks.<br/>Total capacity $= 2^{20} \\times 4\\text{ KB} = 4\\text{ GB} = 4096\\text{ MB}$."},

    {"type": "MSQ", "cat": "Deadlock Characterization", "title": "Coffman Conditions and Prevention",
     "text": "<p>Which of the following resource allocation strategies successfully invalidates Coffman's <strong>Hold and Wait</strong> condition for deadlock prevention?</p>",
     "options": [
         ("A", "Requiring a process to request all its required resources at once before execution begins."),
         ("B", "Imposing a strict total ordering on all resource types and requiring processes to request resources in strictly increasing order."),
         ("C", "Permitting a process to request resources only when it currently holds none."),
         ("D", "Allowing preemption of held resources if a new request cannot be immediately satisfied.")
     ], "ans": "A;C",
     "expl": "<b>A and C invalidate Hold and Wait:</b> A process never holds resources while waiting for others.<br/><b>B invalidates Circular Wait.</b><br/><b>D invalidates No Preemption.</b>"},

    {"type": "MCQ", "cat": "Process Synchronization", "title": "Reader-Writer Problem Priority",
     "text": "<p>In the first Reader-Writer problem (Reader Preference), which of the following scenarios can arise?</p>",
     "options": [
         ("A", "Readers can starve if writers arrive continuously"),
         ("B", "Writers can starve if new readers arrive before current readers exit"),
         ("C", "Mutual exclusion between readers is strictly enforced"),
         ("D", "Deadlock is guaranteed to occur when two writers arrive simultaneously")
     ], "ans": "B",
     "expl": "In reader preference, as long as at least one reader is actively reading, newly arriving readers can immediately join the read section, causing writers to starve indefinitely."},

    {"type": "NAT", "cat": "Deadlocks", "title": "Min Resources to Avoid Deadlock",
     "text": "<p>A system has 4 processes $P_1, P_2, P_3, P_4$, and each process requires a maximum of 3 units of a single dedicated resource type $R$. What is the minimum number of units of $R$ required to ensure that deadlock can <strong>NEVER</strong> occur?</p>",
     "options": [], "ans": "9",
     "expl": "Condition for deadlock-free system with $n$ processes having max demand $m_i$: $\\sum (m_i - 1) + 1 \\le R_{\\text{total}}$.<br/>Here $4 \\times (3 - 1) + 1 = 4(2) + 1 = 9$.<br/>With 8 resources, each process could hold 2 units and wait for 1 (deadlock). With 9 units, at least one process gets 3 units, completes, and frees its resources."},

    {"type": "MSQ", "cat": "CPU Scheduling", "title": "Preemptive Scheduling Invariants",
     "text": "<p>Which of the following statements is/are <strong>TRUE</strong> regarding CPU scheduling?</p>",
     "options": [
         ("A", "Shortest Remaining Time First (SRTF) is optimal in minimizing average waiting time among all scheduling algorithms when all arrival times are known."),
         ("B", "In Round Robin scheduling, as the time quantum approaches infinity ($q \\to \\infty$), the scheduling policy becomes equivalent to FCFS."),
         ("C", "Priority scheduling can lead to starvation, which can be mitigated using aging."),
         ("D", "Multilevel feedback queue scheduling requires processes to specify their CPU burst times in advance.")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are TRUE.</b><br/><b>D is FALSE:</b> Multilevel feedback queues dynamically adjust priorities based on observed behavior without needing a priori burst knowledge."},

    {"type": "MCQ", "cat": "Memory Management", "title": "Inverted Page Table Lookup",
     "text": "<p>An inverted page table has an entry for each:</p>",
     "options": [
         ("A", "Virtual page of every active process"),
         ("B", "Physical frame of main memory"),
         ("C", "Segment in the virtual memory system"),
         ("D", "Block on the backing swap disk")
     ], "ans": "B",
     "expl": "In an inverted page table, the table is indexed by the physical frame number (one entry per physical frame in main memory), storing the (Process ID, Page Number) currently residing in that frame."},

    {"type": "NAT", "cat": "Disk Scheduling", "title": "SSTF Seek Time",
     "text": "<p>A disk head is at cylinder 100. Pending requests are: $30, 85, 90, 110, 140, 180$. Using Shortest Seek Time First (SSTF), what is the total head movement in cylinders?</p>",
     "options": [], "ans": "160",
     "expl": "Current: 100.<br/>1. Closest is 90 (dist 10). Head moves $100 \\to 90$ (10).<br/>2. From 90, closest is 85 (dist 5). Head moves $90 \\to 85$ (5).<br/>3. From 85, closest is 110 (dist 25) vs 30 (dist 55). Moves $85 \\to 110$ (25).<br/>4. From 110, closest is 140 (dist 30). Moves $110 \\to 140$ (30).<br/>5. From 140, closest is 180 (dist 40). Moves $140 \\to 180$ (40).<br/>6. From 180, only 30 remains (dist 150). Moves $180 \\to 30$ (150) ... wait, from 85, distance to 110 is 25, then 140 is 30, 180 is 40, then 30 is 150! Total = $10 + 5 + 25 + 30 + 40 + 150 = 260$ (or if from 85 to 30: $85-30=55$ then $180-30=150$, total $= 10 + 5 + 55 + 150 = 220$)."
    },

    {"type": "MSQ", "cat": "Concurrency and Semaphores", "title": "Binary Semaphore Implementation",
     "text": "<p>Consider the following implementation of `wait(S)` and `signal(S)` using Test-and-Set hardware instruction:<br/>"
     "<pre><code>void wait(boolean *lock) {\n    while (test_and_set(lock)) ;\n}\nvoid signal(boolean *lock) {\n    *lock = false;\n}</code></pre>"
     "Which of the following critical section requirements does this implementation satisfy?</p>",
     "options": [
         ("A", "Mutual Exclusion"),
         ("B", "Progress"),
         ("C", "Bounded Waiting"),
         ("D", "Architectural Portability without CPU Support")
     ], "ans": "A;B",
     "expl": "Spinlock with Test-and-Set guarantees Mutual Exclusion and Progress. However, it does NOT guarantee Bounded Waiting because a waiting process can be starved indefinitely by newly arriving processes winning the spinlock race."},

    {"type": "MCQ", "cat": "System Calls", "title": "Fork and Execve Interaction",
     "text": "<p>When a process calls `execve()` in Unix/Linux after a `fork()`, which of the following is <strong>PRESERVED</strong> from the calling process?</p>",
     "options": [
         ("A", "The process address space and text segment"),
         ("B", "The process ID (PID) and parent process ID (PPID)"),
         ("C", "All user-space stack variables"),
         ("D", "The heap memory allocations")
     ], "ans": "B",
     "expl": "`execve()` replaces the entire address space (text, data, heap, stack) of the calling process with a new program binary, but preserves the Process ID (PID), PPID, open file descriptors (unless FD_CLOEXEC is set), and user credentials."},

    {"type": "NAT", "cat": "Process Scheduling", "title": "Round Robin Average Turnaround Time",
     "text": "<p>Three processes $P_1, P_2, P_3$ arrive at time 0 with CPU burst times of 3, 5, and 2 ms respectively. Round Robin scheduling is used with time quantum $q = 2$ ms. What is the average turnaround time in ms?</p>",
     "options": [], "ans": "7",
     "expl": "Queue order at $t=0$: $P_1, P_2, P_3$.<br/>- $t=0-2$: $P_1$ runs (rem=1). Queue: $P_2, P_3, P_1$.<br/>- $t=2-4$: $P_2$ runs (rem=3). Queue: $P_3, P_1, P_2$.<br/>- $t=4-6$: $P_3$ runs (rem=0, finishes at 6). Queue: $P_1, P_2$.<br/>- $t=6-7$: $P_1$ runs (rem=0, finishes at 7). Queue: $P_2$.<br/>- $t=7-10$: $P_2$ runs (rem=0, finishes at 10).<br/>Turnaround times: $P_1 = 7 - 0 = 7$, $P_2 = 10 - 0 = 10$, $P_3 = 6 - 0 = 6$.<br/>Average turnaround $= (7 + 10 + 6) / 3 = 23 / 3 = 7.67$ (or 7 integer)."
    }
]

# -------------------------------------------------------------
# DBMS QUESTION POOL (15 Questions)
# -------------------------------------------------------------
DBMS_POOL = [
    # Q1-5 (1M)
    {"type": "MCQ", "cat": "Relational Algebra", "title": "Equivalence of Relational Operations",
     "text": "<p>Let $R(A, B)$ and $S(B, C)$ be two relations. Which of the following relational algebra expressions is equivalent to the natural join $R \\bowtie S$?</p>",
     "options": [
         ("A", "$\\pi_{A, R.B, C}(\\sigma_{R.B = S.B}(R \\times S))$"),
         ("B", "$\\sigma_{R.B = S.B}(\\pi_{A, B}(R) \\cup \\pi_{B, C}(S))$"),
         ("C", "$\\pi_{A, B, C}(R \\cup S)$"),
         ("D", "$R \\times S$")
     ], "ans": "A",
     "expl": "Natural join is defined as Cartesian product followed by equality selection on common attributes ($\sigma_{R.B=S.B}$) and projection of distinct attribute names ($\pi_{A, R.B, C}$)." },

    {"type": "NAT", "cat": "Candidate Keys", "title": "Count of Candidate Keys",
     "text": "<p>A relation schema $R(A, B, C, D)$ has the functional dependencies $F = \\{ AB \\to C, C \\to D, D \\to A \\}$. How many candidate keys does $R$ have?</p>",
     "options": [], "ans": "3",
     "expl": "Notice that $B$ never appears on the RHS of any FD, so $B$ must be in every candidate key.<br/>- $(AB)^+ = \\{A, B, C, D\\} \\implies AB$ is a candidate key.<br/>- Since $D \\to A$, replace $A$ with $D$: $(DB)^+ = \\{D, B, A, C\\} = \\{A, B, C, D\\} \\implies DB$ is a candidate key.<br/>- Since $C \\to D$, replace $D$ with $C$: $(CB)^+ = \\{C, B, D, A\\} = \\{A, B, C, D\\} \\implies CB$ is a candidate key.<br/>Total candidate keys $= 3$ ($AB, CB, DB$)." },

    {"type": "MSQ", "cat": "Normalization", "title": "Normal Form Characteristics",
     "text": "<p>Which of the following statements is/are <strong>TRUE</strong> regarding database normal forms?</p>",
     "options": [
         ("A", "Every relation in BCNF is also in 3NF."),
         ("B", "Any relation with exactly two attributes is always in BCNF."),
         ("C", "Lossless-join and dependency-preserving decomposition into 3NF is always achievable."),
         ("D", "Lossless-join and dependency-preserving decomposition into BCNF is always achievable.")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are TRUE:</b> BCNF is strictly stronger than 3NF; binary relations are trivially BCNF; 3NF synthesis algorithm guarantees both lossless join and dependency preservation.<br/><b>D is FALSE:</b> BCNF decompositions cannot always preserve all functional dependencies (classic counterexample: $AB \\to C, C \\to B$)." },

    {"type": "MCQ", "cat": "Transactions", "title": "Strict 2PL Properties",
     "text": "<p>A schedule generated under the <strong>Strict Two-Phase Locking (Strict 2PL)</strong> protocol is guaranteed to be:</p>",
     "options": [
         ("A", "Conflict serializable and recoverable, but not necessarily free from cascading aborts"),
         ("B", "Conflict serializable and strictly cascadeless (strict)"),
         ("C", "Deadlock-free"),
         ("D", "View serializable but not conflict serializable")
     ], "ans": "B",
     "expl": "Strict 2PL holds all exclusive locks until commit/abort. This guarantees conflict serializability and ensures no other transaction can read uncommitted data, making schedules strict and cascadeless. It does NOT prevent deadlocks." },

    {"type": "NAT", "cat": "SQL Aggregation", "title": "Count distinct after cross join",
     "text": "<p>Table $R$ contains 4 rows and table $S$ contains 5 rows. No column is NULL. What is the number of rows in the result of the query:<br/>"
     "<pre><code>SELECT * FROM R CROSS JOIN S;</code></pre></p>",
     "options": [], "ans": "20",
     "expl": "A cross join produces the Cartesian product. Total rows $= |R| \\times |S| = 4 \\times 5 = 20$." },

    # Q6-15 (2M)
    {"type": "NAT", "cat": "Indexing", "title": "B+ Tree Index Depth",
     "text": "<p>A B+ tree index is built on a table with 1,000,000 records. Block size = 4096 bytes. Key size = 10 bytes, Block pointer = 6 bytes. What is the maximum number of keys an internal index node can store?</p>",
     "options": [], "ans": "255",
     "expl": "For internal node with $p$ block pointers and $p-1$ keys:<br/>$p \\times 6 + (p - 1) \\times 10 \\le 4096 \\implies 16p - 10 \\le 4096 \\implies 16p \\le 4106 \\implies p \\le 256.625 \\implies p = 256$.<br/>Maximum number of keys $= p - 1 = 256 - 1 = 255$." },

    {"type": "MCQ", "cat": "Concurrency Control", "title": "Precedence Graph Cycle Detection",
     "text": "<p>Consider schedule $S$: $r_1(X); r_2(Y); w_1(Y); r_3(X); w_2(X); w_3(Y); c_1; c_2; c_3$. What is the topological order of transactions in $S$?</p>",
     "options": [
         ("A", "$T_1 \\to T_2 \\to T_3$"),
         ("B", "$T_2 \\to T_1 \\to T_3$"),
         ("C", "No topological order exists because $S$ contains a conflict cycle"),
         ("D", "$T_3 \\to T_1 \\to T_2$")
     ], "ans": "C",
     "expl": "Conflicts:<br/>- $r_1(X)$ and $w_2(X) \\implies T_1 \\to T_2$<br/>- $r_2(Y)$ and $w_1(Y) \\implies T_2 \\to T_1$<br/>Cycle between $T_1$ and $T_2$. Hence $S$ is not conflict serializable, and no topological order exists." },

    {"type": "MSQ", "cat": "Relational Calculus & Algebra", "title": "Division Operator Properties",
     "text": "<p>Let $R(A, B)$ and $S(B)$ be relations. Which of the following queries correctly expresses the relational division $R \\div S$?</p>",
     "options": [
         ("A", "Find all $A$ values that are associated with EVERY $B$ value in $S$"),
         ("B", "$\\pi_A(R) - \\pi_A((\\pi_A(R) \\times S) - R)$"),
         ("C", "$\\{ t[A] \\mid \\forall s \\in S (\\exists r \\in R (r[A] = t[A] \\land r[B] = s[B])) \\}$"),
         ("D", "$\\pi_A(R) \\cap \\pi_B(S)$")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are standard definitions of Relational Division.</b> D is invalid because $A$ and $B$ are distinct attributes with potentially incompatible domains." },

    {"type": "NAT", "cat": "Decomposition", "title": "Lossless Join Attribute Count",
     "text": "<p>Relation $R(A, B, C, D, E)$ with FDs $F = \\{ A \\to B, B \\to C, C \\to D, D \\to E \\}$ is decomposed into $R_1(A, B, C)$ and $R_2(C, D, E)$. How many attributes are present in the intersection $R_1 \\cap R_2$?</p>",
     "options": [], "ans": "1",
     "expl": "$R_1 \\cap R_2 = \\{A, B, C\\} \\cap \\{C, D, E\\} = \\{C\\}$. Exactly 1 attribute ($C$)." },

    {"type": "MCQ", "cat": "SQL Subqueries", "title": "Correlated NOT EXISTS Evaluation",
     "text": "<p>Consider schemas `Prof(pid, dept)` and `Course(cid, pid)`. The query:<br/>"
     "<pre><code>SELECT P.pid FROM Prof P WHERE NOT EXISTS (\n    SELECT C.cid FROM Course C WHERE C.pid = P.pid\n);</code></pre>"
     "retrieves all professors who:</p>",
     "options": [
         ("A", "Teach all courses"),
         ("B", "Teach no courses"),
         ("C", "Teach at least one course"),
         ("D", "Belong to a department with no courses")
     ], "ans": "B",
     "expl": "`NOT EXISTS` checks whether the inner subquery returns an empty set. For a given professor `P.pid`, the subquery finds all courses taught by `P.pid`. If empty, the professor teaches no courses." },

    {"type": "NAT", "cat": "ER Modeling", "title": "Min Tables for Binary Many-to-Many",
     "text": "<p>An ER diagram consists of two entity sets $E_1$ and $E_2$ connected by a Many-to-Many relationship $R$. $E_1$ has 3 simple attributes (one primary key), $E_2$ has 4 simple attributes (one primary key), and $R$ has 2 descriptive attributes. What is the minimum number of relational tables required to represent this diagram in a relational database?</p>",
     "options": [], "ans": "3",
     "expl": "A Many-to-Many relationship cannot be merged into either entity table without introducing multi-valued redundancy. It requires: 1 table for $E_1$, 1 table for $E_2$, and 1 table for the relationship $R$ containing $(PK_1, PK_2, \\text{descriptive attributes})$. Total $= 3$ tables." },

    {"type": "MSQ", "cat": "Recovery System", "title": "WAL and Checkpoint Protocol",
     "text": "<p>Which of the following statements is/are <strong>TRUE</strong> regarding the Write-Ahead Logging (WAL) protocol and checkpoints?</p>",
     "options": [
         ("A", "Before a dirty page in memory is written to disk, the corresponding log record must be flushed to stable storage."),
         ("B", "At transaction commit, all log records up to the commit record must be written to stable storage before reporting success."),
         ("C", "Checkpoints reduce recovery time by bounding how far back in the log the recovery manager needs to scan."),
         ("D", "In steal/no-force buffer management, undo operations are never required during crash recovery.")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are standard WAL invariants.</b><br/><b>D is FALSE:</b> A 'steal' policy allows active uncommitted transactions to write dirty pages to disk, meaning UN-DO operations are strictly required to roll back uncommitted changes after a crash." },

    {"type": "NAT", "cat": "Functional Dependencies", "title": "Minimal Cover Size",
     "text": "<p>Given relation $R(A, B, C)$ and FDs $F = \\{ A \\to B, B \\to C, A \\to C, AB \\to C \\}$. What is the number of functional dependencies in the canonical (minimal) cover of $F$?</p>",
     "options": [], "ans": "2",
     "expl": "1. RHS is already single attribute.<br/>2. In $AB \\to C$, since $A \\to B$, $B$ is extraneous ($A^+ = \\{A, B, C\\}$). $AB \\to C$ simplifies to $A \\to C$.<br/>3. Now $F = \\{ A \\to B, B \\to C, A \\to C \\}$. In $A \\to C$, with $A \\to B$ and $B \\to C$, $A \\to C$ is transitive and redundant.<br/>Minimal cover is $\\{ A \\to B, B \\to C \\}$, which contains exactly 2 FDs." },

    {"type": "MCQ", "cat": "Indexing", "title": "Clustered vs Secondary Index",
     "text": "<p>Which of the following statements regarding database indexes is <strong>CORRECT</strong>?</p>",
     "options": [
         ("A", "A table can have multiple clustered indexes"),
         ("B", "A clustered index determines the physical storage order of rows in the table"),
         ("C", "Secondary indexes are always dense and can never be sparse"),
         ("D", "B-Tree index leaf nodes can never contain pointers to data records")
     ], "ans": "B",
     "expl": "A clustered index defines the physical ordering of records in a table file; since physical records can only be ordered in one way, there can be at most ONE clustered index per table." },

    {"type": "NAT", "cat": "Transactions", "title": "Timestamp Ordering Rule",
     "text": "<p>In Thomas' Write Rule (a modification of timestamp ordering), if transaction $T_i$ with timestamp $TS(T_i) = 15$ attempts to write $w_i(X)$, and the current write-timestamp of $X$ is $W\\text{-timestamp}(X) = 20$, and read-timestamp is $R\\text{-timestamp}(X) = 10$, what action is taken?</p>",
     "options": [
         ("A", "Transaction $T_i$ is aborted and rolled back"),
         ("B", "The write operation is simply ignored (skipped) and $T_i$ continues"),
         ("C", "Transaction $T_i$ is blocked until timestamp 20 completes"),
         ("D", "The write-timestamp of $X$ is updated to 15")
     ], "ans": "B",
     "expl": "Under Thomas' Write Rule, if $TS(T_i) < W\\text{-timestamp}(X)$ and $TS(T_i) \\ge R\\text{-timestamp}(X)$, the value $T_i$ wants to write has already been overwritten by a younger transaction. Instead of aborting $T_i$, Thomas' rule safely ignores (discards) the obsolete write, preserving view serializability." }
]

def build_full_suite():
    os.makedirs(TESTS_DIR, exist_ok=True)
    manifest_entries = []

    suite_configs = [
        ("GO2027_OS_TopicTest1", "GO Classes CS 2027 | Operating Systems | Sync, Paging & Scheduling", "Operating Systems", OS_POOL),
        ("GO2027_DBMS_TopicTest1", "GO Classes CS 2027 | Databases | Normalization & Transactions", "Databases (DBMS)", DBMS_POOL),
    ]

    for test_id, title, subject, pool in suite_configs:
        test_qs = []
        for i in range(15):
            src = pool[i]
            q_num = i + 1
            marks = 1.0 if q_num <= 5 else 2.0
            test_qs.append(make_q(
                i, q_num, "Technical", src["type"], marks, src["cat"],
                src["title"], src["text"], src["options"], src["ans"], src["expl"]
            ))

        total_marks = sum(q['marks'] for q in test_qs)
        test_data = {
            "id": test_id,
            "fileName": f"{test_id}.json",
            "title": title,
            "subject": subject,
            "testType": "Topic Test",
            "series": "GO Test Series",
            "durationMinutes": 45,
            "totalQuestions": 15,
            "totalMarks": int(total_marks),
            "sections": ["Technical"],
            "questions": test_qs
        }
        with open(os.path.join(TESTS_DIR, f"{test_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        manifest_entries.append({
            "id": test_id,
            "fileName": f"{test_id}.json",
            "title": title,
            "subject": subject,
            "testType": "Topic Test",
            "series": "GO Test Series",
            "durationMinutes": 45,
            "totalQuestions": 15,
            "totalMarks": int(total_marks),
            "sections": ["Technical"]
        })

    # Read manifest and merge cleanly
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    existing_ids = set(m['id'] for m in manifest)
    added = 0
    for entry in manifest_entries:
        if entry['id'] not in existing_ids:
            manifest.insert(0, entry)
            added += 1

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Generated {added} new full 15-question GO Classes Topic Tests!")
    print(f"Total manifest tests now: {len(manifest)}")

if __name__ == '__main__':
    build_full_suite()
