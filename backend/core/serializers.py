from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Transaction, Wallet, Contract, Milestone, Application, Submission, Organization, ProposedMilestone
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'role', 'organization']

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class ContractSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)
    counterpart_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = ['id', 'title', 'description', 'total_budget', 'status', 'milestones', 'counterpart_name']

    def get_counterpart_name(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return "Pending"
            
        # If the logged-in user is the client, the counterpart is the freelancer
        if request.user.role == 'client':
            return obj.freelancer.username if obj.freelancer else "Unassigned"
        # If the logged-in user is the freelancer, the counterpart is the client
        else:
            return obj.client.username if obj.client else "Unknown Client"

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'milestone', 'content', 'submitted_at']
        read_only_fields = ['submitted_at']


    def validate(self, data):
        milestone = data['milestone']
        # Check if submission already exists
        if Submission.objects.filter(milestone=milestone).exists():
            raise serializers.ValidationError("Work has already been submitted for this milestone.")
        return data
    # def validate_milestone(self, value):
    #     if value.status != 'funded':
    #         raise serializers.ValidationError("Can only submit work for a funded milestone.")
    #     return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Allow login with either username or email
        username = attrs.get(self.username_field)
        password = attrs.get('password')

        if username and password:
            # Check if a user with this email exists
            user_obj = User.objects.filter(email=username).first()
            if user_obj:
                # Swap the email for the actual username before authenticating
                attrs[self.username_field] = user_obj.username

        return super().validate(attrs)
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add the custom claims
        token['role'] = user.role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance', 'escrow_balance', 'last_updated']



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=CustomUser.ROLES, required=True)
    company = serializers.CharField(write_only=True, required = False, allow_blank = True)

    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'role', 'email', 'first_name', 'last_name', 'company']

    def create(self, validated_data):
        #extracting company before creating user
        company_name = validated_data.pop('company', None)
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email = validated_data.get('email', ''),
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', ''),
            role=validated_data['role']
        )

        #adding check if role is client then retain the company else remove it from form
        if company_name and user.role == 'client':
            org, created = Organization.objects.get_or_create(name = company_name)
            user.organization = org
            
        # This securely hashes the password!
        user.set_password(validated_data['password'])
        user.save()
        return user


class ProposedMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposedMilestone
        fields = ['title', 'amount', 'due_date']

class ApplicationSerializer(serializers.ModelSerializer):
    proposed_milestones = ProposedMilestoneSerializer(many=True)
    #take 'cover_letter' from frontend and phir map it to pitch
    cover_letter = serializers.CharField(source = 'pitch')

    class Meta:
        model = Application
        fields = ['id', 'contract', 'freelancer', 'cover_letter', 'is_accepted', 'proposed_milestones']
        read_only_fields = ['freelancer', 'is_accepted']

    def create(self, validated_data):
        # Pop the proposed milestones out of the payload
        milestones_data = validated_data.pop('proposed_milestones', [])
        
        # Create the main application record
        application = Application.objects.create(**validated_data)
        
        # Loop through and create the linked proposed milestones
        for milestone_data in milestones_data:
            ProposedMilestone.objects.create(application=application, **milestone_data)
            
        return application