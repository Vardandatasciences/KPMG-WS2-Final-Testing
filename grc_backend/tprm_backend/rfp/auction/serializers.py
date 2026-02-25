from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import Auction, AuctionEvaluationCriteria, AuctionBid


class AuctionEvaluationCriteriaSerializer(AutoDecryptingModelSerializer):
    """Serializer for Auction Evaluation Criteria"""
    auction_id = serializers.IntegerField(write_only=True, required=False)
    auction = serializers.PrimaryKeyRelatedField(queryset=Auction.objects.all(), required=False, allow_null=True)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = AuctionEvaluationCriteria
        fields = [
            'criteria_id', 'auction_id', 'auction', 'criteria_name', 'criteria_description', 
            'weight_percentage', 'evaluation_type', 'min_score', 
            'max_score', 'median_score', 'is_mandatory', 
            'veto_enabled', 'veto_threshold', 'min_word_count',
            'expected_boolean_answer', 'display_order', 'created_by', 'data_inventory'
        ]
        read_only_fields = ['criteria_id', 'created_by']
    
    def validate_data_inventory(self, value):
        if not isinstance(value, dict):
            return {}
        return value
    
    def get_auction_id(self, obj):
        try:
            if hasattr(obj, 'auction_id'):
                return obj.auction_id
            elif hasattr(obj, 'auction') and obj.auction:
                return obj.auction.auction_id
        except Exception:
            pass
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['auction_id'] = self.get_auction_id(instance)
        return representation
    
    def validate(self, data):
        """Validate evaluation criteria data and convert auction_id to auction"""
        # Convert auction_id to auction if auction_id is provided but auction is not
        auction_id = data.pop('auction_id', None)
        if auction_id is not None:
            try:
                from .models import Auction
                auction_obj = Auction.objects.get(auction_id=auction_id)
                data['auction'] = auction_obj
            except Auction.DoesNotExist:
                raise serializers.ValidationError({'auction_id': f'Auction with ID {auction_id} does not exist'})
            except Exception as e:
                raise serializers.ValidationError({'auction_id': f'Error fetching Auction: {str(e)}'})
        elif 'auction' not in data or data.get('auction') is None:
            # If neither auction_id nor auction is provided, make it optional for now
            # The view will handle setting it if needed
            pass
        
        # Validate weight_percentage
        if 'weight_percentage' in data:
            weight = data['weight_percentage']
            if weight < 0 or weight > 100:
                raise serializers.ValidationError(
                    {"weight_percentage": "Weight must be between 0 and 100"}
                )
        
        return data


class AuctionSerializer(AutoDecryptingModelSerializer):
    """Serializer for Auction model"""
    evaluation_criteria = AuctionEvaluationCriteriaSerializer(many=True, required=False)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = Auction
        fields = [
            'auction_id', 'auction_number', 'auction_title', 'description', 'auction_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'created_at', 'updated_at',
            'approval_workflow_id', 'evaluation_method', 'budget_range_min',
            'budget_range_max', 'criticality_level', 'geographical_scope',
            'compliance_requirements', 'custom_fields', 'final_evaluation_score',
            'award_decision_date', 'award_justification', 'documents', 'evaluation_criteria',
            'data_inventory', 'retentionExpiry', 'auction_start_time', 'auction_end_time',
            'starting_bid', 'reserve_price', 'bid_increment', 'auction_format'
        ]
        read_only_fields = ['auction_id', 'auction_number', 'created_by', 'created_at', 'updated_at']
    
    def validate_data_inventory(self, value):
        if not isinstance(value, dict):
            return {}
        return value


class AuctionCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating Auction"""
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Auction
        fields = [
            'auction_id', 'auction_number', 'auction_title', 'description', 'auction_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'approval_workflow_id', 'evaluation_method',
            'budget_range_min', 'budget_range_max', 'criticality_level',
            'geographical_scope', 'compliance_requirements', 'custom_fields',
            'data_inventory', 'retentionExpiry', 'documents', 'auction_start_time',
            'auction_end_time', 'starting_bid', 'reserve_price', 'bid_increment', 'auction_format'
        ]
        read_only_fields = ['auction_id', 'auction_number', 'created_by']


class AuctionListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for Auction list view"""
    
    class Meta:
        model = Auction
        fields = [
            'auction_id', 'auction_number', 'auction_title', 'description', 'auction_type',
            'status', 'created_at', 'submission_deadline', 'criticality_level',
            'created_by', 'budget_range_min', 'budget_range_max', 'category'
        ]
