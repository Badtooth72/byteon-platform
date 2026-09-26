"""Validated response formats shared by printed and online assessments."""
import re
from decimal import Decimal, InvalidOperation

TYPES = {
    'short_value': 'Single word or value', 'word_bank': 'Fill the blanks from a word bank',
    'binary_math': 'Binary addition or shift', 'single_choice': 'Tick one answer',
    'multiple_choice': 'Tick one or more answers', 'matching': 'Matching pairs',
    'prose': 'Short prose answer', 'algorithm': 'Algorithm — Section A, flexible syntax',
    'python': 'Python — Section B, formal syntax', 'essay': 'Extended / essay response',
    'table': 'Complete an existing table',
}


def lines(value, maximum=30):
    items = [item.strip() for item in value.splitlines() if item.strip()]
    if len(items)>maximum or any(len(item)>300 for item in items):
        raise ValueError('Too many items or an item is too long')
    return items


def parse_format(form, question):
    kind=form.get('response_type','prose')
    if kind not in TYPES: raise ValueError('Unknown question type')
    if kind in {'algorithm','python'} and question.get('component')=='J277/01':
        raise ValueError('Section A/B coding formats belong to Paper 2. Choose a Paper 2 question.')
    spec={'version':1,'type':kind}
    marking={}
    if kind=='short_value':
        accepted=lines(form.get('accepted',''))
        if not accepted: raise ValueError('Provide at least one accepted answer')
        marking['accepted']=accepted
    elif kind=='word_bank':
        choices=lines(form.get('choices',''))
        accepted=lines(form.get('blank_answers',''))
        numbers=[int(n) for n in re.findall(r'\[\[(\d+)\]\]',question.get('question_text',''))]
        if not choices or not accepted or sorted(numbers)!=list(range(1,len(accepted)+1)):
            raise ValueError('Use [[1]], [[2]], etc. exactly once in the question text, and enter one answer per blank')
        if any(answer not in choices for answer in accepted): raise ValueError('Every blank answer must be in the word bank')
        spec.update(choices=choices,blank_count=len(accepted))
        marking['answers']=accepted
    elif kind in {'single_choice','multiple_choice'}:
        choices=lines(form.get('choices',''))
        try: correct=sorted(set(int(n.strip())-1 for n in form.get('correct_choices','').split(',') if n.strip()))
        except ValueError: raise ValueError('Enter correct option numbers separated by commas')
        if not 2<=len(choices)<=20 or not correct or any(n<0 or n>=len(choices) for n in correct):
            raise ValueError('Provide 2–20 options and valid correct option numbers')
        if kind=='single_choice' and len(correct)!=1: raise ValueError('Tick-one questions need exactly one correct option')
        spec['choices']=choices
        marking['correct']=correct
    elif kind=='matching':
        pairs=lines(form.get('pairs',''),20)
        if len(pairs)<2 or any('|' not in pair for pair in pairs): raise ValueError('Enter at least two pairs as left item | matching right item')
        left,right=zip(*(pair.split('|',1) for pair in pairs))
        left=[s.strip() for s in left];right=[s.strip() for s in right]
        if not all(left+right) or len(set(right))!=len(right): raise ValueError('Matching items must be non-empty, and right items unique')
        spec.update(left=left,right=right)
        marking['matches']=list(range(len(left)))
    elif kind=='binary_math':
        operation=form.get('operation','add');a=form.get('operand_a','').strip();b=form.get('operand_b','').strip()
        if operation not in {'add','shift_left','shift_right'} or not re.fullmatch('[01]{1,16}',a): raise ValueError('Enter a binary operand of 1–16 bits')
        try: width=int(form.get('width','8'));shift=int(form.get('shift','1'))
        except ValueError: raise ValueError('Width and shift must be whole numbers')
        if not len(a)<=width<=16 or not 1<=shift<=16: raise ValueError('Width must hold the operand (up to 16 bits); shift must be 1–16')
        if operation=='add':
            if not re.fullmatch('[01]{1,16}',b) or len(b)>width: raise ValueError('Enter a second binary operand that fits the width')
            expected=bin(int(a,2)+int(b,2))[2:].zfill(width)
        else:
            value=int(a,2)<<shift if operation=='shift_left' else int(a,2)>>shift
            expected=format(value & ((1<<width)-1),'0'+str(width)+'b')
        spec.update(operation=operation,operand_a=a.zfill(width),operand_b=b.zfill(width) if operation=='add' else '',width=width,shift=shift)
        marking['accepted']=[expected]
    elif kind=='table':
        tables=question.get('question_tables') or []
        if not tables: raise ValueError('This question has no structured table yet')
        marking['table_answers']={}
        keys={cell['answer_key'] for table in tables for row in table['rows'] for cell in row if isinstance(cell,dict) and 'answer_key' in cell}
        for item in lines(form.get('table_answers','')):
            if '=' not in item: raise ValueError('Enter table answers as answer_key = expected answer')
            key,value=(s.strip() for s in item.split('=',1))
            if key not in keys or not value: raise ValueError('Unknown table answer key or empty answer')
            marking['table_answers'][key]=value
    else:
        try: length=int(form.get('answer_lines','12' if kind in {'essay','algorithm','python'} else '4'))
        except ValueError: raise ValueError('Answer space must be a whole number')
        if not 1<=length<=40: raise ValueError('Choose 1–40 answer lines')
        spec['answer_lines']=length
        if kind=='algorithm': spec.update(language='Any structured language or pseudocode',syntax_policy='lenient')
        if kind=='python': spec.update(language='Python',syntax_policy='formal_with_minor_leeway')
        if kind in {'algorithm','python'}:
            starter=form.get('starter_code','')
            if len(starter)>8000: raise ValueError('Starter code is too long')
            spec['starter_code']=starter
            spec['section']='A' if kind=='algorithm' else 'B'
    return spec,marking


def public_question(question):
    return {key:question.get(key) for key in ('question_id','label','question_text','marks','topic_codes','subtopic','question_tables','response_spec','component','ao_marks','ao_review_status','requires_source_visual','format_review_status')}


def prompt_parts(question):
    parts=re.split(r'(\[\[\d+\]\])',question.get('question_text') or '')
    return [{'blank':int(part[2:-2])-1} if re.fullmatch(r'\[\[\d+\]\]',part) else {'text':part} for part in parts]


def normal(value):
    return ' '.join(str(value).casefold().split())


def clean_answer(question,answer):
    if not isinstance(answer,dict): raise ValueError('Invalid answer')
    spec=question.get('response_spec') or {'type':'prose'};kind=spec['type'];result={}
    if kind in {'short_value','binary_math','prose','essay','algorithm','python'}:
        value=answer.get('value','');working=answer.get('working','')
        if not isinstance(value,str) or len(value)>16000 or not isinstance(working,str) or len(working)>8000: raise ValueError('Answer too long')
        result.update(value=value,working=working)
    elif kind in {'single_choice','multiple_choice'}:
        choices=answer.get('choices',[])
        if not isinstance(choices,list) or len(choices)>len(spec['choices']) or any(type(n)!=int or n<0 or n>=len(spec['choices']) for n in choices): raise ValueError('Invalid choice')
        if kind=='single_choice' and len(choices)>1: raise ValueError('Choose one option')
        result['choices']=sorted(set(choices))
    elif kind=='word_bank':
        blanks=answer.get('blanks',[])
        if not isinstance(blanks,list) or len(blanks)!=spec['blank_count'] or any(v not in spec['choices']+[''] for v in blanks): raise ValueError('Invalid blank answer')
        result['blanks']=blanks
    elif kind=='matching':
        matches=answer.get('matches',[])
        if not isinstance(matches,list) or len(matches)!=len(spec['left']) or any(type(n)!=int or n<-1 or n>=len(spec['right']) for n in matches): raise ValueError('Invalid match')
        result['matches']=matches
    elif kind=='table':
        values=answer.get('table',{})
        if not isinstance(values,dict) or len(values)>100 or any(not isinstance(k,str) or not isinstance(v,str) or len(v)>500 for k,v in values.items()): raise ValueError('Invalid table answer')
        allowed=set()
        for table in question.get('question_tables',[]):
            for row in table['rows']:
                for cell in row:
                    if isinstance(cell,dict):
                        if 'answer_key' in cell: allowed.add(cell['answer_key'])
                        if 'choice_group' in cell: allowed.add(cell['choice_group'])
        if set(values)-allowed: raise ValueError('Unknown table field')
        result['table']=values
    return result


def grade_objective(question,answer):
    spec=question['response_spec'];marking=question.get('marking_spec') or {};kind=spec['type'];fraction=None
    if kind in {'short_value','binary_math'}:
        fraction=int(normal(answer.get('value','')) in {normal(v) for v in marking.get('accepted',[])})
        if kind=='binary_math': fraction=int(re.sub(r'\s','',answer.get('value','')) in marking.get('accepted',[]))
    elif kind in {'single_choice','multiple_choice'}:
        fraction=int(answer.get('choices',[])==marking.get('correct'))
    elif kind=='word_bank':
        expected=marking['answers'];fraction=sum(normal(a)==normal(b) for a,b in zip(answer['blanks'],expected))/len(expected)
    elif kind=='matching':
        expected=marking['matches'];fraction=sum(a==b for a,b in zip(answer['matches'],expected))/len(expected)
    # Tables, prose and all code stay in the marking queue. Mathematical
    # working also needs a teacher check when the final answer is wrong.
    if kind=='binary_math' and fraction==0 and answer.get('working','').strip(): fraction=None
    return None if fraction is None else round(question['marks']*fraction,2)


def validate_mark(value,maximum):
    try: mark=Decimal(str(value))
    except InvalidOperation: raise ValueError('Enter a valid mark')
    if not mark.is_finite() or not 0<=mark<=maximum: raise ValueError('Mark must be between zero and the available marks')
    return float(mark)
