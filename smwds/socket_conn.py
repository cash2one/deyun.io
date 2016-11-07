from flask import Flask, render_template, session, request, current_app, session, url_for
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from celery_task_socket import self_test, emit_site_status
import json

import logging


'''
Client socket events.
'''

class Socket_conn(Namespace):
    def on_my_event(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']})

    def on_my_broadcast_event(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']},
             broadcast=True)

    def on_join(self, message):
        join_room(message['room'])
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session['receive_count']})

    def on_leave(self, message):
        leave_room(message['room'])
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session['receive_count']})

    def on_close_room(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                             'count': session['receive_count']},
             room=message['room'])
        close_room(message['room'])

    def on_my_room_event(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']},
             room=message['room'])

    def on_disconnect_request(self):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'Disconnected!', 'count': session['receive_count']})
        disconnect()
    
    def on_func_init(self,message):
        data =  message['data'] 
        if  data:
            if data == 'sitestatus':
              emit_site_status.delay()



    def on_others(self):
        pass

    def on_connect(self):
        current_app.logger.info('@sid:' + str(session.session_id) + ':connected')

        #All client joined the 
        #join_room('1')

        emit('status', json.dumps({'status': 'Connected user', 'userid': session.session_id}))
        #self_test.delay(url = url_for('frontend.test', _external=True))
        emit('func_init','sitestatus')
        #emit('job started')
        #global thread
        #if thread is None:
        #    thread = socketio.start_background_task(target=background_thread)
        #emit('my_response', {'data': 'Connected', 'count': 0})

    def on_disconnect(self):
        #disconnect()
        current_app.logger.info('@sid:' + str(session.session_id) + ':disconnected')