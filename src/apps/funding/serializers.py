from rest_framework import serializers

from .models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingDecision,
    FundingProgramme,
    FundingReview,
    FundingSource,
    ProgrammeRule,
)


class ProgrammeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammeRule
        fields = [
            "id",
            "public_id",
            "rule_name",
            "max_amount_per_case",
            "target_icd10_prefix",
            "description",
            "is_active",
        ]
        read_only_fields = ["id", "public_id"]


class FundingProgrammeSerializer(serializers.ModelSerializer):
    rules = ProgrammeRuleSerializer(many=True, read_only=True)

    class Meta:
        model = FundingProgramme
        fields = [
            "id",
            "public_id",
            "source",
            "name",
            "description",
            "budget_limit",
            "allocated_amount",
            "disbursed_amount",
            "currency_code",
            "status",
            "start_date",
            "end_date",
            "rules",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at"]


class FundingSourceSerializer(serializers.ModelSerializer):
    programmes = FundingProgrammeSerializer(many=True, read_only=True)

    class Meta:
        model = FundingSource
        fields = [
            "id",
            "public_id",
            "name",
            "source_type",
            "status",
            "contact_name",
            "contact_email",
            "currency_code",
            "total_allocation",
            "allocated_amount",
            "disbursed_amount",
            "programmes",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at"]


class FundingReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingReview
        fields = [
            "id",
            "public_id",
            "application",
            "reviewer",
            "recommendation",
            "recommended_amount",
            "review_notes",
            "reviewed_at",
        ]
        read_only_fields = ["id", "public_id", "reviewed_at"]


class FundingDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingDecision
        fields = [
            "id",
            "public_id",
            "application",
            "decision_maker",
            "decision",
            "approved_amount",
            "currency_code",
            "conditions",
            "decision_notes",
            "decided_at",
        ]
        read_only_fields = ["id", "public_id", "decided_at"]


class AssistanceAuthorizationSerializer(serializers.ModelSerializer):
    remaining_balance = serializers.DecimalField(
        max_digits=19,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = AssistanceAuthorization
        fields = [
            "id",
            "public_id",
            "authorization_code",
            "decision",
            "case",
            "facility",
            "authorized_amount",
            "disbursed_amount",
            "remaining_balance",
            "currency_code",
            "valid_from",
            "valid_to",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at", "remaining_balance"]


class FundingApplicationSerializer(serializers.ModelSerializer):
    decision = FundingDecisionSerializer(read_only=True)
    reviews = FundingReviewSerializer(many=True, read_only=True)

    class Meta:
        model = FundingApplication
        fields = [
            "id",
            "public_id",
            "application_number",
            "case",
            "programme",
            "applicant_type",
            "applied_by",
            "requested_amount",
            "approved_amount",
            "currency_code",
            "clinical_justification",
            "status",
            "submitted_at",
            "decision",
            "reviews",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at", "decision", "reviews"]
