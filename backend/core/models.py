import uuid #Instead of IDs like 1, 2, 3, we use UUIDs (e.g., 550e8400-e29b...). 
#This is a security measure so people can't guess the total number of users or scrape your data via URLs.
from django.db import models
from django.contrib.auth.models import AbstractUser
 #inherit from django base user class to create users
#specially use this to build roles (client, worker)

class Organization(models.Model):
    id = models.UUIDField(primary_key = True, editable = False, default = uuid.uuid4) #primary key for each obj (org)
    name = models.CharField(max_length = 255)
    created_at = models.DateTimeField(auto_now_add = True) #to track time when obj created

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    ROLES = (
        ('client', 'Client'), 
        ('freelancer', 'Freelancer')
    )

    id = models.UUIDField(primary_key = True, editable = False, default = uuid.uuid4)
    role = models.CharField(max_length = 10, choices = ROLES)
    organization = models.ForeignKey(  #for many-to-one relationship between models
                                        # works by adding a database column to the local model that references the primary key (or another unique field) 
                                        # of a remote model.
        Organization, 
        on_delete=models.SET_NULL, 
        null = True, 
        blank = True, 
        related_name="members"
    )

class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name = "wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default = 0.00)
    escrow_balance = models.DecimalField(max_digits = 12, decimal_places=2, default = 0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"


class Transaction(models.Model):
    TYPES = (
        ('deposit', 'Deposit'), 
        ('withdraw', 'Withdraw'),
        ('escrow_lock', 'Escrow Lock'),
        ('escrow_release', 'Escrow Release')
    )

    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    wallet = models.ForeignKey(Wallet, on_delete = models.CASCADE, related_name = "transactions")
    amount = models.DecimalField(max_digits = 12, decimal_places=2)
    transaction_type = models.CharField(max_length = 30, choices = TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank = True, null = True)


class Contract(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="contracts_created")
    freelancer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="contracts_joined")
    title = models.CharField(max_length=255)
    description = models.TextField()
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="applications")
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="my_applications")
    pitch = models.TextField(help_text="Why should the client hire you?")
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('contract', 'freelancer') # Prevents a freelancer from applying twice to the same job


class Milestone(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),   # Not started
        ('funded', 'Funded'),     # Money is in Escrow
        ('submitted', 'Submitted'), # Freelancer did the work
        ('approved', 'Approved'),   # Client released the money
        ('disputed', 'Disputed'),   # Something went wrong
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.amount}"


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    milestone = models.OneToOneField(Milestone, on_delete=models.CASCADE, related_name="submission")
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField(help_text="Link to work or description of work done.")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.milestone.title}"


class ProposedMilestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="proposed_milestones")
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"Proposed: {self.title} for {self.application.freelancer.username}"