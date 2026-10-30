import os
import glob
import re
import json
from bs4 import BeautifulSoup

def categorize_test(filename, title):
    f_lower = filename.lower()
    t_lower = title.lower()
    
    subject = 'General Computer Science'
    if 'aimt' in f_lower or 'all india mock' in t_lower:
        subject = 'All India Mock Test (AIMT)'
    elif re.match(r'mt\d+', f_lower) or 'mock test' in t_lower:
        subject = 'Full Mock Test (MT)'
    elif 'algo' in f_lower:
        subject = 'Algorithms'
    elif 'dsa' in f_lower or 'ds' in f_lower or 'data structure' in t_lower:
        subject = 'Data Structures'
    elif 'dbms' in f_lower or 'database' in f_lower:
        subject = 'Databases (DBMS)'
    elif 'os' in f_lower or 'operating system' in t_lower:
        subject = 'Operating Systems'
    elif 'toc' in f_lower or 'theory of computation' in t_lower or 'tpct5' in f_lower:
        subject = 'Theory of Computation (TOC)'
    elif 'cd' in f_lower or 'compiler' in t_lower:
        subject = 'Compiler Design'
    elif 'cn' in f_lower or 'network' in t_lower:
        subject = 'Computer Networks'
    elif 'coa' in f_lower or 'architecture' in t_lower:
        subject = 'Computer Organization (COA)'
    elif 'dl' in f_lower or 'digital' in t_lower:
        subject = 'Digital Logic'
    elif 'dm' in f_lower or 'discrete' in t_lower:
        subject = 'Discrete Mathematics'
    elif 'em' in f_lower or 'engineering math' in t_lower:
        subject = 'Engineering Mathematics'
    elif 'programming' in f_lower or 'cprogramming' in f_lower:
        subject = 'C Programming'
    elif 'calculus' in f_lower:
        subject = 'Calculus & Optimization'
    elif 'probal' in f_lower or 'prob' in f_lower or 'stats' in f_lower:
        subject = 'Probability & Statistics'
    elif 'mixed' in f_lower or 'mised' in f_lower:
        subject = 'Mixed Subjects'

    # Test Type detection
    ttype = 'Topic Test'
    if 'mock' in subject.lower() or 'aimt' in f_lower or re.match(r'mt\d+', f_lower):
        ttype = 'Full Mock Test'
    elif 'subject wise' in t_lower or 'st' in f_lower or 'sst' in f_lower or 's1' in f_lower or 'st1' in f_lower:
        ttype = 'Subject Test'
    elif 'mixed' in f_lower or 'mised' in f_lower:
        ttype = 'Mixed Test'
    
    return subject, ttype

def extract_test(file_path):
    filename = os.path.basename(file_path)
    test_id = os.path.splitext(filename)[0].replace(' ', '_')
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')
    
    # Title
    t_el = soup.find('div', class_='exam_name')
    title = t_el.get_text(strip=True) if t_el else filename
    if title.startswith('Exam Summary ('):
        title = title[len('Exam Summary ('):].rstrip(')')
    
    subject, ttype = categorize_test(filename, title)
    
    # Duration
    duration_mins = 45
    dur_el = soup.find('div', class_='exam_duration')
    if dur_el:
        min_span = dur_el.find('span', class_='exam_min_duration')
        if min_span:
            m = re.search(r'(\d+)', min_span.get_text(strip=True))
            if m:
                duration_mins = int(m.group(1))
    else:
        # Default by type
        if ttype == 'Full Mock Test': duration_mins = 180
        elif ttype == 'Subject Test': duration_mins = 90
        else: duration_mins = 45

    # Total Marks
    total_marks = 0
    tm_el = soup.find('div', class_='exam_total_marks')
    if tm_el:
        num_item = tm_el.find('span', class_='exam_num_item')
        if num_item:
            m = re.search(r'(\d+)', num_item.get_text(strip=True))
            if m: total_marks = int(m.group(1))

    # Sections and Questions
    questions = []
    sections_found = set()
    
    res_sections = soup.find_all('div', class_='res_section')
    if not res_sections:
        res_sections = [soup]
        
    global_q_index = 0
    for sec in res_sections:
        sec_h2 = sec.find('h2')
        sec_name = sec_h2.get_text(strip=True) if sec_h2 else 'Technical'
        sections_found.add(sec_name)
        
        for q in sec.find_all('div', class_='res_question'):
            global_q_index += 1
            meta_spans = q.find_all('span', class_='res_qs_top_meta1')
            q_num_txt = f"Q #{global_q_index}"
            q_type_raw = 'Multiple Choice Type'
            marks = 1.0
            penalty = 0.0
            cat = ''
            
            for s in meta_spans:
                cls = s.get('class', [])
                txt = s.get_text(strip=True)
                if 'res_qs_num' in cls:
                    q_num_txt = txt
                elif 'res_qs_type' in cls:
                    q_type_raw = txt
                elif 'res_qs_marks' in cls:
                    m = re.search(r'([\d\.]+)', txt)
                    if m: marks = float(m.group(1))
                elif 'res_qs_penalty' in cls:
                    m = re.search(r'([\d\.]+)', txt)
                    if m: penalty = float(m.group(1))
                elif 'res_qs_category' in cls:
                    cat = txt
                    
            # Normalize q_type
            q_type = 'MCQ'
            if 'Select' in q_type_raw:
                q_type = 'MSQ'
            elif 'Numerical' in q_type_raw:
                q_type = 'NAT'
                
            # If penalty is 0 for MCQ, set standard GATE negative marks
            if q_type == 'MCQ' and penalty == 0:
                penalty = round(marks / 3.0, 2)
            if q_type in ('MSQ', 'NAT'):
                penalty = 0.0 # GATE has no negative marks for MSQ and NAT
                
            # Correct Answer
            corr_span = q.find('span', class_='correct_solution')
            corr_ans = ''
            if corr_span:
                corr_ans = corr_span.get_text(strip=True).replace('Correct Answer:', '').strip()
                
            # Discussion URL
            disc_span = q.find('span', class_='res_discuss')
            disc_url = ''
            if disc_span and disc_span.find('a'):
                disc_url = disc_span.find('a').get('href', '').strip()
            
            # Question Text and Options extraction
            q_text_div = q.find('div', class_='res_question_text')
            options = []
            
            if q_text_div:
                # Find options ol (not inside pre)
                all_ols = q_text_div.find_all('ol')
                option_lists = [
                    candidate_ol for candidate_ol in all_ols
                    if candidate_ol.find_parent('pre') is None
                    and len(candidate_ol.find_all('li', recursive=False)) >= 2
                ]
                # Source question bodies may contain one-item ordered lists as part
                # of the prompt. The answer choices are the last multi-item list.
                opt_ol = option_lists[-1] if option_lists else None
                        
                if opt_ol:
                    lis = opt_ol.find_all('li', recursive=False)
                    for idx, li in enumerate(lis):
                        opt_id = chr(65 + idx) # A, B, C, D...
                        options.append({
                            'id': opt_id,
                            'textHtml': str(li)
                        })
                    opt_ol.decompose()
                # Do not invent selectable options when the source has none.
                # The client reports incomplete choice data and keeps the item ungradable.
                
                # Question HTML
                q_html = str(q_text_div)
            else:
                q_html = "<p>Question text unavailable.</p>"
                
            questions.append({
                'index': global_q_index - 1,
                'qNum': q_num_txt,
                'displayNum': global_q_index,
                'section': sec_name,
                'type': q_type,
                'typeRaw': q_type_raw,
                'marks': marks,
                'penalty': penalty,
                'category': cat or subject,
                'questionHtml': q_html,
                'options': options,
                'correctAnswer': corr_ans,
                'discussUrl': disc_url
            })
            
    # Calculate total marks if missing
    if total_marks == 0 and questions:
        total_marks = int(sum(q['marks'] for q in questions))
        
    test_data = {
        'id': test_id,
        'fileName': filename,
        'title': title,
        'subject': subject,
        'testType': ttype,
        'durationMinutes': duration_mins,
        'totalQuestions': len(questions),
        'totalMarks': total_marks,
        'sections': list(sections_found) if sections_found else ['Technical'],
        'questions': questions
    }
    
    return test_data

def main():
    html_files = sorted(glob.glob('*.html'))
    # Filter out any generated html files
    html_files = [f for f in html_files if not f.startswith('exam_') and f != 'index.html']
    print(f"Found {len(html_files)} tests to process.")
    
    os.makedirs('data/tests', exist_ok=True)
    manifest = []
    
    for idx, f in enumerate(html_files):
        try:
            test_data = extract_test(f)
            test_id = test_data['id']
            
            # Save individual test JSON
            test_file_path = os.path.join('data', 'tests', f"{test_id}.json")
            with open(test_file_path, 'w', encoding='utf-8') as out_fp:
                json.dump(test_data, out_fp, ensure_ascii=False)
                
            # Add to manifest (lightweight summary)
            manifest.append({
                'id': test_data['id'],
                'fileName': test_data['fileName'],
                'title': test_data['title'],
                'subject': test_data['subject'],
                'testType': test_data['testType'],
                'durationMinutes': test_data['durationMinutes'],
                'totalQuestions': test_data['totalQuestions'],
                'totalMarks': test_data['totalMarks'],
                'sections': test_data['sections']
            })
            
            if (idx + 1) % 10 == 0 or idx == len(html_files) - 1:
                print(f"Processed {idx + 1}/{len(html_files)} tests...")
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    manifest_path = os.path.join('data', 'exam_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as out_fp:
        json.dump(manifest, out_fp, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated manifest with {len(manifest)} tests at {manifest_path}")

if __name__ == '__main__':
    main()
