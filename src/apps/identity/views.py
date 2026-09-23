from .forms import DemoForm
from django.shortcuts import render


def home(request):
    context = {
        "platform_name": "NCD Patient Safety Platform",
        "message": "Patient safety, care coordination and support.",
        "method": request.method,
        "path": request.path,
        "name": request.GET.get("name"),
    }

    return render(request, "home.html", context)


def case_demo(request, case_id):
    context = {
        "case_id": case_id,
    }

    return render(request, "case_demo.html", context)
def demo_form(request):
    form = DemoForm()

    context = {
        "form": form,
    }

    return render(request, "demo_form.html", context)
