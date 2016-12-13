from flask import Flask, render_template, session, request, current_app, session, url_for
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from celery_task_socket import self_test, emit_site_status, emit_master_status, emit_nodelist, emit_salt_task_list, emit_salt_jid
from extensions import redisapi
import json

import logging

'''
Client socket events.
'''


def emit_hacker_list(msg=None, msgtype='info', room=None):
    try:
        emit('hackerlist', json.dumps(
            {'emit_msg': msg, 'type': msgtype}), room=room)
    except Exception as e:
        current_app.logger.warning(
            'socker error :' + str(e) + ':' + room + ' session: ' + session['room'])


class Socket_conn(Namespace):

    def on_disconnect_request(self):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'Disconnected!', 'count': session['receive_count']})
        disconnect()

    def on_func_init(self, message):
        try:
            try:
                data = json.loads(message)
            except TypeError as e :
                data = message
            current_app.logger.info('enter  func' + str(data))
            if data:
                if data['func'] == 'sitestatus':
                    emit_site_status.delay(room=data['room'])
                    #emit('hackerlist',json.dumps({'emit_msg':'initialized sitestatus','type':'info'}),room=data['room'])
                    emit_hacker_list(msg='initialized sitestatus',
                                     room=data['room'])
                if data['func'] == 'm_status':
                    emit_master_status.delay(room=data['room'])
                    #emit('hackerlist',json.dumps({'emit_msg':'initialized m_status','type':'info'}),room=data['room'])
                    emit_hacker_list(msg='initialized m_status', room=data['room'])
                if data['func'] == 'nodelist':
                    emit_nodelist.delay(room=data['room'])
                    #emit('hackerlist',json.dumps({'emit_msg':'initialized m_status','type':'info'}),room=data['room'])
                    emit_hacker_list(msg='initialized nodelist', room=data['room'])
                if data['func'] == 'salt_task_list':
                    emit_salt_task_list.delay(room=session['room'])
                if data['func'] == 'salt_jid':
                    emit_salt_jid.delay(room=session['room'],jid=data['jid'])
                 if data['func'] == 'salt_ping':
                    emit_salt_ping.delay(room=session['room'],tgt=data['tgt'])
        except Exception as e:
            current_app.logger.exception(e)
            current_app.logger.warning(
            'socker_conn error :' + str(e) + ':' + message + ' session: ' + session['room'])
    

    def on_others(self):
        pass

    def on_connect(self):

        # All client joined the
        join_room('all')
        redisapi.hset('websocket',session.session_id,request.sid)
        session['room'] = request.sid
        emit_hacker_list(msg='You have connected', room=session['room'])
        current_app.logger.info(
            '@sid:' + str(session.session_id) + ':connected ' + 'room: ' + session['room'])
        emit('status', json.dumps(
            {'status': 'Connected user', 'userid': session.session_id}))
        #self_test.delay(url = url_for('frontend.test', _external=True))
        emit('func_init', json.dumps(
            {'func': 'sitestatus', 'room': session['room']}))
        # emit('func_init','sitestatus')
        emit('func_init', json.dumps(
            {'func': 'm_status', 'room': session['room']}))

        emit('func_init', json.dumps(
            {'func': 'nodelist', 'room': session['room']}))

        emit('func_init', json.dumps(
            {'func': 'salt_task_list', 'room': session['room']}))

    def on_disconnect(self):
        # disconnect()
        redisapi.hdel('websocket',session.session_id)
        #emit_hacker_list(msg='You have disconnected', room=session['room'])
        current_app.logger.info(
            '@sid:' + str(session.session_id) + ':disconnected')
