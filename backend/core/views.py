from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from .services import FinanceService, RecruitmentService
from .models import CustomUser, Milestone, Application, Submission, Transaction
from .serializers import SubmissionSerializer, ContractSerializer, WalletSerializer, RegisterSerializer, CustomTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsFreelancer
from django.db import transaction
from rest_framework_simplejwt.views import TokenObtainPairView




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
            milestone = FinanceService.release_funds(milestone_id)
            return Response(
                {"message": f"Funds released to {milestone.contract.freelancer.username}"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubmitWorkView(generics.CreateAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [IsFreelancer]

    def perform_create(self, serializer):
        with transaction.atomic():
            submission = serializer.save(freelancer=self.request.user)
            # Update Milestone status
            milestone = submission.milestone
            milestone.status = 'submitted'
            milestone.save()


class WalletDetailView(generics.RetrieveAPIView):
    """Fetches the logged-in user's wallet balances."""
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Automatically returns the wallet of the user making the request
        return self.request.user.wallet

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
        # Stubbed data returning strings to be parsed by your frontend parseFloat()
        # To be replaced later with actual aggregations from Wallet/Transaction models
        return Response({
            "total_earned": "0.00",
            "total_spent": "0.00",
            "in_escrow": "0.00"
        })


class TransactionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    # Assuming you have a TransactionSerializer, otherwise replace with a simple APIView for now
    # serializer_class = TransactionSerializer 
    
    def get_queryset(self):
        return Transaction.objects.filter(wallet__user=self.request.user).order_by('-created_at')