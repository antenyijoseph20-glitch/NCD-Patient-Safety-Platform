import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0002_caseassignment'),
        ('patients', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MentalHealthScreening',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('public_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('screening_tool', models.CharField(choices=[('PHQ9', 'Patient Health Questionnaire (PHQ-9) - Depression'), ('GAD7', 'Generalized Anxiety Disorder (GAD-7) - Anxiety')], default='PHQ9', max_length=20)),
                ('score', models.PositiveSmallIntegerField(help_text='Standard clinical score (0-27 for PHQ-9, 0-21 for GAD-7)')),
                ('severity', models.CharField(choices=[('MINIMAL', 'Minimal / None (Score 0-4)'), ('MILD', 'Mild (Score 5-9)'), ('MODERATE', 'Moderate (Score 10-14)'), ('MODERATELY_SEVERE', 'Moderately Severe (Score 15-19)'), ('SEVERE', 'Severe (Score 20+)')], max_length=30)),
                ('suicidal_ideation_detected', models.BooleanField(default=False, help_text='Flagged if Question 9 on PHQ-9 evaluates > 0')),
                ('depression_risk_flag', models.BooleanField(default=False)),
                ('psychosocial_support_plan', models.TextField(blank=True, default='', help_text='Counselling referral, peer support group, or psycho-oncology liaison')),
                ('screened_at', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mental_health_screenings', to='cases.caresupportcase')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mental_health_screenings', to='patients.patient')),
                ('screened_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='conducted_mental_health_screenings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'mental_health_screening',
                'ordering': ['-screened_at', 'id'],
                'indexes': [
                    models.Index(fields=['case', 'screening_tool'], name='mental_heal_case_id_cd888a_idx'),
                    models.Index(fields=['patient', 'severity'], name='mental_heal_patient_40baf3_idx'),
                    models.Index(fields=['suicidal_ideation_detected'], name='mental_heal_suicida_f4066a_idx'),
                ],
            },
        ),
    ]
