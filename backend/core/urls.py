from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import HireFreelancerView, FundMilestoneView, ReleaseFundsView, SubmitWorkView, WalletDetailView, DashboardContractListView, RegisterUserView, CustomTokenObtainPairView

urlpatterns = [
    #auth endpoints
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='api-login'), #testing
    # path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name = 'token-refresh'),

    #data endpoints
    path('wallet/', WalletDetailView.as_view(), name='my-wallet'),
    path('contracts/', DashboardContractListView.as_view(), name='my-contracts'),
    path('wallet/transactions/', views.TransactionListView.as_view(), name = 'api-transactions'),
    path('analytics/financial-overview', views.FinancialOverviewView.as_view(), name = 'api-financial-overview'),

    #functional endpoints
    path('hire/<uuid:application_id>/', HireFreelancerView.as_view(), name='hire-freelancer'),
    path('fund-milestone/<uuid:milestone_id>/', FundMilestoneView.as_view(), name='fund-milestone'),
    path('release-funds/<uuid:milestone_id>/', ReleaseFundsView.as_view(), name = 'release-funds'),
    path('submit-work/', SubmitWorkView.as_view(), name = 'submit-work'),
    #path('submit-work/<uuid:milestone_id>/', SubmitWorkView.as_view(), name='submit-work') testing
    

]