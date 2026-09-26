import unittest
from exam_formats import parse_format,public_question,clean_answer,grade_objective,validate_mark

class ExamFormatTests(unittest.TestCase):
    def question(self,form,text='Question',marks=4):
        question={'question_id':'sample','question_text':text,'marks':marks}
        question['response_spec'],question['marking_spec']=parse_format(form,question)
        return question

    def test_word_bank_validates_numbered_blanks_and_partial_marks(self):
        q=self.question({'response_type':'word_bank','choices':'RAM\nROM\nCPU','blank_answers':'RAM\nROM'},'[[1]] is volatile, [[2]] is not.')
        answer=clean_answer(q,{'blanks':['RAM','CPU']})
        self.assertEqual(grade_objective(q,answer),2)
        with self.assertRaises(ValueError): self.question({'response_type':'word_bank','choices':'RAM','blank_answers':'RAM'},'[[2]]')

    def test_ticks_do_not_reward_selecting_everything(self):
        q=self.question({'response_type':'multiple_choice','choices':'a\nb\nc','correct_choices':'1,3'})
        self.assertEqual(grade_objective(q,clean_answer(q,{'choices':[2,0]})),4)
        self.assertEqual(grade_objective(q,clean_answer(q,{'choices':[0,1,2]})),0)
        q=self.question({'response_type':'single_choice','choices':'a\nb','correct_choices':'2'})
        with self.assertRaises(ValueError): clean_answer(q,{'choices':[0,1]})

    def test_matching_partial_marks(self):
        q=self.question({'response_type':'matching','pairs':'a | x\nb | y'})
        self.assertEqual(grade_objective(q,clean_answer(q,{'matches':[0,-1]})),2)

    def test_binary_carry_and_fixed_width_shift(self):
        q=self.question({'response_type':'binary_math','operand_a':'1111','operand_b':'0001','width':'4','shift':'1','operation':'add'})
        self.assertEqual(q['marking_spec']['accepted'],['10000'])
        q=self.question({'response_type':'binary_math','operand_a':'1011','width':'4','shift':'1','operation':'shift_left'})
        self.assertEqual(q['marking_spec']['accepted'],['0110'])
        self.assertEqual(grade_objective(q,{'value':'01 10'}),4)
        self.assertIsNone(grade_objective(q,{'value':'wrong','working':'Some working'}))

    def test_code_profiles_require_teacher_judgement(self):
        for kind,policy in [('algorithm','lenient'),('python','formal_with_minor_leeway')]:
            q=self.question({'response_type':kind,'answer_lines':'8','starter_code':'for ???'})
            self.assertEqual(q['response_spec']['syntax_policy'],policy)
            self.assertIsNone(grade_objective(q,{'value':'not executable'}))

    def test_public_questions_never_include_answers_or_guidance(self):
        q=self.question({'response_type':'short_value','accepted':'secret answer'})
        q['marking_guidance']='secret guidance'
        self.assertNotIn('marking_spec',public_question(q))
        self.assertNotIn('marking_guidance',public_question(q))

    def test_reject_nonfinite_or_out_of_range_marks(self):
        for value in ('NaN','Infinity','-1','5','bad'):
            with self.assertRaises(ValueError): validate_mark(value,4)
        self.assertEqual(validate_mark('2.5',4),2.5)

    def test_tables_and_essays_are_pending(self):
        q=self.question({'response_type':'essay','answer_lines':'20'})
        self.assertIsNone(grade_objective(q,{'value':'An essay'}))

if __name__=='__main__': unittest.main()
