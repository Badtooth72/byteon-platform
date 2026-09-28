"""Finite, authored adaptive practice. The server chooses and grades every next question."""
from datetime import datetime

TOPICS={
 'representation':('1.2 Data representation','1.2'),
 'programming':('2.2 Programming fundamentals','2.2'),
 'algorithms':('2.1 Search and sort','2.1'),
 'logic':('2.3 Boolean logic','2.3'),
}
# Each concept has scaffold, core and stretch variants, in that order.
BANK={
 'representation':[
  [('A byte contains how many bits?','8'),('Convert binary 1010 to decimal.','10'),('Convert binary 110101 to decimal.','53')],
  [('How many values fit in two bits?','4'),('How many values fit in four bits?','16'),('How many values fit in seven bits?','128')],
  [('How many bits store one 8-bit character?','8'),('How many bytes store 12 characters at 8 bits each?','12'),('How many bits store 25 characters at 8 bits each?','200')],
  [('How many pixels are in a 4 by 4 bitmap?','16'),('How many bits for a 10 by 10 image at 2-bit colour depth?','200'),('How many bytes for a 20 by 10 image at 4-bit colour depth?','100')],
  [('Which compression preserves every bit: lossless or lossy?','lossless'),('Which compression should preserve source code exactly: lossless or lossy?','lossless'),('Which compression can discard detail to shrink a photograph: lossless or lossy?','lossy')],
 ],
 'programming':[
  [('Which operator assigns a value in Python: = or ==?','='),('Which operator compares equality in Python: = or ==?','=='),('What is printed by x=3; print(x==3)?','True')],
  [('What is the value of 7 % 2?','1'),('What is the value of 17 // 5?','3'),('What is the value of (13 % 5) * 2?','6')],
  [('Which structure repeats instructions: sequence, selection or iteration?','iteration'),('Which structure chooses between branches: selection or iteration?','selection'),('What is printed by: for n in range(2,5): print(n)? Give comma-separated values.','2,3,4')],
  [('What is the first index of a Python list?','0'),('What is printed by values=[4,7,9]; print(values[1])?','7'),('What is printed by values=[4,7,9]; print(values[-1])?','9')],
  [('What is int("5") + 2?','7'),('What is len("byte")?','4'),('What is printed by print(str(12)+"3")?','123')],
 ],
 'algorithms':[
  [('Does linear search require sorted data: yes or no?','no'),('Which search checks items one by one: linear or binary?','linear'),('Which search repeatedly halves sorted data: linear or binary?','binary')],
  [('Which search requires sorted data: linear or binary?','binary'),('What index does binary search check first in a sorted list of 7 items indexed 0 to 6?','3'),('A sorted list has 15 items indexed 0 to 14. What index is checked first in binary search?','7')],
  [('After one bubble-sort comparison of 5,2, which order should the pair have?','2,5'),('After one complete bubble-sort pass over 3,1,2, what is the list?','1,2,3'),('After one bubble-sort pass over 4,1,3,2, what is the list?','1,3,2,4')],
  [('Does merge sort divide the list: yes or no?','yes'),('Merge the sorted lists [1,4] and [2,3]. Give comma-separated values.','1,2,3,4'),('Merge [2,7,9] and [1,6,8]. Give comma-separated values.','1,2,6,7,8,9')],
  [('What is the index of 8 in [3,8,5]?','1'),('In [2,4,6,8], what index holds 6?','2'),('A linear search for 9 in [4,7,9,2] checks how many items?','3')],
 ],
 'logic':[
  [('What is 1 AND 1?','1'),('What is 1 AND 0?','0'),('What is (1 AND 0) OR 1?','1')],
  [('What is 0 OR 1?','1'),('What is 0 OR 0?','0'),('What is (0 OR 1) AND 0?','0')],
  [('What is NOT 0?','1'),('What is NOT 1?','0'),('What is NOT (1 AND 0)?','1')],
  [('Which gate outputs 1 only when both inputs are 1: AND or OR?','AND'),('Which gate outputs 1 when either input is 1: AND or OR?','OR'),('Which gate would output 0 for inputs 1 and 0: AND or OR?','AND')],
  [('What is NOT (0 OR 0)?','1'),('What is (1 OR 0) AND 1?','1'),('What is NOT ((1 AND 1) OR 0)?','0')],
 ],
}
MAX_QUESTIONS=15

def normalise(value):
    return ''.join(str(value).strip().casefold().split()).replace(';',',')

def choose_question(topic, step, previous_correct, used_levels=None):
    """Visit each concept up to three times without repeating its wording."""
    if topic not in BANK or not 0 <= step < MAX_QUESTIONS:raise ValueError('Unknown topic or step')
    concept=step%5
    preferred=1 if previous_correct is None else (2 if previous_correct else 0)
    used=set(used_levels or ())
    remaining=[level for level in range(3) if level not in used]
    if not remaining:raise ValueError('Question bank exhausted')
    level=min(remaining,key=lambda candidate:(abs(candidate-preferred),candidate))
    prompt,answer=BANK[topic][concept][level]
    return {'prompt':prompt,'answer':answer,'level':level,'step':step}

def grade(question, answer):
    return normalise(answer)==normalise(question['answer'])

def register_adaptive(app,mongo,token,valid_form):
    from flask import session,redirect,url_for,request,render_template,jsonify
    @app.route('/adaptive-practice')
    def adaptive_home():
        if not session.get('username'):return redirect(url_for('login'))
        user=mongo.db.users.find_one({'username':session['username']}) or {}
        return render_template('adaptive_practice.html',topics=TOPICS,topic=None,
            records=(user.get('activities') or {}).get('adaptive_practice',{}))
    def run_context(topic, username):
        """Resolve an assignment and question count without trusting the form."""
        assignment_id=request.args.get('assignment','').strip()
        if assignment_id:
            from bson import ObjectId
            try:assignment=mongo.db.homework_assignments.find_one({'_id':ObjectId(assignment_id)})
            except Exception:assignment=None
            user=mongo.db.users.find_one({'username':username}) or {}
            tasks=(assignment or {}).get('tasks') or [{'task_id':(assignment or {}).get('task_id')}]
            allowed=(assignment and assignment.get('activity_key')=='adaptive_practice'
                and any(task.get('task_id')==topic for task in tasks)
                and (user.get('class_name')==assignment.get('class_name') or user.get('role') in {'teacher','admin'}))
            if not allowed:return None
            return assignment_id,int(assignment.get('question_count',5))
        raw=request.args.get('questions','10')
        if raw not in {'10','15'}:return None
        return 'practice-'+raw,int(raw)

    def topic_url(topic, run_key, total):
        return url_for('adaptive_topic',topic=topic,**({'assignment':run_key} if not run_key.startswith('practice-') else {'questions':total}))

    @app.route('/adaptive-practice/<topic>',methods=['GET','POST'])
    def adaptive_topic(topic):
        if not session.get('username'):
            if request.method=='POST':return jsonify(error='Your session expired. Sign in again.'),401
            return redirect(url_for('login'))
        if topic not in TOPICS:return 'Unknown topic',404
        username=session['username']
        context=run_context(topic,username)
        if context is None:return 'Invalid assignment or question count',403
        run_key,total=context
        runs=mongo.db.adaptive_runs
        run=runs.find_one({'username':username,'topic':topic,'run_key':run_key,'status':'active'})
        if not run and run_key=='practice-10':
            legacy=runs.find_one({'username':username,'topic':topic,'status':'active','run_key':{'$exists':False}})
            if legacy:
                runs.update_one({'_id':legacy['_id']},{'$set':{'run_key':run_key,'total':10}})
                run=legacy;run['run_key']=run_key;run['total']=10
        if request.method=='POST':
            if not valid_form():return jsonify(error='Form expired; reload the page.'),400
            if request.form.get('action')=='restart':
                runs.update_many({'username':username,'topic':topic,'run_key':run_key,'status':'active'},{'$set':{'status':'abandoned'}})
                return redirect(topic_url(topic,run_key,total))
            if not run:return jsonify(error='This run has ended. Reload the page.'),409
            answer=request.form.get('answer','')
            if len(answer)>200:return jsonify(error='Answer too long'),400
            question=run['question'];correct=grade(question,answer);now=datetime.utcnow()
            attempt={'prompt':question['prompt'],'answer':answer,'expected':question['answer'],
                'correct':correct,'level':question['level'],'step':question['step'],'at':now}
            # Compare the current step: a double click cannot score twice.
            updated=runs.update_one({'_id':run['_id'],'step':run['step'],'status':'active'},
                {'$push':{'answers':attempt},'$inc':{'step':1,'correct':int(correct)}})
            if not updated.modified_count:return jsonify(error='Already submitted; reload the page.'),409
            step=run['step']+1;score=run['correct']+int(correct)
            if step<run.get('total',5):
                prior=[a['level'] for i,a in enumerate(run.get('answers',[])) if a.get('step',i)%5==step%5]
                if question['step']%5==step%5:prior.append(question['level'])
                next_question=choose_question(topic,step,correct,prior)
                runs.update_one({'_id':run['_id'],'status':'active','step':step},{'$set':{'question':next_question}})
                return jsonify(correct=correct,expected=question['answer'],next=topic_url(topic,run_key,total),finished=False)
            percent=round(score/run.get('total',5)*100)
            runs.update_one({'_id':run['_id']},{'$set':{'status':'complete','finished_at':now,'score':percent}})
            path='activities.adaptive_practice.'+topic
            mongo.db.users.update_one({'username':username},{'$max':{path+'.score':percent},
                '$inc':{path+'.attempts':1},'$set':{path+'.date':now,path+'.last_score':percent}})
            mongo.db.adaptive_attempts.insert_one({'username':username,'topic':topic,'score':percent,
                'finished_at':now,'run_id':run['_id'],'run_key':run_key,'question_count':run.get('total',5)})
            return jsonify(correct=correct,expected=question['answer'],finished=True,score=percent,next=topic_url(topic,run_key,total))
        if not run:
            now=datetime.utcnow();question=choose_question(topic,0,None)
            run={'username':username,'topic':topic,'run_key':run_key,'total':total,'status':'active','step':0,'correct':0,
                 'question':question,'answers':[],'started_at':now}
            result=runs.insert_one(run);run['_id']=result.inserted_id
        user=mongo.db.users.find_one({'username':username}) or {}
        record=((user.get('activities') or {}).get('adaptive_practice') or {}).get(topic,{})
        return render_template('adaptive_practice.html',topics=TOPICS,topic=topic,
            question={k:v for k,v in run['question'].items() if k!='answer'},
            run=run,record=record,form_token=token())
