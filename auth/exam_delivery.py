"""Author response layouts, publish snapshots, and collect school-user answers."""
from datetime import datetime
from secrets import token_urlsafe
import json
from exam_formats import TYPES, parse_format, public_question, clean_answer, grade_objective, validate_mark, prompt_parts
from pymongo.errors import DuplicateKeyError


def register_exam_delivery(app,mongo,teacher,token,valid_form):
    from flask import request,session,render_template,redirect,url_for,jsonify
    from random import Random

    app.jinja_env.globals['exam_prompt_parts']=prompt_parts
    app.jinja_env.globals['response_types']=TYPES
    def right_order(question):
        items=list(enumerate((question.get('response_spec') or {}).get('right',[])))
        Random(question['question_id']).shuffle(items)
        if len(items)>1 and [index for index,_ in items]==list(range(len(items))): items=items[1:]+items[:1]
        return items
    app.jinja_env.globals['exam_matching_right']=right_order

    def draft_questions(test_id):
        draft=mongo.db.exam_test_drafts.find_one({'test_id':test_id,'created_by':session.get('username')})
        if not draft: return None,[]
        found={q['question_id']:q for q in mongo.db.exam_questions.find({'question_id':{'$in':draft['question_ids']}})}
        return draft,[found[qid] for qid in draft['question_ids'] if qid in found]

    @app.route('/exam-bank/new',methods=['GET','POST'])
    def exam_new_question():
        if not teacher(): return 'Access denied',403
        topics=list(mongo.db.exam_topics.find({}, {'_id':0}).sort('code',1))
        error=None
        if request.method=='POST':
            if not valid_form(): return 'Invalid form token',400
            title=request.form.get('title','').strip();text=request.form.get('question_text','').strip()
            component=request.form.get('component','J277/01');topic=request.form.get('topic','')
            try:
                marks=int(request.form.get('marks','1'))
                if not 1<=marks<=40 or not title or len(title)>200 or not text or len(text)>8000: raise ValueError('Provide a title, question text and 1–40 marks')
                if component not in {'J277/01','J277/02'} or topic not in {t['code'] for t in topics} or not topic.startswith('1.' if component=='J277/01' else '2.'):
                    raise ValueError('Choose a topic for the selected paper')
                qid='custom-'+token_urlsafe(12);paper_id='byteon-custom-'+component.replace('/','-')
                mongo.db.exam_papers.update_one({'paper_id':paper_id},{'$setOnInsert':{'paper_id':paper_id,'year':datetime.utcnow().year,'series':'Custom','component':component,'title':'Teacher-authored questions','awarding_body':'Byteon'}},upsert=True)
                mongo.db.exam_questions.insert_one({'question_id':qid,'paper_id':paper_id,'label':title,'summary':title,'question_text':text,'marks':marks,'topic_codes':[topic],'component':component,'year':datetime.utcnow().year,'series':'Custom','number':0,'subtopic':'','created_by':session['username'],'review_status':'draft','prompt_review_status':'draft_needs_source_check','requires_source_visual':False,'paper_pages':[],'mark_scheme_pages':[],'paper_page_text':{},'mark_scheme_page_text':{},'question_tables':[],'review_revision':0})
                return redirect(url_for('exam_question_format',question_id=qid))
            except ValueError as exc: error=str(exc)
        return render_template('exam_new.html',topics=topics,error=error,form_token=token())

    @app.route('/exam-bank/question/<question_id>/format',methods=['GET','POST'])
    def exam_question_format(question_id):
        if not teacher(): return 'Access denied',403
        question=mongo.db.exam_questions.find_one({'question_id':question_id})
        if not question: return 'Question not found',404
        error=None;saved=False
        if request.method=='POST':
            if not valid_form(): return 'Session expired. Reload the page.',400
            try:
                revision=question.get('review_revision',0)
                if request.form.get('revision')!=str(revision): raise ValueError('Question changed elsewhere. Reload before saving.')
                text=request.form.get('question_text','').strip();guidance=request.form.get('marking_guidance','').strip()
                if not text or len(text)>8000 or len(guidance)>12000: raise ValueError('Provide question text (up to 8000 characters) and guidance up to 12000 characters')
                proposed={**question,'question_text':text};spec,marking=parse_format(request.form,proposed)
                verified=request.form.get('verified')=='yes'
                if verified and not guidance: raise ValueError('Verified questions need marking guidance')
                status='teacher_verified' if verified else 'draft_needs_source_check'
                values={'question_text':text,'marking_guidance':guidance,'response_spec':spec,'marking_spec':marking,'format_review_status':status,'prompt_review_status':status,'marking_review_status':status,'review_revision':revision+1,'format_reviewed_by':session['username'],'format_reviewed_at':datetime.utcnow()}
                condition={'_id':question['_id'],'review_revision':revision} if revision else {'_id':question['_id'],'$or':[{'review_revision':0},{'review_revision':{'$exists':False}}]}
                if not mongo.db.exam_questions.update_one(condition,{'$set':values}).modified_count: raise ValueError('Question changed elsewhere. Reload before saving.')
                mongo.db.exam_review_history.insert_one({'question_id':question_id,'edited_by':session['username'],'edited_at':datetime.utcnow(),'previous':{k:question.get(k) for k in values},'updated':values})
                return redirect(url_for('exam_question_format',question_id=question_id,saved='1'))
            except ValueError as exc: error=str(exc)
        return render_template('exam_format.html',question=question,error=error,saved=request.args.get('saved'),form_token=token())

    @app.route('/exam-bank/tests/<test_id>/print')
    def exam_print_test(test_id):
        if not teacher(): return 'Access denied',403
        draft,questions=draft_questions(test_id)
        if not draft: return 'Test not found',404
        return render_template('exam_paper.html',title=draft['title'],questions=[public_question(q) for q in questions],total_marks=sum(q['marks'] for q in questions),mode='print',test_id=test_id)

    @app.route('/exam-bank/tests/<test_id>/publish',methods=['GET','POST'])
    def exam_publish_test(test_id):
        if not teacher(): return 'Access denied',403
        draft,questions=draft_questions(test_id)
        if not draft: return 'Test not found',404
        error=None
        existing=mongo.db.exam_online_tests.find_one({'test_id':test_id})
        problems=[]
        if len(questions)!=len(draft['question_ids']): problems.append('Some questions were removed from the bank.')
        for q in questions:
            if not q.get('question_text') or not q.get('response_spec') or q.get('format_review_status')!='teacher_verified': problems.append(f"{q['label']}: configure and verify the response format.")
            if q.get('requires_source_visual'): problems.append(f"{q['label']}: source diagram still required; cannot publish online yet.")
            if q.get('question_tables') and q.get('table_review_status')!='teacher_verified': problems.append(f"{q['label']}: verify its tables against the source first.")
        classes=sorted(v for v in mongo.db.users.distinct('class_name') if v)
        if request.method=='POST':
            if not valid_form(): return 'Invalid form token',400
            allowed=request.form.getlist('classes')
            if set(allowed)-set(classes): error='Unknown class'
            elif existing: error='This test is already published. Create a new draft to publish a changed version.'
            elif problems: error='Resolve the question checks before publishing.'
            else:
                snapshot=[{**public_question(q),'marking_spec':q.get('marking_spec',{}),'marking_guidance':q.get('marking_guidance',''),'format_review_status':q['format_review_status']} for q in questions]
                mongo.db.exam_online_tests.create_index('test_id',unique=True)
                mongo.db.exam_online_tests.insert_one({'test_id':test_id,'title':draft['title'],'created_by':session['username'],'published_at':datetime.utcnow(),'allowed_classes':allowed,'questions':snapshot,'total_marks':sum(q['marks'] for q in questions)})
                return redirect(url_for('exam_publish_test',test_id=test_id))
        return render_template('exam_publish.html',draft=draft,questions=questions,problems=problems,classes=classes,error=error,existing=existing,form_token=token())

    @app.route('/exam-bank/tests/<test_id>/mark-scheme')
    def exam_print_mark_scheme(test_id):
        if not teacher(): return 'Access denied',403
        draft,questions=draft_questions(test_id)
        if not draft: return 'Test not found',404
        return render_template('exam_mark_scheme.html',draft=draft,questions=questions)

    def accessible(test,user):
        return bool(test) and (test['created_by']==session.get('username') or not test.get('allowed_classes') or user.get('class_name') in test['allowed_classes'])

    @app.route('/exam-bank/online')
    def online_exam_list():
        if not session.get('username'): return redirect(url_for('login'))
        user=mongo.db.users.find_one({'username':session['username']}) or {}
        tests=[t for t in mongo.db.exam_online_tests.find({}, {'questions':0}).sort('published_at',-1) if accessible(t,user)]
        attempts={a['test_id']:a for a in mongo.db.exam_attempts.find({'username':session['username']},{'answers':0,'grades':0})}
        return render_template('exam_online_list.html',tests=tests,attempts=attempts)

    @app.route('/exam-bank/online/<test_id>',methods=['GET','POST'])
    def online_exam(test_id):
        if not session.get('username'):
            if request.method=='POST': return jsonify(error='Your session expired. Sign in again, then reload this page.'),401
            return redirect(url_for('login'))
        test=mongo.db.exam_online_tests.find_one({'test_id':test_id})
        user=mongo.db.users.find_one({'username':session['username']}) or {}
        if not accessible(test,user): return 'Test not available',404
        key={'test_id':test_id,'username':session['username']}
        attempt=mongo.db.exam_attempts.find_one(key)
        if request.method=='POST':
            if not valid_form(): return jsonify(error='Session expired. Reload the page before saving.'),400
            if attempt and attempt.get('status')!='in_progress': return jsonify(error='This test has already been submitted.'),409
            try:
                raw=request.form.get('answers','{}')
                if len(raw)>1000000: raise ValueError('Answers are too large')
                answers=json.loads(raw)
                if not isinstance(answers,dict) or set(answers)-{q['question_id'] for q in test['questions']}: raise ValueError('Unknown question')
                cleaned={q['question_id']:clean_answer(q,answers.get(q['question_id'],{})) for q in test['questions']}
                action=request.form.get('action','save')
                if action not in {'save','submit'}: raise ValueError('Unknown action')
                revision=attempt.get('revision',0) if attempt else 0
                if request.form.get('revision','0')!=str(revision): return jsonify(error='Answers changed in another tab. Reload before saving.'),409
                if not attempt:
                    mongo.db.exam_attempts.create_index([('test_id',1),('username',1)],unique=True)
                    mongo.db.exam_attempts.insert_one({**key,'class_name':user.get('class_name',''),'attempt_id':token_urlsafe(12),'status':'in_progress','revision':0,'started_at':datetime.utcnow()})
                values={'answers':cleaned,'updated_at':datetime.utcnow(),'revision':revision+1}
                if action=='submit':
                    grades={q['question_id']:{'marks':grade_objective(q,cleaned[q['question_id']]),'source':'objective_check','comment':''} for q in test['questions']}
                    values.update(status='submitted',submitted_at=datetime.utcnow(),grades=grades,awarded_marks=sum(g['marks'] or 0 for g in grades.values()),pending_count=sum(g['marks'] is None for g in grades.values()))
                updated=mongo.db.exam_attempts.update_one({**key,'revision':revision,'status':'in_progress'},{'$set':values})
                if not updated.modified_count: return jsonify(error='Answers changed elsewhere. Reload before saving.'),409
                return jsonify(revision=revision+1,message='Submitted for marking' if action=='submit' else 'Answers saved',submitted=action=='submit')
            except DuplicateKeyError: return jsonify(error='Another tab has started this test. Reload to continue.'),409
            except (ValueError,TypeError,KeyError) as exc: return jsonify(error=str(exc)),400
        return render_template('exam_paper.html',title=test['title'],questions=[public_question(q) for q in test['questions']],total_marks=test['total_marks'],mode='online',test_id=test_id,attempt=attempt or {},form_token=token(),username=session['username'])

    @app.route('/exam-bank/tests/<test_id>/responses')
    def exam_responses(test_id):
        if not teacher(): return 'Access denied',403
        test=mongo.db.exam_online_tests.find_one({'test_id':test_id,'created_by':session['username']})
        if not test: return 'Test not found',404
        classes=sorted(v for v in mongo.db.exam_attempts.distinct('class_name',{'test_id':test_id}) if v)
        selected=request.args.get('class_name','');query={'test_id':test_id}
        if selected: query['class_name']=selected
        attempts=list(mongo.db.exam_attempts.find(query,{'answers':0,'grades':0}).sort('updated_at',-1))
        return render_template('exam_responses.html',test=test,attempts=attempts,classes=classes,selected_class=selected)

    @app.route('/exam-bank/attempts/<attempt_id>',methods=['GET','POST'])
    def exam_mark_attempt(attempt_id):
        if not teacher(): return 'Access denied',403
        attempt=mongo.db.exam_attempts.find_one({'attempt_id':attempt_id})
        test=mongo.db.exam_online_tests.find_one({'test_id':attempt['test_id'],'created_by':session['username']}) if attempt else None
        if not test: return 'Response not found',404
        error=None
        if request.method=='POST':
            if not valid_form(): return 'Invalid form token',400
            try:
                if attempt['status']=='in_progress': raise ValueError('The student has not submitted this test yet')
                grades={}
                for q in test['questions']:
                    qid=q['question_id'];comment=request.form.get('comment_'+qid,'').strip()
                    if len(comment)>2000: raise ValueError('Comment too long')
                    grades[qid]={'marks':validate_mark(request.form.get('marks_'+qid,''),q['marks']),'comment':comment,'source':'teacher'}
                revision=attempt.get('revision',0)
                if request.form.get('revision')!=str(revision): raise ValueError('Marks changed elsewhere. Reload this page.')
                if not mongo.db.exam_attempts.update_one({'_id':attempt['_id'],'revision':revision},{'$set':{'grades':grades,'status':'marked','pending_count':0,'awarded_marks':sum(g['marks'] for g in grades.values()),'marked_by':session['username'],'marked_at':datetime.utcnow(),'revision':revision+1}}).modified_count: raise ValueError('Marks changed elsewhere. Reload this page.')
                return redirect(url_for('exam_responses',test_id=test['test_id']))
            except ValueError as exc: error=str(exc)
        return render_template('exam_mark.html',test=test,attempt=attempt,error=error,form_token=token())
