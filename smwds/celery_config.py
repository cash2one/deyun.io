#!/usr/bin/python
#coding:utf-8
    
# Celery configuration
BROKER_URL = 'redis://localhost:6379/5'
CELERY_BACKEND = 'redis://localhost:6379/5'