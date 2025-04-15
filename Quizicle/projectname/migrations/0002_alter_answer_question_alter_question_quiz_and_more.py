# Generated by Django 5.1.5 on 2025-02-24 13:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectname', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='Question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='projectname.question'),
        ),
        migrations.AlterField(
            model_name='question',
            name='Quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='projectname.quiz'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='QuestionCount',
            field=models.IntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='QuizMaximumPoints',
            field=models.IntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='results',
            name='Quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='projectname.quiz'),
        ),
    ]
