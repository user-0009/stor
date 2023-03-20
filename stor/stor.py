from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from stor.auth import login_required
from stor.db import get_db
from math import ceil

bp = Blueprint('stor', __name__)

@bp.route('/')
def index():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 2
    #data = db.execute("SELECT * FROM posts").fetchall()
    #pagination_data = data[(page-1)*per_page:page*per_page]
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    total_pages = ceil(len(posts) / per_page)
    pagination_posts = posts[(page-1)*per_page:page*per_page]

    return render_template('stor/index.html', posts=pagination_posts, page=page, total_pages=total_pages)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Требуется заголовок.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                'VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('stor.index'))

    return render_template('stor/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f'Запись с индификатором {id} не существует.')

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Требуется указать заголовок'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('stor.index'))

    return render_template('stor/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('stor.index'))

def get_comments(post_id):
    comments = get_db().execute(
        '''SELECT comment.body, user.username, comment.created 
                 FROM comment 
                 JOIN user ON comment.author_id = user.id 
                 WHERE comment.post_id = ?''', (post_id,)
    ).fetchall()

    if post_id is None:
        abort(404, f'Запись с индификатором {id} не существует.')

    return comments

#@login_required
@bp.route("/<int:id>/comment", methods=("GET", "POST"))
def comment(id):

    if request.method == "POST":
        body = request.form["body"]
        error = None
        if not body:
            error = "Текст комментария обязателен."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO comment (body, post_id, author_id) VALUES (?, ?, ?)",
                (body, id, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("stor.comment", id=id))
    post = get_post(id)
    comments = get_comments(id)
    return render_template("stor/add_comment.html", post=post, comments=comments)


