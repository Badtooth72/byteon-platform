"""Teacher-only bulk review; originals are retained alongside curated text."""
from datetime import datetime


def register_exam_review(app, mongo, teacher, token, valid_form):
    from flask import request, render_template, session, jsonify

    @app.route('/exam-bank/review')
    def exam_bulk_review():
        if not teacher():
            return 'Access denied', 403
        query = {}
        for field in ('paper_id', 'topic_codes'):
            value = request.args.get(field, '').strip()[:120]
            if value:
                query[field] = value
        if request.args.get('unreviewed') == '1':
            query['marking_review_status'] = {'$ne': 'teacher_verified'}
        try:
            page = max(1, int(request.args.get('page', '1')))
        except ValueError:
            return 'Invalid page', 400
        count = mongo.db.exam_questions.count_documents(query)
        questions = list(mongo.db.exam_questions.find(query).sort([
            ('year', -1), ('paper_id', 1), ('number', 1), ('label', 1)
        ]).skip((page - 1) * 12).limit(12))
        return render_template('exam_review.html', questions=questions,
            papers=list(mongo.db.exam_papers.find({}, {'_id': 0}).sort('year', -1)),
            topics=list(mongo.db.exam_topics.find({}, {'_id': 0}).sort('code', 1)),
            count=count, page=page, pages=max(1, (count + 11) // 12), form_token=token())

    @app.route('/exam-bank/review/<question_id>', methods=['POST'])
    def save_exam_review(question_id):
        if not session.get('username'):
            return jsonify(error='Your session expired. Sign in again, then reload this page.'),401
        if not teacher():
            return jsonify(error='Access denied'), 403
        if not valid_form():
            return jsonify(error='Your session expired. Refresh before saving.'), 400
        question = mongo.db.exam_questions.find_one({'question_id': question_id})
        if not question:
            return jsonify(error='Question not found'), 404
        values = {key: request.form.get(key, '').strip() for key in
                  ('question_text', 'marking_guidance', 'subtopic')}
        if any(len(values[key]) > limit for key, limit in
               [('question_text', 8000), ('marking_guidance', 12000), ('subtopic', 80)]):
            return jsonify(error='Text is too long'), 400
        verified = request.form.get('verified') == 'yes'
        if verified and (not values['question_text'] or not values['marking_guidance']):
            return jsonify(error='Verified questions need question text and marking guidance.'), 400
        revision = question.get('review_revision', 0)
        if request.form.get('revision') != str(revision):
            return jsonify(error='This question changed elsewhere. Refresh before saving.'), 409
        now = datetime.utcnow()
        values.update(prompt_review_status='teacher_verified' if verified else 'draft_needs_source_check',
                      marking_review_status='teacher_verified' if verified else 'draft_needs_source_check',
                      review_revision=revision + 1, prompt_reviewed_by=session['username'],
                      prompt_reviewed_at=now, marking_reviewed_by=session['username'], marking_reviewed_at=now)
        condition = {'_id': question['_id'], 'review_revision': revision} if revision else {
            '_id': question['_id'], '$or': [{'review_revision': 0}, {'review_revision': {'$exists': False}}]}
        result = mongo.db.exam_questions.update_one(condition, {'$set': values})
        if not result.modified_count:
            return jsonify(error='This question changed elsewhere. Refresh before saving.'), 409
        mongo.db.exam_review_history.insert_one({'question_id': question_id, 'edited_by': session['username'],
            'edited_at': now, 'previous': {key: question.get(key) for key in values}, 'updated': values})
        return jsonify(revision=revision + 1, message='Saved and verified' if verified else 'Draft saved')
