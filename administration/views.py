from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.urls import reverse
from authenticator.models import Profile, Form
from tester.models import (Test, Question, TestResult)
from django.db.models.functions import TruncDate
from django.db.models import Count, Sum
from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render
from .forms import CreateTestForm, EditQuestionForm, QuestionUploadForm
import re
import json
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.utils import timezone

from docx import Document


# def print_cbt_cards(request):
#     today = timezone.localdate()
#     students = User.objects.filter(date_joined__date=today)
#
#     context = {
#         'students': students,
#         'exam_url': 'akintolatech.pythonanywhere.com',
#     }
#
#     return render(
#         request,
#         'administration/users/access_cards.html',
#         context,
#     )


def print_cbt_cards(request):
    students = User.objects.all()

    context = {
        'students': students,
        'exam_url': 'akintolatech.pythonanywhere.com',
    }

    return render(
        request,'administration/users/access_cards.html',
        context
    )




@staff_member_required
def upload_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    form = QuestionUploadForm()
    success = 0
    failed = []

    if request.method == 'POST':
        form = QuestionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            content = file.read().decode('utf-8')

            # Split the text into blocks (questions separated by blank lines)
            blocks = re.split(r'\n\s*\n', content.strip())

            for block in blocks:
                lines = block.strip().splitlines()
                question_data = {
                    'question': '',
                    'options': {},
                    'correct_key': '',
                }

                for line in lines:
                    line = line.strip()

                    # Detect options like A. Text
                    match = re.match(r'^([A-Da-d])\.\s*(.+)$', line)
                    if match:
                        key, val = match.groups()
                        question_data['options'][key.upper()] = val.strip()

                    # Detect answer like ANSWER: C
                    elif line.lower().startswith('answer:'):
                        match = re.match(r'^answer\s*[:\-–]?\s*([A-Da-d])$', line, re.IGNORECASE)
                        if match:
                            question_data['correct_key'] = match.group(1).strip().upper()

                    # Assume the first non-option, non-answer line is the question
                    elif not question_data['question']:
                        question_data['question'] = line

                # Validate and store
                if (question_data['question']
                        and question_data['correct_key'] in question_data['options']
                        and len(question_data['options']) == 4):

                    try:
                        correct_option_text = question_data['options'][question_data['correct_key']]

                        Question.objects.create(
                            question_text=question_data['question'],
                            test=test,
                            A=question_data['options'].get('A', ''),
                            B=question_data['options'].get('B', ''),
                            C=question_data['options'].get('C', ''),
                            D=question_data['options'].get('D', ''),
                            correct_option=correct_option_text  # ✅ Save the full text here
                        )
                        success += 1

                    except Exception as e:
                        failed.append({'question': question_data['question'], 'error': str(e)})

                else:
                    failed.append({'question': question_data.get('question', 'Unknown'), 'error': 'Bad formatting or missing data'})

            return render(request, "administration/test_mgmt/upload_questions.html", {
                'form': form,
                'success_count': success,
                'failed': failed,
                'test': test
            })

    return render(request, "administration/test_mgmt/upload_questions.html", {
        'form': form,
        'test': test
    })


@staff_member_required
def administration_dashboard(request):
    today = date.today()
    last_30_days = [today - timedelta(days=i) for i in range(30)]  # Fetch data for last 7 days

    context = {

        # from authenticator.models
        "total_classes": Form.objects.all().count(),
        "total_students": Profile.objects.all().count(),


        # from tester.models
        "total_tests": Test.objects.all().count(),
        "total_results": TestResult.objects.all().count(),
        "total_questions": Question.objects.all().count(),
    }

    return render(request, "administration/dashboard/administration_dashboard.html", context)


@staff_member_required
def test_mgmt(request):
    context = {

        "total_tests": Test.objects.all().count(),
        "tests": Test.objects.all(),
    }
    return render(request, "administration/test_mgmt/test_mgmt.html", context)


@staff_member_required
def create_test(request):
    if request.method == "POST":
        form = CreateTestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Test created successfully.")
            return redirect("administration:create_test")
    else:
        form = CreateTestForm()

    context = {
        "form": form,
    }
    return render(request, "administration/test_mgmt/create_test.html", context)


@staff_member_required
def edit_test(request, test_id):
    test = Test.objects.get(pk=test_id)
    questions = Question.objects.filter(test=test_id)
    if request.method == "POST":
        form = EditQuestionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Test created successfully.")
            return redirect("administration:edit_test")
    else:
        form = EditQuestionForm()

    context = {
        "test": test,
        "questions": questions,
        "form": form
    }
    return render(request, "administration/test_mgmt/edit_test.html",context)