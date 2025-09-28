# csrp_project/tasks.py
from celery import shared_task
import requests
import httpx

@shared_task
def sample_task():
    """Sample Celery task"""
    return "Task completed successfully!"

@shared_task
def fetch_data_requests(url):
    """Sample task using requests"""
    response = requests.get(url)
    return response.json()

@shared_task
def fetch_data_httpx(url):
    """Sample task using httpx"""
    with httpx.Client() as client:
        response = client.get(url)
        return response.json()
