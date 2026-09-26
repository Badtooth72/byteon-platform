import unittest
from network_designer import SCENARIOS, mark_design
from activity_scores import score_activity


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.design = {'nodes':[{'id':key,'type':kind} for key,kind in
            [('p1','pc'),('p2','pc'),('s','switch'),('r','router'),('w','wap'),('t','tablet'),('f','server'),('i','internet')]],
            'links':[{'a':a,'b':b,'medium':medium} for a,b,medium in
                [('p1','s','Ethernet'),('p2','s','Ethernet'),('f','s','Ethernet'),('w','s','Ethernet'),('r','s','Ethernet'),('t','w','Wi-Fi'),('r','i','Ethernet')]]}

    def test_complete_network_and_decisions(self):
        for scenario in SCENARIOS:
            if scenario['id']=='wireless': continue
            answers={str(i):q['answer'] for i,q in enumerate(scenario['questions'])}
            self.assertEqual(mark_design(scenario,self.design,answers)['score'],100)

    def test_disconnected_wireless_does_not_count(self):
        self.design['links']=[l for l in self.design['links'] if l['a']!='w']
        result=mark_design(SCENARIOS[0],self.design,{})
        self.assertFalse(result['feedback'][1]['correct'])
        self.assertFalse(result['feedback'][2]['correct'])

    def test_invalid_link_rejected(self):
        self.design['links'].append({'a':'missing','b':'p1','medium':'Wi-Fi'})
        with self.assertRaises(ValueError): mark_design(SCENARIOS[0],self.design,{})

    def test_mesh_requires_all_three_links(self):
        scenario=next(s for s in SCENARIOS if s['id']=='wireless')
        self.design['nodes'].append({'id':'p3','type':'pc'})
        self.design['links']=[{'a':a,'b':b,'medium':m} for a,b,m in
            [('p1','p2','Ethernet'),('p2','p3','Ethernet'),('p3','p1','Ethernet'),('p1','r','Ethernet'),('p1','w','Ethernet'),('t','w','Wi-Fi'),('r','i','Ethernet')]]
        answers={str(i):q['answer'] for i,q in enumerate(scenario['questions'])}
        self.assertEqual(mark_design(scenario,self.design,answers)['score'],100)
        self.design['links'].pop(0)
        self.assertLess(mark_design(scenario,self.design,answers)['score'],100)

    def test_unattempted_scenarios_count_in_progress(self):
        self.assertEqual(score_activity('network_designer',{'school':{'score':100,'attempts':1}})['percent'],20)


if __name__=='__main__': unittest.main()
