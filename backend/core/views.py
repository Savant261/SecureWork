from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions, viewsets
from django.shortcuts import get_object_or_404
from .services import FinanceService, RecruitmentService, accept_freelancer_proposal
from .models import CustomUser, Milestone, Application, Submission, Transaction, Contract
from .serializers import SubmissionSerializer, ContractSerializer, WalletSerializer, RegisterSerializer, CustomTokenObtainPairSerializer, ApplicationSerializer, TransactionSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsFreelancer
from django.db import transaction
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from django.db.models import Sum,Q
from decimal import Decimal




class HireFreelancerView(APIView):
    '''the client selects a freelancer from the applications.
    so it updates the contract status nad notifies others.
    '''
    def post(self, request, application_id):
        try:
            #using recruitmentservice 
            result = RecruitmentService.hire_freelancer(application_id)
            return Response(result, status = status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)}, status = status.HTTP_400_BAD_REQUEST)

class FundMilestoneView(APIView):
    """
    Action: Client locks money for a specific milestone.
    Effect: Moves balance to escrow_balance in the Wallet.
    """
    def post(self, request, milestone_id):
        try:
            # We call the FinanceService logic
            milestone = FinanceService.fund_milestone(milestone_id)
            return Response(
                {"message": f"Milestone '{milestone.title}' funded successfully."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # Captures 'Insufficient Balance' or other logic errors
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ReleaseFundsView(APIView):
    """
    Action: Client approves work.
    Effect: Money moves from Client's Escrow to Freelancer's Balance.
    """
    def post(self, request, milestone_id):
        try:
            milestone = FinanceService.release_funds(milestone_id, request.user)
            return Response(
                {"message": f"Funds released to {milestone.contract.freelancer.username}"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubmitWorkView(APIView):
    permission_classes = [IsFreelancer]

    def post(self, request, milestone_id):
        content_url = request.data.get('submission_url')
        milestone = get_object_or_404(Milestone, id = milestone_id)

        with transaction.atomic():
            Submission.objects.create(
                milestone = milestone, 
                freelancer = request.user,
                content = content_url
            )
            # submission = serializer.save(freelancer=self.request.user)
            # # Update Milestone status
            # milestone = submission.milestone
            milestone.status = 'submitted'
            milestone.save()

        return Response({"status":"Work submitted successfully"}, status = status.HTTP_201_CREATED)


class WalletDetailView(generics.RetrieveAPIView):
    """Fetches the logged-in user's wallet balances."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        wallet = user.wallet
        escrow_balance = wallet.escrow_balance
        
        # If it's a freelancer, we calculate their "incoming" escrow 
        # from the milestones, rather than their literal wallet field.
        if user.role == 'freelancer':
            escrow_milestones = Milestone.objects.filter(contract__freelancer=user, status__in=['funded', 'submitted'])
            escrow_balance = escrow_milestones.aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            "balance": float(wallet.balance),
            "escrow_balance": float(escrow_balance),
            "last_updated": wallet.last_updated
        })

class DashboardContractListView(generics.ListCreateAPIView):
    """
    GET: Lists contracts relevant to the user (Client's created contracts OR Freelancer's joined contracts).
    POST: Allows a Client to create a new Contract.
    """
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return Contract.objects.filter(client=user).prefetch_related('milestones')
        elif user.role == 'freelancer':
            return Contract.objects.filter(freelancer=user).prefetch_related('milestones')
        return Contract.objects.none()

    def perform_create(self, serializer):
        # Only clients should create contracts.
        if self.request.user.role != 'client':
            raise permissions.PermissionDenied("Only clients can create contracts.")
        serializer.save(client=self.request.user)


class RegisterUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    # OVERRIDE the global setting so new users can actually sign up!
    permission_classes = [AllowAny] 
    serializer_class = RegisterSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class FinancialOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total_value = 0
        escrow_balance = 0
        action_count = 0

        if user.role == 'client':
            # Total Value: Sum of budgets of active/completed contracts
            contracts = Contract.objects.filter(client=user, status__in=['active', 'completed'])
            total_value = contracts.aggregate(Sum('total_budget'))['total_budget__sum'] or 0
            
            # Escrow Balance: Directly from the client's wallet
            escrow_balance = user.wallet.escrow_balance
            
            # Action Required: Pending applications OR submitted milestones needing approval
            pending_apps = Application.objects.filter(contract__client=user, contract__status='published', is_accepted=False).count()
            pending_milestones = Milestone.objects.filter(contract__client=user, status='submitted').count()
            action_count = pending_apps + pending_milestones

        elif user.role == 'freelancer':
            # Total Value: Sum of budgets of active/completed contracts they are assigned to
            contracts = Contract.objects.filter(freelancer=user, status__in=['active', 'completed'])
            total_value = contracts.aggregate(Sum('total_budget'))['total_budget__sum'] or 0
            
            # Escrow Balance: Sum of funded/submitted milestones for their active contracts
            escrow_milestones = Milestone.objects.filter(contract__freelancer=user, status__in=['funded', 'submitted'])
            escrow_balance = escrow_milestones.aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Action Required: Funded milestones that require work to be submitted
            action_count = Milestone.objects.filter(contract__freelancer=user, status='funded').count()

        return Response({
            "totalValue": float(total_value),
            "escrowBalance": float(escrow_balance),
            "actionCount": action_count
        })


class TransactionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    # Assuming you have a TransactionSerializer, otherwise replace with a simple APIView for now
    serializer_class = TransactionSerializer 

    def get_queryset(self):
        return Transaction.objects.filter(wallet__user = self.request.user).order_by('-timestamp')
    
class DepositFundsView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        amount = request.data.get('amount', 0)
        FinanceService.deposit_funds(request.user, Decimal(str(amount)))
        return Response({"status": "Deposit successful"})

class WithdrawFundsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            amount = request.data.get('amount', 0)
            # Now properly wired to your service logic!
            FinanceService.withdraw_funds(request.user, Decimal(str(amount)))
            return Response({"status": "Withdrawal processed successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class ContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            # Clients see only the contracts they created
            return Contract.objects.filter(client=user)
        else:
            # Freelancers see 'published' jobs AND jobs they are actively working on
            return Contract.objects.filter(Q(status='published') | Q(freelancer=user))

    def perform_create(self, serializer):
        # Auto-assign the creator as the client, and set to published
        serializer.save(client=self.request.user, status='published')


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Application.objects.all()

        if user.role == 'client':
            # Clients see pitches submitted to their contracts
            return Application.objects.filter(contract__client=user)
        else:
            # Freelancers see their own submitted pitches
            queryset = queryset.filter(freelancer = user)
        
        contract_id = self.request.query_params.get('contract', None)
        if contract_id is not None:
            queryset = queryset.filter(contract__id = contract_id)
        return queryset



    def perform_create(self, serializer):
        # Auto-assign the applicant as the freelancer
        serializer.save(freelancer=self.request.user)

    # This creates the POST /api/applications/<id>/accept/ endpoint
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        try:
            # Route the request through our secure service transaction
            contract = accept_freelancer_proposal(application_id=pk, client_user=request.user)
            return Response({"id":contract.id, "status": "success", "message": "Freelancer hired and milestones locked!"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


