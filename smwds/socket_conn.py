from flask import Flask, render_template, session, request, current_app, session, url_for
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from celery_task_socket import self_test, emit_site_status, emit_master_status
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
        #data =  message['data'] 
        data = json.loads(message)
        if  data:
            if data['func'] == 'sitestatus':
              emit_site_status.delay(room=data['room'])
              emit('hackerlist',json.dumps({'emit_msg':'initialized sitestatus','type':'info'}),room=data['room'])
            if data['func'] == 'm_status':
              emit_master_status.delay(room=data['room'])
              emit('hackerlist',json.dumps({'emit_msg':'initialized m_status','type':'info'}),room=data['room'])



    def on_others(self):
        pass

    def on_connect(self):

        #All client joined the 
        #join_room('1')
        session['room'] = request.sid
        current_app.logger.info('@sid:' + str(session.session_id) + ':connected '+'room: '+ session['room'])
        emit('status', json.dumps({'status': 'Connected user', 'userid': session.session_id}))
        #self_test.delay(url = url_for('frontend.test', _external=True))
        emit('func_init',json.dumps({'func': 'sitestatus', 'room': session['room']}))
        #emit('func_init','sitestatus')
        emit('func_init',json.dumps({'func': 'm_status', 'room': session['room']}))
        #emit('job started')
        #global thread
        #if thread is None:
        #    thread = socketio.start_background_task(target=background_thread)
        #emit('my_response', {'data': 'Connected', 'count': 0})

    def on_disconnect(self):
        #disconnect()
        current_app.logger.info('@sid:' + str(session.session_id) + ':disconnected')