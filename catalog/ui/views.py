import requests
from django.shortcuts import render

from check import compare_contracts

from . import services
from .ai_assistant import explain_changes


def home(request):
    query = request.GET.get("q", "").strip().lower()
    products = services.load_registry()

    if query:
        products = [
            p for p in products
            if query in p["name"].lower() or query in p["description"].lower()
        ]

    for product in products:
        product["status"] = services.check_status(product)

    return render(request, "ui/home.html", {"products": products, "query": query})


def detail(request, name):
    product = services.find_product(name)
    if product is None:
        return render(request, "ui/detail.html", {"error": "Data product introuvable."}, status=404)

    status = services.check_status(product)
    records = status["records"]
    columns = list(records[0]) if records else []
    preview = [[row.get(col) for col in columns] for row in records[:10]]

    return render(request, "ui/detail.html", {
        "product": product,
        "contract": product["contract"],
        "status": status,
        "columns": columns,
        "preview": preview,
        "row_count": len(records),
        "proposals": services.load_proposals(name),
    })


def changes(request, name):
    product = services.find_product(name)
    if product is None:
        return render(request, "ui/changes.html", {"error": "Data product introuvable."}, status=404)

    proposals = services.load_proposals(name)
    context = {"product": product, "proposals": proposals}
    if not proposals:
        return render(request, "ui/changes.html", context)

    selected = request.GET.get("file", proposals[0]["file"])
    proposal = next((p for p in proposals if p["file"] == selected), proposals[0])

    result, change_list = compare_contracts(product["contract"], proposal["contract"])
    diff = {
        "contract": name,
        "old_version": product["contract"]["version"],
        "new_version": proposal["contract"]["version"],
        "status": result,
        "changes": change_list,
    }

    context.update(selected=proposal["file"], diff=diff, notes=explain_changes(diff))
    return render(request, "ui/changes.html", context)


def revenue(request):
    try:
        products = services.fetch_records(services.find_product("merchandising-products"))
        orders = services.fetch_records(services.find_product("fulfillment-orders"))
        invoices = services.fetch_records(services.find_product("finance-invoices"))
    except requests.RequestException:
        return render(request, "ui/revenue.html", {"error": "Un des domaines ne répond pas."})

    category = {p["product_id"]: p["category"] for p in products}
    product_of_order = {o["order_id"]: o["product_id"] for o in orders}

    totals = {}
    for invoice in invoices:
        if invoice["payment_status"] != "Paid":
            continue
        product_id = product_of_order.get(invoice["order_id"])
        cat = category.get(product_id, "Inconnu")
        totals[cat] = totals.get(cat, 0) + invoice["amount"]

    best = max(totals.values(), default=0)
    rows = [
        {"category": cat, "total": round(total, 2), "width": round(100 * total / best)}
        for cat, total in sorted(totals.items(), key=lambda item: -item[1])
    ]
    return render(request, "ui/revenue.html", {"rows": rows, "total": round(sum(totals.values()), 2)})
