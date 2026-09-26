import unittest
from datetime import datetime,timedelta,timezone
from learning_labs import LABS,BUG_TASKS,mark_lab,canonical_line
from activity_scores import score_activity,course_progress
from achievements import eligible_achievements
from homework import validate_target,specific_progress

class LabTests(unittest.TestCase):
    def test_every_task_can_score_full_marks(self):
        for slug,lab in LABS.items():
            for key,item in lab['tasks'].items():
                answers={'line':str(item['line']),'fix':item['fixes'][0],'output':item['output']} if lab['key']=='bug_hunt' else {str(i):q['answer'] for i,q in enumerate(item['items'])}
                self.assertEqual(mark_lab(lab['key'],key,answers)['score'],100,(slug,key))

    def test_ast_fix_is_whitespace_and_quote_tolerant(self):
        self.assertEqual(canonical_line(' print( names[0] ) '),canonical_line('print(names[0])'))
        self.assertIsNone(canonical_line('if [ broken :'))
        result=mark_lab('bug_hunt','index',{'line':'2','fix':'print( names[0] )','output':'Ada'})
        self.assertEqual(result['score'],100)

    def test_tampered_scores_cannot_supply_credit(self):
        result=mark_lab('data_representation','numbers',{'score':'100','0':'wrong'})
        self.assertEqual(result['score'],0)

    def test_one_perfect_task_is_not_a_complete_lab(self):
        activities={'data_representation':{'numbers':{'score':100,'attempts':2}}}
        self.assertEqual(score_activity('data_representation',activities['data_representation'])['percent'],16.7)
        badges=eligible_achievements(activities)
        self.assertIn('data-perfect',badges);self.assertNotIn('data-all',badges)
        self.assertEqual(course_progress(activities)['points'],10)

    def test_homework_requires_fresh_attempt_and_keeps_post_assignment_best(self):
        now=datetime.now(timezone.utc)
        assignment={'activity_key':'data_representation','task_id':'numbers','created_at':now}
        records={'score':100,'history':[{'score':100,'date':now-timedelta(days=1)},{'score':75,'date':now+timedelta(seconds=1)},{'score':25,'date':now+timedelta(seconds=2)}]}
        self.assertEqual(specific_progress(assignment,{'activities':{'data_representation':{'numbers':records}}}),75)
        self.assertEqual(validate_target('data_representation','numbers','70'),70)
        with self.assertRaises(ValueError):validate_target('data_representation','missing','70')

if __name__=='__main__':unittest.main()
