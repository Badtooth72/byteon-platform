import unittest
from adaptive_practice import TOPICS,BANK,choose_question,grade
from activity_scores import score_activity,course_progress
from homework import validate_target,task_title
from achievements import eligible_achievements
class AdaptiveTests(unittest.TestCase):
 def test_all_topics_have_five_levels_and_grade_their_answers(self):
  for topic in TOPICS:
   self.assertEqual(len(BANK[topic]),5)
   for step in range(5):
    for previous,level in [(False,0),(None,1),(True,2)]:
     q=choose_question(topic,step,previous)
     self.assertEqual(q['level'],level)
     self.assertTrue(grade(q,q['answer']))
 def test_homework_and_tracking(self):
  self.assertEqual(validate_target('adaptive_practice','representation','70'),70)
  self.assertIn('1.2',task_title('adaptive_practice','representation'))
  with self.assertRaises(ValueError):validate_target('adaptive_practice','missing','70')
  data={'representation':{'score':80,'attempts':2}}
  self.assertEqual(score_activity('adaptive_practice',data)['percent'],20)
  self.assertEqual(course_progress({'adaptive_practice':data})['points'],0)
  self.assertIn('adaptive-first',eligible_achievements({'adaptive_practice':data}))
if __name__=='__main__':unittest.main()
