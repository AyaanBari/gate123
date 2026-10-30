import os
import re
import sys
import json
import glob
from pypdf import PdfReader

BASE_DIR = r"d:\Gift\Gift"
TESTS_DIR = os.path.join(BASE_DIR, "data", "tests")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "exam_manifest.json")

# Map volume chapter to standard subject name
SUBJECT_MAPPING = {
    # Volume 1
    "Discrete Mathematics: Combinatory": "Discrete Mathematics",
    "Discrete Mathematics: Graph Theory": "Discrete Mathematics",
    "Discrete Mathematics: Mathematical Logic": "Discrete Mathematics",
    "Discrete Mathematics: Set Theory & Algebra": "Discrete Mathematics",
    "Engineering Mathematics: Calculus": "Engineering Mathematics",
    "Engineering Mathematics: Linear Algebra": "Engineering Mathematics",
    "Engineering Mathematics: Probability": "Probability & Statistics",
    "General Aptitude: Analytical Aptitude": "General Aptitude",
    "General Aptitude: Quantitative Aptitude": "General Aptitude",
    
    # Volume 2
    "Algorithms": "Algorithms",
    "Compiler Design": "Compiler Design",
    "Programming and DS: Data Structures": "Data Structures",
    "Programming: Programming in C": "C Programming",
    "Theory of Computation": "Theory of Computation (TOC)",
    
    # Volume 3
    "CO & Architecture": "Computer Organization (COA)",
    "Computer Networks": "Computer Networks",
    "Databases": "Databases (DBMS)",
    "Digital Logic": "Digital Logic",
    "Operating System": "Operating Systems"
}

def extract_answer_keys(reader):
    """Extract all answer keys across all answer pages in the reader."""
    answers = {}
    total_pages = len(reader.pages)
    
    in_answer_block = False
    
    for p_idx in range(total_pages):
        text = reader.pages[p_idx].extract_text() or ''
        
        if 'Answer Keys' in text:
            in_answer_block = True
            text_part = text.split('Answer Keys')[-1]
        elif in_answer_block:
            # Check if this page is still an answer key page
            # An answer key page contains mostly lines of numbers like X.Y.Z followed by answer
            matches = re.findall(r'(\d+\.\d+\.\d+)\s*\n([^\n]+)', text)
            if len(matches) > 10:
                text_part = text
            else:
                in_answer_block = False
                continue
        else:
            continue
            
        matches = re.findall(r'(\d+\.\d+\.\d+)\s*\n([^\n]+)', text_part)
        for q_id, ans in matches:
            ans_clean = ans.strip()
            # If answer is 'N/A' or descriptive or placeholder
            answers[q_id] = ans_clean
            
    return answers

def clean_question_body(raw_body):
    """Clean question body by stripping tags and extraneous text."""
    lines = raw_body.split('\n')
    cleaned_lines = []
    
    skip = False
    for line in lines:
        s = line.strip()
        # Skip tags lines
        if re.match(r'^(gate(?:cse|it|\d+)[^\n]*|combinatory|one-mark|two-marks|normal|numerical-answers|msq|mcq|Answer key.*|☟.*|\s*)+$', s, re.I):
            continue
        if s == 'Answer key' or s == '☟':
            continue
        cleaned_lines.append(s)
        
    cleaned_text = '\n'.join(cleaned_lines).strip()
    return cleaned_text

def format_question_html(body_text, header_title):
    """Format body text into clean HTML."""
    paragraphs = [p.strip() for p in body_text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [body_text]
        
    html_parts = [f'<div class="res_question_text"><div class="q-source-tag"><strong>{header_title}</strong></div>']
    for p in paragraphs:
        p_html = p.replace('\n', '<br/>')
        html_parts.append(f'<p>{p_html}</p>')
    html_parts.append('</div>')
    return ''.join(html_parts)

def parse_volume(pdf_filename, default_vol_title):
    pdf_path = os.path.join(BASE_DIR, pdf_filename)
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return []
        
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"\nProcessing {pdf_filename} ({total_pages} pages)...")
    
    # 1. Extract all answer keys
    answers = extract_answer_keys(reader)
    print(f"Extracted {len(answers)} answer keys from {pdf_filename}")
    
    # 2. Extract questions page by page
    questions = []
    
    for p_idx in range(total_pages):
        page = reader.pages[p_idx]
        text = page.extract_text() or ''
        
        # Skip pure TOC or pure Answer Key pages
        if 'Table of Contents' in text and p_idx < 15:
            continue
            
        # Find all question headers on this page
        # e.g. "Balls In Bins: GATE CSE 2000 | Question: 5"
        pattern = re.compile(r'(?m)^([A-Za-z0-9 &,/ -]+:\s*GATE\s+(?:CSE|IT|DA|CS)[^\n]+)')
        matches = list(pattern.finditer(text))
        if not matches:
            continue
            
        # Extract page annotation URLs
        urls = []
        for a in page.get('/Annots', []):
            try:
                obj = a.get_object()
                action = obj.get('/A')
                if action and hasattr(action, 'get'):
                    uri = action.get('/URI')
                    if uri and 'gateoverflow.in/' in str(uri) and not '/tag/' in str(uri):
                        u_str = str(uri)
                        if u_str not in urls:
                            urls.append(u_str)
            except Exception:
                pass
                
        # Extract question IDs on this page (e.g. 1.1.2)
        q_ids = re.findall(r'(?m)^(\d+\.\d+\.\d+)$', text)
        
        for idx, m in enumerate(matches):
            start = m.start()
            end = matches[idx+1].start() if idx + 1 < len(matches) else len(text)
            chunk = text[start:end]
            header = m.group(1).strip()
            
            # Map Q ID if count matches or by index
            q_id = q_ids[idx] if idx < len(q_ids) else None
            
            # Extract category/topic from header
            topic = header.split(':')[0].strip()
            
            # Body text
            raw_body = chunk[len(header):].strip()
            body_text = clean_question_body(raw_body)
            
            # Determine marks
            marks = 1.0
            if 'two-marks' in chunk.lower() or 'two marks' in chunk.lower():
                marks = 2.0
            elif 'one-mark' in chunk.lower() or 'one mark' in chunk.lower():
                marks = 1.0
                
            # Determine question type
            # Check answer from answer keys
            correct_ans = answers.get(q_id, '') if q_id else ''
            
            is_nat = False
            is_msq = False
            
            if 'numerical-answers' in chunk.lower() or 'numerical' in chunk.lower():
                is_nat = True
            elif ';' in correct_ans:
                is_msq = True
            elif correct_ans and re.match(r'^-?\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)?$', correct_ans):
                is_nat = True
                
            q_type = "NAT" if is_nat else ("MSQ" if is_msq else "MCQ")
            penalty = round(marks / 3.0, 2) if q_type == "MCQ" else 0.0
            
            # Match GateOverflow URL
            discuss_url = ""
            for u in urls:
                # check if question number or year is in url
                digits = re.findall(r'\d+', header)
                if any(d in u for d in digits):
                    discuss_url = u
                    break
            if not discuss_url and urls:
                discuss_url = urls[min(idx, len(urls)-1)]
                
            # This text-only PDF parser cannot reliably recover answer choices.
            # Keep the options and answer key empty rather than fabricating them.
            options = []
            if correct_ans == 'N/A':
                correct_ans = ''
                
            q_html = format_question_html(body_text, header)
            
            questions.append({
                'header': header,
                'topic': topic,
                'bodyText': body_text,
                'questionHtml': q_html,
                'options': options,
                'type': q_type,
                'typeRaw': 'Numerical Answer Type' if is_nat else ('Multiple Select Question' if is_msq else 'Multiple Choice Type'),
                'marks': marks,
                'penalty': penalty,
                'correctAnswer': correct_ans,
                'discussUrl': discuss_url or 'https://gateoverflow.in',
                'qId': q_id,
                'vol': default_vol_title
            })
            
    print(f"Total parsed questions from {pdf_filename}: {len(questions)}")
    return questions

def map_question_subject(q):
    """Map question to standard subject name based on volume and chapter number X.Y.Z."""
    vol = q.get('vol', '')
    q_id = q.get('qId') or ''
    ch_num = q_id.split('.')[0] if '.' in q_id else ''
    
    if vol == 'Volume 1':
        v1_ch = {
            '1': 'Discrete Mathematics',
            '2': 'Discrete Mathematics',
            '3': 'Discrete Mathematics',
            '4': 'Discrete Mathematics',
            '5': 'Engineering Mathematics',
            '6': 'Engineering Mathematics',
            '7': 'Probability & Statistics',
            '8': 'General Aptitude',
            '9': 'General Aptitude',
        }
        if ch_num in v1_ch:
            return v1_ch[ch_num]
        t = q['topic'].lower()
        if 'probability' in t or 'bayes' in t: return 'Probability & Statistics'
        if 'calculus' in t or 'linear' in t or 'eigen' in t: return 'Engineering Mathematics'
        if 'aptitude' in t or 'word' in t or 'passage' in t: return 'General Aptitude'
        return 'Discrete Mathematics'
        
    elif vol == 'Volume 2':
        v2_ch = {
            '1': 'Algorithms',
            '2': 'Compiler Design',
            '3': 'Data Structures',
            '4': 'C Programming',
            '5': 'C Programming',
            '6': 'Theory of Computation (TOC)',
        }
        if ch_num in v2_ch:
            return v2_ch[ch_num]
        t = q['topic'].lower()
        if 'compiler' in t or 'grammar' in t: return 'Compiler Design'
        if 'automata' in t or 'turing' in t: return 'Theory of Computation (TOC)'
        if 'tree' in t or 'heap' in t or 'stack' in t: return 'Data Structures'
        if 'c programming' in t or 'pointer' in t: return 'C Programming'
        return 'Algorithms'
        
    elif vol == 'Volume 3':
        v3_ch = {
            '1': 'Computer Organization (COA)',
            '2': 'Computer Networks',
            '3': 'Databases (DBMS)',
            '4': 'Digital Logic',
            '5': 'Operating Systems',
        }
        if ch_num in v3_ch:
            return v3_ch[ch_num]
        t = q['topic'].lower()
        if 'process' in t or 'deadlock' in t or 'memory management' in t: return 'Operating Systems'
        if 'network' in t or 'tcp' in t or 'ip' in t: return 'Computer Networks'
        if 'database' in t or 'sql' in t: return 'Databases (DBMS)'
        if 'cache' in t or 'pipeline' in t: return 'Computer Organization (COA)'
        return 'Digital Logic'
        
    return 'General Computer Science'

def build_tests():
    os.makedirs(TESTS_DIR, exist_ok=True)
    # Clean up old PYQ json files
    for old_file in glob.glob(os.path.join(TESTS_DIR, "PYQ_*.json")):
        try:
            os.remove(old_file)
        except Exception:
            pass
            
    # 1. Parse all 3 volumes
    all_qs = []
    all_qs.extend(parse_volume("filter1_volume1.pdf", "Volume 1"))
    all_qs.extend(parse_volume("filter1_volume2.pdf", "Volume 2"))
    all_qs.extend(parse_volume("filter1_volume3.pdf", "Volume 3"))
    
    print(f"\n=======================================================")
    print(f"TOTAL QUESTIONS EXTRACTED ACROSS 3 VOLUMES: {len(all_qs)}")
    print(f"=======================================================")
    
    # 2. Group questions by Subject
    by_subject = {}
    for q in all_qs:
        subj = map_question_subject(q)
        by_subject.setdefault(subj, []).append(q)
        
    for s, qs in by_subject.items():
        print(f"  - {s}: {len(qs)} questions")
        
    # 3. Create Subject-wise PYQ Tests
    pyq_manifest_entries = []
    
    for subj, q_list in by_subject.items():
        if len(q_list) == 0:
            continue
            
        # Clean id
        safe_id = "PYQ_" + re.sub(r'[^A-Za-z0-9]+', '_', subj).strip('_')
        test_filename = f"{safe_id}.json"
        
        # Limit to up to 65 representative questions for a full test, or create parts if large
        # For full comprehensive practice, let's create a curated high-impact test of 30 questions (90 mins)
        # and if > 60 questions, also create Advanced / Complete Part 2
        
        chunk_size = 40
        num_chunks = max(1, (len(q_list) + chunk_size - 1) // chunk_size)
        
        for chunk_idx in range(num_chunks):
            chunk_qs = q_list[chunk_idx * chunk_size : (chunk_idx + 1) * chunk_size]
            part_suffix = f" Part {chunk_idx+1}" if num_chunks > 1 else ""
            part_id = f"{safe_id}_P{chunk_idx+1}" if num_chunks > 1 else safe_id
            part_filename = f"{part_id}.json"
            
            # Format questions for test
            formatted_qs = []
            total_marks = 0
            for i, q in enumerate(chunk_qs):
                total_marks += q['marks']
                formatted_qs.append({
                    "index": i,
                    "qNum": f"Q #{i+1}",
                    "displayNum": i + 1,
                    "section": "Technical",
                    "type": q['type'],
                    "typeRaw": q['typeRaw'],
                    "marks": q['marks'],
                    "penalty": q['penalty'],
                    "category": q['topic'],
                    "questionHtml": q['questionHtml'],
                    "options": q['options'],
                    "correctAnswer": q['correctAnswer'],
                    "discussUrl": q['discussUrl']
                })
                
            duration = 90 if len(formatted_qs) >= 25 else 45
            
            test_data = {
                "id": part_id,
                "fileName": part_filename,
                "title": f"GATE Official PYQs | {subj}{part_suffix}",
                "subject": subj,
                "testType": "GATE PYQ Series",
                "series": "GATE PYQs",
                "durationMinutes": duration,
                "totalQuestions": len(formatted_qs),
                "totalMarks": int(total_marks),
                "sections": ["Technical"],
                "questions": formatted_qs
            }
            
            test_path = os.path.join(TESTS_DIR, part_filename)
            with open(test_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
                
            pyq_manifest_entries.append({
                "id": part_id,
                "fileName": part_filename,
                "title": test_data['title'],
                "subject": subj,
                "testType": "GATE PYQ Series",
                "series": "GATE PYQs",
                "durationMinutes": duration,
                "totalQuestions": len(formatted_qs),
                "totalMarks": int(total_marks),
                "sections": ["Technical"]
            })
            
    print(f"\nGenerated {len(pyq_manifest_entries)} GATE PYQ test papers!")
    
    # 4. Read existing manifest and merge
    existing_manifest = []
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            existing_manifest = json.load(f)
            
    # Tag existing tests as "GO Test Series"
    for item in existing_manifest:
        if 'series' not in item or not item['series']:
            item['series'] = 'GO Test Series'
            
    # Remove old PYQ items if any exist
    existing_manifest = [item for item in existing_manifest if item.get('series') != 'GATE PYQs']
    
    combined_manifest = existing_manifest + pyq_manifest_entries
    
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(combined_manifest, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully updated {MANIFEST_PATH}:")
    print(f"  - GO Classes Test Series: {len(existing_manifest)} tests")
    print(f"  - GATE PYQ Series: {len(pyq_manifest_entries)} tests")
    print(f"  - TOTAL COMBINED: {len(combined_manifest)} tests")

if __name__ == '__main__':
    build_tests()
