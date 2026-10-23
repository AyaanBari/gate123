"""
Generate 80 Full-Length Mock Tests for GATE 2027.
Each test paper contains:
- EXACTLY 65 questions
- EXACTLY 100 marks
- EXACTLY 180 minutes duration
- Section 1: General Aptitude (10 Questions: Q1-Q5 = 1M, Q6-Q10 = 2M; Total 15 Marks)
- Section 2: Technical (55 Questions: Q11-Q35 = 1M, Q36-Q65 = 2M; Total 85 Marks)
Covering all GATE CS subjects:
Algorithms, Data Structures, C Programming, TOC, Compilers, OS, DBMS, Networks, COA, Digital Logic, Discrete Math, Engg Math, Probability & Statistics, General Aptitude.
"""

import os
import glob
import json
import random
import re

BASE_DIR = r"d:\Gift\Gift"
TESTS_DIR = os.path.join(BASE_DIR, "data", "tests")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "exam_manifest.json")

def load_and_categorize_questions():
    print("Loading question bank from existing parsed tests...")
    
    # Pools
    aptitude_1m = []
    aptitude_2m = []
    
    # Subject-wise technical pools
    tech_1m = {
        'Algorithms': [],
        'Data Structures': [],
        'C Programming': [],
        'Theory of Computation (TOC)': [],
        'Compiler Design': [],
        'Operating Systems': [],
        'Databases (DBMS)': [],
        'Computer Networks': [],
        'Computer Organization (COA)': [],
        'Digital Logic': [],
        'Discrete Mathematics': [],
        'Engineering Mathematics': [],
        'Probability & Statistics': []
    }
    
    tech_2m = {k: [] for k in tech_1m.keys()}
    
    seen_hashes = set()
    
    # Load from all test JSONs
    for f in glob.glob(os.path.join(TESTS_DIR, "*.json")):
        # Skip previously generated mocks if any
        if "GATE2027_Mock_" in f:
            continue
            
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                test_subj = data.get('subject', 'General')
                
                for q in data.get('questions', []):
                    # Basic deduplication
                    q_html = q.get('questionHtml', '')
                    text_snippet = re.sub(r'<[^>]+>', '', q_html)[:150].strip()
                    if not text_snippet or text_snippet in seen_hashes:
                        continue
                    seen_hashes.add(text_snippet)
                    
                    sec = q.get('section', 'Technical')
                    cat = q.get('category', test_subj)
                    marks = float(q.get('marks', 1.0))
                    
                    q_item = {
                        'type': q.get('type', 'MCQ'),
                        'typeRaw': q.get('typeRaw', 'Multiple Choice Type'),
                        'marks': marks,
                        'penalty': q.get('penalty', 0.33 if marks == 1.0 else 0.67),
                        'category': cat,
                        'questionHtml': q_html,
                        'options': q.get('options', []),
                        'correctAnswer': q.get('correctAnswer', 'A'),
                        'discussUrl': q.get('discussUrl', 'https://gateoverflow.in')
                    }
                    
                    # Categorize Aptitude vs Technical
                    c_low = cat.lower() + " " + test_subj.lower()
                    if 'aptitude' in sec.lower() or 'aptitude' in c_low or 'verbal' in c_low or 'reasoning' in c_low:
                        if marks <= 1.0:
                            aptitude_1m.append(q_item)
                        else:
                            aptitude_2m.append(q_item)
                    else:
                        # Map to technical subject
                        mapped = 'General'
                        if 'algo' in c_low or 'sort' in c_low or 'greedy' in c_low or 'dynamic' in c_low:
                            mapped = 'Algorithms'
                        elif 'tree' in c_low or 'heap' in c_low or 'stack' in c_low or 'queue' in c_low or 'hash' in c_low or 'data structure' in c_low:
                            mapped = 'Data Structures'
                        elif 'c prog' in c_low or 'pointer' in c_low or 'recursion' in c_low:
                            mapped = 'C Programming'
                        elif 'toc' in c_low or 'automata' in c_low or 'turing' in c_low or 'computation' in c_low or 'cfl' in c_low:
                            mapped = 'Theory of Computation (TOC)'
                        elif 'compiler' in c_low or 'parsing' in c_low or 'grammar' in c_low or 'syntax' in c_low:
                            mapped = 'Compiler Design'
                        elif 'os' in c_low or 'operating' in c_low or 'paging' in c_low or 'deadlock' in c_low or 'process' in c_low or 'semaphore' in c_low:
                            mapped = 'Operating Systems'
                        elif 'dbms' in c_low or 'database' in c_low or 'sql' in c_low or 'relational' in c_low or 'transaction' in c_low:
                            mapped = 'Databases (DBMS)'
                        elif 'network' in c_low or 'tcp' in c_low or 'ip' in c_low or 'routing' in c_low or 'subnet' in c_low:
                            mapped = 'Computer Networks'
                        elif 'coa' in c_low or 'architecture' in c_low or 'cache' in c_low or 'pipeline' in c_low or 'instruction' in c_low:
                            mapped = 'Computer Organization (COA)'
                        elif 'digital' in c_low or 'boolean' in c_low or 'k map' in c_low or 'counter' in c_low or 'flip' in c_low:
                            mapped = 'Digital Logic'
                        elif 'discrete' in c_low or 'graph' in c_low or 'combinat' in c_low or 'logic' in c_low or 'set' in c_low:
                            mapped = 'Discrete Mathematics'
                        elif 'calculus' in c_low or 'linear algebra' in c_low or 'matrix' in c_low or 'eigen' in c_low:
                            mapped = 'Engineering Mathematics'
                        elif 'prob' in c_low or 'stat' in c_low or 'bayes' in c_low or 'random' in c_low:
                            mapped = 'Probability & Statistics'
                        else:
                            mapped = 'Algorithms'
                            
                        if mapped in tech_1m:
                            if marks <= 1.0:
                                tech_1m[mapped].append(q_item)
                            else:
                                tech_2m[mapped].append(q_item)
        except Exception as e:
            pass
            
    print(f"Loaded: Aptitude 1M={len(aptitude_1m)}, Aptitude 2M={len(aptitude_2m)}")
    for s in tech_1m:
        print(f"  {s}: 1M={len(tech_1m[s])}, 2M={len(tech_2m[s])}")
        
    return aptitude_1m, aptitude_2m, tech_1m, tech_2m

def generate_80_mock_tests():
    aptitude_1m, aptitude_2m, tech_1m, tech_2m = load_and_categorize_questions()
    
    # 25 1-Mark Technical distribution across subjects
    tech_1m_dist = {
        'Algorithms': 2,
        'Data Structures': 2,
        'C Programming': 2,
        'Theory of Computation (TOC)': 2,
        'Compiler Design': 2,
        'Operating Systems': 2,
        'Databases (DBMS)': 2,
        'Computer Networks': 2,
        'Computer Organization (COA)': 2,
        'Digital Logic': 2,
        'Discrete Mathematics': 3,
        'Engineering Mathematics': 1,
        'Probability & Statistics': 1
    } # sum = 25
    
    # 30 2-Mark Technical distribution across subjects
    tech_2m_dist = {
        'Algorithms': 3,
        'Data Structures': 2,
        'C Programming': 2,
        'Theory of Computation (TOC)': 3,
        'Compiler Design': 2,
        'Operating Systems': 3,
        'Databases (DBMS)': 3,
        'Computer Networks': 3,
        'Computer Organization (COA)': 3,
        'Digital Logic': 2,
        'Discrete Mathematics': 3,
        'Engineering Mathematics': 1,
        'Probability & Statistics': 2
    } # sum = 30
    
    print("\nStarting generation of 80 full mock tests...")
    manifest_new_entries = []
    
    for test_idx in range(1, 81):
        rng = random.Random(202700 + test_idx)
        test_id = f"GATE2027_Mock_{test_idx:02d}"
        file_name = f"{test_id}.json"
        title = f"GATE 2027 | Full-Length All India Mock Test {test_idx}"
        
        # 1. Section 1: Aptitude (10 Qs = 15 Marks)
        # Q1-Q5: 1M
        apt_1_sample = rng.sample(aptitude_1m, 5) if len(aptitude_1m) >= 5 else [rng.choice(aptitude_1m) for _ in range(5)]
        # Q6-Q10: 2M
        apt_2_sample = rng.sample(aptitude_2m, 5) if len(aptitude_2m) >= 5 else [rng.choice(aptitude_2m) for _ in range(5)]
        
        # 2. Section 2: Technical (55 Qs = 85 Marks)
        # Q11-Q35: 25 1-Mark questions
        tech_1_sample = []
        for subj, count in tech_1m_dist.items():
            pool = tech_1m.get(subj, [])
            if not pool:
                pool = tech_1m['Algorithms']
            sampled = rng.sample(pool, count) if len(pool) >= count else [rng.choice(pool) for _ in range(count)]
            tech_1_sample.extend(sampled)
            
        # Shuffle 1M technical questions so subjects interleave naturally
        rng.shuffle(tech_1_sample)
        tech_1_sample = tech_1_sample[:25]
        
        # Q36-Q65: 30 2-Mark questions
        tech_2_sample = []
        for subj, count in tech_2m_dist.items():
            pool = tech_2m.get(subj, [])
            if not pool:
                pool = tech_2m['Algorithms']
            sampled = rng.sample(pool, count) if len(pool) >= count else [rng.choice(pool) for _ in range(count)]
            tech_2_sample.extend(sampled)
            
        rng.shuffle(tech_2_sample)
        tech_2_sample = tech_2_sample[:30]
        
        # Build full 65 questions list
        final_questions = []
        q_counter = 1
        
        # Q1 to Q5: Aptitude 1M
        for q in apt_1_sample:
            q_copy = dict(q)
            q_copy['index'] = q_counter - 1
            q_copy['qNum'] = f"Q #{q_counter}"
            q_copy['displayNum'] = q_counter
            q_copy['section'] = "Aptitude"
            q_copy['marks'] = 1.0
            q_copy['penalty'] = 0.33 if q_copy.get('type') == 'MCQ' else 0.0
            final_questions.append(q_copy)
            q_counter += 1
            
        # Q6 to Q10: Aptitude 2M
        for q in apt_2_sample:
            q_copy = dict(q)
            q_copy['index'] = q_counter - 1
            q_copy['qNum'] = f"Q #{q_counter}"
            q_copy['displayNum'] = q_counter
            q_copy['section'] = "Aptitude"
            q_copy['marks'] = 2.0
            q_copy['penalty'] = 0.67 if q_copy.get('type') == 'MCQ' else 0.0
            final_questions.append(q_copy)
            q_counter += 1
            
        # Q11 to Q35: Technical 1M
        for q in tech_1_sample:
            q_copy = dict(q)
            q_copy['index'] = q_counter - 1
            q_copy['qNum'] = f"Q #{q_counter}"
            q_copy['displayNum'] = q_counter
            q_copy['section'] = "Technical"
            q_copy['marks'] = 1.0
            q_copy['penalty'] = 0.33 if q_copy.get('type') == 'MCQ' else 0.0
            final_questions.append(q_copy)
            q_counter += 1
            
        # Q36 to Q65: Technical 2M
        for q in tech_2_sample:
            q_copy = dict(q)
            q_copy['index'] = q_counter - 1
            q_copy['qNum'] = f"Q #{q_counter}"
            q_copy['displayNum'] = q_counter
            q_copy['section'] = "Technical"
            q_copy['marks'] = 2.0
            q_copy['penalty'] = 0.67 if q_copy.get('type') == 'MCQ' else 0.0
            final_questions.append(q_copy)
            q_counter += 1
            
        assert len(final_questions) == 65, f"Expected 65 questions, got {len(final_questions)}"
        total_marks = int(sum(q['marks'] for q in final_questions))
        assert total_marks == 100, f"Expected 100 marks, got {total_marks}"
        
        test_payload = {
            "id": test_id,
            "fileName": file_name,
            "title": title,
            "subject": "Full Mock Test (MT)",
            "testType": "Full Mock Test",
            "series": "GATE 2027 Generated Mock Series",
            "durationMinutes": 180,
            "totalQuestions": 65,
            "totalMarks": 100,
            "sections": ["Aptitude", "Technical"],
            "questions": final_questions
        }
        
        # Save JSON
        file_path = os.path.join(TESTS_DIR, file_name)
        with open(file_path, 'w', encoding='utf-8') as out_f:
            json.dump(test_payload, out_f, ensure_ascii=False, indent=2)
            
        manifest_new_entries.append({
            "id": test_id,
            "fileName": file_name,
            "title": title,
            "subject": "Full Mock Test (MT)",
            "testType": "Full Mock Test",
            "series": "GATE 2027 Generated Mock Series",
            "durationMinutes": 180,
            "totalQuestions": 65,
            "totalMarks": 100,
            "sections": ["Aptitude", "Technical"]
        })
        
    print(f"Generated all 80 full mock tests (each with 65 questions, 100 marks)!")
    
    # Update manifest
    manifest = []
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as fp:
            manifest = json.load(fp)
            
    # Remove any existing entries for GATE 2027 Generated Mock Series
    manifest = [m for m in manifest if m.get('series') != 'GATE 2027 Generated Mock Series']
    
    # Prepend the 80 mocks so they appear right at the top
    manifest = manifest_new_entries + manifest
    
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=2)
        
    print(f"Updated manifest at {MANIFEST_PATH}. Total tests in library: {len(manifest)}")

if __name__ == '__main__':
    generate_80_mock_tests()
