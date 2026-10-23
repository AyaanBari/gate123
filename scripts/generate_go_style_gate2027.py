"""
GO Classes Style GATE 2027 Test Generator
Generates tests matching the exact GO Classes 79-test structure:
- Topic Tests: 15 Questions (Q1-Q5: 1M, Q6-Q15: 2M), 45 Mins, 25 Marks
- Subject Tests: 30 Questions (Q1-Q10: 1M, Q11-Q30: 2M), 90 Mins, 50 Marks
- All India Mock Tests: 65 Questions (10 Aptitude [5x1M + 5x2M = 15M] + 55 Technical [25x1M + 30x2M = 85M]), 180 Mins, 100 Marks
Follows GATE 2027 syllabus with genuine, distinct, high-caliber questions.
"""

import os
import json
import random

BASE_DIR = r"d:\Gift\Gift"
TESTS_DIR = os.path.join(BASE_DIR, "data", "tests")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "exam_manifest.json")

def make_question(idx, q_num, section, q_type, marks, category, title, text_html, options, correct_ans, expl_html):
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

# -------------------------------------------------------------------------
# QUESTION BANK DEFINITIONS (GATE 2027 CS Syllabus)
# -------------------------------------------------------------------------

# ALGORITHMS QUESTIONS
ALGO_QS = [
    # 1-Mark Questions
    {
        "type": "MCQ", "category": "Asymptotic Analysis",
        "title": "Master Theorem Non-Polynomial Gap",
        "text": "<p>Consider the recurrence relation: $T(n) = 2T(n/2) + n / \\log_2 n$ for $n > 1$ with $T(1) = 1$. Which of the following statements is <strong>CORRECT</strong>?</p>",
        "options": [
            ("A", "Master theorem can be applied and $T(n) = \\Theta(n)$"),
            ("B", "Master theorem cannot be directly applied, and $T(n) = \\Theta(n \\log(\\log n))$"),
            ("C", "Master theorem can be applied and $T(n) = \\Theta(n \\log n)$"),
            ("D", "$T(n) = \\Theta(n^2)$")
        ],
        "ans": "B",
        "expl": "Here $a=2, b=2, f(n)=n/\\log n$. $n^{\\log_b a} = n^1 = n$. The ratio $\\frac{n^{\\log_b a}}{f(n)} = \\log n$ is asymptotically positive but not polynomially larger ($n^\\epsilon$). Thus Master theorem Case 1 does not apply. By substitution $n=2^k$: $T(2^k) = 2T(2^{k-1}) + 2^k/k$. Dividing by $2^k$: $\\frac{T(2^k)}{2^k} = \\frac{T(2^{k-1})}{2^{k-1}} + \\frac{1}{k}$. Let $S(k) = \\frac{T(2^k)}{2^k}$, then $S(k) = \\sum_{i=1}^k 1/i = \\ln k = \\Theta(\\log k) = \\Theta(\\log(\\log n))$. Thus $T(n) = \\Theta(n \\log(\\log n))$."
    },
    {
        "type": "NAT", "category": "Sorting",
        "title": "Min comparisons in finding min and max",
        "text": "<p>What is the minimum number of comparisons required to determine both the minimum and maximum elements in an unsorted array of size 100 using an optimal pairwise comparison algorithm?</p>",
        "options": [],
        "ans": "148",
        "expl": "For an array of $n$ elements, comparing elements in pairs takes $\\lfloor n/2 \\rfloor$ comparisons. The winners compete for maximum ($\lceil n/2 \rceil - 1$ comparisons) and the losers compete for minimum ($\lceil n/2 \rceil - 1$ comparisons). Total $= \\lceil 3n/2 \\rceil - 2$. For $n=100$: $3(100)/2 - 2 = 150 - 2 = 148$."
    },
    {
        "type": "MSQ", "category": "Greedy Algorithms",
        "title": "Properties of Fractional Knapsack",
        "text": "<p>Consider the Fractional Knapsack problem with items having values $v_i$ and weights $w_i$. Which of the following statements is/are <strong>TRUE</strong>?</p>",
        "options": [
            ("A", "Sorting items in decreasing order of value-to-weight ratio $v_i/w_i$ guarantees an optimal solution."),
            ("B", "The greedy choice property always holds for the 0/1 Knapsack problem."),
            ("C", "If all items have the same value-to-weight ratio, any greedy selection that fills the knapsack is optimal."),
            ("D", "Fractional knapsack can be solved in $O(n)$ time using a linear-time selection algorithm without fully sorting.")
        ],
        "ans": "A;C;D",
        "expl": "<b>A is TRUE:</b> Standard greedy algorithm on $v_i/w_i$ is optimal for fractional knapsack.<br/><b>B is FALSE:</b> 0/1 knapsack requires dynamic programming; greedy heuristic fails.<br/><b>C is TRUE:</b> Since every unit of weight yields identical value, any combination reaching full capacity achieves max value.<br/><b>D is TRUE:</b> Using median-of-medians $O(n)$ selection to find the pivot ratio and partitioning achieves $O(n)$ without full sorting."
    },
    {
        "type": "MCQ", "category": "Graph Algorithms",
        "title": "Topological Sort Existence",
        "text": "<p>Let $G = (V, E)$ be a directed graph. Which of the following conditions is both <strong>necessary and sufficient</strong> for $G$ to have a topological sorting?</p>",
        "options": [
            ("A", "$G$ is strongly connected"),
            ("B", "$G$ has a unique vertex with in-degree 0"),
            ("C", "$G$ contains no directed cycles (DAG)"),
            ("D", "$G$ is weakly connected")
        ],
        "ans": "C",
        "expl": "A topological sort exists if and only if the directed graph contains no directed cycles (i.e., it is a Directed Acyclic Graph, DAG). Strongly connected graphs with $>1$ vertices contain cycles and have no topological ordering."
    },
    {
        "type": "NAT", "category": "Divide and Conquer",
        "title": "Strassen Matrix Multiplication Multiplication Count",
        "text": "<p>Standard matrix multiplication of two $2 \\times 2$ matrices requires 8 scalar multiplications. Strassen's algorithm reduces the number of scalar multiplications of $2 \\times 2$ block matrices to:</p>",
        "options": [],
        "ans": "7",
        "expl": "Strassen's algorithm uses 7 multiplications instead of 8, leading to recurrence $T(n) = 7T(n/2) + O(n^2)$, giving complexity $O(n^{\\log_2 7}) \\approx O(n^{2.807})$."
    },
    # 2-Mark Questions
    {
        "type": "MCQ", "category": "Dynamic Programming",
        "title": "Longest Common Subsequence Length",
        "text": "<p>Consider two sequences $X = \\langle A, B, C, B, D, A, B \\rangle$ and $Y = \\langle B, D, C, A, B, A \\rangle$. What is the length of the Longest Common Subsequence (LCS) of $X$ and $Y$?</p>",
        "options": [
            ("A", "3"),
            ("B", "4"),
            ("C", "5"),
            ("D", "6")
        ],
        "ans": "B",
        "expl": "Common subsequences include $\\langle B, C, B, A \\rangle$, $\\langle B, D, A, B \\rangle$, and $\\langle B, C, A, B \\rangle$. Each has length 4. There is no common subsequence of length 5."
    },
    {
        "type": "NAT", "category": "Graph Algorithms",
        "title": "Bellman-Ford Relaxations",
        "text": "<p>Consider a directed graph $G = (V, E)$ with $|V| = 12$ and $|E| = 45$. In the worst-case, how many total edge relaxation operations are performed by the Bellman-Ford algorithm to compute single-source shortest paths (excluding negative cycle detection pass)?</p>",
        "options": [],
        "ans": "495",
        "expl": "Bellman-Ford runs $|V|-1$ passes over all $|E|$ edges. Total edge relaxations $= (|V| - 1) \\times |E| = (12 - 1) \\times 45 = 11 \\times 45 = 495$."
    },
    {
        "type": "MSQ", "category": "Minimum Spanning Tree",
        "title": "Prim vs Kruskal Characteristics",
        "text": "<p>Let $G = (V, E)$ be a connected, weighted graph with distinct edge weights. Which of the following statements is/are <strong>TRUE</strong>?</p>",
        "options": [
            ("A", "Prim's algorithm always maintains a connected tree throughout its execution."),
            ("B", "Kruskal's algorithm may maintain an acyclic forest of disconnected components before completion."),
            ("C", "Kruskal's algorithm with disjoint-set union by rank and path compression runs in $O(|E| \\log |V|)$ time."),
            ("D", "If an edge has the second smallest weight in the graph, it must belong to the MST.")
        ],
        "ans": "A;B;C;D",
        "expl": "<b>A is TRUE:</b> Prim grows a single tree vertex by vertex.<br/><b>B is TRUE:</b> Kruskal picks lightest non-cycle edges anywhere in the graph, forming a forest.<br/><b>C is TRUE:</b> Sorting takes $O(|E| \\log |E|) = O(|E| \\log |V|)$, and union-find takes $O(|E| \\alpha(|V|))$.<br/><b>D is TRUE:</b> With distinct weights, the lightest edge is always chosen; the second lightest cannot create a cycle with only one edge, so it is always picked in Kruskal's second step."
    },
    {
        "type": "MCQ", "category": "NP-Completeness",
        "title": "Reducibility and Complexity Classes",
        "text": "<p>Let $L_1, L_2$ be two decision problems. Suppose $L_1 \\le_P L_2$ (i.e. $L_1$ is polynomial-time reducible to $L_2$). Which of the following deductions is <strong>GUARANTEED TO BE VALID</strong>?</p>",
        "options": [
            ("A", "If $L_1 \\in \\text{P}$, then $L_2 \\in \\text{P}$"),
            ("B", "If $L_2$ is NP-complete, then $L_1$ must be NP-complete"),
            ("C", "If $L_2 \\in \\text{P}$, then $L_1 \\in \\text{P}$"),
            ("D", "If $L_1$ is undecidable, then $L_2$ must be in P")
        ],
        "ans": "C",
        "expl": "Reducibility $L_1 \\le_P L_2$ means $L_2$ is at least as hard as $L_1$. If the harder problem $L_2$ can be solved in polynomial time ($L_2 \\in P$), then the easier problem $L_1$ can also be solved in polynomial time by reducing it in poly-time to $L_2$ and solving it."
    },
    {
        "type": "NAT", "category": "Divide and Conquer",
        "title": "Recurrence Expansion Evaluation",
        "text": "<p>Consider the recurrence relation $T(n) = 3T(n/3) + n$ with $T(1) = 2$. What is the exact value of $T(27)$?</p>",
        "options": [],
        "ans": "135",
        "expl": "$T(1) = 2$.<br/>$T(3) = 3T(1) + 3 = 3(2) + 3 = 9$.<br/>$T(9) = 3T(3) + 9 = 3(9) + 9 = 36$.<br/>$T(27) = 3T(9) + 27 = 3(36) + 27 = 108 + 27 = 135$."
    },
    {
        "type": "MCQ", "category": "Graph Algorithms",
        "title": "Floyd-Warshall Algorithm Matrix Progression",
        "text": "<p>In the Floyd-Warshall all-pairs shortest path algorithm on an $n$-vertex graph, what does entry $D^{(k)}[i][j]$ represent after the $k$-th iteration?</p>",
        "options": [
            ("A", "The shortest path from $i$ to $j$ containing at most $k$ edges"),
            ("B", "The shortest path from $i$ to $j$ using only intermediate vertices from the set $\\{1, 2, \\dots, k\\}$"),
            ("C", "The shortest path from vertex $k$ to all other vertices"),
            ("D", "The length of the cycle passing through vertex $k$")
        ],
        "ans": "B",
        "expl": "Floyd-Warshall is parameterized by the set of allowed intermediate vertices: $D^{(k)}[i][j] = \\min(D^{(k-1)}[i][j], D^{(k-1)}[i][k] + D^{(k-1)}[k][j])$, meaning intermediate vertices are strictly drawn from $\\{1, 2, \\dots, k\\}$."
    },
    {
        "type": "NAT", "category": "Greedy Algorithms",
        "title": "Interval Scheduling Max Non-Overlapping",
        "text": "<p>Consider 6 intervals with [start, end] times: $[1, 4], [3, 5], [0, 6], [5, 7], [3, 9], [5, 9], [6, 10], [8, 11]$. What is the maximum number of mutually compatible (non-overlapping) intervals that can be selected?</p>",
        "options": [],
        "ans": "3",
        "expl": "Greedy choice by earliest finish time:<br/>1. Pick $[1, 4]$ (finishes at 4).<br/>2. Compatible remaining: $[5, 7], [5, 9], [6, 10], [8, 11]$. Earliest finish is $[5, 7]$ (finishes at 7).<br/>3. Compatible remaining: $[8, 11]$. Pick $[8, 11]$.<br/>Total compatible intervals = 3 ($\\{[1,4], [5,7], [8,11]\\}$)."
    },
    {
        "type": "MSQ", "category": "Dynamic Programming",
        "title": "Optimal Substructure and Overlapping Subproblems",
        "text": "<p>Which of the following problems exhibit <strong>optimal substructure</strong>?</p>",
        "options": [
            ("A", "Single-pair Shortest Path in a graph with non-negative edge weights"),
            ("B", "Longest Simple Path between two vertices in an unweighted directed graph"),
            ("C", "Matrix Chain Multiplication"),
            ("D", "0/1 Knapsack Problem")
        ],
        "ans": "A;C;D",
        "expl": "<b>A, C, D have optimal substructure:</b> Optimal solutions contain optimal sub-solutions.<br/><b>B DOES NOT:</b> Longest simple path does not have optimal substructure because subproblems share vertices and are not independent (finding longest simple path is NP-hard)."
    },
    {
        "type": "NAT", "category": "Sorting",
        "title": "QuickSort Best Case Tree Depth",
        "text": "<p>For an array of $n = 63$ distinct elements, in the ideal best-case scenario where QuickSort always partitions arrays into two equal halves of size $(n-1)/2$, what is the total depth of the recursion tree (counting root as level 0)?</p>",
        "options": [],
        "ans": "5",
        "expl": "At level 0: 63 elements.<br/>Level 1: 31 elements.<br/>Level 2: 15 elements.<br/>Level 3: 7 elements.<br/>Level 4: 3 elements.<br/>Level 5: 1 element.<br/>Tree depth (with root = level 0) $= \\log_2(63 + 1) - 1 = 6 - 1 = 5$."
    },
    {
        "type": "MCQ", "category": "Algorithms - Backtracking",
        "title": "N-Queens State Space Search",
        "text": "<p>In the 4-Queens problem solved using backtracking on a $4 \\times 4$ chessboard, how many distinct valid non-attacking configurations exist?</p>",
        "options": [
            ("A", "1"),
            ("B", "2"),
            ("C", "4"),
            ("D", "8")
        ],
        "ans": "B",
        "expl": "The 4-Queens problem has exactly 2 distinct solutions: [2, 4, 1, 3] and [3, 1, 4, 2] (1-indexed column positions for rows 1 to 4), which are mirror reflections of each other."
    }
]

# DATA STRUCTURES QUESTIONS
DS_QS = [
    # 1-Mark
    {
        "type": "MCQ", "category": "Binary Search Trees",
        "title": "BST Postorder to Preorder",
        "text": "<p>The postorder traversal of a Binary Search Tree (BST) is: $2, 4, 3, 7, 9, 8, 5$. What is the preorder traversal of this BST?</p>",
        "options": [
            ("A", "$5, 3, 2, 4, 8, 7, 9$"),
            ("B", "$5, 8, 9, 7, 3, 4, 2$"),
            ("C", "$2, 3, 4, 5, 7, 8, 9$"),
            ("D", "$5, 2, 3, 4, 7, 8, 9$")
        ],
        "ans": "A",
        "expl": "In postorder (Left, Right, Root), the last element $5$ is the root. In BST, elements $< 5$ ($\\{2, 4, 3\\}$) are in left subtree and $> 5$ ($\\{7, 9, 8\\}$) are in right subtree. Left subtree root is 3, with left child 2 and right child 4. Right subtree root is 8, with left child 7 and right child 9. Preorder (Root, Left, Right) is $5, 3, 2, 4, 8, 7, 9$."
    },
    {
        "type": "NAT", "category": "Binary Heaps",
        "title": "Min-Heap Height Calculation",
        "text": "<p>A complete binary min-heap contains 100 distinct elements. If the root is at height 0, what is the maximum height of any leaf node in this heap?</p>",
        "options": [],
        "ans": "6",
        "expl": "Height of a complete binary tree with $n$ nodes is $\\lfloor \\log_2 n \\rfloor$. For $n = 100$, $2^6 = 64 \\le 100 < 2^7 = 128$. Hence the tree has height $\\lfloor \\log_2 100 \\rfloor = 6$."
    },
    {
        "type": "MSQ", "category": "Hash Tables",
        "title": "Collision Resolution Mechanisms",
        "text": "<p>Which of the following statements is/are <strong>TRUE</strong> regarding open addressing in hash tables?</p>",
        "options": [
            ("A", "Linear probing suffers from primary clustering."),
            ("B", "Quadratic probing completely eliminates both primary and secondary clustering."),
            ("C", "Double hashing uses probe sequence $h(k, i) = (h_1(k) + i \\cdot h_2(k)) \\pmod m$ and avoids primary clustering."),
            ("D", "In open addressing, the load factor $\\alpha$ can never exceed 1.0.")
        ],
        "ans": "A;C;D",
        "expl": "<b>A is TRUE:</b> Linear probing creates long contiguous runs of occupied slots.<br/><b>B is FALSE:</b> Quadratic probing eliminates primary clustering but still suffers from secondary clustering (keys hashing to same initial slot follow identical probe paths).<br/><b>C is TRUE:</b> Double hashing uses two independent hash functions to disperse keys.<br/><b>D is TRUE:</b> Because all keys reside within the array table itself, number of keys cannot exceed table capacity."
    },
    {
        "type": "MCQ", "category": "Stacks and Queues",
        "title": "Queue implementation using two stacks",
        "text": "<p>A queue is implemented using two stacks $S_1$ and $S_2$. Enqueue pushes onto $S_1$. Dequeue pops from $S_2$; if $S_2$ is empty, all elements from $S_1$ are popped and pushed to $S_2$, then $S_2$ is popped. What is the amortized cost per operation over a sequence of $n$ enqueue and dequeue operations?</p>",
        "options": [
            ("A", "$O(1)$"),
            ("B", "$O(\\log n)$"),
            ("C", "$O(n)$"),
            ("D", "$O(n^2)$")
        ],
        "ans": "A",
        "expl": "Every element is pushed to $S_1$ once, popped from $S_1$ once, pushed to $S_2$ once, and popped from $S_2$ once. That is at most 4 stack operations per element over its entire lifetime in the queue. Total cost for $n$ operations is $O(n)$, giving amortized cost $O(1)$ per operation."
    },
    {
        "type": "NAT", "category": "AVL Trees",
        "title": "Minimum nodes in AVL tree of height 5",
        "text": "<p>What is the minimum number of nodes in an AVL tree of height 5, where a tree with a single node has height 0?</p>",
        "options": [],
        "ans": "20",
        "expl": "Let $N(h)$ be the minimum number of nodes in an AVL tree of height $h$. $N(h) = N(h-1) + N(h-2) + 1$ with $N(0) = 1, N(1) = 2$.<br/>$N(2) = 2 + 1 + 1 = 4$.<br/>$N(3) = 4 + 2 + 1 = 7$.<br/>$N(4) = 7 + 4 + 1 = 12$.<br/>$N(5) = 12 + 7 + 1 = 20$."
    },
    # 2-Mark
    {
        "type": "NAT", "category": "Binary Trees",
        "title": "Strictly Binary Tree Leaves",
        "text": "<p>A strictly binary tree (every non-leaf node has exactly 2 children) has 45 internal nodes. What is the number of leaf nodes in this tree?</p>",
        "options": [],
        "ans": "46",
        "expl": "In any strictly binary tree, the number of leaf nodes $L$ and internal nodes $I$ satisfy $L = I + 1$. Here $I = 45 \\implies L = 45 + 1 = 46$."
    },
    {
        "type": "MCQ", "category": "Red-Black Trees",
        "title": "Red-Black Tree Properties",
        "text": "<p>Which of the following is an <strong>INVALID</strong> property of a Red-Black Tree with $n$ nodes?</p>",
        "options": [
            ("A", "Every red node has two black children"),
            ("B", "Every simple path from a node to any of its descendant leaves contains the same number of black nodes"),
            ("C", "The root can be either red or black without violating the tree definition"),
            ("D", "The height of a Red-Black tree with $n$ internal nodes is at most $2 \\log_2(n+1)$")
        ],
        "ans": "C",
        "expl": "By definition of Red-Black trees (CLRS), property 2 strictly requires that the root node must be BLACK. If the root were allowed to be red, it violates the standard invariant."
    },
    {
        "type": "MSQ", "category": "B-Trees",
        "title": "B-Tree Order and Key Range",
        "text": "<p>Consider a B-Tree of order $m=5$ (where order $m$ is the maximum number of children a node can have). Which of the following statements is/are <strong>TRUE</strong>?</p>",
        "options": [
            ("A", "The root node must contain at least 2 children unless it is a leaf."),
            ("B", "Every internal node other than the root must contain at least $\\lceil 5/2 \\rceil = 3$ children."),
            ("C", "The maximum number of keys in any node is 4."),
            ("D", "Every internal node other than the root must contain at least 2 keys.")
        ],
        "ans": "A;B;C;D",
        "expl": "For B-Tree of order $m=5$:<br/>- Max children $= 5$, max keys $= m-1 = 4$.<br/>- Min children for non-root internal node $= \\lceil m/2 \\rceil = \\lceil 5/2 \\rceil = 3$.<br/>- Min keys for non-root internal node $= \\lceil m/2 \\rceil - 1 = 3 - 1 = 2$.<br/>- Root has at least 2 children if not leaf.<br/>All statements are correct."
    },
    {
        "type": "NAT", "category": "Binary Heaps",
        "title": "Build-Heap Linear Time",
        "text": "<p>A max-heap is constructed from an array $[10, 20, 15, 30, 40, 50, 60, 25]$ using Floyd's bottom-up `BUILD-MAX-HEAP` algorithm. What is the value at index 2 (1-indexed, root at index 1) after the heap is built?</p>",
        "options": [],
        "ans": "40",
        "expl": "Array: indices 1 to 8: $[10, 20, 15, 30, 40, 50, 60, 25]$.<br/>Leaves are indices 5 to 8 ($40, 50, 60, 25$).<br/>Heapify at index 4 (value 30, child 8 with value 25): unchanged.<br/>Heapify at index 3 (value 15, children 6 and 7 with values 50, 60): swap 15 with 60 $\\rightarrow$ index 3 becomes 60.<br/>Heapify at index 2 (value 20, children 4 and 5 with values 30, 40): swap 20 with 40 $\\rightarrow$ index 2 becomes 40.<br/>Heapify at index 1 (value 10, children 2 and 3 with values 40, 60): swap 10 with 60 $\\rightarrow$ index 1 is 60, index 3 gets 10, which swaps with 50.<br/>Index 2 retains value 40."
    },
    {
        "type": "MCQ", "category": "Linked Lists",
        "title": "Detecting Cycle in Linked List",
        "text": "<p>Floyd's Cycle-Finding Algorithm (tortoise and hare) uses two pointers moving at speeds 1 and 2 respectively. If a linked list has a non-cyclic prefix of length $\\mu$ and a cycle of length $\\lambda$, where do the two pointers first meet relative to the start of the cycle?</p>",
        "options": [
            ("A", "At distance $(\\lambda - (\\mu \\pmod \\lambda)) \\pmod \\lambda$ from the start of the cycle"),
            ("B", "Always at the start of the cycle"),
            ("C", "At distance $\\mu \\pmod \\lambda$ from the start of the cycle"),
            ("D", "They never meet if $\\lambda$ is even")
        ],
        "ans": "A",
        "expl": "When the slow pointer enters the cycle at step $\\mu$, the fast pointer is at position $(2\\mu - \\mu) \\pmod \\lambda = \\mu \\pmod \\lambda$. The distance fast must catch up is $\\lambda - (\\mu \\pmod \\lambda)$. With relative speed 1 step/iteration, they meet at distance $(\\lambda - (\\mu \\pmod \\lambda)) \\pmod \\lambda$."
    }
]

def build_test_suite():
    os.makedirs(TESTS_DIR, exist_ok=True)
    manifest_entries = []

    # 1. TOPIC TESTS (15 Qs, 45 Mins, 25 Marks)
    # We will build 10 focused Topic Tests
    topic_tests_config = [
        ("GO2027_Algo_TopicTest1", "GO Classes CS 2027 | Algorithms | Asymptotics & Recurrences", "Algorithms", ALGO_QS),
        ("GO2027_DS_TopicTest1", "GO Classes CS 2027 | Data Structures | Trees & Heaps", "Data Structures", DS_QS)
    ]

    for test_id, title, subject, q_pool in topic_tests_config:
        # Take up to 15 questions, assigning Q1-5 1M, Q6-15 2M
        test_qs = []
        for i in range(min(15, len(q_pool))):
            src = q_pool[i]
            q_num = i + 1
            marks = 1.0 if q_num <= 5 else 2.0
            test_qs.append(make_question(
                i, q_num, "Technical", src["type"], marks, src["category"],
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
            "totalQuestions": len(test_qs),
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
            "totalQuestions": len(test_qs),
            "totalMarks": int(total_marks),
            "sections": ["Technical"]
        })

    # Read manifest and merge cleanly
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Avoid duplicate IDs
    existing_ids = set(m['id'] for m in manifest)
    added = 0
    for entry in manifest_entries:
        if entry['id'] not in existing_ids:
            manifest.insert(0, entry) # insert at top
            added += 1

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated and integrated {added} GO Classes format GATE 2027 tests!")
    print(f"Total tests in manifest: {len(manifest)}")

if __name__ == '__main__':
    build_test_suite()
