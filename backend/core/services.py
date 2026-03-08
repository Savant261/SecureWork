from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Wallet, Contract, Transaction, Application, Milestone

class FinanceService:
    @staticmethod
    def deposit_funds(user, amount):
        """
        Adds money to a user's wallet and creates a ledger record.
        Uses transaction.atomic to ensure both happen or neither happens.
        """
        with transaction.atomic():
            wallet = user.wallet
            wallet.balance += amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='deposit',
                description=f"Deposited ${amount}"
            )
            return wallet

    # @staticmethod
    # def fund_milestone(milestone_id):
    #     """
    #     Locks funds from Client's balance into escrow_balance.
    #     """
    #     with transaction.atomic():
    #         # select_for_update() locks the row so no other process can spend this money simultaneously
    #         milestone = Milestone.objects.select_related('contract__client__wallet').get(id=milestone_id)
    #         client_wallet = milestone.contract.client.wallet
            
    #         if client_wallet.balance < milestone.amount:
    #             raise ValidationError("Insufficient balance to fund this milestone.")

    #         # Move money to Escrow
    #         client_wallet.balance -= milestone.amount
    #         client_wallet.escrow_balance += milestone.amount
    #         client_wallet.save()

    #         # Update Milestone Status
    #         milestone.status = 'funded'
    #         milestone.save()

    #         # Ledger record
    #         Transaction.objects.create(
    #             wallet=client_wallet,
    #             amount=milestone.amount,
    #             transaction_type='escrow_lock',
    #             description=f"Funded milestone: {milestone.title}"
    #         )
    #         return milestone

    @staticmethod
    def fund_milestone(milestone_id):
        with transaction.atomic():
        # 1. Fetch milestone (no need for select_related here if we lock wallet separately)
            milestone = Milestone.objects.get(id=milestone_id)
        
        # 2. CRITICAL: Lock the specific wallet row for the duration of this transaction
        # This prevents any other concurrent request from touching this specific wallet.
            client_wallet = Wallet.objects.select_for_update().get(user=milestone.contract.client)
        
            if client_wallet.balance < milestone.amount:
                raise ValidationError("Insufficient balance to fund this milestone.")

        # Move money to Escrow
            client_wallet.balance -= milestone.amount
            client_wallet.escrow_balance += milestone.amount
            client_wallet.save()

        # Update Milestone Status
            milestone.status = 'funded'
            milestone.save()

        # Ledger record
            Transaction.objects.create(
                wallet=client_wallet,
                amount=-milestone.amount,
                transaction_type='escrow_lock',
                description=f"Funded milestone: {milestone.title}"
            )
            return milestone

    @staticmethod
    def release_funds(milestone_id, user):
        """
        Moves money from Client's escrow_balance to Freelancer's balance.
        """
        with transaction.atomic():
            milestone = Milestone.objects.select_related(
                'contract__client__wallet', 
                'contract__freelancer__wallet'
            ).get(id=milestone_id)

            #to check if the current_user is client or freelancer
            if milestone.contract.client != user:
                raise ValidationError("You are not authorized to release funds for this contract.")
            
            client_wallet = milestone.contract.client.wallet
            freelancer_wallet = milestone.contract.freelancer.wallet

            # Logic Check
            if milestone.status != 'submitted':
                raise ValidationError("Milestone work has not been submitted yet.")

            # The Transfer
            client_wallet.escrow_balance -= milestone.amount
            freelancer_wallet.balance += milestone.amount
            
            client_wallet.save()
            freelancer_wallet.save()

            # Finalize Milestone
            milestone.status = 'approved'
            milestone.save()

            # Ledger record for Freelancer
            Transaction.objects.create(
                wallet=freelancer_wallet,
                amount=milestone.amount,
                transaction_type='escrow_release',
                description=f"Received payment for: {milestone.title}"
            )

            Transaction.objects.create(
                wallet=client_wallet,
                amount=-milestone.amount, # Negative to show as a deduction in the ledger
                transaction_type='escrow_release',
                description=f"Released payment for: {milestone.title}"
            )
            
            return milestone


    @staticmethod
    def withdraw_funds(user, amount):
        """
        Removes money from a user's available balance and creates a ledger record.
        Ensures the user has sufficient funds before processing.
        """
        with transaction.atomic():
            # Lock the wallet row to prevent race conditions during withdrawal
            wallet = Wallet.objects.select_for_update().get(user=user)
            
            # Validation: Ensure sufficient funds
            if wallet.balance < amount:
                raise ValidationError("Insufficient balance for withdrawal.")

            # Process the withdrawal
            wallet.balance -= amount
            wallet.save()

            # Create the ledger record
            Transaction.objects.create(
                wallet=wallet,
                amount=-amount, # Stored as a negative value for withdrawals
                transaction_type='withdraw',
                description=f"Withdrew ${amount} to bank account"
            )
            return wallet

class RecruitmentService:
    @staticmethod
    def hire_freelancer(application_id):
        """
        Accepts one application and marks the rest as rejected.
        """
        with transaction.atomic():
            # 1. Get the chosen application
            chosen_app = Application.objects.select_related('contract', 'freelancer').get(id=application_id)
            contract = chosen_app.contract

            # 2. Update Contract state
            contract.freelancer = chosen_app.freelancer
            contract.status = 'active'
            contract.save()

            # 3. Handle the "Selection"
            chosen_app.is_accepted = True
            chosen_app.save()

            # 4. Notify others (Logical effect)
            # We filter for all other applications for this contract
            rejected_apps = Application.objects.filter(contract=contract).exclude(id=application_id)
            
            # Here you would typically trigger a Django Signal or Email Task
            # For now, we just acknowledge they are no longer under consideration
            return {"status": "Success", "hired": chosen_app.freelancer.username}

class WorkService:
    @staticmethod
    def submit_work(milestone_id, freelancer, content):
        """
        Effect: Freelancer uploads proof, milestone status changes to 'submitted'.
        """
        with transaction.atomic():
            milestone = Milestone.objects.get(id=milestone_id)
            # Create the proof record
            Submission.objects.create(
                milestone=milestone,
                freelancer=freelancer,
                content=content
            )
            # Update milestone state
            milestone.status = 'submitted'
            milestone.save()
            return milestone


@transaction.atomic
def accept_freelancer_proposal(application_id, client_user):
    # 1. Fetch the application and ensure the user actually owns the contract
    application = Application.objects.select_related('contract').get(id=application_id)
    contract = application.contract

    if contract.client != client_user:
        raise PermissionError("You do not have permission to accept this proposal.")
    if contract.status != 'published':
        raise ValueError("This contract is no longer available.")

    # 2. Update Application status
    application.is_accepted = True
    application.save()

    # 3. Update Contract status and assign the freelancer
    contract.status = 'active'
    contract.freelancer = application.freelancer
    
    # Update the contract budget to match the exact proposed amount
    proposed_milestones = application.proposed_milestones.all()
    contract.total_budget = sum(pm.amount for pm in proposed_milestones)
    contract.save()

    # 4. Convert ProposedMilestones to official, actionable Milestones
    for pm in proposed_milestones:
        Milestone.objects.create(
            contract=contract,
            title=pm.title,
            amount=pm.amount,
            due_date=pm.due_date,
            status='pending'
        )

    # 5. Clean up: Reject all other applications for this specific contract
    Application.objects.filter(contract=contract, is_accepted=False).delete()

    return contract