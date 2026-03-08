from django.contrib import admin
from .models import Organization, CustomUser, ProposedMilestone, Wallet, Transaction, Contract, Application, Milestone, Submission


admin.site.register(Organization)
admin.site.register(CustomUser)
admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(Contract)
admin.site.register(Application)
admin.site.register(Milestone)
admin.site.register(Submission)
admin.site.register(ProposedMilestone)
