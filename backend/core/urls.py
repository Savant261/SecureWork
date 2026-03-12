from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenRefreshView



router = DefaultRouter()
router.register(r'contracts', views.ContractViewSet, basename = 'contract')
router.register(r'applications', views.ApplicationViewSet, basename = 'application')

urlpatterns = [
    path('',include(router.urls)),
    #auth endpoints
    path('register/', views.RegisterUserView.as_view(), name='register'),
    #path('login/', CustomTokenObtainPairView.as_view(), name='api-login'), #testing
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name = 'token-refresh'),
    path('stats/', views.FinancialOverviewView.as_view(), name = 'api-financial-overview'),
    #data endpoints
    path('wallet/', views.WalletDetailView.as_view(), name='my-wallet'),
    path('wallet/transactions/', views.TransactionListView.as_view(), name = 'api-transaction'),
    path('contracts/', views.DashboardContractListView.as_view(), name='my-contracts'),
    path('wallet/transactions/', views.TransactionListView.as_view(), name = 'api-transactions'),
    path('analytics/financial-overview', views.FinancialOverviewView.as_view(), name = 'api-financial-overview'),

    #functional endpoints
    path('applications/<uuid:application_id>/accept/', views.HireFreelancerView.as_view(), name='hire-freelancer'),
    path('milestones/<uuid:milestone_id>/fund/', views.FundMilestoneView.as_view(), name='fund-milestone'),
    path('release-funds/<uuid:milestone_id>/', views.ReleaseFundsView.as_view(), name = 'release-funds'),
    path('milestones/<uuid:milestone_id>/submit/', views.SubmitWorkView.as_view(), name = 'submit-work'),
    #path('submit-work/<uuid:milestone_id>/', SubmitWorkView.as_view(), name='submit-work') testing
    # urls.py
    path('wallet/deposit/', views.DepositFundsView.as_view(), name='deposit-funds'),
    path('wallet/withdraw/', views.WithdrawFundsView.as_view(), name='withdraw-funds'),


]
