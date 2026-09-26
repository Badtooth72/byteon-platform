"""Scenario-based J277 network design, marked on the server."""
DEVICES = {'pc': 'Computer', 'switch': 'Switch', 'router': 'Router', 'wap': 'Wireless access point', 'server': 'Server', 'internet': 'Internet', 'tablet': 'Tablet'}

def q(prompt, answer, alternatives, explanation):
    return dict(prompt=prompt, answer=answer, options=alternatives, explanation=explanation)

SCENARIOS = [
 dict(id='school', title='Connect a school classroom', brief='Connect two computers and a file server to a central switch. Provide tablet Wi-Fi through an access point, and connect the LAN to the Internet through a router.', questions=[
 q('The classroom network covers one site. What is it?', 'LAN', ['LAN','WAN'], 'A LAN covers a small geographical area; a WAN spans a larger area.'),
 q('What type of network links school sites in different towns?', 'WAN', ['WAN','A single LAN','One NIC'], 'A WAN covers a wide geographical area, often using communications infrastructure from other organisations.'),
 q('Which model gives staff central control over files and accounts?', 'Client-server', ['Client-server','Peer-to-peer'], 'Clients request services from centrally managed servers; peer-to-peer devices share directly.'),
 q('What is a drawback of peer-to-peer file sharing in a large school?', 'Accounts and files are harder to manage centrally', ['Accounts and files are harder to manage centrally','Every peer must be a dedicated server','Peers cannot share files'], 'Peer-to-peer can be inexpensive for small groups, but management and access control become harder at scale.'),
 q('What topology uses a central switch?', 'Star', ['Star','Mesh'], 'Each device connects to the centre. A central switch failure affects the network.'),
 q('Which hardware gives each computer a network connection?', 'NIC', ['NIC','CPU','SSD'], 'A network interface controller connects a device to a network.'),
 q('What happens as more devices share the same bandwidth?', 'Less bandwidth available per device', ['Less bandwidth available per device','Bandwidth always doubles','No possible effect'], 'Network load and available bandwidth affect performance.'),
 q('Which medium is suitable for reliable classroom computer connections?', 'Ethernet cable', ['Ethernet cable','Bluetooth','Wi-Fi only'], 'Wired Ethernet is reliable and avoids wireless interference, but limits movement.')]),
 dict(id='internet', title='Bring a library online', brief='Build the same connected LAN for two library computers, a local server and a Wi-Fi tablet. Then choose how its users reach online services.', questions=[
 q('Which service resolves a domain name to an IP address?', 'DNS', ['DNS','SMTP','FTP'], 'DNS servers provide name resolution so clients can locate servers.'),
 q('Where are cloud services provided?', 'On remote servers', ['On remote servers','Only on the local NIC','Only in a cable'], 'Cloud services provide storage, software or processing remotely.'),
 q('What is a drawback of relying on cloud files?', 'Access depends on connectivity', ['Access depends on connectivity','Files cannot be shared','No remote access'], 'Internet disruption can prevent access; remote access is also a benefit.'),
 q('What is an advantage of using a cloud document service?', 'Access and collaborate from different locations', ['Access and collaborate from different locations','Internet access is never needed','The local NIC stores all remote data'], 'Remote services allow users to access shared work without being at one site.'),
 q('Which protocol encrypts web traffic?', 'HTTPS', ['HTTPS','HTTP','FTP'], 'HTTPS protects data in transit; HTTP does not provide this encryption.'),
 q('Which device forwards data between this LAN and another network?', 'Router', ['Router','Switch','NIC'], 'Routers connect networks. Switches connect devices within a LAN.'),
 q('What does web hosting provide?', 'A server that stores and serves website content', ['A server that stores and serves website content','A replacement for DNS names','A keyboard driver'], 'Web clients request pages from web servers hosted on connected networks.')]),
 dict(id='protocols', title='Equip a small business', brief='Connect the office computers, server, tablet and Internet. The business also needs email, file transfers and interoperable networking.', questions=[
 q('Which protocol sends email?', 'SMTP', ['SMTP','POP','IMAP'], 'SMTP handles sending email between clients and servers and between mail servers.'),
 q('Which email protocol keeps messages on the server and synchronises devices?', 'IMAP', ['IMAP','POP','FTP'], 'IMAP supports server-based mail access across devices.'),
 q('Which protocol typically downloads mail to a client?', 'POP', ['POP','SMTP','HTTP'], 'POP retrieves messages, commonly for local storage; deletion depends on configuration.'),
 q('Which protocol is intended for transferring files?', 'FTP', ['FTP','DNS','SMTP'], 'FTP transfers files between client and server.'),
 q('Which protocol suite supports reliable delivery and addressing on the Internet?', 'TCP/IP', ['TCP/IP','SMTP only','Bluetooth only'], 'TCP manages reliable delivery; IP provides addressing and supports routing between networks.'),
 q('Why use agreed standards and protocols?', 'Devices from different makers can communicate', ['Devices from different makers can communicate','All devices must use one manufacturer','Passwords become unnecessary'], 'Standards define common rules; protocols define communication rules.'),
 q('Why split networking into layers?', 'Parts can be developed and changed independently', ['Parts can be developed and changed independently','It removes the need for addresses','It doubles every connection speed'], 'Layers separate responsibilities, making development and troubleshooting easier.')]),
 dict(id='wireless', title='Plan a resilient workspace', brief='Build a small full mesh: connect three computers directly to one another with Ethernet (three links). Connect an access point and router to one of these computers, add a Wi-Fi tablet, and connect the router to the Internet. This is a simplified topology model for comparing resilience, rather than a hardware configuration exercise.', questions=[
 q('Which connection suits a tablet that moves around the room?', 'Wi-Fi', ['Wi-Fi','Ethernet cable','A server power cable'], 'Wi-Fi allows mobility, but coverage and interference can affect it.'),
 q('Which connection suits a nearby wireless headset?', 'Bluetooth', ['Bluetooth','Ethernet','FTP'], 'Bluetooth is suitable for short-range device connections.'),
 q('Which is a valid example of IPv4 format?', '192.168.1.20', ['192.168.1.20','999.888.777.666','AA:BB:CC:DD:EE:FF'], 'IPv4 has four decimal octets from 0 to 255.'),
 q('Which is an example of IPv6 format?', '2001:db8::1', ['2001:db8::1','192.168.1.20','A website title'], 'IPv6 uses hexadecimal groups separated by colons; consecutive zero groups may be compressed.'),
 q('Which identifies a network interface on a local network?', 'MAC address', ['MAC address','File extension','Domain name'], 'A MAC address is assigned to a network interface, usually shown as six hexadecimal pairs.'),
 q('Which is an example of a MAC address?', 'AA:BB:CC:DD:EE:FF', ['AA:BB:CC:DD:EE:FF','192.168.1.20','2001:db8::1'], 'A MAC address is commonly represented as six pairs of hexadecimal digits.'),
 q('What is a benefit of mesh over a star with one central switch?', 'Alternative paths if a link fails', ['Alternative paths if a link fails','It always needs fewer cables','It cannot fail'], 'Mesh offers redundant paths but can cost more and be harder to manage.')]),
 dict(id='security', title='Secure the school network', brief='Build the connected school LAN, then defend its users, files and online services. Choose protections that address the stated threat.', questions=[
 q('An attachment installs malicious software. What helps detect it?', 'Anti-malware', ['Anti-malware','A faster switch','FTP'], 'Anti-malware detects and removes known malicious software; users should also avoid suspicious attachments.'),
 q('A fake login email tricks a user into revealing a password. Which attack is this?', 'Phishing / social engineering', ['Phishing / social engineering','Mesh networking','File compression'], 'Attackers exploit trust to obtain information. Awareness and verification reduce this risk.'),
 q('What reduces the chance that repeated password guesses succeed?', 'Strong passwords and attempt limits', ['Strong passwords and attempt limits','Short shared passwords','Turning off encryption'], 'Brute-force attacks try many passwords. Long passwords and limiting attempts help.'),
 q('What can filter unwanted network traffic?', 'Firewall', ['Firewall','NIC alone','Bluetooth headset'], 'Firewalls enforce traffic rules. Denial-of-service floods resources; filtering can help but is not a guarantee.'),
 q('An attacker floods a website with requests so legitimate users cannot access it. What is this?', 'Denial of service', ['Denial of service','DNS resolution','IMAP synchronisation'], 'A denial-of-service attack exhausts resources or bandwidth to disrupt availability.'),
 q('What protects intercepted data from being read without the key?', 'Encryption', ['Encryption','A larger monitor','HTTP alone'], 'Encryption transforms readable data into ciphertext; authorised recipients use a key.'),
 q('What does encryption do to readable data before transmission?', 'Transforms it into ciphertext using a key', ['Transforms it into ciphertext using a key','Deletes all network addresses','Stops every possible attack'], 'Encryption protects confidentiality. It does not stop phishing or denial of service on its own.'),
 q('An attacker inserts SQL through a form to manipulate a database. What is this?', 'SQL injection', ['SQL injection','DNS lookup','Cloud hosting'], 'Unsafe query construction can execute attacker-controlled SQL. Parameterised queries and validation reduce risk.'),
 q('How should student access to staff files be controlled?', 'User access levels', ['User access levels','Give everyone administrator access','Use one shared password'], 'Restrict permissions to the resources each role needs.'),
 q('How can weaknesses be identified before attackers exploit them?', 'Authorised penetration testing', ['Authorised penetration testing','Disable all passwords','Publish credentials'], 'Authorised testing probes systems for vulnerabilities so they can be fixed.'),
 q('How can someone be prevented from stealing the server physically?', 'Locked server room', ['Locked server room','HTTPS alone','A domain name'], 'Physical security controls access to equipment.')])
]

def mark_design(scenario, design, answers):
    nodes, links = design.get('nodes', []), design.get('links', [])
    if not isinstance(nodes, list) or not isinstance(links, list) or len(nodes)>20 or len(links)>60:
        raise ValueError('Invalid network size')
    ids = {}
    for node in nodes:
        if not isinstance(node, dict) or node.get('type') not in DEVICES or not isinstance(node.get('id'), str) or len(node['id'])>40 or node['id'] in ids:
            raise ValueError('Invalid device')
        ids[node['id']] = node['type']
        for coordinate in ('x','y'):
            value = node.get(coordinate, 100)
            if not isinstance(value, (int,float)) or isinstance(value,bool) or not 0 <= value <= 900:
                raise ValueError('Invalid device position')
    edges = set()
    for link in links:
        if not isinstance(link, dict) or link.get('a') not in ids or link.get('b') not in ids or link['a']==link['b'] or link.get('medium') not in {'Ethernet','Wi-Fi'}:
            raise ValueError('Invalid connection')
        edges.add((min(link['a'],link['b']),max(link['a'],link['b']),link['medium']))
    pcs = [k for k,v in ids.items() if v=='pc']
    switches = [k for k,v in ids.items() if v=='switch']
    def connected(x,y,medium='Ethernet'):
        return (min(x,y),max(x,y),medium) in edges
    centres = [s for s in switches if sum(connected(pc,s) for pc in pcs)>=2
               and any(connected(v,s) for v,t in ids.items() if t=='server')
               and any(connected(v,s) for v,t in ids.items() if t=='wap')
               and any(connected(v,s) for v,t in ids.items() if t=='router')]
    star = bool(centres)
    wireless = any(connected(w,s) and connected(t,w,'Wi-Fi') for s in centres
                   for w,kind in ids.items() if kind=='wap' for t,t_kind in ids.items() if t_kind=='tablet')
    internet = any(connected(r,s) and connected(i,r) for s in centres
                   for r,kind in ids.items() if kind=='router' for i,i_kind in ids.items() if i_kind=='internet')
    if scenario['id']=='wireless':
        from itertools import combinations
        triples = [triple for triple in combinations(pcs,3) if all(connected(a,b) for a,b in combinations(triple,2))]
        mesh_pcs = {pc for triple in triples for pc in triple}
        checks = [(len(pcs)>=3,'Add three computers.'),
                  (bool(triples),'Connect all three computers to one another using three Ethernet links.'),
                  (any(connected(w,p) and connected(t,w,'Wi-Fi') for p in mesh_pcs for w,k in ids.items() if k=='wap' for t,tk in ids.items() if tk=='tablet'), 'Attach an access point to a mesh computer, then connect a tablet using Wi-Fi.'),
                  (any(connected(r,p) and connected(i,r) for p in mesh_pcs for r,k in ids.items() if k=='router' for i,ik in ids.items() if ik=='internet'), 'Connect a mesh computer to the router, then the router to the Internet.')]
    else:
        checks = [(len(pcs)>=2,'Add at least two computers.'),
                  (star,'Connect both computers, a server, an access point and a router to the same switch using Ethernet.'),
                  (wireless,'Connect a tablet using Wi-Fi to the access point on your completed LAN.'),
                  (internet,'Connect the LAN router to the Internet using Ethernet.')]
    feedback = [dict(correct=ok, text=text) for ok,text in checks]
    for i,item in enumerate(scenario['questions']):
        feedback.append(dict(correct=answers.get(str(i))==item['answer'],text=item['explanation'],prompt=item['prompt']))
    earned = sum(item['correct'] for item in feedback)
    return dict(score=round(earned/len(feedback)*100,1), earned=earned, maximum=len(feedback), feedback=feedback)

def register_network_designer(app,mongo,token,valid_form):
    from flask import session, redirect, url_for, render_template, request, jsonify
    from datetime import datetime
    import json
    @app.route('/network-designer',methods=['GET','POST'])
    def network_designer():
        if not session.get('username'):
            return redirect(url_for('login'))
        scenario = next((s for s in SCENARIOS if s['id']==request.values.get('scenario','school')), None)
        if not scenario:
            return 'Unknown scenario',404
        user = mongo.db.users.find_one({'username':session['username']}) or {}
        saved = (user.get('activities',{}).get('network_designer',{}).get(scenario['id']) or {})
        if request.method=='POST':
            if not valid_form():
                return jsonify(error='Session expired. Refresh the page.'),400
            try:
                if len(request.form.get('design','')) > 20000 or len(request.form.get('answers','')) > 8000:
                    raise ValueError('Submission too large')
                design=json.loads(request.form.get('design','{}'))
                answers=json.loads(request.form.get('answers','{}'))
                if not isinstance(design,dict) or not isinstance(answers,dict): raise ValueError('Invalid submission')
                result=mark_design(scenario,design,answers)
            except (ValueError,TypeError,KeyError):
                return jsonify(error='Invalid network submission'),400
            mongo.db.users.update_one({'username':session['username']},{'$set':{
                f"activities.network_designer.{scenario['id']}.design":design,
                f"activities.network_designer.{scenario['id']}.answers":answers,
                f"activities.network_designer.{scenario['id']}.last_score":result['score'],
                f"activities.network_designer.{scenario['id']}.date":datetime.utcnow()},
                '$max':{f"activities.network_designer.{scenario['id']}.score":result['score']},
                '$inc':{f"activities.network_designer.{scenario['id']}.attempts":1}})
            return jsonify(result)
        public = {key:value for key,value in scenario.items() if key!='questions'}
        public['questions']=[{'prompt':item['prompt'],'options':item['options']} for item in scenario['questions']]
        return render_template('network_designer.html',scenario=public,scenarios=SCENARIOS,devices=DEVICES,saved=saved,form_token=token())
