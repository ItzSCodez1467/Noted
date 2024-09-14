from flask import Flask, render_template, request, jsonify, Response
from .DBWorker import DBWorker, close
from enviromentReader import getSecretKey
from secured import hashPassword, verify
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Union, Any
import sqlite3
import jwt
from functools import wraps

class Noted:

    def __init__(self, app_name: str = "Noted"):
        app = Flask(app_name, template_folder='templates', static_folder='static')
        self.app = app
        self.dbw = DBWorker()
        self.SECRET = getSecretKey()

        # Application Routes
        @app.route('/')
        def home():
            a, b = self.getNotesTaken()
            if not a:
                _nt = "Could not connect to DataBase"
            else:
                _nt = int(b)

            return render_template('index.html', notesTaken=_nt)

        @app.route('/signup', methods=['GET', 'POST'])
        def signup():
            if request.method == 'GET':
                return render_template('signup.html')
            else:
                try:
                    username = request.form.get('username')
                    password = request.form.get('password')

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
                        'status': 501,
                        'error': str(e)
                    }), 501

        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'GET':
                return render_template('login.html')
            else:
                try:
                    username = request.form.get('username')
                    password = request.form.get('password')

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
                        'status': 501,
                        'error': str(e)
                    }), 501

        @app.route('/verifyToken', methods=['POST'])
        @self.user_auth()
        def verifyToken(user_data):
            return jsonify({
                'status': 200,
                'message': 'Token Valid',
                'isValid': True
            }), 200

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
                    # Token expired, return custom 401 response and stop further execution
                    return jsonify({'status': 401, 'message': 'Token has expired', 'isValid': False}), 401

                except jwt.InvalidTokenError:
                    # Invalid token, return custom 401 response and stop further execution
                    return jsonify({'status': 401, 'message': 'Invalid token', 'isValid': False}), 401

                except Exception as e:
                    # Handle any other unforeseen errors and stop further execution
                    return jsonify({'status': 500, 'message': f"An error occurred: {str(e)}", 'isValid': False}), 500

                # Now pull the user data by username
                user_data = self.pullUserByUserName(tokenData['user'])

                if not user_data:
                    # If user data isn't found, return custom unauthorized response
                    return jsonify({'status': 401, 'message': 'User not found', 'isValid': False}), 401

                # Proceed with the actual route function if the token is valid
                return f(user_data, *args, **kwargs)

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
                'status': 501,
                'error': str(e)
            }), 501
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
            return row_dict, 200
        except Exception as e:
            print(f"Error in pullUserByUserName: {e}")
            return None, 501
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