# Generated by Django 2.2.6 on 2019-11-11 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_submission_limit_results'),
    ]

    operations = [
        migrations.AddField(
            model_name='productanalysisresult',
            name='bullets_score',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
