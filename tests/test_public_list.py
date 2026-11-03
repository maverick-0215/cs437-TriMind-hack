import io

from conftest import ITEM_DEFAULTS


def titles(client, query=""):
    return [i["title"] for i in client.get("/api/items" + query).get_json()]


def test_S6_logged_in_user_sees_available_items_newest_first(student, add_item):
    add_item(title="Old umbrella", category="Umbrella", date_found="2026-09-01", general_area="Hostel")
    add_item(title="New bottle", date_found="2026-10-05")

    page = student.get("/").get_data(as_text=True)
    assert "Old umbrella" in page and "Umbrella" in page and "01 Sep 2026" in page and "Hostel" in page
    assert page.index("New bottle") < page.index("Old umbrella")
    assert titles(student) == ["New bottle", "Old umbrella"]


def test_S6_only_available_items_are_listed(add_item, student, other, claim_item):
    claim_item(other, add_item(title="Claimed bottle"))
    add_item(title="Free bottle")
    assert titles(student) == ["Free bottle"]
    assert "Claimed bottle" not in student.get("/").get_data(as_text=True)


def test_S7_list_and_api_hide_private_details(student, add_item):
    add_item()
    page = student.get("/").get_data(as_text=True)
    api = student.get("/api/items").get_data(as_text=True)
    for secret in (ITEM_DEFAULTS["exact_location"], ITEM_DEFAULTS["description"], "SECRET"):
        assert secret not in page
        assert secret not in api
    assert set(student.get("/api/items").get_json()[0]) == {"id", "category", "title", "date_found", "general_area"}


def test_S7_photo_is_not_served_to_non_admins(anon, student, admin):
    data = {**ITEM_DEFAULTS, "photo": (io.BytesIO(b"img"), "p.png")}
    admin.post("/admin/items/new", data=data, content_type="multipart/form-data")
    assert "/photo" not in student.get("/").get_data(as_text=True)
    assert anon.get("/admin/items/1/photo").status_code == 302
    assert student.get("/admin/items/1/photo").status_code == 403


def test_S8_filter_by_category(student, add_item):
    add_item(title="Bottle A")
    add_item(title="Umbrella A", category="Umbrella")
    assert titles(student, "?category=Umbrella") == ["Umbrella A"]
    page = student.get("/?category=Umbrella").get_data(as_text=True)
    assert "Umbrella A" in page and "Bottle A" not in page


def test_S9_filter_by_date_range(student, add_item):
    add_item(title="September", date_found="2026-09-15")
    add_item(title="Early Oct", date_found="2026-10-01")
    add_item(title="Late Oct", date_found="2026-10-31")
    assert titles(student, "?from=2026-10-01&to=2026-10-30") == ["Early Oct"]
    assert titles(student, "?from=2026-10-01") == ["Late Oct", "Early Oct"]
    assert titles(student, "?to=2026-09-30") == ["September"]
    page = student.get("/?from=2026-10-01&to=2026-10-30").get_data(as_text=True)
    assert "Early Oct" in page and "September" not in page and "Late Oct" not in page


def test_S10_keyword_search_matches_title_or_category_ignoring_case(student, add_item):
    add_item(title="Black wallet", category="Wallet/Purse")
    add_item(title="Red umbrella", category="Umbrella")
    add_item(title="Steel flask", category="Bottle")
    assert titles(student, "?q=WALLET") == ["Black wallet"]  # title, any case
    assert titles(student, "?q=bottle") == ["Steel flask"]  # category only
    assert "Red umbrella" in student.get("/?q=uMbReLlA").get_data(as_text=True)


def test_S10_keyword_search_does_not_match_private_description(student, add_item):
    add_item(title="Steel flask", description="contains a hidden passport")
    assert titles(student, "?q=passport") == []
