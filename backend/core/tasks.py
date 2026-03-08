#for handling the auto-release without using Celery (lazy check)
#this will be called using a cron job or Celery beat
#not using signals because they are instant triggers 
# and a 3-day release requires a scheduler (like django-celery-beat) 
# because django doesn't wait for 3 days inside a response-request cycle.
from datetime import timedelta
from django.utils import timezone
from .models import Milestone
from .services import FinanceService

def check_overdue_submissions():
    # Find milestones submitted > 3 days ago that haven't been approved/released
    three_days_ago = timezone.now() - timedelta(days=3)
    overdue_milestones = Milestone.objects.filter(
        status='submitted',
        submission__submitted_at__lte=three_days_ago
    )

    for milestone in overdue_milestones:
        # Use your existing FinanceService to release funds
        FinanceService.release_funds(milestone_id=milestone.id)
        # milestone.status = 'COMPLETED'
        # milestone.save()