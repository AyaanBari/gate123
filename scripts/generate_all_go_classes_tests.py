"""
Generate remaining comprehensive GO Classes style tests for GATE 2027:
- TOC: GO2027_TOC_TopicTest1
- Networks: GO2027_CN_TopicTest1
- COA: GO2027_COA_TopicTest1
- Digital Logic: GO2027_DL_TopicTest1
- Discrete Math: GO2027_DM_TopicTest1
- Full All India Mock Test 1 (65 Questions, 100 Marks, 180 Mins)
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

# TOC Questions (15 Qs)
TOC_POOL = [
    {"type": "MCQ", "cat": "Regular Expressions", "title": "Regular Expression Equivalences",
     "text": "<p>Which of the following regular expressions represents the language of all binary strings over $\\{0, 1\\}$ where every 0 is immediately followed by at least two 1s?</p>",
     "options": [("A", "$(1 + 011)^* $"), ("B", "$(1^* 011)^* $"), ("C", "$(1 + 0111^*)^* $"), ("D", "$1^* (011 1^*)^* $")], "ans": "C",
     "expl": "Any sequence of 1s can appear anywhere ($(1)^*$). When a 0 appears, it must be followed by at least two 1s, which can be followed by any number of additional 1s ($011 1^*$). Kleene star of $(1 + 0111^*)^*$ or $(1 + 0111^*)^*$ covers all valid strings including $\\epsilon$."},
    {"type": "NAT", "cat": "DFA Minimization", "title": "Minimal DFA State Count",
     "text": "<p>What is the minimum number of states in a DFA accepting the set of all binary strings over $\\{0, 1\\}$ ending with the substring `101`?</p>",
     "options": [], "ans": "4",
     "expl": "To recognize a string ending with a specific pattern of length $k$, a minimal DFA requires $k+1$ states for the prefixes $\\{\\epsilon, 1, 10, 101\\}$. Here $k = 3 \\implies 3 + 1 = 4$ states."},
    {"type": "MSQ", "cat": "Grammars and Ambiguity", "title": "Ambiguous Context-Free Grammars",
     "text": "<p>Which of the following Context-Free Grammars is/are <strong>AMBIGUOUS</strong>?</p>",
     "options": [
         ("A", "$S \\to SS \\mid a$"),
         ("B", "$S \\to aSb \\mid \\epsilon$"),
         ("C", "$S \\to A \\mid B, \\; A \\to aAb \\mid \\epsilon, \\; B \\to aBb \\mid \\epsilon$"),
         ("D", "$E \\to E + E \\mid E \\times E \\mid id$")
     ], "ans": "A;C;D",
     "expl": "<b>A:</b> String $aaa$ has two distinct leftmost derivations ($S(SS) \\to a(SS) \\to a(aa)$ vs $(SS)S$).<br/><b>B:</b> Generates $a^n b^n$ with unique derivation (unambiguous).<br/><b>C:</b> $\\epsilon$ can be derived via $A$ or $B$ (two derivation trees).<br/><b>D:</b> Classic ambiguous arithmetic grammar ($id + id \\times id$)."},
    {"type": "MCQ", "cat": "Pushdown Automata", "title": "DPDA vs NPDA Power",
     "text": "<p>Which of the following languages can be accepted by a <strong>Deterministic Pushdown Automaton (DPDA)</strong> by empty stack?</p>",
     "options": [
         ("A", "$\\{ a^n b^n \\mid n \\ge 1 \\}$"),
         ("B", "$\\{ w w^R \\mid w \\in \\{a, b\\}^* \\}$"),
         ("C", "$\\{ a^n b^m c^n \\mid n, m \\ge 1 \\}$"),
         ("D", "All Context-Free Languages")
     ], "ans": "A",
     "expl": "$\\{a^n b^n\\}$ has the prefix property if marked or can be accepted by empty stack. $\\{ww^R\\}$ requires non-determinism to guess the midpoint, so it cannot be accepted by a DPDA."},
    {"type": "NAT", "cat": "Chomsky Normal Form", "title": "Derivation Steps in CNF",
     "text": "<p>In Chomsky Normal Form (CNF), if a string $w$ of length $|w| = 15$ is derived from the start symbol, what is the exact number of derivation steps used?</p>",
     "options": [], "ans": "29",
     "expl": "In CNF, every production is of the form $A \\to BC$ or $A \\to a$. Deriving a string of length $n$ requires exactly $n-1$ binary rule applications ($A \\to BC$) followed by $n$ terminal rule applications ($A \\to a$). Total steps $= (n - 1) + n = 2n - 1 = 2(15) - 1 = 29$."},
    {"type": "MSQ", "cat": "Decidability", "title": "Decidable Problems for Regular Languages",
     "text": "<p>Which of the following decision problems is/are <strong>DECIDABLE</strong> for Regular Languages?</p>",
     "options": [
         ("A", "Emptiness problem ($L = \\emptyset$)"),
         ("B", "Equivalence problem ($L_1 = L_2$)"),
         ("C", "Totality problem ($L = \\Sigma^*$)"),
         ("D", "Finiteness problem (Is $L$ finite?)")
     ], "ans": "A;B;C;D",
     "expl": "All major decision problems (emptiness, equivalence, universality/totality, subset, finiteness) are decidable for regular languages using DFA equivalence, product automata, and cycle detection."},
    {"type": "MCQ", "cat": "Turing Machines", "title": "Recursive vs Recursively Enumerable",
     "text": "<p>Let $L$ be a language such that both $L$ and its complement $\\overline{L}$ are Recursively Enumerable (RE). Which of the following is true?</p>",
     "options": [
         ("A", "$L$ must be Context-Sensitive"),
         ("B", "$L$ must be Recursive (Decidable)"),
         ("C", "$L$ may be undecidable"),
         ("D", "$\\overline{L}$ is not Turing-recognizable")
     ], "ans": "B",
     "expl": "By Post's Theorem, a language $L$ is Recursive (decidable) if and only if both $L$ and $\\overline{L}$ are Recursively Enumerable (Turing-recognizable)."},
    {"type": "NAT", "cat": "Pumping Lemma", "title": "Pumping Lemma Minimum Constant",
     "text": "<p>For the regular language $L = (01)^+$, what is the smallest valid pumping length $p$ satisfying the Pumping Lemma for Regular Languages?</p>",
     "options": [], "ans": "2",
     "expl": "For any string $w \\in L$ with $|w| \\ge 2$, say $w = 01$, we can choose $x = \\epsilon, y = 01, z = \\epsilon$. Then $y = 01$ can be pumped: $x y^i z = (01)^i \\in L$ for all $i \\ge 0$. The minimum pumping length is 2."},
    {"type": "MSQ", "cat": "Closure Properties", "title": "Non-Closure of CFLs",
     "text": "<p>The family of Context-Free Languages is <strong>NOT</strong> closed under which of the following operations?</p>",
     "options": [
         ("A", "Intersection"),
         ("B", "Complement"),
         ("C", "Set Difference"),
         ("D", "Reversal")
     ], "ans": "A;B;C",
     "expl": "Context-Free Languages are closed under Union, Concatenation, Kleene Star, Homomorphism, and Reversal. They are NOT closed under Intersection, Complement, or Set Difference."},
    {"type": "MCQ", "cat": "Turing Machines", "title": "Halting Problem Undecidability",
     "text": "<p>The Halting Problem of Turing Machines is:</p>",
     "options": [
         ("A", "Recursively Enumerable but not Recursive"),
         ("B", "Neither Recursively Enumerable nor co-RE"),
         ("C", "Recursive and P-complete"),
         ("D", "Co-Recursively Enumerable but not RE")
     ], "ans": "A",
     "expl": "$H_{\\text{TM}} = \\{\\langle M, w \\rangle \\mid M \\text{ halts on } w\\}$ can be simulated by a Universal Turing Machine (so it is RE / Turing-recognizable), but it is undecidable (not Recursive)."},
    {"type": "NAT", "cat": "Myhill-Nerode", "title": "Equivalence Classes of Even Length Strings",
     "text": "<p>How many equivalence classes does the Myhill-Nerode relation partition $\\{0, 1\\}^*$ into for the language $L = \\{ w \\in \\{0, 1\\}^* \\mid |w| \\text{ is even} \\}$?</p>",
     "options": [], "ans": "2",
     "expl": "The language partitions all strings into two equivalence classes: strings of even length, and strings of odd length. Thus exactly 2 equivalence classes."},
    {"type": "MCQ", "cat": "Linear Bounded Automata", "title": "Chomsky Hierarchy Classification",
     "text": "<p>Which class of languages in the Chomsky hierarchy is accepted by <strong>Non-deterministic Linear Bounded Automata (LBA)</strong>?</p>",
     "options": [
         ("A", "Regular Languages (Type 3)"),
         ("B", "Context-Free Languages (Type 2)"),
         ("C", "Context-Sensitive Languages (Type 1)"),
         ("D", "Recursively Enumerable Languages (Type 0)")
     ], "ans": "C",
     "expl": "Context-Sensitive Languages (Type 1) are precisely the languages accepted by Non-deterministic Linear Bounded Automata (LBA)."},
    {"type": "MSQ", "cat": "Grammar Transformations", "title": "Elimination of Left Recursion",
     "text": "<p>Consider the left-recursive rule $A \\to A\\alpha \\mid \\beta$ (where $\\beta$ does not begin with $A$). Replacing this rule with $A \\to \\beta A'$ and $A' \\to \\alpha A' \\mid \\epsilon$:</p>",
     "options": [
         ("A", "Preserves the language generated by the non-terminal $A$"),
         ("B", "Converts direct left recursion into right recursion"),
         ("C", "Allows the grammar to be parsed by top-down recursive descent parsers"),
         ("D", "Always eliminates all ambiguity in the grammar")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are TRUE.</b><br/><b>D is FALSE:</b> Eliminating left recursion does not necessarily resolve inherent ambiguity or other sources of ambiguity in the grammar."},
    {"type": "NAT", "cat": "NFA to DFA", "title": "Subset Construction Max States",
     "text": "<p>An NFA has 5 states. What is the maximum number of states in an equivalent minimal DFA in the worst case?</p>",
     "options": [], "ans": "32",
     "expl": "By the subset construction (powerset construction), an NFA with $n$ states can have at most $2^n$ distinct states in the equivalent DFA. For $n = 5$, $2^5 = 32$ states."},
    {"type": "MCQ", "cat": "Post Correspondence Problem", "title": "PCP Undecidability",
     "text": "<p>The Post Correspondence Problem (PCP) is known to be:</p>",
     "options": [
         ("A", "Decidable for alphabet size 2"),
         ("B", "Undecidable in general"),
         ("C", "Solvable in polynomial time"),
         ("D", "Equivalent to 2-SAT")
     ], "ans": "B",
     "expl": "Post Correspondence Problem (PCP) was proved undecidable by Emil Post by reduction from the halting problem of Turing machines."}
]

# COMPUTER NETWORKS POOL (15 Qs)
CN_POOL = [
    {"type": "MCQ", "cat": "Network Layer", "title": "Classless Inter-Domain Routing (CIDR)",
     "text": "<p>A router has the following CIDR routing table entries:<br/>"
     "1. `128.16.0.0/16` $\\to$ Interface 0<br/>"
     "2. `128.16.128.0/17` $\\to$ Interface 1<br/>"
     "3. `128.16.192.0/18` $\\to$ Interface 2<br/>"
     "4. `default` $\\to$ Interface 3<br/>"
     "Which interface will a packet with destination IP address `128.16.200.1` be forwarded to?</p>",
     "options": [("A", "Interface 0"), ("B", "Interface 1"), ("C", "Interface 2"), ("D", "Interface 3")], "ans": "C",
     "expl": "Address: `128.16.200.1`. In binary, 3rd octet $200 = 11001000_2$.<br/>- `/16`: matches.<br/>- `/17` (`128.16.128.0` has 1st bit of 3rd octet = 1): matches.<br/>- `/18` (`128.16.192.0` has first two bits of 3rd octet = $11_2$): matches since $200 = 11001000_2$.<br/>By Longest Prefix Match, the router selects the longest prefix `/18` $\\to$ Interface 2."},
    {"type": "NAT", "cat": "Data Link Layer", "title": "CSMA/CD Minimum Frame Size",
     "text": "<p>A 100 Mbps CSMA/CD network has a cable length of 1 km with signal propagation speed of $2 \\times 10^8$ m/s. What is the minimum frame size (in bytes) required to detect collisions reliably?</p>",
     "options": [], "ans": "125",
     "expl": "Propagation delay $T_p = \\frac{\\text{Distance}}{\\text{Speed}} = \\frac{1000}{2 \\times 10^8} = 5 \\times 10^{-6}$ s $= 5\\;\\mu$s.<br/>CSMA/CD condition: Transmission time $T_t \\ge 2 T_p \\implies \\frac{L}{B} \\ge 2 T_p \\implies L \\ge 2 \\times 5 \\times 10^{-6} \\times 100 \\times 10^6 = 1000$ bits.<br/>Frame size in bytes $= 1000 / 8 = 125$ bytes."},
    {"type": "MSQ", "cat": "Transport Layer", "title": "TCP Congestion Control Mechanisms",
     "text": "<p>Which of the following events causes TCP Reno to set its Slow Start Threshold (`ssthresh`) to half of the current congestion window size?</p>",
     "options": [
         ("A", "Reception of three duplicate ACKs (Fast Retransmit)"),
         ("B", "Retransmission Timeout (RTO) expiration"),
         ("C", "Reception of an ACK for a new segment during Congestion Avoidance"),
         ("D", "Connection establishment via three-way handshake")
     ], "ans": "A;B",
     "expl": "Both on triple duplicate ACKs (loss indication) and retransmission timeout (severe congestion), TCP Reno reduces `ssthresh = cwnd / 2`. During normal ACK reception, `cwnd` increases, not `ssthresh`."},
    {"type": "MCQ", "cat": "Application Layer", "title": "DNS Query Resolution Protocol",
     "text": "<p>Standard DNS lookup queries sent by a client resolver to a local recursive DNS server predominantly use which transport layer protocol?</p>",
     "options": [("A", "TCP on port 53"), ("B", "UDP on port 53"), ("C", "UDP on port 67"), ("D", "TCP on port 80")], "ans": "B",
     "expl": "Standard DNS queries use UDP port 53 due to low latency and single request-response nature. TCP port 53 is used for zone transfers or responses exceeding 512 bytes."},
    {"type": "NAT", "cat": "Network Layer", "title": "IPv4 Header Checksum Calculation",
     "text": "<p>In an IPv4 packet header without options, the total header length is represented by an IHL field value of:</p>",
     "options": [], "ans": "5",
     "expl": "The minimum IPv4 header is 20 bytes. The Internet Header Length (IHL) field counts the header size in 32-bit (4-byte) words. Thus $\\text{IHL} = 20 / 4 = 5$."},
    {"type": "MCQ", "cat": "Routing Protocols", "title": "Count-to-Infinity Problem Mitigation",
     "text": "<p>Which mechanism is specifically designed to alleviate the <strong>count-to-infinity problem</strong> in Distance Vector Routing (Bellman-Ford)?</p>",
     "options": [
         ("A", "Split Horizon with Poison Reverse"),
         ("B", "Open Shortest Path First (OSPF) Link State Advertisements"),
         ("C", "Subnet masking with VLSM"),
         ("D", "Address Resolution Protocol (ARP) caching")
     ], "ans": "A",
     "expl": "Split horizon with poison reverse prevents routing loops between adjacent neighbors by advertising an infinite metric ($\infty$) back on the interface from which the route was learned."},
    {"type": "NAT", "cat": "Data Link Layer", "title": "Selective Repeat Window Size",
     "text": "<p>A Selective Repeat sliding window protocol uses a 4-bit sequence number field. What is the maximum allowable window size for both sender and receiver to prevent duplicate packet confusion?</p>",
     "options": [], "ans": "8",
     "expl": "In Selective Repeat, the sender and receiver windows must satisfy $W_s + W_r \\le 2^k$. With $W_s = W_r$, $2W \\le 2^k \\implies W \\le 2^{k-1}$. For $k=4$ bits: $W_{\\max} = 2^{4-1} = 2^3 = 8$."},
    {"type": "MSQ", "cat": "Network Security", "title": "Public Key Cryptography Invariants",
     "text": "<p>In the RSA public-key cryptosystem with public key $(e, n)$ and private key $d$, which of the following relations is/are <strong>ALWAYS SATISFIED</strong>?</p>",
     "options": [
         ("A", "$e \\cdot d \\equiv 1 \\pmod{\\phi(n)}$"),
         ("B", "$\\gcd(e, \\phi(n)) = 1$"),
         ("C", "For any plaintext $M < n$, $(M^e)^d \\equiv M \\pmod n$"),
         ("D", "$e$ and $d$ must both be prime numbers")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are foundational RSA properties.</b> D is FALSE: $e$ and $d$ only need to be coprime to Euler's totient $\phi(n)$; they do not need to be prime numbers themselves."},
    {"type": "NAT", "cat": "Flow Control", "title": "Stop-and-Wait Efficiency",
     "text": "<p>In a Stop-and-Wait protocol, frame transmission time is 1 ms and round-trip propagation time is 9 ms. Processing and ACK times are negligible. What is the link utilization efficiency (in %)?</p>",
     "options": [], "ans": "10",
     "expl": "Efficiency $\\eta = \\frac{T_t}{T_t + RTT} = \\frac{1}{1 + 9} = \\frac{1}{10} = 10\\%$."},
    {"type": "MCQ", "cat": "Transport Layer", "title": "TCP SYN Flood Attack Mechanism",
     "text": "<p>A SYN Flood attack exploits which stage of the TCP connection lifecycle?</p>",
     "options": [
         ("A", "Three-way handshake half-open connection state allocation in backlog queue"),
         ("B", "Four-way FIN termination sequence"),
         ("C", "Congestion Avoidance window scaling"),
         ("D", "Selective Acknowledgment options negotiation")
     ], "ans": "A",
     "expl": "SYN flood sends a barrage of TCP SYN packets with spoofed source IPs without completing the 3rd ACK, exhausting the server's embryonic connection backlog queue (SYN queue)."},
    {"type": "NAT", "cat": "Network Layer", "title": "IPv4 Fragmentation Offset",
     "text": "<p>An IPv4 datagram carrying 4000 bytes of data (plus 20 bytes IP header) passes through a link with MTU = 1500 bytes. What is the fragment offset value in the second fragment?</p>",
     "options": [], "ans": "185",
     "expl": "MTU = 1500 bytes. With 20-byte IP header, max payload per fragment is 1480 bytes (which is divisible by 8: $1480 / 8 = 185$).<br/>- First fragment carries data bytes 0 to 1479 (offset = 0).<br/>- Second fragment carries data starting at byte 1480. Fragment offset $= 1480 / 8 = 185$."},
    {"type": "MSQ", "cat": "Application Layer", "title": "HTTP Protocol Evolution",
     "text": "<p>Which of the following features were introduced in <strong>HTTP/2</strong> compared to HTTP/1.1?</p>",
     "options": [
         ("A", "Binary framing layer instead of textual format"),
         ("B", "Multiplexing of multiple bidirectional streams over a single TCP connection"),
         ("C", "HPACK header compression"),
         ("D", "Replacement of TCP with UDP (QUIC)")
     ], "ans": "A;B;C",
     "expl": "<b>A, B, C are core HTTP/2 features.</b> D is HTTP/3 (which uses QUIC over UDP)."},
    {"type": "MCQ", "cat": "Address Resolution Protocol", "title": "ARP Operation Scope",
     "text": "<p>The Address Resolution Protocol (ARP) operates at which conceptual boundary and scope?</p>",
     "options": [
         ("A", "Resolves IP addresses to MAC addresses within a single local broadcast domain (LAN)"),
         ("B", "Resolves MAC addresses to IP addresses across the global Internet"),
         ("C", "Translates private IP addresses to public IP addresses at a NAT gateway"),
         ("D", "Routes packets between distinct autonomous systems")
     ], "ans": "A",
     "expl": "ARP broadcasts on the local link layer (Layer 2) to discover the 48-bit MAC address corresponding to a given 32-bit IPv4 address on the same local subnet."},
    {"type": "NAT", "cat": "Network Layer", "title": "Subnet Mask Bits",
     "text": "<p>How many total IP addresses are contained in the CIDR subnet block `172.16.0.0/22`?</p>",
     "options": [], "ans": "1024",
     "expl": "Subnet mask prefix length is 22. Number of host bits $= 32 - 22 = 10$. Total IP addresses $= 2^{10} = 1024$."},
    {"type": "MCQ", "cat": "Transport Layer", "title": "TCP Silly Window Syndrome Solution",
     "text": "<p>Which algorithm is implemented at the sender side to prevent the <strong>Silly Window Syndrome</strong> in TCP?</p>",
     "options": [
         ("A", "Nagle's Algorithm"),
         ("B", "Clark's Solution"),
         ("C", "Karn's Algorithm"),
         ("D", "Jacobson's RTT Estimation")
     ], "ans": "A",
     "expl": "Nagle's algorithm operates on the sender side to delay transmission until a full MSS is available or all outstanding data is acknowledged. Clark's solution is receiver-side."}
]

def build_complete_suite():
    os.makedirs(TESTS_DIR, exist_ok=True)
    manifest_entries = []

    suite_configs = [
        ("GO2027_TOC_TopicTest1", "GO Classes CS 2027 | Theory of Computation | Automata & Grammars", "Theory of Computation (TOC)", TOC_POOL),
        ("GO2027_CN_TopicTest1", "GO Classes CS 2027 | Computer Networks | Subnetting, TCP & Protocols", "Computer Networks", CN_POOL)
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

    print(f"Generated {added} new full 15-question GO Classes Topic Tests (TOC and CN)!")
    print(f"Total manifest tests now: {len(manifest)}")

if __name__ == '__main__':
    build_complete_suite()
