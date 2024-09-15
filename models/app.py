import sqlite3
from collections.abc import Iterable
from datetime import datetime, timedelta
from functools import wraps
from typing import Union, Any

import jwt
import requests
from flask import Flask, render_template, request, jsonify, Response

from enviromentReader import getSecretKey, getRecaptchaSecretKey, getRecaptchaSiteKey
from secured import hashPassword, verify
from .DBWorker import DBWorker, close


class Noted:

    def __init__(self, app_name: str = "Noted"):
        app = Flask(app_name, template_folder='templates', static_folder='static')
        self.app = app
        self.dbw = DBWorker()
        self.SECRET = getSecretKey()
        self.RECAPTCHA_SECRET = getRecaptchaSecretKey()

        # Application Routes
        @app.route('/')
        def home():
            a, b = self.getNotesTaken()
            if not a:
                _nt = "Could not connect to DataBase"
            else:
                _nt = int(b)

            return render_template('index.html', notes_taken=_nt)

        @app.route('/signup', methods=['GET', 'POST'])
        def signup():
            if request.method == 'GET':
                return render_template('signup.html', SITEKEY=getRecaptchaSiteKey())
            else:
                try:
                    username = request.form.get('username')
                    password = request.form.get('password')
                    recaptcha_response = request.form.get('g-recaptcha-response')

                    if not self.verifyRecaptcha(recaptcha_response):
                        return jsonify({'error': 'reCAPTCHA verification failed.'}), 400

                    if not username or not password:
                        print("Missing username or password")
                        return jsonify({
                            'status': 400,
                            'error': 'Data not fulfilled. Expected Username and Password.'
                        }), 400

                    password = hashPassword(password)
                    return self.makeUser(username, password)

                except Exception as e:
                    print(e)
                    return jsonify({
                        'status': 500,
                        'error': str(e)
                    }), 500

        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'GET':
                return render_template('login.html', SITEKEY=getRecaptchaSiteKey())
            else:
                try:
                    username = request.form.get('username')
                    password = request.form.get('password')
                    recaptcha_response = request.form.get('g-recaptcha-response')

                    if not self.verifyRecaptcha(recaptcha_response):
                        return jsonify({'error': 'reCAPTCHA verification failed.'}), 400

                    if not username or not password:
                        print("Missing username or password")
                        return jsonify({
                            'status': 400,
                            'error': 'Data not fulfilled. Expected Username and Password.'
                        }), 400

                    userData, _ = self.pullUserByUserName(username)

                    if not userData:
                        return {
                            "status": 401,
                            "error": "User does not exist."
                        }, 401

                    if not verify(str(userData['password']), password):
                        return {
                            "status": 401,
                            "error": "Invalid User-credentials."
                        }, 401

                    tkn = self.makeToken(username)

                    return {
                        'status': 201,
                        'token': tkn
                    }, 201

                except Exception as e:
                    print(e)
                    return jsonify({
                        'status': 500,
                        'error': str(e)
                    }), 500

        @app.route('/verifyToken', methods=['POST'])
        @self.user_auth()
        def verifyToken(_):
            return jsonify({
                'status': 200,
                'message': 'Token Valid',
                'isValid': True
            }), 200

        @app.route('/getUserData', methods=['POST'])
        @self.user_auth()
        def getUserData(user_data):
            user_data.pop('password', None)
            return user_data

        @app.route('/getNotes', methods=['POST'])
        @self.user_auth()
        def getNotes(user_data):
            uid = user_data['user_idx']
            return self.pullNotesByUserIDX(uid)

        @app.route('/dash', methods=['GET'])
        def dash():
            return render_template('dashboard.html')

        @app.route('/getTag/<int:tag_idx>', methods=['GET'])
        @self.user_auth()
        def getTag(user_data, tag_idx):
            try:
                tagData, _ = self.pullTagByTagIDX(tag_idx)

                if not tagData:
                    return jsonify({'status': 404, 'error': 'Tag not found'}), 404

                if tagData['user_idx'] != user_data['user_idx']:
                    return jsonify({'status': 401, 'error': 'User not authorized'}), 401

                return jsonify({'status': 200, 'data': tagData}), 200

            except Exception as e:
                print(e)
                return jsonify({
                    'status': 500,
                    'error': str(e)
                }), 500

        @app.route('/newTag', methods=['POST'])
        @self.user_auth()
        def newTag(user_data):
            try:
                tag_name = request.form.get('tag_name')
                tag_color = request.form.get('tag_color')
                recaptcha_response = request.form.get('g-recaptcha-response')

                if not self.verifyRecaptcha(recaptcha_response):
                    return jsonify({'error': 'reCAPTCHA verification failed.'}), 400

                if not tag_name or not tag_color:
                    print("Missing tag_name or tag_color")
                    return jsonify({
                        'status': 400,
                        'error': 'Data not fulfilled. Expected tag_name and tag_color.'
                    }), 400
                
                conn, curr = self.dbw.connect()
                q1 = 'INSERT INTO tags (tag_name, tag_color, user_idx, created_on, updated_on) VALUES (?, ?, ?, ?, ?)'
                ts = float((datetime.utcnow() + timedelta(hours=5, minutes=30)).timestamp())
                p1 = (str(tag_name), str(tag_color), int(user_data['user_idx']), ts, ts)
                curr.execute(q1, p1)
                conn.commit()
                return jsonify({
                    'status': 201,
                    'message': 'Success!'
                }), 201

            except Exception as e:
                print(e)
                return jsonify({}), 500

        @app.route('/newNote', methods=['GET', 'POST'])
        @self.user_auth()
        def newNote(user_data):
            if request.method == 'GET':
                return render_template('newNote.html')



        # Error handlers
        @app.errorhandler(404)
        def error_404(_):
            return render_template('404.html')

        @app.errorhandler(500)
        def error_500(error):
            return render_template('500.html', error=str(error)), 500

    def user_auth(self):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.method != 'GET':
                    token = request.headers.get('Authorization', '').split('Bearer ')[-1].strip()
                    try:
                        tokenData = jwt.decode(
                            token,
                            key=self.SECRET.encode(),
                            algorithms=['HS256'],
                            options={
                                "verify_signature": True,
                                "verify_exp": True,
                                "verify_nbf": False,
                                "verify_iat": True,
                                "verify_iss": False,
                                "verify_aud": False,
                                "verify_jti": False
                            }
                        )
                    except jwt.ExpiredSignatureError:
                        return jsonify({'status': 401, 'message': 'Token has expired', 'isValid': False}), 401
                    except jwt.InvalidTokenError:
                        return jsonify({'status': 401, 'message': 'Invalid token', 'isValid': False}), 401
                    except Exception as e:
                        return jsonify({'status': 500, 'message': f"An error occurred: {str(e)}", 'isValid': False}), 500

                    # Fetch the user data using the username
                    user_data, status_code = self.pullUserByUserName(tokenData['user'])

                    if user_data is None:
                        return jsonify({'status': 401, 'message': 'User not found', 'isValid': False}), 401

                    # Ensure user_data is a dictionary
                    user_data = dict(user_data)

                    return f(user_data, *args, **kwargs)
                else:
                    return f(None, *args, **kwargs)

            return decorated_function

        return decorator

    def getNotesTaken(self) -> Iterable[bool, int]:
        conn, curr = self.dbw.connect()
        query = 'SELECT COUNT(*) FROM notes'
        try:
            curr.execute(query)
            count = curr.fetchone()[0]
            return True, count
        except Exception as e:
            print(e)
            return False, 0
        finally:
            close(conn)

    def makeToken(self, username) -> str:
        try:
             return jwt.encode(
                {
                    'user': username,
                    'exp': (datetime.utcnow() + timedelta(hours=48)).timestamp(),
                    'iat': (datetime.utcnow() + timedelta(hours=5, minutes=30)).timestamp()
                }, self.SECRET.encode(), algorithm='HS256'
            )
        except Exception as e:
            raise RuntimeError('Error: ', e)

    def makeUser(self, username, hashed_password) -> Iterable[Response, int]:
        conn, curr = self.dbw.connect()
        query = 'INSERT INTO users (username, password, created_on, updated_on) VALUES (?, ?, ?, ?)'
        ts = float((datetime.utcnow() + timedelta(hours=5, minutes=30)).timestamp())
        params = (str(username), str(hashed_password), ts, ts)

        try:
            curr.execute(query, params)
            conn.commit()
            return jsonify({
                'status': 201,
                'message': 'User successfully created.',
                'token': self.makeToken(username)
            }), 201
        except sqlite3.IntegrityError:
            return jsonify({
                'status': 409,
                'error': 'Username already exists!'
            }), 409
        except Exception as e:
            print(e)
            return jsonify({
                'status': 500,
                'error': str(e)
            }), 500
        finally:
            close(conn)

    def pullUserByUserName(self, username) -> Union[tuple[Union[dict[Any, Any], dict[str, Any], dict[str, str], dict[bytes, bytes]], int], tuple[None, int]]:
        conn, curr = self.dbw.connect()
        q1 = 'SELECT * FROM users WHERE username = ?'
        p1 = (username,)

        try:
            curr.execute(q1, p1)
            row = curr.fetchone()
            if row is None:
                return None, 404  # Not Found if no user is found

            column_names = ['user_idx', 'username', 'password', 'created_on', 'updated_on']
            row_dict = dict(zip(column_names, row))
            readable_create_ts = datetime.fromtimestamp(float(row_dict['created_on'])).strftime('%d-%m-%Y %H:%M:%S %p')
            readable_update_ts = datetime.fromtimestamp(float(row_dict['updated_on'])).strftime('%d-%m-%Y %H:%M:%S %p')
            row_dict['readable_created_on'] = readable_create_ts
            row_dict['readable_updated_on'] = readable_update_ts
            return row_dict, 200
        except Exception as e:
            print(f"Error in pullUserByUserName: {e}")
            return None, 500
        finally:
            close(conn)

    def pullNotesByUserIDX(self, user_idx) -> Union[tuple[None, int], list[dict[str, str]]]:
        conn, curr = self.dbw.connect()
        q1 = 'SELECT * FROM notes WHERE user_idx = ?'
        p1 = (user_idx,)

        try:
            curr.execute(q1, p1)
            rows = curr.fetchall()
            if rows is None:
                return None, 404

            rows_dict = []
            for row in rows:
                colum_names = ['note_idx', 'note_title', 'note_text', 'created_on', 'updated_on', 'user_idx', 'tag_idx']
                row_dict = dict(zip(colum_names, row))
                readable_create_ts = datetime.fromtimestamp(float(row_dict['created_on'])).strftime('%d-%m-%Y %H:%M:%S %p')
                readable_update_ts = datetime.fromtimestamp(float(row_dict['updated_on'])).strftime('%d-%m-%Y %H:%M:%S %p')
                row_dict['readable_created_on'] = readable_create_ts
                row_dict['readable_updated_on'] = readable_update_ts
                rows_dict.append(row_dict)
            return rows_dict



        except Exception as e:
            print(f"Error in pullNotesByUserIDX: {e}")
            return None, 500
        finally:
            close(conn)

    def verifyRecaptcha(self, recaptcha_res):
        payload = {
            'secret': self.RECAPTCHA_SECRET,
            'response': recaptcha_res
        }

        res = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = res.json()
        return result.get('success')

    def pullTagByTagIDX(self, tag_idx) -> Union[tuple[None, int], tuple[dict[Any, Any], int]]:
        conn, curr = self.dbw.connect()
        q1 = 'SELECT * FROM tags WHERE tag_idx = ?'
        p1 = (tag_idx,)

        try:
            curr.execute(q1, p1)
            row = curr.fetchone()

            if row is None:
                return None, 401

            colum_names = ['tag_idx', 'tag_name', 'tag_color', 'user_idx', 'created_on', 'updated_on']
            row_dict = dict(zip(colum_names, row))
            return row_dict, 200

        except Exception as e:
            print(e)
            return None, 500
        finally:
            close(conn)

    def run(self,
            host: str = '0.0.0.0',
            port: int = 8080,
            DEBUG: bool = True):

        self.app.run(
            host=host,
            port=port,
            debug=DEBUG,
        )