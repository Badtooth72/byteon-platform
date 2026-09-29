"""Fixed, server-marked activities with separate best and latest attempt scores."""
import ast
from datetime import datetime

def value(prompt,answer,explanation):return dict(kind='value',prompt=prompt,answer=str(answer),explanation=explanation)
def choice(prompt,answer,options,explanation):return dict(kind='choice',prompt=prompt,answer=answer,options=options,explanation=explanation)
def task(title,topic,items,**extra):return dict(title=title,topic=topic,items=items,**extra)

DATA_TASKS={
 'numbers':task('Bits, bytes and number bases','1.2.4',[
 value('How many bits are in one byte?',8,'A byte contains eight bits.'),
 value('Convert binary 10110110 to decimal.',182,'128 + 32 + 16 + 4 + 2 = 182.'),
 value('Convert decimal 45 to an 8-bit binary number.','00101101','32 + 8 + 4 + 1 = 45.'),
 value('Convert hexadecimal 3F to decimal.',63,'3 × 16 + 15 = 63.')]),
 'arithmetic':task('Binary arithmetic and shifts','1.2.4',[
 value('Add 00101101 and 00010011. Give an 8-bit binary answer.','01000000','45 + 19 = 64; carry bits when a column totals two or more.'),
 value('Left-shift 00110100 by two places using eight bits.','11010000','Each left shift multiplies an unsigned value by two when no significant bits are lost.'),
 value('Right-shift 10110000 by three places using eight bits.','00010110','Fill from the left with zero; the value is divided by eight.'),
 choice('Why does adding 255 and 1 overflow an 8-bit unsigned value?','The result needs nine bits',['The result needs nine bits','A byte has sixteen bits','The answer is negative'],'256 is 100000000 in binary, which does not fit eight bits.')]),
 'characters':task('Characters and character sets','1.2.4',[
 value('A supplied ASCII table gives A as decimal 65. What is the code for D?',68,'Letters have consecutive codes: A=65, B=66, C=67, D=68.'),
 value('Using eight bits per character, how many bytes store 12 characters?',12,'Each character occupies one byte in this question.'),
 choice('Why can Unicode represent more characters than ASCII?','It supports a much larger character repertoire',['It supports a much larger character repertoire','It stores only English letters','It uses no binary codes'],'Unicode supports characters from many writing systems; encodings can use different numbers of bytes.'),
 value('How many different codes can a 7-bit character set represent?',128,'There are 2 to the power of 7 possible patterns.')]),
 'images':task('Pixels, colour and image size','1.2.4',[
 value('A bitmap is 20 pixels wide and 10 pixels high with 4-bit colour. Ignoring metadata, how many bits are required?',800,'Width × height × colour depth = 20 × 10 × 4.'),
 value('How many colours can a 4-bit colour depth represent?',16,'2 to the power of 4 gives sixteen colours.'),
 choice('Which is image metadata?','Width, height and colour depth',['Width, height and colour depth','Only the visible subject','Only the file name extension'],'Metadata describes how image data should be interpreted.'),
 choice('What happens to uncompressed image data size if colour depth doubles, with dimensions unchanged?','It doubles',['It doubles','It halves','It stays unchanged'],'Each pixel now requires twice as many bits.')]),
 'sound':task('Sampling and sound size','1.2.4',[
 value('A mono recording uses 8000 samples per second, 8 bits per sample and lasts 2 seconds. Ignoring metadata, how many bits are required?',128000,'Sample rate × bit depth × duration = 8000 × 8 × 2.'),
 value('How many bytes is that 128000-bit recording?',16000,'Divide the number of bits by eight.'),
 choice('What does a higher sample rate do?','Measures the signal more often',['Measures the signal more often','Always shortens the recording','Reduces every sample to one bit'],'Sampling more frequently can capture more detail and increases uncompressed size.'),
 choice('What does a greater bit depth allow?','More possible values for each sample',['More possible values for each sample','Fewer samples per second automatically','No need for sampling'],'More bits provide more possible amplitude levels, increasing size and potential fidelity.')]),
 'compression':task('Compression choices','1.2.4',[
 choice('Which compression can reconstruct the original data exactly?','Lossless',['Lossless','Lossy','Neither'],'Lossless compression preserves all original information.'),
 choice('Which is suitable for a source-code file that must be recovered exactly?','Lossless',['Lossless','Lossy','Discard half the characters'],'Program text must retain every required character.'),
 choice('Which is a drawback of lossy compression?','Discarded information cannot be fully recovered',['Discarded information cannot be fully recovered','It always increases file size','It never changes quality'],'Lossy compression trades some information for smaller files.'),
 choice('Why compress a file before sending it?','Reduce storage needs and transfer time',['Reduce storage needs and transfer time','Guarantee encryption','Make all files executable'],'Smaller files require fewer bytes to store and transmit.')]),
}

def bug(title,code,line,fixes,output,explanation):
    return dict(title=title,topic='2.3.2',code=code,line=line,fixes=fixes,output=output,explanation=explanation,items=[])
BUG_TASKS={
 'comparison':bug('Assignment or comparison?','age = 16\nif age = 16:\n    print("Eligible")',2,['if age == 16:'],'Eligible','Use == to compare values; = assigns a value.'),
 'range':bug('The missing final number','for number in range(1, 5):\n    print(number)',1,['for number in range(1, 6):'],'1\n2\n3\n4\n5','The stop value in range is excluded.'),
 'input':bug('Adding to an input','age = "15"\nnext_age = age + 1\nprint(next_age)',2,['next_age = int(age) + 1','next_age = 1 + int(age)'],'16','Convert a numeric string to an integer before arithmetic.'),
 'total':bug('A total that forgets','total = 0\nfor value in [3, 5, 2]:\n    total = value\nprint(total)',3,['total += value','total = total + value','total = value + total'],'10','Accumulate each value instead of replacing the running total.'),
 'condition':bug('An impossible condition','score = 70\nif score < 0 and score > 100:\n    print("Invalid")\nelse:\n    print("Valid")',2,['if score < 0 or score > 100:'],'Valid','A number is outside the range if either boundary is exceeded; both cannot hold at once.'),
 'largest':bug('Finding the largest','largest = 6\nfor value in [2, 9, 4]:\n    if value < largest:\n        largest = value\nprint(largest)',3,['if value > largest:'],'9','Replace the largest value only when a larger one is found.'),
 'index':bug('First or second item?','names = ["Ada", "Grace"]\nprint(names[1])',2,['print(names[0])'],'Ada','Python lists start at index zero. Print the first name.'),
 'loop':bug('A loop that never ends','number = 1\nwhile number <= 3:\n    print(number)\n    number = number',4,['number += 1','number = number + 1','number = 1 + number'],'1\n2\n3','Update the loop variable so the condition eventually becomes false.'),
 'average':bug('The incorrect average','values = [2, 4, 6]\naverage = sum(values)\nprint(average)',2,['average = sum(values) / len(values)'],'4.0','An average divides the total by the number of values.'),
 'boundary':bug('Inclusive pass mark','mark = 50\nif mark > 50:\n    print("Pass")\nelse:\n    print("Retry")',2,['if mark >= 50:'],'Pass','A pass mark of 50 includes exactly 50, so use >=.'),
}
for key,goal in {
 'comparison':'Print Eligible when age equals 16.', 'range':'Print the integers 1 to 5 inclusive.',
 'input':'Print the next age as an integer.', 'total':'Print the total of all three values.',
 'condition':'Reject scores below 0 or above 100; accept values in that inclusive range.',
 'largest':'Print the largest value in the data.', 'index':'Print the first name in the list.',
 'loop':'Print 1, 2 and 3, then stop.', 'average':'Print the arithmetic mean as a float.',
 'boundary':'Print Pass for marks of 50 or higher, otherwise Retry.',
}.items(): BUG_TASKS[key]['goal']=goal

QUIZ_TASKS={
 'operating-systems':task('Operating systems','1.5.1',[
 choice('Which OS function lets a user interact through windows and menus?','User interface',['User interface','Defragmentation','Compression'],'A GUI provides visual controls; a command-line interface uses typed commands.'),
 choice('Which OS function allocates memory to applications?','Memory management',['Memory management','Copyright enforcement','Image compression'],'The OS manages memory allocation and movement between memory and storage.'),
 choice('What enables several applications to make progress on one CPU?','The OS schedules processor time',['The OS schedules processor time','Each application owns a separate physical CPU','The OS deletes all unused files'],'Scheduling shares processor time between processes.'),
 choice('What communicates with a particular printer on behalf of the OS?','A device driver',['A device driver','A copyright licence','An archive file'],'Drivers allow the OS to communicate with peripherals.'),
 choice('Which OS functions organise folders and control account permissions?','File management and user management',['File management and user management','Compression and lossy sampling','Defragmentation and colour depth'],'File management organises stored files; user management manages accounts and access.')]),
 'utilities':task('Utility software','1.5.2',[
 choice('Which utility reduces the size of stored files?','Compression',['Compression','Defragmentation','A printer driver'],'Compression reduces the amount of data required for storage or transfer.'),
 choice('Which utility makes data unreadable without the appropriate key?','Encryption',['Encryption','Defragmentation','A graphical interface'],'Encryption protects confidentiality by transforming data into ciphertext.'),
 choice('What does defragmentation do on a magnetic hard disk?','Rearranges file fragments into more contiguous locations',['Rearranges file fragments into more contiguous locations','Deletes every duplicate file','Adds more RAM'],'This can reduce head movement when accessing fragmented files.'),
 choice('Which statement about defragmentation is correct?','It is not needed for SSDs in the same way as HDDs',['It is not needed for SSDs in the same way as HDDs','It doubles SSD capacity','It is a form of encryption'],'SSDs do not use moving read/write heads, so the same seek-time benefit does not apply.'),
 choice('Why are utilities useful alongside an operating system?','They perform additional maintenance tasks',['They perform additional maintenance tasks','They replace all applications','They remove the need for hardware'],'Utilities provide additional housekeeping and maintenance functions.')]),
 'impacts':task('Ethical, cultural and environmental impacts','1.6.1',[
 choice('A recruitment algorithm disadvantages a group because of biased training data. What is the main concern?','Fairness and discrimination',['Fairness and discrimination','Binary overflow','Defragmentation'],'Automated decisions can reproduce bias; organisations should assess fairness and accountability.'),
 choice('A service tracks people without clearly explaining what it collects. Which concern is most direct?','Privacy',['Privacy','Colour depth','Processor speed'],'Tracking can reveal personal information and reduce control over how data is used.'),
 choice('Moving every service online may disadvantage people who lack connectivity. What is this an example of?','The digital divide',['The digital divide','Lossless compression','A syntax error'],'Differences in access, skills and affordability can exclude users.'),
 choice('Which action can reduce the environmental impact of devices?','Repair and responsibly recycle them',['Repair and responsibly recycle them','Replace working devices every month','Send all electronic waste to landfill'],'Repair extends useful life; responsible recycling recovers materials and reduces harmful waste.'),
 choice('Which is a balanced view of remote working technology?','It can reduce travel but increase energy use in homes and data centres',['It can reduce travel but increase energy use in homes and data centres','It has no environmental effects','It always eliminates every journey'],'Impacts depend on use: weigh benefits against energy consumption and other costs.')]),
 'law-licences':task('Legislation and software licences','1.6.1',[
 choice('Which syllabus law concerns processing personal data?','Data Protection Act 2018',['Data Protection Act 2018','Computer Misuse Act 1990','Copyright Designs and Patents Act 1988'],'The Data Protection Act 2018 forms part of the framework for protecting personal data.'),
 choice('Accessing a system without authorisation is primarily linked to which syllabus law?','Computer Misuse Act 1990',['Computer Misuse Act 1990','Copyright Designs and Patents Act 1988','Data Protection Act 2018'],'The Computer Misuse Act addresses unauthorised access and related misuse offences.'),
 choice('Copying software without the required permission relates most directly to which syllabus law?','Copyright Designs and Patents Act 1988',['Copyright Designs and Patents Act 1988','Computer Misuse Act 1990','Data Protection Act 2018'],'Copyright protects software and other creative works; licences specify permitted use.'),
 choice('Which describes open-source software?','Its source code is available under a licence allowing use, modification and redistribution',['Its source code is available under a licence allowing use, modification and redistribution','It has no licence conditions','It must always cost money'],'Open-source licences grant permissions and may impose conditions; open source does not mean no copyright.'),
 choice('Which is a possible advantage of proprietary software?','Commercial support and a managed product',['Commercial support and a managed product','Unlimited modification of closed source is guaranteed','It has no licence restrictions'],'Proprietary products may offer support and integration, with licence and modification restrictions.')]),
}

def gap(sentence, answer, explanation, words=None):
    return dict(kind='gap' if words else 'missing', prompt='Complete the sentence.', sentence=sentence,
                answer=answer, explanation=explanation, options=words or [])
def matching(prompt, pairs):
    return dict(kind='matching', prompt=prompt, pairs=[p[0] for p in pairs], answers=[p[1] for p in pairs],
                options=[p[1] for p in pairs], explanation='Match each term with its definition.')
DATA_TASKS['numbers']['items'][0]=gap('One byte contains ___ bits.','8','A byte contains eight bits.')
DATA_TASKS['characters']['items'][2]=gap('___ supports characters from many writing systems.','Unicode','Unicode supports a larger character repertoire.',['ASCII','Unicode','Metadata'])
DATA_TASKS['images']['items'][2]=matching('Match the image terms to their meanings.',[('Pixel','One point in a bitmap'),('Colour depth','Bits used for each pixel'),('Metadata','Information describing the image')])
DATA_TASKS['sound']['items'][2]=matching('Match the sound terms to their meanings.',[('Sample rate','Measurements taken per second'),('Bit depth','Bits used for each sample'),('Duration','Length of the recording')])
DATA_TASKS['compression']['items'][0]=gap('___ compression reconstructs the original data exactly.','Lossless','Lossless compression retains all original information.',['Lossless','Lossy','Encrypted'])
QUIZ_TASKS['operating-systems']['items'][0]=matching('Match each operating system function to its purpose.',[('User interface','Allows the user to interact with the computer'),('Memory management','Allocates RAM to running programs'),('Peripheral management','Communicates with connected devices using drivers')])
QUIZ_TASKS['utilities']['items'][0]=gap('A ___ utility reduces the size of files.','compression','Compression reduces storage requirements.',['compression','encryption','defragmentation'])
QUIZ_TASKS['utilities']['items'][1]=gap('___ makes data unreadable without the appropriate key.','encryption','Encryption protects the confidentiality of data.')
QUIZ_TASKS['impacts']['items'][2]=gap('Unequal access to technology is known as the digital ___.','divide','The digital divide includes differences in access, affordability and skills.')
QUIZ_TASKS['law-licences']['items'][0]=matching('Match each syllabus law to the issue it addresses.',[('Data Protection Act 2018','Processing personal data'),('Computer Misuse Act 1990','Unauthorised computer access'),('Copyright Designs and Patents Act 1988','Copying protected works without permission')])

DEFENSIVE_TASKS={
 'input-defence':task('Input defence','2.3.1',[
  matching('Match each check to the input it should reject.',[('Range check','A mark of 120 when 0–100 is allowed'),('Type check','The word ten in a numeric field'),('Presence check','A required answer left empty')]),
  choice('A mark must be between 0 and 100 inclusive. Which value is valid boundary data?','100',['100','101','-1','one hundred'],'The upper valid boundary is 100.'),
  gap('Checking that an entered value meets the rules is called ___.','validation','Validation checks whether input follows a stated rule.',['validation','authentication','encryption']),
  choice('What should a program do after rejecting an invalid mark?','Explain the problem and ask again',['Explain the problem and ask again','Silently replace it with 50','Continue using the invalid value'],'A clear error and another attempt help a user correct the input.')]),
 'accounts':task('Accounts and permissions','2.3.1',[
  matching('Match the safeguard to its job.',[('Authentication','Checks the claimed identity of a user'),('Access permissions','Limit which resources an account can use'),('Encryption','Protects data from being read without a key')]),
  choice('A student signs in successfully but must not see staff records. What controls this?','Access permissions',['Access permissions','Authentication alone','A faster processor'],'Authentication identifies the student; permissions control access.'),
  choice('Which response is appropriate after repeated failed sign-ins?','Limit or temporarily lock attempts',['Limit or temporarily lock attempts','Print the correct password','Disable all password checks'],'Rate limits or lockouts can reduce password guessing.'),
  gap('A password confirms a claimed identity: this is ___.','authentication','Authentication checks who a user claims to be.',['authentication','compression','iteration'])]),
 'maintainability':task('Maintainable code','2.3.1',[
  matching('Match the practice to its benefit.',[('Meaningful names','Show what values represent'),('Indentation','Makes blocks of code easier to follow'),('Subprograms','Break a task into reusable parts')]),
  choice('Which variable name makes its purpose clearest?','total_mark',['total_mark','x','q1','data'],'A descriptive name helps a future reader understand the value.'),
  choice('Which comment helps maintainability most?','Explain why an unusual rule exists',['Explain why an unusual rule exists','Repeat every line of code exactly','Add a long unrelated story'],'Comments are most useful when they explain intent or non-obvious decisions.'),
  gap('A named, reusable section of code is a ___.','subprogram','Subprograms help organise and reuse code.',['subprogram','syntax error','pixel'])]),
 'testing':task('Test the edges','2.3.2',[
  matching('A field accepts integers from 11 to 16. Match the test type.',[('Normal','14 should be accepted'),('Boundary','11 and 16 should be accepted'),('Invalid','17 should be rejected'),('Erroneous','eleven should be rejected')]),
  choice('What belongs in a test plan before running the test?','Expected result',['Expected result','Only the actual result','A random grade'],'Expected behaviour lets you judge whether the actual result is correct.'),
  choice('After fixing a bug, what should you do?','Repeat the failed test and check other behaviour',['Repeat the failed test and check other behaviour','Delete the test','Assume all bugs are fixed'],'Retesting verifies the correction and helps spot regressions.')]),
}

LANGUAGE_TASKS={
 'translators':task('How code is translated','2.5.1',[
  matching('Match the translator to its typical process.',[('Compiler','Translates a whole program before execution'),('Interpreter','Translates and runs instructions as the program executes'),('Assembler','Translates assembly language into machine code')]),
  choice('What does a compiler commonly produce?','An executable or object code',['An executable or object code','A more colourful editor','A larger monitor'],'A compiler translates source code into code the processor can execute.'),
  choice('Which translator is commonly useful for testing a statement immediately?','Interpreter',['Interpreter','Assembler','Image editor'],'An interpreter can execute code as it is translated.'),
  gap('Assembly language is translated by an ___.','assembler','An assembler translates assembly language.',['assembler','interpreter','firewall'])]),
 'language-levels':task('High and low level','2.5.1',[
  matching('Match the language type to its characteristic.',[('High-level language','Usually easier for people to read and port'),('Assembly language','Uses mnemonics close to processor instructions'),('Machine code','Binary instructions executed by the CPU')]),
  choice('Why is a high-level language usually more portable?','The same source can be translated for different processors',['The same source can be translated for different processors','Every processor has identical machine code','It needs no translator'],'High-level source is less tied to one processor instruction set.'),
  choice('Which language gives the programmer the most direct control of processor instructions?','Assembly language',['Assembly language','A high-level language','HTML styling'],'Assembly language is closer to the processor instruction set.'),
  gap('The binary instructions executed directly by a processor are ___ code.','machine','Machine code consists of executable processor instructions.',['machine','source','pseudo'])]),
 'ide-tools':task('Inside an IDE','2.5.2',[
  matching('Match each IDE feature to its purpose.',[('Syntax highlighting','Colours code elements to aid reading'),('Breakpoint','Pauses execution at a chosen point'),('Variable watch','Shows changing values while debugging'),('Error diagnostics','Reports likely syntax or translation problems')]),
  choice('A loop produces the wrong total. Which IDE feature best lets you inspect values each pass?','Variable watch',['Variable watch','Font size','File compression'],'A watch displays the changing variable while you step through code.'),
  choice('Why set a breakpoint?','Pause execution and inspect the current state',['Pause execution and inspect the current state','Delete the program','Make the CPU run faster'],'A breakpoint pauses at a chosen point for debugging.'),
  gap('An IDE can suggest and complete code as you type: this is ___.','autocompletion','Autocompletion suggests code or completes names.',['autocompletion','defragmentation','sampling'])]),
}

LABS={
 'data-representation':dict(key='data_representation',title='Data Representation Lab',icon='▦',tasks=DATA_TASKS),
 'find-the-bug':dict(key='bug_hunt',title='Find and Fix the Bug',icon='⚒',tasks=BUG_TASKS),
 'systems-impacts':dict(key='systems_impacts',title='Systems Software and Impacts Quiz',icon='⚖',tasks=QUIZ_TASKS),
 'defensive-design':dict(key='defensive_design',title='Defensive Design Lab',icon='⛨',tasks=DEFENSIVE_TASKS),
 'languages-ides':dict(key='languages_ides',title='Languages and IDE Lab',icon='⌘',tasks=LANGUAGE_TASKS),
}
LAB_KEYS={lab['key']:slug for slug,lab in LABS.items()}

def canonical_line(source):
    source=source.strip()
    if source.endswith(':'):source+='\n    pass'
    try:return ast.dump(ast.parse(source),include_attributes=False)
    except (SyntaxError,ValueError,RecursionError):return None

def mark_lab(lab_key,task_id,answers):
    lab=LABS[LAB_KEYS[lab_key]];item=lab['tasks'][task_id]
    if not isinstance(answers,dict) or len(answers)>40 or any(not isinstance(v,str) or len(v)>2000 for v in answers.values()):raise ValueError('Invalid answers')
    if lab_key=='bug_hunt':
        fixed=canonical_line(answers.get('fix',''))
        checks=[(answers.get('line')==str(item['line']),'Correct faulty line: '+str(item['line'])),
                (fixed is not None and fixed in {canonical_line(f) for f in item['fixes']},item['explanation']),
                (answers.get('output','').strip()==item['output'],'Expected output after the repair:\n'+item['output'])]
    else:
        checks=[]
        for index,q in enumerate(item['items']):
            if q['kind']=='matching':
                for pair_index, expected in enumerate(q['answers']):
                    supplied=answers.get(f'{index}.{pair_index}','').strip()
                    checks.append((supplied.casefold()==expected.casefold(),q['pairs'][pair_index]+': '+expected))
            else:
                supplied=answers.get(str(index),'').strip()
                if q['kind']=='value':supplied=''.join(supplied.split())
                checks.append((supplied.casefold()==q['answer'].casefold(),q['explanation']))
    return {'score':round(sum(ok for ok,_ in checks)/len(checks)*100,1),'earned':sum(ok for ok,_ in checks),'maximum':len(checks),'feedback':[{'correct':ok,'text':text} for ok,text in checks]}

def register_learning_labs(app,mongo,token,valid_form):
    from flask import session,redirect,url_for,request,render_template,jsonify
    from homework import highlight_code
    @app.route('/learning-labs/<slug>')
    def learning_lab_home(slug):
        if not session.get('username'):return redirect(url_for('login'))
        lab=LABS.get(slug)
        if not lab:return 'Unknown lab',404
        user=mongo.db.users.find_one({'username':session['username']}) or {}
        return render_template('learning_lab.html',lab=lab,slug=slug,task=None,records=(user.get('activities') or {}).get(lab['key'],{}),teacher=user.get('role') in {'teacher','admin'})
    @app.route('/learning-labs/<slug>/<task_id>',methods=['GET','POST'])
    def learning_lab_task(slug,task_id):
        if not session.get('username'):
            if request.method=='POST':return jsonify(error='Your session expired. Sign in again, then reload. Your draft is retained in this tab.'),401
            return redirect(url_for('login'))
        lab=LABS.get(slug);item=(lab or {}).get('tasks',{}).get(task_id)
        if not item:return 'Unknown challenge',404
        user=mongo.db.users.find_one({'username':session['username']}) or {};record=(user.get('activities') or {}).get((lab or {})['key'],{}).get(task_id,{})
        if request.method=='POST':
            if not valid_form():return jsonify(error='Your session changed. Reload before saving; your draft is retained.'),400
            answers={k:v for k,v in request.form.items() if k!='form_token'}
            try:result=mark_lab(lab['key'],task_id,answers)
            except ValueError as exc:return jsonify(error=str(exc)),400
            now=datetime.utcnow();path=f"activities.{lab['key']}.{task_id}"
            mongo.db.users.update_one({'username':session['username']},{'$set':{path+'.last_score':result['score'],path+'.date':now,path+'.answers':answers},'$max':{path+'.score':result['score']},'$inc':{path+'.attempts':1},'$push':{path+'.history':{'$each':[{'score':result['score'],'date':now}],'$slice':-100}}})
            mongo.db.learning_lab_attempts.create_index([('username',1),('activity_key',1),('submitted_at',-1)])
            mongo.db.learning_lab_attempts.insert_one({'username':session['username'],'class_name':user.get('class_name',''),'activity_key':lab['key'],'task_id':task_id,'score':result['score'],'answers':answers,'submitted_at':now})
            return jsonify(result)
        public={key:value for key,value in item.items() if key not in {'line','fixes','output','explanation','items'}}
        public['items']=[{k:v for k,v in q.items() if k not in {'answer','answers','explanation'}} for q in item['items']]
        return render_template('learning_lab.html',lab=lab,slug=slug,task=public,task_id=task_id,record=record,form_token=token(),username=session['username'],highlighted=highlight_code(item['code']) if 'code' in item else None)

    @app.route('/learning-labs/reports')
    def learning_lab_reports():
        if not session.get('username'):return redirect(url_for('login'))
        user=mongo.db.users.find_one({'username':session['username']}) or {}
        if user.get('role') not in {'teacher','admin'}:return 'Access denied',403
        query={};selected=request.args.get('activity','');class_name=request.args.get('class_name','')
        if selected:
            if selected not in LAB_KEYS:return 'Unknown activity',400
            query['activity_key']=selected
        if class_name:query['class_name']=class_name
        rows=list(mongo.db.learning_lab_attempts.find(query).sort('submitted_at',-1).limit(200))
        return render_template('learning_lab_reports.html',labs=LABS,rows=rows,classes=sorted(v for v in mongo.db.users.distinct('class_name') if v),selected=selected,class_name=class_name,lab_keys=LAB_KEYS)
