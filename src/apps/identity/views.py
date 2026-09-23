from django.shortcuts import render


def home(request):
    context = {
        "platform_name": "NCD Patient Safety Platform",
        "message": "Patient safety, care coordination and support.",
    }

    return render(request, "home.html", context)


def case_demo(request, case_id):
    context = {
        "case_id": case_id,
    }

    return render(request, "case_demo.html", context)
