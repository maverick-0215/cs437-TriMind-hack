import io
import os
from datetime import date

from app.models import FoundItem
from conftest import ITEM_DEFAULTS


def test_S4_admin_can_add_item_with_all_fields_and_photo(app, admin):
    data = {**ITEM_DEFAULTS, "photo": (io.BytesIO(b"fake-image-bytes"), "bottle.jpg")}
    resp = admin.post("/admin/items/new", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302

    item = FoundItem.query.one()
    assert item.category == "Bottle"
    assert item.title == "Steel bottle"
    assert item.date_found == date(2026, 10, 3)
    assert item.general_area == "Library"
    assert item.exact_location == ITEM_DEFAULTS["exact_location"]
    assert item.description == ITEM_DEFAULTS["description"]
    assert os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], item.photo_path))

    page = admin.get(f"/admin/items/{item.id}").get_data(as_text=True)
    assert ITEM_DEFAULTS["exact_location"] in page
    assert ITEM_DEFAULTS["description"] in page
    assert admin.get(f"/admin/items/{item.id}/photo").data == b"fake-image-bytes"


def test_S4_photo_is_optional(add_item):
    assert add_item().photo_path is None


def test_S4_missing_field_or_unknown_category_is_rejected(admin):
    for bad in [{"title": ""}, {"exact_location": ""}, {"category": "Spaceship"}, {"date_found": "not-a-date"}]:
        resp = admin.post("/admin/items/new", data={**ITEM_DEFAULTS, **bad})
        assert resp.status_code == 400, bad
    assert FoundItem.query.count() == 0


def test_S5_new_item_is_available(add_item):
    assert add_item().status == "AVAILABLE"
